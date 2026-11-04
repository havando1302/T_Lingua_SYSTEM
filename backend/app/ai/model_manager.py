"""
ModelManager — Singleton quản lý lifecycle của tất cả AI models.

Thay vì load model ở module-level (khi import), ModelManager cho phép:
  1. Load tất cả models 1 lần khi FastAPI startup.
  2. Kiểm tra trạng thái models cho /health endpoint.
  3. Các service truy cập model qua model_manager instance thay vì global.
  4. Khi chuyển môi trường (Local → Colab → VPS), chỉ cần đổi config.
"""
import time
from typing import Optional

import torch


class ModelManager:

    def __init__(self):
        self.whisper_model = None
        self.nllb_model = None
        self.nllb_tokenizer = None
        self.tts_model_eng = None
        self.tts_tokenizer_eng = None
        self.tts_model_vie = None
        self.tts_tokenizer_vie = None
        self.deepfilter_model = None
        self.deepfilter_state = None
        self._device: str = "cpu"
        self._loaded: bool = False
        self._whisper_device: str = "not_loaded"
        self._whisper_compute_type: str = "not_loaded"
        self._whisper_backend: str = "not_loaded"
        self._whisper_model_id: str = "not_loaded"
        self._whisper_fallback: bool = False
        self._nllb_model_id: str = "not_loaded"
        self._tts_model_eng: str = "not_loaded"
        self._tts_model_vie: str = "not_loaded"
        self._deepfilter_model_id: str = "none"
        self._tts_device: str = "not_loaded"
        self._tts_dtype: str = "not_loaded"
        self._denoise_device: str = "disabled"
        self._load_seconds: float = 0.0

    # ── Helpers ─────────────────────────────────────────────

    @property
    def device(self) -> str:
        return self._device

    def _resolve_device(self, device_setting: str) -> str:
        if device_setting == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device_setting

    # ── Load ────────────────────────────────────────────────

    def load_all(self, settings) -> None:
        """
        Load tất cả AI models lên device.
        Gọi 1 lần duy nhất từ FastAPI lifespan/startup.
        """
        from app.core.config import settings as _fallback
        s = settings or _fallback

        load_started = time.perf_counter()
        self._device = self._resolve_device(s.DEVICE)
        whisper_device = getattr(s, "WHISPER_DEVICE", "auto")
        whisper_device = self._device if whisper_device == "auto" else whisper_device
        compute_type = s.WHISPER_COMPUTE_TYPE
        if compute_type == "auto":
            compute_type = "float16" if whisper_device == "cuda" else "int8"

        print("=" * 56)
        print("  T-LINGUA MODEL MANAGER")
        print("=" * 56)
        print(f"  Device : {self._device}")
        from app.services.translation_service import TRANSLATION_POLICY_VERSION
        print(f"  Translation policy : {TRANSLATION_POLICY_VERSION}; beam={s.TRANSLATION_BEAM_SIZE}; "
              f"fidelity_rerank={getattr(s, 'TRANSLATION_FIDELITY_RERANK', True)}")
        if self._device == "cuda" and torch.cuda.is_available():
            print(f"  GPU    : {torch.cuda.get_device_name(0)}")
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"  VRAM   : {vram:.2f} GB")
        print("-" * 56)

        # --- Whisper ---
        t0 = time.time()
        backend = getattr(s, "WHISPER_BACKEND", "auto")
        use_torch = backend == "transformers" or (backend == "auto" and s.WHISPER_MODEL == "small")
        whisper_label = (getattr(s, "WHISPER_TORCH_MODEL", "openai/whisper-large-v3-turbo")
                         if whisper_device == "cuda" and use_torch else s.WHISPER_MODEL)
        print(f"  Loading Whisper ({whisper_label}) ...", end=" ", flush=True)
        if whisper_device == "cuda" and use_torch:
            try:
                from app.ai.torch_whisper_adapter import TorchWhisperModel
                self.whisper_model = TorchWhisperModel(
                    getattr(s, "WHISPER_TORCH_MODEL", "openai/whisper-large-v3-turbo"), "cuda",
                    revision=s.WHISPER_TORCH_REVISION,
                    local_files_only=getattr(s, "WHISPER_TORCH_LOCAL_ONLY", False),
                )
                self._whisper_backend = "transformers"
                self._whisper_model_id = getattr(s, "WHISPER_TORCH_MODEL", "openai/whisper-large-v3-turbo")
                compute_type = "float16"
            except Exception as error:
                if backend == "transformers":
                    raise
                self.whisper_model = None
                print(f"Torch GPU checkpoint unavailable ({type(error).__name__}); trying CTranslate2 ...", end=" ", flush=True)
        if self.whisper_model is None:
            from faster_whisper import WhisperModel
            try:
                self.whisper_model = WhisperModel(
                    s.WHISPER_MODEL,
                    device=whisper_device,
                    compute_type=compute_type,
                    cpu_threads=getattr(s, "WHISPER_CPU_THREADS", 4),
                )
                # Validate CUDA libraries now, rather than failing on first turn.
                import numpy as np
                dummy_pcm = np.zeros(1600, dtype=np.float32)
                list(self.whisper_model.transcribe(dummy_pcm, language="vi", vad_filter=False)[0])
            except Exception as error:
                if whisper_device != "cuda":
                    raise
                self._whisper_fallback = True
                self.whisper_model = None
                print(f"Whisper CUDA unavailable ({type(error).__name__}), falling back to CPU int8 ...", end=" ", flush=True)
                whisper_device, compute_type = "cpu", "int8"
                self.whisper_model = WhisperModel(
                    s.WHISPER_MODEL,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=getattr(s, "WHISPER_CPU_THREADS", 4),
                )
            self._whisper_backend = "ctranslate2"
            self._whisper_model_id = s.WHISPER_MODEL
        self._whisper_device, self._whisper_compute_type = whisper_device, compute_type
        print(f"OK ({time.time() - t0:.1f}s)")

        # --- NLLB ---
        t0 = time.time()
        self._nllb_model_id = s.NLLB_MODEL
        print(f"  Loading NLLB ({s.NLLB_MODEL}) ...", end=" ", flush=True)
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        from app.ai.torch_whisper_adapter import load_cached_first
        import os

        self.nllb_tokenizer = load_cached_first(
            AutoTokenizer,
            s.NLLB_MODEL, revision=s.NLLB_REVISION,
        )

        use_int8 = os.getenv("NLLB_INT8", "0") == "1"
        if use_int8:
            self.nllb_model = load_cached_first(
                AutoModelForSeq2SeqLM,
                s.NLLB_MODEL, revision=s.NLLB_REVISION, load_in_8bit=True, device_map="auto"
            )
        else:
            torch_dtype = torch.float16 if self._device == "cuda" else None
            self.nllb_model = load_cached_first(
                AutoModelForSeq2SeqLM,
                s.NLLB_MODEL, revision=s.NLLB_REVISION, dtype=torch_dtype
            ).to(self._device)

            if self._device == "cuda":
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True

        self.nllb_model.eval()

        # Suppress max_length warning
        try:
            self.nllb_model.generation_config.max_length = None
        except Exception:
            pass

        # Optional optimizations
        use_bt = os.getenv("NLLB_BETTER_TRANSFORMER", "0") == "1"
        if use_bt:
            try:
                self.nllb_model = self.nllb_model.to_bettertransformer()
            except Exception:
                pass

        use_compile = os.getenv("NLLB_TORCH_COMPILE", "0") == "1"
        if use_compile:
            try:
                self.nllb_model = torch.compile(self.nllb_model)
            except Exception:
                pass

        print(f"OK ({time.time() - t0:.1f}s)")

        # --- VITS TTS ---
        t0 = time.time()
        print("  Loading VITS (ENG + VIE) ...", end=" ", flush=True)
        from transformers import VitsModel, AutoTokenizer as VitsTokenizer

        configured_tts_device = getattr(s, "TTS_DEVICE", "auto")
        if configured_tts_device == "auto":
            if self._device == "cuda" and torch.cuda.is_available():
                vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                tts_device = "cuda" if vram_gb >= 8 else "cpu"
            else:
                tts_device = "cpu"
        else:
            tts_device = configured_tts_device
        configured_tts_dtype = getattr(s, "TTS_DTYPE", "float32")
        if configured_tts_dtype == "float16" and tts_device == "cuda":
            tts_dtype = torch.float16
        elif configured_tts_dtype == "auto":
            tts_dtype = torch.float16 if tts_device == "cuda" else torch.float32
        else:
            tts_dtype = torch.float32
        self._tts_device = tts_device
        self._tts_dtype = str(tts_dtype).removeprefix("torch.")
        self._tts_model_eng = s.TTS_MODEL_ENG
        self._tts_model_vie = s.TTS_MODEL_VIE
        self.tts_model_eng = load_cached_first(
            VitsModel,
            s.TTS_MODEL_ENG, revision=s.TTS_MODEL_ENG_REVISION,
            dtype=tts_dtype,
        ).to(tts_device).eval()
        self.tts_tokenizer_eng = load_cached_first(
            VitsTokenizer,
            s.TTS_MODEL_ENG, revision=s.TTS_MODEL_ENG_REVISION,
        )
        self.tts_model_vie = load_cached_first(
            VitsModel,
            s.TTS_MODEL_VIE, revision=s.TTS_MODEL_VIE_REVISION,
            dtype=tts_dtype,
        ).to(tts_device).eval()
        self.tts_tokenizer_vie = load_cached_first(
            VitsTokenizer,
            s.TTS_MODEL_VIE, revision=s.TTS_MODEL_VIE_REVISION,
        )
        print(f"OK ({time.time() - t0:.1f}s)")

        # --- DeepFilterNet (optional) ---
        if s.ENABLE_DEEPFILTER:
            t0 = time.time()
            print("  Loading DeepFilterNet ...", end=" ", flush=True)
            try:
                from app.core.compat import apply_torch_patches
                apply_torch_patches()
                configured_denoise_device = getattr(s, "DENOISE_DEVICE", "auto")
                if configured_denoise_device == "auto":
                    if self._device == "cuda" and torch.cuda.is_available():
                        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                        denoise_device = "cuda" if vram_gb >= 8 else "cpu"
                    else:
                        denoise_device = "cpu"
                else:
                    denoise_device = configured_denoise_device
                # DeepFilterNet reads DEVICE from its own global config.  Set
                # it only for initialization; the application model settings
                # were already resolved by Pydantic above.
                previous_device = os.environ.get("DEVICE")
                os.environ["DEVICE"] = denoise_device
                try:
                    from df.enhance import init_df  # type: ignore[import-not-found,import-untyped]
                    # The pretrained cache may be readable but not writable (for
                    # example inside a sandbox or a shared model volume). DeepFilter
                    # only needs the checkpoint; its default enhance.log is optional.
                    self.deepfilter_model, self.deepfilter_state, _ = init_df(log_file=None)
                finally:
                    if previous_device is None:
                        os.environ.pop("DEVICE", None)
                    else:
                        os.environ["DEVICE"] = previous_device
                self._denoise_device = denoise_device
                self._deepfilter_model_id = "DeepFilterNet3"
                print(f"OK ({time.time() - t0:.1f}s)")
            except Exception as e:
                print(f"SKIP ({e})")
                self.deepfilter_model = None
                self.deepfilter_state = None
                self._denoise_device = "unavailable"
        else:
            print("  DeepFilterNet : DISABLED")

        if self._device == "cuda" and getattr(s, "PREWARM_MODELS", True):
            t0 = time.perf_counter()
            print("  Prewarming inference models ...", end=" ", flush=True)
            try:
                import numpy as np
                from app.ai.torch_whisper_adapter import TorchWhisperModel

                if isinstance(self.whisper_model, TorchWhisperModel):
                    self.whisper_model.transcribe(
                        np.zeros(16000, dtype=np.float32), language="vi", beam_size=1)
                if self.deepfilter_model is not None and self.deepfilter_state is not None:
                    from df.enhance import enhance  # type: ignore[import-not-found,import-untyped]
                    with torch.inference_mode():
                        enhance(self.deepfilter_model, self.deepfilter_state,
                                torch.zeros(1, 48000),
                                atten_lim_db=getattr(s, "DENOISE_ATTENUATION_DB", 12.0))
                # NLLB's first CUDA generation initializes kernels and is
                # materially slower than steady state.  Pay that cost during
                # startup so the first user turn has normal latency.
                for source_lang, target_lang, sample in (
                    ("vie_Latn", "eng_Latn", "Hệ thống đã sẵn sàng."),
                    ("eng_Latn", "vie_Latn", "The system is ready."),
                ):
                    self.nllb_tokenizer.src_lang = source_lang
                    nllb_inputs = self.nllb_tokenizer(sample, return_tensors="pt").to(self._device)
                    with torch.inference_mode():
                        self.nllb_model.generate(
                            **nllb_inputs,
                            forced_bos_token_id=self.nllb_tokenizer.convert_tokens_to_ids(target_lang),
                            max_new_tokens=24,
                            num_beams=s.TRANSLATION_BEAM_SIZE,
                        )
                for model, tokenizer, sample in (
                    (self.tts_model_eng, self.tts_tokenizer_eng, "Ready."),
                    (self.tts_model_vie, self.tts_tokenizer_vie, "Sẵn sàng."),
                ):
                    with torch.inference_mode():
                        inputs = tokenizer(sample, return_tensors="pt").to(model.device)
                        model(**inputs, speaking_rate=0.85,
                              noise_scale=0.667, noise_scale_dp=0.8).waveform
                torch.cuda.synchronize()
                print(f"OK ({time.perf_counter() - t0:.1f}s)")
            except Exception as error:
                print(f"SKIP ({type(error).__name__})")

        self._loaded = True
        self._load_seconds = time.perf_counter() - load_started
        print("-" * 56)
        print("  ALL MODELS LOADED")
        print("=" * 56)

    # ── Status ──────────────────────────────────────────────

    def get_status(self) -> dict:
        """Trả về trạng thái models cho /health endpoint."""
        return {
            "whisper": "ready" if self.whisper_model else "not_loaded",
            "nllb": "ready" if self.nllb_model else "not_loaded",
            "vits": "ready" if (self.tts_model_eng and self.tts_model_vie) else "not_loaded",
            "deepfilter": (
                "ready" if self.deepfilter_model
                else "disabled" if self._loaded
                else "not_loaded"
            ),
        }

    def get_runtime_status(self) -> dict:
        from app.core.config import settings as _s
        from app.services.translation_service import TRANSLATION_POLICY_VERSION
        nllb_id = getattr(self, "_nllb_model_id", "not_loaded")
        if nllb_id == "not_loaded":
            nllb_id = getattr(_s, "NLLB_MODEL", "facebook/nllb-200-distilled-1.3B")

        tts_eng = getattr(self, "_tts_model_eng", "not_loaded")
        if tts_eng == "not_loaded":
            tts_eng = getattr(_s, "TTS_MODEL_ENG", "facebook/mms-tts-eng")

        tts_vie = getattr(self, "_tts_model_vie", "not_loaded")
        if tts_vie == "not_loaded":
            tts_vie = getattr(_s, "TTS_MODEL_VIE", "facebook/mms-tts-vie")

        df_id = getattr(self, "_deepfilter_model_id", "none")
        if df_id == "none" and self.deepfilter_model:
            df_id = "DeepFilterNet3"

        whisper_id = self._whisper_model_id
        if whisper_id == "not_loaded":
            whisper_id = getattr(_s, "WHISPER_TORCH_MODEL", None) or getattr(_s, "WHISPER_MODEL", "openai/whisper-large-v3-turbo")

        return {
            "device": self._device,
            "whisper_device": self._whisper_device,
            "whisper_backend": self._whisper_backend,
            "whisper_model_id": whisper_id,
            "whisper_compute_type": self._whisper_compute_type,
            "whisper_cpu_fallback": self._whisper_fallback,
            "nllb_model_id": nllb_id,
            "nllb_revision": getattr(_s, "NLLB_REVISION", None),
            "nllb_device": self._device,
            "nllb_dtype": "float16" if self._device == "cuda" else "float32",
            "translation_policy": TRANSLATION_POLICY_VERSION,
            "translation_beam_size": _s.TRANSLATION_BEAM_SIZE,
            "translation_fidelity_rerank": getattr(_s, "TRANSLATION_FIDELITY_RERANK", True),
            "translation_length_penalty": getattr(_s, "TRANSLATION_LENGTH_PENALTY", 1.2),
            "tts_model_eng": tts_eng,
            "tts_model_vie": tts_vie,
            "tts_device": self._tts_device,
            "tts_dtype": self._tts_dtype,
            "deepfilter_model_id": df_id,
            "deepfilter_enabled": self.deepfilter_model is not None or getattr(_s, "ENABLE_DEEPFILTER", False),
            "denoise_device": self._denoise_device,
            "model_load_seconds": round(self._load_seconds, 3),
        }

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Singleton instance — populated by FastAPI startup.
model_manager = ModelManager()

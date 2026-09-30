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
        print("  T-LANGUA MODEL MANAGER")
        print("=" * 56)
        print(f"  Device : {self._device}")
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
        print(f"  Loading NLLB ({s.NLLB_MODEL}) ...", end=" ", flush=True)
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import os

        self.nllb_tokenizer = AutoTokenizer.from_pretrained(s.NLLB_MODEL)

        use_int8 = os.getenv("NLLB_INT8", "0") == "1"
        if use_int8:
            self.nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
                s.NLLB_MODEL, load_in_8bit=True, device_map="auto"
            )
        else:
            torch_dtype = torch.float16 if self._device == "cuda" else None
            self.nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
                s.NLLB_MODEL, torch_dtype=torch_dtype
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

        self.tts_model_eng = VitsModel.from_pretrained(s.TTS_MODEL_ENG).to(self._device).eval()
        self.tts_tokenizer_eng = VitsTokenizer.from_pretrained(s.TTS_MODEL_ENG)
        self.tts_model_vie = VitsModel.from_pretrained(s.TTS_MODEL_VIE).to(self._device).eval()
        self.tts_tokenizer_vie = VitsTokenizer.from_pretrained(s.TTS_MODEL_VIE)
        print(f"OK ({time.time() - t0:.1f}s)")

        # --- DeepFilterNet (optional) ---
        if s.ENABLE_DEEPFILTER:
            t0 = time.time()
            print("  Loading DeepFilterNet ...", end=" ", flush=True)
            try:
                from app.core.compat import apply_torch_patches
                apply_torch_patches()
                from df.enhance import init_df
                # The pretrained cache may be readable but not writable (for
                # example inside a sandbox or a shared model volume). DeepFilter
                # only needs the checkpoint; its default enhance.log is optional.
                self.deepfilter_model, self.deepfilter_state, _ = init_df(log_file=None)
                print(f"OK ({time.time() - t0:.1f}s)")
            except Exception as e:
                print(f"SKIP ({e})")
                self.deepfilter_model = None
                self.deepfilter_state = None
        else:
            print("  DeepFilterNet : DISABLED")

        if self._device == "cuda" and getattr(s, "PREWARM_MODELS", True):
            t0 = time.perf_counter()
            print("  Prewarming speech models ...", end=" ", flush=True)
            try:
                import numpy as np
                from app.ai.torch_whisper_adapter import TorchWhisperModel

                if isinstance(self.whisper_model, TorchWhisperModel):
                    self.whisper_model.transcribe(
                        np.zeros(16000, dtype=np.float32), language="vi", beam_size=1)
                if self.deepfilter_model is not None and self.deepfilter_state is not None:
                    from df.enhance import enhance
                    with torch.inference_mode():
                        enhance(self.deepfilter_model, self.deepfilter_state,
                                torch.zeros(1, 48000),
                                atten_lim_db=getattr(s, "DENOISE_ATTENUATION_DB", 12.0))
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
        return {"device": self._device, "whisper_device": self._whisper_device,
                "whisper_backend": self._whisper_backend,
                "whisper_model_id": self._whisper_model_id,
                "whisper_compute_type": self._whisper_compute_type,
                "whisper_cpu_fallback": self._whisper_fallback,
                "model_load_seconds": round(self._load_seconds, 3)}

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Singleton instance — populated by FastAPI startup.
model_manager = ModelManager()

"""
Whisper STT service.
Model được load bởi ModelManager, service chỉ xử lý inference.
"""
import time
import re
import os
import threading
import wave
from functools import wraps
import torch
from typing import Optional, Dict, Any, TypedDict


class TranscribeResult(TypedDict):
    text: str
    language: str
    latency: float



# Prompt mồi đơn giản để hướng dẫn Whisper sử dụng dấu câu và ngôn ngữ,
# Tránh liệt kê các câu cụ thể vì Whisper sẽ "ảo giác" lặp lại các câu đó khi có tiếng ồn.
INITIAL_PROMPT = "Đây là văn bản tiếng Việt có dấu câu."

# Prompt mồi cho tiếng Anh
INITIAL_PROMPT_EN = "This is an English text with punctuation."

# Prompt conditioning can dominate very short clips.  In practice this makes
# Whisper turn one or two Vietnamese words into memorised phrases (for example
# a YouTube outro).  Short clips already receive an explicit language token,
# so only a user glossary is useful for them.
SHORT_UTTERANCE_PROMPT_LIMIT_SECONDS = 2.5

USE_SILERO_VAD = os.getenv("USE_SILERO_VAD", "0") == "1"
_silero_model: Any = None
_silero_utils: Any = None


def _load_silero_vad():
    global _silero_model, _silero_utils
    if _silero_model is not None:
        return _silero_model, _silero_utils

    try:
        res: Any = torch.hub.load(
            "snakers4/silero-vad",
            "silero_vad",
            force_reload=False
        )
        _silero_model, _silero_utils = res
    except Exception:
        _silero_model, _silero_utils = None, None
    return _silero_model, _silero_utils


import numpy as np

_inference_lock = threading.RLock()


def _serialized_inference(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        with _inference_lock:
            return fn(*args, **kwargs)
    return run


def should_process_audio(audio_np) -> bool:
    if audio_np is None or len(audio_np) == 0:
        return False
    # Energy floor check: avoid processing dead silence or faint background hum
    rms = float(np.sqrt(np.mean(np.square(audio_np))))
    if rms < 0.002:
        return False

    if not USE_SILERO_VAD:
        return True

    model, utils = _load_silero_vad()
    if model is None or utils is None:
        return True

    try:
        get_speech_timestamps = utils[0]
        audio_tensor = torch.from_numpy(audio_np).float()
        with torch.inference_mode():
            timestamps = get_speech_timestamps(
                audio_tensor,
                model,
                sampling_rate=16000
            )
        return len(timestamps) > 0
    except Exception:
        return True

# Các mẫu hallucination phổ biến của Whisper khi không có giọng nói rõ.
_HALLUCINATION_PATTERNS = re.compile(
    r"(?i)"
    r"(Cảm ơn (các bạn )?đã (theo dõi|xem|lắng nghe))"
    r"|(Đăng ký kênh)"
    r"|(Subscribe)"
    r"|(Thank you for watching)"
    r"|(Nhớ like và subscribe)"
    r"|(\b(\w+\s+)\2{2,})"
)


def _is_hallucination(text: str) -> bool:
    """Phát hiện các đoạn text do Whisper tự bịa ra (hallucination)."""
    if not text:
        return True
    stripped = text.strip(" .!?,")
    if len(stripped) < 1:
        return True
    if _HALLUCINATION_PATTERNS.search(stripped):
        return True
        
    # Tránh ảo giác chính các prompt mồi
    prompt_vi_stripped = INITIAL_PROMPT.strip(" .!?,")
    prompt_en_stripped = INITIAL_PROMPT_EN.strip(" .!?,")
    if stripped == prompt_vi_stripped or stripped == prompt_en_stripped:
        return True
        
    return False


def clean_stt_text(text: str) -> str:
    if not text:
        return text

    # Normalize whitespace first.
    text = re.sub(r"\s+", " ", text)

    # Collapse repeated punctuation.
    text = re.sub(r"([,.!?])\1+", r"\1", text)

    # Normalize spacing around punctuation, except decimal commas between digits (e.g. 1,5).
    text = re.sub(r"(?<!\d)\s*,\s*|\s*,\s*(?!\d)", ", ", text)
    text = re.sub(r"\s*([.!?])\s*", r"\1 ", text)
    return text.strip()


def _get_whisper_model():
    """Lấy Whisper model từ ModelManager singleton."""
    from app.ai.model_manager import model_manager
    if model_manager.whisper_model is None:
        raise RuntimeError("Whisper model chưa được load. Gọi ModelManager.load_all() trước.")
    return model_manager.whisper_model


@_serialized_inference
def transcribe_audio(
    audio: Any,
    beam_size: int = 1,
    temperature: float = 0.0,
    condition_on_previous_text: bool = False,
    use_vad: bool = True,
    context_prompt: str = "",
    vad_parameters: Optional[Dict] = None,
    language: str = "vi",
    preprocess: bool = False,
) -> TranscribeResult:
    start = time.time()

    if vad_parameters is None:
        vad_parameters = {
            "min_silence_duration_ms": 300,
            "speech_pad_ms": 80
        }

    lang_code = {"vi": "vi", "en": "en", "vie_Latn": "vi", "eng_Latn": "en"}.get(language, "vi")

    # HTTP supplies a WAV path; realtime supplies normalized PCM samples.
    if isinstance(audio, (str, os.PathLike)):
        with wave.open(os.fspath(audio), "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype()) != (1, 2, 16000, "NONE"):
                raise ValueError("Expected mono PCM16 WAV at 16 kHz")
            audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    if audio is None or len(audio) < 1600:
        return {"text": "", "language": lang_code, "latency": 0.0}
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 1:
        raise ValueError("Expected mono audio samples")
    if not np.isfinite(audio).all():
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
    if preprocess:
        from app.utils.audio_utils import preprocess_audio_numpy
        from app.services.deepfilter_service import denoise_numpy
        from app.core.config import settings
        audio = denoise_numpy(preprocess_audio_numpy(audio),
                              atten_lim_db=settings.DENOISE_ATTENUATION_DB,
                              min_duration_seconds=getattr(settings, "DENOISE_MIN_AUDIO_SECONDS", 3.0))
    if not should_process_audio(audio):
        return {"text": "", "language": lang_code, "latency": 0.0}
    model = _get_whisper_model()

    # A generic prompt is useful for punctuation in longer speech, but on a
    # one or two-word clip it can outweigh the acoustic signal.  Keep glossary
    # hints because they contain vocabulary chosen by the current user.
    duration_seconds = len(audio) / 16000
    base_prompt = INITIAL_PROMPT if lang_code == "vi" else INITIAL_PROMPT_EN
    if duration_seconds <= SHORT_UTTERANCE_PROMPT_LIMIT_SECONDS:
        combined_prompt = context_prompt
    elif context_prompt:
        combined_prompt = f"{base_prompt} {context_prompt}"
    else:
        combined_prompt = base_prompt

    # Giới hạn độ dài prompt để tránh làm chậm model (max ~400 ký tự).
    if len(combined_prompt) > 400:
        combined_prompt = combined_prompt[-400:]

    # Transcribe với các tham số tối ưu cho độ chính xác và giảm ảo giác
    try:
        with torch.inference_mode():
            segments_gen, info = model.transcribe(
                audio,
                language=lang_code,
                beam_size=beam_size,
                best_of=1,
                temperature=temperature,
                condition_on_previous_text=condition_on_previous_text,
                vad_filter=use_vad,
                vad_parameters=vad_parameters if use_vad else None,
                initial_prompt=combined_prompt,
                without_timestamps=True,
                # Chống hallucination: phạt lặp từ
                repetition_penalty=1.15,
                # Ngưỡng lọc segment rác dựa trên compression ratio
                compression_ratio_threshold=2.4,
                # Ngưỡng lọc segment có xác suất thấp (log probability)
                log_prob_threshold=-1.0,
                # Ngưỡng xác suất "không có giọng nói"
                no_speech_threshold=0.5,
            )
            filtered_texts = []
            for seg in segments_gen:
                seg_no_speech = getattr(seg, "no_speech_prob", 0.0)
                if seg_no_speech > 0.5:
                    continue
                seg_text = seg.text.strip()
                if _is_hallucination(seg_text):
                    continue
                filtered_texts.append(seg_text)
    except Exception as e:
        if not use_vad:
            raise
        import logging
        logging.getLogger(__name__).warning("transcribe_audio retry without vad error_type=%s", type(e).__name__)
        # Fallback without vad_filter if internal VAD fails
        with torch.inference_mode():
            segments_gen, info = model.transcribe(
                audio,
                language=lang_code,
                beam_size=beam_size,
                best_of=1,
                temperature=temperature,
                condition_on_previous_text=condition_on_previous_text,
                vad_filter=False,
                initial_prompt=combined_prompt,
                without_timestamps=True,
                repetition_penalty=1.15,
            )
            filtered_texts = [seg.text.strip() for seg in segments_gen if not _is_hallucination(seg.text.strip())]

    text = " ".join(filtered_texts).strip()

    # Làm sạch rác dấu câu từ STT trước khi áp dụng luật domain.
    text = clean_stt_text(text)

    latency = round(time.time() - start, 2)

    return {
        "text": text,
        "language": info.language,
        "latency": latency
    }

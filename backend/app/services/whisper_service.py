import time
import re
import os
import torch
from typing import Optional, Dict
from faster_whisper import WhisperModel
from app.core.config import (
    WHISPER_MODEL,
    DEVICE,
    CPU_THREADS,
    WHISPER_COMPUTE_TYPE
)

# Tải model 1 lần duy nhất khi khởi động Backend
print(f"Đang tải mô hình Whisper: {WHISPER_MODEL}...")
model = WhisperModel(
    WHISPER_MODEL,
    device=DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE,
    cpu_threads=CPU_THREADS
)
print("Đã tải xong Whisper")

# Prompt mồi đơn giản để hướng dẫn Whisper sử dụng dấu câu và ngôn ngữ,
# Tránh liệt kê các câu cụ thể vì Whisper sẽ "ảo giác" lặp lại các câu đó khi có tiếng ồn.
INITIAL_PROMPT = "Đây là văn bản tiếng Việt có dấu câu."

# [NEW] Prompt mồi cho tiếng Anh
INITIAL_PROMPT_EN = "This is an English text with punctuation."

USE_SILERO_VAD = os.getenv("USE_SILERO_VAD", "0") == "1"
_silero_model = None
_silero_utils = None


def _load_silero_vad():
    global _silero_model, _silero_utils
    if _silero_model is not None:
        return _silero_model, _silero_utils

    try:
        _silero_model, _silero_utils = torch.hub.load(
            "snakers4/silero-vad",
            "silero_vad",
            force_reload=False
        )
    except Exception:
        _silero_model, _silero_utils = None, None
    return _silero_model, _silero_utils


def should_process_audio(audio_np) -> bool:
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
    r"|(Hẹn gặp lại)"
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
        
    # [NEW] Tránh ảo giác chính các prompt mồi
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

    # Remove commas between words/numbers caused by STT artifacts.
    text = re.sub(
        r"(?i)\b([0-9a-zA-ZÀ-ỹ]+)\s*,\s*([0-9a-zA-ZÀ-ỹ]+)\b",
        r"\1 \2",
        text
    )

    # Collapse repeated punctuation.
    text = re.sub(r"([,.!?])\1+", r"\1", text)

    # Normalize spacing around punctuation.
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*([.!?])\s*", r"\1 ", text)
    return text.strip()

def transcribe_audio(
    audio_np,
    beam_size: int,
    temperature: float,
    condition_on_previous_text: bool = False,
    use_vad: bool = True,
    context_prompt: str = "",
    vad_parameters: Optional[Dict] = None,
    language: str = "vi"  # [NEW] Nhận ngôn ngữ từ session thay vì hardcode
):
    start = time.time()

    if vad_parameters is None:
        vad_parameters = {
            "min_silence_duration_ms": 300,
            "speech_pad_ms": 80
        }

    # [NEW] Chọn prompt theo ngôn ngữ
    base_prompt = INITIAL_PROMPT if language == "vi" else INITIAL_PROMPT_EN

    # Luôn kết hợp base_prompt (từ vựng gợi ý) + context gần nhất.
    if context_prompt:
        combined_prompt = f"{base_prompt} {context_prompt}"
    else:
        combined_prompt = base_prompt

    # Giới hạn độ dài prompt để tránh làm chậm model (max ~400 ký tự).
    if len(combined_prompt) > 400:
        combined_prompt = combined_prompt[-400:]

    # Transcribe với các tham số tối ưu cho độ chính xác và giảm ảo giác
    with torch.inference_mode():
        segments_gen, info = model.transcribe(
            audio_np,
            language=language,  # [NEW] Dùng ngôn ngữ từ session
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

    # Lọc từng segment: bỏ segment có no_speech_prob cao hoặc là hallucination.
    filtered_texts = []
    for seg in segments_gen:
        seg_no_speech = getattr(seg, "no_speech_prob", 0.0)
        if seg_no_speech > 0.5:
            continue
        seg_text = seg.text.strip()
        if _is_hallucination(seg_text):
            print(f"[WHISPER] Bỏ ảo giác: \"{seg_text}\"")
            continue
        filtered_texts.append(seg_text)

    text = " ".join(filtered_texts).strip()

    # Làm sạch rác dấu câu từ STT trước khi áp dụng luật domain.
    text = clean_stt_text(text)

    latency = round(time.time() - start, 2)

    return {
        "text": text,
        "language": info.language,
        "latency": latency
    }
"""
VITS TTS service.
Model được load bởi ModelManager, service chỉ xử lý inference.
"""
import io
import os
import time
import uuid
import threading

import torch
import scipy.io.wavfile
from typing import Tuple, Any

from app.core.config import OUTPUT_DIR, DEVICE

_inference_lock = threading.RLock()


def _get_tts_model(target_lang: str) -> Tuple[Any, Any]:
    """Lấy VITS model + tokenizer phù hợp với ngôn ngữ từ ModelManager."""
    from app.ai.model_manager import model_manager
    if target_lang == "vie_Latn":
        model = model_manager.tts_model_vie
        tokenizer = model_manager.tts_tokenizer_vie
    else:
        model = model_manager.tts_model_eng
        tokenizer = model_manager.tts_tokenizer_eng

    if model is None or tokenizer is None:
        raise RuntimeError("TTS model hoặc tokenizer chưa được load. Gọi ModelManager.load_all() trước.")
    return model, tokenizer


def generate_speech_bytes(text: str, target_lang: str = "eng_Latn") -> bytes:
    """
    Tạo WAV audio bytes trên RAM (không ghi file).
    Trả về: bytes của file WAV hoàn chỉnh (có header).
    """
    if not text or not text.strip():
        return b""

    with _inference_lock:
        model, tokenizer = _get_tts_model(target_lang)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            output = model(**inputs, speaking_rate=0.85, noise_scale=0.667, noise_scale_dp=0.8).waveform
        audio_data = output.cpu().numpy().squeeze()

    # Ghi vào bộ đệm RAM thay vì file
    buf = io.BytesIO()
    scipy.io.wavfile.write(buf, model.config.sampling_rate, audio_data)
    return buf.getvalue()


def generate_speech(text, output_path, target_lang="eng_Latn"):
    if not text:
        return {"latency": 0.0}

    start_time = time.time()

    wav_bytes = generate_speech_bytes(text, target_lang)
    with open(output_path, "wb") as destination:
        destination.write(wav_bytes)

    latency = round(time.time() - start_time, 2)

    return {
        "latency": latency
    }


def synthesize_audio(text: str, target_lang: str = "eng_Latn") -> str:
    """Generate TTS audio and return the output filename."""
    filename = f"{uuid.uuid4()}.wav"
    output_path = os.path.join(OUTPUT_DIR, filename)
    generate_speech(text, output_path, target_lang=target_lang)
    return filename


def delete_audio_file(filename: str) -> None:
    """Best-effort cleanup for synthesized audio files."""
    if not filename:
        return

    file_path = os.path.join(OUTPUT_DIR, filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        return
    except Exception:
        # Avoid raising cleanup errors in the main pipeline.
        return

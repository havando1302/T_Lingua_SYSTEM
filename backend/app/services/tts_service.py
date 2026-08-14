import os
import time
import uuid

import torch
import scipy.io.wavfile
from transformers import VitsModel, AutoTokenizer

from app.core.config import (
    OUTPUT_DIR,
    DEVICE,
    TTS_MODEL_ENG,
    TTS_MODEL_VIE
)

print("Đang tải mô hình MMS VITS tiếng Anh...")
model_eng = VitsModel.from_pretrained(TTS_MODEL_ENG).to(DEVICE)
tokenizer_eng = AutoTokenizer.from_pretrained(TTS_MODEL_ENG)
print("Đã tải xong MMS VITS tiếng Anh")

print("Đang tải mô hình MMS VITS tiếng Việt...")
model_vie = VitsModel.from_pretrained(TTS_MODEL_VIE).to(DEVICE)
tokenizer_vie = AutoTokenizer.from_pretrained(TTS_MODEL_VIE)
print("Đã tải xong MMS VITS tiếng Việt")

def generate_speech(text, output_path, target_lang="eng_Latn"):
    if not text:
        return {"latency": 0.0}

    start_time = time.time()

    if target_lang == "vie_Latn":
        model = model_vie
        tokenizer = tokenizer_vie
    else:
        model = model_eng
        tokenizer = tokenizer_eng

    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        output = model(
            **inputs,
            speaking_rate=0.85,
            noise_scale=0.667,
            noise_scale_dp=0.8
        ).waveform

    audio_data = output.cpu().numpy().squeeze()
    scipy.io.wavfile.write(output_path, model.config.sampling_rate, audio_data)

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
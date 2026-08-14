import uuid
import time

from app.services.whisper_service import transcribe_audio
from app.services.translation_service import translate_text
from app.services.tts_service import generate_speech
from app.core.config import TARGET_LANG



def run_pipeline(audio_path: str):

    total_start = time.time()

    # STEP 1 - STT
    stt_result = transcribe_audio(audio_path)

    original_text = stt_result["text"]

    # STEP 2 - TRANSLATION
    translation_result = translate_text(original_text)

    translated_text = translation_result["translated_text"]

    # STEP 3 - TTS
    output_name = f"{uuid.uuid4()}.wav"
    output_path = f"outputs/{output_name}"

    tts_result = generate_speech(
        translated_text,
        output_path,
        target_lang=TARGET_LANG
    )

    total_end = time.time()

    return {
        "original_text": original_text,
        "translated_text": translated_text,
        "audio_url": f"/audio/{output_name}",
        "metrics": {
            "whisper_latency": stt_result["latency"],
            "translation_latency": translation_result["latency"],
            "tts_latency": tts_result["latency"],
            "total_latency": round(total_end - total_start, 2)
        }
    }
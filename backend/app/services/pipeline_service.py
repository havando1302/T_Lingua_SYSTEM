import uuid
import time

from app.services.whisper_service import transcribe_audio
from app.services.translation_service import translate_text
from app.services.tts_service import generate_speech
from app.core.config import TARGET_LANG, settings
from app.services.audio_storage import audio_path as private_audio_path
from app.core.inference_errors import NoSpeechDetected
from app.core.telemetry import GLOBAL_TELEMETRY



def run_pipeline(audio_path: str, *, client_id: str, output_path: str | None = None,
                 source_lang: str = "vi", target_lang: str = TARGET_LANG, use_cache: bool = True):
    metric_id = uuid.uuid4().hex
    GLOBAL_TELEMETRY.start_turn(metric_id, client_id, source_lang=source_lang, target_lang=target_lang)
    try:
        result = _run_pipeline(audio_path, client_id=client_id, output_path=output_path,
                               source_lang=source_lang, target_lang=target_lang, use_cache=use_cache, metric_id=metric_id)
        GLOBAL_TELEMETRY.complete_turn(metric_id)
        return result
    except Exception as error:
        GLOBAL_TELEMETRY.discard_turn(metric_id, error=type(error).__name__)
        raise


def _run_pipeline(audio_path: str, *, client_id: str, output_path: str | None,
                  source_lang: str, target_lang: str, use_cache: bool, metric_id: str):

    total_start = time.time()

    # STEP 1 - STT
    GLOBAL_TELEMETRY.record_stage(metric_id, "stt_start")
    stt_result = transcribe_audio(audio_path, beam_size=settings.WHISPER_BEAM_SIZE, preprocess=True,
                                  language={"vie_Latn": "vi", "eng_Latn": "en"}.get(source_lang, source_lang))
    GLOBAL_TELEMETRY.record_stage(metric_id, "stt_done")

    original_text: str = str(stt_result.get("text") or "")
    if not original_text.strip():
        raise NoSpeechDetected("No intelligible speech was detected")

    # STEP 2 - TRANSLATION
    GLOBAL_TELEMETRY.record_stage(metric_id, "translate_start")
    translation_result = translate_text(original_text, client_id=client_id,
                                        source_lang=source_lang, target_lang=target_lang, use_cache=use_cache)
    GLOBAL_TELEMETRY.record_stage(metric_id, "translate_done")

    translated_text: str = str(translation_result.get("translated_text") or "")
    if not translated_text.strip():
        raise RuntimeError("Translation returned no text")

    # STEP 3 - TTS
    output_name = f"{uuid.uuid4().hex}.wav"
    output_path = output_path or str(private_audio_path(output_name))

    GLOBAL_TELEMETRY.record_stage(metric_id, "tts_start")
    tts_result = generate_speech(
        translated_text,
        output_path,
        target_lang=target_lang
    )
    GLOBAL_TELEMETRY.record_stage(metric_id, "tts_done")

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

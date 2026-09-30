"""
Inference Adapters (Phase 7 Clean Architecture - Adapter Pattern)
Bọc các dịch vụ AI thực tế (Whisper, NLLB, VITS, DeepFilter) và cung cấp Mock Adapters cho kiểm thử độc lập.
"""
from typing import Optional, Dict, Any
import numpy as np

from .interfaces import ISTTAdapter, ITranslationAdapter, ITTSAdapter, IDenoiseAdapter


class WhisperSTTAdapter(ISTTAdapter):
    def transcribe(
        self,
        audio_data: np.ndarray,
        language: str = "vi",
        context_prompt: Optional[str] = None,
        beam_size: int = 1,
    ) -> Dict[str, Any]:
        from app.services.whisper_service import transcribe_audio
        return dict(transcribe_audio(
            audio_data,
            beam_size=beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            use_vad=True,
            context_prompt=context_prompt or "",
            language=language,
        ))


class NLLBTranslationAdapter(ITranslationAdapter):
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from app.services.translation_service import translate_text
        return translate_text(
            text,
            "",
            source_lang=source_lang,
            target_lang=target_lang,
            client_id=client_id,
            # TranslateTurnUseCase owns the injected cache and its runtime setting.
            use_cache=False,
        )


class VitsTTSAdapter(ITTSAdapter):
    def synthesize(
        self,
        text: str,
        language: str,
    ) -> bytes:
        from app.services.tts_service import generate_speech_bytes
        return generate_speech_bytes(text, language) or b""


class DeepFilterDenoiseAdapter(IDenoiseAdapter):
    def denoise(self, audio_data: np.ndarray) -> np.ndarray:
        from app.core.config import settings
        from app.services.deepfilter_service import denoise_numpy
        return denoise_numpy(
            audio_data,
            atten_lim_db=settings.DENOISE_ATTENUATION_DB,
            min_duration_seconds=getattr(settings, "DENOISE_MIN_AUDIO_SECONDS", 3.0),
        )


# ── MOCK ADAPTERS (Dành riêng cho kiểm thử độc lập & Dependency Injection) ───

class MockSTTAdapter(ISTTAdapter):
    def __init__(self, predefined_text: str = "Xin chào tôi là trợ lý ảo"):
        self.predefined_text = predefined_text

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: str = "vi",
        context_prompt: Optional[str] = None,
        beam_size: int = 1,
    ) -> Dict[str, Any]:
        return {
            "text": self.predefined_text,
            "language": language,
            "latency": 0.05,
        }


class MockTranslationAdapter(ITranslationAdapter):
    def __init__(self, mock_map: Optional[Dict[str, str]] = None):
        self.mock_map = mock_map or {
            "xin chào": "hello",
            "cảm ơn": "thank you",
            "tôi yêu bạn": "i love you",
        }

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean = text.strip().lower()
        translated = self.mock_map.get(clean, f"translated_{text}")
        return {
            "translated_text": translated,
            "latency": 0.02,
            "source": "mock_nllb",
        }


class MockTTSAdapter(ITTSAdapter):
    def synthesize(
        self,
        text: str,
        language: str,
    ) -> bytes:
        # Trả về 100ms synthetic mono WAV bytes
        import wave, io
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00" * 3200)
        return buffer.getvalue()

"""
Application Use Cases (Phase 7 Clean Architecture)
Điều phối các luồng nghiệp vụ giữa Domain, Persistence và Inference.
Sử dụng Dependency Injection để hoàn toàn độc lập với phần cứng thực tế.
"""
from typing import Optional, Dict, Any, List
import numpy as np

from app.domain.entities import DomainTurn, TurnStatus, LanguagePair
from app.inference.interfaces import ISTTAdapter, ITranslationAdapter, ITTSAdapter
from app.services.translation_memory import ITranslationMemoryRepository, get_tm_repository
from app.services.translation_cache import TranslationMemoryCache, GLOBAL_TRANSLATION_CACHE
from app.core.telemetry import PipelineTelemetryTracker, GLOBAL_TELEMETRY


class TranslateTurnUseCase:
    """
    Use case điều phối trọn gói quá trình xử lý một lượt nói (Turn):
    Audio -> STT -> Translation Memory/NLLB -> TTS chunks.
    """
    def __init__(
        self,
        stt_adapter: ISTTAdapter,
        translation_adapter: ITranslationAdapter,
        tts_adapter: ITTSAdapter,
        tm_repo: Optional[ITranslationMemoryRepository] = None,
        cache: Optional[TranslationMemoryCache] = None,
        telemetry: Optional[PipelineTelemetryTracker] = None,
        use_cache: bool = True,
    ):
        self._stt = stt_adapter
        self._translator = translation_adapter
        self._tts = tts_adapter
        self._tm = tm_repo or get_tm_repository()
        self._cache = cache or GLOBAL_TRANSLATION_CACHE
        self._telemetry = telemetry or GLOBAL_TELEMETRY
        self._use_cache = use_cache

    def process_turn(
        self,
        turn: DomainTurn,
        audio_np: np.ndarray,
        client_id: str = "default",
    ) -> Dict[str, Any]:
        if not turn.is_active():
            return {"status": turn.status.value, "error": "Turn is not active"}

        # 1. STT Phase
        turn.mark_status(TurnStatus.PROCESSING_STT)
        self._telemetry.record_stage(turn.turn_id, "stt_start")

        stt_res = self._stt.transcribe(
            audio_np,
            language=turn.lang_pair.source_lang,
        )
        source_text = stt_res.get("text", "").strip()
        turn.source_text = source_text
        self._telemetry.record_stage(turn.turn_id, "stt_done")

        if not source_text or not turn.is_active():
            turn.mark_status(TurnStatus.COMPLETED)
            return {"turn_id": turn.turn_id, "source_text": "", "translated_text": "", "audio_chunks": []}

        # 2. Translation Phase (Cache -> TM -> Model)
        turn.mark_status(TurnStatus.PROCESSING_TRANSLATION)
        self._telemetry.record_stage(turn.turn_id, "translate_start")

        # Tra cứu cache
        snapshot = self._cache.get_version_snapshot(client_id) if self._use_cache else None
        cached = self._cache.get(client_id, turn.lang_pair.source_lang, turn.lang_pair.target_lang, source_text) if self._use_cache else None
        if cached is not None:
            translated_text = cached
            trans_source = "cache"
        else:
            # Tra cứu TM
            tm_hit = self._tm.lookup(source_text, client_id=client_id, source_lang=turn.lang_pair.source_lang, target_lang=turn.lang_pair.target_lang)
            if tm_hit is None:
                tm_hit = self._tm.lookup(source_text, client_id="global:approved", source_lang=turn.lang_pair.source_lang, target_lang=turn.lang_pair.target_lang)
            if tm_hit is not None:
                translated_text = tm_hit
                trans_source = "translation_memory"
            else:
                trans_res = self._translator.translate(
                    source_text,
                    source_lang=turn.lang_pair.nllb_source,
                    target_lang=turn.lang_pair.nllb_target,
                    client_id=client_id,
                )
                translated_text = trans_res.get("translated_text", "")
                trans_source = trans_res.get("source", "nllb")

            if translated_text and self._use_cache:
                self._cache.put(client_id, turn.lang_pair.source_lang, turn.lang_pair.target_lang, source_text, translated_text, expected_version=snapshot)

        turn.translated_text = translated_text
        self._telemetry.record_stage(turn.turn_id, "translate_done")

        if not turn.is_active():
            return {"turn_id": turn.turn_id, "source_text": source_text, "translated_text": translated_text, "audio_chunks": []}

        # 3. TTS Phase
        turn.mark_status(TurnStatus.PROCESSING_TTS)
        self._telemetry.record_stage(turn.turn_id, "tts_start")
        audio_bytes = self._tts.synthesize(translated_text, language=turn.lang_pair.nllb_target)
        self._telemetry.record_stage(turn.turn_id, "tts_chunk_0")
        self._telemetry.record_stage(turn.turn_id, "tts_done")
        self._telemetry.complete_turn(turn.turn_id)

        turn.mark_status(TurnStatus.COMPLETED)

        return {
            "turn_id": turn.turn_id,
            "status": turn.status.value,
            "source_text": source_text,
            "translated_text": translated_text,
            "translation_source": trans_source,
            "audio_bytes_length": len(audio_bytes),
        }

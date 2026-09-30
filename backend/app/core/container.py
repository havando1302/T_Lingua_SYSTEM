"""
Dependency Injection Container (Phase 7 Clean Architecture)
Cung cấp Service Locator / Factory tập trung cho toàn bộ ứng dụng.
Cho phép ghi đè (override) bất kỳ adapter nào bằng mock object trong môi trường kiểm thử.
"""
from typing import Optional

from app.inference.interfaces import ISTTAdapter, ITranslationAdapter, ITTSAdapter, IDenoiseAdapter
from app.inference.adapters import (
    WhisperSTTAdapter,
    NLLBTranslationAdapter,
    VitsTTSAdapter,
    DeepFilterDenoiseAdapter,
)
from app.application.use_cases import TranslateTurnUseCase
from app.services.translation_memory import ITranslationMemoryRepository, get_tm_repository
from app.services.translation_cache import TranslationMemoryCache, GLOBAL_TRANSLATION_CACHE
from app.core.telemetry import PipelineTelemetryTracker, GLOBAL_TELEMETRY


class ServiceContainer:
    def __init__(self):
        self._stt_adapter: Optional[ISTTAdapter] = None
        self._translation_adapter: Optional[ITranslationAdapter] = None
        self._tts_adapter: Optional[ITTSAdapter] = None
        self._denoise_adapter: Optional[IDenoiseAdapter] = None
        self._tm_repository: Optional[ITranslationMemoryRepository] = None
        self._translation_cache: Optional[TranslationMemoryCache] = None
        self._telemetry_tracker: Optional[PipelineTelemetryTracker] = None

    def get_stt_adapter(self) -> ISTTAdapter:
        if self._stt_adapter is None:
            self._stt_adapter = WhisperSTTAdapter()
        return self._stt_adapter

    def set_stt_adapter(self, adapter: ISTTAdapter) -> None:
        self._stt_adapter = adapter

    def get_translation_adapter(self) -> ITranslationAdapter:
        if self._translation_adapter is None:
            self._translation_adapter = NLLBTranslationAdapter()
        return self._translation_adapter

    def set_translation_adapter(self, adapter: ITranslationAdapter) -> None:
        self._translation_adapter = adapter

    def get_tts_adapter(self) -> ITTSAdapter:
        if self._tts_adapter is None:
            self._tts_adapter = VitsTTSAdapter()
        return self._tts_adapter

    def set_tts_adapter(self, adapter: ITTSAdapter) -> None:
        self._tts_adapter = adapter

    def get_denoise_adapter(self) -> IDenoiseAdapter:
        if self._denoise_adapter is None:
            self._denoise_adapter = DeepFilterDenoiseAdapter()
        return self._denoise_adapter

    def set_denoise_adapter(self, adapter: IDenoiseAdapter) -> None:
        self._denoise_adapter = adapter

    def get_tm_repository(self) -> ITranslationMemoryRepository:
        if self._tm_repository is None:
            self._tm_repository = get_tm_repository()
        return self._tm_repository

    def set_tm_repository(self, repo: ITranslationMemoryRepository) -> None:
        self._tm_repository = repo

    def get_translation_cache(self) -> TranslationMemoryCache:
        if self._translation_cache is None:
            self._translation_cache = GLOBAL_TRANSLATION_CACHE
        return self._translation_cache

    def get_telemetry_tracker(self) -> PipelineTelemetryTracker:
        if self._telemetry_tracker is None:
            self._telemetry_tracker = GLOBAL_TELEMETRY
        return self._telemetry_tracker

    def get_translate_use_case(self) -> TranslateTurnUseCase:
        return TranslateTurnUseCase(
            stt_adapter=self.get_stt_adapter(),
            translation_adapter=self.get_translation_adapter(),
            tts_adapter=self.get_tts_adapter(),
            tm_repo=self.get_tm_repository(),
            cache=self.get_translation_cache(),
            telemetry=self.get_telemetry_tracker(),
        )

    def reset_overrides(self) -> None:
        self._stt_adapter = None
        self._translation_adapter = None
        self._tts_adapter = None
        self._denoise_adapter = None
        self._tm_repository = None
        self._translation_cache = None
        self._telemetry_tracker = None


CONTAINER = ServiceContainer()

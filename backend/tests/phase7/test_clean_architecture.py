import os
import sys
import unittest
from pathlib import Path
import numpy as np

# Workspace root in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-phase7-tests-must-be-long-enough",
    "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

from unittest.mock import patch
with patch.dict(os.environ, _TEST_ENV):
    from app.domain.entities import DomainTurn, TurnStatus, LanguagePair
    from app.inference.interfaces import ISTTAdapter, ITranslationAdapter, ITTSAdapter
    from app.inference.adapters import MockSTTAdapter, MockTranslationAdapter, MockTTSAdapter
    from app.application.use_cases import TranslateTurnUseCase
    from app.core.container import CONTAINER, ServiceContainer
    from app.core.telemetry import PipelineTelemetryTracker
    from app.services.translation_cache import TranslationMemoryCache


class CleanArchitectureTests(unittest.TestCase):
    def setUp(self):
        CONTAINER.reset_overrides()

    def tearDown(self):
        CONTAINER.reset_overrides()

    def test_domain_language_pair_normalization(self):
        lp1 = LanguagePair.create("vie_Latn", "eng_Latn")
        self.assertEqual(lp1.source_lang, "vi")
        self.assertEqual(lp1.target_lang, "en")
        self.assertEqual(lp1.nllb_source, "vie_Latn")
        self.assertEqual(lp1.nllb_target, "eng_Latn")

        lp2 = LanguagePair.create("EN", "VI")
        self.assertEqual(lp2.source_lang, "en")
        self.assertEqual(lp2.target_lang, "vi")

        with self.assertRaises(ValueError):
            LanguagePair.create("", "en")

    def test_domain_turn_lifecycle(self):
        lp = LanguagePair.create("vi", "en")
        turn = DomainTurn(
            turn_id="turn-clean-1",
            session_id="session-1",
            speaker="speaker_a",
            lang_pair=lp,
            turn_index=1,
        )
        self.assertEqual(turn.status, TurnStatus.CREATED)
        self.assertTrue(turn.is_active())

        turn.mark_status(TurnStatus.PROCESSING_STT)
        self.assertEqual(turn.status, TurnStatus.PROCESSING_STT)

        # Cancel turn
        turn.cancel()
        self.assertEqual(turn.status, TurnStatus.CANCELLED)
        self.assertFalse(turn.is_active())

        # Once cancelled, cannot transition to other active states
        turn.mark_status(TurnStatus.PROCESSING_TRANSLATION)
        self.assertEqual(turn.status, TurnStatus.CANCELLED)

    def test_translate_turn_use_case_with_mock_adapters(self):
        mock_stt = MockSTTAdapter(predefined_text="hôm nay thời tiết đẹp")
        mock_trans = MockTranslationAdapter({"hôm nay thời tiết đẹp": "today the weather is nice"})
        mock_tts = MockTTSAdapter()
        telemetry = PipelineTelemetryTracker()
        cache = TranslationMemoryCache()

        use_case = TranslateTurnUseCase(
            stt_adapter=mock_stt,
            translation_adapter=mock_trans,
            tts_adapter=mock_tts,
            cache=cache,
            telemetry=telemetry,
        )

        lp = LanguagePair.create("vi", "en")
        turn = DomainTurn(
            turn_id="turn-uc-1",
            session_id="session-uc",
            speaker="user1",
            lang_pair=lp,
        )

        dummy_audio = np.zeros(16000, dtype=np.float32)
        result = use_case.process_turn(turn, dummy_audio, client_id="test_client")

        self.assertEqual(result["turn_id"], "turn-uc-1")
        self.assertEqual(result["status"], TurnStatus.COMPLETED.value)
        self.assertEqual(result["source_text"], "hôm nay thời tiết đẹp")
        self.assertEqual(result["translated_text"], "today the weather is nice")
        self.assertGreater(result["audio_bytes_length"], 0)

        # Cache check: second call should hit cache
        cached_result = cache.get("test_client", "vi", "en", "hôm nay thời tiết đẹp")
        self.assertEqual(cached_result, "today the weather is nice")

    def test_dependency_injection_container(self):
        mock_stt = MockSTTAdapter(predefined_text="DI Test")
        CONTAINER.set_stt_adapter(mock_stt)

        self.assertIs(CONTAINER.get_stt_adapter(), mock_stt)

        uc = CONTAINER.get_translate_use_case()
        self.assertIsInstance(uc, TranslateTurnUseCase)

        CONTAINER.reset_overrides()
        # After reset, it creates default Whisper adapter
        from app.inference.adapters import WhisperSTTAdapter
        self.assertIsInstance(CONTAINER.get_stt_adapter(), WhisperSTTAdapter)


if __name__ == "__main__":
    unittest.main()

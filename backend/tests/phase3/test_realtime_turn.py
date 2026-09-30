"""Phase 3 automated tests: Turn metadata immutability, Protocol v2, VAD windowing, and late result filtering."""
import asyncio
import os
import types
import unittest
from unittest.mock import Mock, patch

from app.models.turn_model import TurnMetadata, TurnStatus
from app.models.session_model import RealtimeSession
from app.services.vad_service import WebRtcVadStream


class TurnModelTests(unittest.TestCase):
    def test_turn_metadata_immutability(self):
        turn = TurnMetadata.create(
            session_id="session-123",
            turn_index=1,
            turn_id="turn-abc",
            speaker="partner",
            source_lang="en",
            target_lang="vie_Latn",
            config_version=2,
        )
        self.assertEqual(turn.turn_id, "turn-abc")
        self.assertEqual(turn.speaker, "partner")
        self.assertEqual(turn.source_lang, "en")
        self.assertEqual(turn.target_lang, "vie_Latn")
        self.assertEqual(turn.status, TurnStatus.RECORDING.value)

        # Immutability check: cannot set attribute on frozen dataclass
        with self.assertRaises((TypeError, AttributeError)):
            turn.status = "completed"  # type: ignore

        # with_status returns a fresh copy preserving original fields
        updated = turn.with_status(TurnStatus.COMPLETED)
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.turn_id, turn.turn_id)
        self.assertEqual(updated.source_lang, turn.source_lang)
        self.assertEqual(turn.status, "recording")


class VadWindowingTests(unittest.TestCase):
    def test_vad_finite_window_segmentation(self):
        class SyntheticContinuousSpeechVad:
            def is_speech(self, frame, sample_rate):
                return True

        stream = WebRtcVadStream(
            sample_rate=16000,
            channels=1,
            sample_width=2,
            frame_ms=30,
            silence_ms=700,
            max_speech_ms=3000,  # 3 seconds max window for test
        )
        stream._vad = SyntheticContinuousSpeechVad()

        # Send 7.2 seconds of continuous speech (16000 * 2 bytes/sec * 7.2 = 230400 bytes)
        audio = b"\x01\x00" * int(16000 * 7.2)
        finals, current, in_speech = stream.process(audio)

        # 7.2s with 3s window should produce 2 segmented utterances of 3s each, and 1.2s in current buffer
        self.assertEqual(len(finals), 2)
        # Each segmented utterance must be 3 seconds (16000 * 2 * 3 = 96000 bytes)
        self.assertEqual(len(finals[0]), 96000)
        self.assertEqual(len(finals[1]), 96000)
        self.assertTrue(len(current) <= 96000)

        # Flushing at turn end emits the remaining 1.2s
        flushed = stream.flush()
        self.assertIsNotNone(flushed)
        self.assertEqual(len(flushed), len(current))
        self.assertEqual(len(stream._current), 0)


class SessionTurnLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_session_turn_isolation_and_language_config(self):
        ws = Mock()
        session = RealtimeSession(
            websocket=ws,
            session_id="session-456",
            client_id="owner-456",
        )
        session.source_lang = "vi"
        session.target_lang = "eng_Latn"
        session.speaker = "me"

        # Turn 1: starts with vi -> eng_Latn
        turn1 = session.start_new_turn()
        self.assertEqual(turn1.turn_index, 1)
        self.assertEqual(turn1.source_lang, "vi")
        self.assertEqual(turn1.target_lang, "eng_Latn")
        self.assertEqual(turn1.speaker, "me")

        # User swaps language during recording of Turn 1
        session.update_pending_config(source_lang="en", target_lang="vie_Latn", speaker="partner")

        # Turn 1 must remain vi -> eng_Latn! (Metadata isolation)
        self.assertEqual(turn1.source_lang, "vi")
        self.assertEqual(turn1.target_lang, "eng_Latn")
        self.assertEqual(turn1.speaker, "me")

        # Turn 2: starts with newly configured en -> vie_Latn
        turn2 = session.start_new_turn()
        self.assertEqual(turn2.turn_index, 2)
        self.assertEqual(turn2.source_lang, "en")
        self.assertEqual(turn2.target_lang, "vie_Latn")
        self.assertEqual(turn2.speaker, "partner")

    async def test_late_result_filtering_on_cancelled_turn(self):
        ws = Mock()
        ws.send_json = Mock()
        session = RealtimeSession(
            websocket=ws,
            session_id="session-789",
            client_id="owner-789",
        )
        session.start_sender()

        turn = session.start_new_turn(turn_id="turn-to-cancel")
        self.assertTrue(session.is_turn_active(turn.turn_id))

        # Cancel turn
        session.cancel_active_turn("turn-to-cancel")
        self.assertFalse(session.is_turn_active("turn-to-cancel"))

        # Message for active turn is enqueued
        valid_msg = {"type": "stt", "turn_id": "other-turn", "text": "hello"}
        sent_valid = await session.send_message(valid_msg)
        self.assertTrue(sent_valid)

        # Message for cancelled turn is dropped immediately
        cancelled_msg = {"type": "stt", "turn_id": "turn-to-cancel", "text": "should be dropped"}
        sent_cancelled = await session.send_message(cancelled_msg)
        self.assertFalse(sent_cancelled)

        if session.sender_task:
            session.sender_task.cancel()


if __name__ == "__main__":
    unittest.main()

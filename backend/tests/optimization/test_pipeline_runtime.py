"""Isolated runtime regressions with real session/VAD/workers and mocked models."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

_REPO = Path(__file__).resolve().parents[3]


class RuntimeProcessTests(unittest.TestCase):
    def test_pipeline_runtime_in_isolated_process(self):
        with tempfile.TemporaryDirectory(prefix="runtime-regression-") as directory:
            result = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--isolated"],
                cwd=directory, env={**os.environ, "APP_ENV": "local", "DATABASE_URL": "sqlite:///:memory:",
                                   "JWT_SECRET_KEY": "runtime-test-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                                   "AUTH_REQUIRE_PRIVILEGED_MFA": "false", "USE_SILERO_VAD": "0",
                                   "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True, text=True, timeout=90,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def isolated_suite(legacy=False):
    import asyncio
    import contextlib
    import importlib.util
    import io
    import json
    import threading
    import time
    import types
    import wave
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock, patch

    sys.path.insert(0, str(_REPO / "backend"))
    sys.path.insert(0, str(_REPO))
    import numpy as np
    import httpx
    from fastapi import FastAPI
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy.pool import StaticPool

    def module(name, **values):
        result = types.ModuleType(name)
        result.__dict__.update(values)
        sys.modules[name] = result
        return result

    fake_torch = module("torch", inference_mode=contextlib.nullcontext,
                        cuda=SimpleNamespace(is_available=lambda: False, empty_cache=lambda: None))
    fake_config = module("app.core.config", BYTES_PER_SAMPLE=2, CHANNELS=1, SAMPLE_RATE=16000,
                         VAD_AGGRESSIVENESS=2, VAD_FRAME_MS=30, VAD_SILENCE_MS=700, VAD_SPEECH_PAD_MS=120,
                         MIN_BUFFER_BYTES=3200, MAX_BUFFER_BYTES=960000,
                         STT_CONCURRENCY=1, TRANSLATION_CONCURRENCY=1, TTS_CONCURRENCY=1,
                         TARGET_LANG="eng_Latn", SOURCE_LANG="vie_Latn", DEVICE="cpu",
                         OUTPUT_DIR=str(Path.cwd() / "outputs"),
                         settings=SimpleNamespace(APP_ENV="local", WHISPER_BEAM_SIZE=1,
                                                  TRANSLATION_BEAM_SIZE=1))
    fake_db = module("app.db.database", Base=declarative_base(), get_db=lambda: None)
    fake_db.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    fake_db.SessionLocal = sessionmaker(bind=fake_db.engine)
    model_manager_module = module("app.ai.model_manager", model_manager=SimpleNamespace(is_loaded=False, device="cpu", whisper_model=None))
    queues = module("app.core.queues", GLOBAL_STT_QUEUE=asyncio.Queue(), GLOBAL_TRANSLATE_QUEUE=asyncio.Queue(), GLOBAL_TTS_QUEUE=asyncio.Queue())
    module("app.services.deepfilter_service", denoise_numpy=lambda audio, **kwargs: audio)
    module("app.services.semantic_service", correct_text_semantics=lambda text, context="": text)
    exists = os.path.exists
    live_tm = os.path.normcase(str(_REPO / "backend/data/translation_memory.json"))
    with patch("os.path.exists", side_effect=lambda path: False if os.path.normcase(os.path.abspath(path)) == live_tm else exists(path)):
        from app.services import translation_memory as tm
    from app.core import security, access_policy
    from app.core.inference_errors import NoSpeechDetected
    from app.core.telemetry import PipelineTelemetryTracker
    from app.models.session_model import RealtimeSession
    from app.services.vad_service import WebRtcVadStream
    from app.services import whisper_service as whisper, pipeline_service as pipeline, audio_storage
    from app.api import routes as api, websocket as websocket_api
    from app.api.v1 import health
    from app.workers import runtime, stt_worker as stt, translation_worker as translate, tts_worker as tts
    from app.db.models import User, SystemSetting, TranslationLog
    from app.db.audio_model import AudioAsset

    legacy_app = FastAPI()
    legacy_app.include_router(health.router)
    legacy_app.include_router(health.router, prefix="/api/v1")
    module("app.main", app=legacy_app)

    def load_test(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        return loaded

    if legacy:
        suite = unittest.TestSuite()
        for path, name in (
            (_REPO / "backend/tests/phase5/test_performance_metrics.py", "legacy_phase5"),
            (_REPO / "backend/tests/phase6/test_operations_lifecycle.py", "legacy_phase6"),
        ):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load_test(path, name)))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        fake_db.engine.dispose()
        return 0 if result.wasSuccessful() else 1

    class PipelineRuntimeTests(unittest.IsolatedAsyncioTestCase):
        def setUp(self):
            self.stack = contextlib.ExitStack()
            self.addCleanup(self.stack.close)
            self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="runtime-case-")))
            for name in ("_memory", "_guest_memory", "_guest_expiry"):
                self.stack.enter_context(patch.object(tm, name, {}))
            self.stack.enter_context(patch.object(tm, "_TM_FILE", str(self.temp / "tm.json")))
            self.stack.enter_context(patch.object(tm, "_DATA_DIR", str(self.temp)))
            self.stack.enter_context(patch.object(audio_storage, "SECURE_OUTPUT_DIR", self.temp / "outputs"))
            self.stack.enter_context(patch.object(api, "SECURE_TEMP_DIR", self.temp / "uploads"))
            self.tracker = PipelineTelemetryTracker()
            for target in (runtime, stt, translate, tts, websocket_api, pipeline, api):
                self.stack.enter_context(patch.object(target, "GLOBAL_TELEMETRY", self.tracker))
            self.stt_queue, self.translation_queue, self.tts_queue = asyncio.Queue(maxsize=10), asyncio.Queue(maxsize=10), asyncio.Queue(maxsize=10)
            for target in (websocket_api, stt):
                self.stack.enter_context(patch.object(target, "GLOBAL_STT_QUEUE", self.stt_queue))
            for target in (stt, translate):
                self.stack.enter_context(patch.object(target, "GLOBAL_TRANSLATE_QUEUE", self.translation_queue))
            for target in (translate, tts):
                self.stack.enter_context(patch.object(target, "GLOBAL_TTS_QUEUE", self.tts_queue))
            self.stack.enter_context(patch.object(stt, "_stt_semaphore", asyncio.Semaphore(1)))
            self.stack.enter_context(patch.object(translate, "_translation_semaphore", asyncio.Semaphore(1)))
            self.stack.enter_context(patch.object(tts, "_tts_semaphore", asyncio.Semaphore(1)))
            self.stack.enter_context(patch.object(translate, "_cache_enabled_sync", return_value=True))
            self.stack.enter_context(patch.object(access_policy, "rate_limiter", access_policy.RateLimiter()))
            fake_db.Base.metadata.drop_all(fake_db.engine)
            fake_db.Base.metadata.create_all(fake_db.engine)
            self.db = fake_db.SessionLocal()
            self.stack.callback(self.db.close)
            self.user = User(username="runtime-user", password_hash="unused", role="employee")
            self.db.add(self.user)
            self.db.add(SystemSetting(key="enable_cache", value="true"))
            self.db.commit()
            token = security.issue_user_session(self.user, self.db)["access_token"]
            self.headers = {"Authorization": "Bearer " + token}
            self.app = FastAPI()
            self.app.include_router(api.router)
            self.app.include_router(health.router)
            self.app.dependency_overrides[fake_db.get_db] = lambda: self.db
            self.ws = SimpleNamespace(send_json=AsyncMock())
            self.session = RealtimeSession(self.ws, "runtime-session", client_id=self.user.public_id, source_lang="en", target_lang="vie_Latn")
            self.turn = self.session.start_new_turn("turn1")
            samples = np.sin(np.arange(4800) * (2 * np.pi * 440 / 16000)) * 0.2
            self.pcm = (samples * 32767).astype("<i2").tobytes()
            stream = io.BytesIO()
            with wave.open(stream, "wb") as output:
                output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                output.writeframes(self.pcm)
            self.wav = stream.getvalue()
            self.worker_tasks = []

        async def asyncTearDown(self):
            for task in self.worker_tasks:
                task.cancel()
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        def messages(self):
            result = []
            while not self.session.send_queue.empty():
                result.append(self.session.send_queue.get_nowait())
                self.session.send_queue.task_done()
            return result

        async def queue(self, turn=None):
            return await websocket_api._queue_utterance(self.ws, self.session, self.pcm, turn or self.turn)

        def start_workers(self, all_stages=True):
            self.worker_tasks.append(asyncio.create_task(stt.stt_worker()))
            if all_stages:
                self.worker_tasks.extend([asyncio.create_task(translate.translation_worker()), asyncio.create_task(tts.tts_worker())])

        async def drain(self):
            for queue in (self.stt_queue, self.translation_queue, self.tts_queue):
                await asyncio.wait_for(queue.join(), 2)

        async def test_ws_idle_timeout_waits_for_pending_inference(self):
            socket = SimpleNamespace(receive=AsyncMock())
            calls = 0

            async def wait_for(awaitable, timeout):
                nonlocal calls
                awaitable.close()
                calls += 1
                if calls == 1 or self.session.pending_utterances == 0:
                    raise asyncio.TimeoutError()
                return {"type": "websocket.receive"}

            self.session.pending_utterances = 1
            with patch.object(websocket_api.asyncio, "wait_for", side_effect=wait_for):
                message = await websocket_api._receive_while_processing(socket, self.session, 10)
                self.assertEqual(message["type"], "websocket.receive")
                self.assertEqual(calls, 2)
                self.session.pending_utterances = 0
                with self.assertRaises(asyncio.TimeoutError):
                    await websocket_api._receive_while_processing(socket, self.session, 10)

        async def test_vad_accumulates_frames_then_queues_complete_utterance(self):
            vad = WebRtcVadStream(speech_pad_ms=0, silence_ms=60)
            vad._vad = SimpleNamespace(is_speech=lambda frame, rate: frame[0] != 0)
            speech = b"\1\0" * 480
            silence = b"\0\0" * 480
            final = []
            payload = speech * 4 + silence * 2
            for offset in range(0, len(payload), 320):
                utterances, _, _ = vad.process(payload[offset:offset + 320])
                final.extend(utterances)
            self.assertEqual(final, [payload])
            self.assertFalse(vad.flush())
            self.assertEqual(self.stt_queue.qsize(), 0)
            self.assertTrue(await websocket_api._queue_utterance(self.ws, self.session, final[0], self.turn))
            self.assertEqual(self.stt_queue.qsize(), 1)
            self.assertEqual(self.session.pending_by_turn, {"turn1": 1})

        async def test_pending_limit_four_is_shared_across_turns_and_released_per_turn(self):
            self.assertTrue(await self.queue())
            self.assertTrue(await self.queue())
            self.session.end_active_turn()
            second = self.session.start_new_turn("turn2")
            self.assertTrue(await self.queue(second))
            self.assertTrue(await self.queue(second))
            self.assertFalse(await self.queue(second))
            self.assertEqual(self.session.pending_utterances, 4)
            self.assertEqual(self.session.pending_by_turn, {"turn1": 2, "turn2": 2})
            self.assertIn("busy", [message.get("status") for message in self.messages()])
            first_item = self.stt_queue.get_nowait()
            second_item = self.stt_queue.get_nowait()
            await runtime.finish_work(first_item)
            self.assertEqual(self.messages(), [])
            await runtime.finish_work(second_item)
            self.assertEqual([message["turn_id"] for message in self.messages() if message["type"] == "turn_complete"], ["turn1"])
            self.assertEqual(self.session.pending_by_turn, {"turn2": 2})
            self.assertEqual(self.session.pending_utterances, 2)
            await runtime.finish_work(second_item)
            self.assertEqual(self.session.pending_utterances, 2)

        async def test_full_queue_and_short_audio_do_not_leak_reservations_or_metrics(self):
            for _ in range(10):
                self.stt_queue.put_nowait({"unrelated": True})
            self.assertFalse(await self.queue())
            self.assertFalse(await websocket_api._queue_utterance(self.ws, self.session, b"\1\0" * 100, self.turn))
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.session.pending_by_turn, {})
            self.assertEqual(self.tracker.get_summary()["active_turns"], 0)

        async def test_all_worker_stages_finish_utterances_but_wait_for_end_turn(self):
            with patch.object(stt, "transcribe_audio", return_value={"text": "private transcript", "language": "en", "latency": .01}), \
                 patch.object(translate, "translate_text", return_value={"translated_text": "private translation", "latency": .01}), \
                 patch.object(tts, "generate_speech_bytes", return_value=self.wav):
                self.start_workers()
                await self.queue()
                await self.queue()
                await self.drain()
            messages = self.messages()
            self.assertEqual(sum(m["type"] == "audio_done" for m in messages), 2)
            self.assertEqual(sum(m["type"] == "turn_complete" for m in messages), 0)
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.tracker.get_summary()["total_completed"], 2)
            ended = self.session.end_active_turn()
            await runtime.complete_if_idle(self.session, ended)
            await runtime.complete_if_idle(self.session, ended)
            self.assertEqual(sum(m["type"] == "turn_complete" for m in self.messages()), 1)
            report = json.dumps(self.tracker.get_activity_summary())
            self.assertNotIn("private transcript", report)
            self.assertNotIn("private translation", report)
            self.assertNotIn(self.user.public_id, report)
            self.assertEqual(self.db.query(TranslationLog).count(), 0)

        async def test_end_turn_waits_for_all_queued_work_then_completes_once(self):
            with patch.object(stt, "transcribe_audio", return_value={"text": "hello", "language": "en", "latency": .01}), \
                 patch.object(translate, "translate_text", return_value={"translated_text": "xin chao", "latency": .01}), \
                 patch.object(tts, "generate_speech_bytes", return_value=self.wav):
                await self.queue()
                await self.queue()
                ended = self.session.end_active_turn()
                await runtime.complete_if_idle(self.session, ended)
                self.assertEqual(self.messages(), [])
                self.start_workers()
                await self.drain()
            messages = self.messages()
            self.assertEqual(messages[-1]["type"], "turn_complete")
            self.assertEqual(sum(m["type"] == "turn_complete" for m in messages), 1)
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.session.pending_by_turn, {})
            self.assertEqual(self.tracker.get_summary()["active_turns"], 0)

        async def test_no_speech_releases_queue_and_never_invokes_translation(self):
            with patch.object(stt, "transcribe_audio", return_value={"text": "", "language": "en", "latency": 0}), \
                 patch.object(translate, "translate_text") as inference:
                await self.queue()
                self.session.end_active_turn()
                self.start_workers(all_stages=False)
                await asyncio.wait_for(self.stt_queue.join(), 2)
            inference.assert_not_called()
            self.assertEqual(self.translation_queue.qsize(), 0)
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.tracker.get_summary()["total_completed"], 0)
            self.assertEqual(self.tracker.get_summary()["active_turns"], 0)
            self.assertIn("no_speech_detected", [message.get("code") for message in self.messages()])

        async def test_cancelled_queued_turn_is_discarded_without_success(self):
            await self.queue()
            self.session.cancel_active_turn()
            with patch.object(stt, "transcribe_audio") as inference:
                self.start_workers(all_stages=False)
                await asyncio.wait_for(self.stt_queue.join(), 2)
            inference.assert_not_called()
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.session.pending_by_turn, {})
            self.assertEqual(self.tracker.get_summary()["active_turns"], 0)
            self.assertEqual(self.tracker.get_summary()["total_completed"], 0)
            self.assertEqual(self.messages(), [])

        async def test_cancel_during_tts_does_not_close_session_or_deliver_stale_audio(self):
            await self.queue()
            item = self.stt_queue.get_nowait()
            self.stt_queue.task_done()
            item["text"] = "hello"
            self.tts_queue.put_nowait(item)
            def cancel_during_generation(*args):
                self.session.cancel_active_turn(self.turn.turn_id)
                return self.wav
            with patch.object(tts, "generate_speech_bytes", side_effect=cancel_during_generation):
                self.worker_tasks.append(asyncio.create_task(tts.tts_worker()))
                await asyncio.wait_for(self.tts_queue.join(), 2)
            self.assertTrue(self.session.is_running, "Cancelling one turn must keep the websocket session usable")
            self.assertFalse(any(m["type"] in {"audio_chunk", "audio_done", "turn_complete"} for m in self.messages()))
            self.assertEqual(self.session.pending_utterances, 0)
            self.assertEqual(self.tracker.get_summary()["total_completed"], 0)

        async def test_wav_path_is_decoded_to_float_samples_for_whisper(self):
            path = self.temp / "speech.wav"
            path.write_bytes(self.wav)
            model = MagicMock()
            model.transcribe.return_value = ([SimpleNamespace(text="hello test", no_speech_prob=0.0)], SimpleNamespace(language="en"))
            with patch.object(whisper, "_get_whisper_model", return_value=model):
                result = whisper.transcribe_audio(path, language="eng_Latn")
            self.assertEqual(result["text"], "hello test")
            samples = model.transcribe.call_args.args[0]
            self.assertIsInstance(samples, np.ndarray)
            self.assertEqual(samples.dtype, np.float32)
            self.assertEqual(samples.shape, (4800,))
            self.assertLessEqual(float(np.abs(samples).max()), 1)
            self.assertEqual(model.transcribe.call_args.kwargs["language"], "en")

        async def test_short_audio_does_not_use_generic_prompt(self):
            model = MagicMock()
            model.transcribe.return_value = (
                [SimpleNamespace(text="Sở thú", no_speech_prob=0.0)],
                SimpleNamespace(language="vi"),
            )
            audio = np.full(16000, 0.1, dtype=np.float32)
            with patch.object(whisper, "_get_whisper_model", return_value=model):
                result = whisper.transcribe_audio(audio, language="vi", use_vad=False)
            self.assertEqual(result["text"], "Sở thú")
            self.assertEqual(model.transcribe.call_args.kwargs["initial_prompt"], "")

        async def test_short_audio_keeps_user_glossary_prompt(self):
            model = MagicMock()
            model.transcribe.return_value = (
                [SimpleNamespace(text="Sở thú", no_speech_prob=0.0)],
                SimpleNamespace(language="vi"),
            )
            audio = np.full(16000, 0.1, dtype=np.float32)
            with patch.object(whisper, "_get_whisper_model", return_value=model):
                whisper.transcribe_audio(
                    audio, language="vi", use_vad=False, context_prompt="sở thú",
                )
            self.assertEqual(model.transcribe.call_args.kwargs["initial_prompt"], "sở thú")

        async def test_silence_and_short_audio_never_load_whisper(self):
            with patch.object(whisper, "_get_whisper_model") as model:
                self.assertEqual(whisper.transcribe_audio(np.zeros(16000, dtype=np.float32))["text"], "")
                self.assertEqual(whisper.transcribe_audio(np.ones(100, dtype=np.float32))["text"], "")
            model.assert_not_called()

        async def test_pipeline_no_speech_never_translates_or_synthesizes(self):
            with patch.object(pipeline, "transcribe_audio", return_value={"text": " ", "latency": 0}), \
                 patch.object(pipeline, "translate_text") as translation, \
                 patch.object(pipeline, "generate_speech") as synthesis:
                with self.assertRaises(NoSpeechDetected):
                    pipeline.run_pipeline("unused.wav", client_id=self.user.public_id)
            translation.assert_not_called()
            synthesis.assert_not_called()
            self.assertEqual(self.tracker.get_summary()["active_turns"], 0)
            self.assertEqual(self.tracker.get_summary()["total_completed"], 0)

        async def test_pipeline_records_real_stage_metrics_without_content(self):
            def stt_result(*args, **kwargs):
                time.sleep(.002)
                return {"text": "private original", "latency": .002}
            def translation_result(*args, **kwargs):
                time.sleep(.002)
                return {"translated_text": "private result", "latency": .002}
            def synthesis_result(text, output, **kwargs):
                time.sleep(.002)
                Path(output).write_bytes(self.wav)
                return {"latency": .002}
            with patch.object(pipeline, "transcribe_audio", side_effect=stt_result), \
                 patch.object(pipeline, "translate_text", side_effect=translation_result), \
                 patch.object(pipeline, "generate_speech", side_effect=synthesis_result):
                pipeline.run_pipeline("unused.wav", client_id=self.user.public_id,
                                      source_lang="en", target_lang="vi", output_path=str(self.temp / "out.wav"))
            summary = self.tracker.get_summary()
            self.assertEqual(summary["total_completed"], 1)
            for stage in ("stt", "translate", "tts_total", "end_to_end"):
                self.assertGreater(summary["latencies_ms"][stage]["p50"], 0)
            self.assertEqual(self.tracker.get_activity_summary()["languages"], [{"source_lang": "en", "target_lang": "vi", "value": 1}])
            self.assertNotIn("private", json.dumps(self.tracker.get_activity_summary()))
            self.assertEqual(self.db.query(TranslationLog).count(), 0)

        async def test_http_upload_inference_runs_off_event_loop_and_health_responds(self):
            entered, release = threading.Event(), threading.Event()
            observed = []
            def slow_pipeline(path, **kwargs):
                entered.set()
                observed.append(release.wait(1.0))
                Path(kwargs["output_path"]).write_bytes(self.wav)
                return {"original_text": "fixture", "translated_text": "fixture result"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as client:
                with patch.object(api, "run_pipeline", side_effect=slow_pipeline):
                    upload = asyncio.create_task(client.post("/translate", headers=self.headers,
                        files={"file": ("speech.wav", self.wav, "audio/wav")}))
                    async def wait_until_inference_starts():
                        while not entered.is_set():
                            await asyncio.sleep(.001)
                    await asyncio.wait_for(wait_until_inference_starts(), 2)
                    live = await client.get("/health/live")
                    self.assertEqual(live.status_code, 200)
                    release.set()
                    response = await upload
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(observed, [True], "Inference blocked the event loop before liveness could run")

        async def test_http_no_speech_returns_422_and_cleans_temp_output(self):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as client:
                with patch.object(api, "run_pipeline", side_effect=NoSpeechDetected("fixture")):
                    response = await client.post("/translate", headers=self.headers,
                        files={"file": ("speech.wav", self.wav, "audio/wav")})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(self.db.query(AudioAsset).count(), 0)
            self.assertEqual(list((self.temp / "uploads").glob("*")), [])
            self.assertEqual(list((self.temp / "outputs").glob("*")), [])

        async def test_direct_text_metrics_count_success_and_error_without_retaining_content(self):
            payload = {"text": "private input transcript", "source_lang": "en", "target_lang": "vi"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as client:
                with patch.object(api, "translate_text", return_value={"translated_text": "private output translation"}):
                    success = await client.post("/api/translate-text", headers=self.headers, json=payload)
                with patch.object(api, "translate_text", side_effect=RuntimeError("private details")):
                    failure = await client.post("/api/translate-text", headers=self.headers, json=payload)
            self.assertEqual(success.status_code, 200, success.text)
            self.assertEqual(failure.status_code, 503, failure.text)
            self.assertNotIn("private details", failure.text)
            summary = self.tracker.get_summary()
            self.assertEqual(summary["total_completed"], 1)
            self.assertEqual(summary["total_errors"], 1)
            self.assertEqual(summary["active_turns"], 0)
            self.assertNotIn("private", json.dumps(self.tracker.get_activity_summary()))
            self.assertEqual(self.db.query(TranslationLog).count(), 0)

        async def test_readiness_rejects_missing_empty_dead_or_incomplete_worker_pool(self):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as client:
                self.app.state.expected_worker_count = 2
                for tasks in ([], [SimpleNamespace(done=lambda: False)], [SimpleNamespace(done=lambda: False), SimpleNamespace(done=lambda: True)]):
                    self.app.state.worker_tasks = tasks
                    response = await client.get("/health/ready")
                    self.assertEqual(response.status_code, 503, response.text)
                    self.assertEqual(response.json()["workers"], "error")
                self.app.state.worker_tasks = [SimpleNamespace(done=lambda: False), SimpleNamespace(done=lambda: False)]
                self.assertEqual((await client.get("/health/ready")).status_code, 200)
                self.app.state.is_draining = True
                self.assertEqual((await client.get("/health/ready")).status_code, 503)

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PipelineRuntimeTests))
    fake_db.engine.dispose()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if "--isolated" in sys.argv or "--legacy" in sys.argv:
        raise SystemExit(isolated_suite(legacy="--legacy" in sys.argv))
    unittest.main()

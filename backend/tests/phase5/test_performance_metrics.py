import os
import unittest
import time
from unittest.mock import patch, MagicMock

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-phase5-tests-must-be-long-enough",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from app.core.telemetry import PipelineTelemetryTracker, TurnMetric
    from app.core.scheduler import FairSessionQueue
    from app.core.gpu_manager import GPUResourceManager, ModelConcurrencyGovernor
    from app.services.translation_cache import TranslationMemoryCache
    from app.db.models import TranslationLog, Base, User
    from app.db.database import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker


class Phase5PerformanceMetricsTests(unittest.IsolatedAsyncioTestCase):
    def test_telemetry_turn_recording_and_percentiles(self):
        tracker = PipelineTelemetryTracker(max_history=100)
        
        # Fixed monotonic samples test durations without OS sleep-resolution noise.
        with patch("app.core.telemetry.time.perf_counter", side_effect=[
            100.0, 100.0, 100.01, 100.01, 100.03, 100.03, 100.045, 100.045, 100.045, 100.055,
        ]):
            tracker.start_turn("turn-1", "session-1", audio_duration_s=2.5)
            for stage in ("queue_in", "queue_out", "stt_start", "stt_done", "translate_start",
                          "translate_done", "tts_start", "tts_chunk_0", "tts_done"):
                tracker.record_stage("turn-1", stage)
            completed = tracker.complete_turn("turn-1")

        self.assertIsNotNone(completed)
        self.assertGreater(completed.queue_wait_ms, 5.0)
        self.assertGreater(completed.stt_ms, 15.0)
        self.assertGreater(completed.translate_ms, 10.0)
        self.assertGreater(completed.total_latency_ms, 40.0)

        # Summary
        summary = tracker.get_summary()
        self.assertEqual(summary["total_completed"], 1)
        self.assertGreater(summary["latencies_ms"]["stt"]["p50"], 0.0)
        self.assertGreater(summary["latencies_ms"]["translate"]["p50"], 0.0)
        self.assertGreater(summary["latencies_ms"]["end_to_end"]["p50"], 0.0)

    def test_telemetry_percentiles_use_nearest_rank_for_small_samples(self):
        tracker = PipelineTelemetryTracker(max_history=10)
        tracker._completed_metrics.extend([
            TurnMetric(turn_id="fast", session_id="s", t_turn_received=10.0, t_translate_done=10.1),
            TurnMetric(turn_id="slow", session_id="s", t_turn_received=20.0, t_translate_done=20.4),
        ])
        tracker._total_turns_processed = 2

        latency = tracker.get_summary()["latencies_ms"]["end_to_end"]
        self.assertEqual(latency["p50"], 100.0)
        self.assertEqual(latency["p90"], 400.0)
        self.assertEqual(latency["p99"], 400.0)

    async def test_fair_session_queue_round_robin(self):
        fq = FairSessionQueue(max_per_session=5, max_total_items=20)

        # Session A puts 3 items
        await fq.put({"id": "A1"}, session_id="sessionA")
        await fq.put({"id": "A2"}, session_id="sessionA")
        await fq.put({"id": "A3"}, session_id="sessionA")

        # Session B puts 2 items
        await fq.put({"id": "B1"}, session_id="sessionB")
        await fq.put({"id": "B2"}, session_id="sessionB")

        self.assertEqual(fq.qsize(), 5)
        self.assertEqual(fq.active_session_count(), 2)

        # Popping should alternate between sessionA and sessionB (Round-Robin)
        item1 = await fq.get()
        item2 = await fq.get()
        item3 = await fq.get()
        item4 = await fq.get()
        item5 = await fq.get()

        # Should be A1, B1, A2, B2, A3
        self.assertEqual(item1["id"], "A1")
        self.assertEqual(item2["id"], "B1")
        self.assertEqual(item3["id"], "A2")
        self.assertEqual(item4["id"], "B2")
        self.assertEqual(item5["id"], "A3")

        self.assertEqual(fq.qsize(), 0)
        self.assertTrue(fq.empty())

    async def test_fair_session_queue_per_session_limit(self):
        fq = FairSessionQueue(max_per_session=2, max_total_items=10)
        ok1 = await fq.put({"id": "A1"}, session_id="sessionA")
        ok2 = await fq.put({"id": "A2"}, session_id="sessionA")
        ok3 = await fq.put({"id": "A3"}, session_id="sessionA") # Should be rejected
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertFalse(ok3)
        self.assertEqual(fq.qsize(), 2)

    def test_adaptive_gpu_cleanup_policy(self):
        mgr = GPUResourceManager(memory_threshold_ratio=0.85, idle_cleanup_interval_s=60.0)
        # Without CUDA or below threshold, cleanup should not trigger
        with patch.object(mgr, "is_cuda_available", return_value=True), \
             patch.object(mgr, "get_memory_stats", return_value={"utilization_ratio": 0.40}):
            with patch("torch.cuda.empty_cache") as mock_empty:
                triggered = mgr.adaptive_cleanup(force=False)
                self.assertFalse(triggered)
                mock_empty.assert_not_called()

        # When threshold exceeded (> 85%), cleanup MUST trigger
        with patch.object(mgr, "is_cuda_available", return_value=True), \
             patch.object(mgr, "get_memory_stats", return_value={"utilization_ratio": 0.92}):
            with patch("torch.cuda.empty_cache") as mock_empty:
                triggered = mgr.adaptive_cleanup(force=False)
                self.assertTrue(triggered)
                mock_empty.assert_called_once()

    def test_translation_cache_lru_and_invalidation(self):
        cache = TranslationMemoryCache(max_entries=3, default_ttl_s=3600.0)

        cache.put("user1", "vi", "en", "xin chào", "hello")
        cache.put("user1", "vi", "en", "cảm ơn", "thank you")

        self.assertEqual(cache.get("user1", "vi", "en", "xin chào"), "hello")
        self.assertEqual(cache.get("user1", "vi", "en", "cảm ơn"), "thank you")

        # Invalidate by bumping version
        cache.bump_version("user1")
        # Old entries should be effectively invalidated
        self.assertIsNone(cache.get("user1", "vi", "en", "xin chào"))

    def test_process_metrics_aggregation_does_not_count_retained_qa_content(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # Retained QA text must not be mistaken for current process traffic.
            db.add(TranslationLog(client_id="old-owner", source_text="private QA source", translated_text="private QA target", latency=99, source_lang="en", target_lang="vi"))
            db.commit()

            tracker = PipelineTelemetryTracker()
            for index, (owner, source, target, latency) in enumerate([
                ("c1", "en", "vi", .25), ("c1", "en", "vi", .35), ("c2", "vi", "en", .15),
            ]):
                metric = tracker.start_turn(str(index), owner, source_lang=source, target_lang=target)
                metric.t_translate_done = metric.t_turn_received + latency
                tracker.complete_turn(str(index))
            from app.api import admin_routes
            with patch.object(admin_routes, "GLOBAL_TELEMETRY", tracker):
                langs = admin_routes.get_metrics_languages(db=db, user=MagicMock())
                self.assertEqual(len(langs), 2)
                self.assertTrue(any(item["name"] == "Tiếng Anh -> Tiếng Việt" and item["value"] == 2 for item in langs))
                self.assertTrue(any(item["name"] == "Tiếng Việt -> Tiếng Anh" and item["value"] == 1 for item in langs))
                ts = admin_routes.get_metrics_timeseries(db=db, user=MagicMock())
                self.assertEqual(sum(row["requests"] for row in ts), 3)
                self.assertAlmostEqual(ts[0]["avg_latency"], 0.25, delta=0.01)
                dashboard = admin_routes.get_dashboard_metrics(db=db, user=MagicMock())
                self.assertEqual(dashboard["total_translations"], 3)
                self.assertEqual(dashboard["scope"], "since_process_start")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

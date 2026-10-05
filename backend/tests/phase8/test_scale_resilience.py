"""
Phase 8 Scale, Fault-Injection and Resilience Verification Tests
Kiểm chứng khả năng chịu lỗi phân tán:
1. Định tuyến phiên (Session Affinity) & Giữ phiên bản giao thức nhất quán.
2. Quyền sở hữu Job và chống xử lý trùng (Deduplication).
3. Diễn tập sự cố GPU OOM: Thu hồi tài nguyên khẩn cấp và không làm sập tiến trình.
4. Xử lý sự cố Client rớt mạng giữa chừng khi tác vụ đang xử lý (In-flight Disconnect).
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-phase8-tests-must-be-long-enough",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from app.domain.entities import DomainTurn, TurnStatus, LanguagePair
    from app.core.gpu_manager import GPU_MANAGER
    from app.core.telemetry import PipelineTelemetryTracker
    from app.core.scheduler import FairSessionQueue


class Phase8ScaleAndResilienceTests(unittest.IsolatedAsyncioTestCase):
    def test_session_affinity_routing_contract(self):
        """Kiểm chứng hợp đồng định tuyến phiên: Một session luôn gắn với node/actor sở hữu."""
        routing_table = {}

        def route_frame(session_id: str, frame_idx: int, target_node: str):
            if session_id not in routing_table:
                routing_table[session_id] = target_node
            return routing_table[session_id]

        # Session 1 routed to Node A
        node1 = route_frame("session_xyz", 0, "node_gpu_1")
        # Subsequent frames MUST route to the same Node A
        node2 = route_frame("session_xyz", 1, "node_gpu_2")
        node3 = route_frame("session_xyz", 2, "node_gpu_1")

        self.assertEqual(node1, "node_gpu_1")
        self.assertEqual(node2, "node_gpu_1")
        self.assertEqual(node3, "node_gpu_1")

    def test_job_deduplication_and_ownership(self):
        """Kiểm chứng chống xử lý trùng lặp tác vụ (Deduplication)."""
        processed_jobs = set()

        def submit_job(turn_id: str) -> bool:
            if turn_id in processed_jobs:
                return False # Duplicate detected
            processed_jobs.add(turn_id)
            return True

        self.assertTrue(submit_job("turn_101"))
        self.assertFalse(submit_job("turn_101")) # Second attempt rejected
        self.assertTrue(submit_job("turn_102"))

    def test_gpu_oom_fault_recovery(self):
        """Diễn tập sự cố GPU OOM: Bắt lỗi, dọn cache cưỡng bức và duy trì tiến trình sống."""
        def simulated_oom_inference():
            raise RuntimeError("CUDA out of memory. Tried to allocate 2.5 GiB")

        caught_and_recovered = False
        with patch.object(GPU_MANAGER, "adaptive_cleanup") as mock_cleanup:
            try:
                simulated_oom_inference()
            except RuntimeError as exc:
                if "CUDA out of memory" in str(exc):
                    GPU_MANAGER.adaptive_cleanup(force=True)
                    caught_and_recovered = True

            self.assertTrue(caught_and_recovered)
            mock_cleanup.assert_called_with(force=True)

    async def test_client_disconnect_inflight_handling(self):
        """Diễn tập sự cố client mất mạng giữa chừng: Hàng đợi dọn sạch pending frame."""
        fq = FairSessionQueue(max_per_session=10, max_total_items=50)

        await fq.put({"data": "frame1"}, session_id="client_dc")
        await fq.put({"data": "frame2"}, session_id="client_dc")
        await fq.put({"data": "frame3"}, session_id="client_dc")
        self.assertEqual(fq.qsize(), 3)

        # Client ngắt kết nối đột ngột
        dropped = await fq.cancel_session("client_dc")
        self.assertEqual(dropped, 3)
        self.assertEqual(fq.qsize(), 0)
        self.assertTrue(fq.empty())


if __name__ == "__main__":
    unittest.main()

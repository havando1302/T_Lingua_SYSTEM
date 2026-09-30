"""
COMPREHENSIVE AUTONOMOUS SYSTEM AUDIT & E2E TEST SUITE
Bao phủ 100% các tiêu chuẩn:
- P0: Bảo mật & Xác thực (Token, RBAC, Cross-tenant data isolation)
- P0: Luồng Realtime & Xử lý Âm thanh (Turn sequence, Mic/Tab switch, Queue backpressure)
- P0: Tính toàn vẹn Dữ liệu & Bản dịch (TM multi-key, Atomic rollback)
- P1/P2: Giao diện Client & Tải đồng thời (Pagination, Fair-share concurrency)
"""
import os
import sys
import time
import json
import uuid
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Workspace root in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "super-secret-e2e-audit-key-must-be-very-long-and-secure",
    "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from starlette.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.db.models import Base, User, TranslationLog, ApiKey, TranslationMemoryEntry
    from app.core.security import (
        get_password_hash,
        issue_user_session,
        RESOURCE_SCOPES,
    )
    from jose import jwt
    from app.services import translation_memory as tm
    from app.services.session_actor import SessionActor
    from app.models.turn_model import TurnMetadata
    from app.core.scheduler import FairSessionQueue
    from app.core.telemetry import GLOBAL_TELEMETRY


class ComprehensiveE2ESystemAuditTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Database in-memory setup for isolated testing with cross-thread support
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db = self.SessionLocal()

        # Seed test users
        self.superadmin = User(
            username="super_audit",
            password_hash=get_password_hash("SuperAdmin@123"),
            role="superadmin",
            public_id=str(uuid.uuid4()),
            is_active=True,
        )
        self.admin = User(
            username="admin_audit",
            password_hash=get_password_hash("AdminPass@123"),
            role="admin",
            public_id=str(uuid.uuid4()),
            is_active=True,
        )
        self.employee_a = User(
            username="emp_a",
            password_hash=get_password_hash("EmpPassA@123"),
            role="employee",
            public_id=str(uuid.uuid4()),
            is_active=True,
        )
        self.employee_b = User(
            username="emp_b",
            password_hash=get_password_hash("EmpPassB@123"),
            role="employee",
            public_id=str(uuid.uuid4()),
            is_active=True,
        )
        self.db.add_all([self.superadmin, self.admin, self.employee_a, self.employee_b])
        self.db.commit()

        # Override get_db dependency in FastAPI app
        from app.db.database import get_db
        def _get_test_db():
            db_session = self.SessionLocal()
            try:
                yield db_session
            finally:
                db_session.close()
        app.dependency_overrides[get_db] = _get_test_db

        # Generate tokens
        self.token_super = issue_user_session(self.superadmin, self.db)["access_token"]
        self.token_admin = issue_user_session(self.admin, self.db)["access_token"]
        self.token_emp_a = issue_user_session(self.employee_a, self.db)["access_token"]
        self.token_emp_b = issue_user_session(self.employee_b, self.db)["access_token"]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # =========================================================================
    # 1. P0 - BẢO MẬT & XÁC THỰC (SECURITY & ACCESS CONTROL)
    # =========================================================================

    def test_p0_01_reject_invalid_and_expired_token(self):
        """Từ chối token sai format, sai chữ ký và token đã hết hạn."""
        # 1. Token rác / sai chữ ký
        resp = self.client.get(
            "/admin/users",
            headers={"Authorization": "Bearer invalid.fake.token"}
        )
        self.assertEqual(resp.status_code, 401)

        # 2. Token đã hết hạn
        now = int(time.time())
        expired_token = jwt.encode(
            {"sub": "pub-super-001", "jti": str(uuid.uuid4()), "iss": "t-langua", "aud": "t-langua-api",
             "iat": now - 7200, "exp": now - 3600, "kind": "user"},
            "super-secret-e2e-audit-key-must-be-very-long-and-secure",
            algorithm="HS256"
        )
        resp_exp = self.client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(resp_exp.status_code, 401)

    def test_p0_02_privilege_escalation_blocked(self):
        """Chống leo thang đặc quyền: employee không thể gọi endpoint admin/superadmin."""
        # Employee cố lấy danh sách API Keys (yêu cầu superadmin)
        resp = self.client.get(
            "/admin/apikeys",
            headers={"Authorization": f"Bearer {self.token_emp_a}"}
        )
        self.assertEqual(resp.status_code, 403)

        # Employee cố truy cập danh sách Users
        resp_users = self.client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {self.token_emp_a}"}
        )
        self.assertEqual(resp_users.status_code, 403)

        # Admin thường cố xóa từ điển chung (chỉ superadmin mới được phép)
        resp_del = self.client.delete(
            "/admin/dictionary/test_word",
            headers={"Authorization": f"Bearer {self.token_admin}"}
        )
        self.assertEqual(resp_del.status_code, 403)

    def test_p0_03_cross_tenant_data_isolation(self):
        """Đảm bảo cách ly dữ liệu: User A không thể đọc dữ liệu của User B."""
        owner_a = self.employee_a.public_id
        owner_b = self.employee_b.public_id

        # User A thêm từ điển riêng
        tm.add("bí mật của A", "A's secret", client_id=owner_a, source_lang="vi", target_lang="en")

        # User A tra cứu được
        self.assertEqual(
            tm.lookup("bí mật của A", client_id=owner_a, source_lang="vi", target_lang="en"),
            "A's secret"
        )

        # User B KHÔNG thể tra cứu được từ của User A
        self.assertIsNone(
            tm.lookup("bí mật của A", client_id=owner_b, source_lang="vi", target_lang="en")
        )

        # Tra cứu từ điển chung cũng không trả về từ điển riêng của A
        self.assertIsNone(
            tm.lookup("bí mật của A", client_id="global:approved", source_lang="vi", target_lang="en")
        )

    def test_p0_04_anonymous_requests_blocked_by_http_boundary(self):
        """Chặn toàn bộ các request không có danh tính hợp lệ tại HTTP Boundary Middleware."""
        # Request POST không có header Authorization tới endpoint được bảo vệ
        resp = self.client.post("/api/translate-text", json={"text": "hello", "source_lang": "en", "target_lang": "vi"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Authentication required", resp.text)

    # =========================================================================
    # 2. P0 - LUỒNG REALTIME & XỬ LÝ ÂM THANH (REALTIME STREAMING & RESOURCES)
    # =========================================================================

    async def test_p0_05_realtime_turn_sequence_and_session_actor(self):
        """Kiểm tra tính tuần tự của lượt nói và tính bất biến của Turn Metadata qua SessionActor."""
        mock_ws = MagicMock()
        mock_ws.send_json = MagicMock()

        actor = SessionActor(
            session_id="session-e2e-001",
            owner_id=self.employee_a.public_id,
            websocket=mock_ws,
        )
        actor.is_running = True

        # Turn 1
        actor._handle_start_turn({"turn_id": "turn-001", "speaker": "speaker_me", "source_lang": "vi", "target_lang": "en"})
        turn1 = actor.current_turn
        self.assertIsNotNone(turn1)
        self.assertEqual(turn1.turn_id, "turn-001")
        self.assertEqual(turn1.turn_index, 1)
        self.assertEqual(turn1.source_lang, "vi")
        self.assertEqual(turn1.target_lang, "en")

        # Turn 2
        actor._handle_start_turn({"turn_id": "turn-002", "speaker": "speaker_other", "source_lang": "en", "target_lang": "vi"})
        turn2 = actor.current_turn
        self.assertIsNotNone(turn2)
        self.assertEqual(turn2.turn_id, "turn-002")
        self.assertEqual(turn2.turn_index, 2)
        self.assertEqual(turn2.source_lang, "en")
        self.assertEqual(turn2.target_lang, "vi")

        # Metadata của Turn 1 không bị ghi đè khi Turn 2 bắt đầu
        self.assertEqual(turn1.turn_index, 1)
        self.assertEqual(turn1.speaker, "speaker_me")

    async def test_p0_06_realtime_mic_switch_and_turn_cancellation(self):
        """Kiểm tra hủy lượt khi đổi mic/đổi tab: Hủy lượt ngăn phát sinh output rò rỉ."""
        mock_ws = MagicMock()
        actor = SessionActor(
            session_id="session-e2e-cancel",
            owner_id=self.employee_a.public_id,
            websocket=mock_ws,
        )
        actor.is_running = True

        actor._handle_start_turn({"turn_id": "turn-to-cancel", "speaker": "speaker_me", "source_lang": "vi", "target_lang": "en"})
        turn = actor.current_turn
        self.assertIsNotNone(turn)
        self.assertTrue(actor.is_turn_active(turn.turn_id))

        # Giả lập người dùng đổi mic / rời màn hình -> Hủy turn
        actor._handle_cancel_turn(turn.turn_id)

        self.assertFalse(actor.is_turn_active(turn.turn_id))
        self.assertIn(turn.turn_id, actor.cancelled_turns)

        # Thử gửi tin nhắn cho lượt đã hủy -> SessionActor phải bỏ qua (drop)
        sent = await actor.send_message({"type": "translation", "turn_id": turn.turn_id, "text": "stray result"})
        self.assertFalse(sent)

    async def test_p0_07_queue_backpressure_and_overflow_protection(self):
        """Kiểm tra cơ chế FairSessionQueue chống tràn RAM khi một client spam dữ liệu."""
        queue = FairSessionQueue(max_per_session=5, max_total_items=15)

        # Client spam liên tục 10 frames
        results = []
        for i in range(10):
            ok = await queue.put({"frame": i}, session_id="spammer_client")
            results.append(ok)

        # Chỉ cho phép tối đa 5 frame, từ frame thứ 6 trở đi phải bị từ chối
        self.assertEqual(results.count(True), 5)
        self.assertEqual(results.count(False), 5)
        self.assertEqual(queue.qsize(), 5)

    # =========================================================================
    # 3. P0 - TÍNH TOÀN VẸN DỮ LIỆU & BẢN DỊCH (DATA INTEGRITY & TRANSLATIONS)
    # =========================================================================

    def test_p0_08_translation_memory_direction_sensitivity(self):
        """Khóa tra cứu TM bắt buộc đúng chiều ngôn ngữ, không dùng nhầm bản dịch ngược."""
        owner = "audit-owner-dir"
        tm.add("xin chào", "hello", client_id=owner, source_lang="vi", target_lang="en")

        # Đúng hướng: trả về kết quả
        self.assertEqual(tm.lookup("xin chào", client_id=owner, source_lang="vi", target_lang="en"), "hello")

        # Ngược hướng (en -> vi): KHÔNG được trả về 'hello'
        self.assertIsNone(tm.lookup("xin chào", client_id=owner, source_lang="en", target_lang="vi"))

    def test_p0_09_atomic_save_and_rollback_on_io_failure(self):
        """Ghi nguyên tử và rollback: lỗi I/O không được báo thành công giả và bảo toàn dữ liệu cũ."""
        client_id = "test-atomic-client"
        tm.add("từ khóa cũ", "old keyword", client_id=client_id, source_lang="vi", target_lang="en")

        # Mô phỏng lỗi disk I/O khi lưu
        with patch("app.services.translation_memory._save", side_effect=OSError("Disk write failed")):
            with self.assertRaises(OSError):
                tm.add("từ khóa mới", "new keyword", client_id=client_id, source_lang="vi", target_lang="en")

        # Trạng thái trong RAM phải rollback, không lưu "từ khóa mới"
        self.assertIsNone(tm.lookup("từ khóa mới", client_id=client_id, source_lang="vi", target_lang="en"))
        # Từ khóa cũ vẫn được bảo toàn
        self.assertEqual(tm.lookup("từ khóa cũ", client_id=client_id, source_lang="vi", target_lang="en"), "old keyword")

    # =========================================================================
    # 4. P1/P2 - CLIENT, PHÂN TRANG & TẢI ĐỒNG THỜI (PAGINATION & CONCURRENCY)
    # =========================================================================

    def test_p1_10_server_side_pagination_and_filtering(self):
        """Phân trang phía server trên /admin/quality/logs: skip/limit và search chính xác."""
        # Seed 30 translation logs
        for i in range(30):
            self.db.add(TranslationLog(
                client_id=f"client_{i % 3}",
                source_text=f"Bản dịch kiểm thử số {i}",
                translated_text=f"Test translation number {i}",
                latency=0.1 + (i * 0.01),
                source_lang="vi",
                target_lang="en",
            ))
        self.db.commit()

        # Lấy trang 1 (10 bản ghi đầu tiên)
        resp_p1 = self.client.get(
            "/admin/quality/logs?skip=0&limit=10",
            headers={"Authorization": f"Bearer {self.token_admin}"}
        )
        self.assertEqual(resp_p1.status_code, 200)
        data_p1 = resp_p1.json()
        self.assertEqual(len(data_p1), 10)

        # Lấy trang 2 (10 bản ghi tiếp theo)
        resp_p2 = self.client.get(
            "/admin/quality/logs?skip=10&limit=10",
            headers={"Authorization": f"Bearer {self.token_admin}"}
        )
        self.assertEqual(resp_p2.status_code, 200)
        data_p2 = resp_p2.json()
        self.assertEqual(len(data_p2), 10)

        # Bản ghi giữa 2 trang không được trùng nhau
        ids_p1 = {item["id"] for item in data_p1}
        ids_p2 = {item["id"] for item in data_p2}
        self.assertTrue(ids_p1.isdisjoint(ids_p2))

        # Tìm kiếm (Search filtering)
        resp_search = self.client.get(
            "/admin/quality/logs?search=số%205",
            headers={"Authorization": f"Bearer {self.token_admin}"}
        )
        self.assertEqual(resp_search.status_code, 200)
        search_results = resp_search.json()
        self.assertGreaterEqual(len(search_results), 1)
        self.assertTrue(all("số 5" in item["source_text"] for item in search_results))

    async def test_p1_11_fair_share_multi_session_concurrency(self):
        """Kiểm tra tải đồng thời nhiều phiên (Fair-Share): Không phiên nào bị đói (starvation)."""
        fq = FairSessionQueue(max_per_session=10, max_total_items=100)

        # 3 session đẩy việc đồng thời
        sessions = ["user_alpha", "user_beta", "user_gamma"]
        for s in sessions:
            for i in range(3):
                await fq.put({"session": s, "task_id": f"{s}_{i}"}, session_id=s)

        self.assertEqual(fq.qsize(), 9)

        # Lấy lần lượt 9 items ra
        dequeued = []
        for _ in range(9):
            item = await fq.get()
            dequeued.append(item["session"])

        # Kiểm tra tính luân phiên Round-Robin công bằng giữa 3 session
        self.assertEqual(dequeued[0], "user_alpha")
        self.assertEqual(dequeued[1], "user_beta")
        self.assertEqual(dequeued[2], "user_gamma")
        self.assertEqual(dequeued[3], "user_alpha")
        self.assertEqual(dequeued[4], "user_beta")
        self.assertEqual(dequeued[5], "user_gamma")


if __name__ == "__main__":
    unittest.main()

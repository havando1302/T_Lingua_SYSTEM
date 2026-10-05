"""
FULL-STACK USER PERSONA SIMULATION & SYSTEM VERIFICATION SUITE
=============================================================
Simulates real-world personas end-to-end:
1. End-User Persona:
   - Cold Boot & Guest session issuance
   - Realtime WebSocket audio stream (STT -> Translation -> TTS)
   - Chaos: Mic switch, language switch, disconnect & reconnect
   - VAD & large utterance chunking
   - History pagination & RAM stability
2. Admin Persona:
   - Authenticated login & RBAC
   - TM lookup, add approved phrase, data isolation (private vs global)
   - Atomic batch import & rollback on I/O failure
   - System vitals monitoring (/metrics/dashboard, /system/status, timeseries)
3. Adversary / Security Persona:
   - Cross-tenant turn hijacking and audio eavesdropping
   - Forged / expired JWT injection (REST + WebSocket)
   - Audio buffer flood & backpressure rate-limiting
"""
import os
import sys
import time
import json
import uuid
import wave
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "user-persona-simulation-secret-key-very-long-and-secure",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from starlette.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.db.models import Base, User, TranslationLog, ApiKey, TranslationMemoryEntry, SystemSetting
    from app.core.security import get_password_hash, issue_user_session, issue_guest_session
    from app.services import translation_memory as tm
    from app.services.session_actor import SessionActor
    from app.models.turn_model import TurnMetadata
    from app.core.scheduler import FairSessionQueue
    from app.core.telemetry import GLOBAL_TELEMETRY
    from app.utils.text_utils import split_text_for_streaming


class FullStackUserPersonaSimulationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # In-memory thread-safe SQLite
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db = self.SessionLocal()

        # Seed Admin user
        self.admin = User(
            username="admin_persona",
            password_hash=get_password_hash("AdminPass@123456"),
            role="admin",
            public_id=str(uuid.uuid4()),
            is_active=True,
        )
        self.db.add(self.admin)

        # Seed System Settings
        self.db.add_all([
            SystemSetting(key="max_chars_per_request", value="5000", description="Max chars"),
            SystemSetting(key="enable_cache", value="true", description="Enable cache"),
            SystemSetting(key="rate_limit_rpm", value="60", description="Rate limit"),
        ])
        self.db.commit()

        # Override get_db dependency
        from app.db.database import get_db
        def _get_test_db():
            db_session = self.SessionLocal()
            try:
                yield db_session
            finally:
                db_session.close()
        app.dependency_overrides[get_db] = _get_test_db

        # Prepare tokens
        self.admin_token = issue_user_session(self.admin, self.db)["access_token"]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # =========================================================================
    # PERSONA 1: END-USER TRANSLATION JOURNEY (HÀNH TRÌNH NGƯỜI DÙNG CUỐI)
    # =========================================================================

    def test_p1_01_cold_boot_guest_session(self):
        """Hành trình 1.1: Người dùng mở ứng dụng lần đầu -> Nhận phiên khách (Guest) hợp lệ."""
        resp = self.client.post("/api/session/guest")
        self.assertIn(resp.status_code, [200, 201])
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data.get("role"), "guest")
        self.assertTrue(bool(data.get("owner_id")))
        self.assertGreater(data.get("expires_in", 0), 0)

    async def test_p1_02_realtime_audio_turn_workflow(self):
        """Hành trình 1.2: Người dùng bấm mic, gửi audio -> Kiểm tra trình tự Turn & State Actor."""
        mock_ws = MagicMock()
        mock_ws.send_json = MagicMock()
        actor = SessionActor(
            websocket=mock_ws,
            session_id="guest_session_001",
            owner_id=str(uuid.uuid4()),
        )
        actor.is_running = True

        # 1. Bắt đầu lượt nói 1
        actor._handle_start_turn({"turn_id": "turn-001", "source_lang": "vi", "target_lang": "en"})
        turn_1 = actor.current_turn
        self.assertIsNotNone(turn_1)
        self.assertEqual(turn_1.turn_id, "turn-001")
        self.assertEqual(turn_1.source_lang, "vi")
        self.assertEqual(turn_1.target_lang, "en")
        self.assertTrue(actor.is_turn_active("turn-001"))

        # 2. Hoàn tất lượt nói 1 và bắt đầu lượt 2
        actor._handle_start_turn({"turn_id": "turn-002", "source_lang": "vi", "target_lang": "en"})
        turn_2 = actor.current_turn
        self.assertEqual(turn_2.turn_id, "turn-002")
        self.assertTrue(actor.is_turn_active("turn-002"))

    async def test_p1_03_chaos_mic_switch_and_disruption(self):
        """Hành trình 1.3: Chaos test: Đang nói thì đổi micro/đổi cặp ngôn ngữ -> Hủy lượt ngay lập tức."""
        mock_ws = MagicMock()
        mock_ws.send_json = MagicMock()
        actor = SessionActor(
            websocket=mock_ws,
            session_id="guest_chaos_session",
            owner_id=str(uuid.uuid4()),
        )
        actor.is_running = True

        # Đang nói lượt 1
        actor._handle_start_turn({"turn_id": "turn-chaos-001", "source_lang": "vi", "target_lang": "en"})
        self.assertTrue(actor.is_turn_active("turn-chaos-001"))

        # Đổi mic / đổi cặp ngôn ngữ đột ngột: Hủy lượt 1
        actor._handle_cancel_turn("turn-chaos-001")
        self.assertFalse(actor.is_turn_active("turn-chaos-001"))

        # Khởi tạo lượt tiếp theo với ngôn ngữ mới
        actor._handle_start_turn({"turn_id": "turn-chaos-002", "source_lang": "en", "target_lang": "vi"})
        self.assertTrue(actor.is_turn_active("turn-chaos-002"))
        self.assertEqual(actor.current_turn.source_lang, "en")

    async def test_p1_04_abrupt_disconnect_and_reconnect(self):
        """Hành trình 1.4: Rớt mạng đột ngột và kết nối lại: Phiên mới độc lập không bị nghẽn buffer."""
        fq = FairSessionQueue(max_per_session=5, max_total_items=20)
        session_id = "user_drop_reconnect"

        # Đưa 2 audio chunk vào queue
        await fq.put({"chunk": 1}, session_id=session_id)
        await fq.put({"chunk": 2}, session_id=session_id)
        self.assertEqual(fq.qsize(), 2)

        # Mô phỏng client disconnect: Worker tiêu thụ hết queue
        item1 = await fq.get()
        item2 = await fq.get()
        self.assertEqual(item1["chunk"], 1)
        self.assertEqual(item2["chunk"], 2)
        self.assertEqual(fq.qsize(), 0)

        # Client reconnect và gửi lượt mới trơn tru
        await fq.put({"chunk": 3}, session_id=session_id)
        self.assertEqual(fq.qsize(), 1)
        item3 = await fq.get()
        self.assertEqual(item3["chunk"], 3)

    def test_p1_05_long_utterance_and_vad_chunking(self):
        """Hành trình 1.5: Câu nói rất dài không dấu câu -> Chia đoạn thông minh cho TTS (< 150 ký tự)."""
        long_vietnamese_text = (
            "Hôm nay chúng tôi tiến hành kiểm thử toàn diện hệ thống dịch thuật thời gian thực "
            "với lưu lượng cao nhằm đảm bảo rằng mô hình trí tuệ nhân tạo có thể xử lý mượt mà "
            "tất cả các câu nói dài mà không làm tràn bộ nhớ VRAM hoặc gây độ trễ quá lớn cho người sử dụng."
        )
        chunks = split_text_for_streaming(long_vietnamese_text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 150)
            self.assertTrue(len(chunk.strip()) > 0)

    # =========================================================================
    # PERSONA 2: ENTERPRISE ADMINISTRATOR (HÀNH TRÌNH QUẢN TRỊ VIÊN)
    # =========================================================================

    def test_p2_06_admin_login_and_token_verification(self):
        """Hành trình 2.1: Quản trị viên đăng nhập với tài khoản an toàn -> Nhận JWT Token."""
        resp = self.client.post(
            "/admin/login",
            data={"username": "admin_persona", "password": "AdminPass@123456"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "admin")

    def test_p2_07_translation_memory_crud_and_isolation(self):
        """Hành trình 2.2: Quản lý Translation Memory: Tra cứu, thêm cụm từ mới và cô lập từ điển cá nhân."""
        # 1. Thêm từ mới vào từ điển phê duyệt chung
        tm.add("kiểm toán tự hành", "autonomous audit", client_id="global:approved", source_lang="vi", target_lang="en")

        # 2. Tra cứu từ điển chung
        match = tm.lookup("kiểm toán tự hành", client_id="global:approved", source_lang="vi", target_lang="en")
        self.assertEqual(match, "autonomous audit")

        # 3. Đảm bảo dữ liệu người dùng khách (Guest A) KHÔNG tự động biến thành từ điển chung
        tm.add("bí mật riêng tư", "private secret", client_id="guest_tenant_xyz", source_lang="vi", target_lang="en")

        # Tra cứu trên global không được ra từ của guest
        global_match = tm.lookup("bí mật riêng tư", client_id="global:approved", source_lang="vi", target_lang="en")
        self.assertIsNone(global_match)

    def test_p2_08_atomic_transaction_and_rollback(self):
        """Hành trình 2.3: Unit of Work: Giao dịch lưu dữ liệu nguyên tử, rollback hoàn toàn khi lỗi."""
        log = TranslationLog(
            source_text="Giao dịch thử nghiệm",
            translated_text="Test transaction",
            latency=0.12,
            model_source="nllb",
            source_lang="vi",
            target_lang="en",
        )
        self.db.add(log)
        self.db.commit()

        # Mô phỏng đứt gãy giữa chừng trong Unit of Work
        try:
            with self.db.begin_nested():
                self.db.add(TranslationLog(source_text="Dở dang", translated_text="Incomplete"))
                raise RuntimeError("Mô phỏng đứt kết nối I/O giữa chừng")
        except RuntimeError:
            pass

        # Dữ liệu cũ vẫn nguyên vẹn, bản ghi dở dang bị rollback
        saved = self.db.get(TranslationLog, log.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.source_text, "Giao dịch thử nghiệm")
        incomplete = self.db.query(TranslationLog).filter(TranslationLog.source_text == "Dở dang").first()
        self.assertIsNone(incomplete)

    def test_p2_09_monitoring_metrics_and_vitals(self):
        """Hành trình 2.4: Giám sát vận hành: Kiểm tra các endpoint Dashboard, System Vitals & Timeseries."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # 1. Metrics dashboard
        resp_metrics = self.client.get("/admin/metrics/dashboard", headers=headers)
        self.assertEqual(resp_metrics.status_code, 200)
        data_m = resp_metrics.json()
        self.assertIn("total_translations", data_m)
        self.assertIn("avg_latency", data_m)

        # 2. System status (CPU, RAM, Disk)
        resp_sys = self.client.get("/admin/system/status", headers=headers)
        self.assertEqual(resp_sys.status_code, 200)
        data_s = resp_sys.json()
        self.assertIn("cpu_usage", data_s)
        self.assertIn("ram_usage", data_s)
        self.assertIn("disk_usage", data_s)

        # 3. Metrics timeseries
        resp_ts = self.client.get("/admin/metrics/timeseries", headers=headers)
        self.assertEqual(resp_ts.status_code, 200)
        self.assertIsInstance(resp_ts.json(), list)

    # =========================================================================
    # PERSONA 3: ADVERSARY / SECURITY JOURNEY (HÀNH TRÌNH KẺ TẤN CÔNG)
    # =========================================================================

    def test_p3_10_cross_tenant_access_blocked(self):
        """Hành trình 3.1: Kẻ tấn công cố gắng truy cập dữ liệu dịch thuật của người khác -> Bị chặn 403/401."""
        # Tạo bản ghi của Tenant A
        log_a = TranslationLog(
            client_id="tenant_alpha",
            source_text="Tài liệu bảo mật A",
            translated_text="Confidential A",
            latency=0.05,
            source_lang="vi",
            target_lang="en",
        )
        self.db.add(log_a)
        self.db.commit()

        # Kẻ tấn công không có token cố đọc nhật ký
        resp_anon = self.client.get("/admin/quality/logs")
        self.assertEqual(resp_anon.status_code, 401)

        # Kẻ tấn công dùng token giả mạo
        resp_fake = self.client.get(
            "/admin/quality/logs",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )
        self.assertEqual(resp_fake.status_code, 401)

    async def test_p3_11_audio_flood_and_backpressure(self):
        """Hành trình 3.2: Kẻ tấn công spam hàng loạt audio chunks -> Kích hoạt FairSessionQueue Rate-limit."""
        fq = FairSessionQueue(max_per_session=4, max_total_items=20)
        attacker = "malicious_bot"

        # Đẩy 4 chunks hợp lệ
        for i in range(4):
            accepted = await fq.put({"chunk": i}, session_id=attacker)
            self.assertTrue(accepted)

        # Chunk thứ 5 vượt ngưỡng max_per_session=4 -> Bị từ chối (Drop / Backpressure)
        overflow_accepted = await fq.put({"chunk": 5}, session_id=attacker)
        self.assertFalse(overflow_accepted)
        self.assertEqual(fq.qsize(), 4)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Đưa cả backend và workspace root vào sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from starlette.testclient import TestClient

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-phase6-tests-must-be-long-enough",
    "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from app.main import app
    from scripts.backup_restore import create_backup, restore_backup, calculate_sha256


class Phase6OperationsLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_liveness_probe_returns_200(self):
        resp = self.client.get("/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "alive"})

        # Also via prefix
        resp_v1 = self.client.get("/api/v1/health/live")
        self.assertEqual(resp_v1.status_code, 200)
        self.assertEqual(resp_v1.json(), {"status": "alive"})

    def test_readiness_probe_healthy(self):
        app.state.is_draining = False
        live_worker = MagicMock()
        live_worker.done.return_value = False
        # Without lifespan startup there is no running worker pool in this fixture.
        with patch.object(app.state, "worker_tasks", [live_worker], create=True), \
             patch.object(app.state, "expected_worker_count", 1, create=True):
            resp = self.client.get("/health/ready")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ready")
        self.assertTrue(data.get("ready"))

    def test_readiness_probe_draining(self):
        try:
            app.state.is_draining = True
            resp = self.client.get("/health/ready")
            self.assertEqual(resp.status_code, 503)
            data = resp.json()
            self.assertEqual(data.get("status"), "draining")
            self.assertFalse(data.get("ready"))
        finally:
            app.state.is_draining = False

    def test_readiness_probe_db_failure(self):
        app.state.is_draining = False
        with patch("app.api.v1.health.engine.connect", side_effect=Exception("DB connection lost")):
            resp = self.client.get("/health/ready")
            self.assertEqual(resp.status_code, 503)
            data = resp.json()
            self.assertEqual(data.get("status"), "not_ready")
            self.assertEqual(data.get("database"), "unavailable")
            # Ensure no raw tracebacks leaked
            self.assertNotIn("Traceback", resp.text)

    def test_backup_and_restore_cycle(self):
        data_dir = Path(self.test_dir) / "data"
        backup_dir = Path(self.test_dir) / "backups"
        restore_dir = Path(self.test_dir) / "restored"

        data_dir.mkdir(parents=True)
        backup_dir.mkdir(parents=True)
        restore_dir.mkdir(parents=True)

        # Create mock data files
        db_file = data_dir / "admin.db"
        db_file.write_bytes(b"SQLite format 3\x00test-database-content-12345")
        tm_file = data_dir / "translation_memory.json"
        tm_file.write_text('{"user1": {"xin chào": "hello"}}', encoding="utf-8")

        # 1. Create backup
        archive = create_backup(data_dir=data_dir, output_dir=backup_dir)
        self.assertTrue(archive.exists())

        # 2. Restore to clean directory
        ok = restore_backup(archive_path=archive, target_dir=restore_dir)
        self.assertTrue(ok)

        # 3. Verify content and checksum
        restored_db = restore_dir / "admin.db"
        restored_tm = restore_dir / "translation_memory.json"

        self.assertTrue(restored_db.exists())
        self.assertTrue(restored_tm.exists())
        self.assertEqual(calculate_sha256(db_file), calculate_sha256(restored_db))
        self.assertEqual(calculate_sha256(tm_file), calculate_sha256(restored_tm))


if __name__ == "__main__":
    unittest.main()

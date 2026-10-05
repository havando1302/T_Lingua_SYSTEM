import os
from pathlib import Path
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pyotp
from cryptography.fernet import Fernet

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "admin-extension-test-secret-that-is-long-enough",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
    "CORS_ORIGINS": "http://localhost:5173", "TRUSTED_HOSTS": "testserver",
}


with patch.dict(os.environ, TEST_ENV):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.database import get_db
    from app.db.models import ApiKey, AuditLog, AuthSession, Base, ModelDeployment, QualityReview, SystemSetting, TrainingDataset, TrainingJob, TranslationLog, User
    from app.core.auth_settings import AuthSettings
    from app.core import security
    from app.core.security import get_password_hash, issue_api_key, issue_user_session
    from app.services import training_control


class AdminExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.training_tmp = tempfile.TemporaryDirectory()
        self.training_root_patch = patch.object(training_control, "CONTROL_ROOT", Path(self.training_tmp.name))
        self.training_root_patch.start()
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db = self.Session()
        self.superadmin = User(
            username="extension-root", password_hash=get_password_hash("ExtensionRoot@123"),
            role="superadmin", public_id=str(uuid.uuid4()), is_active=True,
        )
        self.employee = User(
            username="extension-user", password_hash=get_password_hash("ExtensionUser@123"),
            role="employee", public_id=str(uuid.uuid4()), is_active=True,
        )
        self.db.add_all([self.superadmin, self.employee])
        self.db.commit()
        token = issue_user_session(self.superadmin, self.db)["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}
        employee_token = issue_user_session(self.employee, self.db)["access_token"]
        self.employee_headers = {"Authorization": f"Bearer {employee_token}"}

        def override_db():
            session = self.Session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.training_root_patch.stop()
        self.training_tmp.cleanup()

    def test_user_update_session_reset_and_audit(self):
        response = self.client.patch(
            f"/admin/users/{self.employee.id}", headers=self.headers,
            json={"role": "admin", "is_active": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["role"], "admin")
        response = self.client.post(
            f"/admin/users/{self.employee.id}/reset-sessions", headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        audit = self.client.get("/admin/audit", headers=self.headers).json()
        self.assertTrue(any(row["action"] == "user.update" for row in audit))
        self.assertTrue(any(row["action"] == "user.sessions_revoke" for row in audit))

    def test_user_management_errors_are_specific_and_consistent(self):
        duplicate = self.client.post(
            "/admin/users", headers=self.headers,
            json={"username": self.employee.username, "password": "AnotherPassword@123", "role": "employee"},
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.text)
        self.assertEqual(duplicate.json()["detail"], "Tên đăng nhập đã tồn tại")

        invalid_password = self.client.post(
            "/admin/users", headers=self.headers,
            json={"username": "new-employee", "password": "short", "role": "employee"},
        )
        self.assertEqual(invalid_password.status_code, 422, invalid_password.text)
        issue = invalid_password.json()["detail"][0]
        self.assertEqual(issue["loc"][-1], "password")
        self.assertEqual(issue["type"], "string_too_short")

        missing = self.client.patch(
            "/admin/users/999999", headers=self.headers,
            json={"role": "employee"},
        )
        self.assertEqual(missing.status_code, 404, missing.text)
        self.assertEqual(missing.json()["detail"], "Không tìm thấy tài khoản")

        current_account = self.client.patch(
            f"/admin/users/{self.superadmin.id}", headers=self.headers,
            json={"role": "admin"},
        )
        self.assertEqual(current_account.status_code, 403, current_account.text)
        self.assertEqual(
            current_account.json()["detail"],
            "Không thể vô hiệu hóa hoặc đổi quyền của tài khoản đang đăng nhập",
        )

        protected_account = self.client.delete(
            f"/admin/users/{self.superadmin.id}", headers=self.headers,
        )
        self.assertEqual(protected_account.status_code, 403, protected_account.text)
        self.assertEqual(
            protected_account.json()["detail"],
            "Không thể vô hiệu hóa tài khoản quản trị cấp cao",
        )

        missing_reset = self.client.post(
            "/admin/users/999999/reset-sessions", headers=self.headers,
        )
        self.assertEqual(missing_reset.status_code, 404, missing_reset.text)
        self.assertEqual(missing_reset.json()["detail"], "Không tìm thấy tài khoản")

    def test_user_update_patch_is_allowed_by_cors_preflight(self):
        response = self.client.options(
            f"/admin/users/{self.employee.id}",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("PATCH", response.headers.get("access-control-allow-methods", ""))
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

    def test_login_requires_mfa_setup_then_verification_before_session(self):
        settings = AuthSettings(
            _env_file=None,
            APP_ENV="local",
            JWT_SECRET_KEY="mfa-login-test-secret-that-is-long-and-random-enough",
            AUTH_REQUIRE_MFA=True,
            MFA_ENCRYPTION_KEY=Fernet.generate_key().decode(),
        )
        with patch.object(security, "get_auth_settings", return_value=settings):
            first = self.client.post(
                "/admin/login",
                data={"username": "extension-user", "password": "ExtensionUser@123"},
            )
            self.assertEqual(first.status_code, 200, first.text)
            challenge = first.json()
            self.assertEqual(challenge["status"], "mfa_setup_required")
            self.assertTrue(challenge["enrollment_required"])
            self.assertEqual(self.db.query(AuthSession).filter(AuthSession.user_id == self.employee.id).count(), 1)
            # setUp created this account's old non-MFA session; policy makes it unusable
            # and enrollment confirmation revokes it before issuing the new session.

            otp = pyotp.TOTP(challenge["secret"]).now()
            completed = self.client.post(
                "/admin/login",
                data={"username": "extension-user", "password": "ExtensionUser@123", "otp": otp},
            )
            self.assertEqual(completed.status_code, 200, completed.text)
            self.assertIn("access_token", completed.json())
            self.assertTrue(completed.json()["user"]["mfa_enabled"])
            self.db.expire_all()
            self.assertTrue(self.db.get(User, self.employee.id).mfa_enabled)

            prompt = self.client.post(
                "/admin/login",
                data={"username": "extension-user", "password": "ExtensionUser@123"},
            )
            self.assertEqual(prompt.status_code, 200, prompt.text)
            self.assertEqual(prompt.json()["status"], "mfa_required")
            self.assertFalse(prompt.json()["enrollment_required"])
            self.assertNotIn("access_token", prompt.json())

    def test_login_cookie_refresh_and_cookie_only_logout(self):
        self.client.cookies.clear()
        login = self.client.post(
            "/admin/login",
            data={"username": "extension-user", "password": "ExtensionUser@123"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        cookie_header = login.headers.get("set-cookie", "").lower()
        self.assertIn("tlingua_refresh=", cookie_header)
        self.assertIn("httponly", cookie_header)
        self.assertIn("samesite=strict", cookie_header)
        self.assertIn("path=/api/session", cookie_header)

        refreshed = self.client.post("/api/session/refresh")
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertNotEqual(refreshed.json()["access_token"], login.json()["access_token"])
        self.assertEqual(refreshed.json()["user"]["id"], self.employee.id)

        logged_out = self.client.post("/api/session/logout")
        self.assertEqual(logged_out.status_code, 204, logged_out.text)
        self.assertEqual(self.client.post("/api/session/refresh").status_code, 401)
        self.client.cookies.clear()

    def test_api_key_rotation_returns_secret_once_and_revokes_old(self):
        old, _ = issue_api_key(
            self.db, name="mobile", owner_id=self.superadmin.public_id,
            scopes=["translate"], expires_at=datetime.now(timezone.utc) + timedelta(days=20),
            created_by_user_id=self.superadmin.id,
        )
        old_id = old.id
        response = self.client.post(f"/admin/apikeys/{old_id}/rotate", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["key"].startswith("tl_"))
        self.db.expire_all()
        self.assertFalse(self.db.get(ApiKey, old_id).is_active)
        self.assertNotEqual(response.json()["id"], old_id)

    def test_structured_quality_review_and_exports(self):
        log = TranslationLog(
            client_id="synthetic", source_text="Xin chào", translated_text="Hello",
            source_lang="vi", target_lang="en", is_flagged=True,
        )
        self.db.add(log)
        self.db.commit()
        response = self.client.post(
            f"/admin/quality/logs/{log.id}/resolve", headers=self.headers,
            json={
                "corrected_source_text": "Xin chao", "corrected_text": "Hello there",
                "translation_status": "corrected",
                "consent_for_training": True, "pii_status": "clean",
                "use_for_nllb": True,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.query(QualityReview).count(), 1)
        self.db.refresh(log)
        self.assertEqual(log.translated_text, "Hello")
        review = self.db.query(QualityReview).one()
        self.assertEqual(review.corrected_text, "Hello there")
        self.assertEqual(review.corrected_source_text, "Xin chao")
        self.assertTrue(review.use_for_nllb)
        export = self.client.get("/admin/quality/reviews/export", headers=self.headers)
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export.headers["content-type"])
        self.assertIn("adequacy", export.content.decode("utf-8-sig"))
        training = self.client.get("/admin/training/export/nllb", headers=self.headers)
        self.assertEqual(training.status_code, 200, training.text)
        row = __import__("json").loads(training.text)
        self.assertEqual(row["source"], "Xin chao")
        self.assertEqual(row["target"], "Hello there")

    def test_training_export_and_preview_require_data_clearance(self):
        log = TranslationLog(
            client_id="synthetic", source_text="Cam on", translated_text="Thanks",
            source_lang="vie_Latn", target_lang="eng_Latn", is_flagged=True,
        )
        self.db.add(log)
        self.db.commit()
        unresolved = self.client.post(
            f"/admin/quality/logs/{log.id}/resolve", headers=self.headers,
            json={
                "corrected_source_text": "Cam on", "corrected_text": "Thanks",
                "translation_status": "correct", "use_for_nllb": True,
            },
        )
        self.assertEqual(unresolved.status_code, 200, unresolved.text)
        blocked_export = self.client.get("/admin/training/export/nllb", headers=self.headers)
        self.assertEqual(blocked_export.text, "")

        approved = self.client.post(
            f"/admin/quality/logs/{log.id}/resolve", headers=self.headers,
            json={
                "corrected_source_text": "Cam on", "corrected_text": "Thanks",
                "translation_status": "correct", "consent_for_training": True,
                "pii_status": "redacted", "use_for_nllb": True,
            },
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        exported = self.client.get("/admin/training/export/nllb", headers=self.headers)
        row = __import__("json").loads(exported.text)
        self.assertEqual((row["source_lang"], row["target_lang"]), ("vi", "en"))
        preview = self.client.post(
            "/admin/training/datasets/preview-from-qa", headers=self.headers,
            json={"name": "preview-data", "version": "v1", "task": "nllb", "language": "all"},
        )
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["eligible"], 1)

    def test_dictionary_export_is_csv_and_does_not_expose_secrets(self):
        rows = [{
            "source_text": "xin chào", "translated_text": "hello",
            "source_lang": "vi", "target_lang": "en",
        }]
        with patch("app.api.admin_routes.tm.get_entries", return_value=rows):
            response = self.client.get("/admin/dictionary/export", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8-sig")
        self.assertIn("source_text,translated_text,source_lang,target_lang", content)
        self.assertIn("xin chào,hello,vi,en", content)

    def test_employee_portal_permissions_are_useful_but_limited(self):
        qa_log = TranslationLog(
            client_id="qa-client", source_text="Cần kiểm tra", translated_text="Needs review",
            source_lang="vi", target_lang="en", is_flagged=True,
        )
        private_history = TranslationLog(
            client_id="history-client", source_text="Không thuộc QA", translated_text="Not QA",
            source_lang="vi", target_lang="en", is_flagged=False,
        )
        self.db.add_all([qa_log, private_history])
        self.db.commit()

        for path in (
            "/admin/metrics/dashboard",
            "/admin/metrics/timeseries",
            "/admin/metrics/languages",
            "/admin/metrics/pipeline",
            "/admin/metrics/pipeline?time_range=7d",
            "/admin/metrics/pipeline?time_range=all",
            "/admin/metrics/pipeline?start_date=2026-01-01&end_date=2026-01-02",
            "/admin/dictionary",
            "/admin/quality/overview",
        ):
            response = self.client.get(path, headers=self.employee_headers)
            self.assertEqual(response.status_code, 200, f"{path}: {response.text}")
            if "pipeline" in path:
                data = response.json()
                self.assertIn("latencies_ms", data)
                self.assertIn("total_completed", data)

        qa_response = self.client.get("/admin/quality/logs", headers=self.employee_headers)
        self.assertEqual(qa_response.status_code, 200, qa_response.text)
        self.assertEqual([row["id"] for row in qa_response.json()], [qa_log.id])

        reviewed = self.client.post(
            f"/admin/quality/logs/{qa_log.id}/resolve",
            headers=self.employee_headers,
            json={"corrected_text": "Needs a review", "translation_status": "corrected"},
        )
        self.assertEqual(reviewed.status_code, 200, reviewed.text)

        out_of_scope_review = self.client.post(
            f"/admin/quality/logs/{private_history.id}/resolve",
            headers=self.employee_headers,
            json={"corrected_text": "Must stay private", "translation_status": "corrected"},
        )
        self.assertEqual(out_of_scope_review.status_code, 404, out_of_scope_review.text)

        for path in (
            "/admin/system/status",
            "/admin/users",
            "/admin/apikeys",
            "/admin/training/overview",
            "/admin/quality/reviews/export",
        ):
            response = self.client.get(path, headers=self.employee_headers)
            self.assertEqual(response.status_code, 403, f"{path}: {response.text}")

        write_dictionary = self.client.post(
            "/admin/dictionary",
            headers=self.employee_headers,
            json={"source_text": "xin chào", "translated_text": "hello", "source_lang": "vi", "target_lang": "en"},
        )
        self.assertEqual(write_dictionary.status_code, 403, write_dictionary.text)

    def test_model_canary_promote_rollback_and_filtered_audit(self):
        initial = self.client.get("/admin/models/deployments", headers=self.headers)
        self.assertEqual(initial.status_code, 200, initial.text)
        self.assertEqual(len(initial.json()), 4)
        configured = self.client.put(
            "/admin/models/nllb/canary", headers=self.headers,
            json={"model_id": "example/nllb-candidate-v2", "percent": 10},
        )
        self.assertEqual(configured.status_code, 200, configured.text)
        self.assertEqual(configured.json()["canary_percent"], 10)
        promoted = self.client.post("/admin/models/nllb/promote", headers=self.headers)
        self.assertEqual(promoted.status_code, 200, promoted.text)
        self.assertEqual(promoted.json()["active_model"], "example/nllb-candidate-v2")
        rolled_back = self.client.post("/admin/models/nllb/rollback", headers=self.headers)
        self.assertEqual(rolled_back.status_code, 200, rolled_back.text)
        self.assertNotEqual(rolled_back.json()["active_model"], "example/nllb-candidate-v2")
        self.assertEqual(self.db.query(ModelDeployment).count(), 1)
        audit = self.client.get(
            "/admin/audit?actor=extension-root&resource_type=model", headers=self.headers,
        )
        self.assertEqual(audit.status_code, 200, audit.text)
        self.assertEqual(len(audit.json()), 3)

    def test_settings_and_model_validation_errors_are_specific(self):
        self.db.add_all([
            SystemSetting(key="enable_cache", value="true", description="Bộ nhớ đệm"),
            SystemSetting(key="rate_limit_rpm", value="30", description="Giới hạn yêu cầu"),
            SystemSetting(key="max_chars_per_request", value="1000", description="Giới hạn ký tự"),
        ])
        self.db.commit()

        listed = self.client.get("/admin/settings", headers=self.headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual(
            [item["key"] for item in listed.json()],
            ["max_chars_per_request", "rate_limit_rpm", "enable_cache"],
        )

        invalid_setting = self.client.put(
            "/admin/settings/rate_limit_rpm", headers=self.headers, json={"value": "10.5"},
        )
        self.assertEqual(invalid_setting.status_code, 422, invalid_setting.text)
        self.assertIn("số nguyên", invalid_setting.json()["detail"])

        initial = self.client.get("/admin/models/deployments", headers=self.headers).json()
        nllb = next(item for item in initial if item["component"] == "nllb")
        same_as_active = self.client.put(
            "/admin/models/nllb/canary", headers=self.headers,
            json={"model_id": nllb["active_model"], "percent": 10},
        )
        self.assertEqual(same_as_active.status_code, 409, same_as_active.text)
        self.assertIn("phải khác model Active", same_as_active.json()["detail"])

        missing_percent = self.client.put(
            "/admin/models/nllb/canary", headers=self.headers,
            json={"model_id": "example/nllb-v2", "percent": 0},
        )
        self.assertEqual(missing_percent.status_code, 422, missing_percent.text)
        self.assertIn("từ 1% đến 50%", missing_percent.json()["detail"])

        no_canary = self.client.delete("/admin/models/nllb/canary", headers=self.headers)
        self.assertEqual(no_canary.status_code, 409, no_canary.text)
        self.assertEqual(no_canary.json()["detail"], "Chưa có model Canary để hủy")

    def test_training_dataset_validate_freeze_and_queue(self):
        payload = (
            '{"id":"a","source_lang":"vi","target_lang":"en","source":"xin chao","target":"hello","split":"train"}\n'
            '{"id":"b","source_lang":"vi","target_lang":"en","source":"tam biet","target":"goodbye","split":"validation"}\n'
            '{"id":"c","source_lang":"en","target_lang":"vi","source":"thanks","target":"cam on","split":"test"}\n'
        ).encode("utf-8")
        uploaded = self.client.post(
            "/admin/training/datasets/upload", headers=self.headers,
            data={"name": "nllb-test-v1", "version": "v1", "task": "nllb", "rights_confirmed": "true"},
            files={"file": ("dataset.jsonl", payload, "application/x-ndjson")},
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        dataset_id = uploaded.json()["id"]
        validated = self.client.post(
            f"/admin/training/datasets/{dataset_id}/validate", headers=self.headers,
        )
        self.assertEqual(validated.status_code, 200, validated.text)
        self.assertEqual(validated.json()["status"], "validated")
        frozen = self.client.post(
            f"/admin/training/datasets/{dataset_id}/freeze", headers=self.headers,
        )
        self.assertEqual(frozen.status_code, 200, frozen.text)
        self.assertEqual(frozen.json()["status"], "frozen")
        queued = self.client.post(
            "/admin/training/jobs", headers=self.headers,
            json={
                "task": "nllb", "dataset_id": dataset_id, "output_version": "nllb-test-v1",
                "method": "lora", "config": {"runtime": "colab", "batch_size": 1},
            },
        )
        self.assertEqual(queued.status_code, 201, queued.text)
        self.assertEqual(queued.json()["jobs"][0]["status"], "queued")
        job_id = queued.json()["jobs"][0]["id"]
        log = self.client.get(f"/admin/training/jobs/{job_id}/log", headers=self.headers)
        self.assertEqual(log.status_code, 200, log.text)
        self.assertIn("durable training queue", log.text)
        self.assertEqual(self.db.query(TrainingDataset).count(), 1)
        self.assertEqual(self.db.query(TrainingJob).count(), 1)
        manifest = self.client.get(
            f"/admin/training/datasets/{dataset_id}/download?kind=manifest", headers=self.headers,
        )
        self.assertEqual(manifest.status_code, 200, manifest.text)


if __name__ == "__main__":
    unittest.main()

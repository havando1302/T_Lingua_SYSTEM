"""Authentication regression tests using synthetic credentials and temporary databases."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

import bcrypt
from cryptography.fernet import Fernet
from fastapi import HTTPException
from jose import jwt
import pyotp
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


_TEST_ENV = {
    "APP_ENV": "local", "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": secrets.token_urlsafe(48), "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "15",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false", "MFA_ENCRYPTION_KEY": Fernet.generate_key().decode(),
}
# Importing the application DB must never select a developer's live database.
with patch.dict(os.environ, _TEST_ENV):
    from app.core.auth_settings import AuthSettings
    from app.core import security
    from app.db.models import ApiKey, AuthSession, User
    from app.db.database import Base
    from app.db.security_migration import init_security_schema, security_schema_ready


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.settings = AuthSettings(_env_file=None, **_TEST_ENV)
        self.settings_patch = patch.object(security, "get_auth_settings", return_value=self.settings)
        self.settings_patch.start()
        self.engine = create_engine("sqlite:///:memory:")
        init_security_schema(self.engine)
        self.db = sessionmaker(bind=self.engine, expire_on_commit=False)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.settings_patch.stop()

    def user(self, name="tester", role="employee"):
        user = User(username=name, role=role, password_hash=bcrypt.hashpw(b"synthetic-password", bcrypt.gensalt(rounds=4)).decode())
        self.db.add(user)
        self.db.commit()
        return user

    def assert_unauthorized(self, action):
        with self.assertRaises(HTTPException) as caught:
            action()
        self.assertEqual(caught.exception.status_code, 401)

    def test_guest_identity_scopes_and_logout(self):
        first = security.issue_guest_session(self.db)
        second = security.issue_guest_session(self.db)
        self.assertNotEqual(first["owner_id"], second["owner_id"])
        principal = security.authenticate_token(first["access_token"], self.db)
        self.assertEqual(principal.scopes, security.RESOURCE_SCOPES)
        self.assertIsNone(principal.user_id)
        stored = self.db.get(AuthSession, principal.session_id)
        self.assertNotEqual(stored.token_hash, first["access_token"])
        security.revoke_session(principal, self.db)
        self.assert_unauthorized(lambda: security.authenticate_token(first["access_token"], self.db))
        self.assertEqual(security.authenticate_token(second["access_token"], self.db).owner_id, second["owner_id"])

    def test_old_username_tokens_and_unregistered_signed_tokens_fail(self):
        user = self.user()
        old = jwt.encode({"sub": user.username, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
                         self.settings.JWT_SECRET_KEY, algorithm="HS256")
        self.assert_unauthorized(lambda: security.authenticate_token(old, self.db))
        issued = security.issue_user_session(user, self.db)
        claims = security.decode_token(issued["access_token"])
        claims["jti"] = "22222222-2222-4222-8222-222222222222"
        forged = jwt.encode(claims, self.settings.JWT_SECRET_KEY, algorithm="HS256")
        self.assert_unauthorized(lambda: security.authenticate_token(forged, self.db))

    def test_disabled_and_recreated_username_do_not_reactivate_token(self):
        user = self.user()
        old = security.issue_user_session(user, self.db)["access_token"]
        user.is_active = False
        self.db.commit()
        self.assert_unauthorized(lambda: security.authenticate_token(old, self.db))
        self.db.delete(user)
        self.db.commit()
        replacement = self.user()
        replacement.is_active = True
        self.db.commit()
        self.assert_unauthorized(lambda: security.authenticate_token(old, self.db))

    def test_token_version_and_server_expiry_are_enforced(self):
        user = self.user()
        token = security.issue_user_session(user, self.db)["access_token"]
        user.token_version += 1
        self.db.commit()
        self.assert_unauthorized(lambda: security.authenticate_token(token, self.db))
        fresh = security.issue_user_session(user, self.db)["access_token"]
        principal = security.authenticate_token(fresh, self.db)
        stored = self.db.get(AuthSession, principal.session_id)
        stored.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        self.db.commit()
        self.assert_unauthorized(lambda: security.authenticate_token(fresh, self.db))

    def test_refresh_token_renews_access_and_cannot_be_used_as_bearer(self):
        user = self.user()
        access, refresh = security.issue_user_session_pair(user, self.db)
        self.assertEqual(security.authenticate_token(access["access_token"], self.db).user_id, user.id)
        self.assert_unauthorized(lambda: security.authenticate_token(refresh, self.db))

        renewed, renewed_user = security.refresh_user_session(refresh, self.db)
        self.assertEqual(renewed_user.id, user.id)
        self.assertEqual(security.authenticate_token(renewed["access_token"], self.db).user_id, user.id)
        # A stable cookie lets multiple open tabs renew without invalidating each other.
        second, _ = security.refresh_user_session(refresh, self.db)
        self.assertNotEqual(second["access_token"], renewed["access_token"])
        self.assertTrue(security.revoke_refresh_session(refresh, self.db))
        self.assert_unauthorized(lambda: security.refresh_user_session(refresh, self.db))

    def test_api_key_stores_only_digest_and_is_scoped_revocable(self):
        user = self.user()
        record, raw = security.issue_api_key(self.db, name="synthetic", owner_id=user.public_id,
                                           scopes=["translate"], expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                                           created_by_user_id=user.id)
        self.assertEqual(record.key_hash, hashlib.sha256(raw.encode()).hexdigest())
        self.assertNotIn(raw, record.key)
        principal = security.authenticate_token(raw, self.db)
        self.assertEqual(principal.scopes, frozenset({"translate"}))
        self.assertEqual(principal.role, "api_key")
        with self.assertRaises(HTTPException) as caught:
            security.get_current_user(principal, self.db)
        self.assertEqual(caught.exception.status_code, 403)
        security.revoke_session(principal, self.db)
        self.assert_unauthorized(lambda: security.authenticate_token(raw, self.db))

    def test_api_key_creator_disable_and_user_recovery_revoke_keys(self):
        user = self.user()
        _, raw = security.issue_api_key(self.db, name="synthetic", owner_id=user.public_id,
                                       scopes=["audio"], expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                                       created_by_user_id=user.id)
        user.is_active = False
        self.db.commit()
        self.assert_unauthorized(lambda: security.authenticate_token(raw, self.db))
        user.is_active = True
        security.revoke_user_sessions(user, self.db)
        self.assert_unauthorized(lambda: security.authenticate_token(raw, self.db))

    def test_privileged_mfa_enrollment_replay_and_escalation(self):
        self.settings.AUTH_REQUIRE_MFA = True
        user = self.user(role="admin")
        with self.assertRaises(HTTPException):
            security.issue_user_session(user, self.db)
        with self.assertRaises(HTTPException):
            security.verify_user_mfa(user, None, self.db)
        seed = pyotp.random_base32()
        user.mfa_secret_encrypted = security.encrypt_mfa_secret(seed)
        self.assertNotIn(seed, user.mfa_secret_encrypted)
        user.mfa_enabled = True
        self.db.commit()
        self.assert_unauthorized(lambda: security.verify_user_mfa(user, "١٢٣٤٥٦", self.db))
        otp = pyotp.TOTP(seed).now()
        self.assertTrue(security.verify_user_mfa(user, otp, self.db))
        self.assert_unauthorized(lambda: security.verify_user_mfa(user, otp, self.db))
        token = security.issue_user_session(user, self.db, mfa_verified=True)["access_token"]
        self.assertTrue(security.authenticate_token(token, self.db).mfa_verified)
        employee = self.user("second", "employee")
        with self.assertRaises(HTTPException):
            security.issue_user_session(employee, self.db)
        self.settings.AUTH_REQUIRE_MFA = False
        old = security.issue_user_session(employee, self.db)["access_token"]
        self.settings.AUTH_REQUIRE_MFA = True
        self.assert_unauthorized(lambda: security.authenticate_token(old, self.db))

    def test_pending_mfa_enrollment_is_required_before_session_issue(self):
        self.settings.AUTH_REQUIRE_MFA = True
        user = self.user(role="employee")
        challenge = security.begin_user_mfa_enrollment(user, self.db)
        self.assertEqual(challenge["status"], "mfa_setup_required")
        self.assertEqual(challenge["account_name"], user.username)
        self.assertIn("otpauth://totp/", challenge["provisioning_uri"])
        self.assertNotIn(challenge["secret"], user.mfa_secret_encrypted)
        with self.assertRaises(HTTPException):
            security.issue_user_session(user, self.db)

        otp = pyotp.TOTP(challenge["secret"]).now()
        self.assertTrue(security.complete_user_mfa_enrollment(user, otp, self.db))
        self.assertTrue(user.mfa_enabled)
        session = security.issue_user_session(user, self.db, mfa_verified=True)
        self.assertTrue(security.authenticate_token(session["access_token"], self.db).mfa_verified)
        self.assert_unauthorized(lambda: security.verify_user_mfa(user, otp, self.db))

    def test_bad_scope_sets_and_overlong_credentials_are_rejected(self):
        user = self.user()
        with self.assertRaises(ValueError):
            security.issue_api_key(self.db, name="bad", owner_id=user.public_id, scopes=["admin"],
                                   expires_at=datetime.now(timezone.utc) + timedelta(days=1))
        self.assert_unauthorized(lambda: security.authenticate_token("a" * 4097, self.db))
        self.assert_unauthorized(lambda: security.authenticate_token(None, self.db))

    def test_guest_capacity_and_expired_session_cleanup(self):
        self.settings.AUTH_MAX_ACTIVE_GUEST_SESSIONS = 1
        first = security.issue_guest_session(self.db)["access_token"]
        with self.assertRaises(HTTPException) as caught:
            security.issue_guest_session(self.db)
        self.assertEqual(caught.exception.status_code, 503)
        principal = security.authenticate_token(first, self.db)
        stored = self.db.get(AuthSession, principal.session_id)
        stored.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        self.db.commit()
        replacement = security.issue_guest_session(self.db)
        self.assertNotEqual(replacement["owner_id"], principal.owner_id)
        self.assertEqual(self.db.query(AuthSession).count(), 1)
        self.assert_unauthorized(lambda: security.authenticate_token(first, self.db))

    def test_malformed_signed_claims_are_unauthorized(self):
        valid = security.issue_guest_session(self.db)["access_token"]
        original = security.decode_token(valid)
        for key, value in (("sub", []), ("jti", {}), ("kind", "legacy"), ("sub", "username")):
            claims = dict(original)
            claims[key] = value
            token = jwt.encode(claims, self.settings.JWT_SECRET_KEY, algorithm="HS256")
            self.assert_unauthorized(lambda: security.authenticate_token(token, self.db))


class ConfigurationTests(unittest.TestCase):
    def test_production_security_gates_and_error_redaction(self):
        common = dict(_env_file=None, APP_ENV="production", JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
                      AUTH_REQUIRE_PRIVILEGED_MFA=True, MFA_ENCRYPTION_KEY=Fernet.generate_key().decode())
        for secret in ("", "change-me-in-production", "a" * 48):
            with self.assertRaises(ValueError) as caught:
                AuthSettings(**common, JWT_SECRET_KEY=secret)
            if secret:
                self.assertNotIn(secret, str(caught.exception))
        with self.assertRaises(ValueError):
            AuthSettings(_env_file=None, APP_ENV="production", JWT_SECRET_KEY=secrets.token_urlsafe(48),
                         AUTH_REQUIRE_PRIVILEGED_MFA=False, MFA_ENCRYPTION_KEY=Fernet.generate_key().decode(),
                         JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15)
        with self.assertRaises(ValueError):
            AuthSettings(_env_file=None, APP_ENV="colab", JWT_SECRET_KEY="", JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15)
        with self.assertRaises(ValueError):
            AuthSettings(_env_file=None, APP_ENV="unknown", JWT_SECRET_KEY=secrets.token_urlsafe(48),
                         JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15)


class MigrationTests(unittest.TestCase):
    def test_realtime_audio_migration_makes_reviewer_uploader_optional(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE training_audio_assets"))
                connection.execute(text(
                    "CREATE TABLE training_audio_assets ("
                    "id VARCHAR(36) NOT NULL PRIMARY KEY, translation_log_id INTEGER NOT NULL UNIQUE, "
                    "file_name VARCHAR(40) NOT NULL UNIQUE, sha256 VARCHAR(64) NOT NULL, "
                    "duration_ms INTEGER NOT NULL, sample_rate INTEGER NOT NULL, channels INTEGER NOT NULL, "
                    "uploaded_by_user_id INTEGER NOT NULL, created_at DATETIME NOT NULL)"
                ))
            init_security_schema(engine)
            columns = {column["name"]: column for column in inspect(engine).get_columns("training_audio_assets")}
            self.assertTrue(columns["uploaded_by_user_id"]["nullable"])
        finally:
            engine.dispose()

    def test_legacy_data_preserved_keys_retired_default_account_disabled_and_rerun_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            engine = create_engine("sqlite:///" + (Path(temporary) / "audit.db").as_posix())
            try:
                password = bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=4)).decode()
                with engine.begin() as connection:
                    connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT NOT NULL, role TEXT, created_at DATETIME)"))
                    connection.execute(text("CREATE TABLE api_keys (id INTEGER PRIMARY KEY, name TEXT, key TEXT UNIQUE NOT NULL, is_active BOOLEAN, created_at DATETIME)"))
                    connection.execute(text("INSERT INTO users(id,username,password_hash,role) VALUES (1,'admin',:password,'superadmin')"), {"password": password})
                    connection.execute(text("INSERT INTO api_keys(id,name,key,is_active) VALUES (1,'legacy','synthetic-legacy-key',1)"))
                result = init_security_schema(engine)
                self.assertTrue(result["default_admin_disabled"])
                self.assertEqual(result["legacy_keys_retired"], 1)
                self.assertTrue(security_schema_ready(engine))
                with engine.connect() as connection:
                    user = connection.execute(text("SELECT * FROM users")).mappings().one()
                    key = connection.execute(text("SELECT * FROM api_keys")).mappings().one()
                self.assertEqual(user["password_hash"], password)
                self.assertEqual(user["is_active"], 0)
                self.assertEqual(key["is_active"], 0)
                self.assertNotIn("synthetic-legacy-key", key["key"])
                self.assertEqual(key["key_hash"], hashlib.sha256(b"synthetic-legacy-key").hexdigest())
                self.assertFalse(init_security_schema(engine)["applied"])
                with engine.connect() as connection:
                    self.assertEqual(connection.execute(text("SELECT public_id FROM users WHERE id=1")).scalar(), user["public_id"])
                    self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM api_keys")).scalar(), 1)
            finally:
                engine.dispose()

    def test_custom_admin_password_is_preserved_and_kept_active(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            password = bcrypt.hashpw(b"custom-long-password", bcrypt.gensalt(rounds=4)).decode()
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT NOT NULL, role TEXT, created_at DATETIME)"))
                connection.execute(text("INSERT INTO users(id,username,password_hash,role) VALUES (1,'admin',:password,'superadmin')"), {"password": password})
            self.assertFalse(init_security_schema(engine)["default_admin_disabled"])
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT is_active FROM users WHERE id=1")).scalar(), 1)
                self.assertEqual(connection.execute(text("SELECT password_hash FROM users WHERE id=1")).scalar(), password)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()

"""Real HTTP routes and security dependencies against isolated SQLite/TM fixtures."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

_REPO = Path(__file__).resolve().parents[3]


class ApiOptimizationProcessTests(unittest.TestCase):
    def test_api_optimization_contracts_in_isolated_process(self):
        with tempfile.TemporaryDirectory(prefix="tlangua-api-regression-") as directory:
            result = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--isolated"],
                cwd=directory,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "APP_ENV": "local",
                     "DATABASE_URL": "sqlite:///:memory:",
                     "JWT_SECRET_KEY": "regression-only-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                     "AUTH_REQUIRE_PRIVILEGED_MFA": "false", "AUTH_GUEST_ENABLED": "true",
                     "RATE_LIMIT_RPM": "600"},
                capture_output=True, text=True, timeout=90,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def isolated_suite():
    import contextlib
    from datetime import datetime, timedelta, timezone
    import io
    import json
    import types
    from urllib.parse import quote
    from unittest.mock import patch
    import wave

    sys.path.insert(0, str(_REPO / "backend"))
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy.pool import StaticPool

    # Only persistence construction is injected. Every route uses the real JWT,
    # scope, owner and role dependencies; no authentication dependency is bypassed.
    fake_db = types.ModuleType("app.db.database")
    fake_db.Base = declarative_base()
    fake_db.get_db = lambda: None
    sys.modules["app.db.database"] = fake_db
    live_tm = os.path.normcase(str(_REPO / "backend/data/translation_memory.json"))
    exists = os.path.exists
    def isolated_exists(path):
        return False if os.path.normcase(os.path.abspath(path)) == live_tm else exists(path)
    with patch("os.path.exists", side_effect=isolated_exists):
        from app.services import translation_memory as tm

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import admin_routes as admin, auth_routes, routes as api
    from app.core import access_policy, security
    from app.db.audio_model import AudioAsset
    from app.db.models import ApiKey, SystemSetting, TranslationLog, User
    from app.services import audio_storage
    from app.services.translation_cache import GLOBAL_TRANSLATION_CACHE

    class ApiOptimizationTests(unittest.TestCase):
        def setUp(self):
            self.stack = contextlib.ExitStack()
            self.addCleanup(self.stack.close)
            self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="api-case-")))
            self.tm_path = self.temp / "translation_memory.json"
            for name in ("_memory", "_guest_memory", "_guest_expiry"):
                self.stack.enter_context(patch.object(tm, name, {}))
            self.stack.enter_context(patch.object(tm, "_TM_FILE", str(self.tm_path)))
            self.stack.enter_context(patch.object(tm, "_DATA_DIR", str(self.temp)))
            self.stack.enter_context(patch.object(audio_storage, "SECURE_OUTPUT_DIR", self.temp / "outputs"))
            self.stack.enter_context(patch.object(api, "SECURE_TEMP_DIR", self.temp / "uploads"))
            self.stack.enter_context(patch.object(audio_storage, "SECURE_TEMP_DIR", self.temp / "uploads"))
            limiter = access_policy.RateLimiter()
            self.stack.enter_context(patch.object(access_policy, "rate_limiter", limiter))
            self.stack.enter_context(patch.object(admin, "rate_limiter", limiter))
            GLOBAL_TRANSLATION_CACHE.clear()
            self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
            self.stack.callback(self.engine.dispose)
            fake_db.Base.metadata.create_all(self.engine)
            self.db = sessionmaker(bind=self.engine)()
            self.stack.callback(self.db.close)
            self.users = {}
            for role in ("superadmin", "admin", "employee", "otheremployee"):
                user = User(username=role, password_hash="unused-synthetic-password-hash",
                            role="employee" if role == "otheremployee" else role)
                self.db.add(user)
                self.users[role] = user
            self.db.add_all([
                SystemSetting(key="enable_cache", value="true"),
                SystemSetting(key="max_chars_per_request", value="5000"),
                SystemSetting(key="rate_limit_rpm", value="600"),
            ])
            self.db.commit()
            self.headers = {
                role: {"Authorization": "Bearer " + security.issue_user_session(user, self.db)["access_token"]}
                for role, user in self.users.items()
            }
            self.app = FastAPI()
            self.app.include_router(admin.router)
            self.app.include_router(api.router)
            self.app.include_router(auth_routes.router)
            self.app.dependency_overrides[fake_db.get_db] = lambda: self.db
            self.client = self.stack.enter_context(TestClient(self.app))

        def request(self, method, path, role="superadmin", **kwargs):
            return self.client.request(method, path, headers=self.headers[role], **kwargs)

        def add_global(self, source, target, source_lang="en", target_lang="vi"):
            tm.add(source, target, "global:approved", source_lang=source_lang, target_lang=target_lang)

        def assert_utc(self, value, expected):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            self.assertEqual(parsed.utcoffset(), timedelta(0))
            self.assertEqual(parsed.replace(tzinfo=None), expected)

        def test_flag_preserves_en_vi_and_owner_then_serializes_utc(self):
            response = self.request("POST", "/api/flag-translation", role="employee", json={
                "source_text": "hello", "translated_text": "sai",
                "source_lang": "eng_Latn", "target_lang": "vie_Latn",
            })
            self.assertEqual(response.status_code, 200, response.text)
            log = self.db.query(TranslationLog).one()
            self.assertEqual((log.source_lang, log.target_lang), ("en", "vi"))
            self.assertEqual(log.client_id, self.users["employee"].public_id)
            self.assertTrue(log.is_flagged)
            response = self.request("GET", "/admin/quality/logs", role="admin", params={"qa_only": True})
            self.assertEqual(response.status_code, 200, response.text)
            self.assert_utc(response.json()[0]["created_at"], log.created_at)

        def test_user_pagination_and_search_treat_percent_underscore_backslash_literally(self):
            names = ["finder_%", "finderXY", "finder_", "finder%", "finder\\tail"]
            self.db.add_all([User(username=name, password_hash="unused", role="employee") for name in names])
            self.db.commit()
            pages = [self.request("GET", "/admin/users", params={"search": "finder", "limit": 2, "skip": skip}).json()
                     for skip in (0, 2, 4)]
            found = [row["username"] for page in pages for row in page]
            self.assertEqual(len(found), len(set(found)))
            self.assertEqual(set(found), set(names))
            for needle, expected in (("%", {"finder_%", "finder%"}), ("_", {"finder_%", "finder_"}), ("\\", {"finder\\tail"})):
                with self.subTest(needle=needle):
                    response = self.request("GET", "/admin/users", params={"search": needle})
                    self.assertEqual({row["username"] for row in response.json()}, expected)

        def test_key_pagination_literal_search_and_utc_metadata(self):
            created = datetime(2026, 1, 1, 12, 34, 56)
            expires = created + timedelta(days=1)
            names = ["key_%", "keyXY", "key_", "key%", "key\\tail"]
            for index, name in enumerate(names):
                self.db.add(ApiKey(name=name, key=f"redacted:{index}", key_prefix=f"prefix{index}",
                                   scopes='["translate"]', owner_id=self.users["superadmin"].public_id,
                                   created_at=created, expires_at=expires))
            self.db.commit()
            pages = [self.request("GET", "/admin/apikeys", params={"search": "key", "limit": 2, "skip": skip}).json()
                     for skip in (0, 2, 4)]
            rows = [row for page in pages for row in page]
            self.assertEqual({row["name"] for row in rows}, set(names))
            self.assertEqual(len(rows), len(names))
            for row in rows:
                self.assertNotIn("key", row)
                self.assertNotIn("key_hash", row)
                self.assert_utc(row["created_at"], created)
                self.assert_utc(row["expires_at"], expires)
            for needle, expected in (("%", {"key_%", "key%"}), ("_", {"key_%", "key_"}), ("\\", {"key\\tail"})):
                response = self.request("GET", "/admin/apikeys", params={"search": needle})
                self.assertEqual({row["name"] for row in response.json()}, expected)

        def test_dictionary_pages_keep_directions_and_literal_search(self):
            self.add_global("same", "forward")
            self.add_global("same", "reverse", "vi", "en")
            self.add_global("literal_%", "matched")
            self.add_global("ordinary", "target_with_underscore")
            self.add_global("third", "not special")
            tm.add("private_%", "secret", self.users["employee"].public_id)
            pages = [self.request("GET", "/admin/dictionary", role="admin", params={"skip": skip, "limit": 2}).json()
                     for skip in (0, 2, 4)]
            rows = [row for page in pages for row in page]
            self.assertEqual(len(rows), 5)
            self.assertEqual(len({(row["source_text"], row["source_lang"], row["target_lang"]) for row in rows}), 5)
            self.assertNotIn("private_%", {row["source_text"] for row in rows})
            for needle, expected in (("%", {"literal_%"}), ("_", {"literal_%", "ordinary"})):
                response = self.request("GET", "/admin/dictionary", role="admin", params={"search": needle})
                self.assertEqual({row["source_text"] for row in response.json()}, expected)
            legacy_query = self.request("GET", "/admin/dictionary", params={"query": "reverse"})
            self.assertEqual([(row["source_lang"], row["target_lang"]) for row in legacy_query.json()], [("vi", "en")])

        def test_review_status_is_filtered_before_pagination_including_legacy_reviewed(self):
            pending, reviewed = set(), set()
            for index in range(10):
                status = index % 3
                log = TranslationLog(client_id="fixture", source_text=f"row{index}", translated_text="target",
                                     is_flagged=status == 0, is_reviewed=status == 1,
                                     model_source="user_flagged" if status == 2 else "nllb_model")
                self.db.add(log)
                self.db.flush()
                (pending if status == 0 else reviewed).add(log.id)
            self.db.add(TranslationLog(client_id="fixture", source_text="unreviewed noise", translated_text="target",
                                       is_flagged=False, is_reviewed=False, model_source="nllb_model"))
            self.db.commit()
            for status, expected in (("pending", pending), ("reviewed", reviewed)):
                pages = [self.request("GET", "/admin/quality/logs", role="admin",
                                      params={"qa_only": True, "review_status": status, "limit": 2, "skip": skip}).json()
                         for skip in range(0, len(expected) + 2, 2)]
                rows = [row for page in pages for row in page]
                self.assertEqual({row["id"] for row in rows}, expected)
                self.assertEqual(len(rows), len(expected))
                self.assertEqual([row["id"] for row in rows], sorted(expected, reverse=True))

        def test_quality_search_wildcards_are_literal(self):
            for source in ("literal_%", "literalXY", "only_", "only%", "path\\term"):
                self.db.add(TranslationLog(client_id="fixture", source_text=source, translated_text="target",
                                           is_flagged=True))
            self.db.commit()
            for needle, expected in (("%", {"literal_%", "only%"}), ("_", {"literal_%", "only_"}), ("\\", {"path\\term"})):
                response = self.request("GET", "/admin/quality/logs", params={"search": needle})
                self.assertEqual({row["source_text"] for row in response.json()}, expected)

        def test_post_delete_handles_slashes_percent_and_reserved_url_characters(self):
            for source in ("path/with spaces?query#fragment%_", "%2Fliteral", "a\\b", "/leading/path"):
                with self.subTest(source=source):
                    added = self.request("POST", "/admin/dictionary", json={
                        "source_text": source, "translated_text": "target", "source_lang": "en", "target_lang": "vi",
                    })
                    self.assertEqual(added.status_code, 200, added.text)
                    deleted = self.request("POST", "/admin/dictionary/delete", json={
                        "source_text": source, "source_lang": "en", "target_lang": "vi",
                    })
                    self.assertEqual(deleted.status_code, 200, deleted.text)
                    self.assertIsNone(tm.lookup(source, "global:approved", "en", "vi"))

        def test_legacy_delete_path_and_exact_direction_delete(self):
            source = "legacy/slash%_value"
            self.add_global(source, "legacy")
            response = self.request("DELETE", "/admin/dictionary/" + quote(source, safe=""))
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIsNone(tm.lookup(source, "global:approved"))
            self.add_global("same", "forward")
            self.add_global("same", "reverse", "vi", "en")
            response = self.request("POST", "/admin/dictionary/delete", json={
                "source_text": "same", "source_lang": "en", "target_lang": "vi",
            })
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIsNone(tm.lookup("same", "global:approved", "en", "vi"))
            self.assertEqual(tm.lookup("same", "global:approved", "vi", "en"), "reverse")

        def test_atomic_csv_import_io_failure_keeps_disk_memory_and_cache(self):
            self.add_global("old", "original")
            before = self.tm_path.read_bytes()
            GLOBAL_TRANSLATION_CACHE.put(self.users["employee"].public_id, "en", "vi", "cached", "valid cache")
            with patch.object(tm.os, "replace", side_effect=OSError("simulated disk failure")):
                response = self.request("POST", "/admin/dictionary/upload",
                                        data={"source_lang": "en", "target_lang": "vi"},
                                        files={"file": ("new.csv", b"first,target one\nsecond,target two", "text/csv")})
            self.assertEqual(response.status_code, 503, response.text)
            self.assertEqual(self.tm_path.read_bytes(), before)
            self.assertEqual(tm.get_all("global:approved"), {"old": "original"})
            self.assertEqual(GLOBAL_TRANSLATION_CACHE.get(self.users["employee"].public_id, "en", "vi", "cached"), "valid cache")
            self.assertEqual(list(self.temp.glob(".tm-*.tmp")), [])

        def test_csv_import_success_persists_direction_and_invalidates_cache(self):
            owner = self.users["employee"].public_id
            GLOBAL_TRANSLATION_CACHE.put(owner, "en", "vi", "hello", "old")
            response = self.request("POST", "/admin/dictionary/upload",
                                    data={"source_lang": "eng_Latn", "target_lang": "vie_Latn"},
                                    files={"file": ("new.csv", b"hello,xin chao\nbye,tam biet", "text/csv")})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["added"], 2)
            self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get(owner, "en", "vi", "hello"))
            tm._load()
            self.assertEqual(tm.lookup("hello", "global:approved", "en", "vi"), "xin chao")
            self.assertIsNone(tm.lookup("hello", "global:approved", "vi", "en"))

        def test_csv_invalid_late_row_does_not_import_valid_early_row(self):
            response = self.request("POST", "/admin/dictionary/upload",
                                    files={"file": ("invalid.csv", b"valid,target\ninvalid, \n", "text/csv")})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(tm.count("global:approved"), 0)
            self.assertFalse(self.tm_path.exists())

        def test_cache_setting_controls_direct_translate_and_invalidates_existing_entries(self):
            owner = self.users["employee"].public_id
            with patch.object(api, "translate_text", return_value={"translated_text": "translated"}) as inference:
                for enabled in (True, False, True):
                    GLOBAL_TRANSLATION_CACHE.put(owner, "en", "vi", "hello", "cached")
                    setting = self.request("PUT", "/admin/settings/enable_cache", json={"value": str(enabled).lower()})
                    self.assertEqual(setting.status_code, 200, setting.text)
                    self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get(owner, "en", "vi", "hello"))
                    response = self.request("POST", "/api/translate-text", role="employee",
                                            json={"text": "hello", "source_lang": "en", "target_lang": "vi"})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertIs(inference.call_args.kwargs["use_cache"], enabled)
                    self.assertEqual(inference.call_args.kwargs["client_id"], owner)
                    self.assertEqual(inference.call_args.kwargs["source_lang"], "eng_Latn")

        def test_audio_upload_passes_language_cache_and_guards_owner_download(self):
            self.request("PUT", "/admin/settings/enable_cache", json={"value": "false"})
            stream = io.BytesIO()
            with wave.open(stream, "wb") as audio:
                audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                audio.writeframes(b"\0\0" * 1600)
            def pipeline(path, **kwargs):
                Path(kwargs["output_path"]).write_bytes(stream.getvalue())
                return {"source_text": "hello", "translated_text": "xin chao"}
            with patch.object(api, "run_pipeline", side_effect=pipeline) as inference:
                response = self.request("POST", "/translate", role="employee",
                                        data={"source_lang": "en", "target_lang": "vi"},
                                        files={"file": ("speech.wav", stream.getvalue(), "audio/wav")})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertFalse(inference.call_args.kwargs["use_cache"])
            self.assertEqual((inference.call_args.kwargs["source_lang"], inference.call_args.kwargs["target_lang"]),
                             ("eng_Latn", "vie_Latn"))
            url = response.json()["audio_url"]
            self.assertEqual(self.request("GET", url, role="employee").status_code, 200)
            self.assertEqual(self.request("GET", url, role="otheremployee").status_code, 404)
            self.assertEqual(list((self.temp / "uploads").glob("*")), [])
            self.assertEqual(self.db.query(AudioAsset).count(), 1)
            self.assertTrue(response.json()["audio_expires_at"].endswith("Z"))

        def test_guest_private_dictionary_owner_checks_and_logout(self):
            tm.add("private", "employee secret", self.users["employee"].public_id)
            guest = self.client.post("/api/session/guest").json()
            self.headers["guest"] = {"Authorization": "Bearer " + guest["access_token"]}
            denied = self.request("GET", "/api/translation-memory", role="guest",
                                  params={"client_id": self.users["employee"].public_id})
            self.assertEqual(denied.status_code, 403, denied.text)
            self.assertEqual(self.request("GET", "/api/translation-memory", role="guest").json()["entries"], {})
            for path in ("/admin/dictionary", "/admin/users", "/admin/apikeys", "/admin/quality/logs"):
                self.assertEqual(self.request("GET", path, role="guest").status_code, 403)
            before = self.tm_path.read_bytes()
            payload = {"source_text": "guest source", "translated_text": "guest private", "source_lang": "en", "target_lang": "vi"}
            self.assertEqual(self.request("POST", "/api/translation-memory", role="guest", json=payload).status_code, 200)
            self.assertEqual(self.tm_path.read_bytes(), before)
            self.assertEqual(self.request("GET", "/api/translation-memory", role="employee").json()["entries"], {"private": "employee secret"})
            spoofed = self.request("POST", "/api/flag-translation", role="guest",
                                  json={**payload, "client_id": self.users["employee"].public_id})
            self.assertEqual(spoofed.status_code, 403)
            self.assertEqual(self.request("POST", "/api/session/logout", role="guest").status_code, 204)
            self.assertIsNone(tm.lookup("guest source", guest["owner_id"]))
            self.assertEqual(self.request("GET", "/api/translation-memory", role="guest").status_code, 401)

        def test_auth_and_pagination_validation_remain_enforced(self):
            for path in ("/admin/dictionary", "/admin/users", "/admin/apikeys", "/admin/quality/logs"):
                self.assertEqual(self.client.get(path).status_code, 401)
                self.assertEqual(self.request("GET", path, role="employee").status_code, 403)
                self.assertEqual(self.request("GET", path, params={"skip": -1}).status_code, 422)
                self.assertEqual(self.request("GET", path, params={"limit": 0}).status_code, 422)
            self.assertEqual(self.request("GET", "/admin/quality/logs", params={"review_status": "unknown"}).status_code, 422)
            self.assertNotIn("app.main", sys.modules)
            self.assertNotIn("app.core.config", sys.modules)
            self.assertNotIn("torch", sys.modules)
            self.assertIs(sys.modules["app.db.database"], fake_db)

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ApiOptimizationTests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if "--isolated" in sys.argv:
        raise SystemExit(isolated_suite())
    unittest.main()

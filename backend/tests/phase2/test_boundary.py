"""Real HTTP/WS boundaries with synthetic identities, temporary storage and fake inference."""
import asyncio
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
import io
import os
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
import wave

import bcrypt
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect


_TEST_ENV = {
    "APP_ENV": "local", "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": secrets.token_urlsafe(48), "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "15",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false", "MFA_ENCRYPTION_KEY": Fernet.generate_key().decode(),
    "CORS_ORIGINS": "http://localhost:5173", "TRUSTED_HOSTS": "testserver",
}
_fake_queues = types.ModuleType("app.core.queues")
_fake_queues.GLOBAL_STT_QUEUE = asyncio.Queue(maxsize=20)
_fake_session = types.ModuleType("app.models.session_model")
_fake_session.RealtimeSession = lambda **values: types.SimpleNamespace(
    **values, source_lang="vi", target_lang="eng_Latn", is_running=True
)
_real_exists = os.path.exists
_live_memory = str(Path(__file__).resolve().parents[2] / "data" / "translation_memory.json")


def _exists_without_live_memory(path):
    if os.path.normcase(os.path.abspath(path)) == os.path.normcase(_live_memory):
        return False
    return _real_exists(path)


@contextmanager
def _module_override(name, module):
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous


with patch.dict(os.environ, _TEST_ENV), _module_override("app.core.queues", _fake_queues), patch("os.path.exists", side_effect=_exists_without_live_memory):
    from app.core import access_policy, http_boundary, security
    from app.core.auth_settings import AuthSettings
    from app.core.policy_settings import PolicySettings
    from app.api import auth_routes, routes, websocket
    from app.db.database import get_db
    from app.db.models import User
    from app.db.security_migration import init_security_schema
    from app.services import audio_storage, translation_memory as tm


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.directory = Path(self.temporary)
        self.engine = create_engine("sqlite:///" + (self.directory / "test.db").as_posix(), connect_args={"check_same_thread": False})
        init_security_schema(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.settings = AuthSettings(_env_file=None, **_TEST_ENV)
        self.policy = PolicySettings(_env_file=None, APP_ENV="local", CORS_ORIGINS="http://localhost:5173", TRUSTED_HOSTS="testserver", RATE_LIMIT_RPM=600)
        self.stack.enter_context(patch.object(security, "get_auth_settings", return_value=self.settings))
        for module in (access_policy, http_boundary, routes, websocket, audio_storage):
            self.stack.enter_context(patch.object(module, "get_policy_settings", return_value=self.policy))
        limiter = access_policy.RateLimiter()
        self.stack.enter_context(patch.object(access_policy, "rate_limiter", limiter))
        self.stack.enter_context(patch.object(websocket, "rate_limiter", limiter))
        self.stack.enter_context(patch.object(websocket, "connection_slots", access_policy.ConnectionSlots()))
        self.stack.enter_context(patch.object(websocket, "_pending_handshakes", threading.BoundedSemaphore(8)))
        self.stack.enter_context(patch.object(websocket, "SessionLocal", self.session_factory))
        self.stack.enter_context(patch.object(websocket, "GLOBAL_STT_QUEUE", asyncio.Queue(maxsize=20)))
        self.stack.enter_context(_module_override("app.models.session_model", _fake_session))
        for name in ("_memory", "_guest_memory", "_guest_expiry"):
            self.stack.enter_context(patch.object(tm, name, {}))
        self.stack.enter_context(patch.object(tm, "_DATA_DIR", str(self.directory / "data")))
        self.stack.enter_context(patch.object(tm, "_TM_FILE", str(self.directory / "data" / "memory.json")))
        self.stack.enter_context(patch.object(audio_storage, "SECURE_OUTPUT_DIR", self.directory / "outputs" / "secure"))
        self.stack.enter_context(patch.object(audio_storage, "SECURE_TEMP_DIR", self.directory / "temp" / "secure"))
        self.stack.enter_context(patch.object(routes, "SECURE_TEMP_DIR", self.directory / "temp" / "secure"))
        self.app = FastAPI()
        self.app.add_middleware(http_boundary.HTTPBoundaryMiddleware)
        self.app.include_router(auth_routes.router)
        self.app.include_router(routes.router)
        self.app.include_router(websocket.router)

        def temporary_db():
            with self.session_factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = temporary_db
        self.client = self.stack.enter_context(TestClient(self.app))

    def tearDown(self):
        # Close client and patches before disposing/removing temporary SQLite files.
        self.client.close()
        self.engine.dispose()
        self.stack.close()

    def guest(self):
        response = self.client.post("/api/session/guest")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def headers(self, token):
        return {"Authorization": "Bearer " + token}

    def ws_config(self, token=None, **extra):
        payload = {"type": "config", "sample_rate": 16000, "channels": 1, "sample_width": 2,
                   "source_lang": "vi", "target_lang": "en"}
        if token is not None:
            payload["access_token"] = token
        return {**payload, **extra}

    def expect_ws_close(self, stream, code):
        response = stream.receive_json()
        self.assertEqual(response.get("type"), "error")
        with self.assertRaises(WebSocketDisconnect) as caught:
            stream.receive_json()
        self.assertEqual(caught.exception.code, code)

    def test_http_anonymous_and_untrusted_origin_rejected(self):
        self.assertEqual(self.client.get("/api/translation-memory").status_code, 401)
        self.assertEqual(self.client.post("/api/translation-memory", json={"source_text": "x", "translated_text": "y"}).status_code, 401)
        self.assertEqual(self.client.get("/audio/" + "a" * 32 + ".wav").status_code, 401)
        self.assertEqual(self.client.post("/api/session/guest", headers={"Origin": "https://untrusted.invalid"}).status_code, 403)

    def test_guest_dictionary_isolated_volatile_and_logout_erases(self):
        first, second = self.guest(), self.guest()
        body = {"source_text": "private phrase", "translated_text": "private result"}
        a, b = self.headers(first["access_token"]), self.headers(second["access_token"])
        self.assertEqual(self.client.post("/api/translation-memory", json=body, headers=a).status_code, 200)
        self.assertEqual(self.client.get("/api/translation-memory", headers=b).json()["count"], 0)
        for method, path, payload in (
            ("get", "/api/translation-memory?client_id=" + first["owner_id"], None),
            ("post", "/api/translation-memory", {**body, "client_id": first["owner_id"]}),
            ("post", "/api/translation-memory/delete", {"source_text": body["source_text"], "client_id": first["owner_id"]}),
        ):
            response = self.client.request(method, path, json=payload, headers=b)
            self.assertEqual(response.status_code, 403, response.text)
        self.assertFalse(Path(tm._TM_FILE).exists())
        self.assertEqual(self.client.post("/api/session/logout", headers=a).status_code, 204)
        self.assertEqual(tm.get_all(first["owner_id"]), {})
        self.assertEqual(self.client.get("/api/translation-memory", headers=a).status_code, 401)

    def test_guest_expiry_during_write_never_falls_back_to_disk(self):
        owner = "33333333-3333-4333-8333-333333333333"
        tm.register_guest(owner, datetime.now(timezone.utc) + timedelta(minutes=1))
        tm._guest_expiry[owner] = datetime.now(timezone.utc) - timedelta(seconds=1)
        with self.assertRaises(ValueError):
            tm.add("private", "secret", owner, volatile=True)
        self.assertNotIn(owner, tm._memory)
        self.assertFalse(Path(tm._TM_FILE).exists())

    def test_scoped_api_key_cannot_read_dictionary(self):
        with self.session_factory() as db:
            user = User(username="service-owner", role="employee", password_hash=bcrypt.hashpw(b"synthetic-password", bcrypt.gensalt(rounds=4)).decode())
            db.add(user)
            db.commit()
            _, token = security.issue_api_key(db, name="translation-only", owner_id=user.public_id,
                                              scopes=["translate"], expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                                              created_by_user_id=user.id)
        self.assertEqual(self.client.get("/api/translation-memory", headers=self.headers(token)).status_code, 403)
        with self.client.websocket_connect("/ws/realtime") as stream:
            stream.send_json(self.ws_config(token))
            self.expect_ws_close(stream, 4403)

    def test_text_passes_authenticated_owner_to_inference_and_redacts_failure(self):
        guest = self.guest()
        body = {"text": "hello", "source_lang": "en", "target_lang": "vi"}
        with patch.object(routes, "translate_text", return_value={"translated_text": "translated"}) as inference:
            response = self.client.post("/api/translate-text", json=body, headers=self.headers(guest["access_token"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(inference.call_args.kwargs["client_id"], guest["owner_id"])
        with patch.object(routes, "translate_text", side_effect=RuntimeError("synthetic-sensitive-content")):
            response = self.client.post("/api/translate-text", json=body, headers=self.headers(guest["access_token"]))
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("synthetic-sensitive-content", response.text)

    def test_invalid_audio_and_inference_failure_cleanup_temp_outputs(self):
        guest = self.guest()
        headers = self.headers(guest["access_token"])
        response = self.client.post("/translate", files={"file": ("invalid.wav", b"not a WAV", "audio/wav")}, headers=headers)
        self.assertEqual(response.status_code, 422)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b"\0\0" * 160)

        def failure(path, *, client_id, output_path):
            Path(output_path).write_bytes(b"partial-output")
            raise RuntimeError("synthetic-sensitive-content")

        with patch.object(routes, "run_pipeline", side_effect=failure):
            response = self.client.post("/translate", files={"file": ("valid.wav", buffer.getvalue(), "audio/wav")}, headers=headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("synthetic-sensitive-content", response.text)
        self.assertEqual(list((self.directory / "temp" / "secure").iterdir()), [])
        self.assertEqual(list((self.directory / "outputs" / "secure").iterdir()), [])

    def test_audio_owner_and_expiry_enforced(self):
        first, second = self.guest(), self.guest()
        name = "a" * 32 + ".wav"
        audio_storage.audio_path(name).write_bytes(b"synthetic-audio")
        with self.session_factory() as db:
            asset = audio_storage.register_audio(db, name, first["owner_id"])
            self.assertEqual(self.client.get("/audio/" + name, headers=self.headers(first["access_token"])).status_code, 200)
            self.assertEqual(self.client.get("/audio/" + name, headers=self.headers(second["access_token"])).status_code, 404)
            asset.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.client.get("/audio/" + name, headers=self.headers(first["access_token"])).status_code, 404)

    def test_ws_missing_forged_and_cross_owner_credentials(self):
        guest = self.guest()
        for payload, close in ((self.ws_config(), 4401), (self.ws_config("forged-token"), 4401),
                               (self.ws_config(guest["access_token"], client_id="default"), 4403)):
            with self.client.websocket_connect("/ws/realtime") as stream:
                stream.send_json(payload)
                self.expect_ws_close(stream, close)

    def test_ws_origin_and_mutable_identity_rejected(self):
        with self.assertRaises(WebSocketDisconnect) as caught:
            with self.client.websocket_connect("/ws/realtime", headers={"Origin": "https://untrusted.invalid"}):
                pass
        self.assertEqual(caught.exception.code, 4403)
        guest = self.guest()
        with self.client.websocket_connect("/ws/realtime") as stream:
            stream.send_json(self.ws_config(guest["access_token"]))
            self.assertEqual(stream.receive_json()["status"], "authenticated")
            stream.send_json({"type": "config", "client_id": "default"})
            self.expect_ws_close(stream, 4400)

    def test_ws_valid_audio_enters_queue_and_oversize_rejected(self):
        guest = self.guest()
        with self.client.websocket_connect("/ws/realtime") as stream:
            stream.send_json(self.ws_config(guest["access_token"]))
            self.assertEqual(stream.receive_json()["owner_id"], guest["owner_id"])
            stream.send_bytes(b"\0\0" * 100)
            stream.send_bytes(b"\0" * (self.policy.WS_MAX_MESSAGE_BYTES + 2))
            self.expect_ws_close(stream, 4400)
        queued = websocket.GLOBAL_STT_QUEUE.get_nowait()
        self.assertEqual(queued["session"].client_id, guest["owner_id"])
        self.assertEqual(queued["audio"], b"\0\0" * 100)

    def test_ws_turn_controls_remain_available_after_refactor(self):
        guest = self.guest()
        with self.client.websocket_connect("/ws/realtime") as stream:
            stream.send_json(self.ws_config(guest["access_token"]))
            self.assertEqual(stream.receive_json()["status"], "authenticated")
            for command, response in (
                ("start_turn", "turn_started"),
                ("end_turn", "turn_ended"),
                ("cancel_turn", "turn_cancelled"),
            ):
                stream.send_json({"type": command, "turn_id": "turn-1"})
                event = stream.receive_json()
                self.assertEqual(event["type"], response)
                self.assertEqual(event["turn_id"], "turn-1")

    def test_ws_revoked_session_closes_on_authentication_heartbeat(self):
        guest = self.guest()
        with self.client.websocket_connect("/ws/realtime") as stream:
            stream.send_json(self.ws_config(guest["access_token"]))
            self.assertEqual(stream.receive_json()["status"], "authenticated")
            self.assertEqual(self.client.post("/api/session/logout", headers=self.headers(guest["access_token"])).status_code, 204)
            self.expect_ws_close(stream, 4401)

    def test_ws_pending_handshake_capacity_and_release(self):
        with patch.object(websocket, "_pending_handshakes", threading.BoundedSemaphore(2)):
            with ExitStack() as connections:
                connections.enter_context(self.client.websocket_connect("/ws/realtime"))
                connections.enter_context(self.client.websocket_connect("/ws/realtime"))
                with self.assertRaises(WebSocketDisconnect) as caught:
                    with self.client.websocket_connect("/ws/realtime"):
                        pass
                self.assertEqual(caught.exception.code, 4429)
            guest = self.guest()
            with self.client.websocket_connect("/ws/realtime") as stream:
                stream.send_json(self.ws_config(guest["access_token"]))
                self.assertEqual(stream.receive_json()["status"], "authenticated")

    def test_chunked_body_limit_enforced_before_downstream_parser(self):
        sent = []
        received = iter([
            {"type": "http.request", "body": b"a" * 40000, "more_body": True},
            {"type": "http.request", "body": b"b" * 40000, "more_body": False},
        ])
        called = False

        async def downstream(scope, receive, send):
            nonlocal called
            called = True

        async def receive():
            return next(received)

        async def send(message):
            sent.append(message)

        scope = {"type": "http", "method": "POST", "path": "/api/translate-text", "scheme": "http",
                 "headers": [(b"authorization", b"Bearer synthetic")], "query_string": b""}
        asyncio.run(http_boundary.HTTPBoundaryMiddleware(downstream)(scope, receive, send))
        self.assertFalse(called)
        self.assertEqual(sent[0]["status"], 413)

    def test_slow_body_deadline_rejects_without_downstream(self):
        sent = []
        called = False

        async def downstream(scope, receive, send):
            nonlocal called
            called = True

        async def receive():
            await asyncio.sleep(60)
            return {"type": "http.request", "body": b"x", "more_body": False}

        async def send(message):
            sent.append(message)

        scope = {"type": "http", "method": "POST", "path": "/api/translate-text", "scheme": "http",
                 "headers": [(b"authorization", b"Bearer synthetic")], "query_string": b""}
        readings = iter([0.0, 11.0])
        fake_clock = types.SimpleNamespace(monotonic=lambda: next(readings, 11.0))
        with patch.object(http_boundary, "time", fake_clock):
            asyncio.run(http_boundary.HTTPBoundaryMiddleware(downstream)(scope, receive, send))
        self.assertFalse(called)
        self.assertEqual(sent[0]["status"], 408)

    def test_unauthorized_body_is_not_read(self):
        sent = []
        calls = []

        async def downstream(scope, receive, send):
            calls.append("downstream")

        async def receive():
            calls.append("receive")
            return {"type": "http.request", "body": b"x", "more_body": False}

        async def send(message):
            sent.append(message)

        scope = {"type": "http", "method": "POST", "path": "/translate", "scheme": "http", "headers": [], "query_string": b""}
        asyncio.run(http_boundary.HTTPBoundaryMiddleware(downstream)(scope, receive, send))
        self.assertEqual(calls, [])
        self.assertEqual(sent[0]["status"], 401)


if __name__ == "__main__":
    unittest.main()

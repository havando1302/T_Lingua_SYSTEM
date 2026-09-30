"""Bound request bodies before multipart parsing; keep credentials out of responses."""
import asyncio
import time
from starlette.responses import JSONResponse

from app.core.access_policy import get_policy_settings


class HTTPBoundaryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        policy = get_policy_settings()
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        if policy.APP_ENV != "local" and scope.get("scheme") != "https":
            return await JSONResponse({"detail": "HTTPS is required"}, 400)(scope, receive, send)
        origin = headers.get(b"origin")
        if origin is not None:
            origin_str = origin.decode("latin-1")
            is_allowed = origin_str in policy.cors_origin_list
            if not is_allowed and policy.APP_ENV == "local":
                from urllib.parse import urlsplit
                parsed = urlsplit(origin_str)
                if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                    is_allowed = True
            if not is_allowed:
                return await JSONResponse({"detail": "Origin is not allowed"}, 403)(scope, receive, send)

        async def secured_send(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers += [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer")]
                if policy.APP_ENV != "local":
                    response_headers.append((b"strict-transport-security", b"max-age=31536000"))
                message = {**message, "headers": response_headers}
            await send(message)

        if scope.get("method") not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, secured_send)
        path = scope.get("path", "")
        if path not in {"/admin/login", "/api/session/guest"} and not headers.get(b"authorization", b"").startswith(b"Bearer "):
            return await JSONResponse({"detail": "Authentication required"}, 401, headers={"WWW-Authenticate": "Bearer"})(scope, receive, secured_send)
        limit = 65536
        if path == "/translate":
            limit = policy.MAX_AUDIO_UPLOAD_BYTES + 16384
        elif path == "/admin/dictionary/upload":
            limit = policy.MAX_DICTIONARY_UPLOAD_BYTES + 16384
        if b"content-length" in headers:
            try:
                length = int(headers[b"content-length"])
                if length < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({"detail": "Invalid Content-Length"}, 400)(scope, receive, secured_send)
            if length > limit:
                return await JSONResponse({"detail": "Request body too large"}, 413)(scope, receive, secured_send)
        body = bytearray()
        deadline = time.monotonic() + 10
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return await JSONResponse({"detail": "Request body timed out"}, 408)(scope, receive, secured_send)
            try:
                message = await asyncio.wait_for(receive(), remaining)
            except asyncio.TimeoutError:
                return await JSONResponse({"detail": "Request body timed out"}, 408)(scope, receive, secured_send)
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > limit:
                return await JSONResponse({"detail": "Request body too large"}, 413)(scope, receive, secured_send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        consumed = False

        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, secured_send)

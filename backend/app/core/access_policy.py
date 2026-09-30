"""Shared ingress policy for the single-process deployment (no inference imports)."""
import hashlib
import threading
import time

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.policy_settings import PolicySettings, get_policy_settings
from app.core.security import Principal, get_current_principal
from app.db.database import get_db
from app.db.models import SystemSetting


class RateLimiter:
    """Bounded fixed-window counters. Only valid with the current one-worker server."""
    def __init__(self, capacity: int = 10000):
        self._capacity = capacity
        self._buckets = {}
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, *, window: int = 60, cost: int = 1) -> None:
        now = time.monotonic()
        digest = hashlib.sha256(key.encode()).digest()
        with self._lock:
            # Do not store user supplied identifiers or raw IPs in counters/logs.
            if digest not in self._buckets and len(self._buckets) >= self._capacity:
                self._buckets = {k: v for k, v in self._buckets.items() if v[0] > now}
                if len(self._buckets) >= self._capacity:
                    raise HTTPException(429, "Request limit reached", headers={"Retry-After": "60"})
            end, used = self._buckets.get(digest, (now + window, 0))
            if end <= now:
                end, used = now + window, 0
            if used + cost > limit:
                raise HTTPException(429, "Request limit reached", headers={"Retry-After": str(max(1, int(end - now + 1)))})
            self._buckets[digest] = (end, used + cost)


rate_limiter = RateLimiter()


def enforce_origin(connection) -> None:
    settings = get_policy_settings()
    origin = connection.headers.get("origin")
    if origin is not None:
        if origin in settings.cors_origin_list:
            return
        if settings.APP_ENV == "local":
            from urllib.parse import urlsplit
            parsed = urlsplit(origin)
            if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                return
        raise HTTPException(403, "Origin is not allowed")


def enforce_rate(request, principal: Principal | None = None, bucket: str = "api", *, limit: int | None = None) -> None:
    settings = get_policy_settings()
    enforce_origin(request)
    host = request.client.host if request.client else "unknown"
    rate = limit or settings.RATE_LIMIT_RPM
    if bucket == "guest":
        guest_limit = 120 if settings.APP_ENV == "local" else settings.GUEST_SESSIONS_PER_MINUTE
        rate_limiter.check("guest:global", guest_limit)
        rate = guest_limit
    elif bucket == "login":
        rate = 10
    # Socket peer is authoritative; never trust a caller-supplied forwarding header here.
    rate_limiter.check(f"{bucket}:ip:{host}", rate)
    if principal is not None:
        rate_limiter.check(f"{bucket}:owner:{principal.owner_id}", rate)


def configured_limit(db: Session, name: str, default: int) -> int:
    value = db.query(SystemSetting.value).filter(SystemSetting.key == name).scalar()
    try:
        # Runtime settings may tighten but cannot exceed deployment hard limits.
        return max(1, min(default, int(value))) if value is not None else default
    except (TypeError, ValueError):
        return default


def require_scope(scope: str):
    def dependency(request: Request, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> Principal:
        if scope not in principal.scopes:
            raise HTTPException(403, "Insufficient scope")
        limit = configured_limit(db, "rate_limit_rpm", get_policy_settings().RATE_LIMIT_RPM)
        enforce_rate(request, principal, limit=limit)
        return principal
    return dependency


def owner_namespace(principal: Principal, claimed_owner: str | None = None) -> str:
    if claimed_owner is not None and claimed_owner != principal.owner_id:
        raise HTTPException(403, "Owner does not match the authenticated session")
    return principal.owner_id


def validate_text(text: str, db: Session) -> str:
    value = text.strip()
    limit = configured_limit(db, "max_chars_per_request", get_policy_settings().MAX_TEXT_CHARS)
    if not value or len(value) > limit:
        raise HTTPException(422, f"Text length must be between 1 and {limit} characters")
    return value


class ConnectionSlots:
    def __init__(self):
        self._owners = {}
        self._lock = threading.Lock()

    def acquire(self, owner: str) -> bool:
        policy = get_policy_settings()
        with self._lock:
            if sum(self._owners.values()) >= policy.MAX_WS_CONNECTIONS or self._owners.get(owner, 0) >= policy.MAX_WS_CONNECTIONS_PER_OWNER:
                return False
            self._owners[owner] = self._owners.get(owner, 0) + 1
            return True

    def release(self, owner: str) -> None:
        with self._lock:
            remaining = self._owners.get(owner, 0) - 1
            if remaining > 0:
                self._owners[owner] = remaining
            else:
                self._owners.pop(owner, None)


connection_slots = ConnectionSlots()

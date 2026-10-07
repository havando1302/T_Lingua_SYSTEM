"""Revocable sessions, scoped API keys, password hashing and mandatory MFA."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
import uuid

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth_settings import get_auth_settings
from app.db.database import get_db
from app.db.models import ApiKey, AuthSession, User


RESOURCE_SCOPES = frozenset({"translate", "tm:read", "tm:write", "flag", "audio"})
TOKEN_ISSUER = "t-lingua"
TOKEN_AUDIENCE = "t-lingua-api"
PRIVILEGED_ROLES = frozenset({"admin", "superadmin"})
VALID_ROLES = frozenset({"employee", "admin", "superadmin"})
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login", auto_error=False)


@dataclass(frozen=True)
class Principal:
    owner_id: str
    user_id: int | None
    role: str
    scopes: frozenset[str]
    expires_at: datetime
    session_id: str
    mfa_verified: bool = False


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _utcnow() -> datetime:
    # SQLite stores naive UTC. Public expiration values are explicitly tagged UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        encoded = plain_password.encode("utf-8")
        if not encoded or len(encoded) > 72:
            return False
        return bcrypt.checkpw(encoded, hashed_password.encode("ascii"))
    except (ValueError, TypeError, UnicodeError, AttributeError):
        return False


def get_password_hash(password: str) -> str:
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise ValueError("Password must contain at least 12 characters and at most 72 UTF-8 bytes")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def decode_token(token: str) -> dict:
    settings = get_auth_settings()
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=["HS256"],
        issuer=TOKEN_ISSUER, audience=TOKEN_AUDIENCE,
        options={"require": ["exp", "iat", "sub", "jti"]},
    )


def _parse_scopes(raw: str) -> frozenset[str]:
    try:
        scopes = json.loads(raw)
        if not isinstance(scopes, list) or any(not isinstance(item, str) for item in scopes):
            raise ValueError("Invalid stored scope set")
        return frozenset(scopes) & RESOURCE_SCOPES
    except (ValueError, TypeError):
        raise _unauthorized()


def _issue_session(
    db: Session,
    *,
    owner_id: str,
    user: User | None,
    mfa_verified: bool = False,
    token_kind: str | None = None,
    lifetime: timedelta | None = None,
    commit: bool = True,
) -> dict:
    settings = get_auth_settings()
    minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES if user else settings.AUTH_GUEST_TOKEN_EXPIRE_MINUTES
    now = _utcnow().replace(microsecond=0)
    expires_at = now + (lifetime or timedelta(minutes=minutes))
    session_id = str(uuid.uuid4())
    kind = token_kind or ("user" if user else "guest")
    token = jwt.encode(
        {"sub": owner_id, "jti": session_id, "iss": TOKEN_ISSUER, "aud": TOKEN_AUDIENCE,
         "iat": now, "exp": expires_at, "kind": kind},
        settings.JWT_SECRET_KEY, algorithm="HS256",
    )
    session = AuthSession(
        id=session_id, token_hash=hash_api_key(token), owner_id=owner_id,
        user_id=user.id if user else None, token_version=user.token_version if user else 0,
        scopes=json.dumps(sorted(RESOURCE_SCOPES)), mfa_verified=mfa_verified,
        expires_at=expires_at,
    )
    # The write occurs before counting capacity so SQLite serializes concurrent
    # issuers in the same transaction, including issuers in another process.
    db.query(AuthSession).filter(or_(AuthSession.expires_at <= now, AuthSession.revoked_at.is_not(None))).delete(
        synchronize_session=False
    )
    if user is None:
        active_guests = db.query(AuthSession).filter(AuthSession.user_id.is_(None)).count()
        if active_guests >= settings.AUTH_MAX_ACTIVE_GUEST_SESSIONS:
            db.rollback()
            raise HTTPException(status_code=503, detail="Guest session capacity reached", headers={"Retry-After": "60"})
    db.add(session)
    if commit:
        db.commit()
    return {
        "access_token": token, "token_type": "bearer",
        "expires_in": max(1, int((expires_at - now).total_seconds())),
        "expires_at": expires_at.replace(tzinfo=timezone.utc).isoformat(), "owner_id": owner_id,
        "role": user.role if user else "guest",
    }


def issue_user_session(
    user: User,
    db: Session,
    *,
    mfa_verified: bool = False,
    _commit: bool = True,
) -> dict:
    if not user.is_active or not user.public_id or user.role not in VALID_ROLES:
        raise _unauthorized()
    if (user.mfa_enabled or user_requires_mfa(user)) and not mfa_verified:
        raise HTTPException(status_code=403, detail="MFA verification is required")
    return _issue_session(
        db,
        owner_id=user.public_id,
        user=user,
        mfa_verified=mfa_verified,
        commit=_commit,
    )


def issue_user_session_pair(user: User, db: Session, *, mfa_verified: bool = False) -> tuple[dict, str]:
    """Issue a short bearer token plus a longer opaque-to-JS refresh credential."""
    access = issue_user_session(user, db, mfa_verified=mfa_verified, _commit=False)
    refresh = _issue_session(
        db,
        owner_id=user.public_id,
        user=user,
        mfa_verified=mfa_verified,
        token_kind="refresh",
        lifetime=timedelta(days=get_auth_settings().AUTH_REFRESH_TOKEN_EXPIRE_DAYS),
        commit=False,
    )
    db.commit()
    return access, refresh["access_token"]


def issue_guest_session(db: Session) -> dict:
    if not get_auth_settings().AUTH_GUEST_ENABLED:
        raise HTTPException(status_code=403, detail="Guest access is disabled")
    return _issue_session(db, owner_id=str(uuid.uuid4()), user=None)


def _authenticate_api_key(token: str, db: Session) -> Principal:
    key = db.query(ApiKey).populate_existing().filter(ApiKey.key_hash == hash_api_key(token)).first()
    if (
        key is None or not key.is_active or key.revoked_at is not None
        or not key.owner_id or key.expires_at is None or _as_utc_naive(key.expires_at) <= _utcnow()
    ):
        raise _unauthorized()
    if key.created_by_user_id is not None:
        creator = db.get(User, key.created_by_user_id, populate_existing=True)
        if creator is None or not creator.is_active:
            raise _unauthorized()
    # API keys intentionally never acquire interactive administrator permissions.
    return Principal(key.owner_id, None, "api_key", _parse_scopes(key.scopes),
                     key.expires_at.replace(tzinfo=timezone.utc), f"key:{key.id}")


def authenticate_token(token: str | None, db: Session) -> Principal:
    if not isinstance(token, str) or not token or len(token) > 4096:
        raise _unauthorized()
    if token.startswith("tl_"):
        return _authenticate_api_key(token, db)
    try:
        payload = decode_token(token)
        owner_id, session_id = payload["sub"], payload["jti"]
        uuid.UUID(owner_id)
        uuid.UUID(session_id)
        if payload.get("kind") not in {"user", "guest"}:
            raise ValueError("Invalid session kind")
    except (InvalidTokenError, KeyError, ValueError, TypeError, AttributeError):
        raise _unauthorized()
    stored = db.get(AuthSession, session_id, populate_existing=True)
    if (
        stored is None or stored.revoked_at is not None or _as_utc_naive(stored.expires_at) <= _utcnow()
        or stored.owner_id != owner_id or not hmac.compare_digest(stored.token_hash, hash_api_key(token))
        or (stored.user_id is None) != (payload["kind"] == "guest")
    ):
        raise _unauthorized()
    role = "guest"
    if stored.user_id is not None:
        user = db.get(User, stored.user_id, populate_existing=True)
        if (
            user is None or not user.is_active or user.public_id != owner_id
            or user.token_version != stored.token_version or user.role not in VALID_ROLES
        ):
            raise _unauthorized()
        if (user.mfa_enabled or user_requires_mfa(user)) and not stored.mfa_verified:
            raise _unauthorized()
        role = user.role
    return Principal(owner_id, stored.user_id, role, _parse_scopes(stored.scopes),
                     stored.expires_at.replace(tzinfo=timezone.utc), stored.id, stored.mfa_verified)


def _authenticate_refresh_token(token: str | None, db: Session) -> tuple[AuthSession, User]:
    if not isinstance(token, str) or not token or len(token) > 4096:
        raise _unauthorized()
    try:
        payload = decode_token(token)
        owner_id, session_id = payload["sub"], payload["jti"]
        uuid.UUID(owner_id)
        uuid.UUID(session_id)
        if payload.get("kind") != "refresh":
            raise ValueError("Invalid refresh token kind")
    except (InvalidTokenError, KeyError, ValueError, TypeError, AttributeError):
        raise _unauthorized()
    stored = db.get(AuthSession, session_id, populate_existing=True)
    if (
        stored is None or stored.user_id is None or stored.revoked_at is not None
        or _as_utc_naive(stored.expires_at) <= _utcnow()
        or stored.owner_id != owner_id
        or not hmac.compare_digest(stored.token_hash, hash_api_key(token))
    ):
        raise _unauthorized()
    user = db.get(User, stored.user_id, populate_existing=True)
    if (
        user is None or not user.is_active or user.public_id != owner_id
        or user.token_version != stored.token_version or user.role not in VALID_ROLES
        or ((user.mfa_enabled or user_requires_mfa(user)) and not stored.mfa_verified)
    ):
        raise _unauthorized()
    return stored, user


def refresh_user_session(refresh_token: str | None, db: Session) -> tuple[dict, User, str]:
    """Atomically consume a refresh token and rotate it with the access token."""
    stored, user = _authenticate_refresh_token(refresh_token, db)
    rotated_at = _utcnow()
    consumed = db.query(AuthSession).filter(
        AuthSession.id == stored.id,
        AuthSession.revoked_at.is_(None),
        AuthSession.token_hash == hash_api_key(refresh_token),
    ).update({AuthSession.revoked_at: rotated_at}, synchronize_session=False)
    if consumed != 1:
        db.rollback()
        raise _unauthorized()
    try:
        access = issue_user_session(
            user,
            db,
            mfa_verified=stored.mfa_verified,
            _commit=False,
        )
        refresh = _issue_session(
            db,
            owner_id=user.public_id,
            user=user,
            mfa_verified=stored.mfa_verified,
            token_kind="refresh",
            lifetime=timedelta(days=get_auth_settings().AUTH_REFRESH_TOKEN_EXPIRE_DAYS),
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return access, user, refresh["access_token"]


def revoke_refresh_session(refresh_token: str | None, db: Session) -> bool:
    """Best-effort refresh-token revocation used by explicit logout."""
    try:
        stored, _ = _authenticate_refresh_token(refresh_token, db)
    except HTTPException:
        return False
    updated = db.query(AuthSession).filter(
        AuthSession.id == stored.id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: _utcnow()}, synchronize_session=False)
    db.commit()
    return updated == 1


def get_current_principal(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Principal:
    return authenticate_token(token, db)


def get_current_user(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> User:
    if principal.user_id is None:
        raise HTTPException(status_code=403, detail="A user account is required")
    user = db.get(User, principal.user_id, populate_existing=True)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="Administrator permission is required")
    return current_user


def require_reporting_user(current_user: User = Depends(get_current_user)) -> User:
    """Allow staff to read aggregate operational reports, never administration data."""
    if current_user.role not in {"employee", "admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="Reporting permission is required")
    return current_user


def require_dictionary_reader(current_user: User = Depends(get_current_user)) -> User:
    """Allow staff to read the approved shared terminology database."""
    if current_user.role not in {"employee", "admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="Dictionary read permission is required")
    return current_user


def require_qa_reviewer(current_user: User = Depends(get_current_user)) -> User:
    """Allow staff assigned to the QA workflow; export and training remain admin-only."""
    if current_user.role not in {"employee", "admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="QA review permission is required")
    return current_user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Chỉ tài khoản quản trị cấp cao mới được thực hiện thao tác này")
    return current_user


def revoke_session(principal: Principal, db: Session) -> None:
    if principal.session_id.startswith("key:"):
        key = db.get(ApiKey, int(principal.session_id.split(":", 1)[1]))
        if key is not None:
            key.is_active = False
            key.revoked_at = _utcnow()
    else:
        session = db.get(AuthSession, principal.session_id)
        if session is not None:
            session.revoked_at = _utcnow()
    db.commit()


def revoke_user_sessions(user: User, db: Session) -> None:
    user.token_version += 1
    db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).update(
        {AuthSession.revoked_at: _utcnow()}, synchronize_session=False
    )
    db.query(ApiKey).filter(
        or_(ApiKey.created_by_user_id == user.id, ApiKey.owner_id == user.public_id)
    ).update({ApiKey.is_active: False, ApiKey.revoked_at: _utcnow()}, synchronize_session=False)
    db.commit()


def issue_api_key(db: Session, *, name: str, owner_id: str, scopes, expires_at: datetime,
                  created_by_user_id: int | None = None) -> tuple[ApiKey, str]:
    try:
        uuid.UUID(owner_id)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("An immutable owner identifier is required") from exc
    requested = frozenset(scopes)
    if not requested or not requested.issubset(RESOURCE_SCOPES):
        raise ValueError("API key scopes are invalid")
    expires_at = _as_utc_naive(expires_at)
    if not _utcnow() < expires_at <= _utcnow() + timedelta(days=90):
        raise ValueError("API key expiration must be in the next 90 days")
    raw_key = "tl_" + secrets.token_urlsafe(32)
    digest = hash_api_key(raw_key)
    key = ApiKey(name=name, key="redacted:" + digest, key_hash=digest, key_prefix=raw_key[:11],
                 owner_id=owner_id, scopes=json.dumps(sorted(requested)), expires_at=expires_at,
                 created_by_user_id=created_by_user_id, is_active=True)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key, raw_key


def _mfa_cipher() -> Fernet:
    key = get_auth_settings().MFA_ENCRYPTION_KEY
    if not key:
        raise HTTPException(status_code=503, detail="MFA encryption is not configured")
    return Fernet(key.encode("ascii"))


def encrypt_mfa_secret(secret: str) -> str:
    return _mfa_cipher().encrypt(secret.encode("ascii")).decode("ascii")


def user_requires_mfa(user: User) -> bool:
    """Return the effective interactive-login policy for a valid user."""
    return user.role in VALID_ROLES and get_auth_settings().mfa_required


def _decrypt_mfa_secret(user: User) -> str:
    encrypted_secret = user.mfa_secret_encrypted
    if not encrypted_secret:
        raise HTTPException(status_code=503, detail="MFA configuration is unavailable")
    try:
        return _mfa_cipher().decrypt(encrypted_secret.encode("ascii")).decode("ascii")
    except (InvalidToken, ValueError, AttributeError, UnicodeError):
        raise HTTPException(status_code=503, detail="MFA configuration is unavailable")


def _matching_totp_counter(secret: str, otp: str | None) -> int:
    import pyotp

    if not isinstance(otp, str) or len(otp) != 6 or not otp.isascii() or not otp.isdigit():
        raise _unauthorized()
    totp = pyotp.TOTP(secret)
    current_counter = int(datetime.now(timezone.utc).timestamp()) // totp.interval
    matched = next((counter for counter in (current_counter, current_counter - 1, current_counter + 1)
                    if hmac.compare_digest(totp.at(counter * totp.interval), otp)), None)
    if matched is None:
        raise _unauthorized()
    return matched


def begin_user_mfa_enrollment(user: User, db: Session) -> dict:
    """Create or resume an unverified TOTP enrollment after password verification."""
    import pyotp

    if user.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA is already enabled")
    if user.mfa_secret_encrypted:
        secret = _decrypt_mfa_secret(user)
    else:
        secret = pyotp.random_base32()
        user.mfa_secret_encrypted = encrypt_mfa_secret(secret)
        user.mfa_last_counter = -1
        db.commit()
        db.refresh(user)
    issuer = "T-Lingua"
    return {
        "status": "mfa_setup_required",
        "mfa_required": True,
        "enrollment_required": True,
        "issuer": issuer,
        "account_name": user.username,
        "secret": secret,
        "provisioning_uri": pyotp.TOTP(secret).provisioning_uri(
            name=user.username, issuer_name=issuer,
        ),
    }


def complete_user_mfa_enrollment(user: User, otp: str | None, db: Session) -> bool:
    """Confirm a pending seed atomically; no application session exists yet."""
    if user.mfa_enabled:
        return verify_user_mfa(user, otp, db)
    encrypted_secret = user.mfa_secret_encrypted
    secret = _decrypt_mfa_secret(user)
    matched = _matching_totp_counter(secret, otp)
    updated = db.query(User).filter(
        User.id == user.id,
        User.mfa_enabled.is_(False),
        User.mfa_secret_encrypted == encrypted_secret,
        User.mfa_last_counter < matched,
    ).update({User.mfa_enabled: True, User.mfa_last_counter: matched}, synchronize_session=False)
    if updated != 1:
        db.rollback()
        raise _unauthorized()
    db.commit()
    db.refresh(user)
    # Retire any sessions or API keys created before the account acquired MFA.
    revoke_user_sessions(user, db)
    db.refresh(user)
    return True


def verify_user_mfa(user: User, otp: str | None, db: Session) -> bool:
    required = user_requires_mfa(user)
    if not user.mfa_enabled:
        if required:
            raise HTTPException(status_code=403, detail="MFA enrollment is required")
        return False
    matched = _matching_totp_counter(_decrypt_mfa_secret(user), otp)
    # Compare-and-set prevents two concurrent logins from consuming the same code.
    updated = db.query(User).filter(User.id == user.id, User.mfa_last_counter < matched).update(
        {User.mfa_last_counter: matched}, synchronize_session=False
    )
    if updated != 1:
        db.rollback()
        raise _unauthorized()
    db.commit()
    db.refresh(user)
    return True

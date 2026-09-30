"""Additive SQLite authentication migration; never invoked by importing this module."""
from datetime import datetime, timezone
import hashlib
import uuid

import bcrypt
from sqlalchemy import inspect, text

from app.db.database import Base
from app.db import models  # Register tables before create_all.


SECURITY_SCHEMA_VERSION = 1
_ADDITIONS = {
    "users": {
        "public_id": "VARCHAR(36)",
        "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        "token_version": "INTEGER NOT NULL DEFAULT 0",
        "mfa_secret_encrypted": "TEXT",
        "mfa_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "mfa_last_counter": "INTEGER NOT NULL DEFAULT -1",
    },
    "api_keys": {
        "key_hash": "VARCHAR(64)",
        "key_prefix": "VARCHAR(16)",
        "owner_id": "VARCHAR(36)",
        "created_by_user_id": "INTEGER",
        "scopes": "TEXT NOT NULL DEFAULT '[]'",
        "expires_at": "DATETIME",
        "revoked_at": "DATETIME",
    },
    "translation_logs": {
        "source_lang": "VARCHAR(16) DEFAULT 'vi'",
        "target_lang": "VARCHAR(16) DEFAULT 'en'",
        "is_reviewed": "BOOLEAN NOT NULL DEFAULT 0",
        "input_mode": "VARCHAR(16) NOT NULL DEFAULT 'unknown'",
        "stt_model_id": "VARCHAR(200)",
        "nllb_model_id": "VARCHAR(200)",
    },
    "quality_reviews": {
        "corrected_source_text": "TEXT",
        "stt_status": "VARCHAR(24) NOT NULL DEFAULT 'not_applicable'",
        "stt_error_category": "VARCHAR(32)",
        "translation_status": "VARCHAR(24) NOT NULL DEFAULT 'corrected'",
        "domain": "VARCHAR(64)",
        "consent_for_training": "BOOLEAN NOT NULL DEFAULT 0",
        "pii_status": "VARCHAR(16) NOT NULL DEFAULT 'pending'",
        "speaker_id_hash": "VARCHAR(64)",
        "use_for_whisper": "BOOLEAN NOT NULL DEFAULT 0",
        "use_for_nllb": "BOOLEAN NOT NULL DEFAULT 0",
        "whisper_split": "VARCHAR(16)",
        "nllb_split": "VARCHAR(16)",
    },
}


def init_security_schema(engine) -> dict:
    """Preserve legacy rows, retire legacy credentials and record a migration version.

    Run against a backed-up database during controlled startup. Existing PostgreSQL
    deployments need a reviewed dialect-specific migration instead of implicit DDL.
    """
    if engine.dialect.name != "sqlite":
        raise RuntimeError("The security migration currently supports SQLite only")
    with engine.begin() as connection:
        existing_tables = set(inspect(connection).get_table_names())
        for table, additions in _ADDITIONS.items():
            if table not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, definition in additions.items():
                if column not in existing_columns:
                    # All identifiers and definitions are internal constants.
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'))
        Base.metadata.create_all(bind=connection)
        connection.execute(text(
            "CREATE TABLE IF NOT EXISTS security_schema_versions "
            "(version INTEGER PRIMARY KEY, applied_at DATETIME NOT NULL)"
        ))
        applied = connection.execute(text(
            "SELECT 1 FROM security_schema_versions WHERE version=:version"
        ), {"version": SECURITY_SCHEMA_VERSION}).scalar()
        if applied:
            return {"version": SECURITY_SCHEMA_VERSION, "applied": False}

        for row in connection.execute(text("SELECT id FROM users WHERE public_id IS NULL OR public_id=''")):
            connection.execute(text("UPDATE users SET public_id=:public_id WHERE id=:id"),
                               {"public_id": str(uuid.uuid4()), "id": row.id})
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Only the historical bootstrap credential is recognized. Custom credentials
        # are never disabled by username alone, and no password/hash is logged.
        bootstrap = connection.execute(text(
            "SELECT id, password_hash FROM users WHERE username=:username"
        ), {"username": "admin"}).first()
        default_disabled = False
        if bootstrap:
            try:
                known_default = bcrypt.checkpw(b"admin123", bootstrap.password_hash.encode("ascii"))
            except (ValueError, TypeError, UnicodeError, AttributeError):
                known_default = False
            if known_default:
                connection.execute(text(
                    "UPDATE users SET is_active=0, token_version=token_version+1 WHERE id=:id"
                ), {"id": bootstrap.id})
                default_disabled = True

        retired = 0
        for row in connection.execute(text("SELECT id, key, key_hash FROM api_keys")).fetchall():
            if row.key_hash:
                continue
            digest = hashlib.sha256((row.key or str(uuid.uuid4())).encode("utf-8")).hexdigest()
            connection.execute(text(
                "UPDATE api_keys SET key=:redacted, key_hash=:digest, key_prefix=:prefix, "
                "is_active=0, revoked_at=:now, scopes='[]' WHERE id=:id"
            ), {"redacted": "redacted:" + digest, "digest": digest,
                "prefix": "retired", "now": now, "id": row.id})
            retired += 1
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_public_id ON users(public_id)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_api_keys_owner_id ON api_keys(owner_id)"))
        connection.execute(text(
            "INSERT INTO security_schema_versions (version, applied_at) VALUES (:version, :now)"
        ), {"version": SECURITY_SCHEMA_VERSION, "now": now})
    return {"version": SECURITY_SCHEMA_VERSION, "applied": True,
            "legacy_keys_retired": retired, "default_admin_disabled": default_disabled}


def security_schema_ready(engine) -> bool:
    try:
        with engine.connect() as connection:
            version = connection.execute(text("SELECT MAX(version) FROM security_schema_versions")).scalar()
            return version == SECURITY_SCHEMA_VERSION
    except Exception:
        return False

"""Additive authentication migration for SQLite and PostgreSQL.

The application starts against both a local SQLite database and a durable
PostgreSQL database (for example Supabase).  Keep this migration additive and
idempotent because it is executed during every application startup.
"""
from datetime import datetime, timezone
import hashlib
import uuid

import bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    false,
    inspect,
    text,
    true,
)
from sqlalchemy.schema import CreateColumn

from app.db.database import Base
from app.db import models  # Register tables before create_all.
from app.db import audio_model  # noqa: F401 - register audio_assets metadata.


SECURITY_SCHEMA_VERSION = 2
_ADDITIONS = {
    "users": {
        "public_id": Column("public_id", String(36)),
        "is_active": Column("is_active", Boolean, nullable=False, server_default=true()),
        "token_version": Column("token_version", Integer, nullable=False, server_default=text("0")),
        "mfa_secret_encrypted": Column("mfa_secret_encrypted", Text),
        "mfa_enabled": Column("mfa_enabled", Boolean, nullable=False, server_default=false()),
        "mfa_last_counter": Column("mfa_last_counter", Integer, nullable=False, server_default=text("-1")),
    },
    "api_keys": {
        "key_hash": Column("key_hash", String(64)),
        "key_prefix": Column("key_prefix", String(16)),
        "owner_id": Column("owner_id", String(36)),
        "created_by_user_id": Column("created_by_user_id", Integer),
        "scopes": Column("scopes", Text, nullable=False, server_default=text("'[]'")),
        "expires_at": Column("expires_at", DateTime),
        "revoked_at": Column("revoked_at", DateTime),
    },
    "translation_logs": {
        "source_lang": Column("source_lang", String(16), server_default=text("'vi'")),
        "target_lang": Column("target_lang", String(16), server_default=text("'en'")),
        "is_reviewed": Column("is_reviewed", Boolean, nullable=False, server_default=false()),
        "input_mode": Column("input_mode", String(16), nullable=False, server_default=text("'unknown'")),
        "stt_model_id": Column("stt_model_id", String(200)),
        "nllb_model_id": Column("nllb_model_id", String(200)),
    },
    "quality_reviews": {
        "corrected_source_text": Column("corrected_source_text", Text),
        "stt_status": Column("stt_status", String(24), nullable=False, server_default=text("'not_applicable'")),
        "stt_error_category": Column("stt_error_category", String(32)),
        "translation_status": Column("translation_status", String(24), nullable=False, server_default=text("'corrected'")),
        "domain": Column("domain", String(64)),
        "consent_for_training": Column("consent_for_training", Boolean, nullable=False, server_default=false()),
        "pii_status": Column("pii_status", String(16), nullable=False, server_default=text("'pending'")),
        "speaker_id_hash": Column("speaker_id_hash", String(64)),
        "use_for_whisper": Column("use_for_whisper", Boolean, nullable=False, server_default=false()),
        "use_for_nllb": Column("use_for_nllb", Boolean, nullable=False, server_default=false()),
        "whisper_split": Column("whisper_split", String(16)),
        "nllb_split": Column("nllb_split", String(16)),
    },
}


def _add_missing_columns(connection) -> None:
    existing_tables = set(inspect(connection).get_table_names())
    preparer = connection.dialect.identifier_preparer
    for table_name, additions in _ADDITIONS.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {
            column["name"] for column in inspect(connection).get_columns(table_name)
        }
        quoted_table = preparer.quote(table_name)
        for column_name, column in additions.items():
            if column_name in existing_columns:
                continue
            # Types and defaults are compiled for the active dialect, avoiding
            # SQLite-only DATETIME and integer boolean defaults on PostgreSQL.
            definition = str(CreateColumn(column).compile(dialect=connection.dialect))
            connection.execute(text(f"ALTER TABLE {quoted_table} ADD COLUMN {definition}"))


def _ensure_version_table(connection) -> None:
    metadata = MetaData()
    version_table = Table(
        "security_schema_versions",
        metadata,
        Column("version", Integer, primary_key=True),
        Column("applied_at", DateTime, nullable=False),
    )
    version_table.create(bind=connection, checkfirst=True)


def init_security_schema(engine) -> dict:
    """Preserve legacy rows, retire legacy credentials and record a migration version.

    Run against a backed-up database during controlled startup.
    """
    if engine.dialect.name not in {"sqlite", "postgresql"}:
        raise RuntimeError(
            f"Unsupported database dialect for security migration: {engine.dialect.name}"
        )
    with engine.begin() as connection:
        Base.metadata.create_all(bind=connection)
        _add_missing_columns(connection)
        # Version 2 permits realtime capture before a QA reviewer touches the
        # sample. The authenticated owner remains on TranslationLog, while the
        # uploader is null until an administrator manually replaces the audio.
        audio_columns = {
            column["name"]: column
            for column in inspect(connection).get_columns("training_audio_assets")
        }
        if audio_columns and not audio_columns["uploaded_by_user_id"].get("nullable", True):
            if engine.dialect.name == "postgresql":
                connection.execute(text(
                    "ALTER TABLE training_audio_assets "
                    "ALTER COLUMN uploaded_by_user_id DROP NOT NULL"
                ))
            else:
                connection.execute(text(
                    "CREATE TABLE training_audio_assets_v2 ("
                    "id VARCHAR(36) NOT NULL PRIMARY KEY, "
                    "translation_log_id INTEGER NOT NULL UNIQUE REFERENCES translation_logs(id), "
                    "file_name VARCHAR(40) NOT NULL UNIQUE, sha256 VARCHAR(64) NOT NULL, "
                    "duration_ms INTEGER NOT NULL, sample_rate INTEGER NOT NULL, channels INTEGER NOT NULL, "
                    "uploaded_by_user_id INTEGER REFERENCES users(id), created_at DATETIME NOT NULL)"
                ))
                connection.execute(text(
                    "INSERT INTO training_audio_assets_v2 "
                    "SELECT id, translation_log_id, file_name, sha256, duration_ms, sample_rate, channels, "
                    "uploaded_by_user_id, created_at FROM training_audio_assets"
                ))
                connection.execute(text("DROP TABLE training_audio_assets"))
                connection.execute(text("ALTER TABLE training_audio_assets_v2 RENAME TO training_audio_assets"))
                connection.execute(text(
                    "CREATE INDEX ix_training_audio_assets_translation_log_id "
                    "ON training_audio_assets(translation_log_id)"
                ))
                connection.execute(text(
                    "CREATE INDEX ix_training_audio_assets_sha256 ON training_audio_assets(sha256)"
                ))
        _ensure_version_table(connection)
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
                    "UPDATE users SET is_active=:inactive, token_version=token_version+1 WHERE id=:id"
                ), {"inactive": False, "id": bootstrap.id})
                default_disabled = True

        retired = 0
        for row in connection.execute(text("SELECT id, key, key_hash FROM api_keys")).fetchall():
            if row.key_hash:
                continue
            digest = hashlib.sha256((row.key or str(uuid.uuid4())).encode("utf-8")).hexdigest()
            connection.execute(text(
                "UPDATE api_keys SET key=:redacted, key_hash=:digest, key_prefix=:prefix, "
                "is_active=:inactive, revoked_at=:now, scopes='[]' WHERE id=:id"
            ), {"redacted": "redacted:" + digest, "digest": digest,
                "prefix": "retired", "inactive": False, "now": now, "id": row.id})
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

from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="employee", nullable=True) # superadmin, admin, employee
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    public_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_last_counter: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)

class TranslationLog(Base):
    __tablename__ = "translation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str | None] = mapped_column(String, index=True)
    source_text: Mapped[str] = mapped_column(String, nullable=False)
    translated_text: Mapped[str] = mapped_column(String, nullable=False)
    latency: Mapped[float | None] = mapped_column(Float)
    model_source: Mapped[str | None] = mapped_column(String) # Ví dụ: nllb_model, translation_memory
    input_mode: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    stt_model_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    nllb_model_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_lang: Mapped[str] = mapped_column(String(16), default="vi", index=True, nullable=True)
    target_lang: Mapped[str] = mapped_column(String(16), default="en", index=True, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True) # Bị cờ báo (nghi ngờ sai)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # Đã được QA xem xét / chỉnh sửa
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=True)

class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Retained for additive compatibility with old SQLite databases; never a raw key.
    key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    key_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    key_prefix: Mapped[str | None] = mapped_column(String(16), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    mfa_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TranslationMemoryEntry(Base):
    __tablename__ = "translation_memory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False, default="global:approved")
    source_lang: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="vi")
    target_lang: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="en")
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_text_normalized: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    norm_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "source_lang",
            "target_lang",
            "source_text_normalized",
            "norm_version",
            name="uq_tm_owner_langs_norm_text"
        ),
    )


class QualityReview(Base):
    """Structured reviewer assessment kept separately from the translation log."""
    __tablename__ = "quality_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    translation_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("translation_logs.id"), nullable=False, unique=True, index=True
    )
    reviewer_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    adequacy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fluency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    critical_error: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    stt_status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_applicable")
    stt_error_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    translation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="corrected")
    domain: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    consent_for_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pii_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    speaker_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    use_for_whisper: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    use_for_nllb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whisper_split: Mapped[str | None] = mapped_column(String(16), nullable=True)
    nllb_split: Mapped[str | None] = mapped_column(String(16), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TrainingAudioAsset(Base):
    """Consent-bound source audio used only for supervised Whisper datasets."""
    __tablename__ = "training_audio_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    translation_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("translation_logs.id"), nullable=False, unique=True, index=True
    )
    file_name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=16000)
    channels: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploaded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    """Content-minimized administrative audit trail."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ModelDeployment(Base):
    """Versioned control-plane state for active/canary model configuration."""
    __tablename__ = "model_deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    component: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    active_model: Mapped[str] = mapped_column(String(200), nullable=False)
    canary_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    canary_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_active_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )


class TrainingDataset(Base):
    """Immutable, validated dataset snapshot used by an offline training worker."""
    __tablename__ = "training_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    task: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_langs: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", index=True)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    train_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_uri: Mapped[str] = mapped_column(String(300), nullable=False)
    validation_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TrainingJob(Base):
    """Durable queue item claimed by the standalone training worker."""
    __tablename__ = "training_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    depends_on_job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("training_jobs.id"), nullable=True)
    task: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_datasets.id"), nullable=False, index=True)
    base_model: Mapped[str] = mapped_column(String(200), nullable=False)
    output_version: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    method: Mapped[str] = mapped_column(String(24), nullable=False, default="lora")
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    progress_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_epoch: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    train_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    eta_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TrainingJobEvent(Base):
    __tablename__ = "training_job_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_jobs.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, default="log")
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    component: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    base_model: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_datasets.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_jobs.id"), nullable=False, unique=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="transformers")
    storage_uri: Mapped[str] = mapped_column(String(300), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="candidate", index=True)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    component: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    from_artifact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    to_artifact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    strategy: Mapped[str] = mapped_column(String(24), nullable=False)
    canary_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_reload")
    requested_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

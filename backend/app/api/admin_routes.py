"""
Admin API routes.
JWT / password logic delegated to core.security.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError
import csv
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ElementTree
import openpyxl
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
import os
import psutil
import tempfile
from datetime import datetime, timedelta, timezone

from app.db.database import get_db
from app.db.models import (
    User, TranslationLog, ApiKey, SystemSetting, QualityReview, AuditLog,
    ModelDeployment, TrainingAudioAsset,
)
from app.services import translation_memory as tm
from app.services.training_audio_storage import (
    delete_training_audio, store_training_wav, training_audio_path,
)

# ── Security (từ core, không hardcode) ──────────────────────
from app.core.security import (
    verify_password,
    get_password_hash,
    get_current_user,
    require_admin,
    require_superadmin,
    issue_user_session,
    issue_api_key,
    revoke_user_sessions,
    verify_user_mfa,
    RESOURCE_SCOPES,
)
from app.core.access_policy import enforce_rate, get_policy_settings, rate_limiter, validate_text
from app.core.telemetry import GLOBAL_TELEMETRY

router = APIRouter(prefix="/admin", tags=["Admin"])
APPROVED_DICTIONARY = "global:approved"
# A synthetic, cost-12 bcrypt hash keeps unknown usernames on the password-check path.
_DUMMY_PASSWORD_HASH = "$2b$12$5Dupx56hXncQ8KqKGHZCq.rrz3PT9Yvb5O8qCRJnV/KKX6x9AyMw."

# --- Models ---
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=72)
    role: Literal["employee", "admin", "superadmin"] = "employee"
    model_config = {"extra": "forbid"}

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3 or any(char.isspace() or ord(char) < 32 for char in value):
            raise ValueError("Username must have at least 3 characters and contain no whitespace")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    public_id: str
    is_active: bool
    
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    role: Literal["employee", "admin"] | None = None
    password: str | None = Field(default=None, min_length=12, max_length=72)
    is_active: bool | None = None
    model_config = {"extra": "forbid"}

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: str | None) -> str | None:
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["translate", "audio"], min_length=1, max_length=5)
    expires_in_days: int = Field(default=30, ge=1, le=90)
    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("API key name must not be blank")
        return value.strip()

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, value: list[str]) -> list[str]:
        if not set(value).issubset(RESOURCE_SCOPES):
            raise ValueError("API key scopes are invalid")
        return sorted(set(value))

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    scopes: list[str]
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

class CreatedApiKeyResponse(ApiKeyResponse):
    key: str

class SettingUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=20)
    model_config = {"extra": "forbid"}

class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: str | None
    
    model_config = {"from_attributes": True}


ModelComponent = Literal["whisper", "nllb", "tts_eng", "tts_vie"]


class ModelCanaryUpdate(BaseModel):
    model_id: str = Field(min_length=2, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]+$")
    percent: int = Field(ge=1, le=50)
    model_config = {"extra": "forbid"}

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, value: str) -> str:
        if ".." in value or "\\" in value:
            raise ValueError("Unsafe model identifier")
        return value

class DictionaryItem(BaseModel):
    source_text: str = Field(min_length=1, max_length=5000)
    translated_text: str = Field(min_length=1, max_length=5000)
    source_lang: str | None = Field(default=None, max_length=16)
    target_lang: str | None = Field(default=None, max_length=16)
    model_config = {"extra": "forbid"}


def _audit(db: Session, actor: User, action: str, resource_type: str,
           resource_id: str | int | None = None, details: dict | None = None) -> None:
    """Add a content-minimized audit record to the caller's current transaction."""
    db.add(AuditLog(
        actor_user_id=actor.id,
        actor_username=actor.username,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
    ))


# --- AUTH ---
@router.post("/login", response_model=Token)
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
                           otp: str | None = Form(default=None, max_length=6), db: Session = Depends(get_db)):
    enforce_rate(request, bucket="login")
    username = form_data.username.strip()
    rate_limiter.check("login:account:" + username.casefold(), 10)
    user = db.query(User).filter(User.username == username).first() if len(username) <= 100 else None
    password_valid = verify_password(form_data.password, user.password_hash if user else _DUMMY_PASSWORD_HASH)
    if user is None or not password_valid or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )
    mfa_verified = verify_user_mfa(user, otp, db)
    session = issue_user_session(user, db, mfa_verified=mfa_verified)
    return {**session, "user": UserResponse.model_validate(user)}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- USER MANAGEMENT ---
@router.get("/users", response_model=List[UserResponse])
def get_users(skip: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=100, ge=1, le=100),
              search: str | None = Query(default=None, max_length=200),
              db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    query = db.query(User)
    if search:
        query = query.filter(User.username.ilike(_search_pattern(search), escape="\\"))
    users = query.order_by(User.id.desc()).offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    try:
        db.flush()
        _audit(db, admin, "user.create", "user", db_user.id, {"role": user.role})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username đã tồn tại")
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "superadmin":
        raise HTTPException(status_code=403, detail="Không thể xóa superadmin")
    user.is_active = False
    revoke_user_sessions(user, db)
    _audit(db, admin, "user.disable", "user", user.id, {"role": user.role})
    db.commit()
    return {"ok": True}


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_superadmin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "superadmin" and user.id != admin.id:
        raise HTTPException(status_code=403, detail="Another superadministrator cannot be modified")
    if user.id == admin.id and (req.is_active is False or req.role is not None):
        raise HTTPException(status_code=403, detail="Cannot disable or change the role of the current account")
    changed = {}
    if req.role is not None and req.role != user.role:
        if user.role == "superadmin":
            raise HTTPException(status_code=403, detail="Superadministrator role cannot be downgraded here")
        changed["role"] = {"from": user.role, "to": req.role}
        user.role = req.role
    if req.is_active is not None and req.is_active != user.is_active:
        changed["is_active"] = {"from": user.is_active, "to": req.is_active}
        user.is_active = req.is_active
    if req.password is not None:
        user.password_hash = get_password_hash(req.password)
        changed["password_reset"] = True
    if not changed:
        return user
    revoke_user_sessions(user, db)
    _audit(db, admin, "user.update", "user", user.id, changed)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-sessions")
def reset_user_sessions(user_id: int, db: Session = Depends(get_db),
                        admin: User = Depends(require_superadmin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    revoke_user_sessions(user, db)
    _audit(db, admin, "user.sessions_revoke", "user", user.id)
    db.commit()
    return {"ok": True}

# --- DASHBOARD / METRICS ---
@router.get("/metrics/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    activity = GLOBAL_TELEMETRY.get_activity_summary()
    flagged_translations = db.query(TranslationLog).filter(TranslationLog.is_flagged == True).count()
    
    return {
        "total_translations": activity["total_translations"],
        "flagged_translations": flagged_translations,
        "avg_latency": activity["avg_latency"],
        "unique_clients": activity["unique_clients"],
        "scope": activity["scope"], "started_at": activity["started_at"], "sample_limit": activity["sample_limit"],
    }

# --- LOGS / QA ---
@router.get("/quality/logs")
def get_quality_logs(search: str | None = Query(default=None, max_length=200),
                     flagged_only: bool = False,
                     qa_only: bool = False,
                     review_status: Literal["all", "pending", "reviewed"] = "all",
                     skip: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=50, ge=1, le=100),
                     db: Session = Depends(get_db), user: User = Depends(require_admin)):
    query = db.query(TranslationLog)
    if flagged_only:
        query = query.filter(TranslationLog.is_flagged == True)
    elif qa_only:
        query = query.filter(
            (TranslationLog.is_flagged == True) |
            (TranslationLog.is_reviewed == True) |
            (TranslationLog.model_source == "user_flagged")
        )
    reviewed = or_(TranslationLog.is_reviewed == True,
                   and_(TranslationLog.is_flagged == False, TranslationLog.model_source == "user_flagged"))
    if review_status == "reviewed":
        query = query.filter(reviewed)
    elif review_status == "pending":
        query = query.filter(TranslationLog.is_flagged == True, TranslationLog.is_reviewed == False)
    if search:
        pattern = _search_pattern(search)
        query = query.filter(TranslationLog.source_text.ilike(pattern, escape="\\") | TranslationLog.translated_text.ilike(pattern, escape="\\"))
    logs = query.order_by(TranslationLog.id.desc()).offset(skip).limit(limit).all()
    log_ids = [log.id for log in logs]
    reviews = {
        row.translation_log_id: row for row in db.query(QualityReview).filter(
            QualityReview.translation_log_id.in_(log_ids)
        ).all()
    } if log_ids else {}
    audio = {
        row.translation_log_id: row for row in db.query(TrainingAudioAsset).filter(
            TrainingAudioAsset.translation_log_id.in_(log_ids)
        ).all()
    } if log_ids else {}
    result = []
    for log in logs:
        row = {
            column.name: (getattr(log, column.name).replace(tzinfo=timezone.utc)
                          if column.name == "created_at" and getattr(log, column.name) is not None
                          else getattr(log, column.name))
            for column in TranslationLog.__table__.columns
        }
        review = reviews.get(log.id)
        asset = audio.get(log.id)
        row.update({
            "stt_raw": log.source_text,
            "stt_corrected": review.corrected_source_text if review else None,
            "translation_raw": log.translated_text,
            # Keep the legacy display field useful without destroying the raw model output.
            "translated_text": review.corrected_text if review else log.translated_text,
            "stt_status": review.stt_status if review else "pending" if log.input_mode == "voice" else "not_applicable",
            "stt_error_category": review.stt_error_category if review else None,
            "translation_status": review.translation_status if review else "pending",
            "adequacy": review.adequacy if review else None,
            "fluency": review.fluency if review else None,
            "error_category": review.error_category if review else None,
            "critical_error": review.critical_error if review else False,
            "domain": review.domain if review else None,
            "has_audio": asset is not None,
            "audio_duration_ms": asset.duration_ms if asset else None,
            "audio_url": f"/admin/quality/logs/{log.id}/audio" if asset else None,
        })
        result.append(row)
    return result


def _search_pattern(value: str) -> str:
    return "%" + value.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

class ResolveLogRequest(BaseModel):
    corrected_text: str = Field(min_length=1, max_length=5000)
    corrected_source_text: str | None = Field(default=None, max_length=5000)
    adequacy: int | None = Field(default=None, ge=1, le=5)
    fluency: int | None = Field(default=None, ge=1, le=5)
    error_category: Literal[
        "none", "omission", "addition", "mistranslation", "terminology",
        "entity_number", "grammar", "style"
    ] | None = None
    critical_error: bool = False
    stt_status: Literal["not_applicable", "pending", "correct", "corrected", "unusable"] = "not_applicable"
    stt_error_category: Literal[
        "none", "substitution", "omission", "insertion", "number", "entity",
        "language_detection", "punctuation", "hallucination", "cut_off", "noise",
        "speaker_overlap",
    ] | None = None
    translation_status: Literal["pending", "correct", "corrected", "unusable"] = "corrected"
    domain: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]*$")
    consent_for_training: bool = False
    pii_status: Literal["pending", "clean", "redacted", "rejected"] = "pending"
    speaker_id_hash: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]*$")
    use_for_whisper: bool = False
    use_for_nllb: bool = False
    whisper_split: Literal["train", "validation", "test"] | None = None
    nllb_split: Literal["train", "validation", "test"] | None = None
    notes: str | None = Field(default=None, max_length=1000)
    model_config = {"extra": "forbid"}

@router.post("/quality/logs/{log_id}/resolve")
def resolve_log(log_id: int, req: ResolveLogRequest, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    log = db.query(TranslationLog).filter(TranslationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    corrected_source = validate_text(req.corrected_source_text or log.source_text, db)
    corrected_translation = validate_text(req.corrected_text, db)
    audio = db.query(TrainingAudioAsset).filter(TrainingAudioAsset.translation_log_id == log.id).first()
    stt_status = req.stt_status
    if audio is not None and stt_status in {"not_applicable", "pending"}:
        stt_status = "correct" if corrected_source == log.source_text.strip() else "corrected"
    use_for_whisper = audio is not None and stt_status in {"correct", "corrected"}
    use_for_nllb = req.translation_status in {"correct", "corrected"}

    # Mark the QA item reviewed while preserving both raw model outputs.
    log.is_flagged = False
    log.is_reviewed = True
    review = db.query(QualityReview).filter(QualityReview.translation_log_id == log.id).first()
    if review is None:
        review = QualityReview(
            translation_log_id=log.id,
            reviewer_user_id=user.id,
            corrected_text=corrected_translation,
        )
        db.add(review)
    review.reviewer_user_id = user.id
    review.corrected_text = corrected_translation
    review.corrected_source_text = corrected_source
    review.adequacy = req.adequacy
    review.fluency = req.fluency
    review.error_category = req.error_category
    review.critical_error = req.critical_error
    review.stt_status = stt_status
    review.stt_error_category = req.stt_error_category
    review.translation_status = req.translation_status
    review.domain = None
    # Legacy columns remain in the database for compatibility, but the simple QA
    # flow no longer asks reviewers to manage them.
    review.consent_for_training = False
    review.pii_status = "pending"
    review.speaker_id_hash = None
    review.use_for_whisper = use_for_whisper
    review.use_for_nllb = use_for_nllb
    review.whisper_split = _stable_split(audio.sha256) if use_for_whisper and audio else None
    pair_key = f"{log.source_lang}|{log.target_lang}|{corrected_source.casefold()}"
    review.nllb_split = _stable_split(pair_key) if use_for_nllb else None
    review.notes = req.notes.strip() if req.notes else None
    _audit(db, user, "quality.resolve", "translation_log", log.id, {
        "adequacy": req.adequacy,
        "fluency": req.fluency,
        "error_category": req.error_category,
        "critical_error": req.critical_error,
        "stt_status": stt_status,
        "translation_status": req.translation_status,
        "use_for_whisper": use_for_whisper,
        "use_for_nllb": use_for_nllb,
    })
    db.commit()
    
    # QA is a review record only; private source text never publishes to any dictionary.
    return {"ok": True, "message": "Đã lưu bản sửa trong lịch sử; không cập nhật từ điển"}


def _stable_split(group_key: str | None) -> str:
    bucket = int(hashlib.sha256((group_key or "missing").encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


@router.post("/quality/logs/{log_id}/audio")
async def upload_quality_audio(
    log_id: int, file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    log = db.query(TranslationLog).filter(TranslationLog.id == log_id).first()
    if not log:
        raise HTTPException(404, "Log not found")
    existing = db.query(TrainingAudioAsset).filter(TrainingAudioAsset.translation_log_id == log_id).first()
    stored = await store_training_wav(file)
    if existing:
        old_file = existing.file_name
        for key, value in stored.items():
            setattr(existing, key, value)
        existing.uploaded_by_user_id = user.id
        asset = existing
    else:
        old_file = None
        asset = TrainingAudioAsset(
            translation_log_id=log.id, uploaded_by_user_id=user.id, **stored,
        )
        db.add(asset)
    log.input_mode = "voice"
    _audit(db, user, "quality.audio.attach", "translation_log", log.id, {
        "duration_ms": stored["duration_ms"], "sha256_prefix": stored["sha256"][:12],
    })
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_training_audio(stored["file_name"])
        raise
    if old_file:
        delete_training_audio(old_file)
    return {"ok": True, "duration_ms": asset.duration_ms, "audio_url": f"/admin/quality/logs/{log.id}/audio"}


@router.get("/quality/logs/{log_id}/audio")
def get_quality_audio(log_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    asset = db.query(TrainingAudioAsset).filter(TrainingAudioAsset.translation_log_id == log_id).first()
    if not asset:
        raise HTTPException(404, "Training audio not found")
    return FileResponse(training_audio_path(asset.file_name), media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.delete("/quality/logs/{log_id}/audio")
def remove_quality_audio(log_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    asset = db.query(TrainingAudioAsset).filter(TrainingAudioAsset.translation_log_id == log_id).first()
    if not asset:
        raise HTTPException(404, "Training audio not found")
    review = db.query(QualityReview).filter(QualityReview.translation_log_id == log_id).first()
    if review:
        review.use_for_whisper = False
        review.whisper_split = None
    file_name = asset.file_name
    db.delete(asset)
    _audit(db, user, "quality.audio.remove", "translation_log", log_id)
    db.commit()
    delete_training_audio(file_name)
    return {"ok": True}

@router.get("/quality/reviews/export")
def export_quality_reviews(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "log_id", "source_lang", "target_lang", "adequacy", "fluency",
        "error_category", "critical_error", "reviewer_user_id", "reviewed_at",
    ])
    rows = db.query(QualityReview, TranslationLog).join(
        TranslationLog, TranslationLog.id == QualityReview.translation_log_id
    ).order_by(QualityReview.id.asc()).all()
    for review, log in rows:
        writer.writerow([
            log.id, log.source_lang, log.target_lang, review.adequacy, review.fluency,
            review.error_category, review.critical_error, review.reviewer_user_id,
            review.updated_at.isoformat() if review.updated_at else "",
        ])
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=quality-reviews.csv"},
    )


def _approved_training_rows(db: Session):
    return db.query(QualityReview, TranslationLog).join(
        TranslationLog, TranslationLog.id == QualityReview.translation_log_id
    ).order_by(QualityReview.id.asc()).all()


@router.get("/training/stats")
def get_training_stats(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rows = _approved_training_rows(db)
    audio_by_log = {
        item.translation_log_id: item for item in db.query(TrainingAudioAsset).all()
    }
    whisper = [
        (review, log, audio_by_log.get(log.id)) for review, log in rows
        if audio_by_log.get(log.id) is not None and review.stt_status in {"correct", "corrected"}
    ]
    nllb = [(review, log) for review, log in rows if review.translation_status in {"correct", "corrected"}]
    return {
        "whisper": {
            "samples": len(whisper),
            "hours": round(sum(asset.duration_ms for _, _, asset in whisper) / 3_600_000, 3),
            "splits": {split: sum(review.whisper_split == split for review, _, _ in whisper)
                       for split in ("train", "validation", "test")},
        },
        "nllb": {
            "samples": len(nllb),
            "directions": {
                "vi-en": sum((log.source_lang, log.target_lang) == ("vi", "en") for _, log in nllb),
                "en-vi": sum((log.source_lang, log.target_lang) == ("en", "vi") for _, log in nllb),
            },
            "splits": {split: sum(review.nllb_split == split for review, _ in nllb)
                       for split in ("train", "validation", "test")},
        },
    }


@router.get("/training/export/nllb")
def export_nllb_training_data(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    lines = []
    for review, log in _approved_training_rows(db):
        if review.translation_status not in {"correct", "corrected"}:
            continue
        source = (review.corrected_source_text or log.source_text).strip()
        target = review.corrected_text.strip()
        if not source or not target:
            continue
        lines.append(json.dumps({
            "id": f"qa-{log.id}", "source_lang": log.source_lang, "target_lang": log.target_lang,
            "source": source, "target": target, "domain": review.domain or "general",
            "split": review.nllb_split or _stable_split(f"{log.source_lang}|{log.target_lang}|{source.casefold()}"),
        }, ensure_ascii=False))
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return StreamingResponse(
        iter([payload]), media_type="application/x-ndjson; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=nllb-training.jsonl"},
    )


@router.get("/training/export/whisper")
def export_whisper_training_data(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    assets = {row.translation_log_id: row for row in db.query(TrainingAudioAsset).all()}
    manifest = []
    output = tempfile.TemporaryFile()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for review, log in _approved_training_rows(db):
            asset = assets.get(log.id)
            if (
                asset is None or review.stt_status not in {"correct", "corrected"}
                or not review.corrected_source_text
            ):
                continue
            archive_name = f"audio/{asset.file_name}"
            archive.write(training_audio_path(asset.file_name), archive_name)
            manifest.append(json.dumps({
                "id": f"qa-{log.id}", "audio": archive_name,
                "text": review.corrected_source_text.strip(), "language": log.source_lang,
                "split": review.whisper_split or _stable_split(asset.sha256),
                "duration_ms": asset.duration_ms, "sha256": asset.sha256,
            }, ensure_ascii=False))
        archive.writestr("manifest.jsonl", "\n".join(manifest) + ("\n" if manifest else ""))
    output.seek(0)
    def stream_archive():
        try:
            while chunk := output.read(1024 * 1024):
                yield chunk
        finally:
            output.close()
    return StreamingResponse(
        stream_archive(), media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=whisper-training.zip"},
    )


# --- SYSTEM & HARDWARE ---
@router.get("/system/status")
def get_system_status(user: User = Depends(require_admin)):
    from app.core.gpu_manager import GPU_MANAGER
    from app.ai.model_manager import model_manager
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()

    # Use current working directory on non-Unix systems that lack '/'.
    disk_path = '/' if os.name != 'nt' else os.getcwd()[:3]
    disk = psutil.disk_usage(disk_path)
    gpu_stats = GPU_MANAGER.get_memory_stats()
    
    return {
        "cpu_usage": cpu_percent,
        "ram_usage": ram.percent,
        "ram_total": round(ram.total / (1024**3), 2), # GB
        "disk_usage": disk.percent,
        "disk_total": round(disk.total / (1024**3), 2),
        "gpu": gpu_stats,
        "models": model_manager.get_status(),
        "inference_runtime": model_manager.get_runtime_status(),
    }

# --- ANALYTICS TIMESERIES & METRICS ---
@router.get("/metrics/timeseries")
def get_metrics_timeseries(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Content-free activity for at most seven days since this process started."""
    return GLOBAL_TELEMETRY.get_activity_summary()["timeseries"]

@router.get("/metrics/languages")
def get_metrics_languages(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Language counters contain no original or translated conversation content."""
    stats = GLOBAL_TELEMETRY.get_activity_summary()["languages"]
    lang_names = {
        "vi": "Tiếng Việt",
        "en": "Tiếng Anh",
        "vie_Latn": "Tiếng Việt",
        "eng_Latn": "Tiếng Anh",
    }
    result = []
    for row in stats:
        s = lang_names.get(row["source_lang"], row["source_lang"])
        t = lang_names.get(row["target_lang"], row["target_lang"])
        result.append({
            "name": f"{s} -> {t}",
            "value": row["value"]
        })
    return result

@router.get("/metrics/pipeline")
def get_metrics_pipeline(user: User = Depends(require_admin)):
    """Số đo hiệu năng thời gian thực toàn pipeline (P50/P90/P99 latency, queue wait, throughput)."""
    return GLOBAL_TELEMETRY.get_summary()

@router.get("/audit")
def get_audit_log(
    actor: str | None = Query(default=None, max_length=100),
    action: str | None = Query(default=None, max_length=64),
    resource_type: str | None = Query(default=None, max_length=32),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    query = db.query(AuditLog)
    if actor:
        query = query.filter(AuditLog.actor_username.ilike(_search_pattern(actor), escape="\\"))
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if created_from:
        query = query.filter(AuditLog.created_at >= created_from.replace(tzinfo=None))
    if created_to:
        query = query.filter(AuditLog.created_at <= created_to.replace(tzinfo=None))
    records = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    return [{
        "id": record.id,
        "actor_username": record.actor_username,
        "action": record.action,
        "resource_type": record.resource_type,
        "resource_id": record.resource_id,
        "details": json.loads(record.details or "{}"),
        "created_at": record.created_at.replace(tzinfo=timezone.utc) if record.created_at else None,
    } for record in records]


# --- API KEYS ---
@router.get("/apikeys", response_model=List[ApiKeyResponse])
def get_api_keys(skip: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=100, ge=1, le=100),
                 search: str | None = Query(default=None, max_length=200),
                 db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    query = db.query(ApiKey)
    if search:
        query = query.filter(ApiKey.name.ilike(_search_pattern(search), escape="\\"))
    return [_key_metadata(key) for key in query.order_by(ApiKey.id.desc()).offset(skip).limit(limit).all()]

def _key_metadata(key: ApiKey) -> dict:
    try:
        scopes = json.loads(key.scopes)
        if not isinstance(scopes, list) or any(not isinstance(scope, str) for scope in scopes):
            scopes = []
    except (TypeError, ValueError):
        scopes = []
    return {
        "id": key.id, "name": key.name, "prefix": key.key_prefix or "legacy-revoked",
        "scopes": sorted(set(scopes) & RESOURCE_SCOPES),
        "expires_at": key.expires_at.replace(tzinfo=timezone.utc) if key.expires_at else None,
        "is_active": key.is_active and key.revoked_at is None,
        "created_at": key.created_at.replace(tzinfo=timezone.utc),
    }

@router.post("/apikeys", response_model=CreatedApiKeyResponse)
def create_api_key(req: ApiKeyCreate, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    try:
        db_key, raw_key = issue_api_key(
            db, name=req.name, owner_id=admin.public_id, scopes=req.scopes,
            expires_at=datetime.now(timezone.utc) + timedelta(days=req.expires_in_days),
            created_by_user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _audit(db, admin, "api_key.create", "api_key", db_key.id, {"scopes": req.scopes})
    db.commit()
    return {**_key_metadata(db_key), "key": raw_key}

@router.delete("/apikeys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    db_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="Key not found")
    db_key.is_active = False
    db_key.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    _audit(db, admin, "api_key.revoke", "api_key", db_key.id)
    db.commit()
    return {"ok": True}


@router.post("/apikeys/{key_id}/rotate", response_model=CreatedApiKeyResponse)
def rotate_api_key(key_id: int, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    old_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not old_key or not old_key.is_active or old_key.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Active key not found")
    metadata = _key_metadata(old_key)
    remaining = old_key.expires_at - datetime.now(timezone.utc).replace(tzinfo=None) if old_key.expires_at else timedelta(days=30)
    days = max(1, min(90, int(remaining.total_seconds() // 86400) or 1))
    try:
        new_key, raw_key = issue_api_key(
            db, name=old_key.name, owner_id=old_key.owner_id,
            scopes=metadata["scopes"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
            created_by_user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    old_key.is_active = False
    old_key.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    _audit(db, admin, "api_key.rotate", "api_key", old_key.id, {"replacement_id": new_key.id})
    db.commit()
    return {**_key_metadata(new_key), "key": raw_key}

# --- SETTINGS ---
@router.get("/settings", response_model=List[SettingResponse])
def get_settings(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return db.query(SystemSetting).filter(SystemSetting.key.in_(
        ["max_chars_per_request", "rate_limit_rpm", "enable_cache"]
    )).all()

@router.put("/settings/{setting_key}", response_model=SettingResponse)
def update_setting(setting_key: str, req: SettingUpdate, db: Session = Depends(get_db), admin: User = Depends(require_superadmin)):
    value = req.value.strip().lower()
    policy = get_policy_settings()
    if setting_key == "enable_cache":
        if value not in {"true", "false"}:
            raise HTTPException(422, "enable_cache must be true or false")
    elif setting_key in {"max_chars_per_request", "rate_limit_rpm"}:
        maximum = min(5000, policy.MAX_TEXT_CHARS) if setting_key == "max_chars_per_request" else min(60, policy.RATE_LIMIT_RPM)
        if not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= maximum:
            raise HTTPException(422, f"{setting_key} must be an integer between 1 and {maximum}")
        value = str(int(value))
    else:
        raise HTTPException(422, "This setting cannot be changed through the admin API")
    setting = db.query(SystemSetting).filter(SystemSetting.key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    previous = setting.value
    setting.value = value
    _audit(db, admin, "setting.update", "setting", setting_key, {
        "previous_value": previous, "new_value": value,
    })
    db.commit()
    db.refresh(setting)
    if setting_key == "enable_cache":
        from app.services.translation_cache import invalidate_all
        invalidate_all()
    return setting


def _default_model_id(component: ModelComponent) -> str:
    from app.core.config import settings
    return {
        "whisper": settings.WHISPER_MODEL,
        "nllb": settings.NLLB_MODEL,
        "tts_eng": settings.TTS_MODEL_ENG,
        "tts_vie": settings.TTS_MODEL_VIE,
    }[component]


def _model_deployment_payload(component: ModelComponent, row: ModelDeployment | None) -> dict:
    return {
        "component": component,
        "active_model": row.active_model if row else _default_model_id(component),
        "canary_model": row.canary_model if row else None,
        "canary_percent": row.canary_percent if row else 0,
        "previous_active_model": row.previous_active_model if row else None,
        "version": row.version if row else 1,
        "updated_at": row.updated_at.replace(tzinfo=timezone.utc) if row and row.updated_at else None,
        "requires_runtime_reload": True,
    }


def _get_or_create_model_deployment(
    db: Session, component: ModelComponent, admin: User,
) -> ModelDeployment:
    row = db.query(ModelDeployment).filter(ModelDeployment.component == component).first()
    if row is None:
        row = ModelDeployment(
            component=component,
            active_model=_default_model_id(component),
            updated_by_user_id=admin.id,
        )
        db.add(row)
        db.flush()
    return row


@router.get("/models/deployments")
def get_model_deployments(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rows = {row.component: row for row in db.query(ModelDeployment).all()}
    return [
        _model_deployment_payload(component, rows.get(component))
        for component in ("whisper", "nllb", "tts_eng", "tts_vie")
    ]


@router.put("/models/{component}/canary")
def configure_model_canary(
    component: ModelComponent, req: ModelCanaryUpdate,
    db: Session = Depends(get_db), admin: User = Depends(require_superadmin),
):
    row = _get_or_create_model_deployment(db, component, admin)
    if req.model_id == row.active_model:
        raise HTTPException(409, "Canary model must differ from the active model")
    row.canary_model = req.model_id
    row.canary_percent = req.percent
    row.version += 1
    row.updated_by_user_id = admin.id
    _audit(db, admin, "model.canary.configure", "model", component, {
        "active_model": row.active_model,
        "canary_model": row.canary_model,
        "canary_percent": row.canary_percent,
        "version": row.version,
    })
    db.commit()
    db.refresh(row)
    return _model_deployment_payload(component, row)


@router.post("/models/{component}/promote")
def promote_model_canary(
    component: ModelComponent, db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    row = _get_or_create_model_deployment(db, component, admin)
    if not row.canary_model:
        raise HTTPException(409, "No canary model is configured")
    previous, promoted = row.active_model, row.canary_model
    row.previous_active_model = previous
    row.active_model = promoted
    row.canary_model = None
    row.canary_percent = 0
    row.version += 1
    row.updated_by_user_id = admin.id
    _audit(db, admin, "model.canary.promote", "model", component, {
        "from": previous, "to": promoted, "version": row.version,
    })
    db.commit()
    db.refresh(row)
    return _model_deployment_payload(component, row)


@router.post("/models/{component}/rollback")
def rollback_model(
    component: ModelComponent, db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    row = _get_or_create_model_deployment(db, component, admin)
    if not row.previous_active_model:
        raise HTTPException(409, "No previous active model is available")
    current, restored = row.active_model, row.previous_active_model
    row.active_model = restored
    row.previous_active_model = current
    row.canary_model = None
    row.canary_percent = 0
    row.version += 1
    row.updated_by_user_id = admin.id
    _audit(db, admin, "model.rollback", "model", component, {
        "from": current, "to": restored, "version": row.version,
    })
    db.commit()
    db.refresh(row)
    return _model_deployment_payload(component, row)

# --- DICTIONARY (TRANSLATION MEMORY) ---
@router.get("/dictionary")
def get_dictionary(skip: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=1000, ge=1, le=1000),
                   search: str | None = Query(default=None, max_length=200),
                   query: str | None = Query(default=None, max_length=200),
                   user: User = Depends(require_admin)):
    rows = tm.get_entries(APPROVED_DICTIONARY)
    needle = (search or query or "").strip().casefold()
    if needle:
        rows = [row for row in rows if needle in row["source_text"].casefold() or needle in row["translated_text"].casefold()]
    rows.sort(key=lambda row: (row["source_text"], row.get("source_lang") or "", row.get("target_lang") or ""))
    return rows[skip:skip + limit]


@router.get("/dictionary/export")
def export_dictionary(user: User = Depends(require_admin)):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["source_text", "translated_text", "source_lang", "target_lang"])
    rows = tm.get_entries(APPROVED_DICTIONARY)
    rows.sort(key=lambda row: (row["source_text"], row.get("source_lang") or "", row.get("target_lang") or ""))
    for row in rows:
        writer.writerow([
            row["source_text"], row["translated_text"],
            row.get("source_lang") or "", row.get("target_lang") or "",
        ])
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=translation-dictionary.csv"},
    )

@router.post("/dictionary")
def add_dictionary_item(item: DictionaryItem, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    source, target = _validated_pair(item.source_text, item.translated_text, db)
    try:
        success = tm.add(
            source, target, client_id=APPROVED_DICTIONARY,
            source_lang=item.source_lang, target_lang=item.target_lang,
        )
    except ValueError:
        raise HTTPException(422, "Invalid dictionary language pair") from None
    except OSError:
        raise HTTPException(503, "Dictionary storage is unavailable") from None
    if not success:
        raise HTTPException(status_code=400, detail="Invalid data")
    _audit(db, user, "dictionary.add", "dictionary", None, {
        "source_lang": item.source_lang, "target_lang": item.target_lang,
    })
    db.commit()
    return {"ok": True}

@router.post("/dictionary/upload")
def upload_dictionary_csv(file: UploadFile = File(...),
                          source_lang: str | None = Form(default=None, max_length=16),
                          target_lang: str | None = Form(default=None, max_length=16), db: Session = Depends(get_db),
                          user: User = Depends(require_superadmin)):
    filename = (file.filename or "").lower()
    try:
        if not filename.endswith((".csv", ".xlsx")):
            raise HTTPException(400, "Chỉ chấp nhận file CSV hoặc Excel (.xlsx)")
        maximum = min(1_000_000, get_policy_settings().MAX_DICTIONARY_UPLOAD_BYTES)
        contents = file.file.read(maximum + 1)
        if len(contents) > maximum:
            raise HTTPException(413, "Dictionary upload exceeds the size limit")
        if not contents:
            raise HTTPException(422, "Dictionary upload is empty")
        # Parse and validate every row before writing anything to the dictionary.
        rows = _parse_dictionary_rows(contents, filename)
        pairs = [_validated_pair(source, target, db) for source, target in rows]
        if not pairs:
            raise HTTPException(422, "Dictionary upload contains no entries")
        try:
            added = tm.add_many([{"source_text": source, "translated_text": target} for source, target in pairs],
                                client_id=APPROVED_DICTIONARY, source_lang=source_lang, target_lang=target_lang)
        except ValueError:
            raise HTTPException(422, "Invalid dictionary entries or language pair") from None
        except OSError:
            raise HTTPException(503, "Dictionary storage is unavailable; no entries were imported") from None
        _audit(db, user, "dictionary.import", "dictionary", None, {
            "source_lang": source_lang, "target_lang": target_lang, "added": added,
        })
        db.commit()
        return {"ok": True, "added": added}
    finally:
        file.file.close()


def _validated_pair(source: str, target: str, db: Session) -> tuple[str, str]:
    source = validate_text(source, db)
    target = validate_text(target, db)
    if max(len(source), len(target)) > 5000 or not source.strip(".,!?;:\"'").strip():
        raise HTTPException(422, "Dictionary entry is invalid")
    return source, target


def _check_xlsx_archive(contents: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            entries = archive.infolist()
            if len(entries) > 100 or sum(entry.file_size for entry in entries) > 5_000_000:
                raise HTTPException(413, "Excel archive exceeds the expanded size or entry limit")
            if len({entry.filename for entry in entries}) != len(entries):
                raise HTTPException(422, "Excel archive contains duplicate entries")
            expanded = 0
            for entry in entries:
                if entry.flag_bits & 1:
                    raise HTTPException(422, "Encrypted Excel files are not supported")
                data = bytearray()
                with archive.open(entry) as stream:
                    while chunk := stream.read(65536):
                        expanded += len(chunk)
                        if expanded > 5_000_000:
                            raise HTTPException(413, "Excel archive exceeds the expanded size limit")
                        data.extend(chunk)
                if entry.filename.lower().endswith((".xml", ".rels")):
                    xml = bytes(data).replace(b"\x00", b"").upper()
                    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
                        raise HTTPException(422, "XML declarations are not supported in dictionary uploads")
                    if entry.filename.lower().startswith("xl/worksheets/"):
                        # Do not trust workbook dimensions: omitted/lying dimensions
                        # must not hide rows beyond the import limit.
                        document = ElementTree.fromstring(bytes(data))
                        row_count = 0
                        for node in document.iter():
                            if node.tag.rsplit("}", 1)[-1] == "row":
                                row_count += 1
                                row_index = int(node.attrib.get("r", row_count))
                                if row_count > 500 or not 1 <= row_index <= 500:
                                    raise HTTPException(413, "Dictionary upload must not exceed 500 rows")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Không thể đọc cấu trúc file Excel")


def _parse_dictionary_rows(contents: bytes, filename: str) -> list[tuple[str, str]]:
    rows = []
    if filename.endswith(".csv"):
        try:
            reader = csv.reader(io.StringIO(contents.decode("utf-8-sig")), strict=True)
            for index, row in enumerate(reader, start=1):
                if index > 500:
                    raise HTTPException(413, "Dictionary upload must not exceed 500 rows")
                if not row or not any(cell.strip() for cell in row):
                    continue
                if len(row) < 2:
                    raise HTTPException(422, "Each dictionary row requires source and translation")
                rows.append((row[0], row[1]))
        except (UnicodeError, csv.Error):
            raise HTTPException(400, "File CSV phải có định dạng UTF-8 và cấu trúc hợp lệ")
    else:
        _check_xlsx_archive(contents)
        workbook = None
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=False, keep_links=False)
            worksheet = workbook.active
            if worksheet is None:
                raise HTTPException(422, "Excel workbook contains no active worksheet")
            if worksheet.max_row is not None and worksheet.max_row > 500:
                raise HTTPException(413, "Dictionary upload must not exceed 500 rows")
            for index, row in enumerate(worksheet.iter_rows(max_row=501, max_col=2), start=1):
                values = [cell.value for cell in row]
                if all(value is None or str(value).strip() == "" for value in values):
                    continue
                if index > 500:
                    raise HTTPException(413, "Dictionary upload must not exceed 500 rows")
                if any(cell.data_type == "f" for cell in row):
                    raise HTTPException(422, "Excel formulas are not supported in dictionary entries")
                rows.append(tuple(str(value) if value is not None else "" for value in values))
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, "Không thể đọc file Excel")
        finally:
            if workbook is not None:
                workbook.close()
    return rows

class DictionaryDelete(BaseModel):
    source_text: str = Field(min_length=1, max_length=5000)
    source_lang: str | None = Field(default=None, max_length=16)
    target_lang: str | None = Field(default=None, max_length=16)
    model_config = {"extra": "forbid"}


@router.post("/dictionary/delete")
def delete_dictionary_entry(item: DictionaryDelete, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    source = validate_text(item.source_text, db)
    try:
        success = tm.delete(source, client_id=APPROVED_DICTIONARY,
                            source_lang=item.source_lang, target_lang=item.target_lang)
    except ValueError:
        raise HTTPException(422, "Invalid dictionary language pair") from None
    except OSError:
        raise HTTPException(503, "Dictionary storage is unavailable") from None
    if not success:
        raise HTTPException(404, "Item not found")
    _audit(db, user, "dictionary.delete", "dictionary", None, {
        "source_lang": item.source_lang, "target_lang": item.target_lang,
    })
    db.commit()
    return {"ok": True}


@router.delete("/dictionary/{source_text:path}")
def delete_dictionary_item(source_text: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    return delete_dictionary_entry(DictionaryDelete(source_text=source_text), db, user)

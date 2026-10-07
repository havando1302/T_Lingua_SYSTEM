"""Administrative control plane for immutable datasets and offline training jobs."""
from __future__ import annotations
from typing import Any

import asyncio
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import require_admin, require_superadmin
from app.core.model_registry import PINNED_MODEL_REVISIONS
from app.db.database import SessionLocal, get_db
from app.db.models import (
    AuditLog, DeploymentEvent, ModelArtifact, ModelDeployment, QualityReview,
    TrainingAudioAsset, TrainingDataset, TrainingJob, TrainingJobEvent,
    TranslationLog, User,
)
from app.services.training_control import (
    artifact_directory, canonical_language, create_qa_snapshot, directory_fingerprint,
    eligible_for_nllb, eligible_for_whisper, file_sha256, preview_qa_snapshot,
    relative_storage_uri, resolve_storage_uri, store_uploaded_dataset,
    validate_dataset_file, validate_dataset_name,
)


router = APIRouter(prefix="/admin/training", tags=["Training control plane"])
ACTIVE_JOB_STATES = {"validating", "queued", "preparing", "training", "evaluating", "merging_lora", "converting", "cancelling"}
ALLOWED_BASE_MODELS = {
    "nllb": {
        "facebook/nllb-200-distilled-600M",
        "facebook/nllb-200-distilled-1.3B",
    },
    "whisper": {
        "openai/whisper-small",
        "openai/whisper-large-v3-turbo",
        "openai/whisper-large-v3",
    },
}
for _models in ALLOWED_BASE_MODELS.values():
    if not _models.issubset(PINNED_MODEL_REVISIONS):
        raise RuntimeError("Every training model must have an immutable approved revision")
TASK_DEFAULTS = {
    "nllb": {"epochs": 3.0, "batch_size": 2, "gradient_accumulation": 8,
             "learning_rate": 2e-4, "max_source_length": 256, "max_target_length": 256},
    "whisper": {"epochs": 3.0, "batch_size": 1, "gradient_accumulation": 16,
                "learning_rate": 1e-4},
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json(value: str | None, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, ValueError):
        return fallback


def _audit(db: Session, actor: User, action: str, resource_type: str,
           resource_id: Any = None, details: dict | None = None) -> None:
    db.add(AuditLog(
        actor_user_id=actor.id, actor_username=actor.username, action=action,
        resource_type=resource_type, resource_id=str(resource_id) if resource_id is not None else None,
        details=json.dumps(details or {}, ensure_ascii=True, separators=(",", ":")),
    ))


def _event(db: Session, job_id: str, message: str, *, event_type: str = "status",
           level: str = "info", metrics: dict | None = None) -> None:
    db.add(TrainingJobEvent(
        job_id=job_id, level=level, event_type=event_type, message=message[:1000],
        metrics_json=json.dumps(metrics or {}, ensure_ascii=True, separators=(",", ":")),
    ))


class DatasetFromQARequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    version: str = Field(min_length=1, max_length=40)
    task: str
    language: str = "all"
    domain: str | None = Field(default=None, max_length=64)
    created_from: date | None = None
    created_to: date | None = None
    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def name_is_safe(cls, value: str) -> str:
        return validate_dataset_name(value)

    @field_validator("task")
    @classmethod
    def task_is_supported(cls, value: str) -> str:
        if value not in {"nllb", "whisper"}:
            raise ValueError("Task must be nllb or whisper")
        return value

    @field_validator("version")
    @classmethod
    def version_is_safe(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,39}", value) or ".." in value:
            raise ValueError("Version contains unsafe characters")
        return value

    @field_validator("language")
    @classmethod
    def language_is_supported(cls, value: str) -> str:
        if value not in {"all", "vi", "en"}:
            raise ValueError("Language must be all, vi or en")
        return value


class JobConfig(BaseModel):
    epochs: float | None = Field(default=None, ge=0.1, le=30)
    batch_size: int | None = Field(default=None, ge=1, le=8)
    gradient_accumulation: int | None = Field(default=None, ge=1, le=128)
    learning_rate: float | None = Field(default=None, gt=0, le=0.01)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    max_source_length: int | None = Field(default=None, ge=32, le=512)
    max_target_length: int | None = Field(default=None, ge=32, le=512)
    runtime: str = "worker"
    model_config = {"extra": "forbid"}

    @field_validator("runtime")
    @classmethod
    def runtime_is_supported(cls, value: str) -> str:
        if value not in {"worker", "local_auto", "local_cpu", "local_gpu", "external_worker", "colab"}:
            raise ValueError("Unsupported compute target")
        return value


class TrainingJobCreate(BaseModel):
    task: str
    dataset_id: str | None = None
    nllb_dataset_id: str | None = None
    whisper_dataset_id: str | None = None
    base_model: str | None = Field(default=None, max_length=200)
    output_version: str = Field(min_length=2, max_length=80)
    method: str = "lora"
    config: JobConfig = Field(default_factory=JobConfig)
    model_config = {"extra": "forbid"}

    @field_validator("task")
    @classmethod
    def task_is_supported(cls, value: str) -> str:
        if value not in {"nllb", "whisper", "both"}:
            raise ValueError("Task must be nllb, whisper or both")
        return value

    @field_validator("output_version")
    @classmethod
    def version_is_safe(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,79}", value) or ".." in value:
            raise ValueError("Output version contains unsafe characters")
        return value

    @field_validator("method")
    @classmethod
    def method_is_safe(cls, value: str) -> str:
        if value != "lora":
            raise ValueError("Only LoRA is enabled in the web control plane")
        return value


def _dataset_payload(row: TrainingDataset) -> dict:
    return {
        "id": row.id, "name": row.name, "task": row.task, "source_type": row.source_type,
        "source_langs": _json(row.source_langs, []), "version": row.version, "status": row.status,
        "sample_count": row.sample_count, "duration_seconds": row.duration_seconds,
        "train_count": row.train_count, "validation_count": row.validation_count,
        "test_count": row.test_count, "sha256": row.sha256, "size_bytes": row.size_bytes,
        "validation": _json(row.validation_json, {}), "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at.replace(tzinfo=timezone.utc) if row.created_at else None,
        "validated_at": row.validated_at.replace(tzinfo=timezone.utc) if row.validated_at else None,
        "frozen_at": row.frozen_at.replace(tzinfo=timezone.utc) if row.frozen_at else None,
    }


def _job_payload(row: TrainingJob) -> dict:
    return {
        "id": row.id, "group_id": row.group_id, "depends_on_job_id": row.depends_on_job_id,
        "task": row.task, "dataset_id": row.dataset_id, "base_model": row.base_model,
        "output_version": row.output_version, "method": row.method,
        "config": _json(row.config_json, {}), "worker_id": row.worker_id, "status": row.status,
        "progress_percent": row.progress_percent, "current_epoch": row.current_epoch,
        "current_step": row.current_step, "total_steps": row.total_steps,
        "train_loss": row.train_loss, "validation_loss": row.validation_loss,
        "eta_seconds": row.eta_seconds, "artifact_id": row.artifact_id,
        "error_code": row.error_code, "error_message": row.error_message,
        "started_by_user_id": row.started_by_user_id,
        "created_at": row.created_at.replace(tzinfo=timezone.utc) if row.created_at else None,
        "started_at": row.started_at.replace(tzinfo=timezone.utc) if row.started_at else None,
        "finished_at": row.finished_at.replace(tzinfo=timezone.utc) if row.finished_at else None,
        "cancel_requested_at": row.cancel_requested_at.replace(tzinfo=timezone.utc) if row.cancel_requested_at else None,
    }


def _artifact_payload(row: ModelArtifact, deployment: ModelDeployment | None = None) -> dict:
    model_reference = row.storage_uri
    deployment_state = "candidate"
    if deployment:
        if deployment.active_model == model_reference:
            deployment_state = "active"
        elif deployment.previous_active_model == model_reference:
            deployment_state = "previous"
        elif deployment.canary_model == model_reference:
            deployment_state = "canary"
    return {
        "id": row.id, "component": row.component, "version": row.version,
        "base_model": row.base_model, "dataset_id": row.dataset_id, "job_id": row.job_id,
        "format": row.format, "storage_uri": row.storage_uri,
        "sha256": row.sha256, "size_bytes": row.size_bytes,
        "status": row.status, "metrics": _json(row.metrics_json, {}),
        "deployment_state": deployment_state,
        "created_at": row.created_at.replace(tzinfo=timezone.utc) if row.created_at else None,
        "validated_at": row.validated_at.replace(tzinfo=timezone.utc) if row.validated_at else None,
        "requires_runtime_reload": True,
    }


@router.get("/overview")
def training_overview(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    reviewed = db.query(QualityReview, TranslationLog).join(
        TranslationLog, TranslationLog.id == QualityReview.translation_log_id
    ).all()
    assets = {row.translation_log_id: row for row in db.query(TrainingAudioAsset).all()}
    whisper = [(review, log, assets.get(log.id)) for review, log in reviewed
               if eligible_for_whisper(review, assets.get(log.id))]
    nllb = [(review, log) for review, log in reviewed if eligible_for_nllb(review)]
    whisper_splits = {split: sum(review.whisper_split == split for review, _, _ in whisper)
                      for split in ("train", "validation", "test")}
    nllb_splits = {split: sum(review.nllb_split == split for review, _ in nllb)
                   for split in ("train", "validation", "test")}
    hours_by_language = {
        language: round(sum(asset.duration_ms for _, log, asset in whisper if log.source_lang == language) / 3_600_000, 3)
        for language in ("vi", "en")
    }
    active_job = db.query(TrainingJob).filter(TrainingJob.status.in_(ACTIVE_JOB_STATES)).order_by(TrainingJob.created_at.asc()).first()
    try:
        from app.core.gpu_manager import GPU_MANAGER
        gpu = GPU_MANAGER.get_memory_stats()
    except Exception:
        gpu = {"available": False}
    return {
        "runtime": {"status": "online", "gpu": gpu,
                    "worker": "busy" if active_job and active_job.worker_id else "waiting" if active_job else "idle",
                    "active_job_id": active_job.id if active_job else None,
                    "scope": "api_host"},
        "qa": {
            "reviewed": len(reviewed),
            "pending": db.query(TranslationLog).filter(
                TranslationLog.is_flagged == True, TranslationLog.is_reviewed == False
            ).count(),
            "eligible_nllb": len(nllb), "eligible_whisper": len(whisper),
            "blocked_consent": sum(not review.consent_for_training for review, _ in reviewed),
            "blocked_pii": sum(review.pii_status not in {"clean", "redacted"} for review, _ in reviewed),
        },
        "whisper": {
            "samples": len(whisper), "hours": round(sum(asset.duration_ms for _, _, asset in whisper) / 3_600_000, 3),
            "hours_by_language": hours_by_language, "splits": whisper_splits,
            "ready": bool(whisper_splits["train"] and whisper_splits["validation"]),
            "recommended_hours": 10,
        },
        "nllb": {
            "samples": len(nllb), "directions": {
                "vi-en": sum((canonical_language(log.source_lang), canonical_language(log.target_lang)) == ("vi", "en") for _, log in nllb),
                "en-vi": sum((canonical_language(log.source_lang), canonical_language(log.target_lang)) == ("en", "vi") for _, log in nllb),
            }, "splits": nllb_splits,
            "ready": bool(nllb_splits["train"] and nllb_splits["validation"]),
            "recommended_pairs_per_direction": 5000,
        },
        "playground": {"available": False, "reason": "Candidate inference runner is not configured"},
    }


@router.post("/datasets/preview-from-qa")
def preview_dataset_from_qa(req: DatasetFromQARequest, db: Session = Depends(get_db),
                            user: User = Depends(require_admin)):
    if req.created_from and req.created_to and req.created_from > req.created_to:
        raise HTTPException(422, "created_from must not be after created_to")
    return preview_qa_snapshot(
        db, req.task, domain=req.domain, language=None if req.language == "all" else req.language,
        created_from=req.created_from, created_to=req.created_to,
    )


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return [_dataset_payload(row) for row in db.query(TrainingDataset).order_by(TrainingDataset.created_at.desc()).all()]


@router.post("/datasets/from-qa", status_code=201)
def create_dataset_from_qa(req: DatasetFromQARequest, db: Session = Depends(get_db),
                           user: User = Depends(require_admin)):
    if req.created_from and req.created_to and req.created_from > req.created_to:
        raise HTTPException(422, "created_from must not be after created_to")
    preview = preview_qa_snapshot(
        db, req.task, domain=req.domain, language=None if req.language == "all" else req.language,
        created_from=req.created_from, created_to=req.created_to,
    )
    if not preview["ready"]:
        raise HTTPException(422, "; ".join(preview["reasons"]) or "Dataset is not ready")
    row = TrainingDataset(
        name=req.name, task=req.task, source_type="qa", source_langs="[]", version=req.version,
        status="draft", storage_uri="pending", created_by_user_id=user.id,
    )
    db.add(row)
    try:
        db.flush()
        path = create_qa_snapshot(
            db, row, domain=req.domain, language=None if req.language == "all" else req.language,
            created_from=req.created_from, created_to=req.created_to,
        )
        row.storage_uri = relative_storage_uri(path)
        row.sha256 = file_sha256(path)
        row.size_bytes = path.stat().st_size
        _audit(db, user, "training.dataset.create_from_qa", "training_dataset", row.id,
               {"task": row.task, "version": row.version})
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dataset name already exists") from None
    except Exception:
        db.rollback()
        raise
    return _dataset_payload(row)


@router.post("/datasets/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...), name: str = Form(...), version: str = Form(...),
    task: str = Form(...), rights_confirmed: bool = Form(...),
    db: Session = Depends(get_db), user: User = Depends(require_admin),
):
    name = validate_dataset_name(name)
    if task not in {"nllb", "whisper"}:
        raise HTTPException(422, "Task must be nllb or whisper")
    version = version.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,39}", version) or ".." in version:
        raise HTTPException(422, "Version contains unsafe characters")
    if not rights_confirmed:
        raise HTTPException(422, "You must confirm the right to use this dataset")
    row = TrainingDataset(
        name=name, task=task, source_type="upload", source_langs="[]", version=version,
        status="draft", storage_uri="pending", created_by_user_id=user.id,
    )
    db.add(row)
    try:
        db.flush()
        path = await store_uploaded_dataset(row, file)
        row.storage_uri = relative_storage_uri(path)
        row.sha256 = file_sha256(path)
        row.size_bytes = path.stat().st_size
        _audit(db, user, "training.dataset.upload", "training_dataset", row.id,
               {"task": task, "size_bytes": row.size_bytes})
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dataset name already exists") from None
    except Exception:
        db.rollback()
        raise
    return _dataset_payload(row)


@router.post("/datasets/{dataset_id}/validate")
def validate_dataset(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    row = db.get(TrainingDataset, dataset_id)
    if row is None:
        raise HTTPException(404, "Dataset not found")
    if row.status == "frozen":
        raise HTTPException(409, "Frozen datasets are immutable")
    row.status = "validating"
    db.commit()
    try:
        report, canonical = validate_dataset_file(row)
    except Exception:
        row = db.get(TrainingDataset, dataset_id)
        row.status = "invalid"
        row.validation_json = json.dumps({"valid": False, "errors": ["Dataset validation failed"]})
        db.commit()
        raise
    row = db.get(TrainingDataset, dataset_id)
    row.validation_json = json.dumps(report, ensure_ascii=False)
    row.status = "validated" if report["valid"] else "invalid"
    row.sample_count = report["sample_count"]
    row.duration_seconds = report["duration_seconds"]
    row.train_count = report["train_count"]
    row.validation_count = report["validation_count"]
    row.test_count = report["test_count"]
    row.source_langs = json.dumps(report.get("languages", []), ensure_ascii=False)
    row.validated_at = _utcnow()
    if report["valid"]:
        row.storage_uri = relative_storage_uri(canonical)
        row.sha256 = file_sha256(canonical)
        row.size_bytes = canonical.stat().st_size
    _audit(db, user, "training.dataset.validate", "training_dataset", row.id,
           {"valid": report["valid"], "samples": report["sample_count"]})
    db.commit()
    db.refresh(row)
    return _dataset_payload(row)


@router.post("/datasets/{dataset_id}/freeze")
def freeze_dataset(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    row = db.get(TrainingDataset, dataset_id)
    if row is None:
        raise HTTPException(404, "Dataset not found")
    if row.status != "validated":
        raise HTTPException(409, "Dataset must pass validation before it can be frozen")
    path = resolve_storage_uri(row.storage_uri)
    digest = file_sha256(path)
    if digest != row.sha256:
        raise HTTPException(409, "Dataset changed after validation; validate it again")
    row.status = "frozen"
    row.frozen_at = _utcnow()
    manifest = {
        "schema_version": 1, "dataset_id": row.id, "name": row.name, "version": row.version,
        "task": row.task, "sha256": row.sha256, "size_bytes": row.size_bytes,
        "sample_count": row.sample_count, "duration_seconds": row.duration_seconds,
        "splits": {"train": row.train_count, "validation": row.validation_count, "test": row.test_count},
        "source_langs": _json(row.source_langs, []), "validation": _json(row.validation_json, {}),
        "frozen_at": row.frozen_at.replace(tzinfo=timezone.utc).isoformat(),
    }
    (path.parent / "dataset-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _audit(db, user, "training.dataset.freeze", "training_dataset", row.id, {"sha256": row.sha256})
    db.commit()
    db.refresh(row)
    return _dataset_payload(row)


@router.get("/datasets/{dataset_id}/download")
def download_dataset(dataset_id: str, kind: str = Query(default="dataset", pattern="^(dataset|manifest)$"),
                     db: Session = Depends(get_db), user: User = Depends(require_admin)):
    row = db.get(TrainingDataset, dataset_id)
    if row is None:
        raise HTTPException(404, "Dataset not found")
    path = resolve_storage_uri(row.storage_uri)
    if kind == "manifest":
        path = path.parent / "dataset-manifest.json"
        if not path.is_file():
            raise HTTPException(409, "Freeze the dataset before downloading its manifest")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


def _normalised_config(task: str, supplied: JobConfig) -> dict:
    config = dict(TASK_DEFAULTS[task])
    for key, value in supplied.model_dump().items():
        if value is not None:
            config[key] = value
    if task == "whisper":
        config.pop("max_source_length", None)
        config.pop("max_target_length", None)
    return config


def _new_job(db: Session, *, task: str, dataset_id: str, base_model: str | None,
             output_version: str, config: JobConfig, actor: User,
             group_id: str | None = None, depends_on: str | None = None) -> TrainingJob:
    dataset = db.get(TrainingDataset, dataset_id)
    if dataset is None or dataset.task != task:
        raise HTTPException(422, f"A {task} dataset is required")
    if dataset.status != "frozen":
        raise HTTPException(409, f"Dataset {dataset.name} must be frozen before training")
    selected_model = base_model or ("facebook/nllb-200-distilled-1.3B" if task == "nllb" else "openai/whisper-large-v3-turbo")
    if selected_model not in ALLOWED_BASE_MODELS[task]:
        raise HTTPException(422, "Base model is not in the training allowlist")
    if db.query(TrainingJob).filter(TrainingJob.output_version == output_version).first():
        raise HTTPException(409, "Output version already exists")
    row = TrainingJob(
        task=task, dataset_id=dataset.id, base_model=selected_model,
        output_version=output_version, method="lora",
        config_json=json.dumps(_normalised_config(task, config), separators=(",", ":")),
        status="queued", progress_percent=0, started_by_user_id=actor.id,
        group_id=group_id, depends_on_job_id=depends_on,
    )
    db.add(row)
    db.flush()
    _event(db, row.id, "Job accepted into the durable training queue", event_type="queued")
    return row


@router.get("/jobs")
def list_jobs(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db),
              user: User = Depends(require_admin)):
    return [_job_payload(row) for row in db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(limit).all()]


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    row = db.get(TrainingJob, job_id)
    if row is None:
        raise HTTPException(404, "Training job not found")
    return _job_payload(row)


@router.post("/jobs", status_code=201)
def create_job(req: TrainingJobCreate, db: Session = Depends(get_db),
               user: User = Depends(require_superadmin)):
    if db.query(TrainingJob).filter(TrainingJob.status.in_(ACTIVE_JOB_STATES)).count() >= 20:
        raise HTTPException(409, "Training queue is full")
    jobs: list[TrainingJob] = []
    if req.task == "both":
        if not req.nllb_dataset_id or not req.whisper_dataset_id:
            raise HTTPException(422, "Both dataset identifiers are required")
        group_id = str(uuid.uuid4())
        first = _new_job(db, task="nllb", dataset_id=req.nllb_dataset_id, base_model=None,
                         output_version=f"{req.output_version}-nllb", config=req.config,
                         actor=user, group_id=group_id)
        second = _new_job(db, task="whisper", dataset_id=req.whisper_dataset_id, base_model=None,
                          output_version=f"{req.output_version}-whisper", config=req.config,
                          actor=user, group_id=group_id, depends_on=first.id)
        jobs.extend((first, second))
    else:
        if not req.dataset_id:
            raise HTTPException(422, "Dataset identifier is required")
        jobs.append(_new_job(db, task=req.task, dataset_id=req.dataset_id,
                             base_model=req.base_model, output_version=req.output_version,
                             config=req.config, actor=user))
    _audit(db, user, "training.job.create", "training_job", jobs[0].id,
           {"task": req.task, "job_ids": [row.id for row in jobs]})
    db.commit()
    for row in jobs:
        db.refresh(row)
    return {"jobs": [_job_payload(row) for row in jobs]}


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    row = db.get(TrainingJob, job_id)
    if row is None:
        raise HTTPException(404, "Training job not found")
    if row.status not in ACTIVE_JOB_STATES:
        raise HTTPException(409, "This job is no longer cancellable")
    row.cancel_requested_at = _utcnow()
    if row.status == "queued":
        row.status = "cancelled"
        row.finished_at = _utcnow()
        _event(db, row.id, "Queued job cancelled before a worker claimed it", event_type="cancelled")
        dependents = db.query(TrainingJob).filter(
            TrainingJob.depends_on_job_id == row.id, TrainingJob.status == "queued"
        ).all()
        for dependent in dependents:
            dependent.status = "failed"
            dependent.error_code = "DEPENDENCY_CANCELLED"
            dependent.error_message = "The preceding job in this group was cancelled"
            dependent.finished_at = _utcnow()
            _event(db, dependent.id, dependent.error_message, event_type="failed", level="error")
    else:
        row.status = "cancelling"
        _event(db, row.id, "Cancellation requested; worker will stop the training process", event_type="cancelling")
    _audit(db, user, "training.job.cancel", "training_job", row.id)
    db.commit()
    db.refresh(row)
    return _job_payload(row)


@router.get("/jobs/{job_id}/events")
def job_events(job_id: str, after: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=1000),
               db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.get(TrainingJob, job_id) is None:
        raise HTTPException(404, "Training job not found")
    rows = db.query(TrainingJobEvent).filter(
        TrainingJobEvent.job_id == job_id, TrainingJobEvent.id > after
    ).order_by(TrainingJobEvent.id.asc()).limit(limit).all()
    return [{"id": row.id, "level": row.level, "event_type": row.event_type,
             "message": row.message, "metrics": _json(row.metrics_json, {}),
             "created_at": row.created_at.replace(tzinfo=timezone.utc)} for row in rows]


@router.get("/jobs/{job_id}/log")
def download_job_log(job_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(404, "Training job not found")
    rows = db.query(TrainingJobEvent).filter(
        TrainingJobEvent.job_id == job_id
    ).order_by(TrainingJobEvent.id.asc()).all()
    lines = [
        f"{row.created_at.replace(tzinfo=timezone.utc).isoformat()} [{row.level.upper()}] "
        f"{row.event_type}: {row.message}\n" for row in rows
    ]
    return StreamingResponse(
        iter([line.encode("utf-8") for line in lines]), media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="training-{job.id}.log"'},
    )


@router.get("/jobs/{job_id}/events/stream")
def stream_job_events(job_id: str, request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    if db.get(TrainingJob, job_id) is None:
        raise HTTPException(404, "Training job not found")

    async def generate():
        cursor = 0
        idle = 0
        while idle < 120 and not await request.is_disconnected():
            with SessionLocal() as session:
                events = session.query(TrainingJobEvent).filter(
                    TrainingJobEvent.job_id == job_id, TrainingJobEvent.id > cursor
                ).order_by(TrainingJobEvent.id.asc()).limit(200).all()
                job = session.get(TrainingJob, job_id)
                payloads = [{"id": event.id, "level": event.level, "event_type": event.event_type,
                             "message": event.message, "metrics": _json(event.metrics_json, {}),
                             "created_at": event.created_at.replace(tzinfo=timezone.utc).isoformat()}
                            for event in events]
            if payloads:
                idle = 0
                for payload in payloads:
                    cursor = payload["id"]
                    yield f"id: {cursor}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            else:
                idle += 1
                yield ": keepalive\n\n"
            if job and job.status in {"completed", "failed", "cancelled"} and not payloads:
                break
            await asyncio.sleep(1)
    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/models")
def list_models(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    deployments = {row.component: row for row in db.query(ModelDeployment).all()}
    return [_artifact_payload(row, deployments.get(row.component)) for row in
            db.query(ModelArtifact).order_by(ModelArtifact.created_at.desc()).all()]


@router.post("/models/{artifact_id}/validate")
def validate_model_artifact(artifact_id: str, db: Session = Depends(get_db),
                            user: User = Depends(require_admin)):
    artifact = db.get(ModelArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(404, "Model artifact not found")
    path = resolve_storage_uri(artifact.storage_uri, require_file=False)
    if not path.is_dir() or not (path / "training_manifest.json").is_file():
        artifact.status = "invalid"
        db.commit()
        raise HTTPException(422, "Artifact is incomplete or missing its training manifest")
    digest, size = directory_fingerprint(path)
    if digest != artifact.sha256 or size != artifact.size_bytes:
        artifact.status = "invalid"
        db.commit()
        raise HTTPException(409, "Artifact checksum or size does not match the registered release")
    metrics_path = path / "evaluation_metrics.json"
    try:
        evaluation = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        evaluation = {}
    required_metrics = {
        "nllb": {"test_bleu", "test_chrf"},
        "whisper": {"test_wer", "test_cer"},
    }.get(artifact.component, set())
    if not isinstance(evaluation, dict) or not required_metrics.issubset(evaluation):
        artifact.status = "invalid"
        db.commit()
        raise HTTPException(
            422,
            "Artifact is missing locked-test evaluation metrics and cannot be deployed",
        )
    artifact.status = "validated"
    artifact.validated_at = _utcnow()
    _audit(db, user, "training.artifact.validate", "model_artifact", artifact.id,
           {"component": artifact.component, "version": artifact.version})
    db.commit()
    db.refresh(artifact)
    deployment = db.query(ModelDeployment).filter(ModelDeployment.component == artifact.component).first()
    return _artifact_payload(artifact, deployment)


def _deployment_for(db: Session, component: str, user: User) -> ModelDeployment:
    row = db.query(ModelDeployment).filter(ModelDeployment.component == component).first()
    if row is None:
        from app.core.config import settings
        active = settings.NLLB_MODEL if component == "nllb" else settings.WHISPER_TORCH_MODEL
        row = ModelDeployment(component=component, active_model=active, updated_by_user_id=user.id)
        db.add(row)
        db.flush()
    return row


@router.post("/models/{artifact_id}/canary")
def stage_model_canary(artifact_id: str, percent: int = Query(default=5, ge=1, le=50),
                       db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    artifact = db.get(ModelArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(404, "Model artifact not found")
    if artifact.status != "validated":
        raise HTTPException(409, "Artifact must be validated before deployment")
    deployment = _deployment_for(db, artifact.component, user)
    deployment.canary_model = artifact.storage_uri
    deployment.canary_percent = percent
    deployment.version += 1
    deployment.updated_by_user_id = user.id
    db.add(DeploymentEvent(
        component=artifact.component, from_artifact=deployment.active_model,
        to_artifact=artifact.storage_uri, strategy="canary", canary_percent=percent,
        status="pending_reload", requested_by_user_id=user.id,
    ))
    _audit(db, user, "training.model.canary", "model_artifact", artifact.id,
           {"percent": percent, "requires_runtime_reload": True})
    db.commit()
    return {"ok": True, "requires_runtime_reload": True,
            "message": "Canary recorded in the control plane; reload an inference worker before routing traffic"}


@router.post("/models/{artifact_id}/promote")
def promote_model(artifact_id: str, db: Session = Depends(get_db),
                  user: User = Depends(require_superadmin)):
    artifact = db.get(ModelArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(404, "Model artifact not found")
    deployment = _deployment_for(db, artifact.component, user)
    if deployment.canary_model != artifact.storage_uri:
        raise HTTPException(409, "Stage this artifact as canary before promotion")
    previous = deployment.active_model
    deployment.previous_active_model = previous
    deployment.active_model = artifact.storage_uri
    deployment.canary_model = None
    deployment.canary_percent = 0
    deployment.version += 1
    deployment.updated_by_user_id = user.id
    db.add(DeploymentEvent(
        component=artifact.component, from_artifact=previous, to_artifact=artifact.storage_uri,
        strategy="promote_after_restart", status="pending_reload", requested_by_user_id=user.id,
    ))
    _audit(db, user, "training.model.promote", "model_artifact", artifact.id,
           {"requires_runtime_reload": True})
    db.commit()
    return {"ok": True, "requires_runtime_reload": True,
            "message": "Promotion recorded; update runtime configuration and restart with health checks"}


@router.post("/models/{artifact_id}/rollback")
def rollback_model(artifact_id: str, db: Session = Depends(get_db),
                   user: User = Depends(require_superadmin)):
    artifact = db.get(ModelArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(404, "Model artifact not found")
    deployment = _deployment_for(db, artifact.component, user)
    if not deployment.previous_active_model:
        raise HTTPException(409, "No previous model is registered for rollback")
    current, restored = deployment.active_model, deployment.previous_active_model
    deployment.active_model = restored
    deployment.previous_active_model = current
    deployment.canary_model = None
    deployment.canary_percent = 0
    deployment.version += 1
    deployment.updated_by_user_id = user.id
    db.add(DeploymentEvent(
        component=artifact.component, from_artifact=current, to_artifact=restored,
        strategy="rollback_after_restart", status="pending_reload", requested_by_user_id=user.id,
    ))
    _audit(db, user, "training.model.rollback", "model_artifact", artifact.id,
           {"requires_runtime_reload": True})
    db.commit()
    return {"ok": True, "requires_runtime_reload": True,
            "message": "Rollback recorded; restart the inference runtime and run health checks"}


@router.post("/playground/nllb")
@router.post("/playground/whisper")
def unavailable_playground(user: User = Depends(require_admin)):
    raise HTTPException(503, "A/B candidate runner is not configured; no synthetic result was generated")

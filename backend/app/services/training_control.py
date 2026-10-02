"""Dataset snapshots and validation for the offline training control plane."""
from __future__ import annotations

import csv
from datetime import date, datetime, time, timedelta
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import unicodedata
import wave
import zipfile

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.models import QualityReview, TrainingAudioAsset, TrainingDataset, TranslationLog
from app.services.training_audio_storage import training_audio_path


BACKEND_DIR = Path(__file__).resolve().parents[2]
CONTROL_ROOT = Path(os.getenv(
    "TRAINING_CONTROL_ROOT", str(BACKEND_DIR / "data" / "training_control")
)).expanduser()
MAX_DATASET_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 8 * 1024 * 1024 * 1024
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,119}$")
_SPLITS = {"train", "validation", "test"}
_LANGS = {"vi", "en", "vie_Latn", "eng_Latn"}
_CANONICAL_LANGS = {
    "vi": "vi", "vie_Latn": "vi",
    "en": "en", "eng_Latn": "en",
}


def canonical_language(value: str | None) -> str:
    """Keep persisted/exported training data on one stable language-code scheme."""
    return _CANONICAL_LANGS.get((value or "").strip(), (value or "").strip())


def has_training_clearance(review: QualityReview) -> bool:
    return bool(review.consent_for_training and review.pii_status in {"clean", "redacted"})


def eligible_for_nllb(review: QualityReview) -> bool:
    return bool(
        has_training_clearance(review)
        and review.use_for_nllb
        and review.translation_status in {"correct", "corrected"}
    )


def eligible_for_whisper(review: QualityReview, asset: TrainingAudioAsset | None) -> bool:
    return bool(
        asset is not None
        and has_training_clearance(review)
        and review.use_for_whisper
        and review.stt_status in {"correct", "corrected"}
        and (review.corrected_source_text or "").strip()
    )


def validate_dataset_name(value: str) -> str:
    value = value.strip()
    if not _SAFE_NAME.fullmatch(value) or ".." in value:
        raise HTTPException(422, "Dataset name may contain only letters, numbers, dot, dash and underscore")
    return value


def ensure_control_root() -> Path:
    CONTROL_ROOT.mkdir(parents=True, exist_ok=True)
    return CONTROL_ROOT


def dataset_directory(dataset_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f-]{36}", dataset_id):
        raise HTTPException(404, "Dataset not found")
    root = ensure_control_root().resolve()
    path = (root / "datasets" / dataset_id).resolve()
    if root not in path.parents:
        raise HTTPException(404, "Dataset not found")
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_directory(job_id: str, version: str) -> Path:
    if not re.fullmatch(r"[0-9a-f-]{36}", job_id) or not _SAFE_NAME.fullmatch(version):
        raise ValueError("Unsafe artifact identifier")
    root = ensure_control_root().resolve()
    path = (root / "artifacts" / f"{version}-{job_id}").resolve()
    if root not in path.parents:
        raise ValueError("Unsafe artifact path")
    return path


def relative_storage_uri(path: Path) -> str:
    return path.resolve().relative_to(ensure_control_root().resolve()).as_posix()


def resolve_storage_uri(uri: str, *, require_file: bool = True) -> Path:
    root = ensure_control_root().resolve()
    path = (root / PurePosixPath(uri)).resolve()
    if root not in path.parents:
        raise HTTPException(404, "Training asset not found")
    if require_file and not path.is_file():
        raise HTTPException(404, "Training asset not found")
    return path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def directory_fingerprint(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    for item in sorted((entry for entry in path.rglob("*") if entry.is_file()), key=lambda entry: entry.as_posix()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        with item.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                total += len(chunk)
                digest.update(chunk)
    return digest.hexdigest(), total


def stable_split(key: str | None) -> str:
    bucket = int(hashlib.sha256((key or "missing").encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


def _qa_rows(db: Session, domain: str | None, language: str | None,
             created_from: date | None = None, created_to: date | None = None):
    query = db.query(QualityReview, TranslationLog).join(
        TranslationLog, TranslationLog.id == QualityReview.translation_log_id
    )
    if domain:
        query = query.filter(QualityReview.domain == domain)
    if language == "vi":
        query = query.filter(TranslationLog.source_lang.in_(("vi", "vie_Latn")))
    elif language == "en":
        query = query.filter(TranslationLog.source_lang.in_(("en", "eng_Latn")))
    if created_from:
        query = query.filter(TranslationLog.created_at >= datetime.combine(created_from, time.min))
    if created_to:
        query = query.filter(TranslationLog.created_at < datetime.combine(created_to + timedelta(days=1), time.min))
    return query.order_by(QualityReview.id.asc()).all()


def preview_qa_snapshot(db: Session, task: str, *, domain: str | None = None,
                        language: str | None = None, created_from: date | None = None,
                        created_to: date | None = None) -> dict:
    """Return a read-only readiness report using the exact snapshot eligibility rules."""
    rows = _qa_rows(db, domain, language, created_from, created_to)
    assets = {row.translation_log_id: row for row in db.query(TrainingAudioAsset).all()}
    selected: list[tuple[QualityReview, TranslationLog, TrainingAudioAsset | None]] = []
    blockers = {"no_consent": 0, "pii_not_cleared": 0, "not_approved": 0, "missing_audio": 0}

    for review, log in rows:
        asset = assets.get(log.id)
        if not review.consent_for_training:
            blockers["no_consent"] += 1
        if review.pii_status not in {"clean", "redacted"}:
            blockers["pii_not_cleared"] += 1
        if task == "nllb":
            if not review.use_for_nllb or review.translation_status not in {"correct", "corrected"}:
                blockers["not_approved"] += 1
            if eligible_for_nllb(review):
                selected.append((review, log, asset))
        else:
            if asset is None:
                blockers["missing_audio"] += 1
            if not review.use_for_whisper or review.stt_status not in {"correct", "corrected"}:
                blockers["not_approved"] += 1
            if eligible_for_whisper(review, asset):
                selected.append((review, log, asset))

    split_field = "nllb_split" if task == "nllb" else "whisper_split"
    splits = {name: 0 for name in _SPLITS}
    directions: dict[str, int] = {}
    duration_seconds = 0.0
    for review, log, asset in selected:
        if task == "nllb":
            source = (review.corrected_source_text or log.source_text or "").strip()
            split = getattr(review, split_field) or stable_split(
                f"{canonical_language(log.source_lang)}|{canonical_language(log.target_lang)}|{source.casefold()}"
            )
            direction = f"{canonical_language(log.source_lang)}->{canonical_language(log.target_lang)}"
            directions[direction] = directions.get(direction, 0) + 1
        else:
            split = getattr(review, split_field) or stable_split(asset.sha256 if asset else None)
            duration_seconds += (asset.duration_ms if asset else 0) / 1000
        splits[split] += 1

    ready = bool(splits["train"] and splits["validation"])
    reasons = []
    if not selected:
        reasons.append("Không có mẫu đủ điều kiện sử dụng để huấn luyện")
    if not splits["train"]:
        reasons.append("Thiếu dữ liệu train")
    if not splits["validation"]:
        reasons.append("Thiếu dữ liệu validation")
    return {
        "task": task, "reviewed": len(rows), "eligible": len(selected),
        "splits": splits, "directions": directions,
        "duration_seconds": round(duration_seconds, 3),
        "blockers": blockers, "ready": ready, "reasons": reasons,
    }


def create_qa_snapshot(db: Session, dataset: TrainingDataset, *, domain: str | None = None,
                       language: str | None = None, created_from: date | None = None,
                       created_to: date | None = None) -> Path:
    destination = dataset_directory(dataset.id)
    rows = _qa_rows(db, domain, language, created_from, created_to)
    if dataset.task == "nllb":
        path = destination / "nllb-training.jsonl"
        with path.open("x", encoding="utf-8", newline="\n") as output:
            for review, log in rows:
                if not eligible_for_nllb(review):
                    continue
                source = (review.corrected_source_text or log.source_text or "").strip()
                target = (review.corrected_text or "").strip()
                if not source or not target:
                    continue
                output.write(json.dumps({
                    "id": f"qa-{log.id}", "source_lang": canonical_language(log.source_lang),
                    "target_lang": canonical_language(log.target_lang), "source": source, "target": target,
                    "domain": review.domain or "general",
                    "split": review.nllb_split or stable_split(
                        f"{canonical_language(log.source_lang)}|{canonical_language(log.target_lang)}|{source.casefold()}"
                    ),
                }, ensure_ascii=False) + "\n")
        return path

    if dataset.task != "whisper":
        raise HTTPException(422, "Unsupported training task")
    assets = {row.translation_log_id: row for row in db.query(TrainingAudioAsset).all()}
    path = destination / "whisper-training.zip"
    manifest: list[str] = []
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_STORED) as archive:
        for review, log in rows:
            asset = assets.get(log.id)
            if not eligible_for_whisper(review, asset):
                continue
            archive_name = f"audio/{asset.file_name}"
            archive.write(training_audio_path(asset.file_name), archive_name)
            manifest.append(json.dumps({
                "id": f"qa-{log.id}", "audio": archive_name,
                "text": review.corrected_source_text.strip(), "language": canonical_language(log.source_lang),
                "split": review.whisper_split or stable_split(asset.sha256),
                "duration_ms": asset.duration_ms, "sha256": asset.sha256,
            }, ensure_ascii=False))
        archive.writestr("manifest.jsonl", "\n".join(manifest) + ("\n" if manifest else ""))
    return path


async def store_uploaded_dataset(dataset: TrainingDataset, upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    accepted = {"nllb": {".jsonl", ".csv"}, "whisper": {".zip"}}
    if suffix not in accepted.get(dataset.task, set()):
        await upload.close()
        raise HTTPException(422, "Unsupported dataset file type")
    destination = dataset_directory(dataset.id) / f"upload{suffix}"
    total = 0
    try:
        with destination.open("xb") as output:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_DATASET_UPLOAD_BYTES:
                    raise HTTPException(413, "Dataset upload is too large")
                output.write(chunk)
        if total == 0:
            raise HTTPException(422, "Dataset file is empty")
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def _normalise_nllb_row(row: dict, number: int) -> dict:
    source = unicodedata.normalize("NFC", str(row.get("source", "")).strip())
    target = unicodedata.normalize("NFC", str(row.get("target", "")).strip())
    source_lang = canonical_language(str(row.get("source_lang", "")).strip())
    target_lang = canonical_language(str(row.get("target_lang", "")).strip())
    split = str(row.get("split", "")).strip()
    if not source or not target:
        raise ValueError(f"Row {number}: source and target are required")
    if source_lang not in _LANGS or target_lang not in _LANGS or source_lang == target_lang:
        raise ValueError(f"Row {number}: invalid language direction")
    if split not in _SPLITS:
        raise ValueError(f"Row {number}: invalid split")
    return {
        "id": str(row.get("id") or f"external-{number}"), "source_lang": source_lang,
        "target_lang": target_lang, "source": source, "target": target,
        "domain": str(row.get("domain") or "general")[:64], "split": split,
    }


def validate_nllb(path: Path) -> tuple[dict, Path]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict] = []
    try:
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                source_rows = list(csv.DictReader(stream))
        else:
            source_rows = []
            with path.open(encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    if not line.strip():
                        errors.append(f"Line {number}: blank line")
                        continue
                    source_rows.append(json.loads(line))
        for number, row in enumerate(source_rows, 1):
            try:
                rows.append(_normalise_nllb_row(row, number))
            except (TypeError, ValueError) as exc:
                if len(errors) < 50:
                    errors.append(str(exc))
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read dataset: {type(exc).__name__}")

    keys: dict[tuple[str, str, str], dict] = {}
    duplicates = 0
    leakage = 0
    conflicts = 0
    for row in rows:
        key = (row["source_lang"], row["target_lang"], row["source"].casefold())
        previous = keys.get(key)
        if previous is not None:
            duplicates += 1
            if previous["split"] != row["split"]:
                leakage += 1
            if previous["target"].casefold() != row["target"].casefold():
                conflicts += 1
        else:
            keys[key] = row
    if leakage:
        errors.append(f"{leakage} source groups appear in multiple splits")
    if duplicates:
        warnings.append(f"{duplicates} duplicate source rows")
    if conflicts:
        errors.append(f"{conflicts} source groups have conflicting target translations")
    if rows and duplicates / len(rows) > 0.10:
        errors.append("Duplicate source ratio exceeds the 10% validation threshold")
    counts = {split: sum(row["split"] == split for row in rows) for split in _SPLITS}
    if not counts["train"] or not counts["validation"]:
        errors.append("Train and validation splits must both be non-empty")
    directions: dict[str, int] = {}
    for row in rows:
        direction = f'{row["source_lang"]}->{row["target_lang"]}'
        directions[direction] = directions.get(direction, 0) + 1

    canonical = path.parent / "nllb-training.jsonl"
    if not errors:
        with canonical.open("w", encoding="utf-8", newline="\n") as output:
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "valid": not errors, "errors": errors[:50], "warnings": warnings[:50],
        "sample_count": len(rows), "train_count": counts["train"],
        "validation_count": counts["validation"], "test_count": counts["test"],
        "duration_seconds": 0.0, "directions": directions,
        "languages": sorted({row["source_lang"] for row in rows} | {row["target_lang"] for row in rows}),
        "duplicate_count": duplicates, "conflict_count": conflicts,
    }
    return report, canonical if not errors else path


def _safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def validate_whisper(path: Path) -> tuple[dict, Path]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict] = []
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                errors.append("Archive contains too many entries")
            if sum(entry.file_size for entry in entries) > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                errors.append("Archive expands beyond the allowed size")
            if any(not _safe_archive_name(entry.filename) for entry in entries):
                errors.append("Archive contains an unsafe path")
            names = {entry.filename for entry in entries}
            if len(names) != len(entries):
                errors.append("Archive contains duplicate entry names")
            if "manifest.jsonl" not in names:
                errors.append("manifest.jsonl is missing")
            if errors:
                raise ValueError("Unsafe archive")
            with archive.open("manifest.jsonl") as raw:
                manifest = io.TextIOWrapper(raw, encoding="utf-8")
                for number, line in enumerate(manifest, 1):
                    if not line.strip():
                        errors.append(f"Manifest line {number}: blank line")
                        continue
                    row = json.loads(line)
                    audio_name = str(row.get("audio", ""))
                    text = str(row.get("text", "")).strip()
                    language = str(row.get("language", ""))
                    split = str(row.get("split", ""))
                    if not _safe_archive_name(audio_name) or audio_name not in names:
                        errors.append(f"Manifest line {number}: missing or unsafe audio")
                        continue
                    if not text or language not in {"vi", "en"} or split not in _SPLITS:
                        errors.append(f"Manifest line {number}: invalid text, language or split")
                        continue
                    info = archive.getinfo(audio_name)
                    if info.file_size > 50 * 1024 * 1024:
                        errors.append(f"Manifest line {number}: audio file is too large")
                        continue
                    audio_bytes = archive.read(info)
                    try:
                        with wave.open(io.BytesIO(audio_bytes), "rb") as audio:
                            frames = audio.getnframes()
                            if (
                                audio.getframerate() != 16000 or audio.getnchannels() != 1
                                or audio.getsampwidth() != 2 or audio.getcomptype() != "NONE" or frames <= 0
                            ):
                                raise wave.Error("unsupported format")
                            duration_ms = round(frames * 1000 / 16000)
                    except (wave.Error, EOFError):
                        errors.append(f"Manifest line {number}: audio must be PCM16 mono 16 kHz WAV")
                        continue
                    actual_sha = hashlib.sha256(audio_bytes).hexdigest()
                    expected = row.get("sha256")
                    if expected and actual_sha != expected:
                        errors.append(f"Manifest line {number}: audio checksum mismatch")
                        continue
                    rows.append({**row, "duration_ms": duration_ms, "language": language,
                                 "split": split, "_audio_sha256": actual_sha})
    except (OSError, ValueError, UnicodeError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        if not errors:
            errors.append(f"Cannot read Whisper archive: {type(exc).__name__}")

    audio_splits: dict[str, set[str]] = {}
    audio_counts: dict[str, int] = {}
    for row in rows:
        audio_splits.setdefault(row["_audio_sha256"], set()).add(row["split"])
        audio_counts[row["_audio_sha256"]] = audio_counts.get(row["_audio_sha256"], 0) + 1
    duplicate_audio = sum(count - 1 for count in audio_counts.values())
    leaking_audio = sum(len(splits) > 1 for splits in audio_splits.values())
    if duplicate_audio:
        warnings.append(f"{duplicate_audio} duplicate audio entries")
    if leaking_audio:
        errors.append(f"{leaking_audio} audio files appear in multiple splits")
    counts = {split: sum(row["split"] == split for row in rows) for split in _SPLITS}
    if not counts["train"] or not counts["validation"]:
        errors.append("Train and validation splits must both be non-empty")
    duration_seconds = sum(int(row.get("duration_ms") or 0) for row in rows) / 1000
    report = {
        "valid": not errors, "errors": errors[:50], "warnings": warnings[:50],
        "sample_count": len(rows), "train_count": counts["train"],
        "validation_count": counts["validation"], "test_count": counts["test"],
        "duration_seconds": round(duration_seconds, 3),
        "languages": sorted({row["language"] for row in rows}),
        "hours_by_language": {
            language: round(sum(int(row.get("duration_ms") or 0) for row in rows if row["language"] == language) / 3_600_000, 3)
            for language in sorted({row["language"] for row in rows})
        },
    }
    return report, path


def validate_dataset_file(dataset: TrainingDataset) -> tuple[dict, Path]:
    path = resolve_storage_uri(dataset.storage_uri)
    return validate_nllb(path) if dataset.task == "nllb" else validate_whisper(path)

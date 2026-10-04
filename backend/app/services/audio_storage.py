"""Owner-bound expiring output; legacy files remain quarantined."""
import re
import stat
import time
import uuid
import wave
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.access_policy import get_policy_settings
from app.db.audio_model import AudioAsset

BACKEND_DIR = Path(__file__).resolve().parents[2]
SECURE_OUTPUT_DIR = BACKEND_DIR / "outputs" / "secure"
SECURE_TEMP_DIR = BACKEND_DIR / "temp" / "secure"
_FILE_NAME = re.compile(r"^[0-9a-f]{32}\.wav$")


def secure_directory(directory: Path) -> Path:
    for part in [directory.parent, directory]:
        if part.exists() and (part.is_symlink() or getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise RuntimeError("Private audio directory must not be a link")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


def audio_path(file_name: str) -> Path:
    if not _FILE_NAME.fullmatch(file_name):
        raise HTTPException(404, "Audio not found")
    path = secure_directory(SECURE_OUTPUT_DIR) / file_name
    if path.exists():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or getattr(info, "st_file_attributes", 0) & 0x400:
            raise HTTPException(404, "Audio not found")
    return path


def register_audio(db: Session, file_name: str, owner_id: str) -> AudioAsset:
    if not audio_path(file_name).is_file():
        raise RuntimeError("Audio generation did not produce a file")
    asset = AudioAsset(file_name=file_name, owner_id=owner_id, expires_at=datetime.utcnow() + timedelta(seconds=get_policy_settings().TTS_AUDIO_TTL_SECONDS))
    db.add(asset)
    db.commit()
    return asset


def stage_source_pcm(db: Session, pcm: bytes, owner_id: str) -> AudioAsset:
    """Keep source speech briefly so an explicit user report can promote it to QA."""
    if not pcm or len(pcm) % 2 or len(pcm) > 16000 * 2 * 30:
        raise ValueError("Source audio must be mono 16 kHz 16-bit PCM")
    file_name = f"{uuid.uuid4().hex}.wav"
    path = audio_path(file_name)
    try:
        with wave.open(str(path), "wb") as audio:
            audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            audio.writeframes(pcm)
        return register_audio(db, file_name, owner_id)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def owned_audio(db: Session, file_name: str, owner_id: str) -> Path:
    asset = db.query(AudioAsset).filter(AudioAsset.file_name == file_name, AudioAsset.owner_id == owner_id, AudioAsset.expires_at > datetime.utcnow()).first()
    if asset is None:
        raise HTTPException(404, "Audio not found")
    path = audio_path(file_name)
    if not path.is_file():
        raise HTTPException(404, "Audio not found")
    return path


def sweep_audio(db: Session) -> dict:
    removed = 0
    for asset in db.query(AudioAsset).filter(AudioAsset.expires_at <= datetime.utcnow()).all():
        try:
            audio_path(asset.file_name).unlink(missing_ok=True)
        except (OSError, HTTPException):
            continue  # Retry while a Windows player holds the file.
        db.delete(asset)
        removed += 1
    db.commit()
    known = {name for (name,) in db.query(AudioAsset.file_name).all()}
    # Reclaim only new private UUID files; the grace period protects in-flight jobs.
    cutoff = time.time() - 3600
    for directory in (SECURE_OUTPUT_DIR, SECURE_TEMP_DIR):
        secure_directory(directory)
        for path in directory.iterdir():
            info = path.lstat()
            if not _FILE_NAME.fullmatch(path.name) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or getattr(info, "st_file_attributes", 0) & 0x400:
                continue
            if info.st_mtime < cutoff and (directory == SECURE_TEMP_DIR or path.name not in known):
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
    return {"removed_files": removed}

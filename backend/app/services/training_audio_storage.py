"""Private, consent-bound audio storage for supervised Whisper datasets."""
from __future__ import annotations

import hashlib
import os
import re
import stat
import uuid
import wave
from pathlib import Path

from fastapi import HTTPException, UploadFile


BACKEND_DIR = Path(__file__).resolve().parents[2]
TRAINING_AUDIO_DIR = BACKEND_DIR / "data" / "training_audio"
_FILE_NAME = re.compile(r"^[0-9a-f]{32}\.wav$")
MAX_TRAINING_AUDIO_BYTES = 2_000_000
MAX_TRAINING_AUDIO_SECONDS = 30


def secure_training_directory() -> Path:
    directory = TRAINING_AUDIO_DIR
    for part in (directory.parent, directory):
        if part.exists() and (
            part.is_symlink() or getattr(part.lstat(), "st_file_attributes", 0) & 0x400
        ):
            raise RuntimeError("Training audio directory must not be a link")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


def training_audio_path(file_name: str, *, require_exists: bool = True) -> Path:
    if not _FILE_NAME.fullmatch(file_name):
        raise HTTPException(404, "Training audio not found")
    path = secure_training_directory() / file_name
    if require_exists:
        if not path.is_file():
            raise HTTPException(404, "Training audio not found")
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or getattr(info, "st_file_attributes", 0) & 0x400
        ):
            raise HTTPException(404, "Training audio not found")
    return path


async def store_training_wav(upload: UploadFile) -> dict:
    file_name = f"{uuid.uuid4().hex}.wav"
    destination = training_audio_path(file_name, require_exists=False)
    digest = hashlib.sha256()
    total = 0
    try:
        with destination.open("xb") as output:
            while chunk := await upload.read(65536):
                total += len(chunk)
                if total > MAX_TRAINING_AUDIO_BYTES:
                    raise HTTPException(413, "Training audio is too large")
                digest.update(chunk)
                output.write(chunk)
        try:
            with wave.open(os.fspath(destination), "rb") as audio:
                frames = audio.getnframes()
                if (
                    audio.getframerate() != 16000
                    or audio.getnchannels() != 1
                    or audio.getsampwidth() != 2
                    or audio.getcomptype() != "NONE"
                    or not 0 < frames <= 16000 * MAX_TRAINING_AUDIO_SECONDS
                ):
                    raise HTTPException(
                        422, "Audio must be PCM WAV, mono, 16 kHz, 16-bit, at most 30 seconds"
                    )
                if len(audio.readframes(frames)) != frames * 2:
                    raise HTTPException(422, "Training audio is truncated")
        except (wave.Error, EOFError):
            raise HTTPException(422, "Invalid training WAV audio") from None
        return {
            "file_name": file_name,
            "sha256": digest.hexdigest(),
            "duration_ms": round(frames * 1000 / 16000),
            "sample_rate": 16000,
            "channels": 1,
        }
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def delete_training_audio(file_name: str) -> None:
    training_audio_path(file_name, require_exists=False).unlink(missing_ok=True)

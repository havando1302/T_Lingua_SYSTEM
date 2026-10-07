"""Encrypted, authenticated backup and constrained restore for T-Lingua data."""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import os
import stat
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


MAGIC = b"TLINGUA-BACKUP-V2\0"
NONCE_SIZE = 12
TAG_SIZE = 16
CHUNK_SIZE = 1024 * 1024
ALLOWED_FILES = {
    "admin.db": 8 * 1024 * 1024 * 1024,
    "translation_memory.json": 256 * 1024 * 1024,
}
MANIFEST_NAME = "manifest.json"
MANIFEST_MAX_SIZE = 64 * 1024


class SecurityError(Exception):
    """Raised when a backup fails authentication or archive validation."""


def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as source:
        while chunk := source.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _backup_key(explicit_key: str | bytes | None = None) -> bytes:
    encoded = explicit_key if explicit_key is not None else os.getenv("BACKUP_ENCRYPTION_KEY", "")
    if isinstance(encoded, str):
        encoded = encoded.encode("ascii", errors="strict")
    try:
        key = base64.b64decode(encoded, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as error:
        raise SecurityError("BACKUP_ENCRYPTION_KEY must be URL-safe Base64") from error
    if len(key) != 32:
        raise SecurityError("BACKUP_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def _assert_regular_file(path: Path, *, maximum_size: int) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SecurityError(f"Refusing non-regular or linked input: {path.name}")
    if getattr(info, "st_file_attributes", 0) & 0x400:
        raise SecurityError(f"Refusing reparse-point input: {path.name}")
    if info.st_size > maximum_size:
        raise SecurityError(f"Input exceeds the approved limit: {path.name}")


def _secure_temp(directory: Path, suffix: str) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=".tlingua-", suffix=suffix, dir=directory)
    os.close(descriptor)
    path = Path(name)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def _encrypt(source: Path, destination: Path, key: bytes) -> None:
    nonce = os.urandom(NONCE_SIZE)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(MAGIC)
    with source.open("rb") as plain, destination.open("xb") as encrypted:
        encrypted.write(MAGIC)
        encrypted.write(nonce)
        while chunk := plain.read(CHUNK_SIZE):
            encrypted.write(encryptor.update(chunk))
        encrypted.write(encryptor.finalize())
        encrypted.write(encryptor.tag)
        encrypted.flush()
        os.fsync(encrypted.fileno())


def _decrypt(source: Path, destination: Path, key: bytes) -> None:
    minimum = len(MAGIC) + NONCE_SIZE + TAG_SIZE
    if source.stat().st_size < minimum:
        raise SecurityError("Backup is truncated")
    with source.open("rb") as encrypted:
        if encrypted.read(len(MAGIC)) != MAGIC:
            raise SecurityError("Unsupported or unencrypted backup format")
        nonce = encrypted.read(NONCE_SIZE)
        encrypted.seek(-TAG_SIZE, os.SEEK_END)
        tag = encrypted.read(TAG_SIZE)
        remaining = source.stat().st_size - minimum
        encrypted.seek(len(MAGIC) + NONCE_SIZE)
        decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        decryptor.authenticate_additional_data(MAGIC)
        with destination.open("wb") as plain:
            while remaining:
                chunk = encrypted.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    raise SecurityError("Backup ciphertext is truncated")
                remaining -= len(chunk)
                plain.write(decryptor.update(chunk))
            plain.write(decryptor.finalize())
            plain.flush()
            os.fsync(plain.fileno())


def create_backup(
    data_dir: Path,
    output_dir: Path,
    *,
    encryption_key: str | bytes | None = None,
) -> Path:
    data_dir, output_dir = Path(data_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink():
        raise SecurityError("Backup directory must not be a link")
    key = _backup_key(encryption_key)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    destination = output_dir / f"backup_tlingua_{timestamp}.tar.gz.enc"
    tar_path = _secure_temp(output_dir, ".tar.gz")
    encrypted_temp = output_dir / f".{destination.name}.tmp"
    metadata = {"timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0.0", "files": {}}
    try:
        with tarfile.open(tar_path, "w:gz") as archive:
            for name, maximum_size in ALLOWED_FILES.items():
                source = data_dir / name
                if not source.exists():
                    continue
                _assert_regular_file(source, maximum_size=maximum_size)
                metadata["files"][name] = {
                    "size_bytes": source.stat().st_size,
                    "sha256": calculate_sha256(source),
                }
                archive.add(source, arcname=name, recursive=False)
            manifest = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
            if len(manifest) > MANIFEST_MAX_SIZE:
                raise SecurityError("Backup manifest exceeds its approved limit")
            info = tarfile.TarInfo(MANIFEST_NAME)
            info.size = len(manifest)
            info.mode = 0o600
            info.mtime = int(datetime.now(timezone.utc).timestamp())
            archive.addfile(info, io.BytesIO(manifest))
        _encrypt(tar_path, encrypted_temp, key)
        os.replace(encrypted_temp, destination)
        try:
            destination.chmod(0o600)
        except OSError:
            pass
        return destination
    finally:
        tar_path.unlink(missing_ok=True)
        encrypted_temp.unlink(missing_ok=True)


def _validated_members(archive: tarfile.TarFile) -> tuple[dict[str, tarfile.TarInfo], dict]:
    members: dict[str, tarfile.TarInfo] = {}
    allowed = set(ALLOWED_FILES) | {MANIFEST_NAME}
    for member in archive.getmembers():
        if member.name not in allowed or member.name in members:
            raise SecurityError("Backup contains an unexpected or duplicate member")
        if not member.isfile() or member.issym() or member.islnk():
            raise SecurityError("Backup contains a non-regular member")
        limit = MANIFEST_MAX_SIZE if member.name == MANIFEST_NAME else ALLOWED_FILES[member.name]
        if member.size < 0 or member.size > limit:
            raise SecurityError("Backup member exceeds its approved limit")
        members[member.name] = member
    if MANIFEST_NAME not in members:
        raise SecurityError("Backup manifest is missing")
    manifest_file = archive.extractfile(members[MANIFEST_NAME])
    if manifest_file is None:
        raise SecurityError("Backup manifest cannot be read")
    try:
        manifest = json.loads(manifest_file.read(MANIFEST_MAX_SIZE + 1))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SecurityError("Backup manifest is invalid") from error
    if manifest.get("version") != "2.0.0" or not isinstance(manifest.get("files"), dict):
        raise SecurityError("Unsupported backup manifest")
    if set(manifest["files"]) != (set(members) - {MANIFEST_NAME}):
        raise SecurityError("Manifest and archive members do not match")
    return members, manifest


def restore_backup(
    archive_path: Path,
    target_dir: Path,
    *,
    encryption_key: str | bytes | None = None,
) -> bool:
    archive_path, target_dir = Path(archive_path), Path(target_dir)
    decrypted: Path | None = None
    staging: Path | None = None
    try:
        if not archive_path.exists():
            raise FileNotFoundError("Backup archive does not exist")
        _assert_regular_file(archive_path, maximum_size=9 * 1024 * 1024 * 1024)
        target_dir.mkdir(parents=True, exist_ok=True)
        if target_dir.is_symlink():
            raise SecurityError("Restore directory must not be a link")
        decrypted = _secure_temp(target_dir, ".tar.gz")
        _decrypt(archive_path, decrypted, _backup_key(encryption_key))
        staging = Path(tempfile.mkdtemp(prefix=".tlingua-restore-", dir=target_dir))
        with tarfile.open(decrypted, "r:gz") as archive:
            members, manifest = _validated_members(archive)
            for name, details in manifest["files"].items():
                if not isinstance(details, dict) or not isinstance(details.get("size_bytes"), int):
                    raise SecurityError("Manifest file metadata is invalid")
                if details["size_bytes"] != members[name].size:
                    raise SecurityError("Manifest size does not match archive member")
                source = archive.extractfile(members[name])
                if source is None:
                    raise SecurityError("Backup member cannot be read")
                staged = staging / name
                digest = hashlib.sha256()
                written = 0
                with staged.open("xb") as output:
                    while chunk := source.read(CHUNK_SIZE):
                        written += len(chunk)
                        if written > ALLOWED_FILES[name]:
                            raise SecurityError("Extracted member exceeds its approved limit")
                        digest.update(chunk)
                        output.write(chunk)
                    output.flush()
                    os.fsync(output.fileno())
                if written != details["size_bytes"] or digest.hexdigest() != details.get("sha256"):
                    raise SecurityError("Backup member failed integrity verification")
        for name in manifest["files"]:
            os.replace(staging / name, target_dir / name)
        return True
    except Exception as error:
        print(f"[ERROR] Restore failed safely ({type(error).__name__})")
        return False
    finally:
        if decrypted is not None:
            decrypted.unlink(missing_ok=True)
        if staging is not None:
            for child in staging.glob("*"):
                child.unlink(missing_ok=True)
            staging.rmdir()


"""Rotate local signing material without printing secrets. Stop the backend first."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / "backend" / ".env"
PRIVATE_ROOT = ROOT / ".phase1-artifacts"
SAFE_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080,http://localhost:7357,http://127.0.0.1:7357"


def _regular_file(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("Configuration must be a regular unlinked file")


def prepare_local(backup_name="pre-phase2.env"):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+\.env", backup_name):
        raise ValueError("Invalid backup filename")
    for directory in (ROOT / "backend", PRIVATE_ROOT):
        if not directory.is_dir() or directory.is_symlink() or getattr(directory.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("Use a verified Phase 1 private artifact directory")
    existing = ""
    if ENV_FILE.exists():
        _regular_file(ENV_FILE)
        existing = ENV_FILE.read_text(encoding="utf-8-sig")
    values = {}
    for line in existing.splitlines():
        match = re.match(r"^\s*([A-Z_]+)\s*=\s*(.*?)\s*$", line)
        if match:
            values[match[1]] = match[2].strip("\"'")
    if values.get("APP_ENV", "local") != "local":
        raise ValueError("This tool is for local setup; provision non-local secrets through the deployment secret store")
    # Signing material is deliberately rotated; the separate MFA key is preserved.
    updates = {
        "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "AUTH_REQUIRE_MFA": "true",
        "AUTH_REQUIRE_PRIVILEGED_MFA": "true",
    }
    if not values.get("MFA_ENCRYPTION_KEY"):
        updates["MFA_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    if not values.get("BACKUP_ENCRYPTION_KEY"):
        updates["BACKUP_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    if not values.get("CORS_ORIGINS") or values.get("CORS_ORIGINS") == "*":
        updates["CORS_ORIGINS"] = SAFE_ORIGINS
    if not values.get("TRUSTED_HOSTS"):
        updates["TRUSTED_HOSTS"] = "localhost,127.0.0.1,[::1],testserver"
    if values.get("API_HOST", "0.0.0.0") == "0.0.0.0":
        updates["API_HOST"] = "127.0.0.1"
    destination = PRIVATE_ROOT / "config"
    if destination.exists() and (destination.is_symlink() or getattr(destination.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Private backup directory must not be a link")
    destination.mkdir(mode=0o700, exist_ok=True)
    backup = destination / backup_name
    with backup.open("x", encoding="utf-8") as target:
        target.write(existing)
    lines, seen = [], set()
    for line in existing.splitlines():
        match = re.match(r"^\s*([A-Z_]+)\s*=", line)
        key = match[1] if match else None
        if key in updates:
            if key not in seen:
                lines.append(f"{key}={updates[key]}")
                seen.add(key)
        else:
            lines.append(line)
    lines.extend(f"{key}={value}" for key, value in updates.items() if key not in seen)
    descriptor, temporary = tempfile.mkstemp(prefix=".env-phase2-", dir=ENV_FILE.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write("\n".join(lines) + "\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, ENV_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {
        "status": "local_security_prepared",
        "jwt_rotated": True,
        "mfa_key_created": "MFA_ENCRYPTION_KEY" in updates,
        "backup_key_created": "BACKUP_ENCRYPTION_KEY" in updates,
        "backup": str(backup.relative_to(ROOT)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-name", default="pre-phase2.env")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare_local(args.backup_name)))
    except Exception as error:
        parser.exit(1, f"Security preparation failed ({type(error).__name__}); inspect configuration privately.\n")


if __name__ == "__main__":
    main()

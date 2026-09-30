"""Local, allowlisted snapshots and isolated restore drills (Python stdlib only).

Snapshots contain private application data. Hashes detect accidental changes;
they are not signatures and do not establish an archive's authenticity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class RecoveryError(ValueError):
    """A safe-to-display recovery failure that never includes data contents."""


MANIFEST_NAME = "manifest.json"
CONSISTENCY = "individually_validated_not_atomic"
MAX_FILES = 5000
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 128 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024 * 1024
SQLITE_TIMEOUT_SECONDS = 60
_KNOWN_FILES = (
    "backend/data/admin.db",
    "backend/data/translation_memory.json",
    "data/admin.db",
    "data/translation_memory.json",
)
_AUDIO_ROOTS = ("backend/outputs", "outputs")
_AUDIO_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,123}\.(?:wav|mp3)\Z", re.I)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{index}" for prefix in ("COM", "LPT") for index in range(1, 10)
}
_EXPECTED_SCHEMA = {
    "users": {"id", "username", "password_hash", "role", "created_at"},
    "translation_logs": {"id", "client_id", "source_text", "translated_text", "latency",
                         "model_source", "is_flagged", "created_at"},
    "api_keys": {"id", "name", "key", "is_active", "created_at"},
    "system_settings": {"id", "key", "value", "description", "updated_at"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _checked_path(path: Path) -> Path:
    """Reject links/reparse points before resolving an existing ancestor."""
    raw = Path(path)
    if ".." in raw.parts:
        raise RecoveryError("Parent traversal is not allowed in recovery paths.")
    absolute = Path(os.path.abspath(raw))
    if str(absolute).startswith("\\\\"):
        raise RecoveryError("Recovery paths must be local, without UNC or device prefixes.")
    for name in (*raw.parts, *absolute.parts):
        if name in (raw.anchor, absolute.anchor):
            continue
        if (":" in name or "\\" in name or any(ord(character) < 32 for character in name)
                or name.endswith((".", " ")) or name.split(".")[0].upper() in _RESERVED):
            raise RecoveryError("Recovery paths must not contain Windows device names, streams or path aliases.")
    for component in reversed((absolute, *absolute.parents)):
        try:
            metadata = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise RecoveryError("Recovery paths must not contain links or reparse points.")
    return absolute


def _new_destination(path: Path) -> Path:
    destination = _checked_path(path)
    if destination.exists():
        raise RecoveryError("Destination already exists; select a new directory.")
    if not destination.parent.is_dir():
        raise RecoveryError("Destination parent must be an existing directory.")
    return destination


def _assert_outside_runtime(destination: Path, repo_root: Path) -> None:
    protected = (
        repo_root / "backend" / "data", repo_root / "data",
        repo_root / "backend" / "outputs", repo_root / "outputs",
        repo_root / "backend" / "temp", repo_root / "temp",
        repo_root / ".git", repo_root / ".codex", repo_root / ".agents",
    )
    if any(_within(destination, path) or _within(path, destination) for path in protected):
        raise RecoveryError("Destination overlaps a runtime or repository metadata directory.")


def _regular_file(path: Path, limit: int = MAX_FILE_BYTES) -> int:
    checked = _checked_path(path)
    try:
        metadata = checked.stat()
    except OSError:
        raise RecoveryError("Required snapshot file cannot be read.") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise RecoveryError("Snapshot payloads must be regular files.")
    if metadata.st_nlink != 1:
        raise RecoveryError("Hard-linked snapshot files are not supported.")
    if metadata.st_size > limit:
        raise RecoveryError("Snapshot file exceeds the configured size limit.")
    return metadata.st_size


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_new(source: Path, destination: Path) -> None:
    _regular_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _checked_path(destination.parent)
    # Exclusive creation prevents overwriting a file inserted during the drill.
    with source.open("rb") as incoming, destination.open("xb") as outgoing:
        copied = 0
        for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
            copied += len(chunk)
            if copied > MAX_FILE_BYTES:
                raise RecoveryError("Source grew beyond the snapshot size limit.")
            outgoing.write(chunk)
        outgoing.flush()
        os.fsync(outgoing.fileno())


def _json_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError("JSON contains duplicate keys.")
        result[key] = value
    return result


def _read_json(path: Path, limit: int) -> Any:
    _regular_file(path, limit)
    try:
        with path.open("rb") as stream:
            contents = stream.read(limit + 1)
        if len(contents) > limit:
            raise RecoveryError("JSON grew beyond the configured size limit.")
        return json.loads(contents.decode("utf-8"), object_pairs_hook=_json_without_duplicates)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise RecoveryError("JSON is malformed or exceeds supported nesting.") from None


def _validate_tm(path: Path) -> dict[str, Any]:
    value = _read_json(path, MAX_JSON_BYTES)
    if not isinstance(value, dict):
        raise RecoveryError("Translation Memory must be a JSON object.")
    if all(isinstance(target, str) for target in value.values()):
        return {"format": "translation_memory", "shape": "legacy_flat" if value else "empty",
                "entry_count": len(value)}
    if all(isinstance(entries, dict) and all(isinstance(target, str) for target in entries.values())
           for entries in value.values()):
        return {"format": "translation_memory", "shape": "client_mapping",
                "entry_count": sum(len(entries) for entries in value.values())}
    raise RecoveryError("Translation Memory has an unsupported mapping shape.")


def _sqlite_is_wal(path: Path) -> bool:
    with path.open("rb") as stream:
        header = stream.read(100)
    if len(header) < 100 or header[:16] != b"SQLite format 3\x00":
        raise RecoveryError("Database does not have a supported SQLite header.")
    sidecars = (Path(str(path) + "-wal"), Path(str(path) + "-shm"))
    return header[18] == 2 or header[19] == 2 or any(os.path.lexists(p) for p in sidecars)


def _sqlite_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
        deadline = time.monotonic() + SQLITE_TIMEOUT_SECONDS
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        return connection
    except sqlite3.Error:
        connection.close()
        raise


def _validate_sqlite(path: Path) -> dict[str, Any]:
    _regular_file(path)
    if _sqlite_is_wal(path):
        raise RecoveryError("Standalone snapshot must not depend on SQLite WAL sidecars.")
    connection = _sqlite_connection(path)
    try:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RecoveryError("SQLite integrity check failed.")
        schema = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name, tbl_name"
        ).fetchall()
        table_count = sum(row[0] == "table" for row in schema)
        if not table_count:
            raise RecoveryError("Database has no application tables.")
        tables = {row[1] for row in schema if row[0] == "table"}
        missing_tables = sorted(set(_EXPECTED_SCHEMA) - tables)
        missing_columns = {}
        for table in sorted(set(_EXPECTED_SCHEMA) & tables):
            # Table identifiers come only from the fixed application schema map.
            columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
            missing = sorted(_EXPECTED_SCHEMA[table] - columns)
            if missing:
                missing_columns[table] = missing
        signature = hashlib.sha256(json.dumps(schema, ensure_ascii=True).encode("utf-8")).hexdigest()
        return {"format": "sqlite", "integrity": "ok", "table_count": table_count,
                "schema_sha256": signature,
                "application_schema": {"missing_tables": missing_tables, "missing_columns": missing_columns}}
    finally:
        connection.close()


def _snapshot_sqlite(source: Path, destination: Path) -> None:
    _regular_file(source)
    # Read-only SQLite can create shared-memory sidecars in WAL mode. Refuse
    # that mode rather than use immutable=1, which could omit committed WAL data.
    if _sqlite_is_wal(source):
        raise RecoveryError(
            "WAL-mode source is not supported by this non-mutating drill; "
            "use an operator-prepared consistent standalone snapshot."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    _checked_path(destination.parent)
    with destination.open("xb"):
        pass
    reader = _sqlite_connection(source)
    writer = None
    deadline = time.monotonic() + SQLITE_TIMEOUT_SECONDS

    def check_deadline(_status: int, _remaining: int, _total: int) -> None:
        if time.monotonic() > deadline:
            raise RecoveryError("SQLite online backup exceeded its time limit.")

    try:
        writer = sqlite3.connect(str(destination))
        reader.backup(writer, pages=256, progress=check_deadline, sleep=0.05)
    finally:
        if writer is not None:
            writer.close()
        reader.close()


def _safe_relative(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 256 or "\\" in value or ":" in value:
        raise RecoveryError("Manifest contains an invalid payload path.")
    relative = PurePosixPath(value)
    if relative.is_absolute() or str(relative) != value or any(part in ("", ".", "..") for part in relative.parts):
        raise RecoveryError("Manifest contains a noncanonical payload path.")
    if value in _KNOWN_FILES:
        return value
    if str(relative.parent) in _AUDIO_ROOTS and _AUDIO_NAME.fullmatch(relative.name):
        if relative.name.split(".")[0].upper() not in _RESERVED:
            return value
    raise RecoveryError("Manifest contains a file outside the runtime allowlist.")


def _validate_payload(path: Path, relative: str) -> dict[str, Any]:
    if relative.endswith("/admin.db"):
        return _validate_sqlite(path)
    if relative.endswith("/translation_memory.json"):
        return _validate_tm(path)
    return {"format": "audio", "validation": "byte_integrity_only"}


def _entry(path: Path, relative: str) -> dict[str, Any]:
    return {"path": relative, "size_bytes": _regular_file(path), "sha256": _sha256(path),
            "validation": _validate_payload(path, relative)}


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _payload_files(directory: Path, expected: set[str]) -> set[str]:
    actual: set[str] = set()
    allowed_directories = {
        str(parent) for relative in expected for parent in PurePosixPath(relative).parents if str(parent) != "."
    }
    for root, directories, files in os.walk(directory, followlinks=False):
        for name in directories:
            subdirectory = _checked_path(Path(root) / name)
            if subdirectory.relative_to(directory).as_posix() not in allowed_directories:
                raise RecoveryError("Snapshot contains an unexpected directory.")
        for name in files:
            file_path = Path(root) / name
            _regular_file(file_path)
            actual.add(file_path.relative_to(directory).as_posix())
            if len(actual) > MAX_FILES + 1:
                raise RecoveryError("Snapshot has too many files.")
    return actual


def _verified_manifest(backup_dir: Path) -> tuple[Path, dict[str, Any]]:
    directory = _checked_path(backup_dir)
    if not directory.is_dir():
        raise RecoveryError("Backup directory does not exist.")
    manifest = _read_json(directory / MANIFEST_NAME, MAX_MANIFEST_BYTES)
    if not isinstance(manifest, dict) or set(manifest) != {
        "version", "created_at", "consistency", "files", "missing", "audio_included"
    }:
        raise RecoveryError("Unsupported snapshot manifest structure.")
    if type(manifest["version"]) is not int or manifest["version"] != 1 or manifest["consistency"] != CONSISTENCY:
        raise RecoveryError("Unsupported snapshot manifest version or consistency mode.")
    if not isinstance(manifest["created_at"], str) or type(manifest["audio_included"]) is not bool:
        raise RecoveryError("Manifest metadata has invalid types.")
    entries = manifest["files"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
        raise RecoveryError("Manifest file inventory must be nonempty and bounded.")
    missing = manifest["missing"]
    if not isinstance(missing, list) or any(not isinstance(item, str) or item not in _KNOWN_FILES for item in missing):
        raise RecoveryError("Manifest missing-file inventory is invalid.")
    if len(missing) != len(set(missing)):
        raise RecoveryError("Manifest missing-file inventory has duplicates.")
    expected = {MANIFEST_NAME}
    names: set[str] = set()
    total_size = 0
    for record in entries:
        if not isinstance(record, dict) or set(record) != {"path", "size_bytes", "sha256", "validation"}:
            raise RecoveryError("Manifest file record is invalid.")
        relative = _safe_relative(record["path"])
        folded = relative.casefold()
        if folded in names or relative in missing:
            raise RecoveryError("Manifest contains duplicate or conflicting file records.")
        names.add(folded)
        if not manifest["audio_included"] and relative not in _KNOWN_FILES:
            raise RecoveryError("Manifest audio policy conflicts with its file inventory.")
        size = record["size_bytes"]
        if type(size) is not int or not 0 <= size <= MAX_FILE_BYTES:
            raise RecoveryError("Manifest file size is invalid.")
        total_size += size
        if total_size > MAX_TOTAL_BYTES:
            raise RecoveryError("Snapshot exceeds the total size limit.")
        if not isinstance(record["sha256"], str) or not _SHA256.fullmatch(record["sha256"]):
            raise RecoveryError("Manifest SHA-256 is invalid.")
        expected.add("payload/" + relative)
    present_known = {record["path"] for record in entries if record["path"] in _KNOWN_FILES}
    if present_known | set(missing) != set(_KNOWN_FILES):
        raise RecoveryError("Manifest does not account for all known runtime data paths.")
    if _payload_files(directory, expected) != expected:
        raise RecoveryError("Snapshot inventory does not match its files.")
    for record in entries:
        source = directory / "payload" / record["path"]
        if _regular_file(source) != record["size_bytes"] or _sha256(source) != record["sha256"]:
            raise RecoveryError("Snapshot byte size or SHA-256 verification failed.")
        if _validate_payload(source, record["path"]) != record["validation"]:
            raise RecoveryError("Snapshot schema or data-shape validation failed.")
    return directory, manifest


def _schema_warnings(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    warnings = []
    for record in manifest["files"]:
        validation = record["validation"]
        if validation["format"] == "sqlite":
            schema = validation["application_schema"]
            if schema["missing_tables"] or schema["missing_columns"]:
                warnings.append({"path": record["path"], "code": "application_schema_incomplete", **schema})
    return warnings


def create_backup(repo_root: Path, destination: Path, *, include_audio: bool = False) -> dict[str, Any]:
    """Create a new allowlisted snapshot; never overwrite or change live data.

    Run with writers paused for a cross-file recovery point. Each file is checked
    independently; the tool cannot make SQLite and JSON one atomic transaction.
    Failure leaves an incomplete directory for inspection; use a NEW path to retry.
    """
    started = time.monotonic()
    try:
        repository = _checked_path(repo_root)
        if not repository.is_dir():
            raise RecoveryError("Repository root must be an existing directory.")
        target = _new_destination(destination)
        _assert_outside_runtime(target, repository)
        if type(include_audio) is not bool:
            raise RecoveryError("include_audio must be a boolean.")
        sources: list[tuple[str, Path]] = []
        missing = []
        for relative in _KNOWN_FILES:
            source = _checked_path(repository / relative)
            if source.exists():
                _regular_file(source, MAX_JSON_BYTES if relative.endswith(".json") else MAX_FILE_BYTES)
                sources.append((relative, source))
            else:
                missing.append(relative)
        if include_audio:
            for relative_root in _AUDIO_ROOTS:
                audio_root = _checked_path(repository / relative_root)
                if audio_root.exists():
                    if not audio_root.is_dir():
                        raise RecoveryError("Audio source must be a directory.")
                    for source in sorted(audio_root.iterdir()):
                        if source.suffix.lower() not in (".wav", ".mp3"):
                            continue
                        relative = _safe_relative(relative_root + "/" + source.name)
                        _regular_file(source)
                        sources.append((relative, source))
        if not sources:
            raise RecoveryError("No allowlisted runtime files were found; no backup was created.")
        if len(sources) > MAX_FILES or sum(_regular_file(source) for _, source in sources) > MAX_TOTAL_BYTES:
            raise RecoveryError("Selected runtime data exceeds snapshot limits.")
        target.mkdir(mode=0o700)
        files = []
        for relative, source in sources:
            captured = target / "payload" / relative
            if relative.endswith("/admin.db"):
                _snapshot_sqlite(source, captured)
            else:
                before = _sha256(source)
                _copy_new(source, captured)
                if before != _sha256(captured) or before != _sha256(source):
                    raise RecoveryError("Source changed during copy; pause writers and retry with a new destination.")
            files.append(_entry(captured, relative))
        manifest = {"version": 1, "created_at": _now(), "consistency": CONSISTENCY,
                    "files": files, "missing": missing, "audio_included": include_audio}
        _write_new_json(target / MANIFEST_NAME, manifest)
        _, checked = _verified_manifest(target)
        return {"status": "backup_verified", "backup_dir": str(target), "file_count": len(files),
                "total_bytes": sum(entry["size_bytes"] for entry in checked["files"]),
                "missing": missing, "audio_included": include_audio, "consistency": CONSISTENCY,
                "warnings": _schema_warnings(checked),
                "duration_seconds": round(time.monotonic() - started, 3)}
    except RecoveryError:
        raise
    except (OSError, sqlite3.Error, OverflowError):
        raise RecoveryError("Snapshot failed because of a filesystem or SQLite error; no live data was intentionally changed.") from None


def verify_backup(backup_dir: Path) -> dict[str, Any]:
    """Check the entire inventory, hashes, SQLite integrity and JSON mapping shape."""
    started = time.monotonic()
    try:
        directory, manifest = _verified_manifest(backup_dir)
        return {"status": "backup_verified", "backup_dir": str(directory),
                "file_count": len(manifest["files"]),
                "total_bytes": sum(entry["size_bytes"] for entry in manifest["files"]),
                "missing": manifest["missing"], "audio_included": manifest["audio_included"],
                "warnings": _schema_warnings(manifest),
                "consistency": CONSISTENCY, "duration_seconds": round(time.monotonic() - started, 3)}
    except RecoveryError:
        raise
    except (OSError, sqlite3.Error, OverflowError):
        raise RecoveryError("Snapshot verification failed because of a filesystem or SQLite error.") from None


def restore_backup(backup_dir: Path, destination: Path) -> dict[str, Any]:
    """Restore only into a NEW directory inside an existing restore-drills folder.

    This is an isolated validation drill, not a production restore command. The
    entire archive is verified before destination creation, then verified again.
    """
    started = time.monotonic()
    try:
        source, manifest = _verified_manifest(backup_dir)
        target = _new_destination(destination)
        if target.parent.name != "restore-drills":
            raise RecoveryError("Restore destination must be a new child of a restore-drills directory.")
        # This structural restriction also protects runtime roots of repositories
        # other than this checkout; the manifest is never trusted as a path policy.
        if any(part.casefold() in {"data", "outputs", ".git", ".codex", ".agents"} for part in target.parts):
            raise RecoveryError("Restore destination must not be inside a runtime or metadata directory.")
        parts = [part.casefold() for part in target.parts]
        if any(parts[index:index + 2] == ["backend", "temp"] for index in range(len(parts) - 1)):
            raise RecoveryError("Restore destination must not be inside a runtime temp directory.")
        if _within(target, source) or _within(source, target):
            raise RecoveryError("Restore destination must not overlap the backup.")
        target.mkdir(mode=0o700)
        for record in manifest["files"]:
            restored = target / "payload" / record["path"]
            _copy_new(source / "payload" / record["path"], restored)
        _write_new_json(target / MANIFEST_NAME, manifest)
        _verified_manifest(target)
        return {"status": "restore_drill_verified", "restore_dir": str(target),
                "file_count": len(manifest["files"]),
                "total_bytes": sum(entry["size_bytes"] for entry in manifest["files"]),
                "missing": manifest["missing"], "consistency": CONSISTENCY,
                "warnings": _schema_warnings(manifest),
                "duration_seconds": round(time.monotonic() - started, 3)}
    except RecoveryError:
        raise
    except (OSError, sqlite3.Error, OverflowError):
        raise RecoveryError("Restore drill failed; an incomplete isolated destination may remain.") from None

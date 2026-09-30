"""Small filesystem helpers shared by the offline commands."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


class Phase1Error(ValueError):
    """An actionable failure that is safe to display without source data."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reject_links(path: Path) -> None:
    """Reject Windows junctions as well as symlinks before resolving paths."""
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise Phase1Error("Symlinks and reparse points are not supported.")


def artifact_path(repo_root: Path, path: Path) -> Path:
    from .recovery import _checked_path

    # Match recovery's Windows path policy, including ADS and trailing-dot aliases.
    _checked_path(repo_root)
    _checked_path(path)
    root = repo_root.absolute()
    target = path.absolute()
    reject_links(root)
    reject_links(target)
    target = target.resolve()
    storage = (root / ".phase1-artifacts").resolve()
    if target == storage or storage not in target.parents:
        raise Phase1Error("Outputs must be inside the repository's .phase1-artifacts directory.")
    if target.exists():
        raise Phase1Error("Output already exists; choose a new name. No overwrite was performed.")
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    reject_links(target.parent)
    return target


def write_json_new(path: Path, report: dict) -> None:
    # Exclusive creation prevents a second run from replacing an earlier baseline.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

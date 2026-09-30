"""Preview/purge expired Phase 2 QA records in a specified, backed-up SQLite DB.

Legacy QA rows are retained for a separate operator review. Default is read-only.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3

from scripts.phase1.recovery import verify_backup

ROOT = Path(__file__).resolve().parents[2]


def retain(database: Path, *, days: int = 30, apply: bool = False, backup: Path | None = None) -> dict:
    if not 1 <= days <= 90:
        raise ValueError("Retention must be between 1 and 90 days")
    database = database.absolute()
    allowed = {ROOT / "backend" / "data" / "admin.db", ROOT / "data" / "admin.db"}
    if database not in allowed:
        raise ValueError("Select a known runtime database path")
    if database.is_symlink() or not database.is_file() or database.stat().st_nlink != 1 or getattr(database.lstat(), "st_file_attributes", 0) & 0x400:
        raise ValueError("Database must be an existing regular file")
    for parent in database.parents:
        if parent.is_symlink() or getattr(parent.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("Database path must not traverse links")
    if apply:
        if backup is None:
            raise ValueError("Apply requires a verified Phase 1 backup")
        verify_backup(backup)
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        relative = database.relative_to(ROOT).as_posix()
        if relative not in {entry["path"] for entry in manifest["files"]}:
            raise ValueError("Backup does not include the selected database")
        created = datetime.fromisoformat(manifest["created_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - created > timedelta(hours=1):
            raise ValueError("Take a fresh backup before applying retention")
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    mode = "rw" if apply else "ro"
    with sqlite3.connect(database.as_uri() + "?mode=" + mode, uri=True, timeout=10) as connection:
        version = connection.execute("SELECT applied_at FROM security_schema_versions WHERE version=1").fetchone()
        if version is None:
            raise ValueError("Security migration is required before retention")
        since = datetime.fromisoformat(version[0])
        conditions = "created_at >= ? AND created_at < ?"
        parameters = (since.isoformat(" "), cutoff.isoformat(" "))
        count = connection.execute("SELECT COUNT(*) FROM translation_logs WHERE " + conditions, parameters).fetchone()[0]
        if apply:
            snapshot = backup / "payload" / relative
            with sqlite3.connect(snapshot.absolute().as_uri() + "?mode=ro", uri=True) as saved:
                saved_version = saved.execute("SELECT applied_at FROM security_schema_versions WHERE version=1").fetchone()
                if saved_version != version:
                    raise ValueError("Backup belongs to a different security migration")
                # Ensure every row to be removed is recoverable from this exact backup.
                for row in connection.execute("SELECT * FROM translation_logs WHERE " + conditions, parameters):
                    preserved = saved.execute("SELECT * FROM translation_logs WHERE id=?", (row[0],)).fetchone()
                    if row != preserved:
                        raise ValueError("Eligible records changed since backup; take a fresh backup")
            connection.execute("DELETE FROM translation_logs WHERE " + conditions, parameters)
            connection.commit()
    return {"mode": "applied" if apply else "preview", "retention_days": days, "eligible_qa_rows": count, "legacy_rows_preserved": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(retain(args.database, days=args.days, apply=args.apply, backup=args.backup)))
    except Exception as error:
        parser.exit(1, f"Retention failed ({type(error).__name__}); no content is logged.\n")


if __name__ == "__main__":
    main()

"""Preview or add the bundled bilingual glossary without overwriting existing terms.

Run from backend: python scripts/seed_dictionary.py [--apply] [--actor-id ID]
Apply is restricted to local SQLite, backs up first, and writes an audit record.
"""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.utils.translation_safety import has_internal_placeholder, is_glossary_term


def load_seed(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))["entries"]
    seen = set()
    for row in rows:
        src, tgt = row["source_lang"], row["target_lang"]
        source, target = row["source_text"], row["translated_text"]
        if {src, tgt} != {"vi", "en"} or not is_glossary_term(source) or not is_glossary_term(target):
            raise ValueError("Seed requires short bilingual terms in both directions")
        if has_internal_placeholder(source) or has_internal_placeholder(target):
            raise ValueError("Seed contains an internal marker")
        if "?" in source + target or "\ufffd" in source + target:
            raise ValueError("Seed contains a damaged character or sentence punctuation")
        key = (src, tgt, source.strip(" .,!?;:\"'").lower())
        if key in seen:
            raise ValueError("Seed contains duplicate or conflicting sources")
        seen.add(key)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=BACKEND / "resources/dictionary_seed500.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--actor-id", type=int)
    args = parser.parse_args()
    rows = load_seed(args.seed)
    from app.db.database import SessionLocal, engine
    from app.db.models import AuditLog, User
    from app.services import translation_memory as tm
    repository = tm.DatabaseTranslationMemoryRepository()
    with SessionLocal() as db:
        existing = repository.get_entries("global:approved", db=db)
        keys = {(tm._normalize(row["source_text"]), row["source_lang"] or "", row["target_lang"] or "")
                for row in existing}
        pending = [row for row in rows if (tm._normalize(row["source_text"]), row["source_lang"], row["target_lang"]) not in keys
                   and (tm._normalize(row["source_text"]), "", "") not in keys]
        report = {"mode": "apply" if args.apply else "preview", "existing": len(existing),
                  "stored_directions": dict(Counter(f'{r["source_lang"]}->{r["target_lang"]}' for r in existing)),
                  "seed_entries": len(rows), "to_add": len(pending), "preserved": len(rows) - len(pending),
                  "directions": dict(Counter(f'{r["source_lang"]}->{r["target_lang"]}' for r in pending))}
        report["available_actors"] = [
            {"id": actor.id, "username": actor.username}
            for actor in db.query(User).filter(User.role == "superadmin", User.is_active == True).all()
        ]
        if args.apply and pending:
            actors = db.query(User).filter(User.role == "superadmin", User.is_active == True)
            if args.actor_id is not None:
                actors = actors.filter(User.id == args.actor_id)
            actors = actors.all()
            if len(actors) != 1:
                raise ValueError("Specify --actor-id for one active superadmin")
            if engine.dialect.name != "sqlite" or engine.url.database in (None, ":memory:"):
                raise ValueError("Use authenticated admin import for remote databases")
            backup_dir = BACKEND / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / ("dictionary-seed-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".db")
            # sqlite backup includes committed WAL pages; a raw file copy may not.
            with closing(sqlite3.connect(str(engine.url.database))) as source, closing(sqlite3.connect(str(backup))) as destination:
                source.backup(destination)
            repository.add_many(pending, "global:approved", db=db)
            db.add(AuditLog(actor_user_id=actors[0].id, actor_username=actors[0].username,
                            action="dictionary.seed", resource_type="dictionary",
                            details=json.dumps({"added": len(pending), "sha256": hashlib.sha256(args.seed.read_bytes()).hexdigest()})))
            db.commit()
            tm.invalidate_owner("global:approved")
            report["backup"] = str(backup)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

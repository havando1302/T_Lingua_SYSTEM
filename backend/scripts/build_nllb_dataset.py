"""Build a deterministic, upload-ready NLLB dataset from a reviewed CSV corpus."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.utils.translation_safety import INTERNAL_PLACEHOLDER


PLACEHOLDER = INTERNAL_PLACEHOLDER
LANGS = {"vi", "en"}


def normalized(value: object) -> str:
    return unicodedata.normalize("NFC", str(value or "").strip())


def stable_split(key: str) -> str:
    bucket = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    with args.source_csv.open(encoding="utf-8-sig", newline="") as stream:
        for number, raw in enumerate(csv.DictReader(stream), 2):
            source = normalized(raw.get("source"))
            target = normalized(raw.get("reference") or raw.get("target"))
            source_lang = normalized(raw.get("source_lang")).lower()
            target_lang = normalized(raw.get("target_lang")).lower()
            reason = ""
            if not source or not target:
                reason = "missing_source_or_target"
            elif source_lang not in LANGS or target_lang not in LANGS or source_lang == target_lang:
                reason = "invalid_language_direction"
            elif PLACEHOLDER.search(source) or PLACEHOLDER.search(target):
                reason = "placeholder_leak"
            key = (source_lang, target_lang, source.casefold())
            if not reason and key in seen:
                reason = "duplicate_source"
            if reason:
                rejected.append({"row": str(number), "reason": reason})
                continue
            seen.add(key)
            case_id = normalized(raw.get("case_id")) or f"phase2-{len(rows) + 1:04d}"
            rows.append({
                "id": case_id,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source": source,
                "target": target,
                "domain": normalized(raw.get("domain")) or "general",
                "split": stable_split(f"{source_lang}|{target_lang}|{source.casefold()}"),
            })

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    args.output_jsonl.write_text(payload, encoding="utf-8", newline="\n")
    counts = Counter(row["split"] for row in rows)
    directions = Counter(f'{row["source_lang"]}->{row["target_lang"]}' for row in rows)
    domains = Counter(row["domain"] for row in rows)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.source_csv.resolve()),
        "output_file": str(args.output_jsonl.resolve()),
        "valid": bool(rows and counts["train"] and counts["validation"]),
        "sample_count": len(rows),
        "train_count": counts["train"],
        "validation_count": counts["validation"],
        "test_count": counts["test"],
        "directions": dict(sorted(directions.items())),
        "domains": dict(sorted(domains.items())),
        "rejected_count": len(rejected),
        "rejected": rejected,
        "placeholder_count": sum(bool(PLACEHOLDER.search(row["source"] + row["target"])) for row in rows),
        "duplicate_count": len(rows) - len(seen),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }
    report_path = args.output_jsonl.with_name(args.output_jsonl.stem + "_validation.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] and not rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())

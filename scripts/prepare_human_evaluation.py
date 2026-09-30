"""Create a blank, auditable human-review form from the pilot benchmark."""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "progress_2026-09-24" / "evidence" / "translation_baseline_cases.csv"
OUTPUT = ROOT / "docs" / "progress_2026-09-24" / "evidence" / "human_evaluation_form.csv"


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    fields = [
        "case_id", "source_lang", "target_lang", "source", "hypothesis",
        "reviewer_id", "adequacy_1_5", "fluency_1_5", "error_category",
        "critical_error_yes_no", "reviewer_correction", "reviewer_note",
    ]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})
    print(f"Created {OUTPUT} with {len(rows)} blank review rows")


if __name__ == "__main__":
    main()

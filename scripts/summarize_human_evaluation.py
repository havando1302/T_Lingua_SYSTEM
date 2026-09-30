"""Validate two-reviewer scoring and publish an auditable human-evaluation summary."""
from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "progress_2026-09-24" / "evidence"
FORM = EVIDENCE / "human_evaluation_v2_two_reviewers.csv"
OUTPUT = EVIDENCE / "human_evaluation_v2_summary.json"
ERRORS = {"none", "omission", "addition", "mistranslation", "terminology", "entity_number", "grammar", "style"}


def main() -> None:
    with FORM.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    problems = []
    by_case = defaultdict(list)
    for number, row in enumerate(rows, 2):
        by_case[row["case_id"]].append(row)
        for field in ("reviewer_id", "reviewer_signature", "reviewed_at", "adequacy_1_5", "fluency_1_5", "error_category", "critical_error"):
            if not row[field].strip(): problems.append(f"row {number}: missing {field}")
        for field in ("adequacy_1_5", "fluency_1_5"):
            if row[field].strip() and (not row[field].isdigit() or not 1 <= int(row[field]) <= 5):
                problems.append(f"row {number}: {field} must be 1..5")
        if row["error_category"].strip() and row["error_category"].strip() not in ERRORS:
            problems.append(f"row {number}: invalid error_category")
        if row["critical_error"].strip().casefold() not in {"true", "false", "yes", "no", "1", "0", "có", "không"}:
            problems.append(f"row {number}: critical_error must be true/false")
    for case_id, assessments in by_case.items():
        if len(assessments) != 2 or len({row["reviewer_id"] for row in assessments}) != 2:
            problems.append(f"{case_id}: requires exactly two different reviewers")
    if problems:
        raise SystemExit("Human evaluation is incomplete or invalid:\n- " + "\n- ".join(problems[:30]))
    adequacy = [int(row["adequacy_1_5"]) for row in rows]; fluency = [int(row["fluency_1_5"]) for row in rows]
    disagreement = [case_id for case_id, values in by_case.items() if abs(int(values[0]["adequacy_1_5"]) - int(values[1]["adequacy_1_5"])) > 1 or abs(int(values[0]["fluency_1_5"]) - int(values[1]["fluency_1_5"])) > 1]
    critical = sum(row["critical_error"].strip().casefold() in {"true", "yes", "1", "có"} for row in rows)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "cases": len(by_case), "ratings": len(rows),
        "reviewers": sorted({row["reviewer_id"] for row in rows}),
        "mean_adequacy": round(statistics.mean(adequacy), 3), "mean_fluency": round(statistics.mean(fluency), 3),
        "critical_error_rate": round(critical / len(rows), 4),
        "error_categories": dict(Counter(row["error_category"] for row in rows)),
        "cases_requiring_adjudication": disagreement,
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

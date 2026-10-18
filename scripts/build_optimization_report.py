"""Build an auditable before/after report from the two fresh500 result sets."""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "fresh500_evaluation_20261014"
OPT = ROOT / "outputs" / "fresh500_optimized_20261014"


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ("latency_ms", "token_f1", "chrf", "numeric_fidelity"):
            row[key] = float(row[key])
    return rows


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summary(rows: list[dict]) -> dict:
    latency = [row["latency_ms"] for row in rows]
    return {
        "cases": len(rows),
        "latency_mean_ms": round(statistics.mean(latency), 3),
        "latency_p95_ms": round(percentile(latency, .95), 3),
        "within_1000ms_pct": round(statistics.mean(value <= 1000 for value in latency) * 100, 2),
        "token_f1_pct": round(statistics.mean(row["token_f1"] for row in rows) * 100, 4),
        "chrf_pct": round(statistics.mean(row["chrf"] for row in rows) * 100, 4),
        "numeric_fidelity_pct": round(statistics.mean(row["numeric_fidelity"] for row in rows) * 100, 2),
    }


def grouped(rows: list[dict], key: str) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return {name: summary(items) for name, items in sorted(groups.items())}


def main() -> None:
    baseline = read_rows(BASE / "fresh_500_translation_results.csv")
    optimized = read_rows(OPT / "fresh_500_translation_results.csv")
    if [r["case_id"] for r in baseline] != [r["case_id"] for r in optimized]:
        raise RuntimeError("Before/after rows do not contain the same ordered case IDs")
    before, after = summary(baseline), summary(optimized)
    payload = {
        "method": "Same 500 cases and model revision; only production decoding changed.",
        "dataset_sha256": json.loads((OPT / "fresh_500_results.json").read_text(encoding="utf-8"))["metadata"]["dataset_sha256"],
        "baseline": before,
        "optimized": after,
        "improvement": {
            "mean_latency_reduction_pct": round((before["latency_mean_ms"] - after["latency_mean_ms"]) / before["latency_mean_ms"] * 100, 2),
            "p95_latency_reduction_pct": round((before["latency_p95_ms"] - after["latency_p95_ms"]) / before["latency_p95_ms"] * 100, 2),
            "within_1000ms_gain_points": round(after["within_1000ms_pct"] - before["within_1000ms_pct"], 2),
            "token_f1_gain_points": round(after["token_f1_pct"] - before["token_f1_pct"], 4),
            "chrf_gain_points": round(after["chrf_pct"] - before["chrf_pct"], 4),
        },
        "targets": {
            "translation_mean_under_1000ms": after["latency_mean_ms"] < 1000,
            "translation_p95_under_1000ms": after["latency_p95_ms"] < 1000,
            "translation_token_f1_at_least_70pct": after["token_f1_pct"] >= 70,
            "numeric_fidelity_100pct": after["numeric_fidelity_pct"] == 100,
        },
        "optimized_by_source_language": grouped(optimized, "source_lang"),
        "optimized_by_domain": grouped(optimized, "domain"),
        "unchanged_stt_baseline": {
            "latency_mean_ms": 784.389,
            "latency_p95_ms": 1276.958,
            "word_accuracy_pct": 82.0044,
            "char_accuracy_pct": 88.5377,
            "mean_realtime_factor": 0.097726,
            "note": "STT model and decoding were not changed in this optimization; these are the validated fresh500 baseline values.",
        },
    }
    (OPT / "before_after_optimization_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows = []
    for metric in ("latency_mean_ms", "latency_p95_ms", "within_1000ms_pct", "token_f1_pct", "chrf_pct", "numeric_fidelity_pct"):
        rows.append({"metric": metric, "before": before[metric], "after": after[metric]})
    with (OPT / "before_after_summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["metric", "before", "after"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

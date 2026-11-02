"""Summarize paired held-out quality results, retaining regressions for review."""
import argparse
import json
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--candidate-directory", type=Path)
    args = parser.parse_args()
    result = json.loads((args.directory / "holdout/results.json").read_text(encoding="utf-8"))
    candidate = json.loads((args.candidate_directory / "results.json").read_text(encoding="utf-8")) if args.candidate_directory else result
    for key in ["cases_sha256", "glossary_sha256", "partition"]:
        if result["metadata"][key] != candidate["metadata"][key]:
            raise ValueError(f"Baseline and candidate differ in {key}")
    rows = result["rows"]
    before = {r["case_id"]: r for r in rows if r["variant"] == "baseline"}
    after = {r["case_id"]: r for r in candidate["rows"] if r["variant"] == "beam3"}
    if before.keys() != after.keys():
        raise ValueError("Paired evaluation is incomplete")
    pairs = []
    for key in before:
        a, b = before[key], after[key]
        pairs.append({"case_id": key, "source_lang": a["source_lang"], "domain": a["domain"],
                      "source": a["source"], "reference": a["reference"],
                      "before": a["hypothesis"], "after": b["hypothesis"],
                      "token_f1_delta": b["token_f1"] - a["token_f1"],
                      "before_warnings": a.get("quality_warnings", []), "after_warnings": b.get("quality_warnings", [])})
    summaries = result["summary"]
    comparison = {
        "before": summaries["baseline"], "after": candidate["summary"]["beam3"],
        "baseline_metadata": result["metadata"], "candidate_metadata": candidate["metadata"],
        "paired_count": len(pairs),
        "f1_improved": sum(p["token_f1_delta"] > 1e-9 for p in pairs),
        "f1_regressed": sum(p["token_f1_delta"] < -1e-9 for p in pairs),
        "f1_unchanged": sum(abs(p["token_f1_delta"]) <= 1e-9 for p in pairs),
        "domain_f1_deltas": {domain: round(statistics.mean(p["token_f1_delta"] for p in pairs if p["domain"] == domain), 3)
                             for domain in sorted({p["domain"] for p in pairs})},
        "improvement_examples": sorted(pairs, key=lambda p: p["token_f1_delta"], reverse=True)[:6],
        "regression_examples": sorted(pairs, key=lambda p: p["token_f1_delta"])[:6],
        "limitations": [
            "Synthetic reference corpus with shared templates/vocabulary between tuning and validation; exact source overlap with the supplied training file is zero. Some validation examples were inspected while debugging, so this is regression validation rather than a blind generalization study.",
            "Text translation only; no new STT or TTS accuracy measurement and no independent human adequacy score.",
            "Similarity metrics are not percentages of correct translations; number/code checks cover literal numeric tokens, not all number words.",
            "Same cached base NLLB revision and bundled glossary in isolated TM, no cache or private terms; not a remote deployment audit.",
            "GPU timings are sequential single-machine samples and vary with thermal/load conditions.",
        ],
    }
    (args.directory / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: comparison[key] for key in ["paired_count", "f1_improved", "f1_regressed", "f1_unchanged", "domain_f1_deltas"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

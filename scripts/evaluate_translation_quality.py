"""Reproducible offline evaluation of the real T-Lingua text translation path.

Uses cached pinned NLLB weights, an isolated copy of the bundled glossary,
no translation cache, and no production writes. Five cases per domain are
reserved for tuning; remaining cases are held out from configuration choices.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
import unicodedata
from unittest.mock import patch
from contextlib import ExitStack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split()).strip(" .!?")


def token_f1(reference, hypothesis):
    import re
    ref = Counter(re.findall(r"\w+", reference.casefold()))
    hyp = Counter(re.findall(r"\w+", hypothesis.casefold()))
    return 200 * sum((ref & hyp).values()) / max(1, sum(ref.values()) + sum(hyp.values()))


def summarize(rows):
    from sacrebleu.metrics import BLEU, CHRF
    successful = [r for r in rows if not r.get("error")]
    # Empty failed outputs remain in quality denominators.
    hypotheses = [r.get("hypothesis", "") for r in rows]
    references = [[r["reference"] for r in rows]]
    latency = sorted(r["latency_ms"] for r in rows)
    return {"count": len(rows), "successful": len(successful),
            "bleu": round(BLEU(effective_order=True).corpus_score(hypotheses, references).score, 3),
            "chrf_pp": round(CHRF(word_order=2).corpus_score(hypotheses, references).score, 3),
            "mean_token_f1": round(statistics.mean(r["token_f1"] for r in rows), 3),
            "entity_loss_cases": sum(bool(r.get("missing_entities")) for r in rows),
            "placeholder_cases": sum(r.get("placeholder", False) for r in rows),
            "retry_cases": sum(r.get("quality_retried", False) for r in rows),
            "latency_mean_ms": round(statistics.mean(latency), 3),
            "latency_p95_ms": round(latency[min(len(latency)-1, int(len(latency)*.95))], 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "outputs/fresh500_optimized_20261014/fresh_500_test_cases.csv")
    parser.add_argument("--training", type=Path, default=ROOT / "outputs/nllb_dataset_phase2/nllb-training.jsonl")
    parser.add_argument("--allow-training-overlap", action="store_true",
                        help="Only for known regression fixtures; overlap remains recorded in metadata")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--service-file", type=Path, help="Archived service source for paired baseline evaluation")
    parser.add_argument("--paired-baseline", type=Path, help="Evaluate the archived baseline and candidate with the same loaded model")
    parser.add_argument("--baseline-beam", type=int, default=1, choices=range(1, 9))
    parser.add_argument("--partition", choices=["tune", "holdout", "all"], default="tune")
    parser.add_argument("--variants", nargs="+", choices=["current", "beam1", "beam3", "baseline"], default=["current"])
    args = parser.parse_args()
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from app.services import translation_service as service, translation_memory as tm
    if args.service_file:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_quality_baseline_service", args.service_file)
        service = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(service)
    baseline_service = None
    if args.paired_baseline:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_paired_baseline_service", args.paired_baseline)
        baseline_service = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline_service)
    if "baseline" in args.variants and baseline_service is None:
        raise ValueError("--paired-baseline is required for the baseline variant")
    from app.utils.translation_safety import has_internal_placeholder
    if args.cases.suffix.lower() == ".json":
        cases = json.loads(args.cases.read_text(encoding="utf-8"))
        for case in cases:
            case.setdefault("case_id", case.get("id"))
    else:
        cases = list(csv.DictReader(args.cases.open(encoding="utf-8-sig", newline="")))
    training = [json.loads(line) for line in args.training.read_text(encoding="utf-8").splitlines() if line.strip()]
    trained = {(r["source_lang"], normalized(r["source"])) for r in training}
    overlap = [r["case_id"] for r in cases if (r["source_lang"], normalized(r["source"])) in trained]
    if overlap and not args.allow_training_overlap:
        raise ValueError(f"Evaluation overlaps the training corpus in {len(overlap)} cases")
    seen = set()
    for case in cases:
        key = (case["source_lang"], normalized(case["source"]))
        if key in seen:
            raise ValueError("Duplicate evaluation source")
        seen.add(key)
    domains = Counter()
    for case in cases:
        case["partition"] = "tune" if domains[case["domain"]] < 5 else "holdout"
        domains[case["domain"]] += 1
    selected = [r for r in cases if args.partition == "all" or r["partition"] == args.partition]
    if not selected:
        raise ValueError("Empty evaluation selection")
    seed_path = ROOT / "backend/resources/dictionary_seed500.json"
    glossary = json.loads(seed_path.read_text(encoding="utf-8"))["entries"]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id, revision = service.settings.NLLB_MODEL, service.settings.NLLB_REVISION
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = {"model": model_id, "revision": revision, "device": device,
                "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
                "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
                "glossary_sha256": hashlib.sha256(seed_path.read_bytes()).hexdigest(),
                "service_sha256": hashlib.sha256(Path(service.__file__).read_bytes()).hexdigest(),
                "fidelity_sha256": hashlib.sha256((ROOT / "backend/app/services/translation_fidelity.py").read_bytes()).hexdigest(),
                "beam": service.settings.TRANSLATION_BEAM_SIZE,
                "fidelity_rerank": service.settings.TRANSLATION_FIDELITY_RERANK,
                "length_penalty": service.settings.TRANSLATION_LENGTH_PENALTY,
                "baseline_sha256": hashlib.sha256(args.paired_baseline.read_bytes()).hexdigest() if args.paired_baseline else None,
                "training_overlap": len(overlap), "partition": args.partition,
                "scope": "text path, repository defaults, bundled 500-entry glossary, isolated TM, cache disabled",
                "quality_metric_note": "reference similarity scores, not percent accuracy; no human adequacy rating",
                "torch": torch.__version__, "sample_count": len(selected)}
    print(json.dumps({"stage": "loading", **metadata}), flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_id, revision=revision, local_files_only=True,
        dtype=torch.float16 if device == "cuda" else torch.float32,
    ).to(device).eval()
    model.generation_config.max_length = None
    rows = []
    base_beam = service.settings.TRANSLATION_BEAM_SIZE
    with tempfile.TemporaryDirectory(prefix="quality-tm-") as directory, \
         patch.object(tm, "_TM_FILE", str(Path(directory) / "tm.json")), \
         patch.object(tm, "_memory", {}), \
         patch.object(service, "_get_nllb", return_value=(model, tokenizer)), ExitStack() as stack:
        if baseline_service:
            stack.enter_context(patch.object(baseline_service, "_get_nllb", return_value=(model, tokenizer)))
        tm.add_many(glossary, "global:approved")
        # Warm model kernels without including the cold start in measurements.
        service.translate_text("Hello.", source_lang="en", target_lang="vi", use_cache=False)
        for variant in args.variants:
            runtime = baseline_service if variant == "baseline" else service
            beam = {"baseline": args.baseline_beam, "beam1": 1, "beam3": 3}.get(variant, base_beam)
            with patch.object(service.settings, "TRANSLATION_BEAM_SIZE", beam):
                for index, case in enumerate(selected, 1):
                    started = time.perf_counter()
                    row = {**case, "variant": variant, "beam": beam, "hypothesis": ""}
                    try:
                        result = runtime.translate_text(case["source"], source_lang=case["source_lang"],
                                                        target_lang=case["target_lang"], use_cache=False)
                        row.update({key: value for key, value in result.items() if key != "source"})
                        row["translation_source"] = result.get("source")
                        row["hypothesis"] = result["translated_text"]
                    except Exception as error:
                        row["error"] = type(error).__name__ + ": " + str(error)
                    if device == "cuda":
                        torch.cuda.synchronize()
                    row["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
                    row["token_f1"] = token_f1(case["reference"], row["hypothesis"])
                    expected = Counter(v.casefold() for v in service._PROTECTED_ENTITY.findall(case["source"]))
                    actual = Counter(v.casefold() for v in service._PROTECTED_ENTITY.findall(row["hypothesis"]))
                    row["missing_entities"] = list((expected - actual).elements())
                    row["placeholder"] = has_internal_placeholder(row["hypothesis"])
                    rows.append(row)
                    if index % 10 == 0 or index == len(selected):
                        (args.output / "checkpoint.json").write_text(json.dumps({"metadata": metadata, "rows": rows}, ensure_ascii=False), encoding="utf-8")
                        print(json.dumps({"stage": "evaluating", "variant": variant, "completed": index,
                                          "total": len(selected), "last_error": row.get("error")}), flush=True)
    summary = {}
    for variant in args.variants:
        group = [r for r in rows if r["variant"] == variant]
        summary[variant] = {"overall": summarize(group), "by_direction": {}, "by_domain": {}}
        for key, destination in [("source_lang", "by_direction"), ("domain", "by_domain")]:
            for value in sorted({r[key] for r in group}):
                summary[variant][destination][value] = summarize([r for r in group if r[key] == value])
    (args.output / "results.json").write_text(json.dumps({"metadata": metadata, "summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "summary.json").write_text(json.dumps({"metadata": metadata, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage": "complete", "summary": summary}, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

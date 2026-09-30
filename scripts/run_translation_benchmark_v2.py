"""Run the versioned 500-case corpus against the cached local NLLB model."""
from __future__ import annotations

import csv
import json
import math
import platform
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from run_translation_benchmark import percentile, token_f1


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"
DATASET = OUT / "benchmark_v2_500.csv"
MODEL_ID = "facebook/nllb-200-distilled-1.3B"
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def ngrams(tokens: list[str], size: int) -> Counter:
    return Counter(tuple(tokens[index:index + size]) for index in range(len(tokens) - size + 1))


def tokenize(text: str) -> list[str]:
    return "".join(char.casefold() if char.isalnum() else " " for char in text).split()


def corpus_bleu(rows: list[dict]) -> float:
    clipped = [0, 0, 0, 0]; totals = [0, 0, 0, 0]
    hypothesis_length = reference_length = 0
    for row in rows:
        reference, hypothesis = tokenize(row["reference"]), tokenize(row["hypothesis"])
        reference_length += len(reference); hypothesis_length += len(hypothesis)
        for index, size in enumerate(range(1, 5)):
            expected, actual = ngrams(reference, size), ngrams(hypothesis, size)
            clipped[index] += sum((expected & actual).values()); totals[index] += sum(actual.values())
    precisions = [(clipped[index] + 1) / (totals[index] + 1) for index in range(4)]
    brevity = 1.0 if hypothesis_length > reference_length else math.exp(1 - reference_length / max(1, hypothesis_length))
    return 100 * brevity * math.exp(sum(math.log(value) for value in precisions) / 4)


def chrf(reference: str, hypothesis: str) -> float:
    reference = " ".join(reference.casefold().split()); hypothesis = " ".join(hypothesis.casefold().split())
    scores = []
    for size in range(1, 7):
        expected = Counter(reference[index:index + size] for index in range(max(0, len(reference) - size + 1)))
        actual = Counter(hypothesis[index:index + size] for index in range(max(0, len(hypothesis) - size + 1)))
        overlap = sum((expected & actual).values())
        precision = overlap / max(1, sum(actual.values())); recall = overlap / max(1, sum(expected.values()))
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return 100 * statistics.mean(scores)


def main() -> None:
    if not DATASET.exists():
        raise SystemExit("Run scripts/prepare_benchmark_v2.py first")
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        cases = list(csv.DictReader(stream))
    if len(cases) != 500:
        raise SystemExit(f"Expected 500 cases, got {len(cases)}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, dtype=dtype, local_files_only=True).to(device).eval()
    model.generation_config.max_length = None
    load_seconds = time.perf_counter() - load_started
    if device == "cuda": torch.cuda.reset_peak_memory_stats()
    results = []; latencies = []
    for index, case in enumerate(cases, 1):
        tokenizer.src_lang = LANG[case["source_lang"]]
        encoded = tokenizer(case["source"], return_tensors="pt").to(device)
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **encoded, forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG[case["target_lang"]]),
                max_new_tokens=128, num_beams=1, no_repeat_ngram_size=3,
            )
        if device == "cuda": torch.cuda.synchronize()
        latency = (time.perf_counter() - started) * 1000
        hypothesis = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
        terms = [term.strip() for term in case["required_terms"].split("|") if term.strip()]
        hits = sum(term.casefold() in hypothesis.casefold() for term in terms)
        results.append(case | {
            "hypothesis": hypothesis, "latency_ms": round(latency, 3),
            "token_f1": round(token_f1(case["reference"], hypothesis), 4),
            "chrf": round(chrf(case["reference"], hypothesis), 3),
            "term_hits": hits, "term_total": len(terms),
        })
        latencies.append(latency)
        if index % 50 == 0: print(f"completed {index}/500", flush=True)
    total_terms = sum(row["term_total"] for row in results); total_hits = sum(row["term_hits"] for row in results)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "scope": "local_translation_benchmark_v2",
        "model_id": MODEL_ID, "dataset": DATASET.name, "cases": len(results),
        "device": device, "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "python": platform.python_version(), "torch": torch.__version__, "load_seconds": round(load_seconds, 3),
        "latency_ms": {name: round(value, 3) for name, value in {
            "mean": statistics.mean(latencies), "p50": percentile(latencies, .5),
            "p95": percentile(latencies, .95), "p99": percentile(latencies, .99),
            "min": min(latencies), "max": max(latencies),
        }.items()},
        "quality": {
            "corpus_bleu_smoothed": round(corpus_bleu(results), 3),
            "mean_chrf": round(statistics.mean(row["chrf"] for row in results), 3),
            "mean_token_f1": round(statistics.mean(row["token_f1"] for row in results), 4),
            "required_term_accuracy": round(total_hits / total_terms, 4), "term_hits": total_hits, "term_total": total_terms,
        },
        "gpu_peak_memory_mb": round(torch.cuda.max_memory_allocated() / 1024 ** 2, 2) if device == "cuda" else None,
        "limitations": [
            "Controlled synthetic template corpus; not a substitute for licensed natural-domain data.",
            "BLEU implementation uses add-one smoothing; compare only with runs from this script.",
            "COMET and independent human review are not included in this automated run.",
        ],
    }
    with (OUT / "translation_benchmark_v2_cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0])); writer.writeheader(); writer.writerows(results)
    (OUT / "translation_benchmark_v2_summary.json").write_text(json.dumps({"summary": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

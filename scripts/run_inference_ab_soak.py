"""Compare beam settings and run a bounded repeated-inference GPU soak check."""
from __future__ import annotations

import csv
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from run_translation_benchmark import percentile, token_f1
from run_translation_benchmark_v2 import chrf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"
MODEL_ID = "facebook/nllb-200-distilled-1.3B"
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def main() -> None:
    with (OUT / "benchmark_v2_500.csv").open(encoding="utf-8-sig", newline="") as stream:
        corpus = list(csv.DictReader(stream))
    sample = corpus[:25] + corpus[250:275]
    device = "cuda" if torch.cuda.is_available() else "cpu"; dtype = torch.float16 if device == "cuda" else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, dtype=dtype, local_files_only=True).to(device).eval()
    model.generation_config.max_length = None

    def translate(case: dict, beams: int) -> tuple[str, float]:
        tokenizer.src_lang = LANG[case["source_lang"]]; encoded = tokenizer(case["source"], return_tensors="pt").to(device)
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(**encoded, forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG[case["target_lang"]]), max_new_tokens=128, num_beams=beams, no_repeat_ngram_size=3)
        if device == "cuda": torch.cuda.synchronize()
        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip(), (time.perf_counter() - started) * 1000

    configurations = {}
    for beams in (1, 3):
        rows = []
        for case in sample:
            hypothesis, latency = translate(case, beams)
            terms = [term.strip() for term in case["required_terms"].split("|") if term.strip()]
            rows.append({"latency": latency, "f1": token_f1(case["reference"], hypothesis), "chrf": chrf(case["reference"], hypothesis), "hits": sum(term.casefold() in hypothesis.casefold() for term in terms), "terms": len(terms)})
        configurations[f"beam_{beams}"] = {
            "cases": len(rows), "latency_mean_ms": round(statistics.mean(row["latency"] for row in rows), 3),
            "latency_p95_ms": round(percentile([row["latency"] for row in rows], .95), 3),
            "mean_token_f1": round(statistics.mean(row["f1"] for row in rows), 4),
            "mean_chrf": round(statistics.mean(row["chrf"] for row in rows), 3),
            "term_accuracy": round(sum(row["hits"] for row in rows) / max(1, sum(row["terms"] for row in rows)), 4),
        }
    memory = []; soak_latencies = []; oom = False; started = time.perf_counter()
    try:
        for index in range(200):
            _, latency = translate(sample[index % len(sample)], 1); soak_latencies.append(latency)
            if device == "cuda" and (index + 1) % 20 == 0:
                memory.append(round(torch.cuda.memory_allocated() / 1024 ** 2, 2))
    except torch.cuda.OutOfMemoryError:
        oom = True
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "device": device,
        "ab_test": configurations,
        "selected_configuration": "beam_1" if configurations["beam_1"]["latency_p95_ms"] < configurations["beam_3"]["latency_p95_ms"] and configurations["beam_1"]["mean_chrf"] >= configurations["beam_3"]["mean_chrf"] - 1 else "manual_review_required",
        "soak": {
            "iterations_requested": 200, "iterations_completed": len(soak_latencies),
            "duration_seconds": round(time.perf_counter() - started, 3), "oom": oom,
            "latency_p95_ms": round(percentile(soak_latencies, .95), 3) if soak_latencies else None,
            "memory_samples_mb": memory, "memory_growth_mb": round(memory[-1] - memory[0], 2) if len(memory) > 1 else None,
        },
        "limitations": ["Bounded 200-iteration local soak, not a multi-hour concurrent production load test."],
    }
    (OUT / "inference_ab_soak_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

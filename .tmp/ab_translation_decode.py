"""Small, reproducible A/B check for NLLB decoding choices on fresh500."""
from __future__ import annotations

import csv
import re
import statistics
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_fresh_500_evaluation import chrf, token_f1

MODEL_ID = "facebook/nllb-200-distilled-1.3B"
REVISION = "7be3e24664b38ce1cac29b8aeed6911aa0cf0576"
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def main() -> None:
    rows = list(csv.DictReader(
        (ROOT / "outputs/fresh500_evaluation_20261014/fresh_500_test_cases.csv")
        .open(encoding="utf-8-sig")
    ))
    # Stratified selection: all 20 domains, two day/period variants.
    rows = rows[:20] + rows[250:270]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_ID, revision=REVISION, local_files_only=True,
        dtype=torch.float16 if device == "cuda" else torch.float32,
    ).to(device).eval()
    configs = {
        "sentence_batch_greedy": {"num_beams": 1, "segment_batch": True},
        "sentence_batch_beam2": {"num_beams": 2, "segment_batch": True},
        "sentence_batch_beam3": {"num_beams": 3, "segment_batch": True},
    }
    for name, generation in configs.items():
        latencies, f1s, chrfs, complete, details = [], [], [], [], []
        for row in rows:
            tokenizer.src_lang = LANG[row["source_lang"]]
            texts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", row["source"]) if part.strip()] if generation["segment_batch"] else [row["source"]]
            inputs = tokenizer(texts, return_tensors="pt", padding=True).to(device)
            if device == "cuda":
                torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(
                    **inputs,
                    forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG[row["target_lang"]]),
                    max_new_tokens=min(128, max(32, int(inputs.input_ids.shape[1] * 1.6) + 12)),
                    num_beams=generation["num_beams"],
                )
            if device == "cuda":
                torch.cuda.synchronize()
            translated = tokenizer.batch_decode(output, skip_special_tokens=True)
            hypothesis = " ".join(part.lstrip("- ").strip().rstrip(".") + "." for part in translated)
            latencies.append((time.perf_counter() - started) * 1000)
            f1s.append(token_f1(row["reference"], hypothesis))
            chrfs.append(chrf(row["reference"], hypothesis))
            complete.append(int(hypothesis.count(".") >= 2))
            details.append((f1s[-1], row, hypothesis))
        print(name, {
            "mean_ms": round(statistics.mean(latencies), 1),
            "p95_ms": round(sorted(latencies)[int(len(latencies) * .95) - 1], 1),
            "f1_pct": round(statistics.mean(f1s) * 100, 2),
            "chrf_pct": round(statistics.mean(chrfs) * 100, 2),
            "two_sentence_pct": round(statistics.mean(complete) * 100, 2),
        })
        for score, row, hypothesis in sorted(details, key=lambda item: item[0])[:10]:
            print("\n", row["case_id"], row["domain"], round(score, 3))
            print("REF", row["reference"])
            print("HYP", hypothesis)


if __name__ == "__main__":
    main()

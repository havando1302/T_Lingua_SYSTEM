"""Evaluate the temporary CTranslate2 NLLB conversion against fresh500."""
from __future__ import annotations

import csv
import re
import statistics
import sys
import time
from pathlib import Path

import ctranslate2
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_fresh_500_evaluation import chrf, token_f1

HF_MODEL = Path.home() / ".cache/huggingface/hub/models--facebook--nllb-200-distilled-1.3B/snapshots/7be3e24664b38ce1cac29b8aeed6911aa0cf0576"
CT2_MODEL = ROOT / ".tmp/ct2_nllb_1_3b_int8"
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def pct(values, ratio):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * ratio))]


def main():
    with (ROOT / "outputs/fresh500_optimized_20261014/fresh_500_test_cases.csv").open(encoding="utf-8-sig") as stream:
        all_rows = list(csv.DictReader(stream))
    # 100 cases: five variants of each of the 20 domains.
    rows = all_rows[:50] + all_rows[250:300]
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, local_files_only=True)
    translator = ctranslate2.Translator(str(CT2_MODEL), device="cpu", compute_type="int8", inter_threads=1, intra_threads=8)
    translator.translate_batch([["▁Ready", "."]], target_prefix=[["eng_Latn"]], beam_size=1)
    latencies, f1s, chrfs, examples = [], [], [], []
    for row in rows:
        segments = [part.strip() for part in re.split(r"(?<=[.!?])\s+", row["source"]) if part.strip()]
        tokenizer.src_lang = LANG[row["source_lang"]]
        sources = []
        for segment in segments:
            ids = tokenizer(segment, add_special_tokens=True).input_ids
            sources.append(tokenizer.convert_ids_to_tokens(ids))
        started = time.perf_counter()
        results = translator.translate_batch(
            sources,
            target_prefix=[[LANG[row["target_lang"]]] for _ in sources],
            beam_size=1,
            max_decoding_length=96,
            repetition_penalty=1.0,
        )
        latency = (time.perf_counter() - started) * 1000
        parts = []
        for result in results:
            tokens = result.hypotheses[0]
            if tokens and tokens[0] == LANG[row["target_lang"]]:
                tokens = tokens[1:]
            parts.append(tokenizer.decode(tokenizer.convert_tokens_to_ids(tokens), skip_special_tokens=True).strip())
        hypothesis = " ".join(parts)
        score = token_f1(row["reference"], hypothesis)
        latencies.append(latency)
        f1s.append(score)
        chrfs.append(chrf(row["reference"], hypothesis))
        examples.append((score, row["source"], row["reference"], hypothesis))
    print({
        "mean_ms": round(statistics.mean(latencies), 2),
        "p95_ms": round(pct(latencies, .95), 2),
        "f1_pct": round(statistics.mean(f1s) * 100, 3),
        "chrf_pct": round(statistics.mean(chrfs) * 100, 3),
    })
    for score, source, reference, hypothesis in sorted(examples)[:5]:
        print("\n", round(score, 3), "\nSRC", source, "\nREF", reference, "\nHYP", hypothesis)


if __name__ == "__main__":
    main()

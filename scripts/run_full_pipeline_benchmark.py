"""Measure a warm local STT -> NLLB -> TTS pipeline on real model inference."""
from __future__ import annotations

import cProfile
import csv
import gc
import io
import json
import pstats
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.io.wavfile
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values); position = (len(ordered) - 1) * ratio
    low = int(position); high = min(low + 1, len(ordered) - 1); part = position - low
    return ordered[low] + (ordered[high] - ordered[low]) * part


def stats(values: list[float]) -> dict:
    return {"mean": round(statistics.mean(values), 3), "p50": round(percentile(values, .5), 3), "p95": round(percentile(values, .95), 3), "p99": round(percentile(values, .99), 3)}


def main() -> None:
    with (OUT / "speech_benchmark_v2_cases.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    clean_vi = [row for row in rows if row["condition"] == "clean" and row["source_lang"] == "vi"][:5]
    clean_en = [row for row in rows if row["condition"] == "clean" and row["source_lang"] == "en"][:5]
    cases = clean_vi + clean_en
    device = "cuda" if torch.cuda.is_available() else "cpu"; dtype = torch.float16 if device == "cuda" else torch.float32
    from app.ai.torch_whisper_adapter import TorchWhisperModel
    whisper = TorchWhisperModel("openai/whisper-small", device, local_files_only=True)
    nllb_tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-1.3B", local_files_only=True)
    nllb = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-1.3B", dtype=dtype, local_files_only=True).to(device).eval()
    nllb.generation_config.max_length = None
    tts = {}
    for language, model_id in (("en", "facebook/mms-tts-eng"), ("vi", "facebook/mms-tts-vie")):
        tts[language] = (AutoTokenizer.from_pretrained(model_id, local_files_only=True), VitsModel.from_pretrained(model_id, dtype=dtype, local_files_only=True).to(device).eval())
    if device == "cuda": torch.cuda.reset_peak_memory_stats()

    def run(case: dict) -> dict:
        _, pcm = scipy.io.wavfile.read(ROOT / case["file"]); audio = pcm.astype(np.float32) / 32768.0
        started = time.perf_counter(); segments, _ = whisper.transcribe(audio, language=case["source_lang"], beam_size=1)
        if device == "cuda": torch.cuda.synchronize()
        stt_done = time.perf_counter(); transcript = " ".join(segment.text for segment in segments).strip()
        target = "en" if case["source_lang"] == "vi" else "vi"; nllb_tokenizer.src_lang = LANG[case["source_lang"]]
        encoded = nllb_tokenizer(transcript, return_tensors="pt").to(device)
        with torch.inference_mode(): generated = nllb.generate(**encoded, forced_bos_token_id=nllb_tokenizer.convert_tokens_to_ids(LANG[target]), max_new_tokens=128, num_beams=1, no_repeat_ngram_size=3)
        if device == "cuda": torch.cuda.synchronize()
        translation_done = time.perf_counter(); translation = nllb_tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
        tts_tokenizer, tts_model = tts[target]; tts_inputs = tts_tokenizer(translation, return_tensors="pt").to(device)
        with torch.inference_mode(): waveform = tts_model(**tts_inputs).waveform
        if device == "cuda": torch.cuda.synchronize()
        done = time.perf_counter()
        return {
            "case_id": case["case_id"], "source_lang": case["source_lang"], "target_lang": target,
            "transcript": transcript, "translation": translation, "tts_samples": int(waveform.numel()),
            "stt_ms": (stt_done - started) * 1000, "translation_ms": (translation_done - stt_done) * 1000,
            "tts_ms": (done - translation_done) * 1000, "end_to_end_ms": (done - started) * 1000,
        }

    # Warm each direction once; measurements below exclude model load and warm-up.
    run(cases[0]); run(cases[-1])
    profiler = cProfile.Profile(); profiler.enable(); measured = [run(case) for case in cases]; profiler.disable()
    profiler.dump_stats(str(OUT / "full_pipeline_profile.prof")); report = io.StringIO()
    pstats.Stats(profiler, stream=report).sort_stats("cumulative").print_stats(40)
    (OUT / "full_pipeline_profile.txt").write_text(report.getvalue(), encoding="utf-8")
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "scope": "warm_local_stt_nllb_tts",
        "cases": len(measured), "device": device,
        "latency_ms": {stage: stats([row[stage + "_ms"] for row in measured]) for stage in ("stt", "translation", "tts", "end_to_end")},
        "throughput_sequential_turns_per_second": round(1000 / statistics.mean(row["end_to_end_ms"] for row in measured), 3),
        "gpu_peak_memory_mb": round(torch.cuda.max_memory_allocated() / 1024 ** 2, 2) if device == "cuda" else None,
        "network_ms": 0.0, "queue_wait_ms": 0.0,
        "limitations": [
            "Ten local warm sequential cases; network and queue are intentionally excluded.",
            "TTS time measures full waveform generation, not streaming first-chunk latency.",
            "Audio source is synthetic VITS speech; production capacity requires concurrent recorded-audio load tests.",
        ],
    }
    with (OUT / "full_pipeline_benchmark_cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(measured[0])); writer.writeheader(); writer.writerows(measured)
    (OUT / "full_pipeline_benchmark_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    del whisper, nllb, nllb_tokenizer, tts; gc.collect()


if __name__ == "__main__":
    main()

"""Generate 100 versioned clean/noisy audio samples and measure local Whisper WER."""
from __future__ import annotations

import csv
import gc
import hashlib
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.io.wavfile
import scipy.signal
import torch
from transformers import AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"
AUDIO_DIR = OUT / "audio_benchmark_v2"
DATASET = OUT / "benchmark_v2_500.csv"
MODELS = {"vi": "facebook/mms-tts-vie", "en": "facebook/mms-tts-eng"}


def normalize_tokens(text: str) -> list[str]:
    return "".join(char.casefold() if char.isalnum() else " " for char in text).split()


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row, expected in enumerate(reference, 1):
        current = [row]
        for column, actual in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (expected != actual)))
        previous = current
    return previous[-1]


def percentile(values: list[float], ratio: float) -> float:
    values = sorted(values); position = (len(values) - 1) * ratio
    low = int(position); high = min(low + 1, len(values) - 1); fraction = position - low
    return values[low] + (values[high] - values[low]) * fraction


def add_noise(audio: np.ndarray, snr_db: float, seed: int) -> np.ndarray:
    generator = np.random.default_rng(seed); noise = generator.normal(0, 1, len(audio)).astype(np.float32)
    signal_rms = math.sqrt(float(np.mean(audio ** 2)) + 1e-12)
    noise_rms = math.sqrt(float(np.mean(noise ** 2)) + 1e-12)
    scaled = noise * (signal_rms / (10 ** (snr_db / 20)) / noise_rms)
    return np.clip(audio + scaled, -1, 1)


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        all_cases = list(csv.DictReader(stream))
    cases = all_cases[:25] + all_cases[250:275]
    device = "cuda" if torch.cuda.is_available() else "cpu"; dtype = torch.float16 if device == "cuda" else torch.float32
    manifest = []; tts_latencies = []
    for language in ("vi", "en"):
        model_id = MODELS[language]
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
        model = VitsModel.from_pretrained(model_id, dtype=dtype, local_files_only=True).to(device).eval()
        for index, case in enumerate([row for row in cases if row["source_lang"] == language]):
            inputs = tokenizer(case["source"], return_tensors="pt").to(device)
            started = time.perf_counter()
            with torch.inference_mode(): audio = model(**inputs).waveform.squeeze().float().cpu().numpy()
            if device == "cuda": torch.cuda.synchronize()
            tts_latency = (time.perf_counter() - started) * 1000; tts_latencies.append(tts_latency)
            sample_rate = int(model.config.sampling_rate)
            if sample_rate != 16_000:
                divisor = math.gcd(sample_rate, 16_000)
                audio = scipy.signal.resample_poly(audio, 16_000 // divisor, sample_rate // divisor).astype(np.float32)
            variants = (("clean", audio, None), ("noisy_15db", add_noise(audio, 15.0, index + (0 if language == "vi" else 1000)), 15.0))
            for condition, waveform, snr in variants:
                path = AUDIO_DIR / f"{case['case_id']}_{condition}.wav"
                scipy.io.wavfile.write(path, 16_000, (waveform * 32767).astype(np.int16))
                manifest.append({
                    "case_id": case["case_id"], "condition": condition, "source_lang": language,
                    "reference": case["source"], "file": path.relative_to(ROOT).as_posix(),
                    "duration_seconds": round(len(waveform) / 16_000, 3), "snr_db": snr,
                    "tts_latency_ms": round(tts_latency, 3), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                })
        del model, tokenizer; gc.collect()
        if device == "cuda": torch.cuda.empty_cache()

    from app.ai.torch_whisper_adapter import TorchWhisperModel
    recognizer = TorchWhisperModel("openai/whisper-small", device, local_files_only=True)
    stt_latencies = []; total_edits = total_words = 0
    for index, row in enumerate(manifest, 1):
        sample_rate, pcm = scipy.io.wavfile.read(ROOT / row["file"])
        audio = pcm.astype(np.float32) / 32768.0
        started = time.perf_counter(); segments, _ = recognizer.transcribe(audio, language=row["source_lang"], beam_size=1)
        if device == "cuda": torch.cuda.synchronize()
        latency = (time.perf_counter() - started) * 1000; stt_latencies.append(latency)
        hypothesis = " ".join(segment.text for segment in segments).strip()
        expected, actual = normalize_tokens(row["reference"]), normalize_tokens(hypothesis)
        edits = edit_distance(expected, actual); total_edits += edits; total_words += len(expected)
        row.update(hypothesis=hypothesis, word_errors=edits, reference_words=len(expected), wer=round(edits / max(1, len(expected)), 4), stt_latency_ms=round(latency, 3), realtime_factor=round(latency / 1000 / row["duration_seconds"], 4))
        if index % 20 == 0: print(f"completed {index}/100", flush=True)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "scope": "synthetic_tts_to_stt_audio_benchmark_v2",
        "samples": len(manifest), "conditions": {"clean": 50, "noisy_15db": 50}, "device": device,
        "tts_latency_ms": {"mean": round(statistics.mean(tts_latencies), 3), "p95": round(percentile(tts_latencies, .95), 3)},
        "stt_latency_ms": {"mean": round(statistics.mean(stt_latencies), 3), "p50": round(percentile(stt_latencies, .5), 3), "p95": round(percentile(stt_latencies, .95), 3)},
        "wer": round(total_edits / max(1, total_words), 4),
        "wer_by_condition": {condition: round(sum(row["word_errors"] for row in manifest if row["condition"] == condition) / max(1, sum(row["reference_words"] for row in manifest if row["condition"] == condition)), 4) for condition in ("clean", "noisy_15db")},
        "mean_realtime_factor": round(statistics.mean(row["realtime_factor"] for row in manifest), 4),
        "limitations": [
            "Audio is generated by VITS and does not represent real speakers, accents, microphones or rooms.",
            "Noise is deterministic Gaussian noise at 15 dB; production acceptance requires recorded speech.",
            "TTS naturalness/MOS still requires independent human listeners.",
        ],
    }
    with (OUT / "speech_benchmark_v2_cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0])); writer.writeheader(); writer.writerows(manifest)
    (OUT / "speech_benchmark_v2_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

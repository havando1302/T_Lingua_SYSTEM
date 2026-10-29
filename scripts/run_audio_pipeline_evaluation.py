"""Evaluate WAV files through Whisper -> NLLB -> VITS and build evidence reports.

The default inputs are the 500 exported Whisper fixtures in ``outputs/am_thanh``.
Models are loaded one phase at a time so the tool remains usable on 6 GB GPUs.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import scipy.io.wavfile
import scipy.signal
import torch
import transformers
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DEFAULT_AUDIO_DIR = ROOT / "outputs" / "am_thanh"
DEFAULT_MANIFEST = DEFAULT_AUDIO_DIR / "manifest_500_am_thanh.csv"
DEFAULT_CASES = ROOT / "outputs" / "fresh500_optimized_20261014" / "fresh_500_test_cases.csv"
DEFAULT_BASELINE = ROOT / "outputs" / "fresh500_evaluation_20261014" / "fresh_500_results.json"

WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"
WHISPER_REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"
NLLB_MODEL_ID = "facebook/nllb-200-distilled-1.3B"
NLLB_REVISION = "7be3e24664b38ce1cac29b8aeed6911aa0cf0576"
TTS_MODELS = {
    "vi": ("facebook/mms-tts-vie", "b58928d033932a49aa8e3d6cf11625b25fe928d2"),
    "en": ("facebook/mms-tts-eng", "c71de0fe7204c83f1c10820a7d696d0b450048ba"),
}
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}
SAMPLE_RATE = 16_000
TTS_SEED_BASE = 20261024

DETAIL_FIELDS = [
    "order", "case_id", "source_lang", "target_lang", "domain", "length_group", "wav_file",
    "source_text", "reference_translation", "audio_duration_seconds",
    "transcript", "stt_ms", "stt_rtf", "word_errors", "reference_words", "wer",
    "stt_word_accuracy", "char_errors", "reference_chars", "cer",
    "stt_char_accuracy", "stt_exact_match",
    "direct_translation", "direct_translation_ms", "direct_token_f1", "direct_chrf",
    "direct_exact_match", "direct_numeric_fidelity",
    "pipeline_translation", "pipeline_translation_ms", "pipeline_token_f1",
    "pipeline_chrf", "pipeline_exact_match", "pipeline_numeric_fidelity",
    "translation_quality_delta_f1", "translation_quality_delta_chrf",
    "tts_ms", "tts_output_duration_seconds", "tts_rtf", "tts_sample_rate_hz",
    "tts_samples", "tts_output_file", "pipeline_ms", "pipeline_rtf", "status", "error",
]


def local_now() -> str:
    return datetime.now().astimezone().isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=DETAIL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(text: str) -> str:
    return " ".join("".join(char.casefold() if char.isalnum() else " " for char in text).split())


def normalize_tokens(text: str) -> list[str]:
    return normalize_text(text).split()


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row_number, expected in enumerate(reference, 1):
        current = [row_number]
        for column, actual in enumerate(hypothesis, 1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (expected != actual),
            ))
        previous = current
    return previous[-1]


def token_f1(reference: str, hypothesis: str) -> float:
    expected = Counter(normalize_tokens(reference))
    actual = Counter(normalize_tokens(hypothesis))
    overlap = sum((expected & actual).values())
    precision = overlap / max(1, sum(actual.values()))
    recall = overlap / max(1, sum(expected.values()))
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def chrf(reference: str, hypothesis: str) -> float:
    reference_normalized = normalize_text(reference)
    hypothesis_normalized = normalize_text(hypothesis)
    scores = []
    for size in range(1, 7):
        expected = Counter(
            reference_normalized[index:index + size]
            for index in range(max(0, len(reference_normalized) - size + 1))
        )
        actual = Counter(
            hypothesis_normalized[index:index + size]
            for index in range(max(0, len(hypothesis_normalized) - size + 1))
        )
        overlap = sum((expected & actual).values())
        precision = overlap / max(1, sum(actual.values()))
        recall = overlap / max(1, sum(expected.values()))
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def numeric_fidelity(reference: str, hypothesis: str) -> float:
    pattern = r"[A-Za-z]*\d+(?:[.:-]\d+)*[A-Za-z]*"
    expected = Counter(re.findall(pattern, reference.casefold()))
    if not expected:
        return 1.0
    actual = Counter(re.findall(pattern, hypothesis.casefold()))
    return sum((expected & actual).values()) / sum(expected.values())


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def stat_block(values: Iterable[float]) -> dict[str, float | None]:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {key: None for key in ("mean", "p50", "p95", "p99", "min", "max")}
    return {
        "mean": round(sum(clean) / len(clean), 3),
        "p50": round(percentile(clean, 0.50), 3),
        "p95": round(percentile(clean, 0.95), 3),
        "p99": round(percentile(clean, 0.99), 3),
        "min": round(min(clean), 3),
        "max": round(max(clean), 3),
    }


def mean_field(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) not in (None, "")]
    return round(sum(values) / len(values), 6) if values else None


def translation_segments(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()] or [text]


def synchronize(device: str) -> None:
    if device == "cuda":
        torch.cuda.synchronize()


def release_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def normalize_language(value: str) -> str:
    normalized = value.strip().casefold().replace("_latn", "")
    aliases = {"vie": "vi", "vietnamese": "vi", "eng": "en", "english": "en"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in LANG:
        raise ValueError(f"Unsupported language code: {value!r}; expected vi or en")
    return normalized


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_rows(audio_dir: Path, manifest_path: Path, cases_path: Path) -> list[dict[str, Any]]:
    if not audio_dir.is_dir():
        raise FileNotFoundError(f"Audio directory does not exist: {audio_dir}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Audio manifest does not exist: {manifest_path}")
    if not cases_path.is_file():
        raise FileNotFoundError(f"Reference cases do not exist: {cases_path}")

    manifest = read_csv(manifest_path)
    cases = read_csv(cases_path)
    by_id = {row.get("case_id", ""): row for row in cases}
    if not manifest:
        raise ValueError("Audio manifest is empty")
    if len(by_id) != len(cases):
        raise ValueError("Reference cases contain missing or duplicate case_id values")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_files: set[Path] = set()
    for position, audio_row in enumerate(manifest, 1):
        case_id = audio_row.get("case_id", "").strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Missing or duplicate case_id in manifest row {position}: {case_id!r}")
        case = by_id.get(case_id)
        if case is None:
            raise ValueError(f"No reference case found for {case_id}")
        wav_name = (audio_row.get("wav_file") or audio_row.get("file") or "").strip()
        wav_path = (audio_dir / wav_name).resolve()
        try:
            wav_path.relative_to(audio_dir.resolve())
        except ValueError as error:
            raise ValueError(f"Audio path escapes the selected directory: {wav_name}") from error
        if not wav_name or not wav_path.is_file():
            raise FileNotFoundError(f"Missing WAV for {case_id}: {wav_path}")
        if wav_path in seen_files:
            raise ValueError(f"The same WAV is assigned more than once: {wav_path}")

        source_lang = normalize_language(case.get("source_lang") or audio_row.get("source_lang", ""))
        target_lang = normalize_language(case.get("target_lang") or ("en" if source_lang == "vi" else "vi"))
        source_text = (case.get("source") or audio_row.get("source_text") or "").strip()
        reference = (case.get("reference") or audio_row.get("reference_translation") or "").strip()
        if not source_text or not reference:
            raise ValueError(f"Case {case_id} needs both source and reference translation text")
        manifest_text = (audio_row.get("source_text") or "").strip()
        if manifest_text and normalize_text(manifest_text) != normalize_text(source_text):
            raise ValueError(f"Source text differs between manifest and cases for {case_id}")

        rows.append({
            "order": int(audio_row.get("order") or position),
            "case_id": case_id,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "domain": (case.get("domain") or audio_row.get("domain") or "unspecified").strip(),
            "length_group": (
                case.get("length_group") or audio_row.get("length_group") or "unspecified"
            ).strip(),
            "wav_file": wav_name,
            "wav_path": str(wav_path),
            "source_text": source_text,
            "reference_translation": reference,
            "audio_preprocessed": (
                audio_row.get("whisper_preprocessing") == "production_preprocess_audio_numpy"
            ),
            "status": "pending",
            "error": "",
        })
        seen_ids.add(case_id)
        seen_files.add(wav_path)

    rows.sort(key=lambda row: (int(row["order"]), str(row["case_id"])))
    return rows


def select_rows(rows: list[dict[str, Any]], limit: int, limit_per_language: int) -> list[dict[str, Any]]:
    if limit and limit_per_language:
        raise ValueError("Use either --limit or --limit-per-language, not both")
    if limit_per_language:
        selected = []
        for language in ("vi", "en"):
            selected.extend([row for row in rows if row["source_lang"] == language][:limit_per_language])
        selected.sort(key=lambda row: int(row["order"]))
        return selected
    return rows[:limit] if limit else rows


def load_audio(row: dict[str, Any]) -> tuple[np.ndarray, float]:
    from app.utils.audio_utils import preprocess_audio_numpy

    sample_rate, audio = scipy.io.wavfile.read(row["wav_path"])
    if np.issubdtype(audio.dtype, np.integer):
        maximum = max(abs(np.iinfo(audio.dtype).min), np.iinfo(audio.dtype).max)
        audio = audio.astype(np.float32) / float(maximum)
    else:
        audio = audio.astype(np.float32)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sample_rate != SAMPLE_RATE:
        divisor = math.gcd(int(sample_rate), SAMPLE_RATE)
        audio = scipy.signal.resample_poly(
            audio, SAMPLE_RATE // divisor, int(sample_rate) // divisor
        ).astype(np.float32)
    if not row.get("audio_preprocessed"):
        audio = preprocess_audio_numpy(audio)
    if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
        raise ValueError(f"Invalid audio samples in {row['wav_file']}")
    return audio, len(audio) / SAMPLE_RATE


def update_stt_metrics(row: dict[str, Any], transcript: str, duration: float, latency_ms: float) -> None:
    expected_words = normalize_tokens(row["source_text"])
    actual_words = normalize_tokens(transcript)
    expected_chars = list(normalize_text(row["source_text"]).replace(" ", ""))
    actual_chars = list(normalize_text(transcript).replace(" ", ""))
    word_errors = edit_distance(expected_words, actual_words)
    char_errors = edit_distance(expected_chars, actual_chars)
    wer = word_errors / max(1, len(expected_words))
    cer = char_errors / max(1, len(expected_chars))
    row.update({
        "audio_duration_seconds": round(duration, 6),
        "transcript": transcript,
        "stt_ms": round(latency_ms, 3),
        "stt_rtf": round(latency_ms / 1000 / max(duration, 0.001), 6),
        "word_errors": word_errors,
        "reference_words": len(expected_words),
        "wer": round(wer, 6),
        "stt_word_accuracy": round(max(0.0, 1 - wer), 6),
        "char_errors": char_errors,
        "reference_chars": len(expected_chars),
        "cer": round(cer, 6),
        "stt_char_accuracy": round(max(0.0, 1 - cer), 6),
        "stt_exact_match": int(normalize_text(row["source_text"]) == normalize_text(transcript)),
    })


def update_translation_metrics(row: dict[str, Any], prefix: str, hypothesis: str, latency_ms: float) -> None:
    reference = row["reference_translation"]
    row.update({
        f"{prefix}_translation": hypothesis,
        f"{prefix}_translation_ms": round(latency_ms, 3),
        f"{prefix}_token_f1": round(token_f1(reference, hypothesis), 6),
        f"{prefix}_chrf": round(chrf(reference, hypothesis), 6),
        f"{prefix}_exact_match": int(normalize_text(reference) == normalize_text(hypothesis)),
        f"{prefix}_numeric_fidelity": round(numeric_fidelity(reference, hypothesis), 6),
    })


def save_checkpoint(path: Path, metadata: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    atomic_write_json(path, {"metadata": metadata, "rows": rows})


def mark_error(row: dict[str, Any], stage: str, error: Exception) -> None:
    row["status"] = f"error_{stage}"
    row["error"] = f"{type(error).__name__}: {error}"


def run_stt(
    rows: list[dict[str, Any]], device: str, checkpoint: Path,
    metadata: dict[str, Any], checkpoint_every: int,
) -> None:
    from app.ai.torch_whisper_adapter import TorchWhisperModel
    from app.ai.model_manager import model_manager
    from app.services.semantic_service import correct_text_semantics
    from app.services.whisper_service import transcribe_audio

    pending = [row for row in rows if not row.get("transcript") and not str(row.get("status", "")).startswith("error")]
    if not pending:
        print("WHISPER: checkpoint already complete", flush=True)
        return
    print(f"WHISPER: loading {WHISPER_MODEL_ID} on {device}", flush=True)
    started = time.perf_counter()
    recognizer = TorchWhisperModel(
        WHISPER_MODEL_ID, device, revision=WHISPER_REVISION, local_files_only=True
    )
    model_manager.whisper_model = recognizer
    metadata["model_load_seconds"]["whisper"] = round(time.perf_counter() - started, 3)
    recognizer.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language="vi", beam_size=1)
    synchronize(device)
    for completed, row in enumerate(pending, 1):
        try:
            audio, duration = load_audio(row)
            synchronize(device)
            inference_started = time.perf_counter()
            result = transcribe_audio(
                audio,
                language=row["source_lang"],
                beam_size=1,
                preprocess=False,
                use_vad=False,
            )
            synchronize(device)
            latency_ms = (time.perf_counter() - inference_started) * 1000
            transcript = correct_text_semantics(str(result.get("text") or ""), "")
            update_stt_metrics(row, transcript, duration, latency_ms)
            row["status"] = "stt_complete"
        except Exception as error:  # Continue so the report identifies every bad file.
            mark_error(row, "stt", error)
        if completed % checkpoint_every == 0 or completed == len(pending):
            print(f"WHISPER: {completed}/{len(pending)}", flush=True)
            save_checkpoint(checkpoint, metadata, rows)
    model_manager.whisper_model = None
    del recognizer
    release_cuda()


def translate_one(
    tokenizer: Any, model: Any, text: str, source_lang: str, target_lang: str, device: str,
) -> tuple[str, float]:
    from app.services.translation_service import _translate_nllb

    synchronize(device)
    started = time.perf_counter()
    hypothesis = _translate_nllb(text, LANG[source_lang], LANG[target_lang])
    synchronize(device)
    latency_ms = (time.perf_counter() - started) * 1000
    return hypothesis, latency_ms


def run_translation(
    rows: list[dict[str, Any]], device: str, checkpoint: Path,
    metadata: dict[str, Any], checkpoint_every: int,
) -> None:
    from app.ai.model_manager import model_manager

    pending = [
        row for row in rows
        if row.get("transcript") and not row.get("pipeline_translation")
        and not str(row.get("status", "")).startswith("error")
    ]
    if not pending:
        print("NLLB: checkpoint already complete", flush=True)
        return
    print(f"NLLB: loading {NLLB_MODEL_ID} on {device}", flush=True)
    dtype = torch.float16 if device == "cuda" else torch.float32
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        NLLB_MODEL_ID, revision=NLLB_REVISION, local_files_only=True
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        NLLB_MODEL_ID, revision=NLLB_REVISION, dtype=dtype, local_files_only=True
    ).to(device).eval()
    model.generation_config.max_length = None
    model_manager.nllb_tokenizer = tokenizer
    model_manager.nllb_model = model
    metadata["model_load_seconds"]["nllb"] = round(time.perf_counter() - started, 3)
    translate_one(tokenizer, model, pending[0]["source_text"], pending[0]["source_lang"], pending[0]["target_lang"], device)
    for completed, row in enumerate(pending, 1):
        try:
            direct_text, direct_ms = translate_one(
                tokenizer, model, row["source_text"], row["source_lang"], row["target_lang"], device
            )
            pipeline_text, pipeline_ms = translate_one(
                tokenizer, model, row["transcript"], row["source_lang"], row["target_lang"], device
            )
            update_translation_metrics(row, "direct", direct_text, direct_ms)
            update_translation_metrics(row, "pipeline", pipeline_text, pipeline_ms)
            row["translation_quality_delta_f1"] = round(
                row["pipeline_token_f1"] - row["direct_token_f1"], 6
            )
            row["translation_quality_delta_chrf"] = round(
                row["pipeline_chrf"] - row["direct_chrf"], 6
            )
            row["status"] = "translation_complete"
        except Exception as error:
            mark_error(row, "translation", error)
        if completed % checkpoint_every == 0 or completed == len(pending):
            print(f"NLLB: {completed}/{len(pending)}", flush=True)
            save_checkpoint(checkpoint, metadata, rows)
    model_manager.nllb_model = None
    model_manager.nllb_tokenizer = None
    del model, tokenizer
    release_cuda()


def resolve_tts_device(requested: str, primary_device: str) -> str:
    if requested != "auto":
        return requested
    if primary_device == "cuda" and torch.cuda.is_available():
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        return "cuda" if total_gb >= 8 else "cpu"
    return "cpu"


def run_tts(
    rows: list[dict[str, Any]], tts_device: str, checkpoint: Path,
    metadata: dict[str, Any], checkpoint_every: int, save_tts: bool, output_dir: Path,
) -> None:
    output_audio_dir = output_dir / "tts_output"
    if save_tts:
        output_audio_dir.mkdir(parents=True, exist_ok=True)
    for target_lang in ("vi", "en"):
        pending = [
            row for row in rows
            if row.get("pipeline_translation") and row["target_lang"] == target_lang
            and row.get("tts_ms") in (None, "")
            and not str(row.get("status", "")).startswith("error")
        ]
        if not pending:
            continue
        model_id, revision = TTS_MODELS[target_lang]
        print(f"VITS {target_lang}: loading {model_id} on {tts_device}", flush=True)
        started = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True)
        model = VitsModel.from_pretrained(
            model_id, revision=revision, dtype=torch.float32, local_files_only=True
        ).to(tts_device).eval()
        metadata["model_load_seconds"][f"vits_{target_lang}"] = round(
            time.perf_counter() - started, 3
        )
        warm = tokenizer("Sẵn sàng." if target_lang == "vi" else "Ready.", return_tensors="pt").to(tts_device)
        with torch.inference_mode():
            model(**warm, speaking_rate=0.85, noise_scale=0.667, noise_scale_dp=0.8).waveform
        synchronize(tts_device)
        for completed, row in enumerate(pending, 1):
            try:
                torch.manual_seed(TTS_SEED_BASE + int(row["order"]))
                inputs = tokenizer(row["pipeline_translation"], return_tensors="pt").to(tts_device)
                synchronize(tts_device)
                inference_started = time.perf_counter()
                with torch.inference_mode():
                    waveform = model(
                        **inputs, speaking_rate=0.85, noise_scale=0.667, noise_scale_dp=0.8
                    ).waveform.squeeze().float().cpu().numpy()
                synchronize(tts_device)
                latency_ms = (time.perf_counter() - inference_started) * 1000
                if waveform.ndim != 1 or not len(waveform) or not np.isfinite(waveform).all():
                    raise ValueError("VITS returned invalid samples")
                sample_rate = int(model.config.sampling_rate)
                duration = len(waveform) / sample_rate
                output_name = ""
                if save_tts:
                    output_name = f"{int(row['order']):03d}_{row['case_id']}_{target_lang}.wav"
                    scipy.io.wavfile.write(output_audio_dir / output_name, sample_rate, waveform)
                row.update({
                    "tts_ms": round(latency_ms, 3),
                    "tts_output_duration_seconds": round(duration, 6),
                    "tts_rtf": round(latency_ms / 1000 / max(duration, 0.001), 6),
                    "tts_sample_rate_hz": sample_rate,
                    "tts_samples": len(waveform),
                    "tts_output_file": f"tts_output/{output_name}" if output_name else "",
                    "pipeline_ms": round(row["stt_ms"] + row["pipeline_translation_ms"] + latency_ms, 3),
                    "pipeline_rtf": round(
                        (row["stt_ms"] + row["pipeline_translation_ms"] + latency_ms)
                        / 1000 / max(float(row["audio_duration_seconds"]), 0.001), 6
                    ),
                    "status": "complete",
                })
            except Exception as error:
                mark_error(row, "tts", error)
            if completed % checkpoint_every == 0 or completed == len(pending):
                print(f"VITS {target_lang}: {completed}/{len(pending)}", flush=True)
                save_checkpoint(checkpoint, metadata, rows)
        del model, tokenizer
        release_cuda()


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [row for row in rows if row.get("status") == "complete"]
    total_word_errors = sum(int(row["word_errors"]) for row in complete)
    total_words = sum(int(row["reference_words"]) for row in complete)
    total_char_errors = sum(int(row["char_errors"]) for row in complete)
    total_chars = sum(int(row["reference_chars"]) for row in complete)
    return {
        "case_count": len(rows),
        "complete_count": len(complete),
        "error_count": len(rows) - len(complete),
        "stt": {
            "latency_ms": stat_block(row.get("stt_ms") for row in complete),
            "corpus_wer": round(total_word_errors / max(1, total_words), 6),
            "word_accuracy": round(max(0.0, 1 - total_word_errors / max(1, total_words)), 6),
            "corpus_cer": round(total_char_errors / max(1, total_chars), 6),
            "char_accuracy": round(max(0.0, 1 - total_char_errors / max(1, total_chars)), 6),
            "exact_match_rate": mean_field(complete, "stt_exact_match"),
            "mean_rtf": mean_field(complete, "stt_rtf"),
        },
        "translation_direct": {
            "latency_ms": stat_block(row.get("direct_translation_ms") for row in complete),
            "mean_token_f1": mean_field(complete, "direct_token_f1"),
            "mean_chrf": mean_field(complete, "direct_chrf"),
            "exact_match_rate": mean_field(complete, "direct_exact_match"),
            "mean_numeric_fidelity": mean_field(complete, "direct_numeric_fidelity"),
        },
        "translation_pipeline": {
            "latency_ms": stat_block(row.get("pipeline_translation_ms") for row in complete),
            "mean_token_f1": mean_field(complete, "pipeline_token_f1"),
            "mean_chrf": mean_field(complete, "pipeline_chrf"),
            "exact_match_rate": mean_field(complete, "pipeline_exact_match"),
            "mean_numeric_fidelity": mean_field(complete, "pipeline_numeric_fidelity"),
            "mean_f1_delta_vs_direct": mean_field(complete, "translation_quality_delta_f1"),
            "mean_chrf_delta_vs_direct": mean_field(complete, "translation_quality_delta_chrf"),
        },
        "tts": {
            "latency_ms": stat_block(row.get("tts_ms") for row in complete),
            "mean_rtf": mean_field(complete, "tts_rtf"),
            "mean_output_duration_seconds": mean_field(complete, "tts_output_duration_seconds"),
        },
        "pipeline": {
            "latency_ms": stat_block(row.get("pipeline_ms") for row in complete),
            "mean_rtf": mean_field(complete, "pipeline_rtf"),
            "sequential_turns_per_second": (
                round(1000 / (sum(float(row["pipeline_ms"]) for row in complete) / len(complete)), 6)
                if complete else None
            ),
        },
    }


def load_baseline(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    translation = payload.get("translation_summary") or {}
    speech = payload.get("speech_summary") or {}
    if not translation or not speech:
        return None
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path),
        "sha256": sha256_file(path),
        "case_count": payload.get("metadata", {}).get("case_count"),
        "metrics": {
            "stt_mean_ms": speech.get("latency_ms", {}).get("mean"),
            "stt_p95_ms": speech.get("latency_ms", {}).get("p95"),
            "stt_word_accuracy": speech.get("corpus_word_accuracy_capped"),
            "stt_char_accuracy": speech.get("corpus_char_accuracy_capped"),
            "translation_mean_ms": translation.get("latency_ms", {}).get("mean"),
            "translation_p95_ms": translation.get("latency_ms", {}).get("p95"),
            "translation_token_f1": translation.get("mean_token_f1"),
            "translation_chrf": translation.get("mean_chrf"),
            "translation_numeric_fidelity": translation.get("mean_numeric_fidelity"),
        },
    }


def build_comparison(overall: dict[str, Any], baseline: dict[str, Any] | None) -> list[dict[str, Any]]:
    current = {
        "stt_mean_ms": overall["stt"]["latency_ms"]["mean"],
        "stt_p95_ms": overall["stt"]["latency_ms"]["p95"],
        "stt_word_accuracy": overall["stt"]["word_accuracy"],
        "stt_char_accuracy": overall["stt"]["char_accuracy"],
        "translation_mean_ms": overall["translation_direct"]["latency_ms"]["mean"],
        "translation_p95_ms": overall["translation_direct"]["latency_ms"]["p95"],
        "translation_token_f1": overall["translation_direct"]["mean_token_f1"],
        "translation_chrf": overall["translation_direct"]["mean_chrf"],
        "translation_numeric_fidelity": overall["translation_direct"]["mean_numeric_fidelity"],
    }
    labels = {
        "stt_mean_ms": ("STT trung bình", "ms", "lower"),
        "stt_p95_ms": ("STT P95", "ms", "lower"),
        "stt_word_accuracy": ("Độ chính xác từ STT", "%", "higher"),
        "stt_char_accuracy": ("Độ chính xác ký tự STT", "%", "higher"),
        "translation_mean_ms": ("Dịch trực tiếp trung bình", "ms", "lower"),
        "translation_p95_ms": ("Dịch trực tiếp P95", "ms", "lower"),
        "translation_token_f1": ("F1 dịch trực tiếp", "%", "higher"),
        "translation_chrf": ("chrF dịch trực tiếp", "%", "higher"),
        "translation_numeric_fidelity": ("Giữ số/mã", "%", "higher"),
    }
    baseline_metrics = baseline["metrics"] if baseline else {}
    result = []
    for key, value in current.items():
        old = baseline_metrics.get(key)
        result.append({
            "metric_key": key,
            "metric": labels[key][0],
            "unit": labels[key][1],
            "preferred": labels[key][2],
            "current": value,
            "baseline": old,
            "delta": round(value - old, 6) if value is not None and old is not None else None,
        })
    return result


def build_report_payload(
    args: argparse.Namespace, rows: list[dict[str, Any]], metadata: dict[str, Any],
) -> dict[str, Any]:
    overall = summarize_group(rows)
    directions = {}
    for language in ("vi", "en"):
        group = [row for row in rows if row["source_lang"] == language]
        if group:
            directions[f"{language}->{group[0]['target_lang']}"] = summarize_group(group)
    domains = {
        domain: summarize_group([row for row in rows if row["domain"] == domain])
        for domain in sorted({str(row["domain"]) for row in rows})
    }
    length_groups = {
        length_group: summarize_group(
            [row for row in rows if row["length_group"] == length_group]
        )
        for length_group in ("short", "medium", "long")
        if any(row["length_group"] == length_group for row in rows)
    }
    baseline = load_baseline(args.baseline)
    return {
        "metadata": metadata | {
            "completed_at": local_now(),
            "status": "complete" if overall["error_count"] == 0 else "complete_with_errors",
        },
        "overall": overall,
        "by_direction": directions,
        "by_domain": domains,
        "by_length_group": length_groups,
        "historical_baseline": baseline,
        "comparison": build_comparison(overall, baseline),
        "rows": rows,
        "limitations": [
            "Điểm F1, chrF, WER và CER là chỉ số tự động; không thay thế đánh giá mù của chuyên gia ngôn ngữ.",
            "Pipeline chạy theo ba pha để phù hợp GPU 6 GB; tổng latency là tổng thời gian inference ấm của ba mô hình, không gồm thời gian nạp mô hình.",
            "VITS được đánh giá về tốc độ và tính hợp lệ của waveform; báo cáo không tự động chấm độ tự nhiên bằng người nghe.",
            "So sánh lịch sử chỉ có ý nghĩa khi dùng cùng bộ câu, cấu hình mô hình và điều kiện phần cứng.",
        ],
    }


def run_xlsx_builder(payload_path: Path, output_path: Path) -> None:
    command = [
        "node", str(ROOT / "scripts" / "build_audio_pipeline_report.mjs"),
        "--input", str(payload_path), "--output", str(output_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run WAV files through Whisper, NLLB and VITS and export CSV/JSON/XLSX reports."
    )
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--tts-device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--limit-per-language", type=int, default=0)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--save-tts", action="store_true")
    parser.add_argument("--no-xlsx", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for value, label in (
        (args.limit, "--limit"),
        (args.limit_per_language, "--limit-per-language"),
        (args.checkpoint_every, "--checkpoint-every"),
    ):
        if value < 0 or (label == "--checkpoint-every" and value == 0):
            raise ValueError(f"{label} must be positive")

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    tts_device = resolve_tts_device(args.tts_device, device)

    rows = select_rows(
        load_rows(args.audio_dir.resolve(), args.manifest.resolve(), args.cases.resolve()),
        args.limit,
        args.limit_per_language,
    )
    if not rows:
        raise ValueError("No cases selected")

    print(f"INPUT VALID: {len(rows)} audio files", flush=True)
    if args.validate_only:
        print(json.dumps({
            "case_count": len(rows),
            "languages": dict(Counter(row["source_lang"] for row in rows)),
            "domains": dict(Counter(row["domain"] for row in rows)),
            "manifest_sha256": sha256_file(args.manifest),
            "cases_sha256": sha256_file(args.cases),
        }, ensure_ascii=False, indent=2))
        return

    if args.output_dir:
        output_dir = args.output_dir.resolve()
    else:
        stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        output_dir = ROOT / "outputs" / f"audio_pipeline_test_{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.json"
    payload_path = output_dir / "ket_qua_day_du.json"
    csv_path = output_dir / "chi_tiet_ket_qua.csv"
    summary_path = output_dir / "tong_hop.json"
    xlsx_path = output_dir / "Bao_cao_kiem_thu_3_model.xlsx"

    input_signature = {
        "manifest_sha256": sha256_file(args.manifest),
        "cases_sha256": sha256_file(args.cases),
        "selected_case_ids": [row["case_id"] for row in rows],
        "run_config": {
            "device": device,
            "tts_device": tts_device,
            "save_tts": args.save_tts,
            "whisper_revision": WHISPER_REVISION,
            "nllb_revision": NLLB_REVISION,
            "tts_revisions": {language: revision for language, (_, revision) in TTS_MODELS.items()},
        },
    }
    metadata: dict[str, Any] = {
        "created_at": local_now(),
        "case_count": len(rows),
        "input": input_signature,
        "audio_dir": str(args.audio_dir.resolve()),
        "manifest": str(args.manifest.resolve()),
        "cases": str(args.cases.resolve()),
        "device": device,
        "tts_device": tts_device,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "models": {
            "whisper": {"id": WHISPER_MODEL_ID, "revision": WHISPER_REVISION},
            "nllb": {"id": NLLB_MODEL_ID, "revision": NLLB_REVISION},
            "vits": {
                language: {"id": model_id, "revision": revision}
                for language, (model_id, revision) in TTS_MODELS.items()
            },
        },
        "model_load_seconds": {},
    }

    if checkpoint_path.exists() and not args.overwrite:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("metadata", {}).get("input") != input_signature:
            raise RuntimeError(
                "Output directory contains a checkpoint for different inputs. "
                "Choose another --output-dir or pass --overwrite."
            )
        rows = checkpoint["rows"]
        metadata.update(checkpoint.get("metadata", {}))
        print(f"RESUME: {checkpoint_path}", flush=True)
    elif args.overwrite:
        for path in (checkpoint_path, payload_path, csv_path, summary_path, xlsx_path):
            if path.exists():
                path.unlink()

    run_stt(rows, device, checkpoint_path, metadata, args.checkpoint_every)
    run_translation(rows, device, checkpoint_path, metadata, args.checkpoint_every)
    run_tts(
        rows, tts_device, checkpoint_path, metadata, args.checkpoint_every,
        args.save_tts, output_dir,
    )

    payload = build_report_payload(args, rows, metadata)
    atomic_write_json(payload_path, payload)
    write_csv(csv_path, rows)
    atomic_write_json(summary_path, {key: value for key, value in payload.items() if key != "rows"})
    if not args.no_xlsx:
        run_xlsx_builder(payload_path, xlsx_path)

    readme = (
        "# Báo cáo kiểm thử ba mô hình\n\n"
        f"- Số ca: {len(rows)}\n"
        f"- Hoàn thành: {payload['overall']['complete_count']}\n"
        f"- Lỗi: {payload['overall']['error_count']}\n"
        "- Luồng: WAV → Whisper → NLLB → VITS.\n"
        "- `chi_tiet_ket_qua.csv`: kết quả từng tệp.\n"
        "- `tong_hop.json`: chỉ số tổng hợp và so sánh lịch sử.\n"
        "- `ket_qua_day_du.json`: dữ liệu đầy đủ để tái tạo báo cáo.\n"
        + ("- `Bao_cao_kiem_thu_3_model.xlsx`: báo cáo Excel.\n" if not args.no_xlsx else "")
    )
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({
        "status": payload["metadata"]["status"],
        "case_count": len(rows),
        "complete_count": payload["overall"]["complete_count"],
        "error_count": payload["overall"]["error_count"],
        "output_dir": str(output_dir),
        "xlsx": str(xlsx_path) if not args.no_xlsx else None,
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

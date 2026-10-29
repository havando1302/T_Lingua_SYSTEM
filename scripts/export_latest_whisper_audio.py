"""Reproduce the synthetic Whisper inputs from the latest 500-case test setup."""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.io.wavfile
import scipy.signal
import torch
from transformers import AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DEFAULT_DATASET = (
    ROOT / "outputs" / "fresh500_optimized_20261014" / "fresh_500_test_cases.csv"
)
DEFAULT_SPEECH_RESULTS = (
    ROOT / "outputs" / "fresh500_evaluation_20261014" / "fresh_500_speech_results.csv"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "am_thanh"

TTS_MODELS = {
    "vi": ("facebook/mms-tts-vie", "b58928d033932a49aa8e3d6cf11625b25fe928d2"),
    "en": ("facebook/mms-tts-eng", "c71de0fe7204c83f1c10820a7d696d0b450048ba"),
}
SEED_BASE = 20261014
WHISPER_SAMPLE_RATE = 16_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_wav(path: Path, sample_rate: int, audio: np.ndarray) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        scipy.io.wavfile.write(stream, sample_rate, audio)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 500:
        raise RuntimeError(f"Expected exactly 500 cases, found {len(rows)} in {path}")
    case_ids = [row["case_id"] for row in rows]
    if len(set(case_ids)) != 500 or len({row["source"] for row in rows}) != 500:
        raise RuntimeError("The source corpus must contain 500 unique IDs and sentences")
    if set(row["source_lang"] for row in rows) != {"vi", "en"}:
        raise RuntimeError("The source corpus must contain both vi and en cases")
    return rows


def load_expected_durations(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 500:
        raise RuntimeError(f"Expected 500 speech results, found {len(rows)} in {path}")
    return {row["case_id"]: float(row["duration_seconds"]) for row in rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--speech-results", type=Path, default=DEFAULT_SPEECH_RESULTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    from app.utils.audio_utils import preprocess_audio_numpy

    cases = load_cases(args.dataset)
    expected_durations = load_expected_durations(args.speech_results)
    args.output.mkdir(parents=True, exist_ok=True)
    existing_wavs = list(args.output.glob("*.wav"))
    if existing_wavs and not args.overwrite:
        raise RuntimeError(
            f"Output contains {len(existing_wavs)} WAV files; pass --overwrite to regenerate"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    manifest_rows: list[dict[str, object]] = []
    duration_mismatches: list[dict[str, object]] = []
    index_by_id = {case["case_id"]: index for index, case in enumerate(cases)}

    for language in ("vi", "en"):
        model_id, revision = TTS_MODELS[language]
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=revision, local_files_only=True
        )
        model = VitsModel.from_pretrained(
            model_id,
            revision=revision,
            dtype=torch.float32,
            local_files_only=True,
        ).to(device).eval()

        language_cases = [case for case in cases if case["source_lang"] == language]
        for language_index, case in enumerate(language_cases, 1):
            corpus_index = index_by_id[case["case_id"]]
            torch.manual_seed(SEED_BASE + corpus_index)
            inputs = tokenizer(case["source"], return_tensors="pt").to(device)
            with torch.inference_mode():
                waveform = model(**inputs).waveform.squeeze().float().cpu().numpy()

            source_rate = int(model.config.sampling_rate)
            if source_rate != WHISPER_SAMPLE_RATE:
                divisor = math.gcd(source_rate, WHISPER_SAMPLE_RATE)
                waveform = scipy.signal.resample_poly(
                    waveform,
                    WHISPER_SAMPLE_RATE // divisor,
                    source_rate // divisor,
                ).astype(np.float32)

            # This is the exact final transformation in run_fresh_500_evaluation.py
            # immediately before recognizer.transcribe(audio, ...).
            whisper_audio = preprocess_audio_numpy(waveform)
            if whisper_audio.ndim != 1 or not np.isfinite(whisper_audio).all():
                raise RuntimeError(f"Invalid audio generated for {case['case_id']}")

            output_name = f"{corpus_index + 1:03d}_{case['case_id']}.wav"
            output_path = args.output / output_name
            atomic_write_wav(output_path, WHISPER_SAMPLE_RATE, whisper_audio)

            duration = len(whisper_audio) / WHISPER_SAMPLE_RATE
            expected_duration = expected_durations[case["case_id"]]
            rounded_duration = round(duration, 3)
            duration_matches = rounded_duration == expected_duration
            if not duration_matches:
                duration_mismatches.append(
                    {
                        "case_id": case["case_id"],
                        "exported": rounded_duration,
                        "test_result": expected_duration,
                    }
                )

            manifest_rows.append(
                {
                    "order": corpus_index + 1,
                    "case_id": case["case_id"],
                    "source_lang": language,
                    "domain": case["domain"],
                    "source_text": case["source"],
                    "wav_file": output_name,
                    "sample_rate_hz": WHISPER_SAMPLE_RATE,
                    "channels": 1,
                    "sample_format": "IEEE_FLOAT_32_LE",
                    "sample_count": len(whisper_audio),
                    "duration_seconds": f"{duration:.6f}",
                    "test_duration_seconds": f"{expected_duration:.3f}",
                    "duration_matches_test": str(duration_matches).lower(),
                    "sha256": sha256_file(output_path),
                    "tts_model": model_id,
                    "tts_revision": revision,
                    "seed": SEED_BASE + corpus_index,
                    "whisper_preprocessing": "production_preprocess_audio_numpy",
                }
            )
            completed = len(manifest_rows)
            if language_index % 25 == 0:
                print(f"{language}: {language_index}/{len(language_cases)}; total {completed}/500", flush=True)

        del model, tokenizer
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    manifest_rows.sort(key=lambda row: int(row["order"]))
    manifest_path = args.output / "manifest_500_am_thanh.csv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    wav_paths = sorted(args.output.glob("*.wav"))
    if len(wav_paths) != 500:
        raise RuntimeError(f"Expected 500 WAV files after export, found {len(wav_paths)}")

    total_samples = sum(int(row["sample_count"]) for row in manifest_rows)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Deterministic reproduction of post-preprocessing audio inputs for the latest 500-case Whisper evaluation",
        "source_dataset": str(args.dataset.relative_to(ROOT)).replace("\\", "/"),
        "source_dataset_sha256": sha256_file(args.dataset),
        "source_speech_results": str(args.speech_results.relative_to(ROOT)).replace("\\", "/"),
        "source_speech_results_sha256": sha256_file(args.speech_results),
        "audio_file_count": len(wav_paths),
        "manifest_row_count": len(manifest_rows),
        "languages": {
            language: sum(row["source_lang"] == language for row in manifest_rows)
            for language in ("vi", "en")
        },
        "sample_rate_hz": WHISPER_SAMPLE_RATE,
        "channels": 1,
        "sample_format": "IEEE_FLOAT_32_LE",
        "total_duration_seconds": round(total_samples / WHISPER_SAMPLE_RATE, 3),
        "duration_match_count": 500 - len(duration_mismatches),
        "duration_mismatches": duration_mismatches,
        "reproduction_note_vi": (
            "475 tệp khớp thời lượng đã ghi trong kết quả test. 25 ca đầu có thời lượng "
            "khác vì bản test lịch sử không lưu WAV/trạng thái ngẫu nhiên ban đầu; các tệp "
            "thay thế vẫn dùng đúng câu, mô hình, revision, resampling 16 kHz và tiền xử lý Whisper."
        ),
        "device_used_for_reproduction": device,
        "seed_base": SEED_BASE,
        "models": {
            language: {"id": model_id, "revision": revision}
            for language, (model_id, revision) in TTS_MODELS.items()
        },
    }
    summary_path = args.output / "kiem_chung_500_am_thanh.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = "# 500 âm thanh đầu vào Whisper\n\n"
    readme += "Thư mục chứa đúng 500 tệp WAV được tái tạo từ bộ 500 câu kiểm thử mới nhất. "
    readme += "Mỗi tệp là tín hiệu mono 16 kHz, float32 sau bước `preprocess_audio_numpy`, "
    readme += "tức đúng dạng mảng âm thanh được truyền vào `recognizer.transcribe`.\n\n"
    readme += "- `manifest_500_am_thanh.csv`: đối chiếu thứ tự, mã ca, câu nguồn, tệp WAV, thời lượng và SHA-256.\n"
    readme += "- `kiem_chung_500_am_thanh.json`: tổng hợp nguồn dữ liệu, phiên bản mô hình và kiểm tra đầy đủ.\n"
    readme += "- 001–250: tiếng Việt; 251–500: tiếng Anh.\n"
    readme += f"- SHA-256 bộ câu nguồn: `{summary['source_dataset_sha256']}`.\n"
    readme += "- 475/500 tệp khớp thời lượng lịch sử; 25 ca đầu là bản tái tạo cùng cấu hình nhưng trạng thái ngẫu nhiên WAV gốc không còn được lưu.\n"
    (args.output / "README.md").write_text(readme, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

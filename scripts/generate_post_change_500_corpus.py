"""Create a new balanced 500-sentence corpus and its Whisper input WAV files.

The corpus is deliberately disjoint from prior CSV corpora under ``outputs``.
It contains short, medium, and long utterances in both Vietnamese and English.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import scipy.io.wavfile
import scipy.signal
import torch
from transformers import AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DEFAULT_OUTPUT = ROOT / "outputs" / "post_change_500_20261025"
SAMPLE_RATE = 16_000
SEED_BASE = 20261025
TTS_MODELS = {
    "vi": ("facebook/mms-tts-vie", "b58928d033932a49aa8e3d6cf11625b25fe928d2"),
    "en": ("facebook/mms-tts-eng", "c71de0fe7204c83f1c10820a7d696d0b450048ba"),
}

ORDINAL_VI = [
    "nhất", "hai", "ba", "tư", "năm", "sáu", "bảy", "tám", "chín", "mười",
    "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm", "mười sáu",
    "mười bảy", "mười tám", "mười chín", "hai mươi", "hai mươi mốt",
    "hai mươi hai", "hai mươi ba", "hai mươi tư", "hai mươi lăm",
]
ORDINAL_EN = [
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
    "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth",
    "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth",
    "twentieth", "twenty-first", "twenty-second", "twenty-third", "twenty-fourth",
    "twenty-fifth",
]

NAMES = [
    "An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Khánh", "Linh", "Minh", "Phương",
    "Quang", "Trang", "Vy", "Nam", "Sơn", "Lan", "Mai", "Huy", "Ngọc", "Tuấn",
    "Alex", "Bella", "Chris", "Diana", "Ethan",
]
PLACES = [
    "Hà Nội", "Đà Nẵng", "Huế", "Cần Thơ", "Hải Phòng", "Nha Trang", "Đà Lạt",
    "Vũng Tàu", "Quy Nhơn", "Hội An", "Biên Hòa", "Bến Tre", "Ninh Bình",
    "Quảng Ngãi", "Phú Yên", "Đồng Hới", "Long An", "Bắc Ninh", "Hạ Long",
    "Buôn Ma Thuột", "Sa Đéc", "Tuy Hòa", "Tam Kỳ", "Rạch Giá", "Sóc Trăng",
]
PLACES_EN = [
    "Hanoi", "Da Nang", "Hue", "Can Tho", "Hai Phong", "Nha Trang", "Da Lat",
    "Vung Tau", "Quy Nhon", "Hoi An", "Bien Hoa", "Ben Tre", "Ninh Binh",
    "Quang Ngai", "Phu Yen", "Dong Hoi", "Long An", "Bac Ninh", "Ha Long",
    "Buon Ma Thuot", "Sa Dec", "Tuy Hoa", "Tam Ky", "Rach Gia", "Soc Trang",
]
DAYS_VI = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


VI_EN_TEMPLATES = [
    ("operations", "Ca kiểm tra thứ {ord_vi} kết thúc đúng giờ.",
     "The {ord_en} inspection shift ended on time."),
    ("retail", "Cửa hàng bán {number} chiếc đèn trong buổi sáng.",
     "The store sold {number} lamps in the morning."),
    ("logistics", "Xe tải thứ {ord_vi} đã đến kho an toàn.",
     "The {ord_en} truck arrived safely at the warehouse."),
    ("education", "Lớp học thứ {ord_vi} hoàn thành bài đọc hôm nay.",
     "The {ord_en} class completed today's reading."),
    ("healthcare", "Phòng khám tiếp nhận {number} lịch hẹn mới.",
     "The clinic received {number} new appointments."),
    ("tourism", "Đoàn khách thứ {ord_vi} rời bảo tàng lúc {clock}.",
     "The {ord_en} tour group left the museum at {clock}."),
    ("manufacturing", "Tổ máy thứ {ord_vi} hoàn tất kiểm tra đầu ca.",
     "The {ord_en} machine unit completed its start-of-shift inspection."),
    ("agriculture", "Lô rau thứ {ord_vi} đã được đóng gói.",
     "The {ord_en} vegetable batch was packed."),
    ("environment", "Trạm phía bắc ghi nhận {number} milimét mưa.",
     "The northern station recorded {number} millimeters of rain."),
    ("software", "Bản thử nghiệm thứ {ord_vi} khởi động không lỗi.",
     "The {ord_en} test build started without errors."),
]

EN_VI_TEMPLATES = [
    ("customer_service", "The {ord_en} support request was resolved today.",
     "Yêu cầu hỗ trợ thứ {ord_vi} đã được giải quyết hôm nay."),
    ("finance", "The cashier counted {number} receipts before lunch.",
     "Thu ngân đã đếm {number} biên lai trước bữa trưa."),
    ("security", "The {ord_en} patrol completed the eastern route.",
     "Ca tuần tra thứ {ord_vi} đã hoàn thành tuyến phía đông."),
    ("transport", "The morning bus reached the terminal at {clock}.",
     "Xe buýt buổi sáng đến bến lúc {clock}."),
    ("research", "The laboratory reviewed {number} samples this morning.",
     "Phòng thí nghiệm đã xem xét {number} mẫu vào sáng nay."),
    ("hospitality", "The {ord_en} guest room is ready for check-in.",
     "Phòng khách thứ {ord_vi} đã sẵn sàng để nhận phòng."),
    ("energy", "The solar array produced {number} kilowatt-hours today.",
     "Dàn pin mặt trời tạo ra {number} kilowatt giờ hôm nay."),
    ("construction", "The {ord_en} bridge section passed inspection.",
     "Đoạn cầu thứ {ord_vi} đã vượt qua kiểm tra."),
    ("culture", "The gallery welcomed {number} visitors before noon.",
     "Phòng trưng bày đón {number} khách trước buổi trưa."),
    ("food_service", "The kitchen prepared the {ord_en} meal order.",
     "Nhà bếp đã chuẩn bị đơn món ăn thứ {ord_vi}."),
]


def normalize_text(text: str) -> str:
    return " ".join("".join(char.casefold() if char.isalnum() else " " for char in text).split())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_prior_sentences(excluded_root: Path) -> set[str]:
    prior: set[str] = set()
    outputs = ROOT / "outputs"
    for path in outputs.rglob("*.csv"):
        try:
            path.resolve().relative_to(excluded_root.resolve())
            continue
        except ValueError:
            pass
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    for key in ("source", "source_text", "Văn Bản Gốc (Ground Truth)"):
                        value = (row.get(key) or "").strip()
                        if value:
                            prior.add(normalize_text(value))
        except (OSError, UnicodeError, csv.Error):
            continue
    return prior


def context_pair(language: str, length_group: str, values: dict[str, Any]) -> tuple[str, str]:
    if length_group == "short":
        return "", ""
    if language == "vi" and length_group == "medium":
        return (
            " {name} ghi lại kết quả tại {place_vi} vào {day_vi}.",
            " {name} recorded the result in {place_en} on {day_en}.",
        )
    if language == "en" and length_group == "medium":
        return (
            " {name} recorded the result in {place_en} on {day_en}.",
            " {name} ghi lại kết quả tại {place_vi} vào {day_vi}.",
        )
    if language == "vi":
        return (
            " Sau khi kiểm tra lần thứ {ord_vi}, {name} ghi lại kết quả tại {place_vi} "
            "vào {day_vi} và gửi bản tóm tắt cho nhóm trực ca trước khi bàn giao công việc.",
            " After the {ord_en} review, {name} recorded the result in {place_en} on "
            "{day_en} and sent a summary to the duty team before handing over the work.",
        )
    return (
        " After the {ord_en} review, {name} recorded the result in {place_en} on "
        "{day_en} and sent a summary to the duty team before handing over the work.",
        " Sau khi kiểm tra lần thứ {ord_vi}, {name} ghi lại kết quả tại {place_vi} "
        "vào {day_vi} và gửi bản tóm tắt cho nhóm trực ca trước khi bàn giao công việc.",
    )


def build_direction(
    templates: list[tuple[str, str, str]], source_lang: str, target_lang: str, prefix: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(250):
        template_index = index % len(templates)
        variant = index // len(templates)
        length_group = "short" if index < 50 else "medium" if index < 175 else "long"
        place_index = (index * 7 + template_index) % len(PLACES)
        values: dict[str, Any] = {
            "ord_vi": ORDINAL_VI[variant],
            "ord_en": ORDINAL_EN[variant],
            "number": 11 + variant,
            "clock": f"{7 + variant // 4:02d}:{(variant % 4) * 15:02d}",
            "name": NAMES[(index * 3 + template_index) % len(NAMES)],
            "place_vi": PLACES[place_index],
            "place_en": PLACES_EN[place_index],
            "day_vi": DAYS_VI[(variant + template_index) % len(DAYS_VI)],
            "day_en": DAYS_EN[(variant + template_index) % len(DAYS_EN)],
        }
        domain, source_template, reference_template = templates[template_index]
        source_suffix, reference_suffix = context_pair(source_lang, length_group, values)
        source = (source_template + source_suffix).format(**values)
        reference = (reference_template + reference_suffix).format(**values)
        rows.append({
            "case_id": f"{prefix}_{index + 1:03d}",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "domain": domain,
            "length_group": length_group,
            "source": source,
            "reference": reference,
            "provenance": "post_change_disjoint_templates_20261025",
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def atomic_write_wav(path: Path, audio: np.ndarray) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        scipy.io.wavfile.write(stream, SAMPLE_RATE, audio.astype(np.float32))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def generate_audio(cases: list[dict[str, str]], audio_dir: Path, overwrite: bool) -> list[dict[str, Any]]:
    from app.utils.audio_utils import preprocess_audio_numpy

    audio_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    index_by_id = {case["case_id"]: index for index, case in enumerate(cases)}
    manifest: list[dict[str, Any]] = []
    for language in ("vi", "en"):
        model_id, revision = TTS_MODELS[language]
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=revision, local_files_only=True
        )
        model = VitsModel.from_pretrained(
            model_id, revision=revision, dtype=torch.float32, local_files_only=True
        ).to(device).eval()
        language_cases = [case for case in cases if case["source_lang"] == language]
        for completed, case in enumerate(language_cases, 1):
            corpus_index = index_by_id[case["case_id"]]
            output_name = f"{corpus_index + 1:03d}_{case['case_id']}.wav"
            output_path = audio_dir / output_name
            if output_path.exists() and not overwrite:
                sample_rate, waveform = scipy.io.wavfile.read(output_path)
                if sample_rate != SAMPLE_RATE or waveform.ndim != 1:
                    raise RuntimeError(f"Invalid existing audio: {output_path}")
                whisper_audio = waveform.astype(np.float32)
            else:
                torch.manual_seed(SEED_BASE + corpus_index)
                inputs = tokenizer(case["source"], return_tensors="pt").to(device)
                with torch.inference_mode():
                    waveform = model(
                        **inputs, speaking_rate=0.85, noise_scale=0.667, noise_scale_dp=0.8
                    ).waveform.squeeze().float().cpu().numpy()
                source_rate = int(model.config.sampling_rate)
                if source_rate != SAMPLE_RATE:
                    divisor = math.gcd(source_rate, SAMPLE_RATE)
                    waveform = scipy.signal.resample_poly(
                        waveform, SAMPLE_RATE // divisor, source_rate // divisor
                    ).astype(np.float32)
                whisper_audio = preprocess_audio_numpy(waveform)
                if whisper_audio.ndim != 1 or not np.isfinite(whisper_audio).all():
                    raise RuntimeError(f"Invalid audio generated for {case['case_id']}")
                atomic_write_wav(output_path, whisper_audio)
            manifest.append({
                "order": corpus_index + 1,
                "case_id": case["case_id"],
                "source_lang": language,
                "domain": case["domain"],
                "length_group": case["length_group"],
                "source_text": case["source"],
                "reference_translation": case["reference"],
                "wav_file": output_name,
                "sample_rate_hz": SAMPLE_RATE,
                "channels": 1,
                "sample_format": "IEEE_FLOAT_32_LE",
                "sample_count": len(whisper_audio),
                "duration_seconds": f"{len(whisper_audio) / SAMPLE_RATE:.6f}",
                "sha256": sha256_file(output_path),
                "tts_model": model_id,
                "tts_revision": revision,
                "seed": SEED_BASE + corpus_index,
                "whisper_preprocessing": "production_preprocess_audio_numpy",
            })
            if completed % 25 == 0:
                print(f"AUDIO {language}: {completed}/{len(language_cases)}", flush=True)
        del model, tokenizer
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
    manifest.sort(key=lambda row: int(row["order"]))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    audio_dir = output_dir / "audio_input"
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_path = output_dir / "cases_500_new.csv"
    manifest_path = audio_dir / "manifest_500_audio.csv"

    prior_sentences = collect_prior_sentences(output_dir)
    cases = (
        build_direction(VI_EN_TEMPLATES, "vi", "en", "POST_VI_EN")
        + build_direction(EN_VI_TEMPLATES, "en", "vi", "POST_EN_VI")
    )
    normalized = [normalize_text(case["source"]) for case in cases]
    duplicates_with_prior = sorted(set(normalized) & prior_sentences)
    if len(cases) != 500 or len(set(normalized)) != 500:
        raise RuntimeError("New corpus must contain exactly 500 unique source sentences")
    if duplicates_with_prior:
        raise RuntimeError(f"New corpus overlaps prior data in {len(duplicates_with_prior)} sentences")

    write_csv(cases_path, cases)
    manifest = generate_audio(cases, audio_dir, args.overwrite)
    write_csv(manifest_path, manifest)

    wav_files = list(audio_dir.glob("*.wav"))
    if len(wav_files) != 500 or len(manifest) != 500:
        raise RuntimeError(f"Expected 500 WAV files and manifest rows, found {len(wav_files)} and {len(manifest)}")
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "audio_file_count": len(wav_files),
        "languages": dict(Counter(case["source_lang"] for case in cases)),
        "length_groups": dict(Counter(case["length_group"] for case in cases)),
        "domains": dict(Counter(case["domain"] for case in cases)),
        "prior_normalized_sentence_count_checked": len(prior_sentences),
        "exact_overlap_with_prior": len(duplicates_with_prior),
        "unique_source_sentence_count": len(set(normalized)),
        "cases_sha256": sha256_file(cases_path),
        "manifest_sha256": sha256_file(manifest_path),
        "total_audio_duration_seconds": round(sum(float(row["duration_seconds"]) for row in manifest), 3),
        "sample_rate_hz": SAMPLE_RATE,
        "audio_directory": str(audio_dir),
        "cases_file": str(cases_path),
        "manifest_file": str(manifest_path),
    }
    (output_dir / "corpus_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        "# Kiểm thử 500 câu mới sau tối ưu\n\n"
        "- 500 câu không trùng chính xác với các câu nguồn CSV đã có trong `outputs`.\n"
        "- 250 câu Việt sang Anh và 250 câu Anh sang Việt.\n"
        "- 100 câu ngắn, 250 câu trung bình và 150 câu dài.\n"
        "- `audio_input` chứa 500 WAV mono 16 kHz sau tiền xử lý Whisper.\n"
        "- `cases_500_new.csv` chứa câu nguồn và bản dịch tham chiếu.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

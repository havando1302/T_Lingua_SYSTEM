"""Run a fresh 500-case translation and synthetic-speech recognition evaluation.

The corpus is intentionally separate from benchmark_v2.  Every case is evaluated
for translation latency/quality and for ASR latency/accuracy against its source.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import platform
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.signal
import torch
import transformers
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, VitsModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "outputs" / "fresh500_optimized_20261014"
DATASET = OUT / "fresh_500_test_cases.csv"
RESULTS = OUT / "fresh_500_results.json"
TRANSLATION_CSV = OUT / "fresh_500_translation_results.csv"
SPEECH_CSV = OUT / "fresh_500_speech_results.csv"

NLLB_MODEL_ID = "facebook/nllb-200-distilled-1.3B"
NLLB_REVISION = "7be3e24664b38ce1cac29b8aeed6911aa0cf0576"
WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"
WHISPER_REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"
TTS_MODELS = {
    "vi": ("facebook/mms-tts-vie", "b58928d033932a49aa8e3d6cf11625b25fe928d2"),
    "en": ("facebook/mms-tts-eng", "c71de0fe7204c83f1c10820a7d696d0b450048ba"),
}
LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


VI_EN = [
    ("retail", "Cửa hàng {shop} giảm giá {percent_vi} phần trăm cho {product_vi} trong tuần này.",
     "The {shop} store is offering a {percent_en} percent discount on {product_en} this week."),
    ("agriculture", "Trang trại tại {place} thu hoạch {quantity_vi} tấn {crop_vi} vào sáng nay.",
     "The farm in {place} harvested {quantity_en} tons of {crop_en} this morning."),
    ("energy", "Tòa nhà {building} tiêu thụ {quantity_vi} kilowatt giờ điện trong ca đêm.",
     "Building {building} consumed {quantity_en} kilowatt-hours of electricity during the night shift."),
    ("environment", "Nhóm khảo sát ghi nhận nhiệt độ {temperature_vi} độ C tại trạm {station}.",
     "The survey team recorded a temperature of {temperature_en} degrees Celsius at station {station}."),
    ("sports", "Đội {team} ghi {score_vi} bàn trong trận giao hữu chiều nay.",
     "Team {team} scored {score_en} goals in this afternoon's friendly match."),
    ("culture", "Bảo tàng {museum} mở cửa từ {start_time_vi} đến {end_time_vi} vào cuối tuần.",
     "The {museum} museum is open from {start_time_en} to {end_time_en} on weekends."),
    ("hospitality", "Khách sạn {hotel} xác nhận phòng {room} cho {guests_vi} khách vào ngày mai.",
     "The {hotel} hotel confirmed room {room} for {guests_en} guests tomorrow."),
    ("manufacturing", "Dây chuyền {line} hoàn thành {quantity_vi} linh kiện mà không phát hiện lỗi.",
     "Production line {line} completed {quantity_en} components without detecting any defects."),
    ("public_service", "Trung tâm {district} tiếp nhận hồ sơ {code} lúc {start_time_vi} sáng.",
     "The {district} center received application {code} at {start_time_en} in the morning."),
    ("research", "Phòng thí nghiệm {lab} lưu mẫu {code} ở nhiệt độ {temperature_vi} độ C.",
     "Laboratory {lab} stored sample {code} at {temperature_en} degrees Celsius."),
]

EN_VI = [
    ("customer_experience", "Customer {name} rated the delivery service {rating_en} out of five this morning.",
     "Khách hàng {name} chấm dịch vụ giao hàng {rating_vi} trên năm điểm vào sáng nay."),
    ("logistics", "Container {code} cleared customs at {start_time_en} and moved to warehouse {warehouse}.",
     "Công-ten-nơ {code} đã thông quan lúc {start_time_vi} và được chuyển đến kho {warehouse}."),
    ("software", "Release {version} reduced memory usage by {percent_en} percent during the trial.",
     "Bản phát hành {version} đã giảm mức sử dụng bộ nhớ {percent_vi} phần trăm trong đợt thử nghiệm."),
    ("security", "Camera {code} detected {quantity_en} failed badge scans near gate {gate}.",
     "Camera {code} phát hiện {quantity_vi} lần quét thẻ không thành công gần cổng {gate}."),
    ("transport", "Bus route {route} added {quantity_en} morning trips between {city_a} and {city_b}.",
     "Tuyến xe buýt {route} đã bổ sung {quantity_vi} chuyến buổi sáng giữa {city_a} và {city_b}."),
    ("science", "The sensor in laboratory {lab} reported a humidity level of {percent_en} percent.",
     "Cảm biến trong phòng thí nghiệm {lab} báo độ ẩm ở mức {percent_vi} phần trăm."),
    ("food_service", "The kitchen prepared {quantity_en} vegetarian meals for the evening event.",
     "Nhà bếp đã chuẩn bị {quantity_vi} suất ăn chay cho sự kiện buổi tối."),
    ("construction", "Crew {team} inspected bridge section {code} before the rain started.",
     "Đội {team} đã kiểm tra đoạn cầu {code} trước khi trời bắt đầu mưa."),
    ("education", "Class {room} completed chapter {chapter_en} and submitted the quiz online.",
     "Lớp {room} đã hoàn thành chương {chapter_vi} và nộp bài kiểm tra trực tuyến."),
    ("tourism", "Guide {name} welcomed {guests_en} visitors at the north entrance of {museum} museum.",
     "Hướng dẫn viên {name} đón {guests_vi} du khách tại lối vào phía bắc của bảo tàng {museum}."),
]

VALUES = {
    "shop": ["An Nhiên", "Bình Minh", "Cầu Vồng", "Đại Phát", "Hoa Sen"],
    "percent_vi": ["mười", "mười hai", "mười lăm", "mười tám", "hai mươi lăm"],
    "percent_en": ["ten", "twelve", "fifteen", "eighteen", "twenty-five"],
    "product_vi": ["đèn bàn", "bình giữ nhiệt", "tai nghe", "ba lô", "máy lọc khí"],
    "product_en": ["desk lamps", "vacuum flasks", "headphones", "backpacks", "air purifiers"],
    "place": ["Ninh Bình", "Lâm Đồng", "Quảng Nam", "Phú Yên", "Đồng Tháp"],
    "quantity_vi": ["bốn", "sáu", "chín", "mười ba", "hai mươi hai"],
    "quantity_en": ["four", "six", "nine", "thirteen", "twenty-two"],
    "crop_vi": ["cà phê", "thanh long", "ngô", "chè", "xoài"],
    "crop_en": ["coffee", "dragon fruit", "corn", "tea", "mangoes"],
    "building": ["F1", "G2", "H3", "K4", "M5"],
    "temperature_vi": ["mười tám", "hai mươi", "hai mươi ba", "hai mươi sáu", "ba mươi mốt"],
    "temperature_en": ["eighteen", "twenty", "twenty-three", "twenty-six", "thirty-one"],
    "station": ["S1", "S2", "S3", "S4", "S5"],
    "team": ["Sao Mai", "Hải Âu", "Lam Sơn", "Mê Kông", "Trường Sơn"],
    "score_vi": ["một", "hai", "ba", "bốn", "năm"],
    "score_en": ["one", "two", "three", "four", "five"],
    "museum": ["Gốm", "Lụa", "Biển", "Nhiếp ảnh", "Khoa học"],
    "start_time_vi": ["bảy giờ", "tám giờ", "chín giờ", "mười giờ", "mười một giờ"],
    "start_time_en": ["seven", "eight", "nine", "ten", "eleven"],
    "end_time_vi": ["mười sáu giờ", "mười bảy giờ", "mười tám giờ", "mười chín giờ", "hai mươi giờ"],
    "end_time_en": ["sixteen", "seventeen", "eighteen", "nineteen", "twenty"],
    "hotel": ["Ánh Dương", "Mây Trắng", "Sông Xanh", "Hoàng Gia", "Vườn Cau"],
    "room": ["A12", "B23", "C34", "D45", "E56"],
    "guests_vi": ["hai", "ba", "bốn", "năm", "sáu"],
    "guests_en": ["two", "three", "four", "five", "six"],
    "line": ["L1", "L2", "L3", "L4", "L5"],
    "district": ["An Phú", "Bến Nghé", "Cẩm Lệ", "Đông Hải", "Gia Thụy"],
    "code": ["RX11", "QZ24", "MT37", "PK48", "VN59"],
    "lab": ["Alpha", "Beta", "Gamma", "Delta", "Omega"],
    "name": ["Alex", "Bella", "Chris", "Diana", "Ethan"],
    "rating_en": ["one", "two", "three", "four", "five"],
    "rating_vi": ["một", "hai", "ba", "bốn", "năm"],
    "warehouse": ["W1", "W2", "W3", "W4", "W5"],
    "version": ["3.1", "3.2", "4.0", "4.1", "5.0"],
    "gate": ["A", "B", "C", "D", "E"],
    "route": ["R11", "R22", "R33", "R44", "R55"],
    "city_a": ["Hanoi", "Hue", "Da Nang", "Can Tho", "Vung Tau"],
    "city_b": ["Hai Phong", "Hoi An", "Quy Nhon", "Ben Tre", "Bien Hoa"],
    "chapter_en": ["six", "seven", "eight", "nine", "ten"],
    "chapter_vi": ["sáu", "bảy", "tám", "chín", "mười"],
}


def variables(index: int) -> dict[str, str]:
    # Stable named offsets keep corpus variants unchanged when bilingual
    # companion fields are added to VALUES later.
    single_offsets = {
        "shop": 0, "place": 4, "building": 8, "station": 10,
        "team": 11, "museum": 13, "hotel": 16, "room": 17,
        "line": 19, "district": 20, "code": 21, "lab": 22,
        "name": 23, "warehouse": 25, "version": 26, "gate": 27,
        "route": 28, "city_a": 29, "city_b": 30,
    }
    values = {
        key: VALUES[key][(index * (offset * 2 + 1) + offset) % len(VALUES[key])]
        for key, offset in single_offsets.items()
    }
    # Keep bilingual lexical pairs aligned.
    product = index % len(VALUES["product_vi"])
    crop = (index * 3) % len(VALUES["crop_vi"])
    values.update(product_vi=VALUES["product_vi"][product], product_en=VALUES["product_en"][product])
    values.update(crop_vi=VALUES["crop_vi"][crop], crop_en=VALUES["crop_en"][crop])
    # Preserve the original source-side variant selection while aligning the
    # translated number words in the paired language.
    pair_offsets = {
        "percent": 1, "quantity": 5, "temperature": 9, "score": 12,
        "start_time": 14, "end_time": 15, "guests": 18,
        "rating": 24, "chapter": 31,
    }
    for stem, offset in pair_offsets.items():
        pair_value = (index * (offset * 2 + 1) + offset) % 5
        values[f"{stem}_vi"] = VALUES[f"{stem}_vi"][pair_value]
        values[f"{stem}_en"] = VALUES[f"{stem}_en"][pair_value]
    return values


def build_direction(templates: list[tuple[str, str, str]], source_lang: str,
                    target_lang: str, prefix: str) -> list[dict]:
    day_vi = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu"]
    day_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    period_vi = ["đầu giờ sáng", "cuối buổi sáng", "đầu giờ chiều", "cuối buổi chiều", "buổi tối"]
    period_en = ["early in the morning", "late in the morning", "early in the afternoon",
                 "late in the afternoon", "in the evening"]
    rows = []
    for index in range(250):
        domain, source_template, reference_template = templates[index % len(templates)]
        values = variables(index)
        source = source_template.format(**values)
        reference = reference_template.format(**values)
        variant = index // len(templates)
        day_index, period_index = divmod(variant, 5)
        if source_lang == "vi":
            source += f" Người kiểm tra xác nhận vào {period_vi[period_index]} {day_vi[day_index]}."
            reference += f" The inspector confirmed it {period_en[period_index]} on {day_en[day_index]}."
        else:
            source += f" The record was reviewed {period_en[period_index]} on {day_en[day_index]}."
            reference += f" Hồ sơ được rà soát vào {period_vi[period_index]} {day_vi[day_index]}."
        rows.append({
            "case_id": f"{prefix}_{index + 1:03d}",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "domain": domain,
            "source": source,
            "reference": reference,
            "provenance": "fresh_deterministic_templates_20261014",
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_translation_checkpoint(cases: list[dict]) -> list[dict]:
    if not TRANSLATION_CSV.exists():
        return []
    with TRANSLATION_CSV.open(encoding="utf-8-sig", newline="") as stream:
        stored = {row["case_id"]: row for row in csv.DictReader(stream)}
    results = []
    for case in cases:
        row = stored.get(case["case_id"])
        if row is None or row.get("source") != case["source"]:
            break
        row.update(case)
        row["latency_ms"] = float(row["latency_ms"])
        row["token_f1"] = round(token_f1(case["reference"], row["hypothesis"]), 6)
        row["chrf"] = round(chrf(case["reference"], row["hypothesis"]), 6)
        row["exact_match"] = int(normalize_text(case["reference"]) == normalize_text(row["hypothesis"]))
        row["numeric_fidelity"] = round(numeric_fidelity(case["reference"], row["hypothesis"]), 6)
        results.append(row)
    return results


def load_speech_checkpoint(cases: list[dict]) -> list[dict]:
    if not SPEECH_CSV.exists():
        return []
    with SPEECH_CSV.open(encoding="utf-8-sig", newline="") as stream:
        stored = {row["case_id"]: row for row in csv.DictReader(stream)}
    results = []
    for case in cases:
        row = stored.get(case["case_id"])
        if row is None or row.get("reference") != case["source"]:
            break
        for key in ("duration_seconds", "latency_ms", "realtime_factor", "wer", "cer"):
            row[key] = float(row[key])
        for key in ("word_errors", "reference_words", "char_errors", "reference_chars", "exact_match"):
            row[key] = int(row[key])
        results.append(row)
    return results


def create_dataset() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = (build_direction(VI_EN, "vi", "en", "FRESH_VI_EN") +
            build_direction(EN_VI, "en", "vi", "FRESH_EN_VI"))
    if len(rows) != 500 or len({row["source"] for row in rows}) != 500:
        raise RuntimeError("Fresh corpus must contain exactly 500 unique source sentences")
    write_csv(DATASET, rows)
    old_dataset = ROOT / "docs" / "progress_2026-09-24" / "evidence" / "benchmark_v2_500.csv"
    old_sources = set()
    if old_dataset.exists():
        with old_dataset.open(encoding="utf-8-sig", newline="") as stream:
            old_sources = {row["source"] for row in csv.DictReader(stream)}
    overlap = len(old_sources & {row["source"] for row in rows})
    if overlap:
        raise RuntimeError(f"Fresh corpus unexpectedly overlaps old corpus in {overlap} sources")
    return rows


def load_dataset() -> list[dict]:
    if not DATASET.exists():
        return create_dataset()
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 500:
        raise RuntimeError(f"Expected 500 cases, found {len(rows)}")
    return rows


def normalize_text(text: str) -> str:
    return " ".join("".join(char.casefold() if char.isalnum() else " " for char in text).split())


def normalize_tokens(text: str) -> list[str]:
    return normalize_text(text).split()


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row, expected in enumerate(reference, 1):
        current = [row]
        for column, actual in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (expected != actual)))
        previous = current
    return previous[-1]


def token_f1(reference: str, hypothesis: str) -> float:
    expected, actual = Counter(normalize_tokens(reference)), Counter(normalize_tokens(hypothesis))
    overlap = sum((expected & actual).values())
    precision = overlap / max(1, sum(actual.values()))
    recall = overlap / max(1, sum(expected.values()))
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def chrf(reference: str, hypothesis: str) -> float:
    reference, hypothesis = normalize_text(reference), normalize_text(hypothesis)
    scores = []
    for size in range(1, 7):
        expected = Counter(reference[i:i + size] for i in range(max(0, len(reference) - size + 1)))
        actual = Counter(hypothesis[i:i + size] for i in range(max(0, len(hypothesis) - size + 1)))
        overlap = sum((expected & actual).values())
        precision = overlap / max(1, sum(actual.values()))
        recall = overlap / max(1, sum(expected.values()))
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return statistics.mean(scores)


def numeric_fidelity(reference: str, hypothesis: str) -> float:
    expected = Counter(re.findall(r"[A-Za-z]*\d+(?:[.:-]\d+)*[A-Za-z]*", reference.casefold()))
    if not expected:
        return 1.0
    actual = Counter(re.findall(r"[A-Za-z]*\d+(?:[.:-]\d+)*[A-Za-z]*", hypothesis.casefold()))
    return sum((expected & actual).values()) / sum(expected.values())


def percentile(values: list[float], ratio: float) -> float:
    values = sorted(values)
    position = (len(values) - 1) * ratio
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def stat_block(values: list[float]) -> dict:
    return {name: round(value, 3) for name, value in {
        "mean": statistics.mean(values), "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95), "p99": percentile(values, 0.99),
        "min": min(values), "max": max(values),
    }.items()}


def save_results(payload: dict) -> None:
    RESULTS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def translation_segments(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()] or [text]


def run_translation(cases: list[dict], payload: dict, device: str) -> None:
    dtype = torch.float16 if device == "cuda" else torch.float32
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        NLLB_MODEL_ID, revision=NLLB_REVISION, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        NLLB_MODEL_ID, revision=NLLB_REVISION, dtype=dtype,
        local_files_only=True).to(device).eval()
    model.generation_config.max_length = None
    payload["environment"]["nllb_load_seconds"] = round(time.perf_counter() - started, 3)
    tokenizer.src_lang = LANG[cases[0]["source_lang"]]
    warm = tokenizer(translation_segments(cases[0]["source"]), return_tensors="pt", padding=True,
                     truncation=True).to(device)
    if device == "cuda":
        torch.cuda.synchronize()
    cold_started = time.perf_counter()
    with torch.inference_mode():
        model.generate(**warm, forced_bos_token_id=tokenizer.convert_tokens_to_ids(
            LANG[cases[0]["target_lang"]]), max_length=None, max_new_tokens=64, num_beams=1)
    if device == "cuda":
        torch.cuda.synchronize()
    payload["environment"]["translation_cold_start_ms"] = round(
        (time.perf_counter() - cold_started) * 1000, 3)

    results = load_translation_checkpoint(cases)
    if results:
        print(f"TRANSLATION RESUME {len(results)}/500", flush=True)
    for index, case in enumerate(cases[len(results):], len(results) + 1):
        tokenizer.src_lang = LANG[case["source_lang"]]
        segments = translation_segments(case["source"])
        encoded = tokenizer(segments, return_tensors="pt", padding=True, truncation=True).to(device)
        source_tokens = int(encoded.attention_mask.sum(dim=1).max().item())
        token_budget = min(128, max(24, int(source_tokens * 1.6) + 12))
        if device == "cuda":
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG[case["target_lang"]]),
                max_length=None, max_new_tokens=token_budget, num_beams=1)
        if device == "cuda":
            torch.cuda.synchronize()
        latency = (time.perf_counter() - started) * 1000
        hypothesis = " ".join(
            part.lstrip("- ").strip()
            for part in tokenizer.batch_decode(generated, skip_special_tokens=True)
            if part.strip()
        )
        results.append(case | {
            "hypothesis": hypothesis,
            "latency_ms": round(latency, 3),
            "token_f1": round(token_f1(case["reference"], hypothesis), 6),
            "chrf": round(chrf(case["reference"], hypothesis), 6),
            "exact_match": int(normalize_text(case["reference"]) == normalize_text(hypothesis)),
            "numeric_fidelity": round(numeric_fidelity(case["reference"], hypothesis), 6),
        })
        if index % 25 == 0:
            print(f"TRANSLATION {index}/500", flush=True)
            write_csv(TRANSLATION_CSV, results)
    payload["translation_rows"] = results
    latencies = [row["latency_ms"] for row in results]
    payload["translation_summary"] = {
        "latency_ms": stat_block(latencies),
        "mean_token_f1": round(statistics.mean(row["token_f1"] for row in results), 6),
        "mean_chrf": round(statistics.mean(row["chrf"] for row in results), 6),
        "exact_match_rate": round(statistics.mean(row["exact_match"] for row in results), 6),
        "mean_numeric_fidelity": round(statistics.mean(row["numeric_fidelity"] for row in results), 6),
    }
    write_csv(TRANSLATION_CSV, results)
    save_results(payload)
    del model, tokenizer
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()


def run_speech(cases: list[dict], payload: dict, device: str) -> None:
    from app.ai.torch_whisper_adapter import TorchWhisperModel
    from app.utils.audio_utils import preprocess_audio_numpy

    recognizer = TorchWhisperModel(
        WHISPER_MODEL_ID, device, revision=WHISPER_REVISION, local_files_only=True)
    # Prewarm once; exclude first-use kernel setup from steady-state latency.
    recognizer.transcribe(np.zeros(16000, dtype=np.float32), language="vi", beam_size=1)
    if device == "cuda":
        torch.cuda.synchronize()

    results = load_speech_checkpoint(cases)
    if results:
        print(f"SPEECH RESUME {len(results)}/500", flush=True)
    for language in ("vi", "en"):
        model_id, revision = TTS_MODELS[language]
        # TTS is only the deterministic audio fixture generator here, not the
        # system component under timing.  FP32 avoids VITS spline instability
        # on longer sentences while Whisper remains on production FP16.
        dtype = torch.float32
        tts_tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=revision, local_files_only=True)
        tts_model = VitsModel.from_pretrained(
            model_id, revision=revision, dtype=dtype,
            local_files_only=True).to(device).eval()
        language_cases = [case for case in cases if case["source_lang"] == language]
        for local_index, case in enumerate(language_cases, 1):
            if any(row["case_id"] == case["case_id"] for row in results):
                continue
            torch.manual_seed(20261014 + cases.index(case))
            inputs = tts_tokenizer(case["source"], return_tensors="pt").to(device)
            with torch.inference_mode():
                waveform = tts_model(**inputs).waveform.squeeze().float().cpu().numpy()
            source_rate = int(tts_model.config.sampling_rate)
            if source_rate != 16000:
                divisor = math.gcd(source_rate, 16000)
                waveform = scipy.signal.resample_poly(
                    waveform, 16000 // divisor, source_rate // divisor).astype(np.float32)
            duration = len(waveform) / 16000
            audio = preprocess_audio_numpy(waveform)
            if device == "cuda":
                torch.cuda.synchronize()
            started = time.perf_counter()
            segments, _ = recognizer.transcribe(audio, language=language, beam_size=1)
            if device == "cuda":
                torch.cuda.synchronize()
            latency = (time.perf_counter() - started) * 1000
            hypothesis = " ".join(segment.text for segment in segments).strip()
            expected_words, actual_words = normalize_tokens(case["source"]), normalize_tokens(hypothesis)
            expected_chars, actual_chars = list(normalize_text(case["source"]).replace(" ", "")), list(
                normalize_text(hypothesis).replace(" ", ""))
            word_errors = edit_distance(expected_words, actual_words)
            char_errors = edit_distance(expected_chars, actual_chars)
            results.append({
                "case_id": case["case_id"], "source_lang": language,
                "domain": case["domain"], "reference": case["source"],
                "hypothesis": hypothesis, "duration_seconds": round(duration, 3),
                "latency_ms": round(latency, 3),
                "realtime_factor": round(latency / 1000 / max(duration, 0.001), 6),
                "word_errors": word_errors, "reference_words": len(expected_words),
                "wer": round(word_errors / max(1, len(expected_words)), 6),
                "char_errors": char_errors, "reference_chars": len(expected_chars),
                "cer": round(char_errors / max(1, len(expected_chars)), 6),
                "exact_match": int(normalize_text(case["source"]) == normalize_text(hypothesis)),
                "audio_condition": "clean_synthetic_vits",
            })
            overall_index = len(results)
            if overall_index % 25 == 0:
                print(f"SPEECH {overall_index}/500", flush=True)
                write_csv(SPEECH_CSV, results)
        del tts_model, tts_tokenizer
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
    payload["speech_rows"] = results
    latencies = [row["latency_ms"] for row in results]
    total_word_errors = sum(row["word_errors"] for row in results)
    total_words = sum(row["reference_words"] for row in results)
    total_char_errors = sum(row["char_errors"] for row in results)
    total_chars = sum(row["reference_chars"] for row in results)
    payload["speech_summary"] = {
        "latency_ms": stat_block(latencies),
        "corpus_wer": round(total_word_errors / max(1, total_words), 6),
        "corpus_word_accuracy_capped": round(max(0.0, 1 - total_word_errors / max(1, total_words)), 6),
        "corpus_cer": round(total_char_errors / max(1, total_chars), 6),
        "corpus_char_accuracy_capped": round(max(0.0, 1 - total_char_errors / max(1, total_chars)), 6),
        "mean_realtime_factor": round(statistics.mean(row["realtime_factor"] for row in results), 6),
        "exact_match_rate": round(statistics.mean(row["exact_match"] for row in results), 6),
    }
    write_csv(SPEECH_CSV, results)
    save_results(payload)
    del recognizer
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("all", "dataset", "translation", "speech"), default="all")
    args = parser.parse_args()
    cases = create_dataset() if args.phase in ("all", "dataset") else load_dataset()
    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    payload = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "case_count": len(cases), "dataset_sha256": digest,
            "directions": dict(Counter(f"{row['source_lang']}->{row['target_lang']}" for row in cases)),
            "domains": dict(Counter(row["domain"] for row in cases)),
            "method": "same controlled corpus for before/after comparison; optimized batched sentence translation plus clean synthetic VITS speech",
            "limitations": [
                "Translation references are controlled author-written templates and have not received independent human review.",
                "Speech audio is clean VITS synthesis, not recordings from real speakers, accents, microphones, or rooms.",
                "Automated similarity scores do not fully measure meaning, fluency, or business-critical mistranslation.",
            ],
        },
        "environment": {
            "device": device,
            "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
            "python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "translation_model": NLLB_MODEL_ID,
            "translation_revision": NLLB_REVISION, "translation_beam_size": 1,
            "translation_sentence_batch_size": 4,
            "stt_model": WHISPER_MODEL_ID, "stt_revision": WHISPER_REVISION,
            "stt_beam_size": 1, "audio_preprocessing": "production_preprocess_audio_numpy",
        },
    }
    if RESULTS.exists() and args.phase in ("translation", "speech"):
        payload.update(json.loads(RESULTS.read_text(encoding="utf-8")))
    save_results(payload)
    if args.phase == "dataset":
        print(json.dumps(payload["metadata"], ensure_ascii=False, indent=2))
        return
    if args.phase in ("all", "translation"):
        run_translation(cases, payload, device)
    if args.phase in ("all", "speech"):
        run_speech(cases, payload, device)
    payload["metadata"]["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_results(payload)
    print(json.dumps({
        "translation_summary": payload.get("translation_summary"),
        "speech_summary": payload.get("speech_summary"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

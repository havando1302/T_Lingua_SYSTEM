"""Reproducible, local-only pilot benchmark for the translation subsystem.

The benchmark intentionally uses synthetic/general-domain sentences and cached
model weights.  It records raw hypotheses so a human reviewer can audit every
metric.  It is a pilot baseline, not a claim of production quality.
"""
from __future__ import annotations

import csv
import json
import math
import platform
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "progress_2026-09-24" / "evidence"
MODEL_ID = "facebook/nllb-200-distilled-1.3B"


CASES = [
    ("VI_EN_01", "vi", "en", "Xin chào, rất vui được gặp bạn.", "Hello, nice to meet you.", []),
    ("VI_EN_02", "vi", "en", "Hôm nay thời tiết khá dễ chịu.", "The weather is quite pleasant today.", []),
    ("VI_EN_03", "vi", "en", "Cuộc họp bắt đầu lúc chín giờ sáng.", "The meeting starts at nine in the morning.", ["nine"]),
    ("VI_EN_04", "vi", "en", "Vui lòng gửi báo cáo trước thứ Sáu.", "Please send the report before Friday.", ["Friday"]),
    ("VI_EN_05", "vi", "en", "Tôi muốn đặt một vé máy bay đến Hà Nội.", "I would like to book a flight to Hanoi.", ["Hanoi"]),
    ("VI_EN_06", "vi", "en", "Giá trị hợp đồng là 1,5 tỷ đồng.", "The contract value is 1.5 billion dong.", ["1.5"]),
    ("VI_EN_07", "vi", "en", "Hệ thống đang xử lý yêu cầu của bạn.", "The system is processing your request.", ["system"]),
    ("VI_EN_08", "vi", "en", "Bạn có thể nói chậm hơn được không?", "Could you speak more slowly?", []),
    ("VI_EN_09", "vi", "en", "Tài khoản này đã bị khóa vì lý do bảo mật.", "This account has been locked for security reasons.", ["account", "security"]),
    ("VI_EN_10", "vi", "en", "Dữ liệu phải được sao lưu trước khi nâng cấp.", "The data must be backed up before the upgrade.", ["data"]),
    ("VI_EN_11", "vi", "en", "Trí tuệ nhân tạo hỗ trợ dịch hội thoại theo thời gian thực.", "Artificial intelligence supports real-time conversation translation.", ["Artificial intelligence"]),
    ("VI_EN_12", "vi", "en", "Không được chia sẻ khóa API với người không có thẩm quyền.", "Do not share the API key with unauthorized people.", ["API key"]),
    ("VI_EN_13", "vi", "en", "Nếu mất kết nối, ứng dụng sẽ tự động thử lại.", "If the connection is lost, the application will retry automatically.", []),
    ("VI_EN_14", "vi", "en", "Kết quả dịch cần giữ nguyên tên riêng và số liệu.", "The translation must preserve proper names and numbers.", []),
    ("VI_EN_15", "vi", "en", "Cảm ơn bạn đã phản hồi về chất lượng bản dịch.", "Thank you for your feedback on the translation quality.", ["translation"]),
    ("EN_VI_01", "en", "vi", "Good morning. How can I help you?", "Chào buổi sáng. Tôi có thể giúp gì cho bạn?", []),
    ("EN_VI_02", "en", "vi", "Please check your internet connection.", "Vui lòng kiểm tra kết nối Internet của bạn.", ["Internet"]),
    ("EN_VI_03", "en", "vi", "The train will arrive at 10:30.", "Tàu sẽ đến lúc 10 giờ 30.", ["10"]),
    ("EN_VI_04", "en", "vi", "Your password must contain at least twelve characters.", "Mật khẩu của bạn phải chứa ít nhất mười hai ký tự.", ["mười hai"]),
    ("EN_VI_05", "en", "vi", "The administrator revoked the old API key.", "Quản trị viên đã thu hồi khóa API cũ.", ["khóa API"]),
    ("EN_VI_06", "en", "vi", "We need a backup before running the database migration.", "Chúng ta cần sao lưu trước khi chạy quá trình di chuyển cơ sở dữ liệu.", ["sao lưu"]),
    ("EN_VI_07", "en", "vi", "Speech recognition may be less accurate in a noisy room.", "Nhận dạng giọng nói có thể kém chính xác hơn trong phòng nhiều tiếng ồn.", ["Nhận dạng giọng nói"]),
    ("EN_VI_08", "en", "vi", "Do not close the application while audio is being uploaded.", "Không đóng ứng dụng khi âm thanh đang được tải lên.", []),
    ("EN_VI_09", "en", "vi", "The response time improved after enabling the cache.", "Thời gian phản hồi được cải thiện sau khi bật bộ nhớ đệm.", ["bộ nhớ đệm"]),
    ("EN_VI_10", "en", "vi", "Could you repeat the last sentence?", "Bạn có thể lặp lại câu cuối cùng không?", []),
    ("EN_VI_11", "en", "vi", "The quality reviewer corrected the translation.", "Người đánh giá chất lượng đã sửa bản dịch.", []),
    ("EN_VI_12", "en", "vi", "Hanoi is the capital of Vietnam.", "Hà Nội là thủ đô của Việt Nam.", ["Hà Nội", "Việt Nam"]),
    ("EN_VI_13", "en", "vi", "The system supports Vietnamese and English.", "Hệ thống hỗ trợ tiếng Việt và tiếng Anh.", ["tiếng Việt", "tiếng Anh"]),
    ("EN_VI_14", "en", "vi", "An expired session must not access private history.", "Phiên đã hết hạn không được truy cập lịch sử riêng tư.", []),
    ("EN_VI_15", "en", "vi", "Please review the result before adding it to the shared dictionary.", "Vui lòng xem lại kết quả trước khi thêm vào từ điển dùng chung.", ["từ điển"]),
]


LANG = {"vi": "vie_Latn", "en": "eng_Latn"}


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def tokens(text: str) -> list[str]:
    cleaned = "".join(character.casefold() if character.isalnum() else " " for character in text)
    return cleaned.split()


def token_f1(reference: str, hypothesis: str) -> float:
    expected, actual = Counter(tokens(reference)), Counter(tokens(hypothesis))
    overlap = sum((expected & actual).values())
    if not expected or not actual or overlap == 0:
        return 0.0
    precision, recall = overlap / sum(actual.values()), overlap / sum(expected.values())
    return 2 * precision * recall / (precision + recall)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_ID, torch_dtype=dtype, local_files_only=True,
    ).to(device).eval()
    load_seconds = time.perf_counter() - load_started

    rows = []
    latencies = []
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    for case_id, source_lang, target_lang, source, reference, required_terms in CASES:
        tokenizer.src_lang = LANG[source_lang]
        encoded = tokenizer(source, return_tensors="pt").to(device)
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(LANG[target_lang]),
                max_new_tokens=128,
                num_beams=1,
                no_repeat_ngram_size=3,
            )
        if device == "cuda":
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started) * 1000
        hypothesis = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
        char_similarity = SequenceMatcher(None, reference.casefold(), hypothesis.casefold()).ratio()
        f1 = token_f1(reference, hypothesis)
        term_hits = sum(term.casefold() in hypothesis.casefold() for term in required_terms)
        rows.append({
            "case_id": case_id,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source": source,
            "reference": reference,
            "hypothesis": hypothesis,
            "latency_ms": round(latency_ms, 3),
            "char_similarity": round(char_similarity, 4),
            "token_f1": round(f1, 4),
            "required_terms": " | ".join(required_terms),
            "term_hits": term_hits,
            "term_total": len(required_terms),
        })
        latencies.append(latency_ms)

    total_terms = sum(row["term_total"] for row in rows)
    total_hits = sum(row["term_hits"] for row in rows)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "local_only_pilot_text_translation_baseline",
        "limitations": [
            "30 synthetic/general-domain sentences; not a production-representative 500-sentence test set",
            "single automatic reference per case; valid paraphrases may score lower",
            "does not measure STT WER, TTS naturalness, noisy audio, concurrency, or network latency",
            "human adequacy/fluency review remains required",
        ],
        "model_id": MODEL_ID,
        "device": device,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "load_seconds": round(load_seconds, 3),
        "cases": len(rows),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 3),
            "p50": round(percentile(latencies, 0.50), 3),
            "p95": round(percentile(latencies, 0.95), 3),
            "p99": round(percentile(latencies, 0.99), 3),
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
        },
        "quality": {
            "mean_char_similarity": round(statistics.mean(row["char_similarity"] for row in rows), 4),
            "mean_token_f1": round(statistics.mean(row["token_f1"] for row in rows), 4),
            "required_term_accuracy": round(total_hits / total_terms, 4) if total_terms else None,
            "term_hits": total_hits,
            "term_total": total_terms,
        },
        "gpu_peak_memory_mb": round(torch.cuda.max_memory_allocated() / 1024**2, 2) if device == "cuda" else None,
    }

    with (OUT_DIR / "translation_baseline_cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUT_DIR / "translation_baseline_summary.json").open("w", encoding="utf-8", newline="\n") as stream:
        json.dump({"summary": summary, "cases": rows}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Build a deterministic, versioned 500-case Vietnamese/English benchmark corpus."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"


VI_EN = [
    ("operations", "Đơn hàng {number} sẽ được giao đến {city} vào {day}.", "Order {number} will be delivered to {city} on {day}.", "{number}|{city}|{day}"),
    ("business", "Cuộc họp {topic_vi} bắt đầu lúc {time} tại phòng {room}.", "The {topic_en} meeting starts at {time} in room {room}.", "{time}|{room}"),
    ("technology", "Vui lòng sao lưu {item_vi} trước khi cập nhật hệ thống.", "Please back up {item_en} before updating the system.", "system"),
    ("security", "Tài khoản {name} bị khóa sau {number} lần đăng nhập sai.", "The account for {name} was locked after {number} failed login attempts.", "{name}|{number}"),
    ("travel", "Chuyến bay đến {city} khởi hành lúc {time} vào {day}.", "The flight to {city} departs at {time} on {day}.", "{city}|{time}"),
    ("healthcare", "Bệnh nhân cần uống {number} viên thuốc sau bữa ăn.", "The patient needs to take {number} tablets after the meal.", "{number}"),
    ("education", "Sinh viên phải nộp bài trước {time} ngày {day}.", "Students must submit the assignment before {time} on {day}.", "{time}|{day}"),
    ("finance", "Hóa đơn {number} có tổng giá trị là {amount} đô la.", "Invoice {number} has a total value of {amount} dollars.", "{number}|{amount}"),
    ("support", "Nếu mất kết nối, ứng dụng sẽ thử lại sau {number} giây.", "If the connection is lost, the application will retry after {number} seconds.", "{number}"),
    ("translation", "Bản dịch phải giữ nguyên tên {name} và mã {code}.", "The translation must preserve the name {name} and code {code}.", "{name}|{code}"),
]

EN_VI = [
    ("operations", "Package {code} will arrive in {city} on {day}.", "Kiện hàng {code} sẽ đến {city} vào {day}.", "{code}|{city}|{day}"),
    ("business", "The {topic_en} meeting starts at {time} in room {room}.", "Cuộc họp {topic_vi} bắt đầu lúc {time} tại phòng {room}.", "{time}|{room}"),
    ("technology", "Please restart the {item_en} after installing the update.", "Vui lòng khởi động lại {item_vi} sau khi cài đặt bản cập nhật.", ""),
    ("security", "User {name} must change the password within {number} days.", "Người dùng {name} phải đổi mật khẩu trong vòng {number} ngày.", "{name}|{number}"),
    ("travel", "The train to {city} leaves at {time} on {day}.", "Tàu đi {city} khởi hành lúc {time} vào {day}.", "{city}|{time}"),
    ("healthcare", "Take {number} tablets with water after breakfast.", "Uống {number} viên thuốc với nước sau bữa sáng.", "{number}"),
    ("education", "The final exam is scheduled for {time} on {day}.", "Kỳ thi cuối kỳ được tổ chức lúc {time} vào {day}.", "{time}|{day}"),
    ("finance", "Invoice {number} has an outstanding balance of {amount} dollars.", "Hóa đơn {number} còn số dư chưa thanh toán là {amount} đô la.", "{number}|{amount}"),
    ("support", "The application will reconnect automatically after {number} seconds.", "Ứng dụng sẽ tự động kết nối lại sau {number} giây.", "{number}"),
    ("translation", "Keep the name {name} and reference code {code} unchanged.", "Giữ nguyên tên {name} và mã tham chiếu {code}.", "{name}|{code}"),
]

VALUES = {
    "number": ["2", "3", "5", "8", "12", "17", "21", "25", "30", "42", "56", "64", "75"],
    "city": ["Hà Nội", "Đà Nẵng", "Huế", "Hải Phòng", "Cần Thơ", "Bangkok", "Singapore", "London", "Tokyo", "Paris"],
    "day": ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "ngày 15 tháng 9", "ngày 24 tháng 9"],
    "time": ["08:00", "09:15", "10:30", "13:45", "15:00", "17:20"],
    "room": ["A101", "B204", "C305", "D410", "E502"],
    "topic_vi": ["dự án", "kỹ thuật", "chất lượng", "bảo mật", "vận hành"],
    "topic_en": ["project", "technical", "quality", "security", "operations"],
    "item_vi": ["cơ sở dữ liệu", "máy chủ", "tệp cấu hình", "bộ nhớ đệm", "ứng dụng"],
    "item_en": ["database", "server", "configuration file", "cache", "application"],
    "name": ["An", "Bình", "Chi", "Dũng", "Hà", "Linh", "Minh", "Nam", "Trang", "Thọ"],
    "amount": ["15.50", "120", "350.75", "1,000", "2,500"],
    "code": ["AI-101", "QA-204", "TM-305", "WS-410", "API-502"],
}


def variables(index: int) -> dict[str, str]:
    result = {key: values[(index * (offset * 2 + 1) + offset) % len(values)] for offset, (key, values) in enumerate(VALUES.items())}
    # Keep paired topic/item vocabulary aligned.
    topic_index = index % len(VALUES["topic_vi"])
    item_index = (index * 3) % len(VALUES["item_vi"])
    result.update(
        topic_vi=VALUES["topic_vi"][topic_index], topic_en=VALUES["topic_en"][topic_index],
        item_vi=VALUES["item_vi"][item_index], item_en=VALUES["item_en"][item_index],
    )
    return result


def build_direction(templates: list[tuple[str, str, str, str]], source_lang: str, target_lang: str, prefix: str) -> list[dict]:
    rows = []
    for index in range(250):
        domain, source_template, reference_template, terms_template = templates[index % len(templates)]
        values = variables(index)
        source = source_template.format(**values)
        reference = reference_template.format(**values)
        terms = [term.format(**values) for term in terms_template.split("|") if term]
        rows.append({
            "case_id": f"{prefix}_{index + 1:03d}", "source_lang": source_lang,
            "target_lang": target_lang, "domain": domain,
            "length_bucket": "short" if len(source.split()) <= 10 else "medium",
            "source": source, "reference": reference,
            "required_terms": " | ".join(terms), "provenance": "deterministic_template_v2",
        })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_direction(VI_EN, "vi", "en", "V2_VI_EN") + build_direction(EN_VI, "en", "vi", "V2_EN_VI")
    dataset = OUT / "benchmark_v2_500.csv"
    with dataset.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    metadata = {
        "version": "2.0.0", "created_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows), "language_pairs": dict(Counter(f"{r['source_lang']}->{r['target_lang']}" for r in rows)),
        "domains": dict(Counter(r["domain"] for r in rows)), "source": "deterministic bilingual templates",
        "sha256": digest,
        "limitations": [
            "Synthetic template corpus; use a separately licensed natural corpus before production acceptance.",
            "References were authored as controlled template pairs and still require independent human review.",
        ],
    }
    (OUT / "benchmark_v2_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sample = [rows[index] for index in range(0, len(rows), 5)][:100]
    hypotheses = {}
    result_file = OUT / "translation_benchmark_v2_cases.csv"
    if result_file.exists():
        with result_file.open(encoding="utf-8-sig", newline="") as stream:
            hypotheses = {row["case_id"]: row["hypothesis"] for row in csv.DictReader(stream)}
    with (OUT / "human_evaluation_v2_two_reviewers.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["case_id", "reviewer_id", "source_lang", "target_lang", "source", "reference", "hypothesis", "adequacy_1_5", "fluency_1_5", "error_category", "critical_error", "correction", "reviewer_signature", "reviewed_at", "note"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for row in sample:
            for reviewer in ("REVIEWER_A", "REVIEWER_B"):
                writer.writerow({key: row.get(key, "") for key in fields} | {
                    "reviewer_id": reviewer, "hypothesis": hypotheses.get(row["case_id"], ""),
                })
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

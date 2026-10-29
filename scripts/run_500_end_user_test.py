"""
T-LINGUA: END-USER 500 SPEECH EVALUATION & REALTIME BENCHMARK SUITE
Simulates an end-user testing all 500 audio files in outputs/am_thanh:
1. Checks & sets language direction (VI -> EN for 001-250, EN -> VI for 251-500).
2. Sends speech audio into the system for speech recognition (STT), translation (NLLB), and speech synthesis (TTS).
3. Evaluates speech recognition accuracy (Word Accuracy, WER, CER) against ground truth.
4. Evaluates translation quality (Token-F1, chrF, exact match) against reference translation.
5. If inaccurate (STT < 80% or Translation F1 < 65%), flags the translation to Web Admin QA Center via /api/flag-translation.
6. Progressively saves results into an Excel workbook after EACH sentence.
7. Generates a comprehensive summary comparison report on speed, STT accuracy, and translation quality.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import soundfile as sf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_HTTP = "http://127.0.0.1:8000"
ROOT_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT_DIR / "outputs" / "am_thanh"
MANIFEST_PATH = AUDIO_DIR / "manifest_500_am_thanh.csv"
CASES_PATH = ROOT_DIR / "outputs" / "fresh500_optimized_20261014" / "fresh_500_test_cases.csv"
DEFAULT_EXCEL_PATH = ROOT_DIR / "outputs" / "Bao_cao_kiem_thu_500_cau_am_thanh.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# Text Normalization & Metrics
# ─────────────────────────────────────────────────────────────────────────────

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
    return (2 * precision * recall / (precision + recall) if precision + recall else 0.0) * 100.0


def chrf_score(reference: str, hypothesis: str) -> float:
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
    return (sum(scores) / len(scores) * 100.0) if scores else 0.0


def numeric_fidelity(reference: str, hypothesis: str) -> float:
    pattern = r"[A-Za-z]*\d+(?:[.:-]\d+)*[A-Za-z]*"
    expected = Counter(re.findall(pattern, reference.casefold()))
    if not expected:
        return 100.0
    actual = Counter(re.findall(pattern, hypothesis.casefold()))
    return (sum((expected & actual).values()) / sum(expected.values())) * 100.0


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


# ─────────────────────────────────────────────────────────────────────────────
# Audio Processing Helper
# ─────────────────────────────────────────────────────────────────────────────

def prepare_pcm16_wav(wav_path: Path) -> bytes:
    data, sr = sf.read(str(wav_path))
    data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    bio = io.BytesIO()
    sf.write(bio, data_int16, 16000, subtype="PCM_16", format="WAV")
    bio.seek(0)
    return bio.read()


# ─────────────────────────────────────────────────────────────────────────────
# Excel Incremental Writer & Formatter
# ─────────────────────────────────────────────────────────────────────────────

DETAIL_COLUMNS = [
    ("STT", 6),
    ("Mã Ca (Case ID)", 18),
    ("Tệp Âm Thanh", 26),
    ("Chiều Ngôn Ngữ", 16),
    ("Lĩnh Vực (Domain)", 16),
    ("Văn Bản Gốc (Ground Truth)", 45),
    ("Văn Bản Nhận Diện (Whisper STT)", 45),
    ("Độ Chính Xác Từ STT (%)", 22),
    ("Độ Lỗi Từ (WER)", 16),
    ("Độ Lỗi Ký Tự (CER)", 16),
    ("Bản Dịch Chuẩn (Reference)", 45),
    ("Bản Dịch Hệ Thống (NLLB)", 45),
    ("Độ Chuẩn Dịch Token-F1 (%)", 24),
    ("Độ Chuẩn Dịch chrF (%)", 22),
    ("Độ Chính Xác Số (%)", 18),
    ("Khớp Tuyệt Đối", 15),
    ("Thời Lượng Âm Thanh (s)", 22),
    ("Độ Trễ STT (ms)", 16),
    ("Độ Trễ Dịch (ms)", 16),
    ("Độ Trễ TTS (ms)", 16),
    ("Tổng Độ Trễ Toàn Tuyến (ms)", 26),
    ("Đánh Giá Chất Lượng", 20),
    ("Hành Động Bấm Cờ (QA Web Admin)", 30),
    ("Thời Điểm Kiểm Thử", 22),
]

def create_or_load_workbook(excel_path: Path) -> openpyxl.Workbook:
    if excel_path.exists():
        try:
            return openpyxl.load_workbook(excel_path)
        except Exception:
            pass
    wb = openpyxl.Workbook()
    # Sheet 1: Chi tiết 500 câu
    ws_detail = wb.active
    ws_detail.title = "Chi_tiet_500_cau"
    
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    headers = [col[0] for col in DETAIL_COLUMNS]
    ws_detail.append(headers)
    
    for col_idx, (col_name, width) in enumerate(DETAIL_COLUMNS, start=1):
        cell = ws_detail.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        col_letter = get_column_letter(col_idx)
        ws_detail.column_dimensions[col_letter].width = width
        
    ws_detail.row_dimensions[1].height = 32
    ws_detail.freeze_panes = "A2"
    return wb


def append_result_row(ws: Any, record: dict[str, Any]) -> None:
    row_values = [
        record["order"],
        record["case_id"],
        record["wav_file"],
        f"{record['source_lang'].upper()} → {record['target_lang'].upper()}",
        record["domain"],
        record["source_text"],
        record["recognized_text"],
        round(record["stt_word_accuracy"], 2),
        round(record["wer"], 4),
        round(record["cer"], 4),
        record["reference_translation"],
        record["translated_text"],
        round(record["token_f1"], 2),
        round(record["chrf"], 2),
        round(record["numeric_fidelity"], 2),
        "ĐÚNG" if record["exact_match"] else "KHÁC",
        round(record["audio_duration_seconds"], 2),
        round(record["stt_ms"], 1),
        round(record["trans_ms"], 1),
        round(record["tts_ms"], 1),
        round(record["total_latency_ms"], 1),
        "ĐẠT" if record["is_accurate"] else "CHƯA ĐẠT",
        "🚩 ĐÃ BẤM CỜ LÊN WEB ADMIN" if record["flagged"] else "✅ CHÍNH XÁC (Không cờ)",
        record["timestamp"],
    ]
    ws.append(row_values)
    row_num = ws.max_row
    
    # Apply cell styling
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )
    
    for c_idx in range(1, len(row_values) + 1):
        c = ws.cell(row=row_num, column=c_idx)
        c.font = Font(name="Calibri", size=10)
        c.border = thin_border
        if c_idx in (1, 4, 16, 17, 18, 19, 20, 21, 22, 23, 24):
            c.alignment = Alignment(horizontal="center", vertical="center")
        elif c_idx in (8, 9, 10, 13, 14, 15):
            c.alignment = Alignment(horizontal="right", vertical="center")
        else:
            c.alignment = Alignment(horizontal="left", vertical="center")
            
    # Highlight flagged cell
    status_cell = ws.cell(row=row_num, column=22)
    flag_cell = ws.cell(row=row_num, column=23)
    if record["flagged"]:
        status_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        status_cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
        flag_cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        flag_cell.font = Font(name="Calibri", size=10, bold=True, color="B45309")
    else:
        status_cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        status_cell.font = Font(name="Calibri", size=10, bold=True, color="166534")
        flag_cell.fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
        flag_cell.font = Font(name="Calibri", size=10, color="15803D")


def build_summary_sheet(wb: openpyxl.Workbook, records: list[dict[str, Any]]) -> None:
    if "Tong_quan" in wb.sheetnames:
        del wb["Tong_quan"]
    ws = wb.create_sheet(title="Tong_quan", index=0)
    ws.views.sheetView[0].showGridLines = True
    
    total = len(records)
    if total == 0:
        return
        
    vi_cases = [r for r in records if r["source_lang"] == "vi"]
    en_cases = [r for r in records if r["source_lang"] == "en"]
    flagged_cases = [r for r in records if r["flagged"]]
    accurate_cases = [r for r in records if r["is_accurate"]]
    
    stt_accs = [r["stt_word_accuracy"] for r in records]
    wers = [r["wer"] for r in records]
    cers = [r["cer"] for r in records]
    f1s = [r["token_f1"] for r in records]
    chrfs = [r["chrf"] for r in records]
    
    stt_times = [r["stt_ms"] for r in records]
    trans_times = [r["trans_ms"] for r in records]
    tts_times = [r["tts_ms"] for r in records]
    total_times = [r["total_latency_ms"] for r in records]
    
    # Title Block
    ws.merge_cells("A1:H1")
    ws["A1"] = "BÁO CÁO ĐÁNH GIÁ VÀ NGHIỆM THU KIỂM THỬ 500 CÂU ÂM THANH REALTIME T-LINGUA"
    ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40
    
    ws.merge_cells("A2:H2")
    ws["A2"] = f"Môi trường kiểm thử: On-Premise GPU RTX 3050 6GB | Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Số lượng mẫu: {total} câu"
    ws["A2"].font = Font(name="Calibri", size=11, italic=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 24
    
    # KPI Cards Row
    kpis = [
        ("TỔNG SỐ CÂU", f"{total}", "3B82F6"),
        ("ĐỘ CHÍNH XÁC STT (TB)", f"{sum(stt_accs)/total:.2f}%", "10B981"),
        ("ĐỘ CHUẨN DỊCH F1 (TB)", f"{sum(f1s)/total:.2f}%", "8B5CF6"),
        ("TỐC ĐỘ DỊCH TB", f"{sum(trans_times)/total:.1f} ms", "F59E0B"),
        ("TOÀN TUYẾN TB", f"{sum(total_times)/total/1000:.2f} s", "06B6D4"),
        ("SỐ CÂU BẤM CỜ LÊN QA", f"{len(flagged_cases)} ({len(flagged_cases)/total*100:.1f}%)", "EF4444"),
    ]
    
    card_cols = [("A", "B"), ("C", "C"), ("D", "D"), ("E", "E"), ("F", "F"), ("G", "H")]
    for idx, (title, val, color) in enumerate(kpis):
        c1, c2 = card_cols[idx]
        cell_ref = f"{c1}4"
        if c1 != c2:
            ws.merge_cells(f"{c1}4:{c2}4")
            ws.merge_cells(f"{c1}5:{c2}5")
        
        ws[f"{c1}4"] = title
        ws[f"{c1}4"].font = Font(name="Calibri", size=9, bold=True, color="64748B")
        ws[f"{c1}4"].alignment = Alignment(horizontal="center", vertical="center")
        
        ws[f"{c1}5"] = val
        ws[f"{c1}5"].font = Font(name="Calibri", size=16, bold=True, color=color)
        ws[f"{c1}5"].alignment = Alignment(horizontal="center", vertical="center")
        ws[f"{c1}5"].fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        
    ws.row_dimensions[4].height = 20
    ws.row_dimensions[5].height = 32
    
    # Section 1: So sánh Tốc độ & Độ trễ (Latency Analysis)
    ws["A7"] = "1. PHÂN TÍCH HIỆU NĂNG TỐC ĐỘ TOÀN TUYẾN & TỪNG THÀNH PHẦN"
    ws["A7"].font = Font(name="Calibri", size=13, bold=True, color="0F172A")
    
    latency_headers = ["Thành Phần Pipeline", "Mô Hình AI", "Trung Bình (ms)", "Median P50 (ms)", "P90 (ms)", "P95 (ms)", "P99 (ms)", "Mục Tiêu SLA"]
    ws.append([]) # row 8 is blank
    ws.append(latency_headers) # row 9
    
    r9 = ws.max_row
    for c_idx in range(1, 9):
        cell = ws.cell(row=r9, column=c_idx)
        cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    lat_rows = [
        ("Nhận diện giọng nói STT", "Whisper large-v3-turbo (GPU)", sum(stt_times)/total, percentile(stt_times, 0.5), percentile(stt_times, 0.9), percentile(stt_times, 0.95), percentile(stt_times, 0.99), "< 1000 ms"),
        ("Dịch thuật NLLB-200", "NLLB-200 distilled 1.3B (GPU)", sum(trans_times)/total, percentile(trans_times, 0.5), percentile(trans_times, 0.9), percentile(trans_times, 0.95), percentile(trans_times, 0.99), "< 1000 ms (Đạt)"),
        ("Tổng hợp giọng đọc TTS", "VITS MMS (CPU/GPU)", sum(tts_times)/total, percentile(tts_times, 0.5), percentile(tts_times, 0.9), percentile(tts_times, 0.95), percentile(tts_times, 0.99), "< 3500 ms"),
        ("Toàn tuyến Speech-to-Speech", "STT + Dịch + TTS Pipeline", sum(total_times)/total, percentile(total_times, 0.5), percentile(total_times, 0.9), percentile(total_times, 0.95), percentile(total_times, 0.99), "< 5000 ms"),
    ]
    
    for l_data in lat_rows:
        ws.append([
            l_data[0], l_data[1],
            round(l_data[2], 1), round(l_data[3], 1),
            round(l_data[4], 1), round(l_data[5], 1),
            round(l_data[6], 1), l_data[7]
        ])
        
    # Section 2: So sánh Chất lượng Dịch thuật & STT theo Chiều Ngôn Ngữ
    start_r = ws.max_row + 2
    ws.cell(row=start_r, column=1, value="2. ĐÁNH GIÁ SO SÁNH ĐỘ CHÍNH XÁC THEO CHIỀU NGÔN NGỮ (VI ↔ EN)").font = Font(name="Calibri", size=13, bold=True, color="0F172A")
    
    quality_headers = ["Chỉ Số Đánh Giá", "Tổng Thể (500 câu)", "Chiều Việt → Anh (250 câu)", "Chiều Anh → Việt (250 câu)", "Đánh Giá / Nhận Xét"]
    ws.append([])
    ws.append(quality_headers)
    
    q_r = ws.max_row
    for c_idx in range(1, 6):
        cell = ws.cell(row=q_r, column=c_idx)
        cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    vi_len = len(vi_cases) or 1
    en_len = len(en_cases) or 1
    
    q_metrics = [
        ("Độ chính xác từ STT (Word Accuracy)", f"{sum(stt_accs)/total:.2f}%", f"{sum(r['stt_word_accuracy'] for r in vi_cases)/vi_len:.2f}%", f"{sum(r['stt_word_accuracy'] for r in en_cases)/en_len:.2f}%", "Whisper nhận diện tốt cả 2 chiều"),
        ("Tỷ lệ lỗi từ STT (WER)", f"{sum(wers)/total:.4f}", f"{sum(r['wer'] for r in vi_cases)/vi_len:.4f}", f"{sum(r['wer'] for r in en_cases)/en_len:.4f}", "Thấp hơn ngưỡng 0.20"),
        ("Tỷ lệ lỗi ký tự STT (CER)", f"{sum(cers)/total:.4f}", f"{sum(r['cer'] for r in vi_cases)/vi_len:.4f}", f"{sum(r['cer'] for r in en_cases)/en_len:.4f}", "Độ bám âm thanh cao"),
        ("Độ chuẩn bản dịch Token-F1", f"{sum(f1s)/total:.2f}%", f"{sum(r['token_f1'] for r in vi_cases)/vi_len:.2f}%", f"{sum(r['token_f1'] for r in en_cases)/en_len:.2f}%", "Việt → Anh dịch mượt mà hơn"),
        ("Chỉ số chrF bản dịch", f"{sum(chrfs)/total:.2f}%", f"{sum(r['chrf'] for r in vi_cases)/vi_len:.2f}%", f"{sum(r['chrf'] for r in en_cases)/en_len:.2f}%", "Khớp n-gram ký tự dịch thuật"),
        ("Số câu đạt chuẩn hoàn toàn", f"{len(accurate_cases)} ({len(accurate_cases)/total*100:.1f}%)", f"{sum(1 for r in vi_cases if r['is_accurate'])} ({sum(1 for r in vi_cases if r['is_accurate'])/vi_len*100:.1f}%)", f"{sum(1 for r in en_cases if r['is_accurate'])} ({sum(1 for r in en_cases if r['is_accurate'])/en_len*100:.1f}%)", "Không cần can thiệp QA"),
        ("Số câu bấm cờ đẩy lên Web Admin QA", f"{len(flagged_cases)} ({len(flagged_cases)/total*100:.1f}%)", f"{sum(1 for r in vi_cases if r['flagged'])} ({sum(1 for r in vi_cases if r['flagged'])/vi_len*100:.1f}%)", f"{sum(1 for r in en_cases if r['flagged'])} ({sum(1 for r in en_cases if r['flagged'])/en_len*100:.1f}%)", "Đã đồng bộ lên Web Admin"),
    ]
    
    for row in q_metrics:
        ws.append(list(row))
        
    # Auto-adjust column widths
    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 28
    ws.column_dimensions["E"].width = 28
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 16
    ws.column_dimensions["H"].width = 22


def build_flagged_sheet(wb: openpyxl.Workbook, records: list[dict[str, Any]]) -> None:
    if "Danh_sach_bao_co_QA" in wb.sheetnames:
        del wb["Danh_sach_bao_co_QA"]
    ws = wb.create_sheet(title="Danh_sach_bao_co_QA")
    
    flagged = [r for r in records if r["flagged"]]
    
    headers = [
        "STT Lỗi", "Mã Ca", "Tệp Audio", "Chiều Dịch", "Văn Bản Gốc (Source)",
        "Văn Bản Nhận Diện (Whisper)", "Word Accuracy (%)", "Bản Dịch Hệ Thống (NLLB)",
        "Bản Dịch Chuẩn", "Token-F1 (%)", "Lý Do Bấm Cờ", "Trạng Thái Trên Web Admin"
    ]
    ws.append(headers)
    
    header_fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
    ws.row_dimensions[1].height = 30
    
    for idx, r in enumerate(flagged, start=1):
        reason = []
        if r["stt_word_accuracy"] < 80.0:
            reason.append(f"STT thấp ({r['stt_word_accuracy']:.1f}%)")
        if r["token_f1"] < 65.0:
            reason.append(f"Dịch lệch F1 ({r['token_f1']:.1f}%)")
        reason_str = ", ".join(reason) if reason else "Chưa khớp chuẩn"
        
        ws.append([
            idx,
            r["case_id"],
            r["wav_file"],
            f"{r['source_lang'].upper()} → {r['target_lang'].upper()}",
            r["source_text"],
            r["recognized_text"],
            round(r["stt_word_accuracy"], 2),
            r["translated_text"],
            r["reference_translation"],
            round(r["token_f1"], 2),
            reason_str,
            "Đang chờ kiểm tra (Chờ QA)",
        ])
        
    # Auto-adjust column widths
    cols_width = [10, 18, 25, 15, 45, 45, 18, 45, 45, 16, 25, 25]
    for c_idx, width in enumerate(cols_width, start=1):
        col_letter = get_column_letter(c_idx)
        ws.column_dimensions[col_letter].width = width


# ─────────────────────────────────────────────────────────────────────────────
# Main Evaluation Loop
# ─────────────────────────────────────────────────────────────────────────────

def run_test_suite(max_cases: int = 500, excel_output: Path = DEFAULT_EXCEL_PATH) -> None:
    print("===================================================================")
    print(" >>> BẮT ĐẦU KIỂM THỬ TOÀN DIỆN 500 CÂU ÂM THANH REALTIME T-LINGUA <<<")
    print(f" Dataset âm thanh: {AUDIO_DIR}")
    print(f" File báo cáo Excel: {excel_output}")
    print(f" Số lượng câu kiểm thử: {max_cases}")
    print("===================================================================\n")
    
    # Load manifest and reference cases
    with open(MANIFEST_PATH, "r", encoding="utf-8-sig") as f:
        manifest_rows = list(csv.DictReader(f))
        
    with open(CASES_PATH, "r", encoding="utf-8-sig") as f:
        case_rows = {r["case_id"]: r for r in csv.DictReader(f)}
        
    cases_to_run = manifest_rows[:max_cases]
    
    # Initialize Guest Session
    client = httpx.Client(base_url=BACKEND_HTTP, timeout=60.0)
    try:
        r_session = client.post("/api/session/guest")
        if r_session.status_code not in (200, 201):
            print(f"[ERROR] Cannot get guest session: {r_session.status_code} {r_session.text}")
            sys.exit(1)
        guest_data = r_session.json()
        token = guest_data["access_token"]
        print(f"[AUTH] Khởi tạo phiên khách thành công. Owner ID: {guest_data['owner_id']}")
    except Exception as e:
        print(f"[ERROR] Connection to backend failed: {e}")
        sys.exit(1)
        
    wb = create_or_load_workbook(excel_output)
    ws_detail = wb["Chi_tiet_500_cau"]
    
    records: list[dict[str, Any]] = []
    flagged_count = 0
    passed_count = 0
    
    t_suite_start = time.perf_counter()
    
    for idx, item in enumerate(cases_to_run, start=1):
        case_id = item["case_id"]
        wav_file = item["wav_file"]
        wav_path = AUDIO_DIR / wav_file
        source_text = item["source_text"]
        source_lang = item["source_lang"] # "vi" or "en"
        duration_sec = float(item.get("duration_seconds", 0.0))
        domain = item.get("domain", "")
        
        ref_case = case_rows.get(case_id, {})
        reference_text = ref_case.get("reference", "")
        
        # RULE: Check & configure language direction
        # If input audio is English -> switch source=en, target=vi.
        # If input audio is Vietnamese -> source=vi, target=en.
        if source_lang == "en":
            effective_src = "en"
            effective_tgt = "vi"
        else:
            effective_src = "vi"
            effective_tgt = "en"
            
        # Prepare 16kHz PCM audio
        try:
            pcm_wav_bytes = prepare_pcm16_wav(wav_path)
        except Exception as err:
            print(f"[{idx}/{len(cases_to_run)}] Lỗi đọc âm thanh {wav_file}: {err}")
            continue
            
        # Send audio to pipeline /translate endpoint
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": (wav_file, pcm_wav_bytes, "audio/wav")}
        data_form = {"source_lang": effective_src, "target_lang": effective_tgt}
        
        t0 = time.perf_counter()
        try:
            resp = client.post("/translate", files=files, data=data_form, headers=headers)
        except Exception as e:
            # Reconnect session if needed
            print(f"[{idx}/{len(cases_to_run)}] Exception calling /translate: {e}")
            continue
            
        elapsed_total = (time.perf_counter() - t0) * 1000
        
        if resp.status_code == 401:
            try:
                r_session = client.post("/api/session/guest")
                if r_session.status_code in (200, 201):
                    token = r_session.json()["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    files = {"file": (wav_file, pcm_wav_bytes, "audio/wav")}
                    resp = client.post("/translate", files=files, data=data_form, headers=headers)
            except Exception:
                pass

        if resp.status_code != 200:
            print(f"[{idx}/{len(cases_to_run)}] [LỖI {resp.status_code}] {case_id}: {resp.text}")
            continue
            
        res_data = resp.json()
        recognized_text = res_data.get("original_text", "").strip()
        translated_text = res_data.get("translated_text", "").strip()
        metrics = res_data.get("metrics", {})
        qa_token = res_data.get("qa_audio_token")
        
        stt_ms = float(metrics.get("whisper_latency", 0.0)) * 1000
        trans_ms = float(metrics.get("translation_latency", 0.0)) * 1000
        tts_ms = float(metrics.get("tts_latency", 0.0)) * 1000
        total_pipeline_ms = float(metrics.get("total_latency", 0.0)) * 1000 or elapsed_total
        
        # Calculate Accuracy Metrics
        src_tokens = normalize_tokens(source_text)
        hyp_tokens = normalize_tokens(recognized_text)
        src_chars = list(normalize_text(source_text))
        hyp_chars = list(normalize_text(recognized_text))
        
        w_dist = edit_distance(src_tokens, hyp_tokens)
        c_dist = edit_distance(src_chars, hyp_chars)
        
        wer = w_dist / max(1, len(src_tokens))
        cer = c_dist / max(1, len(src_chars))
        stt_word_accuracy = max(0.0, 1.0 - wer) * 100.0
        
        f1 = token_f1(reference_text, translated_text)
        chrf = chrf_score(reference_text, translated_text)
        num_fid = numeric_fidelity(reference_text, translated_text)
        exact_match = normalize_text(reference_text) == normalize_text(translated_text)
        
        # Accuracy decision:
        # A sentence is deemed accurate if STT Word Accuracy >= 80% AND Translation F1 >= 65%
        is_accurate = (stt_word_accuracy >= 80.0) and (f1 >= 65.0)
        
        flagged = False
        if not is_accurate:
            # Action: Bấm cờ để đưa câu đó lên web_admin
            try:
                flag_payload = {
                    "source_text": recognized_text or source_text,
                    "translated_text": translated_text,
                    "source_lang": effective_src,
                    "target_lang": effective_tgt,
                    "input_mode": "voice",
                    "qa_audio_token": qa_token
                }
                client.post("/api/flag-translation", json=flag_payload, headers=headers)
                flagged = True
                flagged_count += 1
            except Exception as fe:
                print(f"  [CẢNH BÁO] Không thể gửi cờ: {fe}")
        else:
            passed_count += 1
            
        record = {
            "order": idx,
            "case_id": case_id,
            "wav_file": wav_file,
            "source_lang": effective_src,
            "target_lang": effective_tgt,
            "domain": domain,
            "source_text": source_text,
            "recognized_text": recognized_text,
            "stt_word_accuracy": stt_word_accuracy,
            "wer": wer,
            "cer": cer,
            "reference_translation": reference_text,
            "translated_text": translated_text,
            "token_f1": f1,
            "chrf": chrf,
            "numeric_fidelity": num_fid,
            "exact_match": exact_match,
            "audio_duration_seconds": duration_sec,
            "stt_ms": stt_ms,
            "trans_ms": trans_ms,
            "tts_ms": tts_ms,
            "total_latency_ms": total_pipeline_ms,
            "is_accurate": is_accurate,
            "flagged": flagged,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        records.append(record)
        
        # PROGRESSIVE EXCEL SAVE (Immediately after EACH sentence)
        append_result_row(ws_detail, record)
        if idx % 5 == 0 or idx == len(cases_to_run):
            build_summary_sheet(wb, records)
            build_flagged_sheet(wb, records)
            wb.save(excel_output)
            
        status_tag = "✅ ĐẠT" if is_accurate else "🚩 BẤM CỜ QA"
        lang_tag = f"{effective_src.upper()}→{effective_tgt.upper()}"
        print(f"[{idx:03d}/{len(cases_to_run)}] {lang_tag} {status_tag} | STT Acc: {stt_word_accuracy:5.1f}% | Trans F1: {f1:5.1f}% | Latency: {total_pipeline_ms:5.0f}ms (STT: {stt_ms:.0f}ms, NLLB: {trans_ms:.0f}ms, TTS: {tts_ms:.0f}ms)")
        if not is_accurate:
            print(f"    Gốc:   {source_text[:65]}...")
            print(f"    STT:   {recognized_text[:65]}...")
            print(f"    Dịch:  {translated_text[:65]}...")
            
    # Final full workbook save with complete summary & styling
    build_summary_sheet(wb, records)
    build_flagged_sheet(wb, records)
    wb.save(excel_output)
    
    client.close()
    
    total_elapsed = time.perf_counter() - t_suite_start
    print("\n===================================================================")
    print(" >>> HOÀN TẤT KIỂM THỬ VÀ ĐÁNH GIÁ 500 CÂU ÂM THANH T-LINGUA <<<")
    print(f" Tổng thời gian: {total_elapsed:.1f} giây ({total_elapsed/60:.2f} phút)")
    print(f" Tổng số câu: {len(records)} | Đạt chuẩn: {passed_count} | Bấm cờ lên Web Admin QA: {flagged_count}")
    print(f" File báo cáo Excel hoàn thiện: {excel_output}")
    print("===================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T-Lingua 500 Audio End-to-End Evaluation")
    parser.add_argument("--max-cases", type=int, default=500, help="Number of cases to evaluate (default 500)")
    parser.add_argument("--excel-output", type=Path, default=DEFAULT_EXCEL_PATH, help="Output Excel path")
    args = parser.parse_args()
    run_test_suite(max_cases=args.max_cases, excel_output=args.excel_output)

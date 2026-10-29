import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import openpyxl
from scripts.run_500_end_user_test import build_summary_sheet, build_flagged_sheet

excel_path = Path("outputs/Bao_cao_kiem_thu_500_cau_am_thanh.xlsx")
wb = openpyxl.load_workbook(excel_path)
ws_detail = wb["Chi_tiet_500_cau"]

records = []
for row in ws_detail.iter_rows(min_row=2, max_row=ws_detail.max_row, values_only=True):
    # Map values back to dict
    records.append({
        "order": row[0],
        "case_id": row[1],
        "wav_file": row[2],
        "source_lang": "vi" if "VI" in str(row[3]).split("→")[0] else "en",
        "target_lang": "en" if "EN" in str(row[3]).split("→")[1] else "vi",
        "domain": row[4],
        "source_text": row[5],
        "recognized_text": row[6],
        "stt_word_accuracy": float(row[7]),
        "wer": float(row[8]),
        "cer": float(row[9]),
        "reference_translation": row[10],
        "translated_text": row[11],
        "token_f1": float(row[12]),
        "chrf": float(row[13]),
        "numeric_fidelity": float(row[14]),
        "exact_match": str(row[15]) == "ĐÚNG",
        "audio_duration_seconds": float(row[16]),
        "stt_ms": float(row[17]),
        "trans_ms": float(row[18]),
        "tts_ms": float(row[19]),
        "total_latency_ms": float(row[20]),
        "is_accurate": str(row[21]) == "ĐẠT",
        "flagged": "ĐÃ BẤM CỜ" in str(row[22]),
        "timestamp": row[23],
    })

print(f"Loaded {len(records)} records.")
build_summary_sheet(wb, records)
build_flagged_sheet(wb, records)
wb.save(excel_path)
print("Updated workbook with clean 500 records successfully!")

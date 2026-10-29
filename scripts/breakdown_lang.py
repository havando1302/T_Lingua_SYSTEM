import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

wb = openpyxl.load_workbook("outputs/Bao_cao_kiem_thu_500_cau_am_thanh.xlsx", data_only=True)
ws = wb["Chi_tiet_500_cau"]

vi_cases = []
en_cases = []

for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    # col 4: lang, col 8: STT Acc, col 9: WER, col 10: CER, col 13: F1, col 14: chrF, col 18: STT ms, col 19: Trans ms, col 20: TTS ms, col 21: Total ms, col 22: Status, col 23: Flag
    lang = str(row[3])
    data = {
        "stt_acc": float(row[7]),
        "wer": float(row[8]),
        "cer": float(row[9]),
        "f1": float(row[12]),
        "chrf": float(row[13]),
        "stt_ms": float(row[17]),
        "trans_ms": float(row[18]),
        "tts_ms": float(row[19]),
        "total_ms": float(row[20]),
        "passed": str(row[21]) == "ĐẠT",
        "flagged": "ĐÃ BẤM CỜ" in str(row[22]),
    }
    if "VI → EN" in lang:
        vi_cases.append(data)
    else:
        en_cases.append(data)

def print_group(name, cases):
    n = len(cases)
    passed = sum(1 for c in cases if c["passed"])
    flagged = sum(1 for c in cases if c["flagged"])
    print(f"\n=== {name} ({n} CÂU) ===")
    print(f"  Đạt chuẩn: {passed} ({passed/n*100:.1f}%) | Bấm cờ QA: {flagged} ({flagged/n*100:.1f}%)")
    print(f"  STT Word Accuracy (TB): {sum(c['stt_acc'] for c in cases)/n:.2f}% | WER: {sum(c['wer'] for c in cases)/n:.4f} | CER: {sum(c['cer'] for c in cases)/n:.4f}")
    print(f"  Dịch thuật Token-F1 (TB): {sum(c['f1'] for c in cases)/n:.2f}% | chrF: {sum(c['chrf'] for c in cases)/n:.2f}%")
    print(f"  Độ trễ STT (TB): {sum(c['stt_ms'] for c in cases)/n:.1f} ms")
    print(f"  Độ trễ Dịch NLLB (TB): {sum(c['trans_ms'] for c in cases)/n:.1f} ms")
    print(f"  Độ trễ TTS (TB): {sum(c['tts_ms'] for c in cases)/n:.1f} ms")
    print(f"  Độ trễ Toàn tuyến (TB): {sum(c['total_ms'] for c in cases)/n/1000:.2f} s")

print_group("CHIỀU VIỆT → ANH", vi_cases)
print_group("CHIỀU ANH → VIỆT", en_cases)

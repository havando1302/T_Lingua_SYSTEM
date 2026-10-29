import openpyxl

wb = openpyxl.load_workbook("outputs/Bao_cao_kiem_thu_500_cau_am_thanh.xlsx", data_only=True)
ws_detail = wb["Chi_tiet_500_cau"]
total_rows = ws_detail.max_row - 1

stt_accs = []
f1s = []
stt_times = []
trans_times = []
tts_times = []
total_times = []
flagged_count = 0
passed_count = 0

for row in ws_detail.iter_rows(min_row=2, max_row=ws_detail.max_row, values_only=True):
    # col 8: STT Acc, col 13: F1, col 18: STT ms, col 19: Trans ms, col 20: TTS ms, col 21: Total ms, col 22: Status, col 23: Flag
    stt_accs.append(float(row[7]))
    f1s.append(float(row[12]))
    stt_times.append(float(row[17]))
    trans_times.append(float(row[18]))
    tts_times.append(float(row[19]))
    total_times.append(float(row[20]))
    if "ĐÃ BẤM CỜ" in str(row[22]):
        flagged_count += 1
    else:
        passed_count += 1

print(f"--- BÁO CÁO TIẾN ĐỘ THỰC TẾ ---")
print(f"Số câu đã hoàn thành: {total_rows}/500 ({total_rows/500*100:.1f}%)")
print(f"Số câu đạt chuẩn: {passed_count} ({passed_count/total_rows*100:.1f}%)")
print(f"Số câu bấm cờ lên Web Admin QA: {flagged_count} ({flagged_count/total_rows*100:.1f}%)")
print(f"Độ chính xác STT trung bình: {sum(stt_accs)/total_rows:.2f}%")
print(f"Độ chuẩn dịch F1 trung bình: {sum(f1s)/total_rows:.2f}%")
print(f"Độ trễ STT trung bình: {sum(stt_times)/total_rows:.1f} ms")
print(f"Độ trễ Dịch NLLB trung bình: {sum(trans_times)/total_rows:.1f} ms")
print(f"Độ trễ TTS trung bình: {sum(tts_times)/total_rows:.1f} ms")
print(f"Độ trễ Toàn tuyến trung bình: {sum(total_times)/total_rows/1000:.2f} s")

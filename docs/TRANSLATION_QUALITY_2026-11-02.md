# Đánh giá và cải thiện dịch T-Lingua — 02/11/2026

Đã đo trực tiếp mô hình NLLB đang được cấu hình trong dự án bằng GPU RTX 3050 6 GB. Kết quả là phép đo đường dịch văn bản cục bộ, không phải kiểm tra dịch vụ Internet hay phần trăm câu được con người đánh giá là đúng nghĩa.

## Kết quả cuối trên 400 câu kiểm chứng

| Chỉ số | Trước: beam 1 | Sau: beam 3 và các sửa lỗi |
|---|---:|---:|
| BLEU | 33,622 | 38,213 |
| chrF++ | 54,956 | 58,581 |
| Token-F1 trung bình | 66,960 | 69,187 |
| Việt → Anh, chrF++ (200 câu) | 56,876 | 61,118 |
| Anh → Việt, chrF++ (200 câu) | 52,493 | 55,416 |
| Độ trễ trung bình | 651,607 ms | 743,778 ms |
| Độ trễ p95 | 1.164,061 ms | 1.381,871 ms |
| Ca lỗi thực thi | 0 | 0 |
| Ca mất số/mã theo bộ kiểm tra | 0 | 0 |
| Ca trả marker nội bộ | 0 | 0 |

Điểm chrF++ tăng 3,625 điểm; BLEU tăng 4,591 điểm. Độ trễ trung bình tăng khoảng 14,1%, p95 tăng khoảng 18,7%. Theo Token-F1, 200 câu tăng điểm, 85 câu giảm điểm, 115 câu không đổi. Nhóm dịch Anh → Việt vẫn yếu hơn. Bốn nhóm có Token-F1 trung bình giảm: customer_experience, manufacturing, public_service và security; cần được ưu tiên rà soát nghĩa và bổ sung dữ liệu QA.

Đã đặt `TRANSLATION_BEAM_SIZE=3` trong cấu hình mặc định, các tệp môi trường mẫu và `backend/.env`. Khóa này trước đó chưa có trong `.env`, nên chỉ thêm một dòng, giữ nguyên các thiết lập khác. Để ưu tiên độ trễ, có thể đặt lại giá trị 1 và khởi động lại backend.

Kiểm thử sau thay đổi cấu hình: **84 test và 20 subtest đạt**. Không khởi động lại hoặc triển khai backend từ xa trong lần làm việc này.

## Phương pháp

- Mô hình: `facebook/nllb-200-distilled-1.3B`, revision `7be3e24664b38ce1cac29b8aeed6911aa0cf0576`; tải từ cache, không tải trọng số mới.
- Cấu hình cục bộ trước sửa: beam 1, retry beam 3, sentence batch 4, fuzzy threshold 0.97, CUDA.
- Bộ câu: `outputs/fresh500_optimized_20261014/fresh_500_test_cases.csv`, 500 câu nguồn khác nhau, 20 lĩnh vực, cân bằng hai chiều. 100 câu khảo sát và 400 câu kiểm chứng.
- Không có câu nguồn trùng với cả 497 dòng trong dataset NLLB đang mở, kể cả các dòng validation/test.
- Bộ 500 câu ngày 25/10 trùng 497 câu với dataset này nên không được dùng làm bằng chứng khái quát hóa.
- So sánh dùng cùng revision mô hình, từ điển khởi tạo 500 mục, TM tạm riêng và tắt cache dịch. Không sửa lịch sử, từ điển cá nhân hoặc dataset đang mở.
- Chỉ nạp NLLB, không nạp Whisper/TTS khi đo. Độ trễ gồm xử lý dịch trong tiến trình; không gồm mạng, STT, TTS hay thời gian nạp mô hình.
- BLEU và chrF++ do SacreBLEU 2.6.0 tính; chrF++ dùng word order 2. Token-F1 là chỉ số so khớp từ. Các chỉ số này không phải tỷ lệ dịch đúng.

## Những lỗi đã sửa

1. Tên riêng tiếng Việt nhiều từ bị dịch nghĩa hoặc biến thành chủ ngữ khác. Bổ sung bảo vệ thận trọng cho các từ viết hoa liên tiếp; bản dịch đã duyệt trong glossary vẫn được ưu tiên.
2. Khi mô hình làm hỏng marker, mất mã/số hoặc bỏ tên, thử lại bằng cách bỏ lớp bảo vệ tên tự suy ra, giữ lớp bảo vệ thuật ngữ đã duyệt và mã/số. Ghi cảnh báo `proper_name_protection_fallback` để có thể rà soát.
3. Marker có hậu tố bị viết sai như `ZXQTLGLOSARY0Q` hoặc `ZXQTLTLENTITY0Q` trước đây có thể lọt qua. Bộ kiểm tra nay nhận tiền tố nội bộ dù hậu tố bị biến dạng.
4. Bảo vệ dấu âm/dương và số lần xuất hiện của số/mã. Kiểm tra fuzzy TM cũng phân biệt những thay đổi này, đồng thời nhận thêm dạng phủ định và dấu nháy cong trong tiếng Anh.
5. Quy tắc hậu xử lý STT chỉ khớp trọn từ, tránh biến “máy tính” thành “máy tínhh” hay “ứng dụng” thành “ứng dụngg”. Bỏ quy tắc sai “dạy học” → “dậy học”; hạn chế các sửa đồng âm dễ làm đổi nghĩa câu vốn đúng.

## Bằng chứng

- Báo cáo so sánh cuối: `outputs/translation_quality_20261102/comparison.json`.
- Chi tiết bản trước: `outputs/translation_quality_20261102/holdout/results.json`, nhóm `baseline`.
- Chi tiết bản cuối: `outputs/translation_quality_20261102/validation_final/results.json`.
- Bản thử đầu của bảo vệ tên được ghi nhận là không đạt an toàn trong `tune_names/safety_reaudit.json`; không dùng bản này làm kết quả cuối.
- Kiểm tra dataset: `outputs/translation_quality_20261102/dataset_audit.json`: 497 dòng, 403 train / 46 validation / 48 test, không phát hiện marker; không sửa dữ liệu.

## Giới hạn và phần còn yếu

- Corpus được tạo theo mẫu. Các nhóm khảo sát và kiểm chứng có chung kiểu câu và từ vựng; một số câu kiểm chứng đã được xem để sửa lỗi. Đây là kiểm chứng hồi quy, không phải nghiên cứu đánh giá mù trên miền dữ liệu hoàn toàn mới.
- Có câu giảm điểm so khớp dù điểm tổng tăng; ví dụ cải thiện và giảm điểm đều được lưu trong báo cáo so sánh. Giảm điểm tự động chưa đủ để kết luận bản dịch sai nghĩa hơn.
- Kiểm tra số/mã chỉ đếm các token số viết bằng chữ số, chưa xác nhận mọi cách đọc số thành chữ, đơn vị, quan hệ chủ ngữ hoặc ý nghĩa toàn câu.
- Bảo vệ tên tự suy ra có thể phải quay lại dịch tự nhiên. Không khẳng định giữ đúng mọi tên riêng; các tên quan trọng vẫn cần glossary đã được thẩm định.
- Chưa đo lại STT/TTS bằng âm thanh thật, chưa có điểm adequacy do người đánh giá và chưa kiểm tra bản đang chạy trên Colab/Internet.
- Tập 497 câu hiện tại không đủ để khẳng định fine-tuning sẽ tốt trên hội thoại đa dạng. Kết quả lần này không ghi lại đáp án đánh giá vào TM hoặc dataset để tăng điểm.

## Chạy lại

Từ thư mục gốc dự án:

```powershell
.\backend\venv\Scripts\python.exe scripts/evaluate_translation_quality.py --partition holdout --variants beam3 --output outputs/translation_quality_recheck
```

Lệnh dùng mô hình đã có trong cache và TM tạm, có thể chạy vài phút trên GPU. File kết quả ghi revision và SHA-256 của dữ liệu, glossary, mã dịch để truy vết cấu hình. Backend đang chạy cần được khởi động lại sau khi cập nhật mã hoặc cấu hình.

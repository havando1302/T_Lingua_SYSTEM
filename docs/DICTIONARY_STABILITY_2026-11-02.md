# Cải thiện từ điển T-Lingua — 02/11/2026

## Kết quả tại máy cục bộ

- Đã nạp thêm 499 mục, giữ nguyên mục có sẵn: tổng cộng 500 mục đã duyệt.
- Việt → Anh: 250 mục. Anh → Việt: 250 mục.
- Dữ liệu khởi tạo: `backend/resources/dictionary_seed500.json`.
- Công cụ: `backend/scripts/seed_dictionary.py`; mặc định chỉ xem trước, `--apply --actor-id 1` mới ghi.
- Audit Log ghi nhận tài khoản `admin` (ID 1), theo lựa chọn của người dùng.
- Đã kiểm tra nạp lại không tạo thêm mục và tra cứu hai chiều tên Đại học Phenikaa.
- Đã sửa hai mục Phenikaa bị lỗi mã hóa ở lần tạo file ban đầu và thêm kiểm tra ngăn tái diễn.

## Thay đổi kỹ thuật

1. Không bảo vệ số lần thứ hai bên trong placeholder glossary. Trước đây điều này có thể khiến marker glossary không được khôi phục.
2. Phát hiện marker ENTITY/GLOSSARY kể cả khi NLLB chèn khoảng trắng, dấu chấm, gạch nối hoặc gạch dưới giữa các ký tự.
3. Bỏ qua cache/TM chứa marker; chặn đầu ra lỗi trước khi ghi cache hoặc chuyển sang TTS. Bản dịch chung hợp lệ vẫn dùng được khi mục cá nhân bị lỗi.
4. Khi thử dịch lại, ưu tiên kết quả không rò marker; nếu cả hai vẫn lỗi thì báo lỗi thay vì trả marker ra người dùng.
5. Dùng cùng quy tắc chặn marker ở API từ điển, xuất QA, xác thực dataset, bộ dựng dataset và trình huấn luyện NLLB.
6. Whisper ưu tiên thuật ngữ có từ trùng ngữ cảnh, sau đó tên riêng, trong giới hạn 300 ký tự. Realtime dùng đoạn nhận diện gần nhất trong cùng phiên, chiều dịch và người nói; không đoán trước nội dung âm thanh.
7. Loại nội dung trên 8 từ hoặc 100 ký tự khỏi runtime glossary. Câu dài vẫn giữ trong Translation Memory. Giao diện giải thích rõ giới hạn này.
8. Giữ các sửa lỗi nhập CSV/XLSX và nhập hàng loạt từ bước trước.

## Sao lưu

- Trước khi nạp: `backend/backups/dictionary-seed-20261102T123624944671Z.db`.
- Trước khi sửa mã hóa: `backend/backups/dictionary-encoding-20261102T123734223689Z.db`.
- Sao lưu dùng SQLite backup API, bao gồm dữ liệu đã commit trong WAL.

## Kiểm chứng

- Bộ kiểm thử liên quan đến API, cache, glossary, NLLB sentence batching, SQLite và realtime: 62 test và 11 subtest đạt.
- Kiểm thử nạp dữ liệu xác nhận sao lưu, giữ nguyên bản dịch có sẵn và tính lặp lại an toàn trên SQLite tạm.
- Build Admin Web: đạt.
- File `outputs/nllb_dataset_phase2/nllb-training.jsonl`: 497 dòng; không phát hiện marker theo bộ kiểm tra mới, không sửa file dữ liệu này.

## Giới hạn đã biết

- Bộ 500 mục chọn từ dữ liệu thuật ngữ có sẵn trong dự án và các ví dụ tên riêng người dùng cung cấp. Kiểm tra tự động xác nhận cấu trúc, chiều dịch, độ dài và không xung đột; không thay thế thẩm định ngôn ngữ theo lĩnh vực.
- Chưa đo lại chất lượng dịch với mô hình thật/GPU. Chưa triển khai hoặc khởi động lại backend từ xa/Colab.
- Backend đang chạy cần khởi động lại sau khi cập nhật mã nguồn để dùng quy tắc mới và loại cache trong tiến trình cũ.
- Không tự gộp 500 mục thuật ngữ vào dataset huấn luyện câu NLLB.

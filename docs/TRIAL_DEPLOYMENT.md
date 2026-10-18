# Triển khai bản dùng thử T-Lingua

## Trạng thái kỹ thuật đã xác nhận

- Cấu hình mục tiêu: một máy NVIDIA có ít nhất 6 GB VRAM, một tiến trình backend GPU.
- Dịch: NLLB 1.3B FP16, greedy, tách câu và dịch batch tối đa 4 câu.
- STT: Whisper large-v3-turbo FP16, greedy.
- TTS: MMS/VITS FP32 trên CPU đối với GPU 6 GB để tránh NaN/Inf và dành VRAM cho STT/dịch.
- Không tăng số tiến trình Uvicorn: mỗi tiến trình sẽ nạp lại toàn bộ model GPU.

## Các bước triển khai

1. Cài NVIDIA driver, NVIDIA Container Toolkit và Docker Compose trên máy chủ.
2. Sao chép `backend/.env.trial.example` thành `backend/.env`.
3. Thay domain và tạo ba khóa độc lập; không dùng các giá trị mẫu.
4. Đặt reverse proxy TLS (Caddy/Nginx/Cloudflare Tunnel) trước cổng backend. Chỉ công khai HTTPS/WSS.
5. Chạy kiểm tra trước triển khai:

   `python scripts/check_trial_readiness.py --env backend/.env`

6. Khởi động: `docker compose up -d --build`.
7. Chờ `/health/ready` trả về thành công rồi mới mở traffic cho người dùng thử.
8. Build ứng dụng Flutter với đúng origin HTTPS:

   `flutter build web --release --dart-define=API_BASE_URL=https://trial.example.com`

9. Sau khi mở thử nghiệm, theo dõi `/admin/metrics`, tỷ lệ lỗi, p95 và dung lượng VRAM.

## Điều kiện phát hành thử

- Bắt buộc: TLS, CORS/Trusted Hosts đúng domain, khóa bí mật riêng, MFA quản trị, backup đã thử khôi phục.
- Giới hạn ban đầu: tối đa 8 WebSocket toàn hệ thống và 1 kết nối trên mỗi chủ thể.
- Chạy thử nội bộ trước; chỉ tăng tải sau khi soak test không có OOM hoặc lỗi model.
- Không dùng 500 câu kiểm thử làm Translation Memory mặc định vì sẽ gây rò rỉ đáp án và làm sai kết quả đánh giá.

## Tiêu chí đánh giá tiếp theo

- Dịch: mean và p95 dưới 1 giây; token-F1/chrF tối thiểu 70% hoặc điểm người đánh giá độc lập tối thiểu 4/5.
- STT: word accuracy tối thiểu 90% trong phòng yên tĩnh và 85% trong nhiễu văn phòng.
- Dữ liệu thật: ít nhất 5 người nói mỗi ngôn ngữ, nhiều thiết bị và ba điều kiện nhiễu.

# Hồ sơ dự án đến hết ngày 24/09/2026

Tài liệu này gom các đầu ra quản lý dự án còn thiếu trong giai đoạn 25/08–24/09. Các số liệu thực nghiệm chỉ được lấy từ artifact có thể chạy lại; không suy diễn số liệu chưa đo.

## 1. Project charter và biên bản kick-off

- Tên dự án: Hệ thống AI dịch thuật T-Langua.
- Thời gian toàn dự án: 25/08/2026–30/10/2026.
- Phạm vi báo cáo này: 25/08/2026–24/09/2026.
- Mục tiêu: hoàn thiện nền Flutter, FastAPI/WebSocket và React Admin đã có; nâng chất lượng/tốc độ dịch; bảo đảm xác thực, phân quyền, quan sát và khả năng vận hành.
- Thành viên: Hà Văn Đô và Nguyễn Quang Thọ.
- Nhịp quản lý: cập nhật hằng ngày; review tích hợp tối thiểu hai lần/tuần; kiểm tra mốc vào cuối mỗi giai đoạn.
- Definition of Done: mã nguồn được review; test liên quan đạt; không còn lỗi P0/P1 đã biết; có bằng chứng kết quả; cập nhật tài liệu; không chứa secret/dữ liệu cá nhân trong artifact.

### RACI

| Nhóm công việc | Hà Văn Đô | Nguyễn Quang Thọ |
|---|---|---|
| Backend, AI, STT–dịch–TTS | R/A | C |
| Hiệu năng, GPU, queue, cache | R/A | C |
| Flutter frontend | C | R/A |
| React admin web | C | R/A |
| API contract và tích hợp | R | R |
| QA, benchmark, nghiệm thu | R | R |
| Triển khai, bảo mật, vận hành | R/A | C |

R = thực hiện, A = chịu trách nhiệm cuối, C = tham vấn.

## 2. Phạm vi MVP và ngoài phạm vi

### Trong phạm vi

- Dịch văn bản Việt–Anh và Anh–Việt.
- Hội thoại giọng nói qua WebSocket với STT, dịch và TTS.
- Flutter: dịch, lịch sử, thiết lập, trạng thái mic/kết nối và phản hồi lỗi.
- Admin: Login, Dashboard, Analytics, Users, API Keys, Dictionary, History, QA, Settings.
- Xác thực session/JWT, API key, RBAC, rate limit và cách ly dữ liệu.
- Translation Memory, cache, chuẩn hóa văn bản, telemetry, queue/backpressure và Docker.

### Ngoài phạm vi đến 24/09

- Huấn luyện foundation model từ đầu.
- Cam kết chất lượng cho cặp ngôn ngữ ngoài Việt–Anh.
- HA đa vùng, billing thương mại và triển khai production.
- Tuyên bố KPI WER/TTS hoặc tải production khi chưa có corpus audio và môi trường tải chuẩn.

## 3. Đánh giá hiện trạng

### Backend/AI

- FastAPI cung cấp REST, WebSocket, health/readiness và admin API.
- Pipeline có STT, NLLB, TTS, VAD, denoise, worker queue và telemetry theo chặng.
- Có session/JWT, API key, RBAC, MFA policy, rate limit và isolation theo owner.
- Có Translation Memory, cache theo owner/ngôn ngữ/version và invalidation.
- Đã bổ sung benchmark 500 câu, 100 audio, WER, full-pipeline profile, fuzzy TM và control plane active/canary/rollback có audit.
- Nợ kỹ thuật còn lại: accuracy thuật ngữ và WER chưa đạt quality gate; TTS MOS/người chấm độc lập chưa hoàn tất; cảnh báo phụ thuộc TestClient cần kế hoạch nâng cấp.

### Flutter

- Có controller/repository cho dịch, lịch sử, settings; WebSocket, audio stream/player và state machine mic.
- Static analysis đạt `No issues found!`; lần timeout ban đầu do sandbox chặn Dart Analysis Server ghi plugin state vào AppData.

### Admin web

- Có đầy đủ route/màn hình MVP; route guard theo role; tìm kiếm, phân trang, trạng thái lỗi/empty/loading.
- Build production và browser test đạt.
- Đã bổ sung rotate API key, reset session, UI sửa role/password, xuất từ điển, chấm/xuất QA, audit filter và model canary/promote/rollback. Nợ kỹ thuật còn lại: hai cảnh báo Fast Refresh không chặn build.

### Hạ tầng

- Dockerfile/compose và `.env.example` đã có.
- Máy đo: Windows, Python 3.10.11, PyTorch 2.7.1+cu118, NVIDIA GeForce RTX 3050 Laptop GPU 6 GB.
- Model NLLB chạy từ cache cục bộ; benchmark không tải dữ liệu bên ngoài.

## 4. Backlog và ma trận truy vết

| Yêu cầu | Thành phần | Chứng thực | Trạng thái 24/09 |
|---|---|---|---|
| Xác thực và RBAC | Backend + Admin | 121 backend tests; route guard | Đạt kỹ thuật |
| Users/API Keys | Admin API/UI | API tests + browser tests | Tạo/sửa/vô hiệu/reset session/rotate/revoke đạt |
| Dashboard/Analytics | Admin API/UI + telemetry | Build + browser tests + telemetry tests | Đạt kỹ thuật |
| Dictionary/TM | Backend + Admin | Regression, isolation/cache/fuzzy tests | Engine đạt; accuracy thuật ngữ benchmark 74,29% chưa đạt KPI |
| History/QA | Backend + Admin | Browser test và API test | Có adequacy/fluency/error taxonomy/export; người thật chưa điền phiếu |
| Chuẩn hóa văn bản | Backend | Unit/regression tests | Đạt |
| Hiệu năng suy luận | NLLB/GPU | 500 câu + A/B/soak + full pipeline | Đã có baseline/profile; chưa phải capacity production |
| Flutter | Flutter | `flutter analyze --no-pub` | Đạt, không phát hiện lỗi |
| Chất lượng STT/TTS | Audio pipeline | 100 audio sạch/nhiễu | Đã đo WER/latency; MOS vẫn chờ người nghe |

## 5. User flow và wireframe admin

### Luồng chính

1. Người dùng vào `/login`, nhập thông tin và OTP nếu chính sách yêu cầu.
2. Route guard lấy `/admin/me`, kiểm tra phiên và role.
3. Admin/Reviewer xem Dashboard, Analytics, History và QA.
4. Superadmin quản lý Users, API Keys, Dictionary và Settings.
5. Mọi request lỗi hiển thị thông báo; token hết hạn đưa về Login; hành động phá hủy yêu cầu xác nhận.

### Wireframe văn bản

```text
+---------------- Sidebar ----------------+------------- Main ------------------+
| Logo / tài khoản                        | Tiêu đề + mô tả                     |
| Dashboard                               | Bộ lọc / tìm kiếm / hành động       |
| Analytics                               | KPI cards / chart / table           |
| History                                 | Loading / empty / error / content   |
| Dictionary / QA                         | Phân trang + thông báo kết quả      |
| Users / API Keys / Settings (theo role) |                                      |
+-----------------------------------------+--------------------------------------+
```

Quy tắc UI: ưu tiên responsive; focus bàn phím rõ; label gắn với input; không hiển thị số liệu giả khi API lỗi; secret chỉ hiển thị một lần.

## 6. Kiến trúc mục tiêu và hợp đồng tích hợp

```text
Flutter / React Admin
        |
 REST + authenticated WebSocket
        |
 FastAPI boundary -> Auth/RBAC/Rate limit
        |
 Session actor -> VAD -> STT queue -> Translation queue -> TTS queue
                          |              |
                    Telemetry       TM + bounded cache
                          |              |
                    Admin metrics    SQLite/PostgreSQL target
```

### Quy tắc API

- REST dùng `Authorization: Bearer <token>`; browser WebSocket gửi token một lần trong frame `config`.
- Mã lỗi: 401 chưa xác thực/hết hạn; 403 thiếu quyền; 413 quá kích thước; 422 dữ liệu sai; 429 quá tải/rate limit; 503 phụ thuộc chưa sẵn sàng.
- WebSocket: `config → start_turn → audio frames → end_turn/cancel_turn`; server trả `stt`, `translation`, `audio_chunk`, `turn_complete` hoặc `error`.
- Identity không được thay đổi giữa phiên; message có `turn_id` để lọc kết quả muộn và chống lẫn lượt.
- Route inventory đầy đủ nằm trong `.phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json`.

## 7. Thiết kế benchmark và baseline

### Bộ benchmark đã chạy

- Pilot 30 câu được giữ làm baseline ban đầu.
- Benchmark v2 gồm 500 câu: 250 Việt→Anh, 250 Anh→Việt, cân bằng 10 domain; 100 audio gồm 50 sạch và 50 nhiễu 15 dB.
- Mỗi dòng lưu nguồn, tham chiếu, hypothesis, latency và thuật ngữ bắt buộc.
- Kết quả chi tiết: `evidence/translation_benchmark_v2_cases.csv`, `evidence/speech_benchmark_v2_cases.csv`.
- Kết quả tổng hợp: `evidence/translation_benchmark_v2_summary.json`, `evidence/speech_benchmark_v2_summary.json`, `evidence/full_pipeline_benchmark_summary.json`.

### Giới hạn bắt buộc công bố

- 500 câu là corpus template có kiểm soát, chưa đại diện dữ liệu tự nhiên production.
- Một tham chiếu/câu có thể phạt các cách diễn đạt đúng khác.
- Đã đo WER/audio nhiễu; chưa có TTS MOS, audio người thật, network và tải đồng thời production.
- Điểm token-F1/character similarity không tương đương BLEU/COMET hoặc đánh giá con người.

## 8. Quy trình đánh giá con người

Mỗi câu cần hai người chấm độc lập, ẩn tên model:

- Adequacy 1–5: giữ đủ và đúng nghĩa.
- Fluency 1–5: tự nhiên, đúng ngữ pháp.
- Lỗi: none, omission, addition, mistranslation, terminology, entity/number, grammar, style.
- Lỗi nghiêm trọng: thay đổi ý định, tên riêng, số tiền, thời gian hoặc chỉ dẫn an toàn.
- Khi chênh điểm lớn hơn 1, hai người thảo luận và ghi điểm quyết định.

Phiếu 100 case × 2 reviewer, đã điền source/reference/hypothesis, nằm tại `evidence/human_evaluation_v2_two_reviewers.csv`. Không ghi điểm thay cho người đánh giá.

## 9. Definition of Done tại mốc 24/09

- Đạt kỹ thuật: 121 backend test, 21 browser test, admin build/lint, regression 7/7, corpus 500 câu, 100 audio, benchmark/profile/A-B/soak và raw evidence.
- Đạt có điều kiện: baseline đã đủ quy mô kế hoạch nhưng accuracy thuật ngữ và WER còn dưới quality gate.
- Chưa đạt: hai người chấm/ký, TTS MOS và capacity test production.


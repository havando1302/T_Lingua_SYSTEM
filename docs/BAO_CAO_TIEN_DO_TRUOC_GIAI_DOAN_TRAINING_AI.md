# BÁO CÁO TIẾN ĐỘ DỰ ÁN T-LINGUA

## Giai đoạn từ hình thành ý tưởng đến trước khi xây dựng chức năng Training AI

**Thời gian được chứng thực:** 25/08/2026–25/09/2026  
**Mốc kết thúc phạm vi:** Trước ngày 30/09/2026, khi mã nguồn Training Center, Training API và Training Worker lần đầu xuất hiện trong lịch sử Git.  
**Thành viên:** Hà Văn Đô, Nguyễn Quang Thọ  
**Dự án:** Hệ thống AI dịch thuật thời gian thực T-Lingua

> Báo cáo này mô tả giai đoạn xây dựng nền tảng, ứng dụng dịch, trang quản trị, quy trình QA và chuẩn bị dữ liệu trước khi triển khai chức năng huấn luyện AI. Báo cáo không tính phần Training Center, Training Worker hoặc quy trình fine-tuning sau ngày 30/09/2026 là kết quả của giai đoạn này.

## 1. Mục tiêu ban đầu

Ý tưởng của T-Lingua là xây dựng một hệ thống hỗ trợ dịch Việt–Anh và Anh–Việt theo thời gian thực, phục vụ cả văn bản và hội thoại giọng nói. Hệ thống được định hướng gồm ba thành phần chính:

1. Ứng dụng Flutter dành cho người dùng cuối, hỗ trợ microphone, phát âm thanh bản dịch, lịch sử và cài đặt.
2. Backend FastAPI/WebSocket chịu trách nhiệm xác thực, nhận âm thanh, nhận dạng giọng nói, dịch văn bản, tổng hợp giọng nói và quản lý dữ liệu.
3. Trang quản trị React dùng để theo dõi hoạt động, quản lý người dùng, API key, từ điển, lịch sử, QA và cấu hình hệ thống.

Trong giai đoạn đầu, nhóm không đặt mục tiêu huấn luyện foundation model từ đầu. Hướng tiếp cận là sử dụng các model có sẵn làm baseline, đo chất lượng thực tế, thu thập và chuẩn hóa dữ liệu, sau đó mới xem xét fine-tuning trên dữ liệu phù hợp.

## 2. Phạm vi MVP trước Training AI

Các chức năng được xác định trong phạm vi gồm:

- Dịch văn bản Việt–Anh và Anh–Việt.
- Hội thoại giọng nói theo pipeline VAD → STT → dịch → TTS.
- Truyền âm thanh và kết quả theo thời gian thực qua WebSocket.
- Quản lý từng lượt nói bằng `turn_id`, chống lẫn kết quả cũ và kết quả đến muộn.
- Translation Memory, cache và từ điển thuật ngữ.
- Xác thực session/JWT, API key, phân quyền vai trò và giới hạn tần suất.
- Ứng dụng Flutter và trang quản trị React.
- Thu thập log dịch, đánh dấu bản dịch chưa tốt và chuẩn bị quy trình QA.
- Xây dựng corpus thử nghiệm, benchmark và biểu mẫu đánh giá con người.

Các nội dung chưa thuộc giai đoạn này:

- Training Center trên giao diện quản trị.
- Training API và worker chạy job huấn luyện.
- Fine-tuning Whisper hoặc NLLB trên dữ liệu dự án.
- Huấn luyện foundation model từ đầu.
- Triển khai production đa vùng hoặc cam kết SLA production.

## 3. Quá trình triển khai

### 3.1. Khởi tạo và đánh giá nền tảng

Nhóm bắt đầu bằng việc rà soát nền tảng Flutter–FastAPI/WebSocket–React Admin đã có, xác định phạm vi MVP, trách nhiệm thành viên, Definition of Done và các luồng người dùng chính.

Inventory kỹ thuật ghi nhận:

- 227 tệp nguồn thuộc phạm vi rà soát.
- 45 route/API làm mốc đối chiếu.
- Có ma trận truy vết giữa yêu cầu, thành phần và bằng chứng kiểm thử.

Definition of Done yêu cầu mã nguồn được kiểm tra, test liên quan đạt, không còn lỗi P0/P1 đã biết, có bằng chứng tái lập và không đưa secret hoặc dữ liệu cá nhân vào artifact.

### 3.2. Xây dựng backend và pipeline AI

Backend được tổ chức quanh FastAPI, REST và WebSocket. Pipeline dịch giọng nói gồm:

```text
Microphone → WebSocket → VAD → STT → NLLB → TTS → phát âm thanh
```

Các thành phần đã có trước giai đoạn Training AI:

- VAD và tiền xử lý âm thanh.
- Hàng đợi riêng cho STT, dịch và TTS.
- Quản lý session và trạng thái từng lượt nói.
- Telemetry theo từng chặng xử lý.
- Queue/backpressure và giới hạn tài nguyên.
- Translation Memory theo owner và chiều ngôn ngữ.
- Cache có version và cơ chế invalidation.
- Chuẩn hóa dấu câu, số, tên riêng và xử lý một số trường hợp hallucination.

Model NLLB được dùng để thiết lập baseline dịch. Model giọng nói và TTS được dùng để đánh giá pipeline, không được tuyên bố là model đã được dự án huấn luyện.

### 3.3. Xây dựng ứng dụng Flutter

Ứng dụng người dùng đã có các luồng chính:

- Chọn ngôn ngữ nguồn và đích.
- Bắt đầu/dừng microphone.
- Nhận kết quả nhận dạng, bản dịch và âm thanh TTS.
- Hiển thị trạng thái kết nối và lỗi.
- Lưu lịch sử và cấu hình người dùng.
- Quản lý state của microphone, WebSocket và audio player.

Kết quả `flutter analyze --no-pub` tại mốc kiểm tra là **No issues found**.

### 3.4. Xây dựng trang quản trị trước Training Center

Trang quản trị đã hoàn thiện các khu vực:

- Login và route guard theo vai trò.
- Dashboard và Analytics.
- Users và quản lý trạng thái tài khoản.
- API Keys.
- Dictionary và Translation Memory.
- History và Quality Assurance.
- Settings, cấu hình model active/canary và rollback.
- Audit log.

Giao diện hỗ trợ tìm kiếm, phân trang, trạng thái loading/empty/error, responsive và kiểm soát quyền theo vai trò. Secret API key chỉ được hiển thị tại thời điểm tạo.

Ở giai đoạn này chưa có trang Training Center. Trang quản trị mới đóng vai trò quan sát hệ thống, thu thập phản hồi QA, quản lý dữ liệu và cấu hình model.

### 3.5. Hoàn thiện bảo mật và ranh giới dữ liệu

Các biện pháp đã được triển khai gồm:

- Session/JWT và API key có scope.
- RBAC cho employee, admin và superadmin.
- Rate limit và giới hạn payload.
- Kiểm soát CORS và trusted host.
- Cách ly dữ liệu theo owner.
- Không cho phép thay đổi identity giữa một WebSocket session.
- Kiểm soát quyền trên các API quản trị và realtime.
- Audit các hành động quản trị quan trọng.

## 4. Chuẩn bị dữ liệu cho giai đoạn Training AI

### 4.1. Baseline ban đầu

Nhóm bắt đầu bằng một bộ pilot gồm 30 câu hai chiều Việt–Anh. Mục tiêu của bộ này là kiểm tra khả năng chạy model, cách đo latency và quy trình lưu source, reference và hypothesis.

Pilot chỉ được xem là mốc kỹ thuật ban đầu, không được dùng để kết luận chất lượng production.

### 4.2. Corpus dịch v2

Corpus v2 được mở rộng thành 500 trường hợp:

- 250 câu Việt → Anh.
- 250 câu Anh → Việt.
- Phân bố trên 10 nhóm lĩnh vực.
- Mỗi dòng lưu câu nguồn, câu tham chiếu, kết quả model, latency và thuật ngữ bắt buộc.
- Dataset và metadata được lưu kèm thông tin phiên bản và SHA-256.

Đây là corpus template có kiểm soát, phù hợp cho benchmark và thử nghiệm quy trình. Nó chưa thay thế được corpus tự nhiên, có giấy phép và đại diện cho dữ liệu người dùng thực tế.

### 4.3. Corpus âm thanh

Bộ đánh giá giọng nói gồm 100 mẫu:

- 50 mẫu sạch.
- 50 mẫu được thêm nhiễu Gaussian ở mức 15 dB.

Audio được tạo tổng hợp bằng TTS, vì vậy chưa đại diện đầy đủ cho giọng người thật, vùng miền, microphone, phòng họp hoặc tiếng ồn thực tế.

### 4.4. Chuẩn bị đánh giá con người

Nhóm đã chuẩn bị biểu mẫu 100 trường hợp cho hai reviewer độc lập. Các trường đánh giá gồm:

- Adequacy từ 1 đến 5.
- Fluency từ 1 đến 5.
- Loại lỗi: thiếu ý, thêm ý, dịch sai, thuật ngữ, tên/số, ngữ pháp và phong cách.
- Đánh dấu lỗi nghiêm trọng.

Biểu mẫu đã được tạo nhưng chưa được hai reviewer hoàn tất và ký xác nhận tại mốc báo cáo. AI không được dùng để giả lập kết quả đánh giá của con người.

### 4.5. Trạng thái sẵn sàng dữ liệu

| Nội dung | Trạng thái trước Training AI |
|---|---|
| Corpus benchmark 500 câu | Đã có |
| Audio sạch/nhiễu 100 mẫu | Đã có |
| Version và SHA-256 | Đã có |
| Phiếu đánh giá hai reviewer | Đã chuẩn bị, chưa chấm xong |
| Corpus tự nhiên có giấy phép | Chưa đủ |
| Audio người thật, accent và môi trường thật | Chưa đủ |
| TTS MOS từ người nghe độc lập | Chưa thực hiện |
| Dữ liệu đủ điều kiện để tuyên bố production | Chưa đạt |

## 5. Kết quả kiểm thử và benchmark tại mốc trước Training AI

### 5.1. Kiểm thử phần mềm

| Hạng mục | Kết quả |
|---|---:|
| Backend automated tests | 121/121 đạt |
| Admin browser tests | 21/21 đạt |
| Admin production build | Đạt |
| Admin lint | Đạt, còn 2 cảnh báo không chặn |
| Flutter static analysis | Đạt, không phát hiện lỗi |
| Regression độc lập | 7/7 đạt |

### 5.2. Benchmark dịch NLLB

Benchmark được chạy local trên NVIDIA GeForce RTX 3050 Laptop GPU 6 GB với model `facebook/nllb-200-distilled-1.3B`.

| Chỉ số | Kết quả |
|---|---:|
| Số trường hợp | 500 |
| Thời gian tải model | 14,996 giây |
| Latency trung bình | 483,109 ms |
| p50 | 450,364 ms |
| p95 | 743,579 ms |
| p99 | 853,838 ms |
| BLEU có smoothing | 56,925 |
| chrF trung bình | 74,867 |
| Token-F1 trung bình | 0,7871 |
| Đúng thuật ngữ bắt buộc | 650/875 = 74,29% |
| Đỉnh bộ nhớ GPU | 2.633,98 MB |

Kết quả cho thấy tốc độ local khả quan nhưng độ chính xác thuật ngữ 74,29% chưa đạt mục tiêu 95%. Đây là một trong các lý do chính để chuẩn bị dữ liệu domain và cân nhắc fine-tuning ở giai đoạn sau.

### 5.3. Benchmark giọng nói

| Chỉ số | Kết quả |
|---|---:|
| Số audio | 100 |
| STT p95 | 480,455 ms |
| TTS p95 | 262,273 ms |
| WER tổng | 39,68% |
| WER audio sạch | 39,03% |
| WER audio nhiễu | 40,33% |
| Realtime factor trung bình | 0,0786 |

WER còn cao và bộ audio là dữ liệu tổng hợp. Do đó chưa đủ cơ sở để bắt đầu huấn luyện production nếu chưa bổ sung audio người thật và quy trình gắn nhãn.

### 5.4. A/B và soak test

- Beam 1: p95 767,597 ms.
- Beam 3: p95 983,532 ms.
- Chất lượng chrF gần tương đương, nên beam 1 được chọn làm cấu hình baseline.
- Soak test hoàn thành 200/200 lượt.
- Không xảy ra OOM.
- Mức tăng bộ nhớ ghi nhận: 0 MB.

### 5.5. Hiệu năng API quản trị

TestClient với SQLite in-memory được chạy trên 5.001 user và 20.000 translation log:

| API | p95 |
|---|---:|
| Dashboard | 15,650 ms |
| Trang QA 100 dòng | 20,135 ms |
| Trang Users 100 dòng | 18,108 ms |

Đây là benchmark trong tiến trình, không bao gồm network, TLS, nhiều worker hoặc cơ sở dữ liệu production.

## 6. Mức độ hoàn thành trước khi chuyển sang Training AI

### Đã hoàn thành

- Kiến trúc ứng dụng Flutter–FastAPI/WebSocket–React Admin.
- Pipeline STT–dịch–TTS cơ bản.
- Ứng dụng người dùng và các trang quản trị MVP.
- Xác thực, phân quyền, rate limit và cách ly dữ liệu.
- Translation Memory, cache và từ điển.
- Quy trình QA và biểu mẫu đánh giá.
- Corpus benchmark 500 câu và 100 audio tổng hợp.
- Benchmark chất lượng, hiệu năng, A/B và soak.
- Bộ kiểm thử tự động và bằng chứng tái lập.

### Chưa hoàn thành tại mốc này

- Chưa xây dựng Training Center.
- Chưa có API hoặc worker thực hiện fine-tuning.
- Chưa có pipeline dataset → train → evaluate → register → deploy.
- Chưa hoàn tất đánh giá của hai reviewer.
- Chưa có đủ corpus tự nhiên có giấy phép và audio người thật.
- Chưa đo TTS MOS.
- Chưa chứng minh capacity production hoặc SLA end-to-end.

## 7. Rủi ro trước khi bắt đầu huấn luyện

1. **Dữ liệu chưa đủ đại diện:** corpus template và audio tổng hợp có thể tạo ra kết quả tốt trong benchmark nhưng không phản ánh người dùng thật.
2. **Thuật ngữ chưa đạt KPI:** mức 74,29% cho thấy cần tiếp tục làm sạch glossary và dữ liệu domain.
3. **WER còn cao:** cần thu thập audio thật, nhiều accent, thiết bị và điều kiện tiếng ồn.
4. **Quyền sử dụng dữ liệu:** mọi dữ liệu đưa vào huấn luyện phải có nguồn gốc, giấy phép, consent và quy tắc loại bỏ PII rõ ràng.
5. **Đánh giá chưa độc lập:** cần hai reviewer hoàn tất adequacy, fluency và lỗi nghiêm trọng trước khi dùng dữ liệu làm ground truth.
6. **Giới hạn GPU 6 GB:** cần lựa chọn LoRA/PEFT, batch size, gradient accumulation và checkpoint phù hợp; chưa nên huấn luyện toàn bộ model 1,3B theo cách không giới hạn.

## 8. Điều kiện đề xuất để bắt đầu giai đoạn Training AI

Chỉ nên chuyển sang triển khai Training Center và fine-tuning khi đáp ứng tối thiểu:

- Chốt schema dataset và quy tắc train/validation/test.
- Có data lineage, version, checksum và quyền sử dụng cho từng nguồn.
- Hoàn tất loại bỏ hoặc kiểm soát PII.
- Hai reviewer hoàn thành đánh giá độc lập.
- Xác định KPI trước/sau training: BLEU, chrF, COMET hoặc human score cho dịch; WER cho STT.
- Có baseline cố định để tránh đánh giá sai cải thiện.
- Thiết kế rollback và không tự động đưa model mới lên production.
- Job training chạy tách biệt khỏi inference để tránh tranh chấp GPU.

## 9. Kết luận

Trước khi xây dựng phần Training AI, T-Lingua đã hoàn thành phần lớn nền tảng cần thiết: ứng dụng người dùng, backend realtime, trang quản trị, bảo mật, QA, Translation Memory, corpus thử nghiệm và benchmark. Giai đoạn này đã chuyển dự án từ một ý tưởng dịch thuật sang một hệ thống có thể chạy, đo và kiểm thử được.

Tuy nhiên, kết quả cũng chỉ ra rõ rằng dữ liệu chưa đủ đại diện để tuyên bố sẵn sàng huấn luyện production. Độ chính xác thuật ngữ 74,29%, WER gần 40%, thiếu audio người thật và đánh giá reviewer chưa hoàn tất là các khoảng trống cần xử lý. Vì vậy, Training AI nên được coi là giai đoạn tiếp theo dựa trên dữ liệu và quality gate, không phải bước triển khai giao diện đơn thuần.

## 10. Nguồn chứng thực

- `docs/progress_2026-09-24/PROJECT_ARTIFACTS.md`
- `docs/progress_2026-09-24/evidence/verification_summary.json`
- `docs/progress_2026-09-24/evidence/translation_benchmark_v2_summary.json`
- `docs/progress_2026-09-24/evidence/speech_benchmark_v2_summary.json`
- `docs/progress_2026-09-24/evidence/inference_ab_soak_summary.json`
- `docs/progress_2026-09-24/evidence/admin_api_large_dataset_benchmark.json`
- `.phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json`
- `.phase1-artifacts/progress_2026-09-24/regression_results_v3.json`

### Ghi chú về tính toàn vẹn thời gian

- Artifact benchmark và verification được tạo vào đêm 24/09 theo UTC, tương ứng ngày 25/09 theo múi giờ Việt Nam.
- Lịch sử Git hiện tại ghi nhận Training Center, Training API và Training Worker xuất hiện trong commit ngày 30/09/2026 với tổng cộng 1.534 dòng thêm ở bốn tệp chính.
- File full-pipeline benchmark hiện có timestamp ngày 02/10/2026 nên không được sử dụng làm số liệu của báo cáo lịch sử trước Training AI này.
- Tại thời điểm artifact cũ được tạo, worktree còn thay đổi chưa commit; vì vậy Git không thể chứng minh chính xác tác giả và ngày hoàn thành của từng thay đổi nhỏ. Báo cáo chỉ sử dụng các mốc và số liệu có artifact đối chiếu được.

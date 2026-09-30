# Kịch bản báo cáo tiến độ dự án AI dịch thuật — bản hoàn thiện kỹ thuật

**Giai đoạn báo cáo:** 25/08/2026–24/09/2026  
**Ngày rà soát và hoàn thiện bù:** 25/09/2026  
**Thành viên:** Hà Văn Đô, Nguyễn Quang Thọ  
**Thời lượng đề xuất:** 10–12 phút

> Nguyên tắc trình bày: phân biệt rõ kết quả có tại mốc 24/09 với phần remediation ngày 25/09. Không đổi ngày artifact hoặc tuyên bố đánh giá người thật khi hai thành viên chưa chấm và ký.

## 1. Mở đầu — 45 giây

“Kính thưa thầy/cô và các anh/chị. Trong giai đoạn từ 25 tháng 8 đến hết 24 tháng 9, nhóm tập trung đánh giá nền Flutter–FastAPI/WebSocket–React Admin đã có, hoàn thiện quản trị và bảo mật, đồng thời đo chất lượng và tốc độ bằng model thật. Sau khi đối chiếu ngày 25 tháng 9, nhóm đã hoàn thiện các hạng mục kỹ thuật còn thiếu và lưu toàn bộ bằng chứng tái lập.”

## 2. Làm được những gì? — 3 phút

“Về quản trị dự án, nhóm đã hoàn thiện phạm vi MVP, RACI, Definition of Done, backlog, ma trận truy vết, luồng người dùng và hợp đồng API.

Về admin web, nhóm hoàn thiện Login, Dashboard, Analytics, Users, API Keys, Dictionary, History, QA và Settings. Users hỗ trợ tạo, sửa role, đặt lại mật khẩu, khóa/mở và thu hồi phiên. API key hỗ trợ tạo, che secret, thu hồi và rotate. Settings có cấu hình model active–canary, promote, rollback theo version và audit. Audit có thể lọc theo người thực hiện, hành động, loại đối tượng và thời gian.

Về backend, nhóm hoàn thiện RBAC, session/JWT, API key scopes, rate limit, kiểm soát payload, cách ly owner, structured QA và export. Lỗi `CancelledError` khi đóng WebSocket đã được sửa bằng cách hủy và chờ sender task kết thúc.

Về chất lượng dịch, Translation Memory đã có exact match và fuzzy match theo đúng chiều ngôn ngữ, ngưỡng chống match mơ hồ, version và cache invalidation. Corpus v2 gồm 500 câu, 10 miền nghiệp vụ và 100 audio sạch/nhiễu đã được tạo có version và SHA-256.

Về hiệu năng, nhóm đã đo API trên 20.000 translation log và 5.001 user; chạy benchmark 500 câu, benchmark 100 audio, pipeline STT–NLLB–TTS, A/B beam 1–3, cProfile và soak 200 lượt.”

## 3. Chứng thực ở đâu? — 2 phút

“Bằng chứng được chia thành năm lớp:

Một là inventory 227 tệp nguồn và 45 route tại `.phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json`.

Hai là regression 7 trên 7 tại `.phase1-artifacts/progress_2026-09-24/regression_results_v3.json`.

Ba là log backend test, admin build, lint và browser test trong `docs/progress_2026-09-24/evidence`. Lần chạy cuối đạt 121/121 backend test và 21/21 browser test; admin build và lint đạt, lint còn hai cảnh báo không chặn.

Bốn là dữ liệu thô từng câu/từng audio, summary JSON và SHA-256 của corpus v2 trong cùng thư mục evidence.

Năm là profile `admin_api_profile.prof`, `full_pipeline_profile.prof` và bản đọc dạng text. Các script tạo dữ liệu và chạy benchmark nằm trong thư mục `scripts`, vì vậy có thể chạy lại.”

## 4. Số liệu thực nghiệm — 3 phút

“Benchmark dịch v2 chạy đủ 500 câu, gồm 250 câu Việt–Anh và 250 câu Anh–Việt trên RTX 3050 6 GB. Latency trung bình là 483,109 mili giây; p50 là 450,364; p95 là 743,579 và p99 là 853,838 mili giây. BLEU có smoothing đạt 56,925; chrF trung bình 74,867; token-F1 0,7871. Độ đúng thuật ngữ là 650 trên 875, tương đương 74,29 phần trăm. Con số này chưa đạt KPI 95 phần trăm.

Benchmark giọng nói gồm 100 audio: 50 sạch và 50 thêm nhiễu Gaussian 15 dB. STT p95 là 480,455 mili giây, RTF trung bình 0,0786. WER sạch là 39,03 phần trăm và WER nhiễu là 40,33 phần trăm; đây là quality gap cần tiếp tục xử lý. TTS p95 là 262,273 mili giây.

Pipeline warm local STT–NLLB–TTS chạy 10 lượt có p95 end-to-end 1.175,470 mili giây; throughput tuần tự 1,036 lượt/giây; đỉnh GPU 3.306 MB. Số này không gồm network và queue.

A/B cho thấy beam 1 có p95 767,597 mili giây, nhanh hơn beam 3 là 983,532 mili giây, trong khi chrF gần tương đương; vì vậy chọn beam 1. Soak 200 trên 200 lượt hoàn tất, không OOM và memory growth bằng 0 MB.

API admin với 20.000 log có dashboard p95 15,650 mili giây; trang QA 100 dòng p95 20,135 mili giây; trang Users p95 18,108 mili giây. Đây là TestClient và SQLite in-memory, không phải capacity production.”

## 5. Tiến độ và phần còn chờ — 1 phút

“Sau remediation, 28 trên 29 công việc đến hạn 24/09 đã hoàn thành kỹ thuật. Mục UI Settings/Models/Audit đến hạn 25/09 cũng đã hoàn thành. Chỉ còn hạng mục đánh giá độc lập: phiếu đã lấy mẫu 100 case cho hai reviewer, nhưng Hà Văn Đô và Nguyễn Quang Thọ phải tự chấm adequacy, fluency, lỗi nghiêm trọng và ký xác nhận. Nhóm không dùng AI để giả mạo đánh giá người thật.

Các công việc có ngày bắt đầu hoặc deadline sau 25/09 được ghi là ‘Chưa đến hạn’, không phải trễ tiến độ. Flutter analyzer ban đầu treo vì sandbox chặn cache AppData; sau khi cấp quyền cache phù hợp, kết quả là `No issues found!`.”

## 6. Rủi ro và quyết định — 1 phút

- Accuracy thuật ngữ 74,29% chưa đạt KPI 95%: ưu tiên glossary theo domain, entity/number preservation và chạy lại quality gate.
- WER 39,68% trên audio tổng hợp còn cao: bổ sung audio người thật, accent và môi trường nhiễu thực tế.
- Corpus v2 là template có kiểm soát: cần bổ sung corpus tự nhiên có giấy phép trước nghiệm thu production.
- Beam 1 được chọn vì giảm p95 khoảng 22% so với beam 3 trong mẫu A/B mà chrF gần như không đổi.
- GPU 6 GB: giữ concurrency limit, backpressure và theo dõi memory; không suy rộng soak 200 lượt thành tải production nhiều giờ.
- Worktree chưa sạch: cần commit/tag/review để chứng minh tác giả và thời điểm thay đổi.

## 7. Kết luận — 30 giây

“Kết luận, nhóm đã hoàn thiện phần kỹ thuật còn thiếu, có admin web đầy đủ hơn, model control plane có rollback, Translation Memory fuzzy, corpus 500 câu, 100 audio và số liệu pipeline thật. Kết quả chứng minh tốc độ local tốt hơn baseline nhỏ nhưng đồng thời chỉ ra hai quality gap là thuật ngữ và WER. Bước xác nhận cuối của giai đoạn là hai thành viên hoàn thành và ký phiếu đánh giá độc lập.”

## 8. Bảng số liệu trình chiếu

| Chỉ số | Kết quả | Nguồn |
|---|---:|---|
| Inventory | 227 tệp, 45 route | `inventory_baseline_v4/report.json` |
| Regression | 7/7 đạt | `regression_results_v3.json` |
| Backend test | 121/121 đạt | `verification_summary.json` |
| Admin browser test | 21/21 đạt | `verification_summary.json` |
| Benchmark dịch v2 | 500/500 case | `translation_benchmark_v2_summary.json` |
| NLLB p50 / p95 / p99 | 450,364 / 743,579 / 853,838 ms | Cùng file summary |
| BLEU / chrF | 56,925 / 74,867 | Cùng file summary |
| Accuracy thuật ngữ | 650/875 = 74,29% | Cùng file summary |
| Audio benchmark | 100 mẫu | `speech_benchmark_v2_summary.json` |
| WER sạch / nhiễu | 39,03% / 40,33% | Cùng file summary |
| Pipeline p95 | 1.175,470 ms | `full_pipeline_benchmark_summary.json` |
| Soak | 200/200, không OOM, +0 MB | `inference_ab_soak_summary.json` |
| Dashboard API p95 | 15,650 ms | `admin_api_large_dataset_benchmark.json` |
| QA API p95 | 20,135 ms | Cùng file summary |
| Flutter analyze | Đạt, không phát hiện lỗi | `verification_summary.json` |

## 9. Câu hỏi phản biện

**Tại sao công việc đã hoàn thành nhưng KPI vẫn chưa đạt?**  
Hoàn thành công việc baseline nghĩa là đã có corpus, phép đo và báo cáo tái lập. Kết quả phép đo có thể cho thấy quality gate chưa đạt; đây là dữ liệu để ưu tiên tối ưu, không phải lý do sửa số liệu.

**p95 1.175 ms có phải SLA production không?**  
Không. Đây là 10 lượt warm local, không có network và queue. Nó chứng minh critical path trên máy thử, không chứng minh capacity production.

**Vì sao chưa đóng 100%?**  
Một hạng mục yêu cầu hai con người chấm độc lập và ký. Phiếu đã sẵn sàng nhưng AI không được tự nhận là reviewer người thật.

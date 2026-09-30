# Kịch bản báo cáo tiến độ dự án AI dịch thuật

Thời gian báo cáo: 25/08/2026–24/09/2026  
Thành viên: Hà Văn Đô, Nguyễn Quang Thọ  
Thời lượng trình bày đề xuất: 10–12 phút

> Lưu ý trung thực về mốc thời gian: báo cáo mô tả trạng thái tại cutoff 24/09 và kết quả hoàn thiện bù được thực hiện khi rà soát ngày 25/09. Khi trình bày, không nói các hạng mục “hoàn thiện bù” đã xong trước deadline nếu Git/biên bản không chứng minh được.

## 1. Mở đầu — 45 giây

“Kính thưa thầy/cô và các anh/chị. Trong giai đoạn từ ngày 25 tháng 8 đến hết ngày 24 tháng 9 năm 2026, nhóm tập trung vào bốn mục tiêu: đánh giá lại nền tảng cũ, hoàn thiện hệ thống quản trị, củng cố bảo mật và độ ổn định, đồng thời tạo baseline thực nghiệm cho chất lượng và tốc độ dịch. Nhóm không xây lại toàn bộ frontend/backend mà tối ưu trên nền Flutter, FastAPI/WebSocket và React Admin đã có.”

## 2. Làm được những gì? — 3 phút

“Thứ nhất, về quản lý và kiến trúc, nhóm đã lập phạm vi MVP, RACI, Definition of Done, ma trận truy vết, luồng người dùng admin và sơ đồ kiến trúc. Công cụ inventory đã chụp 227 tệp nguồn thuộc phạm vi cho phép và nhận diện 45 route để làm mốc đối chiếu.

Thứ hai, về backend và bảo mật, hệ thống hiện có session/JWT, API key, phân quyền theo vai trò, rate limit, kiểm soát CORS/host, giới hạn payload và cách ly dữ liệu theo owner. Pipeline realtime sử dụng turn ID, session state, VAD, các hàng đợi STT–dịch–TTS, cache và Translation Memory.

Thứ ba, về admin web, nhóm đã hoàn thiện các màn hình Login, Dashboard, Analytics, Users, API Keys, Dictionary, History, QA và Settings. Giao diện có route guard theo role, tìm kiếm, phân trang, trạng thái loading/empty/error và xử lý responsive. Sau khi rà soát mốc 24/09, nhóm hoàn thiện bù reset phiên người dùng, rotate API key, xuất từ điển, chấm adequacy/fluency, phân loại lỗi, xuất QA và nhật ký audit; các phần này phải được ghi nhận là remediation ngày 25/09.

Thứ tư, về chất lượng dịch, nhóm bổ sung chuẩn hóa dấu câu, giữ dấu phẩy thập phân, xử lý hallucination, cô lập Translation Memory theo chiều ngôn ngữ và owner, cache có version/invalidation, VAD giới hạn bộ nhớ và chia đoạn TTS.

Thứ năm, khi kiểm tra toàn bộ hệ thống, nhóm phát hiện một lỗi `CancelledError` lúc đóng WebSocket. Nhóm đã sửa cleanup để hủy và chờ sender task kết thúc, sau đó chạy lại toàn bộ test thành công.”

## 3. Chứng thực bằng gì? — 2 phút

“Nhóm sử dụng bốn lớp chứng thực.

Một là snapshot inventory có hash SHA-256, lưu tại `.phase1-artifacts/progress_2026-09-24/inventory_baseline_v4/report.json`. Snapshot ghi nhận source, route, môi trường và trạng thái Git nhưng không thu thập secret.

Hai là bộ regression độc lập gồm 7 probe cho các lỗi chất lượng và ranh giới quyền. Kết quả 7 trên 7 đạt, lưu tại `.phase1-artifacts/progress_2026-09-24/regression_results_v3.json`.

Ba là kiểm thử tự động. Backend chạy 119 test và đạt 119; admin build production thành công; lint đạt với hai cảnh báo không chặn; browser test đạt 19 trên 19. File tổng hợp và log nằm trong thư mục `docs/progress_2026-09-24/evidence`.

Bốn là benchmark model thật. Model `facebook/nllb-200-distilled-1.3B` chạy local-only trên RTX 3050, không gọi dịch vụ bên ngoài. Từng câu nguồn, câu tham chiếu, kết quả dịch và latency đều có trong CSV để kiểm tra lại.”

## 4. Số liệu thực nghiệm như thế nào và ở đâu? — 2 phút

“Với 30 câu thử nghiệm hai chiều Việt–Anh, thời gian nạp model là 20,927 giây. Latency suy luận trung bình là 553,228 mili giây; p50 là 438,622 mili giây; p95 là 789,233 mili giây; p99 là 2.639,994 mili giây. Mẫu nhanh nhất là 271,574 mili giây và chậm nhất là 3.384,371 mili giây. Đỉnh bộ nhớ GPU được ghi nhận là 2.633,69 MB.

Về chất lượng tự động, character similarity trung bình đạt 0,8575; token-F1 đạt 0,8108; thuật ngữ bắt buộc đúng 21 trên 23, tương đương 91,3 phần trăm.
Với kiểm thử phần mềm, backend đạt 119 trên 119 test trong 32,097 giây theo test runner. Bộ regression đạt 7 trên 7. Admin browser đạt 19 trên 19, build production mất 3,371 giây.

Các con số tổng hợp nằm tại `translation_baseline_summary.json` và `verification_summary.json`; dữ liệu từng câu nằm tại `translation_baseline_cases.csv`; log từng lệnh nằm cạnh các file này.”

## 5. Cách diễn giải số liệu đúng — 45 giây

“Nhóm lưu ý đây là baseline pilot 30 câu, chưa phải kết luận chất lượng production. Token-F1 và character similarity không thay thế COMET/BLEU hay đánh giá người dùng. p95 ở đây chỉ là thời gian suy luận NLLB trực tiếp trên một GPU, chưa bao gồm mạng, STT, TTS và queue. Vì vậy nhóm không tuyên bố hệ thống end-to-end đã đạt SLA dựa trên số liệu này.”

## 6. Phần chưa hoàn thành/chưa chứng thực — 1 phút

“Đến hết ngày 24 tháng 9 vẫn còn các nhóm cần xử lý. Một là mở rộng corpus từ 30 lên tối thiểu 500 câu đại diện. Hai là tổ chức hai người chấm adequacy và fluency; hệ thống chỉ chuẩn bị phiếu, không tự điền điểm thay con người. Ba là thu thập corpus audio để đo WER cho audio sạch/nhiễu và MOS cho TTS. Bốn là xử lý việc `flutter analyze` không trả kết quả sau 180 giây. Năm là đo p95 API/toàn pipeline, flame graph, load/soak và A/B cấu hình. Sáu là hoàn thiện fuzzy TM, model canary/rollback và UI sửa role/password. Ngoài ra, worktree còn nhiều thay đổi chưa commit nên Git chưa chứng minh được ngày hoàn thành và tác giả từng thay đổi.”

## 7. Rủi ro và biện pháp — 45 giây

- Tối ưu tốc độ làm giảm chất lượng: mọi thay đổi phải chạy cả quality gate và performance gate.
- Benchmark không đại diện: phân tầng corpus theo domain, độ dài, số/tên riêng, audio sạch/nhiễu.
- Thay đổi API làm vỡ client: khóa contract, contract test và feature freeze.
- GPU 6 GB có nguy cơ OOM: giới hạn concurrency, dùng precision phù hợp, backpressure và graceful degradation.
- Dữ liệu hội thoại nhạy cảm: giảm lưu trữ, ẩn log, phân quyền, retention và audit.

## 8. Kế hoạch ngay sau 24/09 — 45 giây

“Ưu tiên tiếp theo là hoàn tất corpus và đánh giá người thật, đo STT/TTS, sửa quy trình phân tích Flutter, sau đó chạy load test toàn pipeline. Khi các gate này đạt, nhóm mới đóng băng tích hợp và chuyển sang regression, UAT và triển khai.”

## 9. Kết luận — 30 giây

“Kết luận, giai đoạn vừa qua đã đưa hệ thống từ trạng thái có nền tảng rời rạc sang một phiên bản có kiến trúc rõ hơn, bảo mật và kiểm thử tốt hơn, admin web có thể build, đồng thời có baseline model thật và bằng chứng tái lập. Nhóm cũng công khai những phần chưa đo thay vì dùng số liệu ước lượng. Đây là cơ sở để hoàn thiện quality/performance gate trong giai đoạn tiếp theo.”

## 10. Bảng số liệu dùng khi trình chiếu

| Chỉ số | Kết quả | Nguồn |
|---|---:|---|
| Source inventory | 227 tệp | `.phase1-artifacts/.../inventory_baseline_v3/report.json` |
| Route inventory | 45 route | Cùng report inventory |
| Regression probe | 7/7 đạt | `regression_results_v3.json` |
| Backend tests | 119/119 đạt | `evidence/backend_full_tests.log` |
| Admin browser tests | 19/19 đạt | `evidence/admin_browser_tests.log` |
| Admin build | 3,371 giây, đạt | `evidence/admin_build.log` |
| Admin lint | Đạt, 2 cảnh báo | `evidence/admin_lint.log` |
| NLLB pilot | 30 câu | `evidence/translation_baseline_cases.csv` |
| Latency p50/p95 | 438,622 / 789,233 ms | `translation_baseline_summary.json` |
| Token-F1 | 0,8108 | Cùng file summary |
| Character similarity | 0,8575 | Cùng file summary |
| Accuracy thuật ngữ | 21/23 = 91,3% | Cùng file summary |
| Peak GPU memory | 2.633,69 MB | Cùng file summary |
| Flutter analyze | Timeout 180 giây | `evidence/flutter_analyze.log` |

## 11. Câu hỏi phản biện thường gặp

**Tại sao không gọi token-F1 là độ chính xác dịch?**  
Vì đây chỉ là độ trùng token với một câu tham chiếu. Bản dịch đúng có thể dùng từ khác; cần đánh giá con người và chỉ số semantic.

**p95 789 ms có phải tốc độ toàn hệ thống không?**  
Không. Đó là inference NLLB trực tiếp, không gồm STT, TTS, mạng và queue.

**Tại sao Flutter chưa đạt?**  
Lệnh analyzer không trả kết quả trong giới hạn 180 giây. Nhóm không coi timeout là pass.

**Có thể chứng minh thay đổi được làm trong giai đoạn báo cáo không?**  
Artifact có thời điểm tạo và hash, nhưng lịch sử Git hiện chỉ có commit trước giai đoạn và worktree còn bẩn. Muốn chứng minh đầy đủ cần commit/tag và biên bản review.


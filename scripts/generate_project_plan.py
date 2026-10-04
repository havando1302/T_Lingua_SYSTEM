from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Ke_hoach_du_an_AI_dich_thuat_25-08_den_30-10-2026.xlsx"

PROJECT_START = date(2026, 8, 25)
PROJECT_END = date(2026, 10, 30)


def d(value: str) -> date:
    return datetime.strptime(value, "%d/%m/%Y").date()


TASKS = [
    # wbs, owner, start, phase, task, detail, output, end, dependency, priority, acceptance
    ("1.1", "Hà Văn Đô & Nguyễn Quang Thọ", "25/08/2026", "Khởi động & đánh giá", "Kick-off và thống nhất cách làm việc", "Chốt mục tiêu; phạm vi; vai trò; kênh trao đổi; quy ước nhánh/commit; lịch họp; mẫu báo cáo; quy trình xử lý lỗi.", "Biên bản kick-off + RACI + lịch làm việc", "25/08/2026", "-", "Cao", "Hai thành viên xác nhận phạm vi, đầu ra, cách báo cáo và quy tắc Done."),
    ("1.2", "Hà Văn Đô", "25/08/2026", "Khởi động & đánh giá", "Rà soát backend và pipeline AI hiện có", "Kiểm kê FastAPI, WebSocket, worker STT/dịch/TTS, cache, translation memory, DB, cấu hình model, xử lý lỗi và các điểm nghẽn đã biết.", "Báo cáo hiện trạng backend/AI + danh sách nợ kỹ thuật", "27/08/2026", "1.1", "Cao", "Có sơ đồ luồng hiện tại, danh sách lỗi/rủi ro và đề xuất ưu tiên P0/P1/P2."),
    ("1.3", "Nguyễn Quang Thọ", "25/08/2026", "Khởi động & đánh giá", "Rà soát Flutter frontend và admin web", "Kiểm kê luồng dịch văn bản/giọng nói, lịch sử, cài đặt, quản lý trạng thái, API/WebSocket; rà soát các trang Dashboard, Users, API Keys, Dictionary, History, QA, Settings.", "Báo cáo hiện trạng UI + ma trận màn hình/API", "27/08/2026", "1.1", "Cao", "Mỗi màn hình có trạng thái hoàn thiện, API phụ thuộc, lỗi UX và việc cần sửa."),
    ("1.4", "Hà Văn Đô", "26/08/2026", "Khởi động & đánh giá", "Rà soát hạ tầng, dữ liệu và phụ thuộc", "Kiểm tra Docker, cấu hình môi trường, GPU/CPU/RAM, phiên bản model/thư viện, lưu trữ audio, DB, log, dữ liệu nhạy cảm và khả năng tái lập môi trường.", "Checklist hạ tầng + sơ đồ triển khai hiện tại", "28/08/2026", "1.1", "Cao", "Chạy được môi trường chuẩn; ghi rõ cấu hình tối thiểu và điểm khác biệt dev/staging."),
    ("1.5", "Nguyễn Quang Thọ", "28/08/2026", "Khởi động & đánh giá", "Lập backlog và ma trận truy vết", "Tổng hợp phát hiện từ frontend, admin, backend; chia Epic/Story/Bug; gán mức độ; liên kết yêu cầu với màn hình, API và kiểm thử.", "Backlog ưu tiên + Requirement Traceability Matrix", "29/08/2026", "1.2, 1.3, 1.4", "Cao", "100% hạng mục phạm vi có chủ sở hữu, ưu tiên, tiêu chí nghiệm thu và phụ thuộc."),
    ("2.1", "Hà Văn Đô & Nguyễn Quang Thọ", "28/08/2026", "Yêu cầu, thiết kế & baseline", "Chốt phạm vi MVP và tiêu chí thành công", "Xác định ngôn ngữ/chiều dịch ưu tiên; loại đầu vào; chức năng admin; đối tượng sử dụng; ngoài phạm vi; KPI chất lượng, độ trễ, độ ổn định và bảo mật.", "Project Scope + Definition of Done", "31/08/2026", "1.2, 1.3", "Cao", "Phạm vi đủ rõ để không phát sinh chức năng ngoài kế hoạch; KPI có cách đo và ngưỡng pass/fail."),
    ("2.2", "Nguyễn Quang Thọ", "29/08/2026", "Yêu cầu, thiết kế & baseline", "Thiết kế luồng người dùng admin", "Mô tả đăng nhập/RBAC; dashboard; người dùng; API key; từ điển; lịch sử; QA; cấu hình model; audit log; trạng thái loading/empty/error.", "User flow + danh mục use case admin", "31/08/2026", "1.3", "Cao", "Bao phủ vai trò Admin/Reviewer; mọi hành động nhạy cảm có xác nhận và phản hồi rõ ràng."),
    ("2.3", "Nguyễn Quang Thọ", "31/08/2026", "Yêu cầu, thiết kế & baseline", "Wireframe và design system admin", "Thiết kế layout responsive; sidebar; bảng, lọc, phân trang; form; modal; thông báo; màu trạng thái; quy tắc typography và accessibility.", "Wireframe + UI kit tối thiểu", "03/09/2026", "2.2", "Cao", "Có wireframe cho 8 nhóm trang; dùng nhất quán component và hiển thị tốt ở 1366px/1920px."),
    ("2.4", "Hà Văn Đô", "29/08/2026", "Yêu cầu, thiết kế & baseline", "Thiết kế bộ dữ liệu benchmark", "Chọn tập câu theo cặp ngôn ngữ/miền chủ đề/độ dài; audio sạch và nhiễu; câu có tên riêng, số, thuật ngữ; quy tắc ẩn danh và chấm điểm.", "Benchmark spec + bộ mẫu có phiên bản", "02/09/2026", "2.1", "Cao", "Tối thiểu 500 câu văn bản và 100 mẫu audio hoặc quy mô khác được hai thành viên duyệt."),
    ("2.5", "Hà Văn Đô", "03/09/2026", "Yêu cầu, thiết kế & baseline", "Đo baseline chất lượng dịch", "Chạy tập benchmark; đo BLEU/chrF/COMET nếu phù hợp; WER cho STT; accuracy thuật ngữ; chấm adequacy/fluency và phân loại lỗi.", "Báo cáo baseline chất lượng", "05/09/2026", "2.4", "Cao", "Kết quả tái lập được, lưu cấu hình/model/dữ liệu và có phân tích 10 nhóm lỗi lớn nhất."),
    ("2.6", "Hà Văn Đô", "03/09/2026", "Yêu cầu, thiết kế & baseline", "Đo baseline hiệu năng", "Đo p50/p95/p99 cho STT, dịch, TTS và toàn pipeline; time-to-first-partial; RTF; throughput; CPU/GPU/RAM; kiểm thử cold/warm start.", "Báo cáo baseline hiệu năng + profile", "05/09/2026", "1.4, 2.4", "Cao", "Có script/kịch bản đo, cấu hình máy, tải thử và số liệu từng chặng; xác định nút thắt chính."),
    ("2.7", "Hà Văn Đô & Nguyễn Quang Thọ", "05/09/2026", "Yêu cầu, thiết kế & baseline", "Thiết kế kiến trúc mục tiêu và hợp đồng API", "Chốt luồng REST/WebSocket, schema request/response/error, version API, auth, timeout/retry, idempotency, cache, hàng đợi, log/metric/trace.", "Sơ đồ kiến trúc đích + API contract v1", "06/09/2026", "2.5, 2.6", "Cao", "Frontend và backend cùng duyệt; API có ví dụ payload, mã lỗi và tiêu chí tương thích ngược."),
    ("3.1", "Nguyễn Quang Thọ", "07/09/2026", "Hoàn thiện admin web", "Chuẩn hóa layout và component dùng chung", "Hoàn thiện responsive shell, sidebar, header, button/input/table/modal/toast/skeleton; thống nhất loading/empty/error và màu trạng thái.", "Bộ component admin ổn định", "09/09/2026", "2.3", "Cao", "Không trùng lặp component chính; responsive; keyboard focus rõ; build/lint đạt."),
    ("3.2", "Hà Văn Đô", "07/09/2026", "Hoàn thiện admin web", "Hoàn thiện xác thực và phân quyền admin", "Chuẩn hóa login, token/refresh, hash mật khẩu, RBAC, access policy, session timeout, rate limit đăng nhập và audit sự kiện bảo mật.", "API Auth/RBAC + kiểm thử quyền", "09/09/2026", "2.7", "Cao", "API trái quyền trả 401/403 đúng; không lộ dữ liệu; test các vai trò pass."),
    ("3.3", "Nguyễn Quang Thọ", "10/09/2026", "Hoàn thiện admin web", "Tích hợp đăng nhập và route guard", "Kết nối auth API; quản lý phiên; bảo vệ route; xử lý token hết hạn; đăng xuất; hiển thị lỗi; điều hướng theo quyền.", "Login hoàn chỉnh + protected routes", "12/09/2026", "3.1, 3.2", "Cao", "Không truy cập được route trái quyền; hết phiên xử lý nhất quán; không lưu secret không an toàn."),
    ("3.4", "Hà Văn Đô", "10/09/2026", "Hoàn thiện admin web", "API Dashboard và Analytics", "Cung cấp KPI tổng request, lỗi, người dùng, cặp ngôn ngữ, latency, throughput, chất lượng/feedback; hỗ trợ lọc thời gian và aggregate hiệu quả.", "API dashboard có tài liệu", "13/09/2026", "2.7", "Cao", "Dữ liệu đúng theo truy vấn kiểm chứng; p95 API đáp ứng ngưỡng thống nhất trên dữ liệu thử."),
    ("3.5", "Nguyễn Quang Thọ", "13/09/2026", "Hoàn thiện admin web", "Hoàn thiện Dashboard và Analytics UI", "Xây KPI cards, biểu đồ xu hướng, phân bố ngôn ngữ, lỗi, latency; bộ lọc thời gian; tooltip; trạng thái không dữ liệu.", "Dashboard quản trị hoàn chỉnh", "15/09/2026", "3.4", "Cao", "Số liệu khớp API; biểu đồ dễ đọc; lọc hoạt động; không vỡ giao diện ở độ phân giải mục tiêu."),
    ("3.6", "Hà Văn Đô", "14/09/2026", "Hoàn thiện admin web", "API quản lý Users và API Keys", "CRUD/khóa người dùng; phân quyền; reset phiên; tạo/thu hồi/rotate API key; scope; hạn dùng; che khóa; audit thay đổi.", "API Users/API Keys", "16/09/2026", "3.2", "Cao", "Unique/ràng buộc đúng; key chỉ hiển thị một lần; hành động nhạy cảm được audit; test pass."),
    ("3.7", "Nguyễn Quang Thọ", "16/09/2026", "Hoàn thiện admin web", "UI quản lý Users và API Keys", "Danh sách, tìm kiếm, lọc, phân trang; form tạo/sửa/khóa; reset; tạo/thu hồi key; xác nhận thao tác nguy hiểm.", "Trang Users và API Keys hoàn chỉnh", "18/09/2026", "3.6", "Cao", "CRUD, lọc, phân trang và phân quyền hoạt động; lỗi API có thông báo rõ."),
    ("3.8", "Hà Văn Đô", "17/09/2026", "Hoàn thiện admin web", "API Dictionary, History và QA", "CRUD từ điển theo cặp ngôn ngữ; import/export; lịch sử có lọc; chi tiết request; ghi nhận đánh giá/sửa bản dịch; ẩn dữ liệu nhạy cảm.", "API Dictionary/History/QA", "19/09/2026", "2.7", "Cao", "Import kiểm tra lỗi; lọc lịch sử đúng; dữ liệu nhạy cảm bị che; feedback lưu được và truy vết được."),
    ("3.9", "Nguyễn Quang Thọ", "19/09/2026", "Hoàn thiện admin web", "UI Dictionary, History và QA", "Bảng từ điển, import/export, kiểm tra trùng; tra cứu lịch sử; xem chi tiết pipeline; hàng đợi QA; form đánh giá và sửa bản dịch.", "Trang Dictionary/History/QA hoàn chỉnh", "22/09/2026", "3.8", "Cao", "Luồng chính hoàn tất không lỗi; file sai được báo theo dòng; reviewer lưu được điểm và bản sửa."),
    ("3.10", "Hà Văn Đô", "20/09/2026", "Hoàn thiện admin web", "API Settings, Models và Audit log", "Quản lý tham số an toàn theo whitelist; model active/canary; ngưỡng VAD/timeout; audit bất biến; rollback cấu hình; che secret.", "API Settings/Models/Audit", "22/09/2026", "3.2, 2.7", "Cao", "Không sửa được key ngoài whitelist; secret không trả về; cấu hình có version và rollback."),
    ("3.11", "Nguyễn Quang Thọ", "23/09/2026", "Hoàn thiện admin web", "UI Settings, Models và Audit log", "Form cấu hình có validate; cảnh báo ảnh hưởng; chọn model; xem version; rollback; lọc audit theo người dùng/hành động/thời gian.", "Trang Settings/Models/Audit hoàn chỉnh", "25/09/2026", "3.10", "Trung bình", "Validate trước lưu; hiển thị diff; rollback có xác nhận; audit filter hoạt động."),
    ("3.12", "Hà Văn Đô & Nguyễn Quang Thọ", "26/09/2026", "Hoàn thiện admin web", "Kiểm thử tích hợp và chốt admin web", "Chạy luồng Admin/Reviewer; kiểm tra quyền, CRUD, phân trang, responsive, lỗi mạng, dữ liệu lớn; sửa lỗi P0/P1.", "Admin web release candidate", "27/09/2026", "3.3, 3.5, 3.7, 3.9, 3.11", "Cao", "100% smoke test pass; không còn lỗi P0/P1; build production thành công."),
    ("4.1", "Hà Văn Đô", "07/09/2026", "Nâng chất lượng dịch", "Chuẩn hóa tiền/hậu xử lý văn bản", "Unicode/case/punctuation; tách câu; xử lý số, ngày, đơn vị, URL; giữ placeholder; phục hồi format; phát hiện ngôn ngữ và input rỗng/không hợp lệ.", "Module normalization + unit test", "10/09/2026", "2.5", "Cao", "Không làm mất entity/placeholder; bộ test biên pass; giảm lỗi format so với baseline."),
    ("4.2", "Hà Văn Đô", "11/09/2026", "Nâng chất lượng dịch", "Tối ưu từ điển và Translation Memory", "Thiết kế exact/fuzzy match; ưu tiên thuật ngữ; normalize key; version; cache; ngăn thay thế sai ngữ cảnh; kết nối feedback đã duyệt.", "Glossary/TM engine phiên bản hóa", "15/09/2026", "4.1, 3.8", "Cao", "Accuracy thuật ngữ trên bộ kiểm thử đạt ngưỡng KPI; không phá tên riêng/placeholder."),
    ("4.3", "Hà Văn Đô", "16/09/2026", "Nâng chất lượng dịch", "Mở rộng tập kiểm thử chất lượng", "Bổ sung câu ngắn/dài, hội thoại, nhiễu, code-switch, tên riêng, số liệu và domain; chia train/dev/test; khóa test set chống rò rỉ.", "Dataset benchmark v2 + data card", "19/09/2026", "2.4, 2.5", "Cao", "Dataset cân bằng theo nhóm lỗi, có nguồn/gắn nhãn/version và không chứa dữ liệu cá nhân thô."),
    ("4.4", "Nguyễn Quang Thọ", "16/09/2026", "Nâng chất lượng dịch", "Hoàn thiện công cụ chấm và phản hồi QA", "Thiết kế giao diện so sánh nguồn–bản dịch–bản sửa; thang adequacy/fluency; loại lỗi; phím tắt; chống chấm trùng; xuất báo cáo.", "QA annotation workflow", "20/09/2026", "3.9", "Cao", "Reviewer chấm/sửa được; dữ liệu có người chấm, thời gian, phiên bản model và nguyên nhân lỗi."),
    ("4.5", "Hà Văn Đô & Nguyễn Quang Thọ", "21/09/2026", "Nâng chất lượng dịch", "Đánh giá con người vòng 1 và phân tích lỗi", "Chấm mẫu mù; đối chiếu chỉ số tự động; nhóm lỗi omission/addition/mistranslation/grammar/term/entity; ưu tiên lỗi ảnh hưởng người dùng.", "Quality report vòng 1 + backlog cải thiện", "23/09/2026", "4.3, 4.4", "Cao", "Có ít nhất 2 lượt chấm cho mẫu trọng yếu; bất đồng được xử lý; chốt top lỗi và owner."),
    ("4.6", "Hà Văn Đô", "24/09/2026", "Nâng chất lượng dịch", "Tinh chỉnh suy luận và lựa chọn model", "Thử beam/temperature/max length; language routing; fallback; confidence; reranking/rule; so sánh model theo chất lượng, tốc độ và bộ nhớ.", "Cấu hình model tối ưu + báo cáo A/B", "28/09/2026", "4.5", "Cao", "Cấu hình thắng baseline trên tập khóa, không vượt ngân sách latency/tài nguyên đã chốt."),
    ("4.7", "Hà Văn Đô", "29/09/2026", "Nâng chất lượng dịch", "Xử lý audio nhiễu và đầu vào khó", "Tối ưu VAD/denoise/chunking; tránh cắt từ; xử lý im lặng/âm lượng thấp; code-switch; lặp; partial transcript và ghép câu.", "Pipeline audio robust + test", "02/10/2026", "4.6", "Cao", "WER và lỗi cắt câu cải thiện trên tập nhiễu; không tăng đáng kể độ trễ so với ngân sách."),
    ("4.8", "Nguyễn Quang Thọ", "29/09/2026", "Nâng chất lượng dịch", "Luồng người dùng sửa và gửi phản hồi", "Cho phép sửa bản dịch; đánh giá nhanh; báo lỗi; gửi context có kiểm soát; thông báo quyền riêng tư; đồng bộ về QA/TM sau duyệt.", "Feedback loop trên Flutter/admin", "02/10/2026", "3.9, 4.4", "Trung bình", "Phản hồi gắn đúng request/model; không đưa thẳng dữ liệu chưa duyệt vào TM; UX rõ ràng."),
    ("4.9", "Hà Văn Đô & Nguyễn Quang Thọ", "03/10/2026", "Nâng chất lượng dịch", "Regression chất lượng và Quality Gate", "Chạy benchmark v2; đánh giá mù vòng 2; so sánh baseline; kiểm tra từng cặp ngôn ngữ/domain; xác nhận không regression P0.", "Quality Gate report", "05/10/2026", "4.6, 4.7, 4.8", "Cao", "Đạt KPI đã chốt hoặc có biên bản chấp nhận sai lệch; không còn lỗi dịch nghiêm trọng chưa có xử lý."),
    ("5.1", "Hà Văn Đô", "14/09/2026", "Tối ưu tốc độ & ổn định", "Profiling chi tiết pipeline", "Đo CPU/GPU kernel, I/O, serialize, audio decode, model queue, DB/cache; flame graph; tách cold/warm; xác định critical path.", "Performance profile + top bottlenecks", "17/09/2026", "2.6", "Cao", "Giải thích được phần lớn latency p95; mỗi bottleneck có giả thuyết và phương án đo lại."),
    ("5.2", "Hà Văn Đô", "18/09/2026", "Tối ưu tốc độ & ổn định", "Tối ưu tải model và suy luận", "Preload/warm-up; lựa chọn precision/quantization; device placement; batch động; reuse tokenizer; torch inference mode; giới hạn tài nguyên.", "Inference runtime tối ưu", "22/09/2026", "5.1", "Cao", "Giảm latency/tài nguyên so baseline; chất lượng không giảm quá ngưỡng; không OOM ở tải mục tiêu."),
    ("5.3", "Hà Văn Đô", "23/09/2026", "Tối ưu tốc độ & ổn định", "Tối ưu hàng đợi và backpressure", "Thiết kế scheduler; ưu tiên interactive; giới hạn queue; timeout/cancel; circuit breaker; worker health; tránh xử lý audio cũ khi client ngắt.", "Scheduler/worker ổn định", "26/09/2026", "5.2", "Cao", "Không tăng hàng đợi vô hạn; timeout/cancel giải phóng tài nguyên; tải vượt ngưỡng trả lỗi kiểm soát."),
    ("5.4", "Hà Văn Đô", "27/09/2026", "Tối ưu tốc độ & ổn định", "Tối ưu cache, DB và Translation Memory", "Cache kết quả an toàn; index truy vấn; connection/session; batch log; TTL/eviction; chống cache sai theo model, ngôn ngữ hoặc glossary version.", "Cache/DB/TM performance patch", "30/09/2026", "4.2, 5.1", "Cao", "Cache key đúng; tỷ lệ hit được đo; truy vấn trọng yếu đạt SLA; không trả kết quả sai phiên bản."),
    ("5.5", "Nguyễn Quang Thọ", "23/09/2026", "Tối ưu tốc độ & ổn định", "Ổn định WebSocket và state Flutter", "State machine kết nối; reconnect có backoff; heartbeat; deduplicate; cancel; timeout; resume hợp lý; xử lý chuyển mạng và app background.", "WebSocket client ổn định", "26/09/2026", "2.7", "Cao", "Không nhân đôi message; phục hồi sau mất mạng; UI không treo; test state transition pass."),
    ("5.6", "Nguyễn Quang Thọ", "27/09/2026", "Tối ưu tốc độ & ổn định", "Tối ưu audio streaming và cảm nhận tốc độ", "Điều chỉnh chunk/buffer; hiển thị partial; tránh phát audio chồng; prebuffer hợp lý; trạng thái đang nghe/đang dịch/đang phát; chống thao tác lặp.", "Luồng voice UX nhanh và ổn định", "30/09/2026", "5.5, 4.7", "Cao", "Không mất/nhân audio ở kịch bản chuẩn; partial hiển thị đúng thứ tự; thao tác hủy có hiệu lực."),
    ("5.7", "Hà Văn Đô & Nguyễn Quang Thọ", "01/10/2026", "Tối ưu tốc độ & ổn định", "Load test vòng 1", "Chạy tải tăng dần theo text/voice; đo p50/p95/p99, throughput, error, queue, tài nguyên; kiểm tra soak và điểm gãy; ghi đầy đủ cấu hình.", "Load test report vòng 1", "04/10/2026", "5.3, 5.4, 5.6", "Cao", "Số liệu tái lập; xác định tải an toàn; không mất request im lặng; có backlog tuning cụ thể."),
    ("5.8", "Hà Văn Đô", "05/10/2026", "Tối ưu tốc độ & ổn định", "Tuning backend/GPU theo kết quả tải", "Điều chỉnh worker/concurrency/batch/timeout/memory; tách pool; graceful degradation; tối ưu log; sửa leak và contention.", "Backend tuning release", "08/10/2026", "5.7", "Cao", "Đạt hoặc tiến sát KPI tốc độ trong ngân sách phần cứng; soak không leak/OOM; lỗi có kiểm soát."),
    ("5.9", "Nguyễn Quang Thọ", "05/10/2026", "Tối ưu tốc độ & ổn định", "Tối ưu client và admin", "Giảm request thừa; debounce; cache/pagination; lazy loading; hạn chế rebuild; nén payload phù hợp; đo startup/render/network trên thiết bị mục tiêu.", "Frontend performance patch", "08/10/2026", "5.7", "Trung bình", "Không phát request trùng; danh sách lớn vẫn phản hồi tốt; chỉ số UX cải thiện theo phép đo trước/sau."),
    ("5.10", "Hà Văn Đô & Nguyễn Quang Thọ", "09/10/2026", "Tối ưu tốc độ & ổn định", "Load test vòng 2 và Performance Gate", "Lặp tải với release candidate; kiểm tra spike/soak; đối chiếu baseline; xác nhận capacity; chốt cấu hình vận hành và ngưỡng cảnh báo.", "Performance Gate report", "10/10/2026", "5.8, 5.9", "Cao", "KPI đạt hoặc có chấp thuận; xác định capacity; không lỗi P0/P1 về treo, leak, mất request."),
    ("6.1", "Hà Văn Đô", "01/10/2026", "Tích hợp frontend–backend", "Ổn định API contract và xử lý lỗi", "Đóng băng schema v1; mã lỗi chuẩn; correlation ID; validation; giới hạn payload; timeout; retry policy; tài liệu OpenAPI/WebSocket và ví dụ.", "API v1 release candidate", "03/10/2026", "2.7, 3.12", "Cao", "Contract test pass; response/error nhất quán; tài liệu đủ để client tích hợp không cần đọc mã nguồn."),
    ("6.2", "Nguyễn Quang Thọ", "01/10/2026", "Tích hợp frontend–backend", "Cập nhật Flutter repository và auth/session", "Ánh xạ model/API v1; auth header/refresh; timeout/retry; parse lỗi; environment endpoint; lưu lịch sử; dọn tương thích tạm thời.", "Flutter data layer tích hợp API v1", "04/10/2026", "6.1", "Cao", "Không hard-code endpoint/secret; lỗi parse không crash; phiên đăng nhập và lịch sử hoạt động."),
    ("6.3", "Hà Văn Đô & Nguyễn Quang Thọ", "05/10/2026", "Tích hợp frontend–backend", "Kiểm thử E2E dịch văn bản", "Kiểm thử nhập/dịch/sao chép/phát lại/lưu lịch sử/phản hồi; nhiều ngôn ngữ; lỗi mạng; input dài; ký tự đặc biệt; quyền riêng tư.", "E2E text test report + bản sửa", "07/10/2026", "6.1, 6.2, 4.9", "Cao", "100% luồng P0 pass; dữ liệu hiển thị đúng; không mất lịch sử; lỗi được giải thích cho người dùng."),
    ("6.4", "Hà Văn Đô & Nguyễn Quang Thọ", "08/10/2026", "Tích hợp frontend–backend", "Kiểm thử E2E dịch giọng nói", "Kiểm thử mic/VAD/STT/dịch/TTS; hai chiều hội thoại; ngắt/hủy; mất mạng; thiết bị âm thanh; audio nhiễu; phiên dài.", "E2E voice test report + bản sửa", "11/10/2026", "6.2, 4.7, 5.10", "Cao", "Luồng P0 pass; không phát chồng/mất audio; session kết thúc sạch; latency đạt ngưỡng đã chốt."),
    ("6.5", "Nguyễn Quang Thọ", "09/10/2026", "Tích hợp frontend–backend", "Hoàn thiện history, settings và offline/error UX", "Đồng bộ lịch sử; lọc/xóa an toàn; cài đặt ngôn ngữ/audio; thông báo offline; retry; empty state; accessibility; copy và localization.", "Flutter UX release candidate", "12/10/2026", "6.2, 6.3", "Trung bình", "Các trạng thái lỗi/empty/loading đầy đủ; không mất dữ liệu khi retry; UI nhất quán trên thiết bị mục tiêu."),
    ("6.6", "Hà Văn Đô", "11/10/2026", "Tích hợp frontend–backend", "Bổ sung observability và cảnh báo", "Structured log; metric latency/error/queue/GPU/cache; correlation ID xuyên pipeline; health/readiness; dashboard vận hành; ngưỡng cảnh báo và runbook link.", "Telemetry dashboard + alert rules", "13/10/2026", "5.10, 6.1", "Cao", "Truy vết được một request từ client đến worker; cảnh báo thử nghiệm kích hoạt và có hướng xử lý."),
    ("6.7", "Hà Văn Đô & Nguyễn Quang Thọ", "14/10/2026", "Tích hợp frontend–backend", "Integration freeze và chốt release scope", "Đóng băng tính năng; chốt version; rà soát dependency; chỉ nhận bug P0/P1; lập danh sách known issues; chuẩn bị regression.", "Release scope v1.0 + known issues", "15/10/2026", "6.3, 6.4, 6.5, 6.6", "Cao", "Không còn thay đổi schema/tính năng chưa duyệt; artifact và version đồng nhất."),
    ("7.1", "Hà Văn Đô", "12/10/2026", "Kiểm thử, bảo mật & UAT", "Unit/integration test backend", "Bổ sung test domain/service/repository/API/WebSocket/worker; mock model hợp lý; concurrency; timeout; cache; migration; error mapping.", "Backend automated test suite", "15/10/2026", "6.1", "Cao", "Test P0/P1 pass ổn định; coverage phần lõi đạt ngưỡng nhóm chốt; không flaky nghiêm trọng."),
    ("7.2", "Nguyễn Quang Thọ", "12/10/2026", "Kiểm thử, bảo mật & UAT", "Test admin web và Flutter", "Component/route/form; API mock; widget/service/state; quyền; responsive; thiết bị mục tiêu; accessibility smoke; các luồng hồi quy P0.", "Frontend/admin test suite", "15/10/2026", "3.12, 6.5", "Cao", "Build, lint/analyze và test pass; luồng P0 có test; không còn lỗi UI chặn sử dụng."),
    ("7.3", "Hà Văn Đô", "16/10/2026", "Kiểm thử, bảo mật & UAT", "Rà soát bảo mật và quyền riêng tư", "Kiểm tra auth/RBAC, secret, CORS, upload/path, injection, rate limit, dependency, log PII, retention/xóa dữ liệu, API key và cấu hình production.", "Security checklist + remediation", "18/10/2026", "7.1, 7.2", "Cao", "Không còn lỗ hổng Critical/High đã biết; secret/PII không lộ; quyền dữ liệu được kiểm chứng."),
    ("7.4", "Hà Văn Đô & Nguyễn Quang Thọ", "19/10/2026", "Kiểm thử, bảo mật & UAT", "System regression và kiểm thử tương thích", "Chạy toàn bộ suite trên staging; kiểm thử trình duyệt/thiết bị; dữ liệu lớn; migration; restart; mất kết nối; khôi phục; kiểm tra known issues.", "System Test Report", "21/10/2026", "6.7, 7.1, 7.2, 7.3", "Cao", "100% test P0 và >=95% P1 pass; không lỗi blocker/critical; lỗi còn lại có owner và hạn."),
    ("7.5", "Hà Văn Đô & Nguyễn Quang Thọ", "22/10/2026", "Kiểm thử, bảo mật & UAT", "UAT và xử lý lỗi cuối", "Chạy kịch bản người dùng/admin; ghi nhận phản hồi; sửa lỗi được duyệt; retest; ký xác nhận KPI, phạm vi và known issues.", "Biên bản UAT + release approval", "23/10/2026", "7.4", "Cao", "Đại diện nghiệm thu xác nhận; không còn P0/P1; KPI/known issues được ghi rõ."),
    ("8.1", "Hà Văn Đô", "24/10/2026", "Triển khai & bàn giao", "Chuẩn hóa Docker, cấu hình và dữ liệu", "Chốt image/version; env template; healthcheck; migration; seed admin; backup/restore; log rotation; volume; resource limit; rollback artifact.", "Bộ triển khai production + rollback", "26/10/2026", "7.5", "Cao", "Triển khai từ tài liệu trên môi trường sạch; backup/restore thử thành công; không đóng gói secret."),
    ("8.2", "Nguyễn Quang Thọ", "24/10/2026", "Triển khai & bàn giao", "Hoàn thiện tài liệu người dùng và quản trị", "Hướng dẫn cài ứng dụng, dịch text/voice, lịch sử, phản hồi; hướng dẫn admin từng module; FAQ; xử lý lỗi thường gặp; ảnh minh họa.", "User Guide + Admin Guide", "26/10/2026", "7.5", "Trung bình", "Người mới hoàn thành được luồng chính chỉ dựa vào tài liệu; nội dung khớp release candidate."),
    ("8.3", "Hà Văn Đô & Nguyễn Quang Thọ", "27/10/2026", "Triển khai & bàn giao", "Triển khai staging cuối và smoke test", "Deploy đúng artifact; chạy migration; kiểm tra health; smoke text/voice/admin; metric/alert; backup; rollback rehearsal; chốt checklist go-live.", "Staging sign-off + Go-live checklist", "27/10/2026", "8.1, 8.2", "Cao", "Smoke pass; alert nhận được; rollback rehearsal đạt; checklist có người chịu trách nhiệm."),
    ("8.4", "Hà Văn Đô & Nguyễn Quang Thọ", "28/10/2026", "Triển khai & bàn giao", "Đào tạo và chuyển giao vận hành", "Demo hệ thống; hướng dẫn dashboard/cảnh báo/backup/rollback; quy trình duyệt glossary/feedback; phân loại sự cố; hỏi đáp và ghi nhận bàn giao.", "Biên bản đào tạo + runbook vận hành", "28/10/2026", "8.3", "Trung bình", "Người nhận vận hành thực hiện được health check, xem lỗi, backup và rollback theo runbook."),
    ("8.5", "Hà Văn Đô & Nguyễn Quang Thọ", "29/10/2026", "Triển khai & bàn giao", "Go-live readiness review", "Kiểm tra UAT, security, quality/performance gate, capacity, backup, rollback, monitoring, support contact, known issues; ra quyết định Go/No-Go.", "Biên bản Go/No-Go + release notes", "29/10/2026", "8.3, 8.4", "Cao", "Tất cả điều kiện bắt buộc đạt hoặc có người có thẩm quyền chấp nhận; có kế hoạch rollback."),
    ("8.6", "Hà Văn Đô & Nguyễn Quang Thọ", "30/10/2026", "Triển khai & bàn giao", "Go-live, giám sát và nghiệm thu", "Triển khai production; smoke; theo dõi lỗi/latency/tài nguyên; xử lý sự cố; xác nhận backup; bàn giao source, artifact, tài liệu và backlog sau release.", "Hệ thống AI dịch thuật v1.0 + biên bản nghiệm thu", "30/10/2026", "8.5", "Cao", "Production hoạt động; smoke pass; không sự cố P0; đủ mã nguồn/artifact/tài liệu; ký nghiệm thu."),
]


MILESTONES = [
    ("M1", d("29/08/2026"), "Hoàn tất đánh giá hiện trạng", "Báo cáo backend, frontend, hạ tầng và backlog", "1.2–1.5"),
    ("M2", d("06/09/2026"), "Chốt yêu cầu, baseline và kiến trúc", "Scope/DoD, benchmark, baseline, API contract", "2.1–2.7"),
    ("M3", d("27/09/2026"), "Admin web release candidate", "Đủ module quản trị và smoke test", "3.1–3.12"),
    ("M4", d("05/10/2026"), "Vượt Quality Gate", "Báo cáo chất lượng so với baseline", "4.1–4.9"),
    ("M5", d("10/10/2026"), "Vượt Performance Gate", "Load test vòng 2, capacity và cấu hình", "5.1–5.10"),
    ("M6", d("15/10/2026"), "Integration freeze", "Flutter–backend–admin đồng bộ API v1", "6.1–6.7"),
    ("M7", d("18/10/2026"), "Security Gate", "Không còn Critical/High đã biết", "7.3"),
    ("M8", d("23/10/2026"), "UAT sign-off", "Biên bản UAT và release approval", "7.4–7.5"),
    ("M9", d("29/10/2026"), "Go/No-Go", "Go-live checklist, runbook, release notes", "8.1–8.5"),
    ("M10", d("30/10/2026"), "Nghiệm thu v1.0", "Hệ thống production và hồ sơ bàn giao", "8.6"),
]


RISKS = [
    ("R01", "Chất lượng dữ liệu benchmark không đại diện", "Chất lượng", "Cao", "Cao", "P1", "Phân tầng theo ngôn ngữ/domain/độ dài/nhiễu; data card; review chéo; khóa test set.", "Hà Văn Đô", "03/09/2026"),
    ("R02", "Tối ưu tốc độ làm giảm độ chính xác", "Kỹ thuật", "Cao", "Cao", "P1", "Mọi thay đổi inference phải chạy đồng thời quality gate và performance gate; rollback theo version.", "Hà Văn Đô", "10/10/2026"),
    ("R03", "Thiếu GPU hoặc cấu hình môi trường khác production", "Hạ tầng", "Trung bình", "Cao", "P1", "Chốt cấu hình tham chiếu; giới hạn tài nguyên; benchmark cùng profile production; có chế độ degrade.", "Hà Văn Đô", "05/09/2026"),
    ("R04", "Thay đổi API gây vỡ Flutter/admin", "Tích hợp", "Cao", "Cao", "P1", "API version; schema contract; contract test; freeze ngày 15/10; thay đổi phải được hai bên duyệt.", "Hà Văn Đô & Nguyễn Quang Thọ", "15/10/2026"),
    ("R05", "WebSocket mất/nhân bản message khi mạng yếu", "Ổn định", "Cao", "Cao", "P1", "Message ID, state machine, heartbeat, retry/backoff, deduplicate, cancel và test chuyển mạng.", "Nguyễn Quang Thọ", "30/09/2026"),
    ("R06", "Dữ liệu audio/lịch sử làm lộ thông tin cá nhân", "Bảo mật", "Trung bình", "Rất cao", "P1", "Minimize/ẩn danh; retention; phân quyền; che log; mã hóa truyền; test xóa và audit truy cập.", "Hà Văn Đô", "18/10/2026"),
    ("R07", "Phạm vi admin web tăng ngoài kế hoạch", "Phạm vi", "Cao", "Trung bình", "P2", "Khóa MVP; change request ghi tác động; chỉ nhận yêu cầu mới nếu đổi ưu tiên hoặc thời hạn.", "Nguyễn Quang Thọ", "06/09/2026"),
    ("R08", "Hai người bị quá tải do đầu việc song song", "Nguồn lực", "Trung bình", "Cao", "P1", "Giới hạn WIP; ưu tiên đường găng; review chéo ngắn; hạ mức hạng mục P2 trước khi dời mốc P1.", "Hà Văn Đô & Nguyễn Quang Thọ", "Hàng tuần"),
    ("R09", "Dependency/model thay đổi hoặc lỗi giấy phép", "Pháp lý/Kỹ thuật", "Thấp", "Cao", "P2", "Khóa version; lưu SBOM/license; kiểm tra điều khoản model/dataset; có model fallback.", "Hà Văn Đô", "18/10/2026"),
    ("R10", "Không tái lập được kết quả benchmark", "Chất lượng", "Trung bình", "Cao", "P1", "Lưu seed, image, model hash, config, dataset version và raw result; chạy lại độc lập trước gate.", "Hà Văn Đô", "10/10/2026"),
    ("R11", "Migration/triển khai làm mất dữ liệu", "Triển khai", "Thấp", "Rất cao", "P1", "Backup trước migration; dry-run staging; rollback script; kiểm tra restore thực tế.", "Hà Văn Đô", "27/10/2026"),
    ("R12", "Lỗi nghiêm trọng phát hiện sát go-live", "Tiến độ", "Trung bình", "Cao", "P1", "Feature freeze 15/10; triage hằng ngày; tiêu chí Go/No-Go; không go-live khi còn P0/P1.", "Hà Văn Đô & Nguyễn Quang Thọ", "29/10/2026"),
]


KPIS = [
    ("K01", "Chất lượng dịch", "Điểm đánh giá người dùng/chuyên gia (adequacy + fluency)", "Điểm trung bình trên test set khóa, thang 1–5", "≥ 4,2/5 hoặc tăng ≥ 10% so baseline", "Quality Gate 05/10", "Mục tiêu xác nhận sau baseline"),
    ("K02", "Chất lượng dịch", "Tỷ lệ lỗi dịch nghiêm trọng", "Số mẫu có omission/addition/sai nghĩa nghiêm trọng / tổng mẫu", "≤ 2% và không lỗi P0", "Quality Gate 05/10", "Mục tiêu xác nhận sau baseline"),
    ("K03", "Thuật ngữ", "Độ chính xác glossary", "Thuật ngữ dịch đúng / tổng thuật ngữ cần áp dụng", "≥ 95%", "Quality Gate 05/10", "Theo từng cặp ngôn ngữ/domain"),
    ("K04", "STT", "WER audio sạch", "Word Error Rate trên tập audio sạch khóa", "≤ 12% hoặc cải thiện ≥ 15% tương đối", "Quality Gate 05/10", "Mục tiêu xác nhận sau baseline"),
    ("K05", "STT", "WER audio nhiễu", "Word Error Rate trên tập audio nhiễu khóa", "≤ 20% hoặc cải thiện ≥ 15% tương đối", "Quality Gate 05/10", "Mục tiêu xác nhận sau baseline"),
    ("K06", "Tốc độ", "Độ trễ dịch văn bản p95", "Client gửi đến nhận đủ bản dịch, câu ≤ 50 từ, warm", "≤ 1,2 giây hoặc giảm ≥ 30%", "Performance Gate 10/10", "Đo trên cấu hình tham chiếu"),
    ("K07", "Tốc độ", "Time-to-first-partial giọng nói p95", "Bắt đầu nói đến partial transcript/dịch đầu tiên", "≤ 1,0 giây hoặc giảm ≥ 30%", "Performance Gate 10/10", "Đo trên cấu hình tham chiếu"),
    ("K08", "Tốc độ", "Độ trễ phản hồi voice p95", "Kết thúc câu đến bắt đầu phát TTS", "≤ 2,5 giây hoặc giảm ≥ 30%", "Performance Gate 10/10", "Đo trên cấu hình tham chiếu"),
    ("K09", "Ổn định", "Tỷ lệ request thành công", "Request thành công / tổng request hợp lệ ở tải mục tiêu", "≥ 99,5%", "Performance Gate 10/10", "Không tính request client chủ động hủy"),
    ("K10", "Ổn định", "Soak test", "Chạy liên tục ở tải mục tiêu, theo dõi leak/OOM/error", "≥ 4 giờ; không OOM; error < 0,5%", "Performance Gate 10/10", "Có thể tăng thời lượng nếu hạ tầng cho phép"),
    ("K11", "Admin web", "Luồng quản trị trọng yếu", "Smoke test Login/Dashboard/Users/Keys/Dictionary/History/QA/Settings", "100% pass; không P0/P1", "Admin RC 27/09", "Bắt buộc đúng RBAC"),
    ("K12", "Kiểm thử", "Hồi quy P0/P1", "Kịch bản pass / tổng kịch bản", "P0 = 100%; P1 ≥ 95%", "System Test 21/10", "Lỗi còn lại có chấp thuận"),
    ("K13", "Bảo mật", "Lỗ hổng mức Critical/High", "Kết quả review/checklist/dependency scan", "0 lỗi chưa xử lý", "Security Gate 18/10", "Không ghi secret/PII vào log"),
    ("K14", "Triển khai", "Khả năng khôi phục", "Thử backup + restore + rollback trên staging", "100% thành công", "Go-live 27/10", "Có thời gian khôi phục thực đo"),
]


PHASES = [
    ("1", "Khởi động & đánh giá", d("25/08/2026"), d("29/08/2026"), "Nắm hiện trạng và tạo backlog có ưu tiên"),
    ("2", "Yêu cầu, thiết kế & baseline", d("28/08/2026"), d("06/09/2026"), "Chốt phạm vi, KPI, kiến trúc và số liệu gốc"),
    ("3", "Hoàn thiện admin web", d("07/09/2026"), d("27/09/2026"), "Hoàn chỉnh các module quản trị trên nền hiện có"),
    ("4", "Nâng chất lượng dịch", d("07/09/2026"), d("05/10/2026"), "Giảm lỗi STT/dịch và tạo vòng phản hồi có kiểm soát"),
    ("5", "Tối ưu tốc độ & ổn định", d("14/09/2026"), d("10/10/2026"), "Giảm latency, tăng tải và ổn định streaming"),
    ("6", "Tích hợp frontend–backend", d("01/10/2026"), d("15/10/2026"), "Đồng bộ API v1 và hoàn thiện E2E Flutter/admin/backend"),
    ("7", "Kiểm thử, bảo mật & UAT", d("12/10/2026"), d("23/10/2026"), "Đảm bảo chất lượng release và được nghiệm thu người dùng"),
    ("8", "Triển khai & bàn giao", d("24/10/2026"), d("30/10/2026"), "Go-live an toàn, có giám sát, rollback và tài liệu"),
]


NAVY = "17365D"
BLUE = "2F75B5"
LIGHT_BLUE = "D9EAF7"
TEAL = "0F6B78"
GREEN = "70AD47"
LIGHT_GREEN = "E2F0D9"
AMBER = "FFC000"
LIGHT_AMBER = "FFF2CC"
RED = "C00000"
LIGHT_RED = "F4CCCC"
GRAY = "E7E6E6"
LIGHT_GRAY = "F3F6F9"
WHITE = "FFFFFF"

thin_gray = Side(style="thin", color="B7C9D6")
border = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)


def style_title(ws, title: str, subtitle: str, end_col: int) -> None:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=end_col)
    c = ws.cell(1, 1, title)
    c.font = Font(name="Aptos Display", size=20, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 32
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=end_col)
    c = ws.cell(2, 1, subtitle)
    c.font = Font(name="Aptos", size=10, italic=True, color="44546A")
    c.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = 30


def style_header(ws, row: int, start_col: int, end_col: int, fill: str = BLUE) -> None:
    for col in range(start_col, end_col + 1):
        cell = ws.cell(row, col)
        cell.font = Font(name="Aptos", size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[row].height = 34


def apply_body_style(ws, min_row: int, max_row: int, min_col: int, max_col: int) -> None:
    for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
        for cell in row:
            cell.font = Font(name="Aptos", size=9)
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def add_nav(ws, target_cell: str = "A1") -> None:
    links = [
        ("Tổng quan", "Tong_quan"),
        ("Kế hoạch", "Ke_hoach_chi_tiet"),
        ("Tiến độ tuần", "Tien_do_tuan"),
        ("Mốc", "Moc_ban_giao"),
        ("KPI", "KPI_nghiem_thu"),
        ("Rủi ro", "Rui_ro"),
    ]
    row = ws.max_row + 2
    ws.cell(row, 1, "Điều hướng:").font = Font(name="Aptos", bold=True, color=NAVY)
    for idx, (label, sheet) in enumerate(links, start=2):
        c = ws.cell(row, idx, label)
        c.hyperlink = f"#'{sheet}'!{target_cell}"
        c.style = "Hyperlink"


def make_overview(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "Tong_quan"
    ws.sheet_view.showGridLines = False
    style_title(ws, "KẾ HOẠCH DỰ ÁN HỆ THỐNG AI DỊCH THUẬT", "Thời gian: 25/08/2026–30/10/2026 | Nhân sự: Hà Văn Đô, Nguyễn Quang Thọ | Phiên bản kế hoạch: 1.0", 8)

    info = [
        ("Mục tiêu", "Hoàn thiện hệ thống dịch AI end-to-end trên nền frontend/backend đã có; xây dựng admin web; nâng chất lượng và tốc độ; tích hợp, kiểm thử, triển khai và bàn giao."),
        ("Phạm vi kỹ thuật", "Flutter frontend; React/Vite admin web; FastAPI/WebSocket backend; pipeline STT → dịch → TTS; dữ liệu/DB/cache; Docker; quan sát hệ thống và bảo mật."),
        ("Nguyên tắc", "Đo baseline trước khi tối ưu; mỗi thay đổi tốc độ phải qua Quality Gate; mỗi thay đổi chất lượng phải qua Performance Gate; đóng băng tính năng trước hồi quy/UAT."),
        ("Giả định", "Nền tảng hiện có chạy được ở mức cơ bản; hai thành viên làm việc xuyên suốt; hạ tầng GPU/dữ liệu kiểm thử sẵn sàng; KPI số tuyệt đối được xác nhận sau baseline 05/09."),
        ("Ngoài phạm vi mặc định", "Huấn luyện foundation model từ đầu; thêm cặp ngôn ngữ lớn ngoài danh sách ưu tiên; native iOS/Android riêng; billing thương mại; HA đa vùng. Muốn bổ sung phải qua change request."),
    ]
    row = 4
    for label, value in info:
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
        ws.cell(row, 2, label).font = Font(name="Aptos", bold=True, color=WHITE)
        ws.cell(row, 2).fill = PatternFill("solid", fgColor=TEAL)
        ws.cell(row, 2).alignment = Alignment(vertical="center")
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=8)
        ws.cell(row, 4, value).font = Font(name="Aptos", size=10)
        ws.cell(row, 4).fill = PatternFill("solid", fgColor=LIGHT_GRAY)
        ws.cell(row, 4).alignment = Alignment(wrap_text=True, vertical="center")
        for col in range(2, 9):
            ws.cell(row, col).border = border
        ws.row_dimensions[row].height = 44
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
    ws.cell(row, 2, "PHÂN CÔNG CHÍNH").font = Font(name="Aptos", bold=True, color=WHITE)
    ws.cell(row, 2).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row, 2).alignment = Alignment(horizontal="center")
    row += 1
    roles = [
        ("Hà Văn Đô", "Technical Lead Backend/AI", "FastAPI, WebSocket, STT–Translation–TTS, dữ liệu, hiệu năng, bảo mật, Docker/triển khai, observability."),
        ("Nguyễn Quang Thọ", "Frontend & Admin Lead", "Flutter, React admin web, UX/UI, quản lý trạng thái, tích hợp API, QA workflow, tài liệu người dùng và kiểm thử giao diện."),
        ("Cả hai", "Tích hợp & chất lượng", "Chốt yêu cầu/kiến trúc, review chéo, đánh giá chất lượng, load test, E2E, regression, UAT, go-live và nghiệm thu."),
    ]
    ws.cell(row, 2, "Thành viên")
    ws.cell(row, 4, "Vai trò")
    ws.cell(row, 6, "Trách nhiệm")
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=8)
    for col in range(2, 9):
        ws.cell(row, col).fill = PatternFill("solid", fgColor=BLUE)
        ws.cell(row, col).font = Font(name="Aptos", bold=True, color=WHITE)
        ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row, col).border = border
    for member, role, responsibility in roles:
        row += 1
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
        ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=8)
        ws.cell(row, 2, member)
        ws.cell(row, 4, role)
        ws.cell(row, 6, responsibility)
        for col in range(2, 9):
            ws.cell(row, col).border = border
            ws.cell(row, col).fill = PatternFill("solid", fgColor="FFFFFF" if row % 2 else LIGHT_BLUE)
            ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 42

    row += 2
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
    ws.cell(row, 2, "TỔNG HỢP GIAI ĐOẠN").font = Font(name="Aptos", bold=True, color=WHITE)
    ws.cell(row, 2).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row, 2).alignment = Alignment(horizontal="center")
    row += 1
    headers = ["Mã", "Giai đoạn", "Bắt đầu", "Kết thúc", "Ngày lịch", "Số đầu việc", "Mục tiêu"]
    positions = [2, 3, 4, 5, 6, 7, 8]
    for col, header in zip(positions, headers):
        ws.cell(row, col, header)
    style_header(ws, row, 2, 8)
    phase_start_row = row + 1
    for code, phase, start, end, goal in PHASES:
        row += 1
        ws.cell(row, 2, code)
        ws.cell(row, 3, phase)
        ws.cell(row, 4, start)
        ws.cell(row, 5, end)
        ws.cell(row, 6, (end - start).days + 1)
        ws.cell(row, 7, sum(1 for t in TASKS if t[3] == phase))
        ws.cell(row, 8, goal)
        for col in range(2, 9):
            ws.cell(row, col).border = border
            ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row, col).fill = PatternFill("solid", fgColor="FFFFFF" if row % 2 else LIGHT_BLUE)
        ws.cell(row, 4).number_format = "dd/mm/yyyy"
        ws.cell(row, 5).number_format = "dd/mm/yyyy"
    ws.freeze_panes = "B4"
    ws.auto_filter.ref = f"B{phase_start_row-1}:H{row}"
    widths = {"A": 3, "B": 18, "C": 31, "D": 18, "E": 18, "F": 14, "G": 14, "H": 56}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    ws.print_area = f"B1:H{row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    add_nav(ws)


def make_detail(wb: Workbook) -> None:
    ws = wb.create_sheet("Ke_hoach_chi_tiet")
    ws.sheet_view.showGridLines = False
    style_title(ws, "KẾ HOẠCH THỰC HIỆN CHI TIẾT", "Các giai đoạn có chủ ý chạy song song. 'Tổng số ngày TH' là số ngày lịch tính cả hai đầu; 'Ngày công' loại thứ Bảy và Chủ nhật.", 16)
    headers = [
        "STT", "WBS", "Thành viên", "Ngày bắt đầu", "Giai đoạn", "Công việc", "Chi tiết nhiệm vụ",
        "Sản phẩm/Kết quả", "Deadline", "Trạng thái", "Tổng số ngày TH", "Ngày công", "Phụ thuộc",
        "Ưu tiên", "Tiêu chí nghiệm thu", "% hoàn thành",
    ]
    for col, header in enumerate(headers, start=1):
        ws.cell(4, col, header)
    style_header(ws, 4, 1, len(headers), NAVY)

    for idx, task in enumerate(TASKS, start=1):
        wbs, owner, start, phase, name, detail, output, end, dependency, priority, acceptance = task
        row = idx + 4
        values = [idx, wbs, owner, d(start), phase, name, detail, output, d(end), "Chưa bắt đầu"]
        for col, value in enumerate(values, start=1):
            ws.cell(row, col, value)
        ws.cell(row, 11, f"=I{row}-D{row}+1")
        ws.cell(row, 12, f"=NETWORKDAYS(D{row},I{row})")
        ws.cell(row, 13, dependency)
        ws.cell(row, 14, priority)
        ws.cell(row, 15, acceptance)
        ws.cell(row, 16, 0)
        if idx % 2 == 0:
            for col in range(1, 17):
                ws.cell(row, col).fill = PatternFill("solid", fgColor="F7FAFC")
        ws.cell(row, 4).number_format = "dd/mm/yyyy"
        ws.cell(row, 9).number_format = "dd/mm/yyyy"
        ws.cell(row, 16).number_format = "0%"
        ws.row_dimensions[row].height = 66

    last_row = 4 + len(TASKS)
    apply_body_style(ws, 5, last_row, 1, 16)
    for row in range(5, last_row + 1):
        for col in [1, 2, 4, 9, 10, 11, 12, 14, 16]:
            ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    status_dv = DataValidation(type="list", formula1='"Chưa bắt đầu,Đang thực hiện,Tạm dừng,Hoàn thành,Trễ hạn"', allow_blank=False)
    priority_dv = DataValidation(type="list", formula1='"Cao,Trung bình,Thấp"', allow_blank=False)
    percent_dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=False)
    ws.add_data_validation(status_dv)
    ws.add_data_validation(priority_dv)
    ws.add_data_validation(percent_dv)
    status_dv.add(f"J5:J{last_row}")
    priority_dv.add(f"N5:N{last_row}")
    percent_dv.add(f"P5:P{last_row}")

    ws.conditional_formatting.add(f"J5:J{last_row}", CellIsRule(operator="equal", formula=['"Hoàn thành"'], fill=PatternFill("solid", fgColor=LIGHT_GREEN)))
    ws.conditional_formatting.add(f"J5:J{last_row}", CellIsRule(operator="equal", formula=['"Đang thực hiện"'], fill=PatternFill("solid", fgColor=LIGHT_AMBER)))
    ws.conditional_formatting.add(f"J5:J{last_row}", CellIsRule(operator="equal", formula=['"Trễ hạn"'], fill=PatternFill("solid", fgColor=LIGHT_RED)))
    ws.conditional_formatting.add(f"P5:P{last_row}", CellIsRule(operator="equal", formula=["1"], fill=PatternFill("solid", fgColor=LIGHT_GREEN)))
    ws.conditional_formatting.add(f"I5:I{last_row}", FormulaRule(formula=[f'AND($I5<TODAY(),$J5<>"Hoàn thành")'], fill=PatternFill("solid", fgColor="FCE4D6")))

    widths = [7, 8, 27, 13, 25, 31, 55, 38, 13, 16, 14, 11, 14, 11, 47, 14]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "F5"
    ws.auto_filter.ref = f"A4:P{last_row}"
    ws.print_title_rows = "1:4"
    ws.print_area = f"A1:P{last_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.auto_filter.ref = f"A4:P{last_row}"
    add_nav(ws)


def week_ranges() -> list[tuple[date, date]]:
    ranges = []
    start = PROJECT_START
    while start <= PROJECT_END:
        end = min(start + timedelta(days=6), PROJECT_END)
        ranges.append((start, end))
        start = end + timedelta(days=1)
    return ranges


def make_weekly(wb: Workbook) -> None:
    ws = wb.create_sheet("Tien_do_tuan")
    ws.sheet_view.showGridLines = False
    weeks = week_ranges()
    end_col = 6 + len(weeks)
    style_title(ws, "TIẾN ĐỘ THEO TUẦN", "Ô màu thể hiện đầu việc có hoạt động trong tuần; xem sheet Kế hoạch chi tiết để theo dõi ngày và tiêu chí nghiệm thu.", end_col)
    headers = ["WBS", "Giai đoạn", "Thành viên", "Công việc", "Bắt đầu", "Kết thúc"]
    for col, header in enumerate(headers, start=1):
        ws.cell(4, col, header)
    for idx, (start, end) in enumerate(weeks, start=7):
        ws.cell(4, idx, f"T{idx-6}\n{start.strftime('%d/%m')}–{end.strftime('%d/%m')}")
    style_header(ws, 4, 1, end_col, NAVY)
    phase_colors = {
        "Khởi động & đánh giá": "A9D18E",
        "Yêu cầu, thiết kế & baseline": "FFD966",
        "Hoàn thiện admin web": "9DC3E6",
        "Nâng chất lượng dịch": "C9B1FF",
        "Tối ưu tốc độ & ổn định": "F4B183",
        "Tích hợp frontend–backend": "76D7C4",
        "Kiểm thử, bảo mật & UAT": "FF9999",
        "Triển khai & bàn giao": "A5A5A5",
    }
    for idx, task in enumerate(TASKS, start=1):
        wbs, owner, start_s, phase, name, _, _, end_s, *_ = task
        row = idx + 4
        start = d(start_s)
        end = d(end_s)
        for col, value in enumerate([wbs, phase, owner, name, start, end], start=1):
            ws.cell(row, col, value)
        ws.cell(row, 5).number_format = "dd/mm/yyyy"
        ws.cell(row, 6).number_format = "dd/mm/yyyy"
        for week_col, (week_start, week_end) in enumerate(weeks, start=7):
            if start <= week_end and end >= week_start:
                ws.cell(row, week_col, "●")
                ws.cell(row, week_col).fill = PatternFill("solid", fgColor=phase_colors[phase])
                ws.cell(row, week_col).alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[row].height = 31
    last_row = 4 + len(TASKS)
    apply_body_style(ws, 5, last_row, 1, end_col)
    for row in range(5, last_row + 1):
        for col in range(7, end_col + 1):
            ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center")
    widths = {1: 8, 2: 26, 3: 27, 4: 38, 5: 13, 6: 13}
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width
    for col in range(7, end_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = 14
    ws.freeze_panes = "G5"
    ws.auto_filter.ref = f"A4:{get_column_letter(end_col)}{last_row}"
    ws.print_title_rows = "1:4"
    ws.print_area = f"A1:{get_column_letter(end_col)}{last_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1
    add_nav(ws)


def make_milestones(wb: Workbook) -> None:
    ws = wb.create_sheet("Moc_ban_giao")
    ws.sheet_view.showGridLines = False
    style_title(ws, "MỐC KIỂM SOÁT VÀ BÀN GIAO", "Mỗi mốc là một cổng kiểm soát; chỉ chuyển tiếp khi đầu ra và tiêu chí liên quan được xác nhận.", 7)
    headers = ["Mã mốc", "Ngày", "Tên mốc", "Đầu ra bắt buộc", "WBS liên quan", "Trạng thái", "Người xác nhận"]
    for col, header in enumerate(headers, start=1):
        ws.cell(4, col, header)
    style_header(ws, 4, 1, 7, NAVY)
    for idx, (code, due, name, output, wbs) in enumerate(MILESTONES, start=5):
        for col, value in enumerate([code, due, name, output, wbs, "Chưa đạt", "PM/Người nghiệm thu"], start=1):
            ws.cell(idx, col, value)
        ws.cell(idx, 2).number_format = "dd/mm/yyyy"
        ws.row_dimensions[idx].height = 48
    last_row = 4 + len(MILESTONES)
    apply_body_style(ws, 5, last_row, 1, 7)
    for row in range(5, last_row + 1):
        for col in [1, 2, 5, 6]:
            ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    dv = DataValidation(type="list", formula1='"Chưa đạt,Đạt có điều kiện,Đạt"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"F5:F{last_row}")
    ws.conditional_formatting.add(f"F5:F{last_row}", CellIsRule(operator="equal", formula=['"Đạt"'], fill=PatternFill("solid", fgColor=LIGHT_GREEN)))
    ws.conditional_formatting.add(f"F5:F{last_row}", CellIsRule(operator="equal", formula=['"Đạt có điều kiện"'], fill=PatternFill("solid", fgColor=LIGHT_AMBER)))
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 31
    ws.column_dimensions["D"].width = 50
    ws.column_dimensions["E"].width = 17
    ws.column_dimensions["F"].width = 18
    ws.column_dimensions["G"].width = 24
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:G{last_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    add_nav(ws)


def make_kpi(wb: Workbook) -> None:
    ws = wb.create_sheet("KPI_nghiem_thu")
    ws.sheet_view.showGridLines = False
    style_title(ws, "KPI VÀ TIÊU CHÍ NGHIỆM THU", "Các mục tiêu số tuyệt đối về AI/latency là ngưỡng đề xuất; phải xác nhận sau khi có baseline trên phần cứng và dữ liệu thực tế.", 8)
    headers = ["Mã", "Nhóm", "Chỉ số", "Cách đo", "Ngưỡng mục tiêu", "Thời điểm kiểm", "Ghi chú", "Kết quả thực tế"]
    for col, header in enumerate(headers, start=1):
        ws.cell(4, col, header)
    style_header(ws, 4, 1, 8, NAVY)
    for idx, row_data in enumerate(KPIS, start=5):
        for col, value in enumerate(row_data, start=1):
            ws.cell(idx, col, value)
        ws.cell(idx, 8, "Chưa đo")
        ws.row_dimensions[idx].height = 55
    last_row = 4 + len(KPIS)
    apply_body_style(ws, 5, last_row, 1, 8)
    for row in range(5, last_row + 1):
        for col in [1, 2, 6, 8]:
            ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    widths = [9, 17, 34, 45, 34, 22, 35, 22]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:H{last_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    add_nav(ws)


def make_risks(wb: Workbook) -> None:
    ws = wb.create_sheet("Rui_ro")
    ws.sheet_view.showGridLines = False
    style_title(ws, "SỔ ĐĂNG KÝ RỦI RO", "Rà soát tối thiểu mỗi tuần và tại các cổng Quality, Performance, Security, UAT, Go/No-Go.", 11)
    headers = ["Mã", "Rủi ro", "Nhóm", "Khả năng", "Ảnh hưởng", "Mức", "Biện pháp phòng ngừa/ứng phó", "Chủ sở hữu", "Hạn kiểm soát", "Trạng thái", "Ghi chú cập nhật"]
    for col, header in enumerate(headers, start=1):
        ws.cell(4, col, header)
    style_header(ws, 4, 1, 11, NAVY)
    for idx, row_data in enumerate(RISKS, start=5):
        for col, value in enumerate(row_data, start=1):
            if col == 9 and isinstance(value, str) and value != "Hàng tuần":
                value = d(value)
            ws.cell(idx, col, value)
        ws.cell(idx, 10, "Đang theo dõi")
        ws.cell(idx, 11, "")
        if isinstance(ws.cell(idx, 9).value, date):
            ws.cell(idx, 9).number_format = "dd/mm/yyyy"
        ws.row_dimensions[idx].height = 60
    last_row = 4 + len(RISKS)
    apply_body_style(ws, 5, last_row, 1, 11)
    for row in range(5, last_row + 1):
        for col in [1, 3, 4, 5, 6, 9, 10]:
            ws.cell(row, col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    dv = DataValidation(type="list", formula1='"Đang theo dõi,Đã giảm thiểu,Đã xảy ra,Đóng"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"J5:J{last_row}")
    ws.conditional_formatting.add(f"F5:F{last_row}", CellIsRule(operator="equal", formula=['"P1"'], fill=PatternFill("solid", fgColor=LIGHT_RED)))
    ws.conditional_formatting.add(f"J5:J{last_row}", CellIsRule(operator="equal", formula=['"Đóng"'], fill=PatternFill("solid", fgColor=LIGHT_GREEN)))
    widths = [8, 36, 16, 14, 14, 9, 55, 27, 16, 18, 35]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:K{last_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1
    add_nav(ws)


def validate_workbook(path: Path) -> None:
    wb = load_workbook(path, data_only=False)
    assert wb.sheetnames == ["Tong_quan", "Ke_hoach_chi_tiet", "Tien_do_tuan", "Moc_ban_giao", "KPI_nghiem_thu", "Rui_ro"]
    ws = wb["Ke_hoach_chi_tiet"]
    assert ws.max_row >= len(TASKS) + 4
    starts: list[Any] = [ws.cell(row, 4).value for row in range(5, 5 + len(TASKS))]
    ends: list[Any] = [ws.cell(row, 9).value for row in range(5, 5 + len(TASKS))]
    assert min(starts).date() == PROJECT_START
    assert max(ends).date() == PROJECT_END
    assert all(s.date() <= e.date() for s, e in zip(starts, ends))
    assert all(PROJECT_START <= s.date() <= PROJECT_END for s in starts)
    assert all(PROJECT_START <= e.date() <= PROJECT_END for e in ends)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    make_overview(wb)
    make_detail(wb)
    make_weekly(wb)
    make_milestones(wb)
    make_kpi(wb)
    make_risks(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    wb.save(OUTPUT)
    validate_workbook(OUTPUT)
    print(f"Created: {OUTPUT}")
    print(f"Tasks: {len(TASKS)} | Milestones: {len(MILESTONES)} | KPIs: {len(KPIS)} | Risks: {len(RISKS)}")


if __name__ == "__main__":
    main()

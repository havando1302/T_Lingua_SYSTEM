# BÁO CÁO TIẾN ĐỘ DỰ ÁN T-LINGUA

## Giai đoạn 25/09/2026–08/10/2026

**Dự án:** Hệ thống AI dịch thuật thời gian thực T-Lingua  
**Thành viên:** Hà Văn Đô, Nguyễn Quang Thọ  
**Giai đoạn báo cáo:** Từ ngày 25/09/2026 đến hết ngày 08/10/2026  
**Commit kết thúc kỳ báo cáo:** `fb10a6a4ff467bff172e0c423cc0eec7a0e5cc58`

## 1. Tóm tắt điều hành

Trong giai đoạn 25/09–08/10, dự án chuyển từ trạng thái có nền tảng dịch, benchmark và quy trình QA sang một hệ thống có **Training Center**, quản lý dataset/job/model, giao diện quản trị hoàn chỉnh hơn, phiên đăng nhập có refresh cookie, ứng dụng Flutter xử lý barge-in và một lớp hardening bảo mật sâu hơn.

Các kết quả nổi bật:

- Xây dựng Training Center và 22 endpoint phục vụ vòng đời dataset, job huấn luyện và model artifact.
- Bổ sung worker huấn luyện LoRA cho NLLB và Whisper, hỗ trợ quy trình chạy tách biệt trên Google Colab.
- Hoàn thiện Dashboard, Analytics, Dictionary, QA, Settings, Users, Account và phân quyền theo vai trò.
- Khắc phục lỗi người dùng bị đưa về trang đăng nhập sau khi F5 bằng refresh cookie và phục hồi phiên.
- Bổ sung xoay refresh token, chống replay, MFA và thu hồi phiên.
- Khắc phục luồng audio khi người dùng bắt đầu câu mới trong lúc câu trước đang phát.
- Mã hóa lịch sử Flutter, backup và dữ liệu nhạy cảm; làm sạch dữ liệu nhạy cảm khỏi lịch sử Git đang được tham chiếu.
- Nâng cấp và hardening runtime GPU, Docker và dependency.
- Cuối kỳ, toàn bộ test tự động hiện có đạt; không có lỗ hổng High/Medium từ Bandit và không có CVE đã biết trong các dependency được quét.

Hệ thống đạt mức **sẵn sàng có điều kiện** cho thử nghiệm có kiểm soát. Chưa nên tuyên bố production hoàn chỉnh do còn rủi ro cache GitHub cũ, chưa chạy container production thật, chưa hoàn tất đóng gói Android release và chưa chạy training/acoustic/load test trong môi trường thực tế.

## 2. Phạm vi và bằng chứng

Báo cáo được xây dựng từ:

- Lịch sử Git trong khoảng 25/09–08/10.
- Source code hiện tại của backend, admin web và Flutter.
- Artifact benchmark và verification.
- Kết quả kiểm thử lại toàn hệ thống ngày 08/10.
- Tài liệu vận hành Training Center trên Colab.

Trong giai đoạn có 10 commit được ghi nhận. Tổng thống kê commit là khoảng 33.587 dòng thêm và 4.409 dòng xóa. Con số này bao gồm mã nguồn, test, tài liệu, script và artifact benchmark; không được dùng như chỉ số năng suất cá nhân.

> Từ 25/09 đến 29/09 không có commit riêng trong lịch sử hiện tại. Phần công việc được tích hợp và đưa vào commit lớn ngày 30/09. Vì vậy báo cáo không suy diễn tiến độ theo từng ngày trong khoảng này.

## 3. Tiến độ theo mốc thời gian

### 25/09/2026 – Hoàn thiện kỹ thuật sau giai đoạn baseline

Nhóm hoàn thiện và đối chiếu các hạng mục còn thiếu của giai đoạn trước:

- Corpus dịch 500 trường hợp và audio benchmark 100 mẫu.
- Benchmark NLLB, STT, TTS, A/B và soak.
- Quy trình QA và biểu mẫu hai reviewer.
- 121 backend test và 21 browser test đạt.
- Admin build/lint đạt; Flutter analyze không phát hiện lỗi.
- Dashboard, Analytics, Users, API Keys, Dictionary, History, QA và Settings đã có nền tảng vận hành.

Đây là đầu vào trực tiếp cho giai đoạn xây dựng Training Center.

### 30/09/2026 – Tích hợp hệ thống và xây dựng Training Center

Commit `bcdf32d` là mốc đầu tiên lịch sử Git ghi nhận Training Center. Commit này thay đổi 244 tệp, thêm 27.043 dòng và xóa 3.024 dòng, đồng thời tích hợp nhiều phần việc đã được chuẩn bị trước đó.

Các thành phần Training AI được bổ sung:

- Trang `TrainingCenter.tsx` trên admin web.
- `training_routes.py` cung cấp API điều khiển.
- `training_worker.py` thực thi job huấn luyện tách biệt.
- `training_control.py` quản lý dataset, artifact và trạng thái.
- Script `train_nllb.py` và `train_whisper.py`.
- `requirements-training.txt` tách dependency huấn luyện khỏi inference.
- Tài liệu vận hành `COLAB_TRAINING_CENTER.md`.

Training Center hỗ trợ các nhóm chức năng:

1. Tổng quan dữ liệu và runtime.
2. Preview dữ liệu từ QA.
3. Tạo dataset từ dữ liệu QA hoặc upload.
4. Validate, freeze, checksum và download dataset.
5. Tạo, theo dõi, hủy và đọc log job.
6. Theo dõi event và event stream.
7. Quản lý model artifact.
8. Validate, canary, promote và rollback model.
9. Playground cho NLLB và Whisper.

Tổng cộng có 22 endpoint Training Center trong phiên bản cuối kỳ.

Thiết kế an toàn chính:

- Training và inference không dùng GPU cùng lúc trên Colab.
- Dataset phải được validate và freeze trước khi tạo job.
- Worker kiểm tra checksum của dataset.
- Chỉ sử dụng trainer và model revision được allowlist.
- UI chỉ cho phép LoRA, không cho phép full fine-tuning.
- Việc đưa model mới lên runtime vẫn cần thao tác vận hành và restart; hệ thống không tuyên bố hot-swap khi chưa thực hiện.

### 02/10/2026 – Hoàn thiện giao diện quản trị và luồng Training Center

Commit `abf9332` thay đổi 22 tệp, thêm 2.365 dòng và xóa 424 dòng.

Các công việc chính:

- Nâng cấp Analytics, Dictionary, QA và Settings.
- Cải thiện Dashboard, Login, Users và Sidebar.
- Hoàn thiện giao diện Training Center.
- Đồng bộ admin API và training API.
- Cải thiện training control và worker.
- Bổ sung test cho các extension của admin.
- Bổ sung cấu hình kiểm tra kiểu bằng Pyrefly.

### 03/10/2026 – Hoàn thiện phân quyền và trang tài khoản

Commit `f44c8d0` thay đổi 17 tệp, thêm 492 dòng và xóa 143 dòng.

Các kết quả:

- Bổ sung trang Account.
- Cập nhật route guard, Sidebar và logic xác định vai trò.
- Phân tách quyền employee, admin và superadmin.
- Bổ sung quyền báo cáo, quản trị và QA ở backend.
- Thêm test cho role và các thao tác bị cấm.
- Cập nhật benchmark full pipeline phục vụ theo dõi hiệu năng.

### 04/10/2026 – Đồng bộ UI, backend và nhận diện sản phẩm

Commit `bfb807b` thay đổi 68 tệp, thêm 843 dòng và xóa 325 dòng.

Các công việc chính:

- Đồng bộ UI trên Dashboard, Analytics, QA, Settings và Training Center.
- Chuẩn hóa tên và nhận diện T-Lingua trên web/mobile/desktop.
- Bổ sung thông báo có thời hạn trên admin.
- Hoàn thiện model manager, training worker và các script training.
- Cải thiện database migration và cấu trúc dữ liệu.
- Cập nhật audio storage và training audio storage.
- Cải thiện Flutter Home, History, Settings và luồng dịch.
- Cập nhật Docker Compose và tài liệu Training Center.

### 05/10/2026 – Khắc phục phiên đăng nhập và F5

Commit `085da98` thay đổi 32 tệp, thêm 1.233 dòng và xóa 242 dòng.

Mục tiêu chính là giải quyết tình trạng người dùng nhấn F5 bị đưa về Login và phải đăng nhập lại.

Các thay đổi:

- Bổ sung refresh cookie riêng tại `/api/session`.
- Cookie có `HttpOnly`, `SameSite=Strict`; production có `Secure`.
- Admin web thử phục hồi phiên bằng refresh cookie khi tải lại trang.
- Refresh token được xoay sau mỗi lần sử dụng.
- Refresh token cũ bị từ chối khi replay.
- Logout xóa cookie và thu hồi phiên đang sử dụng.
- Bổ sung `/api/session/refresh`, `/api/session/logout` và `/api/session/me`.
- Cải thiện xử lý lỗi tạm thời để tránh logout người dùng sai nguyên nhân.
- Mở rộng test authentication, boundary, performance và lifecycle.

Kết quả cuối kỳ: browser test xác nhận phiên đăng nhập sống qua full-page reload.

### 07/10/2026 – Hoàn thiện Settings và hardening bảo mật

Hai commit `5d7a99e` và `c099ba4` tập trung vào bảo mật, vận hành và độ ổn định.

Các hạng mục chính:

- Hoàn thiện Dashboard, Analytics và Settings.
- Pin model Hugging Face bằng revision bất biến.
- Bổ sung model registry và kiểm tra model được phép.
- Cải thiện health/readiness và telemetry.
- Mã hóa lịch sử Flutter bằng khóa lưu trong secure storage của hệ điều hành.
- Bổ sung test barge-in cho audio player và microphone.
- Mã hóa backup bằng AES-256-GCM và kiểm tra tính toàn vẹn khi restore.
- Chống path traversal khi giải nén backup.
- Bổ sung script hardening ACL cho Windows.
- Hardening Docker: chạy non-root, filesystem read-only, drop capability, giới hạn tài nguyên và health check.
- Nâng cấp các dependency có cảnh báo bảo mật.
- Loại bỏ DeepFilterNet khỏi runtime hardened do phụ thuộc vào stack torchaudio cũ.

DeepFilter bị tắt là một đánh đổi có chủ đích: giảm rủi ro dependency nhưng cần đánh giá lại độ chính xác STT trong môi trường nhiều tiếng ồn.

### 08/10/2026 – Nâng cấp runtime GPU và hoàn thiện ACL

Commit `cd7cbd8` nâng runtime lên:

- PyTorch `2.13.0+cu130`.
- CUDA runtime 13.0.
- GPU kiểm thử: NVIDIA GeForce RTX 3050 6GB Laptop GPU.
- Torch xác nhận `torch.cuda.is_available() == True`.

OSV không ghi nhận lỗ hổng đã biết cho phiên bản Torch này tại thời điểm kiểm tra.

Commit `fb10a6a` sửa script hardening ACL để tương thích PowerShell 5.1 trên Windows.

## 4. Kết quả theo nhóm chức năng

### 4.1. Training AI và quản lý dữ liệu

| Hạng mục | Trạng thái 08/10 |
|---|---|
| Preview dữ liệu QA | Hoàn thành |
| Tạo/upload dataset | Hoàn thành |
| Validate/freeze/checksum | Hoàn thành |
| Tạo và theo dõi job | Hoàn thành |
| Event/log/SSE | Hoàn thành |
| NLLB/Whisper LoRA trainer | Đã có mã nguồn |
| Model artifact registry | Hoàn thành |
| Canary/promote/rollback | Hoàn thành control plane |
| Chạy training thật trên Colab | Chưa có bằng chứng nghiệm thu cuối kỳ |
| Hot-swap model không restart | Chưa hỗ trợ |

### 4.2. Trang quản trị

Đã hoàn thiện hoặc nâng cấp:

- Login và MFA.
- Account.
- Dashboard.
- Analytics nâng cao.
- Users và phân quyền.
- API Keys.
- Dictionary.
- History và QA.
- Settings và model deployment.
- Training Center.
- Responsive/mobile menu.

Các bộ lọc thời gian, percentile, phân trang, tìm kiếm, trạng thái lỗi và validation ngày tùy chỉnh đã được kiểm thử trên Chrome headless.

### 4.3. Flutter và realtime audio

Các thay đổi quan trọng:

- Phiên khách do server phát hành.
- WebSocket có xác thực và quản lý `turn_id`.
- Microphone và audio player có state machine.
- Khi bắt đầu câu mới, playback cũ bị dừng trước khi mở microphone.
- Chunk âm thanh đến muộn của lượt cũ bị loại bỏ.
- Lịch sử cục bộ được mã hóa.
- API release yêu cầu HTTPS và tự chuyển WebSocket sang WSS.

### 4.4. Bảo mật và vận hành

Đã thực hiện:

- Refresh token rotation và chống replay.
- MFA cho tài khoản tương tác theo chính sách production.
- Rate limit cho login, guest và API.
- Trusted Host, CORS allowlist và giới hạn request body.
- Security header `nosniff`, `no-referrer`, `no-store` và HSTS ở production.
- Mã hóa backup và lịch sử Flutter.
- Model revision allowlist.
- Docker non-root/read-only.
- Làm sạch `admin.db` và `translation_memory.json` khỏi lịch sử nhánh `main` đang được tham chiếu.
- Secret scan trên mã nguồn hiện tại không phát hiện chuỗi khớp mẫu secret.

## 5. Kết quả kiểm thử cuối kỳ ngày 08/10

### 5.1. Kiểm thử tự động

| Hạng mục | Kết quả |
|---|---:|
| Backend pytest | 135 đạt, 0 thất bại |
| Backend subtests | 10 đạt |
| Admin browser | 37/37 đạt |
| JavaScript browser errors | 0 |
| Flutter test | 2/2 đạt |
| Flutter analyze | Không phát hiện lỗi |
| Admin production build | Thành công, 611 module |
| Admin lint | Đạt, 2 cảnh báo Fast Refresh không chặn |

Backend test chạy trong 72,75 giây. Admin browser test chạy trên Chrome 155 trong 10,9 giây. Flutter analyze hoàn thành trong 61,3 giây.

### 5.2. Kiểm thử phiên HTTP thật

Backend được chạy với database cô lập, không sử dụng dữ liệu thật.

| Thao tác | HTTP | Độ trễ |
|---|---:|---:|
| Liveness | 200 | 16,70 ms |
| Readiness | 200 | 3,14 ms |
| Tạo phiên khách | 200 | 24,67 ms |
| Đọc thông tin phiên | 200 | 6,18 ms |
| Refresh thiếu cookie | 401 | 3,58 ms |
| Host giả | 400 | 1,37 ms |
| Logout | 204 | 17,85 ms |
| Dùng token đã logout | 401 | 3,43 ms |

Kiểm thử phiên admin thật xác nhận:

- Login trả access token và refresh cookie.
- Refresh xoay cả access và refresh token.
- Refresh token cũ bị replay trả 401.
- Token giả trả 401.
- Body đăng nhập 70 KB trả 413.
- Origin không được phép trả 403.
- Cookie production có `Secure`, `HttpOnly`, `SameSite=Strict` và path `/api/session`.

### 5.3. Rate limit và tải nhẹ

- Login brute-force bị chặn bằng 429 sau khi đạt ngưỡng.
- Header `Retry-After` được gửi.
- 120 phiên khách/phút được chấp nhận trong local test; phiên thứ 121 trả 429.
- 100 readiness request với 20 luồng đồng thời: 100 thành công, 0 lỗi.
- Readiness p50: 18,43 ms; p95: 25,71 ms; cao nhất: 28,74 ms.

Đây là kiểm thử health/database nhẹ, không phải load test pipeline STT–NLLB–TTS đồng thời.

### 5.4. Kiểm thử bảo mật

| Công cụ/hạng mục | Kết quả |
|---|---:|
| `npm audit --omit=dev` | 0 lỗ hổng |
| `pip-audit` | Không có CVE đã biết trong package được nhận diện |
| OSV cho Torch 2.13.0 | 0 lỗ hổng |
| Bandit High | 0 |
| Bandit Medium | 0 |
| Bandit Low | 21 |
| Secret pattern scan | 0 kết quả |
| Sensitive paths trong `main` | Không còn |

Các cảnh báo Bandit mức Low chủ yếu là chuỗi bị nhận nhầm là mật khẩu, `try/except/pass` và cảnh báo subprocess. Training worker sử dụng danh sách tham số với `shell=False`, module cố định và revision allowlist; chưa phát hiện đường command injection từ dữ liệu người dùng.

### 5.5. Backup và triển khai

- Có một backup mã hóa.
- Khôi phục backup thành công và xác minh được 2 tệp.
- Hai file Docker Compose parse YAML thành công.
- Docker chưa được cài trên máy kiểm thử nên chưa build/run container production thật.
- Flutter Web release build thành công trong 50,3 giây.
- Artifact Web có 41 tệp, tổng 41.944.833 byte và không chứa endpoint localhost.
- Chrome CDP xác nhận giao diện Flutter có 22 node semantics và không có console exception.
- APK Android chưa build được do máy thiếu Android SDK.

## 6. Lỗi và rủi ro còn mở

### P0 – Dữ liệu lịch sử GitHub có thể còn trong cache

Nhánh `main` hiện đã được rewrite và không còn hai đường dẫn dữ liệu nhạy cảm. Tuy nhiên, URL raw/SHA cũ từng vẫn trả nội dung từ cache GitHub.

Cần gửi GitHub Support yêu cầu dereference, garbage collection và xóa cached view cho các commit cũ liên quan. Rewrite Git history không tự bảo đảm object biến mất ngay khỏi hạ tầng GitHub.

### P1 – Điều kiện triển khai production chưa hoàn tất

- Chưa build và chạy Docker image production thật.
- Chưa xác nhận chạy script ACL cuối cùng bằng Administrator sau khi hoàn tất công việc.
- Android chưa có SDK trong máy kiểm thử.
- Android vẫn dùng application ID mẫu và release signing bằng debug key.
- Chưa có bằng chứng chạy một job fine-tuning hoàn chỉnh trên Colab rồi đánh giá, đăng ký và rollback artifact.

### P2 – Thu hồi access token theo session family

Kiểm thử phát hiện access token được cấp trước một lần refresh vẫn còn hiệu lực sau khi logout bằng access token mới. Cửa sổ tồn tại tối đa là 15 phút.

Đề xuất:

- Bổ sung `session_family_id`.
- Logout thu hồi toàn bộ access/refresh token trong cùng family.
- Bổ sung regression test cho chuỗi login → refresh → logout → mọi access token đều 401.

### P2 – Chất lượng audio và tải thực tế

- Chưa kiểm thử microphone/loa vật lý trong môi trường ồn.
- DeepFilter bị tắt trong hardened runtime.
- Chưa có load/endurance test nhiều người dùng trên pipeline AI.
- Chưa đo first-audio latency và chất lượng TTS bằng người nghe độc lập.

## 7. Đánh giá tiến độ cuối kỳ

| Nhóm công việc | Đánh giá |
|---|---|
| Nền tảng backend/realtime | Đạt kỹ thuật |
| Admin web | Đạt kiểm thử tự động |
| Phiên đăng nhập/F5 | Đạt, còn P2 session family |
| Training Center control plane | Hoàn thành chức năng chính |
| Training model thực tế | Chưa nghiệm thu end-to-end |
| Flutter realtime/barge-in | Đạt test logic |
| Dữ liệu/QA | Có nền tảng, cần thêm dữ liệu thật và reviewer |
| Bảo mật ứng dụng | Đã harden đáng kể, còn P0 GitHub cache |
| Docker/Android production | Chưa nghiệm thu |

Đánh giá tổng thể cuối kỳ: **hệ thống đạt mức sẵn sàng có điều kiện cho demo và thử nghiệm có kiểm soát; chưa đủ điều kiện nghiệm thu production công khai**.

## 8. Kế hoạch đề xuất sau ngày 08/10

1. Gửi yêu cầu purge cache/object cũ đến GitHub Support.
2. Bổ sung session family và thu hồi toàn bộ token khi logout.
3. Chạy script hardening ACL cuối cùng bằng Administrator.
4. Cài Docker và chạy build/up/health test trong cấu hình production.
5. Cấu hình application ID và release keystore Android; build APK/AAB release.
6. Chạy một job NLLB hoặc Whisper LoRA thật trên Colab bằng dataset đã freeze.
7. Đánh giá candidate model trên tập test không dùng để train.
8. Thực hiện human review và TTS MOS.
9. Chạy acoustic test bằng microphone thật và load/endurance test nhiều người dùng.
10. Chỉ promote model sau khi quality gate đạt và rollback được kiểm chứng.

## 9. Danh sách commit trong kỳ

| Ngày | Commit | Nội dung |
|---|---|---|
| 30/09 | `bcdf32d` | Tích hợp hệ thống và Training Center |
| 30/09 | `96de785` | Cập nhật README |
| 02/10 | `abf9332` | Hoàn thiện UI admin và training flow |
| 03/10 | `f44c8d0` | Hoàn thiện role/phân quyền và Account |
| 04/10 | `bfb807b` | Đồng bộ UI, backend và Flutter |
| 05/10 | `085da98` | Khắc phục phiên đăng nhập và F5 |
| 07/10 | `5d7a99e` | Settings, bảo mật, backup và audio barge-in |
| 07/10 | `c099ba4` | Khắc phục các phát hiện security audit còn lại |
| 08/10 | `cd7cbd8` | Nâng cấp hardened GPU runtime |
| 08/10 | `fb10a6a` | Tương thích Windows ACL hardening |

## 10. Nguồn đối chiếu

- `docs/progress_2026-09-24/BAO_CAO_TIEN_DO_HOAN_THIEN_KY_THUAT_25-09-2026.md`
- `docs/progress_2026-09-24/evidence/verification_summary.json`
- `docs/COLAB_TRAINING_CENTER.md`
- `backend/app/api/training_routes.py`
- `backend/app/training_worker.py`
- `backend/app/services/training_control.py`
- `admin_web/src/pages/TrainingCenter.tsx`
- `backend/app/core/security.py`
- `backend/app/core/session_cookie.py`
- `frontend/test/barge_in_playback_test.dart`
- `scripts/secure_backup.py`
- `scripts/harden_windows_acl.ps1`
- Lịch sử Git từ `bcdf32d` đến `fb10a6a`.

### Ghi chú về tính toàn vẹn báo cáo

- Commit ngày 30/09 là lần đầu Git ghi nhận các file Training Center, nhưng không chứng minh toàn bộ nội dung được viết riêng trong ngày đó.
- Một số artifact full-pipeline có timestamp 02/10 và được tính trong kỳ báo cáo này, không được tính ngược vào báo cáo trước Training AI.
- Số liệu kiểm thử cuối kỳ được lấy từ lần chạy lại trên commit `fb10a6a` với database test cô lập.
- Các giới hạn môi trường như thiếu Docker và Android SDK được ghi là chưa nghiệm thu, không được coi là test đạt.

# -*- coding: utf-8 -*-
"""
Master Sequence Diagrams Generator for T-Lingua System.
Generates all 20 UML Sequence Diagrams (Figures 3.8 to 3.27)
strictly according to Section 2.1.4 Use Case specifications
and Section 3.2 Class Lifelines with Robustness Analysis Icons.
All images saved to C:\\Du_an\\T_Langua_Test\\docs\\img\\tt
Monochrome black styling, accented Vietnamese messages, zero watermark, zero internal title.
"""
import os
import sys

sys.path.insert(0, r"C:\Du_an\T_Langua_Test")

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from scripts.sequence_builder import SequenceDiagram

TT_IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img\tt"
os.makedirs(TT_IMG_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# NHÓM 1: DỊCH GIỌNG NÓI VÀ HỘI THOẠI (UC1.1 - UC1.3)
# -----------------------------------------------------------------------------

def gen_fig_3_8():
    """UC1.1 - Dịch giọng nói một chiều thời gian thực"""
    sd = SequenceDiagram(width=1460)
    sd.add_lifeline("user", "Người dùng", "actor")
    sd.add_lifeline("ui", ":RealtimeVoiceScreen", "boundary")
    sd.add_lifeline("ws", ":WebSocketRouter", "boundary")
    sd.add_lifeline("actor", ":SessionActor", "control")
    sd.add_lifeline("vad", ":WebRtcVadStream", "control")
    sd.add_lifeline("stt", ":STTWorker (Whisper)", "worker")
    sd.add_lifeline("trans", ":TransWorker (NLLB)", "worker")
    sd.add_lifeline("tts", ":TTSWorker (VITS)", "worker")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("user", "ui", "1: Nhấn giữ nút Mic()")
    sd.message("ui", "ws", "2: Kết nối WebSocket (ws://.../translate)")
    sd.message("ws", "actor", "3: Khởi tạo phiên làm việc (create_session)")
    sd.message("actor", "ui", "4: Chấp nhận kết nối (101 Protocols)", is_return=True)
    sd.message("user", "ui", "5: Bắt đầu phát âm câu nói")
    sd.message("ui", "actor", "6: Truyền luồng PCM 16kHz (20ms/gói)")
    sd.message("actor", "vad", "7: Đẩy khối âm thanh vào VAD (push)")
    sd.message("vad", "actor", "8: Bắt đầu tiếng nói (SPEECH_START)")
    sd.message("actor", "ui", "9: Báo bắt đầu nói & hiển thị sóng âm")
    sd.message("user", "ui", "10: Dứt lời nói (Khoảng lặng)")
    sd.message("ui", "actor", "11: Truyền tiếp các gói âm thanh tĩnh")
    sd.message("actor", "vad", "12: Đẩy khối âm thanh tĩnh (push)")
    sd.message("vad", "actor", "13: Khoảng lặng 500ms (SILENCE_CUTOFF)")
    sd.message("actor", "stt", "14: Yêu cầu nhận dạng giọng nói (transcribe)")
    sd.message("stt", "actor", "15: Trả về văn bản nguồn (source_text, stt_ms)", is_return=True)
    sd.message("actor", "ui", "16: Hiển thị văn bản nhận dạng tức thời")
    sd.message("actor", "trans", "17: Yêu cầu dịch máy (translate 'vi' -> 'en')")
    sd.message("trans", "actor", "18: Trả về bản dịch tiếng Anh (target_text, trans_ms)", is_return=True)
    sd.message("actor", "ui", "19: Hiển thị bản dịch tức thời trên màn hình")
    sd.message("actor", "tts", "20: Yêu cầu tổng hợp giọng đọc (synthesize 'en')")
    sd.message("tts", "actor", "21: Trả về luồng byte âm thanh (wav_bytes, tts_ms)", is_return=True)
    sd.message("actor", "ui", "22: Truyền luồng âm thanh nhị phân (wav_bytes)")
    sd.message("ui", "user", "23: Phát âm thanh câu dịch qua loa ngoài")
    sd.message("actor", "db", "24: Lưu vết lượt dịch & đo kiểm vi mô (save_turn)")
    sd.message("db", "actor", "25: Xác nhận lưu trữ thành công (log_id, SUCCESS)", is_return=True)

    out = os.path.join(TT_IMG_DIR, "hinh_3_8_seq_uc1_1_dich_giong_noi_mot_chieu.png")
    sd.export_png(out)

def gen_fig_3_9():
    """UC1.2 - Hội thoại song ngữ hai chiều"""
    sd = SequenceDiagram(width=1240)
    sd.add_lifeline("user_a", "Người dùng A (VN)", "actor")
    sd.add_lifeline("user_b", "Người dùng B (EN)", "actor")
    sd.add_lifeline("ui", ":BilingualConversationScreen", "boundary")
    sd.add_lifeline("actor", ":SessionActor", "control")
    sd.add_lifeline("mutex", ":MicMutex", "control")
    sd.add_lifeline("pipe", ":AIPipelineWorkers", "worker")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("user_a", "ui", "1: Nhấn giữ Mic A nói tiếng Việt")
    sd.message("ui", "actor", "2: Yêu cầu chiếm quyền mic ('side_a')")
    sd.message("actor", "mutex", "3: Xin cấp khóa tranh chấp (acquire)")
    sd.message("mutex", "actor", "4: Cấp khóa thành công (LockAcquired)", is_return=True)
    sd.message("actor", "ui", "5: Kích hoạt Mic A, vô hiệu hóa Mic B")

    sd.frame_start("opt", "Xung đột: Người dùng B nhấn Mic B cùng lúc")
    sd.message("user_b", "ui", "6: Nhấn giữ Mic B đồng thời")
    sd.message("ui", "actor", "7: Yêu cầu chiếm mic ('side_b')")
    sd.message("actor", "mutex", "8: Xin cấp khóa tranh chấp (acquire)")
    sd.message("mutex", "actor", "9: Từ chối do mic đang bận (LockRejected)", is_return=True)
    sd.message("actor", "ui", "10: Rung phản hồi báo mic đang bận")
    sd.frame_end()

    sd.message("user_a", "ui", "11: Thả Mic A / Dứt câu nói")
    sd.message("ui", "actor", "12: Đóng gói và gửi âm thanh câu nói")
    sd.message("actor", "pipe", "13: Điều phối chuỗi AI (Whisper -> NLLB -> VITS)")
    sd.message("pipe", "actor", "14: Trả về câu dịch tiếng Anh & âm thanh", is_return=True)
    sd.message("actor", "mutex", "15: Giải phóng khóa micrô (release)")
    sd.message("actor", "ui", "16: Phát âm thanh câu dịch & mở khóa Mic B")
    sd.message("actor", "db", "17: Lưu lượt đối thoại (TranslationLog)")

    out = os.path.join(TT_IMG_DIR, "hinh_3_9_seq_uc1_2_hoi_thoai_song_ngu_hai_chieu.png")
    sd.export_png(out)

def gen_fig_3_10():
    """UC1.3 - Tương tác với kết quả dịch"""
    sd = SequenceDiagram(width=1420)
    sd.add_lifeline("user", "Người dùng", "actor")
    sd.add_lifeline("ui", ":RealtimeVoiceScreen", "boundary")
    sd.add_lifeline("player", ":AudioPlayer", "control")
    sd.add_lifeline("clip", ":ClipboardManager", "control")
    sd.add_lifeline("local_db", ":LocalStorage (SQLite)", "database")
    sd.add_lifeline("fb_ctrl", ":FeedbackController", "control")
    sd.add_lifeline("qa_ent", ":QualityReview", "entity")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("user", "ui", "1: Chọn thao tác trên thẻ kết quả dịch")

    sd.frame_start("alt", "Thao tác 1: Phát lại âm thanh theo tốc độ đã chọn")
    sd.message("user", "ui", "2a: Nhấn nút Phát lại âm thanh")
    sd.message("ui", "player", "3a: play_audio(wav_bytes, speed)")
    sd.message("player", "user", "4a: Phát âm thanh câu dịch ra loa ngoài")

    sd.frame_else("Thao tác 2: Sao chép bản dịch vào bộ nhớ tạm")
    sd.message("user", "ui", "2b: Nhấn nút Sao chép văn bản")
    sd.message("ui", "clip", "3b: copy_to_clipboard(target_text)")
    sd.message("clip", "ui", "4b: Đã lưu vào bộ nhớ tạm", is_return=True)
    sd.message("ui", "user", "5b: Hiển thị thông báo 'Đã sao chép vào bộ nhớ'")

    sd.frame_else("Thao tác 3: Lưu bản ghi vào lịch sử cục bộ")
    sd.message("user", "ui", "2c: Nhấn nút Lưu vào lịch sử cục bộ")
    sd.message("ui", "local_db", "3c: insert_local_history(TurnData)")
    sd.message("local_db", "ui", "4c: Lưu thành công (local_id)", is_return=True)
    sd.message("ui", "user", "5c: Cập nhật trạng thái đã lưu vào lịch sử")

    sd.frame_else("Thao tác 4: Gắn cờ gửi khối kiểm soát chất lượng QA")
    sd.message("user", "ui", "2d: Nhấn nút Gắn cờ & nhập lý do nghi ngờ")
    sd.message("ui", "fb_ctrl", "3d: POST /api/v1/feedback/flag {text, lang, is_voice, audio_ref}")
    sd.message("fb_ctrl", "qa_ent", "4d: create_qa_review(TurnPayload, status='PENDING')")
    sd.message("qa_ent", "db", "5d: INSERT INTO quality_reviews")
    sd.message("db", "qa_ent", "6d: Xác nhận tạo phiếu QA thành công", is_return=True)
    sd.message("fb_ctrl", "ui", "7d: 200 OK {message: 'Đã chuyển vào hàng đợi QA'}")
    sd.message("ui", "user", "8d: Hiển thị thông báo 'Đã gửi phản hồi kiểm soát chất lượng'")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_10_seq_uc1_3_tuong_tac_ket_qua_dich.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 2: LỊCH SỬ VÀ CẤU HÌNH ỨNG DỤNG (UC2.1 - UC2.3)
# -----------------------------------------------------------------------------

def gen_fig_3_11():
    """UC2.1 - Quản lý lịch sử dịch (Lưu trữ và tương tác 100% cục bộ trên thiết bị di động)"""
    sd = SequenceDiagram(width=1080)
    sd.add_lifeline("user", "Người dùng", "actor")
    sd.add_lifeline("ui", ":HistoryScreen", "boundary")
    sd.add_lifeline("ctrl", ":HistoryController", "control")
    sd.add_lifeline("db", ":LocalStorage (SQLite)", "database")
    sd.add_lifeline("player", ":AudioPlayer", "control")

    sd.message("user", "ui", "1: Mở mục Lịch sử từ thanh điều hướng")
    sd.message("ui", "ctrl", "2: Yêu cầu tải danh sách lịch sử dịch cục bộ")
    sd.message("ctrl", "ctrl", "3: Kiểm tra trạng thái bật lưu lịch sử (is_enabled)")
    sd.message("ctrl", "db", "4: Truy vấn danh sách bản ghi theo thời gian gần nhất")
    sd.message("db", "ctrl", "5: Danh sách bản dịch đã lưu trong bộ nhớ máy", is_return=True)
    sd.message("ctrl", "ui", "6: Gửi danh sách dữ liệu lịch sử hiển thị", is_return=True)
    sd.message("ui", "user", "7: Hiển thị danh sách các câu dịch theo dòng thời gian")

    sd.frame_start("alt", "Xem chi tiết & phát lại âm thanh cục bộ")
    sd.message("user", "ui", "8: Chạm xem chi tiết bản ghi & nhấn nút Loa")
    sd.message("ui", "player", "9: Yêu cầu phát lại âm thanh câu nói đã lưu")
    sd.message("player", "user", "10: Phát âm thanh câu nói qua loa thiết bị")

    sd.frame_else("Cuộn màn hình để tải thêm dữ liệu")
    sd.message("user", "ui", "11: Cuộn màn hình xuống cuối danh sách")
    sd.message("ui", "ctrl", "12: Yêu cầu nạp thêm trang dữ liệu tiếp theo")
    sd.message("ctrl", "db", "13: Đọc thêm các bản ghi cũ hơn từ bộ nhớ")
    sd.message("db", "ctrl", "14: Trả về danh sách bản ghi bổ sung", is_return=True)
    sd.message("ctrl", "ui", "15: Nối thêm dữ liệu vào danh sách", is_return=True)
    sd.message("ui", "user", "16: Hiển thị mượt mà các bản ghi tiếp theo")

    sd.frame_else("Người dùng thực hiện xóa bản ghi")
    sd.message("user", "ui", "17: Nhấn nút Xóa bản ghi đã chọn")
    sd.message("ui", "ctrl", "18: Yêu cầu xóa bản ghi lịch sử theo mã ID")
    sd.message("ctrl", "db", "19: Xóa bản ghi trong cơ sở dữ liệu cục bộ")
    sd.message("db", "ctrl", "20: Xác nhận xóa bản ghi thành công", is_return=True)
    sd.message("ctrl", "ui", "21: Cập nhật lại danh sách hiển thị", is_return=True)
    sd.message("ui", "user", "22: Cập nhật giao diện và xóa bỏ bản ghi khỏi danh sách")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_11_seq_uc2_1_quan_ly_lich_su_dich.png")
    sd.export_png(out)

def gen_fig_3_12():
    """UC2.2 - Quản lý bản dịch yêu thích (Đánh dấu / Bỏ đánh dấu và lọc cục bộ)"""
    sd = SequenceDiagram(width=1000)
    sd.add_lifeline("user", "Người dùng", "actor")
    sd.add_lifeline("ui", ":HistoryScreen", "boundary")
    sd.add_lifeline("ctrl", ":HistoryController", "control")
    sd.add_lifeline("db", ":LocalStorage (SQLite)", "database")

    # Luồng đánh dấu / bỏ đánh dấu yêu thích
    sd.message("user", "ui", "1: Nhấn biểu tượng ngôi sao trên bản ghi lịch sử")
    sd.message("ui", "ctrl", "2: Yêu cầu chuyển đổi trạng thái yêu thích (toggle_favorite)")
    sd.message("ctrl", "db", "3: Cập nhật trạng thái is_favorite theo mã bản ghi")

    sd.frame_start("alt", "Cập nhật thành công vào bộ nhớ máy")
    sd.message("db", "ctrl", "4: Xác nhận cập nhật trạng thái thành công", is_return=True)
    sd.message("ctrl", "ui", "5: Phản hồi trạng thái yêu thích mới (True / False)", is_return=True)
    sd.message("ui", "ui", "6: Đổi màu biểu tượng ngôi sao (Vàng / Xám)")
    sd.message("ui", "user", "7: Hiển thị phản hồi giao diện đã ghi nhận trạng thái")

    sd.frame_else("Ngoại lệ: Lỗi ghi bộ nhớ hoặc bản ghi không tồn tại")
    sd.message("db", "ctrl", "8: Báo lỗi ghi bộ nhớ hoặc bản ghi đã bị xóa", is_return=True)
    sd.message("ctrl", "ui", "9: Thông báo cập nhật trạng thái thất bại", is_return=True)
    sd.message("ui", "ui", "10: Hoàn tác biểu tượng về trạng thái ban đầu")
    sd.message("ui", "user", "11: Hiển thị thông báo lỗi cập nhật cho người dùng")
    sd.frame_end()

    # Luồng tra cứu / lọc bản dịch yêu thích trên cùng màn hình
    sd.frame_start("opt", "Người dùng bật bộ lọc hiển thị bản dịch yêu thích")
    sd.message("user", "ui", "12: Nhấn biểu tượng bộ lọc Chỉ xem yêu thích")
    sd.message("ui", "ctrl", "13: Yêu cầu lấy danh sách bản ghi có is_favorite = True")
    sd.message("ctrl", "db", "14: Truy vấn các bản ghi yêu thích trong bộ nhớ")
    sd.message("db", "ctrl", "15: Danh sách các bản ghi thỏa mãn điều kiện", is_return=True)
    sd.message("ctrl", "ui", "16: Gửi danh sách bản dịch đã lọc hiển thị", is_return=True)
    sd.message("ui", "user", "17: Hiển thị danh sách các bản dịch đã ghim yêu thích")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_12_seq_uc2_2_quan_ly_ban_dich_yeu_thich.png")
    sd.export_png(out)

def gen_fig_3_13():
    """UC2.3 - Cấu hình ứng dụng"""
    sd = SequenceDiagram(width=1080)
    sd.add_lifeline("user", "Người dùng", "actor")
    sd.add_lifeline("ui", ":SettingsScreen", "boundary")
    sd.add_lifeline("ctrl", ":SettingsController", "control")
    sd.add_lifeline("local", ":LocalStorage (Cục bộ)", "database")
    sd.add_lifeline("server", ":SessionRouter", "boundary")

    sd.message("user", "ui", "1: Mở màn hình Cài đặt ứng dụng")
    sd.message("ui", "ctrl", "2: Yêu cầu tải các tùy chọn cấu hình hiện tại")
    sd.message("ctrl", "local", "3: Đọc thiết lập tốc độ, ngôn ngữ, thời hạn lưu")
    sd.message("local", "ctrl", "4: Trả về dữ liệu cấu hình đã lưu trong máy", is_return=True)
    sd.message("ctrl", "ui", "5: Hiển thị các tùy chọn thiết lập hiện thời", is_return=True)
    sd.message("ui", "user", "6: Trình bày danh mục cài đặt hệ thống")

    sd.frame_start("alt", "Người dùng lưu thay đổi cấu hình ứng dụng")
    sd.message("user", "ui", "7: Thay đổi tốc độ nói / ngôn ngữ / thời hạn lưu")
    sd.message("ui", "ctrl", "8: Yêu cầu cập nhật các giá trị cấu hình mới")
    sd.message("ctrl", "local", "9: Ghi nhận giá trị cài đặt mới vào bộ nhớ máy")
    sd.message("local", "ctrl", "10: Xác nhận lưu thiết lập thành công", is_return=True)
    sd.message("ctrl", "ui", "11: Thông báo áp dụng cấu hình thành công", is_return=True)
    sd.message("ui", "user", "12: Cập nhật giao diện phản ánh cài đặt mới")

    sd.frame_else("Người dùng thực hiện xóa toàn bộ lịch sử")
    sd.message("user", "ui", "13: Nhấn nút Xóa toàn bộ lịch sử & xác nhận")
    sd.message("ui", "ctrl", "14: Yêu cầu xóa sạch toàn bộ bản ghi lịch sử")
    sd.message("ctrl", "local", "15: Xóa toàn bộ dữ liệu lịch sử trong SQLite")
    sd.message("local", "ctrl", "16: Xác nhận đã làm sạch bộ nhớ lịch sử", is_return=True)
    sd.message("ctrl", "ui", "17: Thông báo xóa sạch lịch sử thành công", is_return=True)
    sd.message("ui", "user", "18: Hiển thị trạng thái lịch sử đã dọn sạch")

    sd.frame_else("Người dùng đăng xuất khỏi phiên khách")
    sd.message("user", "ui", "19: Nhấn nút Đăng xuất khỏi phiên khách")
    sd.message("ui", "ctrl", "20: Yêu cầu kết thúc phiên khách hiện tại")
    sd.message("ctrl", "local", "21: Xóa thông tin phiên khách trong bộ nhớ máy")
    sd.message("ctrl", "server", "22: Gửi yêu cầu thu hồi phiên làm việc")
    sd.message("server", "ctrl", "23: Xác nhận thu hồi phiên phía máy chủ", is_return=True)
    sd.message("ctrl", "ui", "24: Điều hướng về màn hình khởi động ứng dụng", is_return=True)
    sd.message("ui", "user", "25: Hiển thị giao diện chào mừng ban đầu")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_13_seq_uc2_3_cau_hinh_ung_dung.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 3: XÁC THỰC VÀ HỒ SƠ QUẢN TRỊ (UC3.1 - UC3.2)
# -----------------------------------------------------------------------------

def gen_fig_3_14():
    """UC3.1 - Đăng nhập hệ thống quản trị"""
    sd = SequenceDiagram(width=1120)
    sd.add_lifeline("admin", "Người dùng Quản trị", "actor")
    sd.add_lifeline("ui", ":LoginScreen", "boundary")
    sd.add_lifeline("guard", ":RateLimiterGuard", "control")
    sd.add_lifeline("auth", ":AuthService", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("admin", "ui", "1: Nhập tên đăng nhập, mật khẩu và gửi biểu mẫu")
    sd.message("ui", "guard", "2: Gửi yêu cầu xác thực tài khoản đăng nhập")
    sd.message("guard", "guard", "3: Kiểm tra giới hạn số lần thử (Rate Limit)")
    sd.message("guard", "auth", "4: Chuyển tiếp thông tin xác thực tài khoản")
    sd.message("auth", "db", "5: Truy vấn tài khoản và chuỗi băm mật khẩu Argon2id")
    sd.message("db", "auth", "6: Trả về thông tin tài khoản và trạng thái hoạt động", is_return=True)
    sd.message("auth", "auth", "7: Xác minh mật khẩu & kiểm tra trạng thái kích hoạt")

    sd.frame_start("alt", "Tài khoản đặc quyền yêu cầu xác thực hai bước TOTP")
    sd.message("auth", "ui", "8: Yêu cầu cung cấp mã xác thực TOTP 6 chữ số", is_return=True)
    sd.message("ui", "admin", "9: Hiển thị biểu mẫu yêu cầu nhập mã TOTP")
    sd.message("admin", "ui", "10: Nhập mã xác thực từ ứng dụng Authenticator")
    sd.message("ui", "auth", "11: Gửi mã TOTP kèm mã yêu cầu phiên")
    sd.message("auth", "auth", "12: Xác minh tính hợp lệ của mã thời gian TOTP")
    sd.message("auth", "auth", "13: Khởi tạo phiên làm việc và cấp mã truy cập JWT")
    sd.message("auth", "ui", "14: Trả về mã JWT kèm quyền hạn và vai trò", is_return=True)
    sd.message("ui", "admin", "15: Lưu phiên đăng nhập và điều hướng vào Dashboard")

    sd.frame_else("Xác thực thất bại (Sai mật khẩu / Sai TOTP / Bị khóa)")
    sd.message("auth", "guard", "16: Ghi nhận số lần đăng nhập sai và từ chối", is_return=True)
    sd.message("guard", "ui", "17: Báo lỗi xác thực hoặc cảnh báo tạm khóa tài khoản", is_return=True)
    sd.message("ui", "admin", "18: Hiển thị thông báo lỗi từ chối đăng nhập")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_14_seq_uc3_1_dang_nhap_he_thong_quan_tri.png")
    sd.export_png(out)

def gen_fig_3_15():
    """UC3.2 - Xem hồ sơ và đăng xuất"""
    sd = SequenceDiagram(width=1040)
    sd.add_lifeline("user", "Người dùng Web Admin", "actor")
    sd.add_lifeline("ui", ":UserProfileScreen", "boundary")
    sd.add_lifeline("ctrl", ":UserController", "control")
    sd.add_lifeline("auth", ":AuthService", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("user", "ui", "1: Mở mục Hồ sơ cá nhân trên thanh điều hướng")
    sd.message("ui", "ctrl", "2: Yêu cầu lấy thông tin chi tiết hồ sơ tài khoản")
    sd.message("ctrl", "db", "3: Truy vấn thông tin người dùng, vai trò và quyền hạn")
    sd.message("db", "ctrl", "4: Trả về dữ liệu hồ sơ (loại trừ mật khẩu và khóa bí mật)", is_return=True)
    sd.message("ctrl", "ui", "5: Gửi thông tin hồ sơ tài khoản hiển thị", is_return=True)
    sd.message("ui", "user", "6: Hiển thị tên đăng nhập, vai trò, ngày tạo, trạng thái MFA và quyền")

    sd.frame_start("opt", "Người dùng thực hiện đăng xuất tài khoản")
    sd.message("user", "ui", "7: Nhấn nút Đăng xuất khỏi hệ thống")
    sd.message("ui", "auth", "8: Gửi yêu cầu thu hồi phiên làm việc hiện tại")
    sd.message("auth", "db", "9: Vô hiệu hóa mã phiên trong cơ sở dữ liệu")
    sd.message("db", "auth", "10: Xác nhận thu hồi phiên thành công", is_return=True)
    sd.message("auth", "ui", "11: Phản hồi kết thúc phiên làm việc thành công", is_return=True)
    sd.message("ui", "ui", "12: Xóa mã truy cập JWT lưu trên bộ nhớ trình duyệt")
    sd.message("ui", "user", "13: Điều hướng người dùng về màn hình Đăng nhập")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_15_seq_uc3_2_xem_ho_so_va_dang_xuat.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 4: TỪ ĐIỂN VÀ ĐÁNH GIÁ CHẤT LƯỢNG (UC4.1 - UC4.4)
# -----------------------------------------------------------------------------

def gen_fig_3_16():
    """UC4.1 - Tra cứu và xuất Từ điển"""
    sd = SequenceDiagram(width=1000)
    sd.add_lifeline("staff", "Nhân viên / Quản trị", "actor")
    sd.add_lifeline("ui", ":DictionaryScreen", "boundary")
    sd.add_lifeline("service", ":TranslationMemoryService", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("staff", "ui", "1: Mở trang Từ điển & chọn bộ lọc cặp ngôn ngữ")
    sd.message("ui", "service", "2: Yêu cầu tra cứu từ điển kèm điều kiện tìm kiếm/lọc")
    sd.message("service", "service", "3: Kiểm tra quyền đọc dữ liệu của người dùng")
    sd.message("service", "db", "4: Truy vấn danh sách thuật ngữ song ngữ theo trang")
    sd.message("db", "service", "5: Trả về danh sách các cặp từ điển thỏa mãn", is_return=True)
    sd.message("service", "ui", "6: Gửi dữ liệu danh mục thuật ngữ hiển thị phân trang", is_return=True)
    sd.message("ui", "staff", "7: Hiển thị bảng thuật ngữ song ngữ chuyên ngành")

    sd.frame_start("opt", "Người dùng thực hiện xuất dữ liệu ra tệp CSV")
    sd.message("staff", "ui", "8: Nhấn nút Xuất dữ liệu CSV")
    sd.message("ui", "service", "9: Yêu cầu trích xuất tệp CSV theo phạm vi đang xem")
    sd.message("service", "db", "10: Đọc toàn bộ các bản ghi theo bộ lọc hiện tại")
    sd.message("db", "service", "11: Trả về tập dữ liệu các mục từ điển", is_return=True)
    sd.message("service", "ui", "12: Đóng gói và trả về luồng tệp tải xuống định dạng CSV", is_return=True)
    sd.message("ui", "staff", "13: Trình duyệt tự động tải tệp CSV về máy người dùng")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_16_seq_uc4_1_tra_cuu_va_xuat_tu_dien.png")
    sd.export_png(out)

def gen_fig_3_17():
    """UC4.2 - Cập nhật Từ điển"""
    sd = SequenceDiagram(width=1080)
    sd.add_lifeline("admin", "Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":DictionaryScreen", "boundary")
    sd.add_lifeline("service", ":TranslationMemoryService", "control")
    sd.add_lifeline("norm", ":TextNormalizer", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("admin", "ui", "1: Nhập cặp thuật ngữ hoặc tải tệp danh mục CSV/XLSX")
    sd.message("ui", "service", "2: Yêu cầu thêm mới hoặc nhập hàng loạt cặp dịch chuẩn")
    sd.message("service", "service", "3: Kiểm tra quyền Quản trị cấp cao và tính hợp lệ dữ liệu")
    sd.message("service", "norm", "4: Chuẩn hóa câu chữ, loại bỏ khoảng trắng và ký tự thừa")
    sd.message("norm", "service", "5: Trả về chuỗi văn bản đã chuẩn hóa hình thức", is_return=True)

    sd.frame_start("alt", "Thêm mới hoặc nhập hàng loạt cặp thuật ngữ")
    sd.message("service", "db", "6: Lưu các cặp thuật ngữ vào bảng từ điển chuẩn")
    sd.message("db", "service", "7: Xác nhận đã ghi dữ liệu và làm mới bộ nhớ đệm", is_return=True)
    sd.message("service", "ui", "8: Phản hồi kết quả cập nhật từ điển thành công", is_return=True)
    sd.message("ui", "admin", "9: Làm mới danh mục từ điển và thông báo thành công")

    sd.frame_else("Xóa mục thuật ngữ chuẩn")
    sd.message("admin", "ui", "10: Nhấn nút Xóa mục thuật ngữ & xác nhận thao tác")
    sd.message("ui", "service", "11: Yêu cầu xóa mục từ điển theo mã ID")
    sd.message("service", "db", "12: Xóa bản ghi trong CSDL và vô hiệu hóa bộ đệm liên quan")
    sd.message("db", "service", "13: Xác nhận đã loại bỏ bản ghi thành công", is_return=True)
    sd.message("service", "ui", "14: Phản hồi kết quả xóa mục thuật ngữ thành công", is_return=True)
    sd.message("ui", "admin", "15: Cập nhật giao diện loại bỏ bản ghi khỏi danh mục")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_17_seq_uc4_2_cap_nhat_tu_dien.png")
    sd.export_png(out)

def gen_fig_3_18():
    """UC4.3 - Đánh giá và hiệu chỉnh chất lượng bản dịch"""
    sd = SequenceDiagram(width=1120)
    sd.add_lifeline("reviewer", "Nhân viên thẩm định QA", "actor")
    sd.add_lifeline("ui", ":QAQueueReviewScreen", "boundary")
    sd.add_lifeline("service", ":QualityReviewService", "control")
    sd.add_lifeline("mqm", ":MQMEvaluator", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("reviewer", "ui", "1: Mở hàng đợi thẩm định QA & chọn bản ghi cần đánh giá")
    sd.message("ui", "service", "2: Yêu cầu lấy thông tin chi tiết lượt dịch kèm tệp âm thanh")
    sd.message("service", "db", "3: Truy vấn bản ghi dịch gốc và liên kết tài sản âm thanh")
    sd.message("db", "service", "4: Trả về câu gốc, câu dịch máy và đường dẫn âm thanh", is_return=True)
    sd.message("service", "ui", "5: Hiển thị chi tiết bản dịch để thẩm định viên kiểm tra", is_return=True)
    sd.message("reviewer", "ui", "6: Nhập văn bản hiệu chỉnh chuẩn, chọn thang điểm và gán lỗi MQM")
    sd.message("ui", "service", "7: Gửi phiếu đánh giá chất lượng (Adequacy, Fluency, Lỗi MQM)")
    sd.message("service", "mqm", "8: Tính toán điểm số MQM và phân loại mức độ nghiêm trọng")
    sd.message("mqm", "service", "9: Trả về điểm MQM và danh mục mức độ lỗi", is_return=True)
    sd.message("service", "db", "10: Lưu bản ghi thẩm định mới (QualityReview) và cập nhật cờ đã duyệt")
    sd.message("db", "service", "11: Xác nhận lưu phiếu thẩm định và nhật ký kiểm toán thành công", is_return=True)
    sd.message("service", "ui", "12: Thông báo lưu kết quả đánh giá chất lượng thành công", is_return=True)
    sd.message("ui", "reviewer", "13: Cập nhật trạng thái bản ghi trong hàng đợi sang Đã thẩm định")

    out = os.path.join(TT_IMG_DIR, "hinh_3_18_seq_uc4_3_danh_gia_va_hieu_chinh_chat_luong_ban_dich.png")
    sd.export_png(out)

def gen_fig_3_19():
    """UC4.4 - Chuẩn bị dữ liệu QA cho huấn luyện"""
    sd = SequenceDiagram(width=1120)
    sd.add_lifeline("reviewer", "Nhân viên kiểm soát QA", "actor")
    sd.add_lifeline("ui", ":QAQueueReviewScreen", "boundary")
    sd.add_lifeline("service", ":QualityReviewService", "control")
    sd.add_lifeline("extractor", ":DatasetCorpusExtractor", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("reviewer", "ui", "1: Chọn mục đích gắn nhãn dữ liệu huấn luyện cho Whisper / NLLB")
    sd.message("reviewer", "ui", "2: Xác nhận trạng thái đồng ý sử dụng & kiểm duyệt an toàn PII")
    sd.message("reviewer", "ui", "3: Chọn phân chia tập dữ liệu (Huấn luyện / Kiểm định / Kiểm tra)")
    sd.message("ui", "service", "4: Gửi yêu cầu phê duyệt bản ghi vào kho ngữ liệu huấn luyện")
    sd.message("service", "service", "5: Kiểm tra tính hợp lệ của âm thanh nguồn và văn bản chuẩn hóa")

    sd.frame_start("alt", "Đủ điều kiện đưa vào kho ngữ liệu huấn luyện sạch")
    sd.message("service", "extractor", "6: Trích xuất và định dạng mẫu câu theo chuẩn Whisper/NLLB")
    sd.message("extractor", "service", "7: Gói dữ liệu mẫu câu huấn luyện đã sẵn sàng", is_return=True)
    sd.message("service", "db", "8: Cập nhật cờ use_for_whisper / use_for_nllb và split_tag vào CSDL")
    sd.message("db", "service", "9: Xác nhận lưu trạng thái mẫu câu huấn luyện thành công", is_return=True)
    sd.message("service", "ui", "10: Thông báo bản ghi đã sẵn sàng phục vụ đóng băng tập dữ liệu", is_return=True)
    sd.message("ui", "reviewer", "11: Hiển thị nhãn phê duyệt dữ liệu huấn luyện thành công")

    sd.frame_else("Không đủ điều kiện (Thiếu âm thanh hợp lệ hoặc vi phạm PII)")
    sd.message("service", "db", "12: Đánh dấu bản ghi bị loại khỏi nguồn ngữ liệu huấn luyện")
    sd.message("db", "service", "13: Xác nhận ghi nhận trạng thái từ chối dữ liệu", is_return=True)
    sd.message("service", "ui", "14: Phản hồi lý do không đủ điều kiện đưa vào tập dữ liệu", is_return=True)
    sd.message("ui", "reviewer", "15: Hiển thị cảnh báo từ chối phê duyệt dữ liệu huấn luyện")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_19_seq_uc4_4_chuan_bi_du_lieu_qa_cho_huan_luyen.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 5: GIÁM SÁT VÀ LỊCH SỬ HỆ THỐNG (UC5.1 - UC5.2)
# -----------------------------------------------------------------------------

def gen_fig_3_20():
    """UC5.1 - Xem Bảng điều khiển và Thống kê"""
    sd = SequenceDiagram(width=1080)
    sd.add_lifeline("user", "Người dùng Quản trị", "actor")
    sd.add_lifeline("ui", ":DashboardScreen", "boundary")
    sd.add_lifeline("ctrl", ":TelemetryController", "control")
    sd.add_lifeline("metric", ":PipelineMetric", "entity")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("user", "ui", "1: Mở Bảng điều khiển & chọn khoảng thời gian giám sát")
    sd.message("ui", "ctrl", "2: Yêu cầu truy vấn số liệu tổng quan và biểu đồ vận hành")
    sd.message("ctrl", "ctrl", "3: Khởi tạo tiến trình tổng hợp số liệu đo kiểm độ trễ")
    sd.message("ctrl", "metric", "4: Yêu cầu tính toán phân vị độ trễ P50/P90/P99 và tỷ lệ lỗi")
    sd.message("metric", "db", "5: Quét bảng pipeline_metrics và translation_logs theo mốc thời gian")
    sd.message("db", "metric", "6: Trả về tập dữ liệu đo kiểm và các lượt dịch liên quan", is_return=True)
    sd.message("metric", "ctrl", "7: Trả về các chỉ số phân vị độ trễ và tỷ lệ gắn cờ", is_return=True)
    sd.message("ctrl", "ctrl", "8: Đóng gói số liệu tổng hợp (Lượt dịch, cờ lỗi, phiên đồng thời)")
    sd.message("ctrl", "ui", "9: Gửi gói dữ liệu thống kê tổng hợp về giao diện", is_return=True)
    sd.message("ui", "user", "10: Hiển thị các thẻ chỉ số KPI và biểu đồ độ trễ thời gian thực")

    out = os.path.join(TT_IMG_DIR, "hinh_3_20_seq_uc5_1_xem_bang_dieu_khien_va_thong_ke.png")
    sd.export_png(out)

def gen_fig_3_21():
    """UC5.2 - Tra cứu lịch sử hệ thống"""
    sd = SequenceDiagram(width=1080)
    sd.add_lifeline("admin", "Quản trị viên / Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":SystemHistoryScreen", "boundary")
    sd.add_lifeline("guard", ":RBACGuard", "control")
    sd.add_lifeline("ctrl", ":HistoryAdminController", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("admin", "ui", "1: Mở trang Lịch sử hệ thống & nhập tiêu chí tra cứu")
    sd.message("ui", "guard", "2: Gửi yêu cầu truy vấn nhật ký dịch máy chủ")
    sd.message("guard", "guard", "3: Kiểm tra quyền hạn truy cập theo vai trò người dùng")

    sd.frame_start("alt", "Người dùng có quyền hợp lệ (Admin / SuperAdmin)")
    sd.message("guard", "ctrl", "4: Chuyển tiếp yêu cầu truy vấn nhật ký hệ thống")
    sd.message("ctrl", "db", "5: Truy vấn bảng nhật ký dịch theo từ khóa, thời gian và trạng thái")
    sd.message("db", "ctrl", "6: Trả về danh sách các bản ghi nhật ký dịch máy chủ", is_return=True)
    sd.message("ctrl", "ui", "7: Gửi danh sách kết quả lịch sử hệ thống hiển thị phân trang", is_return=True)
    sd.message("ui", "admin", "8: Hiển thị bảng nhật ký gồm câu gốc, câu dịch, thời gian và trạng thái")

    sd.frame_else("Không đủ quyền truy cập (Nhân viên nghiệp vụ)")
    sd.message("guard", "ui", "9: Từ chối truy cập và báo lỗi không có quyền (403 Forbidden)", is_return=True)
    sd.message("ui", "admin", "10: Hiển thị cảnh báo từ chối quyền truy cập trang lịch sử hệ thống")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_21_seq_uc5_2_tra_cuu_lich_su_he_thong.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 6: QUẢN TRỊ HỆ THỐNG (UC6.1 - UC6.3)
# -----------------------------------------------------------------------------

def gen_fig_3_22():
    """UC6.1 - Quản lý người dùng"""
    sd = SequenceDiagram(width=1100)
    sd.add_lifeline("admin", "Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":UserManagementScreen", "boundary")
    sd.add_lifeline("ctrl", ":UserController", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")
    sd.add_lifeline("audit", ":AuditLogger", "control")

    sd.message("admin", "ui", "1: Mở danh sách người dùng & chọn tạo mới hoặc cập nhật tài khoản")
    sd.message("ui", "ctrl", "2: Gửi thông tin tài khoản (Tên đăng nhập, vai trò, trạng thái)")
    sd.message("ctrl", "ctrl", "3: Kiểm tra quyền Quản trị cấp cao và chính sách bảo vệ tài khoản")

    sd.frame_start("alt", "Tạo mới tài khoản quản trị viên / nhân viên")
    sd.message("ctrl", "ctrl", "4: Băm mật khẩu an toàn bằng giải thuật Argon2id")
    sd.message("ctrl", "db", "5: Lưu thông tin tài khoản mới vào cơ sở dữ liệu")
    sd.message("db", "ctrl", "6: Xác nhận tạo tài khoản thành công", is_return=True)
    sd.message("ctrl", "audit", "7: Ghi nhật ký kiểm toán hành vi tạo người dùng mới")
    sd.message("ctrl", "ui", "8: Thông báo tạo tài khoản thành công và cấp quyền", is_return=True)
    sd.message("ui", "admin", "9: Cập nhật danh sách hiển thị người dùng mới")

    sd.frame_else("Vô hiệu hóa tài khoản & thu hồi toàn bộ phiên hoạt động")
    sd.message("ctrl", "db", "10: Cập nhật trạng thái tài khoản thành Không hoạt động (Soft Delete)")
    sd.message("ctrl", "db", "11: Thu hồi toàn bộ các phiên làm việc đang hoạt động của tài khoản")
    sd.message("db", "ctrl", "12: Xác nhận đã khóa tài khoản và hủy phiên thành công", is_return=True)
    sd.message("ctrl", "audit", "13: Ghi nhận sự kiện vô hiệu hóa tài khoản vào nhật ký kiểm toán")
    sd.message("ctrl", "ui", "14: Phản hồi trạng thái vô hiệu hóa tài khoản thành công", is_return=True)
    sd.message("ui", "admin", "15: Cập nhật giao diện làm mới danh sách tài khoản")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_22_seq_uc6_1_quan_ly_nguoi_dung.png")
    sd.export_png(out)

def gen_fig_3_23():
    """UC6.2 - Quản lý khóa API"""
    sd = SequenceDiagram(width=1100)
    sd.add_lifeline("admin", "Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":ApiKeyScreen", "boundary")
    sd.add_lifeline("service", ":ApiKeyService", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")
    sd.add_lifeline("audit", ":AuditLogger", "control")

    sd.message("admin", "ui", "1: Mở mục Quản lý khóa API & nhấn Tạo khóa mới")
    sd.message("admin", "ui", "2: Nhập tên khóa, chọn phạm vi quyền và thời hạn hiệu lực")
    sd.message("ui", "service", "3: Gửi yêu cầu phát hành khóa truy cập API mới")
    sd.message("service", "service", "4: Sinh ngẫu nhiên chuỗi khóa bí mật và băm SHA-256 để lưu trữ")
    sd.message("service", "db", "5: Lưu thông tin khóa băm, phạm vi quyền và thời hạn vào CSDL")
    sd.message("db", "service", "6: Xác nhận lưu thông tin khóa thành công", is_return=True)
    sd.message("service", "audit", "7: Ghi nhật ký kiểm toán hành vi phát hành khóa API mới")
    sd.message("service", "ui", "8: Phản hồi chuỗi khóa gốc an toàn (chỉ hiển thị một lần duy nhất)", is_return=True)
    sd.message("ui", "admin", "9: Hiển thị hộp thoại chứa mã khóa bí mật kèm nút sao chép an toàn")

    sd.frame_start("opt", "Thu hồi khóa API đang hoạt động")
    sd.message("admin", "ui", "10: Nhấn nút Thu hồi khóa API đã chọn")
    sd.message("ui", "service", "11: Gửi lệnh thu hồi và hủy hiệu lực của khóa")
    sd.message("service", "db", "12: Cập nhật trạng thái khóa thành Đã thu hồi (Revoked) trong CSDL")
    sd.message("db", "service", "13: Xác nhận đã hủy hiệu lực của khóa", is_return=True)
    sd.message("service", "audit", "14: Ghi nhật ký kiểm toán hành vi thu hồi khóa API")
    sd.message("service", "ui", "15: Thông báo thu hồi khóa API thành công", is_return=True)
    sd.message("ui", "admin", "16: Cập nhật giao diện và làm mới trạng thái danh sách khóa")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_23_seq_uc6_2_quan_ly_khoa_api.png")
    sd.export_png(out)

def gen_fig_3_24():
    """UC6.3 - Quản lý cấu hình hệ thống"""
    sd = SequenceDiagram(width=1100)
    sd.add_lifeline("admin", "Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":SystemSettingsScreen", "boundary")
    sd.add_lifeline("ctrl", ":SettingsController", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")
    sd.add_lifeline("audit", ":AuditLogger", "control")

    sd.message("admin", "ui", "1: Mở trang Cài đặt hệ thống & xem các thông số vận hành")
    sd.message("admin", "ui", "2: Thay đổi giá trị cấu hình (Ngưỡng VAD, thời gian phiên, hạn mức gọi)")
    sd.message("ui", "ctrl", "3: Gửi yêu cầu cập nhật các giá trị cấu hình hệ thống")
    sd.message("ctrl", "ctrl", "4: Kiểm tra tính hợp lệ về kiểu dữ liệu và phạm vi cho phép")

    sd.frame_start("alt", "Giá trị hợp lệ và áp dụng thành công")
    sd.message("ctrl", "db", "5: Lưu các giá trị thiết lập mới vào bảng cấu hình hệ thống")
    sd.message("db", "ctrl", "6: Xác nhận lưu các thay đổi cấu hình thành công", is_return=True)
    sd.message("ctrl", "audit", "7: Ghi nhật ký kiểm toán chi tiết các thay đổi cấu hình")
    sd.message("ctrl", "ui", "8: Phản hồi cập nhật cấu hình hệ thống thành công", is_return=True)
    sd.message("ui", "admin", "9: Hiển thị thông báo đã áp dụng cấu hình và làm mới giao diện")

    sd.frame_else("Giá trị không hợp lệ hoặc vượt ngưỡng an toàn")
    sd.message("ctrl", "ui", "10: Từ chối lưu cấu hình và báo lỗi tham số không hợp lệ", is_return=True)
    sd.message("ui", "admin", "11: Hiển thị thông báo lỗi chi tiết từng tham số vi phạm")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_24_seq_uc6_3_quan_ly_cau_hinh_he_thong.png")
    sd.export_png(out)

# -----------------------------------------------------------------------------
# NHÓM 7: HUẤN LUYỆN VÀ QUẢN LÝ MÔ HÌNH (UC7.1 - UC7.3)
# -----------------------------------------------------------------------------

def gen_fig_3_25():
    """UC7.1 - Quản lý tập dữ liệu huấn luyện"""
    sd = SequenceDiagram(width=1120)
    sd.add_lifeline("admin", "Quản trị viên / Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":TrainingCenterScreen", "boundary")
    sd.add_lifeline("ds_mgr", ":DatasetManager", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")
    sd.add_lifeline("storage", ":FileStorage (NFS/Disk)", "database")

    sd.message("admin", "ui", "1: Mở mục Dữ liệu huấn luyện & xem số lượng mẫu QA đủ điều kiện")
    sd.message("admin", "ui", "2: Chọn tác vụ (NLLB / Whisper) và tỷ lệ phân chia tập (80:10:10)")
    sd.message("ui", "ds_mgr", "3: Gửi yêu cầu trích xuất và khởi tạo tập dữ liệu huấn luyện")
    sd.message("ds_mgr", "db", "4: Truy vấn các mẫu câu đạt chuẩn QA có gắn nhãn đồng ý huấn luyện")
    sd.message("db", "ds_mgr", "5: Trả về tập hợp các bản ghi mẫu hợp lệ", is_return=True)
    sd.message("ds_mgr", "ds_mgr", "6: Kiểm tra định dạng, phân chia các tập Train / Validation / Test")
    sd.message("ds_mgr", "storage", "7: Ghi tệp dữ liệu huấn luyện đóng gói vào kho lưu trữ")
    sd.message("storage", "ds_mgr", "8: Xác nhận tệp dữ liệu đã ghi xong", is_return=True)
    sd.message("ds_mgr", "ds_mgr", "9: Tạo mã băm toàn vẹn SHA-256 để chống can thiệp dữ liệu")
    sd.message("ds_mgr", "db", "10: Lưu bản ghi phiên bản tập dữ liệu và đặt trạng thái Đóng băng (FROZEN)")
    sd.message("db", "ds_mgr", "11: Xác nhận tạo và đóng băng tập dữ liệu thành công", is_return=True)
    sd.message("ds_mgr", "ui", "12: Phản hồi thông tin tập dữ liệu đã sẵn sàng phục vụ huấn luyện", is_return=True)
    sd.message("ui", "admin", "13: Hiển thị thông tin phiên bản tập dữ liệu và mã kiểm tra SHA-256")

    out = os.path.join(TT_IMG_DIR, "hinh_3_25_seq_uc7_1_quan_ly_tap_du_lieu_huan_luyen.png")
    sd.export_png(out)

def gen_fig_3_26():
    """UC7.2 - Quản lý tiến trình huấn luyện"""
    sd = SequenceDiagram(width=1120)
    sd.add_lifeline("admin", "Quản trị viên / Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":TrainingCenterScreen", "boundary")
    sd.add_lifeline("worker", ":TrainingWorker", "control")
    sd.add_lifeline("gpu", ":GPUResourceManager", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")

    sd.message("admin", "ui", "1: Chọn tập dữ liệu đóng băng, mô hình nền và cấu hình tham số LoRA")
    sd.message("ui", "worker", "2: Gửi yêu cầu khởi tạo tiến trình huấn luyện mới")
    sd.message("worker", "gpu", "3: Kiểm tra tài nguyên bộ nhớ VRAM của GPU")
    sd.message("gpu", "worker", "4: Cấp phát tài nguyên GPU sẵn sàng cho tiến trình", is_return=True)
    sd.message("worker", "db", "5: Tạo bản ghi tiến trình huấn luyện với trạng thái Chờ xử lý (PENDING)")
    sd.message("worker", "worker", "6: Khởi chạy luồng huấn luyện nền và chuyển trạng thái sang RUNNING")
    sd.message("worker", "ui", "7: Xác nhận tiến trình đã bắt đầu chạy và trả về mã Job ID", is_return=True)
    sd.message("ui", "admin", "8: Hiển thị bảng theo dõi tiến trình huấn luyện thời gian thực")

    sd.frame_start("loop", "Chu kỳ huấn luyện qua các Epoch")
    sd.message("worker", "worker", "9: Huấn luyện tiến trình LoRA và tính toán giá trị độ lỗi (Train/Val Loss)")
    sd.message("worker", "db", "10: Ghi nhận chỉ số Epoch, Step, Loss vào bảng nhật ký sự kiện huấn luyện")
    sd.message("worker", "ui", "11: Gửi thông báo cập nhật tiến độ huấn luyện lên giao diện", is_return=True)
    sd.message("ui", "admin", "12: Cập nhật đường cong suy giảm độ lỗi (Loss Curve) trên biểu đồ")
    sd.frame_end()

    sd.message("worker", "worker", "13: Đóng gói trọng số mô hình LoRA thành phẩm (ModelArtifact)")
    sd.message("worker", "db", "14: Cập nhật trạng thái tiến trình thành Hoàn thành (COMPLETED)")
    sd.message("db", "worker", "15: Xác nhận lưu gói mô hình và trạng thái thành công", is_return=True)
    sd.message("worker", "ui", "16: Thông báo tiến trình huấn luyện hoàn tất thành công", is_return=True)
    sd.message("ui", "admin", "17: Hiển thị liên kết gói mô hình sẵn sàng đưa vào triển khai")

    out = os.path.join(TT_IMG_DIR, "hinh_3_26_seq_uc7_2_quan_ly_tien_trinh_huan_luyen.png")
    sd.export_png(out)

def gen_fig_3_27():
    """UC7.3 - Quản lý gói và phiên bản mô hình"""
    sd = SequenceDiagram(width=1160)
    sd.add_lifeline("admin", "Quản trị cấp cao", "actor")
    sd.add_lifeline("ui", ":DeploymentScreen", "boundary")
    sd.add_lifeline("mgr", ":DeploymentManager", "control")
    sd.add_lifeline("router", ":CanaryTrafficRouter", "control")
    sd.add_lifeline("db", ":PostgreSQL DB", "database")
    sd.add_lifeline("audit", ":AuditLogger", "control")

    sd.message("admin", "ui", "1: Mở trung tâm triển khai mô hình & chọn gói mô hình LoRA")
    sd.message("ui", "mgr", "2: Yêu cầu áp dụng cấu hình thử nghiệm Canary 10% lưu lượng")
    sd.message("mgr", "db", "3: Cập nhật trạng thái triển khai Canary vào cơ sở dữ liệu")
    sd.message("mgr", "router", "4: Thiết lập tỷ lệ điều hướng lưu lượng: 90% Bản chính, 10% Bản thử nghiệm")
    sd.message("router", "mgr", "5: Xác nhận điều phối lưu lượng trong bộ nhớ thành công", is_return=True)
    sd.message("mgr", "audit", "6: Ghi nhật ký kiểm toán sự kiện triển khai thử nghiệm Canary")
    sd.message("mgr", "ui", "7: Xác nhận cấu hình Canary đã kích hoạt thành công", is_return=True)
    sd.message("ui", "admin", "8: Hiển thị trạng thái phân luồng thử nghiệm trên giao diện")

    sd.frame_start("alt", "Thử nghiệm đạt yêu cầu - Đưa vào phục vụ chính thức (Promote)")
    sd.message("admin", "ui", "9: Nhấn nút Đưa vào sử dụng chính thức (Promote Active)")
    sd.message("ui", "mgr", "10: Yêu cầu chuyển mô hình mới thành Active Model 100%")
    sd.message("mgr", "db", "11: Lưu phiên bản hiện tại thành Bản dự phòng trước đó và kích hoạt bản mới")
    sd.message("mgr", "router", "12: Điều hướng toàn bộ 100% lưu lượng sang mô hình mới")
    sd.message("mgr", "audit", "13: Ghi nhận sự kiện thăng cấp mô hình vào nhật ký kiểm toán")
    sd.message("mgr", "ui", "14: Thông báo mô hình đã trở thành phiên bản chính thức", is_return=True)
    sd.message("ui", "admin", "15: Cập nhật trạng thái Active trên bảng quản lý triển khai")

    sd.frame_else("Phát hiện sự cố - Phục hồi phiên bản trước (1-Click Rollback)")
    sd.message("admin", "ui", "16: Nhấn nút Khôi phục phiên bản trước (Rollback khẩn cấp)")
    sd.message("ui", "mgr", "17: Yêu cầu hoàn tác tức thì về phiên bản mô hình cũ")
    sd.message("mgr", "db", "18: Khôi phục mô hình Active về phiên bản dự phòng trước đó trong CSDL")
    sd.message("mgr", "router", "19: Điều hướng ngay lập tức 100% lưu lượng về mô hình ổn định")
    sd.message("mgr", "audit", "20: Ghi nhận sự kiện phục hồi khẩn cấp vào nhật ký kiểm toán")
    sd.message("mgr", "ui", "21: Thông báo đã hoàn tác hệ thống về phiên bản an toàn", is_return=True)
    sd.message("ui", "admin", "22: Cập nhật giao diện phục hồi phiên bản trước thành công")
    sd.frame_end()

    out = os.path.join(TT_IMG_DIR, "hinh_3_27_seq_uc7_3_quan_ly_goi_va_phien_ban_mo_hinh.png")
    sd.export_png(out)

def main():
    print("=== Đang tạo toàn bộ 20 Biểu đồ tuần tự theo danh sách UC 2.1.4 ===")
    print("Mục tiêu xuất ảnh: docs/img/tt")
    gen_fig_3_8()
    gen_fig_3_9()
    gen_fig_3_10()
    gen_fig_3_11()
    gen_fig_3_12()
    gen_fig_3_13()
    gen_fig_3_14()
    gen_fig_3_15()
    gen_fig_3_16()
    gen_fig_3_17()
    gen_fig_3_18()
    gen_fig_3_19()
    gen_fig_3_20()
    gen_fig_3_21()
    gen_fig_3_22()
    gen_fig_3_23()
    gen_fig_3_24()
    gen_fig_3_25()
    gen_fig_3_26()
    gen_fig_3_27()
    print("=== Hoàn thành xuất 20 Biểu đồ tuần tự vào docs/img/tt ===")

if __name__ == "__main__":
    main()

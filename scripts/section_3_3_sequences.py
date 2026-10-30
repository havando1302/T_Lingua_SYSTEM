# -*- coding: utf-8 -*-
"""
Module providing Section 3.3: Thiết kế biểu đồ tuần tự (Sequence Diagrams) for T-Lingua report.
Covering all 20 Use Cases strictly structured according to Section 2.1.4 and Section 3.2:
- UC1: Dịch giọng nói và hội thoại (UC1.1, UC1.2, UC1.3)
- UC2: Lịch sử và cấu hình ứng dụng (UC2.1, UC2.2, UC2.3)
- UC3: Xác thực và hồ sơ quản trị (UC3.1, UC3.2)
- UC4: Từ điển và đánh giá chất lượng (UC4.1, UC4.2, UC4.3, UC4.4)
- UC5: Giám sát và lịch sử hệ thống (UC5.1, UC5.2)
- UC6: Quản trị hệ thống (UC6.1, UC6.2, UC6.3)
- UC7: Huấn luyện và quản lý mô hình (UC7.1, UC7.2, UC7.3)
Embeds high-resolution UML Sequence diagrams from docs/img/tt with monochrome black styling,
accented Vietnamese messages, and synchronized step interaction tables.
"""
import os
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from scripts.docx_utils import (
    add_paragraph, add_heading_2, add_heading_3, add_caption, add_bullet,
    add_diagram_box, set_cell_background, set_cell_margins, set_table_borders,
    PRIMARY_COLOR, SECONDARY_COLOR, HEADER_BG_HEX, SUBHEADER_BG_HEX, ZEBRA_BG_HEX
)

IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img\tt"

def embed_diagram_figure(doc, img_filename, caption_text, width_inches=6.2):
    """Embeds an image from docs/img/tt with center alignment and caption."""
    img_path = os.path.join(IMG_DIR, img_filename)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inches))
    else:
        add_diagram_box(doc, caption_text, f"[Diagram File Missing: {img_filename}]")
    add_caption(doc, caption_text, is_table=False)

def render_sequence_table(doc, steps):
    """
    Renders step-by-step message sequence table:
    [STT, Bên gửi (Lifeline), Bên nhận (Lifeline), Thông điệp / Lời gọi hàm, Dữ liệu phản hồi, Ý nghĩa nghiệp vụ chi tiết]
    """
    tbl = doc.add_table(rows=0, cols=6)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)
    
    headers = ["STT", "Bên gửi (Lifeline)", "Bên nhận (Lifeline)", "Thông điệp / Hàm gọi", "Dữ liệu phản hồi", "Ý nghĩa nghiệp vụ chi tiết"]
    widths = [Inches(0.45), Inches(1.15), Inches(1.15), Inches(1.75), Inches(0.95), Inches(1.55)]
    
    hdr = tbl.add_row()
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=80, bottom=80, left=70, right=70)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, s in enumerate(steps):
        row = tbl.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(6):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            p = cell.paragraphs[0]
            val = str(s[col_idx])
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.bold = True
            elif col_idx in (1, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.bold = True
            elif col_idx == 3:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_paragraph(doc, "", space_after=4)

def build_section_3_3(doc):
    """Generates Section 3.3: Thiết kế biểu đồ tuần tự covering all 20 Use Cases."""
    add_heading_2(doc, "3.3. Thiết kế biểu đồ tuần tự (Sequence Diagrams)")
    
    add_paragraph(
        doc,
        "Biểu đồ tuần tự (Sequence Diagram) là thành phần trọng yếu trong thiết kế động của hệ thống T-Lingua, "
        "thể hiện chi tiết dòng thời gian và trình tự tương tác giữa các tác nhân (Actors), các giao diện người dùng "
        "(Flutter Mobile / React Web Admin), các bộ điều phối bất đồng bộ (SessionActor, MicMutex), chuỗi xử lý "
        "trí tuệ nhân tạo (WebRTC VAD, Whisper STT, NLLB NMT, MMS VITS) và hệ thống lưu trữ bền vững (PostgreSQL DB). "
        "Để đảm bảo tính nhất quán tuyệt đối 100% với 20 ca sử dụng đã chốt tại Mục 2.1.4 và mô hình lớp tại Mục 3.2, "
        "hệ thống thiết kế chi tiết 20 biểu đồ tuần tự tương ứng 1:1 từ Hình 3.8 đến Hình 3.27. "
        "Toàn bộ sơ đồ được mô hình hóa theo phong cách UML chuyên nghiệp tham khảo từ mẫu báo cáo tốt nghiệp [ĐALN]2210: "
        "áp dụng ký hiệu phân tích Robustness (Actor, Boundary, Control, Entity, Database, Worker) đơn sắc đen sang trọng, "
        "thông điệp Tiếng Việt có dấu chuẩn mực, thanh kích hoạt liền mạch và các khung rẽ nhánh điều kiện (alt, opt)."
    )

    # =========================================================================
    # NHÓM 1: DỊCH GIỌNG NÓI VÀ HỘI THOẠI (UC1.1 - UC1.3)
    # =========================================================================
    add_heading_3(doc, "3.3.1. Nhóm UC1 - Dịch giọng nói và hội thoại")

    # UC1.1
    add_paragraph(doc, "3.3.1.1. Sơ đồ tuần tự UC1.1 - Dịch giọng nói một chiều thời gian thực:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Thể hiện chuỗi xử lý luồng âm thanh liên tục khi người dùng nhấn giữ micrô nói một câu đơn. "
        "Hệ thống thu nhận các khối nhị phân PCM 16kHz, phân tích năng lượng qua WebRTC VAD, nhận dạng giọng nói tức thời với Whisper, "
        "dịch câu với NLLB-200, tổng hợp phát âm với MMS VITS và ghi nhận chỉ số đo kiểm vi mô (Telemetry)."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_8_seq_uc1_1_dich_giong_noi_mot_chieu.png",
        caption_text="Hình 3.8: Biểu đồ tuần tự ca sử dụng UC1.1 - Dịch giọng nói một chiều thời gian thực",
        width_inches=6.3
    )
    uc1_1_steps = [
        ("1", "Người dùng", ":RealtimeVoiceScreen", "Nhấn giữ nút Mic()", "None", "Người dùng ra lệnh bắt đầu thu âm câu nói."),
        ("2", ":RealtimeVoiceScreen", ":WebSocketRouter", "Kết nối WebSocket (ws://.../translate)", "101 Protocols", "Thiết lập đường truyền nhị phân hai chiều độ trễ thấp."),
        ("3", ":WebSocketRouter", ":SessionActor", "Khởi tạo phiên làm việc (create_session)", "Actor Instance", "Khởi tạo tác tử cô lập phiên xử lý của người dùng."),
        ("4", ":SessionActor", ":RealtimeVoiceScreen", "Chấp nhận kết nối (101 Protocols)", "WS Ready", "Thông báo máy khách sẵn sàng truyền dữ liệu."),
        ("5", "Người dùng", ":RealtimeVoiceScreen", "Bắt đầu phát âm câu nói", "Sóng âm vật lý", "Microphone thu nhận tín hiệu âm thanh analog."),
        ("6", ":RealtimeVoiceScreen", ":SessionActor", "Truyền luồng PCM 16kHz (20ms/gói)", "None", "Gửi các khối nhị phân PCM 16kHz mono 20ms liên tục."),
        ("7", ":SessionActor", ":WebRtcVadStream", "Đẩy khối âm thanh vào VAD (push)", "VAD Decision", "Bộ lọc WebRTC VAD phân tích mức năng lượng âm thanh."),
        ("8", ":WebRtcVadStream", ":SessionActor", "Bắt đầu tiếng nói (SPEECH_START)", "Event Signal", "Xác nhận phát hiện người dùng bắt đầu nói."),
        ("9", ":SessionActor", ":RealtimeVoiceScreen", "Báo bắt đầu nói & hiển thị sóng âm", "JSON Payload", "Ứng dụng bật hoạt ảnh sóng âm nhấp nháy báo hiệu."),
        ("10", "Người dùng", ":RealtimeVoiceScreen", "Dứt lời nói (Khoảng lặng)", "Khoảng lặng âm", "Người dùng kết thúc câu phát ngôn."),
        ("11", ":RealtimeVoiceScreen", ":SessionActor", "Truyền tiếp các gói âm thanh tĩnh", "None", "Ứng dụng tiếp tục truyền các khung âm thanh nền."),
        ("12", ":SessionActor", ":WebRtcVadStream", "Đẩy khối âm thanh tĩnh (push)", "VAD Decision", "Phát hiện năng lượng âm thanh rơi xuống dưới ngưỡng."),
        ("13", ":WebRtcVadStream", ":SessionActor", "Khoảng lặng 500ms (SILENCE_CUTOFF)", "Event Signal", "Xác định khoảng lặng liên tiếp 500ms -> Chốt kết thúc câu."),
        ("14", ":SessionActor", ":STTWorker (Whisper)", "Yêu cầu nhận dạng giọng nói (transcribe)", "Async Call", "Gửi toàn bộ đệm âm thanh của câu nói sang mô hình Whisper."),
        ("15", ":STTWorker (Whisper)", ":SessionActor", "Trả về văn bản nguồn (source_text, stt_ms)", "Text + Metric", "Mô hình nhận dạng giọng nói trả về chuỗi văn bản tiếng Việt."),
        ("16", ":SessionActor", ":RealtimeVoiceScreen", "Hiển thị văn bản nhận dạng tức thời", "JSON Payload", "Hiển thị văn bản nhận diện tức thời trên màn hình máy khách."),
        ("17", ":SessionActor", ":TransWorker (NLLB)", "Yêu cầu dịch máy (translate 'vi' -> 'en')", "Async Call", "Gửi chuỗi văn bản sang mô hình NLLB-200 kèm bộ điều phối LoRA."),
        ("18", ":TransWorker (NLLB)", ":SessionActor", "Trả về bản dịch tiếng Anh (target_text, trans_ms)", "Text + Metric", "Mô hình dịch máy trả về bản dịch tiếng Anh chuẩn xác."),
        ("19", ":SessionActor", ":RealtimeVoiceScreen", "Hiển thị bản dịch tức thời trên màn hình", "JSON Payload", "Hiển thị bản dịch nổi bật trên màn hình kết quả."),
        ("20", ":SessionActor", ":TTSWorker (VITS)", "Yêu cầu tổng hợp giọng đọc (synthesize 'en')", "Async Call", "Kích hoạt mô hình MMS VITS tổng hợp giọng đọc tiếng Anh bản xứ."),
        ("21", ":TTSWorker (VITS)", ":SessionActor", "Trả về luồng byte âm thanh (wav_bytes, tts_ms)", "Audio Bytes", "Trả về luồng byte âm thanh WAV 16kHz đã tổng hợp."),
        ("22", ":SessionActor", ":RealtimeVoiceScreen", "Truyền luồng âm thanh nhị phân (wav_bytes)", "Binary Stream", "Truyền trực tiếp luồng byte âm thanh về thiết bị di động."),
        ("23", ":RealtimeVoiceScreen", "Người dùng", "Phát âm thanh câu dịch qua loa ngoài", "Âm thanh loa ngoài", "Phát câu dịch ra loa cho người dùng và đối tác cùng nghe."),
        ("24", ":SessionActor", ":PostgreSQL DB", "Lưu vết lượt dịch & đo kiểm vi mô (save_turn)", "INSERT Query", "Ghi vết chi tiết lượt dịch vào translation_logs & pipeline_metrics."),
        ("25", ":PostgreSQL DB", ":SessionActor", "Xác nhận lưu trữ thành công (log_id, SUCCESS)", "SUCCESS ACK", "Phản hồi xác nhận ghi thành công bản ghi vào CSDL.")
    ]
    render_sequence_table(doc, uc1_1_steps)

    # UC1.2
    add_paragraph(doc, "3.3.1.2. Sơ đồ tuần tự UC1.2 - Hội thoại song ngữ hai chiều:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Điều phối cuộc đối thoại trực tiếp giữa hai người bản địa và ngoại quốc thông qua thanh DualMicBar. "
        "Áp dụng cơ chế khóa hàng rào tranh chấp (MicMutex) để ngăn xung đột khi cả hai bên cùng chạm nút micrô đồng thời."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_9_seq_uc1_2_hoi_thoai_song_ngu_hai_chieu.png",
        caption_text="Hình 3.9: Biểu đồ tuần tự ca sử dụng UC1.2 - Hội thoại song ngữ hai chiều",
        width_inches=6.3
    )
    uc1_2_steps = [
        ("1", "Người dùng A (VN)", ":BilingualConversationScreen", "Nhấn giữ Mic A nói tiếng Việt", "None", "Người dùng A chiếm quyền nói tiếng Việt."),
        ("2", ":BilingualConversationScreen", ":SessionActor", "Yêu cầu chiếm quyền mic ('side_a')", "Lock Request", "Gửi yêu cầu xin cấp phát khóa mic về máy chủ."),
        ("3", ":SessionActor", ":MicMutex", "Xin cấp khóa tranh chấp (acquire)", "Lock Call", "Kiểm tra trạng thái tranh chấp của biến khóa mic."),
        ("4", ":MicMutex", ":SessionActor", "Cấp khóa thành công (LockAcquired)", "True", "Xác nhận cấp phát quyền sử dụng mic cho phía A."),
        ("5", ":SessionActor", ":BilingualConversationScreen", "Kích hoạt Mic A, vô hiệu hóa Mic B", "UI State", "Giao diện kích hoạt sóng âm phía A và khóa vô hiệu hóa nút Mic B."),
        ("6", "Người dùng B (EN)", ":BilingualConversationScreen", "Nhấn giữ Mic B đồng thời", "Touch Event", "Người dùng B cố tình chen ngang khi A đang nói."),
        ("7", ":BilingualConversationScreen", ":SessionActor", "Yêu cầu chiếm mic ('side_b')", "Lock Request", "Gửi yêu cầu xin cấp khóa cho phía B."),
        ("8", ":SessionActor", ":MicMutex", "Xin cấp khóa tranh chấp (acquire)", "Lock Call", "Yêu cầu khóa mic cho phía B khi A chưa nhả mic."),
        ("9", ":MicMutex", ":SessionActor", "Từ chối do mic đang bận (LockRejected)", "False", "Từ chối cấp phát do tài nguyên mic đang bị chiếm hữu."),
        ("10", ":SessionActor", ":BilingualConversationScreen", "Rung phản hồi báo mic đang bận", "Vibrate/Toast", "Báo hiệu máy rung nhẹ và hiện thông báo chờ đối phương dứt lời."),
        ("11", "Người dùng A (VN)", ":BilingualConversationScreen", "Thả Mic A / Dứt câu nói", "Touch Up", "Người dùng A kết thúc phát ngôn."),
        ("12", ":BilingualConversationScreen", ":SessionActor", "Đóng gói và gửi âm thanh câu nói", "Audio Buffer", "Đóng gói toàn bộ âm thanh câu nói gửi lên chuỗi xử lý AI."),
        ("13", ":SessionActor", ":AIPipelineWorkers", "Điều phối chuỗi AI (Whisper -> NLLB -> VITS)", "Pipeline Run", "Kích hoạt xử lý nối tiếp các mô hình AI."),
        ("14", ":AIPipelineWorkers", ":SessionActor", "Trả về câu dịch tiếng Anh & âm thanh", "Result DTO", "Trả về văn bản dịch tiếng Anh và âm thanh phát âm."),
        ("15", ":SessionActor", ":MicMutex", "Giải phóng khóa micrô (release)", "Unlock", "Giải phóng tài nguyên khóa micrô cho phiên làm việc."),
        ("16", ":SessionActor", ":BilingualConversationScreen", "Phát âm thanh câu dịch & mở khóa Mic B", "Audio + State", "Phát âm thanh câu dịch ra loa ngoài và kích hoạt lại nút Mic B."),
        ("17", ":SessionActor", ":PostgreSQL DB", "Lưu lượt đối thoại (TranslationLog)", "INSERT Query", "Lưu trữ lịch sử hội thoại đối đáp vào CSDL bền vững.")
    ]
    render_sequence_table(doc, uc1_2_steps)

    # UC1.3
    add_paragraph(doc, "3.3.1.3. Sơ đồ tuần tự UC1.3 - Tương tác với kết quả dịch:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Sau khi một lượt dịch giọng nói hoàn tất, người dùng có thể thực hiện 4 thao tác tương tác chính trên thẻ kết quả: "
        "(1) Phát lại âm thanh theo tốc độ đã chọn qua AudioPlayer; (2) Sao chép bản dịch vào bộ nhớ tạm thiết bị qua ClipboardManager; "
        "(3) Lưu bản ghi câu dịch vào cơ sở dữ liệu lịch sử cục bộ (LocalStorage / SQLite); và (4) Gắn cờ kết quả nghi ngờ "
        "kèm văn bản nhận dạng, bản dịch, cặp ngôn ngữ, thông tin đầu vào giọng nói và mã tham chiếu âm thanh chuyển lên máy chủ để đưa vào hàng đợi kiểm soát chất lượng (QA)."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_10_seq_uc1_3_tuong_tac_ket_qua_dich.png",
        caption_text="Hình 3.10: Biểu đồ tuần tự ca sử dụng UC1.3 - Tương tác với kết quả dịch",
        width_inches=6.3
    )
    uc1_3_steps = [
        ("1", "Người dùng", ":RealtimeVoiceScreen", "Chọn thao tác trên thẻ kết quả dịch", "Touch Event", "Người dùng chạm vào một trong các nút thao tác trên thẻ kết quả."),
        ("2a", "Người dùng", ":RealtimeVoiceScreen", "Nhấn nút Phát lại âm thanh", "Button Click", "Yêu cầu nghe lại câu phát âm theo tốc độ đã cấu hình."),
        ("3a", ":RealtimeVoiceScreen", ":AudioPlayer", "play_audio(wav_bytes, speed)", "Audio Call", "Kích hoạt engine âm thanh phát luồng byte WAV câu dịch."),
        ("4a", ":AudioPlayer", "Người dùng", "Phát âm thanh câu dịch ra loa ngoài", "Audio Wave", "Người dùng nghe phát âm câu dịch qua loa ngoài thiết bị."),
        ("2b", "Người dùng", ":RealtimeVoiceScreen", "Nhấn nút Sao chép văn bản", "Button Click", "Yêu cầu sao chép chuỗi văn bản dịch vào bộ nhớ tạm."),
        ("3b", ":RealtimeVoiceScreen", ":ClipboardManager", "copy_to_clipboard(target_text)", "System Call", "Đưa văn bản dịch vào Clipboard hệ điều hành."),
        ("4b", ":ClipboardManager", ":RealtimeVoiceScreen", "Đã lưu vào bộ nhớ tạm", "Success ACK", "Xác nhận sao chép thành công."),
        ("5b", ":RealtimeVoiceScreen", "Người dùng", "Hiển thị thông báo 'Đã sao chép vào bộ nhớ'", "Snackbar", "Phản hồi trực quan thông báo cho người dùng."),
        ("2c", "Người dùng", ":RealtimeVoiceScreen", "Nhấn nút Lưu vào lịch sử cục bộ", "Button Click", "Yêu cầu lưu trữ câu dịch vào bộ nhớ offline trên máy."),
        ("3c", ":RealtimeVoiceScreen", ":LocalStorage (SQLite)", "insert_local_history(TurnData)", "Local Insert", "Lưu trữ bản ghi câu dịch vào SQLite cục bộ (tránh trùng lặp)."),
        ("4c", ":LocalStorage (SQLite)", ":RealtimeVoiceScreen", "Lưu thành công (local_id)", "Record ID", "Xác nhận đã ghi bản ghi vào cơ sở dữ liệu cục bộ."),
        ("5c", ":RealtimeVoiceScreen", "Người dùng", "Cập nhật trạng thái đã lưu vào lịch sử", "UI State", "Biểu tượng chuyển sang trạng thái đã lưu vào lịch sử máy."),
        ("2d", "Người dùng", ":RealtimeVoiceScreen", "Nhấn nút Gắn cờ & nhập lý do nghi ngờ", "Dialog Input", "Người dùng phát hiện câu dịch sai nghĩa và gửi cờ phản hồi."),
        ("3d", ":RealtimeVoiceScreen", ":FeedbackController", "POST /api/v1/feedback/flag {text, lang, is_voice, audio_ref}", "HTTP POST", "Gửi gói tin gắn cờ kèm thông tin tham chiếu âm thanh lên máy chủ."),
        ("4d", ":FeedbackController", ":QualityReview", "create_qa_review(TurnPayload, status='PENDING')", "ORM Create", "Tạo phiếu thẩm định chất lượng mới vào hàng đợi kiểm soát chất lượng."),
        ("5d", ":QualityReview", ":PostgreSQL DB", "INSERT INTO quality_reviews", "SQL INSERT", "Lưu phiếu QA với trạng thái PENDING chờ chuyên gia xử lý."),
        ("6d", ":PostgreSQL DB", ":QualityReview", "Xác nhận tạo phiếu QA thành công", "Success ACK", "CSDL xác nhận tạo thành công bản ghi."),
        ("7d", ":FeedbackController", ":RealtimeVoiceScreen", "200 OK {message: 'Đã chuyển vào hàng đợi QA'}", "JSON Response", "Máy chủ phản hồi xác nhận tiếp nhận phản ánh chất lượng."),
        ("8d", ":RealtimeVoiceScreen", "Người dùng", "Hiển thị thông báo 'Đã gửi phản hồi kiểm soát chất lượng'", "Toast Alert", "Thông báo cảm ơn người dùng và hoàn tất luồng kiểm soát.")
    ]
    render_sequence_table(doc, uc1_3_steps)

    # =========================================================================
    # NHÓM 2: LỊCH SỬ VÀ CẤU HÌNH ỨNG DỤNG (UC2.1 - UC2.3)
    # =========================================================================
    add_heading_3(doc, "3.3.2. Nhóm UC2 - Lịch sử và cấu hình ứng dụng")

    # UC2.1
    add_paragraph(doc, "3.3.2.1. Sơ đồ tuần tự UC2.1 - Quản lý lịch sử dịch:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng xem các bản dịch giọng nói đã lưu trữ cục bộ trên thiết bị di động, "
        "mở chi tiết nghe lại âm thanh, cuộn tải thêm các trang dữ liệu cũ hơn và thực hiện xóa bản ghi. "
        "Tuân thủ nghiêm ngặt quy tắc bảo mật và quyền riêng tư: toàn bộ dữ liệu lịch sử dịch của người dùng cuối "
        "được duy trì hoàn toàn trong cơ sở dữ liệu cục bộ (:LocalStorage - SQLite) và không gửi lên máy chủ xử lý."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_11_seq_uc2_1_quan_ly_lich_su_dich.png",
        caption_text="Hình 3.11: Biểu đồ tuần tự ca sử dụng UC2.1 - Quản lý lịch sử dịch",
        width_inches=6.2
    )
    uc2_1_steps = [
        ("1", "Người dùng", ":HistoryScreen", "Mở mục Lịch sử từ thanh điều hướng", "UI Event", "Người dùng chọn tab Lịch sử trên thanh điều hướng ứng dụng."),
        ("2", ":HistoryScreen", ":HistoryController", "Yêu cầu tải danh sách lịch sử dịch cục bộ", "Local Call", "Giao diện kích hoạt Controller khởi tạo tiến trình truy vấn dữ liệu máy."),
        ("3", ":HistoryController", ":HistoryController", "Kiểm tra trạng thái bật lưu lịch sử (is_enabled)", "Self Check", "Kiểm tra cấu hình người dùng có cho phép lưu lịch sử hay không."),
        ("4", ":HistoryController", ":LocalStorage (SQLite)", "Truy vấn danh sách bản ghi theo thời gian gần nhất", "Local Query", "Đọc các bản dịch đã lưu trong CSDL SQLite cục bộ trên điện thoại."),
        ("5", ":LocalStorage (SQLite)", ":HistoryController", "Danh sách bản dịch đã lưu trong bộ nhớ máy", "Recordset", "Trả về tập bản ghi gồm câu nguồn, câu đích, thời gian và đường dẫn tệp audio."),
        ("6", ":HistoryController", ":HistoryScreen", "Gửi danh sách dữ liệu lịch sử hiển thị", "Data List", "Truyền danh sách đối tượng bản ghi về màn hình giao diện Flutter."),
        ("7", ":HistoryScreen", "Người dùng", "Hiển thị danh sách các câu dịch theo dòng thời gian", "Render UI", "Trình bày danh sách trực quan dạng danh sách cuộn mượt mà."),
        ("8", "Người dùng", ":HistoryScreen", "Chạm xem chi tiết bản ghi & nhấn nút Loa", "Touch Event", "Người dùng chọn một thẻ kết quả và nhấn nút biểu tượng loa để nghe lại."),
        ("9", ":HistoryScreen", ":AudioPlayer", "Yêu cầu phát lại âm thanh câu nói đã lưu", "Play Audio", "Yêu cầu AudioPlayer phát tệp âm thanh câu dịch lưu trong bộ nhớ cục bộ."),
        ("10", ":AudioPlayer", "Người dùng", "Phát âm thanh câu nói qua loa thiết bị", "Speaker Output", "Phát âm thanh câu nói trực tiếp qua loa ngoài hoặc tai nghe của thiết bị."),
        ("11", "Người dùng", ":HistoryScreen", "Cuộn màn hình xuống cuối danh sách", "Scroll Event", "Người dùng vuốt màn hình xuống dưới để xem thêm các bản ghi cũ hơn."),
        ("12", ":HistoryScreen", ":HistoryController", "Yêu cầu nạp thêm trang dữ liệu tiếp theo", "Pagination Req", "Kích hoạt cơ chế phân trang cục bộ (Infinite Scroll Pagination)."),
        ("13", ":HistoryController", ":LocalStorage (SQLite)", "Đọc thêm các bản ghi cũ hơn từ bộ nhớ", "Local Query", "Truy vấn thêm khối dữ liệu với chỉ số phân trang kế tiếp từ SQLite."),
        ("14", ":LocalStorage (SQLite)", ":HistoryController", "Trả về danh sách bản ghi bổ sung", "Recordset", "CSDL SQLite trả về các bản dịch thuộc trang tiếp theo."),
        ("15", ":HistoryController", ":HistoryScreen", "Nối thêm dữ liệu vào danh sách", "Append Data", "Bổ sung danh sách các bản ghi mới vào danh sách hiện tại của giao diện."),
        ("16", ":HistoryScreen", "Người dùng", "Hiển thị mượt mà các bản ghi tiếp theo", "Render UI", "Cập nhật hiển thị giao diện nối dài danh sách mà không bị giật lag."),
        ("17", "Người dùng", ":HistoryScreen", "Nhấn nút Xóa bản ghi đã chọn", "Action Event", "Người dùng vuốt thẻ hoặc bấm biểu tượng thùng rác để xóa bản ghi."),
        ("18", ":HistoryScreen", ":HistoryController", "Yêu cầu xóa bản ghi lịch sử theo mã ID", "Delete Call", "Gửi mã định danh duy nhất (UUID) của bản ghi cần xóa tới Controller."),
        ("19", ":HistoryController", ":LocalStorage (SQLite)", "Xóa bản ghi trong cơ sở dữ liệu cục bộ", "Delete Record", "Thực thi xóa bản ghi và giải phóng tệp âm thanh đính kèm trong SQLite."),
        ("20", ":LocalStorage (SQLite)", ":HistoryController", "Xác nhận xóa bản ghi thành công", "Success Ack", "CSDL cục bộ phản hồi kết quả thao tác xóa hoàn tất thành công."),
        ("21", ":HistoryController", ":HistoryScreen", "Cập nhật lại danh sách hiển thị", "State Update", "Thông báo trạng thái để giao diện cập nhật loại bỏ phần tử đã xóa."),
        ("22", ":HistoryScreen", "Người dùng", "Cập nhật giao diện và xóa bỏ bản ghi khỏi danh sách", "UI Animation", "Thực hiện hiệu ứng xóa mượt mà, biến mất thẻ câu dịch khỏi màn hình.")
    ]
    render_sequence_table(doc, uc2_1_steps)

    # UC2.2
    add_paragraph(doc, "3.3.2.2. Sơ đồ tuần tự UC2.2 - Quản lý bản dịch yêu thích:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng đánh dấu hoặc bỏ đánh dấu một bản ghi lịch sử dịch là yêu thích "
        "ngay trên màn hình Lịch sử (:HistoryScreen) để thuận tiện tìm lại các nội dung thường dùng. "
        "Yêu thích chỉ là thuộc tính bổ trợ của bản ghi lịch sử cục bộ trong SQLite (:LocalStorage), không làm thay đổi "
        "kết quả dịch gốc và không truyền dữ liệu lên máy chủ. Nếu người dùng đổi trạng thái liên tục, "
        "hệ thống áp dụng cơ chế đồng bộ trạng thái cuối cùng để ghi nhận bền vững vào bộ nhớ máy."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_12_seq_uc2_2_quan_ly_ban_dich_yeu_thich.png",
        caption_text="Hình 3.12: Biểu đồ tuần tự ca sử dụng UC2.2 - Quản lý bản dịch yêu thích",
        width_inches=6.2
    )
    uc2_2_steps = [
        ("1", "Người dùng", ":HistoryScreen", "Nhấn biểu tượng ngôi sao trên bản ghi lịch sử", "Touch Event", "Người dùng chạm vào biểu tượng ngôi sao tại một thẻ bản dịch lịch sử để đổi trạng thái yêu thích."),
        ("2", ":HistoryScreen", ":HistoryController", "Yêu cầu chuyển đổi trạng thái yêu thích (toggle_favorite)", "Local Event", "Giao diện gửi mã định danh bản ghi yêu cầu Controller đổi trạng thái is_favorite."),
        ("3", ":HistoryController", ":LocalStorage (SQLite)", "Cập nhật trạng thái is_favorite theo mã bản ghi", "Local Update", "Thực thi cập nhật trường is_favorite (True/False) trong bảng lịch sử SQLite cục bộ."),
        ("4", ":LocalStorage (SQLite)", ":HistoryController", "Xác nhận cập nhật trạng thái thành công", "Success Ack", "Bộ lưu trữ cục bộ xác nhận thao tác ghi dữ liệu hoàn tất."),
        ("5", ":HistoryController", ":HistoryScreen", "Phản hồi trạng thái yêu thích mới (True / False)", "State Callback", "Controller báo lại giá trị cờ yêu thích mới để giao diện xử lý."),
        ("6", ":HistoryScreen", ":HistoryScreen", "Đổi màu biểu tượng ngôi sao (Vàng / Xám)", "UI State Update", "Giao diện đổi màu biểu tượng: vàng (đã ghim yêu thích) hoặc xám (đã bỏ yêu thích)."),
        ("7", ":HistoryScreen", "Người dùng", "Hiển thị phản hồi giao diện đã ghi nhận trạng thái", "UI Feedback", "Phản hồi trực quan thông qua hiệu ứng hoạt họa (Animation) cho người dùng."),
        ("8", ":LocalStorage (SQLite)", ":HistoryController", "Báo lỗi ghi bộ nhớ hoặc bản ghi đã bị xóa", "Error Signal", "Ngoại lệ khi tệp cơ sở dữ liệu bị khóa hoặc bản ghi không còn tồn tại."),
        ("9", ":HistoryController", ":HistoryScreen", "Thông báo cập nhật trạng thái thất bại", "Error Callback", "Báo lỗi để màn hình không ghi nhận sai lệch trạng thái hiển thị."),
        ("10", ":HistoryScreen", ":HistoryScreen", "Hoàn tác biểu tượng về trạng thái ban đầu", "Rollback UI", "Khôi phục lại màu sắc biểu tượng sao về đúng trạng thái thực tế trước khi nhấn."),
        ("11", ":HistoryScreen", "Người dùng", "Hiển thị thông báo lỗi cập nhật cho người dùng", "SnackBar / Toast", "Hiển thị thông báo cảnh báo lỗi thao tác để người dùng thử lại sau."),
        ("12", "Người dùng", ":HistoryScreen", "Nhấn biểu tượng bộ lọc Chỉ xem yêu thích", "Filter Event", "Người dùng kích hoạt bộ lọc trên thanh công cụ để tra cứu nhanh các câu đã ghim."),
        ("13", ":HistoryScreen", ":HistoryController", "Yêu cầu lấy danh sách bản ghi có is_favorite = True", "Filter Call", "Ủy quyền Controller truy vấn lọc các bản dịch thỏa mãn điều kiện yêu thích."),
        ("14", ":HistoryController", ":LocalStorage (SQLite)", "Truy vấn các bản ghi yêu thích trong bộ nhớ", "Local Query", "Thực thi lọc các hàng có is_favorite = 1 theo thứ tự thời gian mới nhất."),
        ("15", ":LocalStorage (SQLite)", ":HistoryController", "Danh sách các bản ghi thỏa mãn điều kiện", "Recordset", "Trả về tập hợp các câu dịch yêu thích từ bộ nhớ máy."),
        ("16", ":HistoryController", ":HistoryScreen", "Gửi danh sách bản dịch đã lọc hiển thị", "Data List", "Truyền tập dữ liệu đã lọc về danh sách hiển thị trên giao diện."),
        ("17", ":HistoryScreen", "Người dùng", "Hiển thị danh sách các bản dịch đã ghim yêu thích", "Render UI", "Cập nhật danh sách trên màn hình chỉ chứa các mục đắc dụng được ghim sao.")
    ]
    render_sequence_table(doc, uc2_2_steps)

    # UC2.3
    add_paragraph(doc, "3.3.2.3. Sơ đồ tuần tự UC2.3 - Cấu hình ứng dụng:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng tùy chọn cấu hình các chức năng đang triển khai gồm: tốc độ phát giọng nói "
        "(Chậm / Bình thường / Nhanh), ngôn ngữ mặc định (Việt / Anh), bật lưu lịch sử sau khi xác nhận đồng ý, chọn thời hạn lưu "
        "(1/3/7/14/30 ngày), xóa toàn bộ lịch sử cục bộ và đăng xuất khỏi phiên khách để làm sạch dữ liệu."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_13_seq_uc2_3_cau_hinh_ung_dung.png",
        caption_text="Hình 3.13: Biểu đồ tuần tự ca sử dụng UC2.3 - Cấu hình ứng dụng",
        width_inches=6.2
    )
    uc2_3_steps = [
        ("1", "Người dùng", ":SettingsScreen", "Mở màn hình Cài đặt ứng dụng", "UI Event", "Người dùng chạm chọn mục Cài đặt trên thanh điều hướng."),
        ("2", ":SettingsScreen", ":SettingsController", "Yêu cầu tải các tùy chọn cấu hình hiện tại", "Local Call", "Giao diện kích hoạt Controller nạp trạng thái thiết lập hiện có."),
        ("3", ":SettingsController", ":LocalStorage (Cục bộ)", "Đọc thiết lập tốc độ, ngôn ngữ, thời hạn lưu", "Query Config", "Truy vấn các tham số đã lưu trong bộ nhớ máy."),
        ("4", ":LocalStorage (Cục bộ)", ":SettingsController", "Trả về dữ liệu cấu hình đã lưu trong máy", "Recordset", "Trả về tập giá trị cấu hình lưu trữ."),
        ("5", ":SettingsController", ":SettingsScreen", "Hiển thị các tùy chọn thiết lập hiện thời", "State Data", "Cung cấp dữ liệu để màn hình render các công tắc và lựa chọn."),
        ("6", ":SettingsScreen", "Người dùng", "Trình bày danh mục cài đặt hệ thống", "Render UI", "Hiển thị trực quan danh sách thiết lập cho người dùng thao tác."),
        ("7", "Người dùng", ":SettingsScreen", "Thay đổi tốc độ nói / ngôn ngữ / thời hạn lưu", "Form Input", "Người dùng thay đổi tốc độ đọc, ngôn ngữ hoặc mốc ngày lưu trữ."),
        ("8", ":SettingsScreen", ":SettingsController", "Yêu cầu cập nhật các giá trị cấu hình mới", "Action Call", "Gửi gói cấu hình mới tới Controller để xử lý lưu trữ."),
        ("9", ":SettingsController", ":LocalStorage (Cục bộ)", "Ghi nhận giá trị cài đặt mới vào bộ nhớ máy", "Commit Config", "Ghi đè giá trị cấu hình mới vào bộ nhớ cục bộ."),
        ("10", ":LocalStorage (Cục bộ)", ":SettingsController", "Xác nhận lưu thiết lập thành công", "Success Ack", "Bộ lưu trữ cục bộ xác nhận cập nhật thành công."),
        ("11", ":SettingsController", ":SettingsScreen", "Thông báo áp dụng cấu hình thành công", "Notify Success", "Báo lại trạng thái cập nhật thành công về giao diện."),
        ("12", ":SettingsScreen", "Người dùng", "Cập nhật giao diện phản ánh cài đặt mới", "UI Update", "Giao diện cập nhật trạng thái hiển thị của các nút gạt và lựa chọn."),
        ("13", "Người dùng", ":SettingsScreen", "Nhấn nút Xóa toàn bộ lịch sử & xác nhận", "Action Event", "Người dùng chọn xóa sạch lịch sử dịch và xác nhận hộp thoại cảnh báo."),
        ("14", ":SettingsScreen", ":SettingsController", "Yêu cầu xóa sạch toàn bộ bản ghi lịch sử", "Delete All Req", "Gửi lệnh yêu cầu dọn sạch bảng lưu trữ lịch sử."),
        ("15", ":SettingsController", ":LocalStorage (Cục bộ)", "Xóa toàn bộ dữ liệu lịch sử trong SQLite", "Execute Truncate", "Xóa sạch toàn bộ các hàng dữ liệu lịch sử trong SQLite."),
        ("16", ":LocalStorage (Cục bộ)", ":SettingsController", "Xác nhận đã làm sạch bộ nhớ lịch sử", "Success Ack", "Bộ lưu trữ xác nhận toàn bộ bản ghi đã bị xóa sạch."),
        ("17", ":SettingsController", ":SettingsScreen", "Thông báo xóa sạch lịch sử thành công", "Notify Success", "Controller báo lại giao diện kết quả xóa thành công."),
        ("18", ":SettingsScreen", "Người dùng", "Hiển thị trạng thái lịch sử đã dọn sạch", "UI Alert", "Thông báo hiển thị danh sách lịch sử trống."),
        ("19", "Người dùng", ":SettingsScreen", "Nhấn nút Đăng xuất khỏi phiên khách", "Logout Click", "Người dùng yêu cầu kết thúc phiên sử dụng hiện tại."),
        ("20", ":SettingsScreen", ":SettingsController", "Yêu cầu kết thúc phiên khách hiện tại", "Logout Req", "Gửi yêu cầu hủy phiên khách tới Controller."),
        ("21", ":SettingsController", ":LocalStorage (Cục bộ)", "Xóa thông tin phiên khách trong bộ nhớ máy", "Clear Local", "Xóa toàn bộ token và phiên tạm lưu trong bộ nhớ máy."),
        ("22", ":SettingsController", ":SessionRouter", "Gửi yêu cầu thu hồi phiên làm việc", "API Logout", "Gửi thông báo tới máy chủ để thu hồi phiên kết nối khách."),
        ("23", ":SessionRouter", ":SettingsController", "Xác nhận thu hồi phiên phía máy chủ", "Server Ack", "Máy chủ phản hồi xác nhận phiên đã bị hủy bỏ."),
        ("24", ":SettingsController", ":SettingsScreen", "Điều hướng về màn hình khởi động ứng dụng", "Navigation", "Yêu cầu giao diện chuyển hướng về màn hình ban đầu."),
        ("25", ":SettingsScreen", "Người dùng", "Hiển thị giao diện chào mừng ban đầu", "Render Welcome", "Hiển thị giao diện chào đón người dùng khởi tạo phiên mới.")
    ]
    render_sequence_table(doc, uc2_3_steps)

    # =========================================================================
    # NHÓM 3: XÁC THỰC VÀ HỒ SƠ QUẢN TRỊ (UC3.1 - UC3.2)
    # =========================================================================
    add_heading_3(doc, "3.3.3. Nhóm UC3 - Xác thực và hồ sơ quản trị")

    # UC3.1
    add_paragraph(doc, "3.3.3.1. Sơ đồ tuần tự UC3.1 - Đăng nhập hệ thống quản trị:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép nhân viên nghiệp vụ, quản trị viên và quản trị cấp cao đăng nhập Trang quản trị Web bằng "
        "tên đăng nhập và mật khẩu được băm an toàn bằng Argon2id. Máy chủ áp dụng cơ chế giới hạn số lần thử (Rate Limiter). "
        "Đối với các tài khoản đặc quyền, hệ thống bắt buộc kiểm tra mã xác thực hai bước TOTP trước khi cấp mã truy cập JWT."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_14_seq_uc3_1_dang_nhap_he_thong_quan_tri.png",
        caption_text="Hình 3.14: Biểu đồ tuần tự ca sử dụng UC3.1 - Đăng nhập hệ thống quản trị",
        width_inches=6.2
    )
    uc3_1_steps = [
        ("1", "Người dùng Quản trị", ":LoginScreen", "Nhập tên đăng nhập, mật khẩu và gửi biểu mẫu", "Form Submit", "Người dùng điền thông tin tài khoản và nhấn Đăng nhập."),
        ("2", ":LoginScreen", ":RateLimiterGuard", "Gửi yêu cầu xác thực tài khoản đăng nhập", "HTTP POST", "Gửi gói tin đăng nhập qua cổng kiểm soát an ninh."),
        ("3", ":RateLimiterGuard", ":RateLimiterGuard", "Kiểm tra giới hạn số lần thử (Rate Limit)", "Security Guard", "Chặn đứng các cuộc tấn công Brute-force bằng Token Bucket."),
        ("4", ":RateLimiterGuard", ":AuthService", "Chuyển tiếp thông tin xác thực tài khoản", "Internal Call", "Chuyển tiếp thông tin hợp lệ sang dịch vụ xác thực."),
        ("5", ":AuthService", ":PostgreSQL DB", "Truy vấn tài khoản và chuỗi băm mật khẩu Argon2id", "SQL Query", "Truy vấn bản ghi tài khoản theo tên đăng nhập."),
        ("6", ":PostgreSQL DB", ":AuthService", "Trả về thông tin tài khoản và trạng thái hoạt động", "Recordset", "Trả về dữ liệu người dùng, trạng thái kích hoạt và chuỗi băm."),
        ("7", ":AuthService", ":AuthService", "Xác minh mật khẩu & kiểm tra trạng thái kích hoạt", "Crypto Verify", "Kiểm tra khớp mật khẩu bằng Argon2id và kiểm tra tài khoản có bị khóa không."),
        ("8", ":AuthService", ":LoginScreen", "Yêu cầu cung cấp mã xác thực TOTP 6 chữ số", "MFA Required", "Yêu cầu giao diện mở biểu mẫu nhập mã xác thực cấp hai."),
        ("9", ":LoginScreen", "Người dùng Quản trị", "Hiển thị biểu mẫu yêu cầu nhập mã TOTP", "Render MFA", "Hiển thị ô nhập mã TOTP từ Google Authenticator."),
        ("10", "Người dùng Quản trị", ":LoginScreen", "Nhập mã xác thực từ ứng dụng Authenticator", "Input Code", "Người dùng nhập mã 6 chữ số biến đổi theo thời gian."),
        ("11", ":LoginScreen", ":AuthService", "Gửi mã TOTP kèm mã yêu cầu phiên", "Verify MFA", "Gửi mã TOTP lên máy chủ xác minh."),
        ("12", ":AuthService", ":AuthService", "Xác minh tính hợp lệ của mã thời gian TOTP", "TOTP Validate", "Kiểm tra thuật toán RFC 6238 bảo đảm mã chính xác."),
        ("13", ":AuthService", ":AuthService", "Khởi tạo phiên làm việc và cấp mã truy cập JWT", "Generate JWT", "Tạo JWT Access Token chứa vai trò và phân quyền chi tiết."),
        ("14", ":AuthService", ":LoginScreen", "Trả về mã JWT kèm quyền hạn và vai trò", "Auth Success", "Gửi token xác thực thành công về trình duyệt."),
        ("15", ":LoginScreen", "Người dùng Quản trị", "Lưu phiên đăng nhập và điều hướng vào Dashboard", "Redirect", "Lưu token an toàn và chuyển tiếp vào Bảng điều khiển quản trị."),
        ("16", ":AuthService", ":RateLimiterGuard", "Ghi nhận số lần đăng nhập sai và từ chối", "Auth Failure", "Tăng biến đếm đăng nhập sai trong bộ đếm an ninh."),
        ("17", ":RateLimiterGuard", ":LoginScreen", "Báo lỗi xác thực hoặc cảnh báo tạm khóa tài khoản", "Error Response", "Phản hồi mã lỗi xác thực sai thông tin."),
        ("18", ":LoginScreen", "Người dùng Quản trị", "Hiển thị thông báo lỗi từ chối đăng nhập", "Show Error", "Hiển thị cảnh báo lỗi chi tiết cho người dùng.")
    ]
    render_sequence_table(doc, uc3_1_steps)

    # UC3.2
    add_paragraph(doc, "3.3.3.2. Sơ đồ tuần tự UC3.2 - Xem hồ sơ và đăng xuất:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng Trang quản trị Web xem thông tin hồ sơ tài khoản: tên đăng nhập, vai trò, "
        "mã công khai, ngày tạo, trạng thái xác thực nhiều yếu tố (MFA) và các quyền được cấp. Người dùng có thể thực hiện đăng xuất "
        "để thu hồi phiên làm việc trên máy chủ và xóa sạch mã truy cập lưu trong trình duyệt."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_15_seq_uc3_2_xem_ho_so_va_dang_xuat.png",
        caption_text="Hình 3.15: Biểu đồ tuần tự ca sử dụng UC3.2 - Xem hồ sơ và đăng xuất",
        width_inches=6.0
    )
    uc3_2_steps = [
        ("1", "Người dùng Web Admin", ":UserProfileScreen", "Mở mục Hồ sơ cá nhân trên thanh điều hướng", "UI Click", "Người dùng chọn xem thông tin tài khoản cá nhân."),
        ("2", ":UserProfileScreen", ":UserController", "Yêu cầu lấy thông tin chi tiết hồ sơ tài khoản", "API GET", "Gửi yêu cầu truy vấn thông tin định danh."),
        ("3", ":UserController", ":PostgreSQL DB", "Truy vấn thông tin người dùng, vai trò và quyền hạn", "SQL Query", "Đọc dữ liệu tài khoản từ bảng users."),
        ("4", ":PostgreSQL DB", ":UserController", "Trả về dữ liệu hồ sơ (loại trừ mật khẩu và khóa bí mật)", "UserDTO", "Trả về tập dữ liệu an toàn không chứa bí mật."),
        ("5", ":UserController", ":UserProfileScreen", "Gửi thông tin hồ sơ tài khoản hiển thị", "Data Response", "Truyền đối tượng hồ sơ về màn hình quản trị."),
        ("6", ":UserProfileScreen", "Người dùng Web Admin", "Hiển thị tên đăng nhập, vai trò, ngày tạo, trạng thái MFA và quyền", "Render Profile", "Hiển thị đầy đủ thông số tài khoản và các quyền được cấp."),
        ("7", "Người dùng Web Admin", ":UserProfileScreen", "Nhấn nút Đăng xuất khỏi hệ thống", "Logout Click", "Người dùng chọn kết thúc phiên làm việc trên Web Admin."),
        ("8", ":UserProfileScreen", ":AuthService", "Gửi yêu cầu thu hồi phiên làm việc hiện tại", "API Logout", "Gửi yêu cầu hủy token tới máy chủ xác thực."),
        ("9", ":AuthService", ":PostgreSQL DB", "Vô hiệu hóa mã phiên trong cơ sở dữ liệu", "SQL Update", "Cập nhật trường revoked = True trong bảng auth_sessions."),
        ("10", ":PostgreSQL DB", ":AuthService", "Xác nhận thu hồi phiên thành công", "Success Ack", "CSDL xác nhận bản ghi phiên đã bị vô hiệu hóa."),
        ("11", ":AuthService", ":UserProfileScreen", "Phản hồi kết thúc phiên làm việc thành công", "Logout Success", "Phản hồi thông báo phiên đã kết thúc an toàn."),
        ("12", ":UserProfileScreen", ":UserProfileScreen", "Xóa mã truy cập JWT lưu trên bộ nhớ trình duyệt", "Clear Storage", "Xóa sạch access token khỏi localStorage / cookie."),
        ("13", ":UserProfileScreen", "Người dùng Web Admin", "Điều hướng người dùng về màn hình Đăng nhập", "Redirect", "Chuyển hướng trình duyệt về giao diện đăng nhập ban đầu.")
    ]
    render_sequence_table(doc, uc3_2_steps)

    # =========================================================================
    # NHÓM 4: TỪ ĐIỂN VÀ ĐÁNH GIÁ CHẤT LƯỢNG (UC4.1 - UC4.4)
    # =========================================================================
    add_heading_3(doc, "3.3.4. Nhóm UC4 - Từ điển và đánh giá chất lượng")

    # UC4.1
    add_paragraph(doc, "3.3.4.1. Sơ đồ tuần tự UC4.1 - Tra cứu và xuất Từ điển:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng Trang quản trị Web đã xác thực tra cứu các cặp thuật ngữ trong Từ điển chuẩn "
        "(Bộ nhớ dịch - Translation Memory), tìm kiếm lọc phân trang theo cặp ngôn ngữ (Việt - Anh hoặc Anh - Việt) và xuất dữ liệu "
        "ra tệp CSV phục vụ đối soát hoặc lưu trữ."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_16_seq_uc4_1_tra_cuu_va_xuat_tu_dien.png",
        caption_text="Hình 3.16: Biểu đồ tuần tự ca sử dụng UC4.1 - Tra cứu và xuất Từ điển",
        width_inches=6.0
    )
    uc4_1_steps = [
        ("1", "Nhân viên / Quản trị", ":DictionaryScreen", "Mở trang Từ điển & chọn bộ lọc cặp ngôn ngữ", "UI Event", "Người dùng mở danh mục Từ điển và chọn chiều dịch cần xem."),
        ("2", ":DictionaryScreen", ":TranslationMemoryService", "Yêu cầu tra cứu từ điển kèm điều kiện tìm kiếm/lọc", "API Query", "Gửi yêu cầu nạp dữ liệu phân trang và bộ lọc cặp ngôn ngữ."),
        ("3", ":TranslationMemoryService", ":TranslationMemoryService", "Kiểm tra quyền đọc dữ liệu của người dùng", "RBAC Check", "Xác minh vai trò có quyền xem từ điển."),
        ("4", ":TranslationMemoryService", ":PostgreSQL DB", "Truy vấn danh sách thuật ngữ song ngữ theo trang", "SQL Query", "Quét bảng tm_entries theo ngôn ngữ nguồn và đích."),
        ("5", ":PostgreSQL DB", ":TranslationMemoryService", "Trả về danh sách các cặp từ điển thỏa mãn", "Recordset", "Trả về danh sách thuật ngữ và số lượng bản ghi."),
        ("6", ":TranslationMemoryService", ":DictionaryScreen", "Gửi dữ liệu danh mục thuật ngữ hiển thị phân trang", "Data Response", "Truyền tập bản ghi về cho bảng dữ liệu giao diện."),
        ("7", ":DictionaryScreen", "Nhân viên / Quản trị", "Hiển thị bảng thuật ngữ song ngữ chuyên ngành", "Render Table", "Hiển thị bảng danh mục thuật ngữ rõ ràng kèm phân trang."),
        ("8", "Nhân viên / Quản trị", ":DictionaryScreen", "Nhấn nút Xuất dữ liệu CSV", "Export Click", "Người dùng bấm nút xuất tệp CSV chứa dữ liệu đang xem."),
        ("9", ":DictionaryScreen", ":TranslationMemoryService", "Yêu cầu trích xuất tệp CSV theo phạm vi đang xem", "API Export", "Gửi yêu cầu tạo luồng tệp CSV từ bộ lọc hiện thời."),
        ("10", ":TranslationMemoryService", ":PostgreSQL DB", "Đọc toàn bộ các bản ghi theo bộ lọc hiện tại", "SQL Query", "Truy vấn toàn bộ các bản ghi khớp điều kiện lọc."),
        ("11", ":PostgreSQL DB", ":TranslationMemoryService", "Trả về tập dữ liệu các mục từ điển", "Recordset", "CSDL cung cấp toàn bộ tập dữ liệu cần xuất."),
        ("12", ":TranslationMemoryService", ":DictionaryScreen", "Đóng gói và trả về luồng tệp tải xuống định dạng CSV", "Stream File", "Đóng gói tệp CSV với mã hóa UTF-8 kèm BOM."),
        ("13", ":DictionaryScreen", "Nhân viên / Quản trị", "Trình duyệt tự động tải tệp CSV về máy người dùng", "File Download", "Tệp CSV được tải về thư mục Download của người dùng.")
    ]
    render_sequence_table(doc, uc4_1_steps)

    # UC4.2
    add_paragraph(doc, "3.3.4.2. Sơ đồ tuần tự UC4.2 - Cập nhật Từ điển:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị cấp cao thêm, xóa hoặc nhập hàng loạt các cặp thuật ngữ chuẩn trên Trang quản trị Web. "
        "Hệ thống tự động chuẩn hóa văn bản (:TextNormalizer) để tránh trùng lặp hình thức và vô hiệu hóa bộ đệm liên quan "
        "khi có thay đổi nhằm đảm bảo tính đồng nhất của Bộ nhớ dịch."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_17_seq_uc4_2_cap_nhat_tu_dien.png",
        caption_text="Hình 3.17: Biểu đồ tuần tự ca sử dụng UC4.2 - Cập nhật Từ điển",
        width_inches=6.2
    )
    uc4_2_steps = [
        ("1", "Quản trị cấp cao", ":DictionaryScreen", "Nhập cặp thuật ngữ hoặc tải tệp danh mục CSV/XLSX", "Form / Upload", "Nhập văn bản nguồn/đích hoặc tải lên tệp danh sách thuật ngữ."),
        ("2", ":DictionaryScreen", ":TranslationMemoryService", "Yêu cầu thêm mới hoặc nhập hàng loạt cặp dịch chuẩn", "API Mutation", "Gửi gói dữ liệu thuật ngữ cần cập nhật tới Service."),
        ("3", ":TranslationMemoryService", ":TranslationMemoryService", "Kiểm tra quyền Quản trị cấp cao và tính hợp lệ dữ liệu", "RBAC Check", "Chỉ Quản trị cấp cao mới được cấp quyền sửa đổi Từ điển."),
        ("4", ":TranslationMemoryService", ":TextNormalizer", "Chuẩn hóa câu chữ, loại bỏ khoảng trắng và ký tự thừa", "Normalize Call", "Tiến hành chuẩn hóa chuỗi văn bản nguồn và đích."),
        ("5", ":TextNormalizer", ":TranslationMemoryService", "Trả về chuỗi văn bản đã chuẩn hóa hình thức", "Normalized Text", "Cung cấp chuỗi chuẩn hóa để kiểm tra trùng lặp."),
        ("6", ":TranslationMemoryService", ":PostgreSQL DB", "Lưu các cặp thuật ngữ vào bảng từ điển chuẩn", "SQL Insert/Upsert", "Ghi nhận bản ghi mới vào bảng tm_entries."),
        ("7", ":PostgreSQL DB", ":TranslationMemoryService", "Xác nhận đã ghi dữ liệu và làm mới bộ nhớ đệm", "Success Ack", "CSDL xác nhận lưu thành công và cập nhật bộ đệm TM."),
        ("8", ":TranslationMemoryService", ":DictionaryScreen", "Phản hồi kết quả cập nhật từ điển thành công", "API Success", "Báo cáo kết quả thêm/nhập thuật ngữ hoàn tất."),
        ("9", ":DictionaryScreen", "Quản trị cấp cao", "Làm mới danh mục từ điển và thông báo thành công", "Render Alert", "Làm mới bảng hiển thị và báo số lượng mục đã thêm."),
        ("10", "Quản trị cấp cao", ":DictionaryScreen", "Nhấn nút Xóa mục thuật ngữ & xác nhận thao tác", "Delete Click", "Người dùng chọn mục cần xóa và xác nhận cảnh báo."),
        ("11", ":DictionaryScreen", ":TranslationMemoryService", "Yêu cầu xóa mục từ điển theo mã ID", "API Delete", "Gửi lệnh yêu cầu xóa mục thuật ngữ chỉ định."),
        ("12", ":TranslationMemoryService", ":PostgreSQL DB", "Xóa bản ghi trong CSDL và vô hiệu hóa bộ đệm liên quan", "SQL Delete", "Thực thi xóa hàng dữ liệu và xóa khóa cache liên quan."),
        ("13", ":PostgreSQL DB", ":TranslationMemoryService", "Xác nhận đã loại bỏ bản ghi thành công", "Success Ack", "CSDL xác nhận đã xóa sạch bản ghi chỉ định."),
        ("14", ":TranslationMemoryService", ":DictionaryScreen", "Phản hồi kết quả xóa mục thuật ngữ thành công", "API Success", "Controller báo kết quả xóa hoàn tất về giao diện."),
        ("15", ":DictionaryScreen", "Quản trị cấp cao", "Cập nhật giao diện loại bỏ bản ghi khỏi danh mục", "UI Animation", "Xóa dòng tương ứng khỏi bảng hiển thị từ điển.")
    ]
    render_sequence_table(doc, uc4_2_steps)

    # UC4.3
    add_paragraph(doc, "3.3.4.3. Sơ đồ tuần tự UC4.3 - Đánh giá và hiệu chỉnh chất lượng bản dịch:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép nhân viên nghiệp vụ và các vai trò cao hơn duyệt hàng đợi kiểm soát chất lượng (QA), kiểm tra "
        "văn bản nhận dạng và bản dịch kèm âm thanh gốc, chấm độ đầy đủ ý nghĩa (adequacy), độ trôi chảy (fluency), phân loại lỗi "
        "theo chuẩn MQM và lưu riêng văn bản hiệu chỉnh tách khỏi kết quả gốc để phục vụ truy vết."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_18_seq_uc4_3_danh_gia_va_hieu_chinh_chat_luong_ban_dich.png",
        caption_text="Hình 3.18: Biểu đồ tuần tự ca sử dụng UC4.3 - Đánh giá và hiệu chỉnh chất lượng bản dịch",
        width_inches=6.2
    )
    uc4_3_steps = [
        ("1", "Nhân viên thẩm định QA", ":QAQueueReviewScreen", "Mở hàng đợi thẩm định QA & chọn bản ghi cần đánh giá", "UI Select", "Nhân viên chọn một lượt dịch trong hàng đợi QA cần thẩm định."),
        ("2", ":QAQueueReviewScreen", ":QualityReviewService", "Yêu cầu lấy thông tin chi tiết lượt dịch kèm tệp âm thanh", "API GET", "Gửi yêu cầu tải toàn bộ ngữ cảnh lượt dịch cần xem xét."),
        ("3", ":QualityReviewService", ":PostgreSQL DB", "Truy vấn bản ghi dịch gốc và liên kết tài sản âm thanh", "SQL Query", "Đọc bảng translation_logs và audio_assets liên kết."),
        ("4", ":PostgreSQL DB", ":QualityReviewService", "Trả về câu gốc, câu dịch máy và đường dẫn âm thanh", "Recordset", "Trả về đầy đủ văn bản nhận dạng, bản dịch và tệp WAV."),
        ("5", ":QualityReviewService", ":QAQueueReviewScreen", "Hiển thị chi tiết bản dịch để thẩm định viên kiểm tra", "Render Detail", "Giao diện hiển thị đối chiếu câu gốc, câu dịch và trình phát audio."),
        ("6", "Nhân viên thẩm định QA", ":QAQueueReviewScreen", "Nhập văn bản hiệu chỉnh chuẩn, chọn thang điểm và gán lỗi MQM", "Input Evaluation", "Thẩm định viên nhập bản dịch chuẩn, chấm điểm và gán lỗi."),
        ("7", ":QAQueueReviewScreen", ":QualityReviewService", "Gửi phiếu đánh giá chất lượng (Adequacy, Fluency, Lỗi MQM)", "API POST", "Gửi toàn bộ phiếu chấm điểm và văn bản hiệu chỉnh."),
        ("8", ":QualityReviewService", ":MQMEvaluator", "Tính toán điểm số MQM và phân loại mức độ nghiêm trọng", "Eval Calc", "Tính trọng số lỗi MQM (Minor, Major, Critical)."),
        ("9", ":MQMEvaluator", ":QualityReviewService", "Trả về điểm MQM và danh mục mức độ lỗi", "Score Result", "Cung cấp điểm tổng hợp và mức độ nghiêm trọng của bản dịch."),
        ("10", ":QualityReviewService", ":PostgreSQL DB", "Lưu bản ghi thẩm định mới (QualityReview) và cập nhật cờ đã duyệt", "SQL Insert/Update", "Lưu phiếu đánh giá vào quality_reviews và cập nhật trạng thái."),
        ("11", ":PostgreSQL DB", ":QualityReviewService", "Xác nhận lưu phiếu thẩm định và nhật ký kiểm toán thành công", "Success Ack", "CSDL xác nhận bản ghi đánh giá đã được lưu trữ bền vững."),
        ("12", ":QualityReviewService", ":QAQueueReviewScreen", "Thông báo lưu kết quả đánh giá chất lượng thành công", "API Success", "Phản hồi kết quả đánh giá hoàn tất về giao diện."),
        ("13", ":QAQueueReviewScreen", "Nhân viên thẩm định QA", "Cập nhật trạng thái bản ghi trong hàng đợi sang Đã thẩm định", "UI Status Update", "Chuyển màu trạng thái bản ghi sang xanh lá (Đã kiểm chuẩn).")
    ]
    render_sequence_table(doc, uc4_3_steps)

    # UC4.4
    add_paragraph(doc, "3.3.4.4. Sơ đồ tuần tự UC4.4 - Chuẩn bị dữ liệu QA cho huấn luyện:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép thẩm định viên xác định bản ghi kiểm soát chất lượng có đủ điều kiện làm nguồn dữ liệu "
        "huấn luyện cho Whisper hoặc NLLB hay không; đồng thời ghi nhận trạng thái đồng ý sử dụng dữ liệu (consent), kiểm soát "
        "thông tin nhận dạng cá nhân (PII) và phân bổ dữ liệu thuộc tập huấn luyện, kiểm định hoặc kiểm tra (split_tag)."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_19_seq_uc4_4_chuan_bi_du_lieu_qa_cho_huan_luyen.png",
        caption_text="Hình 3.19: Biểu đồ tuần tự ca sử dụng UC4.4 - Chuẩn bị dữ liệu QA cho huấn luyện",
        width_inches=6.2
    )
    uc4_4_steps = [
        ("1", "Nhân viên kiểm soát QA", ":QAQueueReviewScreen", "Chọn mục đích gắn nhãn dữ liệu huấn luyện cho Whisper / NLLB", "Checkbox Select", "Thẩm định viên tích chọn mô hình mục tiêu cần sử dụng mẫu câu."),
        ("2", "Nhân viên kiểm soát QA", ":QAQueueReviewScreen", "Xác nhận trạng thái đồng ý sử dụng & kiểm duyệt an toàn PII", "Consent / PII", "Xác nhận người dùng đồng ý và dữ liệu không chứa thông tin nhạy cảm."),
        ("3", "Nhân viên kiểm soát QA", ":QAQueueReviewScreen", "Chọn phân chia tập dữ liệu (Huấn luyện / Kiểm định / Kiểm tra)", "Split Tag Dropdown", "Gán nhãn phân chia dữ liệu (Train / Validation / Test)."),
        ("4", ":QAQueueReviewScreen", ":QualityReviewService", "Gửi yêu cầu phê duyệt bản ghi vào kho ngữ liệu huấn luyện", "API Approve", "Gửi thông tin phê chuẩn mẫu dữ liệu huấn luyện."),
        ("5", ":QualityReviewService", ":QualityReviewService", "Kiểm tra tính hợp lệ của âm thanh nguồn và văn bản chuẩn hóa", "Integrity Check", "Kiểm tra định dạng audio 16kHz và độ dài văn bản hợp lệ."),
        ("6", ":QualityReviewService", ":DatasetCorpusExtractor", "Trích xuất và định dạng mẫu câu theo chuẩn Whisper/NLLB", "Extract Corpus", "Định dạng mẫu câu song ngữ hoặc cặp âm thanh - văn bản."),
        ("7", ":DatasetCorpusExtractor", ":QualityReviewService", "Gói dữ liệu mẫu câu huấn luyện đã sẵn sàng", "Ready Package", "Xác nhận gói dữ liệu mẫu câu đã chuẩn hóa thành công."),
        ("8", ":QualityReviewService", ":PostgreSQL DB", "Cập nhật cờ use_for_whisper / use_for_nllb và split_tag vào CSDL", "SQL Update", "Lưu trạng thái phê duyệt huấn luyện vào bảng quality_reviews."),
        ("9", ":PostgreSQL DB", ":QualityReviewService", "Xác nhận lưu trạng thái mẫu câu huấn luyện thành công", "Success Ack", "CSDL xác nhận bản ghi đã nằm trong kho dữ liệu huấn luyện."),
        ("10", ":QualityReviewService", ":QAQueueReviewScreen", "Thông báo bản ghi đã sẵn sàng phục vụ đóng băng tập dữ liệu", "API Success", "Báo cáo bản ghi đã đạt chuẩn huấn luyện AI."),
        ("11", ":QAQueueReviewScreen", "Nhân viên kiểm soát QA", "Hiển thị nhãn phê duyệt dữ liệu huấn luyện thành công", "UI Badge Update", "Hiển thị huy hiệu Đạt chuẩn huấn luyện trên giao diện."),
        ("12", ":QualityReviewService", ":PostgreSQL DB", "Đánh dấu bản ghi bị loại khỏi nguồn ngữ liệu huấn luyện", "SQL Reject", "Đánh dấu từ chối bản ghi nếu vi phạm PII hoặc thiếu audio."),
        ("13", ":PostgreSQL DB", ":QualityReviewService", "Xác nhận ghi nhận trạng thái từ chối dữ liệu", "Success Ack", "CSDL cập nhật trạng thái không đủ điều kiện."),
        ("14", ":QualityReviewService", ":QAQueueReviewScreen", "Phản hồi lý do không đủ điều kiện đưa vào tập dữ liệu", "API Reject", "Thông báo lý do từ chối mẫu dữ liệu."),
        ("15", ":QAQueueReviewScreen", "Nhân viên kiểm soát QA", "Hiển thị cảnh báo từ chối phê duyệt dữ liệu huấn luyện", "Show Warning", "Hiển thị cảnh báo màu đỏ thông báo nguyên nhân vi phạm.")
    ]
    render_sequence_table(doc, uc4_4_steps)

    # =========================================================================
    # NHÓM 5: GIÁM SÁT VÀ LỊCH SỬ HỆ THỐNG (UC5.1 - UC5.2)
    # =========================================================================
    add_heading_3(doc, "3.3.5. Nhóm UC5 - Giám sát và lịch sử hệ thống")

    # UC5.1
    add_paragraph(doc, "3.3.5.1. Sơ đồ tuần tự UC5.1 - Xem Bảng điều khiển và Thống kê:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng Trang quản trị Web theo dõi số liệu tổng quan, hoạt động dịch, bản ghi bị gắn cờ, "
        "độ trễ phân vị P50/P90/P99 và các số đo vận hành nhằm đánh giá tình trạng hiệu năng hệ thống theo thời gian thực."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_20_seq_uc5_1_xem_bang_dieu_khien_va_thong_ke.png",
        caption_text="Hình 3.20: Biểu đồ tuần tự ca sử dụng UC5.1 - Xem Bảng điều khiển và Thống kê",
        width_inches=6.2
    )
    uc5_1_steps = [
        ("1", "Người dùng Quản trị", ":DashboardScreen", "Mở Bảng điều khiển & chọn khoảng thời gian giám sát", "UI Event", "Người dùng truy cập Dashboard và chọn mốc thời gian Hôm nay/Tuần/Tháng."),
        ("2", ":DashboardScreen", ":TelemetryController", "Yêu cầu truy vấn số liệu tổng quan và biểu đồ vận hành", "API Query", "Gửi yêu cầu tải gói dữ liệu thống kê tổng hợp."),
        ("3", ":TelemetryController", ":TelemetryController", "Khởi tạo tiến trình tổng hợp số liệu đo kiểm độ trễ", "Aggregate Init", "Khởi tạo tiến trình tính toán chỉ số hiệu năng."),
        ("4", ":TelemetryController", ":PipelineMetric", "Yêu cầu tính toán phân vị độ trễ P50/P90/P99 và tỷ lệ lỗi", "Metric Query", "Yêu cầu trích xuất số liệu đo kiểm độ trễ từng chặng."),
        ("5", ":PipelineMetric", ":PostgreSQL DB", "Quét bảng pipeline_metrics và translation_logs theo mốc thời gian", "SQL Aggregate", "Thực thi truy vấn tổng hợp trên cơ sở dữ liệu."),
        ("6", ":PostgreSQL DB", ":PipelineMetric", "Trả về tập dữ liệu đo kiểm và các lượt dịch liên quan", "Recordset", "CSDL trả về tập hợp dữ liệu thống kê."),
        ("7", ":PipelineMetric", ":TelemetryController", "Trả về các chỉ số phân vị độ trễ và tỷ lệ gắn cờ", "Calculated Stats", "Cung cấp phân vị độ trễ P50, P90, P99 và tỷ lệ gắn cờ QA."),
        ("8", ":TelemetryController", ":TelemetryController", "Đóng gói số liệu tổng hợp (Lượt dịch, cờ lỗi, phiên đồng thời)", "Package DTO", "Đóng gói số liệu tổng quan cho giao diện Dashboard."),
        ("9", ":TelemetryController", ":DashboardScreen", "Gửi gói dữ liệu thống kê tổng hợp về giao diện", "API Response", "Truyền dữ liệu JSON chứa toàn bộ biểu đồ và thẻ chỉ số."),
        ("10", ":DashboardScreen", "Người dùng Quản trị", "Hiển thị các thẻ chỉ số KPI và biểu đồ độ trễ thời gian thực", "Render Charts", "Vẽ biểu đồ ECharts và hiển thị các thẻ KPI trực quan.")
    ]
    render_sequence_table(doc, uc5_1_steps)

    # UC5.2
    add_paragraph(doc, "3.3.5.2. Sơ đồ tuần tự UC5.2 - Tra cứu lịch sử hệ thống:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị viên và Quản trị cấp cao tra cứu lịch sử các lượt dịch đã ghi nhận ở máy chủ xử lý "
        "để phục vụ điều tra vận hành và đối chiếu kiểm soát chất lượng (QA). Phân quyền RBAC nghiêm ngặt: Nhân viên nghiệp vụ "
        "bị từ chối truy cập trang này."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_21_seq_uc5_2_tra_cuu_lich_su_he_thong.png",
        caption_text="Hình 3.21: Biểu đồ tuần tự ca sử dụng UC5.2 - Tra cứu lịch sử hệ thống",
        width_inches=6.2
    )
    uc5_2_steps = [
        ("1", "Quản trị viên / Quản trị cấp cao", ":SystemHistoryScreen", "Mở trang Lịch sử hệ thống & nhập tiêu chí tra cứu", "UI Filter", "Người dùng mở trang Lịch sử hệ thống và điền bộ lọc tra cứu."),
        ("2", ":SystemHistoryScreen", ":RBACGuard", "Gửi yêu cầu truy vấn nhật ký dịch máy chủ", "API Request", "Gửi yêu cầu truy vấn nhật ký qua cổng phân quyền."),
        ("3", ":RBACGuard", ":RBACGuard", "Kiểm tra quyền hạn truy cập theo vai trò người dùng", "Role Check", "Xác minh người dùng có vai trò Admin hoặc SuperAdmin."),
        ("4", ":RBACGuard", ":HistoryAdminController", "Chuyển tiếp yêu cầu truy vấn nhật ký hệ thống", "Forward Call", "Chuyển tiếp yêu cầu hợp lệ sang Controller xử lý."),
        ("5", ":HistoryAdminController", ":PostgreSQL DB", "Truy vấn bảng nhật ký dịch theo từ khóa, thời gian và trạng thái", "SQL Query", "Quét bảng translation_logs theo điều kiện lọc."),
        ("6", ":PostgreSQL DB", ":HistoryAdminController", "Trả về danh sách các bản ghi nhật ký dịch máy chủ", "Recordset", "Trả về danh sách các lượt dịch hệ thống thỏa mãn."),
        ("7", ":HistoryAdminController", ":SystemHistoryScreen", "Gửi danh sách kết quả lịch sử hệ thống hiển thị phân trang", "API Response", "Gửi danh sách bản ghi về giao diện hiển thị."),
        ("8", ":SystemHistoryScreen", "Quản trị viên / Quản trị cấp cao", "Hiển thị bảng nhật ký gồm câu gốc, câu dịch, thời gian và trạng thái", "Render Table", "Hiển thị bảng chi tiết các lượt dịch máy chủ xử lý."),
        ("9", ":RBACGuard", ":SystemHistoryScreen", "Từ chối truy cập và báo lỗi không có quyền (403 Forbidden)", "Forbidden Error", "Báo lỗi từ chối truy cập đối với Nhân viên nghiệp vụ."),
        ("10", ":SystemHistoryScreen", "Quản trị viên / Quản trị cấp cao", "Hiển thị cảnh báo từ chối quyền truy cập trang lịch sử hệ thống", "Show 403 Alert", "Hiển thị thông báo người dùng không có quyền truy cập.")
    ]
    render_sequence_table(doc, uc5_2_steps)

    # =========================================================================
    # NHÓM 6: QUẢN TRỊ HỆ THỐNG (UC6.1 - UC6.3)
    # =========================================================================
    add_heading_3(doc, "3.3.6. Nhóm UC6 - Quản trị hệ thống")

    # UC6.1
    add_paragraph(doc, "3.3.6.1. Sơ đồ tuần tự UC6.1 - Quản lý người dùng:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị cấp cao xem, tìm kiếm, tạo và cập nhật tài khoản trên Trang quản trị Web; thay đổi "
        "vai trò (Nhân viên / Quản trị viên), trạng thái hoạt động và thu hồi phiên. Khi ngừng sử dụng, chuyển tài khoản sang trạng thái "
        "không hoạt động (Soft Delete) thay vì xóa vật lý dữ liệu; toàn bộ thao tác được ghi nhận vào nhật ký kiểm toán."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_22_seq_uc6_1_quan_ly_nguoi_dung.png",
        caption_text="Hình 3.22: Biểu đồ tuần tự ca sử dụng UC6.1 - Quản lý người dùng",
        width_inches=6.2
    )
    uc6_1_steps = [
        ("1", "Quản trị cấp cao", ":UserManagementScreen", "Mở danh sách người dùng & chọn tạo mới hoặc cập nhật tài khoản", "UI Action", "Quản trị cấp cao mở mục quản lý nhân sự và chọn tác vụ."),
        ("2", ":UserManagementScreen", ":UserController", "Gửi thông tin tài khoản (Tên đăng nhập, vai trò, trạng thái)", "API Mutation", "Gửi thông tin tài khoản cần xử lý tới Controller."),
        ("3", ":UserController", ":UserController", "Kiểm tra quyền Quản trị cấp cao và chính sách bảo vệ tài khoản", "Security Check", "Kiểm tra quyền tối cao và chống tự vô hiệu hóa tài khoản chính mình."),
        ("4", ":UserController", ":UserController", "Băm mật khẩu an toàn bằng giải thuật Argon2id", "Crypto Hash", "Băm mật khẩu với muối ngẫu nhiên theo chuẩn bảo mật cao."),
        ("5", ":UserController", ":PostgreSQL DB", "Lưu thông tin tài khoản mới vào cơ sở dữ liệu", "SQL Insert", "Ghi bản ghi người dùng mới vào bảng users."),
        ("6", ":PostgreSQL DB", ":UserController", "Xác nhận tạo tài khoản thành công", "Success Ack", "CSDL xác nhận lưu người dùng mới thành công."),
        ("7", ":UserController", ":AuditLogger", "Ghi nhật ký kiểm toán hành vi tạo người dùng mới", "Audit Action", "Ghi nhận sự kiện tạo tài khoản vào bảng audit_logs."),
        ("8", ":UserController", ":UserManagementScreen", "Thông báo tạo tài khoản thành công và cấp quyền", "API Success", "Phản hồi kết quả tạo tài khoản thành công về giao diện."),
        ("9", ":UserManagementScreen", "Quản trị cấp cao", "Cập nhật danh sách hiển thị người dùng mới", "Render UI", "Làm mới bảng danh sách tài khoản quản trị."),
        ("10", ":UserController", ":PostgreSQL DB", "Cập nhật trạng thái tài khoản thành Không hoạt động (Soft Delete)", "SQL Update", "Chuyển cờ is_active = False trong bảng users."),
        ("11", ":UserController", ":PostgreSQL DB", "Thu hồi toàn bộ các phiên làm việc đang hoạt động của tài khoản", "SQL Revoke", "Đánh dấu thu hồi toàn bộ token phiên trong auth_sessions."),
        ("12", ":PostgreSQL DB", ":UserController", "Xác nhận đã khóa tài khoản và hủy phiên thành công", "Success Ack", "CSDL xác nhận hoàn tất thao tác vô hiệu hóa."),
        ("13", ":UserController", ":AuditLogger", "Ghi nhận sự kiện vô hiệu hóa tài khoản vào nhật ký kiểm toán", "Audit Action", "Lưu vết sự kiện khóa tài khoản vào nhật ký an ninh."),
        ("14", ":UserController", ":UserManagementScreen", "Phản hồi trạng thái vô hiệu hóa tài khoản thành công", "API Success", "Controller báo kết quả hoàn tất về giao diện."),
        ("15", ":UserManagementScreen", "Quản trị cấp cao", "Cập nhật giao diện làm mới danh sách tài khoản", "UI Update", "Cập nhật huy hiệu trạng thái tài khoản sang Đã khóa.")
    ]
    render_sequence_table(doc, uc6_1_steps)

    # UC6.2
    add_paragraph(doc, "3.3.6.2. Sơ đồ tuần tự UC6.2 - Quản lý khóa API:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị cấp cao tạo và quản lý các khóa truy cập API dùng cho tích hợp hệ thống. Mỗi khóa có "
        "tên, phạm vi quyền (scopes) và thời hạn rõ ràng. Giá trị khóa nguyên bản chỉ hiển thị một lần duy nhất lúc tạo; hệ thống chỉ lưu "
        "chuỗi băm SHA-256 trong CSDL. Quản trị viên có thể thu hồi khóa bất cứ lúc nào."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_23_seq_uc6_2_quan_ly_khoa_api.png",
        caption_text="Hình 3.23: Biểu đồ tuần tự ca sử dụng UC6.2 - Quản lý khóa API",
        width_inches=6.2
    )
    uc6_2_steps = [
        ("1", "Quản trị cấp cao", ":ApiKeyScreen", "Mở mục Quản lý khóa API & nhấn Tạo khóa mới", "UI Click", "Người dùng mở trang quản lý khóa và nhấn nút Tạo khóa mới."),
        ("2", "Quản trị cấp cao", ":ApiKeyScreen", "Nhập tên khóa, chọn phạm vi quyền và thời hạn hiệu lực", "Form Input", "Điền tên định danh, phạm vi dịch và chọn số ngày hiệu lực."),
        ("3", ":ApiKeyScreen", ":ApiKeyService", "Gửi yêu cầu phát hành khóa truy cập API mới", "API Create", "Gửi thông số khóa mới tới ApiKeyService."),
        ("4", ":ApiKeyService", ":ApiKeyService", "Sinh ngẫu nhiên chuỗi khóa bí mật và băm SHA-256 để lưu trữ", "Crypto Hash", "Sinh token an toàn 64 ký tự và tính chuỗi băm SHA-256."),
        ("5", ":ApiKeyService", ":PostgreSQL DB", "Lưu thông tin khóa băm, phạm vi quyền và thời hạn vào CSDL", "SQL Insert", "Lưu bản ghi vào bảng api_keys với chuỗi băm."),
        ("6", ":PostgreSQL DB", ":ApiKeyService", "Xác nhận lưu thông tin khóa thành công", "Success Ack", "CSDL xác nhận lưu khóa mới thành công."),
        ("7", ":ApiKeyService", ":AuditLogger", "Ghi nhật ký kiểm toán hành vi phát hành khóa API mới", "Audit Action", "Ghi nhận sự kiện phát hành khóa vào audit_logs."),
        ("8", ":ApiKeyService", ":ApiKeyScreen", "Phản hồi chuỗi khóa gốc an toàn (chỉ hiển thị một lần duy nhất)", "Key Response", "Truyền khóa bí mật nguyên bản về trình duyệt."),
        ("9", ":ApiKeyScreen", "Quản trị cấp cao", "Hiển thị hộp thoại chứa mã khóa bí mật kèm nút sao chép an toàn", "Modal Show", "Hiển thị modal với cảnh báo sao chép và lưu trữ an toàn."),
        ("10", "Quản trị cấp cao", ":ApiKeyScreen", "Nhấn nút Thu hồi khóa API đã chọn", "Revoke Click", "Người dùng chọn khóa cần hủy hiệu lực và xác nhận."),
        ("11", ":ApiKeyScreen", ":ApiKeyService", "Gửi lệnh thu hồi và hủy hiệu lực của khóa", "API Revoke", "Gửi yêu cầu thu hồi khóa tới Service."),
        ("12", ":ApiKeyService", ":PostgreSQL DB", "Cập nhật trạng thái khóa thành Đã thu hồi (Revoked) trong CSDL", "SQL Update", "Cập nhật trường is_active = False trong api_keys."),
        ("13", ":PostgreSQL DB", ":ApiKeyService", "Xác nhận đã hủy hiệu lực của khóa", "Success Ack", "CSDL xác nhận khóa đã bị vô hiệu hóa."),
        ("14", ":ApiKeyService", ":AuditLogger", "Ghi nhật ký kiểm toán hành vi thu hồi khóa API", "Audit Action", "Lưu vết sự kiện thu hồi khóa vào audit_logs."),
        ("15", ":ApiKeyService", ":ApiKeyScreen", "Thông báo thu hồi khóa API thành công", "API Success", "Phản hồi thông báo thu hồi khóa thành công."),
        ("16", ":ApiKeyScreen", "Quản trị cấp cao", "Cập nhật giao diện và làm mới trạng thái danh sách khóa", "Render UI", "Cập nhật trạng thái khóa sang Đã thu hồi trên bảng danh sách.")
    ]
    render_sequence_table(doc, uc6_2_steps)

    # UC6.3
    add_paragraph(doc, "3.3.6.3. Sơ đồ tuần tự UC6.3 - Quản lý cấu hình hệ thống:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị cấp cao thay đổi các thiết lập vận hành hệ thống được công bố (ngưỡng cắt câu VAD, "
        "thời gian giữ phiên, hạn mức gọi API, tỷ lệ Canary); kiểm tra định dạng và phạm vi giá trị trước khi áp dụng và lưu vết kiểm toán."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_24_seq_uc6_3_quan_ly_cau_hinh_he_thong.png",
        caption_text="Hình 3.24: Biểu đồ tuần tự ca sử dụng UC6.3 - Quản lý cấu hình hệ thống",
        width_inches=6.2
    )
    uc6_3_steps = [
        ("1", "Quản trị cấp cao", ":SystemSettingsScreen", "Mở trang Cài đặt hệ thống & xem các thông số vận hành", "UI Event", "Người dùng mở trang cấu hình hệ thống trên Web Admin."),
        ("2", "Quản trị cấp cao", ":SystemSettingsScreen", "Thay đổi giá trị cấu hình (Ngưỡng VAD, thời gian phiên, hạn mức gọi)", "Form Edit", "Điều chỉnh các thông số vận hành trong phạm vi cho phép."),
        ("3", ":SystemSettingsScreen", ":SettingsController", "Gửi yêu cầu cập nhật các giá trị cấu hình hệ thống", "API Update", "Gửi gói dữ liệu cấu hình mới tới SettingsController."),
        ("4", ":SettingsController", ":SettingsController", "Kiểm tra tính hợp lệ về kiểu dữ liệu và phạm vi cho phép", "Validate Config", "Kiểm tra kiểu dữ liệu và các giới hạn ngưỡng giá trị."),
        ("5", ":SettingsController", ":PostgreSQL DB", "Lưu các giá trị thiết lập mới vào bảng cấu hình hệ thống", "SQL Upsert", "Cập nhật các cặp khóa - giá trị vào bảng system_settings."),
        ("6", ":PostgreSQL DB", ":SettingsController", "Xác nhận lưu các thay đổi cấu hình thành công", "Success Ack", "CSDL xác nhận lưu các tham số cấu hình thành công."),
        ("7", ":SettingsController", ":AuditLogger", "Ghi nhật ký kiểm toán chi tiết các thay đổi cấu hình", "Audit Action", "Ghi nhận sự kiện sửa đổi cấu hình vào audit_logs."),
        ("8", ":SettingsController", ":SystemSettingsScreen", "Phản hồi cập nhật cấu hình hệ thống thành công", "API Success", "Báo cáo cập nhật thành công về cho giao diện."),
        ("9", ":SystemSettingsScreen", "Quản trị cấp cao", "Hiển thị thông báo đã áp dụng cấu hình và làm mới giao diện", "Render Toast", "Hiển thị thông báo áp dụng cấu hình thành công."),
        ("10", ":SettingsController", ":SystemSettingsScreen", "Từ chối lưu cấu hình và báo lỗi tham số không hợp lệ", "Validation Error", "Báo lỗi nếu tham số nằm ngoài phạm vi cho phép."),
        ("11", ":SystemSettingsScreen", "Quản trị cấp cao", "Hiển thị thông báo lỗi chi tiết từng tham số vi phạm", "Show Error", "Hiển thị cảnh báo lỗi chi tiết tại từng trường nhập liệu vi phạm.")
    ]
    render_sequence_table(doc, uc6_3_steps)

    # =========================================================================
    # NHÓM 7: HUẤN LUYỆN VÀ QUẢN LÝ MÔ HÌNH (UC7.1 - UC7.3)
    # =========================================================================
    add_heading_3(doc, "3.3.7. Nhóm UC7 - Huấn luyện và quản lý mô hình")

    # UC7.1
    add_paragraph(doc, "3.3.7.1. Sơ đồ tuần tự UC7.1 - Quản lý tập dữ liệu huấn luyện:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị viên và Quản trị cấp cao xem khả năng sẵn sàng của dữ liệu kiểm soát chất lượng (QA), "
        "tạo tập dữ liệu từ QA hoặc nguồn tải lên cho tác vụ NLLB hoặc Whisper, kiểm tra tính hợp lệ và đóng băng bản dữ liệu "
        "(Dataset Freeze) kèm mã băm SHA-256 cố định trước khi đưa vào huấn luyện."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_25_seq_uc7_1_quan_ly_tap_du_lieu_huan_luyen.png",
        caption_text="Hình 3.25: Biểu đồ tuần tự ca sử dụng UC7.1 - Quản lý tập dữ liệu huấn luyện",
        width_inches=6.2
    )
    uc7_1_steps = [
        ("1", "Quản trị viên / Quản trị cấp cao", ":TrainingCenterScreen", "Mở mục Dữ liệu huấn luyện & xem số lượng mẫu QA đủ điều kiện", "UI Event", "Người dùng mở tab Tập dữ liệu trong Trung tâm huấn luyện AI."),
        ("2", "Quản trị viên / Quản trị cấp cao", ":TrainingCenterScreen", "Chọn tác vụ (NLLB / Whisper) và tỷ lệ phân chia tập (80:10:10)", "Form Select", "Chọn mô hình mục tiêu và tỷ lệ chia tập Train/Val/Test."),
        ("3", ":TrainingCenterScreen", ":DatasetManager", "Gửi yêu cầu trích xuất và khởi tạo tập dữ liệu huấn luyện", "API Create Dataset", "Gửi yêu cầu tạo phiên bản tập dữ liệu huấn luyện mới."),
        ("4", ":DatasetManager", ":PostgreSQL DB", "Truy vấn các mẫu câu đạt chuẩn QA có gắn nhãn đồng ý huấn luyện", "SQL Query", "Truy vấn các bản ghi có use_for_whisper/nllb = True và consent = True."),
        ("5", ":PostgreSQL DB", ":DatasetManager", "Trả về tập hợp các bản ghi mẫu hợp lệ", "Recordset", "Trả về tập mẫu câu sạch kèm tệp âm thanh liên quan."),
        ("6", ":DatasetManager", ":DatasetManager", "Kiểm tra định dạng, phân chia các tập Train / Validation / Test", "Split Dataset", "Phân chia ngẫu nhiên có hạt giống (Seed) theo tỷ lệ 80:10:10."),
        ("7", ":DatasetManager", ":FileStorage (NFS/Disk)", "Ghi tệp dữ liệu huấn luyện đóng gói vào kho lưu trữ", "Write File", "Ghi các tệp JSONL/WAV vào thư mục lưu trữ tập dữ liệu."),
        ("8", ":FileStorage (NFS/Disk)", ":DatasetManager", "Xác nhận tệp dữ liệu đã ghi xong", "Success Ack", "Hệ thống tệp xác nhận việc lưu trữ tệp hoàn tất."),
        ("9", ":DatasetManager", ":DatasetManager", "Tạo mã băm toàn vẹn SHA-256 để chống can thiệp dữ liệu", "Compute Hash", "Tính mã băm SHA-256 trên toàn bộ tệp dữ liệu huấn luyện."),
        ("10", ":DatasetManager", ":PostgreSQL DB", "Lưu bản ghi phiên bản tập dữ liệu và đặt trạng thái Đóng băng (FROZEN)", "SQL Insert", "Lưu thông tin tập dữ liệu vào training_datasets với trạng thái FROZEN."),
        ("11", ":PostgreSQL DB", ":DatasetManager", "Xác nhận tạo và đóng băng tập dữ liệu thành công", "Success Ack", "CSDL xác nhận bản ghi tập dữ liệu đã đóng băng thành công."),
        ("12", ":DatasetManager", ":TrainingCenterScreen", "Phản hồi thông tin tập dữ liệu đã sẵn sàng phục vụ huấn luyện", "API Success", "Gửi thông tin phiên bản tập dữ liệu về cho giao diện."),
        ("13", ":TrainingCenterScreen", "Quản trị viên / Quản trị cấp cao", "Hiển thị thông tin phiên bản tập dữ liệu và mã kiểm tra SHA-256", "Render UI", "Hiển thị thông tin chi tiết phiên bản và huy hiệu Đóng băng.")
    ]
    render_sequence_table(doc, uc7_1_steps)

    # UC7.2
    add_paragraph(doc, "3.3.7.2. Sơ đồ tuần tự UC7.2 - Quản lý tiến trình huấn luyện:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị viên khởi tạo và theo dõi tiến trình huấn luyện LoRA (PEFT) trên GPU bằng tập dữ liệu "
        "đã đóng băng; theo dõi chu kỳ Epoch, bước Step và hàm mất mát (Train / Val Loss) thời gian thực; khi hoàn tất, đóng gói "
        "trọng số mô hình thành ModelArtifact sẵn sàng triển khai."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_26_seq_uc7_2_quan_ly_tien_trinh_huan_luyen.png",
        caption_text="Hình 3.26: Biểu đồ tuần tự ca sử dụng UC7.2 - Quản lý tiến trình huấn luyện",
        width_inches=6.2
    )
    uc7_2_steps = [
        ("1", "Quản trị viên / Quản trị cấp cao", ":TrainingCenterScreen", "Chọn tập dữ liệu đóng băng, mô hình nền và cấu hình tham số LoRA", "Form Config", "Cấu hình rank, alpha, learning rate và chọn tập dữ liệu đóng băng."),
        ("2", ":TrainingCenterScreen", ":TrainingWorker", "Gửi yêu cầu khởi tạo tiến trình huấn luyện mới", "API Start Job", "Gửi yêu cầu kích hoạt tiến trình huấn luyện."),
        ("3", ":TrainingWorker", ":GPUResourceManager", "Kiểm tra tài nguyên bộ nhớ VRAM của GPU", "Resource Check", "Kiểm tra bộ nhớ GPU còn trống có đủ tải batch size không."),
        ("4", ":GPUResourceManager", ":TrainingWorker", "Cấp phát tài nguyên GPU sẵn sàng cho tiến trình", "Resource Allocated", "Khóa và cấp phát tài nguyên GPU cho tiến trình huấn luyện."),
        ("5", ":TrainingWorker", ":PostgreSQL DB", "Tạo bản ghi tiến trình huấn luyện với trạng thái Chờ xử lý (PENDING)", "SQL Insert", "Ghi bản ghi vào training_jobs với trạng thái PENDING."),
        ("6", ":TrainingWorker", ":TrainingWorker", "Khởi chạy luồng huấn luyện nền và chuyển trạng thái sang RUNNING", "Async Thread", "Khởi chạy luồng huấn luyện PyTorch nền và đổi trạng thái sang RUNNING."),
        ("7", ":TrainingWorker", ":TrainingCenterScreen", "Xác nhận tiến trình đã bắt đầu chạy và trả về mã Job ID", "API Response", "Trả về định danh tiến trình huấn luyện cho giao diện."),
        ("8", ":TrainingCenterScreen", "Quản trị viên / Quản trị cấp cao", "Hiển thị bảng theo dõi tiến trình huấn luyện thời gian thực", "Render Monitor", "Hiển thị tiến độ và kết nối WebSocket nhận chỉ số thời gian thực."),
        ("9", ":TrainingWorker", ":TrainingWorker", "Huấn luyện tiến trình LoRA và tính toán giá trị độ lỗi (Train/Val Loss)", "Train Step", "Thực hiện lan truyền xuôi, lan truyền ngược và tính loss sau mỗi step."),
        ("10", ":TrainingWorker", ":PostgreSQL DB", "Ghi nhận chỉ số Epoch, Step, Loss vào bảng nhật ký sự kiện huấn luyện", "SQL Insert Log", "Ghi các bản ghi sự kiện vào training_job_events."),
        ("11", ":TrainingWorker", ":TrainingCenterScreen", "Gửi thông báo cập nhật tiến độ huấn luyện lên giao diện", "WS Telemetry", "Bắn sự kiện WebSocket chứa step, train_loss, val_loss hiện tại."),
        ("12", ":TrainingCenterScreen", "Quản trị viên / Quản trị cấp cao", "Cập nhật đường cong suy giảm độ lỗi (Loss Curve) trên biểu đồ", "Update Chart", "Vẽ biểu đồ hội tụ độ lỗi theo thời gian thực."),
        ("13", ":TrainingWorker", ":TrainingWorker", "Đóng gói trọng số mô hình LoRA thành phẩm (ModelArtifact)", "Package Weights", "Đóng gói tệp adapter weights kèm metadata và mã băm SHA-256."),
        ("14", ":TrainingWorker", ":PostgreSQL DB", "Cập nhật trạng thái tiến trình thành Hoàn thành (COMPLETED)", "SQL Update", "Cập nhật training_jobs sang COMPLETED và tạo bản ghi model_artifacts."),
        ("15", ":PostgreSQL DB", ":TrainingWorker", "Xác nhận lưu gói mô hình và trạng thái thành công", "Success Ack", "CSDL xác nhận lưu gói mô hình thành phẩm thành công."),
        ("16", ":TrainingWorker", ":TrainingCenterScreen", "Thông báo tiến trình huấn luyện hoàn tất thành công", "WS Complete", "Gửi sự kiện hoàn tất tiến trình huấn luyện lên giao diện."),
        ("17", ":TrainingCenterScreen", "Quản trị viên / Quản trị cấp cao", "Hiển thị liên kết gói mô hình sẵn sàng đưa vào triển khai", "Render Success", "Hiển thị huy hiệu Hoàn thành và nút điều hướng tới Triển khai.")
    ]
    render_sequence_table(doc, uc7_2_steps)

    # UC7.3
    add_paragraph(doc, "3.3.7.3. Sơ đồ tuần tự UC7.3 - Quản lý gói và phiên bản mô hình:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép theo dõi các gói mô hình do quá trình huấn luyện tạo ra và cho phép Quản trị cấp cao điều khiển "
        "vòng đời triển khai: đưa mô hình mới vào thử nghiệm giới hạn với tỷ lệ cho phép (Canary 10%), đưa vào phục vụ chính thức "
        "(Promote 100%) hoặc thực hiện khôi phục tức thì về phiên bản trước (1-Click Rollback) khi phát hiện sự cố."
    )
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_27_seq_uc7_3_quan_ly_goi_va_phien_ban_mo_hinh.png",
        caption_text="Hình 3.27: Biểu đồ tuần tự ca sử dụng UC7.3 - Quản lý gói và phiên bản mô hình",
        width_inches=6.3
    )
    uc7_3_steps = [
        ("1", "Quản trị cấp cao", ":DeploymentScreen", "Mở trung tâm triển khai mô hình & chọn gói mô hình LoRA", "UI Event", "Người dùng mở trang Triển khai và chọn gói mô hình cần thử nghiệm."),
        ("2", ":DeploymentScreen", ":DeploymentManager", "Yêu cầu áp dụng cấu hình thử nghiệm Canary 10% lưu lượng", "API Deploy Canary", "Gửi yêu cầu phân luồng 10% lưu lượng cho mô hình mới."),
        ("3", ":DeploymentManager", ":PostgreSQL DB", "Cập nhật trạng thái triển khai Canary vào cơ sở dữ liệu", "SQL Update", "Cập nhật canary_model và canary_percent = 10 trong model_deployments."),
        ("4", ":DeploymentManager", ":CanaryTrafficRouter", "Thiết lập tỷ lệ điều hướng lưu lượng: 90% Bản chính, 10% Bản thử nghiệm", "Set Routing", "Cấu hình bộ định tuyến lưu lượng trong bộ nhớ RAM."),
        ("5", ":CanaryTrafficRouter", ":DeploymentManager", "Xác nhận điều phối lưu lượng trong bộ nhớ thành công", "Success Ack", "Router xác nhận phân luồng đã có hiệu lực tức thì."),
        ("6", ":DeploymentManager", ":AuditLogger", "Ghi nhật ký kiểm toán sự kiện triển khai thử nghiệm Canary", "Audit Action", "Ghi nhận sự kiện triển khai Canary vào audit_logs."),
        ("7", ":DeploymentManager", ":DeploymentScreen", "Xác nhận cấu hình Canary đã kích hoạt thành công", "API Success", "Phản hồi kết quả kích hoạt phân luồng Canary về giao diện."),
        ("8", ":DeploymentScreen", "Quản trị cấp cao", "Hiển thị trạng thái phân luồng thử nghiệm trên giao diện", "Render UI", "Hiển thị tỷ lệ 90% Active / 10% Canary trên thanh giám sát."),
        ("9", "Quản trị cấp cao", ":DeploymentScreen", "Nhấn nút Đưa vào sử dụng chính thức (Promote Active)", "Promote Click", "Người dùng quyết định thăng cấp mô hình thử nghiệm thành bản chính thức."),
        ("10", ":DeploymentScreen", ":DeploymentManager", "Yêu cầu chuyển mô hình mới thành Active Model 100%", "API Promote", "Gửi lệnh thăng cấp mô hình thành Active."),
        ("11", ":DeploymentManager", ":PostgreSQL DB", "Lưu phiên bản hiện tại thành Bản dự phòng trước đó và kích hoạt bản mới", "SQL Update", "Cập nhật previous_active_model và active_model trong CSDL."),
        ("12", ":DeploymentManager", ":CanaryTrafficRouter", "Điều hướng toàn bộ 100% lưu lượng sang mô hình mới", "Route 100%", "Thiết lập điều hướng 100% lưu lượng sang mô hình mới."),
        ("13", ":DeploymentManager", ":AuditLogger", "Ghi nhận sự kiện thăng cấp mô hình vào nhật ký kiểm toán", "Audit Action", "Lưu vết sự kiện thăng cấp mô hình chính thức vào audit_logs."),
        ("14", ":DeploymentManager", ":DeploymentScreen", "Thông báo mô hình đã trở thành phiên bản chính thức", "API Success", "Phản hồi kết quả thăng cấp thành công về giao diện."),
        ("15", ":DeploymentScreen", "Quản trị cấp cao", "Cập nhật trạng thái Active trên bảng quản lý triển khai", "Render UI", "Cập nhật huy hiệu Active màu xanh cho mô hình mới."),
        ("16", "Quản trị cấp cao", ":DeploymentScreen", "Nhấn nút Khôi phục phiên bản trước (Rollback khẩn cấp)", "Emergency Click", "Phát hiện lỗi suy luận tăng vọt, người dùng nhấn Rollback khẩn cấp."),
        ("17", ":DeploymentScreen", ":DeploymentManager", "Yêu cầu hoàn tác tức thì về phiên bản mô hình cũ", "API Rollback", "Gửi lệnh phục hồi khẩn cấp về phiên bản trước đó."),
        ("18", ":DeploymentManager", ":PostgreSQL DB", "Khôi phục mô hình Active về phiên bản dự phòng trước đó trong CSDL", "SQL Rollback", "Đổi lại active_model = previous_active_model trong CSDL."),
        ("19", ":DeploymentManager", ":CanaryTrafficRouter", "Điều hướng ngay lập tức 100% lưu lượng về mô hình ổn định", "Reset Routing", "Ép router điều hướng toàn bộ lưu lượng về mô hình an toàn."),
        ("20", ":DeploymentManager", ":AuditLogger", "Ghi nhận sự kiện phục hồi khẩn cấp vào nhật ký kiểm toán", "Audit Action", "Ghi nhận sự kiện Rollback khẩn cấp vào nhật ký an ninh."),
        ("21", ":DeploymentManager", ":DeploymentScreen", "Thông báo đã hoàn tác hệ thống về phiên bản an toàn", "API Success", "Báo cáo hệ thống đã phục hồi an toàn thành công."),
        ("22", ":DeploymentScreen", "Quản trị cấp cao", "Cập nhật giao diện phục hồi phiên bản trước thành công", "Render Toast", "Giao diện chuyển trạng thái an toàn, hoàn tác mô hình thành công.")
    ]
    render_sequence_table(doc, uc7_3_steps)

    print("Section 3.3 built successfully with all 20 Sequence Diagrams matching Section 2.1.4.")

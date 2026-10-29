# -*- coding: utf-8 -*-
"""
Module providing Section 3.3: Thiet ke bieu do tuan tu (Sequence Diagrams) for T-Lingua report.
Includes all 18 Use Cases (UC1.1 to UC7.3) in 1:1 mapping with detailed UML sequence diagrams,
Vietnamese lifelines, message flow tables, and condition blocks matching Phenikaa standards and [DALN]2210.
"""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from scripts.docx_utils import (
    add_paragraph, add_heading_2, add_heading_3, add_caption, add_bullet,
    add_diagram_box, set_cell_background, set_cell_margins, set_table_borders,
    PRIMARY_COLOR, SECONDARY_COLOR, HEADER_BG_HEX, SUBHEADER_BG_HEX, ZEBRA_BG_HEX
)

def render_sequence_table(doc, steps):
    """
    Renders step-by-step message sequence table:
    [STT, Bên gửi, Bên nhận, Thông điệp / Lời gọi hàm, Dữ liệu phản hồi, Ý nghĩa nghiệp vụ]
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
    """Generates Section 3.3: Thiet ke bieu do tuan tu covering all 18 Use Cases."""
    add_heading_2(doc, "3.3. Thiết kế biểu đồ tuần tự (Sequence Diagrams)")
    
    add_paragraph(
        doc,
        "Biểu đồ tuần tự (Sequence Diagram) là thành phần then chốt trong thiết kế động của hệ thống T-Lingua, "
        "thể hiện chi tiết dòng thời gian và thứ tự tương tác giữa các tác nhân (Actors), các giao diện người dùng "
        "(Flutter Mobile / React Web Admin), các bộ điều phối bất đồng bộ (SessionActor, Mutex Lock), chuỗi xử lý "
        "trí tuệ nhân tạo (WebRTC VAD, Whisper STT, NLLB NMT, MMS VITS) và hệ thống lưu trữ bền vững (Database). "
        "Để đảm bảo tính nhất quán và hoàn thiện 100% với 18 ca sử dụng đã đặc tả tại Mục 3.1, hệ thống thiết kế "
        "chi tiết 18 biểu đồ tuần tự tương ứng 1:1, áp dụng đầy đủ các đường sinh (Lifelines) có nhãn tiếng Việt chuẩn mực "
        "và các khối điều kiện rẽ nhánh (alt), tùy chọn (opt) và lặp (loop)."
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
        "Hệ thống thu nhận các gói nhị phân PCM 16kHz, phân tích năng lượng qua WebRTC VAD, nhận dạng giọng nói tức thời với Whisper, "
        "dịch câu với NLLB-200, tổng hợp phát âm với MMS VITS và ghi nhận chỉ số đo kiểm vi mô (Telemetry)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC1.1 - Dịch giọng nói một chiều thời gian thực",
        """
Người_dùng     Giao_diện_Flutter    Cổng_WebSocket    SessionActor    Bộ_lọc_VAD     Tiến_trình_STT    Tiến_trình_NMT    Tiến_trình_TTS    CSDL_Telemetry
    |                  |                  |                |              |              |                 |                 |                 |
    |--[1] Nhấn Mic--->|                  |                |              |              |                 |                 |                 |
    |                  |--[2] ws://connect---------------->|              |              |                 |                 |                 |
    |                  |                  |--[3] init()--->|              |              |                 |                 |                 |
    |                  |<--[4] 101 Switching Protocols-----|              |              |                 |                 |                 |
    |--[5] Bắt đầu nói>|                  |                |              |              |                 |                 |                 |
    |                  |===[6] Stream PCM Chunks (20ms)===>|              |              |                 |                 |                 |
    |                  |                  |                |--[7] push--->|              |                 |                 |                 |
    |                  |                  |                |<--[8] SPEECH_START----------|                 |                 |                 |
    |                  |<--[9] Hiện sóng âm nhấp nháy------|              |              |                 |                 |                 |
    |--[10] Dứt lời--->|                  |                |              |              |                 |                 |                 |
    |                  |===[11] Stream Silent PCM Chunks==>|              |              |                 |                 |                 |
    |                  |                  |                |--[12] push-->|              |                 |                 |                 |
    |                  |                  |                |<--[13] SILENCE_CUTOFF (500ms)                 |                 |                 |
    |                  |                  |                |--[14] transcribe(audio_buffer)--------------->|                 |                 |
    |                  |                  |                |              |              |  (Whisper ASR)  |                 |                 |
    |                  |                  |                |<--[15] Trả về: source_text, stt_ms------------|                 |                 |
    |                  |<--[16] JSON: {event: 'STT_RESULT', text: source_text}-----------|                 |                 |                 |
    |                  |                  |                |--[17] translate(source_text, 'vi', 'en')----------------------->|                 |
    |                  |                  |                |              |              |                 |  (NLLB-200 NMT) |                 |
    |                  |                  |                |<--[18] Trả về: target_text, nmt_ms------------------------------|                 |
    |                  |<--[19] JSON: {event: 'TRANS_RESULT', text: target_text}---------|                 |                 |                 |
    |                  |                  |                |--[20] synthesize(target_text, 'en')-------------------------------------------->|
    |                  |                  |                |              |              |                 |                 |  (MMS VITS TTS) |
    |                  |                  |                |<--[21] Trả về: wav_bytes, tts_ms------------------------------------------------|
    |                  |<=== [22] Binary Stream: wav_bytes ==============================|                 |                 |                 |
    |<--[23] Phát loa--|                  |                |                                                                                   |
    |                  |                  |                |--[24] save_metrics(TurnData, VAD, STT, NMT, TTS, End-to-End Latency)------------->|
    |                  |                  |                |<--[25] Xác nhận ghi thành công (log_id, turn_id)----------------------------------|
"""
    )
    add_caption(doc, "Hình 3.3: Biểu đồ tuần tự ca sử dụng UC1.1 - Dịch giọng nói một chiều thời gian thực", is_table=False)

    uc1_1_steps = [
        ("1", "Người dùng", "Giao diện Flutter", "Chạm hoặc nhấn giữ nút Micrô", "None", "Người dùng ra lệnh bắt đầu thu âm câu nói."),
        ("2", "Giao diện Flutter", "Cổng WebSocket", "ws://.../ws/translate?src=vi&tgt=en", "101 Protocols", "Thiết lập đường truyền nhị phân hai chiều độ trễ thấp."),
        ("3", "Cổng WebSocket", "SessionActor", "SessionActor.create(session_id)", "Actor Instance", "Khởi tạo tác tử cô lập phiên xử lý của người dùng."),
        ("4", "SessionActor", "Giao diện Flutter", "emit_ready_event()", "WS Ready", "Thông báo máy khách sẵn sàng truyền dữ liệu."),
        ("5", "Người dùng", "Giao diện Flutter", "Phát ra giọng nói (Ví dụ: 'Xin chào...')", "Sóng âm vật lý", "Microphone thu nhận tín hiệu âm thanh analog."),
        ("6", "Giao diện Flutter", "SessionActor", "send_binary(pcm_chunk_20ms)", "None", "Gửi các khối nhị phân PCM 16kHz mono 20ms liên tục."),
        ("7", "SessionActor", "Bộ lọc VAD", "process_chunk(chunk)", "VAD Decision", "Bộ lọc WebRTC VAD phân tích mức năng lượng âm thanh."),
        ("8", "Bộ lọc VAD", "SessionActor", "VadEvent(SPEECH_START)", "Event Signal", "Xác nhận phát hiện người dùng bắt đầu nói."),
        ("9", "SessionActor", "Giao diện Flutter", "send_json({'event': 'SPEECH_START'})", "JSON Payload", "Ứng dụng bật hoạt ảnh sóng âm nhấp nháy báo hiệu."),
        ("10", "Người dùng", "Giao diện Flutter", "Dứt lời nói và giữ yên lặng", "Khoảng lặng âm", "Người dùng kết thúc câu phát ngôn."),
        ("11", "Giao diện Flutter", "SessionActor", "send_binary(silent_pcm_chunks)", "None", "Ứng dụng tiếp tục truyền các khung âm thanh nền."),
        ("12", "SessionActor", "Bộ lọc VAD", "process_chunk(silent_chunk)", "VAD Decision", "Phát hiện năng lượng âm thanh rơi xuống dưới ngưỡng."),
        ("13", "Bộ lọc VAD", "SessionActor", "VadEvent(SILENCE_CUTOFF)", "Event Signal", "Xác định khoảng lặng liên tiếp 500ms -> Chốt kết thúc câu."),
        ("14", "SessionActor", "Tiến trình STT", "transcribe(audio_buffer)", "Async Call", "Gửi toàn bộ đệm âm thanh của câu nói sang mô hình Whisper."),
        ("15", "Tiến trình STT", "SessionActor", "source_text, stt_latency_ms", "Text + Metric", "Mô hình nhận dạng giọng nói trả về chuỗi văn bản tiếng Việt."),
        ("16", "SessionActor", "Giao diện Flutter", "send_json({'event': 'STT_RESULT'})", "JSON Payload", "Hiển thị văn bản nhận diện tức thời trên màn hình máy khách."),
        ("17", "SessionActor", "Tiến trình NMT", "translate(source_text, 'vi', 'en')", "Async Call", "Gửi chuỗi văn bản sang mô hình NLLB-200 kèm bộ điều phối LoRA."),
        ("18", "Tiến trình NMT", "SessionActor", "target_text, nmt_latency_ms", "Text + Metric", "Mô hình dịch máy trả về bản dịch tiếng Anh chuẩn xác."),
        ("19", "SessionActor", "Giao diện Flutter", "send_json({'event': 'TRANS_RESULT'})", "JSON Payload", "Hiển thị bản dịch nổi bật trên màn hình kết quả."),
        ("20", "SessionActor", "Tiến trình TTS", "synthesize(target_text, 'en')", "Async Call", "Kích hoạt mô hình MMS VITS tổng hợp giọng đọc tiếng Anh bản xứ."),
        ("21", "Tiến trình TTS", "SessionActor", "wav_bytes, tts_latency_ms", "Audio Bytes", "Trả về luồng byte âm thanh WAV 16kHz đã tổng hợp."),
        ("22", "SessionActor", "Giao diện Flutter", "send_binary(wav_bytes)", "Binary Stream", "Truyền trực tiếp luồng byte âm thanh về thiết bị di động."),
        ("23", "Giao diện Flutter", "Người dùng", "play_audio(wav_bytes)", "Âm thanh loa ngoài", "Phát câu dịch ra loa cho người dùng và đối tác cùng nghe."),
        ("24", "SessionActor", "CSDL Telemetry", "save_metrics(TurnData)", "INSERT Query", "Ghi vết chi tiết lượt dịch vào translation_logs & pipeline_metrics.")
    ]
    render_sequence_table(doc, uc1_1_steps)

    # UC1.2
    add_paragraph(doc, "3.3.1.2. Sơ đồ tuần tự UC1.2 - Hội thoại song phương hai chiều với khóa Mutex:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Điều phối cuộc đối thoại trực tiếp giữa hai người bản địa và ngoại quốc thông qua thanh DualMicBar. "
        "Áp dụng cơ chế khóa tranh chấp (Mutex Lock) để ngăn xung đột khi cả hai người cùng chạm nút micrô đồng thời."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC1.2 - Hội thoại song phương với khóa hàng rào Mutex",
        """
Người_dùng_A(VN)  Người_dùng_B(EN)   DualMicBar_Flutter     SessionActor       Khóa_Mutex        Chuỗi_AI_Pipeline     Loa_phát_âm
      |                  |                   |                   |                  |                   |                 |
      |--[1] Nhấn Mic A->|                   |                   |                  |                   |                 |
      |                  |                   |--[2] req_lock('A')->                  |                   |                 |
      |                  |                   |                   |--[3] acquire()-->|                   |                 |
      |                  |                   |                   |<--[4] Lock_OK----|                   |                 |
      |                  |                   |<--[5] Mic A Active (Mic B Disabled)--|                   |                 |
      |                  |--[6] Nhấn Mic B-->|                   |                  |                   |                 |
      |                  |   (Cố gắng nói)   |--[7] Bị từ chối: Nút B màu xám, rung xúc giác báo bận----|                 |
      |--[8] Nói tiếng Việt----------------->|                   |                  |                   |                 |
      |                  |                   |===[9] Stream Audio A nhị phân=======>|                   |                 |
      |--[10] Dứt lời--->|                   |                   |--[11] VAD End--->|                   |                 |
      |                  |                   |                   |--[12] execute_pipeline(Audio A, 'vi', 'en')---------->|
      |                  |                   |                   |                  |                   |<--[13] WAV_EN---|
      |                  |                   |                   |--[14] release()->|                   |                 |
      |                  |                   |                   |<--[15] Unlocked--|                   |                 |
      |                  |                   |<--[16] Khôi phục trạng thái sẵn sàng cả 2 Mic------------|                 |
      |                  |                   |================================[17] Phát câu dịch tiếng Anh===============>|
      |                  |<==================[18] Nghe loa tiếng Anh dịch=================================================|
      |                  |                   |                   |                  |                   |                 |
      |                  |--[19] Nhấn Mic B->|                   |                  |                   |                 |
      |                  |                   |--[20] req_lock('B')->                |                   |                 |
      |                  |                   |                   |--[21] acquire()->|                   |                 |
      |                  |                   |                   |<--[22] Lock_OK---|                   |                 |
      |                  |                   |<--[23] Mic B Active (Mic A Disabled)-|                   |                 |
      |                  |--[24] Nói tiếng Anh==================>|                  |                   |                 |
      |                  |--[25] Dứt lời---->|                   |--[26] execute_pipeline(Audio B, 'en', 'vi')---------->|
      |                  |                   |                   |<--[27] Unlocked--|--[28] release()---|                 |
      |<=====================================[29] Nghe loa phát câu dịch tiếng Việt=======================================|
"""
    )
    add_caption(doc, "Hình 3.4: Biểu đồ tuần tự ca sử dụng UC1.2 - Hội thoại song phương với khóa hàng rào Mutex", is_table=False)

    uc1_2_steps = [
        ("1", "Người dùng A", "DualMicBar", "Nhấn nút Mic A (Tiếng Việt)", "None", "Người dùng A kích hoạt lượt nói tiếng Việt."),
        ("2", "DualMicBar", "SessionActor", "request_mic_turn(side='LEFT')", "Async Request", "Yêu cầu chiếm quyền micrô bên trái."),
        ("3", "SessionActor", "Khóa Mutex", "acquire()", "Boolean", "Khóa hàng rào loại trừ tương hỗ (Mutual Exclusion)."),
        ("4", "Khóa Mutex", "SessionActor", "True (Lock Granted)", "Success", "Xác nhận khóa thành công; ngăn mọi yêu cầu khác."),
        ("5", "SessionActor", "DualMicBar", "emit_state('A_ACTIVE')", "UI State", "Giao diện hiển thị nút A màu xanh; vô hiệu hóa nút B (màu xám)."),
        ("6", "Người dùng B", "DualMicBar", "Nhấn nút Mic B trong lúc A đang nói", "Bị chặn", "Người dùng B cố can thiệp vào cuộc đối thoại."),
        ("7", "DualMicBar", "Người dùng B", "Haptic Alert + Reject Tone", "Phản hồi", "Ứng dụng rung nhẹ và phát âm báo bận, không tiếp nhận audio B."),
        ("8", "Người dùng A", "SessionActor", "Phát âm câu nói tiếng Việt", "Binary Stream", "Luồng âm thanh A được gửi lên bộ xử lý."),
        ("9", "SessionActor", "Chuỗi AI Pipeline", "execute_pipeline(Audio A, 'vi', 'en')", "Async Task", "Thực hiện nhận dạng STT, dịch NMT và tổng hợp TTS tiếng Anh."),
        ("10", "Chuỗi AI Pipeline", "SessionActor", "target_wav_bytes", "Audio Bytes", "Trả về tệp âm thanh tiếng Anh đã tổng hợp hoàn tất."),
        ("11", "SessionActor", "Khóa Mutex", "release()", "None", "Giải phóng khóa Mutex; kết thúc phiên độc quyền của A."),
        ("12", "SessionActor", "DualMicBar", "emit_state('IDLE_READY')", "UI State", "Khôi phục trạng thái sẵn sàng cho cả 2 nút Mic A và B."),
        ("13", "DualMicBar", "Loa phát âm", "play_audio(target_wav_bytes)", "Âm thanh", "Phát câu dịch tiếng Anh cho Người dùng B nghe."),
        ("14", "Người dùng B", "DualMicBar", "Nhấn nút Mic B (Tiếng Anh) phản hồi", "None", "B chiếm quyền micrô tiếp theo; quy trình lặp lại đảo chiều.")
    ]
    render_sequence_table(doc, uc1_2_steps)

    # UC1.3
    add_paragraph(doc, "3.3.1.3. Sơ đồ tuần tự UC1.3 - Dịch văn bản thuần túy và tra cứu nhanh qua REST API:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng nhập trực tiếp văn bản qua bàn phím hoặc dán văn bản từ clipboard. "
        "Hệ thống gửi yêu cầu HTTP POST RESTful, kiểm tra bộ nhớ dịch (Translation Memory) để trả về ngay nếu khớp chuẩn, "
        "ngược lại gọi mô hình NLLB-200 và lưu trữ nhật ký."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC1.3 - Dịch văn bản thuần túy qua REST API",
        """
Người_dùng     Giao_diện_Flutter    Bộ_định_tuyến_REST   Dịch_vụ_Dịch_thuật   Bộ_nhớ_dịch_TM    Mô_hình_NLLB_200    CSDL_Logs
    |                  |                     |                    |                 |                  |                 |
    |--[1] Nhập text-->|                     |                    |                 |                  |                 |
    |--[2] Bấm 'Dịch'->|                     |                    |                 |                  |                 |
    |                  |--[3] POST /api/v1/translate/text-------->|                 |                  |                 |
    |                  |      {text, src_lang, tgt_lang}          |--[4] lookup()-->|                  |                 |
    |                  |                     |                    |<--[5] Match?----|                  |                 |
    |                  |                     |                    |                 |                  |                 |
    |                  |                     |     [alt: Khớp cụm từ trong Bộ nhớ dịch (TM)]           |                 |
    |                  |                     |                    |--Trả về translated_text từ TM----->|                 |
    |                  |                     |                    |                 |                  |                 |
    |                  |                     |     [alt: Không khớp TM -> Gọi suy luận mô hình AI]     |                 |
    |                  |                     |                    |--[6] predict(text, src, tgt)------>|                 |
    |                  |                     |                    |<--[7] Trả về: translated_text------|                 |
    |                  |                     |                    |                 |                  |                 |
    |                  |                     |                    |--[8] async_log_entry(text, trans, latency)---------->|
    |                  |                     |<--[9] 200 OK: {translated_text, latency, source: 'nllb'}---|                 |
    |                  |<--[10] Render kết quả bản dịch           |                 |                  |                 |
"""
    )
    add_caption(doc, "Hình 3.5: Biểu đồ tuần tự ca sử dụng UC1.3 - Dịch văn bản thuần túy qua REST API", is_table=False)

    uc1_3_steps = [
        ("1", "Người dùng", "Giao diện Flutter", "Nhập văn bản vào TextField", "None", "Nhập đoạn văn bản cần dịch."),
        ("2", "Người dùng", "Giao diện Flutter", "Bấm nút 'Dịch ngay'", "None", "Gửi lệnh dịch văn bản."),
        ("3", "Giao diện Flutter", "Bộ định tuyến REST", "POST /api/v1/translate/text", "HTTP Request", "Gửi gói tin JSON {text, source_lang, target_lang}."),
        ("4", "Bộ định tuyến REST", "Dịch vụ Dịch thuật", "translate_text(payload)", "Internal Call", "Điều phối quy trình dịch văn bản."),
        ("5", "Dịch vụ Dịch thuật", "Bộ nhớ dịch TM", "lookup_exact(text, src, tgt)", "Query", "Kiểm tra xem câu văn đã có bản dịch chuẩn trong Glossary chưa."),
        ("6", "Dịch vụ Dịch thuật", "Mô hình NLLB-200", "generate(tokens)", "Inference Call", "Nếu chưa có trong TM, kích hoạt suy luận NLLB-200 sinh chuỗi đích."),
        ("7", "Mô hình NLLB-200", "Dịch vụ Dịch thuật", "translated_text", "Result String", "Trả về văn bản đã dịch."),
        ("8", "Dịch vụ Dịch thuật", "CSDL Logs", "INSERT INTO translation_logs", "Async DB Write", "Ghi nhật ký phục vụ tra cứu lịch sử."),
        ("9", "Bộ định tuyến REST", "Giao diện Flutter", "200 OK: {translated_text, latency}", "JSON Response", "Trả kết quả về ứng dụng di động."),
        ("10", "Giao diện Flutter", "Người dùng", "Hiển thị bản dịch lên TextCard", "UI Render", "Người dùng đọc bản dịch và có thể sao chép.")
    ]
    render_sequence_table(doc, uc1_3_steps)

    # =========================================================================
    # NHÓM 2: LỊCH SỬ VÀ CẤU HÌNH ỨNG DỤNG (UC2.1 - UC2.3)
    # =========================================================================
    add_heading_3(doc, "3.3.2. Nhóm UC2 - Lịch sử và cấu hình ứng dụng")

    # UC2.1
    add_paragraph(doc, "3.3.2.1. Sơ đồ tuần tự UC2.1 - Xem và tìm kiếm lịch sử các phiên dịch:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Người dùng mở màn hình Lịch sử để duyệt lại các câu dịch trước đây. "
        "Ứng dụng hỗ trợ phân trang (Pagination), tìm kiếm từ khóa và phát lại tệp âm thanh câu dịch."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC2.1 - Xem và tìm kiếm lịch sử phiên dịch",
        """
Người_dùng     Giao_diện_Lịch_sử    Bộ_định_tuyến_History   Dịch_vụ_Lịch_sử      CSDL_Logs       Kho_lưu_trữ_Audio
    |                  |                      |                   |                  |                   |
    |--[1] Mở Tab Lịch sử                     |                   |                  |                   |
    |                  |--[2] GET /api/v1/history?page=1&limit=20>|                  |                   |
    |                  |                      |--[3] get_logs()-->|                  |                   |
    |                  |                      |                   |--[4] SELECT * FROM logs WHERE client_id=?
    |                  |                      |                   |<--[5] Trả về danh sách records---|
    |                  |<--[6] 200 OK: {items: [...], total: 145}-|                  |                   |
    |--[7] Nhập từ khóa 'bảo tàng'            |                   |                  |                   |
    |                  |--[8] GET /api/v1/history?keyword='bảo tàng'---------------->|                   |
    |                  |<--[9] 200 OK: {items: [2 bản ghi lọc]}---|                  |                   |
    |--[10] Bấm Nghe lại audio câu #12------->|                   |                  |                   |
    |                  |--[11] GET /api/v1/audio/{file_name}----->|                  |                   |
    |                  |                      |                   |--[12] read()---->|--[13] get_bytes-->|
    |                  |<--[14] Audio stream (audio/wav)----------|                  |<--[15] bytes------|
    |<--[16] Phát loa--|                      |                   |                  |                   |
"""
    )
    add_caption(doc, "Hình 3.6: Biểu đồ tuần tự ca sử dụng UC2.1 - Xem và tìm kiếm lịch sử phiên dịch", is_table=False)

    uc2_1_steps = [
        ("1", "Người dùng", "Giao diện Lịch sử", "Chạm vào Tab 'Lịch sử'", "None", "Mở màn hình duyệt lịch sử dịch."),
        ("2", "Giao diện Lịch sử", "Bộ định tuyến History", "GET /api/v1/history?page=1", "HTTP Request", "Gửi yêu cầu lấy 20 mục lịch sử mới nhất."),
        ("3", "Bộ định tuyến History", "Dịch vụ Lịch sử", "get_user_history(client_id, page)", "Query Call", "Truy vấn dữ liệu theo định danh thiết bị."),
        ("4", "Dịch vụ Lịch sử", "CSDL Logs", "SELECT * FROM translation_logs ...", "SQL Query", "Đọc các bản ghi sắp xếp giảm dần theo created_at."),
        ("5", "CSDL Logs", "Dịch vụ Lịch sử", "Danh sách bản ghi (List[TranslationLog])", "Result Set", "Trả về tập kết quả."),
        ("6", "Bộ định tuyến History", "Giao diện Lịch sử", "200 OK: {items: [...], total}", "JSON Array", "Hiển thị danh sách câu dịch dạng thẻ Card."),
        ("7", "Người dùng", "Giao diện Lịch sử", "Nhập từ khóa tìm kiếm", "Filter Input", "Lọc các câu dịch chứa từ khóa chỉ định."),
        ("8", "Người dùng", "Giao diện Lịch sử", "Bấm biểu tượng loa nghe lại", "Event Click", "Yêu cầu nghe lại phát âm thanh của câu dịch."),
        ("9", "Giao diện Lịch sử", "Kho lưu trữ Audio", "GET /api/v1/audio/{file_name}", "WAV Bytes", "Tải luồng âm thanh tệp WAV từ máy chủ."),
        ("10", "Giao diện Lịch sử", "Người dùng", "play_audio()", "Âm thanh", "Phát lại câu dịch ra loa điện thoại.")
    ]
    render_sequence_table(doc, uc2_1_steps)

    # UC2.2
    add_paragraph(doc, "3.3.2.2. Sơ đồ tuần tự UC2.2 - Gắn cờ báo lỗi câu dịch và đánh dấu yêu thích:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng đánh dấu cờ (Flag Issue) khi phát hiện bản dịch sai lệch ngữ nghĩa. "
        "Thao tác này tự động chuyển câu dịch vào Hàng đợi kiểm duyệt QA của chuyên gia ngôn ngữ trên Web Admin."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC2.2 - Gắn cờ báo lỗi và đánh dấu yêu thích câu dịch",
        """
Người_dùng     Giao_diện_Flutter    Bộ_định_tuyến_Flag    Dịch_vụ_Feedback      CSDL_Logs        Hàng_đợi_QA
    |                  |                     |                    |                 |                 |
    |--[1] Bấm icon cờ>|                     |                    |                 |                 |
    |--[2] Chọn lý do->|                     |                    |                 |                 |
    |  ('Sai ngữ nghĩa')                     |                    |                 |                 |
    |                  |--[3] POST /api/v1/translations/{id}/flag>|                 |                 |
    |                  |      {reason: 'Accuracy', note: '...'}   |                 |                 |
    |                  |                     |--[4] flag_item()-->|                 |                 |
    |                  |                     |                    |--[5] UPDATE translation_logs ---->|
    |                  |                     |                    |      SET is_flagged=True          |
    |                  |                     |                    |--[6] INSERT INTO quality_reviews->|
    |                  |                     |                    |      (status='PENDING')           |
    |                  |                     |                    |<--[7] DB Success------------------|
    |                  |                     |<--[8] 200 OK: {status: 'flagged'}----|                 |
    |                  |<--[9] Toast: 'Đã gửi phản hồi kiểm duyệt'|                 |                 |
"""
    )
    add_caption(doc, "Hình 3.7: Biểu đồ tuần tự ca sử dụng UC2.2 - Gắn cờ báo lỗi câu dịch", is_table=False)

    uc2_2_steps = [
        ("1", "Người dùng", "Giao diện Flutter", "Bấm biểu tượng lá cờ (Flag Icon)", "None", "Mở hộp thoại gửi phản hồi chất lượng câu dịch."),
        ("2", "Người dùng", "Giao diện Flutter", "Chọn loại lỗi và nhập ghi chú mô tả", "Form Input", "Cung cấp ngữ cảnh lỗi cho chuyên gia thẩm định."),
        ("3", "Giao diện Flutter", "Bộ định tuyến Flag", "POST /api/v1/translations/{id}/flag", "HTTP Request", "Gửi yêu cầu đánh dấu lỗi câu dịch."),
        ("4", "Bộ định tuyến Flag", "Dịch vụ Feedback", "process_flag_report(id, reason)", "Service Call", "Xử lý nghiệp vụ phân loại và gắn cờ."),
        ("5", "Dịch vụ Feedback", "CSDL Logs", "UPDATE logs SET is_flagged = True", "SQL Update", "Đánh dấu bản ghi có vấn đề chất lượng."),
        ("6", "Dịch vụ Feedback", "Hàng đợi QA", "INSERT INTO quality_reviews (status='PENDING')", "SQL Insert", "Tạo phiếu thẩm định chất lượng mới cho Reviewer."),
        ("7", "Bộ định tuyến Flag", "Giao diện Flutter", "200 OK: {status: 'success'}", "JSON Response", "Báo thành công."),
        ("8", "Giao diện Flutter", "Người dùng", "Hiển thị thông báo Toast thành công", "UI Alert", "Người dùng nhận phản hồi và biểu tượng cờ đổi sang màu cam.")
    ]
    render_sequence_table(doc, uc2_2_steps)

    # UC2.3
    add_paragraph(doc, "3.3.2.3. Sơ đồ tuần tự UC2.3 - Tùy chỉnh cấu hình ứng dụng di động:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Người dùng điều chỉnh tốc độ đọc TTS (0.75x, 1.0x, 1.25x), độ nhạy phát hiện tiếng nói VAD "
        "và bật/tắt chế độ tự động phát âm thanh sau khi dịch. Cấu hình được lưu trữ bền vững tại bộ nhớ thiết bị."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC2.3 - Tùy chỉnh cấu hình ứng dụng di động",
        """
Người_dùng     Giao_diện_Cài_đặt    Controller_Settings   SharedPreferences   Bộ_xử_lý_VAD_Local    Audio_Player
    |                  |                      |                   |                  |                 |
    |--[1] Mở Cài đặt->|                      |                   |                  |                 |
    |--[2] Đổi tốc độ đọc (1.25x)------------>|                   |                  |                 |
    |--[3] Chọn độ nhạy VAD (Mức 3 - Cao)---->|                   |                  |                 |
    |--[4] Bật Auto-Play Speech-------------->|                   |                  |                 |
    |                  |--[5] save_config()-->|                   |                  |                 |
    |                  |                      |--[6] setDouble('tts_speed', 1.25)--->|                 |
    |                  |                      |--[7] setInt('vad_mode', 3)---------->|                 |
    |                  |                      |--[8] setBool('auto_play', True)----->|                 |
    |                  |                      |<--[9] Lưu thành công-----------------|                 |
    |                  |                      |--[10] apply_vad_mode(3)------------->|                 |
    |                  |                      |--[11] set_playback_rate(1.25)------------------------->|
    |                  |<--[12] Báo 'Cài đặt đã lưu thành công'---|                  |                 |
"""
    )
    add_caption(doc, "Hình 3.8: Biểu đồ tuần tự ca sử dụng UC2.3 - Tùy chỉnh cấu hình ứng dụng di động", is_table=False)

    uc2_3_steps = [
        ("1", "Người dùng", "Giao diện Cài đặt", "Truy cập Tab 'Cài đặt'", "None", "Mở màn hình thiết lập tham số."),
        ("2", "Người dùng", "Giao diện Cài đặt", "Kéo thanh trượt tốc độ đọc TTS lên 1.25x", "Slider Change", "Thay đổi tốc độ phát âm thanh câu dịch."),
        ("3", "Người dùng", "Giao diện Cài đặt", "Chọn độ nhạy VAD mức 3 (Lọc ồn mạnh)", "Dropdown Select", "Thiết lập lọc nhiễu môi trường cao."),
        ("4", "Giao diện Cài đặt", "Controller Settings", "update_settings(payload)", "Event", "Chuyển dữ liệu cấu hình xuống tầng logic."),
        ("5", "Controller Settings", "SharedPreferences", "save_to_local_storage(key, value)", "Disk Write", "Ghi dữ liệu cấu hình vào bộ nhớ Flash của điện thoại."),
        ("6", "Controller Settings", "Bộ xử lý VAD Local", "set_aggressiveness(3)", "Configure", "Áp dụng ngay ngưỡng lọc ồn cho các phiên thu âm tiếp theo."),
        ("7", "Controller Settings", "Audio Player", "set_speed(1.25)", "Configure", "Cấu hình tốc độ cho trình phát âm thanh."),
        ("8", "Giao diện Cài đặt", "Người dùng", "Hiển thị thông báo đã cập nhật cấu hình", "UI Render", "Hoàn tất lưu cấu hình cá nhân hóa.")
    ]
    render_sequence_table(doc, uc2_3_steps)

    # =========================================================================
    # NHÓM 3: XÁC THỰC VÀ HỒ SƠ QUẢN TRỊ (UC3.1 - UC3.2)
    # =========================================================================
    add_heading_3(doc, "3.3.3. Nhóm UC3 - Xác thực và hồ sơ quản trị")

    # UC3.1
    add_paragraph(doc, "3.3.3.1. Sơ đồ tuần tự UC3.1 - Đăng nhập Web Admin và xác thực hai yếu tố (TOTP MFA):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Quy trình đăng nhập bảo mật hai lớp bắt buộc đối với nhân viên và quản trị viên. "
        "Bước 1 kiểm tra tên người dùng và mật khẩu băm Argon2id; nếu thành công, bước 2 yêu cầu nhập mã OTP thời gian thực (RFC 6238)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC3.1 - Đăng nhập Web Admin và xác thực TOTP MFA",
        """
Quản_trị_viên    Giao_diện_React      Router_Auth       Dịch_vụ_Auth     Bộ_băm_Argon2     Bộ_xác_thực_TOTP    CSDL_Users_Audit
      |                 |                  |                 |                |                 |                 |
      |--[1] Nhập User, Mật khẩu---------->|                 |                |                 |                 |
      |                 |--[2] POST /api/v1/auth/login------>|                |                 |                 |
      |                 |                  |--[3] auth()---->|                |                 |                 |
      |                 |                  |                 |--[4] find_user_by_username()---------------------->|
      |                 |                  |                 |<--[5] Trả về User record (password_hash, mfa)------|
      |                 |                  |                 |--[6] verify(password, password_hash)------------>|
      |                 |                  |                 |<--[7] True (Mật khẩu hợp lệ)--------------------|
      |                 |                  |<--[8] MFA_CHALLENGE (temp_jwt_token)               |                 |
      |                 |<--[9] Hiển thị màn hình nhập 6 số OTP               |                 |                 |
      |--[10] Nhập mã 6 số TOTP----------->|                 |                |                 |                 |
      |                 |--[11] POST /api/v1/auth/mfa/verify |                |                 |                 |
      |                 |   {temp_token, totp_code}--------->|                |                 |                 |
      |                 |                  |                 |--[12] verify_totp(totp_code, mfa_secret)---------->|
      |                 |                  |                 |<--[13] True (Mã hợp lệ theo time-window 30s)-------|
      |                 |                  |                 |--[14] INSERT auth_sessions (Access + Refresh)----->|
      |                 |                  |                 |--[15] INSERT audit_logs (USER_LOGIN_SUCCESS)------>|
      |                 |                  |<--[16] 200 OK: {access_token, role, user_info}-----|                 |
      |                 |<--[17] Lưu Auth State, chuyển hướng vào Dashboard---------------------|                 |
"""
    )
    add_caption(doc, "Hình 3.9: Biểu đồ tuần tự ca sử dụng UC3.1 - Đăng nhập Web Admin và xác thực TOTP MFA", is_table=False)

    uc3_1_steps = [
        ("1", "Quản trị viên", "Giao diện React", "Nhập tên người dùng và mật khẩu", "None", "Gửi thông tin xác thực cấp 1."),
        ("2", "Giao diện React", "Router Auth", "POST /api/v1/auth/login", "HTTP Request", "Gửi payload đăng nhập."),
        ("3", "Router Auth", "Dịch vụ Auth", "authenticate_user(username, pwd)", "Service Call", "Kiểm tra danh tính tài khoản."),
        ("4", "Dịch vụ Auth", "CSDL Users", "SELECT * FROM users WHERE username=?", "SQL Query", "Truy vấn dữ liệu tài khoản và khóa bí mật MFA."),
        ("5", "Dịch vụ Auth", "Bộ băm Argon2", "verify(pwd, password_hash)", "Crypto Call", "So sánh mật khẩu an toàn theo thời gian không đổi."),
        ("6", "Router Auth", "Giao diện React", "200 OK: {mfa_required: true, temp_token}", "JSON", "Mật khẩu đúng, yêu cầu xác thực cấp 2."),
        ("7", "Giao diện React", "Quản trị viên", "Chuyển sang giao diện 6 ô nhập mã OTP", "UI Form", "Nhắc người dùng mở ứng dụng Authenticator."),
        ("8", "Quản trị viên", "Giao diện React", "Nhập mã số TOTP 6 chữ số", "OTP Input", "Nhập mã xác thực biến đổi theo thời gian."),
        ("9", "Giao diện React", "Router Auth", "POST /api/v1/auth/mfa/verify", "HTTP Request", "Gửi mã OTP kèm token tạm thời."),
        ("10", "Dịch vụ Auth", "Bộ xác thực TOTP", "verify_code(code, secret)", "RFC 6238 Call", "Xác thực mã số theo cửa sổ thời gian 30 giây."),
        ("11", "Dịch vụ Auth", "CSDL Audit", "INSERT INTO auth_sessions & audit_logs", "SQL Insert", "Tạo phiên làm việc mới và ghi vết kiểm toán an ninh."),
        ("12", "Router Auth", "Giao diện React", "200 OK: {access_token, role}", "JWT Tokens", "Cấp quyền truy cập hệ thống quản trị.")
    ]
    render_sequence_table(doc, uc3_1_steps)

    # UC3.2
    add_paragraph(doc, "3.3.3.2. Sơ đồ tuần tự UC3.2 - Đổi mật khẩu tài khoản quản trị và thu hồi phiên làm việc cũ:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép người dùng cập nhật mật khẩu mới định kỳ. Để đảm bảo an toàn tuyệt đối, hệ thống tự động "
        "tăng chỉ số token_version và thu hồi (Revoke) toàn bộ các phiên làm việc đang mở trên các trình duyệt khác."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC3.2 - Đổi mật khẩu tài khoản quản trị và thu hồi phiên",
        """
Quản_trị_viên    Giao_diện_Hồ_sơ      Router_User       Dịch_vụ_User      Bộ_băm_Argon2        CSDL_Users_Sessions
      |                 |                  |                 |                 |                      |
      |--[1] Nhập pass cũ, pass mới------->|                 |                 |                      |
      |                 |--[2] POST /api/v1/auth/change-pwd->|                 |                      |
      |                 |                  |--[3] change()-->|                 |                      |
      |                 |                  |                 |--[4] verify(old_pwd, hash)------------>|
      |                 |                  |                 |<--[5] True (Mật khẩu cũ khớp)----------|
      |                 |                  |                 |--[6] generate_hash(new_pwd)----------->|
      |                 |                  |                 |<--[7] new_password_hash----------------|
      |                 |                  |                 |--[8] UPDATE users SET password_hash,   |
      |                 |                  |                 |      token_version = token_version + 1>|
      |                 |                  |                 |--[9] UPDATE auth_sessions              |
      |                 |                  |                 |      SET revoked_at=now() ------------>|
      |                 |                  |                 |--[10] INSERT audit_logs (PWD_CHANGED)->|
      |                 |                  |<--[11] 200 OK---|                 |                      |
      |                 |<--[12] Thông báo thành công, yêu cầu đăng nhập lại---|                      |
"""
    )
    add_caption(doc, "Hình 3.10: Biểu đồ tuần tự ca sử dụng UC3.2 - Đổi mật khẩu và thu hồi phiên làm việc cũ", is_table=False)

    uc3_2_steps = [
        ("1", "Quản trị viên", "Giao diện Hồ sơ", "Nhập mật khẩu cũ, mật khẩu mới (xác nhận lại)", "Form Input", "Cung cấp mật khẩu hiện tại và mật khẩu mới."),
        ("2", "Giao diện Hồ sơ", "Router User", "POST /api/v1/auth/change-password", "HTTP Request", "Gửi yêu cầu đổi mật khẩu kèm JWT token."),
        ("3", "Router User", "Dịch vụ User", "change_password(user_id, old_p, new_p)", "Service Call", "Xử lý kiểm tra và đổi mật khẩu."),
        ("4", "Dịch vụ User", "Bộ băm Argon2", "verify(old_p, current_hash)", "Crypto Verify", "Xác thực mật khẩu cũ có đúng không."),
        ("5", "Dịch vụ User", "Bộ băm Argon2", "hash(new_p)", "Crypto Hash", "Băm mật khẩu mới kèm muối độc lập."),
        ("6", "Dịch vụ User", "CSDL Users", "UPDATE users SET token_version = token_version + 1", "SQL Update", "Tăng phiên bản token để vô hiệu hóa toàn bộ JWT cũ."),
        ("7", "Dịch vụ User", "CSDL Sessions", "UPDATE auth_sessions SET revoked_at=now()", "SQL Update", "Thu hồi tất cả các phiên làm việc trên các thiết bị."),
        ("8", "Router User", "Giao diện Hồ sơ", "200 OK: {message: 'Password changed'}", "JSON Response", "Báo cập nhật thành công, điều hướng về trang đăng nhập.")
    ]
    render_sequence_table(doc, uc3_2_steps)

    # =========================================================================
    # NHÓM 4: TỪ ĐIỂN VÀ ĐÁNH GIÁ CHẤT LƯỢNG (UC4.1 - UC4.4)
    # =========================================================================
    add_heading_3(doc, "3.3.4. Nhóm UC4 - Từ điển và đánh giá chất lượng")

    # UC4.1
    add_paragraph(doc, "3.3.4.1. Sơ đồ tuần tự UC4.1 - Quản lý và tra cứu bộ nhớ dịch thuật chuyên ngành:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép nhân viên và chuyên gia ngôn ngữ xem danh mục thuật ngữ chuẩn hóa, lọc theo cặp ngôn ngữ "
        "và tìm kiếm các cặp câu mẫu trong cơ sở dữ liệu Bộ nhớ dịch thuật (Translation Memory)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC4.1 - Quản lý và tra cứu bộ nhớ dịch thuật chuyên ngành",
        """
Chuyên_gia_QA    Giao_diện_Từ_điển    Router_Dictionary    Dịch_vụ_TM         CSDL_TM_Entries
      |                  |                    |                |                    |
      |--[1] Mở mục Từ điển                   |                |                    |
      |                  |--[2] GET /api/v1/dictionary?page=1->|                    |
      |                  |                    |--[3] list()--->|                    |
      |                  |                    |                |--[4] SELECT * FROM tm_entries LIMIT 20-->|
      |                  |                    |                |<--[5] Trả về danh sách mục từ------------|
      |                  |<--[6] 200 OK: {items: [...], total}-|                    |
      |--[7] Lọc theo chuyên ngành 'Y tế'---->|                |                    |
      |                  |--[8] GET /api/v1/dictionary?domain='medical'------------>|
      |                  |<--[9] 200 OK: {items: [Danh sách thuật ngữ Y tế]}--------|
"""
    )
    add_caption(doc, "Hình 3.11: Biểu đồ tuần tự ca sử dụng UC4.1 - Quản lý và tra cứu bộ nhớ dịch thuật", is_table=False)

    uc4_1_steps = [
        ("1", "Chuyên gia QA", "Giao diện Từ điển", "Truy cập mục 'Bộ nhớ dịch & Thuật ngữ'", "None", "Mở màn hình quản trị từ điển."),
        ("2", "Giao diện Từ điển", "Router Dictionary", "GET /api/v1/dictionary?page=1", "HTTP Request", "Yêu cầu tải danh sách thuật ngữ."),
        ("3", "Router Dictionary", "Dịch vụ TM", "get_glossary_entries(filter_params)", "Service Call", "Truy vấn danh mục từ vựng."),
        ("4", "Dịch vụ TM", "CSDL TM Entries", "SELECT * FROM translation_memory_entries", "SQL Query", "Lấy dữ liệu mục từ kèm số lần khớp match_count."),
        ("5", "Router Dictionary", "Giao diện Từ điển", "200 OK: {items: [...], total}", "JSON Array", "Hiển thị bảng dữ liệu thuật ngữ trên Web Admin.")
    ]
    render_sequence_table(doc, uc4_1_steps)

    # UC4.2
    add_paragraph(doc, "3.3.4.2. Sơ đồ tuần tự UC4.2 - Thêm mới và chuẩn hóa thuật ngữ chuyên ngành vào bộ nhớ dịch:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Thêm mới một cặp từ vựng chuyên ngành vào bộ nhớ dịch. Hệ thống tự động kích hoạt bộ chuẩn hóa văn bản "
        "(TextNormalizer) để loại bỏ ký tự đặc biệt, chuẩn hóa chữ thường và tính chỉ mục tìm kiếm nhanh (Fast Index Lookup)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC4.2 - Thêm mới và chuẩn hóa thuật ngữ vào bộ nhớ dịch",
        """
Chuyên_gia_QA    Form_Thêm_Từ_Điển    Router_Dictionary    Bộ_chuẩn_hóa_Text    Dịch_vụ_TM         CSDL_TM_Audit
      |                  |                    |                    |                |                    |
      |--[1] Nhập: 'chụp cộng hưởng từ'       |                    |                |                    |
      |      Dịch: 'Magnetic Resonance Imaging'                    |                |                    |
      |--[2] Bấm 'Lưu thuật ngữ'------------->|                    |                |                    |
      |                  |--[3] POST /api/v1/dictionary----------->|                |                    |
      |                  |      {src_text, tgt_text, domain}       |                |                    |
      |                  |                    |--[4] add_entry()------------------->|                    |
      |                  |                    |                    |--[5] normalize(src_text)            |
      |                  |                    |                    |<--[6] 'chup cong huong tu'          |
      |                  |                    |                    |                |--[7] INSERT INTO tm_entries
      |                  |                    |                    |                |      (source_normalized)-->|
      |                  |                    |                    |                |--[8] INSERT audit_logs---->|
      |                  |                    |<--[9] 200 OK: {id: 45, status: 'created'}----------------|
      |                  |<--[10] Modal đóng, hiển thị thông báo thành công--------|
"""
    )
    add_caption(doc, "Hình 3.12: Biểu đồ tuần tự ca sử dụng UC4.2 - Thêm mới và chuẩn hóa thuật ngữ", is_table=False)

    uc4_2_steps = [
        ("1", "Chuyên gia QA", "Form Thêm Từ Điển", "Nhập cụm từ nguồn, nghĩa dịch đích, chuyên ngành", "Form Input", "Cung cấp cặp thuật ngữ cần chuẩn hóa."),
        ("2", "Form Thêm Từ Điển", "Router Dictionary", "POST /api/v1/dictionary", "HTTP Request", "Gửi payload tạo mục từ vựng mới."),
        ("3", "Router Dictionary", "Dịch vụ TM", "create_entry(payload)", "Service Call", "Xử lý nghiệp vụ thêm từ điển."),
        ("4", "Dịch vụ TM", "Bộ chuẩn hóa Text", "normalize(source_text)", "Internal Call", "Chuyển chữ thường, bỏ dấu khoảng trắng thừa phục vụ so khớp nhanh."),
        ("5", "Dịch vụ TM", "CSDL TM Audit", "INSERT INTO translation_memory_entries", "SQL Insert", "Lưu cặp từ chuẩn hóa vào cơ sở dữ liệu."),
        ("6", "Router Dictionary", "Form Thêm Từ Điển", "200 OK: {id, status: 'created'}", "JSON", "Thông báo tạo thành công, cập nhật lưới hiển thị.")
    ]
    render_sequence_table(doc, uc4_2_steps)

    # UC4.3
    add_paragraph(doc, "3.3.4.3. Sơ đồ tuần tự UC4.3 - Thẩm định và chấm điểm chất lượng câu dịch (Human QA Review):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Chuyên gia ngôn ngữ lắng nghe tệp âm thanh gốc, rà soát câu nhận dạng STT và câu dịch NMT, "
        "đánh giá điểm chất lượng MQM, phân loại lỗi và chỉnh sửa câu dịch chuẩn xác để phục vụ cải tiến mô hình."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC4.3 - Thẩm định và chấm điểm chất lượng câu dịch",
        """
Chuyên_gia_QA    Giao_diện_Duyệt_QA    Router_QA_Review    Dịch_vụ_Review     CSDL_Logs        CSDL_Quality_Reviews
      |                  |                    |                 |                 |                     |
      |--[1] Mở Hàng đợi QA                   |                 |                 |                     |
      |                  |--[2] GET /api/v1/qa/queue----------->|                 |                     |
      |                  |<--[3] 200 OK: {flagged_items: [...]} |                 |                     |
      |--[4] Nghe Audio, đối chiếu câu dịch---|                 |                 |                     |
      |--[5] Sửa câu dịch, chọn lỗi Accuracy  |                 |                 |                     |
      |--[6] Bấm 'Phê duyệt & Sửa'----------->|                 |                 |                     |
      |                  |--[7] POST /api/v1/qa/reviews/{id}/approve------------->|                     |
      |                  |      {corrected_text, mqm_score: 90, severity: 'Minor'}|                     |
      |                  |                    |                 |--[8] UPDATE translation_logs -------->|
      |                  |                    |                 |      SET is_reviewed=True, is_flagged=False
      |                  |                    |                 |--[9] INSERT INTO quality_reviews ---->|
      |                  |                    |                 |      (corrected_text, adequacy: 5)----|
      |                  |                    |<--[10] 200 OK: {review_id: 102, status: 'APPROVED'}----|
      |                  |<--[11] Xóa khỏi hàng đợi, tải câu tiếp theo---------|
"""
    )
    add_caption(doc, "Hình 3.13: Biểu đồ tuần tự ca sử dụng UC4.3 - Thẩm định và chấm điểm chất lượng câu dịch", is_table=False)

    uc4_3_steps = [
        ("1", "Chuyên gia QA", "Giao diện Duyệt QA", "Mở tab 'Hàng đợi thẩm định chất lượng'", "None", "Mở danh sách các câu dịch có vấn đề."),
        ("2", "Giao diện Duyệt QA", "Router QA Review", "GET /api/v1/qa/queue?status=PENDING", "HTTP Request", "Lấy danh sách các câu dịch bị gắn cờ."),
        ("3", "Chuyên gia QA", "Giao diện Duyệt QA", "Nghe audio gốc, đối chiếu và sửa câu dịch", "Form Edit", "Nhập câu dịch chuẩn xác, chọn phân loại lỗi MQM."),
        ("4", "Giao diện Duyệt QA", "Router QA Review", "POST /api/v1/qa/reviews/{id}/approve", "HTTP Request", "Gửi dữ liệu phê duyệt của chuyên gia."),
        ("5", "Router QA Review", "Dịch vụ Review", "save_review_decision(review_data)", "Service Call", "Xử lý phê duyệt chất lượng."),
        ("6", "Dịch vụ Review", "CSDL Logs", "UPDATE logs SET is_reviewed=1, is_flagged=0", "SQL Update", "Đóng cờ cảnh báo của câu dịch."),
        ("7", "Dịch vụ Review", "CSDL Quality Reviews", "INSERT INTO quality_reviews (...) VALUES (...)", "SQL Insert", "Lưu bản ghi thẩm định phục vụ làm dữ liệu huấn luyện."),
        ("8", "Giao diện Duyệt QA", "Chuyên gia QA", "Tự động nạp câu dịch tiếp theo trong hàng đợi", "UI Update", "Chuyển sang mục tiếp theo giúp tăng tốc độ kiểm duyệt.")
    ]
    render_sequence_table(doc, uc4_3_steps)

    # UC4.4
    add_paragraph(doc, "3.3.4.4. Sơ đồ tuần tự UC4.4 - Đóng băng và xuất bản tập dữ liệu huấn luyện:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Quản trị viên trích xuất toàn bộ các câu dịch đã được chuyên gia QA phê duyệt, phân chia ngẫu nhiên "
        "thành 3 tập Train (80%), Val (10%), Test (10%), tính mã băm SHA-256 bảo đảm tính toàn vẹn và đóng băng bất biến (Dataset Freeze)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC4.4 - Đóng băng và xuất bản tập dữ liệu huấn luyện",
        """
Quản_trị_viên    Giao_diện_MLOps      Router_Datasets     Dịch_vụ_Datasets    Bộ_băm_SHA256      CSDL_Datasets_Audit
      |                 |                   |                   |                  |                    |
      |--[1] Chọn phiên bản 'v1.2', chia 80/10/10               |                  |                    |
      |--[2] Bấm 'Đóng băng tập dữ liệu'--->|                   |                  |                    |
      |                 |--[3] POST /api/v1/datasets/freeze---->|                  |                    |
      |                 |      {name: 'corpus_v1.2', task: 'nmt'|                  |                    |
      |                 |                   |--[4] freeze()---->|                  |                    |
      |                 |                   |                   |--[5] Trích xuất các mẫu đã APPROVED|
      |                 |                   |                   |--[6] Phân tách train/val/test------|
      |                 |                   |                   |--[7] calc_sha256(parquet_file)---->|
      |                 |                   |                   |<--[8] băm SHA-256 (64 ký tự hex)---|
      |                 |                   |                   |--[9] INSERT INTO training_datasets |
      |                 |                   |                   |      (status='frozen', sha256)---->|
      |                 |                   |<--[10] 200 OK: {dataset_id, sample_count: 10500}------|
      |                 |<--[11] Hiển thị tập dữ liệu mới ở trạng thái KHÓA BẤT BIẾN-----------------|
"""
    )
    add_caption(doc, "Hình 3.14: Biểu đồ tuần tự ca sử dụng UC4.4 - Đóng băng và xuất bản tập dữ liệu", is_table=False)

    uc4_4_steps = [
        ("1", "Quản trị viên", "Giao diện MLOps", "Đặt tên tập dữ liệu, tỷ lệ chia 80:10:10", "Config Input", "Thiết lập thông số đóng gói dữ liệu."),
        ("2", "Giao diện MLOps", "Router Datasets", "POST /api/v1/datasets/freeze", "HTTP Request", "Gửi lệnh đóng băng tập dữ liệu."),
        ("3", "Router Datasets", "Dịch vụ Datasets", "create_frozen_snapshot(params)", "Service Call", "Kích hoạt tiến trình trích xuất và đóng gói."),
        ("4", "Dịch vụ Datasets", "Bộ băm SHA256", "hash_file(file_path)", "Crypto Hash", "Tính toán mã băm SHA-256 chống sửa đổi dữ liệu."),
        ("5", "Dịch vụ Datasets", "CSDL Datasets", "INSERT INTO training_datasets (is_frozen=1)", "SQL Insert", "Lưu bản ghi tập dữ liệu ở trạng thái đóng băng vĩnh viễn."),
        ("6", "Giao diện MLOps", "Quản trị viên", "Báo thành công, hiển thị mã băm toàn vẹn", "UI Render", "Sẵn sàng đưa vào huấn luyện mô hình.")
    ]
    render_sequence_table(doc, uc4_4_steps)

    # =========================================================================
    # NHÓM 5: GIÁM SÁT VÀ LỊCH SỬ HỆ THỐNG (UC5.1 - UC5.2)
    # =========================================================================
    add_heading_3(doc, "3.3.5. Nhóm UC5 - Giám sát và lịch sử hệ thống")

    # UC5.1
    add_paragraph(doc, "3.3.5.1. Sơ đồ tuần tự UC5.1 - Giám sát hiệu năng và đo kiểm độ trễ chặng theo thời gian thực:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cung cấp bảng điều khiển giám sát vi mô các chặng xử lý (VAD, STT, NMT, TTS) qua kênh WebSocket. "
        "Tự động tính toán các phân vị độ trễ P50, P90, P99 và cảnh báo ngay khi độ trễ vượt ngưỡng cam kết SLA (>1500ms)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC5.1 - Giám sát hiệu năng và đo kiểm Telemetry realtime",
        """
Quản_trị_viên    Giao_diện_Dashboard    Kênh_WebSocket_Metrics    Dịch_vụ_Telemetry    CSDL_Pipeline_Metrics
      |                   |                       |                       |                      |
      |--[1] Mở Dashboard |                       |                       |                      |
      |                   |--[2] ws://connect /ws/admin/telemetry-------->|                      |
      |                   |<--[3] 101 Switching Protocols-----------------|                      |
      |                   |                       |                       |--[4] get_realtime_metrics()
      |                   |                       |                       |      (P50, P90, P99) |
      |                   |                       |<--[5] Emit Telemetry Event-------------------|
      |                   |<==[6] JSON Stream: {vad_ms: 120, stt_ms: 450, nmt_ms: 180, e2e: 850}========|
      |                   |--[7] Vẽ đồ thị trực quan đường trễ EChart----------------------------|
      |                   |                       |                       |                      |
      |                   |     [opt: Độ trễ P99 vượt ngưỡng SLA > 1500ms]                       |
      |                   |<==[8] JSON Event: {alert: 'SLA_VIOLATION_LATENCY_HIGH'}==============|
      |                   |--[9] Bật chuông cảnh báo đỏ trên Dashboard---------------------------|
"""
    )
    add_caption(doc, "Hình 3.15: Biểu đồ tuần tự ca sử dụng UC5.1 - Giám sát hiệu năng Telemetry realtime", is_table=False)

    uc5_1_steps = [
        ("1", "Quản trị viên", "Giao diện Dashboard", "Truy cập màn hình Giám sát Hiệu năng", "None", "Mở trang Dashboard Telemetry."),
        ("2", "Giao diện Dashboard", "Kênh WebSocket", "ws://.../ws/admin/telemetry", "WS Connect", "Thiết lập kết nối luồng nhận số liệu thời gian thực."),
        ("3", "Dịch vụ Telemetry", "CSDL Metrics", "aggregate_percentiles(window=5min)", "SQL Aggregate", "Tính toán phân vị P50, P90, P99 cho từng chặng xử lý."),
        ("4", "Kênh WebSocket", "Giao diện Dashboard", "send_json(metrics_payload)", "JSON Stream", "Bắn tọa độ độ trễ theo từng giây."),
        ("5", "Giao diện Dashboard", "Giao diện Dashboard", "render_echarts(latencies)", "Canvas Draw", "Cập nhật đồ thị đường biểu diễn độ trễ vi mô tức thời."),
        ("6", "Dịch vụ Telemetry", "Giao diện Dashboard", "emit_alert_if_over_threshold()", "Alert Event", "Phát cảnh báo màu đỏ nếu phát hiện nghẽn mạng hoặc suy giảm GPU.")
    ]
    render_sequence_table(doc, uc5_1_steps)

    # UC5.2
    add_paragraph(doc, "3.3.5.2. Sơ đồ tuần tự UC5.2 - Tra cứu và lọc nâng cao nhật ký phiên dịch và sự cố hệ thống:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép thanh tra, quản trị viên lọc lịch sử toàn bộ các câu dịch trong hệ thống theo nhiều tiêu chí: "
        "khoảng thời gian, mã phiên, ngôn ngữ, trạng thái có lỗi (error_stage), hoặc câu dịch bị gắn cờ."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC5.2 - Tra cứu và lọc nâng cao nhật ký phiên dịch",
        """
Quản_trị_viên    Giao_diện_Logs_Admin   Router_Admin_Logs    Dịch_vụ_Truy_vấn_Log    CSDL_Translation_Logs
      |                   |                      |                    |                      |
      |--[1] Thiết lập bộ lọc:                   |                    |                      |
      |  status='error', lang='vi->en', 24 giờ qua                    |                      |
      |--[2] Bấm 'Tìm kiếm'--------------------->|                    |                      |
      |                   |--[3] GET /api/v1/admin/logs?status=error->|                      |
      |                   |                      |--[4] query_logs()-->                      |
      |                   |                      |                    |--[5] Dynamic SQL Query với Index
      |                   |                      |                    |<--[6] Kết quả 14 bản ghi lỗi--|
      |                   |<--[7] 200 OK: {logs: [...], total: 14}----|                      |
      |                   |--[8] Hiển thị bảng chi tiết lỗi kèm chi tiết chặng gặp sự cố-----|
"""
    )
    add_caption(doc, "Hình 3.16: Biểu đồ tuần tự ca sử dụng UC5.2 - Tra cứu và lọc nâng cao nhật ký", is_table=False)

    uc5_2_steps = [
        ("1", "Quản trị viên", "Giao diện Logs Admin", "Nhập các tham số lọc nâng cao trên thanh công cụ", "Filter Params", "Chỉ định điều kiện tìm kiếm sự cố."),
        ("2", "Giao diện Logs Admin", "Router Admin Logs", "GET /api/v1/admin/logs?params", "HTTP Request", "Gửi yêu cầu truy vấn nhật ký chi tiết."),
        ("3", "Router Admin Logs", "Dịch vụ Truy vấn Log", "execute_filter(params)", "Service Call", "Xây dựng câu lệnh truy vấn động tối ưu index."),
        ("4", "Dịch vụ Truy vấn Log", "CSDL Logs", "SELECT * FROM translation_logs WHERE ...", "SQL Query", "Lọc các bản ghi khớp tiêu chí."),
        ("5", "Router Admin Logs", "Giao diện Logs Admin", "200 OK: {logs: [...], total}", "JSON Array", "Trả về danh sách phục vụ công tác thanh tra chất lượng.")
    ]
    render_sequence_table(doc, uc5_2_steps)

    # =========================================================================
    # NHÓM 6: QUẢN TRỊ HỆ THỐNG (UC6.1 - UC6.2)
    # =========================================================================
    add_heading_3(doc, "3.3.6. Nhóm UC6 - Quản trị hệ thống")

    # UC6.1
    add_paragraph(doc, "3.3.6.1. Sơ đồ tuần tự UC6.1 - Quản lý tài khoản người dùng và phân quyền vai trò (RBAC):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Thao tác đặc quyền dành cho Quản trị cấp cao (Superadmin) để tạo mới tài khoản nhân viên, "
        "gán vai trò phân quyền (admin, reviewer, employee), kích hoạt/khóa tài khoản và cấp lại quyền bảo mật."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC6.1 - Quản lý người dùng và phân quyền RBAC",
        """
Superadmin       Giao_diện_User_Admin   Router_User_Admin    Dịch_vụ_RBAC       CSDL_Users_Audit
    |                     |                      |                |                    |
    |--[1] Nhập: username, email, role='reviewer'|                |                    |
    |--[2] Bấm 'Tạo tài khoản'------------------>|                |                    |
    |                     |--[3] POST /api/v1/admin/users-------->|                    |
    |                     |      {username, role, temp_pwd}       |                    |
    |                     |                      |--[4] create()->|                    |
    |                     |                      |                |--[5] Băm mật khẩu tạm Argon2id
    |                     |                      |                |--[6] INSERT INTO users (role)----->|
    |                     |                      |                |--[7] INSERT INTO audit_logs ------->|
    |                     |                      |<--[8] 201 Created: {user_id: 15}---|
    |                     |<--[9] Hiển thị thành công, cập nhật danh sách người dùng---|
"""
    )
    add_caption(doc, "Hình 3.17: Biểu đồ tuần tự ca sử dụng UC6.1 - Quản lý người dùng và phân quyền RBAC", is_table=False)

    uc6_1_steps = [
        ("1", "Superadmin", "Giao diện User Admin", "Điền biểu mẫu thông tin tài khoản và vai trò", "Form Input", "Nhập thông tin nhân sự cần cấp quyền."),
        ("2", "Giao diện User Admin", "Router User Admin", "POST /api/v1/admin/users", "HTTP Request", "Gửi yêu cầu tạo người dùng mới."),
        ("3", "Router User Admin", "Dịch vụ RBAC", "create_user_with_role(payload)", "Service Call", "Kiểm tra thẩm quyền Superadmin và hợp lệ dữ liệu."),
        ("4", "Dịch vụ RBAC", "CSDL Users", "INSERT INTO users (...) VALUES (...)", "SQL Insert", "Lưu tài khoản mới với mật khẩu băm bảo mật."),
        ("5", "Dịch vụ RBAC", "CSDL Audit", "INSERT INTO audit_logs (action='USER_CREATED')", "SQL Insert", "Ghi nhật ký kiểm toán hành động tạo tài khoản."),
        ("6", "Router User Admin", "Giao diện User Admin", "201 Created: {user_id, status}", "JSON", "Báo tạo tài khoản thành công.")
    ]
    render_sequence_table(doc, uc6_1_steps)

    # UC6.2
    add_paragraph(doc, "3.3.6.2. Sơ đồ tuần tự UC6.2 - Quản lý và cấp phát khóa tích hợp API đối tác (API Keys):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Cho phép Quản trị viên sinh khóa API mới dành cho các ứng dụng ngoại vi (Kiosk sân bay, hệ thống khách sạn). "
        "Chuỗi khóa bí mật chỉ được hiển thị duy nhất một lần (One-time Display) và chỉ lưu mã băm SHA-256 trong CSDL."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC6.2 - Quản lý và cấp phát khóa API Keys",
        """
Quản_trị_viên    Giao_diện_API_Keys     Router_API_Keys     Dịch_vụ_ApiKey     Bộ_băm_SHA256      CSDL_ApiKeys
      |                   |                     |                   |                 |                |
      |--[1] Nhập nhãn: 'Kiosk San Bay', RPM: 60|                   |                 |                |
      |--[2] Bấm 'Tạo khóa mới'---------------->|                   |                 |                |
      |                   |--[3] POST /api/v1/admin/api-keys------->|                 |                |
      |                   |      {name, rate_limit: 60}             |                 |                |
      |                   |                     |--[4] generate()-->|                 |                |
      |                   |                     |                   |--[5] Sinh ngẫu nhiên chuỗi key thô: 'tlg_live_...'
      |                   |                     |                   |--[6] hash_key(raw_key)---------->|
      |                   |                     |                   |<--[7] key_hash (64 hex)----------|
      |                   |                     |                   |--[8] INSERT INTO api_keys ------>|
      |                   |                     |                   |      (key_prefix, key_hash, RPM) |
      |                   |                     |<--[9] 201 Created: {raw_key: 'tlg_live_...'}---------|
      |                   |<--[10] Modal Popup hiển thị raw_key duy nhất 1 lần (Kèm nút Copy)----------|
"""
    )
    add_caption(doc, "Hình 3.18: Biểu đồ tuần tự ca sử dụng UC6.2 - Cấp phát khóa tích hợp API Keys", is_table=False)

    uc6_2_steps = [
        ("1", "Quản trị viên", "Giao diện API Keys", "Nhập tên nhãn gợi nhớ và hạn mức giới hạn gọi RPM", "Form Input", "Cung cấp tham số cấu hình API Key."),
        ("2", "Giao diện API Keys", "Router API Keys", "POST /api/v1/admin/api-keys", "HTTP Request", "Gửi yêu cầu khởi tạo khóa."),
        ("3", "Router API Keys", "Dịch vụ ApiKey", "generate_new_key(name, rpm)", "Service Call", "Sinh chuỗi khóa bảo mật ngẫu nhiên cao."),
        ("4", "Dịch vụ ApiKey", "Bộ băm SHA256", "sha256(raw_key)", "Crypto Hash", "Băm chuỗi khóa để lưu trữ bảo mật trong DB."),
        ("5", "Dịch vụ ApiKey", "CSDL ApiKeys", "INSERT INTO api_keys (key_prefix, key_hash, rpm)", "SQL Insert", "Lưu khóa và hạn mức RPM vào cơ sở dữ liệu."),
        ("6", "Router API Keys", "Giao diện API Keys", "201 Created: {raw_key}", "JSON Response", "Trả về chuỗi key đầy đủ lần duy nhất."),
        ("7", "Giao diện API Keys", "Quản trị viên", "Hiện hộp thoại cảnh báo sao chép khóa bí mật", "Modal Popup", "Quản trị viên sao chép khóa để tích hợp vào ứng dụng ngoại vi.")
    ]
    render_sequence_table(doc, uc6_2_steps)

    # =========================================================================
    # NHÓM 7: HUẤN LUYỆN VÀ QUẢN LÝ MÔ HÌNH (UC7.1 - UC7.3)
    # =========================================================================
    add_heading_3(doc, "3.3.7. Nhóm UC7 - Huấn luyện và quản lý mô hình")

    # UC7.1
    add_paragraph(doc, "3.3.7.1. Sơ đồ tuần tự UC7.1 - Khởi tạo và giám sát tiến trình huấn luyện mô hình LoRA PEFT:", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Quản trị viên kích hoạt tiến trình huấn luyện thích ứng thứ hạng thấp LoRA trên GPU độc lập. "
        "Tiến trình phát luồng tọa độ giá trị hàm mất mát (Loss) qua WebSocket để vẽ đồ thị hội tụ trực tiếp trên Web Admin."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC7.1 - Khởi tạo và giám sát tiến trình huấn luyện LoRA PEFT",
        """
Quản_trị_viên    Giao_diện_Training     Router_Training     Dịch_vụ_Training    Worker_PyTorch_GPU    CSDL_Jobs_Events
      |                   |                     |                   |                   |                    |
      |--[1] Chọn tập v1.2, r=16, lr=2e-4, 5 epochs                 |                   |                    |
      |--[2] Bấm 'Chạy huấn luyện GPU'--------->|                   |                   |                    |
      |                   |--[3] POST /api/v1/training/jobs-------->|                   |                    |
      |                   |      {dataset_id, model: 'nllb', lora_r}|                   |                    |
      |                   |                     |--[4] spawn_job()->|                   |                    |
      |                   |                     |                   |--[5] Khởi chạy tiến trình Python nền->|
      |                   |                     |                   |--[6] INSERT training_jobs (RUNNING)|
      |                   |<--[7] 202 Accepted: {job_id: 'job_01'}--|                   |                    |
      |                   |                                         |                   |                    |
      |                   |====[LOOP: Huấn luyện từng bước trên GPU và phát sự kiện Realtime]===============|
      |                   |                     |                   |                   |--[8] train_step()->|
      |                   |                     |                   |                   |--[9] INSERT event->|
      |                   |                     |<===[10] WS Event: {step: 100, loss: 1.84, lr: 2e-4}=======|
      |                   |<===[11] Cập nhật đồ thị hàm mất mát Loss trực tiếp trên UI=======================|
      |                   |                     |                   |                   |                    |
      |                   |                     |                   |                   |--[12] eval_bleu()->|
      |                   |                     |                   |                   |--[13] export_lora()|
      |                   |                     |                   |<--[14] Job Finished (BLEU: 38.6)---|
      |                   |                     |                   |--[15] INSERT model_artifacts ------>|
      |                   |<--[16] Báo hoàn tất, mở khóa mô hình ứng viên (Candidate Artifact)---------------|
"""
    )
    add_caption(doc, "Hình 3.19: Biểu đồ tuần tự ca sử dụng UC7.1 - Khởi tạo và giám sát tiến trình huấn luyện LoRA", is_table=False)

    uc7_1_steps = [
        ("1", "Quản trị viên", "Giao diện Training", "Cấu hình siêu tham số: tập dữ liệu, lora_r=16, lr=2e-4", "Config Input", "Thiết lập cấu hình huấn luyện."),
        ("2", "Giao diện Training", "Router Training", "POST /api/v1/training/jobs", "HTTP Request", "Gửi lệnh kích hoạt tiến trình huấn luyện GPU."),
        ("3", "Router Training", "Dịch vụ Training", "launch_training_job(params)", "Service Call", "Khởi tạo tác vụ trong cơ sở dữ liệu."),
        ("4", "Dịch vụ Training", "Worker PyTorch GPU", "spawn_process(train_lora.py)", "Process Exec", "Khởi chạy tiến trình PyTorch độc lập chiếm dụng GPU."),
        ("5", "Worker PyTorch GPU", "Giao diện Training", "ws.send({'step': s, 'loss': l})", "WS Event", "Bắn dữ liệu mất mát Loss liên tục qua WebSocket."),
        ("6", "Giao diện Training", "Quản trị viên", "Cập nhật đường cong Loss thời gian thực", "UI Chart", "Người dùng theo dõi mức độ hội tụ của mô hình."),
        ("7", "Worker PyTorch GPU", "Dịch vụ Training", "on_job_completed(metrics)", "Callback", "Huấn luyện xong, đánh giá BLEU trên tập test."),
        ("8", "Dịch vụ Training", "CSDL Jobs Events", "INSERT INTO model_artifacts (status='candidate')", "SQL Insert", "Đăng ký gói mô hình thành phẩm vào kho lưu trữ.")
    ]
    render_sequence_table(doc, uc7_1_steps)

    # UC7.2 & UC7.3
    add_paragraph(doc, "3.3.7.2. Sơ đồ tuần tự UC7.2 & UC7.3 - Triển khai thử nghiệm Canary và Thu hồi phiên bản khẩn cấp (Rollback):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mô tả nghiệp vụ: Thao tác điều hướng lưu lượng suy luận phục vụ người dùng thực tế. Quản trị cấp cao định tuyến 10% lưu lượng "
        "sang mô hình ứng viên mới (Canary 10%). Nếu phát hiện suy giảm chất lượng hoặc độ trễ tăng cao, cơ chế Rollback 1-click "
        "ngay lập tức hoàn nguyên phiên bản ổn định trước đó mà không cần khởi động lại máy chủ (Zero Downtime)."
    )
    add_diagram_box(
        doc,
        "Biểu đồ tuần tự: UC7.2 & UC7.3 - Triển khai thử nghiệm Canary và Thu hồi Rollback",
        """
Quản_trị_cấp_cao  Giao_diện_Deploy      Router_Deploy       ModelManager        CSDL_Deployments     Audit_Log
       |                  |                   |                  |                    |                  |
       |===[GIAI ĐOẠN 1: TRIỂN KHAI THỬ NGHIỆM CANARY 10% (UC7.2)]===========================================|
       |--[1] Chọn model candidate, đặt Canary=10%               |                    |                  |
       |--[2] Bấm 'Áp dụng Canary'----------->|                  |                    |                  |
       |                  |--[3] POST /api/v1/deployments/canary>|                    |                  |
       |                  |      {canary_model: 'v1.2', pct: 10} |                    |                  |
       |                  |                   |--[4] set_canary->|                    |                  |
       |                  |                   |                  |--[5] reload_routing_table()           |
       |                  |                   |                  |      (90% Active, 10% Canary)         |
       |                  |                   |                  |--[6] UPDATE model_deployments-------->|
       |                  |                   |                  |--[7] INSERT deployment_events-------->|
       |                  |                   |                  |--[8] INSERT audit_logs -------------->|
       |                  |<--[9] 200 OK: 'Canary 10% Active'----|                    |                  |
       |                  |<--[10] Cập nhật giao diện: 10% người dùng thực tế chuyển sang mô hình mới--------|
       |                  |                   |                  |                    |                  |
       |===[GIAI ĐOẠN 2: THU HỒI KHẨN CẤP ROLLBACK NẾU PHÁT SINH LỖI (UC7.3)]================================|
       |--[11] Phát hiện P99 tăng vọt -> Bấm 'Rollback Khẩn cấp'>|                    |                  |
       |                  |--[12] POST /api/v1/deployments/rollback------------------>|                  |
       |                  |                   |--[13] rollback()->                    |                  |
       |                  |                   |                  |--[14] revert_to_previous_active()     |
       |                  |                   |                  |      (Active = Previous, Canary = 0)  |
       |                  |                   |                  |--[15] UPDATE model_deployments------->|
       |                  |                   |                  |--[16] INSERT deployment_events------->|
       |                  |                   |                  |--[17] INSERT audit_logs ------------->|
       |                  |<--[18] 200 OK: 'Rollback Completed'--|                    |                  |
       |<--[19] Cảnh báo an toàn: Hệ thống đã hoàn nguyên phiên bản ổn định trước đó tức thì-----------------|
"""
    )
    add_caption(doc, "Hình 3.20: Biểu đồ tuần tự ca sử dụng UC7.2 & UC7.3 - Triển khai Canary và Thu hồi Rollback", is_table=False)

    uc7_2_steps = [
        ("1", "Quản trị cấp cao", "Giao diện Deploy", "Chọn mô hình v1.2, đặt tỷ lệ Canary 10%", "Config Input", "Cấu hình phân luồng lưu lượng thử nghiệm."),
        ("2", "Giao diện Deploy", "Router Deploy", "POST /api/v1/deployments/canary", "HTTP Request", "Gửi yêu cầu áp dụng tỷ lệ Canary."),
        ("3", "Router Deploy", "ModelManager", "update_canary_routing('v1.2', 10)", "Internal Call", "Cập nhật thuật toán bốc thăm lưu lượng suy luận trong RAM."),
        ("4", "ModelManager", "CSDL Deployments", "UPDATE model_deployments & deployment_events", "SQL Update", "Lưu vết cấu hình phân bổ lưu lượng mới."),
        ("5", "Router Deploy", "Audit Log", "INSERT INTO audit_logs (action='CANARY_SET')", "SQL Insert", "Ghi nhật ký kiểm toán hành động thay đổi cấu hình."),
        ("6", "Giao diện Deploy", "Quản trị cấp cao", "Báo áp dụng thành công; hiển thị đo kiểm 2 luồng", "UI Render", "Theo dõi song song tỷ lệ lỗi giữa Active và Canary."),
        ("7", "Quản trị cấp cao", "Giao diện Deploy", "Phát hiện sự cố -> Bấm nút 'Rollback Khẩn cấp'", "Click Button", "Kích hoạt cơ chế an toàn phục hồi phiên bản."),
        ("8", "Giao diện Deploy", "Router Deploy", "POST /api/v1/deployments/rollback", "HTTP Request", "Gửi yêu cầu hoàn nguyên phiên bản."),
        ("9", "Router Deploy", "ModelManager", "rollback_to_previous_active()", "Internal Call", "Hoán đổi ngay lập tức phiên bản Active về phiên bản trước đó."),
        ("10", "ModelManager", "CSDL Deployments", "UPDATE model_deployments (canary_percent=0)", "SQL Update", "Xóa bỏ cấu hình canary, đưa 100% lưu lượng về an toàn."),
        ("11", "Giao diện Deploy", "Quản trị cấp cao", "Thông báo hoàn tất thu hồi phiên bản trong 0.2s", "UI Alert", "Bảo đảm dịch vụ dịch thuật không bị gián đoạn.")
    ]
    render_sequence_table(doc, uc7_2_steps)

    print("All 18 Use Cases Sequence Diagrams rendered successfully.")
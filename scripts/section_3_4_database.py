# -*- coding: utf-8 -*-
"""
Module providing 3.4: Thiet ke co so du lieu (Database Design & Data Dictionary) for T-Lingua report.
Includes ERD architecture, Table 3.3 summary, and exhaustive data dictionaries for all 17 tables
matching the actual backend SQLAlchemy schema and the university thesis standards of [DALN]2210.
"""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from scripts.docx_utils import (
    add_paragraph, add_heading_2, add_heading_3, add_caption, add_bullet,
    add_diagram_box, set_cell_background, set_cell_margins, set_table_borders,
    PRIMARY_COLOR, SECONDARY_COLOR, HEADER_BG_HEX, SUBHEADER_BG_HEX, ZEBRA_BG_HEX
)

def render_data_dictionary_table(doc, table_name, table_desc, columns):
    """
    Renders standard Data Dictionary table for a database table:
    [STT, Tên trường, Kiểu dữ liệu, PK, FK, Null, Mặc định, Mô tả & Ràng buộc]
    """
    add_paragraph(doc, f"Bảng: {table_name}", bold=True, font_size=12, space_before=6, space_after=2, color=PRIMARY_COLOR)
    add_paragraph(doc, f"Mô tả nghiệp vụ: {table_desc}", italic=False, font_size=11, space_after=4)
    
    tbl = doc.add_table(rows=0, cols=8)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)
    
    headers = ["STT", "Tên trường", "Kiểu dữ liệu", "PK", "FK", "Null", "Mặc định", "Mô tả ý nghĩa & Ràng buộc"]
    widths = [Inches(0.4), Inches(1.5), Inches(1.1), Inches(0.4), Inches(0.5), Inches(0.5), Inches(0.9), Inches(1.9)]
    
    hdr = tbl.add_row()
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, col in enumerate(columns):
        row = tbl.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for c_idx in range(8):
            cell = row.cells[c_idx]
            cell.width = widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            p = cell.paragraphs[0]
            val = str(col[c_idx])
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.bold = True
            elif c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.bold = True
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
            elif c_idx in (2, 3, 4, 5, 6):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_paragraph(doc, "", space_after=4)

def build_section_3_4(doc):
    """Generates Section 3.4: Thiet ke co so du lieu."""
    add_heading_2(doc, "3.4. Thiết kế cơ sở dữ liệu (Database Design)")
    
    add_paragraph(
        doc,
        "Cơ sở dữ liệu của hệ thống T-Lingua được xây dựng dựa trên hệ quản trị cơ sở dữ liệu quan hệ (RDBMS), "
        "sử dụng ORM SQLAlchemy 2.0 cho phép linh hoạt vận hành trên cả SQLite (môi trường thử nghiệm cục bộ/kiểm thử tự động) "
        "và PostgreSQL (môi trường sản xuất doanh nghiệp). "
        "Mô hình dữ liệu được thiết kế đạt chuẩn hóa dạng 3 (3NF), loại bỏ tối đa dư thừa dữ liệu, đồng thời phân tách rõ ràng "
        "giữa dữ liệu phiên dịch thời gian thực (Realtime Logs & Metrics), dữ liệu kiểm soát truy cập (Access Control), "
        "bộ nhớ dịch thuật (Translation Memory) và chu trình học máy (MLOps Artifacts & Deployments)."
    )

    # 3.4.1
    add_heading_3(doc, "3.4.1. Lược đồ quan hệ thực thể tổng thể (Entity Relationship Diagram - ERD)")
    add_paragraph(
        doc,
        "Lược đồ ERD mô tả cấu trúc liên kết giữa 17 bảng trong hệ thống T-Lingua. "
        "Mối quan hệ trung tâm được thiết lập xung quanh bảng 'users' (quản lý phân quyền và người tác động), "
        "'translation_logs' (lưu vết từng câu dịch thực tế), 'quality_reviews' (cầu nối phản hồi giữa chuyên gia và tập dữ liệu) "
        "và chuỗi MLOps 'training_datasets' -> 'training_jobs' -> 'model_artifacts' -> 'model_deployments'."
    )

    add_diagram_box(
        doc,
        "Lược đồ quan hệ thực thể tổng thể (ERD Diagram)",
        """
 +------------------+           +------------------+           +--------------------+
 |      users       | 1       * |  auth_sessions   |           |    audio_assets    |
 |------------------|-----------|------------------|           |--------------------|
 | PK  id           |           | PK  id           |           | PK  file_name      |
 |     username     |           | FK  user_id      |           |     owner_id       |
 |     password_hash|           |     token_hash   |           |     expires_at     |
 |     role         |           +------------------+           +--------------------+
 |     mfa_enabled  | 1       * +------------------+
 +------------------+-----------|     api_keys     |
   | 1             | 1          |------------------|
   |               |            | PK  id           |
   |               |            | FK  created_by   |
   |               |            +------------------+
   |               | 1        * +------------------+
   |               +------------|    audit_logs    |
   |                            |------------------|
   |                            | PK  id           |
   |                            | FK  actor_user_id|
   |                            +------------------+
   v 1
 +------------------+ 1       1 +------------------+ 1       * +--------------------+
 |  quality_reviews |-----------| translation_logs |-----------|  pipeline_metrics  |
 |------------------|           |------------------|           |--------------------|
 | PK  id           |           | PK  id           |           | PK  id             |
 | FK  trans_log_id |           |     session_id   |           |     turn_id        |
 | FK  reviewer_id  |           |     source_text  |           |     stt_ms         |
 |     mqm_score    |           |     trans_text   |           |     translate_ms   |
 |     corrected_txt|           |     is_flagged   |           |     tts_total_ms   |
 +------------------+           +------------------+           |     end_to_end_ms  |
         | 1                             | 1                   +--------------------+
         |                               v 1
         |                      +------------------+
         |                      |train_audio_assets|
         |                      |------------------|
         |                      | PK  id           |
         |                      | FK  trans_log_id |
         |                      |     file_name    |
         |                      +------------------+
         v 1 (xuất thành)
 +------------------+ 1       * +------------------+ 1       1 +--------------------+
 | training_datasets|-----------|  training_jobs   |-----------|   model_artifacts  |
 |------------------|           |------------------|           |--------------------|
 | PK  id           |           | PK  id           |           | PK  id             |
 |     name         |           | FK  dataset_id   |           | FK  dataset_id     |
 |     version      |           |     base_model   |           | FK  job_id         |
 |     sample_count |           |     lora_r       |           |     storage_uri    |
 |     sha256       |           |     train_loss   |           |     sha256         |
 |     is_frozen    |           |     status       |           |     test_bleu      |
 +------------------+           +------------------+           +--------------------+
                                         | 1                             | 1..* (tham chiếu)
                                         v *                             v
                                +------------------+           +--------------------+
                                |train_job_events  |           | model_deployments  |
                                |------------------|           |--------------------|
                                | PK  id           |           | PK  id             |
                                | FK  job_id       |           |     component      |
                                |     metrics_json |           |     active_model   |
                                +------------------+           |     canary_model   |
                                                               |     canary_percent |
                                                               +--------------------+
"""
    )
    add_caption(doc, "Hình 3.8: Lược đồ quan hệ thực thể tổng thể (ERD) của hệ thống T-Lingua", is_table=False)

    # 3.4.2 Bảng tổng hợp danh sách các bảng
    add_heading_3(doc, "3.4.2. Danh sách tổng hợp các bảng trong hệ thống (Bảng 3.3)")
    add_paragraph(
        doc,
        "Hệ thống cơ sở dữ liệu T-Lingua bao gồm tổng cộng 17 bảng nghiệp vụ, được phân chia theo 4 nhóm chức năng rõ rệt:"
    )
    
    tbl_summary = doc.add_table(rows=0, cols=4)
    tbl_summary.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_summary)
    
    sum_headers = ["STT", "Tên bảng", "Phân nhóm chức năng", "Mô tả mục đích lưu trữ"]
    sum_widths = [Inches(0.6), Inches(2.2), Inches(1.8), Inches(2.6)]
    
    hdr = tbl_summary.add_row()
    for i, h in enumerate(sum_headers):
        cell = hdr.cells[i]
        cell.width = sum_widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=90, bottom=90, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    tables_list = [
        ("1", "users", "Xác thực & Bảo mật", "Lưu trữ tài khoản người dùng, băm mật khẩu Argon2, vai trò RBAC và khóa MFA."),
        ("2", "auth_sessions", "Xác thực & Bảo mật", "Quản lý phiên đăng nhập JWT, băm refresh token, thời hạn và trạng thái thu hồi."),
        ("3", "api_keys", "Xác thực & Bảo mật", "Lưu trữ khóa API dành cho ứng dụng tích hợp bên ngoài, quota giới hạn RPM."),
        ("4", "audit_logs", "Xác thực & Bảo mật", "Nhật ký kiểm toán an ninh bất biến, ghi lại mọi hành vi nhạy cảm của người dùng."),
        ("5", "translation_logs", "Dịch thuật & Telemetry", "Lưu trữ lịch sử các câu dịch, mã phiên, văn bản gốc, bản dịch, điểm tin cậy và cờ lỗi."),
        ("6", "pipeline_metrics", "Dịch thuật & Telemetry", "Số liệu đo kiểm vi mô độ trễ từng chặng (VAD, STT, NMT, TTS, End-to-End) theo turn."),
        ("7", "audio_assets", "Dịch thuật & Telemetry", "Quản lý siêu dữ liệu các tệp âm thanh ghi âm và phát âm gắn liền với phiên dịch."),
        ("8", "translation_memory_entries", "Bộ nhớ Dịch & QA", "Kho từ vựng và cặp câu chuẩn hóa (Glossary/TM) phục vụ can thiệp dịch chuyên ngành."),
        ("9", "quality_reviews", "Bộ nhớ Dịch & QA", "Phiếu thẩm định của chuyên gia ngôn ngữ, đánh giá lỗi MQM, văn bản đã sửa và nhãn huấn luyện."),
        ("10", "training_audio_assets", "Bộ nhớ Dịch & QA", "Âm thanh nguồn đạt chuẩn kèm sự đồng thuận bản quyền làm dữ liệu huấn luyện Whisper."),
        ("11", "system_settings", "Cấu hình Hệ thống", "Lưu trữ các tham số cấu hình động toàn hệ thống dưới dạng Key-Value."),
        ("12", "training_datasets", "MLOps & Huấn luyện", "Các bản chụp tập dữ liệu huấn luyện đóng băng (Frozen Datasets) kèm mã băm SHA-256."),
        ("13", "training_jobs", "MLOps & Huấn luyện", "Quản lý hàng đợi và tiến trình huấn luyện mô hình học sâu LoRA PEFT trên GPU."),
        ("14", "training_job_events", "MLOps & Huấn luyện", "Nhật ký sự kiện chi tiết từng bước (step/epoch/loss) của tiến trình huấn luyện."),
        ("15", "model_artifacts", "MLOps & Triển khai", "Kho lưu trữ các gói mô hình AI thành phẩm (weights, adapters, metrics, checksum)."),
        ("16", "model_deployments", "MLOps & Triển khai", "Bảng cấu hình định tuyến phục vụ suy luận thực tế (Active Model, Canary Model, %)."),
        ("17", "deployment_events", "MLOps & Triển khai", "Lịch sử các đợt phát hành, điều chỉnh tỷ lệ canary, thăng hạng hoặc thu hồi rollback.")
    ]
    
    for idx, t in enumerate(tables_list):
        row = tbl_summary.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = sum_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.add_run(t[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.bold = True
            elif col_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.bold = True
                run.font.name = "Consolas"
                run.font.size = Pt(9)
            elif col_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_caption(doc, "Bảng 3.3: Danh sách tổng hợp các bảng trong cơ sở dữ liệu T-Lingua")

    # 3.4.3 Chi tiết Nhóm Xác thực & Bảo mật
    add_heading_3(doc, "3.4.3. Từ điển dữ liệu Nhóm Xác thực, Người dùng và Kiểm toán (Auth & Security)")

    # 1. users
    render_data_dictionary_table(
        doc,
        table_name="users",
        table_desc="Bảng trung tâm lưu trữ thông tin tài khoản người dùng, băm mật khẩu, phân quyền và cấu hình xác thực đa yếu tố.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của tài khoản."),
            ("2", "username", "VARCHAR(64)", "", "", "No", "None", "Tên đăng nhập duy nhất (Unique Index), dùng xác thực."),
            ("3", "password_hash", "VARCHAR(255)", "", "", "No", "None", "Mật khẩu đã băm bằng thuật toán Argon2id kèm muối an toàn."),
            ("4", "role", "VARCHAR(32)", "", "", "Yes", "'employee'", "Vai trò hệ thống: superadmin, admin, employee, reviewer."),
            ("5", "created_at", "DATETIME", "", "", "Yes", "utcnow()", "Thời điểm tạo tài khoản."),
            ("6", "public_id", "VARCHAR(36)", "", "", "No", "UUIDv4", "Mã định danh công khai (UUID) dùng cho API ngoại vi."),
            ("7", "is_active", "BOOLEAN", "", "", "No", "True", "Trạng thái kích hoạt. Nếu False, người dùng bị cấm đăng nhập."),
            ("8", "token_version", "INTEGER", "", "", "No", "0", "Phiên bản token. Tăng lên khi muốn thu hồi toàn bộ token cũ."),
            ("9", "mfa_secret_encrypted", "TEXT", "", "", "Yes", "None", "Khóa bí mật TOTP được mã hóa AES-GCM 256-bit."),
            ("10", "mfa_enabled", "BOOLEAN", "", "", "No", "False", "Cờ bật/tắt xác thực 2 yếu tố TOTP qua Google Authenticator."),
            ("11", "mfa_last_counter", "INTEGER", "", "", "No", "-1", "Bước thời gian TOTP gần nhất đã dùng, chống tấn công phát lại.")
        ]
    )

    # 2. auth_sessions
    render_data_dictionary_table(
        doc,
        table_name="auth_sessions",
        table_desc="Lưu trữ phiên làm việc hợp lệ của người dùng, liên kết với Refresh Token đã băm.",
        columns=[
            ("1", "id", "VARCHAR(36)", "V", "", "No", "UUIDv4", "Khóa chính định danh phiên."),
            ("2", "token_hash", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 của Refresh Token bảo vệ an toàn trong DB."),
            ("3", "owner_id", "VARCHAR(36)", "", "", "No", "None", "public_id của người sở hữu phiên."),
            ("4", "user_id", "INTEGER", "", "users.id", "Yes", "None", "Khóa ngoại tham chiếu đến bảng users."),
            ("5", "token_version", "INTEGER", "", "", "No", "0", "Phiên bản token tương ứng lúc cấp phát phiên."),
            ("6", "scopes", "TEXT", "", "", "No", "None", "Danh sách quyền hạn gán cho phiên dạng chuỗi JSON."),
            ("7", "mfa_verified", "BOOLEAN", "", "", "No", "False", "Đánh dấu phiên này đã vượt qua bước xác thực TOTP hay chưa."),
            ("8", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm đăng nhập."),
            ("9", "expires_at", "DATETIME", "", "", "No", "None", "Thời điểm phiên hết hạn bắt buộc đăng nhập lại."),
            ("10", "revoked_at", "DATETIME", "", "", "Yes", "None", "Thời điểm phiên bị thu hồi thủ công (hoặc NULL nếu còn hạn).")
        ]
    )

    # 3. api_keys
    render_data_dictionary_table(
        doc,
        table_name="api_keys",
        table_desc="Quản lý khóa API dành cho các máy khách tích hợp và đối tác doanh nghiệp.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của API key."),
            ("2", "name", "VARCHAR(100)", "", "", "No", "None", "Tên hoặc nhãn gợi nhớ của khóa."),
            ("3", "key", "VARCHAR(255)", "", "", "No", "None", "Định danh khóa tương thích ngược."),
            ("4", "is_active", "BOOLEAN", "", "", "Yes", "True", "Trạng thái hiệu lực của khóa."),
            ("5", "created_at", "DATETIME", "", "", "Yes", "utcnow()", "Thời điểm cấp khóa."),
            ("6", "key_hash", "VARCHAR(64)", "", "", "Yes", "None", "Mã băm SHA-256 của chuỗi secret key dùng để so khớp."),
            ("7", "key_prefix", "VARCHAR(16)", "", "", "Yes", "None", "Tiền tố hiển thị công khai nhận diện ứng dụng (ví dụ: 'tlg_live_')."),
            ("8", "owner_id", "VARCHAR(36)", "", "", "Yes", "None", "Mã public_id của người sở hữu."),
            ("9", "created_by_user_id", "INTEGER", "", "users.id", "Yes", "None", "Khóa ngoại trỏ về tài khoản quản trị cấp khóa."),
            ("10", "scopes", "TEXT", "", "", "No", "'[]'", "Mảng JSON quy định các quyền API cho phép."),
            ("11", "expires_at", "DATETIME", "", "", "Yes", "None", "Thời hạn hết hạn của khóa."),
            ("12", "revoked_at", "DATETIME", "", "", "Yes", "None", "Thời điểm khóa bị vô hiệu hóa.")
        ]
    )

    # 4. audit_logs
    render_data_dictionary_table(
        doc,
        table_name="audit_logs",
        table_desc="Nhật ký kiểm toán an ninh lưu vết bất biến các hành động can thiệp hệ thống.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của bản ghi nhật ký."),
            ("2", "actor_user_id", "INTEGER", "", "users.id", "No", "None", "Khóa ngoại tham chiếu người thực hiện hành động."),
            ("3", "actor_username", "VARCHAR(100)", "", "", "No", "None", "Tên đăng nhập của người thực hiện tại thời điểm đó."),
            ("4", "action", "VARCHAR(64)", "", "", "No", "None", "Mã hành động: USER_LOGIN, CANARY_UPDATE, DICT_EDIT..."),
            ("5", "resource_type", "VARCHAR(32)", "", "", "No", "None", "Loại thực thể bị tác động: User, Deployment, Glossary..."),
            ("6", "resource_id", "VARCHAR(128)", "", "", "Yes", "None", "Mã định danh của thực thể bị thay đổi."),
            ("7", "details", "TEXT", "", "", "No", "'{}'", "Dữ liệu JSON chi tiết nội dung thay đổi (trước/sau)."),
            ("8", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm ghi nhận sự kiện kiểm toán.")
        ]
    )

    # 3.4.4 Chi tiết Nhóm Dịch thuật & Telemetry
    add_heading_3(doc, "3.4.4. Từ điển dữ liệu Nhóm Dịch thuật và Đo kiểm Telemetry (Translation & Telemetry)")

    # 5. translation_logs
    render_data_dictionary_table(
        doc,
        table_name="translation_logs",
        table_desc="Lưu trữ lịch sử chi tiết của từng lượt dịch thời gian thực trong hệ thống.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của lượt dịch."),
            ("2", "client_id", "VARCHAR(64)", "", "", "Yes", "None", "Định danh máy khách hoặc phiên kết nối."),
            ("3", "source_text", "TEXT", "", "", "No", "None", "Văn bản nhận dạng giọng nói từ Whisper."),
            ("4", "translated_text", "TEXT", "", "", "No", "None", "Văn bản dịch máy do NLLB-200 sinh ra."),
            ("5", "latency", "FLOAT", "", "", "Yes", "None", "Tổng thời gian xử lý dịch tính bằng giây."),
            ("6", "model_source", "VARCHAR(64)", "", "", "Yes", "None", "Nguồn sinh bản dịch: nllb_model hoặc translation_memory."),
            ("7", "input_mode", "VARCHAR(16)", "", "", "No", "'unknown'", "Chế độ nhập liệu: voice (âm thanh) hoặc text (văn bản)."),
            ("8", "stt_model_id", "VARCHAR(200)", "", "", "Yes", "None", "Phiên bản mô hình STT đang phục vụ."),
            ("9", "nllb_model_id", "VARCHAR(200)", "", "", "Yes", "None", "Phiên bản mô hình NMT đang phục vụ."),
            ("10", "source_lang", "VARCHAR(16)", "", "", "Yes", "'vi'", "Mã ngôn ngữ nguồn (ví dụ: 'vi', 'en', 'zh')."),
            ("11", "target_lang", "VARCHAR(16)", "", "", "Yes", "'en'", "Mã ngôn ngữ đích cần dịch sang."),
            ("12", "is_flagged", "BOOLEAN", "", "", "Yes", "False", "Cờ đánh dấu câu dịch bị nghi ngờ có lỗi."),
            ("13", "is_reviewed", "BOOLEAN", "", "", "No", "False", "Đã được chuyên gia QA xem xét và xử lý hay chưa."),
            ("14", "created_at", "DATETIME", "", "", "Yes", "utcnow()", "Thời điểm phát sinh lượt dịch.")
        ]
    )

    # 6. pipeline_metrics
    render_data_dictionary_table(
        doc,
        table_name="pipeline_metrics",
        table_desc="Lưu số liệu đo kiểm vi mô hiệu năng từng chặng (Telemetry) của từng lượt hội thoại âm thanh.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của bản ghi đo kiểm."),
            ("2", "turn_id", "VARCHAR(64)", "", "", "No", "None", "Mã lượt nói duy nhất (Unique), liên kết ngữ cảnh."),
            ("3", "session_id_hash", "VARCHAR(64)", "", "", "Yes", "None", "Băm bảo mật mã phiên hội thoại WebSocket."),
            ("4", "source_lang", "VARCHAR(16)", "", "", "No", "'vi'", "Mã ngôn ngữ nguồn."),
            ("5", "target_lang", "VARCHAR(16)", "", "", "No", "'en'", "Mã ngôn ngữ đích."),
            ("6", "status", "VARCHAR(16)", "", "", "No", "'success'", "Trạng thái: success, failed, timeout."),
            ("7", "error_stage", "VARCHAR(32)", "", "", "Yes", "None", "Chặng gặp sự cố: vad, stt, translate, tts."),
            ("8", "error_code", "VARCHAR(64)", "", "", "Yes", "None", "Mã lỗi chi tiết để lọc báo cáo."),
            ("9", "queue_wait_ms", "FLOAT", "", "", "Yes", "None", "Thời gian chờ hàng đợi xử lý (ms)."),
            ("10", "stt_ms", "FLOAT", "", "", "Yes", "None", "Thời gian nhận dạng âm thanh Whisper (ms)."),
            ("11", "translate_ms", "FLOAT", "", "", "Yes", "None", "Thời gian dịch máy NLLB-200 (ms)."),
            ("12", "tts_first_chunk_ms", "FLOAT", "", "", "Yes", "None", "Độ trễ phát ra gói âm thanh đầu tiên của TTS (ms)."),
            ("13", "tts_total_ms", "FLOAT", "", "", "Yes", "None", "Tổng thời gian tổng hợp toàn bộ âm thanh (ms)."),
            ("14", "end_to_end_ms", "FLOAT", "", "", "Yes", "None", "Tổng thời gian trễ trọn gói từ dứt lời đến phát loa (ms)."),
            ("15", "audio_duration_s", "FLOAT", "", "", "Yes", "None", "Thời lượng tệp âm thanh đầu vào tính bằng giây."),
            ("16", "text_length", "INTEGER", "", "", "Yes", "None", "Độ dài ký tự của câu dịch."),
            ("17", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm thu thập số liệu.")
        ]
    )

    # 7. audio_assets
    render_data_dictionary_table(
        doc,
        table_name="audio_assets",
        table_desc="Quản lý siêu dữ liệu và thời hạn tồn tại của các tệp âm thanh lưu trữ trên hệ thống.",
        columns=[
            ("1", "file_name", "VARCHAR(40)", "V", "", "No", "None", "Tên tệp âm thanh duy nhất trên ổ đĩa (UUID.wav)."),
            ("2", "owner_id", "VARCHAR(36)", "", "", "No", "None", "Định danh người sở hữu hoặc mã phiên tạo ra tệp."),
            ("3", "expires_at", "DATETIME", "", "", "No", "None", "Thời điểm tệp âm thanh hết hạn bị tự động xóa."),
            ("4", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm tệp âm thanh được ghi thành công.")
        ]
    )

    # 3.4.5 Chi tiết Nhóm Bộ nhớ Dịch & QA
    add_heading_3(doc, "3.4.5. Từ điển dữ liệu Nhóm Bộ nhớ Dịch và Kiểm soát Chất lượng (TM & QA)")

    # 8. translation_memory_entries
    render_data_dictionary_table(
        doc,
        table_name="translation_memory_entries",
        table_desc="Kho lưu trữ các cặp câu mẫu và thuật ngữ chuyên ngành chuẩn hóa (Glossary/Translation Memory).",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của mục từ điển."),
            ("2", "owner_id", "VARCHAR(64)", "", "", "No", "'global:approved'", "Chủ sở hữu hoặc phân vùng từ vựng."),
            ("3", "source_lang", "VARCHAR(16)", "", "", "No", "'vi'", "Mã ngôn ngữ nguồn."),
            ("4", "target_lang", "VARCHAR(16)", "", "", "No", "'en'", "Mã ngôn ngữ đích."),
            ("5", "source_text", "TEXT", "", "", "No", "None", "Cụm từ gốc trong ngôn ngữ nguồn."),
            ("6", "source_text_normalized", "VARCHAR(512)", "", "", "No", "None", "Văn bản nguồn đã chuẩn hóa chữ thường, xóa dấu cách thừa."),
            ("7", "translated_text", "TEXT", "", "", "No", "None", "Nghĩa dịch chuẩn bắt buộc áp dụng."),
            ("8", "norm_version", "INTEGER", "", "", "No", "1", "Phiên bản thuật toán chuẩn hóa văn bản."),
            ("9", "is_approved", "BOOLEAN", "", "", "No", "False", "Đã được phê duyệt áp dụng chính thức hay chưa."),
            ("10", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm tạo mục từ."),
            ("11", "updated_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm cập nhật gần nhất.")
        ]
    )

    # 9. quality_reviews
    render_data_dictionary_table(
        doc,
        table_name="quality_reviews",
        table_desc="Phiếu thẩm định và gắn nhãn chất lượng của chuyên gia ngôn ngữ đối với câu dịch.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của phiếu thẩm định."),
            ("2", "translation_log_id", "INTEGER", "", "translation_logs.id", "No", "None", "Khóa ngoại duy nhất trỏ đến câu dịch cần thẩm định."),
            ("3", "reviewer_user_id", "INTEGER", "", "users.id", "No", "None", "Khóa ngoại trỏ đến tài khoản chuyên gia thực hiện duyệt."),
            ("4", "adequacy", "INTEGER", "", "", "Yes", "None", "Điểm mức độ truyền tải đầy đủ ý nghĩa (1 đến 5 sao)."),
            ("5", "fluency", "INTEGER", "", "", "Yes", "None", "Điểm mức độ lưu loát tự nhiên của ngữ pháp (1 đến 5 sao)."),
            ("6", "error_category", "VARCHAR(32)", "", "", "Yes", "None", "Phân loại lỗi theo MQM: Accuracy, Terminology, Fluency..."),
            ("7", "critical_error", "BOOLEAN", "", "", "No", "False", "Đánh dấu lỗi nghiêm trọng làm sai lệch hoàn toàn ý nghĩa."),
            ("8", "corrected_text", "TEXT", "", "", "No", "None", "Văn bản bản dịch chuẩn xác do chuyên gia viết lại."),
            ("9", "corrected_source_text", "TEXT", "", "", "Yes", "None", "Văn bản gốc đã sửa lỗi chính tả nếu STT nghe sai."),
            ("10", "stt_status", "VARCHAR(24)", "", "", "No", "'not_applicable'", "Trạng thái nhận diện âm thanh."),
            ("11", "domain", "VARCHAR(64)", "", "", "Yes", "None", "Lĩnh vực chuyên ngành: Medical, Travel, General..."),
            ("12", "consent_for_training", "BOOLEAN", "", "", "No", "False", "Sự đồng thuận cho phép sử dụng mẫu này để huấn luyện AI."),
            ("13", "use_for_whisper", "BOOLEAN", "", "", "No", "False", "Cho phép dùng mẫu này để huấn luyện Whisper ASR."),
            ("14", "use_for_nllb", "BOOLEAN", "", "", "No", "False", "Cho phép dùng mẫu này để huấn luyện NLLB-200 NMT."),
            ("15", "whisper_split", "VARCHAR(16)", "", "", "Yes", "None", "Phân vùng tập dữ liệu Whisper: train, val, test."),
            ("16", "nllb_split", "VARCHAR(16)", "", "", "Yes", "None", "Phân vùng tập dữ liệu NLLB: train, val, test."),
            ("17", "notes", "TEXT", "", "", "Yes", "None", "Ghi chú phân tích lỗi của chuyên gia."),
            ("18", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm tạo phiếu duyệt."),
            ("19", "updated_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm cập nhật phiếu duyệt.")
        ]
    )

    # 10. training_audio_assets
    render_data_dictionary_table(
        doc,
        table_name="training_audio_assets",
        table_desc="Đoạn âm thanh nguồn đã xác thực bản quyền và chất lượng dùng huấn luyện mô hình Whisper.",
        columns=[
            ("1", "id", "VARCHAR(36)", "V", "", "No", "UUIDv4", "Khóa chính của tài sản âm thanh huấn luyện."),
            ("2", "translation_log_id", "INTEGER", "", "translation_logs.id", "No", "None", "Khóa ngoại duy nhất trỏ đến câu dịch gốc."),
            ("3", "file_name", "VARCHAR(40)", "", "", "No", "None", "Tên tệp WAV trên ổ đĩa lưu trữ bảo mật."),
            ("4", "sha256", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 bảo đảm tính toàn vẹn của tệp âm thanh."),
            ("5", "duration_ms", "INTEGER", "", "", "No", "None", "Thời lượng âm thanh tính bằng mili-giây."),
            ("6", "sample_rate", "INTEGER", "", "", "No", "16000", "Tần số lấy mẫu âm thanh chuẩn 16 kHz."),
            ("7", "channels", "INTEGER", "", "", "No", "1", "Số kênh âm thanh (1 kênh Mono)."),
            ("8", "uploaded_by_user_id", "INTEGER", "", "users.id", "Yes", "None", "Khóa ngoại trỏ đến người tải lên (hoặc NULL nếu hệ thống tự ghi)."),
            ("9", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm lưu trữ.")
        ]
    )

    # 11. system_settings
    render_data_dictionary_table(
        doc,
        table_name="system_settings",
        table_desc="Lưu trữ các tham số cấu hình động toàn hệ thống dưới dạng Key-Value.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của mục cấu hình."),
            ("2", "key", "VARCHAR(100)", "", "", "No", "None", "Khóa cấu hình duy nhất (ví dụ: 'vad_silence_ms', 'max_upload_mb')."),
            ("3", "value", "TEXT", "", "", "No", "None", "Giá trị cấu hình dạng chuỗi."),
            ("4", "description", "VARCHAR(255)", "", "", "Yes", "None", "Giải thích ý nghĩa tham số cấu hình."),
            ("5", "updated_at", "DATETIME", "", "", "Yes", "utcnow()", "Thời điểm chỉnh sửa tham số gần nhất.")
        ]
    )

    # 3.4.6 Chi tiết Nhóm MLOps & Vòng đời Mô hình
    add_heading_3(doc, "3.4.6. Từ điển dữ liệu Nhóm MLOps và Vòng đời Mô hình (Training Center & Lifecycle)")

    # 12. training_datasets
    render_data_dictionary_table(
        doc,
        table_name="training_datasets",
        table_desc="Lưu các phiên bản tập dữ liệu huấn luyện đã được kiểm định và đóng băng bất biến.",
        columns=[
            ("1", "id", "VARCHAR(36)", "V", "", "No", "UUIDv4", "Khóa chính của tập dữ liệu."),
            ("2", "name", "VARCHAR(120)", "", "", "No", "None", "Tên tập dữ liệu duy nhất (Unique Index)."),
            ("3", "task", "VARCHAR(16)", "", "", "No", "None", "Nhiệm vụ: 'stt' (nhận dạng giọng nói) hoặc 'nmt' (dịch máy)."),
            ("4", "source_type", "VARCHAR(16)", "", "", "No", "None", "Nguồn dữ liệu: qa_reviewed hoặc synthetic."),
            ("5", "source_langs", "TEXT", "", "", "No", "'[]'", "Mảng JSON danh sách các ngôn ngữ có trong tập dữ liệu."),
            ("6", "version", "VARCHAR(40)", "", "", "No", "None", "Số hiệu phiên bản ngữ nghĩa (ví dụ: 'v1.0.0')."),
            ("7", "status", "VARCHAR(16)", "", "", "No", "'draft'", "Trạng thái: draft, validated, frozen."),
            ("8", "sample_count", "INTEGER", "", "", "No", "0", "Tổng số lượng mẫu câu trong tập."),
            ("9", "duration_seconds", "FLOAT", "", "", "No", "0.0", "Tổng thời lượng âm thanh (với bài toán STT)."),
            ("10", "train_count", "INTEGER", "", "", "No", "0", "Số lượng mẫu trong tập huấn luyện (Train split)."),
            ("11", "validation_count", "INTEGER", "", "", "No", "0", "Số lượng mẫu trong tập kiểm định (Validation split)."),
            ("12", "test_count", "INTEGER", "", "", "No", "0", "Số lượng mẫu trong tập kiểm thử độc lập (Test split)."),
            ("13", "sha256", "VARCHAR(64)", "", "", "Yes", "None", "Mã băm SHA-256 bảo đảm tập dữ liệu bất biến không bị sửa đổi."),
            ("14", "size_bytes", "INTEGER", "", "", "No", "0", "Dung lượng tệp dữ liệu nén (bytes)."),
            ("15", "storage_uri", "VARCHAR(300)", "", "", "No", "None", "Đường dẫn lưu trữ tệp dữ liệu đóng gói trên ổ đĩa."),
            ("16", "created_by_user_id", "INTEGER", "", "users.id", "No", "None", "Khóa ngoại trỏ đến quản trị viên tạo tập dữ liệu."),
            ("17", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm tạo bản ghi."),
            ("18", "frozen_at", "DATETIME", "", "", "Yes", "None", "Thời điểm đóng băng khóa tập dữ liệu vĩnh viễn.")
        ]
    )

    # 13. training_jobs
    render_data_dictionary_table(
        doc,
        table_name="training_jobs",
        table_desc="Lưu trữ hàng đợi và tiến trình thực thi huấn luyện mô hình học sâu LoRA PEFT trên GPU.",
        columns=[
            ("1", "id", "VARCHAR(36)", "V", "", "No", "UUIDv4", "Khóa chính của tiến trình huấn luyện."),
            ("2", "task", "VARCHAR(16)", "", "", "No", "None", "Nhiệm vụ huấn luyện: 'stt' hoặc 'nmt'."),
            ("3", "dataset_id", "VARCHAR(36)", "", "training_datasets.id", "No", "None", "Khóa ngoại tham chiếu đến tập dữ liệu đầu vào."),
            ("4", "base_model", "VARCHAR(200)", "", "", "No", "None", "Tên mô hình gốc (ví dụ: facebook/nllb-200-distilled-600M)."),
            ("5", "output_version", "VARCHAR(80)", "", "", "No", "None", "Số hiệu phiên bản đầu ra duy nhất dự kiến sinh."),
            ("6", "method", "VARCHAR(24)", "", "", "No", "'lora'", "Phương pháp huấn luyện: lora, qlora, full."),
            ("7", "config_json", "TEXT", "", "", "No", "'{}'", "Cấu hình siêu tham số dạng JSON: {r, alpha, lr, batch_size...}."),
            ("8", "worker_id", "VARCHAR(100)", "", "", "Yes", "None", "Định danh GPU Worker đang nhận thực thi tiến trình."),
            ("9", "status", "VARCHAR(24)", "", "", "No", "'queued'", "Trạng thái: queued, running, completed, failed, cancelled."),
            ("10", "progress_percent", "FLOAT", "", "", "No", "0.0", "Tiến độ hoàn thành công việc từ 0.0% đến 100.0%."),
            ("11", "current_epoch", "FLOAT", "", "", "Yes", "None", "Chu kỳ huấn luyện hiện tại."),
            ("12", "current_step", "INTEGER", "", "", "Yes", "None", "Bước cập nhật trọng số hiện tại."),
            ("13", "total_steps", "INTEGER", "", "", "Yes", "None", "Tổng số bước dự kiến của toàn bộ quá trình huấn luyện."),
            ("14", "train_loss", "FLOAT", "", "", "Yes", "None", "Hàm mất mát trên tập huấn luyện mới nhất."),
            ("15", "validation_loss", "FLOAT", "", "", "Yes", "None", "Hàm mất mát trên tập kiểm định mới nhất."),
            ("16", "eta_seconds", "INTEGER", "", "", "Yes", "None", "Thời gian ước tính còn lại tính bằng giây."),
            ("17", "artifact_id", "VARCHAR(36)", "", "", "Yes", "None", "Mã artifact sinh ra sau khi hoàn thành."),
            ("18", "started_by_user_id", "INTEGER", "", "users.id", "No", "None", "Khóa ngoại trỏ đến người kích hoạt huấn luyện."),
            ("19", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm tạo việc vào hàng đợi."),
            ("20", "started_at", "DATETIME", "", "", "Yes", "None", "Thời điểm bắt đầu chạy GPU."),
            ("21", "finished_at", "DATETIME", "", "", "Yes", "None", "Thời điểm kết thúc.")
        ]
    )

    # 14. training_job_events
    render_data_dictionary_table(
        doc,
        table_name="training_job_events",
        table_desc="Nhật ký chi tiết từng bước huấn luyện phục vụ vẽ đồ thị loss và giám sát realtime.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của sự kiện huấn luyện."),
            ("2", "job_id", "VARCHAR(36)", "", "training_jobs.id", "No", "None", "Khóa ngoại tham chiếu tiến trình huấn luyện."),
            ("3", "level", "VARCHAR(16)", "", "", "No", "'info'", "Mức độ log: info, warning, error."),
            ("4", "event_type", "VARCHAR(32)", "", "", "No", "'log'", "Loại sự kiện: step_metric, epoch_metric, checkpoint."),
            ("5", "message", "VARCHAR(1000)", "", "", "No", "None", "Thông điệp mô tả sự kiện."),
            ("6", "metrics_json", "TEXT", "", "", "No", "'{}'", "Chỉ số tức thời dạng JSON: {loss, lr, gpu_mem_mb...}."),
            ("7", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm phát sinh sự kiện.")
        ]
    )

    # 15. model_artifacts
    render_data_dictionary_table(
        doc,
        table_name="model_artifacts",
        table_desc="Kho lưu trữ các gói mô hình AI thành phẩm đã xuất xưởng sau huấn luyện.",
        columns=[
            ("1", "id", "VARCHAR(36)", "V", "", "No", "UUIDv4", "Khóa chính của gói mô hình."),
            ("2", "component", "VARCHAR(16)", "", "", "No", "None", "Cấu phần: 'stt' hoặc 'nmt'."),
            ("3", "version", "VARCHAR(80)", "", "", "No", "None", "Phiên bản mô hình duy nhất (Unique Index)."),
            ("4", "base_model", "VARCHAR(200)", "", "", "No", "None", "Tên mô hình nền tảng gốc."),
            ("5", "dataset_id", "VARCHAR(36)", "", "training_datasets.id", "No", "None", "Khóa ngoại trỏ đến tập dữ liệu đã dùng để huấn luyện."),
            ("6", "job_id", "VARCHAR(36)", "", "training_jobs.id", "No", "None", "Khóa ngoại duy nhất trỏ đến tiến trình huấn luyện tương ứng."),
            ("7", "storage_uri", "VARCHAR(300)", "", "", "No", "None", "Đường dẫn thư mục chứa trọng số LoRA adapters."),
            ("8", "sha256", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 xác thực tính toàn vẹn gói mô hình."),
            ("9", "size_bytes", "INTEGER", "", "", "No", "None", "Dung lượng gói tệp trọng số (bytes)."),
            ("10", "status", "VARCHAR(24)", "", "", "No", "'candidate'", "Trạng thái: candidate, active, archived, rejected."),
            ("11", "metrics_json", "TEXT", "", "", "No", "'{}'", "Kết quả kiểm định độc lập dạng JSON: {bleu, chrf, wer...}."),
            ("12", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm xuất xưởng gói mô hình.")
        ]
    )

    # 16. model_deployments
    render_data_dictionary_table(
        doc,
        table_name="model_deployments",
        table_desc="Bảng điều khiển trạng thái định tuyến mô hình phục vụ suy luận thực tế (Canary Routing).",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính của cấu hình triển khai."),
            ("2", "component", "VARCHAR(32)", "", "", "No", "None", "Cấu phần AI triển khai (Unique Index): 'stt' hoặc 'nmt'."),
            ("3", "active_model", "VARCHAR(200)", "", "", "No", "None", "Tên hoặc ID của mô hình đang phục vụ chính thức."),
            ("4", "canary_model", "VARCHAR(200)", "", "", "Yes", "None", "Tên hoặc ID của mô hình ứng viên đang chạy thử nghiệm canary."),
            ("5", "canary_percent", "INTEGER", "", "", "No", "0", "Tỷ lệ % lưu lượng người dùng hướng vào mô hình canary (0-100)."),
            ("6", "previous_active_model", "VARCHAR(200)", "", "", "Yes", "None", "Mô hình phiên bản trước dùng cho tính năng Rollback 1-click."),
            ("7", "version", "INTEGER", "", "", "No", "1", "Số lần cập nhật cấu hình triển khai."),
            ("8", "updated_by_user_id", "INTEGER", "", "users.id", "Yes", "None", "Khóa ngoại trỏ đến quản trị cấp cao thực hiện cập nhật."),
            ("9", "updated_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm cập nhật cấu hình gần nhất.")
        ]
    )

    # 17. deployment_events
    render_data_dictionary_table(
        doc,
        table_name="deployment_events",
        table_desc="Lịch sử các đợt phát hành, điều chỉnh tỷ lệ canary, promote hoặc thu hồi rollback.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của sự kiện triển khai."),
            ("2", "component", "VARCHAR(16)", "", "", "No", "None", "Cấu phần AI: 'stt' hoặc 'nmt'."),
            ("3", "from_artifact", "VARCHAR(200)", "", "", "Yes", "None", "Phiên bản mô hình ban đầu."),
            ("4", "to_artifact", "VARCHAR(200)", "", "", "Yes", "None", "Phiên bản mô hình mới được áp dụng."),
            ("5", "strategy", "VARCHAR(24)", "", "", "No", "None", "Chiến lược triển khai: canary, promote_active, rollback."),
            ("6", "canary_percent", "INTEGER", "", "", "No", "0", "Tỷ lệ % canary áp dụng."),
            ("7", "status", "VARCHAR(24)", "", "", "No", "'pending_reload'", "Trạng thái: pending_reload, active, failed."),
            ("8", "requested_by_user_id", "INTEGER", "", "users.id", "No", "None", "Khóa ngoại trỏ đến người ra lệnh triển khai."),
            ("9", "created_at", "DATETIME", "", "", "No", "utcnow()", "Thời điểm gửi yêu cầu triển khai."),
            ("10", "completed_at", "DATETIME", "", "", "Yes", "None", "Thời điểm hoàn tất việc hoán đổi mô hình."),
            ("11", "failure_reason", "VARCHAR(500)", "", "", "Yes", "None", "Nguyên nhân thất bại nếu có sự cố.")
        ]
    )

    print("Section 3.4 completed.")

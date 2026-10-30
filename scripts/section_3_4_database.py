# -*- coding: utf-8 -*-
"""
Module providing Section 3.4: Thiết kế cơ sở dữ liệu (Database Design & Data Dictionary) for T-Lingua report.
Strictly formatted according to Phenikaa University thesis standards matching [DALN]2210.pdf.
Includes:
- Section 3.4.1: Sơ đồ cơ sở dữ liệu tổng thể T-Lingua (Overall ERD, Figure 3.28 + Table 3.21 summary)
- Section 3.4.2: Nhóm tài khoản, người dùng và phân quyền (Figure 3.29 + Data Dictionary Tables 3.22 - 3.25)
- Section 3.4.3: Nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry (Figure 3.30 + Data Dictionary Tables 3.26 - 3.28)
- Section 3.4.4: Nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA) (Figure 3.31 + Data Dictionary Tables 3.29 - 3.31)
- Section 3.4.5: Nhóm MLOps, dữ liệu và vòng đời mô hình (Figure 3.32 + Data Dictionary Tables 3.32 - 3.37)
- Section 3.4.6: Nhóm cấu hình và tham số hệ thống (Figure 3.33 + Data Dictionary Table 3.38)
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

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSDL_IMG_DIR = os.path.join(WORKSPACE_ROOT, "docs", "img", "csdl")

def add_erd_image(doc, img_filename, caption_text, width_inches=6.0):
    """Embeds an ERD diagram image from docs/img/csdl/ with standard thesis caption."""
    img_path = os.path.join(CSDL_IMG_DIR, img_filename)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inches))
    else:
        add_diagram_box(doc, caption_text, f"[Tệp hình ảnh chưa tồn tại: {img_filename}]")
    add_caption(doc, caption_text, is_table=False)

def render_data_dictionary_table(doc, table_num, table_name, table_desc, columns):
    """
    Renders standard Data Dictionary table for a database entity:
    [STT, Tên trường, Kiểu dữ liệu, PK, FK, Null, Mặc định, Mô tả ý nghĩa & Ràng buộc]
    """
    add_paragraph(doc, f"Mô tả nghiệp vụ bảng {table_name}: {table_desc}", italic=False, font_size=11, space_before=6, space_after=4)
    
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
    add_caption(doc, f"{table_num}: Từ điển dữ liệu bảng {table_name}")
    add_paragraph(doc, "", space_after=4)

def build_section_3_4(doc):
    """Generates Section 3.4: Cơ sở dữ liệu for T-Lingua report."""
    add_heading_2(doc, "3.4. Cơ sở dữ liệu")
    
    add_paragraph(
        doc,
        "Cơ sở dữ liệu của hệ thống T-Lingua được xây dựng dựa trên hệ quản trị cơ sở dữ liệu quan hệ (RDBMS), "
        "kết hợp kiến trúc Object-Relational Mapping (ORM) thông qua SQLAlchemy 2.0. Mô hình thiết kế cho phép hệ thống "
        "vận hành linh hoạt trên cả SQLite (môi trường thử nghiệm cục bộ, kiểm thử tự động, trạm di động) và PostgreSQL "
        "(môi trường triển khai đám mây doanh nghiệp với khả năng chịu tải cao và đồng thời đa luồng). "
        "Cấu trúc bảng được chuẩn hóa đạt mức chuẩn 3 (3NF), loại bỏ hoàn toàn dư thừa dữ liệu bất thường (Anomalies), "
        "đồng thời thiết lập các ràng buộc toàn vẹn khóa ngoại (Foreign Keys) nghiêm ngặt nhằm bảo toàn mối quan hệ thực thể."
    )
    add_paragraph(
        doc,
        "Toàn bộ mô hình dữ liệu T-Lingua được chia tách thành 5 phân nhóm chức năng độc lập nhưng liên kết chặt chẽ: "
        "(1) Nhóm tài khoản, người dùng và phân quyền; (2) Nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry; "
        "(3) Nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA); (4) Nhóm MLOps, dữ liệu và vòng đời mô hình; "
        "và (5) Nhóm cấu hình và tham số hệ thống. Cách phân tách này giúp đảm bảo tính module hóa cao, dễ dàng mở rộng và "
        "cô lập rủi ro trong các tác vụ tính toán học máy nặng trên GPU."
    )

    # =========================================================================
    # 3.4.1. Sơ đồ cơ sở dữ liệu tổng thể T-Lingua
    # =========================================================================
    add_heading_3(doc, "3.4.1. Sơ đồ cơ sở dữ liệu tổng thể T-Lingua")
    add_paragraph(
        doc,
        "Sơ đồ cơ sở dữ liệu tổng thể của hệ thống T-Lingua phản ánh toàn diện 17 thực thể dữ liệu nghiệp vụ và các liên kết "
        "Crow's Foot chuẩn mực giữa chúng. Mối quan hệ hạt nhân của hệ thống xoay quanh bảng 'users' (quản lý danh tính, phân quyền và kiểm toán), "
        "bảng 'translation_logs' (lưu vết từng câu dịch thực tế từ ứng dụng di động), bảng 'quality_reviews' (cầu nối phản hồi Human-in-the-Loop "
        "giữa chuyên gia ngôn ngữ và dữ liệu sản xuất) cùng chuỗi vòng đời học máy khép kín: "
        "'training_datasets' -> 'training_jobs' -> 'training_job_events' -> 'model_artifacts' -> 'model_deployments' -> 'deployment_events'."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_28_sodo_csdl_tong_the_t_lingua.png",
        caption_text="Hình 3.28: Sơ đồ cơ sở dữ liệu tổng thể hệ thống T-Lingua",
        width_inches=6.3
    )

    add_paragraph(
        doc,
        "Mô tả quan hệ tổng thể giữa các phân nhóm chức năng:\n"
        "• Nhóm Tài khoản & Bảo mật ('users', 'auth_sessions', 'api_keys', 'audit_logs'): Đóng vai trò kiểm soát truy cập và "
        "bảo mật toàn diện. Mỗi người dùng ('users') sở hữu nhiều phiên đăng nhập JWT ('auth_sessions'), được cấp phát nhiều khóa API tích hợp ('api_keys') "
        "và mọi hành vi thay đổi cấu hình hay thẩm định đều được ghi vết bất biến vào 'audit_logs'.\n"
        "• Nhóm Dịch thuật & Telemetry ('translation_logs', 'pipeline_metrics', 'audio_assets'): Khi người dùng gửi yêu cầu dịch giọng nói, "
        "mỗi lượt dịch tương ứng với một bản ghi 'translation_logs'. Lượt dịch này được đo kiểm chi tiết độ trễ từng vi chặng (VAD, STT, NMT, TTS) "
        "bởi bảng 'pipeline_metrics' (quan hệ 1-N) và liên kết với tệp âm thanh nguồn/đích trong 'audio_assets' (quan hệ 1-1).\n"
        "• Nhóm Bộ nhớ Dịch & QA ('translation_memory_entries', 'quality_reviews', 'training_audio_assets'): Các bản ghi câu dịch có nghi ngờ "
        "sẽ được đưa vào hàng đợi thẩm định 'quality_reviews' (quan hệ 1-1 với 'translation_logs'). Chuyên gia thẩm định ('users') sẽ gán nhãn lỗi MQM "
        "và hiệu chỉnh câu dịch chuẩn. Câu thoại có âm thanh chất lượng cao kèm đồng thuận bản quyền sẽ được chuyển vào 'training_audio_assets'. "
        "Đồng thời, kho thuật ngữ chuẩn hóa 'translation_memory_entries' được quản trị viên hiệu chỉnh để can thiệp trực tiếp trước suy luận.\n"
        "• Nhóm MLOps & Vòng đời Mô hình ('training_datasets', 'training_jobs', 'training_job_events', 'model_artifacts', 'model_deployments', 'deployment_events'): "
        "Các câu dịch đạt chuẩn từ QA sẽ được trích xuất và đóng băng vào 'training_datasets' (kèm mã băm SHA-256). Từ một tập dữ liệu đóng băng, "
        "quản trị viên có thể khởi tạo nhiều tiến trình huấn luyện thích ứng LoRA ('training_jobs'). Mỗi tiến trình sẽ phát sinh chuỗi sự kiện telemetry "
        "realtime trong 'training_job_events' và sau khi hoàn tất sẽ kết xuất gói trọng số thành phẩm 'model_artifacts'. Gói trọng số này được nạp vào "
        "phục vụ suy luận thông qua 'model_deployments', cho phép cấu hình lưu lượng Canary và ghi nhận lịch sử thăng cấp/rollback khẩn cấp vào 'deployment_events'.\n"
        "• Nhóm Cấu hình Hệ thống ('system_settings'): Lưu trữ động các tham số ngưỡng ngắt câu VAD, thời hạn token JWT, tỷ lệ chia tập dữ liệu. "
        "Mọi thao tác sửa đổi tham số đều sinh ra bản ghi kiểm toán trong 'audit_logs'."
    )

    # Summary Table 3.21
    add_paragraph(doc, "Bảng 3.21 tổng hợp danh mục 17 bảng trong cơ sở dữ liệu T-Lingua phân theo từng nhóm chức năng nghiệp vụ:")
    tbl_summary = doc.add_table(rows=0, cols=4)
    tbl_summary.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_summary)
    
    sum_headers = ["STT", "Tên bảng", "Phân nhóm chức năng", "Mô tả mục đích lưu trữ"]
    sum_widths = [Inches(0.5), Inches(2.2), Inches(1.8), Inches(2.7)]
    
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
        ("1", "users", "Tài khoản & Phân quyền", "Lưu trữ tài khoản người dùng, băm mật khẩu Argon2id, vai trò RBAC và bí mật TOTP MFA."),
        ("2", "auth_sessions", "Tài khoản & Phân quyền", "Quản lý phiên đăng nhập JWT, băm refresh token, thời hạn và trạng thái thu hồi."),
        ("3", "api_keys", "Tài khoản & Phân quyền", "Lưu trữ khóa API dành cho ứng dụng đối tác tích hợp, giới hạn hạn ngạch RPM."),
        ("4", "audit_logs", "Tài khoản & Phân quyền", "Nhật ký kiểm toán an ninh bất biến, ghi lại mọi thao tác quản trị và thay đổi cấu hình."),
        ("5", "translation_logs", "Dịch thuật & Đo kiểm", "Lưu trữ chi tiết các lượt dịch câu thoại, mã phiên, văn bản gốc, bản dịch và cờ lỗi."),
        ("6", "pipeline_metrics", "Dịch thuật & Đo kiểm", "Số liệu đo kiểm vi mô độ trễ từng chặng (VAD, STT, NMT, TTS, End-to-End) theo turn."),
        ("7", "audio_assets", "Dịch thuật & Đo kiểm", "Quản lý siêu dữ liệu các tệp âm thanh ghi âm mono 16kHz và âm thanh tổng hợp."),
        ("8", "translation_memory_entries", "Bộ nhớ Dịch & QA", "Kho từ vựng và cặp câu thuật ngữ chuẩn hóa (Glossary/TM) phục vụ can thiệp dịch."),
        ("9", "quality_reviews", "Bộ nhớ Dịch & QA", "Phiếu thẩm định của chuyên gia ngôn ngữ, đánh giá lỗi MQM, bản dịch sửa chuẩn."),
        ("10", "training_audio_assets", "Bộ nhớ Dịch & QA", "Đoạn âm thanh chuẩn hóa kèm văn bản nguồn phục vụ tập huấn luyện mô hình Whisper."),
        ("11", "training_datasets", "MLOps & Vòng đời", "Các bản chụp tập dữ liệu huấn luyện đóng băng (Frozen Datasets) kèm mã băm SHA-256."),
        ("12", "training_jobs", "MLOps & Vòng đời", "Quản lý hàng đợi và tiến trình huấn luyện mô hình học sâu LoRA PEFT trên GPU PyTorch."),
        ("13", "training_job_events", "MLOps & Vòng đời", "Nhật ký sự kiện chi tiết từng bước (step/epoch/loss/telemetry) của tiến trình huấn luyện."),
        ("14", "model_artifacts", "MLOps & Vòng đời", "Kho lưu trữ các gói trọng số mô hình AI thành phẩm (LoRA weights, adapter, metrics)."),
        ("15", "model_deployments", "MLOps & Vòng đời", "Bảng cấu hình định tuyến phục vụ suy luận thực tế (Active Model, Canary Model, %)."),
        ("16", "deployment_events", "MLOps & Vòng đời", "Lịch sử các đợt phát hành, điều chỉnh tỷ lệ canary, thăng cấp hoặc rollback khẩn cấp."),
        ("17", "system_settings", "Cấu hình Hệ thống", "Lưu trữ các tham số cấu hình động toàn hệ thống dưới dạng Key-Value có kiểm toán.")
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
    add_caption(doc, "Bảng 3.21: Danh sách tổng hợp các bảng trong cơ sở dữ liệu T-Lingua")

    # =========================================================================
    # 3.4.2. Nhóm tài khoản, người dùng và phân quyền
    # =========================================================================
    add_heading_3(doc, "3.4.2. Nhóm tài khoản, người dùng và phân quyền")
    add_paragraph(
        doc,
        "Nhóm bảng này đóng vai trò nền tảng trong việc xác thực danh tính, phân quyền người dùng (Role-Based Access Control - RBAC) "
        "và giám sát an ninh hệ thống. Bảng 'users' lưu trữ thông tin tài khoản cốt lõi, mật khẩu được băm an toàn bằng thuật toán "
        "Argon2id kết hợp chuỗi muối (salt) ngẫu nhiên, cùng bí mật TOTP (Time-based One-Time Password) phục vụ xác thực hai yếu tố (2FA/MFA). "
        "Mỗi phiên làm việc của người dùng sinh ra bản ghi 'auth_sessions' quản lý vòng đời refresh token JWT. "
        "Đối với các hệ thống bên thứ ba hoặc thiết bị đối tác tích hợp qua API, bảng 'api_keys' quản lý các khóa truy cập kèm chính sách hạn ngạch "
        "(Rate Limiting RPM). Đặc biệt, mọi hành động nhạy cảm như đăng nhập, đổi mật khẩu, thăng cấp mô hình hay sửa đổi cấu hình đều được ghi nhận bất biến "
        "vào bảng 'audit_logs' kèm địa chỉ IP và dấu vết thiết bị."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_29_nhom_tai_khoan_nguoi_dung_phan_quyen.png",
        caption_text="Hình 3.29: Sơ đồ CSDL nhóm tài khoản, người dùng và phân quyền",
        width_inches=5.8
    )

    add_paragraph(
        doc,
        "Dưới đây là từ điển dữ liệu chi tiết cấu trúc các trường, kiểu dữ liệu và ràng buộc của 4 bảng thuộc Nhóm Tài khoản & Phân quyền:"
    )

    # 1. users
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.22",
        table_name="users",
        table_desc="Bảng trung tâm lưu trữ thông tin tài khoản người dùng, băm mật khẩu, phân quyền và cấu hình xác thực đa yếu tố.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của tài khoản."),
            ("2", "username", "VARCHAR(64)", "", "", "No", "None", "Tên đăng nhập duy nhất (Unique Index), dùng xác thực."),
            ("3", "password_hash", "VARCHAR(255)", "", "", "No", "None", "Mật khẩu đã băm bằng thuật toán Argon2id kèm muối an toàn."),
            ("4", "role", "VARCHAR(32)", "", "", "Yes", "'employee'", "Vai trò hệ thống: superadmin, admin, employee, reviewer."),
            ("5", "full_name", "VARCHAR(128)", "", "", "Yes", "None", "Họ và tên hiển thị đầy đủ của người dùng."),
            ("6", "is_active", "BOOLEAN", "", "", "No", "True", "Cờ xác định trạng thái tài khoản khả dụng hay bị khóa."),
            ("7", "mfa_enabled", "BOOLEAN", "", "", "No", "False", "Trạng thái kích hoạt xác thực hai yếu tố TOTP MFA."),
            ("8", "mfa_secret", "VARCHAR(64)", "", "", "Yes", "None", "Chuỗi bí mật Base32 phục vụ sinh mã OTP theo chuẩn RFC 6238."),
            ("9", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm khởi tạo tài khoản trên hệ thống."),
            ("10", "updated_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm cập nhật thông tin hồ sơ gần nhất.")
        ]
    )

    # 2. auth_sessions
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.23",
        table_name="auth_sessions",
        table_desc="Quản lý phiên đăng nhập của người dùng, băm refresh token, theo dõi thời hạn và hỗ trợ thu hồi token từ xa.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của phiên đăng nhập."),
            ("2", "user_id", "INTEGER", "", "V (users)", "No", "None", "Khóa ngoại tham chiếu đến tài khoản người dùng tương ứng."),
            ("3", "refresh_token_hash", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 của Refresh Token bảo đảm an toàn cơ sở dữ liệu."),
            ("4", "expires_at", "TIMESTAMP", "", "", "No", "None", "Thời điểm hết hạn hiệu lực của phiên đăng nhập."),
            ("5", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm đăng nhập và tạo phiên làm việc."),
            ("6", "revoked_at", "TIMESTAMP", "", "", "Yes", "None", "Thời điểm phiên bị thu hồi (khi người dùng đăng xuất hoặc đổi mật khẩu).")
        ]
    )

    # 3. api_keys
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.24",
        table_name="api_keys",
        table_desc="Lưu trữ khóa API dành cho đối tác hoặc ứng dụng tích hợp bên ngoài, quota giới hạn RPM.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của bản ghi khóa API."),
            ("2", "name", "VARCHAR(128)", "", "", "No", "None", "Tên gợi nhớ mục đích sử dụng của khóa API."),
            ("3", "key_hash", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 của chuỗi khóa API (không lưu khóa gốc thô)."),
            ("4", "created_by", "INTEGER", "", "V (users)", "No", "None", "Khóa ngoại tham chiếu người dùng/quản trị viên tạo khóa."),
            ("5", "is_active", "BOOLEAN", "", "", "No", "True", "Cờ cho biết khóa API có đang được kích hoạt hay không."),
            ("6", "rate_limit_rpm", "INTEGER", "", "", "No", "60", "Hạn ngạch số lượng yêu cầu tối đa cho phép trong một phút (RPM)."),
            ("7", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm cấp phát khóa API."),
            ("8", "last_used_at", "TIMESTAMP", "", "", "Yes", "None", "Thời điểm gửi yêu cầu thành công gần nhất qua khóa API này.")
        ]
    )

    # 4. audit_logs
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.25",
        table_name="audit_logs",
        table_desc="Nhật ký kiểm toán an ninh bất biến, ghi lại mọi hành vi nhạy cảm của người dùng và quản trị viên.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của nhật ký kiểm toán."),
            ("2", "actor_user_id", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại tham chiếu tài khoản thực hiện thao tác (Null nếu hệ thống)."),
            ("3", "action", "VARCHAR(64)", "", "", "No", "None", "Tên hành vi: LOGIN, LOGOUT, CHANGE_PASSWORD, PROMOTE_CANARY, UPDATE_SETTING..."),
            ("4", "target_type", "VARCHAR(64)", "", "", "Yes", "None", "Loại đối tượng chịu tác động: user, dataset, job, model, setting."),
            ("5", "target_id", "VARCHAR(64)", "", "", "Yes", "None", "Mã định danh của đối tượng chịu tác động."),
            ("6", "detail_json", "TEXT", "", "", "Yes", "None", "Dữ liệu chi tiết sự kiện dưới định dạng JSON (trạng thái trước/sau)."),
            ("7", "created_at", "TIMESTAMP", "", "", "No", "now()", "Dấu thời gian bất biến ghi nhận hành động.")
        ]
    )

    # =========================================================================
    # 3.4.3. Nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry
    # =========================================================================
    add_heading_3(doc, "3.4.3. Nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry")
    add_paragraph(
        doc,
        "Nhóm bảng này chịu trách nhiệm lưu trữ toàn bộ dữ liệu giao dịch dịch thuật diễn ra trên hệ thống thời gian thực. "
        "Bảng 'translation_logs' là bảng lưu trữ trung tâm của mỗi câu thoại được xử lý, bao gồm mã phiên WebSocket, "
        "văn bản nhận dạng giọng nói từ Whisper (STT), bản dịch máy từ NLLB-200 (NMT), điểm số tin cậy và trạng thái cờ lỗi (is_flagged). "
        "Mỗi câu dịch được đo kiểm vi mô độ trễ bằng bảng 'pipeline_metrics' (quan hệ 1-N), ghi nhận chính xác thời gian tính toán của từng mắt xích "
        "(VAD cutoff, STT inference, NMT translation, TTS synthesis, Network transport và End-to-End latency). "
        "Các tệp âm thanh nguồn (PCM mono 16kHz) và âm thanh tổng hợp được quản lý qua bảng 'audio_assets' (quan hệ 1-1) "
        "với mã băm SHA-256 bảo đảm tính toàn vẹn dữ liệu âm học."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_30_nhom_dich_thuat_audio_telemetry.png",
        caption_text="Hình 3.30: Sơ đồ CSDL nhóm dịch thuật, tài sản âm thanh và đo kiểm Telemetry",
        width_inches=5.8
    )

    add_paragraph(
        doc,
        "Dưới đây là từ điển dữ liệu chi tiết của 3 bảng thuộc Nhóm Dịch thuật & Đo kiểm:"
    )

    # 5. translation_logs
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.26",
        table_name="translation_logs",
        table_desc="Lưu trữ lịch sử chi tiết các câu dịch giọng nói, mã phiên, văn bản gốc, bản dịch, điểm tin cậy và cờ lỗi.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của lượt dịch."),
            ("2", "session_id", "VARCHAR(64)", "", "", "No", "None", "Mã định danh phiên làm việc WebSocket kết nối hai chiều."),
            ("3", "user_id", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại người dùng thực hiện (Null nếu phiên khách vãng lai)."),
            ("4", "source_lang", "VARCHAR(16)", "", "", "No", "'vi'", "Mã ngôn ngữ câu nói đầu vào (vi, en, ko, ja, zh...)."),
            ("5", "target_lang", "VARCHAR(16)", "", "", "No", "'en'", "Mã ngôn ngữ kết quả dịch đích."),
            ("6", "source_text", "TEXT", "", "", "No", "None", "Văn bản nhận dạng từ giọng nói (Whisper STT output)."),
            ("7", "translated_text", "TEXT", "", "", "No", "None", "Văn bản đã được dịch máy (NLLB-200 NMT output)."),
            ("8", "stt_confidence", "FLOAT", "", "", "Yes", "None", "Độ tin cậy xác suất của mô hình nhận dạng âm thanh (0.0 đến 1.0)."),
            ("9", "latency_ms", "FLOAT", "", "", "Yes", "None", "Tổng thời gian xử lý toàn trình của câu dịch tính bằng mili-giây."),
            ("10", "is_flagged", "BOOLEAN", "", "", "No", "False", "Cờ đánh dấu câu dịch bị nghi ngờ có lỗi, chuyển sang luồng QA."),
            ("11", "flag_reason", "VARCHAR(255)", "", "", "Yes", "None", "Lý do người dùng gắn cờ báo lỗi câu dịch."),
            ("12", "audio_asset_id", "VARCHAR(128)", "", "V (audio_assets)", "Yes", "None", "Khóa ngoại liên kết tệp ghi âm giọng nói tương ứng."),
            ("13", "created_at", "TIMESTAMP", "", "", "No", "now()", "Dấu thời gian thời điểm ghi nhận lượt dịch.")
        ]
    )

    # 6. pipeline_metrics
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.27",
        table_name="pipeline_metrics",
        table_desc="Số liệu đo kiểm vi mô chi tiết độ trễ từng chặng (VAD, STT, NMT, TTS, End-to-End) theo từng turn dịch thoại.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của bản ghi đo kiểm vi mô."),
            ("2", "turn_id", "VARCHAR(64)", "", "", "No", "None", "Mã định danh lượt thoại duy nhất trong phiên dịch."),
            ("3", "vad_ms", "FLOAT", "", "", "Yes", "0.0", "Thời gian phát hiện giọng nói và phát hiện khoảng lặng VAD cutoff."),
            ("4", "stt_ms", "FLOAT", "", "", "Yes", "0.0", "Thời gian mô hình Whisper xử lý chuyển đổi âm thanh sang văn bản."),
            ("5", "translate_ms", "FLOAT", "", "", "Yes", "0.0", "Thời gian mô hình NLLB-200 dịch văn bản từ nguồn sang đích."),
            ("6", "tts_first_chunk_ms", "FLOAT", "", "", "Yes", "0.0", "Thời gian tổng hợp và phản hồi luồng âm thanh đầu tiên đến máy khách."),
            ("7", "tts_total_ms", "FLOAT", "", "", "Yes", "0.0", "Tổng thời gian tổng hợp hoàn thiện toàn bộ luồng âm thanh TTS."),
            ("8", "end_to_end_ms", "FLOAT", "", "", "Yes", "0.0", "Tổng thời gian xử lý toàn trình từ dứt tiếng nói đến khi phát loa."),
            ("9", "network_transport_ms", "FLOAT", "", "", "Yes", "0.0", "Thời gian truyền tải gói tin nhị phân qua WebSocket trên mạng."),
            ("10", "recorded_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm ghi nhận số liệu đo kiểm vào cơ sở dữ liệu.")
        ]
    )

    # 7. audio_assets
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.28",
        table_name="audio_assets",
        table_desc="Quản lý siêu dữ liệu các tệp âm thanh ghi âm mono 16kHz và âm thanh tổng hợp được lưu trữ trên hệ thống tệp.",
        columns=[
            ("1", "file_name", "VARCHAR(128)", "V", "", "No", "None", "Khóa chính định danh tên tệp âm thanh duy nhất."),
            ("2", "storage_path", "VARCHAR(255)", "", "", "No", "None", "Đường dẫn lưu trữ vật lý của tệp âm thanh trên ổ đĩa máy chủ."),
            ("3", "sample_rate", "INTEGER", "", "", "No", "16000", "Tần số lấy mẫu âm thanh chuẩn hóa (mặc định 16.000 Hz)."),
            ("4", "channels", "INTEGER", "", "", "No", "1", "Số kênh âm thanh (chuẩn 1 kênh Mono)."),
            ("5", "format", "VARCHAR(16)", "", "", "No", "'wav'", "Định dạng đóng gói âm thanh (WAV PCM 16-bit)."),
            ("6", "size_bytes", "INTEGER", "", "", "No", "None", "Kích thước tệp âm thanh tính bằng byte."),
            ("7", "duration_sec", "FLOAT", "", "", "Yes", "None", "Độ dài thời lượng âm thanh tính bằng giây."),
            ("8", "sha256", "VARCHAR(64)", "", "", "Yes", "None", "Mã băm SHA-256 bảo đảm tính toàn vẹn của tệp âm thanh."),
            ("9", "owner_id", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại người sở hữu tệp âm thanh."),
            ("10", "expires_at", "TIMESTAMP", "", "", "Yes", "None", "Thời hạn lưu giữ tệp âm thanh theo chính sách quyền riêng tư."),
            ("11", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm tạo và ghi tệp âm thanh vào hệ thống.")
        ]
    )

    # =========================================================================
    # 3.4.4. Nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)
    # =========================================================================
    add_heading_3(doc, "3.4.4. Nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)")
    add_paragraph(
        doc,
        "Nhóm bảng này hiện thực hóa cơ chế vòng lặp phản hồi người dùng (Human-in-the-Loop) và quản lý tri thức thuật ngữ chuyên ngành. "
        "Bảng 'quality_reviews' lưu trữ các phiếu thẩm định chất lượng bản dịch do chuyên gia ngôn ngữ thực hiện đối với các câu bị gắn cờ "
        "hoặc được chọn ngẫu nhiên. Phiếu thẩm định phân loại lỗi theo chuẩn công nghiệp MQM (Multidimensional Quality Metrics) "
        "bao gồm các chiều: Độ chính xác (Accuracy), Độ lưu loát (Fluency), Thuật ngữ (Terminology) và Phong cách (Style) "
        "cùng mức độ nghiêm trọng (Minor, Major, Critical). Các câu dịch sau khi được chuyên gia hiệu chỉnh câu chuẩn sẽ được "
        "trích xuất âm thanh vào bảng 'training_audio_assets' nếu có sự đồng thuận bản quyền làm mẫu huấn luyện ASR Whisper. "
        "Đồng thời, bảng 'translation_memory_entries' lưu trữ kho bộ nhớ dịch và từ điển thuật ngữ chuẩn hóa (Glossary/TM), "
        "cho phép quản trị viên can thiệp trực tiếp vào văn bản trước và sau dịch nhằm bảo đảm tính chính xác tuyệt đối của các thuật ngữ chuyên ngành."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_31_nhom_bo_nho_dich_qa.png",
        caption_text="Hình 3.31: Sơ đồ CSDL nhóm bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)",
        width_inches=5.8
    )

    add_paragraph(
        doc,
        "Dưới đây là từ điển dữ liệu chi tiết của 3 bảng thuộc Nhóm Bộ nhớ Dịch & Kiểm chuẩn QA:"
    )

    # 8. translation_memory_entries
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.29",
        table_name="translation_memory_entries",
        table_desc="Kho từ vựng và cặp câu chuẩn hóa (Glossary/TM) phục vụ can thiệp dịch thuật ngữ chuyên ngành chính xác.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của mục bộ nhớ dịch."),
            ("2", "source_lang", "VARCHAR(16)", "", "", "No", "None", "Mã ngôn ngữ nguồn của cặp thuật ngữ."),
            ("3", "target_lang", "VARCHAR(16)", "", "", "No", "None", "Mã ngôn ngữ đích tương ứng."),
            ("4", "source_term", "TEXT", "", "", "No", "None", "Cụm từ hoặc câu nguồn cần chuẩn hóa (có đánh chỉ mục tìm kiếm)."),
            ("5", "target_term", "TEXT", "", "", "No", "None", "Bản dịch thuật ngữ chuẩn được phê duyệt bắt buộc sử dụng."),
            ("6", "domain", "VARCHAR(64)", "", "", "No", "'general'", "Lĩnh vực chuyên môn áp dụng (medical, tech, legal, general)."),
            ("7", "is_active", "BOOLEAN", "", "", "No", "True", "Trạng thái áp dụng can thiệp thuật ngữ vào pipeline dịch."),
            ("8", "created_by", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại chuyên gia/quản trị viên tạo thuật ngữ."),
            ("9", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm tạo mục từ vựng trong bộ nhớ dịch."),
            ("10", "updated_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm cập nhật cặp thuật ngữ gần nhất.")
        ]
    )

    # 9. quality_reviews
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.30",
        table_name="quality_reviews",
        table_desc="Phiếu thẩm định của chuyên gia ngôn ngữ, đánh giá lỗi MQM, văn bản đã sửa và gắn nhãn tập huấn luyện.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của phiếu thẩm định QA."),
            ("2", "translation_log_id", "INTEGER", "", "V (trans_logs)", "No", "None", "Khóa ngoại tham chiếu câu dịch cần thẩm định (Unique)."),
            ("3", "reviewer_user_id", "INTEGER", "", "V (users)", "No", "None", "Khóa ngoại chuyên gia ngôn ngữ tiến hành đánh giá."),
            ("4", "review_status", "VARCHAR(32)", "", "", "No", "'PENDING'", "Trạng thái thẩm định: PENDING, APPROVED, REJECTED, EDITED."),
            ("5", "mqm_score", "FLOAT", "", "", "Yes", "None", "Điểm số chất lượng tính theo công thức trọng số lỗi chuẩn MQM."),
            ("6", "mqm_category", "VARCHAR(64)", "", "", "Yes", "None", "Phân loại lỗi chính: Accuracy, Fluency, Terminology, Style."),
            ("7", "severity", "VARCHAR(32)", "", "", "Yes", "None", "Mức độ nghiêm trọng của lỗi: Minor, Major, Critical."),
            ("8", "corrected_source_text", "TEXT", "", "", "Yes", "None", "Văn bản nguồn sau khi được chuyên gia hiệu chỉnh chính tả."),
            ("9", "corrected_trans_text", "TEXT", "", "", "Yes", "None", "Bản dịch chuẩn mực sau khi được chuyên gia trau chuốt."),
            ("10", "is_training_eligible", "BOOLEAN", "", "", "No", "False", "Cờ xác nhận dữ liệu đạt chuẩn đưa vào tập huấn luyện tiếp theo."),
            ("11", "feedback_comment", "TEXT", "", "", "Yes", "None", "Ghi chú nhận xét chuyên môn của người thẩm định."),
            ("12", "reviewed_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm hoàn tất việc thẩm định và chấm điểm.")
        ]
    )

    # 10. training_audio_assets
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.31",
        table_name="training_audio_assets",
        table_desc="Đoạn âm thanh chuẩn hóa kèm văn bản nguồn phục vụ tập huấn luyện thích ứng mô hình nhận dạng tiếng nói Whisper.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của tài sản âm thanh huấn luyện."),
            ("2", "translation_log_id", "INTEGER", "", "V (trans_logs)", "Yes", "None", "Khóa ngoại liên kết câu dịch gốc nếu trích xuất từ logs."),
            ("3", "file_name", "VARCHAR(128)", "", "", "No", "None", "Tên tệp âm thanh huấn luyện được lưu trữ trong thư mục dataset."),
            ("4", "source_audio_path", "VARCHAR(255)", "", "", "No", "None", "Đường dẫn tệp âm thanh chuẩn 16kHz Mono WAV."),
            ("5", "normalized_transcript", "TEXT", "", "", "No", "None", "Văn bản phát âm chuẩn hóa đã kiểm định tương ứng với tệp âm thanh."),
            ("6", "duration_sec", "FLOAT", "", "", "No", "None", "Thời lượng âm thanh tính bằng giây."),
            ("7", "sample_rate", "INTEGER", "", "", "No", "16000", "Tần số lấy mẫu âm thanh phục vụ huấn luyện (16.000 Hz)."),
            ("8", "snr_db", "FLOAT", "", "", "Yes", "None", "Tỷ số tín hiệu trên nhiễu (Signal-to-Noise Ratio) của đoạn âm thanh."),
            ("9", "consent_granted", "BOOLEAN", "", "", "No", "True", "Xác nhận đã có sự đồng thuận bản quyền dữ liệu của người dùng."),
            ("10", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm nhập đoạn âm thanh vào kho tài sản huấn luyện.")
        ]
    )

    # =========================================================================
    # 3.4.5. Nhóm MLOps, dữ liệu và vòng đời mô hình
    # =========================================================================
    add_heading_3(doc, "3.4.5. Nhóm MLOps, dữ liệu và vòng đời mô hình")
    add_paragraph(
        doc,
        "Nhóm bảng MLOps tạo thành chu trình phát triển, huấn luyện và phát hành mô hình học máy tự động (Continuous Training & Deployment). "
        "Bảng 'training_datasets' lưu trữ thông tin các phiên bản tập dữ liệu được 'đóng băng' (FROZEN), bao gồm số lượng mẫu, tỷ lệ phân chia "
        "Train/Val/Test và mã băm SHA-256 bảo đảm tính tái lập của thí nghiệm (Reproducibility). "
        "Mỗi đợt huấn luyện LoRA PEFT trên GPU PyTorch được quản lý bởi bảng 'training_jobs' với đầy đủ siêu tham số (Epoch, Batch size, Learning rate, LoRA rank). "
        "Trong suốt quá trình huấn luyện, bảng 'training_job_events' (quan hệ 1-N) ghi nhận liên tục từng bước tiến trình (step, loss, GPU memory) "
        "để phát luồng telemetry qua WebSocket lên bảng điều khiển quản trị. "
        "Khi hoàn tất, gói mô hình AI được đóng gói thành một bản ghi 'model_artifacts' kèm đường dẫn lưu trữ và các chỉ số đo lường (BLEU, chrF++). "
        "Mô hình thành phẩm được đưa vào bảng 'model_deployments' để phục vụ suy luận thực tế với cơ chế phân bổ lưu lượng Canary (ví dụ: 10% lưu lượng sang model mới). "
        "Cuối cùng, mọi thao tác thăng cấp toàn phần (Promote) hoặc khôi phục khẩn cấp (1-Click Rollback) đều được ghi nhận chi tiết vào 'deployment_events'."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_32_nhom_mlops_vong_doi_mo_hinh.png",
        caption_text="Hình 3.32: Sơ đồ CSDL nhóm MLOps, dữ liệu và vòng đời mô hình",
        width_inches=6.0
    )

    add_paragraph(
        doc,
        "Dưới đây là từ điển dữ liệu chi tiết của 6 bảng thuộc Nhóm MLOps & Vòng đời Mô hình:"
    )

    # 11. training_datasets
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.32",
        table_name="training_datasets",
        table_desc="Các bản chụp tập dữ liệu huấn luyện đóng băng (Frozen Datasets) kèm tỷ lệ chia tập và mã băm SHA-256.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của tập dữ liệu huấn luyện."),
            ("2", "name", "VARCHAR(128)", "", "", "No", "None", "Tên tập dữ liệu (ví dụ: T-Lingua-General-v1.0)."),
            ("3", "version", "VARCHAR(32)", "", "", "No", "None", "Mã phiên bản ngữ nghĩa (Semantic Versioning)."),
            ("4", "domain", "VARCHAR(64)", "", "", "No", "'general'", "Miền dữ liệu chuyên biệt (medical, tech, dialogue, general)."),
            ("5", "sample_count", "INTEGER", "", "", "No", "0", "Tổng số lượng mẫu câu (cặp câu song ngữ hoặc audio-text)."),
            ("6", "split_ratio", "VARCHAR(32)", "", "", "No", "'80/10/10'", "Tỷ lệ phân chia tập Train / Validation / Test."),
            ("7", "storage_path", "VARCHAR(255)", "", "", "No", "None", "Đường dẫn lưu trữ tệp dữ liệu đã đóng gói trên ổ đĩa máy chủ."),
            ("8", "sha256", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 bảo đảm tập dữ liệu bất biến không bị sửa đổi."),
            ("9", "is_frozen", "BOOLEAN", "", "", "No", "True", "Cờ đóng băng: ngăn chặn mọi hành vi thêm/bớt dữ liệu sau khi chốt."),
            ("10", "created_by", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại quản trị viên tạo tập dữ liệu."),
            ("11", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm tạo và đóng băng tập dữ liệu.")
        ]
    )

    # 12. training_jobs
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.33",
        table_name="training_jobs",
        table_desc="Quản lý hàng đợi và tiến trình huấn luyện mô hình học sâu LoRA PEFT trên GPU PyTorch.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của tiến trình huấn luyện."),
            ("2", "job_name", "VARCHAR(128)", "", "", "No", "None", "Tên gợi nhớ của tiến trình huấn luyện."),
            ("3", "dataset_id", "INTEGER", "", "V (datasets)", "No", "None", "Khóa ngoại tập dữ liệu đóng băng dùng để huấn luyện."),
            ("4", "base_model", "VARCHAR(128)", "", "", "No", "None", "Tên mô hình nền (facebook/nllb-200-distilled-600M hoặc openai/whisper-small)."),
            ("5", "epochs", "INTEGER", "", "", "No", "3", "Tổng số chu kỳ huấn luyện toàn bộ dữ liệu (epochs)."),
            ("6", "batch_size", "INTEGER", "", "", "No", "16", "Kích thước lô mẫu dữ liệu nạp vào GPU mỗi bước huấn luyện."),
            ("7", "learning_rate", "FLOAT", "", "", "No", "2e-4", "Tốc độ học khởi tạo của bộ tối ưu AdamW."),
            ("8", "lora_r", "INTEGER", "", "", "No", "16", "Hạng của ma trận thích ứng LoRA (Rank dimension)."),
            ("9", "lora_alpha", "INTEGER", "", "", "No", "32", "Hệ số tỷ lệ co giãn trọng số của LoRA (Scaling factor)."),
            ("10", "status", "VARCHAR(32)", "", "", "No", "'QUEUED'", "Trạng thái: QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED."),
            ("11", "current_epoch", "INTEGER", "", "", "No", "0", "Vòng lặp epoch hiện tại đang được thực thi trên GPU."),
            ("12", "current_step", "INTEGER", "", "", "No", "0", "Bước bước tối ưu hiện tại."),
            ("13", "total_steps", "INTEGER", "", "", "No", "0", "Tổng số bước tối ưu dự kiến của toàn bộ tiến trình."),
            ("14", "train_loss", "FLOAT", "", "", "Yes", "None", "Hàm mất mát huấn luyện ghi nhận ở bước gần nhất."),
            ("15", "val_loss", "FLOAT", "", "", "Yes", "None", "Hàm mất mát trên tập kiểm định validation."),
            ("16", "error_message", "TEXT", "", "", "Yes", "None", "Thông báo chi tiết nguyên nhân lỗi nếu tiến trình thất bại."),
            ("17", "started_at", "TIMESTAMP", "", "", "Yes", "None", "Thời điểm GPU bắt đầu cấp phát tài nguyên tính toán."),
            ("18", "finished_at", "TIMESTAMP", "", "", "Yes", "None", "Thời điểm kết thúc huấn luyện.")
        ]
    )

    # 13. training_job_events
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.34",
        table_name="training_job_events",
        table_desc="Nhật ký sự kiện chi tiết từng bước (step/epoch/loss/telemetry) của tiến trình huấn luyện phục vụ WebSocket dashboard.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của sự kiện tiến trình huấn luyện."),
            ("2", "job_id", "INTEGER", "", "V (jobs)", "No", "None", "Khóa ngoại tham chiếu tiến trình huấn luyện tương ứng."),
            ("3", "step", "INTEGER", "", "", "No", "None", "Chỉ số bước huấn luyện hiện tại (training step)."),
            ("4", "epoch", "FLOAT", "", "", "No", "None", "Chỉ số epoch tương ứng (có thể là số thập phân)."),
            ("5", "loss", "FLOAT", "", "", "Yes", "None", "Giá trị hàm mất mát loss tại bước này."),
            ("6", "learning_rate", "FLOAT", "", "", "Yes", "None", "Tốc độ học tức thời sau khi áp dụng Learning Rate Scheduler."),
            ("7", "gpu_memory_used_mb", "INTEGER", "", "", "Yes", "None", "Dung lượng bộ nhớ VRAM của GPU đang bị chiếm dụng (MB)."),
            ("8", "created_at", "TIMESTAMP", "", "", "No", "now()", "Dấu thời gian ghi nhận sự kiện phục vụ hiển thị đồ thị realtime.")
        ]
    )

    # 14. model_artifacts
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.35",
        table_name="model_artifacts",
        table_desc="Kho lưu trữ các gói mô hình AI thành phẩm (LoRA weights, adapter, metrics, checksum).",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của gói mô hình AI thành phẩm."),
            ("2", "model_name", "VARCHAR(128)", "", "", "No", "None", "Tên định danh gói mô hình (ví dụ: NLLB-ViEn-Medical-LoRA)."),
            ("3", "version", "VARCHAR(32)", "", "", "No", "None", "Phiên bản của mô hình."),
            ("4", "component", "VARCHAR(32)", "", "", "No", "'translation'", "Thành phần suy luận đảm nhiệm: 'translation', 'stt', 'tts'."),
            ("5", "job_id", "INTEGER", "", "V (jobs)", "Yes", "None", "Khóa ngoại tham chiếu tiến trình huấn luyện đã kết xuất gói mô hình."),
            ("6", "storage_path", "VARCHAR(255)", "", "", "No", "None", "Đường dẫn thư mục lưu trữ trọng số LoRA adapters và cấu hình trên ổ đĩa."),
            ("7", "sha256", "VARCHAR(64)", "", "", "No", "None", "Mã băm SHA-256 của toàn bộ gói trọng số bảo đảm toàn vẹn khi tải nạp."),
            ("8", "test_bleu", "FLOAT", "", "", "Yes", "None", "Điểm số chất lượng dịch BLEU đo trên tập Test độc lập."),
            ("9", "test_chrf", "FLOAT", "", "", "Yes", "None", "Điểm số chất lượng dịch chrF++ trên tập Test."),
            ("10", "is_active", "BOOLEAN", "", "", "No", "False", "Cờ cho biết gói mô hình có đang được tải nạp phục vụ hay không."),
            ("11", "created_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm hoàn tất đóng gói mô hình vào kho lưu trữ.")
        ]
    )

    # 15. model_deployments
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.36",
        table_name="model_deployments",
        table_desc="Bảng cấu hình định tuyến phục vụ suy luận thực tế (Active Model, Canary Model, Canary Percent).",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của bản ghi triển khai mô hình."),
            ("2", "component", "VARCHAR(32)", "", "", "No", "None", "Thành phần AI phục vụ: 'translation', 'stt', 'tts' (Unique)."),
            ("3", "active_model_id", "INTEGER", "", "V (artifacts)", "No", "None", "Khóa ngoại trỏ đến gói mô hình chính thức tiếp nhận phần lớn lưu lượng."),
            ("4", "canary_model_id", "INTEGER", "", "V (artifacts)", "Yes", "None", "Khóa ngoại trỏ đến gói mô hình thử nghiệm Canary."),
            ("5", "canary_percent", "INTEGER", "", "", "No", "0", "Tỷ lệ phần trăm lưu lượng ngẫu nhiên chuyển hướng sang mô hình Canary (0-100%)."),
            ("6", "is_enabled", "BOOLEAN", "", "", "No", "True", "Cờ bật/tắt toàn bộ dịch vụ suy luận của thành phần này."),
            ("7", "updated_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm điều chỉnh tỷ lệ canary hoặc chuyển đổi mô hình gần nhất.")
        ]
    )

    # 16. deployment_events
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.37",
        table_name="deployment_events",
        table_desc="Lịch sử các đợt phát hành, điều chỉnh tỷ lệ canary, thăng cấp lên Active hoặc thu hồi khẩn cấp 1-Click Rollback.",
        columns=[
            ("1", "id", "INTEGER", "V", "", "No", "Auto-inc", "Khóa chính tự tăng của sự kiện triển khai."),
            ("2", "deployment_id", "INTEGER", "", "V (deployments)", "No", "None", "Khóa ngoại tham chiếu bản ghi cấu hình triển khai tương ứng."),
            ("3", "event_type", "VARCHAR(32)", "", "", "No", "None", "Loại sự kiện: SET_CANARY, PROMOTE_ACTIVE, ROLLBACK, DISABLE."),
            ("4", "from_model_id", "INTEGER", "", "V (artifacts)", "Yes", "None", "Khóa ngoại mô hình bị thay thế hoặc giảm lưu lượng."),
            ("5", "to_model_id", "INTEGER", "", "V (artifacts)", "Yes", "None", "Khóa ngoại mô hình được thăng cấp hoặc nhận thêm lưu lượng."),
            ("6", "reason", "VARCHAR(255)", "", "", "Yes", "None", "Lý do quản trị viên thực hiện thao tác (ví dụ: 'Canary BLEU drop below 25')."),
            ("7", "actor_user_id", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại quản trị viên thực hiện thao tác triển khai/rollback."),
            ("8", "created_at", "TIMESTAMP", "", "", "No", "now()", "Dấu thời gian ghi nhận sự kiện vận hành.")
        ]
    )

    # =========================================================================
    # 3.4.6. Nhóm cấu hình và tham số hệ thống
    # =========================================================================
    add_heading_3(doc, "3.4.6. Nhóm cấu hình và tham số hệ thống")
    add_paragraph(
        doc,
        "Nhóm bảng này cho phép hệ thống vận hành linh hoạt và có khả năng tùy biến cao mà không cần biên dịch lại mã nguồn "
        "hoặc khởi động lại dịch vụ backend. Bảng 'system_settings' lưu trữ các tham số cấu hình động toàn hệ thống dưới dạng Key-Value "
        "kèm kiểu dữ liệu định nghĩa (STRING, INT, FLOAT, JSON, BOOLEAN). "
        "Các tham số quan trọng bao gồm: ngưỡng thời gian phát hiện khoảng lặng VAD Silence Cutoff (mặc định 500ms), thời hạn hiệu lực của access token JWT (60 phút), "
        "hạn ngạch quota cuộc gọi API mặc định (60 RPM), ngưỡng cảnh báo độ trễ mạng P99, và danh sách các cặp ngôn ngữ được phép phục vụ. "
        "Mọi thao tác cập nhật cấu hình đều được liên kết tự động với bảng 'audit_logs' để lưu vết truy cứu an ninh."
    )

    add_erd_image(
        doc,
        img_filename="hinh_3_33_nhom_cau_hinh_he_thong.png",
        caption_text="Hình 3.33: Sơ đồ CSDL nhóm cấu hình và tham số hệ thống",
        width_inches=5.2
    )

    add_paragraph(
        doc,
        "Dưới đây là từ điển dữ liệu chi tiết của bảng 'system_settings':"
    )

    # 17. system_settings
    render_data_dictionary_table(
        doc,
        table_num="Bảng 3.38",
        table_name="system_settings",
        table_desc="Lưu trữ các tham số cấu hình động toàn hệ thống dưới dạng Key-Value có phân loại kiểu và kiểm toán thay đổi.",
        columns=[
            ("1", "key", "VARCHAR(64)", "V", "", "No", "None", "Khóa định danh tham số duy nhất toàn hệ thống (Primary Key)."),
            ("2", "value", "TEXT", "", "", "No", "None", "Giá trị cấu hình hiện tại lưu dưới dạng chuỗi hoặc chuỗi JSON."),
            ("3", "data_type", "VARCHAR(32)", "", "", "No", "'STRING'", "Kiểu dữ liệu của giá trị tham số: STRING, INT, FLOAT, JSON, BOOLEAN."),
            ("4", "description", "VARCHAR(255)", "", "", "Yes", "None", "Mô tả ý nghĩa nghiệp vụ và tầm ảnh hưởng của tham số."),
            ("5", "is_public", "BOOLEAN", "", "", "No", "False", "Cờ cho phép ứng dụng máy khách (Mobile App) được đọc cấu hình công khai."),
            ("6", "updated_by", "INTEGER", "", "V (users)", "Yes", "None", "Khóa ngoại quản trị viên sửa đổi giá trị tham số gần nhất."),
            ("7", "updated_at", "TIMESTAMP", "", "", "No", "now()", "Thời điểm cập nhật giá trị tham số gần nhất.")
        ]
    )

    add_paragraph(
        doc,
        "Tổng kết Mục 3.4: Cơ sở dữ liệu của hệ thống T-Lingua gồm 17 bảng dữ liệu quan hệ được thiết kế chuẩn mực 3NF, "
        "đáp ứng đầy đủ các yêu cầu khắt khe về tính toàn vẹn dữ liệu, khả năng mở rộng phân tán, kiểm toán an ninh bất biến, "
        "và đồng hành cùng toàn bộ vòng đời huấn luyện - thẩm định - triển khai học sâu (MLOps). "
        "Đây là nền tảng dữ liệu vững chắc bảo đảm hệ thống vận hành liên tục, ổn định và có khả năng tự cải tiến chất lượng "
        "qua từng lượt tương tác của người dùng."
    )

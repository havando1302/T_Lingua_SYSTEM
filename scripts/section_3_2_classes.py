# -*- coding: utf-8 -*-
"""
Module providing Section 3.2: Mô hình lớp và đối tượng (Class & Object Model)
for the T-Lingua graduation thesis report.
Follows strictly the structure, styling, and pedagogical depth of [ĐALN]2210.pdf.
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

IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img"

def embed_diagram_figure(doc, img_filename, caption_text, width_inches=6.2):
    """Embeds an image from docs/img with center alignment and caption."""
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

def render_subsystem_summary_table(doc, classes_summary):
    """
    Renders the summary table of classes for a subsystem:
    Cột 1: Lớp | Cột 2: Vai trò
    Matches the standard table format in [ĐALN]2210.pdf.
    """
    add_paragraph(doc, "Các lớp chính gồm:", bold=True, font_size=11, space_before=4, space_after=2)
    tbl = doc.add_table(rows=0, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)
    
    hdr = tbl.add_row()
    headers = ["Lớp", "Vai trò"]
    widths = [Inches(2.2), Inches(4.3)]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, (cls_name, role_desc) in enumerate(classes_summary):
        row = tbl.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate([cls_name, role_desc]):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            if col_idx == 0:
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_paragraph(doc, "", space_after=4)

def render_class_table(doc, class_name, description, inheritance, attributes, methods, relationships=None):
    """
    Renders detailed class specification tables:
    - Class name & overview
    - Inheritance / Interfaces
    - Attributes table
    - Methods table
    - Relationships
    """
    add_paragraph(doc, f"Lớp: {class_name}", bold=True, font_size=12, space_before=6, space_after=2, color=PRIMARY_COLOR)
    add_paragraph(doc, f"Mô tả ý nghĩa: {description}", italic=False, font_size=11, space_after=3)
    if inheritance:
        add_paragraph(doc, f"Kế thừa / Giao diện: {inheritance}", bold=True, italic=True, font_size=10.5, space_after=3, color=SECONDARY_COLOR)
    
    # 1. Attributes Table
    add_paragraph(doc, f"Bảng thuộc tính của lớp {class_name}:", bold=True, font_size=10.5, space_before=3, space_after=2)
    tbl_attr = doc.add_table(rows=0, cols=4)
    tbl_attr.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_attr)
    
    hdr = tbl_attr.add_row()
    headers = ["Tên thuộc tính", "Kiểu dữ liệu", "Phạm vi", "Mô tả ý nghĩa"]
    widths = [Inches(1.8), Inches(1.2), Inches(0.9), Inches(2.6)]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, attr in enumerate(attributes):
        row = tbl_attr.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.add_run(attr[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            if col_idx == 0:
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif col_idx in (1, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # 2. Methods Table
    add_paragraph(doc, f"Bảng phương thức của lớp {class_name}:", bold=True, font_size=10.5, space_before=4, space_after=2)
    tbl_meth = doc.add_table(rows=0, cols=4)
    tbl_meth.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_meth)
    
    hdr_m = tbl_meth.add_row()
    m_headers = ["Tên phương thức", "Tham số đầu vào", "Kiểu trả về", "Chức năng & Mô tả"]
    m_widths = [Inches(1.8), Inches(1.5), Inches(1.1), Inches(2.1)]
    for i, h in enumerate(m_headers):
        cell = hdr_m.cells[i]
        cell.width = m_widths[i]
        set_cell_background(cell, SUBHEADER_BG_HEX)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, meth in enumerate(methods):
        row = tbl_meth.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = m_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.add_run(meth[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            if col_idx == 0:
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif col_idx in (1, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Relationships if provided
    if relationships:
        add_paragraph(doc, f"Mối quan hệ của lớp {class_name}:", bold=True, font_size=10.5, space_before=3, space_after=2)
        for rel in relationships:
            add_bullet(doc, rel, prefix="- ")
    add_paragraph(doc, "", space_after=3)

def render_key_relationships(doc, relationships_list):
    """Renders the 'Quan hệ chính:' bullet section for a subsystem."""
    add_paragraph(doc, "Quan hệ chính:", bold=True, font_size=11, space_before=4, space_after=2)
    for rel in relationships_list:
        add_bullet(doc, rel, prefix="● ")
    add_paragraph(doc, "", space_after=4)

def build_section_3_2(doc):
    """
    Builds the complete Section 3.2: Mô hình lớp và đối tượng
    strictly matching [ĐALN]2210.pdf.
    """
    # Heading 2
    add_heading_2(doc, "3.2 Mô hình lớp và đối tượng")
    
    # ---------------------------------------------------------
    # 3.2.1 Mục đích của mô hình lớp
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.1 Mục đích của mô hình lớp")
    add_paragraph(
        doc,
        "Mô hình lớp (UML Class Diagram) được sử dụng nhằm mô tả cấu trúc tĩnh của hệ thống T-Lingua, "
        "thể hiện các lớp đối tượng, thuộc tính, phương thức và mối quan hệ giữa các lớp trong quá trình "
        "xây dựng nền tảng dịch thuật giọng nói song phương thời gian thực tích hợp trí tuệ nhân tạo (AI/ML). "
        "Thông qua mô hình lớp, các thành phần của hệ thống được xác định và tổ chức rõ ràng, tạo cơ sở vững chắc "
        "cho việc thiết kế, hiện thực hóa mã nguồn, kiểm thử và bảo trì lâu dài."
    )
    add_paragraph(
        doc,
        "Do đặc thù của một hệ thống xử lý giọng nói và dịch máy đa ngôn ngữ có yêu cầu khắt khe về độ trễ cực thấp "
        "(dưới 1500ms cho toàn bộ chu trình End-to-End), mô hình lớp của T-Lingua được xây dựng kết hợp giữa hai tầng: "
        "tầng các thực thể bền vững (Persistence Domain Entities) lưu trữ dữ liệu an toàn trong cơ sở dữ liệu quan hệ, "
        "và tầng các lớp hướng đối tượng xử lý luồng bộ nhớ trong (In-Memory Realtime Actor Pipeline) chạy bất đồng bộ "
        "trên nền tảng Python FastAPI / Asyncio. Toàn bộ kiến trúc tuân thủ nghiêm ngặt các nguyên lý SOLID, đảm bảo tính đóng gói cao, "
        "khả năng mở rộng độc lập và cách ly lỗi hoàn hảo giữa các thành phần."
    )
    add_paragraph(
        doc,
        "Hệ thống T-Lingua được tổ chức thành 5 phân hệ lớp chính với các trách nhiệm rành mạch:"
    )
    add_bullet(doc, "Phân hệ Xác thực và Kiểm soát Truy cập (Auth & Access Control Subsystem): Chịu trách nhiệm quản lý tài khoản người dùng, kiểm soát phân quyền theo vai trò (Role-Based Access Control - RBAC), quản lý token phiên (JWT), khóa tích hợp API Keys và nhật ký kiểm toán an ninh bất biến (Audit Log).")
    add_bullet(doc, "Phân hệ Dịch thuật và Đo kiểm Pipeline (Translation & Telemetry Subsystem): Lưu trữ chi tiết từng lượt dịch hoàn chỉnh (TranslationLog), tài sản âm thanh nhị phân liên quan (AudioAsset) và các chỉ số đo kiểm hiệu năng vi mô chặng (PipelineMetric).")
    add_bullet(doc, "Phân hệ Bộ nhớ Dịch và Kiểm soát Chất lượng (Translation Memory & QA Subsystem): Quản lý kho thuật ngữ chuyên ngành (TranslationMemoryEntry) và quy trình gán cờ, thẩm định lỗi ngôn ngữ của chuyên gia theo chuẩn MQM (QualityReview).")
    add_bullet(doc, "Phân hệ MLOps và Vòng đời Mô hình (Training Center & Model Lifecycle Subsystem): Quản lý tập dữ liệu đóng băng (TrainingDataset), tiến trình huấn luyện lặp PEFT LoRA (TrainingJob), sự kiện huấn luyện (TrainingJobEvent), kho lưu trữ artifact (ModelArtifact) và cấu hình phân luồng Canary/Rollback (ModelDeployment).")
    add_bullet(doc, "Phân hệ Xử lý Luồng Thời gian thực và Tác tử (Realtime Stream & Actor Pipeline Subsystem): Chứa các đối tượng bộ nhớ trong: RealtimeSession, SessionActor điều phối trạng thái, WebRtcVadStream lọc âm, PipelineQueues và Singleton ModelManager điều phối tài nguyên GPU/VRAM.")

    # Embed Figure 3.1: Package Architecture
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_1_kien_truc_phan_tang_cac_goi_lop.png",
        caption_text="Hình 3.1: Kiến trúc phân tầng các gói lớp trong hệ thống T-Lingua",
        width_inches=6.2
    )

    # ---------------------------------------------------------
    # 3.2.2 Mô hình lớp tổng quát
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.2 Mô hình lớp tổng quát")
    add_paragraph(
        doc,
        "Mô hình lớp tổng quát của hệ thống T-Lingua thể hiện cấu trúc và mối quan hệ giữa các lớp chính trong toàn bộ "
        "hệ thống dịch thuật giọng nói thời gian thực tích hợp trí tuệ nhân tạo. Mô hình bao gồm các nhóm lớp phục vụ "
        "quản lý người dùng, phiên làm việc, khóa API, nhật ký kiểm toán, lượt dịch thoại, tài sản âm thanh, số liệu đo kiểm vi mô, "
        "bộ nhớ dịch, thẩm định chất lượng MQM, đóng băng tập dữ liệu, tiến trình huấn luyện LoRA, kho mô hình thành phẩm, "
        "phân luồng lưu lượng Canary và các tác tử xử lý luồng thời gian thực. "
        "Mô hình tạo nền tảng vững chắc cho việc thiết kế, triển khai và mở rộng quy mô hệ thống."
    )

    # Embed Figure 3.2: Global Class Diagram
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_2_mo_hinh_lop_tong_quat.png",
        caption_text="Hình 3.2: Sơ đồ mô hình lớp tổng quát hệ thống T-Lingua",
        width_inches=6.3
    )

    # Global Summary Table (Matching Table 155 in [DALN]2210)
    render_subsystem_summary_table(doc, [
        ("User", "Quản lý tài khoản đăng nhập, thông tin xác thực, phân quyền theo vai trò (RBAC) và bảo mật hai yếu tố TOTP MFA."),
        ("AuthSession", "Lưu trữ phiên làm việc đã xác thực, token JWT, thời hạn hiệu lực và phòng chống chiếm đoạt phiên."),
        ("ApiKey", "Quản lý khóa truy cập API dành cho các ứng dụng ngoại vi và đối tác, tích hợp giới hạn tốc độ gọi (Rate Limiting)."),
        ("AuditLog", "Bản ghi kiểm toán an ninh bất biến (Append-only Trail), ghi vết các thao tác can thiệp hệ thống nhạy cảm."),
        ("TranslationLog", "Lưu trữ thông tin nghiệp vụ của một lượt dịch hoàn chỉnh (turn), văn bản nguồn STT, văn bản đích NMT và điểm tin cậy."),
        ("AudioAsset", "Quản lý tệp âm thanh nhị phân 16kHz mono (WAV/WebM) lưu trữ trong kho dữ liệu phục vụ nghe lại và huấn luyện."),
        ("PipelineMetric", "Đo kiểm chi tiết độ trễ vi mô của từng mắt xích trong chuỗi xử lý (VAD -> STT -> NMT -> TTS) cho mỗi lượt dịch."),
        ("TranslationMemoryEntry", "Quản lý các cặp thuật ngữ chuyên ngành và câu mẫu song ngữ can thiệp dịch chuẩn xác."),
        ("QualityReview", "Quản lý quy trình thẩm định và gán nhãn kiểm soát chất lượng câu dịch theo khung Multidimensional Quality Metrics (MQM)."),
        ("TrainingDataset", "Quản lý phiên bản tập dữ liệu đóng băng (Frozen Dataset) phục vụ huấn luyện lặp có thể tái lập."),
        ("TrainingJob", "Quản lý vòng đời thực thi tiến trình huấn luyện mô hình học sâu LoRA PEFT (Whisper, NLLB-200)."),
        ("ModelArtifact", "Đại diện cho gói mô hình AI thành phẩm đã kiểm định, lưu trữ trọng số LoRA adapters và cấu hình suy luận."),
        ("ModelDeployment", "Quản lý trạng thái phân luồng lưu lượng suy luận AI (Active/Canary) và cơ chế Rollback an toàn 1-click."),
        ("RealtimeSession", "Đại diện cho phiên làm việc WebSocket hai chiều đang hoạt động giữa máy khách và máy chủ backend."),
        ("SessionActor", "Tác tử điều phối độc lập trạng thái phiên hội thoại theo mô hình Actor Model, ngăn chặn tranh chấp dữ liệu qua khóa Mutex."),
        ("WebRtcVadStream", "Bộ đệm và phân tích tín hiệu âm thanh liên tục bằng thuật toán WebRTC VAD 30ms/16kHz mono phát hiện ranh giới tiếng nói."),
        ("ModelManager", "Bộ nạp và quản lý tài nguyên mô hình AI trong bộ nhớ GPU/CPU theo mẫu thiết kế Singleton (Singleton Resource Manager).")
    ])

    # ---------------------------------------------------------
    # 3.2.3 Mô hình lớp tài khoản, người dùng và phân quyền
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.3 Mô hình lớp tài khoản, người dùng và phân quyền")
    add_paragraph(
        doc,
        "Nhóm lớp tài khoản, người dùng và phân quyền quản lý thông tin tài khoản, xác thực người dùng, phân quyền "
        "truy cập theo vai trò (Role-Based Access Control - RBAC), phiên đăng nhập bảo mật, khóa tích hợp API Keys và "
        "nhật ký kiểm toán an ninh. Ngoài ra, nhóm lớp còn hỗ trợ cơ chế xác thực hai lớp (TOTP MFA theo chuẩn RFC 6238), "
        "khóa tài khoản tự động khi đăng nhập sai quá số lần quy định, và thuật toán giới hạn tần suất gọi API "
        "(Token Bucket / Sliding Window Rate Limiting) bảo vệ hệ thống trước tấn công từ chối dịch vụ."
    )
    add_paragraph(
        doc,
        "Mỗi người dùng (User) được gán một vai trò cụ thể (ADMIN, AUDITOR, REVIEWER, TRANSLATOR). Người dùng có thể khởi tạo "
        "nhiều phiên làm việc (AuthSession) trên các thiết bị khác nhau, sở hữu nhiều khóa API (ApiKey) để tích hợp ứng dụng, "
        "và mọi hành vi thay đổi cấu hình quan trọng đều được ghi nhận tự động vào bảng nhật ký an ninh bất biến (AuditLog)."
    )

    # Embed Figure 3.3: Auth & Security
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_3_mo_hinh_lop_tai_khoan_bao_mat.png",
        caption_text="Hình 3.3: Mô hình lớp tài khoản, người dùng, phân quyền và bảo mật",
        width_inches=6.2
    )

    # Summary table for Auth
    render_subsystem_summary_table(doc, [
        ("User", "Quản lý thông tin đăng nhập, mật khẩu băm Argon2/Bcrypt, vai trò RBAC, trạng thái kích hoạt và bảo mật hai lớp TOTP."),
        ("AuthSession", "Lưu trữ phiên làm việc đã xác thực, token JWT, địa chỉ IP, User-Agent và kiểm soát thu hồi phiên."),
        ("ApiKey", "Quản lý khóa truy cập API dành cho đối tác tích hợp, tiền tố hiển thị và hạn ngạch Requests Per Minute."),
        ("AuditLog", "Bản ghi kiểm toán an ninh bất biến, lưu vết hành động, tài nguyên bị tác động, trạng thái trước/sau và IP người dùng."),
        ("RoleEnum", "Xác định các vai trò người dùng trong hệ thống gồm ADMIN, AUDITOR, REVIEWER, TRANSLATOR.")
    ])

    # Detailed tables for Auth
    render_class_table(
        doc,
        class_name="User",
        description="Đại diện cho thực thể người dùng và tài khoản quản trị hệ thống. Quản lý thông tin định danh, cơ chế băm mật khẩu bảo mật cao (Argon2id/Bcrypt), cấu hình phân quyền theo vai trò (Role-Based Access Control - RBAC) và bảo mật hai lớp (TOTP MFA).",
        inheritance="SQLAlchemy DeclarativeBase (ORM Mapping)",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID định danh duy nhất người dùng."),
            ("username", "String(64)", "Public", "Tên đăng nhập hệ thống, là duy nhất (unique), không rỗng."),
            ("email", "String(128)", "Public", "Địa chỉ hòm thư điện tử dùng để nhận cảnh báo và phục hồi tài khoản."),
            ("hashed_password", "String(255)", "Private", "Chuỗi mật khẩu đã được băm bảo mật kèm muối (Salt) bằng Argon2id/Bcrypt."),
            ("role", "Enum(RoleEnum)", "Public", "Vai trò người dùng: ADMIN, AUDITOR, REVIEWER, TRANSLATOR."),
            ("is_active", "Boolean", "Public", "Cờ trạng thái kích hoạt tài khoản. Nếu False, tài khoản bị khóa đăng nhập."),
            ("is_verified", "Boolean", "Public", "Trạng thái đã xác minh danh tính qua email hoặc quản trị viên phê duyệt."),
            ("mfa_enabled", "Boolean", "Public", "Cờ kích hoạt xác thực hai yếu tố (TOTP) bắt buộc đối với vai trò quản trị."),
            ("mfa_secret", "String(64)", "Private", "Mã khóa bí mật dùng để sinh mã số TOTP 6 chữ số theo chuẩn RFC 6238."),
            ("failed_login_attempts", "Integer", "Private", "Số lần đăng nhập sai liên tiếp. Vượt quá 5 lần sẽ tạm khóa 15 phút."),
            ("locked_until", "DateTime", "Private", "Mốc thời gian tài khoản bị tạm khóa đến thời điểm chỉ định."),
            ("created_at", "DateTime", "Public", "Thời điểm bản ghi tài khoản được khởi tạo trong hệ thống."),
            ("updated_at", "DateTime", "Public", "Thời điểm cập nhật thông tin tài khoản gần nhất.")
        ],
        methods=[
            ("verify_password(raw_pwd)", "raw_pwd: str", "bool", "Băm mật khẩu thô và so sánh với hashed_password theo hàm thời gian không đổi (constant-time) tránh Timing Attack."),
            ("set_password(new_pwd)", "new_pwd: str", "None", "Sinh muối mới và thực hiện băm mật khẩu an toàn, ghi đè vào hashed_password."),
            ("verify_totp(totp_code)", "totp_code: str", "bool", "Kiểm tra tính hợp lệ của mã 6 chữ số dựa trên mfa_secret và đồng hồ hệ thống theo chuẩn TOTP."),
            ("has_permission(perm)", "perm: Permission", "bool", "Kiểm tra vai trò hiện tại của User có quyền thực thi thao tác nghiệp vụ perm hay không."),
            ("record_failed_login()", "None", "None", "Tăng biến đếm failed_login_attempts. Nếu >= 5, thiết lập locked_until = now() + 15 phút."),
            ("reset_failed_logins()", "None", "None", "Đặt lại failed_login_attempts về 0 sau khi người dùng đăng nhập thành công.")
        ]
    )

    render_class_table(
        doc,
        class_name="AuthSession",
        description="Quản lý vòng đời phiên làm việc đã xác thực của người dùng. Lưu trữ định danh JWT, thời gian hiệu lực và thông tin nguồn gốc yêu cầu (IP, User-Agent) phục vụ phòng chống đánh cắp phiên (Session Hijacking).",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của phiên làm việc."),
            ("user_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến User.id."),
            ("token_hash", "String(255)", "Private", "Mã băm SHA-256 của Refresh Token nhằm tra cứu nhanh và bảo vệ token trong DB."),
            ("ip_address", "String(45)", "Public", "Địa chỉ IPv4/IPv6 của thiết bị khách khi thiết lập phiên kết nối."),
            ("user_agent", "String(255)", "Public", "Chuỗi nhận dạng trình duyệt/ứng dụng của thiết bị khách."),
            ("expires_at", "DateTime", "Public", "Thời điểm phiên hết hạn bắt buộc người dùng thực hiện tái xác thực."),
            ("is_revoked", "Boolean", "Public", "Cờ thu hồi phiên (ví dụ khi người dùng đăng xuất hoặc bị quản trị hủy phiên)."),
            ("created_at", "DateTime", "Public", "Thời điểm khởi tạo phiên làm việc.")
        ],
        methods=[
            ("is_valid()", "None", "bool", "Kiểm tra phiên còn hạn (expires_at > now()) và chưa bị thu hồi (is_revoked == False)."),
            ("revoke()", "None", "None", "Đánh dấu is_revoked = True và vô hiệu hóa phiên ngay lập tức.")
        ]
    )

    render_class_table(
        doc,
        class_name="ApiKey",
        description="Quản lý khóa truy cập API dành cho các ứng dụng ngoại vi hoặc đối tác tích hợp vào nền tảng T-Lingua. Đi kèm cơ chế phân mức giới hạn tốc độ gọi (Rate Limiting).",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của API Key."),
            ("user_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến tài khoản chủ sở hữu User.id."),
            ("key_prefix", "String(8)", "Public", "Tiền tố hiển thị công khai (ví dụ: 'tlg_live_') giúp nhận dạng khóa."),
            ("key_hash", "String(255)", "Private", "Băm mật mã của toàn bộ API Key để so khớp an toàn."),
            ("label", "String(100)", "Public", "Nhãn gợi nhớ do người dùng đặt (ví dụ: 'Khóa Tích Hợp Kiosk Sân Bay')."),
            ("rate_limit_rpm", "Integer", "Public", "Số lượt gọi tối đa cho phép trong 1 phút (Requests Per Minute)."),
            ("is_active", "Boolean", "Public", "Trạng thái hoạt động của khóa API."),
            ("expires_at", "DateTime", "Public", "Hạn sử dụng của khóa (hoặc NULL nếu vô thời hạn)."),
            ("created_at", "DateTime", "Public", "Thời điểm tạo khóa.")
        ],
        methods=[
            ("verify_key(raw_key)", "raw_key: str", "bool", "Kiểm tra chuỗi API key gửi lên qua header X-API-KEY có khớp với key_hash không."),
            ("check_rate_limit(redis)", "redis: RedisClient", "bool", "Sử dụng thuật toán Token Bucket / Sliding Window trên Redis để xác định có vượt hạn ngạch RPM hay không.")
        ]
    )

    render_class_table(
        doc,
        class_name="AuditLog",
        description="Bản ghi kiểm toán an ninh bất biến (Append-only Immutable Trail). Lưu trữ toàn bộ các thao tác can thiệp hệ thống nhạy cảm phục vụ công tác thanh tra và bảo đảm an toàn thông tin.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của bản ghi nhật ký kiểm toán."),
            ("actor_id", "String(36)", "Public", "Định danh người thực hiện (User.id hoặc 'SYSTEM')."),
            ("action", "String(64)", "Public", "Mã hành động: USER_LOGIN, CANARY_PROMOTE, GLOSSARY_UPDATE, QA_APPROVE..."),
            ("resource_type", "String(64)", "Public", "Loại tài nguyên bị tác động: User, ModelDeployment, TrainingJob..."),
            ("resource_id", "String(64)", "Public", "Khóa định danh của tài nguyên bị thay đổi."),
            ("payload_before", "JSON", "Private", "Dữ liệu trạng thái của tài nguyên trước khi thay đổi."),
            ("payload_after", "JSON", "Private", "Dữ liệu trạng thái mới sau khi thao tác thay đổi hoàn tất."),
            ("ip_address", "String(45)", "Public", "Địa chỉ IP thực hiện yêu cầu can thiệp."),
            ("timestamp", "DateTime", "Public", "Thời gian ghi nhận bản ghi với độ chính xác mili-giây.")
        ],
        methods=[
            ("log_event(actor, action, res_type, res_id, before, after, ip)", "Đa tham số", "AuditLog", "Phương thức tĩnh (factory method) khởi tạo bản ghi kiểm toán mới và đẩy vào luồng ghi bất đồng bộ.")
        ]
    )

    # Relationships bullet list (Matching [DALN]2210 style)
    render_key_relationships(doc, [
        "Một User có thể sở hữu nhiều AuthSession (Quan hệ 1-N, Cascade Delete khi hủy tài khoản).",
        "Một User có thể sở hữu nhiều ApiKey phục vụ các ứng dụng tích hợp ngoại vi (Quan hệ 1-N).",
        "Một User có thể phát sinh nhiều bản ghi kiểm toán AuditLog trong suốt quá trình thao tác (Quan hệ 1-N).",
        "Một User được xác định bởi một vai trò duy nhất thông qua RoleEnum (Quan hệ 1-1).",
        "Một User có vai trò REVIEWER có thể tham gia thẩm định nhiều bản ghi QualityReview trong phân hệ kiểm soát chất lượng."
    ])

    # ---------------------------------------------------------
    # 3.2.4 Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.4 Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry")
    add_paragraph(
        doc,
        "Nhóm lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry quản lý toàn bộ vòng đời của các lượt nói dịch "
        "(turns) trong hệ thống T-Lingua. Trong nhóm này, TranslationLog đóng vai trò là lớp trung tâm, liên kết văn bản "
        "nhận dạng giọng nói (STT), văn bản dịch máy (NMT), độ tin cậy mô hình, tệp âm thanh nhị phân gốc (AudioAsset) "
        "và các chỉ số đo kiểm hiệu năng vi mô chặng (PipelineMetric)."
    )
    add_paragraph(
        doc,
        "AudioAsset lưu trữ tệp âm thanh 16kHz mono (WAV/WebM) phục vụ nghe lại và trích xuất dữ liệu huấn luyện giọng nói. "
        "PipelineMetric ghi nhận chi tiết độ trễ của từng mắt xích: thời gian WebRTC VAD phát hiện tiếng nói (vad_ms), "
        "thời gian nhận dạng Whisper (stt_ms), thời gian dịch máy NLLB-200 (nmt_ms), thời gian tổng hợp giọng đọc MMS VITS (tts_ms) "
        "và tổng thời gian trễ trọn gói (e2e_ms), cho phép giám sát nghiêm ngặt cam kết chất lượng dịch vụ (SLA < 1500ms)."
    )

    # Embed Figure 3.4: Translation & Telemetry
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_4_mo_hinh_lop_dich_thuat_telemetry.png",
        caption_text="Hình 3.4: Mô hình lớp dịch thuật, tài sản âm thanh và đo kiểm Telemetry",
        width_inches=6.2
    )

    # Summary table for Translation & Telemetry
    render_subsystem_summary_table(doc, [
        ("TranslationLog", "Lưu trữ thông tin chi tiết một lượt dịch hoàn chỉnh: phiên, ngôn ngữ nguồn/đích, văn bản STT, văn bản NMT và cờ báo lỗi."),
        ("AudioAsset", "Quản lý tệp âm thanh nhị phân gốc trên hệ thống tệp lưu trữ: đường dẫn, dung lượng, thời lượng, tần số lấy mẫu và định dạng."),
        ("PipelineMetric", "Lưu trữ số liệu đo kiểm độ trễ vi mô của từng mắt xích xử lý AI (VAD, STT, NMT, TTS, E2E) và phiên bản mô hình phục vụ.")
    ])

    # Detailed tables
    render_class_table(
        doc,
        class_name="TranslationLog",
        description="Thực thể trung tâm lưu trữ thông tin nghiệp vụ của một lượt dịch hoàn chỉnh (turn). Kết nối văn bản nguồn từ STT, văn bản đích từ NMT, điểm tin cậy và các chỉ số đo kiểm chất lượng.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của lượt dịch."),
            ("session_id", "String(36)", "Public", "Mã định danh phiên hội thoại WebSocket hoặc REST."),
            ("turn_index", "Integer", "Public", "Số thứ tự lượt nói trong phiên hội thoại song phương."),
            ("source_lang", "String(10)", "Public", "Mã ngôn ngữ nguồn (ví dụ: 'vie_Latn', 'eng_Latn', 'zh_Hans')."),
            ("target_lang", "String(10)", "Public", "Mã ngôn ngữ đích cần dịch sang."),
            ("source_text", "Text", "Public", "Văn bản nhận dạng giọng nói tự động thu được từ Whisper."),
            ("target_text", "Text", "Public", "Văn bản dịch máy do mô hình NLLB-200 sinh ra."),
            ("confidence_score", "Float", "Public", "Độ tin cậy của mô hình nhận dạng giọng nói (0.0 đến 1.0)."),
            ("is_flagged", "Boolean", "Public", "Cờ đánh dấu lượt dịch có vấn đề chất lượng do người dùng hoặc Reviewer gắn."),
            ("created_at", "DateTime", "Public", "Thời điểm phát sinh lượt dịch.")
        ],
        methods=[
            ("flag_issue(reason)", "reason: str", "None", "Gắn cờ is_flagged = True và tự động tạo một phiếu QualityReview mới trong hàng đợi kiểm chuẩn."),
            ("to_dict()", "None", "dict", "Chuyển đổi dữ liệu bản ghi thành đối tượng JSON chuẩn hóa phục vụ hiển thị trên Admin Dashboard và Mobile History.")
        ]
    )

    render_class_table(
        doc,
        class_name="AudioAsset",
        description="Đại diện cho tệp âm thanh nhị phân được lưu trữ an toàn trong kho lưu trữ cục bộ hoặc Object Storage, phục vụ nghe lại và trích xuất dữ liệu huấn luyện giọng nói.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của tài sản âm thanh."),
            ("translation_log_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến TranslationLog.id."),
            ("file_path", "String(500)", "Public", "Đường dẫn tuyệt đối hoặc định danh URI trỏ đến tệp WAV/WebM trên ổ đĩa."),
            ("file_size_bytes", "Integer", "Public", "Kích thước dung lượng của tệp âm thanh (bytes)."),
            ("duration_ms", "Integer", "Public", "Thời lượng âm thanh tính bằng mili-giây."),
            ("sample_rate", "Integer", "Public", "Tần số lấy mẫu âm thanh (mặc định 16000 Hz theo chuẩn AI)."),
            ("channels", "Integer", "Public", "Số kênh âm thanh (1: Mono, 2: Stereo). Chuẩn xử lý là Mono 1 kênh."),
            ("format", "String(10)", "Public", "Định dạng đóng gói tệp: 'wav', 'webm', 'ogg'."),
            ("created_at", "DateTime", "Public", "Thời điểm tệp âm thanh được lưu trữ hoàn tất.")
        ],
        methods=[
            ("get_audio_bytes()", "None", "bytes", "Đọc luồng byte nhị phân của tệp âm thanh từ hệ thống tệp lưu trữ."),
            ("delete_physical_file()", "None", "bool", "Xóa tệp vật lý trên ổ đĩa khi bản ghi hết hạn hoặc bị xóa theo chính sách bảo mật.")
        ]
    )

    render_class_table(
        doc,
        class_name="PipelineMetric",
        description="Lưu trữ số liệu đo kiểm chi tiết về độ trễ vi mô của từng mắt xích trong chuỗi xử lý Pipeline (VAD -> STT -> NMT -> TTS) cho mỗi lượt dịch.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của chỉ số đo kiểm."),
            ("translation_log_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến TranslationLog.id."),
            ("vad_latency_ms", "Float", "Public", "Thời gian phát hiện và cắt đoạn tiếng nói của WebRTC VAD (ms)."),
            ("stt_latency_ms", "Float", "Public", "Thời gian nhận dạng âm thanh thành văn bản của Whisper (ms)."),
            ("nmt_latency_ms", "Float", "Public", "Thời gian dịch máy ngôn ngữ nguồn -> đích của NLLB-200 (ms)."),
            ("tts_latency_ms", "Float", "Public", "Thời gian tổng hợp âm thanh giọng đọc của MMS VITS (ms)."),
            ("e2e_latency_ms", "Float", "Public", "Tổng thời gian trễ trọn gói từ lúc dứt câu đến khi phát âm thanh (ms)."),
            ("model_version_stt", "String(50)", "Public", "Phiên bản mô hình STT đang phục vụ lúc đo kiểm."),
            ("model_version_nmt", "String(50)", "Public", "Phiên bản mô hình NMT đang phục vụ lúc đo kiểm."),
            ("created_at", "DateTime", "Public", "Thời điểm thu thập số liệu.")
        ],
        methods=[
            ("calculate_e2e()", "None", "float", "Tính toán tổng e2e_latency_ms = vad_ms + stt_ms + nmt_ms + tts_ms và kiểm tra ngưỡng cảnh báo SLA (< 1500ms).")
        ]
    )

    # Relationships
    render_key_relationships(doc, [
        "Một TranslationLog liên kết với duy nhất một AudioAsset chứa tệp âm thanh gốc (Quan hệ 1-1).",
        "Một TranslationLog sở hữu một hoặc nhiều bản ghi PipelineMetric đo kiểm các chặng suy luận (Quan hệ 1-N).",
        "Một TranslationLog có thể phát sinh tối đa một bản ghi QualityReview khi bị gắn cờ báo lỗi (Quan hệ 1-0..1)."
    ])

    # ---------------------------------------------------------
    # 3.2.5 Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.5 Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng")
    add_paragraph(
        doc,
        "Nhóm lớp này quản lý các cặp thuật ngữ chuyên ngành (Translation Memory / Glossary) và quy trình thẩm định, "
        "gán nhãn chất lượng bản dịch có sự tham gia của con người (Human-in-the-loop Quality Assurance). "
        "TranslationMemoryEntry cho phép can thiệp tiền xử lý và hậu xử lý dịch máy, đảm bảo các thuật ngữ chuyên ngành "
        "(Du lịch, Y tế, Pháp lý, Công nghệ) luôn được dịch chuẩn xác theo đúng từ điển quy chuẩn của tổ chức."
    )
    add_paragraph(
        doc,
        "QualityReview quản lý phiếu thẩm định lỗi ngôn ngữ đối với các câu dịch bị người dùng hoặc hệ thống gắn cờ. "
        "Chuyên gia thẩm định sẽ chấm điểm theo khung Multidimensional Quality Metrics (MQM), phân loại danh mục lỗi "
        "(Accuracy, Fluency, Terminology, Hallucination), nhập câu dịch đã hiệu chỉnh (corrected_text) và phê duyệt "
        "để tự động xuất sang tập dữ liệu huấn luyện (TrainingDataset) phục vụ các vòng lặp cải tiến mô hình AI tiếp theo."
    )

    # Embed Figure 3.5: TM & QA
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_5_mo_hinh_lop_bo_nho_dich_qa.png",
        caption_text="Hình 3.5: Mô hình lớp bộ nhớ dịch và kiểm chuẩn chất lượng (TM & QA)",
        width_inches=6.2
    )

    # Summary table for TM & QA
    render_subsystem_summary_table(doc, [
        ("TranslationMemoryEntry", "Quản lý cặp thuật ngữ hoặc câu mẫu song ngữ: nguồn, đích, lĩnh vực, tần suất so khớp và trạng thái áp dụng."),
        ("QualityReview", "Quản lý phiếu thẩm định chất lượng câu dịch: điểm MQM, nhóm lỗi, mức độ nghiêm trọng, văn bản sửa đổi và trạng thái duyệt."),
        ("ReviewStatus", "Định nghĩa các trạng thái thẩm định: PENDING, APPROVED, REJECTED, SENT_TO_DATASET."),
        ("ErrorCategory", "Phân loại các nhóm lỗi ngôn ngữ: ACCURACY, FLUENCY, TERMINOLOGY, HALLUCINATION.")
    ])

    # Detailed tables
    render_class_table(
        doc,
        class_name="TranslationMemoryEntry",
        description="Đại diện cho một cặp thuật ngữ hoặc câu mẫu trong Bộ nhớ dịch / Thuật ngữ chuyên ngành (Glossary / Translation Memory). Can thiệp tiền/hậu xử lý dịch để ép chuẩn từ chuyên ngành.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của mục từ điển thuật ngữ."),
            ("source_text", "String(500)", "Public", "Cụm từ hoặc câu chuẩn trong ngôn ngữ nguồn."),
            ("target_text", "String(500)", "Public", "Nghĩa dịch chuẩn bắt buộc trong ngôn ngữ đích."),
            ("source_lang", "String(10)", "Public", "Mã ngôn ngữ nguồn."),
            ("target_lang", "String(10)", "Public", "Mã ngôn ngữ đích."),
            ("domain", "String(50)", "Public", "Lĩnh vực chuyên môn: 'General', 'Medical', 'Tourism', 'Technology'..."),
            ("match_count", "Integer", "Public", "Số lần cặp thuật ngữ này được khớp và áp dụng thành công trong thực tế."),
            ("is_active", "Boolean", "Public", "Cờ cho phép sử dụng mục từ này trong quy trình dịch tự động."),
            ("created_by", "String(36)", "Public", "Khóa ngoại tham chiếu User.id của người tạo mục từ.")
        ],
        methods=[
            ("increment_match()", "None", "None", "Tăng biến đếm match_count khi bộ máy dịch áp dụng cụm từ này."),
            ("normalize_text()", "None", "None", "Chuẩn hóa khoảng trắng, chữ hoa/thường để tối ưu tốc độ so khớp chuỗi.")
        ]
    )

    render_class_table(
        doc,
        class_name="QualityReview",
        description="Quản lý quy trình thẩm định và gán nhãn kiểm soát chất lượng (Human-in-the-loop QA) đối với các câu dịch bị cảnh báo hoặc gắn cờ.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của phiếu thẩm định QA."),
            ("translation_log_id", "String(36)", "Public", "Khóa ngoại tham chiếu TranslationLog.id cần thẩm định."),
            ("reviewer_id", "String(36)", "Public", "Khóa ngoại tham chiếu User.id của chuyên gia thực hiện duyệt."),
            ("mqm_score", "Float", "Public", "Điểm số chất lượng theo khung Multidimensional Quality Metrics (0.0 đến 100.0)."),
            ("error_category", "Enum(ErrorCategory)", "Public", "Nhóm lỗi: ACCURACY, FLUENCY, TERMINOLOGY, HALLUCINATION."),
            ("severity", "String(20)", "Public", "Mức độ nghiêm trọng: 'Minor', 'Major', 'Critical'."),
            ("corrected_text", "Text", "Public", "Văn bản đã được chuyên gia sửa lại cho chuẩn xác."),
            ("feedback_note", "Text", "Public", "Ghi chú giải thích chi tiết của chuyên gia."),
            ("status", "Enum(ReviewStatus)", "Public", "Trạng thái: PENDING, APPROVED, REJECTED, SENT_TO_DATASET."),
            ("reviewed_at", "DateTime", "Public", "Thời điểm chuyên gia hoàn thành đánh giá.")
        ],
        methods=[
            ("approve_and_export(dataset, split)", "dataset: TrainingDataset, split: str", "bool", "Phê duyệt câu dịch đã sửa và tự động đẩy vào tập dữ liệu huấn luyện (TrainingDataset) với nhãn split (train/val/test)."),
            ("reject(reason)", "reason: str", "None", "Bác bỏ cờ báo lỗi nếu câu dịch gốc thực tế không có vấn đề sai sót.")
        ]
    )

    # Relationships
    render_key_relationships(doc, [
        "Một QualityReview thuộc về duy nhất một bản ghi TranslationLog (Quan hệ 1-1).",
        "Một QualityReview được thẩm định bởi một User có vai trò REVIEWER (Quan hệ N-1).",
        "Các câu dịch được phê duyệt từ QualityReview có thể được tổng hợp và xuất sang một hoặc nhiều TrainingDataset (Quan hệ N-N logic).",
        "Một TranslationMemoryEntry được khởi tạo và quản lý bởi một User có thẩm quyền (Quan hệ N-1)."
    ])

    # ---------------------------------------------------------
    # 3.2.6 Mô hình lớp MLOps, huấn luyện và vòng đời mô hình
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.6 Mô hình lớp MLOps, huấn luyện và vòng đời mô hình")
    add_paragraph(
        doc,
        "Nhóm lớp MLOps và vòng đời mô hình quản lý toàn bộ quy trình kỹ thuật học máy khép kín: từ đóng băng dữ liệu "
        "huấn luyện, thực thi tiến trình fine-tuning LoRA, đóng gói xuất xưởng mô hình thành phẩm, đến triển khai phục vụ "
        "thực tế với cơ chế phân luồng Canary Deployment và phục hồi tức thì (1-click Rollback)."
    )
    add_paragraph(
        doc,
        "TrainingDataset đại diện cho tập dữ liệu đóng băng bất biến có mã kiểm tra SHA-256. TrainingJob quản lý tiến trình "
        "chạy GPU huấn luyện bộ điều hợp LoRA PEFT (cho Whisper hoặc NLLB-200), phát sinh các sự kiện TrainingJobEvent "
        "ghi vết loss và learning rate theo thời gian thực. Khi hoàn thành đạt chuẩn, kết quả được đóng gói thành ModelArtifact. "
        "Lớp ModelDeployment quản lý trạng thái định tuyến luồng suy luận phục vụ thực tế (Serving Routing State), "
        "cho phép điều tiết tỷ lệ phần trăm lưu lượng hướng vào mô hình thử nghiệm (Canary Model) trước khi thăng hạng "
        "làm mô hình chính thức (Active Model) hoặc khôi phục phiên bản trước (Previous Model)."
    )

    # Embed Figure 3.6: MLOps & Model Lifecycle
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_6_mo_hinh_lop_mlops_vong_doi_mo_hinh.png",
        caption_text="Hình 3.6: Mô hình lớp MLOps, huấn luyện và vòng đời mô hình",
        width_inches=6.3
    )

    # Summary table for MLOps
    render_subsystem_summary_table(doc, [
        ("TrainingDataset", "Quản lý phiên bản tập dữ liệu đóng băng: số lượng mẫu, tỷ lệ phân chia train/val/test, mã băm SHA-256 và cờ đóng băng."),
        ("TrainingJob", "Quản lý tiến trình huấn luyện mô hình học sâu LoRA PEFT: tham số LoRA (r, alpha), learning rate, epochs, trạng thái và điểm BLEU."),
        ("TrainingJobEvent", "Bản ghi sự kiện tiến độ huấn luyện tức thời: epoch, step, train_loss, val_loss và thời điểm ghi nhận."),
        ("ModelArtifact", "Gói mô hình AI thành phẩm: đường dẫn lưu trữ trọng số adapter, dung lượng, mã băm SHA-256, điểm test BLEU/chrF++ và trạng thái."),
        ("ModelDeployment", "Quản lý cấu hình phân luồng suy luận AI thực tế: active_model_id, canary_model_id, tỷ lệ canary_percent và hỗ trợ rollback tức thì.")
    ])

    # Detailed tables
    render_class_table(
        doc,
        class_name="TrainingDataset",
        description="Đại diện cho một phiên bản tập dữ liệu đóng băng (Frozen Dataset Version) phục vụ huấn luyện tinh chỉnh mô hình AI có thể tái lập.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của phiên bản tập dữ liệu."),
            ("version", "String(20)", "Public", "Số hiệu phiên bản ngữ nghĩa (Semantic Versioning), ví dụ: 'v1.0.0'."),
            ("description", "String(255)", "Public", "Mô tả nguồn gốc và mục tiêu của tập dữ liệu huấn luyện."),
            ("sample_count", "Integer", "Public", "Tổng số lượng mẫu câu (cặp song ngữ hoặc âm thanh) có trong tập."),
            ("split_ratio", "String(20)", "Public", "Tỷ lệ phân chia tập Train / Validation / Test (ví dụ: '80:10:10')."),
            ("file_uri", "String(500)", "Public", "Đường dẫn lưu trữ tệp dữ liệu đã nén hoặc file parquet/jsonl."),
            ("checksum_sha256", "String(64)", "Public", "Mã băm SHA-256 xác thực tính toàn vẹn và bất biến của dữ liệu."),
            ("is_frozen", "Boolean", "Public", "Cờ đóng băng. Khi True, nghiêm cấm mọi thao tác thêm/sửa/xóa mẫu."),
            ("created_at", "DateTime", "Public", "Thời điểm tạo tập dữ liệu.")
        ],
        methods=[
            ("freeze()", "None", "None", "Tính toán mã băm checksum_sha256 và khóa tập dữ liệu vĩnh viễn (is_frozen = True)."),
            ("get_splits()", "None", "tuple", "Nạp dữ liệu và phân tách thành 3 tập dữ liệu con train_data, val_data, test_data.")
        ]
    )

    render_class_table(
        doc,
        class_name="TrainingJob",
        description="Quản lý vòng đời thực thi của một tiến trình huấn luyện mô hình học sâu (Deep Learning Training Job) sử dụng kỹ thuật tham số hiệu quả PEFT LoRA.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của tiến trình huấn luyện."),
            ("dataset_id", "String(36)", "Public", "Khóa ngoại tham chiếu TrainingDataset.id làm dữ liệu đầu vào."),
            ("model_component", "String(20)", "Public", "Cấu phần huấn luyện: 'STT' (Whisper) hoặc 'NMT' (NLLB-200)."),
            ("base_model_name", "String(100)", "Public", "Tên mô hình nền tảng gốc: 'facebook/nllb-200-distilled-600M' hoặc 'openai/whisper-small'."),
            ("lora_r", "Integer", "Public", "Hạng ma trận (Rank) của bộ điều hợp LoRA (ví dụ: 16 hoặc 32)."),
            ("lora_alpha", "Integer", "Public", "Hệ số co giãn alpha trong thuật toán LoRA (ví dụ: 32)."),
            ("learning_rate", "Float", "Public", "Tốc độ học khởi tạo của bộ tối ưu AdamW (ví dụ: 2e-4)."),
            ("batch_size", "Integer", "Public", "Kích thước gói dữ liệu huấn luyện mỗi bước tính toán."),
            ("epochs", "Integer", "Public", "Tổng số chu kỳ duyệt toàn bộ dữ liệu (Epochs)."),
            ("status", "Enum(JobStatus)", "Public", "Trạng thái: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED."),
            ("progress_percent", "Float", "Public", "Tiến độ hoàn thành công việc hiện tại (0.0 đến 100.0%)."),
            ("current_epoch", "Integer", "Public", "Chu kỳ huấn luyện đang thực hiện."),
            ("current_step", "Integer", "Public", "Bước tối ưu hóa trọng số hiện tại."),
            ("train_loss", "Float", "Public", "Giá trị hàm mất mát trên tập huấn luyện mới nhất."),
            ("val_loss", "Float", "Public", "Giá trị hàm mất mát trên tập kiểm định mới nhất."),
            ("bleu_score", "Float", "Public", "Điểm số BLEU đánh giá trên tập kiểm thử độc lập sau huấn luyện."),
            ("error_message", "Text", "Public", "Nội dung thông báo lỗi chi tiết nếu tiến trình gặp sự cố dừng bất thường."),
            ("started_at", "DateTime", "Public", "Thời điểm bắt đầu chạy GPU."),
            ("finished_at", "DateTime", "Public", "Thời điểm kết thúc toàn bộ tiến trình.")
        ],
        methods=[
            ("start()", "None", "None", "Khởi tạo môi trường ảo, nạp GPU và kích hoạt luồng huấn luyện nền."),
            ("update_progress(step, loss, lr)", "Đa tham số", "None", "Cập nhật tiến độ tức thời và phát sinh bản ghi TrainingJobEvent."),
            ("complete(artifact)", "artifact: ModelArtifact", "None", "Đánh dấu trạng thái COMPLETED và lưu trữ liên kết tới artifact đã xuất."),
            ("cancel()", "None", "None", "Gửi tín hiệu ngắt SIGTERM tới tiến trình PyTorch nền và giải phóng VRAM.")
        ]
    )

    render_class_table(
        doc,
        class_name="ModelArtifact",
        description="Đại diện cho gói mô hình AI thành phẩm (Model Package) đã được huấn luyện, nén và kiểm thử đạt chuẩn kỹ thuật, sẵn sàng triển khai phục vụ.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của gói mô hình thành phẩm."),
            ("job_id", "String(36)", "Public", "Khóa ngoại tham chiếu TrainingJob.id đã sinh ra mô hình này."),
            ("component", "String(20)", "Public", "Cấu phần AI: 'STT' hoặc 'NMT'."),
            ("artifact_uri", "String(500)", "Public", "Đường dẫn lưu trữ tệp trọng số LoRA adapters và cấu hình mô hình."),
            ("file_size_bytes", "Integer", "Public", "Dung lượng gói trọng số đã đóng gói (bytes)."),
            ("sha256_hash", "String(64)", "Public", "Mã băm kiểm tra tính toàn vẹn của gói tệp trọng số."),
            ("test_bleu", "Float", "Public", "Điểm BLEU kiểm định độc lập."),
            ("test_chrf", "Float", "Public", "Điểm chrF++ kiểm định độc lập."),
            ("status", "Enum(ArtifactStatus)", "Public", "Trạng thái: CANDIDATE, ACTIVE, ARCHIVED, REJECTED."),
            ("created_at", "DateTime", "Public", "Thời điểm xuất xưởng gói mô hình.")
        ],
        methods=[
            ("verify_checksum()", "None", "bool", "Xác thực mã băm tệp trên đĩa khớp với sha256_hash đã đăng ký."),
            ("promote_to_candidate()", "None", "None", "Đánh dấu mô hình đủ điều kiện đưa vào thử nghiệm Canary.")
        ]
    )

    render_class_table(
        doc,
        class_name="ModelDeployment",
        description="Quản lý trạng thái phân luồng lưu lượng suy luận AI phục vụ thực tế (Serving Routing State). Hiện thực hóa chiến lược phát hành Canary Deployment và Rollback an toàn 1-click.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của trạng thái triển khai."),
            ("component", "String(20)", "Public", "Cấu phần triển khai: 'STT' hoặc 'NMT'."),
            ("active_model_id", "String(36)", "Public", "Khóa ngoại tham chiếu ModelArtifact.id đang phục vụ chính thức."),
            ("canary_model_id", "String(36)", "Public", "Khóa ngoại tham chiếu ModelArtifact.id đang thử nghiệm canary (hoặc NULL)."),
            ("canary_percent", "Integer", "Public", "Tỷ lệ phần trăm lưu lượng hướng vào mô hình canary (0% đến 100%)."),
            ("previous_active_model_id", "String(36)", "Public", "Khóa ngoại tham chiếu ModelArtifact.id phiên bản trước để Rollback tức thì."),
            ("updated_by", "String(36)", "Public", "Khóa ngoại tham chiếu User.id của Quản trị cấp cao phê duyệt triển khai."),
            ("updated_at", "DateTime", "Public", "Thời điểm cập nhật phân luồng gần nhất.")
        ],
        methods=[
            ("set_canary(canary_id, percent)", "canary_id: str, percent: int", "None", "Kích hoạt định tuyến thử nghiệm Canary với tỷ lệ phần trăm chỉ định."),
            ("promote_canary()", "None", "None", "Thăng hạng mô hình Canary thành Active Model chính thức, lưu Active cũ vào Previous."),
            ("rollback()", "None", "None", "Khôi phục tức thì previous_active_model_id làm Active Model và hủy bỏ Canary.")
        ]
    )

    # Relationships
    render_key_relationships(doc, [
        "Một TrainingDataset có thể làm nguồn cấp dữ liệu cho nhiều tiến trình TrainingJob (Quan hệ 1-N).",
        "Một TrainingJob sở hữu nhiều bản ghi TrainingJobEvent ghi nhận tiến độ từng bước huấn luyện (Quan hệ 1-N).",
        "Một TrainingJob khi hoàn thành thành công sẽ sản sinh ra một gói ModelArtifact (Quan hệ 1-1).",
        "Một ModelDeployment tham chiếu đến tối đa 3 gói ModelArtifact gồm Active Model, Canary Model và Previous Model (Quan hệ N-1).",
        "Thao tác cập nhật ModelDeployment được ghi nhận vào nhật ký an ninh AuditLog có định danh người thực hiện updated_by."
    ])

    # ---------------------------------------------------------
    # 3.2.7 Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử
    # ---------------------------------------------------------
    add_heading_3(doc, "3.2.7 Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử")
    add_paragraph(
        doc,
        "Nhóm lớp xử lý luồng thời gian thực và điều phối tác tử là các đối tượng thuần bộ nhớ trong (In-Memory Objects) "
        "hoạt động trên nền tảng bất đồng bộ Python FastAPI / Asyncio. Nhóm lớp này chịu trách nhiệm duy trì kết nối WebSocket "
        "nhị phân liên tục, thu nhận các khung âm thanh PCM 16kHz mono, phân tích phát hiện tiếng nói liên tục và điều phối "
        "chuỗi xử lý AI đa luồng với độ trễ cực thấp."
    )
    add_paragraph(
        doc,
        "Trong nhóm này, SessionActor là lớp trung tâm áp dụng mẫu kiến trúc tác tử (Actor Model). Mỗi phiên kết nối "
        "(RealtimeSession) được quản lý bởi một SessionActor độc lập, sở hữu hàng đợi thông điệp riêng và khóa hàng rào "
        "Mutex (mic_mutex). Khóa Mutex đảm bảo tại một thời điểm chỉ có duy nhất một bên được phát âm trong chế độ đối thoại "
        "song phương (Turn-taking), loại bỏ hoàn toàn hiện tượng xung đột dữ liệu (Race Condition). "
        "WebRtcVadStream thực hiện phân đoạn âm thanh khung 30ms, phát hiện ranh giới câu nói và kích hoạt các callback. "
        "ModelManager là đối tượng Singleton chịu trách nhiệm nạp sẵn trọng số trong VRAM GPU, cấp phát thể hiện mô hình "
        "phù hợp theo tỷ lệ Canary Deployment cho các Worker nền (STTWorker, TranslationWorker, TTSWorker)."
    )

    # Embed Figure 3.7: In-Memory Realtime Pipeline
    embed_diagram_figure(
        doc,
        img_filename="hinh_3_7_mo_hinh_lop_realtime_actor_pipeline.png",
        caption_text="Hình 3.7: Mô hình lớp xử lý luồng thời gian thực và điều phối tác tử",
        width_inches=6.2
    )

    # Summary table for Realtime Pipeline
    render_subsystem_summary_table(doc, [
        ("RealtimeSession", "Đại diện phiên kết nối WebSocket hai chiều: socket, ngôn ngữ nguồn/đích, chế độ đối thoại và trạng thái kết nối."),
        ("SessionActor", "Tác tử điều phối trạng thái phiên hội thoại, quản lý khóa Mutex chống xung đột tiếng nói và điều phối các Worker."),
        ("WebRtcVadStream", "Bộ phân tích và cắt đoạn âm thanh liên tục khung 30ms/16kHz mono dựa trên thư viện WebRTC VAD."),
        ("ModelManager", "Bộ quản lý tài nguyên mô hình AI Singleton: nạp sẵn VRAM GPU, ánh xạ định tuyến Canary và hoán đổi mô hình không gián đoạn."),
        ("PipelineQueues", "Tập hợp các hàng đợi bất đồng bộ asyncio.Queue kết nối truyền thông điệp giữa các chặng xử lý."),
        ("STTWorker", "Công nhân nền nhận dạng âm thanh tiếng nói thành văn bản bằng mô hình Whisper."),
        ("TransWorker", "Công nhân nền dịch máy văn bản nguồn sang đích bằng mô hình NLLB-200 kết hợp bộ điều hợp LoRA."),
        ("TTSWorker", "Công nhân nền tổng hợp âm thanh giọng đọc tự nhiên từ văn bản đích bằng mô hình MMS VITS.")
    ])

    # Detailed tables
    render_class_table(
        doc,
        class_name="RealtimeSession",
        description="Đại diện cho phiên làm việc WebSocket đang hoạt động giữa máy khách và máy chủ. Chứa thông tin ngữ cảnh hội thoại, cặp ngôn ngữ lựa chọn và trạng thái kết nối mạng.",
        inheritance="None (In-Memory Pure Object)",
        attributes=[
            ("session_id", "String", "Public", "Định danh duy nhất của phiên kết nối WebSocket."),
            ("user_id", "Optional[String]", "Public", "Định danh người dùng nếu đã đăng nhập (hoặc Guest ID)."),
            ("source_lang", "String", "Public", "Ngôn ngữ nguồn của người nói hiện tại."),
            ("target_lang", "String", "Public", "Ngôn ngữ đích cần hệ thống dịch và phát âm thanh."),
            ("mode", "Enum(SessionMode)", "Public", "Chế độ dịch: ONE_WAY (Đơn thoại) hoặc TURN_TAKING (Song phương đối thoại)."),
            ("websocket", "WebSocket", "Private", "Đối tượng kết nối WebSocket nhị phân hai chiều của FastAPI."),
            ("is_alive", "Boolean", "Public", "Trạng thái kết nối socket còn thông suốt hay không.")
        ],
        methods=[
            ("send_json(data)", "data: dict", "Coroutine", "Gửi gói tin trạng thái JSON bất đồng bộ về ứng dụng di động máy khách."),
            ("send_binary(pcm_bytes)", "pcm_bytes: bytes", "Coroutine", "Gửi luồng byte âm thanh đã tổng hợp (TTS) về máy khách để phát loa."),
            ("close(code)", "code: int", "Coroutine", "Đóng kết nối WebSocket một cách an toàn và giải phóng toàn bộ tài nguyên liên kết.")
        ]
    )

    render_class_table(
        doc,
        class_name="SessionActor",
        description="Thực thể trung tâm áp dụng mô hình Actor Model để quản lý trạng thái độc lập của từng phiên hội thoại. Ngăn chặn hiện tượng xung đột dữ liệu (Race Condition) và khóa tranh chấp qua hàng rào mic_mutex.",
        inheritance="None (In-Memory Async Actor)",
        attributes=[
            ("session", "RealtimeSession", "Public", "Tham chiếu đến đối tượng phiên WebSocket của máy khách."),
            ("vad_stream", "WebRtcVadStream", "Private", "Bộ xử lý phát hiện tiếng nói và cắt đoạn âm thanh liên tục."),
            ("mic_mutex", "asyncio.Lock", "Private", "Khóa bất đồng bộ đảm bảo tại một thời điểm chỉ có 1 kênh micrô được phép gửi luồng âm thanh xử lý."),
            ("current_turn", "Optional[TurnMetadata]", "Public", "Thông tin ngữ cảnh của lượt nói đang diễn ra."),
            ("queues", "PipelineQueues", "Private", "Tập hợp các hàng đợi bất đồng bộ kết nối giữa các công nhân xử lý AI.")
        ],
        methods=[
            ("receive_audio_chunk(chunk)", "chunk: bytes", "Coroutine", "Tiếp nhận mẩu âm thanh PCM nhị phân 16kHz từ máy khách và nạp vào vad_stream."),
            ("on_speech_start()", "None", "Coroutine", "Callback được gọi khi phát hiện người dùng bắt đầu nói. Gửi sự kiện 'speech_start' về máy khách để hiện hoạt ảnh sóng âm."),
            ("on_speech_end(complete_audio)", "complete_audio: bytes", "Coroutine", "Callback được kích hoạt khi dứt tiếng nói. Đóng gói audio và đẩy vào hàng đợi nhận dạng STT."),
            ("dispatch_translation(text)", "text: str", "Coroutine", "Nhận kết quả văn bản STT và đẩy vào hàng đợi dịch thuật NLLB-200."),
            ("dispatch_synthesis(text)", "text: str", "Coroutine", "Nhận kết quả dịch và kích hoạt bộ tổng hợp âm thanh giọng nói MMS VITS.")
        ]
    )

    render_class_table(
        doc,
        class_name="WebRtcVadStream",
        description="Bộ đệm và phân tích âm thanh thời gian thực dựa trên thư viện WebRTC VAD. Xử lý các khung âm thanh 30ms với tần số 16kHz mono để phát hiện chính xác ranh giới tiếng nói người.",
        inheritance="None (Audio Signal Processing Helper)",
        attributes=[
            ("sample_rate", "Integer", "Public", "Tần số lấy mẫu âm thanh (mặc định: 16000 Hz)."),
            ("frame_duration_ms", "Integer", "Public", "Độ dài một khung phân tích (30 ms)."),
            ("vad_mode", "Integer", "Public", "Mức độ lọc nhiễu của WebRTC VAD (từ 0 đến 3, mức 3 lọc nhiễu môi trường mạnh nhất)."),
            ("silence_threshold_ms", "Integer", "Public", "Ngưỡng thời gian im lặng liên tiếp để xác định dứt câu (400 - 600 ms)."),
            ("audio_buffer", "bytearray", "Private", "Bộ đệm tích lũy các khối âm thanh nhị phân của câu nói hiện tại.")
        ],
        methods=[
            ("process_chunk(chunk_bytes)", "chunk_bytes: bytes", "List[VadEvent]", "Phân đoạn luồng âm thanh đầu vào thành các khung chuẩn, tính toán xác suất tiếng nói và trả về các sự kiện VAD."),
            ("reset()", "None", "None", "Làm rỗng audio_buffer sau khi một câu nói đã được chốt và gửi đi xử lý.")
        ]
    )

    render_class_table(
        doc,
        class_name="ModelManager",
        description="Bộ quản lý nạp và cấp phát tài nguyên mô hình AI trong bộ nhớ (Singleton Pattern). Áp dụng kỹ thuật Caching, tối ưu VRAM và hoán đổi mô hình Canary linh hoạt mà không cần khởi động lại máy chủ.",
        inheritance="None (Singleton Resource Manager)",
        attributes=[
            ("_instance", "ModelManager", "Private Static", "Thể hiện duy nhất của lớp Singleton."),
            ("loaded_models", "Dict[str, Any]", "Private", "Từ điển ánh xạ ID mô hình với các thể hiện nạp sẵn trong VRAM GPU."),
            ("device", "torch.device", "Public", "Thiết bị tính toán: 'cuda' (NVIDIA GPU) hoặc 'cpu'."),
            ("active_routing", "Dict[str, ModelDeployment]", "Private", "Bản đồ lưu trữ cấu hình phân luồng Canary/Active hiện hành.")
        ],
        methods=[
            ("get_instance()", "None", "ModelManager", "Phương thức tĩnh trả về thể hiện duy nhất của ModelManager."),
            ("get_stt_model(session_id)", "session_id: str", "WhisperModel", "Trả về thể hiện mô hình Whisper phù hợp theo cơ chế phân bổ Canary."),
            ("get_nmt_model(session_id)", "session_id: str", "NLLBModel", "Trả về thể hiện mô hình NLLB-200 kèm adapter LoRA phù hợp."),
            ("get_tts_model(lang)", "lang: str", "VITSModel", "Trả về mô hình tổng hợp giọng đọc MMS VITS tương ứng với ngôn ngữ đích."),
            ("reload_deployment_config()", "None", "None", "Nạp lại cấu hình phân luồng từ cơ sở dữ liệu khi có sự kiện Promote hoặc Rollback.")
        ]
    )

    # Relationships
    render_key_relationships(doc, [
        "Một SessionActor sở hữu duy nhất một RealtimeSession, một WebRtcVadStream và một PipelineQueues (Quan hệ Composition 1-1).",
        "SessionActor tương tác với ModelManager (Singleton) để điều hướng các tác vụ suy luận AI tới các Worker nền.",
        "ModelManager cấp phát các thể hiện mô hình AI được chia sẻ bộ nhớ cho STTWorker, TransWorker và TTSWorker.",
        "Sau khi hoàn thành một lượt dịch, SessionActor đẩy bản ghi kết quả xuống cơ sở dữ liệu bền vững để tạo TranslationLog, AudioAsset và PipelineMetric."
    ])

    print("Section 3.2 completed successfully.")

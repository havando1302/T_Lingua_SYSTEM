# -*- coding: utf-8 -*-
"""
Module providing 3.2: Thiet ke mo hinh lop (Class & Object Model) for T-Lingua report.
Includes complete UML descriptions, class diagrams, attribute tables, method tables,
and relationship matrices matching the university thesis standards of [DALN]2210.
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

def render_class_table(doc, class_name, description, inheritance, attributes, methods, relationships):
    """
    Renders standard class specification table:
    - Class name & overview
    - Inheritance / Interfaces
    - Attributes table
    - Methods table
    - Relationships
    """
    p_name = add_paragraph(doc, f"Lớp: {class_name}", bold=True, font_size=13, space_before=6, space_after=2, color=PRIMARY_COLOR)
    p_desc = add_paragraph(doc, f"Mô tả ý nghĩa: {description}", italic=False, font_size=12, space_after=4)
    if inheritance:
        add_paragraph(doc, f"Kế thừa / Giao diện: {inheritance}", bold=True, italic=True, font_size=11, space_after=4, color=SECONDARY_COLOR)
    
    # 1. Attributes Table
    add_paragraph(doc, f"Bảng thuộc tính của lớp {class_name}:", bold=True, font_size=11, space_before=4, space_after=2)
    tbl_attr = doc.add_table(rows=0, cols=4)
    tbl_attr.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_attr)
    
    # Header
    hdr = tbl_attr.add_row()
    headers = ["Tên thuộc tính", "Kiểu dữ liệu", "Phạm vi", "Mô tả ý nghĩa"]
    widths = [Inches(1.8), Inches(1.2), Inches(0.9), Inches(2.6)]
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
        
    for idx, attr in enumerate(attributes):
        row = tbl_attr.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(attr[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            if col_idx == 0:
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif col_idx in (1, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # 2. Methods Table
    add_paragraph(doc, f"Bảng phương thức của lớp {class_name}:", bold=True, font_size=11, space_before=4, space_after=2)
    tbl_meth = doc.add_table(rows=0, cols=4)
    tbl_meth.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_meth)
    
    hdr_m = tbl_meth.add_row()
    m_headers = ["Tên phương thức", "Tham số đầu vào", "Kiểu trả về", "Chức năng & Mô tả thuật toán"]
    m_widths = [Inches(1.8), Inches(1.5), Inches(1.1), Inches(2.1)]
    for i, h in enumerate(m_headers):
        cell = hdr_m.cells[i]
        cell.width = m_widths[i]
        set_cell_background(cell, SUBHEADER_BG_HEX)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    for idx, meth in enumerate(methods):
        row = tbl_meth.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = m_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(meth[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            if col_idx == 0:
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif col_idx in (1, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Relationships
    if relationships:
        p_rel = add_paragraph(doc, "Mối quan hệ với các lớp khác:", bold=True, font_size=11, space_before=4, space_after=2)
        for rel in relationships:
            add_bullet(doc, rel, prefix="- ")
    add_paragraph(doc, "", space_after=4)

def build_section_3_2(doc):
    """Generates Section 3.2: Thiet ke mo hinh lop."""
    add_heading_2(doc, "3.2. Thiết kế mô hình lớp (Class & Object Model)")
    
    add_paragraph(
        doc,
        "Mô hình lớp đóng vai trò là xương sống trong kiến trúc hướng đối tượng của hệ thống T-Lingua. "
        "Do đặc thù của một hệ thống dịch thuật song phương thời gian thực tích hợp trí tuệ nhân tạo (AI/ML), "
        "T-Lingua không chỉ bao gồm các thực thể lưu trữ dữ liệu bền vững (Persistence Domain Entities) trong cơ sở dữ liệu "
        "mà còn sở hữu một hệ thống các lớp xử lý luồng thời gian thực hướng tác tử (In-Memory Realtime Actor Pipeline). "
        "Toàn bộ mô hình lớp được thiết kế tuân thủ nghiêm ngặt các nguyên lý SOLID, phân tách rành mạch trách nhiệm giữa tầng "
        "giao tiếp WebSocket, tầng điều phối xử lý hội thoại (Actor), tầng công nhân nền AI (Background Workers) và tầng "
        "lưu vết kiểm chuẩn chất lượng (QA & Telemetry)."
    )
    
    # 3.2.1
    add_heading_3(doc, "3.2.1. Phân tầng kiến trúc và phân chia gói lớp (Package Architecture)")
    add_paragraph(
        doc,
        "Hệ thống T-Lingua được tổ chức thành 5 phân hệ lớp chính, đảm bảo tính đóng gói cao và độc lập module:"
    )
    add_bullet(doc, "Phân hệ Xác thực và Kiểm soát Truy cập (Auth & Access Control Subsystem): Chịu trách nhiệm quản lý định danh người dùng, kiểm soát quyền truy cập theo vai trò (RBAC), quản lý token phiên (JWT), khóa API đối tác và nhật ký kiểm toán bất biến (Audit Log).")
    add_bullet(doc, "Phân hệ Dịch thuật và Đo kiểm Pipeline (Translation & Telemetry Subsystem): Lưu trữ chi tiết từng lượt dịch (TranslationLog), tài sản âm thanh liên quan (AudioAsset) và các chỉ số đo kiểm hiệu năng vi mô chặng (PipelineMetric).")
    add_bullet(doc, "Phân hệ Bộ nhớ Dịch và Kiểm soát Chất lượng (Translation Memory & QA Subsystem): Quản lý kho từ vựng chuyên ngành, các cặp thuật ngữ dịch chuẩn (TranslationMemoryEntry) và quy trình gán cờ, thẩm định lỗi ngôn ngữ (QualityReview).")
    add_bullet(doc, "Phân hệ MLOps và Vòng đời Mô hình (Training Center & Model Lifecycle Subsystem): Quản lý tập dữ liệu đóng băng (TrainingDataset), tiến trình huấn luyện lặp (TrainingJob), sự kiện huấn luyện (TrainingJobEvent), kho lưu trữ artifact (ModelArtifact) và cấu hình phân luồng Canary/Active (ModelDeployment).")
    add_bullet(doc, "Phân hệ Xử lý Luồng Thời gian thực (Realtime Stream & Actor Pipeline Subsystem): Chứa các đối tượng xử lý bộ nhớ trong: RealtimeSession, SessionActor điều phối trạng thái, WebRtcVadStream lọc âm, PipelineQueues và ModelManager điều phối tài nguyên VRAM.")

    img_path = r"C:\Du_an\T_Langua_Test\docs\img\hinh_3_1_kien_truc_phan_tang_cac_goi_lop.png"
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(6.3))
    else:
        add_diagram_box(
            doc,
            "Sơ đồ quan hệ phân tầng các gói lớp trong T-Lingua",
            """
+---------------------------------------------------------------------------------------------------+
|                                  GIAO DIỆN CLIENT (FLUTTER & REACT)                              |
+---------------------------------------------------------------------------------------------------+
                                         | REST API (HTTP)           | WebSocket (Binary PCM Stream)
                                         v                           v
+--------------------------------------------------+  +---------------------------------------------+
| PHÂN HỆ QUẢN TRỊ BẢO MẬT & API (REST)           |  | PHÂN HỆ XỬ LÝ LUỒNG THỜI GIAN THỰC (ACTOR) |
| - User, AuthSession, ApiKey, AuditLog, Setting   |  | - RealtimeSession, SessionActor             |
+--------------------------------------------------+  | - WebRtcVadStream, PipelineQueues           |
                         |                            | - Workers: STTWorker, TransWorker, TTSWorker|
                         |                            +---------------------------------------------+
                         v                                                   |
+----------------------------------------------------------------------------+                      |
| PHÂN HỆ MLOPS & HUẤN LUYỆN (LIFECYCLE)           | PHÂN HỆ DỊCH THUẬT & TELEMETRY (PERSISTENCE)   |
| - TrainingDataset, TrainingJob, TrainingJobEvent | - TranslationLog, AudioAsset, PipelineMetric   |
| - ModelArtifact, ModelDeployment, Event          | - TranslationMemoryEntry, QualityReview        |
+--------------------------------------------------+------------------------------------------------+
                         |                                                   |
                         +-------------------------+-------------------------+
                                                   v
                                 +-----------------------------------+
                                 | CƠ SỞ DỮ LIỆU BỀN VỮNG (RDBMS/ORM)|
                                 | SQLAlchemy 2.0 ORM Base Model     |
                                 +-----------------------------------+
"""
        )
    add_caption(doc, "Hình 3.1: Kiến trúc phân tầng các gói lớp trong hệ thống T-Lingua", is_table=False)

    # 3.2.2 Sơ đồ lớp tổng thể
    add_heading_3(doc, "3.2.2. Biểu đồ lớp tổng thể (Global Class Diagram)")
    add_paragraph(
        doc,
        "Biểu đồ lớp tổng thể thể hiện cấu trúc tĩnh của toàn bộ các thực thể cốt lõi trong hệ thống và các mối liên kết bản số (multiplicity) "
        "giữa chúng. Mô hình thể hiện rõ mối quan hệ 1-N giữa User với AuthSession, ApiKey, AuditLog và QualityReview; mối quan hệ 1-N giữa "
        "TranslationLog với PipelineMetric và QualityReview; mối quan hệ 1-N giữa TrainingDataset với TrainingJob; và liên kết điều phối "
        "giữa ModelArtifact với ModelDeployment."
    )
    
    add_diagram_box(
        doc,
        "Biểu đồ lớp tổng thể hệ thống T-Lingua (UML Class Diagram)",
        """
 +-----------------------+        1..* +----------------------+
 |         User          |------------<|     AuthSession      |
 |-----------------------|             |----------------------|
 | - id: String (UUID)   |             | - id: String         |
 | - username: String    |             | - user_id: String    |
 | - hashed_password: Str|             | - token: String      |
 | - role: RoleEnum      |             | - expires_at: Datetime
 | - totp_secret: String |             +----------------------+
 | - is_active: Boolean  |        1..* +----------------------+
 | - mfa_enabled: Boolean|------------<|        ApiKey        |
 +-----------------------+             |----------------------|
      | 1           | 1                | - id: String         |
      |             |                  | - key_hash: String   |
      |             |                  | - rate_limit: Int    |
      |             |                  +----------------------+
      |             |             1..* +----------------------+
      |             +-----------------<|       AuditLog       |
      |                                |----------------------|
      |                                | - action: String     |
      |                                | - timestamp: Datetime|
      |                                +----------------------+
      v 1..*
 +-----------------------+        1..* +----------------------+
 |     QualityReview     |>------------|    TranslationLog    |
 |-----------------------|             |----------------------|
 | - id: String          |             | - id: String         |
 | - reviewer_id: String |             | - session_id: String |
 | - translation_id: Str |             | - source_lang: String|
 | - mqm_score: Float    |             | - target_lang: String|
 | - error_category: Str |             | - source_text: String|
 | - status: ReviewStatus|             | - target_text: String|
 +-----------------------+             | - is_flagged: Boolean|
                                       +----------------------+
                                            | 1             | 1
                                            v 1..1          v 1..*
                                 +------------------+ +------------------+
                                 |    AudioAsset    | |  PipelineMetric  |
                                 |------------------| |------------------|
                                 | - id: String     | | - id: String     |
                                 | - file_path: Str | | - vad_ms: Float  |
                                 | - duration_ms:Int| | - stt_ms: Float  |
                                 | - format: String | | - nmt_ms: Float  |
                                 +------------------+ | - tts_ms: Float  |
                                                      | - e2e_ms: Float  |
                                                      +------------------+

 +-----------------------+        1..* +----------------------+
 |    TrainingDataset    |------------<|     TrainingJob      |
 |-----------------------|             |----------------------|
 | - id: String          |             | - id: String         |
 | - version: String     |             | - dataset_id: String |
 | - sample_count: Int   |             | - model_type: String |
 | - split_ratio: String |             | - status: JobStatus  |
 | - checksum_sha256: Str|             | - lora_r: Integer    |
 +-----------------------+             | - val_loss: Float    |
                                       +----------------------+
                                            | 1 (tạo ra)
                                            v 1
 +-----------------------+        1..1 +----------------------+
 |    ModelDeployment    |------------<|    ModelArtifact     |
 |-----------------------|             |----------------------|
 | - id: String          | (tham chiếu)| - id: String         |
 | - active_model_id: Str|             | - artifact_uri: Str  |
 | - canary_model_id: Str|             | - sha256_hash: Str   |
 | - canary_percent: Int |             | - test_bleu: Float   |
 | - status: DeployStatus|             | - status: ArtStatus  |
 +-----------------------+             +----------------------+
"""
    )
    add_caption(doc, "Hình 3.2: Biểu đồ lớp tổng thể các thực thể nghiệp vụ (Domain Entities) T-Lingua", is_table=False)

    # 3.2.3 Chi tiết Phân hệ Xác thực & Quản trị Bảo mật
    add_heading_3(doc, "3.2.3. Chi tiết các lớp Phân hệ Xác thực và Bảo mật (Auth & Security Subsystem)")
    
    # Class User
    render_class_table(
        doc,
        class_name="User",
        description="Đại diện cho thực thể người dùng và tài khoản quản trị hệ thống. Quản lý thông tin định danh, cơ chế băm mật khẩu bảo mật cao (Argon2id/Bcrypt), cấu hình phân quyền theo vai trò (Role-Based Access Control - RBAC) và bảo mật hai lớp (TOTP MFA).",
        inheritance="SQLAlchemy DeclarativeBase (ORM Mapping)",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID định danh duy nhất người dùng."),
            ("username", "String(64)", "Public", "Tên đăng nhập hệ thống, là duy nhất (unique), không rỗng."),
            ("email", "String(128)", "Public", "Địa chỉ hòm thư điện tử dùng để nhận cảnh báo và phục hồi."),
            ("hashed_password", "String(255)", "Private", "Chuỗi mật khẩu đã được băm bảo mật kèm muối (Salt) bằng Argon2/Bcrypt."),
            ("role", "Enum(RoleEnum)", "Public", "Vai trò: ADMIN, SENIOR_ADMIN, AUDITOR, REVIEWER, TRANSLATOR."),
            ("is_active", "Boolean", "Public", "Cờ trạng thái kích hoạt tài khoản. Nếu False, tài khoản bị vô hiệu hóa."),
            ("is_verified", "Boolean", "Public", "Trạng thái đã xác minh danh tính qua email hoặc quản trị phê duyệt."),
            ("mfa_enabled", "Boolean", "Public", "Cờ kích hoạt xác thực hai yếu tố (TOTP) bắt buộc với vai trò quản trị."),
            ("mfa_secret", "String(64)", "Private", "Mã khóa bí mật dùng để sinh mã số TOTP 6 chữ số theo chuẩn RFC 6238."),
            ("failed_login_attempts", "Integer", "Private", "Số lần đăng nhập sai liên tiếp. Vượt quá 5 lần sẽ tạm khóa 15 phút."),
            ("locked_until", "DateTime", "Private", "Mốc thời gian tài khoản bị tạm khóa đến thời điểm chỉ định."),
            ("created_at", "DateTime", "Public", "Thời điểm bản ghi tài khoản được khởi tạo trong hệ thống."),
            ("updated_at", "DateTime", "Public", "Thời điểm cập nhật thông tin tài khoản gần nhất.")
        ],
        methods=[
            ("verify_password(raw_pwd)", "raw_pwd: str", "bool", "Băm mật khẩu thô và so sánh với hashed_password theo hàm thời gian không đổi (constant-time) tránh tấn công Timing Attack."),
            ("set_password(new_pwd)", "new_pwd: str", "None", "Sinh muối mới và thực hiện băm mật khẩu an toàn, ghi đè vào hashed_password."),
            ("verify_totp(totp_code)", "totp_code: str", "bool", "Kiểm tra tính hợp lệ của mã 6 chữ số dựa trên mfa_secret và đồng hồ hệ thống theo chuẩn TOTP."),
            ("has_permission(perm)", "perm: Permission", "bool", "Kiểm tra xem vai trò hiện tại của User có quyền thực thi thao tác nghiệp vụ perm hay không."),
            ("record_failed_login()", "None", "None", "Tăng biến đếm failed_login_attempts. Nếu >= 5, thiết lập locked_until = now() + 15 phút."),
            ("reset_failed_logins()", "None", "None", "Đặt lại failed_login_attempts về 0 sau khi đăng nhập thành công.")
        ],
        relationships=[
            "1 User sở hữu 0..* AuthSession (Quan hệ 1-N, Cascade Delete).",
            "1 User sở hữu 0..* ApiKey (Quan hệ 1-N).",
            "1 User có thể là tác nhân của 0..* AuditLog (Quan hệ 1-N).",
            "1 User (với vai trò Reviewer) có thể thẩm định 0..* QualityReview (Quan hệ 1-N)."
        ]
    )

    # Class AuthSession
    render_class_table(
        doc,
        class_name="AuthSession",
        description="Quản lý vòng đời phiên làm việc đã xác thực của người dùng. Lưu trữ định danh JWT, thời gian hiệu lực và thông tin nguồn gốc yêu cầu (IP, User-Agent) phục vụ phòng chống đánh cắp phiên (Session Hijacking).",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của phiên."),
            ("user_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến User.id."),
            ("token_hash", "String(255)", "Private", "Mã băm SHA-256 của Refresh Token nhằm tra cứu nhanh và bảo vệ token trong DB."),
            ("ip_address", "String(45)", "Public", "Địa chỉ IPv4/IPv6 của thiết bị khách khi thiết lập phiên."),
            ("user_agent", "String(255)", "Public", "Chuỗi nhận dạng trình duyệt/ứng dụng của thiết bị khách."),
            ("expires_at", "DateTime", "Public", "Thời điểm phiên hết hạn bắt buộc người dùng đăng nhập lại."),
            ("is_revoked", "Boolean", "Public", "Cờ thu hồi phiên (ví dụ khi người dùng bấm Đăng xuất hoặc bị quản trị hủy phiên)."),
            ("created_at", "DateTime", "Public", "Thời điểm khởi tạo phiên.")
        ],
        methods=[
            ("is_valid()", "None", "bool", "Kiểm tra phiên còn hạn (expires_at > now()) và chưa bị thu hồi (is_revoked == False)."),
            ("revoke()", "None", "None", "Đánh dấu is_revoked = True và giải phóng phiên ngay lập tức.")
        ],
        relationships=[
            "Nhiều AuthSession thuộc về duy nhất 1 User (Quan hệ N-1)."
        ]
    )

    # Class ApiKey
    render_class_table(
        doc,
        class_name="ApiKey",
        description="Quản lý khóa truy cập API dành cho các ứng dụng ngoại vi hoặc đối tác tích hợp vào nền tảng T-Lingua. Đi kèm cơ chế phân mức giới hạn tốc độ gọi (Rate Limiting).",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của API Key."),
            ("user_id", "String(36)", "Public", "Khóa ngoại tham chiếu đến tài khoản người dùng/chủ sở hữu."),
            ("key_prefix", "String(8)", "Public", "Tiền tố hiển thị công khai (ví dụ: 'tlg_live_') giúp nhận dạng khóa."),
            ("key_hash", "String(255)", "Private", "Băm mật mã của toàn bộ API Key để so khớp an toàn."),
            ("label", "String(100)", "Public", "Nhãn gợi nhớ do người dùng đặt (ví dụ: 'Key Tích Hợp Kiosk Sân Bay')."),
            ("rate_limit_rpm", "Integer", "Public", "Số lượt gọi tối đa cho phép trong 1 phút (Requests Per Minute)."),
            ("is_active", "Boolean", "Public", "Trạng thái hoạt động của khóa API."),
            ("expires_at", "DateTime", "Public", "Hạn sử dụng của khóa (hoặc NULL nếu vô thời hạn)."),
            ("created_at", "DateTime", "Public", "Thời điểm tạo khóa.")
        ],
        methods=[
            ("verify_key(raw_key)", "raw_key: str", "bool", "Kiểm tra chuỗi API key gửi lên qua header X-API-KEY có khớp với key_hash không."),
            ("check_rate_limit(redis_client)", "redis: Redis", "bool", "Sử dụng thuật toán Token Bucket / Sliding Window trên Redis để xác định có bị quá tải RPM hay không.")
        ],
        relationships=[
            "Nhiều ApiKey thuộc về 1 User sở hữu (Quan hệ N-1)."
        ]
    )

    # Class AuditLog
    render_class_table(
        doc,
        class_name="AuditLog",
        description="Bản ghi kiểm toán an ninh bất biến (Append-only Immutable Trail). Lưu trữ toàn bộ các thao tác can thiệp hệ thống nhạy cảm phục vụ công tác thanh tra và an ninh thông tin.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của bản ghi nhật ký."),
            ("actor_id", "String(36)", "Public", "Định danh người thực hiện (User.id hoặc 'SYSTEM')."),
            ("action", "String(64)", "Public", "Mã hành động: USER_LOGIN, CANARY_PROMOTE, DICT_ADD, QA_REJECT..."),
            ("resource_type", "String(64)", "Public", "Loại tài nguyên bị tác động: User, ModelDeployment, Gloss..."),
            ("resource_id", "String(64)", "Public", "Khóa định danh của tài nguyên bị thay đổi."),
            ("payload_before", "JSON", "Private", "Dữ liệu trạng thái của tài nguyên trước khi thay đổi."),
            ("payload_after", "JSON", "Private", "Dữ liệu trạng thái mới sau khi thay đổi hoàn tất."),
            ("ip_address", "String(45)", "Public", "Địa chỉ IP thực hiện yêu cầu."),
            ("timestamp", "DateTime", "Public", "Thời gian ghi nhận bản ghi với độ chính xác mili-giây.")
        ],
        methods=[
            ("log_event(actor, action, res_type, res_id, before, after, ip)", "Đa tham số", "AuditLog", "Phương thức tĩnh (factory method) khởi tạo bản ghi kiểm toán mới và đẩy vào luồng ghi bất đồng bộ.")
        ],
        relationships=[
            "Nhiều AuditLog có thể tham chiếu đến 1 User (Quan hệ N-1, trường actor_id)."
        ]
    )

    # 3.2.4 Chi tiết Phân hệ Dịch thuật & Telemetry
    add_heading_3(doc, "3.2.4. Chi tiết các lớp Phân hệ Dịch thuật và Đo kiểm Pipeline (Translation & Telemetry Subsystem)")
    
    # Class TranslationLog
    render_class_table(
        doc,
        class_name="TranslationLog",
        description="Thực thể trung tâm lưu trữ thông tin nghiệp vụ của một lượt dịch hoàn chỉnh (turn). Kết nối văn bản nguồn từ STT, văn bản đích từ NMT và các chỉ số đo kiểm chất lượng.",
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
            ("flag_issue(reason)", "reason: str", "None", "Gắn cờ is_flagged = True và kích hoạt tạo một phiếu QualityReview mới trong hàng đợi."),
            ("to_dict()", "None", "dict", "Chuyển đổi dữ liệu bản ghi thành đối tượng JSON chuẩn hóa phục vụ hiển thị trên Admin Dashboard và Mobile History.")
        ],
        relationships=[
            "1 TranslationLog liên kết với 1 AudioAsset âm thanh giọng nói (Quan hệ 1-1).",
            "1 TranslationLog sở hữu 1..* PipelineMetric đo kiểm các chặng xử lý (Quan hệ 1-N).",
            "1 TranslationLog có thể có 0..1 bản ghi QualityReview (Quan hệ 1-1)."
        ]
    )

    # Class AudioAsset
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
            ("format", "String(10)", "Public", "Định dạng đóng gói: 'wav', 'webm', 'ogg'."),
            ("created_at", "DateTime", "Public", "Thời điểm tệp âm thanh được lưu trữ hoàn tất.")
        ],
        methods=[
            ("get_audio_bytes()", "None", "bytes", "Đọc luồng byte nhị phân của tệp âm thanh từ hệ thống tệp lưu trữ."),
            ("delete_physical_file()", "None", "bool", "Xóa tệp vật lý trên ổ đĩa khi bản ghi hết hạn hoặc bị xóa theo chính sách bảo mật.")
        ],
        relationships=[
            "AudioAsset thuộc về duy nhất 1 TranslationLog (Quan hệ N-1 / 1-1)."
        ]
    )

    # Class PipelineMetric
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
            ("e2e_latency_ms", "Float", "Public", "Tổng thời gian trễ trọn gói từ lúc dứt câu đến khi phát âm (ms)."),
            ("model_version_stt", "String(50)", "Public", "Phiên bản mô hình STT đang phục vụ lúc đo kiểm."),
            ("model_version_nmt", "String(50)", "Public", "Phiên bản mô hình NMT đang phục vụ lúc đo kiểm."),
            ("created_at", "DateTime", "Public", "Thời điểm thu thập số liệu.")
        ],
        methods=[
            ("calculate_e2e()", "None", "float", "Tính toán tổng e2e_latency_ms = vad_ms + stt_ms + nmt_ms + tts_ms và kiểm tra ngưỡng cảnh báo (SLA < 1500ms).")
        ],
        relationships=[
            "Thuộc về duy nhất 1 TranslationLog (Quan hệ N-1)."
        ]
    )

    # 3.2.5 Chi tiết Phân hệ Bộ nhớ Dịch & QA
    add_heading_3(doc, "3.2.5. Chi tiết các lớp Phân hệ Bộ nhớ Dịch và Kiểm chuẩn Chất lượng (TM & QA Subsystem)")

    # Class TranslationMemoryEntry
    render_class_table(
        doc,
        class_name="TranslationMemoryEntry",
        description="Đại diện cho một cặp thuật ngữ hoặc câu mẫu trong Bộ nhớ dịch / Thuật ngữ chuyên ngành (Glossary / Translation Memory). Can thiệp tiền/hậu xử lý dịch để ép chuẩn từ chuyên ngành.",
        inheritance="SQLAlchemy DeclarativeBase",
        attributes=[
            ("id", "String(36)", "Private", "Khóa chính UUID của mục từ điển."),
            ("source_text", "String(500)", "Public", "Cụm từ hoặc câu chuẩn trong ngôn ngữ nguồn."),
            ("target_text", "String(500)", "Public", "Nghĩa dịch chuẩn bắt buộc trong ngôn ngữ đích."),
            ("source_lang", "String(10)", "Public", "Mã ngôn ngữ nguồn."),
            ("target_lang", "String(10)", "Public", "Mã ngôn ngữ đích."),
            ("domain", "String(50)", "Public", "Lĩnh vực chuyên môn: 'General', 'Medical', 'Tourism', 'Technology'..."),
            ("match_count", "Integer", "Public", "Số lần cặp từ này được khớp và áp dụng thành công trong thực tế."),
            ("is_active", "Boolean", "Public", "Cờ cho phép sử dụng mục từ này trong quy trình dịch tự động."),
            ("created_by", "String(36)", "Public", "Khóa ngoại tham chiếu User.id của người tạo mục từ.")
        ],
        methods=[
            ("increment_match()", "None", "None", "Tăng biến đếm match_count khi bộ máy dịch áp dụng cụm từ này."),
            ("normalize_text()", "None", "None", "Chuẩn hóa khoảng trắng, chữ hoa/thường để tối ưu tốc độ so khớp chuỗi.")
        ],
        relationships=[
            "Được quản lý bởi các User có vai trò Admin hoặc Reviewer."
        ]
    )

    # Class QualityReview
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
            ("error_category", "String(50)", "Public", "Nhóm lỗi: 'Accuracy' (Sai nghĩa), 'Fluency' (Ngữ pháp), 'Terminology' (Thuật ngữ), 'Hallucination' (Ảo giác)."),
            ("severity", "String(20)", "Public", "Mức độ nghiêm trọng: 'Minor', 'Major', 'Critical'."),
            ("corrected_text", "Text", "Public", "Văn bản đã được chuyên gia sửa lại cho chuẩn xác."),
            ("feedback_note", "Text", "Public", "Ghi chú giải thích của chuyên gia."),
            ("status", "Enum(ReviewStatus)", "Public", "Trạng thái: PENDING, APPROVED, REJECTED, SENT_TO_DATASET."),
            ("reviewed_at", "DateTime", "Public", "Thời điểm chuyên gia hoàn thành đánh giá.")
        ],
        methods=[
            ("approve_and_export(split_tag)", "split_tag: str", "TrainingDataset", "Phê duyệt câu dịch đã sửa và tự động đẩy vào tập dữ liệu huấn luyện (TrainingDataset) với nhãn split_tag (train/val/test)."),
            ("reject(reason)", "reason: str", "None", "Bác bỏ cờ báo lỗi nếu câu dịch gốc thực tế không có vấn đề.")
        ],
        relationships=[
            "Thuộc về 1 TranslationLog cụ thể (Quan hệ 1-1).",
            "Được đánh giá bởi 1 User có vai trò Reviewer (Quan hệ N-1)."
        ]
    )

    # 3.2.6 Chi tiết Phân hệ MLOps & Vòng đời Mô hình
    add_heading_3(doc, "3.2.6. Chi tiết các lớp Phân hệ MLOps và Vòng đời Mô hình (Training & Lifecycle Subsystem)")

    # Class TrainingDataset
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
        ],
        relationships=[
            "1 TrainingDataset có thể được sử dụng làm đầu vào cho 0..* TrainingJob (Quan hệ 1-N)."
        ]
    )

    # Class TrainingJob
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
        ],
        relationships=[
            "Thuộc về 1 TrainingDataset (Quan hệ N-1).",
            "Sở hữu 1..* TrainingJobEvent ghi vết tiến trình huấn luyện (Quan hệ 1-N).",
            "Sản sinh ra tối đa 1 ModelArtifact khi hoàn thành thành công (Quan hệ 1-1)."
        ]
    )

    # Class ModelArtifact & ModelDeployment
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
            ("sha256_hash", "String(64)", "Public", "Mã băm kiểm tra tính toàn vẹn của gói tệp."),
            ("test_bleu", "Float", "Public", "Điểm BLEU kiểm định độc lập."),
            ("test_chrf", "Float", "Public", "Điểm chrF++ kiểm định độc lập."),
            ("status", "Enum(ArtifactStatus)", "Public", "Trạng thái: CANDIDATE, ACTIVE, ARCHIVED, REJECTED."),
            ("created_at", "DateTime", "Public", "Thời điểm xuất xưởng gói mô hình.")
        ],
        methods=[
            ("verify_checksum()", "None", "bool", "Xác thực mã băm tệp trên đĩa khớp với sha256_hash đã đăng ký."),
            ("promote_to_candidate()", "None", "None", "Đánh dấu mô hình đủ điều kiện đưa vào thử nghiệm Canary.")
        ],
        relationships=[
            "Được sinh ra từ duy nhất 1 TrainingJob (Quan hệ 1-1).",
            "Có thể được cấu hình trong ModelDeployment như một Active Model hoặc Canary Model."
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
        ],
        relationships=[
            "Tham chiếu đến 3 đối tượng ModelArtifact (Active, Canary, Previous).",
            "Phát sinh các bản ghi lịch sử trong bảng DeploymentEvent."
        ]
    )

    # 3.2.7 Chi tiết Phân hệ Xử lý Luồng Thời gian thực
    add_heading_3(doc, "3.2.7. Chi tiết các lớp Phân hệ Xử lý Luồng Thời gian thực (In-Memory Realtime Actor Pipeline)")
    add_paragraph(
        doc,
        "Đây là các lớp xử lý bất đồng bộ (Asyncio) chạy trong bộ nhớ RAM máy chủ backend FastAPI. "
        "Các lớp này chịu trách nhiệm duy trì kết nối WebSocket liên tục, phân tích tín hiệu âm thanh và điều phối "
        "mô hình AI với độ trễ thấp dưới 1500ms."
    )

    # RealtimeSession & SessionActor
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
            ("close()", "code: int", "Coroutine", "Đóng kết nối WebSocket một cách an toàn và dọn dẹp các tài nguyên liên kết.")
        ],
        relationships=[
            "Được điều phối trực tiếp bởi 1 đối tượng SessionActor."
        ]
    )

    render_class_table(
        doc,
        class_name="SessionActor",
        description="Thực thể trung tâm áp dụng mô hình Actor Model để quản lý trạng thái độc lập của từng phiên hội thoại. Ngăn chặn hiện tượng xung đột dữ liệu (Race Condition) và khóa tranh chấp (Mutex) khi cả hai người cùng nói trong chế độ song ngữ.",
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
            ("on_speech_start()", "None", "Coroutine", "Callback được gọi khi phát hiện người dùng bắt đầu nói. Gửi sự kiện 'speech_start' về máy khách để hiện hiệu ứng sóng âm."),
            ("on_speech_end(complete_audio)", "complete_audio: bytes", "Coroutine", "Callback được kích hoạt khi dứt tiếng nói. Đóng gói audio và đẩy vào hàng đợi nhận dạng STT."),
            ("dispatch_translation(text)", "text: str", "Coroutine", "Nhận kết quả văn bản STT và đẩy vào hàng đợi dịch thuật NLLB."),
            ("dispatch_synthesis(text)", "text: str", "Coroutine", "Nhận kết quả dịch và kích hoạt bộ tổng hợp âm thanh giọng nói TTS.")
        ],
        relationships=[
            "Sở hữu 1 RealtimeSession, 1 WebRtcVadStream và 1 PipelineQueues.",
            "Tương tác với ModelManager để gửi yêu cầu suy luận AI tới các Worker nền."
        ]
    )

    # WebRtcVadStream & ModelManager
    render_class_table(
        doc,
        class_name="WebRtcVadStream",
        description="Bộ đệm và phân tích âm thanh thời gian thực dựa trên thư viện WebRTC VAD. Xử lý các khung âm thanh 20ms/30ms với tần số 16kHz mono để phát hiện chính xác ranh giới tiếng nói người.",
        inheritance="None (Audio Signal Processing Helper)",
        attributes=[
            ("sample_rate", "Integer", "Public", "Tần số lấy mẫu âm thanh (mặc định: 16000 Hz)."),
            ("frame_duration_ms", "Integer", "Public", "Độ dài một khung phân tích (30 ms)."),
            ("vad_mode", "Integer", "Public", "Mức độ lọc nhiễu của WebRTC VAD (từ 0 đến 3, mức 3 lọc nhiễu môi trường mạnh nhất)."),
            ("silence_threshold_ms", "Integer", "Public", "Ngưỡng thời gian im lặng liên tiếp để xác định ngắt câu (400 - 600 ms)."),
            ("audio_buffer", "bytearray", "Private", "Bộ đệm tích lũy các khối âm thanh nhị phân của câu nói hiện tại.")
        ],
        methods=[
            ("process_chunk(chunk_bytes)", "chunk_bytes: bytes", "List[VadEvent]", "Phân đoạn luồng âm thanh đầu vào thành các khung chuẩn, thực hiện tính toán xác suất tiếng nói và trả về các sự kiện VAD."),
            ("reset()", "None", "None", "Làm rỗng audio_buffer sau khi một câu nói đã được chốt và gửi đi xử lý.")
        ],
        relationships=[
            "Được chứa và điều khiển bởi SessionActor."
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
        ],
        relationships=[
            "Cung cấp tài nguyên mô hình AI dùng chung cho các Worker (STTWorker, TranslationWorker, TTSWorker)."
        ]
    )

    print("Section 3.2 completed.")

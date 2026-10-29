# -*- coding: utf-8 -*-
"""
Module providing 3.5: Thiet ke giao dien nguoi dung (UI/UX Design) for T-Lingua report.
Includes Mobile Flutter (4 screens) and React Web Admin (10 screens) with layout wireframes,
component tables, user interaction flows, and RBAC visibility matching [DALN]2210.
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

def render_ui_component_table(doc, screen_name, components):
    """
    Renders UI Component Specification table:
    [STT, Tên thành phần, Loại Widget / Control, Dữ liệu / Trạng thái, Ý nghĩa & Tương tác người dùng]
    """
    add_paragraph(doc, f"Bảng thành phần giao diện màn hình: {screen_name}", bold=True, font_size=11, space_before=4, space_after=2)
    tbl = doc.add_table(rows=0, cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)
    
    headers = ["STT", "Tên thành phần", "Loại Widget / Control", "Dữ liệu / Trạng thái", "Ý nghĩa & Tương tác"]
    widths = [Inches(0.5), Inches(1.8), Inches(1.4), Inches(1.5), Inches(2.0)]
    
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
        
    for idx, comp in enumerate(components):
        row = tbl.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for c_idx in range(5):
            cell = row.cells[c_idx]
            cell.width = widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            p = cell.paragraphs[0]
            val = str(comp[c_idx])
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.bold = True
            elif c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.bold = True
            elif c_idx in (2, 3):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_paragraph(doc, "", space_after=4)

def build_section_3_5(doc):
    """Generates Section 3.5: Thiet ke giao dien nguoi dung."""
    add_heading_2(doc, "3.5. Thiết kế giao diện người dùng (UI/UX Design)")
    
    add_paragraph(
        doc,
        "Giao diện người dùng của hệ thống T-Lingua được thiết kế dựa trên nguyên lý thiết kế lấy người dùng làm trung tâm "
        "(User-Centered Design - UCD) và triết lý Thiết kế nguyên tử (Atomic Design). "
        "Hệ thống bao gồm hai giao diện người dùng độc lập:"
    )
    add_bullet(doc, "Ứng dụng Di động T-Lingua Mobile (Flutter): Tối ưu hóa cho trải nghiệm di chuyển ngoài trời, du lịch, hội họp trực tiếp với cơ chế điều khiển bằng giọng nói chạm tối thiểu (Zero/Minimal Click), phản hồi trực quan bằng hoạt ảnh sóng âm và rung xúc giác (Haptic Feedback).")
    add_bullet(doc, "Cổng Thông tin Quản trị Web Admin (React): Tối ưu hóa cho màn hình máy tính để bàn (Desktop Dashboard) với bố cục đa cột, thanh điều hướng bên (Sidebar Navigation), hệ thống thẻ chỉ số (KPI Metric Cards), đồ thị động thời gian thực (ECharts/Chart.js) và cơ chế ẩn/hiện chức năng nghiêm ngặt theo phân quyền vai trò (Role-Based Access Control).")

    # 3.5.1
    add_heading_3(doc, "3.5.1. Nguyên lý và Tiêu chuẩn Thiết kế UI/UX")
    add_paragraph(
        doc,
        "Để đảm bảo tính nhất quán trên toàn bộ hệ thống, bộ nhận diện giao diện áp dụng các quy chuẩn chặt chẽ:"
    )
    add_bullet(doc, "Bảng màu chủ đạo (Color Palette): Màu xanh Phenikaa (#1B365D) tượng trưng cho sự tin cậy, tri thức và bảo mật; Màu xanh điểm nhấn Electric Blue (#0066CC) dùng cho các nút tương tác chính; Màu xanh lá cây (#10B981) biểu thị trạng thái kết nối thành công và độ chính xác cao; Màu hổ phách/cam (#F59E0B) cảnh báo các câu dịch cần kiểm duyệt; Màu đỏ Crimson (#EF4444) thông báo lỗi đường truyền hoặc cảnh báo hệ thống.")
    add_bullet(doc, "Quy tắc Typography: Sử dụng phông chữ không chân hiện đại (Inter, Roboto, SF Pro) hỗ trợ đầy đủ bộ ký tự Unicode tiếng Việt và các ký tự tượng hình đa ngữ (Trung, Nhật, Hàn, Thái) với tỷ lệ độ tương phản WCAG 2.1 AA.")
    add_bullet(doc, "Phản hồi trạng thái tức thời (Instant State Feedback): Khi người dùng nói, giao diện di động ngay lập tức hiển thị bộ sóng âm nhấp nháy theo năng lượng âm thanh; văn bản nhận dạng STT hiển thị tức thời (streaming transcript) trước khi kết quả dịch cuối cùng được phát âm thanh.")

    # 3.5.2 Thiết kế Giao diện Ứng dụng Di động Flutter
    add_heading_3(doc, "3.5.2. Thiết kế giao diện Ứng dụng Di động T-Lingua Mobile (Flutter Client)")
    add_paragraph(
        doc,
        "Ứng dụng Flutter bao gồm 4 màn hình chính được liên kết thông qua thanh điều hướng đáy (Bottom Navigation Bar):"
    )

    # Screen 1: Home
    add_paragraph(doc, "1. Màn hình Dịch một chiều tức thời (Home Screen):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mục đích: Cho phép người dùng nhanh chóng chọn cặp ngôn ngữ, nhấn giữ hoặc chạm micrô để nói một câu đơn "
        "và ngay lập tức nhận bản dịch văn bản kèm phát âm thanh tự động."
    )
    add_diagram_box(
        doc,
        "Wireframe Bố cục: Màn hình Dịch một chiều tức thời (Home Screen)",
        """
+-----------------------------------------------------------+
| [Header]   T-LINGUA REALTIME                     [GearIcon]|
|            Trạng thái máy chủ: [● Đã kết nối]              |
+-----------------------------------------------------------+
|                                                           |
|  [ Lang Selector Card ]                                   |
|  +-----------------------+     <--->     +--------------+ |
|  | Tiếng Việt (vi-VN)    |   [SwapBtn]   | English (US) | |
|  +-----------------------+               +--------------+ |
|                                                           |
|  [ Speech Recognition Result Area ]                       |
|  "Xin chào, tôi muốn hỏi đường đến bảo tàng mỹ thuật..." |
|                                                           |
|  -------------------------------------------------------  |
|                                                           |
|  [ Translated Output Card ]                               |
|  "Hello, I would like to ask for directions to the        |
|   Fine Arts Museum..."                                    |
|                                                           |
|  [🔊 Play TTS]   [📋 Copy]   [⭐ Bookmark]   [🚩 Report]   |
|                                                           |
|                                                           |
|                      +-----------------+                  |
|                      |   (((( 🎙️ ))))  |                  |
|                      |  [Big Mic Button|                  |
|                      |  Waveform Pulse]|                  |
|                      +-----------------+                  |
|                      Chạm hoặc nhấn giữ để nói            |
|                                                           |
+-----------------------------------------------------------+
| [Tab: Home]    [Tab: Đối thoại]    [Tab: Lịch sử]   [Tab: Cài đặt]|
+-----------------------------------------------------------+
"""
    )
    add_caption(doc, "Hình 3.9: Wireframe bố cục màn hình Dịch một chiều tức thời trên Flutter Mobile", is_table=False)

    home_components = [
        ("1", "StatusBadge", "Container / Badge", "Xanh lá: Online / Đỏ: Offline", "Hiển thị trạng thái kết nối WebSocket tới máy chủ FastAPI."),
        ("2", "SourceLangDropdown", "DropdownButtonHideUnderline", "Danh sách 200 ngôn ngữ", "Cho phép chọn ngôn ngữ nói của người sử dụng."),
        ("3", "SwapLangButton", "IconButton (Icons.swap_horiz)", "Active / Disabled", "Đảo ngược vị trí giữa ngôn ngữ nguồn và ngôn ngữ đích."),
        ("4", "TargetLangDropdown", "DropdownButtonHideUnderline", "Danh sách 200 ngôn ngữ", "Cho phép chọn ngôn ngữ cần dịch sang."),
        ("5", "SourceTranscriptBox", "AnimatedTextKit / Card", "Text chuỗi nguồn", "Hiển thị văn bản Whisper nhận dạng với hiệu ứng chữ chạy tức thời."),
        ("6", "TargetResultCard", "Card / Elevation 4", "Text chuỗi dịch NLLB", "Hiển thị văn bản bản dịch nổi bật kèm màu nền dễ đọc ngoài trời."),
        ("7", "ActionToolbar", "Row (IconButton)", "Play, Copy, Bookmark, Flag", "Các nút chức năng: Nghe lại phát âm, Sao chép, Lưu yêu thích, Báo lỗi."),
        ("8", "CentralMicButton", "AnimatedContainer / FloatingActionButton", "Idle, Listening, Processing", "Nút micrô chính kích hoạt thu âm PCM 16kHz kèm hiệu ứng vòng tròn sóng âm lan tỏa.")
    ]
    render_ui_component_table(doc, "Trang chủ Dịch một chiều (Home Screen)", home_components)

    # Embed screenshot if available
    img_frontend_path = r"c:\Du_an\T_Langua_Test\outputs\screenshot_frontend.png"
    if os.path.exists(img_frontend_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_frontend_path, width=Inches(3.2))
        add_caption(doc, "Hình 3.10: Giao diện thực tế ứng dụng di động T-Lingua trong chế độ dịch tức thời", is_table=False)

    # Screen 2: Conversation DualMic
    add_paragraph(doc, "2. Màn hình Đối thoại song phương hai chiều (Conversation DualMic Screen):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mục đích: Phục vụ hai người khác ngôn ngữ giao tiếp trực tiếp mặt-đối-mặt (Face-to-face). "
        "Màn hình chia đôi không gian hiển thị theo dạng khung chat bong bóng hai chiều, tích hợp thanh micrô kép "
        "(DualMicBar) có cơ chế khóa Mutex chống xung đột khi cả hai người cùng nói."
    )
    add_diagram_box(
        doc,
        "Wireframe Bố cục: Màn hình Đối thoại song phương (Conversation DualMic Screen)",
        """
+-----------------------------------------------------------+
| [< Quay lại]    HỘI THOẠI SONG PHƯƠNG        [Xóa hội thoại]|
+-----------------------------------------------------------+
|                                                           |
|  [Bong bóng chat - Phía Đối tác Nước ngoài (Tiếng Anh)]   |
|  +-----------------------------------------------------+  |
|  | 🇺🇸 "Could you tell me how much this souvenir costs?" |  |
|  | 🇻🇳 "Bạn có thể cho tôi biết món quà lưu niệm này    |  |
|  |     giá bao nhiêu không?"                           |  |
|  +-----------------------------------------------------+  |
|                                                           |
|  [Bong bóng chat - Phía Bản địa Việt Nam (Tiếng Việt)]    |
|                     +----------------------------------+  |
|                     | 🇻🇳 "Món này có giá 150 nghìn ạ." |  |
|                     | 🇺🇸 "This one costs 150,000 VND." |  |
|                     +----------------------------------+  |
|                                                           |
|  (Lịch sử cuộn tự động theo lượt nói mới nhất...)         |
|                                                           |
|-----------------------------------------------------------|
| [DUAL MIC BAR - THANH MICRÔ ĐỐI THOẠI KÉP VỚI MUTEX LOCK] |
|                                                           |
|   +--------------------------+  +----------------------+  |
|   |       🎙️ BÊN TRÁI        |  |     🎙️ BÊN PHẢI       |  |
|   |    TIẾNG VIỆT (TÔI)      |  |   ENGLISH (ĐỐI TÁC)  |  |
|   |   [ĐANG NÓI - XANH LÁ]   |  |   [BỊ KHÓA - MÀU XÁM] |  |
|   +--------------------------+  +----------------------+  |
|    Chạm để nói tiếng Việt        Chạm để nói tiếng Anh    |
+-----------------------------------------------------------+
"""
    )
    add_caption(doc, "Hình 3.11: Wireframe màn hình Đối thoại song phương với thanh điều khiển DualMicBar", is_table=False)

    conv_components = [
        ("1", "ChatBubblePartner", "ChatBubbleWidget", "Bên trái / Xám nhạt", "Hiển thị câu nói và câu dịch của người nước ngoài hướng về phía trên."),
        ("2", "ChatBubbleUser", "ChatBubbleWidget", "Bên phải / Xanh Phenikaa", "Hiển thị câu nói và câu dịch của người bản địa hướng về phía dưới."),
        ("3", "AudioReplayButton", "IconButton (Icons.volume_up)", "Active", "Cho phép chạm vào từng bong bóng để nghe lại âm thanh câu dịch tương ứng."),
        ("4", "DualMicLeftButton", "ElevatedButton / MicIcon", "Xanh lá (Active) / Xám (Disabled)", "Kích hoạt lượt nói tiếng Việt. Chiếm khóa Mutex, vô hiệu hóa nút bên phải."),
        ("5", "DualMicRightButton", "ElevatedButton / MicIcon", "Xanh dương (Active) / Xám (Disabled)", "Kích hoạt lượt nói ngôn ngữ đối tác. Chiếm khóa Mutex, vô hiệu hóa nút bên trái."),
        ("6", "ClearSessionButton", "IconButton (Icons.delete_sweep)", "Active", "Xóa toàn bộ các lượt đối thoại trong phiên làm việc hiện tại.")
    ]
    render_ui_component_table(doc, "Đối thoại song phương (Conversation Screen)", conv_components)

    # Screen 3 & 4: History & Settings
    add_paragraph(doc, "3. Màn hình Lịch sử & Đánh dấu Yêu thích (History & Favorites Screen):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mục đích: Cho phép người dùng duyệt lại toàn bộ các câu dịch đã thực hiện, lọc theo cặp ngôn ngữ, "
        "tìm kiếm từ khóa, nghe lại âm thanh đã lưu hoặc gắn cờ báo lỗi nếu câu dịch chưa chuẩn xác."
    )
    add_paragraph(doc, "4. Màn hình Cài đặt & Tùy chọn Hệ thống (Settings Screen):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Mục đích: Cấu hình tốc độ đọc giọng nói TTS (0.5x đến 2.0x), chọn giọng đọc nam/nữ, điều chỉnh độ nhạy micrô VAD, "
        "bật/tắt chế độ tự động phát âm thanh và kiểm tra thông tin phiên bản ứng dụng."
    )

    # 3.5.3 Thiết kế Giao diện Cổng Thông tin Quản trị Web Admin (React)
    add_heading_3(doc, "3.5.3. Thiết kế giao diện Cổng Quản trị Web Admin (React Single-Page Application)")
    add_paragraph(
        doc,
        "Giao diện Web Admin được xây dựng trên nền tảng React 18, Ant Design và Tailwind CSS. "
        "Hệ thống bao gồm 10 phân hệ màn hình chuyên sâu phục vụ công tác vận hành, kiểm định chất lượng và MLOps:"
    )

    # Table of 10 screens with RBAC
    add_paragraph(doc, "Bảng tổng hợp 10 phân hệ màn hình Web Admin và Phân quyền RBAC:", bold=True, font_size=11, space_before=4, space_after=2)
    tbl_screens = doc.add_table(rows=0, cols=4)
    tbl_screens.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_screens)
    
    scr_headers = ["STT", "Tên màn hình Web Admin", "Mã Route URL", "Vai trò cho phép truy cập (RBAC)"]
    scr_widths = [Inches(0.5), Inches(2.5), Inches(1.8), Inches(2.2)]
    
    hdr_s = tbl_screens.add_row()
    for i, h in enumerate(scr_headers):
        cell = hdr_s.cells[i]
        cell.width = scr_widths[i]
        set_cell_background(cell, HEADER_BG_HEX)
        set_cell_margins(cell, top=80, bottom=80, left=70, right=70)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    screens_list = [
        ("1", "Màn hình Đăng nhập & Xác thực TOTP MFA", "/login & /auth/mfa", "Tất cả các vai trò (Public Auth)"),
        ("2", "Bảng điều khiển Tổng quan (Dashboard)", "/dashboard", "Superadmin, Admin, Reviewer, Employee"),
        ("3", "Phân tích & Đo kiểm hiệu năng Telemetry", "/analytics", "Superadmin, Admin"),
        ("4", "Quản lý Bộ nhớ dịch & Từ điển (Glossary/TM)", "/dictionary", "Superadmin, Admin, Reviewer"),
        ("5", "Hàng đợi Thẩm định chất lượng (QA Queue)", "/qa-queue", "Superadmin, Admin, Reviewer"),
        ("6", "Lịch sử Phiên dịch chi tiết (Translation History)", "/history", "Superadmin, Admin, Reviewer, Employee"),
        ("7", "Quản lý Người dùng & Phân quyền (Users)", "/users", "Superadmin"),
        ("8", "Quản lý Khóa API Tích hợp (API Keys)", "/api-keys", "Superadmin, Admin"),
        ("9", "Trung tâm Huấn luyện & MLOps (Training Center)", "/training", "Superadmin, Admin"),
        ("10", "Cấu hình Hệ thống động (System Settings)", "/settings", "Superadmin")
    ]
    
    for idx, s in enumerate(screens_list):
        row = tbl_screens.add_row()
        bg = ZEBRA_BG_HEX if idx % 2 == 1 else "FFFFFF"
        for col_idx in range(4):
            cell = row.cells[col_idx]
            cell.width = scr_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            p = cell.paragraphs[0]
            run = p.add_run(s[col_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.bold = True
            elif col_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.bold = True
            elif col_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_caption(doc, "Bảng 3.4: Danh mục các màn hình Web Admin và ma trận phân quyền RBAC")

    # Chi tiết 4 màn hình tiêu biểu của Web Admin
    # 1. Login & MFA
    add_paragraph(doc, "Màn hình 1: Đăng nhập & Xác thực TOTP MFA (/login):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Giao diện chia đôi màn hình: bên trái là hình ảnh nhận diện thương hiệu T-Lingua, bên phải là form đăng nhập 2 bước. "
        "Sau khi mật khẩu hợp lệ, form trượt mượt mà sang giao diện nhập 6 ô số TOTP từ ứng dụng Google Authenticator."
    )

    # 2. Dashboard
    add_paragraph(doc, "Màn hình 2: Bảng điều khiển Tổng quan (Dashboard - /dashboard):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_diagram_box(
        doc,
        "Wireframe Bố cục: Bảng điều khiển Tổng quan (Admin Dashboard)",
        """
+---------------------------------------------------------------------------------------------------+
| [Logo] T-LINGUA ADMIN    [Search...]                 [Mô hình Active: NLLB-LoRA-v1.2]  [👤 Admin] |
+--------------------+------------------------------------------------------------------------------+
| [Sidebar Menu]     |  [ KPI SUMMARY CARDS ]                                                       |
| • Dashboard        |  +----------------+ +----------------+ +----------------+ +----------------+ |
| • Analytics        |  | Tổng câu dịch  | | Độ trễ P50/P90 | | Tỷ lệ gắn cờ   | | Canary Traffic | |
| • QA Queue (12)    |  | 142,580 câu    | | 640ms / 1120ms | | 2.14% (Bình th)| | 10% (Chạy tốt) | |
| • Từ điển / TM     |  +----------------+ +----------------+ +----------------+ +----------------+ |
| • MLOps Training   |                                                                              |
| • Lịch sử dịch     |  [ REALTIME LATENCY & TRAFFIC CHART (ECHART) ]                               |
| • Người dùng       |  +-------------------------------------------------------------------------+ |
| • Khóa API         |  | [Đồ thị đường biểu diễn độ trễ mili-giây từng phút: VAD, STT, NMT, TTS] | |
| • Cài đặt hệ thống |  +-------------------------------------------------------------------------+ |
|                    |                                                                              |
|                    |  [ RECENT TRANSLATION ACTIVITY TABLE ]             [ RECENT QA ALERTS ]      |
|                    |  +-----------------------------------------------+ +-----------------------+ |
|                    |  | ID   | Nguồn -> Đích | Độ trễ | Trạng thái    | | ID: #982 (Accuracy)   | |
|                    |  | #102 | vi -> en      | 780ms  | Hoàn tất      | | ID: #985 (Terminology)| |
|                    |  +-----------------------------------------------+ +-----------------------+ |
+--------------------+------------------------------------------------------------------------------+
"""
    )
    add_caption(doc, "Hình 3.12: Wireframe bố cục Bảng điều khiển Tổng quan Web Admin", is_table=False)

    # 3. QA Review Queue
    add_paragraph(doc, "Màn hình 5: Hàng đợi Thẩm định chất lượng (QA Review Queue - /qa-queue):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_paragraph(
        doc,
        "Màn hình trung tâm của quy trình Human-in-the-loop: Chuyên gia ngôn ngữ lắng nghe tệp âm thanh nguồn, "
        "đối chiếu văn bản STT và văn bản NMT, lựa chọn phân loại lỗi MQM, chỉnh sửa câu dịch chuẩn và bấm 'Phê duyệt & Đẩy vào Dataset'."
    )
    
    img_qa_path = r"c:\Du_an\T_Langua_Test\outputs\screenshot_admin_qa.png"
    if os.path.exists(img_qa_path):
        p_qa = doc.add_paragraph()
        p_qa.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_qa.paragraph_format.space_before = Pt(6)
        p_qa.paragraph_format.space_after = Pt(2)
        run_qa = p_qa.add_run()
        run_qa.add_picture(img_qa_path, width=Inches(6.0))
        add_caption(doc, "Hình 3.13: Giao diện thực tế Hàng đợi thẩm định chất lượng QA Reviewer trên Web Admin", is_table=False)

    # 4. Training Center & MLOps
    add_paragraph(doc, "Màn hình 9: Trung tâm Huấn luyện & Vòng đời MLOps (Training Center - /training):", bold=True, font_size=12, color=PRIMARY_COLOR)
    add_diagram_box(
        doc,
        "Wireframe Bố cục: Trung tâm Huấn luyện & Vòng đời MLOps (Training Center)",
        """
+---------------------------------------------------------------------------------------------------+
| [Sidebar]          | TRUNG TÂM HUẤN LUYỆN & MLOPS (TRAINING CENTER)                                |
| • Dashboard        |                                                                              |
| • QA Queue         | [TAB 1: TẬP DỮ LIỆU ĐÓNG BĂNG]  [TAB 2: TIẾN TRÌNH HUẤN LUYỆN]  [TAB 3: CANARY]|
| • MLOps Center     |------------------------------------------------------------------------------|
|   - Datasets       | [KHỞI TẠO TIẾN TRÌNH HUẤN LUYỆN MỚI (LORA / PEFT)]                           |
|   - Training Jobs  | Mô hình nền tảng: [ facebook/nllb-200-distilled-600M  ▼ ]                    |
|   - Canary Deploy  | Tập dữ liệu đã đóng băng: [ dataset_vi_en_frozen_v1.2 (10,500 mẫu)  ▼ ]       |
| • Cài đặt          | Siêu tham số: LoRA Rank [ 16 ]  LoRA Alpha [ 32 ]  Learning Rate [ 0.0002 ]  |
|                    | Số Epoch: [ 5 ]   Batch Size: [ 16 ]           [🚀 Bắt đầu Huấn luyện GPU]   |
|                    |------------------------------------------------------------------------------|
|                    | [GIÁM SÁT TIẾN TRÌNH HUẤN LUYỆN REALTIME: JOB #job_lora_20261026_01]         |
|                    | Trạng thái: [● RUNNING]   Tiến độ: [===========>       ] 64%                 |
|                    | Epoch: 3/5  |  Step: 850/1320  |  Train Loss: 1.624  |  Val Loss: 1.712      |
|                    | [Đồ thị hàm mất mát Loss Curve cập nhật trực tiếp qua WebSocket]             |
|                    |------------------------------------------------------------------------------|
|                    | [ĐIỀU HƯỚNG CANARY & ROLLBACK PHỤC VỤ]                                       |
|                    | Active Model: nllb-lora-v1.1 (90% Traffic)                                   |
|                    | Canary Model: nllb-lora-v1.2 (10% Traffic)  --> BLEU: 38.6 (+1.8 điểm)       |
|                    | [✅ Promote to 100% Active]         [⏪ Rollback về Phiên bản Cũ]             |
+--------------------+------------------------------------------------------------------------------+
"""
    )
    add_caption(doc, "Hình 3.14: Wireframe bảng điều khiển Trung tâm Huấn luyện LoRA và Triển khai Canary MLOps", is_table=False)

    training_components = [
        ("1", "BaseModelSelect", "Select (Dropdown)", "NLLB-200 / Whisper", "Lựa chọn mô hình AI nền tảng cần huấn luyện thích ứng LoRA."),
        ("2", "FrozenDatasetSelect", "Select (Dropdown)", "Danh sách tập v1.0, v1.1, v1.2", "Chọn tập dữ liệu đã đóng băng và xác thực toàn vẹn SHA-256."),
        ("3", "HyperparamInputs", "InputNumber Group", "Rank, Alpha, LR, Batch, Epoch", "Nhập các tham số tinh chỉnh cấu hình LoRA PEFT."),
        ("4", "StartJobButton", "Button (type='primary')", "Active / Loading", "Kích hoạt gửi tiến trình xuống GPU Worker thực thi."),
        ("5", "LossChartLive", "EChart Line Component", "Loss curves (Train vs Val)", "Hiển thị đồ thị hội tụ của mô hình nhận luồng dữ liệu thời gian thực."),
        ("6", "CanarySlider", "Slider (0% - 100%)", "Giá trị phần trăm", "Điều chỉnh tỷ lệ phân bổ lưu lượng người dùng cho mô hình thử nghiệm."),
        ("7", "PromoteButton", "Button (type='success')", "Active", "Thăng hạng mô hình Canary thành Active Model chính thức phục vụ toàn hệ thống."),
        ("8", "RollbackButton", "Button (danger=true)", "Active", "Thu hồi khẩn cấp hoán đổi về phiên bản hoạt động ổn định trước đó.")
    ]
    render_ui_component_table(doc, "Trung tâm Huấn luyện & MLOps (Training Center)", training_components)

    print("Section 3.5 completed.")

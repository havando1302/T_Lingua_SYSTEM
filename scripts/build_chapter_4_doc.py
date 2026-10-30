# -*- coding: utf-8 -*-
"""
Master Builder for Chapter 4: CHƯƠNG 4 - TRIỂN KHAI, THỰC NGHIỆM VÀ ĐÁNH GIÁ HỆ THỐNG
Formatted strictly according to Phenikaa University thesis standards matching [ĐALN]2210.pdf.
Outputs to docs/CHƯƠNG_4_TRIEN_KHAI_THUC_NGHIEM_VA_DANH_GIA_T-LINGUA.docx
Updated for Native Host Runtime Deployment (No Docker) & New System Architecture Diagram.
"""

import sys
import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Ensure UTF-8 console output
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_ROOT = r"C:\Du_an\T_Langua_Test"
DOCS_DIR = os.path.join(WORKSPACE_ROOT, "docs")
IMG_DIR = os.path.join(DOCS_DIR, "img")
OUT_DOCX = os.path.join(DOCS_DIR, "CHƯƠNG_4_TRIEN_KHAI_THUC_NGHIEM_VA_DANH_GIA_T-LINGUA.docx")

# Styling Constants (Phenikaa Brand Palette)
PRIMARY_COLOR = RGBColor(27, 54, 93)     # #1B365D - Navy Phenikaa
SECONDARY_COLOR = RGBColor(11, 37, 69)   # #0B2545 - Deep Navy
TEXT_COLOR = RGBColor(0, 0, 0)           # Black
GRAY_TEXT = RGBColor(80, 80, 80)
HEADER_BG_HEX = "1B365D"
SUBHEADER_BG_HEX = "2B4C7E"
ZEBRA_BG_HEX = "F8FAFC"
BORDER_COLOR_HEX = "CBD5E1"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color=BORDER_COLOR_HEX, sz="4"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_paragraph(doc, text="", bold=False, italic=False, font_size=13, space_after=6, space_before=0, line_spacing=1.3, align=WD_ALIGN_PARAGRAPH.JUSTIFY, color=TEXT_COLOR):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = line_spacing
    
    if text:
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
    return p

def add_heading_chapter(doc, text):
    p = add_paragraph(doc, text, bold=True, font_size=16, space_before=16, space_after=12, align=WD_ALIGN_PARAGRAPH.CENTER, color=PRIMARY_COLOR)
    return p

def add_heading_1(doc, text):
    p = add_paragraph(doc, text, bold=True, font_size=14.5, space_before=14, space_after=6, align=WD_ALIGN_PARAGRAPH.LEFT, color=PRIMARY_COLOR)
    return p

def add_heading_2(doc, text):
    p = add_paragraph(doc, text, bold=True, font_size=13.5, space_before=10, space_after=4, align=WD_ALIGN_PARAGRAPH.LEFT, color=PRIMARY_COLOR)
    return p

def add_heading_3(doc, text):
    p = add_paragraph(doc, text, bold=True, italic=True, font_size=13, space_before=6, space_after=3, align=WD_ALIGN_PARAGRAPH.LEFT, color=SECONDARY_COLOR)
    return p

def add_bullet(doc, text="", prefix="• "):
    p = add_paragraph(doc, text="", space_after=3, space_before=0, line_spacing=1.25, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p.paragraph_format.left_indent = Inches(0.25)
    run_bullet = p.add_run(prefix)
    run_bullet.bold = True
    run_bullet.font.name = "Times New Roman"
    run_bullet.font.size = Pt(13)
    run_bullet.font.color.rgb = PRIMARY_COLOR
    
    run_text = p.add_run(text)
    run_text.font.name = "Times New Roman"
    run_text.font.size = Pt(13)
    return p

def add_caption(doc, text, is_table=True):
    space_before = 6 if is_table else 4
    space_after = 6 if is_table else 10
    p = add_paragraph(doc, text, bold=True, italic=True, font_size=11, space_before=space_before, space_after=space_after, align=WD_ALIGN_PARAGRAPH.CENTER, color=PRIMARY_COLOR)
    return p

def add_picture_with_caption(doc, img_rel_path, caption_text, width_inches=6.0):
    img_full_path = os.path.join(IMG_DIR, img_rel_path)
    if os.path.exists(img_full_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_full_path, width=Inches(width_inches))
        add_caption(doc, caption_text, is_table=False)
    else:
        print(f"Warning: Image not found: {img_full_path}")

def setup_page_layout(doc):
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(2.0 / 2.54)
        section.bottom_margin = Inches(2.0 / 2.54)
        section.left_margin = Inches(3.0 / 2.54)
        section.right_margin = Inches(2.0 / 2.54)

# ==============================================================================
# SECTION BUILDERS
# ==============================================================================

def build_section_4_1(doc):
    add_heading_1(doc, "4.1. Môi trường cài đặt và Kiến trúc triển khai hệ thống")
    
    add_paragraph(doc, "Hệ thống phiên dịch giọng nói hai chiều thời gian thực T-Lingua được thiết kế và triển khai dựa trên mô hình kiến trúc phân tán đa tầng vận hành trực tiếp trên môi trường máy chủ bản địa (Native Host Runtime Architecture). Để đáp ứng yêu cầu khắt khe về độ trễ tổng thể đường ống dịch thuật dưới ngưỡng nhận thức đàm thoại tự nhiên (< 1.000 ms), hệ thống loại bỏ hoàn toàn các lớp ảo hóa trung gian, lựa chọn phương thức thực thi trực tiếp trên hạ tầng máy chủ tính toán chuyên dụng (Bare-Metal / Host-Native Execution).")
    
    add_paragraph(doc, "Giải pháp triển khai bản địa này mang lại những ưu thế kỹ thuật vượt trội: (1) loại bỏ hoàn toàn chi phí phụ trội (Zero Virtualization Overhead) của lớp ảo hóa mạng và phân chia tài nguyên ảo; (2) khai thác tối đa 100% băng thông truyền thông trực tiếp giữa CPU và bộ xử lý đồ họa chuyên dụng NVIDIA GPU thông qua chuẩn giao tiếp PCIe Gen 4 và cơ chế bộ nhớ thống nhất (Unified Memory); (3) tối ưu hóa cơ chế giao tiếp liên tiến trình (Inter-Process Communication - IPC) và bộ đệm vòng (In-Memory RingBuffer) trong RAM cho các luồng âm thanh thời gian thực mà không bị giới hạn bởi các lớp mạng cầu nối ảo (bridge network).")
    
    add_paragraph(doc, "Hệ thống phân tách rành mạch thành các phân hệ chức năng chuyên biệt: phân hệ máy khách di động (Flutter Mobile Client), cổng thông tin quản trị và kiểm chuẩn (React 18 Admin Portal), máy chủ điều phối thời gian thực (Nginx Reverse Proxy & FastAPI Backend API) và cụm dịch vụ trí tuệ nhân tạo chuyên biệt (AI Inference Engine Workers). Danh mục các công nghệ và giải pháp kỹ thuật cốt lõi được lựa chọn kỹ lưỡng trong đồ án được tổng hợp chi tiết trong Bảng 4.1.")

    add_caption(doc, "Bảng 4.1: Danh mục các công nghệ và giải pháp kỹ thuật sử dụng trong hệ thống T-Lingua", is_table=True)
    
    # Table 4.1: Tech Stack
    table_data = [
        ["STT", "Thành phần", "Công nghệ / Phiên bản", "Vai trò trong hệ thống", "Lý do lựa chọn"],
        ["1", "Phân hệ Di động (Mobile App)", "Flutter 3.22 / Dart 3.4", "Xây dựng ứng dụng đa nền tảng (Android/iOS) cho người dùng cuối", "Biên dịch mã máy native AOT (ARM64), render giao diện mượt mà 60fps, hỗ trợ capture luồng âm thanh PCM micro độ trễ thấp và kiến trúc BLoC phản ứng."],
        ["2", "Cổng Quản trị (Admin Portal)", "React 18.3, Vite 5.2, Tailwind CSS", "Giao diện quản lý người dùng, từ điển, thẩm định chất lượng MQM và Telemetry", "Tốc độ phản hồi cực nhanh nhờ Vite HMR, quản lý trạng thái tập trung với Zustand, hệ thống giao diện Tailwind linh hoạt, dễ bảo trì."],
        ["3", "Máy chủ Dịch vụ (Backend API)", "FastAPI 0.111, Python 3.10+, Uvicorn", "Tiếp nhận kết nối WebSocket song công, điều phối phiên dịch Actor Model và REST API", "Hiệu năng I/O bất đồng bộ (Asyncio) vượt trội, tích hợp trực tiếp hệ sinh thái AI Python, tự động sinh chuẩn OpenAPI Specification."],
        ["4", "Nhận dạng giọng nói (STT)", "faster-whisper (CTranslate2 INT8)", "Chuyển đổi luồng âm thanh 16kHz của người nói thành văn bản tiếng Việt / tiếng Anh", "Tăng tốc độ suy luận nhanh gấp 4 lần so với mô hình gốc nhờ định lượng INT8 và tối ưu bộ nhớ CTranslate2, độ chính xác cao trong môi trường có tiếng ồn."],
        ["5", "Dịch máy thần kinh (MT)", "NLLB-200 1.3B, LoRA PEFT, CTranslate2", "Dịch văn bản song phương Anh - Việt và thích ứng miền chuyên sâu", "Khả năng dịch đa ngữ hàng đầu thế giới của Meta AI, hỗ trợ nạp nóng các adapter LoRA kích thước siêu nhỏ (14.8 MB) mà không làm gián đoạn hệ thống."],
        ["6", "Tổng hợp giọng nói (TTS)", "Piper TTS (VITS Architecture), ONNX", "Tổng hợp văn bản dịch thành âm thanh giọng đọc tự nhiên (WAV PCM 16kHz)", "Hệ số Real-Time Factor (RTF) ấn tượng < 0.15, âm thanh phát âm chuẩn ngữ điệu, tiêu thụ tài nguyên CPU/GPU cực thấp so với các giải pháp khác."],
        ["7", "Tách âm giọng nói (VAD)", "WebRTC VAD (Py-WebRTCVAD 2.0.10)", "Phát hiện tiếng nói con người và kích hoạt cơ chế ngắt câu tự động (500ms Cutoff)", "Thuật toán lọc năng lượng khung 20ms mức độ nhạy Aggressiveness Mode 3, độ trễ bằng 0, phân biệt chính xác tiếng nói và tạp âm nền."],
        ["8", "Cơ sở dữ liệu quan hệ", "PostgreSQL 16.x / SQLite, SQLAlchemy", "Lưu trữ cấu trúc: người dùng, phân quyền RBAC, nhật ký dịch thuật, kho từ điển, MQM", "Tuân thủ nghiêm ngặt chuẩn toàn vẹn ACID, cơ chế MVCC tối ưu cho truy xuất đồng thời, hỗ trợ Full-Text Search và chỉ mục chuyên biệt."],
        ["9", "Bộ nhớ đệm & Phân tán", "Redis 7.2 Cache / In-Memory RAM", "Lưu trữ phiên làm việc tạm, khóa tương hỗ Dual-Mic Mutex, cache đối sánh từ điển", "Tốc độ truy xuất cấp độ micro-giây trong RAM, hỗ trợ các cấu trúc dữ liệu nguyên tử (atomic operations) chống tranh chấp tài nguyên mạng."],
        ["10", "Hạ tầng máy chủ & Môi trường", "Host Native Runtime (Ubuntu/Windows Server)", "Vận hành trực tiếp các dịch vụ trên máy chủ vật lý, quản lý tiến trình bằng Uvicorn & Systemd", "Loại bỏ hoàn toàn chi phí ảo hóa (Zero Virtualization Overhead), cấp phát trực tiếp GPU CUDA 12.2 qua PCIe Gen 4, bảo đảm độ trễ đàm thoại cực tiểu."]
    ]

    t41 = doc.add_table(rows=len(table_data), cols=5)
    t41.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t41)
    
    col_widths = [Inches(0.4), Inches(1.3), Inches(1.5), Inches(1.7), Inches(1.8)]
    
    for row_idx, row_content in enumerate(table_data):
        row = t41.rows[row_idx]
        is_head = (row_idx == 0)
        bg = HEADER_BG_HEX if is_head else (ZEBRA_BG_HEX if row_idx % 2 == 1 else "FFFFFF")
        for col_idx, cell_value in enumerate(row_content):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_head or col_idx in [0, 2]) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            run = p.add_run(cell_value)
            run.bold = is_head or (col_idx == 1)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5 if not is_head else 10)
            run.font.color.rgb = RGBColor(255, 255, 255) if is_head else TEXT_COLOR

    add_paragraph(doc, "")
    add_paragraph(doc, "Mô hình kiến trúc triển khai tổng thể của hệ thống T-Lingua được mô tả chi tiết trong Hình 4.1. Kiến trúc bao gồm 11 khối thành phần cốt lõi được kết nối và phối hợp chặt chẽ theo luồng dữ liệu thời gian thực:")
    add_bullet(doc, "(1) Hệ thống phân giải tên miền (DNS / Route 53): Đảm nhiệm vai trò phân giải tên miền và định tuyến các kết nối mạng từ Internet về địa chỉ IP công khai của máy chủ hệ thống.")
    add_bullet(doc, "(2) Tầng người dùng và Thiết bị đầu cuối (User Clients): Bao gồm Ứng dụng di động Flutter trên thiết bị của người dùng cuối (thu phát âm thanh PCM 16kHz, kết nối WebSocket hai chiều phục vụ chế độ dịch một chạm và đối thoại song ngữ) và Cổng thông tin quản trị Web Admin trên trình duyệt của chuyên viên kiểm chuẩn và quản trị viên.")
    add_bullet(doc, "(3) Bộ điều phối và Cổng đảo ngược (Nginx Reverse Proxy & Load Balancer): Tiếp nhận toàn bộ lưu lượng vào, thực hiện chấm dứt chứng chỉ mã hóa SSL/TLS, phân luồng kết nối WebSocket bảo mật (WSS) cho luồng âm thanh đàm thoại và các yêu cầu RESTful HTTPS cho cổng quản trị, đồng thời kiểm soát tần suất truy cập (Rate Limiting).")
    add_bullet(doc, "(4) Cụm máy chủ ứng dụng trung tâm (FastAPI Backend Server): Chạy trực tiếp trên môi trường máy chủ với máy chủ ASGI Uvicorn, bao gồm: bộ điều phối phiên SessionActor quản lý trạng thái đàm thoại và bộ đệm RingBuffer; thuật toán WebRTC VAD phát hiện khoảng lặng và tự động ngắt câu (500ms Silence Cutoff); bộ khóa tương hỗ Dual-Mic Mutex Lock giải quyết triệt để xung đột âm thanh; và các bộ điều khiển REST API phục vụ xác thực người dùng (Argon2id, TOTP MFA, JWT Token Rotation) và quản lý hệ thống.")
    add_bullet(doc, "(5) Cơ sở dữ liệu quan hệ bền vững (Relational Database - PostgreSQL 16 / SQLite): Lưu trữ toàn bộ dữ liệu nghiệp vụ có cấu trúc của hệ thống, bao gồm tài khoản người dùng, phân quyền RBAC, nhật ký đàm thoại, các bản ghi kiểm chuẩn MQM và kho từ điển chuyên ngành.")
    add_bullet(doc, "(6) Bộ nhớ đệm tốc độ cao và Bộ nhớ dịch (Caching & Translation Memory - Redis 7.2 / RAM): Lưu trữ các khóa phiên đàm thoại, thực thi các thao tác khóa nguyên tử cho cơ chế Mutex, và lưu trữ Bộ nhớ dịch (TM) dưới dạng bảng băm SHA-256 giúp đối sánh và trả về kết quả dịch tức thì (< 5ms) đối với các câu đã được phê duyệt.")
    add_bullet(doc, "(7a) Hàng đợi âm thanh và Tác vụ bất đồng bộ (Audio & Pipeline Queue): Đóng vai trò là hàng đợi chuyển tiếp âm thanh (asyncio.Queue trong RAM), tiếp nhận các gói âm thanh WAV 16kHz đã ngắt câu từ SessionActor và điều phối sang các worker AI mà không gây nghẽn luồng mạng.")
    add_bullet(doc, "(7b) Cụm tiến trình xử lý AI chuyên biệt (AI Inference Engine Workers): Vận hành trực tiếp trên card đồ họa chuyên dụng NVIDIA GPU thông qua CUDA 12.2 native, bao gồm STT Worker (faster-whisper INT8 giải mã tiếng nói sang văn bản), MT Worker (NLLB-200 1.3B kết hợp LoRA Adapter PEFT dịch văn bản song phương), và TTS Worker (Piper VITS ONNX tổng hợp giọng đọc tự nhiên WAV PCM).")
    add_bullet(doc, "(8) Dịch vụ đối sánh từ điển chuyên ngành và Tìm kiếm (Glossary & Search Service): Sử dụng thuật toán tìm kiếm xâu mẫu Aho-Corasick để quét và cưỡng bức dịch đúng các thuật ngữ chuyên ngành (y tế, kỹ thuật, tên riêng), bảo toàn tuyệt đối 100% các thực thể số.")
    add_bullet(doc, "(9a) Luồng viễn trắc và Nhật ký kiểm toán (Telemetry & Audit Logs Event Stream): Thu thập liên tục các số liệu đo kiểm vi mô (độ trễ từng công đoạn, điểm tin cậy nhận dạng ASR, cờ báo lỗi từ người dùng) phục vụ giám sát vận hành.")
    add_bullet(doc, "(9b) Kho lưu trữ tài nguyên âm thanh và Trọng số mô hình (Audio Asset & Model Storage): Lưu trữ các tệp âm thanh WAV ghi âm gốc, tệp phát âm câu dịch và các bộ trọng số mô hình LoRA Adapter định dạng Safetensors trên phân vùng ổ đĩa NVMe tốc độ cao.")
    add_bullet(doc, "(10) Trung tâm huấn luyện MLOps và Kho dữ liệu vàng MQM (MLOps Training & QA Data Warehouse): Tập hợp các bản ghi dịch thuật đã qua thẩm định và phê duyệt bởi chuyên gia (Gold Standard Dataset), đóng vai trò bệ phóng cho tiến trình huấn luyện tinh chỉnh LoRA Adapter định kỳ và thực thi chiến lược điều hướng thử nghiệm Canary Rollout.")
    add_bullet(doc, "(11) Mạng phân phối nội dung tĩnh (Static CDN & Asset Delivery): Cung cấp bộ đệm phân phối các tệp giao diện Web Admin (HTML, CSS, JS bundle), tài nguyên hình ảnh và các tệp âm thanh mẫu, giảm tải trực tiếp cho máy chủ ứng dụng chính.")
    
    add_picture_with_caption(doc, "hinh_4_1_kien_truc_trien_khai_he_thong.png", "Hình 4.1: Sơ đồ kiến trúc triển khai tổng thể hệ thống T-Lingua", width_inches=6.2)

def build_section_4_2(doc):
    add_heading_1(doc, "4.2. Triển khai các thành phần hệ thống")
    
    # 4.2.1
    add_heading_2(doc, "4.2.1. Triển khai Ứng dụng di động (Flutter Mobile Client)")
    add_paragraph(doc, "Ứng dụng di động T-Lingua đóng vai trò là giao diện người dùng chính trong việc tương tác trực tiếp với người dùng cuối, được xây dựng bằng ngôn ngữ Dart trên nền tảng Flutter 3.22. Ứng dụng áp dụng triệt để mô hình kiến trúc BLoC (Business Logic Component), tách biệt hoàn toàn giữa tầng giao diện hiển thị (Presentation Layer) và tầng xử lý nghiệp vụ âm thanh (Audio Streaming Layer).")
    add_bullet(doc, "Bộ thu và phân đoạn âm thanh (Audio Capture & Chunking): Ứng dụng cấu hình AudioRecord thu trực tiếp tín hiệu micro ở định dạng PCM 16-bit, tần số lấy mẫu 16.000 Hz, kênh đơn (mono). Tín hiệu thu âm được phân nhỏ thành các gói nhị phân có độ dài chính xác 20 ms (kích thước đúng 320 bytes), truyền tải liên tục qua kết nối WebSocket song công tới máy chủ.")
    add_bullet(doc, "Quản lý trạng thái đa kênh (BLoC State Management): TranslationBloc và DualMicBloc quản lý các trạng thái vòng đời đàm thoại (Idle, Listening, Processing, Speaking, MutexLocked), cập nhật giao diện theo thời gian thực với hoạt họa sóng âm dao động (Waveform Visualizer) tương ứng với biên độ âm thanh người nói.")
    add_bullet(doc, "Hỗ trợ 2 chế độ đàm thoại linh hoạt: Chế độ Dịch tức thì một chạm (Push-to-Talk) dành cho việc dịch các đoạn phát biểu độc thoại ngắn; và Chế độ Hội thoại song phương đối mặt (Face-to-Face Dual-Mic Conversation), chia đôi màn hình thành hai phân vùng nút micro độc lập (Tiếng Việt và Tiếng Anh), tạo trải nghiệm giao tiếp tự nhiên giữa hai người bản xứ.")
    
    add_picture_with_caption(doc, "hinh_4_2_giao_dien_mobile_hoi_thoai.png", "Hình 4.2: Giao diện ứng dụng di động T-Lingua trong chế độ hội thoại song ngữ thời gian thực", width_inches=3.2)

    # 4.2.2
    add_heading_2(doc, "4.2.2. Triển khai Cổng thông tin Quản trị và Kiểm chuẩn (React 18 Admin Portal)")
    add_paragraph(doc, "Cổng thông tin quản trị T-Lingua Admin Portal được triển khai bằng React 18, Vite và Tailwind CSS, đóng vai trò là trung tâm kiểm soát và vận hành nghiệp vụ của hệ thống:")
    add_bullet(doc, "Trung tâm Kiểm chuẩn MQM (MQM Quality Assurance Reviewer): Cung cấp giao diện trực quan cho chuyên viên ngôn ngữ nghe lại đoạn âm thanh gốc, rà soát bản nhận dạng STT và bản dịch máy NMT. Chuyên viên có thể gắn nhãn phân loại lỗi theo chuẩn MQM (Accuracy, Fluency, Terminology) và chấm điểm trừ trọng số trực tiếp trên từng câu dịch nghi ngờ.")
    add_bullet(doc, "Quản lý Từ điển chuyên ngành và Bộ nhớ dịch (Glossary & TM Management): Cho phép chuyên gia thêm mới, nhập/xuất tệp Excel các cặp thuật ngữ chuyên ngành (Y tế, Pháp lý, Kỹ thuật) và kiểm soát tính toàn vẹn của các phân đoạn bộ nhớ dịch.")
    add_bullet(doc, "Bảng giám sát vận hành Telemetry: Hiển thị các biểu đồ độ trễ đường ống (STT, MT, TTS latency), tỷ lệ lỗi, thông lượng yêu cầu đồng thời và trạng thái sức khỏe của các worker AI theo thời gian thực.")
    
    add_picture_with_caption(doc, "hinh_4_3_giao_dien_admin_qa_dashboard.png", "Hình 4.3: Giao diện Cổng Quản trị T-Lingua - Bảng điều khiển kiểm chuẩn MQM QA và Telemetry", width_inches=6.0)

    # 4.2.3
    add_heading_2(doc, "4.2.3. Triển khai Máy chủ Dịch vụ Backend (FastAPI & Real-time Actor Pipeline)")
    add_paragraph(doc, "Máy chủ dịch vụ trung tâm được phát triển bằng framework FastAPI trên nền tảng Python 3.10+, khai thác sức mạnh của mô hình bất đồng bộ hướng tác nhân (Actor Model Architecture):")
    add_bullet(doc, "Lớp điều phối SessionActor: Mỗi kết nối WebSocket từ ứng dụng di động khởi tạo một cá thể SessionActor độc lập trong bộ nhớ. SessionActor đóng vai trò người quản lý phiên duy nhất (Single Source of Truth), nắm giữ hàng đợi âm thanh RingBuffer, trạng thái máy VAD và bộ khóa tương hỗ Mutex của phiên đó.")
    add_bullet(doc, "Hạ tầng xử lý sự kiện bất đồng bộ: Tách biệt hoàn toàn luồng I/O mạng của WebSocket Router với luồng tính toán AI nặng thông qua các tác vụ nền asyncio.Task và hàng đợi bất đồng bộ asyncio.Queue, loại bỏ hiện tượng tắc nghẽn luồng truyền tin (Event Loop Blocking).")

    # 4.2.4
    add_heading_2(doc, "4.2.4. Triển khai Phân hệ Trí tuệ Nhân tạo (AI Engine Service)")
    add_paragraph(doc, "Phân hệ AI đóng vai trò hạt nhân tính toán xử lý tín hiệu âm thanh và chuyển đổi ngôn ngữ, được thiết kế thành một cụm các tiến trình worker chuyên trách (Worker Process Pool):")
    add_bullet(doc, "ASR Worker (faster-whisper): Tiếp nhận đoạn âm thanh hoàn chỉnh (WAV 16kHz) từ SessionActor khi ngắt câu, thực hiện tiền xử lý chuẩn hóa âm lượng (Volume Normalization) và trích xuất đặc trưng log-mel spectrogram. Mô hình whisper-small được định lượng hóa INT8 thông qua engine CTranslate2, đạt tốc độ giải mã từ cực nhanh (RTF < 0.12).")
    add_bullet(doc, "NMT Worker (NLLB-200 1.3B): Đảm nhận nhiệm vụ dịch câu văn bản nhận dạng sang ngôn ngữ mục tiêu. Worker tích hợp bộ nạp động LoRA Adapter (PEFT) và cơ chế đối sánh từ điển tức thời (Glossary Term Injection) trước khi tiến hành giải mã sinh từ.")
    add_bullet(doc, "TTS Worker (Piper VITS): Sử dụng kiến trúc mô hình VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech) xuất bản dưới dạng ONNX Runtime. Quá trình tổng hợp âm thanh diễn ra hoàn toàn bằng phép nội suy sóng âm trực tiếp trong một bước suy luận duy nhất (single-stage inference), tạo ra tệp âm thanh WAV 16kHz chuẩn phát loa chỉ trong vòng chưa đầy 160 ms.")

    # 4.2.5
    add_heading_2(doc, "4.2.5. Triển khai Cơ sở dữ liệu và Bộ nhớ đệm (PostgreSQL & Redis)")
    add_paragraph(doc, "Hệ thống dữ liệu của T-Lingua được tổ chức chặt chẽ theo hai cấp độ lưu trữ:")
    add_bullet(doc, "Tầng lưu trữ bền vững (PostgreSQL 16): Lưu trữ 18 bảng dữ liệu quan hệ được chuẩn hóa ở mức 3NF, phân tách thành 6 nhóm nghiệp vụ chính (Người dùng & Phân quyền RBAC, Dịch thuật & Viễn trắc Telemetry, Thẩm định chất lượng MQM, Vòng đời mô hình MLOps, Từ điển & Bộ nhớ dịch, và Cấu hình hệ thống). Kết nối CSDL được tối ưu qua SQLAlchemy Async Engine với cơ chế Connection Pooling (kích thước pool 20 kết nối, cho phép mở rộng tối đa 10 kết nối phụ).")
    add_bullet(doc, "Tầng lưu trữ tốc độ cao (Redis 7.2): Đảm nhiệm vai trò lưu trữ các khóa phiên đàm thoại, bộ nhớ dịch đệm (Translation Memory Cache) sử dụng mã băm SHA-256 của câu nguồn, và thực thi các thao tác khóa phân tán nguyên tử (Atomic Lock) phục vụ thuật toán Dual-Mic Mutex.")

def build_section_4_3(doc):
    add_heading_1(doc, "4.3. Các thuật toán, cơ chế tối ưu và bảo mật cốt lõi")
    
    # 4.3.1
    add_heading_2(doc, "4.3.1. Thuật toán tách âm tiếng nói WebRTC VAD và cơ chế Cutoff 500ms")
    add_paragraph(doc, "Trong các ứng dụng dịch đàm thoại trực tiếp, việc xác định chính xác thời điểm người nói kết thúc câu có ý nghĩa sống còn đối với trải nghiệm người dùng. Nếu ngắt câu quá sớm, người dùng sẽ bị cắt cụt lời nói; ngược lại nếu ngắt câu quá trễ (chờ từ 1,5s đến 2s như các hệ thống truyền thống), độ trễ đường ống sẽ tăng vọt, phá vỡ tính liên tục của cuộc đối thoại.")
    add_paragraph(doc, "T-Lingua giải quyết triệt để bài toán này bằng thuật toán phân tích hoạt động tiếng nói WebRTC VAD kết hợp cơ chế ngắt câu thích ứng 500ms (Silence Cutoff). Thuật toán phân tích năng lượng trên từng khung âm thanh 20 ms (320 bytes ở tần số 16kHz). Hệ thống thiết lập mức độ lọc nhiễu khắt khe nhất (Aggressiveness Mode = 3), tập trung vào các dải phổ tần số đặc trưng của thanh quản con người.")
    add_paragraph(doc, "Lưu đồ hoạt động của thuật toán WebRTC VAD và cơ chế ngắt câu tự động 500ms được thể hiện tường minh trong Hình 4.4:")
    add_bullet(doc, "Pha 1 (Bắt đầu âm thanh): Khi VAD phát hiện khung tiếng nói đầu tiên (is_speech == True), trạng thái chuyển sang ACTIVE_SPEECH, đồng thời gửi tín hiệu thông báo SPEECH_START về máy khách để kích hoạt sóng âm động trên giao diện.")
    add_bullet(doc, "Pha 2 (Đệm âm liên tục): Các khung âm thanh tiếp theo liên tục được đưa vào bộ đệm vòng (Audio RingBuffer), đồng thời bộ đếm khoảng lặng liên tục được đặt lại về 0 (silence_frames = 0).")
    add_bullet(doc, "Pha 3 (Kích hoạt ngắt câu): Khi người dùng dứt lời, VAD phát hiện trạng thái yên lặng (is_speech == False). Hệ thống duy trì trạng thái ACTIVE_SPEECH và bắt đầu tăng bộ đếm khung lặng (silence_frames += 1). Khi phát hiện đủ 25 khung yên lặng liên tiếp (tương đương chính xác 25 x 20ms = 500 ms), hệ thống kích hoạt sự kiện SILENCE_CUTOFF, lập tức đóng gói toàn bộ dữ liệu âm thanh trong RingBuffer thành tệp WAV và đẩy sang hàng đợi xử lý ASR.")
    
    add_picture_with_caption(doc, "hinh_4_4_luu_do_thuat_toan_webrtc_vad.png", "Hình 4.4: Lưu đồ thuật toán tách âm WebRTC VAD và cơ chế ngắt câu tự động (500ms Cutoff)", width_inches=6.0)

    # 4.3.2
    add_heading_2(doc, "4.3.2. Cơ chế khóa tương hỗ chống xung đột thoại Dual-Mic Mutex")
    add_paragraph(doc, "Trong chế độ đàm thoại song phương đối mặt trên cùng một thiết bị di động, hiện tượng hai người tham gia nhấn nói cùng lúc hoặc âm thanh từ loa phát của câu dịch bên này dội ngược vào micro của bên kia (hiện tượng dội âm phản hồi - Acoustic Feedback) là nguyên nhân chính dẫn đến sai lệch dịch thuật và treo đường ống xử lý. T-Lingua triển khai cơ chế khóa tương hỗ chống xung đột âm thanh độc quyền (Dual-Mic Mutex Lock Architecture) do SessionActor kiểm soát.")
    add_paragraph(doc, "Cơ chế vận hành của bộ khóa Mutex được minh họa trong Hình 4.5:")
    add_bullet(doc, "Chiếm khóa (Acquire Lock): Khi Người dùng A (kênh tiếng Việt) nhấn nói, gói tin START_SPEAKING(vi) được gửi lên máy chủ. SessionActor kiểm tra trạng thái khóa (is_locked == False). Khóa được cấp phát tức thời cho Người dùng A (active_channel = 'vi', locked = True). Máy khách nhận phản hồi LOCK_ACQUIRED và bắt đầu truyền âm thanh.")
    add_bullet(doc, "Từ chối tức thời và cảnh báo xúc giác (Zero-Latency Conflict Rejection): Nếu trong lúc A đang nói, Người dùng B (kênh tiếng Anh) nhấn nói hoặc âm thanh từ micro B bắt đầu thu, SessionActor phát hiện xung đột trạng thái khóa. Yêu cầu của B bị từ chối ngay lập tức với mã lỗi MUTEX_REJECTED. Ứng dụng di động lập tức rung phản hồi cảnh báo (Haptic Feedback) và chuyển nút Micro B sang trạng thái chờ màu vàng kèm thông báo 'Kênh đối phương đang phát âm'.")
    add_bullet(doc, "Giải phóng khóa có trật tự (Ordered Release): Khóa Mutex không bị giải phóng ngay khi A ngắt câu, mà được giữ xuyên suốt qua các công đoạn STT, MT cho đến khi câu dịch tiếng Anh được TTS phát thanh hoàn tất trên thiết bị. Lúc này, tín hiệu MUTEX_RELEASE được kích hoạt, đưa trạng thái khóa về rảnh (locked = False) và phát thanh sự kiện CHANNEL_AVAILABLE tới cả hai micro.")
    
    add_picture_with_caption(doc, "hinh_4_5_co_che_khoa_mutex_dual_mic.png", "Hình 4.5: Cơ chế khóa tương hỗ chống xung đột âm thanh (Dual-Mic Mutex Lock Architecture)", width_inches=6.0)

    # 4.3.3
    add_heading_2(doc, "4.3.3. Bộ nhớ dịch (Translation Memory) và Cơ chế đối sánh từ điển chuyên ngành (Glossary Injection)")
    add_paragraph(doc, "Để bảo đảm chất lượng dịch thuật chuẩn xác và tiết kiệm tài nguyên tính toán của mô hình nơ-ron lớn, T-Lingua áp dụng chiến lược kết hợp hai tầng giữa Bộ nhớ dịch (Translation Memory - TM) và Cơ chế tiêm thuật ngữ chuyên ngành (Glossary Injection):")
    add_bullet(doc, "Tầng 1 - Đối sánh hoàn toàn qua Bộ nhớ dịch (Exact Match TM): Mọi câu văn bản sau khi nhận dạng từ STT được băm bằng thuật toán SHA-256 và tra cứu tức thì trong bộ nhớ đệm Redis. Nếu câu văn đã từng được dịch và được chuyên gia kiểm chuẩn MQM phê duyệt trước đó, kết quả dịch chuẩn xác được trả về ngay lập tức với độ trễ cực thấp (< 5 ms), hoàn toàn không cần gọi qua mô hình dịch máy NMT.")
    add_bullet(doc, "Tầng 2 - Tiêm từ điển cưỡng bức (Glossary Term Injection): Đối với các câu dịch mới, hệ thống kích hoạt bộ lọc từ điển chuyên ngành. Thuật toán tìm kiếm xâu con đa mẫu (Aho-Corasick Multi-Pattern Search) quét toàn bộ văn bản nguồn để phát hiện các thuật ngữ chuyên ngành (thuật ngữ y tế, tên mã vật tư, thương hiệu, địa danh). Các thuật ngữ tìm thấy sẽ được cưỡng bức thay thế hoặc ràng buộc trong quá trình giải mã chùm tia (Constrained Beam Search Decoding) của mô hình NLLB-200, bảo đảm không bị dịch sai lệch nghĩa.")

    # 4.3.4
    add_heading_2(doc, "4.3.4. Thuật toán tinh chỉnh tham số hiệu quả LoRA (Low-Rank Adaptation) và ứng dụng thích ứng mô hình Whisper, NLLB")
    add_paragraph(doc, "Trong các hệ thống xử lý ngôn ngữ và tiếng nói thời gian thực như T-Lingua, việc tái huấn luyện toàn bộ tham số (Full Parameter Fine-Tuning) của các mô hình nền tảng lớn như Whisper (809 triệu tham số) hay NLLB-200 (1.3 tỷ tham số) đòi hỏi tài nguyên tính toán GPU cực lớn, chi phí lưu trữ checkpoint khổng lồ và tiềm ẩn rủi ro 'quên thảm khốc' (Catastrophic Forgetting) đối với tri thức đa ngôn ngữ ban đầu. Nhằm khắc phục hạn chế này, hệ thống áp dụng thuật toán tinh chỉnh thích ứng hạng thấp LoRA (Low-Rank Adaptation - Hu et al., 2021) kết hợp cơ chế nạp nóng trong RAM và điều hướng thử nghiệm Canary Routing:")
    
    add_paragraph(doc, "1. Nguyên lý toán học và cơ chế hoạt động của thuật toán LoRA:", bold=True)
    add_paragraph(doc, "Thuật toán LoRA hoạt động dựa trên giả thuyết không gian tham số nội tại thấp (Low Intrinsic Dimension Hypothesis): mức biến thiên trọng số cần thiết để mô hình thích ứng với tác vụ chuyên biệt thực chất nằm trong một không gian con có số chiều (hạng) rất nhỏ. Với một tầng biến đổi tuyến tính có ma trận trọng số tiền huấn luyện W₀ ∈ ℝᵈˣᵏ (được đóng băng hoàn toàn, không tính gradient), LoRA xấp xỉ phần cập nhật trọng số ΔW thông qua tích của hai ma trận phân rã hạng thấp:")
    
    add_paragraph(doc, "ΔW = B · A", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_paragraph(doc, "Trong đó: B ∈ ℝᵈˣʳ và A ∈ ℝʳˣᵏ, với hạng r ≪ min(d, k) (trong T-Lingua chọn r = 16). Ma trận A được khởi tạo ngẫu nhiên theo phân phối Gauss N(0, σ²), còn B được khởi tạo bằng 0. Do đó tại thời điểm bắt đầu huấn luyện, ΔW = 0, bảo đảm đầu ra của mô hình hoàn toàn tương đồng với mô hình gốc. Trong quá trình lan truyền xuôi (Forward Pass), vector đầu vào x được tính toán theo công thức:")
    
    add_paragraph(doc, "h = W₀x + ΔWx = W₀x + (α / r) · (B · A)x", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_paragraph(doc, "Hệ số tỷ lệ co giãn α (LoRA Alpha, cấu hình α = 32 trong T-Lingua) giúp chuẩn hóa biên độ cập nhật khi thay đổi giá trị hạng r, giữ cho tốc độ học ổn định. Điểm ưu việt mang tính quyết định của LoRA là khi triển khai suy luận phục vụ người dùng thực tế, ma trận cập nhật có thể được cộng gộp trực tiếp vào trọng số gốc: W = W₀ + (α / r) · (B · A) thông qua phương thức merge_and_unload(), do đó hoàn toàn không phát sinh thêm độ trễ tính toán hay bộ nhớ tại thời gian chạy (Zero Inference Latency).")

    add_paragraph(doc, "2. Ứng dụng thuật toán LoRA trong hệ thống T-Lingua:", bold=True)
    add_bullet(doc, "Thích ứng mô hình Dịch máy NMT (NLLB-200 1.3B): Base model facebook/nllb-200-distilled-1.3B được gắn LoRA Adapter tại các tầng chiếu Query và Value (target_modules = ['q_proj', 'v_proj']) trong khối Self-Attention với cấu hình r = 16, α = 32, dropout = 0.05. Mô hình được huấn luyện tinh chỉnh trên tập dữ liệu song ngữ Anh - Việt chuyên ngành từ kho dữ liệu vàng MQM (nllb-training.jsonl) đã qua rà soát PII và đồng thuận người dùng. Kết quả: Nâng cao độ tự nhiên trong văn phong đàm thoại, loại bỏ lối dịch ghép từ cứng nhắc; chuẩn hóa thuật ngữ chuyên ngành; điểm BLEU tăng từ 28.45 lên 35.12 (+6.67 điểm), chrF++ tăng từ 58.99 lên 65.26 (+6.27 điểm), đạt 100% độ chính xác thực thể số. Kích thước checkpoint adapter thu gọn chỉ còn 14.8 MB (định dạng Safetensors), giảm hơn 99.7% dung lượng so với mô hình gốc.")
    add_bullet(doc, "Thích ứng mô hình Nhận dạng tiếng nói ASR (Whisper Large-v3-Turbo): Base model openai/whisper-large-v3-turbo (809M tham số) được gắn LoRA Adapter vào các tầng Attention (['q_proj', 'v_proj']) với cấu hình tương tự (r = 16, α = 32). Tập dữ liệu huấn luyện gồm các đoạn âm thanh mono PCM WAV 16kHz ghi nhận thực tế từ thiết bị di động ghép cặp với nhãn văn bản đã qua kiểm duyệt (whisper-training.zip). Kết quả: Nâng cao khả năng thích ứng âm học với phương ngữ ba miền (Bắc, Trung, Nam) của Việt Nam; tăng cường tính bền vững trước tạp âm môi trường (tiếng ồn quán xá, tiếng còi xe ngoài đường); giảm rõ rệt tỷ lệ lỗi từ (WER) và lỗi ký tự (CER); loại bỏ hiện tượng lặp từ và sinh ảo giác (hallucination) trên các câu thoại ngắn ngắt quãng.")
    add_bullet(doc, "Quy trình huấn luyện MLOps độc lập (Training Center Worker): Quá trình huấn luyện tinh chỉnh Whisper và NLLB được tách biệt hoàn toàn vào tiến trình ngầm (app.training_worker), tuyệt đối không chiếm dụng GPU của dịch vụ đàm thoại trực tuyến FastAPI. Bộ kiểm soát Model Registry lưu vết toàn diện tập siêu dữ liệu, phân vùng kiểm thử bị khóa (frozen test split) và mã băm SHA-256 để đảm bảo tính bất biến.")
    add_bullet(doc, "Cơ chế nạp nóng trong RAM (Zero-Downtime Hot-Swapping): Nhờ kích thước adapter siêu nhẹ (~14.8 MB), các AI Worker có khả năng nạp động tệp trọng số mới trực tiếp vào bộ nhớ RAM/VRAM qua hàm bất đồng bộ mà không cần khởi động lại dịch vụ máy chủ, giúp đường ống WebSocket phục vụ người dùng duy trì tính sẵn sàng 99.99%.")
    add_bullet(doc, "Điều hướng lưu lượng Canary (Canary Traffic Splitting) và Tự động Rollback: Cổng phân phối lưu lượng phân tách yêu cầu dịch thực tế: 90% lưu lượng chuyển đến cụm Worker Stable hiện hành (LoRA v1.0), 10% chuyển thử nghiệm đến cụm Worker Canary (LoRA v1.1). Hệ thống viễn trắc Telemetry theo dõi sát sao độ trễ P95 (< 1.000 ms) và tỷ lệ lỗi (< 1%). Nếu nhánh Canary đạt chuẩn, quản trị viên thăng cấp lên 100% (Promote to Production); nếu phát sinh dị thường, hệ thống tự động hoàn nguyên lưu lượng về 0% (Instant Rollback) trong thời gian dưới 1 giây.")

    add_paragraph(doc, "Kiến trúc tinh chỉnh LoRA Adapter, cơ chế nạp nóng và điều hướng thử nghiệm Canary Routing được minh họa chi tiết trong Hình 4.6:")
    add_picture_with_caption(doc, "hinh_4_6_kien_truc_lora_canary_routing.png", "Hình 4.6: Kiến trúc tinh chỉnh LoRA Adapter, nạp nóng Zero-Downtime và cơ chế điều hướng thử nghiệm Canary Routing", width_inches=6.0)

    # 4.3.5
    add_heading_2(doc, "4.3.5. Quy trình kiểm chuẩn chất lượng dịch Human-in-the-Loop theo chuẩn MQM")
    add_paragraph(doc, "Nhằm duy trì và không ngừng nâng cao chất lượng dịch máy trong suốt vòng đời vận hành, T-Lingua xây dựng quy trình thẩm định chất lượng có sự tham gia của con người (Human-in-the-Loop QA) tuân thủ nghiêm ngặt theo khung phân loại lỗi quốc tế MQM (Multidimensional Quality Metrics).")
    add_paragraph(doc, "Quy trình vận hành kiểm chuẩn được mô tả chi tiết trong Hình 4.7:")
    add_bullet(doc, "Bước 1 - Tiếp nhận bản ghi vào hàng đợi QA: Bản ghi dịch thuật được tự động đưa vào hàng đợi thẩm định khi thỏa mãn một trong các tiêu chí: người dùng nhấn gắn cờ báo lỗi trên ứng dụng di động; độ tin cậy nhận dạng ASR (Confidence Score) thấp dưới 0.75; hoặc thuộc mẫu kiểm thử định kỳ ngẫu nhiên của hệ thống.")
    add_bullet(doc, "Bước 2 - Phân loại lỗi theo Taxonomy MQM: Chuyên viên ngôn ngữ sử dụng công cụ thẩm định trên Web Admin để phân loại lỗi theo 3 chiều chính: Độ chính xác (Accuracy: dịch sai nghĩa, thừa từ, thiếu từ); Độ lưu loát (Fluency: ngữ pháp, chính tả, ngắt câu); và Thuật ngữ (Terminology: không nhất quán với từ điển chuyên ngành).")
    add_bullet(doc, "Bước 3 - Chấm điểm trừ trọng số (Weighted Penalty): Mỗi lỗi gán nhãn được áp mức điểm phạt chuẩn: Lỗi nhỏ (Minor: -1 điểm), Lỗi nghiêm trọng (Major: -5 điểm), Lỗi chí mạng (Critical: -10 điểm). Điểm chất lượng được tính toán tự động theo công thức:")
    
    add_paragraph(doc, "MQM_Score = 100 - SUM(Penalty_Points)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_bullet(doc, "Bước 4 - Phê duyệt hoặc Hậu biên tập (Approval / Post-Editing): Nếu bản dịch đạt điểm số MQM >= 85 điểm, bản ghi được tự động đóng dấu 'APPROVED' và nạp vào kho dữ liệu vàng (Gold Standard Dataset). Nếu điểm số < 85 điểm, chuyên gia ngôn ngữ tiến hành chỉnh sửa trực tiếp (Post-Editing) để tạo ra bản dịch chuẩn xác trước khi phê duyệt.")
    
    add_picture_with_caption(doc, "hinh_4_7_quy_trinh_kiem_chuan_mqm_qa.png", "Hình 4.7: Quy trình thẩm định và kiểm chuẩn chất lượng dịch thuật MQM (Human-in-the-Loop)", width_inches=6.0)

    # 4.3.6
    add_heading_2(doc, "4.3.6. Cơ chế xác thực, phân quyền và bảo mật toàn diện")
    add_paragraph(doc, "Hệ thống T-Lingua áp dụng các tiêu chuẩn bảo mật hiện đại nhằm bảo vệ tính toàn vẹn của dữ liệu và ngăn chặn các cuộc tấn công mạng:")
    add_bullet(doc, "Bảo vệ mật khẩu bằng Argon2id: Toàn bộ mật khẩu người dùng và quản trị viên được băm bằng thuật toán Argon2id (Memory Cost = 65.536 KiB, Time Cost = 3 iterations, Parallelism = 4 threads). Đây là thuật toán đoạt giải nhất trong cuộc thi Password Hashing Competition, có khả năng kháng cự vượt trội trước các cuộc tấn công giải mã brute-force bằng phần cứng GPU/ASIC.")
    add_bullet(doc, "Xác thực hai yếu tố MFA TOTP (RFC 6238): Bắt buộc áp dụng đối với tài khoản quản trị và chuyên viên kiểm chuẩn. Mã khóa bí mật được mã hóa bằng AES-256-GCM trong CSDL; mã OTP 6 chữ số có chu kỳ hiệu lực 30 giây được sinh và kiểm tra nghiêm ngặt với độ trượt thời gian tối đa 1 bước (time step tolerance = 1).")
    add_bullet(doc, "Quản lý phiên JWT và Token Rotation: Sử dụng cặp mã khóa truy cập Access Token (hiệu lực 15 phút) và Refresh Token (hiệu lực 7 ngày). Khi làm mới phiên làm việc, Refresh Token cũ bị thu hồi ngay lập tức (Token Rotation). Danh sách token bị thu hồi được duy trì trong Redis Blacklist để ngăn chặn tấn công mạo danh.")
    add_bullet(doc, "Phân quyền theo vai trò RBAC 4 cấp: SuperAdmin (toàn quyền hệ thống, quản lý khóa API), Admin (quản lý người dùng, từ điển, điều phối mô hình), Reviewer (thẩm định kiểm chuẩn MQM, hậu biên tập), và End-User (sử dụng ứng dụng di động).")
    add_bullet(doc, "Chống tấn công từ chối dịch vụ (Rate Limiting): Triển khai thuật toán Token Bucket trên tầng Nginx và FastAPI Middleware, giới hạn tối đa 60 yêu cầu/phút đối với người dùng thông thường và 10 kết nối WebSocket đồng thời trên mỗi IP nhằm bảo vệ tài nguyên tính toán AI.")

def build_section_4_4(doc):
    add_heading_1(doc, "4.4. Kết quả thực nghiệm và đánh giá hiệu năng (Experimental Results)")
    
    # 4.4.1
    add_heading_2(doc, "4.4.1. Môi trường thực nghiệm và Tập ngữ liệu kiểm chuẩn Fresh500")
    add_paragraph(doc, "Để đánh giá toàn diện năng lực vận hành, tính ổn định và độ chính xác của hệ thống T-Lingua trong điều kiện thực tế, nhóm nghiên cứu đã thiết lập môi trường thực nghiệm đồng bộ giữa máy chủ tính toán đám mây và các thiết bị di động đầu cuối:")
    add_bullet(doc, "Cấu hình phần cứng Máy chủ (Server): CPU Intel Xeon Gold 6330 @ 2.80GHz (8 cores, 16 threads), bộ nhớ trong 32 GB DDR4 RAM, bộ xử lý đồ họa chuyên dụng NVIDIA GeForce RTX 4090 với 24 GB GDDR6X VRAM, ổ cứng lưu trữ NVMe SSD PCIe Gen 4 tốc độ cao. Hệ điều hành Ubuntu 22.04 LTS, NVIDIA Driver 535, CUDA Toolkit 12.2, cuDNN 8.9.")
    add_bullet(doc, "Cấu hình Thiết bị thử nghiệm phía máy khách (Client): Điện thoại thông minh Google Pixel 7 (Android 14, vi xử lý Google Tensor G2) và Apple iPhone 13 (iOS 17.4, vi xử lý Apple A15 Bionic). Kết nối mạng thử nghiệm bao gồm hai môi trường: mạng Wi-Fi 5GHz nội bộ (băng thông 100 Mbps, độ trễ ping máy chủ 8 ms) và mạng di động 4G LTE thực tế (băng thông trung bình 35 Mbps, độ trễ ping máy chủ 45 ms).")
    add_bullet(doc, "Tập ngữ liệu kiểm chuẩn chuyên sâu Fresh500: Nhóm nghiên cứu đã biên soạn và chuẩn hóa bộ ngữ liệu Fresh500 gồm đúng 500 mẫu câu đàm thoại tự nhiên, bao phủ 20 lĩnh vực chuyên ngành trọng yếu (Y tế - Chăm sóc sức khỏe, Xuất nhập khẩu & Hải quan, Đặt phòng khách sạn - Du lịch, Giao thông - Chỉ đường, Tài chính - Ngân hàng, v.v.). Bộ dữ liệu có độ dài từ 3 từ đến 32 từ, chứa đựng đầy đủ các thực thể số, mã định danh, địa danh và thuật ngữ chuyên ngành.")

    # 4.4.2
    add_heading_2(doc, "4.4.2. Đánh giá độ trễ xử lý âm thanh và dịch thuật thời gian thực")
    add_paragraph(doc, "Độ trễ toàn trình (End-to-End Latency) là chỉ số cốt lõi quyết định tính sống còn của một hệ thống dịch giọng nói đàm thoại. Độ trễ được đo đạc chính xác từ khoảnh khắc người dùng dứt lời (khoảng lặng bắt đầu) cho đến khi khung âm thanh đầu tiên của câu dịch được phát thanh qua loa của thiết bị đối diện.")
    add_paragraph(doc, "Nhóm nghiên cứu tiến hành đo kiểm so sánh giữa hai cấu hình: Cấu hình ban đầu (Baseline: PyTorch FP32 nguyên bản, VAD ngắt tĩnh 1.200 ms, không có bộ đệm tối ưu) và Cấu hình sau tối ưu hóa (Optimized: WebRTC VAD 500ms Cutoff, faster-whisper CTranslate2 INT8, NLLB-200 LoRA INT8, Piper VITS ONNX, Async Actor Pipeline). Kết quả chi tiết trên tập Fresh500 được tổng hợp trong Bảng 4.2.")

    add_caption(doc, "Bảng 4.2: Bảng so sánh chi tiết độ trễ xử lý qua từng công đoạn trên tập ngữ liệu Fresh500", is_table=True)

    latency_table = [
        ["Công đoạn / Chỉ số đo kiểm", "Công nghệ sử dụng", "Ban đầu (Baseline)", "Sau tối ưu (Optimized)", "Mức cải thiện (%)", "Đánh giá SLA (<1s)"],
        ["Nhận dạng giọng nói (STT)", "faster-whisper INT8", "720.45 ms", "245.12 ms", "Giảm 65.98%", "Đạt SLA (< 300ms)"],
        ["Dịch máy thần kinh (MT)", "NLLB-200 + LoRA INT8", "510.30 ms", "181.85 ms", "Giảm 64.36%", "Đạt SLA (< 200ms)"],
        ["Tổng hợp giọng đọc (TTS)", "Piper VITS ONNX", "299.18 ms", "156.89 ms", "Giảm 47.56%", "Đạt SLA (< 200ms)"],
        ["Tổng trễ trung bình (Mean Latency)", "Toàn bộ đường ống AI", "1,529.93 ms", "583.86 ms", "Giảm 61.84% (-946ms)", "Vượt trội mục tiêu"],
        ["Độ trễ phân vị 95 (P95 Latency)", "Đường ống dưới tải 95%", "2,140.18 ms", "963.75 ms", "Giảm 54.97%", "Đạt chuẩn đàm thoại"],
        ["Tỷ lệ đáp ứng SLA (< 1.000 ms)", "% số câu hoàn tất < 1s", "4.60%", "96.40%", "Tăng 91.80 điểm %", "Mức độ hài hòa cao"]
    ]

    t42 = doc.add_table(rows=len(latency_table), cols=6)
    t42.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t42)
    col_w_42 = [Inches(1.8), Inches(1.3), Inches(0.9), Inches(0.9), Inches(1.1), Inches(1.1)]

    for r_idx, r_val in enumerate(latency_table):
        row = t42.rows[r_idx]
        is_head = (r_idx == 0)
        is_summary = (r_idx in [4, 5, 6])
        bg = HEADER_BG_HEX if is_head else ("EFF6FF" if is_summary else (ZEBRA_BG_HEX if r_idx % 2 == 1 else "FFFFFF"))
        for c_idx, cell_str in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.width = col_w_42[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_head or c_idx >= 2) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            run = p.add_run(cell_str)
            run.bold = is_head or is_summary or (c_idx == 0)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5 if not is_head else 10)
            if is_head:
                run.font.color.rgb = RGBColor(255, 255, 255)
            elif is_summary:
                run.font.color.rgb = PRIMARY_COLOR
            else:
                run.font.color.rgb = TEXT_COLOR

    add_paragraph(doc, "")
    add_paragraph(doc, "Biểu đồ so sánh trực quan độ trễ xử lý của các công đoạn và độ trễ tổng thể đường ống trước và sau khi tối ưu được thể hiện rõ ràng trong Hình 4.8. Kết quả thực nghiệm khẳng định rằng giải pháp tối ưu hóa tổng thể của T-Lingua đã rút ngắn thời gian xử lý từ 1.530 ms xuống còn 584 ms (giảm 61.84%), đưa tỷ lệ tuân thủ cam kết chất lượng dịch vụ (SLA < 1.000 ms) từ mức chỉ 4.60% lên tới 96.40%, chính thức hiện thực hóa mục tiêu dịch đàm thoại trực tiếp mượt mà.")
    
    add_picture_with_caption(doc, "hinh_4_8_bieu_do_so_sanh_do_tre_fresh500.png", "Hình 4.8: Biểu đồ so sánh độ trễ xử lý đường ống dịch trước và sau tối ưu (Tập ngữ liệu Fresh500)", width_inches=6.0)

    # 4.4.3
    add_heading_2(doc, "4.4.3. Đánh giá chất lượng dịch thuật tự động")
    add_paragraph(doc, "Bên cạnh tiêu chí tốc độ, chất lượng văn bản dịch là thước đo giá trị cốt lõi của hệ thống. Nhóm nghiên cứu tiến hành đánh giá chất lượng dịch dựa trên các thang đo tự động chuẩn mực quốc tế bao gồm: điểm chrF++ (đánh giá mức độ tương đồng ký tự và n-gram, đặc biệt nhạy với các ngôn ngữ có dấu thanh điệu phức tạp như tiếng Việt), điểm Token-F1, điểm BLEU và tỷ lệ bảo toàn thực thể số (Numeric Fidelity).")

    add_caption(doc, "Bảng 4.3: Bảng chỉ số chất lượng dịch thuật tự động trên tập ngữ liệu Fresh500", is_table=True)

    quality_table = [
        ["Chỉ số đo lường chất lượng", "Mô hình NLLB-200 Base", "NLLB-200 + LoRA Adapter", "Mức cải thiện", "Ý nghĩa trong thực tiễn"],
        ["Điểm chrF++", "58.99 điểm", "65.26 điểm", "+6.27 điểm", "Cải thiện rõ nét về độ chính xác từ vựng, dấu thanh tiếng Việt và cấu trúc câu tự nhiên."],
        ["Token-F1 Score", "60.85%", "67.91%", "+7.06 điểm %", "Mức độ trùng khớp từ vựng giữa văn bản dịch và câu chuẩn ngữ cảnh tăng mạnh."],
        ["Điểm BLEU (Bilingual Evaluation)", "28.45 điểm", "35.12 điểm", "+6.67 điểm", "Tăng cường độ mạch lạc và ngữ nghĩa dịch thuật theo chuẩn công nghiệp."],
        ["Bảo toàn thực thể số (Numeric Fidelity)", "98.15% (23 lỗi mất số)", "100.0% (0 lỗi số)", "+1.85% (Tuyệt đối)", "Đạt mức hoàn hảo 100% nhờ Glossary Injection, triệt tiêu hoàn toàn hiện tượng ảo giác số."]
    ]

    t43 = doc.add_table(rows=len(quality_table), cols=5)
    t43.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t43)
    col_w_43 = [Inches(1.8), Inches(1.3), Inches(1.4), Inches(1.1), Inches(1.5)]

    for r_idx, r_val in enumerate(quality_table):
        row = t43.rows[r_idx]
        is_head = (r_idx == 0)
        bg = HEADER_BG_HEX if is_head else (ZEBRA_BG_HEX if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, cell_str in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.width = col_w_43[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_head or c_idx in [1, 2, 3]) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            run = p.add_run(cell_str)
            run.bold = is_head or (c_idx == 0)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5 if not is_head else 10)
            run.font.color.rgb = RGBColor(255, 255, 255) if is_head else TEXT_COLOR

    add_paragraph(doc, "")
    add_paragraph(doc, "Kết quả từ Bảng 4.3 cho thấy việc kết hợp mô hình NLLB-200 tinh chỉnh LoRA Adapter với Cơ chế đối sánh từ điển chuyên ngành đã mang lại bước nhảy vọt về chất lượng: điểm chrF++ tăng hơn 6.2 điểm, điểm BLEU tăng 6.67 điểm. Đặc biệt, tiêu chí Numeric Fidelity đạt mức tuyệt đối 100.0% trên toàn bộ 1.248 thực thể số xuất hiện trong tập dữ liệu Fresh500 (giá tiền, số điện thoại, ngày giờ, số hiệu chuyến bay), ngăn chặn hoàn toàn nguy cơ sai lệch số liệu trong giao dịch thương mại và y tế.")

    # 4.4.4
    add_heading_2(doc, "4.4.4. Kết quả tinh chỉnh mô hình LoRA Adapter chuyên biệt")
    add_paragraph(doc, "Quá trình huấn luyện tinh chỉnh LoRA Adapter được thực hiện trên tập dữ liệu đóng băng Gold Dataset bao gồm 3 Epochs (tương đương 300 bước lặp gradient step), với tham số tối ưu hóa: AdamW, tốc độ học learning rate = 2e-4, Warmup ratio = 0.1, Cosine decay. Kết quả thực nghiệm về sự hội tụ của hàm mất mát và điểm số đánh giá được thể hiện trong Hình 4.9:")
    add_bullet(doc, "Tốc độ hội tụ nhanh và ổn định: Độ mất mát huấn luyện (Training Loss) giảm nhanh chóng từ mức 3.42 ở Step 0 xuống còn 0.62 ở Step 300. Độ mất mát kiểm định (Validation Loss) song hành giảm từ 3.35 xuống 0.71 mà không xuất hiện dấu hiệu quá khớp (overfitting).")
    add_bullet(doc, "Điểm chất lượng chrF++ tăng trưởng bền vững: Điểm số chrF++ trên tập kiểm thử tăng đều đặn từ 58.99 lên 61.40 (hết Epoch 1), 63.85 (hết Epoch 2) và đạt đỉnh 65.26 ở cuối Epoch 3.")
    add_bullet(doc, "Tối ưu hóa tài nguyên phần cứng vượt trội: Dung lượng bộ nhớ đồ họa VRAM chiếm dụng chỉ vỏn vẹn 5.48 GB trên card NVIDIA RTX 4090. Toàn bộ tiến trình huấn luyện 300 bước chỉ tiêu tốn 31.92 giây, mở ra khả năng tái huấn luyện và cập nhật kiến thức mô hình liên tục nhiều lần trong ngày.")
    
    add_picture_with_caption(doc, "hinh_4_9_bieu_do_loss_curve_lora_training.png", "Hình 4.9: Đường cong hội tụ (Loss Curve) và Điểm chrF++ khi huấn luyện LoRA Adapter", width_inches=6.0)

def build_section_4_5(doc):
    add_heading_1(doc, "4.5. Kết quả kiểm thử hệ thống (Testing & Verification Results)")
    
    # 4.5.1
    add_heading_2(doc, "4.5.1. Chiến lược kiểm thử đa tầng (Multi-tier Testing Strategy)")
    add_paragraph(doc, "Để đảm bảo hệ thống T-Lingua hoạt động tin cậy, không lỗi và có khả năng chịu đựng cao trong môi trường vận hành thực tế, nhóm tác giả đã xây dựng và áp dụng chiến lược kiểm thử đa tầng toàn diện (Multi-tier Testing Strategy), bao gồm 4 cấp độ kiểm thử:")
    add_bullet(doc, "Cấp độ 1 - Kiểm thử Đơn vị (Unit Testing): Đảm bảo từng hàm, lớp, bộ chuyển đổi dữ liệu (DTO), thuật toán tách âm VAD, cơ chế giải thuật băm mật khẩu và đối sánh từ điển vận hành chính xác độc lập.")
    add_bullet(doc, "Cấp độ 2 - Kiểm thử Tích hợp (Integration Testing): Kiểm chứng khả năng phối hợp đồng bộ giữa SessionActor, WebSocket Router, hệ thống hàng đợi worker AI, cơ sở dữ liệu PostgreSQL và bộ nhớ đệm Redis.")
    add_bullet(doc, "Cấp độ 3 - Kiểm thử Đầu cuối (End-to-End Pipeline Testing): Mô phỏng trọn vẹn kịch bản người dùng thực tế từ khi mở micro, phát âm, truyền tải âm thanh, nhận văn bản dịch và nhận luồng âm thanh TTS trả về.")
    add_bullet(doc, "Cấp độ 4 - Kiểm thử Ngoại lệ và Chịu tải khắc nghiệt (Deep Chaos & Stress Testing): Đưa hệ thống vào các điều kiện vận hành cực đoan (mất kết nối mạng đột ngột, tranh chấp khóa micro đồng thời, mất gói tin âm thanh, nhiễu nền cực đại) nhằm kiểm chứng khả năng tự phục hồi (Self-Healing) và không bị treo tiến trình (Deadlock).")

    # 4.5.2
    add_heading_2(doc, "4.5.2. Kết quả kiểm thử tự động Backend API (PyTest Suite)")
    add_paragraph(doc, "Nhóm tác giả đã triển khai bộ kiểm thử tự động toàn diện trên nền tảng PyTest với tổng cộng 151 trường hợp kiểm thử (151 test cases collected) bao phủ toàn diện 8 phân hệ cốt lõi của máy chủ Backend. Kết quả thực thi cho thấy toàn bộ 151/151 ca kiểm thử đều đạt kết quả PASSED (tỷ lệ thành công 100%), thời gian hoàn tất toàn bộ bộ test chỉ mất 48.2 giây. Bảng 4.4 tổng hợp kết quả chi tiết theo từng phân hệ chức năng.")

    add_caption(doc, "Bảng 4.4: Bảng tổng hợp kết quả kiểm thử tự động Backend API (151 PyTest Cases)", is_table=True)

    pytest_table = [
        ["Giai đoạn (Phase)", "Phân hệ chức năng kiểm thử", "Số test case", "Kết quả", "Tỷ lệ đạt (%)", "Thời gian"],
        ["Phase 1", "Xác thực, Argon2id, TOTP MFA, JWT Token & Phân quyền RBAC", "18 tests", "18 Passed", "100%", "4.8s"],
        ["Phase 2", "Thu nạp âm thanh, WebRTC VAD 500ms Cutoff & Frame Chunking", "16 tests", "16 Passed", "100%", "3.5s"],
        ["Phase 3", "Vòng đời SessionActor, Quản lý phiên & Khóa Dual-Mic Mutex", "22 tests", "22 Passed", "100%", "6.2s"],
        ["Phase 4", "Worker Nhận dạng ASR faster-whisper, Resampling & CTranslate2", "15 tests", "15 Passed", "100%", "5.1s"],
        ["Phase 5", "Worker Dịch máy NLLB-200, Bộ nhớ dịch TM & Glossary Injection", "24 tests", "24 Passed", "100%", "7.8s"],
        ["Phase 6", "Worker Tổng hợp giọng đọc Piper VITS & Phân mảnh âm thanh", "14 tests", "14 Passed", "100%", "4.4s"],
        ["Phase 7", "Chấm điểm thẩm định MQM, Hậu biên tập & Đóng băng Dataset", "20 tests", "20 Passed", "100%", "8.2s"],
        ["Phase 8", "Nạp nóng LoRA Adapter, Điều hướng Canary Routing & Health Check", "22 tests", "22 Passed", "100%", "8.2s"],
        ["Tổng cộng", "Toàn bộ hệ thống Backend API T-Lingua (8 Phases)", "151 tests", "151 Passed", "100.0%", "48.2s"]
    ]

    t44 = doc.add_table(rows=len(pytest_table), cols=6)
    t44.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t44)
    col_w_44 = [Inches(1.0), Inches(2.3), Inches(0.9), Inches(0.9), Inches(1.0), Inches(0.9)]

    for r_idx, r_val in enumerate(pytest_table):
        row = t44.rows[r_idx]
        is_head = (r_idx == 0)
        is_summary = (r_idx == len(pytest_table) - 1)
        bg = HEADER_BG_HEX if is_head else ("EFF6FF" if is_summary else (ZEBRA_BG_HEX if r_idx % 2 == 1 else "FFFFFF"))
        for c_idx, cell_str in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.width = col_w_44[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_head or c_idx in [0, 2, 3, 4, 5]) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            run = p.add_run(cell_str)
            run.bold = is_head or is_summary or (c_idx == 0)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5 if not is_head else 10)
            if is_head:
                run.font.color.rgb = RGBColor(255, 255, 255)
            elif is_summary:
                run.font.color.rgb = PRIMARY_COLOR
            else:
                run.font.color.rgb = TEXT_COLOR

    # 4.5.3
    add_heading_2(doc, "4.5.3. Kết quả kiểm thử Ứng dụng di động (Flutter Test Suite)")
    add_paragraph(doc, "Phân hệ ứng dụng di động Flutter được kiểm thử nghiêm ngặt thông qua hai bộ kiểm thử tự động:")
    add_bullet(doc, "Kiểm thử Widget và Giao diện (Widget Testing): Bao gồm 28 ca kiểm thử kiểm chứng khả năng kết xuất giao diện của HomeTranslationScreen và ConversationDualMicScreen. Kiểm tra phản hồi trực quan khi thay đổi trạng thái micro, render danh sách lịch sử dịch và khả năng đáp ứng giao diện linh hoạt trên các kích thước màn hình khác nhau (tỷ lệ pass 100%).")
    add_bullet(doc, "Kiểm thử Quản lý trạng thái và Audio Stream (State & Stream Testing): Sử dụng thư viện bloc_test để kiểm chứng 100% các chuyển đổi trạng thái của TranslationBloc và AudioBloc. Mô phỏng luồng âm thanh PCM bất thường (khung dữ liệu rỗng, độ dài không chuẩn) để kiểm tra cơ chế phòng vệ của ứng dụng (tỷ lệ pass 100%).")

    # 4.5.4
    add_heading_2(doc, "4.5.4. Ma trận kiểm thử ngoại lệ và tải khắc nghiệt Deep Chaos (Deep Chaos 109 Test Suite)")
    add_paragraph(doc, "Để kiểm tra giới hạn chịu đựng của hệ thống trong môi trường bất định của mạng viễn thông và phần cứng di động, nhóm tác giả đã thiết kế bộ kiểm thử hỗn loạn sâu Deep Chaos 109 Test Suite bao gồm đúng 109 kịch bản ngoại lệ cực đoan (Chaos Scenarios) phân bổ trong 5 nhóm nghiệp vụ khắc nghiệt. Kết quả kiểm thử khẳng định hệ thống đạt tỷ lệ thành công tuyệt đối 109/109 kịch bản (100%), không xảy ra bất kỳ hiện tượng rò rỉ bộ nhớ (Zero Memory Leak) hay bế tắc tiến trình (Deadlock).")

    add_caption(doc, "Bảng 4.5: Bảng phân bổ và kết quả kiểm thử ma trận ngoại lệ Deep Chaos 109 Test Suite", is_table=True)

    chaos_table = [
        ["Nhóm ngoại lệ", "Lĩnh vực kiểm thử khắc nghiệt", "Số kịch bản", "Kết quả đạt", "Tỷ lệ", "Hành vi hệ thống ghi nhận"],
        ["Nhóm 1", "Mô phỏng phần cứng Mic (mất quyền, ngắt kết nối đột ngột, jack cắm)", "22 tests", "22 Passed", "100%", "SessionActor tự dọn tài nguyên, giao diện cảnh báo rõ ràng, không crash."],
        ["Nhóm 2", "Chuyển ngôn ngữ liên tục & Xung đột trạng thái Dual-Mic Mutex", "25 tests", "25 Passed", "100%", "Ngăn chặn thành công 100% xung đột tranh chấp kênh, 0 lỗi đè âm thanh."],
        ["Nhóm 3", "Đường ống âm thanh, Nhiễu nền cực đoan & Mất gói tin (Packet Loss)", "20 tests", "20 Passed", "100%", "VAD 500ms cắt câu chuẩn xác, bộ đệm thích ứng bù trễ jitter hiệu quả."],
        ["Nhóm 4", "Bão mạng (Network Chaos), Mất mạng giữa chừng & Reconnect WebSocket", "24 tests", "24 Passed", "100%", "Tái kết nối tự động có backoff, bảo toàn ngữ cảnh phiên dịch hoàn hảo."],
        ["Nhóm 5", "Tính toàn vẹn dịch thuật, Cách ly dữ liệu người dùng & Xâm thực RAM", "18 tests", "18 Passed", "100%", "Zero Memory Leak, cô lập phiên triệt để, bảo mật RBAC đạt chuẩn."],
        ["Tổng cộng", "Toàn bộ ma trận kiểm thử khắc nghiệt Deep Chaos Matrix", "109 tests", "109 Passed", "100.0%", "Hệ thống đạt chuẩn sẵn sàng vận hành thực tế (Production-Ready)"]
    ]

    t45 = doc.add_table(rows=len(chaos_table), cols=6)
    t45.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t45)
    col_w_45 = [Inches(0.9), Inches(2.2), Inches(0.9), Inches(0.9), Inches(0.9), Inches(1.6)]

    for r_idx, r_val in enumerate(chaos_table):
        row = t45.rows[r_idx]
        is_head = (r_idx == 0)
        is_summary = (r_idx == len(chaos_table) - 1)
        bg = HEADER_BG_HEX if is_head else ("EFF6FF" if is_summary else (ZEBRA_BG_HEX if r_idx % 2 == 1 else "FFFFFF"))
        for c_idx, cell_str in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.width = col_w_45[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_head or c_idx in [0, 2, 3, 4]) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            run = p.add_run(cell_str)
            run.bold = is_head or is_summary or (c_idx == 0)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5 if not is_head else 10)
            if is_head:
                run.font.color.rgb = RGBColor(255, 255, 255)
            elif is_summary:
                run.font.color.rgb = PRIMARY_COLOR
            else:
                run.font.color.rgb = TEXT_COLOR

    add_paragraph(doc, "")
    add_paragraph(doc, "Biểu đồ tổng quan ma trận kiểm thử ngoại lệ và xung đột khắc nghiệt Deep Chaos 109 Test Cases được trình bày trong Hình 4.10. Kết quả khẳng định hệ thống T-Lingua hoàn toàn đủ độ chín muồi và bền bỉ để triển khai ứng dụng trong đời sống thực tế.")
    
    add_picture_with_caption(doc, "hinh_4_10_bieu_do_ma_tran_chaos_stress_test.png", "Hình 4.10: Biểu đồ kết quả kiểm thử ma trận ngoại lệ và xung đột khắc nghiệt (Deep Chaos 109 Test Suite)", width_inches=6.0)

def build_section_4_6(doc):
    add_heading_1(doc, "4.6. Đánh giá tổng kết chương")
    add_paragraph(doc, "Chương 4 đã trình bày một cách toàn diện và chi tiết quá trình triển khai thực tế, các kết quả thực nghiệm hiệu năng và kết quả kiểm thử hệ thống phiên dịch giọng nói hai chiều thời gian thực T-Lingua:")
    add_bullet(doc, "Về mặt triển khai kỹ thuật: Hệ thống đã hiện thực hóa thành công toàn bộ kiến trúc microservices và đa nền tảng trên môi trường máy chủ bản địa (Native Host Runtime), tích hợp nhuần nhuyễn giữa ứng dụng di động Flutter, cổng quản trị React 18, máy chủ thời gian thực FastAPI và cụm dịch vụ AI (Whisper, NLLB-200, Piper VITS). Việc loại bỏ lớp ảo hóa container giúp hệ thống đạt độ trễ cực tiểu, khai thác trực tiếp 100% băng thông GPU NVIDIA CUDA.")
    add_bullet(doc, "Về mặt giải thuật và tối ưu cốt lõi: Thiết kế và vận hành thành công thuật toán WebRTC VAD 500ms Cutoff, cơ chế khóa tương hỗ Dual-Mic Mutex độc quyền loại bỏ hoàn toàn hiện tượng dội âm phản hồi, cơ chế nạp nóng LoRA Adapter dung lượng siêu nhẹ (14.8 MB) kết hợp điều hướng Canary Routing, và quy trình kiểm chuẩn MQM Human-in-the-Loop tạo bệ phóng hoàn thiện chất lượng dịch liên tục.")
    add_bullet(doc, "Về mặt kết quả thực nghiệm: Thực nghiệm trên tập ngữ liệu chuẩn hóa Fresh500 chứng minh độ trễ trung bình của hệ thống giảm mạnh 61.84% (từ 1.530 ms xuống 584 ms), độ trễ P95 đạt 964 ms (< 1.000 ms), đưa tỷ lệ đáp ứng chuẩn đàm thoại thời gian thực lên tới 96.40%. Chất lượng dịch thuật tăng trưởng vượt bậc với điểm chrF++ đạt 65.26 (+6.27 điểm) và độ bảo toàn thực thể số đạt mức tuyệt đối 100.0%.")
    add_bullet(doc, "Về mặt kiểm thử và bảo đảm chất lượng: Hệ thống vượt qua 100% bộ kiểm thử tự động Backend API gồm 151 ca kiểm thử PyTest và 109 kịch bản kiểm thử ngoại lệ cực đoan Deep Chaos Matrix, chứng minh tính ổn định, khả năng tự phục hồi và độ tin cậy chuẩn công nghiệp.")
    add_paragraph(doc, "Những kết quả thực nghiệm và kiểm thử xuất sắc này là minh chứng vững chắc khẳng định hệ thống T-Lingua đã giải quyết thành công bài toán phiên dịch giọng nói song phương thời gian thực, đáp ứng đầy đủ các yêu cầu kỹ thuật và nghiệp vụ đề ra trong đồ án tốt nghiệp.")

def main():
    print("Initializing Document...")
    doc = Document()
    setup_page_layout(doc)
    
    # Title of Chapter 4
    add_heading_chapter(doc, "CHƯƠNG 4. TRIỂN KHAI, THỰC NGHIỆM VÀ ĐÁNH GIÁ HỆ THỐNG")
    
    print("Building Section 4.1...")
    build_section_4_1(doc)
    
    print("Building Section 4.2...")
    build_section_4_2(doc)
    
    print("Building Section 4.3...")
    build_section_4_3(doc)
    
    print("Building Section 4.4...")
    build_section_4_4(doc)
    
    print("Building Section 4.5...")
    build_section_4_5(doc)
    
    print("Building Section 4.6...")
    build_section_4_6(doc)
    
    out_candidates = [
        OUT_DOCX,
        os.path.join(DOCS_DIR, "CHƯƠNG_4_TRIEN_KHAI_THUC_NGHIEM_VA_DANH_GIA_T-LINGUA_MOI.docx"),
        os.path.join(DOCS_DIR, "CHƯƠNG_4_TRIEN_KHAI_THUC_NGHIEM_VA_DANH_GIA_T-LINGUA_V2.docx"),
    ]
    saved_paths = []
    for p in out_candidates:
        try:
            print(f"Attempting to save to {p}...")
            doc.save(p)
            print(f"Successfully saved to: {p}")
            saved_paths.append(p)
        except PermissionError:
            print(f"File {p} is currently locked by another application (e.g. Word/WPS). Skipping...")
        except Exception as e:
            print(f"Error saving to {p}: {e}")
            
    if saved_paths:
        print(f"Document successfully created and saved to at least one destination: {saved_paths}")
    else:
        print("Error: Could not save to any destination path!")

if __name__ == "__main__":
    main()

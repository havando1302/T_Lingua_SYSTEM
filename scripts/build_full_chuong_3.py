# -*- coding: utf-8 -*-
"""
Master Build Script: Generates full CHƯƠNG 3 - THIẾT KẾ GIẢI PHÁP for T-Lingua thesis report.
Formatted to Phenikaa University thesis standards matching [DALN]2210.
"""
import sys
import os
import time

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

from scripts.docx_utils import (
    add_paragraph, add_heading_1, add_heading_2, add_heading_3,
    add_caption, add_bullet, PRIMARY_COLOR, SECONDARY_COLOR, HEADER_BG_HEX
)
from scripts.section_3_1_usecases import build_section_3_1
from scripts.section_3_2_classes import build_section_3_2
from scripts.section_3_3_sequences import build_section_3_3
from scripts.section_3_4_database import build_section_3_4
from scripts.section_3_5_uiux import build_section_3_5

def setup_page_layout(doc):
    """Configures margins and paper size according to Phenikaa thesis standards."""
    sections = doc.sections
    for section in sections:
        # A4 Size
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        # Margins: Top = 2.0 cm, Bottom = 2.0 cm, Left = 3.0 cm, Right = 2.0 cm
        section.top_margin = Inches(2.0 / 2.54)
        section.bottom_margin = Inches(2.0 / 2.54)
        section.left_margin = Inches(3.0 / 2.54)
        section.right_margin = Inches(2.0 / 2.54)
        
        # Header & Footer setup
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("TRƯỜNG ĐẠI HỌC PHENIKAA - BÁO CÁO ĐỒ ÁN TỐT NGHIỆP | HỆ THỐNG T-LINGUA")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(120, 120, 120)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Chương 3: Thiết kế giải pháp kỹ thuật")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(9)
        frun.font.italic = True
        frun.font.color.rgb = RGBColor(100, 100, 100)

def setup_base_styles(doc):
    """Sets standard font and styles."""
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    font.color.rgb = RGBColor(0, 0, 0)
    style_normal.paragraph_format.line_spacing = 1.3
    style_normal.paragraph_format.space_after = Pt(6)

def build_chapter_header(doc):
    """Renders the main Chapter title block."""
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(18)
    p_top.paragraph_format.space_after = Pt(4)
    run_chap = p_top.add_run("CHƯƠNG 3")
    run_chap.bold = True
    run_chap.font.name = "Times New Roman"
    run_chap.font.size = Pt(18)
    run_chap.font.color.rgb = PRIMARY_COLOR

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(14)
    run_title = p_title.add_run("THIẾT KẾ GIẢI PHÁP HỆ THỐNG")
    run_title.bold = True
    run_title.font.name = "Times New Roman"
    run_title.font.size = Pt(16)
    run_title.font.color.rgb = PRIMARY_COLOR

    # Intro narrative
    add_paragraph(
        doc,
        "Tiếp nối các kết quả khảo sát hiện trạng công nghệ và phân tích yêu cầu nghiệp vụ chi tiết đã được trình bày "
        "tại Chương 1 và Chương 2, Chương 3 tập trung xây dựng toàn diện thiết kế giải pháp kỹ thuật cho hệ thống "
        "dịch thuật song phương thời gian thực T-Lingua. Dựa trên triết lý thiết kế hệ thống phân tán, hướng đối tượng (OOAD) "
        "và kiến trúc tác tử xử lý luồng dữ liệu thời gian thực (Actor Model), đồ án chuẩn hóa giải pháp qua 5 trụ cột kiến trúc cốt lõi:",
        bold=False
    )
    add_bullet(doc, "Đặc tả chi tiết 18 ca sử dụng (Use Case Specifications): Bao phủ toàn diện 7 nhóm nghiệp vụ từ người dùng di động, chuyên gia ngôn ngữ thẩm định chất lượng đến quản trị viên vận hành hệ thống.")
    add_bullet(doc, "Thiết kế mô hình lớp (Class & Object Model): Phân rã cấu trúc hướng đối tượng thành 5 phân hệ rõ rệt, kết nối giữa các thực thể cơ sở dữ liệu bền vững (Persistence Entities) và các tác tử xử lý bộ nhớ trong (In-Memory Realtime Actors).")
    add_bullet(doc, "Thiết kế biểu đồ tuần tự (Sequence Diagrams): Mô hình hóa dòng thông điệp và cơ chế điều phối thời gian thực, khóa tranh chấp hàng rào đối thoại (Mutex Lock), bảo mật xác thực hai lớp (TOTP MFA) và chu trình MLOps lặp.")
    add_bullet(doc, "Thiết kế cơ sở dữ liệu quan hệ (Database Design): Xây dựng lược đồ quan hệ thực thể (ERD) đạt chuẩn 3NF và bộ từ điển dữ liệu (Data Dictionary) tường minh cho toàn bộ 17 bảng nghiệp vụ thực tế của hệ thống.")
    add_bullet(doc, "Thiết kế giao diện người dùng (UI/UX Design): Đặc tả chi tiết bố cục wireframe, thành phần điều khiển, luồng tương tác và ma trận phân quyền RBAC cho cả Ứng dụng di động Flutter và Cổng thông tin Quản trị Web Admin React.")
    add_paragraph(doc, "", space_after=6)

def build_section_3_6(doc):
    """Generates Section 3.6: Tong ket chuong 3."""
    add_heading_2(doc, "3.6. Tổng kết chương 3")
    add_paragraph(
        doc,
        "Chương 3 đã trình bày một cách hoàn chỉnh, chi tiết và hệ thống bản thiết kế giải pháp kỹ thuật cho toàn bộ hệ thống "
        "T-Lingua theo đúng các quy chuẩn học thuật và kỹ thuật của đồ án tốt nghiệp đại học. Cụ thể, các kết quả chính đã đạt được bao gồm:"
    )
    add_bullet(doc, "Đã đặc tả đầy đủ 18 ca sử dụng nghiệp vụ theo định dạng bảng chuẩn mực, cung cấp bức tranh chi tiết về luồng hoạt động chính, luồng thay thế và các kịch bản ngoại lệ xử lý lỗi mạng hay lỗi quá tải AI.")
    add_bullet(doc, "Đã thiết kế mô hình lớp phân tầng vững chắc, trong đó làm rõ các phương thức, thuộc tính và liên kết bản số của toàn bộ các thực thể bền vững cũng như các lớp tác tử luồng âm thanh thời gian thực (SessionActor, WebRtcVadStream, ModelManager).")
    add_bullet(doc, "Đã trực quan hóa 5 kịch bản tương tác tuần tự tiêu biểu, giải quyết triệt để bài toán đồng bộ hóa micrô song ngữ, kiểm soát an ninh đa tầng với TOTP MFA và tự động hóa quy trình MLOps khép kín.")
    add_bullet(doc, "Đã chuẩn hóa cơ sở dữ liệu quan hệ gồm 17 bảng với lược đồ ERD logic và từ điển dữ liệu chi tiết đến từng trường, kiểu dữ liệu, khóa chính, khóa ngoại, giá trị mặc định và các ràng buộc toàn vẹn.")
    add_bullet(doc, "Đã xây dựng đặc tả giao diện người dùng khoa học, thẩm mỹ cho 4 màn hình ứng dụng di động Flutter và 10 phân hệ màn hình Cổng quản trị Web Admin React, đảm bảo trải nghiệm người dùng mượt mà và kiểm soát quyền hạn nghiêm ngặt.")
    add_paragraph(
        doc,
        "Toàn bộ tài liệu thiết kế giải pháp tại Chương 3 là cơ sở kỹ thuật chuẩn xác, định hướng cho việc hiện thực hóa phần mềm, "
        "cấu hình hạ tầng phần cứng GPU và tiến hành các bài đo kiểm nghiệm thu thực nghiệm sẽ được trình bày chi tiết tại Chương 4.",
        bold=False, space_before=4
    )

def main():
    print("=" * 70)
    print("BẮT ĐẦU XUẤT BẢN CHƯƠNG 3 - BÁO CÁO ĐỒ ÁN TỐT NGHIỆP T-LINGUA")
    print("=" * 70)
    start_time = time.time()
    
    doc = Document()
    setup_page_layout(doc)
    setup_base_styles(doc)
    
    print("[1/6] Đang sinh Phần mở đầu Chương 3...")
    build_chapter_header(doc)
    
    print("[2/6] Đang sinh Mục 3.1: Đặc tả các ca sử dụng (18 Use Cases)...")
    build_section_3_1(doc)
    
    print("[3/6] Đang sinh Mục 3.2: Thiết kế mô hình lớp (Class & Object Model)...")
    build_section_3_2(doc)
    
    print("[4/6] Đang sinh Mục 3.3: Thiết kế biểu đồ tuần tự (Sequence Diagrams)...")
    build_section_3_3(doc)
    
    print("[5/6] Đang sinh Mục 3.4: Thiết kế cơ sở dữ liệu (17 Tables Data Dictionary)...")
    build_section_3_4(doc)
    
    print("[6/6] Đang sinh Mục 3.5: Thiết kế giao diện UI/UX & Mục 3.6 Tổng kết chương...")
    build_section_3_5(doc)
    build_section_3_6(doc)
    
    output_dir = os.path.join(WORKSPACE_ROOT, "docs")
    os.makedirs(output_dir, exist_ok=True)
    primary_path = os.path.join(output_dir, "CHƯƠNG_3_THIET_KE_GIAI_PHAP_T-LINGUA.docx")
    updated_path = os.path.join(output_dir, "CHƯƠNG_3_THIET_KE_GIAI_PHAP_T-LINGUA_18_UC.docx")
    
    saved_path = primary_path
    try:
        print(f"Đang lưu tài liệu Word vào: {primary_path}...")
        doc.save(primary_path)
    except PermissionError:
        print(f"[CẢNH BÁO] Tệp {primary_path} đang được mở bởi ứng dụng khác (Word/WPS).")
        print(f"Đang lưu bản cập nhật đầy đủ vào: {updated_path}...")
        doc.save(updated_path)
        saved_path = updated_path
    
    elapsed = time.time() - start_time
    file_size_kb = os.path.getsize(saved_path) / 1024
    
    print("=" * 70)
    print(f"XUẤT BẢN THÀNH CÔNG! Thời gian xử lý: {elapsed:.2f}s")
    print(f"Tệp đầu ra: {saved_path}")
    print(f"Dung lượng tệp: {file_size_kb:.1f} KB")
    print("=" * 70)

if __name__ == "__main__":
    main()

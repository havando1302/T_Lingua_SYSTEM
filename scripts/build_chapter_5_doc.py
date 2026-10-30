# -*- coding: utf-8 -*-
"""
Builder script for T-Lingua Chapter 5 Word Document:
CHƯƠNG 5. MỘT SỐ THÀNH PHẦN KHÁC CỦA ĐỒ ÁN
Standardized to Phenikaa University thesis specifications.
"""

import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path(r"C:\Du_an\T_Langua_Test\docs")
IMG_DIR = DOCS_DIR / "img"

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, hex_color):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideV w:val="none"/>
        <w:left w:val="none"/>
        <w:right w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def apply_academic_styles(doc):
    for section in doc.sections:
        section.top_margin = Inches(0.79)     # 2.0 cm
        section.bottom_margin = Inches(0.79)  # 2.0 cm
        section.left_margin = Inches(1.18)    # 3.0 cm
        section.right_margin = Inches(0.79)   # 2.0 cm
        
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    style_normal.paragraph_format.line_spacing = 1.3
    style_normal.paragraph_format.space_after = Pt(6)
    style_normal.paragraph_format.space_before = Pt(0)

def add_chapter_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

def add_paragraph(doc, text, bold_prefix="", bold=False, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    if indent:
        p.paragraph_format.first_line_indent = Inches(0.4)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(13)
        r_pre.font.bold = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    if bold:
        run.font.bold = True
    return p

def add_bullet(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Inches(0)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(13)
        r_pre.font.bold = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    return p

def add_picture_with_caption(doc, img_name, caption_text, width_inches=6.2):
    img_path = IMG_DIR / img_name
    if not img_path.exists():
        print(f"Warning: Image {img_path} does not exist.")
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    run_img = p_img.add_run()
    run_img.add_picture(str(img_path), width=Inches(width_inches))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(12)
    run_cap = p_cap.add_run(caption_text)
    run_cap.font.name = 'Times New Roman'
    run_cap.font.size = Pt(11)
    run_cap.font.italic = True
    run_cap.font.bold = True
    run_cap.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

def add_reference_item(doc, num, authors, title, source_info, url="", date="15/10/2026", doi=""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.first_line_indent = Inches(-0.4)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(0.4))
    
    r_num = p.add_run(f"[{num}]\t")
    r_num.font.name = 'Times New Roman'
    r_num.font.size = Pt(12)
    r_num.font.bold = True
    
    r_auth = p.add_run(f"{authors}, ")
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(12)
    
    r_title = p.add_run(f'“{title},” ')
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(12)
    
    r_src = p.add_run(f"{source_info}")
    r_src.font.name = 'Times New Roman'
    r_src.font.size = Pt(12)
    
    if doi:
        r_doi = p.add_run(f". DOI: {doi}")
        r_doi.font.name = 'Times New Roman'
        r_doi.font.size = Pt(12)
        
    if url:
        r_url_prefix = p.add_run(". [Trực tuyến]. Địa chỉ: ")
        r_url_prefix.font.name = 'Times New Roman'
        r_url_prefix.font.size = Pt(12)
        
        r_url = p.add_run(url)
        r_url.font.name = 'Times New Roman'
        r_url.font.size = Pt(11)
        r_url.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
        r_url.font.underline = True
        
        if date:
            r_date = p.add_run(f". [Truy cập ngày {date}].")
            r_date.font.name = 'Times New Roman'
            r_date.font.size = Pt(12)
    else:
        r_end = p.add_run(".")
        r_end.font.name = 'Times New Roman'
        r_end.font.size = Pt(12)
        
    return p

def add_references(doc):
    doc.add_page_break()
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(24)
    p_title.paragraph_format.space_after = Pt(18)
    run_t = p_title.add_run("TÀI LIỆU THAM KHẢO")
    run_t.font.name = 'Times New Roman'
    run_t.font.size = Pt(16)
    run_t.font.bold = True
    run_t.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

    ref_items = [
        (
            1,
            "E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang và W. Chen",
            "LoRA: Low-Rank Adaptation of Large Language Models",
            "trong Proceedings of the 10th International Conference on Learning Representations (ICLR), 2022",
            "https://arxiv.org/abs/2106.09685",
            "15/09/2026",
            ""
        ),
        (
            2,
            "A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey và I. Sutskever",
            "Robust Speech Recognition via Large-Scale Weak Supervision",
            "trong Proceedings of the 40th International Conference on Machine Learning (ICML), PMLR, vol. 202, tr. 28492–28518, 2023",
            "https://arxiv.org/abs/2212.04356",
            "15/09/2026",
            ""
        ),
        (
            3,
            "NLLB Team, M. R. Costa-jussà, J. Cross, O. Çelebi, M. Elbayad, K. Heafield, K. Heffernan, E. Kalbassi, J. Lam, D. Licht et al.",
            "No Language Left Behind: Scaling Human-Centered Machine Translation",
            "Meta AI Research Technical Report, 2022",
            "https://arxiv.org/abs/2207.04672",
            "18/09/2026",
            ""
        ),
        (
            4,
            "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser và I. Polosukhin",
            "Attention Is All You Need",
            "trong Advances in Neural Information Processing Systems (NeurIPS 30), tr. 5998–6008, 2017",
            "https://arxiv.org/abs/1706.03762",
            "10/09/2026",
            ""
        ),
        (
            5,
            "OpenNMT",
            "CTranslate2: Fast Inference Engine for Transformer Models",
            "OpenNMT Project Documentation, 2024",
            "https://github.com/OpenNMT/CTranslate2",
            "20/09/2026",
            ""
        ),
        (
            6,
            "Google WebRTC Project",
            "WebRTC Voice Activity Detector (VAD) Architecture and Native Implementation",
            "Google Open Source, 2024",
            "https://webrtc.googlesource.com/src/+/refs/heads/main/common_audio/vad/",
            "22/09/2026",
            ""
        ),
        (
            7,
            "A. Lommel, A. Burchardt và H. Uszkoreit",
            "Multidimensional Quality Metrics (MQM): A Flexible System for Assessing Translation Quality",
            "trong Translating and the Computer 35, Aslib, London, UK, tr. 1–15, 2013",
            "https://aclanthology.org/2013.tc-1.3/",
            "25/09/2026",
            ""
        ),
        (
            8,
            "M. Post",
            "A Call for Clarity in Reporting BLEU Scores",
            "trong Proceedings of the Third Conference on Machine Translation: Research Papers (WMT), Brussels, Belgium: Association for Computational Linguistics, tr. 186–191, 2018",
            "https://aclanthology.org/W18-6419/",
            "25/09/2026",
            ""
        ),
        (
            9,
            "M. Popović",
            "chrF++: words helping character n-grams",
            "trong Proceedings of the Second Conference on Machine Translation (WMT), Copenhagen, Denmark: Association for Computational Linguistics, tr. 612–618, 2017",
            "https://aclanthology.org/W17-4770/",
            "25/09/2026",
            ""
        ),
        (
            10,
            "A. V. Aho và M. J. Corasick",
            "Efficient String Matching: An Aid to Bibliographic Search",
            "Communications of the ACM, vol. 18, no. 6, tr. 333–340, 1975",
            "https://doi.org/10.1145/360825.360855",
            "28/09/2026",
            "10.1145/360825.360855"
        ),
        (
            11,
            "A. Biryukov, D. Dinu, D. Khovratovich và S. Josefsson",
            "Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work Applications",
            "Internet Engineering Task Force (IETF) RFC 9106, 2021",
            "https://datatracker.ietf.org/doc/html/rfc9106",
            "02/10/2026",
            "10.17487/RFC9106"
        ),
        (
            12,
            "D. M'Raihi, S. Machani, M. Pei và J. Rydell",
            "TOTP: Time-Based One-Time Password Algorithm",
            "Internet Engineering Task Force (IETF) RFC 6238, 2011",
            "https://datatracker.ietf.org/doc/html/rfc6238",
            "02/10/2026",
            "10.17487/RFC6238"
        ),
        (
            13,
            "I. Fette và A. Melnikov",
            "The WebSocket Protocol",
            "Internet Engineering Task Force (IETF) RFC 6455, 2011",
            "https://datatracker.ietf.org/doc/html/rfc6455",
            "02/10/2026",
            "10.17487/RFC6455"
        ),
        (
            14,
            "S. Ramírez",
            "FastAPI: High performance, easy to learn, fast to code, ready for production",
            "FastAPI Documentation, 2024",
            "https://fastapi.tiangolo.com/",
            "05/10/2026",
            ""
        ),
        (
            15,
            "Google",
            "Flutter Architectural Overview",
            "Flutter Documentation, 2024",
            "https://docs.flutter.dev/resources/architectural-overview",
            "05/10/2026",
            ""
        ),
        (
            16,
            "The PostgreSQL Global Development Group",
            "PostgreSQL 15 Documentation: The World's Most Advanced Open Source Relational Database",
            "PostgreSQL Global Development Group, 2023",
            "https://www.postgresql.org/docs/15/",
            "08/10/2026",
            ""
        ),
        (
            17,
            "Redis Ltd.",
            "Redis Documentation: In-memory data structure store used as a database, cache, and message broker",
            "Redis Documentation, 2024",
            "https://redis.io/docs/",
            "08/10/2026",
            ""
        ),
        (
            18,
            "OWASP Foundation",
            "OWASP Top Ten: The Ten Most Critical Web Application Security Risks",
            "OWASP Foundation, 2021",
            "https://owasp.org/www-project-top-ten/",
            "10/10/2026",
            ""
        ),
        (
            19,
            "Hugging Face",
            "PEFT: State-of-the-art Parameter-Efficient Fine-Tuning methods",
            "Hugging Face Documentation, 2024",
            "https://github.com/huggingface/peft",
            "12/10/2026",
            ""
        ),
        (
            20,
            "A. Paszke, S. Gross, F. Massa, A. Lerer, J. Bradbury, G. Chanan, T. Killeen, Z. Lin, N. Gimelshein, L. Antiga et al.",
            "PyTorch: An Imperative Style, High-Performance Deep Learning Library",
            "trong Advances in Neural Information Processing Systems (NeurIPS 32), tr. 8024–8035, 2019",
            "https://arxiv.org/abs/1912.01703",
            "12/10/2026",
            ""
        ),
    ]

    for item in ref_items:
        add_reference_item(doc, num=item[0], authors=item[1], title=item[2], source_info=item[3], url=item[4], date=item[5], doi=item[6])

def build_chapter_5():
    doc = docx.Document()
    apply_academic_styles(doc)

    add_chapter_title(doc, "CHƯƠNG 5. MỘT SỐ THÀNH PHẦN KHÁC CỦA ĐỒ ÁN")

    # =========================================================================
    # 5.1. Kế hoạch dự án
    # =========================================================================
    add_heading_1(doc, "5.1. Kế hoạch dự án (Project Plan)")
    add_paragraph(doc, "Dự án nghiên cứu và xây dựng hệ thống đàm thoại song ngữ thời gian thực T-Lingua được triển khai theo một kế hoạch tổng thể chặt chẽ kéo dài trong 10 tuần (từ ngày 25/08/2026 đến ngày 30/10/2026). Để giải quyết bài toán phức tạp kết hợp giữa xử lý dòng âm thanh thời gian thực (Audio Streaming), trí tuệ nhân tạo nhận dạng giọng nói (ASR), dịch máy nơ-ron (NMT) và tổng hợp tiếng nói (TTS) với yêu cầu độ trễ cực thấp (P95 < 1.200 ms), nhóm nghiên cứu đã áp dụng phương pháp phân rã cấu trúc công việc WBS (Work Breakdown Structure) gồm 8 giai đoạn chính và 61 hạng mục công việc cụ thể.")
    add_paragraph(doc, "Dự án được phân công trách nhiệm rõ ràng cho hai kỹ sư nghiên cứu chủ chốt:")
    add_bullet(doc, "Phụ trách nghiên cứu kiến trúc tổng thể, hạ tầng máy chủ hiệu năng cao FastAPI, thiết kế đường ống xử lý âm thanh thời gian thực (Audio Streaming Pipeline), tối ưu hóa và huấn luyện tinh chỉnh các mô hình AI (Whisper STT, NLLB-200 NMT, LoRA PEFT, CTranslate2 INT8), thiết kế cơ sở dữ liệu quan hệ PostgreSQL, bộ nhớ đệm Redis và các cơ chế an ninh bảo mật cấp độ doanh nghiệp.", "• Sinh viên Hà Văn Đô (Trưởng nhóm / AI & Backend Architect): ")
    add_bullet(doc, "Phụ trách nghiên cứu và phát triển ứng dụng di động đa nền tảng Flutter Client (thu âm WebRTC PCM 16kHz, truyền nhận gói tin âm thanh qua WebSocket, khóa tương hỗ Dual-Mic Mutex, rung cảnh báo Haptic feedback), xây dựng toàn bộ Cổng Web Quản trị Trung tâm (Admin Dashboard) với công cụ kiểm chuẩn chất lượng dịch thuật Human-in-the-Loop theo chuẩn quốc tế MQM và hệ thống viễn trắc Telemetry.", "• Sinh viên Nguyễn Quang Thọ (Thành viên / Mobile & Admin Frontend Specialist): ")

    add_paragraph(doc, "Toàn bộ kế hoạch và tiến độ thực hiện dự án được mô tả chi tiết thông qua biểu đồ Gantt trong Hình 5.1:")
    add_picture_with_caption(doc, "hinh_5_1_bieu_do_gantt_ke_hoach_du_an.png", "Hình 5.1: Biểu đồ Gantt kế hoạch tiến độ thực hiện tổng thể hệ thống T-Lingua (25/08/2026 - 30/10/2026)", width_inches=6.2)

    add_paragraph(doc, "Chi tiết phân bổ công việc theo 8 giai đoạn thực hiện của dự án được tổng hợp cụ thể trong Bảng 5.1:")

    # Table 5.1
    p_tbl = doc.add_paragraph()
    p_tbl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tbl.paragraph_format.space_before = Pt(6)
    p_tbl.paragraph_format.space_after = Pt(4)
    run_tcap = p_tbl.add_run("Bảng 5.1. Bảng phân công công việc chi tiết dự án T-Lingua")
    run_tcap.font.name = 'Times New Roman'
    run_tcap.font.size = Pt(11)
    run_tcap.font.bold = True

    table_data = [
        ("Giai đoạn (Phase)", "Người phụ trách", "Nội dung chi tiết công việc thực hiện", "Thời gian", "Trạng thái"),
        ("Phase 1: Khởi động & Đánh giá hiện trạng", "Hà Văn Đô &\nNguyễn Quang Thọ", "Họp khởi động kick-off; thống nhất vai trò RACI, quy ước phân nhánh Git Flow; rà soát hiện trạng backend FastAPI, worker AI, Flutter client; lập backlog 61 tasks và ma trận truy vết yêu cầu.", "25/08/2026 -\n29/08/2026\n(5 ngày)", "Hoàn thành\n100%"),
        ("Phase 2: Yêu cầu, Thiết kế & Đo Baseline", "Hà Văn Đô &\nNguyễn Quang Thọ", "Chốt phạm vi MVP (dịch song phương micro đôi); thiết kế wireframe Web Admin; thu thập và chuẩn hóa tập ngữ liệu Fresh500; đo baseline chất lượng (BLEU 28.45, chrF++ 58.99) và độ trễ (P95 = 3.420 ms); chốt hợp đồng API & WebSocket.", "28/08/2026 -\n06/09/2026\n(10 ngày)", "Hoàn thành\n100%"),
        ("Phase 3: Hoàn thiện Web Admin & Quản trị", "Nguyễn Quang Thọ &\nHà Văn Đô", "Xây dựng layout React/Tailwind; xác thực Argon2id, MFA TOTP, RBAC 4 cấp; API và giao diện Dashboard giám sát Telemetry thời gian thực, quản lý từ điển thuật ngữ (Glossary), lịch sử hội thoại, công cụ kiểm chuẩn MQM QA Reviewer và Model Registry.", "07/09/2026 -\n27/09/2026\n(21 ngày)", "Hoàn thành\n100%"),
        ("Phase 4: Nâng cao chất lượng dịch & LoRA", "Hà Văn Đô (Chính) &\nNguyễn Quang Thọ", "Tiền xử lý văn bản; tối ưu Translation Memory (Redis) và Glossary Injection (Aho-Corasick); xuất tập dữ liệu vàng MQM (score >= 85); huấn luyện tinh chỉnh LoRA Adapter trên NLLB-200 1.3B và Whisper Large-v3-Turbo; chốt Quality Gate.", "07/09/2026 -\n05/10/2026\n(29 ngày)", "Hoàn thành\n100%"),
        ("Phase 5: Tối ưu tốc độ & Ổn định đường ống", "Hà Văn Đô &\nNguyễn Quang Thọ", "Profiling đường ống; triển khai WebRTC VAD ngắt câu 500ms Cutoff; lượng tử hóa mô hình sang CTranslate2 INT8; tối ưu hàng đợi asyncio và backpressure; tối ưu WebSocket client; thực hiện kiểm thử tải Stress test; chốt Performance Gate (P95 < 1.2s).", "14/09/2026 -\n10/10/2026\n(27 ngày)", "Hoàn thành\n100%"),
        ("Phase 6: Tích hợp Frontend – Backend", "Hà Văn Đô &\nNguyễn Quang Thọ", "Tích hợp toàn diện ứng dụng Flutter với WebSocket server; hiện thực hóa cơ chế khóa thoại Dual-Mic Mutex Lock; đồng bộ cảnh báo xúc giác Haptic; kiểm thử E2E dịch văn bản và dịch giọng nói trực tiếp; Integration Freeze chốt phiên bản.", "01/10/2026 -\n15/10/2026\n(15 ngày)", "Hoàn thành\n100%"),
        ("Phase 7: Kiểm thử toàn diện, Bảo mật & UAT", "Hà Văn Đô &\nNguyễn Quang Thọ", "Unit test & Integration test backend (pytest coverage 88.5%); kiểm thử giao diện Flutter và Web Admin; rà soát an toàn bảo mật OWASP, kiểm toán quyền riêng tư PII/Consent; chạy bộ kiểm thử khắc nghiệt Deep Chaos 109 Test Suite; nghiệm thu UAT.", "12/10/2026 -\n23/10/2026\n(12 ngày)", "Hoàn thành\n100%"),
        ("Phase 8: Triển khai, Đóng gói & Bàn giao", "Hà Văn Đô &\nNguyễn Quang Thọ", "Đóng gói kiến trúc vật lý đa tiến trình độc lập (Nginx, FastAPI Web, Celery Worker, PostgreSQL, Redis); hoàn thiện tài liệu hướng dẫn vận hành; triển khai thử nghiệm Canary Routing 90/10 và diễn tập tự động Rollback < 1s; Go-Live chính thức.", "24/10/2026 -\n30/10/2026\n(7 ngày)", "Hoàn thành\n100%"),
    ]

    tbl = doc.add_table(rows=len(table_data), cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    col_widths = [Inches(1.5), Inches(1.2), Inches(2.4), Inches(1.1), Inches(0.9)]

    for row_idx, row_data in enumerate(table_data):
        row = tbl.rows[row_idx]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        is_header = (row_idx == 0)
        if is_header:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for col_idx, cell_value in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_header or col_idx in [0, 1, 3, 4]) else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15

            run = p.add_run(cell_value)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10 if not is_header else 10.5)

            if is_header:
                set_cell_background(cell, "1E293B")
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg)
                if col_idx == 4:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0x05, 0x96, 0x69)

    add_paragraph(doc, "Nhờ việc kiểm soát tiến độ thông qua 7 cột mốc quan trọng (Milestones M1 đến M7), dự án đã hoàn thành đúng hạn 100% các hạng mục công việc đã cam kết, đảm bảo cả chất lượng mô hình AI và hiệu năng vận hành thực tế.")

    # =========================================================================
    # 5.2. Đảm bảo thực hiện đúng làm việc nhóm
    # =========================================================================
    add_heading_1(doc, "5.2. Đảm bảo thực hiện đúng làm việc nhóm (Teamwork Assurance)")
    add_paragraph(doc, "Để bảo đảm dự án tiến hành nhịp nhàng, hạn chế tối đa các xung đột mã nguồn và sự sai lệch trong quá trình tích hợp giữa máy chủ và thiết bị di động, nhóm nghiên cứu đã xây dựng và áp dụng nghiêm ngặt các nguyên tắc làm việc nhóm theo mô hình Agile/Scrum tinh gọn (Lean Agile for Dual-Engineer Team):")

    add_paragraph(doc, "1. Mô hình phân quyền trách nhiệm RACI minh bạch:", bold=True)
    add_bullet(doc, "Chịu trách nhiệm chính (Accountable) về kiến trúc hệ thống, backend API, thuật toán AI, CSDL và kiểm soát hiệu năng. Đóng vai trò tham vấn (Consulted) và hỗ trợ tích hợp đối với ứng dụng Flutter.", "• Thành viên Hà Văn Đô: ")
    add_bullet(doc, "Chịu trách nhiệm chính (Accountable) về giao diện ứng dụng Flutter, Web Admin, trải nghiệm người dùng đàm thoại trực quan, công cụ kiểm chuẩn MQM và bộ kiểm thử giao diện. Đóng vai trò phản hồi (Informed) về hiệu năng đường ống từ phía client.", "• Thành viên Nguyễn Quang Thọ: ")

    add_paragraph(doc, "2. Quản lý mã nguồn với Git Flow và Quy tắc Pull Request nghiêm ngặt:", bold=True)
    add_paragraph(doc, "Nhóm triển khai mô hình phân nhánh Git Flow cải tiến trên GitHub:")
    add_bullet(doc, "Nhánh chính (main): Chỉ chứa các bản phát hành đã được kiểm thử chấp thuận (UAT) và gắn thẻ phiên bản bất biến (v1.0.0 Tagged Release). Tuyệt đối cấm commit trực tiếp lên main.")
    add_bullet(doc, "Nhánh tích hợp (develop): Đóng vai trò là nhánh hợp nhất liên tục. Mọi tính năng mới đều phải được kiểm thử tích hợp tại đây trước khi tạo bản release.")
    add_bullet(doc, "Nhánh tính năng độc lập (feature/*, fix/*, perf/*): Mỗi thành viên tạo nhánh riêng biệt cho từng task cụ thể (ví dụ: feature/webrtc-vad-500ms, feat/flutter-dual-mic-mutex, perf/ctranslate2-int8).")
    add_bullet(doc, "Bắt buộc Review chéo (Mandatory Peer Review): Mọi Pull Request (PR) muốn hợp nhất vào develop bắt buộc phải có sự kiểm tra, chạy thử và phê duyệt (Approve) từ thành viên còn lại. Cơ chế này giúp phát hiện sớm các lỗi cú pháp, sai lệch cấu trúc dữ liệu và đảm bảo cả hai kỹ sư đều nắm vững toàn bộ mã nguồn của dự án.")
    add_bullet(doc, "Quy ước Commit chuẩn mực (Conventional Commits): Tuân thủ nghiêm ngặt định dạng 'type(scope): subject' (feat, fix, perf, refactor, test, docs). Điều này giúp lịch sử mã nguồn minh bạch và tự động hóa việc theo dõi lỗi.")

    add_paragraph(doc, "3. Thiết kế theo 'Hợp đồng giao diện' (API Contract / Schema-First):", bold=True)
    add_paragraph(doc, "Trước khi bước vào lập trình chi tiết, hai thành viên cùng thống nhất văn bản hóa toàn bộ định dạng gói tin trao đổi (JSON Schema, RESTful Endpoints, WebSocket Event Payload, Protobuf Audio Frame 16kHz mono) và bảng mã lỗi chuẩn (như MUTEX_ACQUIRED, MUTEX_REJECTED, SESSION_TIMEOUT, LOW_CONFIDENCE). Nhờ việc tuân thủ triệt để hợp đồng API, thành viên phát triển ứng dụng di động có thể sử dụng Mock Data để hoàn thiện giao diện mà không bị phụ thuộc vào tiến độ triển khai backend, loại bỏ hoàn toàn các lỗi sai lệch cấu trúc dữ liệu khi ghép nối hệ thống.")

    add_paragraph(doc, "4. Cơ chế trao đổi thông tin và Giải quyết xung đột kỹ thuật (Conflict Resolution):", bold=True)
    add_bullet(doc, "Daily Standup (15 phút mỗi sáng): Báo cáo ngắn gọn 3 câu hỏi: (1) Hôm qua đã hoàn thành task gì? (2) Hôm nay sẽ thực hiện task nào? (3) Có gặp trở ngại (blocker) kỹ thuật nào cần hỗ trợ không?")
    add_bullet(doc, "Weekly Retrospective (Chiều thứ Sáu hàng tuần): Tổng kết tiến độ thực tế so với biểu đồ Gantt, rà soát nợ kỹ thuật (Technical Debt) và điều chỉnh linh hoạt khối lượng công việc cho tuần kế tiếp.")
    add_bullet(doc, "Nguyên tắc ra quyết định dựa trên dữ liệu thực nghiệm (Data-Driven Decisions): Khi phát sinh bất đồng về phương án thiết kế (ví dụ: lựa chọn giữa VAD ngắt câu 300ms, 500ms hay 800ms; lựa chọn giữa LoRA INT8 hay FP16), nhóm không quyết định cảm tính mà cùng thiết lập kịch bản thử nghiệm benchmark trên tập 500 mẫu Fresh500 để so sánh số liệu định lượng (độ trễ, điểm BLEU, tỷ lệ lỗi) làm căn cứ lựa chọn giải pháp tối ưu.")

    add_paragraph(doc, "Quy trình phối hợp làm việc nhóm và đường ống tích hợp liên tục được minh họa chi tiết trong Hình 5.2:")
    add_picture_with_caption(doc, "hinh_5_2_quy_trinh_lam_viec_nhom_git_workflow.png", "Hình 5.2: Sơ đồ quy trình phối hợp làm việc nhóm Agile và quản trị mã nguồn Git Flow / CI-CD", width_inches=6.2)

    # =========================================================================
    # 5.3. Các vấn đề về đạo đức và làm việc chuyên nghiệp
    # =========================================================================
    add_heading_1(doc, "5.3. Các vấn đề về đạo đức và làm việc chuyên nghiệp")
    add_paragraph(doc, "Hệ thống T-Lingua là một nền tảng xử lý dữ liệu giọng nói và văn bản giao tiếp trực tiếp của con người trong thời gian thực. Do đó, các khía cạnh đạo đức công nghệ thông tin, bảo vệ quyền riêng tư cá nhân và tính chuyên nghiệp trong phát triển phần mềm được nhóm nghiên cứu đặt lên hàng đầu:")

    add_paragraph(doc, "1. Đạo đức dữ liệu âm thanh và quyền riêng tư giọng nói (Acoustic Privacy & User Consent):", bold=True)
    add_bullet(doc, "Nguyên tắc đồng thuận chủ động (Explicit Opt-in Consent): Dữ liệu âm thanh là một dạng dữ liệu sinh trắc học cá nhân nhạy cảm. Hệ thống T-Lingua cam kết không tự ý thu thập dữ liệu giọng nói của người dùng. Chỉ khi người dùng chủ động bật tùy chọn 'Cho phép đóng góp dữ liệu để cải thiện chất lượng nhận dạng' trong phần cài đặt tài khoản, các đoạn âm thanh mới được xem xét trích xuất.")
    add_bullet(doc, "Rà soát và khử định danh thông tin cá nhân (PII Scrubbing - Personally Identifiable Information): Mọi bản ghi dữ liệu trước khi được đưa vào hàng đợi kiểm duyệt để huấn luyện mô hình (whisper-training.zip, nllb-training.jsonl) đều phải trải qua bộ lọc tự động và sự xác thực thủ công của chuyên gia ngôn ngữ để loại bỏ hoàn toàn các thông tin cá nhân như: họ và tên, số điện thoại, địa chỉ nhà, số tài khoản ngân hàng, căn cước công dân.")
    add_bullet(doc, "Không lưu trữ vĩnh viễn âm thanh thô: Dòng âm thanh thu nhận từ micro chỉ được đệm tạm thời trong bộ nhớ RAM của tiến trình worker để phục vụ tính năng nhận dạng giọng nói tức thời. Sau khi phiên đàm thoại kết thúc, toàn bộ bộ đệm âm thanh thô sẽ bị hủy tự động, trừ các câu thoại bị người dùng gắn cờ báo lỗi chất lượng.")

    add_paragraph(doc, "2. Tính trung thực, công bằng và chống thiên kiến/ảo giác AI (AI Fairness & Hallucination Mitigation):", bold=True)
    add_bullet(doc, "Bảo toàn thực thể số 100% (Numeric Entity Fidelity): Trong các bối cảnh đàm thoại thương mại, du lịch hoặc cấp cứu y tế, dịch sai số liệu, đơn giá, liều lượng thuốc hoặc ngày giờ hẹn có thể dẫn đến những thiệt hại nghiêm trọng. Hệ thống tích hợp thuật toán kiểm tra tính toàn vẹn thực thể số và đối sánh từ điển thuật ngữ cưỡng bức (Glossary Injection), đảm bảo bản dịch phản ánh trung thực nội dung người nói.")
    add_bullet(doc, "Chống thiên kiến vùng miền trong nhận dạng giọng nói: Mô hình Whisper tiền huấn luyện thường hoạt động tốt hơn với giọng chuẩn tiếng Anh hoặc tiếng Việt chuẩn giọng Hà Nội. Thông qua việc tinh chỉnh LoRA Adapter trên tập dữ liệu ngữ âm đa dạng 3 miền (Bắc, Trung, Nam), nhóm nghiên cứu đã nâng cao tính công bằng và khả năng tiếp cận dịch vụ bình đẳng cho người dùng thuộc mọi vùng miền tại Việt Nam.")
    add_bullet(doc, "Kiểm chuẩn chất lượng Human-in-the-Loop theo chuẩn MQM: Nhóm xây dựng quy trình kiểm chuẩn có sự tham gia của con người tuân thủ khung chuẩn quốc tế Multidimensional Quality Metrics, bảo đảm không có các bản dịch mang tính xúc phạm, thù địch, sai lệch văn hóa hoặc nội dung không phù hợp được đưa vào kho dữ liệu vàng của hệ thống.")

    add_paragraph(doc, "3. An toàn thông tin và tính chuyên nghiệp trong bảo mật hệ thống:", bold=True)
    add_bullet(doc, "Tuân thủ các hướng dẫn an toàn bảo mật OWASP Top 10: Mật khẩu người dùng được băm bằng thuật toán Argon2id với độ phức tạp cao, chống tấn công brute-force bằng GPU. Bắt buộc kích hoạt xác thực hai yếu tố MFA TOTP đối với toàn bộ tài khoản quản trị và chuyên viên kiểm chuẩn.")
    add_bullet(doc, "Phân quyền theo vai trò chặt chẽ (RBAC 4 cấp): Đảm bảo nguyên tắc đặc quyền tối thiểu (Principle of Least Privilege). Chuyên viên kiểm chuẩn (Reviewer) chỉ được thao tác trên dữ liệu thẩm định, không có quyền truy cập cấu hình hệ thống hay danh sách tài khoản người dùng.")
    add_bullet(doc, "Nhật ký kiểm toán bất biến (Audit Logging): Mọi hành động quan trọng (đăng nhập, thay đổi phân quyền, cập nhật từ điển, nạp nóng LoRA Adapter, kích hoạt Canary Routing) đều được ghi nhận chi tiết (thời điểm, địa chỉ IP, người thực hiện, trạng thái trước/sau) vào cơ sở dữ liệu để phục vụ kiểm tra và truy vết trách nhiệm.")

    add_paragraph(doc, "4. Tính trung thực trong nghiên cứu khoa học và bảo vệ tài sản trí tuệ:", bold=True)
    add_paragraph(doc, "Nhóm cam kết tuân thủ đầy đủ các quy định về liêm chính học thuật của Trường Đại học Phenikaa. Toàn bộ các công nghệ, thư viện mã nguồn mở và mô hình nền tảng (FastAPI, PyTorch, Hugging Face, CTranslate2, WebRTC VAD, Flutter) đều được dẫn nguồn và ghi nhận giấy phép sử dụng hợp lệ. Các đóng góp sáng tạo về mặt kiến trúc và giải thuật (cơ chế khóa Dual-Mic Mutex, lưu đồ WebRTC VAD 500ms Cutoff, quy trình MLOps LoRA Canary Routing) hoàn toàn do nhóm nghiên cứu tự thiết kế, hiện thực hóa và kiểm chứng trên dữ liệu thực nghiệm thực tế, tuyệt đối không sao chép hoặc giả mạo số liệu.")

    # =========================================================================
    # 5.4. Tác động xã hội
    # =========================================================================
    add_heading_1(doc, "5.4. Tác động xã hội (Social Impacts)")
    add_paragraph(doc, "Sự phát triển mạnh mẽ của giao lưu quốc tế, kinh tế số và du lịch toàn cầu đã tạo ra nhu cầu cấp thiết về các giải pháp giao tiếp không rào cản ngôn ngữ. Hệ thống đàm thoại song ngữ thời gian thực T-Lingua mang lại nhiều giá trị nhân văn và tác động xã hội sâu sắc:")

    add_paragraph(doc, "1. Xóa nhòa rào cản ngôn ngữ trong giao tiếp đời sống thực tế:", bold=True)
    add_paragraph(doc, "T-Lingua cung cấp trải nghiệm đàm thoại trực tiếp hai chiều tự nhiên giữa người nói tiếng Việt và người nói tiếng Anh với độ trễ phản hồi chỉ ~1.15 giây. Hệ thống giúp người dân, hộ kinh doanh nhỏ và người lao động Việt Nam có thể tự tin trò chuyện, làm việc và trao đổi thông tin với bạn bè, đối tác quốc tế mà không bị cản trở bởi rào cản ngoại ngữ hay phải chi trả chi phí thuê phiên dịch viên đắt đỏ.")

    add_paragraph(doc, "2. Hỗ trợ đắc lực cho các lĩnh vực kinh tế - xã hội then chốt:", bold=True)
    add_bullet(doc, "Hỗ trợ khách du lịch nước ngoài dễ dàng giao tiếp với tài xế taxi, nhân viên lễ tân khách sạn, tiểu thương tại các chợ truyền thống và hướng dẫn viên địa phương, góp phần quảng bá hình ảnh đất nước Việt Nam thân thiện, hiện đại và hiếu khách.", "• Du lịch và Dịch vụ thương mại: ")
    add_bullet(doc, "Hỗ trợ y bác sĩ tại các cơ sở khám chữa bệnh giao tiếp nhanh chóng với bệnh nhân người nước ngoài trong các tình huống sơ cấp cứu, hỏi bệnh sử hoặc tư vấn dùng thuốc khi không có thông dịch viên y tế túc trực.", "• Y tế và Cứu trợ khẩn cấp: ")
    add_bullet(doc, "Hỗ trợ các doanh nghiệp vừa và nhỏ (SMEs), các cơ sở sản xuất thủ công mỹ nghệ Việt Nam thương thảo hợp đồng, báo giá sản phẩm và đàm phán giao thương trực tiếp với khách mua hàng quốc tế.", "• Thương mại và Xuất nhập khẩu: ")
    add_bullet(doc, "Tính năng nhận dạng tiếng nói hiển thị phụ đề trực quan (Speech-to-Text) và chuyển đổi văn bản thành tiếng nói (Text-to-Speech) giúp những người có rào cản về phát âm hoặc suy giảm thính lực có thể tham gia vào các cuộc đàm thoại giao tiếp bình đẳng trong xã hội.", "• Hỗ trợ người khuyết tật và bình đẳng xã hội: ")

    add_paragraph(doc, "3. Thúc đẩy chủ quyền công nghệ số và an toàn dữ liệu quốc gia:", bold=True)
    add_paragraph(doc, "Phần lớn các dịch vụ dịch giọng nói hiện nay phụ thuộc hoàn toàn vào các nền tảng đám mây thương mại nước ngoài (Google Cloud Speech, Microsoft Azure, OpenAI API). Việc T-Lingua xây dựng thành công một giải pháp mã nguồn mở hoàn chỉnh, có khả năng triển khai độc lập trên hạ tầng máy chủ On-Premises hoặc Private Cloud nội địa giúp các tổ chức, doanh nghiệp trong nước chủ động kiểm soát 100% dữ liệu âm thanh và bí mật thông tin, đồng thời tiết kiệm đáng kể chi phí ngoại tệ.")

    add_paragraph(doc, "4. Nhận diện rủi ro tiềm ẩn và các biện pháp kiểm soát:", bold=True)
    add_bullet(doc, "Rủi ro dịch sai nghĩa trong ngữ cảnh nhạy cảm: Được kiểm soát chặt chẽ bằng việc luôn hiển thị song song văn bản nhận dạng gốc kèm điểm số tin cậy (Confidence Score). Nếu độ tin cậy thấp (< 0.75), giao diện sẽ phát cảnh báo để người dùng xác nhận lại trước khi truyền phát bản dịch.", "• Kiểm soát sai lệch ngữ nghĩa: ")
    add_bullet(doc, "Ngăn ngừa rủi ro giả mạo giọng nói (Deepfake Audio): Hệ thống T-Lingua chỉ sử dụng các giọng đọc tổng hợp tiêu chuẩn đã được cấp phép, tuyệt đối không tích hợp tính năng nhân bản giọng nói cá nhân (Voice Cloning), loại bỏ hoàn toàn nguy cơ kẻ xấu lợi dụng để tạo âm thanh giả mạo lừa đảo.", "• Phòng chống mạo danh âm thanh: ")

    # =========================================================================
    # 5.5. Kế hoạch cho kiến thức mới và chiến lược học tập
    # =========================================================================
    add_heading_1(doc, "5.5. Kế hoạch cho kiến thức mới và chiến lược học tập")
    add_paragraph(doc, "Quá trình thực hiện đồ án đòi hỏi nhóm nghiên cứu phải tiếp cận, làm chủ và tích hợp một khối lượng kiến thức chuyên sâu đa ngành: từ xử lý tín hiệu âm thanh kỹ thuật số, kiến trúc mô hình học sâu Transformer, kỹ thuật nén và tăng tốc mô hình AI, đến lập trình mạng bất đồng bộ hiệu năng cao và phát triển ứng dụng di động.")
    add_paragraph(doc, "Bảng 5.2 tổng hợp các nhóm kiến thức công nghệ mới mà nhóm đã tiếp thu và vận dụng cụ thể vào hệ thống T-Lingua:")

    # Table 5.2
    p_tbl2 = doc.add_paragraph()
    p_tbl2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tbl2.paragraph_format.space_before = Pt(6)
    p_tbl2.paragraph_format.space_after = Pt(4)
    run_tcap2 = p_tbl2.add_run("Bảng 5.2. Các nhóm kiến thức mới và cách thức áp dụng vào dự án T-Lingua")
    run_tcap2.font.name = 'Times New Roman'
    run_tcap2.font.size = Pt(11)
    run_tcap2.font.bold = True

    table_data_2 = [
        ("Nhóm công nghệ", "Nội dung kiến thức chuyên sâu", "Cách thức áp dụng cụ thể vào hệ thống T-Lingua"),
        ("Xử lý âm thanh &\nWebRTC VAD", "Cơ chế phân tích phổ năng lượng âm thanh, chia frame 20ms/30ms PCM 16kHz mono, phát hiện khoảng lặng.", "Hiện thực hóa thuật toán WebRTC VAD tách âm nói và cơ chế ngắt câu tự động 500ms Cutoff, giảm 43.8% độ trễ STT."),
        ("ASR Foundation Model\n(Whisper Turbo)", "Kiến trúc Encoder-Decoder Transformer, log-mel spectrogram, decoding chùm tia (beam search), timestamp token.", "Triển khai worker nhận dạng giọng nói tiếng Việt và tiếng Anh thời gian thực, duy trì RTF < 0.22 trên GPU."),
        ("Dịch máy nơ-ron\n(NLLB-200 1.3B)", "Mô hình dịch máy đa ngôn ngữ Seq2Seq, embedding không gian dùng chung, xử lý cặp ngôn ngữ vie_Latn <-> eng_Latn.", "Đảm nhận dịch thuật hai chiều Anh - Việt, kết hợp ràng buộc thuật ngữ chuyên ngành trong quá trình sinh từ."),
        ("Tinh chỉnh tham số\nLoRA (PEFT)", "Phân rã ma trận hạng thấp ΔW = B · A (r=16, α=32), đóng băng mô hình gốc, tối ưu trên GPU tiêu chuẩn.", "Huấn luyện tinh chỉnh NLLB-200 (tăng +6.67 BLEU) và Whisper (thích ứng phương ngữ 3 miền), tạo adapter siêu nhẹ 14.8 MB."),
        ("Tăng tốc suy luận\nCTranslate2 INT8", "Kỹ thuật lượng tử hóa trọng số INT8, tối ưu hóa SIMD/AVX-512 và nhân tính toán Tensor Core trên GPU.", "Nén mô hình NLLB-200 từ 5.2 GB xuống 1.3 GB, tăng tốc độ dịch lên gấp 2.8 lần (từ 510 ms xuống 181 ms)."),
        ("FastAPI & Asynchronous\nStreaming Architecture", "Lập trình mạng bất đồng bộ Python asyncio, quản lý kết nối WebSocket song phương, xử lý hàng đợi non-blocking.", "Xây dựng máy chủ Gateway kết nối thời gian thực, điều phối luồng âm thanh đa phiên và cơ chế khóa Mutual Exclusion (Mutex)."),
        ("Ứng dụng di động\nFlutter Audio Streaming", "Thu âm micro thời gian thực (16kHz mono), truyền streaming qua WebSocket, quản lý state luân phiên và Haptic feedback.", "Xây dựng ứng dụng di động đàm thoại song ngữ hai micro, rung phản hồi tức thì khi phát hiện xung đột thoại."),
        ("Bộ nhớ dịch & Caching\n(Redis & Aho-Corasick)", "Cấu trúc dữ liệu lưu trữ in-memory, băm câu SHA-256 tra cứu TM, thuật toán tìm kiếm xâu con đa mẫu Aho-Corasick.", "Bộ nhớ dịch Translation Memory phản hồi < 5ms cho các câu đã duyệt MQM; tiêm từ điển Glossary chuẩn xác 100%."),
        ("Bảo mật hiện đại\n(Argon2id, MFA, JWT)", "Thuật toán băm Argon2id kháng ASIC/GPU brute-force, chuẩn TOTP RFC 6238, cơ chế xoay vòng JWT Token Rotation.", "Bảo vệ tài khoản quản trị và người dùng, bảo mật các kênh trao đổi API qua HTTPS/WSS và phân quyền RBAC 4 cấp."),
        ("Kiểm chuẩn chất lượng\nHuman-in-the-Loop MQM", "Khung phân loại lỗi dịch thuật quốc tế MQM (Accuracy, Fluency, Terminology), tính điểm trừ trọng số Weighted Penalty.", "Xây dựng Cổng Web Admin thẩm định chất lượng dịch, lọc dữ liệu vàng (MQM score >= 85) phục vụ tái huấn luyện LoRA."),
    ]

    tbl2 = doc.add_table(rows=len(table_data_2), cols=3)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl2)

    col_widths2 = [Inches(1.8), Inches(2.2), Inches(3.1)]

    for row_idx, row_data in enumerate(table_data_2):
        row = tbl2.rows[row_idx]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        is_header = (row_idx == 0)
        if is_header:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for col_idx, cell_value in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.width = col_widths2[col_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_header or col_idx == 0) else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15

            run = p.add_run(cell_value)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10 if not is_header else 10.5)

            if is_header:
                set_cell_background(cell, "1E293B")
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg)

    add_paragraph(doc, "Chiến lược học tập và tiếp thu kiến thức mới của nhóm được thực hiện một cách bài bản thông qua chu trình 4 bước khép kín (4-Step Systematic Learning Cycle):", bold_prefix="Chiến lược học tập 4 bước của nhóm nghiên cứu: ")

    add_bullet(doc, "Trước khi bắt tay vào triển khai một tính năng phức tạp, thành viên phụ trách tiến hành đọc các bài báo khoa học gốc (như nghiên cứu về LoRA của Hu et al. [1], Whisper của Radford et al. [2], NLLB của Meta AI [3], kiến trúc Transformer của Vaswani et al. [4]) và tài liệu kỹ thuật chính thức từ nhà phát triển. Nhóm tập trung sâu vào các nguyên lý cốt lõi, tránh việc sử dụng công nghệ một cách thụ động như 'hộp đen'.", "• Bước 1: Khảo cứu tài liệu học thuật và tài liệu kỹ thuật chính thức: ")
    add_bullet(doc, "Đối với các kỹ thuật có độ rủi ro cao (như chuyển đổi CTranslate2 INT8 [5], thuật toán tách âm WebRTC VAD [6], khóa Mutex thoại đa luồng), nhóm không vội tích hợp vào hệ sinh thái chính mà luôn xây dựng các mã nguồn thử nghiệm cô lập trong thư mục scripts/ để kiểm tra độ tin cậy và đo đạc thông số sơ bộ. Điều này giúp khoanh vùng và khắc phục lỗi sớm, không làm ảnh hưởng đến mã nguồn chính.", "• Bước 2: Xây dựng các mẫu thử nghiệm độc lập (Isolated Prototyping & PoC): ")
    add_bullet(doc, "Sau khi mẫu PoC đạt yêu cầu, tính năng được đóng gói thành các module chuẩn mực và tích hợp vào hệ thống theo hợp đồng giao diện đã thống nhất. Các thành viên phối hợp chặt chẽ để đảm bảo sự tương thích hoàn hảo giữa backend và ứng dụng di động.", "• Bước 3: Tích hợp module theo hợp đồng chuẩn hóa: ")
    add_bullet(doc, "Sau khi hoàn thiện tích hợp, nhóm tiến hành đo kiểm định lượng trên tập 500 mẫu kiểm chuẩn Fresh500 và chạy bộ ma trận kiểm thử khắc nghiệt 109 test cases theo khung kiểm chuẩn MQM [7], SacreBLEU [8] và chrF++ [9]. Các bài học kinh nghiệm, giải pháp khắc phục sự cố và kiến thức thu được đều được ghi chép có hệ thống vào tài liệu kỹ thuật (README.md, docstrings, tài liệu kiến trúc) để toàn bộ nhóm cùng nắm bắt.", "• Bước 4: Đo kiểm thực nghiệm, Đánh giá hồi quy và Đóng gói tri thức: ")

    add_paragraph(doc, "Nhờ chiến lược học tập khoa học và tinh thần cầu thị, nhóm nghiên cứu không chỉ hoàn thành xuất sắc các mục tiêu kỹ thuật của đồ án T-Lingua mà còn trang bị cho bản thân tư duy kỹ thuật hệ thống, khả năng tự học công nghệ mới và tác phong làm việc chuyên nghiệp của người kỹ sư công nghệ thông tin hiện đại.")

    # =========================================================================
    # TÀI LIỆU THAM KHẢO (REFERENCES)
    # =========================================================================
    add_references(doc)

    # Save to files
    target_files = [
        DOCS_DIR / "CHUONG_5_VA_TAI_LIEU_THAM_KHAO_T-LINGUA.docx",
        DOCS_DIR / "CHUONG_5_MOT_SO_THANH_PHAN_KHAC_CUA_DO_AN_T-LINGUA_BAN_MOI_NHAT.docx",
        DOCS_DIR / "CHUONG_5_MOT_SO_THANH_PHAN_KHAC_CUA_DO_AN_T-LINGUA.docx",
        DOCS_DIR / "CHUONG_5_MOT_SO_THANH_PHAN_KHAC_CUA_DO_AN_T-LINGUA_V2.docx",
    ]

    saved_paths = []
    for out_path in target_files:
        try:
            doc.save(str(out_path))
            print(f"Successfully generated: {out_path}")
            saved_paths.append(out_path)
        except PermissionError:
            print(f"Note: Could not overwrite {out_path.name} because it is currently open in Word/WPS.")

    if not saved_paths:
        import time
        ts_path = DOCS_DIR / f"CHUONG_5_VA_TAI_LIEU_THAM_KHAO_{int(time.time())}.docx"
        doc.save(str(ts_path))
        print(f"Saved to timestamped file: {ts_path}")

if __name__ == "__main__":
    print("Building Chapter 5 document...")
    build_chapter_5()

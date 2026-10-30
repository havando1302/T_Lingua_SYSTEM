# -*- coding: utf-8 -*-
"""
Builder script for T-Lingua Task Assignment Document (Siêu ngắn gọn - Đồ án liên ngành):
BẢNG PHÂN CÔNG NHIỆM VỤ ĐỒ ÁN LIÊN NGÀNH T-LINGUA
Định dạng ngắn gọn, súc tích, bao quát 100% nhiệm vụ thực tế của Đồ án liên ngành.
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

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
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

def set_table_borders(table, color="94A3B8", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def build_task_assignment_doc():
    doc = docx.Document()

    # Page setup (A4, Left: 3cm, Right: 2cm, Top: 2cm, Bottom: 2cm)
    for section in doc.sections:
        section.top_margin = Inches(0.79)     # 2.0 cm
        section.bottom_margin = Inches(0.79)  # 2.0 cm
        section.left_margin = Inches(1.18)    # 3.0 cm
        section.right_margin = Inches(0.79)   # 2.0 cm

    # Document Header
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(2)
    r1 = p_inst.add_run("TRƯỜNG ĐẠI HỌC PHENIKAA\nKHOA CÔNG NGHỆ THÔNG TIN")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(12)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_div.paragraph_format.space_before = Pt(0)
    p_div.paragraph_format.space_after = Pt(12)
    r_div = p_div.add_run("--------------------***--------------------")
    r_div.font.name = 'Times New Roman'
    r_div.font.size = Pt(10)
    r_div.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("BẢNG PHÂN CÔNG NHIỆM VỤ ĐỒ ÁN LIÊN NGÀNH")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(6)
    r_sub = p_sub.add_run("Đề tài: Hoàn thiện hệ thống đàm thoại song ngữ thời gian thực T-Lingua (Speech-to-Speech)")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p_note = doc.add_paragraph()
    p_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_note.paragraph_format.space_before = Pt(0)
    p_note.paragraph_format.space_after = Pt(14)
    r_note = p_note.add_run("(Nhiệm vụ thực hiện giai đoạn 25/08/2026 – 30/10/2026 kế thừa từ Đồ án cơ sở)")
    r_note.font.name = 'Times New Roman'
    r_note.font.size = Pt(11)
    r_note.font.italic = True
    r_note.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # Table setup
    col_widths = [Inches(0.5), Inches(1.2), Inches(0.9), Inches(3.0), Inches(0.7)]
    headers = ["STT", "Họ và tên", "Mã sinh viên", "Các nhiệm vụ được giao", "Tỉ lệ đóng góp"]

    table_data = [
        (
            "1",
            "Hà Văn Đô",
            "23010406",
            [
                "Đo baseline chất lượng (BLEU/chrF) và hiệu năng (p50/p95) trên tập benchmark.",
                "Tinh chỉnh LoRA Adapter cho Whisper, NLLB-200 và tối ưu CTranslate2 INT8.",
                "Xây dựng tách âm WebRTC VAD (500ms Cutoff) và lọc nhiễu DeepFilterNet.",
                "Xây dựng Translation Memory (Redis) và tiêm từ điển Glossary (Aho-Corasick).",
                "Phát triển toàn bộ RESTful API và WebSocket phục vụ Web Admin Dashboard.",
                "Profiling tối ưu độ trễ toàn tuyến (P95 < 1.2s), quản lý hàng đợi và tuning GPU.",
                "Triển khai an ninh bảo mật (Argon2id, MFA TOTP) và Telemetry giám sát.",
                "Kiểm thử tải, đóng gói triển khai Docker và viết báo cáo kỹ thuật đồ án."
            ],
            "50%"
        ),
        (
            "2",
            "Nguyễn Quang Thọ",
            "23010162",
            [
                "Lập backlog ưu tiên, ma trận truy vết (RTM) và thiết kế Design System.",
                "Phát triển toàn diện Cổng Web Quản trị (Admin Dashboard) bằng React/Tailwind.",
                "Xây dựng công cụ kiểm chuẩn chất lượng MQM (Human-in-the-Loop) và lọc dữ liệu vàng.",
                "Tối ưu WebSocket client trên Flutter (reconnect, heartbeat, phục hồi mạng).",
                "Tối ưu streaming âm thanh Flutter: hiển thị partial text và chống chồng âm TTS.",
                "Hoàn thiện khóa thoại Dual-Mic Mutex Lock, rung Haptic và lưu lịch sử Hive.",
                "Kiểm thử giao diện, kiểm thử E2E hệ thống và tối ưu trải nghiệm người dùng (UI/UX).",
                "Soạn thảo tài liệu người dùng/quản trị, chuẩn bị kịch bản demo và viết báo cáo."
            ],
            "50%"
        )
    ]

    tbl = doc.add_table(rows=1 + len(table_data), cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    # Header Row
    hdr_row = tbl.rows[0]
    hdr_trPr = hdr_row._tr.get_or_add_trPr()
    hdr_trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    hdr_trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    for c_idx, h_text in enumerate(headers):
        cell = hdr_row.cells[c_idx]
        cell.width = col_widths[c_idx]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=100, bottom=100, left=80, right=80)

        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(h_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Data Rows
    for r_idx, (stt, name, msv, tasks, contrib) in enumerate(table_data, start=1):
        row = tbl.rows[r_idx]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        # Cell 0: STT
        c0 = row.cells[0]
        c0.width = col_widths[0]
        c0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c0, top=80, bottom=80, left=60, right=60)
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(stt)
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(11)
        r0.font.bold = True

        # Cell 1: Name
        c1 = row.cells[1]
        c1.width = col_widths[1]
        c1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c1, top=80, bottom=80, left=80, right=80)
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1_n = p1.add_run(name)
        r1_n.font.name = 'Times New Roman'
        r1_n.font.size = Pt(11)
        r1_n.font.bold = True

        # Cell 2: MSV
        c2 = row.cells[2]
        c2.width = col_widths[2]
        c2.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c2, top=80, bottom=80, left=60, right=60)
        p2 = c2.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        r2_m = p2.add_run(msv)
        r2_m.font.name = 'Times New Roman'
        r2_m.font.size = Pt(11)

        # Cell 3: Tasks
        c3 = row.cells[3]
        c3.width = col_widths[3]
        c3.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        set_cell_margins(c3, top=80, bottom=80, left=100, right=100)
        for t_idx, task_text in enumerate(tasks):
            if t_idx == 0:
                p_task = c3.paragraphs[0]
            else:
                p_task = c3.add_paragraph()
            p_task.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_task.paragraph_format.space_before = Pt(1)
            p_task.paragraph_format.space_after = Pt(2)
            p_task.paragraph_format.line_spacing = 1.15
            p_task.paragraph_format.left_indent = Inches(0.18)
            p_task.paragraph_format.first_line_indent = Inches(-0.18)

            r_bullet = p_task.add_run("- ")
            r_bullet.font.name = 'Times New Roman'
            r_bullet.font.size = Pt(10.5)
            r_bullet.font.bold = True

            r_text = p_task.add_run(task_text)
            r_text.font.name = 'Times New Roman'
            r_text.font.size = Pt(10.5)

        # Cell 4: Contrib
        c4 = row.cells[4]
        c4.width = col_widths[4]
        c4.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(c4, top=80, bottom=80, left=60, right=60)
        p4 = c4.paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p4.paragraph_format.space_before = Pt(0)
        p4.paragraph_format.space_after = Pt(0)
        r4_c = p4.add_run(contrib)
        r4_c.font.name = 'Times New Roman'
        r4_c.font.size = Pt(11)
        r4_c.font.bold = True
        r4_c.font.color.rgb = RGBColor(0x05, 0x96, 0x69)

        # Alternating background
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c in [c0, c1, c2, c3, c4]:
            set_cell_background(c, bg_color)

    # Signatures
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(24)
    p_space.paragraph_format.space_after = Pt(0)

    sig_tbl = doc.add_table(rows=2, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_widths = [Inches(3.15), Inches(3.15)]

    # Row 0: Titles
    r0 = sig_tbl.rows[0]
    p_gv = r0.cells[0].paragraphs[0]
    p_gv.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_gv_t = p_gv.add_run("GIẢNG VIÊN HƯỚNG DẪN\n(Ký và ghi rõ họ tên)")
    r_gv_t.font.name = 'Times New Roman'
    r_gv_t.font.size = Pt(12)
    r_gv_t.font.bold = True

    p_sv = r0.cells[1].paragraphs[0]
    p_sv.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sv.paragraph_format.space_after = Pt(4)
    date_run = p_sv.add_run("Hà Nội, ngày 30 tháng 10 năm 2026\n")
    date_run.font.name = 'Times New Roman'
    date_run.font.size = Pt(11)
    date_run.font.italic = True
    r_sv_t = p_sv.add_run("SINH VIÊN THỰC HIỆN\n(Ký và ghi rõ họ tên)")
    r_sv_t.font.name = 'Times New Roman'
    r_sv_t.font.size = Pt(12)
    r_sv_t.font.bold = True

    # Row 1: Names
    r1 = sig_tbl.rows[1]
    p_gv_name = r1.cells[0].paragraphs[0]
    p_gv_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_gv_name.paragraph_format.space_before = Pt(54)
    r_gvn = p_gv_name.add_run("(Họ và tên CBHD)")
    r_gvn.font.name = 'Times New Roman'
    r_gvn.font.size = Pt(12)
    r_gvn.font.italic = True

    p_sv_name = r1.cells[1].paragraphs[0]
    p_sv_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sv_name.paragraph_format.space_before = Pt(54)
    r_svn = p_sv_name.add_run("Hà Văn Đô                Nguyễn Quang Thọ")
    r_svn.font.name = 'Times New Roman'
    r_svn.font.size = Pt(12)
    r_svn.font.bold = True

    for row in sig_tbl.rows:
        for c_idx, cell in enumerate(row.cells):
            cell.width = sig_widths[c_idx]

    # Save to files
    target_files = [
        DOCS_DIR / "BANG_PHAN_CONG_NHIEM_VU_DO_AN_LIEN_NGANH_T-LINGUA.docx",
        DOCS_DIR / "BANG_PHAN_CONG_NHIEM_VU_T-LINGUA.docx",
        DOCS_DIR / "BANG_PHAN_CONG_NHIEM_VU_T-LINGUA_V2.docx",
    ]

    for out_path in target_files:
        try:
            doc.save(str(out_path))
            print(f"Successfully saved: {out_path}")
        except PermissionError:
            print(f"Note: Cannot overwrite {out_path.name} (file is open in another program).")

if __name__ == "__main__":
    build_task_assignment_doc()

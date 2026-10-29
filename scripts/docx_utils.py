# -*- coding: utf-8 -*-
"""
Builder helper for formatting docx documents according to Phenikaa University thesis standards.
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

PRIMARY_COLOR = RGBColor(27, 54, 93)     # #1B365D - Navy Phenikaa
SECONDARY_COLOR = RGBColor(11, 37, 69)   # #0B2545 - Deep Navy
TEXT_COLOR = RGBColor(0, 0, 0)           # Black
GRAY_TEXT = RGBColor(80, 80, 80)
HEADER_BG_HEX = "1B365D"
SUBHEADER_BG_HEX = "2B4C7E"
ZEBRA_BG_HEX = "F4F6F9"
BORDER_COLOR_HEX = "D0D7DE"

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
    pPr = p._p.get_or_add_pPr()
    
    # Set spacing
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

def add_heading_1(doc, text):
    p = add_paragraph(doc, text, bold=True, font_size=16, space_before=14, space_after=8, align=WD_ALIGN_PARAGRAPH.LEFT, color=PRIMARY_COLOR)
    return p

def add_heading_2(doc, text):
    p = add_paragraph(doc, text, bold=True, font_size=14, space_before=10, space_after=6, align=WD_ALIGN_PARAGRAPH.LEFT, color=PRIMARY_COLOR)
    return p

def add_heading_3(doc, text):
    p = add_paragraph(doc, text, bold=True, italic=True, font_size=13, space_before=6, space_after=4, align=WD_ALIGN_PARAGRAPH.LEFT, color=SECONDARY_COLOR)
    return p

def add_bullet(doc, text="", prefix="• "):
    p = add_paragraph(doc, text="", space_after=4, space_before=0, line_spacing=1.25, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
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
    p = add_paragraph(doc, text, bold=True, italic=True, font_size=11, space_before=4, space_after=6, align=WD_ALIGN_PARAGRAPH.CENTER, color=PRIMARY_COLOR)
    return p

def add_diagram_box(doc, title, ascii_art):
    """Render a clean framed box for UML/Architectural/Flow diagrams."""
    p_box = doc.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_box.paragraph_format.space_before = Pt(6)
    p_box.paragraph_format.space_after = Pt(4)
    p_box.paragraph_format.left_indent = Inches(0.1)
    p_box.paragraph_format.right_indent = Inches(0.1)
    
    # Border & light gray shading
    pPr = p_box._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="4" w:color="{BORDER_COLOR_HEX}"/>'
        f'<w:left w:val="single" w:sz="18" w:space="8" w:color="{HEADER_BG_HEX}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="4" w:color="{BORDER_COLOR_HEX}"/>'
        f'<w:right w:val="single" w:sz="6" w:space="4" w:color="{BORDER_COLOR_HEX}"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
    pPr.append(shd)
    
    run_title = p_box.add_run(f"[{title}]\n")
    run_title.bold = True
    run_title.font.name = "Consolas"
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = PRIMARY_COLOR
    
    run_art = p_box.add_run(ascii_art.strip())
    run_art.font.name = "Consolas"
    run_art.font.size = Pt(9.5)
    run_art.font.color.rgb = RGBColor(30, 41, 59)
    return p_box

print("Docx styling utilities ready.")


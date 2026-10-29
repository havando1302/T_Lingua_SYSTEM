# -*- coding: utf-8 -*-
import sys
import docx

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

doc = docx.Document('docs/CHƯƠNG_3_THIET_KE_GIAI_PHAP_T-LINGUA_18_UC.docx')
print('=== THỐNG KÊ TÀI LIỆU CHƯƠNG 3 ===')
print('Số đoạn văn (paragraphs):', len(doc.paragraphs))
print('Số bảng biểu (tables):', len(doc.tables))

headings = [p.text for p in doc.paragraphs if p.text.startswith(('CHƯƠNG 3', '3.'))]
print('\nDanh sách các mục chính:')
for h in headings:
    print('  *', h)

total_words = sum(len(p.text.split()) for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        for cell in row.cells:
            total_words += sum(len(p.text.split()) for p in cell.paragraphs)

print(f'\nTổng số từ (Word Count): {total_words:,} từ')
estimated_pages = total_words // 450
print(f'Ước tính số trang theo định dạng Phenikaa (Times New Roman 13pt, 1.3 line spacing): ~{estimated_pages} - {estimated_pages + 10} trang')


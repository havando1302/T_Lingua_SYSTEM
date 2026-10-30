import pypdf

pdf_path = r'C:\Users\ADMIN\.gemini\antigravity\brain\6e6af05b-0b05-4700-a92d-be2368974fe7\.user_uploaded\media_1793294668612_47d760dd.pdf'
reader = pypdf.PdfReader(pdf_path)

pages_to_check = [186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205]

with open('scripts/pdf_3_4_content.txt', 'w', encoding='utf-8') as f:
    for p_idx in pages_to_check:
        if p_idx < len(reader.pages):
            f.write(f"\n==================== PAGE {p_idx + 1} ====================\n")
            txt = reader.pages[p_idx].extract_text() or ''
            f.write(txt)

print("Extracted to scripts/pdf_3_4_content.txt")

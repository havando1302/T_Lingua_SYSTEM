import docx

doc_path = r"C:\Du_an\T_Langua_Test\docs\CHƯƠNG_3_THIET_KE_GIAI_PHAP_T-LINGUA_BAN_CAP_NHAT.docx"
doc = docx.Document(doc_path)
print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")

found_headings = []
for p in doc.paragraphs:
    if p.text.startswith("3.4"):
        found_headings.append(p.text)
    elif "Hình 3.28" in p.text or "Hình 3.29" in p.text or "Hình 3.30" in p.text or "Hình 3.31" in p.text or "Hình 3.32" in p.text or "Hình 3.33" in p.text or "Bảng 3.3" in p.text:
        found_headings.append(p.text)

print("\n--- FOUND HEADINGS & CAPTIONS IN 3.4 ---")
for h in found_headings:
    print(h)


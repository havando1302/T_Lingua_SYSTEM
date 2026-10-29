import openpyxl
from collections import OrderedDict

excel_path = "outputs/Bao_cao_kiem_thu_500_cau_am_thanh.xlsx"
wb = openpyxl.load_workbook(excel_path)
ws = wb["Chi_tiet_500_cau"]

headers = [cell.value for cell in ws[1]]
rows_by_case = OrderedDict()

for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    case_id = row[1]
    rows_by_case[case_id] = row

print(f"Total rows in sheet: {ws.max_row - 1}")
print(f"Unique case IDs: {len(rows_by_case)}")

# If there are duplicates (e.g. from the 5-sample smoke test), rewrite cleanly with exactly 500 unique cases
if len(rows_by_case) == 500 and (ws.max_row - 1) != 500:
    print("Deduplicating to exactly 500 rows...")
    # Recreate sheet with clean 500 rows
    wb.remove(ws)
    ws_clean = wb.create_sheet(title="Chi_tiet_500_cau", index=1)
    ws_clean.append(headers)
    for idx, (cid, r_vals) in enumerate(rows_by_case.items(), start=1):
        clean_row = list(r_vals)
        clean_row[0] = idx
        ws_clean.append(clean_row)
    wb.save(excel_path)
    print("Cleaned successfully.")

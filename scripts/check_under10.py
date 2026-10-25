import openpyxl
import re

wb = openpyxl.load_workbook("file/PHS 2026 (Jawaban) (2).xlsx", data_only=True)
sheet = wb.active

rows = []
for r in sheet.iter_rows(min_row=3, values_only=False):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        rows.append(r)

print(f"Total visible rows: {len(rows)}")

under_10 = []
for r in rows:
    v = str(r[13].value).strip()
    m = re.search(r"(\d+)", v)
    age = int(m.group(1)) if m else None
    cat = str(r[14].value).strip()
    if age is not None and age < 10:
        under_10.append((r[0].row, r[9].value, age, cat))
    elif cat == "5 - 9 tahun":
        under_10.append((r[0].row, r[9].value, age, cat))

print(f"Count under 10 or '5 - 9 tahun': {len(under_10)}")
for u in under_10:
    print(u)

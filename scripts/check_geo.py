import openpyxl
from collections import Counter

wb = openpyxl.load_workbook("file/PHS 2026 (Jawaban) (2).xlsx", data_only=True)
sheet = wb.active

rows = []
for r in sheet.iter_rows(min_row=3, values_only=False):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        rows.append([c.value for c in r])

print("Total visible:", len(rows))
desas = Counter(str(r[4]).strip() for r in rows)
print("Desa:", dict(desas))

kaders = Counter(str(r[1]).strip() for r in rows)
print("Kader sample:", list(kaders.items())[:5])

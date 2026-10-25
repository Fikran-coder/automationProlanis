import openpyxl
import os
import csv

fname = "file/PHS 2026 (Jawaban) (2).xlsx"
if not os.path.exists(fname):
    print(f"Error: {fname} not found!")
    exit(1)

wb = openpyxl.load_workbook(fname, data_only=True)
sheet = wb.active

headers = [c.value for c in sheet[2]]
rows = []
for r in sheet.iter_rows(min_row=3, values_only=False):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        rows.append([c.value for c in r])

print("Total visible rows:", len(rows))
print("Headers count:", len(headers))
for idx, h in enumerate(headers):
    print(f"{idx}: {h}")

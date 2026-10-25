import openpyxl

wb = openpyxl.load_workbook("file/PHS 2026 (Jawaban) (2).xlsx", data_only=True)
sheet = wb.active

for idx, r in enumerate(sheet.iter_rows(min_row=3, values_only=False), start=3):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        cat = str(r[14].value)
        if "5 - 9" in cat or "10 - 14" in cat:
            print(f"Row {idx}: Nama={r[9].value}, Usia={r[13].value}, Kategori={r[14].value}, Pekerjaan={r[12].value}")

import openpyxl
from collections import Counter

wb = openpyxl.load_workbook("file/PHS 2026 (Jawaban) (2).xlsx", data_only=True)
sheet = wb.active

headers = [c.value for c in sheet[2]]
rows = []
for r in sheet.iter_rows(min_row=3, values_only=False):
    if not sheet.row_dimensions[r[0].row].hidden and any(c.value is not None for c in r):
        rows.append([c.value for c in r])

print("Total rows:", len(rows))

# Let's inspect unique values for each relevant column
col_indices = {
    "Pendidikan": 11,
    "Pekerjaan": 12,
    "Usia": 13,
    "Kategori_Usia": 14,
    "Aktivitas_Fisik": 15,
    "Cuci_Tangan_Biasa": 16,
    "Cuci_Tangan_Air": 17,
    "Cuci_Tangan_Sabun": 18,
    "Cuci_Tangan_Waktu": 19,
    "Buah_Sayur": 20,
    "Tekanan_Darah": 21,
    "Tempat_Tekanan_Darah": 22,
    "Gula_Darah": 23,
    "Tempat_Gula_Darah": 24,
    "Merokok": 25,
    "Berapa_Kali_Merokok": 26,
    "Berapa_Lama_Berhenti": 27,
}

for name, idx in col_indices.items():
    vals = [r[idx] for r in rows]
    c = Counter(vals)
    print(f"\n--- {name} (col {idx}: {headers[idx]}) ---")
    for val, count in c.most_common(10):
        print(f"  {repr(val)}: {count}")
    if len(c) > 10:
        print(f"  ... total {len(c)} distinct values")

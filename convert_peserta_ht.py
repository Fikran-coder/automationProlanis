"""
Convert PESERTA_HT CSV to peserta_prolanis_data format.
Splits output into files of 100 rows each.

Input:  file/PESERTA_HT_10040403_2026_7_202607306335194.csv (semicolon-delimited)
Output: file/peserta_ht_sirnagalih/peserta_001.csv, peserta_002.csv, ...
Format: NO_BPJS,TELEPON,ALAMAT
"""

import csv
import os

SOURCE = "file/PESERTA_HT_10040403_2026_7_202607306335194.csv"
OUTPUT_DIR = "file/peserta_ht_sirnagalih"
ROWS_PER_FILE = 100
ALAMAT = "SIRNAGALIH"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read source CSV (semicolon-delimited, BOM-aware)
    with open(SOURCE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = []
        for row in reader:
            rows.append({
                "NO_BPJS": row["Nomor_Kartu"].strip(),
                "TELEPON": row["Nomor_HP"].strip(),
                "ALAMAT": ALAMAT,
            })

    # Split and write
    total = len(rows)
    file_count = 0
    for i in range(0, total, ROWS_PER_FILE):
        file_count += 1
        chunk = rows[i:i + ROWS_PER_FILE]
        filename = os.path.join(OUTPUT_DIR, f"peserta_{file_count:03d}.csv")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["NO_BPJS", "TELEPON", "ALAMAT"])
            writer.writeheader()
            writer.writerows(chunk)

    print(f"Done! {total} rows → {file_count} files in {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()

import os
import sys
sys.path.insert(0, ".")
import pandas as pd
from playwright.sync_api import sync_playwright
from phs_automation import run_phs_batch

# Create a small 1-record test CSV
test_csv = "file/test_phs_sample.csv"
sample_data = [{
    "No": "1",
    "Kecamatan": "Tamansari",
    "Desa": "Tamansari",
    "Puskesmas": "Puskesmas Sirnagalih",
    "Pendata": "Kader",
    "RW": "01",
    "RT": "02",
    "NIK": "3201010101010001",
    "Nama": "Test Responden PHS",
    "Jenis Kelamin": "Perempuan",
    "Rentang Usia": "≥ 15 tahun",
    "Usia": "35",
    "Pendidikan Terakhir": "SMA Sederajat",
    "Pekerjaan": "Ibu Rumah Tangga",
    "Cek Tekanan Darah": "Ya",
    "Tempat Tekanan Darah": "Posyandu/ Posbindu",
    "Cek Gula Darah": "Ya",
    "Tempat Gula Darah": "Posyandu/ Posbindu",
    "Aktivitas Fisik": "Ya",
    "Cuci Tangan": "Ya",
    "Buah dan Sayur": "3 Porsi",
    "Perokok Aktif": "Tidak",
    "Pernah Merokok": "Tidak",
    "Lama Berhenti Merokok": ""
}]

pd.DataFrame(sample_data).to_csv(test_csv, index=False)

def test_single_test_mode():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logs = []
        counts = run_phs_batch(page, test_csv, submit_form=False, log=lambda m: logs.append(m))
        print("Batch Counts:", counts)
        print("Logs:")
        for l in logs:
            print(" ", l)

        assert counts["test"] == 1, f"Expected 1 test success, got {counts}"
        assert counts["error"] == 0, f"Expected 0 errors, got {counts}"
        browser.close()
        print("PASSED TEST SINGLE ROW IN TEST MODE!")

if __name__ == "__main__":
    test_single_test_mode()

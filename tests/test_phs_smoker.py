import os
import sys
sys.path.insert(0, ".")
import pandas as pd
from playwright.sync_api import sync_playwright
from phs_automation import run_phs_batch

test_csv = "file/test_phs_smoker.csv"
sample_data = [{
    "No": "1",
    "Kecamatan": "Tamansari",
    "Desa": "Tamansari",
    "Puskesmas": "Puskesmas Sirnagalih",
    "Pendata": "Kader",
    "RW": "01",
    "RT": "02",
    "NIK": "3201010101010002",
    "Nama": "Test Smoker Responden",
    "Jenis Kelamin": "Laki - Laki",
    "Rentang Usia": "≥ 15 tahun",
    "Usia": "40",
    "Pendidikan Terakhir": "SMA Sederajat",
    "Pekerjaan": "Buruh",
    "Cek Tekanan Darah": "Ya",
    "Tempat Tekanan Darah": "Puskesmas",
    "Cek Gula Darah": "Ya",
    "Tempat Gula Darah": "Puskesmas",
    "Aktivitas Fisik": "Ya",
    "Cuci Tangan": "Ya",
    "Buah dan Sayur": "3 Porsi",
    "Perokok Aktif": "Ya",
    "Pernah Merokok": "",
    "Lama Berhenti Merokok": ""
}]

pd.DataFrame(sample_data).to_csv(test_csv, index=False)

def test_smoker_test_mode():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logs = []
        counts = run_phs_batch(page, test_csv, submit_form=False, log=lambda m: logs.append(m))
        print("Smoker Batch Counts:", counts)
        print("Logs:")
        for l in logs:
            print(" ", l)

        assert counts["test"] == 1, f"Expected 1 test success, got {counts}"
        assert counts["error"] == 0, f"Expected 0 errors, got {counts}"
        browser.close()
        print("PASSED TEST SMOKER ROW IN TEST MODE!")

if __name__ == "__main__":
    test_smoker_test_mode()

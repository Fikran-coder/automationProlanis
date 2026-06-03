import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CSV_FILE = "pcare_test_one_data.csv"
FORM_URL = "https://pcarejkn.bpjs-kesehatan.go.id/eclaim/EntriDaftarDokkel"

# 037 = Senam-Kelompok Prolanis
# 036 = Edukasi-Kelompok Prolanis
DEFAULT_KEGIATAN = "037"

# Constant vital signs for Prolanis group activities
DEFAULT_RESP_RATE = "20"
DEFAULT_HEART_RATE = "80"

# Set False for first test so it fills the form but does NOT click Simpan.
# Change to True when you are ready to submit.
SUBMIT_FORM = False


def split_value(value):
    parts = str(value).replace("\n", "/").split("/")
    first = parts[0].strip()
    second = parts[1].strip() if len(parts) > 1 else ""
    return first, second


def fill_one_row(page, row, index):
    no_bpjs = str(row["NO_BPJS"]).strip()
    tinggi_badan, berat_badan = split_value(row["TB_BB"])
    lingkar_perut = str(row["LP"]).strip()
    sistole, diastole = split_value(row["TD"])
    kegiatan = str(row.get("KEGIATAN", DEFAULT_KEGIATAN)).strip() or DEFAULT_KEGIATAN

    print(f"Processing row {index + 1}: {no_bpjs}")

    # Search BPJS number
    page.locator("#txtnokartu").fill(no_bpjs)
    page.locator("#btnCariPeserta").click()
    page.wait_for_timeout(2500)

    # Check if patient data was found and skrining is done
    # If an alert/warning appears or Simpan is already disabled, skip this patient
    alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
    if alert.is_visible():
        msg = alert.inner_text()
        print(f"SKIPPED row {index + 1}: {no_bpjs} — {msg}")
        # Dismiss alert if there's a button
        dismiss = page.locator(".bootbox .btn-primary, .alert .close").first
        if dismiss.is_visible():
            dismiss.click()
            page.wait_for_timeout(500)
        return 'skipped'

    # Kunjungan Sehat
    page.locator('input[name="kunjSakitF"][value="false"]').check(force=True)

    # Rawat Jalan. If this selector differs, inspect the radio input name/value.
    try:
        page.locator('input[name="rawatInap"][value="false"]').check(force=True, timeout=3000)
    except PlaywrightTimeoutError:
        page.get_by_text("Rawat Jalan").click()

    # Kegiatan dropdown
    page.locator("#poli").select_option(kegiatan)

    # Pemeriksaan Fisik
    page.locator("#tinggiBadan").fill(tinggi_badan)
    page.locator("#beratBadan").fill(berat_badan)
    page.locator("#lingkarPerut").fill(lingkar_perut)

    # Tekanan Darah
    page.locator("#sistole").fill(sistole)
    page.locator("#diastole").fill(diastole)

    # Constant values
    page.locator("#respRate").fill(DEFAULT_RESP_RATE)
    page.locator("#heartRate").fill(DEFAULT_HEART_RATE)

    print("Filled data:")
    print({
        "NO_BPJS": no_bpjs,
        "tinggiBadan": tinggi_badan,
        "beratBadan": berat_badan,
        "lingkarPerut": lingkar_perut,
        "sistole": sistole,
        "diastole": diastole,
        "respRate": DEFAULT_RESP_RATE,
        "heartRate": DEFAULT_HEART_RATE,
        "kegiatan": kegiatan,
    })

    if SUBMIT_FORM:
        # Wait for JS validation to settle before checking button state
        page.wait_for_timeout(1000)
        if page.locator('#btnSimpanPendaftaran').is_disabled():
            print(f"SKIPPED row {index + 1}: {no_bpjs} — button is disabled.")
            return 'skipped'
        page.locator("#btnSimpanPendaftaran").click()
        page.wait_for_timeout(2500)
        print(f"SUCCESS row {index + 1}: {no_bpjs} — submitted.")
        return 'success'
    else:
        print("TEST MODE: form was filled but not submitted. Set SUBMIT_FORM = True to click Simpan.")
        return 'test'


if __name__ == "__main__":
    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="browser_session",
            headless=False,
        )

        page = browser.pages[0]
        page.goto(FORM_URL)

        input("Login manually and set the date first, then press Enter to start...")

        results = []
        for index, row in df.iterrows():
            try:
                result = fill_one_row(page, row, index)
            except Exception as e:
                print(f"ERROR row {index + 1}: {e}")
                result = 'error'
            results.append(result)

        print(f"\n=== SUMMARY: success={results.count('success')}, skipped={results.count('skipped')}, errors={results.count('error')} ===")

        input("Review the browser result. Press Enter to close...")
        browser.close()

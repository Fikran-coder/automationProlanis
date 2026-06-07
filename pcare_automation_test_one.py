import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CSV_FILE = "pcare_data.csv"
FORM_URL = "https://pcarejkn.bpjs-kesehatan.go.id/eclaim/EntriDaftarDokkel"

# 037 = Senam-Kelompok Prolanis
# 036 = Edukasi-Kelompok Prolanis
DEFAULT_KEGIATAN = "037"

# Constant vital signs for Prolanis group activities
DEFAULT_RESP_RATE = "20"
DEFAULT_HEART_RATE = "80"


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

    print(f"Processing row {index + 1}: {no_bpjs}")

    # Search BPJS number
    page.locator("#txtnokartu").fill(no_bpjs)
    page.locator("#btnCariPeserta").click()
    # Wait for search result: either patient name loads or an alert appears
    page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning, .bootbox-body").first.wait_for(state="visible", timeout=15000)

    # Check if patient data was found and skrining is done
    # If an alert/warning appears or Simpan is already disabled, skip this patient
    alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
    if alert.is_visible():
        msg = alert.inner_text().strip()
        print(f"SKIPPED row {index + 1}: {no_bpjs} — {msg}")
        # Dismiss alert if there's a button
        dismiss = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
        if dismiss.is_visible():
            dismiss.click()
            page.wait_for_timeout(500)
        # Reset form and wait for it to be ready
        page.goto(FORM_URL, wait_until="networkidle")
        page.locator("#btnCariPeserta").wait_for(state="visible", timeout=10000)
        return 'skipped'

    # Kunjungan Sehat
    page.locator('input[name="kunjSakitF"][value="false"]').check(force=True)

    # Rawat Jalan
    page.locator('input[name="tkp"][value="10"]').check(force=True)

    # Kegiatan dropdown
    page.locator("#poli").select_option(DEFAULT_KEGIATAN)

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
        "kegiatan": DEFAULT_KEGIATAN,
    })

    if SUBMIT_FORM:
        # Wait for JS validation to settle before checking button state
        page.wait_for_timeout(1000)
        if page.locator('#btnSimpanPendaftaran').is_disabled():
            print(f"SKIPPED row {index + 1}: {no_bpjs} — button is disabled.")
            page.goto(FORM_URL, wait_until="networkidle")
            return 'skipped'
        page.locator("#btnSimpanPendaftaran").click()
        # Wait for success banner/alert that confirms save and resets the form
        try:
            page.locator(".alert-success, .gritter-item-wrapper").first.wait_for(state="visible", timeout=10000)
            print(f"SUCCESS row {index + 1}: {no_bpjs} — submitted.")
            # Dismiss success notification if needed
            dismiss = page.locator(".gritter-close").first
            if dismiss.is_visible():
                dismiss.click()
            return 'success'
        except PlaywrightTimeoutError:
            print(f"WARNING row {index + 1}: {no_bpjs} — clicked submit but no confirmation banner detected.")
            return 'success'
    else:
        print("TEST MODE: form was filled but not submitted. Set SUBMIT_FORM = True to click Simpan.")
        return 'test'


if __name__ == "__main__":
    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    print("Pilih kegiatan:")
    print("  1. Senam (037)")
    print("  2. Edukasi (036)")
    pilihan = input("Masukkan pilihan (1/2): ").strip()
    if pilihan == "2":
        DEFAULT_KEGIATAN = "036"
        print("Kegiatan: Edukasi-Kelompok Prolanis")
    else:
        DEFAULT_KEGIATAN = "037"
        print("Kegiatan: Senam-Kelompok Prolanis")

    pilihan_submit = input("Submit data? (y/n): ").strip().lower()
    SUBMIT_FORM = pilihan_submit == "y"
    if SUBMIT_FORM:
        print("Mode: SUBMIT (data akan disimpan)")
    else:
        print("Mode: TEST (form diisi tapi tidak disimpan)")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="browser_session",
            headless=False,
        )

        page = browser.pages[0]
        page.goto(FORM_URL)

        input("Login dulu dan atur tanggal, lalu tekan Enter untuk mulai...")

        log = {'success': [], 'skipped': [], 'error': [], 'test': []}
        for index, row in df.iterrows():
            no_bpjs = str(row["NO_BPJS"]).strip()
            try:
                result = fill_one_row(page, row, index)
            except Exception as e:
                print(f"ERROR row {index + 1}: {e}")
                result = 'error'
                # Reset page to clean state for next patient
                page.goto(FORM_URL, wait_until="networkidle")
            log[result].append(no_bpjs)
            # Delay between rows to avoid PCare rate limiting
            page.wait_for_timeout(3000)

        total = len(df)
        print(f"\n=== SUMMARY ({total} total) ===")
        print(f"SUCCESS ({len(log['success'])}): {', '.join(log['success']) or '-'}")
        print(f"SKIPPED ({len(log['skipped'])}): {', '.join(log['skipped']) or '-'}")
        print(f"ERROR   ({len(log['error'])}): {', '.join(log['error']) or '-'}")
        print(f"TEST    ({len(log['test'])}): {', '.join(log['test']) or '-'}")

        input("Cek hasil di browser. Tekan Enter untuk menutup...")
        browser.close()

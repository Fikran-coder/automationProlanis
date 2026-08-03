from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import random

EPUSKESMAS_LOGIN_URL = "https://bogor.epuskesmas.id/login"
EPUSKESMAS_PASIEN_URL = "https://bogor.epuskesmas.id/pasien"

FALLBACK_ALAMAT = ["SIRNAGALIH", "SUKAMANTRI", "TAMANSARI", "PASIREURIH"]


def search_alamat(page, no_bpjs):
    """Search for a BPJS number on ePuskesmas and return the alamat from the result table.
    
    Returns:
        tuple: (status, alamat_or_message)
            status: "success", "not_found", "error"
            alamat_or_message: the address string, or error/skip message
    """
    # Ensure search type is set to "NIK / No Asuransi"
    page.locator('select[name="typeSearch"]').select_option("nik_no_asuransi")

    # Clear and fill the search field
    search_input = page.locator('input[name="typeSearchValue"]')
    search_input.fill(no_bpjs)

    # Click Cari button
    page.locator('#form_search button[type="submit"]').click()

    # Wait for table to update (either rows appear or "no data" message)
    try:
        page.locator(".datatable tbody tr").first.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        return "error", "timeout menunggu hasil pencarian"

    # Small buffer for table to fully render
    page.wait_for_timeout(1000)

    # Check if there are results
    rows = page.locator(".datatable tbody tr")
    row_count = rows.count()

    if row_count == 0:
        return "not_found", "tidak ditemukan di ePuskesmas"

    # The table has: No, No.eRM, No.RM Lama, No.Dok.RM, Nama, NIK, No.Penjamin, JK, TTL, Kelurahan, Alamat, Cetak, Check
    # Kelurahan is column index 9 (0-based)
    first_row = rows.first
    cells = first_row.locator("td")

    # Check if we got a "no data" row
    cell_count = cells.count()
    if cell_count < 11:
        return "not_found", "tidak ditemukan di ePuskesmas"

    # Get kelurahan from column index 9
    kelurahan = cells.nth(9).inner_text().strip()

    if not kelurahan:
        return "not_found", "kelurahan kosong di ePuskesmas"

    return "success", kelurahan


def run_update_alamat(page, csv_path, submit_form=True, log=None, stop_check=None):
    """Process a single CSV file: search each BPJS number and update alamat.
    
    Args:
        page: Playwright page object (already logged in to ePuskesmas)
        csv_path: Path to the CSV file to update
        submit_form: If True, save updated CSV. If False, only log results (test mode).
        log: Optional callback function for logging
        stop_check: Optional callable that returns True if automation should stop
        
    Returns:
        dict: counts of success, not_found, error
    """
    import pandas as pd
    import os

    def _log(msg):
        if log:
            log(msg)

    # Read CSV
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    total = len(df)
    _log(f"📁 File: {os.path.basename(csv_path)} ({total} data)")

    counts = {"success": 0, "not_found": 0, "error": 0, "skipped": 0}

    for index, row in df.iterrows():
        if stop_check and stop_check():
            _log("🛑 Dihentikan oleh user.")
            break

        no_bpjs = str(row["NO_BPJS"]).strip()
        current_alamat = str(row["ALAMAT"]).strip()

        _log(f"  [{index + 1}/{total}] {no_bpjs}")

        try:
            status, result = search_alamat(page, no_bpjs)

            if status == "success":
                if submit_form:
                    df.at[index, "ALAMAT"] = result
                counts["success"] += 1
                _log(f"    ✅ {result}")
            elif status == "not_found":
                # Assign random fallback address
                fallback = random.choice(FALLBACK_ALAMAT)
                if submit_form:
                    df.at[index, "ALAMAT"] = fallback
                counts["not_found"] += 1
                _log(f"    ⏭ {result} → fallback: {fallback}")
            else:
                counts["error"] += 1
                _log(f"    ❌ {result}")
        except Exception as e:
            counts["error"] += 1
            _log(f"    ❌ ERROR: {e}")

        # Small delay between searches
        page.wait_for_timeout(1000)

    # Save updated CSV only in submit mode
    if submit_form:
        df.to_csv(csv_path, index=False)
        _log(f"  💾 Disimpan: {os.path.basename(csv_path)}")
    else:
        _log(f"  🔍 TEST MODE — file tidak diubah")

    return counts

"""Komdat Posyandu automation — fills the monthly posyandu form on microsite kemkes."""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

KOMDAT_LOGIN_URL = "https://microsite.kemkes.go.id/med_mci_si12/web/site/login"
KOMDAT_EDIT_URL = "/med_mci_si12/web/data-posyandu-aktif/update?id=rPQOpkQP653sXmE6v4K5Mw%3D%3D"
BASE_URL = "https://microsite.kemkes.go.id"

MONTH_MAP = {
    "jan": 1, "januari": 1,
    "feb": 2, "februari": 2,
    "mar": 3, "maret": 3,
    "apr": 4, "april": 4,
    "mei": 5, "may": 5,
    "jun": 6, "juni": 6,
    "jul": 7, "juli": 7,
    "aug": 8, "agu": 8, "agustus": 8,
    "sep": 9, "september": 9,
    "okt": 10, "oct": 10, "oktober": 10,
    "nov": 11, "november": 11,
    "des": 12, "dec": 12, "desember": 12,
}


def parse_month(month_str: str) -> int:
    """Convert month string like 'mei', 'jun', 'april' to month number."""
    key = month_str.strip().lower()
    if key.isdigit():
        return int(key)
    if key not in MONTH_MAP:
        raise ValueError(f"Bulan tidak dikenal: '{month_str}'. Contoh: jan, feb, mar, apr, mei, jun")
    return MONTH_MAP[key]


def navigate_to_table(page: Page):
    """Click the Edit button on the Kegiatan Posyandu page."""
    page.locator("a.btn-success.btn-action[title='Edit']").first.click()
    page.wait_for_timeout(3000)


def fill_posyandu_modal(page: Page, submit_form: bool):
    """Fill the modal form with the standard answers and click UPDATE if submit_form=True."""
    # Wait for modal content to load
    page.wait_for_timeout(2000)

    modal = page.locator("#editModalId2")

    # 1. Melakukan Kegiatan Hari Buka
    modal.locator("input[name='status_layanan'][value='1']").click()
    page.wait_for_timeout(500)

    # Check the 3 layanan_bayi_balita checkboxes
    modal.locator("#layanan_bayi_balita_1").check(force=True)
    modal.locator("#layanan_bayi_balita_2").check(force=True)
    modal.locator("#layanan_bayi_balita_3").check(force=True)

    # 2. Melakukan Penyuluhan Kesehatan dan Gizi
    modal.locator("input[name='status_penyuluhan'][value='1']").click()
    page.wait_for_timeout(300)

    # 3. Melakukan Pemberian PMT → Sesuai Standar
    modal.locator("input[name='pmt_penyuluhan'][value='Ya']").click()
    page.wait_for_timeout(300)
    modal.locator("input[name='pmt_penyuluhan_standar'][value='Ya']").click()
    page.wait_for_timeout(300)

    # Sumber Pembiayaan: leave as is (don't select anything)

    # 4. Melakukan Layanan Kunjungan Rumah
    modal.locator("input[name='status_layanan_kunjungan_rumah'][value='1']").click()
    page.wait_for_timeout(300)

    # 5. Bimbingan Teknis: Sudah
    modal.locator("input[name='pembinaan_teknis'][value='Sudah']").click()
    page.wait_for_timeout(300)

    # Pendamping: PUSKESMAS
    modal.locator("#pendamping_pembinaan_teknis").select_option("1")

    # 6. Lapor Kegiatan: Sudah
    modal.locator("input[name='laporan_pustu'][value='Sudah']").click()
    page.wait_for_timeout(300)

    # Periode: 1 Kali/Minggu
    modal.locator("#periode_laporan_pustu").select_option("1 Kali/Minggu")

    # 7. Supervisi: Sudah
    modal.locator("input[name='supervisi_posyandu'][value='Sudah']").click()
    page.wait_for_timeout(300)

    if not submit_form:
        # Test mode: close modal without saving
        modal.locator(".close[data-dismiss='modal']").click()
        page.wait_for_timeout(1000)
        return

    # 8. Click UPDATE button
    modal.locator("#btn-simpan").click()
    page.wait_for_timeout(3000)

    # Dismiss SweetAlert if visible
    try:
        swal_btn = page.locator(".swal2-confirm, .confirm, .swal2-styled")
        if swal_btn.first.is_visible(timeout=3000):
            swal_btn.first.click()
            page.wait_for_timeout(1000)
    except Exception:
        pass


def run_komdat(page: Page, month_num: int, submit_form: bool, log_fn, stop_check):
    """
    Main automation loop: iterate all posyandu rows for the given month.
    - Skip green buttons (btn-success)
    - Click grey buttons (btn-default) and fill the modal
    """
    # Find all UPDATE buttons for the target month (column index based on month)
    # The buttons have class like btn-bulan{posyandu_id}{month_num}
    # and contain "bulan={month_num}" in their delete-url
    rows = page.locator("table.table-bordered tbody tr")
    row_count = rows.count()
    log_fn(f"📊 Found {row_count} posyandu rows")

    processed = 0
    skipped = 0

    for i in range(row_count):
        if stop_check():
            log_fn("🛑 Stop requested.")
            break

        row = rows.nth(i)
        # Get posyandu name from 3rd td
        name_el = row.locator("td").nth(2)
        posyandu_name = name_el.inner_text().strip() if name_el.is_visible() else f"Row {i+1}"

        # Find the UPDATE button for this month by matching bulan= in the URL
        btn = row.locator(f"a.modalButton[delete-url*='bulan={month_num}']")
        if btn.count() == 0:
            log_fn(f"  [{i+1}] {posyandu_name} — bulan {month_num} tidak tersedia, skip")
            skipped += 1
            continue

        # Check if already done (green = btn-success)
        btn_class = btn.first.get_attribute("class") or ""
        if "btn-success" in btn_class:
            log_fn(f"  [{i+1}] {posyandu_name} — ✅ already done, skip")
            skipped += 1
            continue

        # Click the grey button to open modal
        log_fn(f"  [{i+1}] {posyandu_name} — filling...")
        btn.first.click()
        page.wait_for_timeout(2000)

        try:
            fill_posyandu_modal(page, submit_form)
            processed += 1
            log_fn(f"  [{i+1}] {posyandu_name} — ✅ done")
        except Exception as e:
            log_fn(f"  [{i+1}] {posyandu_name} — ❌ error: {e}")
            # Try to close modal
            try:
                page.locator("#editModalId2 .close").click()
                page.wait_for_timeout(1000)
            except Exception:
                pass

        page.wait_for_timeout(1000)

    return processed, skipped

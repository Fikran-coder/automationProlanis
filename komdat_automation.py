"""Komdat Posyandu automation — fills the monthly posyandu form on microsite kemkes."""

import random

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


def generate_sasaran_data() -> dict:
    """
    Generate random values for the mandatory "Kelompok Sasaran" table.

    Rules (sasaran = jumlah sasaran, kunjungan = jumlah kunjungan ke posyandu):
    - Ibu Hamil:  sasaran = rand(8, 12);   kunjungan = sasaran - rand(0, 1)
    - Bayi/Balita: sasaran = rand(31, 47); kunjungan = sasaran - rand(5, 7)
    - Remaja:     sasaran = rand(9, 11);   kunjungan = sasaran - rand(1, 3)
    - Dewasa (usia_produktif): sasaran = rand(21, 27); kunjungan = sasaran - rand(7, 10)
    - Lansia:     sasaran = rand(26, 31);  kunjungan = sasaran - rand(7, 10)

    All "dirujuk" (kunjungan dirujuk) fields are set to 0.

    Returns a dict of field_id -> value (int) for the sasaran, kunjungan and
    dirujuk inputs.
    """
    ibu_hamil_sasaran = random.randint(8, 12)
    ibu_hamil = ibu_hamil_sasaran - random.randint(0, 1)

    bayi_balita_sasaran = random.randint(31, 47)
    bayi_balita = bayi_balita_sasaran - random.randint(5, 7)

    remaja_sasaran = random.randint(9, 11)
    remaja = remaja_sasaran - random.randint(1, 3)

    usia_produktif_sasaran = random.randint(21, 27)
    usia_produktif = usia_produktif_sasaran - random.randint(7, 10)

    lansia_sasaran = random.randint(26, 31)
    lansia = lansia_sasaran - random.randint(7, 10)

    return {
        "ibu_hamil_sasaran": ibu_hamil_sasaran,
        "ibu_hamil": ibu_hamil,
        "ibu_hamil_dirujuk": 0,
        "bayi_balita_sasaran": bayi_balita_sasaran,
        "bayi_balita": bayi_balita,
        "bayi_balita_dirujuk": 0,
        "remaja_sasaran": remaja_sasaran,
        "remaja": remaja,
        "remaja_dirujuk": 0,
        "usia_produktif_sasaran": usia_produktif_sasaran,
        "usia_produktif": usia_produktif,
        "usia_produktif_dirujuk": 0,
        "lansia_sasaran": lansia_sasaran,
        "lansia": lansia,
        "lansia_dirujuk": 0,
    }


def fill_kelompok_sasaran(page, container, log_fn=None) -> dict:
    """
    Fill the mandatory "Kelompok Sasaran" table with random-generated values.

    The percentage columns are readonly and recalculated by the page's jQuery
    `keyup` handlers, so after setting each value we dispatch input/keyup events
    to trigger the auto-calculation.

    `container` is a Playwright locator scoping the inputs (e.g. the modal), so
    we don't accidentally match hidden inputs elsewhere on the page.
    """
    data = generate_sasaran_data()

    # Order matters for the auto-percentage: fill sasaran (pembagi) before the
    # kunjungan value, and the kunjungan value before its dirujuk value, so the
    # keyup handlers compute correct percentages.
    fill_order = [
        "ibu_hamil_sasaran", "ibu_hamil", "ibu_hamil_dirujuk",
        "bayi_balita_sasaran", "bayi_balita", "bayi_balita_dirujuk",
        "remaja_sasaran", "remaja", "remaja_dirujuk",
        "usia_produktif_sasaran", "usia_produktif", "usia_produktif_dirujuk",
        "lansia_sasaran", "lansia", "lansia_dirujuk",
    ]

    for field_id in fill_order:
        value = data[field_id]
        field = container.locator(f"#{field_id}")
        field.wait_for(state="visible", timeout=10000)
        # Clear then type so the number input accepts the value and native
        # events (input) fire; then explicitly dispatch keyup for the jQuery
        # handlers bound with .keyup().
        field.fill("")
        field.fill(str(value))
        field.dispatch_event("input")
        field.dispatch_event("keyup")
        if log_fn:
            log_fn(f"    ✏️  {field_id} = {value}")
        page.wait_for_timeout(150)

    if log_fn:
        log_fn(
            "    📝 Sasaran (kunjungan/sasaran): "
            f"Ibu Hamil {data['ibu_hamil']}/{data['ibu_hamil_sasaran']}, "
            f"Bayi/Balita {data['bayi_balita']}/{data['bayi_balita_sasaran']}, "
            f"Remaja {data['remaja']}/{data['remaja_sasaran']}, "
            f"Dewasa {data['usia_produktif']}/{data['usia_produktif_sasaran']}, "
            f"Lansia {data['lansia']}/{data['lansia_sasaran']}"
        )

    return data


def fill_posyandu_modal(page: Page, submit_form: bool, log_fn=None):
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

    # 8. Kelompok Sasaran (mandatory) — random-generated values.
    # Scope to the modal if the inputs live there; otherwise fall back to page.
    if modal.locator("#ibu_hamil_sasaran").count() > 0:
        sasaran_container = modal
    else:
        sasaran_container = page
    fill_kelompok_sasaran(page, sasaran_container, log_fn)

    if not submit_form:
        # Test mode: close modal without saving
        modal.locator(".close[data-dismiss='modal']").click()
        page.wait_for_timeout(1000)
        return

    # 9. Click UPDATE button
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


def run_komdat(page: Page, month_num: int, submit_form: bool, log_fn, stop_check, on_progress=None):
    """
    Main automation loop: iterate all posyandu rows for the given month.
    - Skip green buttons (btn-success)
    - Click grey buttons (btn-default) and fill the modal
    - on_progress(processed, skipped, errors) called after each row
    """
    rows = page.locator("table.table-bordered tbody tr")
    row_count = rows.count()
    log_fn(f"📊 Found {row_count} posyandu rows")

    processed = 0
    skipped = 0
    errors = 0

    for i in range(row_count):
        if stop_check():
            log_fn("🛑 Stop requested.")
            break

        row = rows.nth(i)
        name_el = row.locator("td").nth(2)
        posyandu_name = name_el.inner_text().strip() if name_el.is_visible() else f"Row {i+1}"

        btn = row.locator(f"a.modalButton[delete-url*='bulan={month_num}']")
        if btn.count() == 0:
            log_fn(f"  [{i+1}] {posyandu_name} — bulan {month_num} tidak tersedia, skip")
            skipped += 1
            if on_progress:
                on_progress(processed, skipped, errors)
            continue

        btn_class = btn.first.get_attribute("class") or ""
        if "btn-success" in btn_class:
            log_fn(f"  [{i+1}] {posyandu_name} — ✅ already done, skip")
            skipped += 1
            if on_progress:
                on_progress(processed, skipped, errors)
            continue

        log_fn(f"  [{i+1}] {posyandu_name} — filling...")
        btn.first.click()
        page.wait_for_timeout(2000)

        try:
            fill_posyandu_modal(page, submit_form, log_fn)
            processed += 1
            log_fn(f"  [{i+1}] {posyandu_name} — ✅ done")
        except Exception as e:
            errors += 1
            log_fn(f"  [{i+1}] {posyandu_name} — ❌ error: {e}")
            # Try to close modal
            try:
                page.locator("#editModalId2 .close").click()
                page.wait_for_timeout(1000)
            except Exception:
                pass

        if on_progress:
            on_progress(processed, skipped, errors)
        page.wait_for_timeout(1000)

    return processed, skipped, errors

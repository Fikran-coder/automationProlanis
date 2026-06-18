from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

FORM_URL = "https://pcarejkn.bpjs-kesehatan.go.id/eclaim/EntriPesertaProlanis"

# Constants
DEFAULT_EMAIL = "upttamansari@gmail.com"
DEFAULT_KETERANGAN = "riwayat hipertensi"
DEFAULT_PROGRAM = "02"  # 02 = Hipertensi
DEFAULT_TENAGA_MEDIS = "NETTY SUSILAWATI"
DEFAULT_TELEPON = "089526585949"


def fill_peserta_row(page, row, index, submit_form):
    no_bpjs = str(row["NO_BPJS"]).strip()
    telepon = str(row["TELEPON"]).strip()
    alamat = str(row["ALAMAT"]).strip()

    # Search patient
    page.locator("#txtnokartu").fill(no_bpjs)
    page.locator("#btnCariPeserta").click()
    page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning, .bootbox-body").first.wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(800)

    # Check alerts
    alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
    if alert.is_visible():
        msg = alert.inner_text().strip()
        dismiss = page.locator(".bootbox .btn, .bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
        if dismiss.is_visible():
            dismiss.click()
        page.locator(".bootbox.modal").wait_for(state="hidden", timeout=5000)
        page.wait_for_timeout(500)
        page.locator("#txtnokartu").fill("")
        return "skipped", msg

    # Check if already registered as Prolanis
    prb_lbl = page.locator("#prb_lbl")
    if prb_lbl.is_visible() and "Prolanis" in prb_lbl.inner_text():
        page.locator("#txtnokartu").fill("")
        return "skipped", "sudah terdaftar Prolanis"

    # Fill form
    page.locator("#cbx_program").select_option(DEFAULT_PROGRAM)

    # Tenaga Medis (select2) - click to open, then select
    page.locator("#select2-cbx_tenagamedis-container").click()
    page.get_by_role("treeitem", name=DEFAULT_TENAGA_MEDIS).click()

    if telepon and telepon.strip("0") and len(telepon) >= 8:
        page.locator("#txt_telepon").fill(telepon)
    else:
        page.locator("#txt_telepon").fill(DEFAULT_TELEPON)
    page.locator("#txt_email").fill(DEFAULT_EMAIL)
    if alamat:
        page.locator("#txt_alamat").fill(alamat)
    page.locator("#txt_keterangan").fill(DEFAULT_KETERANGAN)

    if submit_form:
        page.wait_for_timeout(1000)
        if page.locator("#btnSimpanPesertaProlanis").is_disabled():
            page.locator("#txtnokartu").fill("")
            return "skipped", "button disabled"
        page.locator("#btnSimpanPesertaProlanis").click()
        try:
            page.locator(".alert-success, .gritter-item-wrapper").first.wait_for(state="visible", timeout=10000)
            dismiss = page.locator(".gritter-close").first
            if dismiss.is_visible():
                dismiss.click()
            return "success", ""
        except PlaywrightTimeoutError:
            return "success", "no banner"
    else:
        return "test", ""

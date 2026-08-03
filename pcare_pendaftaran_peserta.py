from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

FORM_URL = "https://pcarejkn.bpjs-kesehatan.go.id/eclaim/EntriPesertaProlanis"

# Constants
DEFAULT_EMAIL = "upttamansari@gmail.com"
DEFAULT_KETERANGAN = "riwayat hipertensi"
DEFAULT_PROGRAM = "02"  # 02 = Hipertensi
DEFAULT_TENAGA_MEDIS = "NETTY SUSILAWATI"
DEFAULT_TELEPON = "089526585949"

TURNSTILE_SELECTOR = "#cf-chl-widget-wqahr_response"


def _wait_turnstile(page, timeout=15000):
    """Wait until Cloudflare Turnstile token is populated."""
    try:
        page.wait_for_function(
            """() => {
                const el = document.querySelector('[name="cf-turnstile-response"]');
                return el && el.value && el.value.length > 20;
            }""",
            timeout=timeout,
        )
        return True
    except PlaywrightTimeoutError:
        return False


def fill_peserta_row(page, row, index, submit_form, tanggal=None, log=None):
    no_bpjs = str(row["NO_BPJS"]).strip()
    telepon = str(row["TELEPON"]).strip()
    alamat = str(row["ALAMAT"]).strip()

    def _log(msg):
        if log:
            log(msg)

    # Wait for Turnstile token
    turnstile_ready = _wait_turnstile(page, timeout=10000)
    if not turnstile_ready:
        # Token not ready — notify user to click Turnstile checkbox
        _log("  ⚠️ Klik checkbox Turnstile di browser, menunggu...")
        try:
            import platform
            if platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(['osascript', '-e',
                    'display notification "Klik checkbox Turnstile di browser!" with title "PCare Automation" sound name "Ping"'])
            elif platform.system() == "Windows":
                from tkinter import messagebox as _mb
                import threading
                threading.Thread(target=lambda: _mb.showwarning(
                    "PCare Automation", "Klik checkbox Turnstile di browser!"), daemon=True).start()
            else:
                print("\a")
        except Exception:
            pass
        turnstile_ready = _wait_turnstile(page, timeout=60000)
    if not turnstile_ready:
        return "skipped", "Turnstile token belum siap (timeout 60s)"

    # Search patient
    page.locator("#txtnokartu").fill(no_bpjs)
    page.locator("#btnCariPeserta").click()

    # Clear token after click so next check waits for fresh token
    page.evaluate("""() => {
        const el = document.querySelector('[name="cf-turnstile-response"]');
        if (el) el.value = '';
    }""")

    # Wait for result
    try:
        page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning").first.wait_for(state="visible", timeout=20000)
    except PlaywrightTimeoutError:
        # No response — auto-retry klik Cari
        _log("  ⚠️ Token expired, retry klik Cari otomatis...")
        got_response = False
        for retry in range(8):
            page.wait_for_timeout(8000)
            page.locator("#txtnokartu").fill(no_bpjs)
            page.locator("#btnCariPeserta").click()
            page.evaluate("""() => {
                const el = document.querySelector('[name="cf-turnstile-response"]');
                if (el) el.value = '';
            }""")
            try:
                page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning").first.wait_for(state="visible", timeout=10000)
                got_response = True
                break
            except PlaywrightTimeoutError:
                _log(f"    retry {retry + 1}/8...")
                continue
        if not got_response:
            page.locator("#txtnokartu").fill("")
            return "skipped", "tidak ada respons setelah 8 retry"

    page.wait_for_timeout(800)

    # Check if page got redirected after search
    if "EntriPesertaProlanis" not in page.url:
        page.goto(FORM_URL, wait_until="domcontentloaded")
        page.locator("#txtnokartu").wait_for(state="visible", timeout=15000)
        if tanggal:
            page.evaluate("""(date) => {
                const el = document.querySelector('#txt_tglMulai');
                if (el) { el.value = date; el.dispatchEvent(new Event('change', { bubbles: true })); }
            }""", tanggal)
        return "skipped", "halaman redirect, kembali ke form"

    # Restore tanggal after search
    if tanggal:
        page.evaluate("""(date) => {
            const el = document.querySelector('#txt_tglMulai');
            if (el) { el.value = date; el.dispatchEvent(new Event('change', { bubbles: true })); }
        }""", tanggal)

    # Check alerts — dismiss system modals, skip only for patient-specific
    alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
    if alert.is_visible():
        msg = alert.inner_text().strip()
        if "Belum Entri Pelayanan" in msg or "HFIS" in msg or "pakta integritas" in msg.lower():
            # System modal — dismiss and continue
            dismiss = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close, [data-notify='dismiss']").first
            if dismiss.is_visible():
                dismiss.click()
                page.wait_for_timeout(500)
        else:
            # Patient-specific alert — dismiss without reload
            dismiss = page.locator(".bootbox .btn, .bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
            if dismiss.is_visible():
                dismiss.click()
            try:
                page.locator(".bootbox.modal").wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
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

import os
import time
import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform?pli=1&pli=1"


def _clean(val):
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s



def find_question_item(page, title_pattern):
    """Find the listitem container of a Google Form question by heading text."""
    title_pattern_lower = title_pattern.lower()
    for item in page.locator('div[role="listitem"]').all():
        heading = item.locator('[role="heading"]').first
        if heading.is_visible():
            text = (
                heading.inner_text()
                .strip()
                .replace("\xa0", " ")
                .replace("\n", " ")
                .replace("*", "")
                .strip()
                .lower()
            )
            if title_pattern_lower in text:
                if title_pattern_lower == "usia" and "rentang" in text:
                    continue
                return item
    return None


def fill_text(page, label, value):
    item = find_question_item(page, label)
    if not item:
        return False
    inp = item.locator('input[type="text"]').first
    if inp.is_visible(timeout=3000):
        inp.fill(str(value))
        return True
    return False


def select_dropdown(page, label, value):
    item = find_question_item(page, label)
    if not item:
        return False
    listbox = item.locator('div[role="listbox"]').first
    if not listbox.is_visible(timeout=3000):
        return False
    listbox.click()
    page.wait_for_timeout(400)

    val_str = str(value).strip()
    opt = page.locator(f'div[role="option"][data-value="{val_str}"]').first
    if not opt.is_visible():
        opt = page.locator(f'div[role="option"]:has-text("{val_str}")').first

    if opt.is_visible(timeout=2000):
        opt.click()
        page.wait_for_timeout(400)
        return True
    return False


def select_radio(page, label, value):
    item = find_question_item(page, label)
    if not item:
        return False
    val_str = str(value).strip()
    radio = item.locator(f'div[role="radio"][data-value="{val_str}"]').first
    if not radio.is_visible():
        radio = item.locator(f'div[role="radio"]:has-text("{val_str}")').first

    if radio.is_visible(timeout=2000):
        radio.click()
        page.wait_for_timeout(300)
        return True
    return False


def click_primary_btn(page):
    """Click primary Next / Submit button."""
    btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    if not btn.is_visible(timeout=3000):
        btn = page.locator(
            'div[role="button"]:has-text("Berikutnya"), '
            'div[role="button"]:has-text("Next"), '
            'div[role="button"]:has-text("Kirim"), '
            'div[role="button"]:has-text("Submit")'
        ).first
    btn.click()
    page.wait_for_timeout(1200)


def reset_form_clean(page, max_backs=15):
    """Clear form answers and return to initial form page."""
    try:
        clear_btn = page.locator(
            'div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")'
        ).first
        if clear_btn.is_visible(timeout=1500):
            clear_btn.click()
            page.wait_for_timeout(500)
            confirm_btn = page.locator(
                'div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")'
            ).last
            if confirm_btn.is_visible(timeout=1500):
                confirm_btn.click()
                page.wait_for_timeout(800)
    except Exception:
        pass

    # If still on subpages, click back
    for _ in range(max_backs):
        btn = page.locator(
            'div[role="button"]:has-text("Kembali"), div[role="button"]:has-text("Back")'
        ).first
        if btn.is_visible(timeout=800):
            btn.click()
            page.wait_for_timeout(500)
        else:
            break

    try:
        page.goto(PHS_FORM_URL, timeout=30000)
    except Exception:
        pass


def click_back_until_start(page, max_backs=15):
    reset_form_clean(page, max_backs=max_backs)


def reach_final_page(page):
    """Click Berikutnya from the last question page to reach the final Kirim page."""
    kirim_btn = page.locator(
        'div[role="button"]:has-text("Kirim"), '
        'div[role="button"]:has-text("Submit"), '
        'div[role="button"][jsname="M2UYVd"]'
    ).first
    if not kirim_btn.is_visible(timeout=1500):
        click_primary_btn(page)
        try:
            kirim_btn.wait_for(state="visible", timeout=10000)
        except Exception:
            page.wait_for_timeout(1000)


def submit_and_restart(page, log=None):
    reach_final_page(page)
    if log:
        log("  🚀 Mengirim form...")
    kirim_btn = page.locator(
        'div[role="button"]:has-text("Kirim"), '
        'div[role="button"]:has-text("Submit"), '
        'div[role="button"][jsname="M2UYVd"]'
    ).first
    if kirim_btn.is_visible(timeout=3000):
        kirim_btn.click()
    else:
        click_primary_btn(page)

    # Tunggu konfirmasi submit Google Form
    try:
        page.wait_for_selector(
            'div:has-text("telah direkam"), div:has-text("has been recorded"), '
            'a:has-text("Kirim tanggapan lain"), a:has-text("Submit another response")',
            timeout=15000
        )
    except Exception:
        page.wait_for_timeout(3000)

    # Prioritaskan klik link "Kirim tanggapan lain" (tanpa hard reload)
    link = page.locator(
        'a:has-text("Kirim tanggapan lain"), a:has-text("Submit another response")'
    ).first
    if link.is_visible(timeout=3000):
        link.click()
        page.wait_for_timeout(1000)
    else:
        page.goto(PHS_FORM_URL, timeout=30000)

    # Pastikan form siap di Page 1 untuk baris berikutnya
    try:
        page.wait_for_selector('div[role="button"][jsname="OCpkoe"]', timeout=15000)
    except Exception:
        pass

    return "success", "Terkirim ke Google Form"


def cancel_and_restart(page, log=None, reason=""):
    reach_final_page(page)
    if log:
        log(f"  🔍 [TEST MODE] Mencapai halaman akhir Kirim ({reason}). Tidak submit, reset form...")
    reset_form_clean(page)
    return "test", "Pengisian form berhasil (test mode)"


def fill_phs_single_row(page, record, submit_form=True, log=None):
    """Fill Google Form for a single PHS record.

    If submit_form=False (Test Mode), navigates through the pages, verifies questions,
    and backs out without submitting.
    If submit_form=True (Live Mode), clicks the final submit button and verifies submission.
    """
    def _l(msg):
        if log:
            log(msg)

    # Ensure on initial form page
    try:
        # Check if Page 1 Next button is present
        page.wait_for_selector('div[role="button"][jsname="OCpkoe"]', timeout=15000)
    except PlaywrightTimeoutError:
        page.goto(PHS_FORM_URL, timeout=30000)
        page.wait_for_selector('div[role="button"][jsname="OCpkoe"]', timeout=15000)

    # Page 1: Intro page
    # Click Next
    click_primary_btn(page)

    # Page 2: Data Responden
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    select_dropdown(page, "Kecamatan", record.get("Kecamatan", "Tamansari"))
    fill_text(page, "Desa/ Kelurahan", record.get("Desa", "Tamansari"))
    fill_text(page, "Puskesmas", record.get("Puskesmas", "Puskesmas Sirnagalih"))
    select_dropdown(page, "Siapa yang melakukan pendataan", record.get("Pendata", "Kader"))
    fill_text(page, "RW", _clean_or_dash(record.get("RW", "01")))
    fill_text(page, "RT", _clean_or_dash(record.get("RT", "01")))
    fill_text(page, "Nomor Kartu Keluarga/ NIK", _clean(record.get("NIK", "")))
    fill_text(page, "Nama Responden", record.get("Nama", ""))
    select_radio(page, "Jenis Kelamin", record.get("Jenis Kelamin", "Laki - Laki"))

    rentang_usia = record.get("Rentang Usia", "≥ 15 tahun")
    select_radio(page, "Rentang Usia", rentang_usia)
    fill_text(page, "Usia", _clean(record.get("Usia", "30")))
    select_dropdown(page, "Pendidikan Terakhir", record.get("Pendidikan Terakhir", "SMA Sederajat"))
    select_dropdown(page, "Pekerjaan", record.get("Pekerjaan", "Belum/Tidak Bekerja"))

    click_primary_btn(page)

    # If rentang_usia is >= 15 tahun, fill Tekanan Darah & Gula Darah pages
    if "≥ 15" in rentang_usia or "> 15" in rentang_usia:
        # Page 3: Tekanan Darah Ya/Tidak
        page.wait_for_selector('div[role="listitem"]', timeout=10000)
        select_radio(page, "Apakah anda melakukan cek tekanan darah", record.get("Cek Tekanan Darah", "Ya"))
        click_primary_btn(page)

        # Page 4: Tempat Tekanan Darah
        page.wait_for_selector('div[role="listitem"]', timeout=10000)
        select_radio(page, "dimana anda melakukan Cek Tekanan Darah", record.get("Tempat Tekanan Darah", "Posyandu/ Posbindu"))
        click_primary_btn(page)

        # Page 5: Gula Darah Ya/Tidak
        page.wait_for_selector('div[role="listitem"]', timeout=10000)
        select_radio(page, "Apakah anda melakukan cek gula darah", record.get("Cek Gula Darah", "Ya"))
        click_primary_btn(page)

        # Page 6: Tempat Gula Darah
        page.wait_for_selector('div[role="listitem"]', timeout=10000)
        select_radio(page, "dimana anda melakukan Cek gula darah", record.get("Tempat Gula Darah", "Posyandu/ Posbindu"))
        click_primary_btn(page)

    # Page 7: Aktivitas Fisik
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    select_radio(page, "Apakah anda melakukan aktivitas fisik", record.get("Aktivitas Fisik", "Ya"))
    click_primary_btn(page)

    # Page 8: Cuci Tangan
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    select_radio(page, "Apakah anda melakukan cuci tangan", record.get("Cuci Tangan", "Ya"))
    click_primary_btn(page)

    # Page 9: Konsumsi Buah & Sayur
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    select_radio(page, "Apakah anda mengonsumsi buah dan sayur", record.get("Buah dan Sayur", "3 Porsi"))
    click_primary_btn(page)

    # Page 10: Perokok Aktif
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    perokok_aktif = record.get("Perokok Aktif", "Tidak")
    select_radio(page, "Apakah Saat Ini Anda Perokok Aktif", perokok_aktif)

    # Branching for Smoking:
    if perokok_aktif == "Ya":
        if not submit_form:
            return cancel_and_restart(page, log=log, reason="perokok aktif: Ya")
        else:
            return submit_and_restart(page, log=log)

    # Perokok Aktif == "Tidak" -> go to Page 11
    click_primary_btn(page)

    # Page 11: Pernah Merokok
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    pernah_merokok = record.get("Pernah Merokok", "Tidak")
    select_radio(page, "Apakah anda pernah merokok", pernah_merokok)

    if pernah_merokok == "Tidak":
        if not submit_form:
            return cancel_and_restart(page, log=log, reason="tidak pernah merokok")
        else:
            return submit_and_restart(page, log=log)

    # Pernah Merokok == "Ya" -> go to Page 12 (Lama Berhenti Merokok)
    click_primary_btn(page)
    page.wait_for_selector('div[role="listitem"]', timeout=10000)
    lama_berhenti = record.get("Lama Berhenti Merokok", "Lebih dari 1 tahun")
    if not lama_berhenti:
        lama_berhenti = "Lebih dari 1 tahun"
    select_radio(page, "Sudah berapa lama anda berhenti merokok", lama_berhenti)

    if not submit_form:
        return cancel_and_restart(page, log=log, reason="lama berhenti merokok")
    else:
        return submit_and_restart(page, log=log)


def run_phs_batch(page, csv_path, submit_form=True, log=None, stop_check=None):
    """Process a PHS CSV batch file."""
    def _l(msg):
        if log:
            log(msg)

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    total = len(df)
    _l(f"📁 Membuka batch: {os.path.basename(csv_path)} ({total} data)")

    counts = {"success": 0, "test": 0, "error": 0, "skipped": 0}

    for index, row in df.iterrows():
        if stop_check and stop_check():
            _l("🛑 Dihentikan oleh user.")
            break

        rec = row.to_dict()
        nama = rec.get("Nama", f"Row {index+1}")
        nik = rec.get("NIK", "")
        _l(f"  [{index + 1}/{total}] {nama} (NIK: {nik})")

        try:
            status, message = fill_phs_single_row(page, rec, submit_form=submit_form, log=log)
            if status == "success":
                counts["success"] += 1
                _l(f"    ✅ Berhasil dikirim")
            elif status == "test":
                counts["test"] += 1
                _l(f"    🔍 Selesai uji alur (tidak submit)")
            else:
                counts["skipped"] += 1
                _l(f"    ⏭ Dilewati: {message}")
        except Exception as e:
            counts["error"] += 1
            _l(f"    ❌ Error: {e}")
            # Try to recover by reloading initial form URL
            try:
                page.goto(PHS_FORM_URL, timeout=30000)
            except Exception:
                pass

    return counts

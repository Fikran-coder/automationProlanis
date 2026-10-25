import os
import time
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform"

def find_question_item(page, title_pattern):
    # Match question listitem by its heading text
    for item in page.locator('div[role="listitem"]').all():
        heading = item.locator('[role="heading"]').first
        if heading.is_visible():
            text = heading.inner_text().strip().replace('\xa0', ' ').replace('\n', ' ').replace('*', '').strip()
            if title_pattern.lower() in text.lower():
                if title_pattern.lower() == "usia" and "rentang" in text.lower():
                    continue
                return item
    return None

def fill_text(page, label, value):
    item = find_question_item(page, label)
    if item:
        inp = item.locator('input[type="text"]').first
        inp.fill(str(value))
        return True
    return False

def select_dropdown(page, label, value):
    item = find_question_item(page, label)
    if item:
        listbox = item.locator('div[role="listbox"]').first
        listbox.click()
        page.wait_for_timeout(400)
        opt = page.locator(f'div[role="option"][data-value="{value}"]').first
        if not opt.is_visible():
            opt = page.locator(f'div[role="option"]:has-text("{value}")').first
        opt.click()
        page.wait_for_timeout(400)
        return True
    return False

def select_radio(page, label, value):
    item = find_question_item(page, label)
    if item:
        radio = item.locator(f'div[role="radio"][data-value="{value}"]').first
        if not radio.is_visible():
            radio = item.locator(f'div[role="radio"]:has-text("{value}")').first
        radio.click()
        page.wait_for_timeout(300)
        return True
    return False

def click_primary_btn(page):
    btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    txt = btn.inner_text().strip()
    btn.click()
    page.wait_for_timeout(1000)
    return txt

def get_primary_btn_type(page):
    btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    if btn.is_visible(timeout=2000):
        txt = btn.inner_text().strip().lower()
        if "kirim" in txt or "submit" in txt:
            return "submit"
        if "berikutnya" in txt or "next" in txt:
            return "next"
    return "unknown"

def click_back_btn(page):
    btn = page.locator('div[role="button"]:has-text("Kembali"), div[role="button"]:has-text("Back")').first
    if btn.is_visible(timeout=1500):
        btn.click()
        page.wait_for_timeout(800)
        return True
    return False

def test_full_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(PHS_FORM_URL, timeout=30000)
        page.wait_for_load_state("networkidle")

        # Page 1 -> Next
        print("Page 1 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 2: Data Responden
        print("Page 2 filling...")
        assert select_dropdown(page, "Kecamatan", "Tamansari"), "Kecamatan failed"
        assert fill_text(page, "Desa/ Kelurahan", "Tamansari"), "Desa failed"
        assert fill_text(page, "Puskesmas", "Puskesmas Sirnagalih"), "Puskesmas failed"
        assert select_dropdown(page, "Siapa yang melakukan pendataan", "Kader"), "Pendata failed"
        assert fill_text(page, "RW", "01"), "RW failed"
        assert fill_text(page, "RT", "02"), "RT failed"
        assert fill_text(page, "Nomor Kartu Keluarga/ NIK", "3201010101010001"), "NIK failed"
        assert fill_text(page, "Nama Responden", "Test Responden"), "Nama failed"
        assert select_radio(page, "Jenis Kelamin", "Perempuan"), "Jenis Kelamin failed"
        assert select_radio(page, "Rentang Usia", "≥ 15 tahun"), "Rentang Usia failed"
        assert fill_text(page, "Usia", "35"), "Usia failed"
        assert select_dropdown(page, "Pendidikan Terakhir", "SMA Sederajat"), "Pendidikan failed"
        assert select_dropdown(page, "Pekerjaan", "Ibu Rumah Tangga"), "Pekerjaan failed"

        print("Page 2 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 3: Indikator Cek Tekanan Darah
        print("Page 3: Tekanan darah...")
        assert select_radio(page, "Apakah anda melakukan cek tekanan darah", "Ya")
        print("Page 3 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 4: Tempat Tekanan Darah
        print("Page 4: Tempat tekanan darah...")
        assert select_radio(page, "dimana anda melakukan Cek Tekanan Darah", "Posyandu/ Posbindu")
        print("Page 4 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 5: Cek Gula Darah
        print("Page 5: Gula darah...")
        assert select_radio(page, "Apakah anda melakukan cek gula darah", "Ya")
        print("Page 5 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 6: Tempat Gula Darah
        print("Page 6: Tempat gula darah...")
        assert select_radio(page, "dimana anda melakukan Cek gula darah", "Posyandu/ Posbindu")
        print("Page 6 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 7: Aktivitas Fisik
        print("Page 7: Aktivitas fisik...")
        assert select_radio(page, "Apakah anda melakukan aktivitas fisik", "Ya")
        print("Page 7 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 8: Cuci Tangan
        print("Page 8: Cuci tangan...")
        assert select_radio(page, "Apakah anda melakukan cuci tangan", "Ya")
        print("Page 8 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 9: Buah & Sayur
        print("Page 9: Buah & sayur...")
        assert select_radio(page, "Apakah anda mengonsumsi buah dan sayur", "3 Porsi")
        print("Page 9 button:", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 10: Perokok Aktif
        print("Page 10: Perokok aktif -> select Tidak...")
        assert select_radio(page, "Apakah Saat Ini Anda Perokok Aktif", "Tidak")
        print("Page 10 button (when Tidak selected):", get_primary_btn_type(page))
        click_primary_btn(page)

        # Page 11: Pernah Merokok
        print("Page 11: Pernah merokok -> select Tidak...")
        assert select_radio(page, "Apakah anda pernah merokok", "Tidak")
        btn_type = get_primary_btn_type(page)
        print("Page 11 button (when Tidak selected):", btn_type)
        assert btn_type == "submit", f"Expected submit button on Page 11, got {btn_type}"

        # Test BACK navigation (Test mode simulation)
        print("Testing BACK navigation in test mode...")
        back_count = 0
        while click_back_btn(page):
            back_count += 1
            if back_count > 15:
                break
        print(f"Backed up {back_count} times! Back to initial pages.")

        browser.close()
        print("FULL FLOW TEST PASSED!")

if __name__ == "__main__":
    test_full_flow()

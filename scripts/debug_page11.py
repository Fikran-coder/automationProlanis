import os
import time
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform"

def find_question_item(page, title_pattern):
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
        page.wait_for_timeout(300)
        opt = page.locator(f'div[role="option"][data-value="{value}"]').first
        if not opt.is_visible():
            opt = page.locator(f'div[role="option"]:has-text("{value}")').first
        opt.click()
        page.wait_for_timeout(300)
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PHS_FORM_URL)

    # Page 1
    click_primary_btn(page)
    # Page 2
    select_dropdown(page, "Kecamatan", "Tamansari")
    fill_text(page, "Desa/ Kelurahan", "Tamansari")
    fill_text(page, "Puskesmas", "Puskesmas Sirnagalih")
    select_dropdown(page, "Siapa yang melakukan pendataan", "Kader")
    fill_text(page, "RW", "01")
    fill_text(page, "RT", "02")
    fill_text(page, "Nomor Kartu Keluarga/ NIK", "3201010101010001")
    fill_text(page, "Nama Responden", "Test Responden")
    select_radio(page, "Jenis Kelamin", "Perempuan")
    select_radio(page, "Rentang Usia", "≥ 15 tahun")
    fill_text(page, "Usia", "35")
    select_dropdown(page, "Pendidikan Terakhir", "SMA Sederajat")
    select_dropdown(page, "Pekerjaan", "Ibu Rumah Tangga")
    click_primary_btn(page)
    # Page 3
    select_radio(page, "Apakah anda melakukan cek tekanan darah", "Ya")
    click_primary_btn(page)
    # Page 4
    select_radio(page, "dimana anda melakukan Cek Tekanan Darah", "Posyandu/ Posbindu")
    click_primary_btn(page)
    # Page 5
    select_radio(page, "Apakah anda melakukan cek gula darah", "Ya")
    click_primary_btn(page)
    # Page 6
    select_radio(page, "dimana anda melakukan Cek gula darah", "Posyandu/ Posbindu")
    click_primary_btn(page)
    # Page 7
    select_radio(page, "Apakah anda melakukan aktivitas fisik", "Ya")
    click_primary_btn(page)
    # Page 8
    select_radio(page, "Apakah anda melakukan cuci tangan", "Ya")
    click_primary_btn(page)
    # Page 9
    select_radio(page, "Apakah anda mengonsumsi buah dan sayur", "3 Porsi")
    click_primary_btn(page)
    # Page 10
    select_radio(page, "Apakah Saat Ini Anda Perokok Aktif", "Tidak")
    click_primary_btn(page)

    # Page 11
    print("Page 11 items:")
    for it in page.locator('div[role="listitem"]').all():
        h = it.locator('[role="heading"]').first
        if h.is_visible():
            print(" ", h.inner_text().strip().replace('\n', ' '))
    select_radio(page, "Apakah anda pernah merokok", "Tidak")

    # Check button text and attributes on Page 11
    btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    print("Button text on Page 11:", btn.inner_text().strip())
    print("Button outerHTML:", btn.evaluate("el => el.outerHTML"))

    # What if we click Submit or click Next?
    # Note: DO NOT CLICK if it submits in live mode! But wait, is it submit button or next button?
    # Let's inspect the buttons container!
    btns = page.locator('div[role="button"]').all()
    for b in btns:
        if b.is_visible():
            print("Visible button:", b.inner_text().strip())

    browser.close()

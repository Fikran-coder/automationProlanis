import os
import time
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform"

def test_page_elements():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(PHS_FORM_URL, timeout=30000)
        page.wait_for_load_state("networkidle")

        # Check Page 1 (Intro)
        print("Page 1 Title:", page.title())
        next_btn = page.locator('div[role="button"]:has-text("Next"), div[role="button"]:has-text("Berikutnya")').first
        print("Next button visible on Page 1:", next_btn.is_visible())
        next_btn.click()
        page.wait_for_timeout(1500)

        # Page 2 (Data Responden)
        print("Page 2 Title:", page.locator('div[role="heading"]').first.inner_text())

        # Test finding dropdown for Kecamatan
        kec_item = page.locator('div[role="listitem"]:has-text("Kecamatan")').first
        print("Kecamatan question visible:", kec_item.is_visible())
        listbox = kec_item.locator('div[role="listbox"]').first
        print("Kecamatan listbox visible:", listbox.is_visible())
        listbox.click()
        page.wait_for_timeout(500)

        tamansari_opt = page.locator('div[role="option"][data-value="Tamansari"]').first
        print("Tamansari option visible:", tamansari_opt.is_visible())
        tamansari_opt.click()
        page.wait_for_timeout(500)

        # Test text input for Desa
        desa_item = page.locator('div[role="listitem"]:has-text("Desa")').first
        desa_input = desa_item.locator('input[type="text"]').first
        desa_input.fill("Tamansari")
        print("Desa filled:", desa_input.input_value())

        # Test radio for Jenis Kelamin
        jk_item = page.locator('div[role="listitem"]:has-text("Jenis Kelamin")').first
        jk_radio = jk_item.locator('div[role="radio"][data-value="Perempuan"]').first
        if not jk_radio.is_visible():
            jk_radio = jk_item.locator('div[role="radio"]:has-text("Perempuan")').first
        print("Jenis Kelamin radio visible:", jk_radio.is_visible())
        jk_radio.click()
        page.wait_for_timeout(500)

        browser.close()
        print("Test completed successfully!")

if __name__ == "__main__":
    test_page_elements()

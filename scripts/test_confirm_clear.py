import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform?pli=1&pli=1"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PHS_FORM_URL)
    page.wait_for_selector('div[role="button"]')
    page.locator('div[role="button"][jsname="OCpkoe"]').click()
    page.wait_for_timeout(1000)

    inp = page.locator('input[type="text"]').first
    inp.fill("Testing Reset")
    page.wait_for_timeout(500)

    # Click Kosongkan formulir on page
    clear_btn = page.locator('div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")').first
    clear_btn.click()
    page.wait_for_timeout(500)

    # Click confirmation button inside modal dialog
    # Modal dialog usually has role="dialog" or we can find the confirm button
    dialog = page.locator('div[role="dialog"]').first
    if dialog.is_visible():
        confirm_btn = dialog.locator('div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")').first
        confirm_btn.click()
        page.wait_for_timeout(1000)
        print("Clicked confirm clear in dialog!")

    print("Page URL after clear:", page.url)
    print("Any text input value:", page.locator('input[type="text"]').count())
    # Is Page 1 Next button visible?
    next_btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    print("Next btn visible:", next_btn.is_visible(), "Text:", next_btn.inner_text().strip())

    browser.close()

import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform?pli=1&pli=1"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PHS_FORM_URL)
    page.locator('div[role="button"][jsname="OCpkoe"]').click()
    page.wait_for_timeout(1000)

    # Click Kosongkan formulir on page
    clear_btn = page.locator('div[role="button"]:has-text("Kosongkan formulir")').first
    clear_btn.click()
    page.wait_for_timeout(1000)

    # Find all visible buttons now
    for b in page.locator('div[role="button"]').all():
        if b.is_visible():
            txt = b.inner_text().strip().replace('\n', ' ')
            print("Visible button:", txt, "HTML snippet:", b.evaluate("el => el.outerHTML.slice(0, 120)"))

    browser.close()

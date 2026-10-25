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

    # Click Kosongkan formulir
    page.locator('div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")').first.click()
    page.wait_for_timeout(500)

    # Click confirmation in modal (the last button with that text)
    page.locator('div[role="button"]:has-text("Kosongkan formulir"), div[role="button"]:has-text("Clear form")').last.click()
    page.wait_for_timeout(1000)

    print("Page URL after clear:", page.url)
    btn = page.locator('div[role="button"][jsname="OCpkoe"]').first
    print("Is Page 1 visible?:", btn.is_visible(), "Text:", btn.inner_text().strip())
    browser.close()

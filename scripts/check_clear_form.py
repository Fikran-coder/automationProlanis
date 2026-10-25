import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform?pli=1&pli=1"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PHS_FORM_URL)
    page.wait_for_selector('div[role="button"]')

    # Check all buttons on Page 1
    print("Page 1 buttons:")
    for b in page.locator('div[role="button"]').all():
        if b.is_visible():
            print(" -", b.inner_text().strip().replace('\n', ' '))

    # Click Next
    page.locator('div[role="button"][jsname="OCpkoe"]').click()
    page.wait_for_timeout(1000)

    # Check all buttons on Page 2
    print("Page 2 buttons:")
    for b in page.locator('div[role="button"]').all():
        if b.is_visible():
            print(" -", b.inner_text().strip().replace('\n', ' '))

    browser.close()

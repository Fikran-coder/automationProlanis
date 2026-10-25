import re
from playwright.sync_api import sync_playwright

PHS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PHS_FORM_URL)
    page.locator('div[role="button"]:has-text("Next"), div[role="button"]:has-text("Berikutnya")').first.click()
    page.wait_for_timeout(1500)

    items = page.locator('div[role="listitem"]').all()
    print("Found items on Page 2:", len(items))
    for i, it in enumerate(items):
        heading = it.locator('[role="heading"]').first
        title = heading.inner_text().strip() if heading.is_visible() else "NO HEADING"
        has_input = it.locator('input[type="text"]').count() > 0
        has_radio = it.locator('div[role="radio"]').count() > 0
        has_listbox = it.locator('div[role="listbox"]').count() > 0
        print(f"Item {i}: Title={title!r}, input={has_input}, radio={has_radio}, listbox={has_listbox}")
    browser.close()

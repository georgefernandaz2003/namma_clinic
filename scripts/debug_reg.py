import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()

    page.on('response', lambda res: print(f"[HTTP {res.status}] {res.url}") if '/api/' in res.url else None)

    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", "e2e_compounder_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/front-desk", timeout=10000)

    # Click Register New Patient
    page.click("button:has-text('Register New Patient')")
    time.sleep(1)

    timestamp = int(time.time()) % 100000
    name = f"Test Citizen {timestamp}"
    mobile = f"99111{timestamp:05d}"

    page.fill("input[placeholder='e.g. Ramesh Kumar']", name)
    page.fill("input[placeholder='e.g. 35']", "32")
    page.select_option("select:has(option[value='FEMALE'])", "FEMALE")
    page.fill("input[placeholder='10-digit mobile number']", mobile)

    page.click("button[type='submit']:has-text('Register Patient')")
    time.sleep(3)

    print("Page text snippet:")
    print(page.locator("div.fixed").all_inner_texts() if page.locator("div.fixed").count() > 0 else "Modal closed")
    print("Alerts:")
    print(page.locator("[role='alert'], .text-emerald-800, .bg-emerald-50").all_inner_texts())

    browser.close()

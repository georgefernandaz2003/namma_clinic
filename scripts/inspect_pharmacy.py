import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page()

    page.goto("http://localhost:3000/login")
    page.fill("#login-username", "e2e_pharmacist_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/pharmacy")
    page.wait_for_load_state("networkidle")

    # Navigate to /pharmacy
    page.goto("http://localhost:3000/pharmacy")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    print("Headings:", page.locator("h1, h2, h3").all_inner_texts()[:5])
    print("Buttons:", page.locator("button").all_inner_texts()[:10])
    
    b.close()

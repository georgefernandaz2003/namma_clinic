import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page()

    page.goto("http://localhost:3000/login")
    page.fill("#login-username", "e2e_doctor_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/doctor")
    page.wait_for_load_state("networkidle")

    # Navigate to visit 35 consultation
    page.goto("http://localhost:3000/consultation?visit=35")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    print("Title on page:", page.locator("h1, h2, h3").all_inner_texts()[:5])
    print("Test Masters select visible:", page.locator("select").count())
    
    b.close()

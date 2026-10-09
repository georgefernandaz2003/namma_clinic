import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page()
    page.goto("http://localhost:3000/login")
    page.fill("#login-username", "e2e_compounder_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/front-desk")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    rows = page.locator("table tbody tr").all_inner_texts()
    print("Found rows count:", len(rows))
    for r in rows[:5]:
        print("Row:", r.replace("\n", " | "))
    b.close()

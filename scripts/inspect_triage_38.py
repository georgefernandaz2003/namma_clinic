import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page()

    page.goto("http://localhost:3000/login")
    page.fill("#login-username", "e2e_nurse_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/nurse")

    page.goto("http://localhost:3000/triage?visit=38")
    time.sleep(2)

    main_el = page.locator("main")
    if main_el.count() > 0:
        print("Main text:")
        print(main_el.inner_text().encode('ascii', errors='ignore').decode())
    else:
        print("No main tag found. Body headings:")
        print(page.locator("h1, h2, h3, h4").all_inner_texts())

    b.close()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000/login")
    page.fill("#login-username", "e2e_compounder_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/front-desk")
    page.wait_for_timeout(3000)
    
    # Grab the text in the card
    text = page.locator("text=Registered Patients").locator("..").locator("div.text-xl").inner_text()
    print("UI Registered Patients Count:", text)
    browser.close()

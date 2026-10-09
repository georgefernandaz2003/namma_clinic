import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"E:\Namma_clinic\docs\audits\screenshots_e2e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(msg):
    print(f"[E2E] {msg}", flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    # STEP 1: Front Desk
    log("Navigating to login page...")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_selector("#login-username")
    page.fill("#login-username", "e2e_compounder_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")

    page.wait_for_url("**/dashboard/front-desk", timeout=10000)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    log("Front Desk Dashboard loaded.")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_front_desk_dashboard.png"))

    # Verify patient directory has Arun Kumar
    content = page.content()
    assert "Arun Kumar" in content, "Arun Kumar should appear in patient directory"
    log("Verified Arun Kumar appears in patient directory.")

    browser.close()
    log("Part 1 test passed successfully!")

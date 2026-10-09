import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"E:\Namma_clinic\docs\audits\screenshots_e2e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()

    page.on('response', lambda res: print(f"[HTTP {res.status}] {res.url}") if '/api/' in res.url else None)

    # Login as nurse
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", "e2e_nurse_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard/nurse", timeout=10000)
    page.wait_for_load_state("networkidle")
    print("Nurse Dashboard loaded.")

    # Check Priya Nair
    content = page.content()
    print("Priya Nair in dashboard:", "Priya Nair" in content)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_nurse_dashboard.png"))

    # Open Triage Station
    page.click("button:has-text('Open Triage Station')")
    page.wait_for_url("**/triage**", timeout=10000)
    page.wait_for_load_state("networkidle")
    print("Triage station loaded:", page.url)

    # Look for triage form
    time.sleep(1)
    notes_locator = page.locator("textarea[data-testid='nurse-notes'], textarea").first
    notes_locator.fill("Patient examined. Vitals normal. Referred to medical officer.")

    save_btn = page.locator("button[data-testid='save-triage-btn'], button:has-text('Save Triage & Send to Doctor')").first
    print("Save triage button visible:", save_btn.is_visible())
    save_btn.click()
    time.sleep(2)

    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_nurse_triage_completed.png"))
    print("Triage saved successfully!")

    browser.close()

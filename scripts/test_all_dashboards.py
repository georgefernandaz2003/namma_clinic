import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"E:\Namma_clinic\docs\audits\screenshots_e2e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ROLES = [
    ("e2e_compounder_user", "Password123!", "/dashboard/front-desk", "01_front_desk_dashboard.png"),
    ("e2e_nurse_user", "Password123!", "/dashboard/nurse", "03_nurse_dashboard.png"),
    ("e2e_doctor_user", "Password123!", "/dashboard/doctor", "05_doctor_dashboard.png"),
    ("e2e_lab_user", "Password123!", "/dashboard/lab", "07_lab_dashboard.png"),
    ("e2e_pharmacist_user", "Password123!", "/dashboard/pharmacy", "13_pharmacy_dashboard.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()

    for username, password, expected_path, screenshot_name in ROLES:
        print(f"Testing login for {username} -> {expected_path}...")
        page.goto(f"{BASE_URL}/login")
        page.fill("#login-username", username)
        page.fill("#login-password", password)
        page.click("button[type='submit']")
        page.wait_for_url(lambda u: expected_path in u, timeout=12000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        print(f"  Successfully landed at: {page.url}")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, screenshot_name))

    browser.close()
    print("All 5 roles logged in and landed at their respective dashboards perfectly!")

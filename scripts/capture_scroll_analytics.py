import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:3000"
ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity-ide\brain\a6c795c2-dc94-4409-bfa1-ef40002933eb"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    print("1. Logging in as Hospital Admin...")
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", "e2e_admin_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url(lambda u: "/dashboard" in u or "/admin" in u, timeout=10000)

    print("2. Navigating to /admin/analytics...")
    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Scroll Tab 1
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 550;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab1_scroll_urban_rural.png"))
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 1100;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab1_scroll_hierarchy_table.png"))

    # Tab 2: Trends
    print("3. Testing Tab 2: Trends...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.click("button:has-text('2. Longitudinal')")
    time.sleep(1)
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 450;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab2_scroll_chart_bars.png"))
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 950;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab2_scroll_epidemic_curves.png"))

    # Tab 3: Predictive
    print("4. Testing Tab 3: Predictive...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.click("button:has-text('3. Predictive')")
    time.sleep(1)
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 450;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab3_scroll_stock_table.png"))
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 950;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "tab3_scroll_ward_queue.png"))

    browser.close()
    print("All scroll screenshots captured successfully with #main-content scrolling!")

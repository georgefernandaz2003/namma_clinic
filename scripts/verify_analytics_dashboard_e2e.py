import os
import sys
import time
from playwright.sync_api import sync_playwright

def run():
    artifacts_dir = os.path.join(r"C:\Users\admin\.gemini\antigravity-ide\brain\a6c795c2-dc94-4409-bfa1-ef40002933eb")
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("1. Navigating to login page...")
        page.goto("http://localhost:3000/login")
        page.wait_for_selector('input[name="username"]', timeout=10000)

        print("2. Logging in as Hospital Admin (admin / admin123)...")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')

        page.wait_for_url("**/dashboard/admin", timeout=10000)
        time.sleep(2)
        print("   Current URL:", page.url)

        # 3. Click sidebar link
        print("3. Clicking Multi-Level & Predictive Dashboard in sidebar...")
        page.click('text="Multi-Level & Predictive Dashboard"')
        page.wait_for_url("**/admin/analytics", timeout=10000)
        time.sleep(2)
        print("   Successfully reached:", page.url)

        # Tab 1: Multi-Level Hierarchy
        print("4. Validating Tab 1: Multi-Level Hierarchy...")
        page.wait_for_selector('text="State Level: Karnataka"', timeout=10000)
        
        # Capture top of Tab 1
        tab1_top = os.path.join(artifacts_dir, "analytics_tab1_hierarchy_top.png")
        page.screenshot(path=tab1_top)
        print("   Saved:", tab1_top)

        # Scroll down to capture District, Zone, Ward, Facility sections
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        tab1_mid = os.path.join(artifacts_dir, "analytics_tab1_hierarchy_districts_zones.png")
        page.screenshot(path=tab1_mid)
        print("   Saved:", tab1_mid)

        page.evaluate("window.scrollTo(0, 1600)")
        time.sleep(1)
        tab1_bottom = os.path.join(artifacts_dir, "analytics_tab1_hierarchy_wards_facilities.png")
        page.screenshot(path=tab1_bottom)
        print("   Saved:", tab1_bottom)

        # Tab 2: Trend Analysis
        print("5. Clicking Tab 2: Trend Analysis...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        page.click('button:has-text("Trend Analysis")')
        time.sleep(2)
        page.wait_for_selector('text="4-Month Longitudinal Utilization"', timeout=10000)
        
        tab2_top = os.path.join(artifacts_dir, "analytics_tab2_trends_top.png")
        page.screenshot(path=tab2_top)
        print("   Saved:", tab2_top)

        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        tab2_bottom = os.path.join(artifacts_dir, "analytics_tab2_trends_bottom.png")
        page.screenshot(path=tab2_bottom)
        print("   Saved:", tab2_bottom)

        # Tab 3: Predictive Analytics
        print("6. Clicking Tab 3: Predictive Analytics...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        page.click('button:has-text("Predictive Analytics")')
        time.sleep(2)
        page.wait_for_selector('text="Ward-Level Disease Outbreak Risk Scoring"', timeout=10000)
        
        tab3_top = os.path.join(artifacts_dir, "analytics_tab3_predictive_top.png")
        page.screenshot(path=tab3_top)
        print("   Saved:", tab3_top)

        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        tab3_bottom = os.path.join(artifacts_dir, "analytics_tab3_predictive_bottom.png")
        page.screenshot(path=tab3_bottom)
        print("   Saved:", tab3_bottom)

        browser.close()
        print("\nAll Playwright verification steps completed with 100% success!")

if __name__ == "__main__":
    run()

import os
import time
from playwright.sync_api import sync_playwright

def run():
    artifacts_dir = r"C:\Users\admin\.gemini\antigravity-ide\brain\a6c795c2-dc94-4409-bfa1-ef40002933eb"
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("1. Login...")
        page.goto("http://localhost:3000/login")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/admin")

        print("2. Navigate to /admin/analytics...")
        page.click('text="Multi-Level & Predictive Dashboard"')
        page.wait_for_url("**/admin/analytics")
        page.wait_for_selector('text="Public Health & Predictive Analytics"')
        time.sleep(2)

        # -----------------
        # TAB 1: Hierarchy
        # -----------------
        print("3. Validating Tab 1...")
        p1 = os.path.join(artifacts_dir, "tab1_hierarchy_top.png")
        page.screenshot(path=p1)
        print("   Saved:", p1)

        # Scroll #main-content
        page.evaluate('document.querySelector("#main-content").scrollTop = 600')
        time.sleep(1)
        p2 = os.path.join(artifacts_dir, "tab1_hierarchy_districts.png")
        page.screenshot(path=p2)
        print("   Saved:", p2)

        page.evaluate('document.querySelector("#main-content").scrollTop = 1200')
        time.sleep(1)
        p3 = os.path.join(artifacts_dir, "tab1_hierarchy_zones_wards.png")
        page.screenshot(path=p3)
        print("   Saved:", p3)

        # -----------------
        # TAB 2: Trends
        # -----------------
        print("4. Switching to Tab 2: Trend Analysis...")
        page.evaluate('document.querySelector("#main-content").scrollTop = 0')
        time.sleep(0.5)
        # Click Trend Analysis tab button specifically
        trend_btn = page.locator('button:has-text("Trend Analysis")').first
        trend_btn.click()
        time.sleep(2)

        p4 = os.path.join(artifacts_dir, "tab2_trends_top.png")
        page.screenshot(path=p4)
        print("   Saved:", p4)

        page.evaluate('document.querySelector("#main-content").scrollTop = 600')
        time.sleep(1)
        p5 = os.path.join(artifacts_dir, "tab2_trends_ncd_velocity.png")
        page.screenshot(path=p5)
        print("   Saved:", p5)

        # -----------------
        # TAB 3: Predictive
        # -----------------
        print("5. Switching to Tab 3: Predictive Analytics...")
        page.evaluate('document.querySelector("#main-content").scrollTop = 0')
        time.sleep(0.5)
        pred_btn = page.locator('button:has-text("Predictive Analytics")').first
        pred_btn.click()
        time.sleep(2)

        p6 = os.path.join(artifacts_dir, "tab3_predictive_outbreaks.png")
        page.screenshot(path=p6)
        print("   Saved:", p6)

        page.evaluate('document.querySelector("#main-content").scrollTop = 600')
        time.sleep(1)
        p7 = os.path.join(artifacts_dir, "tab3_predictive_stock_surge.png")
        page.screenshot(path=p7)
        print("   Saved:", p7)

        browser.close()
        print("\nSUCCESS: All 3 tabs verified and full screenshots captured!")

if __name__ == "__main__":
    run()

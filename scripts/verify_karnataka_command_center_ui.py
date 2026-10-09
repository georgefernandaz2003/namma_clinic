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

    print("1. Logging into Namma Clinic application...")
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", "e2e_admin_user")
    page.fill("#login-password", "Password123!")
    page.click("button[type='submit']")
    page.wait_for_url(lambda u: "/dashboard" in u or "/admin" in u, timeout=10000)
    print(f"Landed at: {page.url}")

    print("2. Navigating to Healthcare Dashboard (/admin/analytics)...")
    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Verify Simplified Header
    header_text = page.locator("h1").inner_text()
    print(f"Header Verified: {header_text}")
    assert "Healthcare Dashboard" in header_text

    # Verify Health Overview
    assert page.locator("text=WHAT'S CHANGING").is_visible()
    assert page.locator("text=Outpatient visits increased 12%.").is_visible()

    # Verify District Healthcare Overview Title
    assert page.locator("text=District Healthcare Overview").is_visible()

    # Screenshot 1: Overview (State-Wide Karnataka default)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_overview.png"))
    print("Captured: healthcare_dashboard_overview.png")

    # Test Metric Selector Toggle on District Healthcare Overview
    print("Testing District Metric Selector toggle...")
    page.click("button:has-text('Total Beds')")
    time.sleep(1)
    page.click("button:has-text('Active Emergency Cases')")
    time.sleep(1)
    page.click("button:has-text('OPD Visits (Thousands)')")
    time.sleep(1)

    # Scroll down to capture Trend Charts, District Comparison, Predictions, and Alerts
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 550;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_overview_bottom.png"))
    print("Captured: healthcare_dashboard_overview_bottom.png")

    # Scroll further down to capture Predictions and Alerts
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 1100;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_overview_predictions_alerts.png"))
    print("Captured: healthcare_dashboard_overview_predictions_alerts.png")

    # 3. Test Cascading Filter: Select Dakshina Kannada
    print("3. Testing Cascading Filter: Select Dakshina Kannada...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.select_option("#district-filter-select", "dakshina_kannada")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_dakshina.png"))
    print("Captured: healthcare_dashboard_dakshina.png")

    # Select Zone: Mangalore Zone
    print("4. Testing Cascading Filter: Select Mangalore Zone...")
    page.select_option("#zone-filter-select", "mangalore_zone")
    time.sleep(1.5)

    # Select Hospital: Wenlock District Hospital
    print("5. Testing Cascading Filter: Select Wenlock District Hospital...")
    page.select_option("#hospital-filter-select", "wenlock_dh")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_wenlock.png"))
    print("Captured: healthcare_dashboard_wenlock.png")

    # Reset to All Districts for broad state-wide inspection
    print("6. Resetting filter to All Karnataka Districts...")
    page.select_option("#district-filter-select", "all")
    time.sleep(1.5)

    # 7. Test Tab: Trend Analysis
    print("7. Testing Tab: Trend Analysis...")
    page.click("button:has-text('Trend Analysis')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_trends.png"))
    print("Captured: healthcare_dashboard_trends.png")

    # 8. Test Tab: Predictions & Trends
    print("8. Testing Tab: Predictions & Trends...")
    page.click("button:has-text('Predictions & Trends')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_predictions.png"))
    print("Captured: healthcare_dashboard_predictions.png")

    # 9. Test Tab: Alerts & Recommendations
    print("9. Testing Tab: Alerts & Recommendations...")
    page.click("button:has-text('Alerts & Recommendations')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_dashboard_alerts.png"))
    print("Captured: healthcare_dashboard_alerts.png")

    browser.close()
    print("=== All Healthcare Dashboard UI Validations Passed Successfully! ===")

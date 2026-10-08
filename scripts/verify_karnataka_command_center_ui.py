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

    print("2. Navigating to Karnataka Command Center (/admin/analytics)...")
    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Verify Command Center Header
    header_text = page.locator("h1").inner_text()
    print(f"Header Verified: {header_text}")
    assert "KARNATAKA PUBLIC HEALTH COMMAND CENTER" in header_text

    # Screenshot 1: Command Center Overview (State-Wide Karnataka default)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab1_overview.png"))
    print("Captured: karnataka_cc_tab1_overview.png")

    # 3. Test Cascading Filter: Select Dakshina Kannada
    print("3. Testing Cascading Filter: Select Dakshina Kannada...")
    page.select_option("#district-filter-select", "dakshina_kannada")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_district_dakshina.png"))
    print("Captured: karnataka_cc_district_dakshina.png")

    # Select Zone: Mangalore Zone
    print("4. Testing Cascading Filter: Select Mangalore Zone...")
    page.select_option("#zone-filter-select", "mangalore_zone")
    time.sleep(1.5)

    # Select Hospital: Wenlock District Hospital
    print("5. Testing Cascading Filter: Select Wenlock District Hospital...")
    page.select_option("#hospital-filter-select", "wenlock_dh")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_hospital_wenlock.png"))
    print("Captured: karnataka_cc_hospital_wenlock.png")

    # Reset to All Districts for broad state-wide inspection
    print("6. Resetting filter to All Karnataka Districts...")
    page.select_option("#district-filter-select", "all")
    time.sleep(1.5)

    # 7. Test Tab 2: Trend Analysis
    print("7. Testing Tab 2: Trend Analysis...")
    page.click("button:has-text('2. Trend Analysis')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab2_trends.png"))
    print("Captured: karnataka_cc_tab2_trends.png")

    # 8. Test Tab 3: Disease Intelligence
    print("8. Testing Tab 3: Disease Intelligence...")
    page.click("button:has-text('3. Disease Intelligence')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab3_diseases.png"))
    print("Captured: karnataka_cc_tab3_diseases.png")

    # 9. Test Tab 4: Healthcare Operations
    print("9. Testing Tab 4: Healthcare Operations...")
    page.click("button:has-text('4. Healthcare Operations')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab4_operations.png"))
    print("Captured: karnataka_cc_tab4_operations.png")

    # 10. Test Tab 5: Pharmacy & Supply Chain
    print("10. Testing Tab 5: Pharmacy & Supply Chain...")
    page.click("button:has-text('5. Pharmacy & Supply Chain')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab5_pharmacy.png"))
    print("Captured: karnataka_cc_tab5_pharmacy.png")

    # 11. Test Tab 6: Workforce Intelligence
    print("11. Testing Tab 6: Workforce Intelligence...")
    page.click("button:has-text('6. Workforce Intelligence')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab6_workforce.png"))
    print("Captured: karnataka_cc_tab6_workforce.png")

    # 12. Test Tab 7: Predictive Intelligence
    print("12. Testing Tab 7: Predictive Intelligence...")
    page.click("button:has-text('7. Predictive Intelligence')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab7_predictions.png"))
    print("Captured: karnataka_cc_tab7_predictions.png")

    # 13. Test Tab 8: Alerts & Actions
    print("13. Testing Tab 8: Alerts & Actions...")
    page.click("button:has-text('8. Alerts & Actions')")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "karnataka_cc_tab8_alerts.png"))
    print("Captured: karnataka_cc_tab8_alerts.png")

    browser.close()
    print("=== All Karnataka Command Center UI Validations Passed Successfully! ===")

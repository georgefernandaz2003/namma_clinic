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
    page = browser.new_page(viewport={"width": 1440, "height": 950})

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

    # 3. Click Disease Intelligence Tab
    print("3. Switching to Disease Intelligence Tab...")
    page.click("button:has-text('Disease Intelligence')")
    time.sleep(1.5)

    # Verify Header & Subtitle
    assert page.locator("h2:has-text('Disease Intelligence')").is_visible()
    subtitle = page.locator("text=Monitor disease burden, trends, hotspots and short-term forecasts.")
    assert subtitle.is_visible()
    print("Header & Subtitle verified!")

    # Verify 4 Top KPIs
    assert page.locator("text=Total Active Cases").is_visible()
    assert page.locator("text=New Cases").is_visible()
    assert page.locator("text=High-Risk Diseases").is_visible()
    assert page.locator("text=Diseases Increasing").is_visible()
    print("Top 4 KPIs verified!")

    # Verify Main Disease Trend and Selector
    assert page.locator("h3:has-text('Disease Trend')").is_visible()
    page.select_option("#trend-disease-select", "tuberculosis")
    time.sleep(1)
    page.select_option("#trend-disease-select", "dengue")
    time.sleep(1)
    print("Main Disease Trend & Selector verified!")

    # Screenshot 1: Disease Intelligence Top Half (Header, 4 KPIs, Main Disease Trend)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_top.png"))
    print("Captured: disease_intelligence_top.png")

    # Scroll down to capture Current Disease Burden & Geographic Distribution
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 500;")
    time.sleep(1)
    assert page.locator("h3:has-text('Current Disease Burden')").is_visible()
    assert page.locator("h3:has-text('Disease Distribution by District')").is_visible()
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_middle.png"))
    print("Captured: disease_intelligence_middle.png")

    # Scroll down to capture Disease Summary Table
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 1000;")
    time.sleep(1)
    assert page.locator("h3:has-text('Disease Summary Table')").is_visible()
    assert page.locator("th:has-text('Disease')").is_visible()
    assert page.locator("th:has-text('Category')").is_visible()
    assert page.locator("th:has-text('Current')").is_visible()
    assert page.locator("th:has-text('Active')").is_visible()
    assert page.locator("th:has-text('Recovered')").is_visible()
    assert page.locator("th:has-text('7-Day Forecast')").is_visible()
    assert page.locator("th:has-text('Risk')").is_visible()
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_table.png"))
    print("Captured: disease_intelligence_table.png")

    # Test Category Filter Buttons
    print("4. Testing Category Filters: Vector-Borne, Airborne, Non-Communicable...")
    page.click("button:has-text('Vector-Borne')")
    time.sleep(1)
    page.click("button:has-text('All')")
    time.sleep(1)

    # 5. Test Disease Detail Drilldown (Click Dengue Fever)
    print("5. Testing Disease Detail Drilldown for Dengue Fever...")
    page.click("tr:has-text('Dengue Fever')")
    time.sleep(1.5)

    # Verify Detail Modal contents
    assert page.locator("h3:has-text('Dengue Fever')").is_visible()
    assert page.locator("text=Current Cases").is_visible()
    assert page.locator("text=Predictive Trajectory").is_visible()
    assert page.locator("text=Highest Affected Areas:").is_visible()
    assert page.locator("text=Clinical & Surveillance Recommendation").is_visible()
    assert page.locator("text=Increase surveillance and vector-control activities.").is_visible()
    print("Disease Detail Modal verified!")

    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_detail_modal.png"))
    print("Captured: disease_intelligence_detail_modal.png")

    # Close Detail Modal
    page.click("button:has-text('Close Detail View')")
    time.sleep(1)

    # 6. Test Cascading Global Filters on Disease Intelligence
    print("6. Testing Global Filter: Dakshina Kannada...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.select_option("#district-filter-select", "dakshina_kannada")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_dakshina.png"))
    print("Captured: disease_intelligence_dakshina.png")

    # Select Zone: Mangalore Zone
    print("7. Testing Global Filter: Mangalore Zone...")
    page.select_option("#zone-filter-select", "mangalore_zone")
    time.sleep(1.5)

    # Select Hospital: Wenlock District Hospital
    print("8. Testing Global Filter: Wenlock District Hospital...")
    page.select_option("#hospital-filter-select", "wenlock_dh")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "disease_intelligence_wenlock.png"))
    print("Captured: disease_intelligence_wenlock.png")

    # Reset back to All
    page.select_option("#district-filter-select", "all")
    time.sleep(1)

    browser.close()
    print("=== All Disease Intelligence Analytical Dashboard Validations Passed! ===")

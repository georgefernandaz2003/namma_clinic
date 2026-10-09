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

    # 3. Click Healthcare Operations Tab
    print("3. Switching to Healthcare Operations Tab...")
    page.click("button:has-text('Healthcare Operations')")
    time.sleep(1.5)

    # Verify Header & Subtitle
    assert page.locator("h2:has-text('Healthcare Operations')").is_visible()
    subtitle = page.locator("text=Bed capacity, patient workload, emergency demand and referrals")
    assert subtitle.is_visible()
    print("Header & Subtitle verified!")

    # Verify 6 Compact KPIs
    assert page.get_by_text("Total Beds", exact=True).is_visible()
    assert page.get_by_text("Occupancy", exact=True).is_visible()
    assert page.get_by_text("ICU Occupancy", exact=True).is_visible()
    assert page.get_by_text("Waiting Time", exact=True).is_visible()
    assert page.get_by_text("Avg Stay", exact=True).is_visible()
    assert page.get_by_text("Referrals", exact=True).is_visible()
    print("Top 6 KPI Cards verified!")

    # Verify Charts
    assert page.locator("h3:has-text('Patient & Hospital Workload')").is_visible()
    assert page.locator("text=OPD").first.is_visible()
    assert page.locator("text=IPD").first.is_visible()
    assert page.locator("text=Emergency").first.is_visible()

    assert page.locator("h3:has-text('Bed Occupancy Trend')").is_visible()
    assert page.locator("text=90% Capacity Warning").is_visible()
    print("Workload and Bed Occupancy Charts verified!")

    # Screenshot 1: Top section with Header, 6 KPIs, and the two line charts
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_top.png"))
    print("Captured: healthcare_ops_top.png")

    # Scroll down to Hospital Performance
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 450;")
    time.sleep(1)
    assert page.locator("h3:has-text('Hospital Performance')").is_visible()
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_perf.png"))
    print("Captured: healthcare_ops_perf.png")

    # Scroll further down to Referrals & Admissions and Capacity Alerts
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 950;")
    time.sleep(1)

    assert page.locator("h3:has-text('Referrals & Admissions')").is_visible()
    assert page.get_by_text("Referrals Received", exact=True).is_visible()
    assert page.get_by_text("Admissions", exact=True).is_visible()
    assert page.get_by_text("Transfers", exact=True).is_visible()
    assert page.get_by_text("Readmissions", exact=True).is_visible()
    print("Referrals & Admissions verified!")

    assert page.locator("h3:has-text('Capacity Alerts')").is_visible()
    assert page.locator("text=ICU occupancy expected to exceed 95%").is_visible()
    assert page.locator("text=Emergency demand increasing").is_visible()
    assert page.locator("text=Referral volume increasing").is_visible()
    print("Capacity Alerts (🔴, 🟠, 🟡) verified!")

    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_bottom.png"))
    print("Captured: healthcare_ops_bottom.png")

    # Scroll to absolute bottom to see full Referrals & Alerts cards
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 1350;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_alerts_full.png"))
    print("Captured: healthcare_ops_alerts_full.png")

    # 4. Test Cascading Global Filter: Dakshina Kannada
    print("4. Testing Global Filter: Dakshina Kannada...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.select_option("#district-filter-select", "dakshina_kannada")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_dakshina.png"))
    print("Captured: healthcare_ops_dakshina.png")

    # Select Hospital: Wenlock District Hospital
    print("5. Testing Global Filter: Wenlock District Hospital...")
    page.select_option("#zone-filter-select", "mangalore_zone")
    time.sleep(1)
    page.select_option("#hospital-filter-select", "wenlock_dh")
    time.sleep(1.5)

    # Scroll down to verify department breakdown for hospital level
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 450;")
    time.sleep(1)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "healthcare_ops_wenlock.png"))
    print("Captured: healthcare_ops_wenlock.png")

    # Reset back to All
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.select_option("#district-filter-select", "all")
    time.sleep(1)

    browser.close()
    print("=== All Healthcare Operations Validations Passed Successfully! ===")

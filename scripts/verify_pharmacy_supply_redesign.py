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

    # 3. Click Pharmacy & Supply Chain Tab
    print("3. Switching to Pharmacy & Supply Chain Tab...")
    page.click("button:has-text('Pharmacy & Supply Chain')")
    time.sleep(1.5)

    # Verify Header & Subtitle
    assert page.locator("h2:has-text('Pharmacy & Supply Chain')").is_visible()
    subtitle = page.locator("text=Stock, consumption, expiry, procurement and stock-out prediction")
    assert subtitle.is_visible()
    print("Header & Subtitle verified!")

    # Verify 5 Compact KPIs
    assert page.get_by_text("Total Medicines", exact=True).is_visible()
    assert page.get_by_text("Low Stock", exact=True).is_visible()
    assert page.get_by_text("Critical Stock", exact=True).is_visible()
    assert page.get_by_text("Expiring <30 Days", exact=True).is_visible()
    assert page.get_by_text("Stock Value", exact=True).is_visible()
    print("Top 5 KPI Cards verified!")

    # Verify Consumption Line Chart & Top Medicines Bar Chart
    assert page.locator("h3:has-text('Medicine Consumption')").is_visible()
    assert page.locator("text=Current Year").first.is_visible()
    assert page.locator("text=Previous Year").first.is_visible()
    assert page.locator("h3:has-text('Top Medicines by Consumption')").is_visible()
    print("Medicine Consumption & Top Medicines charts verified!")

    # Screenshot 1: Top section with Header, 5 KPIs, and the two charts
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "pharmacy_supply_top.png"))
    print("Captured: pharmacy_supply_top.png")

    # Scroll down to Stock & Stock-Out Risk table
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 500;")
    time.sleep(1)

    assert page.locator("h3:has-text('Stock & Stock-Out Risk')").is_visible()
    # Check table column headers
    assert page.get_by_role("columnheader", name="Medicine", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Stock", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Daily Use", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Days Left", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Stock-out", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Reorder", exact=True).is_visible()
    print("Stock & Stock-Out Risk Table and Columns verified!")

    page.screenshot(path=os.path.join(ARTIFACT_DIR, "pharmacy_supply_middle.png"))
    print("Captured: pharmacy_supply_middle.png")

    # Scroll further down to Orders & Supply, Expiry, and Predictions
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 1000;")
    time.sleep(1)

    # Orders & Supply
    assert page.locator("h3:has-text('Orders & Supply')").is_visible()
    assert page.get_by_role("columnheader", name="Last Order", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Supplier", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Qty", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Delivery", exact=True).is_visible()
    assert page.get_by_role("columnheader", name="Status", exact=True).is_visible()
    print("Orders & Supply Table verified!")

    # Expiry
    expiry_card = page.locator("div.bg-white", has=page.locator("h3:has-text('Expiry')"))
    assert expiry_card.is_visible()
    assert expiry_card.get_by_text("7 Days", exact=True).is_visible()
    assert expiry_card.get_by_text("30 Days", exact=True).is_visible()
    assert expiry_card.get_by_text("60 Days", exact=True).is_visible()
    assert expiry_card.get_by_text("90 Days", exact=True).is_visible()
    print("Expiry 4 timeline buckets verified!")

    # Predictions
    pred_card = page.locator("div.bg-white", has=page.locator("h3:has-text('Predictions')"))
    assert pred_card.is_visible()
    assert pred_card.locator("text=Expected stock-out").first.is_visible()
    assert pred_card.locator("text=Recommended reorder").first.is_visible()
    print("Stock-out & Reorder Predictions verified!")

    page.screenshot(path=os.path.join(ARTIFACT_DIR, "pharmacy_supply_bottom.png"))
    print("Captured: pharmacy_supply_bottom.png")

    # 4. Test Cascading Global Filter: Dakshina Kannada
    print("4. Testing Global Filter: Dakshina Kannada...")
    page.evaluate("const el = document.getElementById('main-content'); if (el) el.scrollTop = 0;")
    page.select_option("#district-filter-select", "dakshina_kannada")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "pharmacy_supply_dakshina.png"))
    print("Captured: pharmacy_supply_dakshina.png")

    # Reset back to All
    page.select_option("#district-filter-select", "all")
    time.sleep(1)

    browser.close()
    print("=== All Pharmacy & Supply Chain Validations Passed Successfully! ===")

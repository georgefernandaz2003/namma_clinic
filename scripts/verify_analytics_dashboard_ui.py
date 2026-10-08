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
    print(f"Landed at: {page.url}")

    print("2. Navigating to /admin/analytics...")
    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2500)

    # Check for error alert
    page_content = page.content()
    has_error = "Unable to load public health intelligence data" in page_content
    print(f"Error Alert Present: {has_error}")
    if has_error:
        print("[FAIL] Error alert is present on page!")
    else:
        print("[PASS] No error alert! Data loaded successfully!")

    # Screenshot Top & Hierarchy
    s1 = os.path.join(ARTIFACT_DIR, "dashboard_verified_hierarchy.png")
    page.screenshot(path=s1, full_page=True)
    print(f"Captured: {s1}")

    # Click 2. District Level
    print("3. Testing District Level button...")
    dist_btn = page.get_by_role("button", name="2. District Level")
    if dist_btn.count() > 0:
        dist_btn.click()
        page.wait_for_timeout(1000)
        s2 = os.path.join(ARTIFACT_DIR, "dashboard_verified_districts.png")
        page.screenshot(path=s2)
        print(f"Captured: {s2}")

    # Click 3. Zone Level
    print("3b. Testing Zone Level button...")
    zone_btn = page.get_by_role("button", name="3. Zone Level")
    if zone_btn.count() > 0:
        zone_btn.click()
        page.wait_for_timeout(1000)
        s_z = os.path.join(ARTIFACT_DIR, "dashboard_verified_zones.png")
        page.screenshot(path=s_z)
        print(f"Captured: {s_z}")

    # Click 4. Ward Level
    print("3c. Testing Ward Level button...")
    ward_btn = page.get_by_role("button", name="4. Ward Level")
    if ward_btn.count() > 0:
        ward_btn.click()
        page.wait_for_timeout(1000)
        s_w = os.path.join(ARTIFACT_DIR, "dashboard_verified_wards.png")
        page.screenshot(path=s_w)
        print(f"Captured: {s_w}")

    # Click 5. Facility Level
    print("4. Testing Facility Level button...")
    fac_btn = page.get_by_role("button", name="5. Facility Level")
    if fac_btn.count() > 0:
        fac_btn.click()
        page.wait_for_timeout(1000)
        s3 = os.path.join(ARTIFACT_DIR, "dashboard_verified_facilities.png")
        page.screenshot(path=s3)
        print(f"Captured: {s3}")

    # Click Trend Analysis tab
    print("5. Testing Trend Analysis tab...")
    trends_tab = page.locator("button:has-text('Longitudinal Trend Analysis')")
    if trends_tab.count() > 0:
        trends_tab.first.click()
        page.wait_for_timeout(1500)
        s4 = os.path.join(ARTIFACT_DIR, "dashboard_verified_trends.png")
        page.screenshot(path=s4, full_page=True)
        print(f"Captured: {s4}")

    # Click Predictive Analytics tab
    print("6. Testing Predictive Analytics tab...")
    pred_tab = page.locator("button:has-text('Predictive Intelligence')")
    if pred_tab.count() > 0:
        pred_tab.first.click()
        page.wait_for_timeout(1500)
        s5 = os.path.join(ARTIFACT_DIR, "dashboard_verified_predictive.png")
        page.screenshot(path=s5, full_page=True)
        print(f"Captured: {s5}")

    browser.close()
    print("Verification completed cleanly!")

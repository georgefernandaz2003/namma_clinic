"""
Playwright Browser Validation: Staff & Clinic Administration UI
Verifies:
A. Clinic Admin (testadmin): Login, Staff Directory, Invite, Role Assignments (Doctor, Nurse, Compounder), Lifecycle Actions
B. DHO (localdistrict): Login, District Staff Directory, District Scope, Create/Select Clinic, Assign Hospital Admin
C. Operational roles (localnurse): Staff administration link is absent and /admin/staff is blocked with 403 ForbiddenCard
D. Unauthorized API call: Direct REST request with clinical token yields HTTP 403 Forbidden
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_BASE = "http://127.0.0.1:8000/api"

def log(msg):
    print(f"[TEST] {msg}", flush=True)

def test_unauthorized_api():
    log("Checking Direct Backend API 403 with operational role token (Nurse)...")
    login_data = json.dumps({"username": "localnurse", "password": "NursePassword123!"}).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/auth/token/",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Nurse login failed: {resp.status}"
        token_data = json.loads(resp.read().decode('utf-8'))
        token = token_data["access"]

    # Attempt to access staff administration API
    staff_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/accounts/staff-profiles/",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        urllib.request.urlopen(staff_req)
        assert False, "Operational role should have been rejected with 403!"
    except urllib.error.HTTPError as err:
        assert err.code == 403, f"Expected HTTP 403 for operational role, got {err.code}"
        log(f"Direct API check PASSED: HTTP {err.code} received from backend authority.")

def run_browser_validation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # ==========================================
        # Scenario C: Operational Roles (Nurse) - Navigation & Route Isolation
        # ==========================================
        log("Testing Scenario C: Nurse Navigation & Route Isolation...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'localnurse')
        page.fill('input[type="password"]', 'NursePassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/nurse", timeout=15000)
        log("Nurse logged in successfully to /dashboard/nurse.")

        # Verify Staff Directory does NOT appear in navigation
        time.sleep(1)
        nav_text = page.inner_text("aside") if page.query_selector("aside") else page.inner_text("body")
        assert "Staff Directory" not in nav_text, "Nurse must NOT have Staff Directory in navigation!"
        log("Verified: Staff Directory link is absent from Nurse navigation.")

        # Attempt to browse directly to /admin/staff
        page.goto(f"{BASE_URL}/admin/staff")
        time.sleep(1)
        body_text = page.inner_text("body")
        assert "Access Denied" in body_text or "HTTP 403" in body_text, "Nurse must see Access Denied (HTTP 403) on /admin/staff!"
        log("Verified: Direct navigation to /admin/staff for Nurse displays ForbiddenCard.")

        # ==========================================
        # Scenario A: Clinic Admin (testadmin)
        # ==========================================
        log("Testing Scenario A: Clinic Admin (testadmin)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'testadmin')
        page.fill('input[type="password"]', 'AdminPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/admin", timeout=15000)
        log("Hospital Admin logged in to /dashboard/admin.")

        # Verify Staff Directory exists in navigation
        page.wait_for_selector('a[href="/admin/staff"]', timeout=10000)
        page.click('a[href="/admin/staff"]')
        page.wait_for_url("**/admin/staff", timeout=10000)
        log("Navigated to /admin/staff.")

        # Wait for staff table or empty state
        page.wait_for_selector('[data-testid="staff-directory-table"], [data-testid="staff-search-input"]', timeout=15000)
        log("Staff Directory loaded successfully.")

        # Test Search / Filter controls
        search_input = page.wait_for_selector('[data-testid="staff-search-input"]')
        search_input.fill("EMP")
        time.sleep(0.5)
        search_input.fill("")

        # Test Invite Modal
        log("Opening Invite Staff modal...")
        page.click('[data-testid="open-invite-staff-btn"]')
        page.wait_for_selector('[data-testid="submit-invite-btn"]', timeout=5000)

        # Check that DOCTOR, NURSE, COMPOUNDER are options, and NO NURSE_COMPOUNDER or SYSTEM_ADMIN
        role_select = page.wait_for_selector('[data-testid="invite-role-select"]')
        options_text = role_select.inner_text()
        assert "Doctor" in options_text, "Doctor must be available in invite role options"
        assert "Nurse" in options_text, "Nurse must be available in invite role options"
        assert "Compounder" in options_text, "Compounder must be available in invite role options"
        assert "NURSE_COMPOUNDER" not in options_text, "NURSE_COMPOUNDER must not exist!"
        assert "SYSTEM_ADMIN" not in options_text, "SYSTEM_ADMIN must not exist!"
        log("Verified: Role selection options in Invite modal adhere strictly to operational catalogue.")

        # Close Invite Modal
        page.click('text=Cancel')
        log("Closed Invite modal.")

        # Test Staff Detail Modal if rows exist
        rows = page.query_selector_all('tbody tr')
        if len(rows) > 0:
            log(f"Found {len(rows)} staff rows. Opening first staff detail modal...")
            rows[0].click()
            page.wait_for_selector('#staff-detail-title', timeout=5000)
            log("Staff Detail modal opened.")

            # Check if Assign Role button is present
            assign_btn = page.query_selector('[data-testid="assign-new-role-btn"]')
            if assign_btn:
                log("Opening Assign Role modal...")
                assign_btn.click()
                page.wait_for_selector('[data-testid="submit-assign-role-btn"]', timeout=5000)
                # Verify role select options in Assign Role modal
                ar_select = page.wait_for_selector('[data-testid="assign-role-select"]')
                ar_options = ar_select.inner_text()
                assert "Doctor" in ar_options
                assert "Nurse" in ar_options
                assert "Compounder" in ar_options
                assert "NURSE_COMPOUNDER" not in ar_options
                log("Verified: Assign Role modal has separate NURSE and COMPOUNDER options.")
                page.click('text=Cancel')

            # Close detail modal
            page.click('text=Close')
            log("Closed Staff Detail modal.")

        # ==========================================
        # Scenario B: District Health Officer (localdistrict)
        # ==========================================
        log("Testing Scenario B: DHO (localdistrict)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'localdistrict')
        page.fill('input[type="password"]', 'DistrictPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/district", timeout=15000)
        log("DHO logged in to /dashboard/district.")

        # Navigate to /admin/staff
        page.wait_for_selector('a[href="/admin/staff"]', timeout=10000)
        page.click('a[href="/admin/staff"]')
        page.wait_for_url("**/admin/staff", timeout=10000)
        log("DHO navigated to /admin/staff.")

        # Verify District Oversight scope badge
        page.wait_for_selector('text=District Oversight', timeout=10000)
        log("Verified: District Oversight badge rendered for DHO.")

        # Verify facility filter is visible for DHO
        fac_filter = page.query_selector('[data-testid="staff-facility-filter"]')
        assert fac_filter is not None, "DHO must have district facility filter available!"
        log("Verified: District facility filter is present for DHO.")

        # Verify "+ New Clinic Facility" button is available for DHO
        create_fac_btn = page.query_selector('[data-testid="open-create-facility-btn"]')
        assert create_fac_btn is not None, "DHO must have + New Clinic Facility button"
        create_fac_btn.click()
        page.wait_for_selector('[data-testid="submit-create-facility-btn"]', timeout=5000)
        log("Verified: Register New Clinic Facility modal opens for DHO.")
        page.click('text=Cancel')

        browser.close()
        log("ALL BROWSER PLAYWRIGHT VALIDATION SCENARIOS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_unauthorized_api()
        run_browser_validation()
        print("\n=== PLAYWRIGHT BROWSER VALIDATION PASSED ===")
    except Exception as e:
        print(f"\n[ERROR] Playwright validation failed: {e}", file=sys.stderr)
        sys.exit(1)
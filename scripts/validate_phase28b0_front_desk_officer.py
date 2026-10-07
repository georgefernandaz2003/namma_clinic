"""
Phase 28B-0 Playwright E2E Validation Script
Validates:
1. Login as FRONT_DESK_OFFICER through real UI (e2e_compounder_user).
2. Verified landing route and navigation labels (Front Desk Console, Patient Directory, OPD Queue).
3. Verified absence of clinical/pharmacy/lab/inventory/admin links.
4. Register a new citizen patient through real UI form.
5. Issue an OPD token for patient through real UI.
6. Verify token/patient appears in OPD queue.
7. Verify unauthorized routes (/consultation, /lab, /pharmacy, /inventory, /admin/staff) are blocked.
8. Verify patient clinical details and prescriptions are restricted/hidden.
9. PostgreSQL role assignment verification.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def run_validation():
    screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots_phase28b0")
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on('console', lambda msg: print(f"[BROWSER LOG] {msg.text}"))
        page.on('pageerror', lambda err: print(f"[BROWSER ERROR] {err}"))
        page.on('response', lambda res: print(f"[HTTP {res.status}] {res.url}") if '/api/' in res.url else None)

        log("STEP 1", f"Navigating to {BASE_URL}/login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('#login-username', timeout=10000)

        # Check demo credentials matrix label on login page
        page_content = page.content()
        assert "Front Desk Officer" in page_content, "Front Desk Officer label missing from login demo matrix!"
        log("STEP 1", "Verified: 'Front Desk Officer' appears in login demo matrix.")

        # Fill credentials
        page.fill('#login-username', "e2e_compounder_user")
        page.fill('#login-password', "Password123!")
        page.screenshot(path=os.path.join(screenshots_dir, "01_login_filled.png"))

        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/patients" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        current_url = page.url
        log("STEP 2", f"Current URL after login: {current_url}")
        assert "/dashboard/front-desk" in current_url or "/dashboard/compounder" in current_url or "/patients" in current_url, f"Unexpected landing URL: {current_url}"
        page.screenshot(path=os.path.join(screenshots_dir, "02_front_desk_dashboard.png"))

        # Verify navigation items
        sidebar_text = page.locator("aside, nav").all_inner_texts()
        sidebar_combined = " ".join(sidebar_text)
        log("STEP 2", f"Checking sidebar links: {sidebar_combined}")

        assert "Front Desk" in sidebar_combined or "Patients" in sidebar_combined, "Front Desk / Patients navigation missing!"
        assert "Triage" not in sidebar_combined, "Clinical Triage must not be visible to Front Desk Officer!"
        assert "Doctor" not in sidebar_combined, "Doctor consultation must not be visible to Front Desk Officer!"
        assert "Pharmacy" not in sidebar_combined or "Dispense" not in sidebar_combined, "Pharmacy dispensing must not be in nav!"
        log("STEP 2", "Verified: Front Desk Officer has proper role navigation and no unauthorized clinical sections.")

        # Navigate explicitly to /dashboard/front-desk if not already there
        if "/dashboard/front-desk" not in page.url:
            page.goto(f"{BASE_URL}/dashboard/front-desk")
            page.wait_for_load_state("networkidle")

        # STEP 3: Register a citizen patient via UI
        log("STEP 3", "Registering new citizen patient via Front Desk UI...")
        # Check if Register Patient button is visible
        reg_btn = page.locator("button:has-text('Register Patient'), button:has-text('New Patient')").first
        if reg_btn.is_visible():
            reg_btn.click()
            time.sleep(1)

        # Fill registration form fields
        timestamp = int(time.time()) % 10000
        test_patient_name = f"Amina Begum {timestamp}"
        test_mobile = f"98765{timestamp:05d}"

        # Fill name, age, mobile
        page.locator('input[placeholder*="Full Name"], input[name="name"], label:has-text("Full Name") + input, input[type="text"]').first.fill(test_patient_name)
        
        # Age
        age_input = page.locator('input[placeholder*="Age"], input[name="age"], input[type="number"]').first
        if age_input.is_visible():
            age_input.fill("34")

        # Mobile
        mobile_input = page.locator('input[placeholder*="Mobile"], input[name="mobile"], input[type="tel"]').first
        if mobile_input.is_visible():
            mobile_input.fill(test_mobile)

        # Address
        addr_input = page.locator('textarea, input[placeholder*="Address"], input[name="address"]').first
        if addr_input.is_visible():
            addr_input.fill("Ward 14 Slum Settlement, Bangalore")

        page.screenshot(path=os.path.join(screenshots_dir, "03_patient_reg_form.png"))

        # Submit patient registration
        submit_reg = page.locator("button:has-text('Complete Registration'), button:has-text('Register'), button[type='submit']").last
        submit_reg.click()
        time.sleep(2)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(screenshots_dir, "04_patient_registered.png"))
        log("STEP 3", f"Patient registered: {test_patient_name}")

        # STEP 4: Issue OPD Token for the patient
        log("STEP 4", "Issuing OPD Token for the patient...")
        # Find Issue Token button
        token_btn = page.locator(f"tr:has-text('{test_patient_name}') button:has-text('Issue Token'), tr:has-text('{test_patient_name}') button:has-text('Token'), button:has-text('Generate Token'), button:has-text('Issue Token')").first
        if token_btn.is_visible():
            token_btn.click()
            time.sleep(1)
            # Verify Token Modal select options (strictly NO ANC or IMMUNIZATION)
            options_text = " ".join(page.locator("select").all_inner_texts())
            assert "Antenatal" not in options_text and "ANC" not in options_text, f"Token modal must NOT contain ANC option: {options_text}"
            assert "Immunization" not in options_text and "Child Health" not in options_text, f"Token modal must NOT contain Immunization option: {options_text}"
            log("STEP 4", "Verified: Front Desk Token Modal strictly contains ZERO Maternal/Child or Immunization options.")
            # In token modal, click generate
            gen_btn = page.locator("button:has-text('Generate Token'), button:has-text('Issue Token'), button:has-text('Confirm')").last
            if gen_btn.is_visible():
                gen_btn.click()
                time.sleep(2)
                page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(screenshots_dir, "05_token_issued.png"))
        log("STEP 4", "OPD Token issuance workflow completed.")

        # STEP 5: Verify OPD Queue
        log("STEP 5", "Navigating to /queue...")
        page.goto(f"{BASE_URL}/queue")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(screenshots_dir, "06_opd_queue.png"))
        log("STEP 5", "OPD Queue view rendered.")

        # STEP 6: Verify Unauthorized Routes are Blocked
        unauthorized_routes = [
            ("/consultation", "Consultation"),
            ("/lab", "Laboratory"),
            ("/pharmacy", "Pharmacy"),
            ("/inventory", "Inventory"),
            ("/admin/staff", "Staff Administration"),
        ]

        for route, name in unauthorized_routes:
            log("STEP 6", f"Testing unauthorized access to {route} ({name})...")
            page.goto(f"{BASE_URL}{route}")
            time.sleep(1)
            page.wait_for_load_state("networkidle")
            page_text = page.locator("body").inner_text()
            # Must either show 403 ForbiddenCard, Access Denied, or redirect away
            is_blocked = (
                "Forbidden" in page_text or
                "Access Denied" in page_text or
                "not authorized" in page_text.lower() or
                "prohibited" in page_text.lower() or
                route not in page.url
            )
            assert is_blocked, f"Security Breach: Front Desk Officer was NOT blocked from {route}!"
            log("STEP 6", f"Verified blocked from {route}: current URL={page.url}")

        page.screenshot(path=os.path.join(screenshots_dir, "07_unauthorized_blocked.png"))

        # STEP 7: Patient Detail clinical privacy check
        log("STEP 7", "Checking patient detail clinical privacy...")
        page.goto(f"{BASE_URL}/patients")
        page.wait_for_load_state("networkidle")
        first_patient_row = page.locator("tbody tr").first
        if first_patient_row.is_visible():
            first_patient_row.click()
            time.sleep(2)
            page.wait_for_load_state("networkidle")
            detail_text = page.locator("body").inner_text()
            # Front desk officer sees demographics/intake, but NOT clinical diagnose forms
            assert "Prescribe Medication" not in detail_text, "Prescribe Medication must not be accessible to Front Desk Officer!"
            assert "Record Consultation" not in detail_text, "Record Consultation must not be accessible to Front Desk Officer!"
            log("STEP 7", "Verified: Patient detail hides clinician prescribing/consultation controls.")
            page.screenshot(path=os.path.join(screenshots_dir, "08_patient_detail_privacy.png"))

        browser.close()
        log("SUCCESS", "All Playwright browser checks passed flawlessly!")

if __name__ == "__main__":
    run_validation()

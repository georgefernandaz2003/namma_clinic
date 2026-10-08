import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def run_validation():
    screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots_phase40_registration")
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on('console', lambda msg: print(f"[BROWSER LOG] {msg.text}"))
        page.on('pageerror', lambda err: print(f"[BROWSER ERROR] {err}"))
        page.on('response', lambda res: print(f"[HTTP {res.status}] {res.url}") if '/api/' in res.url else None)

        # 1. Login
        log("STEP 1", f"Navigating to {BASE_URL}/login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('#login-username', timeout=10000)

        page.fill('#login-username', "e2e_compounder_user")
        page.fill('#login-password', "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/patients" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("STEP 1", "Logged in successfully as Front Desk Officer.")

        # 2. Go to /patients
        log("STEP 2", f"Navigating to {BASE_URL}/patients...")
        page.goto(f"{BASE_URL}/patients")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('text=Patient Master Directory', timeout=10000)
        page.screenshot(path=os.path.join(screenshots_dir, "01_patients_registry.png"))

        # 3. Open Register New Patient Modal
        log("STEP 3", "Clicking 'Register New Patient' button...")
        reg_btn = page.locator('button:has-text("Register New Patient")').first
        reg_btn.click()
        page.wait_for_selector('h2:has-text("Register New Patient")', timeout=5000)
        log("STEP 3", "Registration modal opened.")

        # 4. Fill form
        ts = int(time.time())
        patient_name = f"Kavitha R {ts % 10000}"
        patient_mobile = f"99887{str(ts % 100000).zfill(5)}"
        log("STEP 4", f"Filling patient registration form for {patient_name} ({patient_mobile})...")

        page.fill('input[placeholder="e.g. Rajesh Gowda"]', patient_name)
        page.fill('input[placeholder="e.g. 35"]', "28")
        page.select_option('select:has-text("Male")', "FEMALE")
        page.fill('input[placeholder="10-digit mobile"]', patient_mobile)
        page.fill('input[placeholder="14-digit ABHA (optional)"]', "14-9988-7766-5544")
        page.fill('textarea[placeholder="Street / Slum Ward / Village address"]', "12 4th Cross Malleshwaram")
        page.screenshot(path=os.path.join(screenshots_dir, "02_registration_form_filled.png"))

        # 5. Submit form
        log("STEP 5", "Submitting form via 'Register & Verify Duplicate Status'...")
        submit_btn = page.locator('button:has-text("Register & Verify Duplicate Status")')
        assert submit_btn.is_visible(), "Submit button 'Register & Verify Duplicate Status' must be visible!"
        submit_btn.click()

        # 6. Verify confirmation modal
        log("STEP 6", "Waiting for confirmation modal to appear...")
        page.wait_for_selector('[data-testid="patient-registration-success-modal"]', timeout=10000)
        page.wait_for_selector('text=Patient Registered Successfully', timeout=5000)

        # Ensure registration form modal is no longer active
        assert not page.locator('text=Patient Full Name *').is_visible(), "Registration form modal must be closed!"

        # Extract details
        disp_name = page.locator('[data-testid="registered-patient-name"]').inner_text().strip()
        disp_id = page.locator('[data-testid="registered-patient-id"]').inner_text().strip()
        disp_mobile = page.locator('[data-testid="registered-patient-mobile"]').inner_text().strip()
        disp_status = page.locator('[data-testid="registered-patient-status"]').inner_text().strip()

        log("STEP 6", f"Confirmed modal details: Name='{disp_name}', ID='{disp_id}', Mobile='{disp_mobile}', Status='{disp_status}'")
        assert disp_name == patient_name, f"Expected name {patient_name}, got {disp_name}"
        assert disp_id and len(disp_id) > 0, "Patient ID must not be empty"
        assert disp_mobile == patient_mobile, f"Expected mobile {patient_mobile}, got {disp_mobile}"
        assert "Registered" in disp_status, "Status must show Registered"

        # Check action buttons
        close_btn = page.locator('[data-testid="close-confirmation-button"]')
        view_btn = page.locator('[data-testid="view-patient-button"]')
        assert close_btn.is_visible(), "Close button must be visible"
        assert view_btn.is_visible(), "View Patient button must be visible"

        page.screenshot(path=os.path.join(screenshots_dir, "03_confirmation_popup.png"))
        log("STEP 6", "Confirmation popup verified successfully.")

        # 7. Test 'View Patient' navigation
        log("STEP 7", "Clicking 'View Patient' on confirmation modal...")
        view_btn.click()
        page.wait_for_url(lambda u: "/patients/" in u and not u.endswith("/patients"), timeout=10000)
        log("STEP 7", f"Navigated successfully to Patient Detail URL: {page.url}")
        page.wait_for_selector(f'h1:has-text("{patient_name}")', timeout=10000)
        page.screenshot(path=os.path.join(screenshots_dir, "04_patient_detail_page.png"))

        # Navigate back to /patients
        page.goto(f"{BASE_URL}/patients")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('text=Patient Master Directory', timeout=10000)

        # 8. Register second patient to test 'Close' button & patient list refresh
        log("STEP 8", "Registering second patient to verify 'Close' button and list revalidation...")
        reg_btn = page.locator('button:has-text("Register New Patient")').first
        reg_btn.click()
        page.wait_for_selector('h2:has-text("Register New Patient")', timeout=5000)

        ts2 = int(time.time()) + 1
        patient2_name = f"Rajesh Patel {ts2 % 10000}"
        patient2_mobile = f"99777{str(ts2 % 100000).zfill(5)}"
        page.fill('input[placeholder="e.g. Rajesh Gowda"]', patient2_name)
        page.fill('input[placeholder="e.g. 35"]', "45")
        page.select_option('select:has-text("Male")', "MALE")
        page.fill('input[placeholder="10-digit mobile"]', patient2_mobile)
        page.fill('textarea[placeholder="Street / Slum Ward / Village address"]', "45 Gandhi Road")

        submit_btn = page.locator('button:has-text("Register & Verify Duplicate Status")')
        submit_btn.click()

        page.wait_for_selector('[data-testid="patient-registration-success-modal"]', timeout=10000)
        log("STEP 8", f"Second confirmation modal appeared for {patient2_name}.")

        close_btn = page.locator('[data-testid="close-confirmation-button"]')
        close_btn.click()
        page.wait_for_timeout(1000)

        assert not page.locator('[data-testid="patient-registration-success-modal"]').is_visible(), "Confirmation modal must close!"
        page.wait_for_selector(f'text={patient2_name}', timeout=10000)
        log("STEP 8", f"Verified {patient2_name} appears in Patient Directory table after Close.")
        page.screenshot(path=os.path.join(screenshots_dir, "05_second_patient_in_table.png"))

        # 9. Test duplicate detection flow
        log("STEP 9", "Testing duplicate registration flow with same demographics...")
        reg_btn.click()
        page.wait_for_selector('h2:has-text("Register New Patient")', timeout=5000)

        page.fill('input[placeholder="e.g. Rajesh Gowda"]', patient2_name)
        page.fill('input[placeholder="e.g. 35"]', "45")
        page.select_option('select:has-text("Male")', "MALE")
        page.fill('input[placeholder="10-digit mobile"]', patient2_mobile)

        submit_btn = page.locator('button:has-text("Register & Verify Duplicate Status")')
        submit_btn.click()

        # Wait for duplicate conflict error
        page.wait_for_selector('text=already registered', timeout=10000)
        log("STEP 9", "Verified duplicate conflict error banner is displayed.")

        # Ensure confirmation popup did NOT appear
        assert not page.locator('[data-testid="patient-registration-success-modal"]').is_visible(), "Confirmation modal must NOT appear on duplicate error!"

        # Ensure registration form remains open with inputs
        assert page.locator('h2:has-text("Register New Patient")').is_visible(), "Registration form modal must remain open on error!"

        page.screenshot(path=os.path.join(screenshots_dir, "06_duplicate_conflict_error.png"))

        # Close registration modal via Cancel
        page.locator('button:has-text("Cancel")').first.click()
        log("STEP 9", "Cancelled duplicate registration modal.")

        browser.close()
        log("SUCCESS", "ALL BROWSER VALIDATION CHECKS (VIEW PATIENT, CLOSE, DUPLICATE DETECTION) PASSED PERFECTLY!")

if __name__ == "__main__":
    run_validation()

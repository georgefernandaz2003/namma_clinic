import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def verify_database(patient_name, patient_mobile):
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    sys.path.insert(0, os.path.abspath('backend'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from apps.patients.models import Patient
    from apps.visits.models import Visit, Token

    patient = Patient.objects.filter(name=patient_name, mobile=patient_mobile).first()
    assert patient is not None, f"Database verification failed: Patient {patient_name} not found in DB!"
    log("DB_VERIFY", f"Found Patient in DB: id={patient.id}, patient_id={patient.patient_id}, name={patient.name}")

    visit = Visit.objects.filter(patient=patient).order_by('-id').first()
    assert visit is not None, f"Database verification failed: No Visit found for patient {patient_name}!"
    log("DB_VERIFY", f"Found Visit in DB: id={visit.id}, visit_id={visit.visit_id}, status={visit.status}, queue={visit.current_queue}")

    token = Token.objects.filter(visit=visit).first()
    assert token is not None, f"Database verification failed: No Token found for visit {visit.visit_id}!"
    facility_str = getattr(token.facility, 'facility_name', str(token.facility))
    log("DB_VERIFY", f"Found Token in DB: token_number={token.token_number}, status={token.status}, facility={facility_str}")

    return patient, visit, token

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

        # 6. Verify confirmation modal & token prompt
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

        # Verify OPD Token confirmation prompt is present
        assert page.locator('[data-testid="token-confirmation-prompt"]').is_visible(), "OPD token confirmation section must be visible!"
        prompt_text = page.locator('[data-testid="token-confirmation-prompt"]').inner_text()
        log("STEP 6", f"Confirmation prompt text: {prompt_text}")
        assert "Issue OPD Queue Token" in prompt_text, "Prompt title 'Issue OPD Queue Token' must be present!"
        assert "automatically create an OPD queue token" in prompt_text, "Prompt body must explain OPD token creation!"

        # Verify confirmation button is visible
        confirm_token_btn = page.locator('[data-testid="confirm-issue-token-button"]')
        assert confirm_token_btn.is_visible(), "Confirmation button 'Confirm & Create OPD Token' must be visible!"
        assert "Confirm & Create OPD Token" in confirm_token_btn.inner_text()

        page.screenshot(path=os.path.join(screenshots_dir, "03_confirmation_popup_with_token_prompt.png"))
        log("STEP 6", "Confirmation popup with token prompt verified successfully.")

        # 7. Click confirmation button to automatically create OPD token
        log("STEP 7", "Clicking 'Confirm & Create OPD Token' button...")
        confirm_token_btn.click()

        # Wait for token issuance success card
        page.wait_for_selector('[data-testid="token-issued-success"]', timeout=10000)
        token_success_card = page.locator('[data-testid="token-issued-success"]').inner_text()
        log("STEP 7", f"Token issued success card text:\n{token_success_card}")
        assert "OPD Queue Token Created Successfully!" in token_success_card

        token_num_text = page.locator('[data-testid="issued-token-number"]').inner_text().strip()
        log("STEP 7", f"Issued token number displayed: {token_num_text}")
        assert "Token #" in token_num_text

        # Verify 'View in OPD Queue' button is now visible
        view_queue_btn = page.locator('[data-testid="go-to-queue-button"]')
        assert view_queue_btn.is_visible(), "'View in OPD Queue' button must be visible after token creation!"

        page.screenshot(path=os.path.join(screenshots_dir, "04_opd_token_created_modal.png"))

        # 8. Navigate to OPD Queue via the button
        log("STEP 8", "Clicking 'View in OPD Queue' button...")
        view_queue_btn.click()
        page.wait_for_url(lambda u: "/queue" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("STEP 8", f"Navigated to queue page: {page.url}")
        page.screenshot(path=os.path.join(screenshots_dir, "05_queue_page_with_new_token.png"))

        # 9. Database Verification
        log("STEP 9", "Performing authoritative PostgreSQL database verification...")
        db_patient, db_visit, db_token = verify_database(patient_name, patient_mobile)
        assert str(db_token.token_number) in token_num_text, f"UI token {token_num_text} must match DB token #{db_token.token_number}"
        log("STEP 9", f"Database verification successful: Visit {db_visit.visit_id}, Token #{db_token.token_number}")

        # 10. Register second patient to verify Close button
        log("STEP 10", "Navigating back to /patients to verify Close workflow...")
        page.goto(f"{BASE_URL}/patients")
        page.wait_for_load_state("networkidle")

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
        log("STEP 10", f"Second confirmation modal appeared for {patient2_name}.")

        close_btn = page.locator('[data-testid="close-confirmation-button"]')
        close_btn.click()
        page.wait_for_timeout(1000)

        assert not page.locator('[data-testid="patient-registration-success-modal"]').is_visible(), "Confirmation modal must close!"
        page.wait_for_selector(f'text={patient2_name}', timeout=10000)
        log("STEP 10", f"Verified {patient2_name} appears in Patient Directory table after Close.")

        # 11. Test duplicate detection flow
        log("STEP 11", "Testing duplicate registration flow with same demographics...")
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
        log("STEP 11", "Verified duplicate conflict error banner is displayed.")

        # Ensure confirmation popup did NOT appear
        assert not page.locator('[data-testid="patient-registration-success-modal"]').is_visible(), "Confirmation modal must NOT appear on duplicate error!"

        # Ensure registration form remains open with inputs
        assert page.locator('h2:has-text("Register New Patient")').is_visible(), "Registration form modal must remain open on error!"

        page.screenshot(path=os.path.join(screenshots_dir, "06_duplicate_conflict_error.png"))

        # Close registration modal via Cancel
        page.locator('button:has-text("Cancel")').first.click()
        log("STEP 11", "Cancelled duplicate registration modal.")

        browser.close()
        log("SUCCESS", "ALL BROWSER & DATABASE VALIDATION CHECKS (CONFIRMATION, OPD TOKEN CREATION, QUEUE NAVIGATION, DB RECORD) PASSED PERFECTLY!")

if __name__ == "__main__":
    run_validation()

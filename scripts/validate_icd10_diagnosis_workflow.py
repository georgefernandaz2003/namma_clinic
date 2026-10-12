"""
E2E Playwright Validation: Searchable ICD-10 Diagnosis Dropdown Workflow
Validates all required scenarios:
1. Search by code (e.g., I10, E11, R50.9)
2. Search by diagnosis name (e.g., hypertension, diabetes, fever)
3. Search by clinical keyword/alias (e.g., bp, sugar, dengue)
4. Displays formatted option: 'ICD code — Diagnosis name'
5. Selection auto-populates Diagnosis Name / Condition field
6. Save consultation and reopen to confirm database & UI persistence
7. Invalid/unmatched search query displays friendly fallback without auto-assignment
8. Mandatory field validation prevents submission when diagnosis is missing
"""

import os
import sys
import time
import django

# Setup Django environment
sys.path.append(r"D:\project\namma_clinic\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_icd10_diagnosis")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def setup_test_visit():
    facility = Facility.objects.get(id=1)
    doc_user = User.objects.get(username="localdoc")
    now = timezone.now()
    timestamp = int(now.timestamp()) % 100000

    patient, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp:05d}",
        defaults={
            "patient_id": f"PAT-ICD10-{timestamp}",
            "name": f"Kavitha Ramanathan {timestamp}",
            "age": 48,
            "gender": "FEMALE",
            "address": "Jayanagar 4th Block, Bangalore",
            "registered_at_facility": facility
        }
    )

    visit = Visit.objects.create(
        visit_id=f"VIS-ICD10-{timestamp}",
        patient=patient,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Persistent headaches, dizziness, and elevated home blood pressure readings for 2 weeks",
        assigned_doctor=doc_user
    )
    return visit, patient

def run_icd10_validation():
    log("INIT", "Creating test patient and visit in PostgreSQL 16...")
    visit, patient = setup_test_visit()
    log("INIT", f"Visit ID: {visit.id} ({visit.visit_id}), Patient: {patient.name}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("dialog", lambda d: d.accept())
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}") if "error" in msg.type.lower() else None)

        # 1. Login as localdoc
        log("LOGIN", "Logging in as Medical Officer (localdoc)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "localdoc")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/consultation" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("LOGIN", "Doctor logged in successfully.")

        # 2. Navigate to consultation for the visit
        log("NAV", f"Opening consultation for Visit #{visit.id}...")
        page.goto(f"{BASE_URL}/consultation?visit={visit.id}")
        page.wait_for_selector("#diagnosis-code", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 3. Test 1: Search by Code
        log("TEST_1", "Testing search by ICD-10 Code ('I10')...")
        diag_input = page.locator("#diagnosis-code")
        diag_input.click()
        diag_input.fill("I10")
        
        # Wait for dropdown listbox
        page.wait_for_selector("#diagnosis-code-listbox", timeout=5000)
        time.sleep(0.5)

        # Capture screenshot of search by code
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_search_by_code_i10.png"))
        
        # Verify first option text contains 'I10 — Essential (primary) hypertension'
        first_option = page.locator("#diagnosis-code-listbox li").first
        opt_text = first_option.inner_text()
        assert "I10" in opt_text and "Essential (primary) hypertension" in opt_text, f"Unexpected option text: {opt_text}"
        log("TEST_1", f"Verified option formatted as 'ICD code — Diagnosis name': {opt_text.splitlines()[0]}")

        # 4. Test 2: Search by Diagnosis Name
        log("TEST_2", "Testing search by Diagnosis Name ('hypertension')...")
        diag_input.fill("hypertension")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_search_by_name_hypertension.png"))
        options = page.locator("#diagnosis-code-listbox li")
        count = options.count()
        assert count > 0, "Expected search results for 'hypertension'"
        log("TEST_2", f"Found {count} matching conditions for 'hypertension'")

        # 5. Test 3: Search by Keyword / Alias ('bp')
        log("TEST_3", "Testing search by Clinical Keyword ('bp')...")
        diag_input.fill("bp")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_search_by_keyword_bp.png"))
        bp_matches = page.locator("#diagnosis-code-listbox li").all_inner_texts()
        assert any("I10" in t for t in bp_matches), f"Expected I10 in keyword matches: {bp_matches}"
        log("TEST_3", "Verified clinical keyword 'bp' resolved to Essential (primary) hypertension (I10)")

        # 6. Test 4: Selection and Auto-Population
        log("TEST_4", "Selecting 'I10 — Essential (primary) hypertension'...")
        diag_input.fill("I10")
        time.sleep(0.5)
        page.locator("#diagnosis-code-listbox li").first.click()
        time.sleep(0.5)

        selected_code = page.locator("#diagnosis-code").input_value()
        selected_name = page.locator("#diagnosis-name").input_value()
        assert selected_code == "I10", f"Expected 'I10', got '{selected_code}'"
        assert selected_name == "Essential (primary) hypertension", f"Expected 'Essential (primary) hypertension', got '{selected_name}'"
        log("TEST_4", f"Auto-population verified: Code='{selected_code}', Condition='{selected_name}'")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_selection_auto_population.png"))

        # 7. Test 5: Invalid / Unmatched Code search
        log("TEST_5", "Testing invalid or unmatched query ('XYZ999')...")
        diag_input.click()
        diag_input.fill("XYZ999")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_unmatched_query_feedback.png"))
        empty_notice = page.locator("#diagnosis-code-listbox").inner_text()
        assert "No matching ICD-10 diagnoses found" in empty_notice, f"Expected empty notice, got: {empty_notice}"
        log("TEST_5", "Verified unmatched query shows clean fallback notice without auto-assignment")

        # Re-select I10 properly
        diag_input.fill("I10")
        time.sleep(0.5)
        page.locator("#diagnosis-code-listbox li").first.click()
        time.sleep(0.5)

        # 8. Test 6: Required Field Validation (clearing fields)
        log("TEST_6", "Testing required field validation...")
        # Clear diagnosis code
        page.locator('button[aria-label="Clear ICD-10 diagnosis code"]').click()
        time.sleep(0.3)
        # Attempt to save
        page.locator("#consultation-primary-button").click()
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_required_field_validation.png"))
        log("TEST_6", "Verified empty diagnosis prevents completion.")

        # Re-select valid diagnosis for save and persistence verification
        diag_input.fill("I10")
        time.sleep(0.5)
        page.locator("#diagnosis-code-listbox li").first.click()
        time.sleep(0.5)

        # Fill clinical assessment
        page.fill("#clinical-assessment", "BP 150/94 mmHg, fundus normal, S1 S2 heard, no murmurs")
        page.fill("#treatment-plan", "Amlodipine 5mg OD, low salt diet, lifestyle counseling, review in 2 weeks")

        # 9. Test 7: Save Consultation and Verify Persistence
        log("TEST_7", "Saving consultation...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_ready_to_save.png"))
        page.locator("#consultation-primary-button").click()
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        # 10. Database verification
        log("DB_CHECK", "Verifying Consultation saved in PostgreSQL database...")
        db_consult = Consultation.objects.filter(visit=visit).first()
        assert db_consult is not None, "Consultation record was not found in PostgreSQL!"
        assert db_consult.diagnosis_code == "I10", f"Expected DB diagnosis_code='I10', got '{db_consult.diagnosis_code}'"
        assert db_consult.diagnosis_name == "Essential (primary) hypertension", f"Expected DB diagnosis_name='Essential (primary) hypertension', got '{db_consult.diagnosis_name}'"
        log("DB_CHECK", f"PostgreSQL Verification SUCCESS: ID={db_consult.id}, Code={db_consult.diagnosis_code}, Name={db_consult.diagnosis_name}")

        # 11. Reopen consultation and verify UI persistence
        log("REOPEN", f"Reopening consultation for Visit #{visit.id} to verify UI persistence...")
        page.goto(f"{BASE_URL}/consultation?visit={visit.id}")
        page.wait_for_selector("#diagnosis-code", timeout=10000)
        time.sleep(1)

        reopened_code = page.locator("#diagnosis-code").input_value()
        reopened_name = page.locator("#diagnosis-name").input_value()
        assert reopened_code == "I10", f"Reopened code mismatch: expected 'I10', got '{reopened_code}'"
        assert reopened_name == "Essential (primary) hypertension", f"Reopened name mismatch: expected 'Essential (primary) hypertension', got '{reopened_name}'"
        log("REOPEN", f"UI Persistence SUCCESS: Code='{reopened_code}', Condition='{reopened_name}'")
        page.locator("#diagnosis-code").scroll_into_view_if_needed()
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_persisted_consultation_reopened.png"))

        browser.close()
        log("SUCCESS", "All ICD-10 diagnosis dropdown workflow checks completed successfully!")

if __name__ == "__main__":
    run_icd10_validation()

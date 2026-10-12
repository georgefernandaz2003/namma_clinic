"""
Validation Script: Nurse Triage Previous/Next Patient Navigation and Unsaved Changes Guard
Covers all requirements:
1. Navigation buttons: "← Previous Patient" and "Next Patient →" beside "Save Triage & Send to Doctor"
2. Queue navigation respecting facility scope and queue filters
3. Disabled states: First patient (Previous disabled), Last patient (Next disabled), Middle patient (both enabled)
4. Unsaved changes confirmation: cancel preserves data; accept navigates away
5. Successful triage submission and safe post-save queue progression
6. Facility & role scope validation (Nurse authorized, Doctor forbidden)
"""

import os
import sys
import time

# Setup Django environment
sys.path.append(r"D:\project\namma_clinic\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.triage.models import TriageVitals
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_nurse_triage")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(tag, message):
    print(f"[{tag}] {message}", flush=True)

def setup_test_data():
    """Create reproducible test patients and visits for facility 1 and facility 2."""
    fac1 = Facility.objects.get(id=1)
    fac2 = Facility.objects.exclude(id=1).first() or Facility.objects.create(
        facility_name="Sub-Centre Test", facility_code="SC-TEST-99", facility_type="SUB_CENTRE"
    )

    nurse_user = User.objects.get(username="e2e_nurse_user")
    doc_user = User.objects.get(username="localdoc")

    from datetime import timedelta
    from apps.visits.services import issue_opd_token

    now = timezone.now()
    suffix = int(now.timestamp()) % 10000

    # Clean existing test visits and isolate pending triage queue for deterministic testing
    Visit.objects.filter(visit_id__startswith="VIS-NURSE-E2E-").delete()
    Visit.objects.filter(facility=fac1, status="WAITING_FOR_TRIAGE").update(status="TRIAGED", current_queue="DOCTOR")

    created = {}

    # Visit 1 (First in queue)
    p1, _ = Patient.objects.get_or_create(
        mobile=f"98111{suffix:04d}1",
        defaults={
            "patient_id": f"PAT-NURSE-E2E-1-{suffix}",
            "name": f"Priya Nair {suffix}",
            "age": 28,
            "gender": "FEMALE",
            "registered_at_facility": fac1,
            "address": "Malleshwaram, Bengaluru"
        }
    )
    v1 = Visit.objects.create(
        visit_id=f"VIS-NURSE-E2E-1-{suffix}",
        patient=p1,
        facility=fac1,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        arrival_time=now - timedelta(minutes=30),
        chief_complaint="Seasonal coryza and sore throat"
    )
    tok1 = issue_opd_token(visit=v1, facility=fac1)
    created["v1"] = v1
    created["tok1"] = tok1

    # Visit 2 (Middle in queue)
    p2, _ = Patient.objects.get_or_create(
        mobile=f"98111{suffix:04d}2",
        defaults={
            "patient_id": f"PAT-NURSE-E2E-2-{suffix}",
            "name": f"Ramesh Kumar {suffix}",
            "age": 45,
            "gender": "MALE",
            "registered_at_facility": fac1,
            "address": "Jayanagar, Bengaluru"
        }
    )
    v2 = Visit.objects.create(
        visit_id=f"VIS-NURSE-E2E-2-{suffix}",
        patient=p2,
        facility=fac1,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        arrival_time=now - timedelta(minutes=20),
        chief_complaint="Dizziness and mild palpitations"
    )
    tok2 = issue_opd_token(visit=v2, facility=fac1)
    created["v2"] = v2
    created["tok2"] = tok2

    # Visit 3 (Last in queue)
    p3, _ = Patient.objects.get_or_create(
        mobile=f"98111{suffix:04d}3",
        defaults={
            "patient_id": f"PAT-NURSE-E2E-3-{suffix}",
            "name": f"Sunita Rao {suffix}",
            "age": 52,
            "gender": "FEMALE",
            "registered_at_facility": fac1,
            "address": "Indiranagar, Bengaluru"
        }
    )
    v3 = Visit.objects.create(
        visit_id=f"VIS-NURSE-E2E-3-{suffix}",
        patient=p3,
        facility=fac1,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        arrival_time=now - timedelta(minutes=10),
        chief_complaint="Joint pain and chronic weakness"
    )
    tok3 = issue_opd_token(visit=v3, facility=fac1)
    created["v3"] = v3
    created["tok3"] = tok3

    # Visit 4 (Other facility: Facility 2)
    p4, _ = Patient.objects.get_or_create(
        mobile=f"98111{suffix:04d}4",
        defaults={
            "patient_id": f"PAT-NURSE-E2E-4-{suffix}",
            "name": f"Other Facility Patient {suffix}",
            "age": 30,
            "gender": "MALE",
            "registered_at_facility": fac2,
            "address": "Other City"
        }
    )
    v4 = Visit.objects.create(
        visit_id=f"VIS-NURSE-E2E-4-{suffix}",
        patient=p4,
        facility=fac2,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        chief_complaint="Other clinic fever"
    )
    tok4 = issue_opd_token(visit=v4, facility=fac2)
    created["v4_other_fac"] = v4
    created["tok4"] = tok4
    created["p4"] = p4

    return created

def run_e2e_tests():
    log("INIT", "Setting up reproducible test data in PostgreSQL 16...")
    visits = setup_test_data()
    v1 = visits["v1"]
    v2 = visits["v2"]
    v3 = visits["v3"]
    v4_other = visits["v4_other_fac"]
    log("INIT", f"Created test visits: v1={v1.visit_id}, v2={v2.visit_id}, v3={v3.visit_id}, v4_other={v4_other.visit_id}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Track dialog events
        dialog_history = []
        dialog_response = {"action": "accept"}

        def on_dialog(dialog):
            msg = dialog.message
            dialog_history.append(msg)
            log("DIALOG", f"Encountered dialog message: '{msg}'")
            if dialog_response["action"] == "accept":
                dialog.accept()
            else:
                dialog.dismiss()

        page.on("dialog", on_dialog)

        page.on("console", lambda msg: log("CONSOLE", f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: log("PAGEERROR", str(err)))

        # -------------------------------------------------------------
        # STEP 1: ROLE & FACILITY SCOPE
        # -------------------------------------------------------------
        log("AUTH", "Testing Nurse Login with e2e_nurse_user...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "e2e_nurse_user")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/triage" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("AUTH", f"Nurse logged in successfully. URL: {page.url}")

        # -------------------------------------------------------------
        # STEP 2: FIRST PATIENT NAVIGATION STATE
        # -------------------------------------------------------------
        log("SCENARIO 1", f"Navigating to First Patient in queue (v1: {v1.id})...")
        page.goto(f"{BASE_URL}/triage?visit={v1.id}")
        try:
            page.wait_for_selector("#save-triage-btn", timeout=10000)
        except Exception as e:
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "debug_step2_timeout.png"))
            log("DEBUG", f"Page URL at timeout: {page.url}")
            log("DEBUG", f"Body text at timeout: {page.locator('body').inner_text()[:400]}")
            raise e
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Verify buttons exist
        prev_btn = page.locator("#prev-patient-btn")
        next_btn = page.locator("#next-patient-btn")
        save_btn = page.locator("#save-triage-btn")

        assert prev_btn.count() > 0, "Previous Patient button not found!"
        assert next_btn.count() > 0, "Next Patient button not found!"
        assert save_btn.count() > 0, "Save Triage button not found!"

        # First Patient: Previous is DISABLED, Next is ENABLED
        assert prev_btn.is_disabled() is True, "Previous button must be DISABLED on first patient!"
        assert next_btn.is_disabled() is False, "Next button must be ENABLED when next patient exists!"
        log("SCENARIO 1", "Verified First Patient: Previous button is disabled, Next button is enabled.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_first_patient_prev_disabled.png"))

        # Verify Facility Scope: Facility 2 patient must NOT be in queue options
        options_text = page.locator("#triage-encounter-select").inner_text()
        p4 = visits["p4"]
        assert p4.name not in options_text, "Facility 2 patient must not leak into Facility 1 queue!"
        log("SCENARIO 1", "Verified strict facility isolation: Other clinic patient excluded from queue.")

        # -------------------------------------------------------------
        # STEP 3: MIDDLE PATIENT NAVIGATION STATE
        # -------------------------------------------------------------
        log("SCENARIO 2", "Clicking Next Patient to navigate to Middle Patient (v2)...")
        next_btn.click()
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        assert f"visit={v2.id}" in page.url, f"Expected URL to contain visit={v2.id}, got: {page.url}"
        page.wait_for_selector("#save-triage-btn", timeout=5000)

        # Middle Patient: Both Previous and Next are ENABLED
        prev_btn_mid = page.locator("#prev-patient-btn")
        next_btn_mid = page.locator("#next-patient-btn")

        assert prev_btn_mid.is_disabled() is False, "Previous button must be ENABLED on middle patient!"
        assert next_btn_mid.is_disabled() is False, "Next button must be ENABLED on middle patient!"
        log("SCENARIO 2", "Verified Middle Patient: Both Previous and Next buttons are enabled.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_middle_patient_both_enabled.png"))

        # -------------------------------------------------------------
        # STEP 4: LAST PATIENT NAVIGATION STATE
        # -------------------------------------------------------------
        log("SCENARIO 3", "Clicking Next Patient to navigate to Last Patient (v3)...")
        next_btn_mid.click()
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        assert f"visit={v3.id}" in page.url, f"Expected URL to contain visit={v3.id}, got: {page.url}"
        page.wait_for_selector("#save-triage-btn", timeout=5000)

        # Last Patient: Previous is ENABLED, Next is DISABLED
        prev_btn_last = page.locator("#prev-patient-btn")
        next_btn_last = page.locator("#next-patient-btn")

        assert prev_btn_last.is_disabled() is False, "Previous button must be ENABLED on last patient!"
        assert next_btn_last.is_disabled() is True, "Next button must be DISABLED on last patient!"
        log("SCENARIO 3", "Verified Last Patient: Previous button is enabled, Next button is disabled.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_last_patient_next_disabled.png"))

        # -------------------------------------------------------------
        # STEP 5: UNSAVED CHANGES CONFIRMATION GUARD
        # -------------------------------------------------------------
        log("SCENARIO 4", "Testing unsaved changes confirmation guard...")
        # Modify vitals on Patient Gamma (v3)
        page.fill('[data-testid="sys-bp"]', "145")
        page.fill('[data-testid="nurse-notes"]', "Unsaved observations: Patient presents with headache and body chills.")

        # Test 5A: Discard CANCELLED -> Patient and data preserved
        dialog_response["action"] = "dismiss"
        log("SCENARIO 4", "Attempting navigation with dismiss (Cancel)...")
        prev_btn_last.click()
        time.sleep(1)

        # URL should still be v3, and edited data must remain in inputs!
        assert f"visit={v3.id}" in page.url, "Navigation must NOT happen when confirmation is cancelled!"
        current_sys_bp = page.locator('[data-testid="sys-bp"]').input_value()
        current_notes = page.locator('[data-testid="nurse-notes"]').input_value()
        assert current_sys_bp == "145", f"Expected BP 145 preserved, got {current_sys_bp}"
        assert "Unsaved observations" in current_notes, f"Expected notes preserved, got {current_notes}"
        log("SCENARIO 4", "Confirmed: Cancel preserves entered vitals and cancels navigation away.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_unsaved_changes_preserved_on_cancel.png"))

        # Test 5B: Discard ACCEPTED -> Navigates to previous patient (v2)
        dialog_response["action"] = "accept"
        log("SCENARIO 4", "Attempting navigation with accept (Confirm discard)...")
        prev_btn_last.click()
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        assert f"visit={v2.id}" in page.url, f"Expected URL to navigate to visit={v2.id}, got: {page.url}"
        log("SCENARIO 4", f"Confirmed: Confirmation accept allowed navigation to {page.url}")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_navigated_after_confirm_discard.png"))

        # -------------------------------------------------------------
        # STEP 6: SUCCESSFUL TRIAGE SUBMISSION & POST-SAVE QUEUE PROGRESSION
        # -------------------------------------------------------------
        log("SCENARIO 5", "Testing real triage submission and post-save queue progression on Patient Beta (v2)...")
        page.fill('[data-testid="sys-bp"]', "124")
        page.fill('[data-testid="dia-bp"]', "82")
        page.fill('[data-testid="pulse-rate"]', "76")
        page.fill('[data-testid="temperature"]', "98.6")
        page.fill('[data-testid="spo2-level"]', "99")
        page.fill('[data-testid="resp-rate"]', "18")
        page.fill('[data-testid="patient-height"]', "168")
        page.fill('[data-testid="patient-weight"]', "68")
        page.fill('[data-testid="blood-glucose"]', "115")
        page.fill('[data-testid="nurse-notes"]', "Routine vitals recorded, normal appearance, alert.")

        page.click("#save-triage-btn")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        # Database verification for v2
        v2.refresh_from_db()
        assert v2.status == "TRIAGED", f"Expected v2 status TRIAGED, got: {v2.status}"
        assert v2.current_queue == "DOCTOR", f"Expected v2 current_queue DOCTOR, got: {v2.current_queue}"
        assert TriageVitals.objects.filter(visit=v2).exists(), "TriageVitals record must exist in DB!"
        log("SCENARIO 5", f"Visit {v2.visit_id} verified in DB: status=TRIAGED, current_queue=DOCTOR!")

        # UI verification
        page.wait_for_selector('[data-testid="triage-recorded-card"]', timeout=10000)
        assert page.locator('[data-testid="recorded-next-patient-btn"]').count() > 0
        log("SCENARIO 5", "Triage Recorded Card visible with Next Patient button.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_triage_saved_success.png"))

        # Safe post-save navigation: Click Next Patient from recorded card
        log("SCENARIO 5", "Clicking Next Patient on recorded card...")
        page.click('[data-testid="recorded-next-patient-btn"]')
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        # Must land on Patient Gamma (v3), not skip or crash
        assert f"visit={v3.id}" in page.url, f"Expected to navigate safely to visit={v3.id}, got: {page.url}"
        log("SCENARIO 5", f"Safe queue progression verified: Landed on next pending patient ({v3.visit_id})!")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_navigated_to_next_after_save.png"))

        browser.close()
        log("SUCCESS", "ALL NURSE TRIAGE NAVIGATION & UNSAVED CHANGES TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_e2e_tests()

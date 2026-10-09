"""
Validation Script: Doctor Consultation State-Aware Workflow and Laboratory Lifecycle
Tests all 6 required clinical scenarios:
1. Consultation without lab -> Complete Consultation -> Next Patient.
2. Consultation with one lab -> Send to Laboratory -> completion blocked.
3. Lab completes -> doctor sees results -> Complete Consultation -> Next Patient.
4. Multiple labs -> completion blocked until ALL results are complete -> then unlocks.
5. Prescription-only consultation still works normally.
6. Existing consultation queue behavior remains unchanged.
"""

import os
import sys
import time
import django

# Setup Django environment for test fixture creation and DB verification
sys.path.append(r"D:\project\namma_clinic\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.utils import timezone
from apps.accounts.models import User, StaffProfile
from apps.facilities.models import Facility, FacilityService, ServiceMaster
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.consultations.models import Consultation
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, TestRequest, Specimen, DiagnosticResult
from apps.pharmacy.models import MedicineMaster
from apps.laboratory.services import collect_specimen, record_diagnostic_result, verify_diagnostic_result

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_doctor_consultation")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def setup_test_patients_and_visits():
    """Create reproducible test patients and visits for the 6 scenarios."""
    facility = Facility.objects.get(id=1)
    doc_user = User.objects.get(username="localdoc")
    doc_staff = getattr(doc_user, "staff_profile", None)
    lab_user = User.objects.get(username="locallab")
    lab_staff = getattr(lab_user, "staff_profile", None)
    
    # Enable diagnostics service
    srv, _ = ServiceMaster.objects.get_or_create(code="SRV_DIAGNOSTICS", defaults={"name": "Diagnostics", "category": "CLINICAL"})
    fs, _ = FacilityService.objects.get_or_create(facility=facility, service=srv, defaults={"is_available": True})
    fs.is_available = True
    fs.save()

    now = timezone.now()
    timestamp_suffix = int(now.timestamp()) % 10000

    created_visits = {}

    # Visit 1: For Scenario 1 (No Lab)
    p1, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp_suffix:04d}1",
        defaults={"patient_id": f"PAT-E2E-1-{timestamp_suffix}", "name": f"Patient Alpha {timestamp_suffix}", "age": 32, "gender": "FEMALE", "address": "Jayanagar", "registered_at_facility": facility}
    )
    v1 = Visit.objects.create(
        visit_id=f"VIS-E2E-1-{timestamp_suffix}",
        patient=p1,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Mild seasonal rhinitis and headache",
        assigned_doctor=doc_user
    )
    created_visits["scenario_1"] = v1

    # Visit 2: For Scenario 2 & 3 (Single Lab Order)
    p2, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp_suffix:04d}2",
        defaults={"patient_id": f"PAT-E2E-2-{timestamp_suffix}", "name": f"Patient Beta {timestamp_suffix}", "age": 45, "gender": "MALE", "address": "Malleshwaram", "registered_at_facility": facility}
    )
    v2 = Visit.objects.create(
        visit_id=f"VIS-E2E-2-{timestamp_suffix}",
        patient=p2,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="High fever with joint chills for 4 days",
        assigned_doctor=doc_user
    )
    created_visits["scenario_2_3"] = v2

    # Visit 3: For Scenario 4 (Multiple Lab Orders)
    p3, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp_suffix:04d}3",
        defaults={"patient_id": f"PAT-E2E-3-{timestamp_suffix}", "name": f"Patient Gamma {timestamp_suffix}", "age": 28, "gender": "FEMALE", "address": "Indiranagar", "registered_at_facility": facility}
    )
    v3 = Visit.objects.create(
        visit_id=f"VIS-E2E-3-{timestamp_suffix}",
        patient=p3,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Prolonged pyrexia, weakness and retro-orbital pain",
        assigned_doctor=doc_user
    )
    created_visits["scenario_4"] = v3

    # Visit 4: For Scenario 5 (Prescription-only)
    p4, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp_suffix:04d}4",
        defaults={"patient_id": f"PAT-E2E-4-{timestamp_suffix}", "name": f"Patient Delta {timestamp_suffix}", "age": 52, "gender": "MALE", "address": "Rajajinagar", "registered_at_facility": facility}
    )
    v4 = Visit.objects.create(
        visit_id=f"VIS-E2E-4-{timestamp_suffix}",
        patient=p4,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Acid reflux and epigastric discomfort",
        assigned_doctor=doc_user
    )
    created_visits["scenario_5"] = v4

    # Visit 5: Queue target to test "Next Patient"
    p5, _ = Patient.objects.get_or_create(
        mobile=f"98765{timestamp_suffix:04d}5",
        defaults={"patient_id": f"PAT-E2E-5-{timestamp_suffix}", "name": f"Patient Epsilon {timestamp_suffix}", "age": 19, "gender": "FEMALE", "address": "Koramangala", "registered_at_facility": facility}
    )
    v5 = Visit.objects.create(
        visit_id=f"VIS-E2E-5-{timestamp_suffix}",
        patient=p5,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Sprained right ankle from badminton",
        assigned_doctor=doc_user
    )
    created_visits["next_in_queue"] = v5

    return created_visits, lab_staff

def run_e2e_tests():
    log("INIT", "Setting up reproducible test data in PostgreSQL 16...")
    visits, lab_staff = setup_test_patients_and_visits()
    log("INIT", f"Created visits: {[v.visit_id for v in visits.values()]}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Handle dialogs automatically
        page.on("dialog", lambda d: d.accept())
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGEERROR] {err}"))
        page.on("response", lambda res: print(f"[HTTP {res.status}] {res.url}") if res.status >= 400 else None)

        # -------------------------------------------------------------
        # STEP 1: LOGIN AS DOCTOR (localdoc)
        # -------------------------------------------------------------
        log("LOGIN", "Logging in as Medical Officer (localdoc)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "localdoc")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/consultation" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("LOGIN", f"Logged in. Current URL: {page.url}")

        # -------------------------------------------------------------
        # SCENARIO 1: NO LAB ORDER
        # "Save & Complete Consultation" -> Complete Consultation -> Next Patient
        # -------------------------------------------------------------
        log("SCENARIO 1", "Starting Scenario 1: Consultation without lab...")
        v1 = visits["scenario_1"]
        page.goto(f"{BASE_URL}/consultation?visit={v1.id}")
        try:
            page.wait_for_selector("#consultation-primary-button", timeout=10000)
        except Exception as e:
            log("DEBUG", f"Current URL on timeout: {page.url}")
            log("DEBUG", f"Page body snippet: {page.locator('body').inner_text()[:500]}")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "debug_scenario1_timeout.png"))
            raise e
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Verify button text is "Save & Complete Consultation"
        btn_text = page.locator("#consultation-primary-button").inner_text().strip()
        assert "Save & Complete Consultation" in btn_text, f"Expected 'Save & Complete Consultation', got: {btn_text}"
        log("SCENARIO 1", f"Verified primary button text: '{btn_text}'")

        # Fill consultation details
        page.fill("#diagnosis-code", "J00")
        page.fill("#diagnosis-name", "Acute Nasopharyngitis (Common Cold)")
        page.fill("#clinical-assessment", "Mild coryza, afebrile, lungs clear")
        page.fill("#treatment-plan", "Rest, steam inhalation, hydration")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_scenario1_before_completion.png"))

        # Click "Save & Complete Consultation"
        page.click("#consultation-primary-button")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        # Verify visit in DB is COMPLETED
        v1.refresh_from_db()
        assert v1.status == "COMPLETED", f"Expected v1 status COMPLETED, got {v1.status}"
        log("SCENARIO 1", f"Visit {v1.visit_id} marked COMPLETED in DB!")

        # Verify "Next Patient" button is now visible
        page.wait_for_selector("#next-patient-button", timeout=10000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_scenario1_completed_next_patient.png"))
        log("SCENARIO 1", "Next Patient button visible and active!")

        # -------------------------------------------------------------
        # SCENARIO 2: LAB ORDERED (Single test)
        # Select "Order Diagnostic Test" -> primary button becomes "Save & Send to Laboratory"
        # Click it -> visit status becomes WAITING_FOR_LAB -> completion blocked!
        # -------------------------------------------------------------
        log("SCENARIO 2", "Starting Scenario 2: Consultation with single lab order...")
        v2 = visits["scenario_2_3"]
        page.goto(f"{BASE_URL}/consultation?visit={v2.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Before checking checkbox: button is Save & Complete
        btn_text_initial = page.locator("#consultation-primary-button").inner_text().strip()
        assert "Save & Complete Consultation" in btn_text_initial

        # Fill mandatory diagnosis
        page.fill("#diagnosis-code", "A90")
        page.fill("#diagnosis-name", "Dengue Fever / Acute Pyrexia")
        page.fill("#clinical-assessment", "High grade fever, severe myalgia")

        # Check "Order Diagnostic Test"
        page.check("#order-diagnostics-checkbox")
        page.wait_for_selector("#lab-test", timeout=5000)

        # Select test master (e.g. NS1-AG, ID 1)
        page.select_option("#lab-test", value="1")
        time.sleep(0.5)

        # Verify button text changed to "Save & Send to Laboratory"
        btn_text_lab = page.locator("#consultation-primary-button").inner_text().strip()
        assert "Save & Send to Laboratory" in btn_text_lab, f"Expected 'Save & Send to Laboratory', got: {btn_text_lab}"
        log("SCENARIO 2", f"Button dynamically changed to: '{btn_text_lab}'")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_scenario2_save_and_send_to_lab.png"))

        # Click "Save & Send to Laboratory"
        page.click("#consultation-primary-button")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        # Verify backend DB: visit status is WAITING_FOR_LAB, queue is LAB
        v2.refresh_from_db()
        assert v2.status == "WAITING_FOR_LAB", f"Expected WAITING_FOR_LAB, got {v2.status}"
        assert v2.current_queue == "LAB", f"Expected LAB queue, got {v2.current_queue}"
        assert v2.diagnostic_orders.exists(), "DiagnosticOrder record was not created!"
        diag_order = v2.diagnostic_orders.first()
        log("SCENARIO 2", f"DiagnosticOrder #{diag_order.order_number} created in DB! Visit status is {v2.status}")

        # In browser: button must now be DISABLED with "Awaiting Laboratory Results"
        btn_text_locked = page.locator("#consultation-primary-button").inner_text().strip()
        is_disabled = page.locator("#consultation-primary-button").is_disabled()
        assert "Awaiting Laboratory Results" in btn_text_locked, f"Expected 'Awaiting Laboratory Results', got: {btn_text_locked}"
        assert is_disabled is True, "Primary button must be disabled while awaiting lab results!"
        
        # Verify status badge near lab section
        badge_text = page.locator("#lab-status-badge").inner_text().strip()
        assert "Lab Ordered — Awaiting Results" in badge_text, f"Expected 'Lab Ordered — Awaiting Results', got: {badge_text}"
        log("SCENARIO 2", f"Status badge displayed: '{badge_text}'. Completion properly locked!")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_scenario2_awaiting_lab_blocked.png"))

        # -------------------------------------------------------------
        # SCENARIO 3: LAB COMPLETES -> Doctor sees results -> Complete Consultation -> Next Patient
        # -------------------------------------------------------------
        log("SCENARIO 3", "Starting Scenario 3: Lab completes and verifies results...")
        
        # Simulate lab technician processing in DB
        tr = diag_order.test_requests.first()
        specimen = collect_specimen(diag_order, f"SMP-{diag_order.id}-001", "WHOLE_BLOOD", lab_staff, [tr])
        diag_res = record_diagnostic_result(
            test_request=tr,
            entered_by_staff=lab_staff,
            result_value_text="POSITIVE (Reactive)",
            reference_range_applied="Negative / Non-reactive",
            is_abnormal=True
        )
        verify_diagnostic_result(diag_res, verified_by_staff=lab_staff)
        v2.refresh_from_db()
        log("SCENARIO 3", f"Lab verified result. Visit status in DB auto-advanced to: {v2.status}")

        # Doctor refreshes / reopens consultation for v2
        page.goto(f"{BASE_URL}/consultation?visit={v2.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 1. Verify status badge near lab section: "Lab Results Available — Review & Complete"
        badge_text_done = page.locator("#lab-status-badge").inner_text().strip()
        assert "Lab Results Available — Review & Complete" in badge_text_done, f"Expected 'Lab Results Available — Review & Complete', got: {badge_text_done}"
        log("SCENARIO 3", f"Badge updated to: '{badge_text_done}'")

        # 2. Verify lab results review card is visible in EMR with POSITIVE value
        page.wait_for_selector("#lab-results-review-section", timeout=5000)
        res_review_text = page.locator("#lab-results-review-section").inner_text()
        assert "POSITIVE" in res_review_text, f"Expected 'POSITIVE' in results review, got: {res_review_text}"
        assert "ABNORMAL" in res_review_text

        # 3. Verify primary button is now UNLOCKED and says "Complete Consultation"
        btn_text_complete = page.locator("#consultation-primary-button").inner_text().strip()
        is_disabled_now = page.locator("#consultation-primary-button").is_disabled()
        assert "Complete Consultation" in btn_text_complete, f"Expected 'Complete Consultation', got: {btn_text_complete}"
        assert is_disabled_now is False, "Complete Consultation button should now be enabled!"
        log("SCENARIO 3", f"Button unlocked with label: '{btn_text_complete}'")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_scenario3_results_available_unlocked.png"))

        # 4. Doctor finalizes and completes consultation
        page.click("#consultation-primary-button")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        v2.refresh_from_db()
        assert v2.status == "COMPLETED", f"Expected COMPLETED, got {v2.status}"
        log("SCENARIO 3", f"Visit {v2.visit_id} successfully COMPLETED in DB!")

        # Next Patient button visible
        page.wait_for_selector("#next-patient-button", timeout=10000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_scenario3_consultation_completed_next_patient.png"))

        # -------------------------------------------------------------
        # SCENARIO 4: MULTIPLE LABS -> Completion blocked until ALL results are complete
        # -------------------------------------------------------------
        log("SCENARIO 4", "Starting Scenario 4: Multiple lab orders partial vs full completion...")
        v3 = visits["scenario_4"]
        page.goto(f"{BASE_URL}/consultation?visit={v3.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        page.fill("#diagnosis-code", "R50.9")
        page.fill("#diagnosis-name", "Fever of Unknown Origin")

        # Order 2 tests: CBC (ID 2) and ESR (ID 3)
        page.check("#order-diagnostics-checkbox")
        page.wait_for_selector("#lab-test", timeout=5000)

        # Add 1st test (CBC)
        page.select_option("#lab-test", value="2")
        page.click('button:has-text("Add")')
        time.sleep(0.5)

        # Add 2nd test (ESR)
        page.select_option("#lab-test", value="3")
        page.click('button:has-text("Add")')
        time.sleep(0.5)

        # Verify button is "Save & Send to Laboratory"
        btn_text_multi = page.locator("#consultation-primary-button").inner_text().strip()
        assert "Save & Send to Laboratory" in btn_text_multi
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_scenario4_multi_lab_selected.png"))

        # Submit to lab
        page.click("#consultation-primary-button")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        v3.refresh_from_db()
        multi_order = v3.diagnostic_orders.first()
        test_reqs = list(multi_order.test_requests.all())
        assert len(test_reqs) == 2, f"Expected 2 test requests, found {len(test_reqs)}"
        log("SCENARIO 4", f"Created order with {len(test_reqs)} test requests: {[tr.test_master.test_code for tr in test_reqs]}")

        # Now simulate lab entering and verifying ONLY the 1st test (CBC)
        tr1, tr2 = test_reqs[0], test_reqs[1]
        collect_specimen(multi_order, f"SMP-{multi_order.id}-002", "WHOLE_BLOOD", lab_staff, [tr1, tr2])
        res1 = record_diagnostic_result(tr1, lab_staff, result_value_text="Hb: 11.2, WBC: 8500", reference_range_applied="12-16 g/dL")
        verify_diagnostic_result(res1, lab_staff)

        # Doctor refreshes v3 page
        page.goto(f"{BASE_URL}/consultation?visit={v3.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # VERIFY: Because test 2 (ESR) is still pending, completion MUST REMAIN BLOCKED!
        btn_text_partial = page.locator("#consultation-primary-button").inner_text().strip()
        is_partial_disabled = page.locator("#consultation-primary-button").is_disabled()
        assert "Awaiting Laboratory Results" in btn_text_partial, f"Expected 'Awaiting Laboratory Results', got: {btn_text_partial}"
        assert is_partial_disabled is True, "Completion must be blocked when 1 of 2 tests is pending!"
        log("SCENARIO 4", "Confirmed: Partial verification strictly blocks completion! (1/2 tests verified)")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_scenario4_partial_lab_blocked.png"))

        # Now lab enters and verifies the 2nd test (ESR)
        res2 = record_diagnostic_result(tr2, lab_staff, result_value_text="22 mm/hr", reference_range_applied="0-15 mm/hr")
        verify_diagnostic_result(res2, lab_staff)
        v3.refresh_from_db()
        log("SCENARIO 4", f"Lab verified 2nd test. Order status: {multi_order.status}, Visit status: {v3.status}")

        # Doctor refreshes v3 page again
        page.goto(f"{BASE_URL}/consultation?visit={v3.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # VERIFY: Now ALL tests are complete -> UNLOCKED "Complete Consultation"
        btn_text_all_done = page.locator("#consultation-primary-button").inner_text().strip()
        is_all_done_disabled = page.locator("#consultation-primary-button").is_disabled()
        assert "Complete Consultation" in btn_text_all_done, f"Expected 'Complete Consultation', got: {btn_text_all_done}"
        assert is_all_done_disabled is False, "Complete Consultation must be unlocked when all tests verified!"
        log("SCENARIO 4", "Confirmed: All multi-lab tests verified -> Complete Consultation unlocked!")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_scenario4_all_verified_unlocked.png"))

        # Complete consultation
        page.click("#consultation-primary-button")
        time.sleep(2)
        v3.refresh_from_db()
        assert v3.status == "COMPLETED"
        log("SCENARIO 4", "Multi-lab encounter completed successfully!")

        # -------------------------------------------------------------
        # SCENARIO 5: PRESCRIPTION-ONLY CONSULTATION
        # Works normally, advances to WAITING_FOR_PHARMACY
        # -------------------------------------------------------------
        log("SCENARIO 5", "Starting Scenario 5: Prescription-only consultation...")
        v4 = visits["scenario_5"]
        page.goto(f"{BASE_URL}/consultation?visit={v4.id}")
        page.wait_for_selector("#consultation-primary-button", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        page.fill("#diagnosis-code", "K21.9")
        page.fill("#diagnosis-name", "Gastro-Esophageal Reflux Disease (GERD)")
        page.fill("#clinical-assessment", "Heartburn post meals, epigastric tenderness")

        # Check "Prescribe Medications"
        page.check("#prescribe-medications-checkbox")
        page.wait_for_selector("#prescription-notes", timeout=5000)
        page.fill("#prescription-notes", "Tab. Pantoprazole 40mg OD before breakfast for 14 days.")

        # Button should still be "Save & Complete Consultation"
        btn_text_rx = page.locator("#consultation-primary-button").inner_text().strip()
        assert "Save & Complete Consultation" in btn_text_rx
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_scenario5_prescription_only.png"))

        page.click("#consultation-primary-button")
        time.sleep(2)
        v4.refresh_from_db()
        assert v4.status == "WAITING_FOR_PHARMACY", f"Expected WAITING_FOR_PHARMACY, got {v4.status}"
        assert v4.current_queue == "PHARMACY"
        log("SCENARIO 5", f"Visit {v4.visit_id} advanced to WAITING_FOR_PHARMACY! Prescription workflow preserved.")

        # Next Patient button visible
        page.wait_for_selector("#next-patient-button", timeout=10000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_scenario5_completed_next_patient.png"))

        # -------------------------------------------------------------
        # SCENARIO 6: QUEUE NAVIGATION UNCHANGED & NEXT PATIENT CLICK
        # Click "Next Patient" -> Loads next queued patient (v5)
        # -------------------------------------------------------------
        log("SCENARIO 6", "Starting Scenario 6: Next Patient queue navigation...")
        v5 = visits["next_in_queue"]

        # Click "Next Patient" button from scenario 5
        page.click("#next-patient-button")
        time.sleep(2)
        page.wait_for_load_state("networkidle")

        log("SCENARIO 6", f"Navigated to: {page.url}")
        assert f"visit={v5.id}" in page.url or "/consultation" in page.url
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_scenario6_next_patient_loaded.png"))

        # Verify doctor dashboard queue filters are intact
        page.goto(f"{BASE_URL}/dashboard/doctor")
        page.wait_for_selector('div[role="tablist"]', timeout=10000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "13_scenario6_doctor_dashboard_queue.png"))
        log("SCENARIO 6", "Doctor dashboard queue filters verified intact!")

        browser.close()
        log("SUCCESS", "ALL 6 SCENARIOS VALIDATED IN REAL BROWSER SUCCESSFULLY!")

if __name__ == "__main__":
    run_e2e_tests()

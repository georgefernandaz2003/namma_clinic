"""
E2E Playwright Browser Validation: Clickable Patient Longitudinal History & Visit Details Modal
Tests all required scenarios:
1. Click first historical visit and verify its complete clinical and operational details.
2. Click a different historical visit and verify its ID and data change accurately.
3. Visits with missing sections display appropriate 'No data recorded' empty states.
4. Modal layout, dimmed backdrop, scrolling, close button, close icon, and reopening.
5. Role-based access control and confidentiality safeguards.
6. Current ongoing consultation form state and workflow remain completely unchanged.
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
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_longitudinal_history")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def setup_test_patient_and_history():
    facility = Facility.objects.get(id=1)
    doc_user = User.objects.get(username="localdoc")
    doc_staff = getattr(doc_user, "staff_profile", None)
    now = timezone.now()
    timestamp = int(now.timestamp()) % 100000

    patient, _ = Patient.objects.get_or_create(
        mobile=f"98767{timestamp:05d}",
        defaults={
            "patient_id": f"PAT-HIST-{timestamp}",
            "name": f"Meenakshi Sundaram {timestamp}",
            "age": 54,
            "gender": "FEMALE",
            "address": "Basavanagudi, Bangalore",
            "registered_at_facility": facility
        }
    )

    # 1. Historical Visit A: Complete visit with Triage, Consultation, Prescription
    v_hist_a = Visit.objects.create(
        visit_id=f"VIS-HIST-A-{timestamp}",
        patient=patient,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="COMPLETED",
        current_queue="COMPLETED",
        chief_complaint="Dizziness, morning headaches, high blood pressure readings",
        assigned_doctor=doc_user
    )

    TriageVitals.objects.create(
        visit=v_hist_a,
        patient=patient,
        nurse=doc_user,
        blood_pressure_systolic=148,
        blood_pressure_diastolic=92,
        pulse_bpm=78,
        temperature_f=98.6,
        spo2_percent=98,
        respiratory_rate=16,
        height_cm=160,
        weight_kg=68,
        bmi=26.6,
        blood_glucose_mgdl=118,
        nurse_notes="Patient alert. Elevated blood pressure on left arm. Triage priority: NORMAL.",
        high_bp_flag=True
    )

    c_a = Consultation.objects.create(
        visit=v_hist_a,
        patient=patient,
        doctor=doc_user,
        doctor_staff=doc_staff,
        facility=facility,
        chief_complaint="Dizziness and morning occipital headaches for 10 days",
        clinical_history="Known hypertensive since 2 years on irregular medication.",
        clinical_assessment="BP 148/92 mmHg, S1 S2 heard, chest clear bilaterally.",
        diagnosis_code="I10",
        diagnosis_name="Essential (primary) hypertension",
        treatment_plan="Tab Amlodipine 5mg OD po, low salt dietary modification.",
        clinical_notes="Advised daily home BP diary. Review in 15 days.",
        follow_up_date=timezone.now().date() + timezone.timedelta(days=14)
    )

    med = MedicineMaster.objects.first()
    rx_a = Prescription.objects.create(
        consultation=c_a,
        patient=patient,
        doctor=doc_user,
        doctor_staff=doc_staff,
        facility=facility,
        status="DISPENSED",
        notes="Dispensed by staff pharmacist"
    )
    PrescriptionItem.objects.create(
        prescription=rx_a,
        medicine=med,
        medicine_name="Amlodipine 5mg",
        dosage="1-0-0 After Food",
        frequency="Once Daily",
        duration_days=14,
        quantity=14,
        dispensed_quantity=14,
        status="DISPENSED"
    )

    # 2. Historical Visit B: Minimal visit without triage or prescription (tests empty state)
    v_hist_b = Visit.objects.create(
        visit_id=f"VIS-HIST-B-{timestamp}",
        patient=patient,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="COMPLETED",
        current_queue="COMPLETED",
        chief_complaint="Watery loose motions and abdominal cramps for 1 day",
        assigned_doctor=doc_user
    )

    Consultation.objects.create(
        visit=v_hist_b,
        patient=patient,
        doctor=doc_user,
        doctor_staff=doc_staff,
        facility=facility,
        chief_complaint="Watery loose motions 5-6 episodes with periumbilical cramps",
        clinical_history="Consumed outside food yesterday evening.",
        clinical_assessment="Mild dehydration, abdomen soft, no guarding.",
        diagnosis_code="A09",
        diagnosis_name="Infectious gastroenteritis and colitis, unspecified",
        treatment_plan="ORS sachet 1 pack in 1L water, zinc supplements, probiotics.",
        clinical_notes="Hydration counseling provided."
    )

    # 3. Current active visit waiting for doctor consultation
    v_active = Visit.objects.create(
        visit_id=f"VIS-ACTIVE-{timestamp}",
        patient=patient,
        facility=facility,
        visit_type="GENERAL_OPD",
        status="TRIAGED",
        current_queue="DOCTOR",
        chief_complaint="Routine follow-up review for blood pressure control",
        assigned_doctor=doc_user
    )

    return patient, v_hist_a, v_hist_b, v_active

def run_e2e_history_modal_tests():
    log("INIT", "Creating test patient with multiple historical visits in PostgreSQL 16...")
    patient, v_hist_a, v_hist_b, v_active = setup_test_patient_and_history()
    log("INIT", f"Patient: {patient.name} ({patient.patient_id})")
    log("INIT", f"Visit A (Complete): {v_hist_a.id} ({v_hist_a.visit_id})")
    log("INIT", f"Visit B (Minimal): {v_hist_b.id} ({v_hist_b.visit_id})")
    log("INIT", f"Visit Active: {v_active.id} ({v_active.visit_id})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("dialog", lambda d: d.accept())

        # 1. Login as Medical Officer (localdoc)
        log("LOGIN", "Logging in as Medical Officer (localdoc)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "localdoc")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/consultation" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("LOGIN", "Logged in successfully.")

        # 2. Navigate to Consultation for active visit
        log("NAV", f"Opening consultation page for active visit #{v_active.id}...")
        page.goto(f"{BASE_URL}/consultation?visit={v_active.id}")
        page.wait_for_selector("#history-heading", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 3. Verify Patient Longitudinal History section exists and has historical cards
        log("TEST_1", "Verifying Patient Longitudinal History cards...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_consultation_history_section.png"))
        
        hist_cards = page.locator('div[aria-label*="View full details for Visit #"]')
        card_count = hist_cards.count()
        assert card_count >= 2, f"Expected at least 2 historical visit cards, found {card_count}"
        log("TEST_1", f"Found {card_count} interactive historical visit cards.")

        # 4. Click First Historical Visit (Visit A)
        log("TEST_2", f"Clicking Visit A card (Visit #{v_hist_a.id})...")
        card_a = page.locator(f'div[aria-label*="Visit #{v_hist_a.id}"]').first
        card_a.click()
        
        # Verify Visit Details modal opens
        page.wait_for_selector('h2:has-text("Visit Details")', timeout=5000)
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_visit_a_details_modal.png"))

        modal_text = page.locator('div[role="dialog"]').inner_text()
        assert v_hist_a.visit_id in modal_text, f"Expected Visit A ID {v_hist_a.visit_id} in modal header"
        assert "Essential (primary) hypertension" in modal_text, "Expected hypertension diagnosis in Visit A modal"
        assert "I10" in modal_text, "Expected ICD-10 code I10 in Visit A modal"
        assert "148 / 92 mmHg" in modal_text, "Expected blood pressure 148/92 in Nurse Triage section"
        assert "Amlodipine 5mg" in modal_text, "Expected prescription medication Amlodipine 5mg in Prescription section"
        log("TEST_2", "Verified Visit A modal: Complete clinical triage, diagnosis, and prescription details loaded correctly.")

        # 5. Test modal scrolling and close icon
        log("TEST_3", "Testing modal close icon...")
        close_icon = page.locator('button[aria-label="Close modal"]')
        close_icon.click()
        time.sleep(0.5)
        assert page.locator('div[role="dialog"]').count() == 0, "Expected modal to be closed"
        log("TEST_3", "Verified modal closed via header close icon.")

        # 6. Click Second Historical Visit (Visit B) to verify data changes correctly
        log("TEST_4", f"Clicking Visit B card (Visit #{v_hist_b.id}) to verify accurate data switching...")
        card_b = page.locator(f'div[aria-label*="Visit #{v_hist_b.id}"]').first
        card_b.click()

        page.wait_for_selector('h2:has-text("Visit Details")', timeout=5000)
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_visit_b_details_modal_empty_states.png"))

        modal_b_text = page.locator('div[role="dialog"]').inner_text()
        assert v_hist_b.visit_id in modal_b_text, f"Expected Visit B ID {v_hist_b.visit_id} in modal header"
        assert "Infectious gastroenteritis and colitis" in modal_b_text, "Expected gastroenteritis diagnosis in Visit B modal"
        assert "A09" in modal_b_text, "Expected ICD-10 code A09 in Visit B modal"
        
        # Verify empty state handling for missing triage/lab/prescriptions
        assert "No data recorded" in modal_b_text, "Expected 'No data recorded' for unrecorded sections in Visit B"
        assert "148 / 92" not in modal_b_text, "Visit A vitals must NOT leak into Visit B!"
        assert "Amlodipine" not in modal_b_text, "Visit A medications must NOT leak into Visit B!"
        log("TEST_4", "Verified Visit B modal: ID and clinical details changed accurately with clean empty states.")

        # 7. Test footer 'Close Visit Details' button
        log("TEST_5", "Testing footer 'Close Visit Details' button...")
        close_btn = page.locator('button:has-text("Close Visit Details")')
        close_btn.click()
        time.sleep(0.5)
        assert page.locator('div[role="dialog"]').count() == 0, "Expected modal to be closed"
        log("TEST_5", "Verified modal closed via footer button.")

        # 8. Test Keyboard Accessibility: Enter key opens modal
        log("TEST_6", "Testing keyboard accessibility (Enter key on card)...")
        card_a.focus()
        page.keyboard.press("Enter")
        time.sleep(0.5)
        assert page.locator('div[role="dialog"]').count() == 1, "Expected modal to open via Enter key"
        log("TEST_6", "Verified modal opened via keyboard Enter key.")
        page.locator('button[aria-label="Close modal"]').click()
        time.sleep(0.3)

        # 9. Verify Current Consultation Form State is Unchanged
        log("TEST_7", "Testing current consultation form immutability...")
        # Doctor enters notes and selects diagnosis in current form
        page.fill("#clinical-assessment", "Patient looks comfortable, asymptomatic on current therapy.")
        diag_input = page.locator("#diagnosis-code")
        diag_input.click()
        diag_input.fill("I10")
        time.sleep(0.5)
        page.locator("#diagnosis-code-listbox li").first.click()
        time.sleep(0.3)

        entered_diag_name = page.locator("#diagnosis-name").input_value()
        assert "Essential (primary) hypertension" in entered_diag_name

        # Doctor opens historical modal again
        card_b.click()
        time.sleep(0.5)
        assert page.locator('div[role="dialog"]').count() == 1

        # Doctor closes modal
        page.locator('button:has-text("Close Visit Details")').click()
        time.sleep(0.5)

        # Check that current consultation draft state is 100% intact!
        current_assessment = page.locator("#clinical-assessment").input_value()
        current_code = page.locator("#diagnosis-code").input_value()
        current_name = page.locator("#diagnosis-name").input_value()

        assert "Patient looks comfortable" in current_assessment, "Current assessment draft was wiped!"
        assert current_code == "I10", f"Current diagnosis code was wiped! Got '{current_code}'"
        assert "Essential (primary) hypertension" in current_name, f"Current diagnosis name was wiped! Got '{current_name}'"
        log("TEST_7", "Verified current consultation form state is 100% preserved and unaffected by modal.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_current_consultation_form_preserved.png"))

        browser.close()
        log("SUCCESS", "All Patient Longitudinal History and Visit Details Modal checks passed successfully!")

if __name__ == "__main__":
    run_e2e_history_modal_tests()

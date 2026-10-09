"""
Playwright Browser Validation: Clickable Patient Timeline & Role-Based Visit Detail Modals
Validates:
1. FRONT_DESK_OFFICER sees clickable timeline entries for "Clinic Visit (#9)" and "Patient Registered".
2. FRONT_DESK_OFFICER clicks "Clinic Visit (#9)" -> Visit Details modal opens.
3. FRONT_DESK_OFFICER can view Patient/Visit demographics, OPD token, and status history.
4. FRONT_DESK_OFFICER cannot view clinical triage, consultation notes, diagnosis, prescriptions, or lab results (privacy banner shown).
5. FRONT_DESK_OFFICER clicks "Patient Registered" -> Registration / Intake details modal opens with real demographics.
6. DOCTOR logs in, clicks "Clinic Visit (#9)" -> opens Visit Details modal with full authorized clinical consultation, diagnosis [E11], and treatment plan.
7. User can also open the Visit Details modal from the Visits tab table.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_timeline_visit_details")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -------------------------------------------------------------
        # STEP 1: LOGIN AS FRONT_DESK_OFFICER
        # -------------------------------------------------------------
        log("STEP 1", "Logging in as FRONT_DESK_OFFICER (e2e_compounder_user)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "e2e_compounder_user")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/patients" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("STEP 1", f"Logged in. Current URL: {page.url}")

        # -------------------------------------------------------------
        # STEP 2: OPEN PATIENT 173 (ARUN KUMAR)
        # -------------------------------------------------------------
        log("STEP 2", "Navigating to /patients/173...")
        page.goto(f"{BASE_URL}/patients/173")
        page.wait_for_selector("div.pb-12", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Check patient header
        assert "Arun Kumar" in page.content(), "Expected patient Arun Kumar to be visible"
        assert "NC-KA-2026-0001" in page.content(), "Expected patient ID NC-KA-2026-0001"

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_patient_overview_timeline.png"))
        log("STEP 2", "Patient detail loaded successfully.")

        # -------------------------------------------------------------
        # STEP 3: CLICK "Clinic Visit (#9)" TIMELINE ENTRY
        # -------------------------------------------------------------
        log("STEP 3", "Clicking 'Clinic Visit (#9)' timeline entry...")
        visit_entry = page.locator('div:has-text("Clinic Visit (#9)")').last
        visit_entry.click()
        time.sleep(1)

        # Verify Visit Details modal opens
        page.wait_for_selector('h2:has-text("Visit Details")', timeout=5000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_front_desk_visit_details_modal.png"))
        log("STEP 3", "Verified: Visit Details modal opened successfully!")

        modal_text = page.locator('div.max-w-4xl').inner_text()

        # Check Section 1: Patient / Visit
        assert "Arun Kumar" in modal_text, "Expected Patient Name in modal"
        assert "GENERAL OPD" in modal_text or "General OPD" in modal_text, "Expected Visit Type in modal"
        assert "COMPLETED" in modal_text, "Expected Visit Status in modal"

        # Check Section 2: OPD / Queue
        assert "Token #9" in modal_text, "Expected Token #9 in modal"

        # Check Section 3, 4, 5, 6, 7: Front Desk Privacy Notices
        assert "Clinical triage vitals are restricted to authorized clinical staff" in modal_text, "Expected Triage privacy notice for Front Desk"
        assert "Doctor clinical consultation records, diagnoses, and examination notes are restricted" in modal_text, "Expected Doctor consultation privacy notice for Front Desk"
        assert "Diagnostic laboratory investigations and specimen results are restricted" in modal_text, "Expected Lab privacy notice for Front Desk"
        assert "Prescription medication orders are restricted" in modal_text, "Expected Prescription privacy notice for Front Desk"
        assert "Pharmacy dispensing records are restricted" in modal_text, "Expected Pharmacy privacy notice for Front Desk"

        # Check that clinical diagnosis and doctor examination notes are NOT leaked to Front Desk
        assert "E11" not in modal_text, "Diagnosis code E11 must NOT be exposed to Front Desk Officer"
        assert "Type 2 Diabetes Mellitus" not in modal_text, "Diagnosis name must NOT be exposed to Front Desk Officer"

        log("STEP 3", "Verified: Front Desk RBAC is strictly enforced in Visit Details modal.")

        # Close the modal
        page.click('button:has-text("Close Visit Details")')
        time.sleep(0.5)
        assert page.locator('h2:has-text("Visit Details")').count() == 0, "Modal should close"

        # -------------------------------------------------------------
        # STEP 4: CLICK "Patient Registered" TIMELINE ENTRY
        # -------------------------------------------------------------
        log("STEP 4", "Clicking 'Patient Registered' timeline entry...")
        reg_entry = page.locator('div:has-text("Patient Registered")').last
        reg_entry.click()
        time.sleep(1)

        # Verify Registration Details modal opens
        page.wait_for_selector('h2:has-text("Patient Registration & Intake Record")', timeout=5000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_patient_registration_modal.png"))
        log("STEP 4", "Verified: Registration Details modal opened successfully!")

        reg_modal_text = page.locator('div.max-w-2xl').inner_text()
        assert "Arun Kumar" in reg_modal_text, "Expected patient name in registration modal"
        assert "NC-KA-2026-0001" in reg_modal_text, "Expected patient ID in registration modal"
        assert "9800010001" in reg_modal_text, "Expected mobile number in registration modal"
        assert "ABHA-DEMO-0001" in reg_modal_text, "Expected ABHA ID in registration modal"
        assert ("General Population" in reg_modal_text or "General BPL" in reg_modal_text), "Expected vulnerability in registration modal"

        # Close registration modal
        page.click('button:has-text("Close Details")')
        time.sleep(0.5)
        assert page.locator('h2:has-text("Patient Registration & Intake Record")').count() == 0, "Registration modal should close"

        # -------------------------------------------------------------
        # STEP 5: LOG IN AS DOCTOR AND VERIFY FULL CLINICAL TRANSACTION
        # -------------------------------------------------------------
        log("STEP 5", "Logging out and logging in as DOCTOR (e2e_doctor_user)...")
        context.clear_cookies()
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "e2e_doctor_user")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/patients" in u or "/consultation" in u, timeout=10000)
        page.wait_for_load_state("networkidle")

        log("STEP 5", "Doctor accessing /patients/173...")
        page.goto(f"{BASE_URL}/patients/173")
        page.wait_for_selector("div.pb-12", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Doctor clicks "Clinic Visit (#9)"
        log("STEP 5", "Doctor clicking 'Clinic Visit (#9)' timeline entry...")
        doctor_visit_entry = page.locator('div:has-text("Clinic Visit (#9)")').last
        doctor_visit_entry.click()
        time.sleep(1)

        page.wait_for_selector('h2:has-text("Visit Details")', timeout=5000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_doctor_visit_details_clinical.png"))

        doctor_modal_text = page.locator('div.max-w-4xl').inner_text()

        # Doctor must see Doctor Consultation & Clinical Diagnosis
        assert "Type 2 Diabetes Mellitus" in doctor_modal_text, "Doctor must see diagnosis name"
        assert "E11" in doctor_modal_text, "Doctor must see ICD diagnosis code E11"
        assert "Oral hydration, rest, symptomatic relief" in doctor_modal_text, "Doctor must see clinical treatment plan"
        assert "No data recorded" in doctor_modal_text, "Doctor must see 'No data recorded' for empty lab/triage sections without crash"

        log("STEP 5", "Verified: Doctor has full authorized clinical access to consultation, diagnosis, and treatment plan.")

        # Close modal
        page.click('button:has-text("Close Visit Details")')
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 6: VERIFY OPENING FROM VISITS TAB
        # -------------------------------------------------------------
        log("STEP 6", "Doctor switching to Visits tab...")
        page.locator('button:has-text("Visits")').first.click()
        time.sleep(1)

        page.wait_for_selector('table', timeout=5000)
        log("STEP 6", "Clicking 'View Details' action on visit row...")
        page.locator('button:has-text("View Details")').first.click()
        time.sleep(1)

        page.wait_for_selector('h2:has-text("Visit Details")', timeout=5000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_visits_tab_modal_open.png"))
        assert "Type 2 Diabetes Mellitus" in page.locator('div.max-w-4xl').inner_text()

        log("STEP 6", "Verified: Opening Visit Details from Visits tab succeeded!")

        browser.close()
        log("SUCCESS", "All browser checks passed perfectly!")

if __name__ == "__main__":
    run_test()

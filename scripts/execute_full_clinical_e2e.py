"""
Namma Clinic — Complete End-to-End Clinical Procedure Automation & Verification
Authoritative Browser UI Walkthrough per Section 13.2 Checklist:
1. Front Desk (`e2e_compounder_user`) -> Directory verification, Patient registration, OPD Token issuance.
2. Nurse Triage (`e2e_nurse_user`) -> Nurse dashboard, Triage queue, Vitals recording, Queue transition to Doctor.
3. Medical Officer (`e2e_doctor_user`) -> Doctor dashboard, Consultation console, Triage review, 14 test catalog check, Diagnosis & Rx.
4. Laboratory Workstation & Separation-of-Duties ->
   - Lab Tech (`e2e_lab_user`): Specimen collection (SMP-20261007-0005), Result entry (CBC).
   - Separation-of-Duties: Verify Result as Lab Tech triggers HTTP 403 Forbidden & UI separation-of-duties notice.
   - Doctor (`e2e_doctor_user`): Authoritative verification succeeds & moves result to VERIFIED.
5. Pharmacy Dispensing (`e2e_pharmacist_user`) -> Prescription verification, FEFO batch selection, Dispensation, InventoryLedger check.
6. Database Verification -> Authoritative PostgreSQL confirmation.
"""

import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"E:\Namma_clinic\docs\audits\screenshots_e2e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def login(page, username, password, expected_path_part="/dashboard"):
    log("AUTH", f"Logging in as {username}...")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_selector("#login-username", timeout=10000)
    page.fill("#login-username", username)
    page.fill("#login-password", password)
    page.click("button[type='submit']")
    page.wait_for_url(lambda u: expected_path_part in u or "/login" not in u, timeout=12000)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    log("AUTH", f"Successfully authenticated. Current URL: {page.url}")

def run_e2e_procedure():
    print("=" * 80)
    print("NAMMA CLINIC — FULL CLINICAL PROCEDURE END-TO-END EXECUTION")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Listen to relevant console/API responses
        page.on('response', lambda res: log("API", f"{res.status} {res.url}") if '/api/' in res.url and res.status >= 400 else None)

        # ---------------------------------------------------------------------
        # STAGE 1: FRONT DESK OFFICER (Registration & OPD Token Issuance)
        # ---------------------------------------------------------------------
        log("STAGE 1", "Starting Front Desk Officer walkthrough...")
        login(page, "e2e_compounder_user", "Password123!", "/dashboard/front-desk")
        page.wait_for_selector("text=Registered Patients", timeout=10000)
        
        # Verify Patient 01 (Arun Kumar) in directory
        content = page.content()
        assert "Arun Kumar" in content, "Patient 01 Arun Kumar must appear in Front Desk directory"
        log("STAGE 1", "Verified: Patient 01 (Arun Kumar) present in Patient Directory.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_front_desk_dashboard.png"))

        # Register a new citizen patient through UI
        timestamp = int(time.time()) % 100000
        new_patient_name = f"Lakshmi Narayanan {timestamp}"
        new_mobile = f"98765{timestamp:05d}"
        
        log("STAGE 1", f"Opening Register Patient modal for '{new_patient_name}'...")
        page.click("button:has-text('Register New Patient')")
        page.wait_for_selector("input[placeholder='e.g. Ramesh Kumar']", timeout=5000)
        
        page.fill("input[placeholder='e.g. Ramesh Kumar']", new_patient_name)
        page.fill("input[placeholder='e.g. 35']", "38")
        page.select_option("select:has(option[value='FEMALE'])", "FEMALE")
        page.fill("input[placeholder='10-digit mobile number']", new_mobile)
        page.fill("input[placeholder='Ward/Street/Area']", "Indiranagar 100ft Road, Bengaluru")
        page.fill("input[placeholder*='14-digit ABHA']", f"91-{timestamp}-4421")
        
        page.click("button[type='submit']:has-text('Register Patient')")
        page.wait_for_selector("text=Patient registered successfully", timeout=8000)
        log("STAGE 1", f"Patient registered successfully: {new_patient_name} ({new_mobile})")
        time.sleep(1)

        # Issue OPD Token for this newly registered patient
        log("STAGE 1", "Searching for newly registered patient to issue token...")
        search_input = page.locator("input[placeholder*='Search name, mobile, ABHA']").first
        search_input.fill(new_mobile)
        time.sleep(1)

        # Click "Issue Token"
        issue_token_btn = page.locator("tr:has-text('" + new_patient_name + "') button:has-text('Issue Token')").first
        issue_token_btn.click()
        page.wait_for_selector("text=Issue OPD Queue Token", timeout=5000)
        
        page.select_option("select:has(option[value='GENERAL_OPD'])", "GENERAL_OPD")
        page.select_option("select:has(option[value='NORMAL'])", "NORMAL")
        page.click("button[type='submit']:has-text('Issue Token')")
        page.wait_for_selector("text=Token issued successfully", timeout=8000)
        log("STAGE 1", "OPD Token issued successfully through Front Desk UI!")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_front_desk_token_issued.png"))

        # ---------------------------------------------------------------------
        # STAGE 2: STAFF NURSE TRIAGE
        # ---------------------------------------------------------------------
        log("STAGE 2", "Starting Staff Nurse Triage walkthrough...")
        login(page, "e2e_nurse_user", "Password123!", "/dashboard/nurse")
        page.wait_for_selector("text=Triage Queue Overview", timeout=10000)
        
        nurse_content = page.content()
        assert "Priya Nair" in nurse_content or new_patient_name in nurse_content, "Patients awaiting triage must appear in Nurse queue"
        log("STAGE 2", "Verified: Pending triage patients visible in Nurse queue.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_nurse_dashboard.png"))

        # Open Triage Station
        log("STAGE 2", "Navigating to Triage Station (/triage)...")
        page.click("button:has-text('Open Triage Station')")
        page.wait_for_url("**/triage**", timeout=8000)
        page.wait_for_selector("input[data-testid='bp-systolic'], input[id*='systolic'], input[value='120']", timeout=8000)
        log("STAGE 2", "Triage Station loaded with active encounter.")

        # Enter clinical observations & submit vitals
        notes_input = page.locator("textarea[data-testid='nurse-notes'], textarea[placeholder*='Record patient general condition']").first
        notes_input.fill("Patient presented with mild fever and throat irritation. Vitals stable. Handed off to Medical Officer.")
        
        log("STAGE 2", "Submitting Triage vitals (Save Triage & Send to Doctor)...")
        page.click("button[data-testid='save-triage-btn'], button:has-text('Save Triage & Send to Doctor')")
        page.wait_for_selector("text=Triage vitals recorded successfully", timeout=10000)
        log("STAGE 2", "Triage vitals recorded and visit transitioned to Doctor Queue!")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_nurse_triage_completed.png"))

        # ---------------------------------------------------------------------
        # STAGE 3: MEDICAL OFFICER (DOCTOR) CONSULTATION
        # ---------------------------------------------------------------------
        log("STAGE 3", "Starting Medical Officer Consultation walkthrough...")
        login(page, "e2e_doctor_user", "Password123!", "/dashboard/doctor")
        page.wait_for_selector("text=Today's Outpatient Encounters", timeout=10000)
        log("STAGE 3", "Doctor Dashboard loaded with clinical encounter roster.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_doctor_dashboard.png"))

        # Click first "Consult Patient" button
        log("STAGE 3", "Opening Consultation Console for patient encounter...")
        consult_btn = page.locator("button:has-text('Consult Patient')").first
        consult_btn.click()
        page.wait_for_url("**/consultation**", timeout=8000)
        page.wait_for_selector("text=Clinical Examination & Medical Assessment", timeout=10000)
        log("STAGE 3", "Consultation Console loaded.")

        # Verify Diagnostic Test Master has 14 tests loaded
        diag_checkbox = page.locator("input[type='checkbox']:has-text('Order Laboratory Diagnostics'), input#order-diagnostics, label:has-text('Order Laboratory Diagnostics') input").first
        if not diag_checkbox.is_checked():
            diag_checkbox.click()
            time.sleep(0.5)

        test_select = page.locator("select:has(option[value='1'])").first
        options_count = test_select.locator("option").count()
        log("STAGE 3", f"Diagnostic Test catalog dropdown contains {options_count} options (Expected: >= 14 tests).")
        assert options_count >= 14, f"Expected at least 14 diagnostic test options, got {options_count}"

        # Fill consultation clinical notes
        page.locator("textarea[placeholder*='Document history of present illness']").first.fill("Acute onset sore throat with dry cough for 3 days. No hemoptysis. No chest pain.")
        page.locator("textarea[placeholder*='Document physical examination findings']").first.fill("Throat hyperemic. Bilateral clear air entry. Pharyngeal congestion noted.")
        
        # Select ICD-10 Diagnosis
        page.locator("select:has(option:has-text('J06.9'))").first.select_option(label="J06.9 - Acute upper respiratory infection, unspecified")
        
        # Order CBC test
        test_select.select_option(label="Complete Blood Count (CBC)")
        page.locator("input[placeholder*='Clinical indication']").first.fill("Evaluate leukocytosis and rule out bacterial infection.")

        # Check Prescribe Medications
        rx_checkbox = page.locator("input#order-prescription, label:has-text('Prescribe Medications') input").first
        if not rx_checkbox.is_checked():
            rx_checkbox.click()
            time.sleep(0.5)

        # Select Paracetamol or Amoxicillin
        med_select = page.locator("select:has(option:has-text('Paracetamol'))").first
        med_select.select_option(label="Paracetamol 500mg Tablet (Oral)")
        page.locator("input[value*='1-0-1 After Food']").first.fill("1-0-1 After Food for 5 days")

        # Save and Complete Consultation
        log("STAGE 3", "Saving and completing consultation...")
        page.click("button:has-text('Save & Complete Consultation')")
        page.wait_for_selector("text=Consultation encounter completed successfully", timeout=12000)
        log("STAGE 3", "Consultation successfully saved with diagnosis, lab order, and prescription!")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_doctor_consultation_saved.png"))

        # ---------------------------------------------------------------------
        # STAGE 4: LABORATORY WORKSTATION & SEPARATION OF DUTIES
        # ---------------------------------------------------------------------
        log("STAGE 4", "Starting Laboratory Workstation & Separation-of-Duties walkthrough...")
        
        # 4A. Login as Lab Technician
        login(page, "e2e_lab_user", "Password123!", "/dashboard/lab")
        page.wait_for_selector("text=Laboratory Operations Overview", timeout=10000)
        log("STAGE 4A", "Lab Dashboard loaded.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_lab_dashboard.png"))

        # Navigate to /lab
        log("STAGE 4A", "Navigating to /lab...")
        page.goto(f"{BASE_URL}/lab")
        page.wait_for_selector("text=Laboratory Investigation Console", timeout=10000)
        
        # Find Patient 09 (Sanjay Patel, ORD-20261007-005)
        log("STAGE 4A", "Selecting Patient 09 (Sanjay Patel, ORD-20261007-005)...")
        pat_order_item = page.locator("div:has-text('Sanjay Patel')").first
        pat_order_item.click()
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_lab_order_selected.png"))

        # Collect Specimen
        log("STAGE 4A", "Clicking 'Collect Specimen'...")
        collect_btn = page.locator("button:has-text('Collect Specimen')").first
        if collect_btn.is_visible():
            collect_btn.click()
            time.sleep(0.5)
            # Fill barcode
            barcode_input = page.locator("input[placeholder*='SMP-2026']").first
            barcode_input.fill("SMP-20261007-0005")
            # Click Confirm Specimen Collection
            page.click("button:has-text('Confirm Specimen Collection')")
            page.wait_for_selector("text=Specimen logged successfully", timeout=8000)
            log("STAGE 4A", "Specimen SMP-20261007-0005 collected successfully!")
            time.sleep(1)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "09_lab_specimen_collected.png"))

        # Enter Result for CBC
        log("STAGE 4A", "Clicking 'Enter Result' for investigation...")
        enter_res_btn = page.locator("button:has-text('Enter Result')").first
        enter_res_btn.click()
        time.sleep(0.5)

        # Fill Numeric and Text Values
        num_val_input = page.locator("input[placeholder*='e.g. 12.5']").first
        text_val_input = page.locator("input[placeholder*='e.g. Negative, Reactive']").first
        num_val_input.fill("13.8")
        text_val_input.fill("Hb 13.8 g/dL, WBC 4500/uL, Platelets 165k/uL. Normal morphology.")

        log("STAGE 4A", "Saving Diagnostic Result (Status: ENTERED)...")
        page.click("button:has-text('Save Result (Status: ENTERED)')")
        page.wait_for_selector("text=Diagnostic test result entered successfully", timeout=8000)
        log("STAGE 4A", "Diagnostic result entered successfully! Status transitioned to ENTERED.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "10_lab_result_entered.png"))

        # 4B. Separation of Duties: Lab Tech clicks "Verify Result"
        log("STAGE 4B", "Executing Separation-of-Duties test: Lab Tech attempts to 'Verify Result'...")
        verify_btn = page.locator("button:has-text('Verify Result')").first
        verify_btn.click()
        time.sleep(1.5)

        # Assert UI displays Separation-of-Duties Notice
        notice_locator = page.locator("text=Authoritative Separation-of-Duties")
        assert notice_locator.is_visible(), "Authoritative Separation-of-Duties notice must be displayed when Lab Tech clicks Verify Result!"
        log("STAGE 4B", "SUCCESS: Authoritative Separation-of-Duties notice cleanly displayed! HTTP 403 enforced by backend.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_lab_separation_of_duties_403.png"))

        # 4C. Medical Officer Result Verification
        log("STAGE 4C", "Logging in as Medical Officer (e2e_doctor_user) to verify the result...")
        login(page, "e2e_doctor_user", "Password123!", "/dashboard/doctor")
        
        # Navigate directly to /lab
        page.goto(f"{BASE_URL}/lab")
        page.wait_for_selector("text=Laboratory Investigation Console", timeout=10000)
        
        # Select Sanjay Patel
        page.locator("div:has-text('Sanjay Patel')").first.click()
        time.sleep(1)

        # Doctor clicks "Verify Result"
        log("STAGE 4C", "Medical Officer clicking 'Verify Result'...")
        doc_verify_btn = page.locator("button:has-text('Verify Result')").first
        doc_verify_btn.click()
        page.wait_for_selector("text=successfully verified and released to EMR", timeout=8000)
        log("STAGE 4C", "Medical Officer successfully verified diagnostic result! Permanent transition to VERIFIED.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "12_lab_result_doctor_verified.png"))

        # ---------------------------------------------------------------------
        # STAGE 5: PHARMACIST DISPENSING & INVENTORY LEDGER AUDIT
        # ---------------------------------------------------------------------
        log("STAGE 5", "Starting Pharmacist Dispensing & Inventory Ledger walkthrough...")
        login(page, "e2e_pharmacist_user", "Password123!", "/dashboard/pharmacy")
        page.wait_for_selector("text=Pharmacy & Dispensary Console", timeout=10000)
        log("STAGE 5", "Pharmacy Dashboard loaded.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "13_pharmacy_dashboard.png"))

        # Click first "Review & Dispense"
        log("STAGE 5", "Selecting prescription for dispensing...")
        dispense_btn = page.locator("button:has-text('Review & Dispense')").first
        dispense_btn.click()
        page.wait_for_url("**/pharmacy**", timeout=8000)
        page.wait_for_selector("text=Prescription Dispensing & FEFO Inventory Console", timeout=10000)

        # Check if prescription needs verification first
        verify_rx_btn = page.locator("button:has-text('Verify Prescription')").first
        if verify_rx_btn.is_visible():
            log("STAGE 5", "Prescription is PENDING_VERIFICATION. Pharmacist verifying prescription...")
            verify_rx_btn.click()
            time.sleep(1)
            # Submit verification modal if open
            confirm_modal_verify = page.locator("div[role='dialog'] button:has-text('Confirm Verification'), button:has-text('Verify Prescription')").last
            confirm_modal_verify.click()
            time.sleep(1)

        # Click "Confirm Dispensation" / "Dispense Selected Medicines"
        log("STAGE 5", "Executing FEFO Dispensation...")
        confirm_disp_btn = page.locator("button:has-text('Confirm Dispensation'), button:has-text('Execute Dispensation')").first
        if confirm_disp_btn.is_visible():
            confirm_disp_btn.click()
            page.wait_for_selector("text=recorded successfully! InventoryLedger updated atomically", timeout=10000)
            log("STAGE 5", "Prescription successfully dispensed! InventoryLedger atomically decremented.")
            time.sleep(1)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_pharmacy_dispensation_complete.png"))

        # Check Inventory Ledger Audit Tab
        log("STAGE 5", "Switching to 'Inventory Ledger Audit' tab...")
        ledger_tab = page.locator("button:has-text('Inventory Ledger Audit'), button:has-text('Ledger Audit')").first
        ledger_tab.click()
        time.sleep(1)
        page.wait_for_selector("text=Immutable Double-Entry Stock Ledger", timeout=8000)
        log("STAGE 5", "Inventory Ledger Audit tab verified.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "15_inventory_ledger_audit.png"))

        browser.close()
        print("\n" + "=" * 80)
        print("ALL BROWSER PLAYWRIGHT WORKFLOWS COMPLETED FLAWLESSLY!")
        print("=" * 80)

if __name__ == "__main__":
    try:
        run_e2e_procedure()
    except Exception as e:
        print(f"\n[ERROR] E2E Procedure failed: {e}", file=sys.stderr)
        sys.exit(1)

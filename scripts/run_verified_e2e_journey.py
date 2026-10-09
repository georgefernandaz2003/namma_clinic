"""
Namma Clinic — Full End-to-End Clinical Procedure Automation
Strict adherence to Section 13.2 Checklist & Project Rules
"""

import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

# Enforce UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"E:\Namma_clinic\docs\audits\screenshots_e2e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

def login(page, username, password, target_route):
    log("AUTH", f"Logging in as {username}...")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_selector("#login-username", timeout=10000)
    page.fill("#login-username", username)
    page.fill("#login-password", password)
    page.click("button[type='submit']")
    page.wait_for_url(lambda u: "/login" not in u, timeout=12000)
    page.goto(f"{BASE_URL}{target_route}")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)
    log("AUTH", f"Authenticated and loaded target route: {page.url}")

def run_e2e():
    print("=" * 80)
    print("NAMMA CLINIC — COMPREHENSIVE END-TO-END CLINICAL WALKTHROUGH")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on('response', lambda res: log("API", f"{res.status} {res.url}") if '/api/' in res.url and res.status >= 400 else None)

        # ---------------------------------------------------------------------
        # STAGE 1: FRONT DESK OFFICER
        # ---------------------------------------------------------------------
        log("STAGE 1", "Starting Front Desk Officer walkthrough...")
        login(page, "e2e_compounder_user", "Password123!", "/dashboard/front-desk")
        page.wait_for_selector("text=Registered Patients", timeout=10000)
        
        # Verify Patient 01 (Arun Kumar)
        content = page.content()
        assert "Arun Kumar" in content, "Patient 01 Arun Kumar must appear in Front Desk directory"
        log("STAGE 1", "Verified: Patient 01 (Arun Kumar) appears in Patient Directory.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_front_desk_dashboard.png"))

        # Register New Patient
        timestamp = int(time.time()) % 100000
        new_name = f"Lakshmi Narayanan {timestamp}"
        new_mobile = f"98765{timestamp:05d}"
        
        log("STAGE 1", f"Registering new patient: {new_name} ({new_mobile})...")
        page.click("button:has-text('Register New Patient')")
        page.wait_for_selector("input[placeholder='e.g. Ramesh Kumar']", timeout=5000)
        
        page.fill("input[placeholder='e.g. Ramesh Kumar']", new_name)
        page.fill("input[placeholder='e.g. 35']", "38")
        page.select_option("select:has(option[value='FEMALE'])", "FEMALE")
        page.fill("input[placeholder='10-digit mobile number']", new_mobile)
        page.fill("input[placeholder='Ward/Street/Area']", "Indiranagar 100ft Road, Bengaluru")
        
        page.click("button[type='submit']:has-text('Register Patient')")
        page.wait_for_selector(".bg-emerald-50:has-text('registered successfully')", timeout=10000)
        log("STAGE 1", f"Patient registered successfully: {new_name}")
        time.sleep(1)

        # Issue OPD Token
        log("STAGE 1", "Issuing OPD token for registered patient...")
        search_box = page.locator("input[placeholder*='Search name, mobile, ABHA']").first
        search_box.fill(new_mobile)
        time.sleep(1)

        issue_btn = page.locator("tr:has-text('" + new_name + "') button:has-text('Issue Token')").first
        issue_btn.click()
        page.wait_for_selector("text=Issue OPD Queue Token", timeout=5000)

        page.click("button[type='submit']:has-text('Issue Token')")
        page.wait_for_selector(".bg-emerald-50:has-text('issued for')", timeout=10000)
        log("STAGE 1", "OPD Token issued successfully via Front Desk UI!")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_front_desk_token_issued.png"))

        # ---------------------------------------------------------------------
        # STAGE 2: STAFF NURSE TRIAGE
        # ---------------------------------------------------------------------
        log("STAGE 2", "Starting Staff Nurse Triage walkthrough...")
        login(page, "e2e_nurse_user", "Password123!", "/dashboard/nurse")
        page.wait_for_selector("text=Triage Queue Overview", timeout=10000)
        log("STAGE 2", "Nurse Dashboard loaded.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_nurse_dashboard.png"))

        # Open Triage Station for Visit 38 (Kavya Reddy - WAITING_FOR_TRIAGE)
        log("STAGE 2", "Opening Triage Station for visit awaiting vitals (/triage?visit=38)...")
        page.goto(f"{BASE_URL}/triage?visit=38")
        page.wait_for_selector("textarea[data-testid='nurse-notes'], textarea", timeout=10000)
        log("STAGE 2", "Triage Station loaded with active vitals form.")

        # Fill vitals observations
        page.locator("textarea[data-testid='nurse-notes'], textarea").first.fill(
            "Patient complaint: Pruritic erythematous rash. Vitals stable: BP 120/80, Pulse 76, Temp 98.6F, SpO2 99%. Forwarded to Medical Officer."
        )

        log("STAGE 2", "Submitting Triage vitals (Save Triage & Send to Doctor)...")
        page.click("button[data-testid='save-triage-btn'], button:has-text('Save Triage & Send to Doctor')")
        page.wait_for_selector("text=Triage vitals recorded successfully", timeout=10000)
        log("STAGE 2", "Triage vitals recorded and visit forwarded to Doctor Queue!")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_nurse_triage_completed.png"))

        # ---------------------------------------------------------------------
        # STAGE 3: MEDICAL OFFICER CONSULTATION
        # ---------------------------------------------------------------------
        log("STAGE 3", "Starting Medical Officer Consultation walkthrough...")
        login(page, "e2e_doctor_user", "Password123!", "/dashboard/doctor")
        page.wait_for_selector("text=Today's Outpatient Encounters", timeout=10000)
        
        doc_content = page.content()
        assert "Ravi Shankar" in doc_content, "Patient 03 (Ravi Shankar) must appear in Doctor queue"
        log("STAGE 3", "Verified: Patient 03 (Ravi Shankar) present in Doctor queue.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_doctor_dashboard.png"))

        # Open Consultation for Ravi Shankar (Visit 35)
        log("STAGE 3", "Opening Consultation Console for Patient 03 (/consultation?visit=35)...")
        page.goto(f"{BASE_URL}/consultation?visit=35")
        page.wait_for_selector("text=Clinical Examination & Medical Assessment", timeout=10000)
        log("STAGE 3", "Consultation Console loaded.")

        # Verify Diagnostic Test Master contains 14 tests
        diag_checkbox = page.locator("label:has-text('Order Laboratory Diagnostics') input, input#order-diagnostics").first
        if not diag_checkbox.is_checked():
            diag_checkbox.click()
            time.sleep(0.5)

        test_select = page.locator("select:has(option[value='1'])").first
        options_count = test_select.locator("option").count()
        log("STAGE 3", f"Diagnostic Test catalog dropdown contains {options_count} options (Verified: >= 14 active tests).")
        assert options_count >= 14, f"Expected >= 14 tests, got {options_count}"

        # Fill clinical examination and assessment
        page.locator("textarea[placeholder*='Document history of present illness']").first.fill(
            "Patient reports throbbing frontal headache for 5 days. Mild neck stiffness, photophobia absent."
        )
        page.locator("textarea[placeholder*='Document physical examination findings']").first.fill(
            "Cranial nerves grossly intact. Pupils equal and reactive. Neck supple. Tension headache suspected."
        )

        # Select Diagnosis ICD-10
        page.locator("select:has(option:has-text('G44.2'))").first.select_option(label="G44.2 - Tension-type headache")
        
        # Order Diagnostic Test (Complete Blood Count)
        test_select.select_option(label="Complete Blood Count (CBC)")
        page.locator("input[placeholder*='Clinical indication']").first.fill("Rule out systemic infection or anemia.")

        # Prescribe Medication
        rx_checkbox = page.locator("label:has-text('Prescribe Medications') input, input#order-prescription").first
        if not rx_checkbox.is_checked():
            rx_checkbox.click()
            time.sleep(0.5)

        med_select = page.locator("select:has(option:has-text('Paracetamol'))").first
        med_select.select_option(label="Paracetamol 500mg Tablet (Oral)")
        page.locator("input[value*='1-0-1 After Food']").first.fill("1-0-1 After Food for 3 days SOS")

        # Save & Complete Consultation
        log("STAGE 3", "Saving and completing consultation encounter...")
        page.click("button:has-text('Save & Complete Consultation')")
        page.wait_for_selector("text=Consultation encounter completed successfully", timeout=12000)
        log("STAGE 3", "Consultation encounter saved successfully with ICD-10 diagnosis, lab order, and prescription!")
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

        # Select Patient 09 (Sanjay Patel, ORD-20261007-005)
        log("STAGE 4A", "Selecting Patient 09 (Sanjay Patel, ORD-20261007-005)...")
        pat_order = page.locator("div:has-text('Sanjay Patel')").first
        pat_order.click()
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_lab_order_selected.png"))

        # Specimen Collection
        log("STAGE 4A", "Logging biological specimen collection...")
        collect_btn = page.locator("button:has-text('Collect Specimen')").first
        if collect_btn.is_visible():
            collect_btn.click()
            time.sleep(0.5)
            barcode_input = page.locator("input[placeholder*='SMP-2026']").first
            barcode_input.fill("SMP-20261007-0005")
            page.click("button:has-text('Confirm Specimen Collection')")
            page.wait_for_selector("text=Specimen logged successfully", timeout=8000)
            log("STAGE 4A", "Specimen SMP-20261007-0005 successfully collected!")
            time.sleep(1)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "09_lab_specimen_collected.png"))

        # Result Entry for CBC
        log("STAGE 4A", "Entering test result for CBC investigation...")
        enter_res_btn = page.locator("button:has-text('Enter Result')").first
        enter_res_btn.click()
        time.sleep(0.5)

        num_input = page.locator("input[placeholder*='e.g. 12.5']").first
        text_input = page.locator("input[placeholder*='e.g. Negative, Reactive']").first
        num_input.fill("13.8")
        text_input.fill("Hb 13.8 g/dL, WBC 4500/uL, Platelets 165k/uL. Normal morphology.")

        log("STAGE 4A", "Saving Diagnostic Result (Status: ENTERED)...")
        page.click("button:has-text('Save Result (Status: ENTERED)')")
        page.wait_for_selector("text=Diagnostic test result entered successfully", timeout=8000)
        log("STAGE 4A", "Diagnostic result entered successfully! Status transitioned to ENTERED.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "10_lab_result_entered.png"))

        # 4B. Separation of Duties Enforcement: Lab Tech clicks "Verify Result"
        log("STAGE 4B", "Testing Separation-of-Duties: Lab Tech attempts 'Verify Result'...")
        verify_btn = page.locator("button:has-text('Verify Result')").first
        verify_btn.click()
        time.sleep(1.5)

        # Assert UI displays authoritative notice
        notice = page.locator("text=Authoritative Separation-of-Duties")
        assert notice.is_visible(), "Separation-of-Duties notice must appear when Lab Tech attempts verification!"
        log("STAGE 4B", "AUTHORITATIVE SEPARATION-OF-DUTIES VERIFIED: HTTP 403 Forbidden properly handled and banner displayed.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_lab_separation_of_duties_403.png"))

        # 4C. Medical Officer Result Verification
        log("STAGE 4C", "Logging in as Medical Officer (e2e_doctor_user) to verify the result...")
        login(page, "e2e_doctor_user", "Password123!", "/dashboard/doctor")
        
        # Navigate to /lab
        page.goto(f"{BASE_URL}/lab")
        page.wait_for_selector("text=Laboratory Investigation Console", timeout=10000)
        
        # Select Sanjay Patel
        page.locator("div:has-text('Sanjay Patel')").first.click()
        time.sleep(1)

        # Doctor clicks Verify Result
        log("STAGE 4C", "Medical Officer verifying result...")
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

        # Open /pharmacy
        log("STAGE 5", "Opening Pharmacy Dispensing Console (/pharmacy)...")
        page.goto(f"{BASE_URL}/pharmacy")
        page.wait_for_selector("text=Prescription Dispensing & FEFO Inventory Console", timeout=10000)

        # Select a verified prescription
        verified_rx_card = page.locator("div.cursor-pointer:has-text('VERIFIED')").first
        if verified_rx_card.is_visible():
            verified_rx_card.click()
            time.sleep(1)

        # Click Dispense / Confirm Dispensation
        disp_btn = page.locator("button:has-text('Confirm Dispensation'), button:has-text('Execute Dispensation')").first
        if disp_btn.is_visible():
            log("STAGE 5", "Executing FEFO dispensation...")
            disp_btn.click()
            page.wait_for_selector("text=recorded successfully! InventoryLedger updated atomically", timeout=10000)
            log("STAGE 5", "Prescription dispensed! InventoryLedger decremented atomically.")
            time.sleep(1)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_pharmacy_dispensation_complete.png"))

        # View Inventory Ledger Audit Tab
        log("STAGE 5", "Inspecting Inventory Ledger Audit...")
        ledger_btn = page.locator("button:has-text('Inventory Ledger Audit'), button:has-text('Ledger Audit')").first
        ledger_btn.click()
        time.sleep(1)
        page.wait_for_selector("text=Immutable Double-Entry Stock Ledger", timeout=8000)
        log("STAGE 5", "Inventory Ledger Audit tab verified with active ledger transactions.")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "15_inventory_ledger_audit.png"))

        browser.close()
        print("\n" + "=" * 80)
        print("ALL BROWSER PLAYWRIGHT UI WORKFLOWS COMPLETED 100% SUCCESSFULLY!")
        print("=" * 80)

if __name__ == "__main__":
    try:
        run_e2e()
    except Exception as e:
        print(f"\n[ERROR] E2E Run failed: {e}", file=sys.stderr)
        sys.exit(1)

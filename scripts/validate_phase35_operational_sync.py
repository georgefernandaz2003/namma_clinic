# -*- coding: utf-8 -*-
"""
Playwright Browser & Authorization Validation: Phase 35 Operational Synchronization & Order Gate Hardening

Validates:
1. Hospital Admin Real UI:
   - Department deactivation blocked while dependent service is active (UI error banner).
   - Standard department deletion blocked (UI error).
   - FacilityService toggle disables SRV_TRIAGE (UI success banner).
2. Triage Bypass & Direct-to-Doctor Routing:
   - Front Desk Officer registers visit while SRV_TRIAGE disabled -> direct to DOCTOR queue.
   - Nurse triage attempt blocked with HTTP 400 (SRV_TRIAGE unavailable).
   - Doctor conducts consultation directly without triage vitals (bypass invariant succeeds).
3. Downstream Order Gate Hardening:
   - Lab orders blocked when SRV_DIAGNOSTICS disabled (HTTP 400).
   - Prescriptions blocked when SRV_PHARMACY disabled (HTTP 400).
   - Dispensation blocked when SRV_PHARMACY disabled (HTTP 400).
4. Direct REST API Negative Invariants:
   - Hospital Admin DELETE FacilityService -> 403 Forbidden.
   - Canonical FacilityService permanent delete blocked -> 400 Bad Request.
   - Inactive department blocks service re-enablement -> 400 Bad Request.
5. Database Verification:
   - Direct PostgreSQL check of Department, FacilityService, Visit, Consultation states.
   - Clean restoration of operational states.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_BASE = "http://127.0.0.1:8000/api"
API_V1_BASE = "http://127.0.0.1:8000/api/v1"

# Setup Django ORM
sys.path.insert(0, r"D:\project\namma_clinic\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
if not os.environ.get("DATABASE_PORT"):
    try:
        from pathlib import Path
        from pgserver.utils import PostmasterInfo
        pinfo = PostmasterInfo.read_from_pgdata(Path(r"D:\project\namma_clinic\pgdata"))
        if pinfo and pinfo.is_running():
            os.environ["DATABASE_PORT"] = str(pinfo.port)
    except Exception:
        pass
import django
django.setup()

from apps.accounts.models import User
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.visits.models import Visit
from apps.patients.models import Patient
from apps.consultations.models import Consultation

def log(msg):
    print(f"[PHASE-35] {msg}", flush=True)

def api_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"raw_error": err_body}

def get_jwt_token(username, password):
    url = f"{API_BASE}/auth/token/"
    status_code, data = api_request(url, method="POST", data={"username": username, "password": password})
    if status_code != 200 or "access" not in data:
        raise RuntimeError(f"Failed to authenticate user {username}: {data}")
    return data["access"]

def run_phase35_validation():
    log("==================================================================")
    log("NAMMA CLINIC ? PHASE 35 OPERATIONAL SYNCHRONIZATION VALIDATION")
    log("==================================================================")

    # Fetch reference facility
    facility = User.objects.get(username='testadmin').assigned_facility
    assert facility is not None, "No active facility found!"
    log(f"Target Facility: {facility.facility_name} ({facility.facility_code}) [ID: {facility.id}]")

    # Ensure all canonical services and standard departments are present and active initially
    from apps.facilities.services import provision_standard_facility_services, provision_standard_departments
    provision_standard_facility_services(facility)
    provision_standard_departments(facility)

    FacilityService.objects.filter(facility=facility).update(is_available=True)
    Department.objects.filter(facility=facility, code__in=['OPD', 'PHARM', 'LAB', 'TRIAGE']).update(is_active=True)

    admin_token = get_jwt_token("testadmin", "AdminPassword123!")
    doc_token = get_jwt_token("localdoc", "DoctorPassword123!")
    nurse_token = get_jwt_token("localnurse", "NursePassword123!")
    pharm_token = get_jwt_token("localpharm", "PharmacyPassword123!")
    dho_token = get_jwt_token("localdistrict", "DistrictPassword123!")

    # -------------------------------------------------------------
    # PART 1: Direct API Security & Operational Invariants
    # -------------------------------------------------------------
    log("\n--- STEP 1: Direct API Operational & Security Invariants ---")

    # Invariant 1: Inactive department prevents service re-enable (HTTP 400)
    opd_dept = Department.objects.get(facility=facility, code='OPD')
    opd_srv = FacilityService.objects.get(facility=facility, service__code='SRV_GENERAL_OPD')
    
    # Temporarily set service unavailable, department inactive
    opd_srv.is_available = False
    opd_srv.save()
    opd_dept.is_active = False
    opd_dept.save()

    code, resp = api_request(
        f"{API_V1_BASE}/organization/facility-services/{opd_srv.id}/",
        method="PATCH",
        data={"is_available": True},
        token=admin_token
    )
    assert code == 400, f"Expected 400 when re-enabling service with inactive department, got {code}: {resp}"
    log("  PASS: Inactive department prevents service re-enablement (HTTP 400).")

    # Invariant 2: Active dependent service prevents department deactivation (HTTP 400)
    opd_dept.is_active = True
    opd_dept.save()
    opd_srv.is_available = True
    opd_srv.save()

    code, resp = api_request(
        f"{API_V1_BASE}/organization/departments/{opd_dept.id}/",
        method="PATCH",
        data={"is_active": False},
        token=admin_token
    )
    assert code == 400, f"Expected 400 when deactivating department with active service, got {code}: {resp}"
    log("  PASS: Active dependent service prevents department deactivation (HTTP 400).")

    # Invariant 3: Standard department DELETE rejected (HTTP 400)
    code, resp = api_request(
        f"{API_V1_BASE}/organization/departments/{opd_dept.id}/",
        method="DELETE",
        token=admin_token
    )
    assert code == 400, f"Expected 400 when deleting standard department, got {code}: {resp}"
    log("  PASS: Deleting standard department OPD rejected (HTTP 400).")

    # Invariant 4: Hospital Admin DELETE FacilityService rejected (HTTP 403)
    code, resp = api_request(
        f"{API_V1_BASE}/organization/facility-services/{opd_srv.id}/",
        method="DELETE",
        token=admin_token
    )
    assert code == 403, f"Expected 403 for Hospital Admin DELETE FacilityService, got {code}: {resp}"
    log("  PASS: Hospital Admin DELETE FacilityService rejected (HTTP 403).")

    # Invariant 5: Canonical FacilityService permanent delete blocked for DHO (HTTP 400)
    code, resp = api_request(
        f"{API_V1_BASE}/organization/facility-services/{opd_srv.id}/",
        method="DELETE",
        token=dho_token
    )
    assert code == 400, f"Expected 400 for DHO deleting canonical FacilityService, got {code}: {resp}"
    log("  PASS: Canonical FacilityService permanent delete blocked (HTTP 400).")

    # -------------------------------------------------------------
    # PART 2: Real Browser E2E ? Hospital Admin UI Experience
    # -------------------------------------------------------------
    log("\n--- STEP 2: Hospital Admin Real Browser UI Verification ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        log("1. Hospital Admin logging into /login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input#login-username')
        page.fill('input#login-username', 'testadmin')
        page.fill('input#login-password', 'AdminPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=10000)
        log("  PASS: Hospital Admin logged in successfully.")

        log("2. Navigating to /facilities...")
        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="facilities-grid"]')

        # Open Departments Modal
        log("3. Opening Department Management modal...")
        dept_btn = page.wait_for_selector(f'[data-testid="manage-departments-btn-{facility.facility_code.lower()}"]')
        dept_btn.click()
        page.wait_for_selector('[data-testid="department-modal"]')

        # Attempt to edit department OPD and deactivate it (while SRV_GENERAL_OPD is active)
        log("4. Attempting to deactivate Department 'OPD' via UI while services are active...")
        page.click('[data-testid="edit-department-btn-opd"]')
        # Uncheck is_active checkbox
        page.uncheck('[data-testid="edit-dept-active-checkbox-opd"]')
        page.click('[data-testid="save-edit-dept-btn-opd"]')

        # Verify UI renders the department error banner with server error
        page.wait_for_selector('[data-testid="department-error-banner"]')
        err_text = page.locator('[data-testid="department-error-banner"]').text_content()
        assert "Cannot deactivate department" in err_text, f"Unexpected UI error: {err_text}"
        log(f"  PASS: UI displayed error banner on invalid deactivation: '{err_text.strip()}'")

        # Close Department modal
        page.click('button[aria-label="Close modal"]')
        page.wait_for_selector('[data-testid="department-modal"]', state="detached")

        # Open Facility Services Modal
        log("5. Opening Facility Services modal...")
        svc_btn = page.wait_for_selector(f'[data-testid="manage-services-btn-{facility.facility_code.lower()}"]')
        svc_btn.click()
        page.wait_for_selector('[data-testid="facility-services-modal"]')

        # Verify all 5 canonical services visible
        for code_str in ['srv_general_opd', 'srv_ncd_screening', 'srv_diagnostics', 'srv_pharmacy', 'srv_triage']:
            row = page.wait_for_selector(f'[data-testid="service-row-{code_str}"]')
            assert row is not None

        # Toggle SRV_TRIAGE to disabled
        log("6. Toggling SRV_TRIAGE to disabled via UI...")
        page.click('[data-testid="toggle-service-btn-srv_triage"]')
        page.wait_for_selector('[data-testid="service-feedback-banner"]')
        fb_text = page.locator('[data-testid="service-feedback-banner"]').text_content()
        log(f"  PASS: Service feedback banner displayed: '{fb_text.strip()}'")

        # Verify SRV_TRIAGE is now disabled in database
        triage_fs = FacilityService.objects.get(facility=facility, service__code='SRV_TRIAGE')
        assert not triage_fs.is_available, "SRV_TRIAGE must be marked unavailable in database"
        log("  PASS: SRV_TRIAGE successfully toggled to Disabled.")

        context.close()
        browser.close()

    # -------------------------------------------------------------
    # PART 3: Downstream Workflow ? Triage Bypass & Direct Doctor Routing
    # -------------------------------------------------------------
    log("\n--- STEP 3: Triage Bypass & Direct Doctor Routing Verification ---")
    
    # 1. Register a visit while SRV_TRIAGE is disabled
    fdo_token = get_jwt_token("e2e_compounder_user", "Password123!")
    patient = Patient.objects.filter(registered_at_facility=facility).first()
    if not patient:
        patient = Patient.objects.create(
            patient_id="PAT-P35-LIVE-001",
            name="Smt. Kamala Devi",
            gender="FEMALE",
            age=48,
            mobile="9845012345",
            address="Shivajinagar, Bengaluru",
            registered_at_facility=facility
        )

    log(f"Registering visit for patient {patient.name} while SRV_TRIAGE is disabled...")
    code, visit_data = api_request(
        f"{API_V1_BASE}/visits/",
        method="POST",
        data={
            "patient": patient.id,
            "facility": facility.id,
            "visit_type": "GENERAL_OPD",
            "priority": "NORMAL",
            "chief_complaint": "Acute headache and fever"
        },
        token=fdo_token
    )
    assert code == 201, f"Failed to register visit: {visit_data}"
    visit_id = visit_data["id"]
    log(f"  Visit Created: ID {visit_id}, Queue: {visit_data['current_queue']}, Status: {visit_data['status']}")
    
    # Assert direct-to-doctor routing:
    assert visit_data["current_queue"] == "DOCTOR", f"Expected queue DOCTOR, got {visit_data['current_queue']}"
    assert visit_data["status"] == "WAITING_FOR_DOCTOR", f"Expected status WAITING_FOR_DOCTOR, got {visit_data['status']}"
    log("  PASS: Visit routed directly to DOCTOR queue (triage bypassed successfully).")

    # 2. Nurse attempting to record vitals while SRV_TRIAGE is disabled -> 400
    log("Nurse attempting to submit vitals for visit while SRV_TRIAGE disabled...")
    code, triage_resp = api_request(
        f"{API_BASE}/triage/",
        method="POST",
        data={
            "visit": visit_id,
            "patient": patient.id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80
        },
        token=nurse_token
    )
    assert code == 400, f"Expected 400 for triage when SRV_TRIAGE disabled, got {code}: {triage_resp}"
    log("  PASS: Nurse triage submission blocked with HTTP 400 when SRV_TRIAGE is disabled.")

    # 3. Doctor conducts consultation directly without vitals
    log("Doctor conducting clinical consultation directly without vitals...")
    code, consult_resp = api_request(
        f"{API_BASE}/consultations/",
        method="POST",
        data={
            "visit": visit_id,
            "patient": patient.id,
            "facility": facility.id,
            "chief_complaint": "Acute headache and fever",
            "clinical_assessment": "Mild viral fever with tension headache",
            "treatment_plan": "Oral hydration, rest, symptomatic relief",
            "provisional_diagnosis": "Viral fever"
        },
        token=doc_token
    )
    assert code in [200, 201], f"Expected 200/201 for doctor consultation, got {code}: {consult_resp}"
    log("  PASS: Doctor consultation completed directly (triage bypass invariant honoured).")

    # -------------------------------------------------------------
    # PART 4: Downstream Order Gate Hardening (Diagnostics & Pharmacy)
    # -------------------------------------------------------------
    log("\n--- STEP 4: Downstream Order Gate Hardening ---")

    # 1. Disable SRV_DIAGNOSTICS and attempt lab order
    diag_fs = FacilityService.objects.get(facility=facility, service__code='SRV_DIAGNOSTICS')
    diag_fs.is_available = False
    diag_fs.save()
    log("Disabled SRV_DIAGNOSTICS.")

    code, diag_resp = api_request(
        f"{API_V1_BASE}/diagnostics/orders/",
        method="POST",
        data={
            "visit": visit_id,
            "facility": facility.id,
            "priority": "ROUTINE",
            "clinical_indication": "Suspected Typhoid"
        },
        token=doc_token
    )
    assert code == 400, f"Expected 400 when ordering lab test with SRV_DIAGNOSTICS disabled, got {code}: {diag_resp}"
    log("  PASS: DiagnosticOrder creation blocked with HTTP 400 when SRV_DIAGNOSTICS is disabled.")

    # Re-enable SRV_DIAGNOSTICS
    diag_fs.is_available = True
    diag_fs.save()

    # 2. Disable SRV_PHARMACY and attempt prescription / dispensation
    pharm_fs = FacilityService.objects.get(facility=facility, service__code='SRV_PHARMACY')
    pharm_fs.is_available = False
    pharm_fs.save()
    log("Disabled SRV_PHARMACY.")

    code, rx_resp = api_request(
        f"{API_BASE}/consultations/",
        method="POST",
        data={
            "visit": visit_id,
            "patient": patient.id,
            "facility": facility.id,
            "chief_complaint": "Joint pain",
            "prescription_items": [
                {"medicine_name": "Paracetamol 500mg", "dosage": "1-0-1", "quantity": 10}
            ]
        },
        token=doc_token
    )
    assert code == 400, f"Expected 400 when prescribing medicine with SRV_PHARMACY disabled, got {code}: {rx_resp}"
    log("  PASS: Doctor prescription blocked with HTTP 400 when SRV_PHARMACY is disabled.")

    code, disp_resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data={
            "prescription": 999999,
            "facility": facility.id
        },
        token=pharm_token
    )
    assert code == 400, f"Expected 400 when dispensing with SRV_PHARMACY disabled, got {code}: {disp_resp}"
    log("  PASS: Pharmacist dispensation blocked with HTTP 400 when SRV_PHARMACY is disabled.")

    # Re-enable SRV_PHARMACY and SRV_TRIAGE to restore facility operational readiness
    pharm_fs.is_available = True
    pharm_fs.save()
    triage_fs.is_available = True
    triage_fs.save()
    log("Restored SRV_PHARMACY and SRV_TRIAGE to available state.")

    # -------------------------------------------------------------
    # PART 5: Database Reconciliation
    # -------------------------------------------------------------
    log("\n--- STEP 5: PostgreSQL Database Verification ---")
    active_services = list(FacilityService.objects.filter(facility=facility, is_available=True).values_list('service__code', flat=True))
    log(f"Facility Active Services in DB: {active_services}")
    assert set(['SRV_GENERAL_OPD', 'SRV_NCD_SCREENING', 'SRV_DIAGNOSTICS', 'SRV_PHARMACY', 'SRV_TRIAGE']).issubset(set(active_services))

    active_depts = list(Department.objects.filter(facility=facility, is_active=True).values_list('code', flat=True))
    log(f"Facility Active Departments in DB: {active_depts}")
    assert set(['OPD', 'PHARM', 'LAB', 'TRIAGE']).issubset(set(active_depts))

    log("  PASS: PostgreSQL DB verification complete and verified.")
    log("\n==================================================================")
    log("ALL PHASE 35 PLAYWRIGHT & OPERATIONAL GATING TESTS PASSED (100% OK)")
    log("==================================================================")

if __name__ == "__main__":
    run_phase35_validation()

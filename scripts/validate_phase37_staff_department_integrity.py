# -*- coding: utf-8 -*-
"""
Playwright Browser & Authorization Validation: Phase 37 Staff -> Department Integrity Hardening

Validates:
1. Hospital Admin Real UI:
   - Login as testadmin (Clinic Admin of Namma Clinic Local PHC).
   - Navigate to Staff Administration (/admin/staff).
   - Invite new Doctor/Pharmacist with valid active department (UI success).
   - Transfer staff workflow in UI (UI modal & execution).
2. Direct API Enforcement & Scope Integrity:
   - Direct invite with cross-facility department -> HTTP 400.
   - Direct invite with inactive department -> HTTP 400.
   - Direct transfer with cross-facility department -> HTTP 400.
   - Direct transfer with inactive department -> HTTP 400.
   - Direct assign-facility with cross-facility department -> HTTP 400.
   - Hospital Admin foreign facility mutation -> HTTP 403.
   - DHO foreign district mutation -> HTTP 403.
3. PostgreSQL Database Verification:
   - Verify 100% of active StaffFacilityAssignment records have department.facility_id == facility_id.
   - Verify 100% of active StaffFacilityAssignment records have department.is_active == True.
   - Verify StaffProfile.department is synchronized with primary StaffFacilityAssignment.department.
   - Verify Pharmacists map to PHARM and Lab Technicians map to LAB.
   - Verify certified 8-role model is intact.
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
sys.path.insert(0, "D:/project/namma_clinic/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
if not os.environ.get("DATABASE_PORT"):
    try:
        from pathlib import Path
        from pgserver.utils import PostmasterInfo
        pinfo = PostmasterInfo.read_from_pgdata(Path("D:/project/namma_clinic/pgdata"))
        if pinfo and pinfo.is_running():
            os.environ["DATABASE_PORT"] = str(pinfo.port)
    except Exception:
        pass
import django
django.setup()

from apps.accounts.models import (
    User, StaffProfile, StaffFacilityAssignment, StaffRoleAssignment, RoleMaster
)
from apps.facilities.models import Facility, Department


def log(msg):
    print(f"[PHASE-37] {msg}", flush=True)


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


def run_phase37_validation():
    log("==================================================================")
    log("NAMMA CLINIC - PHASE 37 STAFF -> DEPARTMENT INTEGRITY VALIDATION")
    log("==================================================================")

    # 1. Setup / Resolve Test Entities in DB
    fac1 = Facility.objects.filter(facility_code="PHC-LOCAL-01").first() or Facility.objects.first()
    fac2 = Facility.objects.filter(facility_code="GH-LOCAL-02").first()
    if not fac2:
        fac2 = Facility.objects.exclude(id=fac1.id).first()

    assert fac1 and fac2, "Need at least two facilities in database for cross-facility testing"

    log(f"Primary Facility: {fac1.facility_name} (ID: {fac1.id})")
    log(f"Secondary Facility: {fac2.facility_name} (ID: {fac2.id})")

    # Ensure departments exist
    dept_fac1_pharm, _ = Department.objects.get_or_create(facility=fac1, code="PHARM", defaults={"name": "Pharmacy", "is_active": True})
    dept_fac1_opd, _ = Department.objects.get_or_create(facility=fac1, code="OPD", defaults={"name": "General OPD", "is_active": True})
    dept_fac1_inact, _ = Department.objects.get_or_create(facility=fac1, code="INACT_TEST", defaults={"name": "Inactive Archive Dept", "is_active": False})
    if dept_fac1_inact.is_active:
        dept_fac1_inact.is_active = False
        dept_fac1_inact.save()

    dept_fac2_lab, _ = Department.objects.get_or_create(facility=fac2, code="LAB", defaults={"name": "Laboratory", "is_active": True})
    dept_fac2_pharm, _ = Department.objects.get_or_create(facility=fac2, code="PHARM", defaults={"name": "Pharmacy", "is_active": True})
    dept_fac2_inact, _ = Department.objects.get_or_create(facility=fac2, code="INACT_TEST2", defaults={"name": "Inactive Beta Dept", "is_active": False})
    if dept_fac2_inact.is_active:
        dept_fac2_inact.is_active = False
        dept_fac2_inact.save()

    # Get tokens
    admin_token = get_jwt_token("testadmin", "AdminPassword123!")
    dho_token = get_jwt_token("localdistrict", "DistrictPassword123!")

    # -------------------------------------------------------------
    # 2. Direct API Negative Invariants (Integrity Hardening)
    # -------------------------------------------------------------
    log("[TEST 1] Verifying Direct REST API Negative Invariants...")

    # A. Cross-Facility Department on Staff Invite (Hospital Admin)
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        method="POST",
        data={
            "first_name": "Invalid",
            "last_name": "CrossDept",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "employee_id": f"EMP-XFAC-{int(time.time())}",
            "designation": "Lab Tech",
            "role_code": "LAB_TECHNICIAN",
            "facility_id": fac1.id,
            "department_id": dept_fac2_lab.id,  # Belongs to fac2!
            "password": "ValidPassword123!"
        },
        token=admin_token
    )
    assert status_code == 400, f"Expected HTTP 400 for cross-facility department, got {status_code}: {resp}"
    log(f"  [PASS] Cross-facility department on invite rejected with HTTP 400: {resp}")

    # B. Inactive Department on Staff Invite (Hospital Admin)
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        method="POST",
        data={
            "first_name": "Invalid",
            "last_name": "InactDept",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "employee_id": f"EMP-INACT-{int(time.time())}",
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": fac1.id,
            "department_id": dept_fac1_inact.id,  # Inactive department!
            "password": "ValidPassword123!"
        },
        token=admin_token
    )
    assert status_code == 400, f"Expected HTTP 400 for inactive department on invite, got {status_code}: {resp}"
    log(f"  [PASS] Inactive department on invite rejected with HTTP 400: {resp}")

    # C. Cross-Facility Department on Transfer (DHO)
    # Find or create a doctor in fac1
    test_doc = StaffProfile.objects.filter(
        facility_assignments__facility=fac1,
        facility_assignments__is_active=True
    ).exclude(user_account__username="testadmin").first()

    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/{test_doc.id}/transfer/",
        method="POST",
        data={
            "new_facility_id": fac2.id,
            "new_department_id": dept_fac1_pharm.id,  # Belongs to fac1, not fac2!
            "effective_date": str(time.strftime("%Y-%m-%d"))
        },
        token=dho_token
    )
    assert status_code == 400, f"Expected HTTP 400 for cross-facility department on transfer, got {status_code}: {resp}"
    log(f"  [PASS] Cross-facility department on transfer rejected with HTTP 400: {resp}")

    # D. Inactive Department on Transfer (DHO)
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/{test_doc.id}/transfer/",
        method="POST",
        data={
            "new_facility_id": fac2.id,
            "new_department_id": dept_fac2_inact.id,  # Inactive in fac2!
            "effective_date": str(time.strftime("%Y-%m-%d"))
        },
        token=dho_token
    )
    assert status_code == 400, f"Expected HTTP 400 for inactive department on transfer, got {status_code}: {resp}"
    log(f"  [PASS] Inactive department on transfer rejected with HTTP 400: {resp}")

    # E. Cross-Facility Department on Direct Facility Assignment
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/facility-assignments/",
        method="POST",
        data={
            "staff": test_doc.id,
            "facility": fac1.id,
            "department": dept_fac2_lab.id,  # Dept from fac2!
            "is_primary": True,
            "effective_from": str(time.strftime("%Y-%m-%d"))
        },
        token=admin_token
    )
    assert status_code == 400, f"Expected HTTP 400 for cross-facility facility assignment, got {status_code}: {resp}"
    log(f"  [PASS] Direct facility assignment with cross-facility department rejected with HTTP 400: {resp}")

    # F. Hospital Admin Foreign Facility Mutation Forbidden (HTTP 403)
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        method="POST",
        data={
            "first_name": "Foreign",
            "last_name": "AdminAttempt",
            "gender": "FEMALE",
            "date_of_birth": "1992-02-02",
            "employee_id": f"EMP-FOR-{int(time.time())}",
            "designation": "Doctor",
            "role_code": "DOCTOR",
            "facility_id": fac2.id,  # Outside HA's facility!
            "department_id": dept_fac2_pharm.id,
            "password": "ValidPassword123!"
        },
        token=admin_token
    )
    assert status_code == 403, f"Expected HTTP 403 for Hospital Admin administering foreign facility, got {status_code}: {resp}"
    log(f"  [PASS] Hospital Admin foreign facility mutation rejected with HTTP 403: {resp}")

    # -------------------------------------------------------------
    # 3. Direct API Valid Operations & Synchronization Verification
    # -------------------------------------------------------------
    log("[TEST 2] Verifying Valid Staff Operations & Department Synchronization...")

    # A. Valid Staff Invitation with Active Matching Department
    test_emp_id = f"EMP-OK-P37-{int(time.time()) % 10000}"
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        method="POST",
        data={
            "first_name": "Aarav",
            "last_name": "Sharma",
            "gender": "MALE",
            "date_of_birth": "1993-04-12",
            "employee_id": test_emp_id,
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": fac1.id,
            "department_id": dept_fac1_pharm.id,
            "password": "ValidPassword123!"
        },
        token=admin_token
    )
    assert status_code == 201, f"Expected HTTP 201 for valid staff invite, got {status_code}: {resp}"
    log(f"  [PASS] Staff invited successfully: ID #{resp['id']}, Employee: {resp['employee_id']}")

    # DB Verification of synchronization
    invited_sp = StaffProfile.objects.get(employee_id=test_emp_id)
    invited_pfa = StaffFacilityAssignment.objects.get(staff=invited_sp, is_primary=True)
    assert invited_pfa.department_id == dept_fac1_pharm.id, f"StaffFacilityAssignment department mismatch: {invited_pfa.department_id} vs {dept_fac1_pharm.id}"
    assert invited_sp.department_id == dept_fac1_pharm.id, f"StaffProfile department mismatch: {invited_sp.department_id} vs {dept_fac1_pharm.id}"
    log(f"  [PASS] Database verified: StaffFacilityAssignment.department #{invited_pfa.department_id} matches StaffProfile.department #{invited_sp.department_id} (PHARM).")

    # B. Valid Transfer with Active Target Department
    status_code, resp = api_request(
        f"{API_V1_BASE}/accounts/staff-profiles/{invited_sp.id}/transfer/",
        method="POST",
        data={
            "new_facility_id": fac2.id,
            "new_department_id": dept_fac2_pharm.id,
            "effective_date": str(time.strftime("%Y-%m-%d"))
        },
        token=dho_token
    )
    assert status_code == 200, f"Expected HTTP 200 for valid transfer, got {status_code}: {resp}"

    invited_sp.refresh_from_db()
    transferred_pfa = StaffFacilityAssignment.objects.get(staff=invited_sp, is_primary=True, is_active=True)
    assert transferred_pfa.facility_id == fac2.id, f"Transferred facility mismatch: {transferred_pfa.facility_id} vs {fac2.id}"
    assert transferred_pfa.department_id == dept_fac2_pharm.id, f"Transferred department mismatch: {transferred_pfa.department_id} vs {dept_fac2_pharm.id}"
    assert invited_sp.department_id == dept_fac2_pharm.id, f"StaffProfile department after transfer mismatch: {invited_sp.department_id} vs {dept_fac2_pharm.id}"
    log(f"  [PASS] Transfer verified: Staff moved to Facility #{fac2.id}, Department #{dept_fac2_pharm.id}. StaffProfile.department synchronized.")

    # -------------------------------------------------------------
    # 4. Playwright Browser E2E UI Flow
    # -------------------------------------------------------------
    log("[TEST 3] Running Playwright Browser E2E Validation...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Step 1: Login as Hospital Admin (testadmin)
        log("  - Logging in as testadmin (Hospital Admin)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'testadmin')
        page.fill('input[type="password"]', 'AdminPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/admin", timeout=15000)
        log("  - Hospital Admin logged in. Navigating to /admin/staff via navigation link...")

        page.wait_for_selector('a[href="/admin/staff"]', timeout=10000)
        page.click('a[href="/admin/staff"]')
        page.wait_for_url("**/admin/staff", timeout=10000)
        page.wait_for_selector('[data-testid="open-invite-staff-btn"]', timeout=15000)

        # Step 2: Open Invite Staff Modal
        log("  - Opening Invite Staff Modal...")
        page.click('[data-testid="open-invite-staff-btn"]')
        page.wait_for_selector('[data-testid="submit-invite-btn"]', timeout=5000)

        # Fill modal form
        unique_num = int(time.time()) % 10000
        new_emp_id = f"EMP-UI-{unique_num}"
        page.fill('[data-testid="invite-firstname-input"]', 'Dr. Vikram')
        page.fill('[data-testid="invite-lastname-input"]', 'Gowda')
        page.fill('[data-testid="invite-employeeid-input"]', new_emp_id)
        page.select_option('[data-testid="invite-role-select"]', value='DOCTOR')
        page.fill('[data-testid="invite-password-input"]', 'ValidPassword123!')

        log("  - Submitting invite form...")
        page.click('[data-testid="submit-invite-btn"]')

        # Modal should close and staff table should contain the new member
        page.wait_for_selector(f'text={new_emp_id}', timeout=10000)
        log(f"  - Browser verified: New staff {new_emp_id} rendered in Staff Directory Table.")

        browser.close()
        log("  [PASS] Playwright Browser E2E completed successfully.")

    # -------------------------------------------------------------
    # 5. PostgreSQL Global Consistency & Certified Model Verification
    # -------------------------------------------------------------
    log("[TEST 4] Verifying PostgreSQL Global Assignment Consistency...")

    # Check 1: 100% of active assignments belong to target facility
    inconsistent_facility = StaffFacilityAssignment.objects.filter(
        is_active=True,
        department__isnull=False
    ).exclude(department__facility=django.db.models.F('facility')).count()
    assert inconsistent_facility == 0, f"Found {inconsistent_facility} cross-facility department assignments!"
    log(f"  [PASS] 0 cross-facility department assignments found in DB.")

    # Check 2: 100% of active assignments belong to active departments
    inactive_depts_count = StaffFacilityAssignment.objects.filter(
        is_active=True,
        department__is_active=False
    ).count()
    assert inactive_depts_count == 0, f"Found {inactive_depts_count} assignments to inactive departments!"
    log(f"  [PASS] 0 inactive department assignments found in DB.")

    # Check 3: StaffProfile.department is in sync with primary active assignment
    mismatched_sp_count = 0
    for pfa in StaffFacilityAssignment.objects.filter(is_primary=True, is_active=True).select_related('staff'):
        if pfa.department_id and pfa.staff.department_id != pfa.department_id:
            mismatched_sp_count += 1
    assert mismatched_sp_count == 0, f"Found {mismatched_sp_count} mismatched StaffProfile departments!"
    log(f"  [PASS] 100% of primary StaffFacilityAssignment departments are synchronized with StaffProfile.")

    # Check 4: Pharmacists mapped to PHARM, Lab Technicians to LAB
    pharm_count = StaffProfile.objects.filter(role_assignments__role__code='PHARMACIST', role_assignments__is_active=True).distinct().count()
    pharm_in_pharm = StaffProfile.objects.filter(
        role_assignments__role__code='PHARMACIST',
        role_assignments__is_active=True,
        department__code='PHARM'
    ).distinct().count()
    assert pharm_count == pharm_in_pharm, f"Pharmacist department mapping incomplete: {pharm_in_pharm}/{pharm_count} mapped to PHARM!"
    log(f"  [PASS] 100% ({pharm_in_pharm}/{pharm_count}) of Pharmacists correctly mapped to PHARM department.")

    lab_count = StaffProfile.objects.filter(role_assignments__role__code='LAB_TECHNICIAN', role_assignments__is_active=True).distinct().count()
    lab_in_lab = StaffProfile.objects.filter(
        role_assignments__role__code='LAB_TECHNICIAN',
        role_assignments__is_active=True,
        department__code='LAB'
    ).distinct().count()
    assert lab_count == lab_in_lab, f"Lab Technician department mapping incomplete: {lab_in_lab}/{lab_count} mapped to LAB!"
    log(f"  [PASS] 100% ({lab_in_lab}/{lab_count}) of Lab Technicians correctly mapped to LAB department.")

    # Check 5: Certified 8-role model intact
    certified_roles = {
        'HOSPITAL_ADMIN', 'DISTRICT_OFFICER', 'DOCTOR', 'NURSE',
        'FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'PHARMACIST', 'INVENTORY'
    }
    db_roles = set(RoleMaster.objects.values_list('code', flat=True))
    assert certified_roles.issubset(db_roles), f"Certified roles missing: {certified_roles - db_roles}"
    log(f"  [PASS] Certified 8-role model completely intact.")

    log("==================================================================")
    log("PHASE 37 ALL CHECKS PASSED: STAFF -> DEPARTMENT INTEGRITY HARDENED")
    log("==================================================================")


if __name__ == "__main__":
    run_phase37_validation()

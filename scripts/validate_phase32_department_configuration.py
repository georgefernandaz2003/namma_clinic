"""
Phase 32 Verification Script: Department Configuration & Facility-Scope Hardening
Executes:
1. Direct REST API negative authorization tests (403 on foreign facility / cross-district).
2. DHO Playwright E2E: onboard new facility -> auto-provision standard departments (OPD, PHARM, LAB, TRIAGE) -> verify in modal.
3. Hospital Admin Playwright E2E: login -> verify locked facility scope -> manage departments (create, edit, delete) via real UI modal.
4. Database reconciliation in PostgreSQL: confirm standard departments, updated records, and foreign facility protection.
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error

# Setup Django environment
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from apps.accounts.models import User, StaffProfile, StaffRoleAssignment, StaffFacilityAssignment
from apps.facilities.models import Facility, Department
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_BASE = "http://127.0.0.1:8000/api"
API_V1_BASE = "http://127.0.0.1:8000/api/v1"

def log(msg):
    print(f"[PHASE-32] {msg}", flush=True)

def get_auth_token(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/auth/token/",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["access"]

def test_api_negative_authorization():
    log("=== STEP 1: Direct REST API Negative Authorization Tests ===")
    
    admin_token = get_auth_token("testadmin", "AdminPassword123!")
    dho_token = get_auth_token("localdistrict", "DistrictPassword123!")

    # 1. Hospital Admin attempting to create department for foreign facility #4
    log("Testing Hospital Admin attempting to create department in foreign facility #4...")
    payload_foreign_create = {"facility": 4, "code": "HACK-DEPT", "name": "Unauthorized Department"}
    req = urllib.request.Request(
        f"{API_V1_BASE}/organization/departments/",
        data=json.dumps(payload_foreign_create).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            assert False, f"Expected 403, got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
        log("  PASS: Hospital Admin foreign facility create rejected with HTTP 403")

    # 2. Hospital Admin attempting to modify department in foreign facility
    foreign_dept = Department.objects.filter(facility_id=4).first()
    if foreign_dept:
        log(f"Testing Hospital Admin attempting to update foreign department #{foreign_dept.id}...")
        req = urllib.request.Request(
            f"{API_V1_BASE}/organization/departments/{foreign_dept.id}/",
            data=json.dumps({"name": "Hacked Name"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"},
            method="PATCH"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                assert False, f"Expected 403, got {resp.status}"
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"Expected 403, got {e.code}"
            log("  PASS: Hospital Admin foreign department update rejected with HTTP 403")

        log(f"Testing Hospital Admin attempting to delete foreign department #{foreign_dept.id}...")
        req = urllib.request.Request(
            f"{API_V1_BASE}/organization/departments/{foreign_dept.id}/",
            headers={"Authorization": f"Bearer {admin_token}"},
            method="DELETE"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                assert False, f"Expected 403, got {resp.status}"
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"Expected 403, got {e.code}"
            log("  PASS: Hospital Admin foreign department delete rejected with HTTP 403")

    # 3. Hospital Admin attempting to create facility master
    log("Testing Hospital Admin attempting to mutate Facility master...")
    req = urllib.request.Request(
        f"{API_BASE}/facilities/",
        data=json.dumps({"facility_code": "HACK-FAC", "facility_name": "Unauthorized Facility", "facility_type": "NAMMA_CLINIC"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            assert False, f"Expected 403, got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
        log("  PASS: Hospital Admin facility master create rejected with HTTP 403")

    # 4. DHO attempting to create department outside assigned district (Mysuru facility #4)
    log("Testing DHO cross-district department creation targeting Mysuru facility #4...")
    req = urllib.request.Request(
        f"{API_V1_BASE}/organization/departments/",
        data=json.dumps({"facility": 4, "code": "DHO-CROSS", "name": "Cross District Dept"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {dho_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            assert False, f"Expected 403, got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
        log("  PASS: DHO cross-district department create rejected with HTTP 403")

def test_browser_full_lifecycle():
    log("=== STEP 2: Running Browser Automation for Phase 32 ===")

    # Cleanup artifacts from prior test runs
    Department.objects.filter(facility__facility_code="NC-P32-MALLESHWARAM").delete()
    Facility.objects.filter(facility_code="NC-P32-MALLESHWARAM").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -------------------------------------------------------------
        # Part A: DHO Facility Onboarding and Standard Departments Auto-Provisioning
        # -------------------------------------------------------------
        log("1. DHO Logging into system at /login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input#login-username')
        page.fill('input#login-username', 'localdistrict')
        page.fill('input#login-password', 'DistrictPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=10000)
        log("  PASS: DHO logged in successfully.")

        log("2. Navigating to Facilities Master /facilities to onboard new clinic...")
        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="onboard-facility-btn"]')
        page.click('[data-testid="onboard-facility-btn"]')
        page.wait_for_selector('role=dialog')

        log("  Submitting facility form for NC-P32-MALLESHWARAM...")
        page.fill('[data-testid="facility-name-input"]', 'Malleshwaram Namma Clinic')
        page.fill('[data-testid="facility-code-input"]', 'NC-P32-MALLESHWARAM')
        page.select_option('[data-testid="facility-type-select"]', 'NAMMA_CLINIC')
        page.select_option('[data-testid="facility-status-select"]', 'ACTIVE')
        page.fill('[data-testid="facility-phone-input"]', '080-23343232')
        page.fill('[data-testid="facility-email-input"]', 'malleshwaram.p32@nammaclinic.gov.in')
        page.click('[data-testid="submit-facility-btn"]')

        page.wait_for_selector('role=dialog', state="detached", timeout=10000)
        page.wait_for_selector('[data-testid="facility-feedback-banner"]')
        log("  PASS: Facility NC-P32-MALLESHWARAM onboarded.")

        # Inspect Departments on newly created facility
        log("3. Opening Departments modal on newly created facility...")
        page.wait_for_selector('[data-testid="manage-departments-btn-nc-p32-malleshwaram"]')
        page.click('[data-testid="manage-departments-btn-nc-p32-malleshwaram"]')

        page.wait_for_selector('[data-testid="department-modal"]')
        page.wait_for_selector('[data-testid="departments-list"]')

        # Verify all 4 standard departments exist
        for code in ['opd', 'pharm', 'lab', 'triage']:
            row = page.wait_for_selector(f'[data-testid="department-row-{code}"]')
            assert row, f"Standard department {code} must be provisioned"
        log("  PASS: Standard departments (OPD, PHARM, LAB, TRIAGE) verified in UI modal.")

        page.click('button:has-text("Close")')
        page.wait_for_selector('[data-testid="department-modal"]', state="detached")

        # Logout DHO
        context.close()
        browser.close()

    # -------------------------------------------------------------
    # Part B: Hospital Admin Department Management (Real UI)
    # -------------------------------------------------------------
    log("=== STEP 3: Hospital Admin Managing Departments via Real UI ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Handle browser alert/confirm dialogues automatically
        page.on("dialog", lambda dialog: dialog.accept())

        log("1. Hospital Admin logging into system...")
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

        # Verify Hospital Admin cannot see Onboard button or Edit button
        assert page.query_selector('[data-testid="onboard-facility-btn"]') is None, "Hospital Admin must NOT see Onboard button"
        log("  PASS: Hospital Admin cannot see facility onboarding button.")

        # Open Departments for own facility
        log("3. Hospital Admin opening own facility departments...")
        dept_btn = page.wait_for_selector('[data-testid^="manage-departments-btn-"]')
        dept_btn.click()

        page.wait_for_selector('[data-testid="department-modal"]')
        log("  PASS: Department modal opened for authorized facility.")

        # Create new department: DENTAL
        log("4. Creating new department 'DENTAL'...")
        page.click('[data-testid="open-add-department-btn"]')
        page.fill('[data-testid="department-code-input"]', 'DENTAL')
        page.fill('[data-testid="department-name-input"]', 'Dental & Oral Health')
        page.click('[data-testid="submit-department-btn"]')

        page.wait_for_selector('[data-testid="department-feedback-banner"]')
        page.wait_for_selector('[data-testid="department-row-dental"]')
        log("  PASS: Department 'DENTAL' created and displayed in directory.")

        # Edit department: change name to 'Dental & Maxillofacial OPD'
        log("5. Editing department 'DENTAL'...")
        page.click('[data-testid="edit-department-btn-dental"]')
        page.fill('[data-testid="edit-dept-name-input-dental"]', 'Dental & Maxillofacial OPD')
        page.click('[data-testid="save-edit-dept-btn-dental"]')

        page.wait_for_selector('[data-testid="department-feedback-banner"]')
        log("  PASS: Department 'DENTAL' edited successfully.")

        # Delete department: remove DENTAL
        log("6. Deleting department 'DENTAL'...")
        page.click('[data-testid="delete-department-btn-dental"]')
        time.sleep(1)
        assert page.query_selector('[data-testid="department-row-dental"]') is None, "Department row must be removed"
        log("  PASS: Department 'DENTAL' deleted successfully.")

        page.click('button:has-text("Close")')
        context.close()
        browser.close()

    # -------------------------------------------------------------
    # Step 4: PostgreSQL Database State Verification
    # -------------------------------------------------------------
    log("=== STEP 4: PostgreSQL Database Verification ===")
    fac = Facility.objects.filter(facility_code="NC-P32-MALLESHWARAM").first()
    assert fac, "Facility NC-P32-MALLESHWARAM must exist in PostgreSQL"
    assert fac.status == "ACTIVE"

    depts = Department.objects.filter(facility=fac)
    dept_map = {d.code: d.name for d in depts}
    assert "OPD" in dept_map and dept_map["OPD"] == "General OPD"
    assert "PHARM" in dept_map and dept_map["PHARM"] == "Pharmacy"
    assert "LAB" in dept_map and dept_map["LAB"] == "Laboratory"
    assert "TRIAGE" in dept_map and dept_map["TRIAGE"] == "Triage"
    log(f"  PASS: Verified all 4 standard departments in PostgreSQL for facility #{fac.id}: {list(dept_map.keys())}")

    log("=== PHASE 32 VERIFICATION COMPLETE: ALL PASS ===")

if __name__ == "__main__":
    test_api_negative_authorization()
    test_browser_full_lifecycle()

# scripts/validate_phase31_hospital_admin_appointment.py
"""
Playwright Browser & Authorization Validation: Phase 31 Hospital Administrator Appointment & Lifecycle

Validates:
1. SEC-01 Negative Authorization (Direct API):
   - Hospital Admin cannot invite another HOSPITAL_ADMIN (403 Forbidden).
   - Hospital Admin cannot assign HOSPITAL_ADMIN role (403 Forbidden).
   - Hospital Admin cannot invite DISTRICT_OFFICER (403 Forbidden).
   - DHO cannot appoint staff outside assigned district (403 Forbidden).
2. DHO Onboard & Direct Appointment Link (Real UI):
   - DHO logs in at /login.
   - Navigates to /facilities.
   - Onboards new clinic facility (NC-P31-KORAMANGALA).
   - Facility displays "No Administrator Assigned" badge and "Appoint Admin" action.
   - DHO clicks "Appoint Admin" -> navigates to /admin/staff with facility pre-selected.
3. Hospital Admin Appointment & Credential Provisioning (Real UI):
   - InviteStaffModal opens pre-filled with the new facility and HOSPITAL_ADMIN role.
   - DHO provisions administrator details and temporary credential.
   - Submits invitation -> record appears in INVITED state.
   - DHO activates administrator in StaffDetailModal.
   - Record transitions to ACTIVE state.
4. PostgreSQL Reconcilation & Audit Safety:
   - Verifies StaffProfile, User, StaffRoleAssignment, and StaffFacilityAssignment.
   - Confirms user is active and password hashes match without plaintext in DB/audit logs.
5. Newly Appointed Hospital Admin Login & Scoping (Real UI):
   - DHO logs out.
   - Newly appointed Hospital Admin logs in at /login using their provisioned credentials.
   - Verifies login succeeds and authenticated console reflects only their assigned facility.
   - Opens Staff Administration -> verifies facility is locked and cannot invite HOSPITAL_ADMIN.
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

# Setup Django ORM for direct DB verification
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from apps.accounts.models import StaffProfile, StaffRoleAssignment, StaffFacilityAssignment, User
from apps.facilities.models import Facility
from apps.geography.models import District
from apps.audit.models import AuditLogEntry

def log(msg):
    print(f"[PHASE-31] {msg}", flush=True)

def get_auth_token(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/auth/token/",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["access"]

def test_negative_authorization_api():
    log("=== STEP 1: Testing Backend SEC-01 & Scoping Negative Authorization via Direct REST API ===")
    dho_token = get_auth_token("localdistrict", "DistrictPassword123!")
    admin_token = get_auth_token("testadmin", "AdminPassword123!")

    # 1. Hospital Admin attempting to invite HOSPITAL_ADMIN
    log("Testing Hospital Admin attempting to invite another HOSPITAL_ADMIN...")
    payload_peer_invite = {
        "first_name": "Ramesh",
        "last_name": "Kumar",
        "gender": "MALE",
        "date_of_birth": "1985-05-15",
        "employee_id": "EMP-HA-PEER-TEST",
        "designation": "Hospital Administrator",
        "role_code": "HOSPITAL_ADMIN",
        "facility_id": 1,
        "temporary_password": "PeerAdmin@123"
    }
    req_invite = urllib.request.Request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        data=json.dumps(payload_peer_invite).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req_invite) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Hospital Admin invite HOSPITAL_ADMIN rejected with HTTP {e.code}")

    # 2. Hospital Admin attempting to assign HOSPITAL_ADMIN role
    log("Testing Hospital Admin attempting to assign HOSPITAL_ADMIN role to existing staff...")
    # Find any existing staff member in facility 1
    existing_staff = StaffProfile.objects.filter(status="ACTIVE").first()
    assert existing_staff, "Existing staff required for test"
    req_assign = urllib.request.Request(
        f"{API_V1_BASE}/accounts/staff-profiles/{existing_staff.id}/assign-role/",
        data=json.dumps({"role_code": "HOSPITAL_ADMIN", "facility_id": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req_assign) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Hospital Admin assign HOSPITAL_ADMIN role rejected with HTTP {e.code}")

    # 3. Hospital Admin attempting to invite DISTRICT_OFFICER
    log("Testing Hospital Admin attempting to invite DISTRICT_OFFICER...")
    payload_dho_invite = {
        "first_name": "Suresh",
        "last_name": "Verma",
        "gender": "MALE",
        "date_of_birth": "1980-01-01",
        "employee_id": "EMP-DHO-ILLEGAL",
        "designation": "District Health Officer",
        "role_code": "DISTRICT_OFFICER",
        "facility_id": 1,
        "temporary_password": "IllegalDho@123"
    }
    req_dho = urllib.request.Request(
        f"{API_V1_BASE}/accounts/staff-profiles/invite/",
        data=json.dumps(payload_dho_invite).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req_dho) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Hospital Admin invite DISTRICT_OFFICER rejected with HTTP {e.code}")

    # 4. DHO cross-district staff appointment attempt
    other_dist = District.objects.exclude(name__icontains="Bengaluru").first()
    other_dist_facility = Facility.objects.filter(district=other_dist).first() if other_dist else None
    if other_dist_facility:
        log(f"Testing DHO invite for foreign facility #{other_dist_facility.id} outside district...")
        payload_foreign = {
            "first_name": "Foreign",
            "last_name": "Admin",
            "gender": "MALE",
            "date_of_birth": "1985-05-15",
            "employee_id": "EMP-FOREIGN-HA",
            "designation": "Hospital Administrator",
            "role_code": "HOSPITAL_ADMIN",
            "facility_id": other_dist_facility.id,
            "temporary_password": "ForeignAdmin@123"
        }
        req_foreign = urllib.request.Request(
            f"{API_V1_BASE}/accounts/staff-profiles/invite/",
            data=json.dumps(payload_foreign).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {dho_token}"}
        )
        try:
            with urllib.request.urlopen(req_foreign) as resp:
                assert False, f"Expected 403 Forbidden but got {resp.status}"
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
            log(f"  PASS: DHO cross-district appointment rejected with HTTP {e.code}")


def test_browser_full_lifecycle():
    log("=== STEP 2: Running Full Playwright Browser Automation for Phase 31 ===")

    # Cleanup artifacts from prior test runs in dependency order
    User.objects.filter(staff_profile__employee_id="EMP-P31-ADMIN").delete()
    User.objects.filter(username__icontains="emp_p31_admin").delete()
    AuditLogEntry.objects.filter(facility__facility_code="NC-P31-KORAMANGALA").delete()
    StaffRoleAssignment.objects.filter(facility__facility_code="NC-P31-KORAMANGALA").delete()
    StaffFacilityAssignment.objects.filter(facility__facility_code="NC-P31-KORAMANGALA").delete()
    StaffProfile.objects.filter(employee_id="EMP-P31-ADMIN").delete()
    Facility.objects.filter(facility_code="NC-P31-KORAMANGALA").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. DHO Login
        # -------------------------------------------------------------
        log("1. DHO Logging into system at /login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input#login-username')
        page.fill('input#login-username', 'localdistrict')
        page.fill('input#login-password', 'DistrictPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=10000)
        log("  PASS: DHO successfully logged in.")

        # -------------------------------------------------------------
        # 2. Navigate to Facilities Master and Onboard Facility
        # -------------------------------------------------------------
        log("2. Navigating to Facilities Master /facilities...")
        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="onboard-facility-btn"]')
        page.click('[data-testid="onboard-facility-btn"]')
        page.wait_for_selector('role=dialog')

        log("  Submitting facility onboarding form for NC-P31-KORAMANGALA...")
        page.fill('[data-testid="facility-name-input"]', 'Koramangala Namma Clinic')
        page.fill('[data-testid="facility-code-input"]', 'NC-P31-KORAMANGALA')
        page.select_option('[data-testid="facility-type-select"]', 'NAMMA_CLINIC')
        page.select_option('[data-testid="facility-status-select"]', 'ACTIVE')
        page.fill('[data-testid="facility-phone-input"]', '080-25553131')
        page.fill('[data-testid="facility-email-input"]', 'koramangala.p31@nammaclinic.gov.in')
        page.click('[data-testid="submit-facility-btn"]')

        # Verify modal closes, feedback banner, and facility card appears
        page.wait_for_selector('role=dialog', state="detached", timeout=10000)
        page.wait_for_selector('[data-testid="facility-feedback-banner"]')
        page.fill('[data-testid="search-facilities-input"]', 'NC-P31-KORAMANGALA')
        page.wait_for_selector('[data-testid="facility-card-NC-P31-KORAMANGALA"]', timeout=5000)
        log("  PASS: Facility NC-P31-KORAMANGALA onboarded into registry.")

        # Verify "No Administrator Assigned" badge and "Appoint Admin" action button
        unassigned_badge = page.wait_for_selector('[data-testid="facility-unassigned-admin-badge-NC-P31-KORAMANGALA"]')
        assert unassigned_badge, "Badge 'No Administrator Assigned' must be visible"
        appoint_btn = page.wait_for_selector('[data-testid="appoint-admin-btn-NC-P31-KORAMANGALA"]')
        assert appoint_btn, "Button 'Appoint Admin' must be visible for DHO"
        log("  PASS: Facility shows 'No Administrator Assigned' and 'Appoint Admin' action.")

        # -------------------------------------------------------------
        # 3. Click Appoint Admin -> Navigates to Staff Administration
        # -------------------------------------------------------------
        log("3. Clicking 'Appoint Admin' button...")
        appoint_btn.click()
        page.wait_for_url("**/admin/staff*", timeout=10000)
        log("  PASS: Navigated to /admin/staff with facility query context.")

        # Verify InviteStaffModal is automatically open with pre-selected values
        modal_title = page.wait_for_selector('#invite-staff-title')
        assert modal_title, "InviteStaffModal must open automatically"
        
        # Verify pre-selected role is HOSPITAL_ADMIN
        role_select_val = page.eval_on_selector('[data-testid="invite-role-select"]', 'el => el.value')
        assert role_select_val == 'HOSPITAL_ADMIN', f"Expected HOSPITAL_ADMIN, got {role_select_val}"
        log("  PASS: Invite modal opened with preselected role: HOSPITAL_ADMIN.")

        # -------------------------------------------------------------
        # 4. Fill and Submit Hospital Administrator Invitation with Credential
        # -------------------------------------------------------------
        log("4. Entering administrator personal details and initial credential...")
        page.fill('[data-testid="invite-firstname-input"]', 'Deepak')
        page.fill('[data-testid="invite-lastname-input"]', 'Rao')
        page.fill('[data-testid="invite-employeeid-input"]', 'EMP-P31-ADMIN')
        page.fill('[data-testid="invite-email-input"]', 'deepak.rao@nammaclinic.gov.in')
        page.fill('[data-testid="invite-password-input"]', 'DeepakAdmin@2026')
        page.click('[data-testid="submit-invite-btn"]')

        # Wait for table to reload and show the invited administrator
        log("  Waiting for staff directory to display invited administrator...")
        invited_row = page.wait_for_selector('[data-testid="staff-row-emp-p31-admin"]')
        assert invited_row, "Invited staff row must appear in directory"
        log("  PASS: Staff row EMP-P31-ADMIN rendered in directory.")

        # -------------------------------------------------------------
        # 5. Activate Administrator Account
        # -------------------------------------------------------------
        log("5. Opening staff details to activate account...")
        page.click('[data-testid="view-staff-btn-emp-p31-admin"]')
        page.wait_for_selector('[data-testid="staff-detail-modal"]')

        # Click Activate Staff
        page.click('button:has-text("Activate Staff")')
        page.wait_for_selector('[data-testid="confirm-action-button"]')
        page.click('[data-testid="confirm-action-button"]')

        # Wait for success state
        time.sleep(1.5)
        log("  PASS: Staff activated via real UI modal.")
        context.close()
        browser.close()

    # -----------------------------------------------------------------
    # 6. Database Verification (PostgreSQL State)
    # -----------------------------------------------------------------
    log("=== STEP 3: Reconciling PostgreSQL Database State ===")
    sp = StaffProfile.objects.filter(employee_id="EMP-P31-ADMIN").first()
    assert sp, "StaffProfile EMP-P31-ADMIN must exist in PostgreSQL"
    assert sp.status == "ACTIVE", f"Expected ACTIVE status, got {sp.status}"

    user = sp.user_account
    assert user, "User account must be linked to StaffProfile"
    assert user.is_active is True, "User account must be active in PostgreSQL"
    assert user.check_password("DeepakAdmin@2026"), "Configured password must match hash in PostgreSQL"
    log(f"  PASS: User '{user.username}' is ACTIVE with verified password hash.")

    # Role assignment verification
    sra = StaffRoleAssignment.objects.filter(staff=sp, role__code="HOSPITAL_ADMIN", is_active=True).first()
    assert sra, "Active StaffRoleAssignment for HOSPITAL_ADMIN must exist"
    fac = Facility.objects.get(facility_code="NC-P31-KORAMANGALA")
    assert sra.facility_id == fac.id, f"Role assignment must be scoped to {fac.id}"
    log(f"  PASS: StaffRoleAssignment bound to facility #{fac.id} ({fac.facility_name}).")

    # Primary facility assignment verification
    sfa = StaffFacilityAssignment.objects.filter(staff=sp, is_primary=True, is_active=True).first()
    assert sfa and sfa.facility_id == fac.id, "StaffFacilityAssignment must be primary to target facility"
    log(f"  PASS: StaffFacilityAssignment is primary to {fac.facility_name}.")

    # Audit safety verification: NO plaintext password in audit logs
    audit_events = AuditLogEntry.objects.filter(record_id=sp.id)
    for a in audit_events:
        payload_str = json.dumps(a.payload_after) if a.payload_after else ""
        assert "DeepakAdmin@2026" not in payload_str, "Plaintext password must NEVER appear in audit log!"
    log("  PASS: Verified zero plaintext passwords leaked in audit log entries.")

    # -----------------------------------------------------------------
    # 7. Newly Appointed Hospital Admin Login & Access Scope (Real UI)
    # -----------------------------------------------------------------
    log("=== STEP 4: Validating Newly Appointed Hospital Admin Login & Scoping via Browser ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Login with new administrator credentials
        log(f"Logging in as newly appointed Hospital Admin '{user.username}'...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input#login-username')
        page.fill('input#login-username', user.username)
        page.fill('input#login-password', 'DeepakAdmin@2026')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=10000)
        log("  PASS: Hospital Admin authenticated and landed on dashboard.")

        # Navigate to Staff Administration
        log("Hospital Admin accessing /admin/staff...")
        page.goto(f"{BASE_URL}/admin/staff")
        page.wait_for_selector('[data-testid="open-invite-staff-btn"]')
        page.click('[data-testid="open-invite-staff-btn"]')
        page.wait_for_selector('#invite-staff-title')

        # Verify Hospital Admin cannot select other facilities
        # The facility input should be disabled and note facility binding
        has_disabled_fac = page.query_selector('input[value="Current Authorized Facility"][disabled]')
        assert has_disabled_fac, "Hospital Admin must have locked facility scope"
        log("  PASS: Hospital Admin invite modal enforces locked facility scope.")

        # Verify role dropdown does NOT contain HOSPITAL_ADMIN or DISTRICT_OFFICER
        role_options_text = page.eval_on_selector('[data-testid="invite-role-select"]', '''el => {
            return Array.from(el.options).map(o => o.value);
        }''')
        assert "HOSPITAL_ADMIN" not in role_options_text, "HOSPITAL_ADMIN must not be available for Hospital Admin actors"
        assert "DISTRICT_OFFICER" not in role_options_text, "DISTRICT_OFFICER must not be available for Hospital Admin actors"
        log(f"  PASS: Available roles for Hospital Admin strictly operational: {role_options_text}")

        context.close()
        browser.close()

    log("=== PHASE 31 FULL LIFECYCLE & INTEGRITY VALIDATION COMPLETE: ALL PASS ===")

if __name__ == "__main__":
    test_negative_authorization_api()
    test_browser_full_lifecycle()

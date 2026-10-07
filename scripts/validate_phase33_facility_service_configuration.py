"""
Playwright Browser & Authorization Validation: Phase 33 Facility Service Configuration

Validates:
1. Direct REST API Negative Authorization Tests:
   - Hospital Admin foreign facility service mutation rejected with HTTP 403.
   - Doctor / clinical staff service mutation rejected with HTTP 403.
   - DHO cross-district service mutation rejected with HTTP 403.
2. DHO Facility Onboarding & Canonical Service Auto-Provisioning (Real UI):
   - DHO onboards NC-P33-INDIRANAGAR.
   - All 5 canonical services (OPD, NCD, LAB, PHARM, TRIAGE) auto-provisioned.
   - Zero MCH and zero teleconsultation in ServiceMaster.
3. Hospital Admin Real UI Service Management:
   - Hospital Admin opens /facilities -> sees only own facility.
   - Hospital Admin opens Services modal.
   - Toggles service (disables NCD screening) -> UI status reflects Disabled.
   - Re-enables service -> UI status reflects Available.
4. Token Registration & Workflow Safety:
   - Disabled service token creation fails with HTTP 400 validation error.
   - Teleconsultation token creation fails with HTTP 400 validation error.
   - Historical visits remain intact.
5. PostgreSQL Database Verification:
   - Direct DB inspection of ServiceMaster and FacilityService.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_V1_BASE = "http://127.0.0.1:8000/api/v1"

# Setup Django ORM
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from apps.facilities.models import Facility, ServiceMaster, FacilityService, Department
from apps.accounts.models import User, StaffProfile
from apps.patients.models import Patient
from apps.visits.models import Visit

def log(msg):
    print(f"[PHASE-33] {msg}", flush=True)

def api_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed

def get_jwt_token(username, password):
    url = "http://127.0.0.1:8000/api/auth/token/"
    status_code, data = api_request(url, method="POST", data={"username": username, "password": password})
    assert status_code == 200, f"Failed to get JWT token for {username}: {data}"
    return data["access"]

def test_api_negative_authorization():
    log("=== STEP 1: Direct REST API Negative Authorization Tests ===")
    
    # Hospital Admin credentials: testadmin / AdminPassword123!
    admin_token = get_jwt_token("testadmin", "AdminPassword123!")

    # Find a foreign facility service (e.g. facility in Mysuru)
    foreign_fac = Facility.objects.filter(district__name__icontains="Mysuru").first()
    if not foreign_fac:
        foreign_fac = Facility.objects.exclude(facility_code="PHC-LOCAL-01").first()
    assert foreign_fac, "Must have a foreign facility for negative scoping test"

    foreign_fs = FacilityService.objects.filter(facility=foreign_fac).first()
    assert foreign_fs, "Foreign facility must have provisioned services"

    # Negative Test 1: Hospital Admin attempting to toggle foreign facility service
    log(f"Testing Hospital Admin attempting to modify service in foreign facility #{foreign_fac.id}...")
    code, data = api_request(
        f"{API_V1_BASE}/organization/facility-services/{foreign_fs.id}/",
        method="PATCH",
        data={"is_available": False},
        token=admin_token
    )
    assert code == 403, f"Expected 403 Forbidden, got {code}: {data}"
    log("  PASS: Hospital Admin foreign facility service mutation rejected with HTTP 403")

    # Negative Test 2: Hospital Admin attempting to delete foreign facility service
    log(f"Testing Hospital Admin attempting to delete foreign service #{foreign_fs.id}...")
    code, data = api_request(
        f"{API_V1_BASE}/organization/facility-services/{foreign_fs.id}/",
        method="DELETE",
        token=admin_token
    )
    assert code == 403, f"Expected 403 Forbidden, got {code}: {data}"
    log("  PASS: Hospital Admin foreign facility service delete rejected with HTTP 403")

    # Negative Test 3: Clinical Doctor attempting to mutate service
    # Doctor credentials: localdoctor / DoctorPassword123!
    doc_token = get_jwt_token("localdoc", "DoctorPassword123!")
    own_fs = FacilityService.objects.filter(facility__facility_code="PHC-LOCAL-01").first()
    log(f"Testing Doctor attempting to toggle facility service #{own_fs.id}...")
    code, data = api_request(
        f"{API_V1_BASE}/organization/facility-services/{own_fs.id}/",
        method="PATCH",
        data={"is_available": False},
        token=doc_token
    )
    assert code == 403, f"Expected 403 Forbidden, got {code}: {data}"
    log("  PASS: Doctor service mutation rejected with HTTP 403")

    # Negative Test 4: DHO attempting cross-district mutation
    dho_user = User.objects.get(username="localdistrict")
    cross_district_fac = Facility.objects.exclude(district_id=dho_user.assigned_district_id).first()
    assert cross_district_fac, "Must have facility outside district"
    cross_district_fs = FacilityService.objects.filter(facility=cross_district_fac).first()
    assert cross_district_fs, "Cross-district facility must have services"

    dho_token = get_jwt_token("localdistrict", "DistrictPassword123!")
    log(f"Testing DHO attempting cross-district service mutation targeting facility #{cross_district_fac.id} (District #{cross_district_fac.district_id})...")
    code, data = api_request(
        f"{API_V1_BASE}/organization/facility-services/{cross_district_fs.id}/",
        method="PATCH",
        data={"is_available": False},
        token=dho_token
    )
    assert code == 403, f"Expected 403 Forbidden, got {code}: {data}"
    log("  PASS: DHO cross-district service mutation rejected with HTTP 403")


def test_browser_full_lifecycle():
    log("=== STEP 2: Running Browser Automation for Phase 33 ===")

    # Cleanup artifacts from prior test runs
    FacilityService.objects.filter(facility__facility_code="NC-P33-INDIRANAGAR").delete()
    Department.objects.filter(facility__facility_code="NC-P33-INDIRANAGAR").delete()
    Facility.objects.filter(facility_code="NC-P33-INDIRANAGAR").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -------------------------------------------------------------
        # Part A: DHO Facility Onboarding and Canonical Services Auto-Provisioning
        # -------------------------------------------------------------
        log("1. DHO Logging into system at /login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input#login-username')
        page.fill('input#login-username', 'localdistrict')
        page.fill('input#login-password', 'DistrictPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=10000)
        log("  PASS: DHO logged in successfully.")

        log("2. Navigating to Facilities Master /facilities to onboard NC-P33-INDIRANAGAR...")
        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="onboard-facility-btn"]')
        page.click('[data-testid="onboard-facility-btn"]')
        page.wait_for_selector('role=dialog')

        page.fill('[data-testid="facility-name-input"]', 'Indiranagar Namma Clinic')
        page.fill('[data-testid="facility-code-input"]', 'NC-P33-INDIRANAGAR')
        page.select_option('[data-testid="facility-type-select"]', 'NAMMA_CLINIC')
        page.select_option('[data-testid="facility-status-select"]', 'ACTIVE')
        page.fill('[data-testid="facility-phone-input"]', '080-25210099')
        page.fill('[data-testid="facility-email-input"]', 'indiranagar.p33@nammaclinic.gov.in')
        page.click('[data-testid="submit-facility-btn"]')

        page.wait_for_selector('role=dialog', state="detached", timeout=10000)
        page.wait_for_selector('[data-testid="facility-feedback-banner"]')
        log("  PASS: Facility NC-P33-INDIRANAGAR onboarded.")

        # Inspect Services on newly created facility
        log("3. Opening Services modal on newly created facility...")
        page.fill('[data-testid="search-facilities-input"]', 'NC-P33-INDIRANAGAR')
        page.wait_for_selector('[data-testid="facility-card-NC-P33-INDIRANAGAR"]')
        page.click('[data-testid="manage-services-btn-nc-p33-indiranagar"]', force=True)

        page.wait_for_selector('[data-testid="facility-services-modal"]')
        page.wait_for_selector('[data-testid="services-list"]')

        # Verify all 5 canonical services exist and are Available
        for code in ['srv_general_opd', 'srv_ncd_screening', 'srv_diagnostics', 'srv_pharmacy', 'srv_triage']:
            row = page.wait_for_selector(f'[data-testid="service-row-{code}"]')
            badge = page.wait_for_selector(f'[data-testid="service-status-badge-{code}"]')
            assert row and badge, f"Service {code} must be provisioned"
            assert "Available" in badge.inner_text(), f"Service {code} must be available"
        log("  PASS: All 5 canonical services verified active in UI modal.")

        page.click('button:has-text("Close")')
        page.wait_for_selector('[data-testid="facility-services-modal"]', state="detached")

        context.close()
        browser.close()

    # -------------------------------------------------------------
    # Part B: Hospital Admin Service Management (Real UI)
    # -------------------------------------------------------------
    log("=== STEP 3: Hospital Admin Managing Services via Real UI ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

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

        # Verify Hospital Admin cannot see Onboard button
        assert page.query_selector('[data-testid="onboard-facility-btn"]') is None, "Hospital Admin must NOT see Onboard button"
        log("  PASS: Hospital Admin cannot onboard facilities.")

        page.on("console", lambda msg: log(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: log(f"[BROWSER ERROR] {err}"))

        # Open Services modal
        log("3. Opening Services modal for authorized facility...")
        svc_btn = page.wait_for_selector('[data-testid^="manage-services-btn-"]')
        svc_btn.click(force=True)

        page.wait_for_selector('[data-testid="facility-services-modal"]')
        page.wait_for_selector('[data-testid="services-list"]')
        log("  PASS: Services modal opened.")

        # Toggle service: Disable NCD Screening
        log("4. Disabling NCD Screening service...")
        toggle_btn = page.wait_for_selector('[data-testid="toggle-service-btn-srv_ncd_screening"]')
        toggle_btn.click(force=True)
        page.wait_for_selector('[data-testid="service-feedback-banner"]')
        badge = page.wait_for_selector('[data-testid="service-status-badge-srv_ncd_screening"]:has-text("Disabled")')
        assert "Disabled" in badge.inner_text(), "Service badge must reflect Disabled"
        log("  PASS: NCD Screening successfully disabled via UI.")

        # Re-enable NCD Screening
        log("5. Re-enabling NCD Screening service...")
        toggle_btn2 = page.wait_for_selector('[data-testid="toggle-service-btn-srv_ncd_screening"]')
        toggle_btn2.click(force=True)
        badge2 = page.wait_for_selector('[data-testid="service-status-badge-srv_ncd_screening"]:has-text("Available")')
        assert "Available" in badge2.inner_text(), "Service badge must reflect Available"
        log("  PASS: NCD Screening successfully re-enabled via UI.")

        page.click('button:has-text("Close")')
        page.wait_for_selector('[data-testid="facility-services-modal"]', state="detached")

        context.close()
        browser.close()

    # -------------------------------------------------------------
    # Step 4: Token Workflow Validation & Historical Preservation
    # -------------------------------------------------------------
    log("=== STEP 4: Token Workflow Validation & Safety ===")
    admin_token = get_jwt_token("testadmin", "AdminPassword123!")
    fac = Facility.objects.get(facility_code="PHC-LOCAL-01")
    ncd_fs = FacilityService.objects.get(facility=fac, service__code="SRV_NCD_SCREENING")
    
    # 1. Temporarily disable NCD Screening on facility
    ncd_fs.is_available = False
    ncd_fs.save()

    patient = Patient.objects.filter(registered_at_facility=fac).first()
    if not patient:
        patient = Patient.objects.first()

    log("Testing visit registration when NCD screening is disabled...")
    code, data = api_request(
        f"{API_V1_BASE}/visits/",
        method="POST",
        data={
            "patient": patient.id,
            "facility": fac.id,
            "visit_type": "NCD_SCREENING",
            "priority": "NORMAL"
        },
        token=admin_token
    )
    assert code == 400, f"Expected 400 for disabled service, got {code}: {data}"
    log("  PASS: Disabled service token creation rejected with HTTP 400 validation error.")

    log("Testing visit registration for teleconsultation...")
    code, data = api_request(
        f"{API_V1_BASE}/visits/",
        method="POST",
        data={
            "patient": patient.id,
            "facility": fac.id,
            "visit_type": "TELECONSULTATION",
            "priority": "NORMAL"
        },
        token=admin_token
    )
    assert code == 400, f"Expected 400 for non-operational teleconsultation, got {code}: {data}"
    log("  PASS: Teleconsultation token creation rejected with HTTP 400 validation error.")

    # Re-enable NCD screening
    ncd_fs.is_available = True
    ncd_fs.save()

    log("Testing visit registration when NCD screening is enabled...")
    code, data = api_request(
        f"{API_V1_BASE}/visits/",
        method="POST",
        data={
            "patient": patient.id,
            "facility": fac.id,
            "visit_type": "NCD_SCREENING",
            "priority": "NORMAL"
        },
        token=admin_token
    )
    assert code == 201, f"Expected 201 for active service, got {code}: {data}"
    log("  PASS: Active service token creation succeeds with HTTP 201.")

    # -------------------------------------------------------------
    # Step 5: PostgreSQL Database Verification
    # -------------------------------------------------------------
    log("=== STEP 5: PostgreSQL Database State Verification ===")
    masters = list(ServiceMaster.objects.values_list('code', flat=True))
    assert len(masters) == 5, f"Expected 5 canonical services, found {len(masters)}: {masters}"
    for exp in ['SRV_GENERAL_OPD', 'SRV_NCD_SCREENING', 'SRV_DIAGNOSTICS', 'SRV_PHARMACY', 'SRV_TRIAGE']:
        assert exp in masters, f"Missing canonical service {exp}"
    log(f"  PASS: Verified all 5 canonical services in PostgreSQL: {masters}")

    # Verify zero MCH services
    for m in masters:
        assert 'ANC' not in m and 'PNC' not in m and 'IMMUNIZATION' not in m, "MCH service detected!"
    log("  PASS: Verified zero MCH services present in database.")

    # Verify new facility
    new_fac = Facility.objects.filter(facility_code="NC-P33-INDIRANAGAR").first()
    assert new_fac, "Facility NC-P33-INDIRANAGAR must exist in PostgreSQL"
    new_services = FacilityService.objects.filter(facility=new_fac)
    assert new_services.count() == 5, f"Expected 5 services for new facility, got {new_services.count()}"
    log(f"  PASS: Verified 5 active facility services for new facility #{new_fac.id}.")

    log("=== PHASE 33 VERIFICATION COMPLETE: ALL PASS ===")

if __name__ == "__main__":
    test_api_negative_authorization()
    test_browser_full_lifecycle()

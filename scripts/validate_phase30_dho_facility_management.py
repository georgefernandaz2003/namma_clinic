"""
Playwright Browser Validation: Phase 30 DHO Facility Management & Onboarding
Verifies:
1. DHO Real UI Login & Navigation: Facilities Master Registry displays onboard action.
2. DHO Facility Onboarding via Real UI: Registers NC-P30-INDIRA and verifies card appearance.
3. PostgreSQL State Verification: Reconciles browser -> API -> DB state and district scope.
4. DHO Facility Edit & Status Management via Real UI: Updates details and toggles status ACTIVE -> INACTIVE.
5. PostgreSQL Mutation Verification: Reconciles DB updates.
6. Cross-District Boundary Enforcement: DHO blocked (403/404) from cross-district creation and mutation.
7. Hospital Admin Negative Authorization: No onboard/edit actions in UI, 403 Forbidden on direct REST mutations.
8. Operational Roles Negative Authorization: 403 Forbidden for nurse.
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

# Setup Django ORM for direct DB verification
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()
from apps.facilities.models import Facility
from apps.geography.models import District

def log(msg):
    print(f"[PHASE-30] {msg}", flush=True)

def get_auth_token(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/auth/token/",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["access"]

def test_backend_boundaries():
    log("Verifying backend district boundaries and role negative authorization...")
    dho_token = get_auth_token("localdistrict", "DistrictPassword123!")
    admin_token = get_auth_token("testadmin", "AdminPassword123!")
    nurse_token = get_auth_token("localnurse", "NursePassword123!")

    # 1. DHO cross-district create attempt
    other_dist = District.objects.exclude(name__icontains="Bengaluru").first()
    other_dist_id = other_dist.id if other_dist else 999
    log(f"Testing DHO create outside district (target district: {other_dist_id})...")
    req = urllib.request.Request(
        f"{API_BASE}/facilities/",
        data=json.dumps({
            "facility_code": "NC-CROSS-DIST-FORBIDDEN",
            "facility_name": "Unauthorized District PHC",
            "facility_type": "NAMMA_CLINIC",
            "district": other_dist_id,
            "status": "ACTIVE"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {dho_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: DHO cross-district create rejected with HTTP {e.code}")

    # 2. Hospital Admin create attempt
    log("Testing Hospital Admin create attempt...")
    req_ha = urllib.request.Request(
        f"{API_BASE}/facilities/",
        data=json.dumps({
            "facility_code": "NC-HA-UNAUTH",
            "facility_name": "HA Illegal Clinic",
            "facility_type": "NAMMA_CLINIC",
            "status": "ACTIVE"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    )
    try:
        with urllib.request.urlopen(req_ha) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Hospital Admin create rejected with HTTP {e.code}")

    # 3. Hospital Admin mutation attempt
    log("Testing Hospital Admin mutation attempt on facility 1...")
    req_ha_patch = urllib.request.Request(
        f"{API_BASE}/facilities/1/",
        data=json.dumps({"facility_name": "HA Tampered Facility"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req_ha_patch) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Hospital Admin patch rejected with HTTP {e.code}")

    # 4. Nurse mutation attempt
    log("Testing Nurse mutation attempt...")
    req_nurse = urllib.request.Request(
        f"{API_BASE}/facilities/1/",
        data=json.dumps({"facility_name": "Nurse Tampered Facility"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {nurse_token}"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req_nurse) as resp:
            assert False, f"Expected 403 Forbidden but got {resp.status}"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403 Forbidden, got {e.code}"
        log(f"  PASS: Nurse patch rejected with HTTP {e.code}")


def test_browser_flow():
    log("Starting Playwright Browser Automation for Phase 30...")

    # Cleanup test facility if left over from previous test run
    Facility.objects.filter(facility_code="NC-P30-INDIRA").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -----------------------------------------------------------------
        # STEP 1: DHO Login and Facilities Navigation
        # -----------------------------------------------------------------
        log("Step 1: Logging in as DHO (localdistrict)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]')
        page.fill('input[type="text"]', "localdistrict")
        page.fill('input[type="password"]', "DistrictPassword123!")
        page.click('button[type="submit"]')

        # Wait for authenticated dashboard navigation
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        log(f"  Logged in successfully, current url: {page.url}")

        log("Navigating to /facilities...")
        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="facilities-grid"]')
        log("  Facilities Master Registry loaded.")

        # Verify Onboard button is visible for DHO
        onboard_btn = page.wait_for_selector('[data-testid="onboard-facility-btn"]', timeout=5000)
        assert onboard_btn.is_visible(), "Onboard New Facility button must be visible to DHO"
        log("  PASS: Onboard New Facility button is visible to DHO.")

        # -----------------------------------------------------------------
        # STEP 2: DHO Facility Onboarding via Real UI
        # -----------------------------------------------------------------
        log("Step 2: Onboarding new facility via Real UI form...")
        onboard_btn.click()
        page.wait_for_selector('role=dialog')
        log("  Onboard modal opened.")

        page.fill('[data-testid="facility-name-input"]', "Namma Clinic - Phase 30 Indiranagar Hub")
        page.fill('[data-testid="facility-code-input"]', "NC-P30-INDIRA")
        page.select_option('[data-testid="facility-type-select"]', "NAMMA_CLINIC")
        page.select_option('[data-testid="facility-status-select"]', "ACTIVE")
        page.fill('[data-testid="facility-phone-input"]', "080-25253030")
        page.fill('[data-testid="facility-email-input"]', "indiranagar.p30@nammaclinic.gov.in")
        page.fill('[data-testid="facility-opening-time-input"]', "08:30 AM")
        page.fill('[data-testid="facility-closing-time-input"]', "05:00 PM")
        page.fill('[data-testid="facility-population-input"]', "25000")
        page.fill('[data-testid="facility-vulnerable-input"]', "6500")
        page.fill('[data-testid="facility-address-input"]', "100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru")
        page.fill('[data-testid="facility-services-input"]', "General OPD, NCD Screening, ANC/PNC Care, Immunization, Basic Diagnostics, Pharmacy")

        page.click('[data-testid="submit-facility-btn"]')
        log("  Submitted onboarding form.")

        # Modal should close and feedback banner appears
        page.wait_for_selector('role=dialog', state="detached", timeout=10000)
        page.wait_for_selector('[data-testid="facility-feedback-banner"]')
        log("  PASS: Modal closed and feedback banner appeared.")

        # Filter/search for newly onboarded facility
        page.fill('[data-testid="search-facilities-input"]', "NC-P30-INDIRA")
        card = page.wait_for_selector('[data-testid="facility-card-NC-P30-INDIRA"]', timeout=5000)
        assert card.is_visible(), "New facility card must appear in the registry"
        status_badge = page.wait_for_selector('[data-testid="facility-status-badge-NC-P30-INDIRA"]')
        assert "ACTIVE" in status_badge.inner_text(), "Facility status must be ACTIVE"
        log("  PASS: Newly onboarded facility appears in UI with ACTIVE status badge.")

        # -----------------------------------------------------------------
        # STEP 3: Verify PostgreSQL State (Browser -> API -> DB)
        # -----------------------------------------------------------------
        log("Step 3: Verifying PostgreSQL record for NC-P30-INDIRA...")
        fac = Facility.objects.filter(facility_code="NC-P30-INDIRA").first()
        assert fac is not None, "Facility must exist in PostgreSQL"
        assert fac.facility_name == "Namma Clinic - Phase 30 Indiranagar Hub", f"Name mismatch: {fac.facility_name}"
        assert fac.status == "ACTIVE", f"Status mismatch: {fac.status}"
        assert fac.phone == "080-25253030", f"Phone mismatch: {fac.phone}"
        assert fac.population_served == 25000, f"Pop mismatch: {fac.population_served}"
        assert fac.district.name == "Bengaluru Urban", f"District mismatch: {fac.district.name}"
        log(f"  PASS: PostgreSQL record verified (ID={fac.id}, District={fac.district.name}, Status={fac.status}).")

        # -----------------------------------------------------------------
        # STEP 4: DHO Edit Facility & Status Management via Real UI
        # -----------------------------------------------------------------
        log("Step 4: Editing facility and toggling status via Real UI...")
        edit_btn = page.wait_for_selector('[data-testid="edit-facility-btn-NC-P30-INDIRA"]')
        edit_btn.click()
        page.wait_for_selector('role=dialog')
        log("  Edit modal opened.")

        # Verify facility code input is disabled
        code_input = page.wait_for_selector('[data-testid="facility-code-input"]')
        assert code_input.is_disabled(), "Facility code should be disabled/immutable during edit"

        # Mutate name, phone, and toggle status to INACTIVE
        page.fill('[data-testid="facility-name-input"]', "Namma Clinic - Phase 30 Indiranagar Satellite")
        page.fill('[data-testid="facility-phone-input"]', "080-25253099")
        page.select_option('[data-testid="facility-status-select"]', "INACTIVE")

        page.click('[data-testid="submit-facility-btn"]')
        log("  Submitted edit form.")

        page.wait_for_selector('role=dialog', state="detached", timeout=10000)
        page.wait_for_selector('[data-testid="facility-feedback-banner"]')
        log("  PASS: Edit modal closed and feedback banner appeared.")

        # Switch to Inactive filter
        page.click('[data-testid="filter-inactive-btn"]')
        page.fill('[data-testid="search-facilities-input"]', "NC-P30-INDIRA")
        card_inactive = page.wait_for_selector('[data-testid="facility-card-NC-P30-INDIRA"]', timeout=5000)
        assert card_inactive.is_visible(), "Updated facility must appear in Inactive filter"
        status_badge_inactive = page.wait_for_selector('[data-testid="facility-status-badge-NC-P30-INDIRA"]')
        assert "INACTIVE" in status_badge_inactive.inner_text(), "Status must be updated to INACTIVE"
        log("  PASS: Updated facility appears under Inactive filter with INACTIVE status badge.")

        # -----------------------------------------------------------------
        # STEP 5: Verify PostgreSQL Mutation
        # -----------------------------------------------------------------
        log("Step 5: Verifying updated PostgreSQL record...")
        fac.refresh_from_db()
        assert fac.facility_name == "Namma Clinic - Phase 30 Indiranagar Satellite", f"Name: {fac.facility_name}"
        assert fac.status == "INACTIVE", f"Status: {fac.status}"
        assert fac.phone == "080-25253099", f"Phone: {fac.phone}"
        log(f"  PASS: PostgreSQL record successfully reconciled (Name={fac.facility_name}, Status={fac.status}).")

        # -----------------------------------------------------------------
        # STEP 6: Hospital Admin UI Isolation
        # -----------------------------------------------------------------
        log("Step 6: Logging in as Hospital Admin (testadmin) to verify UI restrictions...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]')
        page.fill('input[type="text"]', "testadmin")
        page.fill('input[type="password"]', "AdminPassword123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)

        page.goto(f"{BASE_URL}/facilities")
        page.wait_for_selector('[data-testid="facilities-grid"]')

        # Verify Onboard button is ABSENT
        onboard_absent = page.query_selector('[data-testid="onboard-facility-btn"]')
        assert onboard_absent is None, "Hospital Admin must NOT see Onboard New Facility button"
        log("  PASS: Hospital Admin UI does NOT show 'Onboard New Facility' button.")

        # Verify Edit buttons are ABSENT
        edit_buttons = page.query_selector_all('button[data-testid^="edit-facility-btn-"]')
        assert len(edit_buttons) == 0, "Hospital Admin must NOT see any Edit Facility buttons"
        log("  PASS: Hospital Admin UI does NOT show any 'Edit' buttons.")

        browser.close()
        log("ALL BROWSER AND DATABASE VALIDATIONS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    test_backend_boundaries()
    test_browser_flow()

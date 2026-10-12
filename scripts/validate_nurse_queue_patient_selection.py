"""
Validation Script: Nurse Triage Queue Patient Selection Bug Verification
Tests:
1. Click Triage on the first waiting patient -> opens exact first patient.
2. Return and click Triage on the second waiting patient -> opens exact second patient (NOT the first).
3. Confirm each page displays the correct patient name, patient ID, visit ID, and token.
4. Test browser refresh preserving selected encounter.
5. Test Previous/Next navigation from selected patient.
6. Confirm facility scope and role authorization.
"""

import os
import sys
import time
from datetime import timedelta

sys.path.append(r"D:\project\namma_clinic\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.visits.services import issue_opd_token
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots_queue_selection")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(tag, message):
    print(f"[{tag}] {message}", flush=True)

def setup_test_queue():
    fac1 = Facility.objects.get(id=1)
    fac2 = Facility.objects.exclude(id=1).first() or Facility.objects.create(
        facility_name="Sub-Centre Test", facility_code="SC-TEST-99", facility_type="SUB_CENTRE"
    )

    now = timezone.now()
    suffix = int(now.timestamp()) % 10000

    # Clean old test visits and set other pending visits to TRIAGED
    Visit.objects.filter(visit_id__startswith="VIS-SEL-E2E-").delete()
    Visit.objects.filter(facility=fac1, status="WAITING_FOR_TRIAGE").update(status="TRIAGED", current_queue="DOCTOR")

    data = {}

    # Patient 1 (First in queue)
    p1, _ = Patient.objects.get_or_create(
        mobile=f"97111{suffix:04d}1",
        defaults={
            "patient_id": f"PAT-SEL-1-{suffix}",
            "name": f"Aarav Sharma {suffix}",
            "age": 34,
            "gender": "MALE",
            "registered_at_facility": fac1,
            "address": "Malleswaram, Bangalore"
        }
    )
    v1 = Visit.objects.create(
        visit_id=f"VIS-SEL-1-{suffix}",
        patient=p1,
        facility=fac1,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        arrival_time=now - timedelta(minutes=25),
        chief_complaint="High fever and severe body ache"
    )
    tok1 = issue_opd_token(visit=v1, facility=fac1)
    data["p1"] = p1
    data["v1"] = v1
    data["tok1"] = tok1

    # Patient 2 (Second in queue)
    p2, _ = Patient.objects.get_or_create(
        mobile=f"97111{suffix:04d}2",
        defaults={
            "patient_id": f"PAT-SEL-2-{suffix}",
            "name": f"Bhavna Patel {suffix}",
            "age": 42,
            "gender": "FEMALE",
            "registered_at_facility": fac1,
            "address": "Rajajinagar, Bangalore"
        }
    )
    v2 = Visit.objects.create(
        visit_id=f"VIS-SEL-2-{suffix}",
        patient=p2,
        facility=fac1,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        arrival_time=now - timedelta(minutes=15),
        chief_complaint="Persistent dry cough and mild dyspnea"
    )
    tok2 = issue_opd_token(visit=v2, facility=fac1)
    data["p2"] = p2
    data["v2"] = v2
    data["tok2"] = tok2

    # Patient 3 in Facility 2 (Scope check)
    p3_fac2, _ = Patient.objects.get_or_create(
        mobile=f"97111{suffix:04d}3",
        defaults={
            "patient_id": f"PAT-SEL-3-{suffix}",
            "name": f"Other Clinic Patient {suffix}",
            "age": 29,
            "gender": "FEMALE",
            "registered_at_facility": fac2,
            "address": "Other District"
        }
    )
    v3_fac2 = Visit.objects.create(
        visit_id=f"VIS-SEL-3-{suffix}",
        patient=p3_fac2,
        facility=fac2,
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_TRIAGE",
        current_queue="TRIAGE",
        chief_complaint="Unrelated scope visit"
    )
    tok3 = issue_opd_token(visit=v3_fac2, facility=fac2)
    data["p3_fac2"] = p3_fac2
    data["v3_fac2"] = v3_fac2
    data["tok3"] = tok3

    return data

def run_tests():
    log("INIT", "Seeding reproducible test queue in PostgreSQL 16...")
    data = setup_test_queue()
    p1 = data["p1"]
    v1 = data["v1"]
    tok1 = data["tok1"]

    p2 = data["p2"]
    v2 = data["v2"]
    tok2 = data["tok2"]

    p3_fac2 = data["p3_fac2"]

    log("INIT", f"Patient 1: {p1.name} (Visit: {v1.visit_id}, ID: {v1.id}, Token: #{tok1.token_number})")
    log("INIT", f"Patient 2: {p2.name} (Visit: {v2.visit_id}, ID: {v2.id}, Token: #{tok2.token_number})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: log("CONSOLE", f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: log("PAGEERROR", str(err)))

        # 1. Login as Nurse
        log("AUTH", "Logging in as Nurse (e2e_nurse_user)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "e2e_nurse_user")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/queue" in u, timeout=10000)
        page.wait_for_load_state("networkidle")
        log("AUTH", f"Logged in. URL: {page.url}")

        # 2. Navigate to Nurse Triage Queue (/queue)
        log("QUEUE", "Navigating to /queue...")
        page.goto(f"{BASE_URL}/queue")
        page.wait_for_selector(f"#queue-triage-btn-{v1.id}", timeout=10000)
        page.wait_for_selector(f"#queue-triage-btn-{v2.id}", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Facility Scope Check: Facility 2 patient must NOT appear in queue table
        page_text = page.locator("body").inner_text()
        assert p3_fac2.name not in page_text, "Facility 2 patient must not leak into Facility 1 queue!"
        log("SCOPE", "Verified: Facility 2 patient is strictly excluded from Nurse Queue.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_nurse_queue_table.png"))

        # 3. Test Step 1: Click Triage on FIRST waiting patient (v1)
        log("STEP 1", f"Clicking Triage for Patient 1 ({p1.name}, visit {v1.id})...")
        page.click(f"#queue-triage-btn-{v1.id}")
        page.wait_for_url(lambda u: f"visit={v1.id}" in u, timeout=10000)
        page.wait_for_selector("#save-triage-btn", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Verify Patient 1 details on Triage Page
        body_text_v1 = page.locator("body").inner_text()
        assert p1.name in body_text_v1, f"Expected {p1.name} on triage page, but not found!"
        assert v1.visit_id in body_text_v1, f"Expected visit ID {v1.visit_id} on triage page!"
        assert f"#{tok1.token_number}" in body_text_v1, f"Expected Token #{tok1.token_number} on triage page!"
        assert f"visit={v1.id}" in page.url, f"Expected URL to contain visit={v1.id}, got {page.url}"
        log("STEP 1", f"Verified Patient 1 triage page correctly loaded: Name={p1.name}, Token=#{tok1.token_number}, Visit={v1.visit_id}")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_first_patient_triage_opened.png"))

        # 4. Test Step 2: Return to /queue and click Triage on SECOND waiting patient (v2)
        log("STEP 2", "Returning to /queue to select Patient 2...")
        page.goto(f"{BASE_URL}/queue")
        page.wait_for_selector(f"#queue-triage-btn-{v2.id}", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        log("STEP 2", f"Clicking Triage for Patient 2 ({p2.name}, visit {v2.id})...")
        page.click(f"#queue-triage-btn-{v2.id}")
        page.wait_for_url(lambda u: f"visit={v2.id}" in u, timeout=10000)
        page.wait_for_selector("#save-triage-btn", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Verify Patient 2 details on Triage Page (MUST NOT be Patient 1!)
        body_text_v2 = page.locator("body").inner_text()
        assert p2.name in body_text_v2, f"Expected {p2.name} on triage page, but got: {body_text_v2[:300]}"
        assert p1.name not in body_text_v2, f"Bug detected: Patient 1 ({p1.name}) was loaded instead of Patient 2!"
        assert v2.visit_id in body_text_v2, f"Expected visit ID {v2.visit_id} on triage page!"
        assert f"#{tok2.token_number}" in body_text_v2, f"Expected Token #{tok2.token_number} on triage page!"
        assert f"visit={v2.id}" in page.url, f"Expected URL to contain visit={v2.id}, got {page.url}"
        log("STEP 2", f"Verified Patient 2 triage page correctly loaded: Name={p2.name}, Token=#{tok2.token_number}, Visit={v2.visit_id}")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_second_patient_triage_opened.png"))

        # 5. Test Step 3: Test Browser Refresh on Patient 2
        log("STEP 3", "Refreshing page (F5 reload) on Patient 2...")
        page.reload()
        page.wait_for_selector("#save-triage-btn", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        body_text_after_reload = page.locator("body").inner_text()
        assert p2.name in body_text_after_reload, f"Reload failed to preserve Patient 2 ({p2.name})!"
        assert f"visit={v2.id}" in page.url, f"Reload lost visit query parameter: {page.url}"
        log("STEP 3", "Verified: Browser reload accurately preserves selected Patient 2 encounter!")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_patient_preserved_on_refresh.png"))

        # 6. Test Step 4: Previous / Next Navigation from Patient 2
        log("STEP 4", "Testing Previous Patient navigation from Patient 2...")
        prev_btn = page.locator("#prev-patient-btn")
        next_btn = page.locator("#next-patient-btn")

        assert prev_btn.is_disabled() is False, "Previous Patient button must be ENABLED on Patient 2!"
        prev_btn.click()
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        # Must transition back to Patient 1
        assert f"visit={v1.id}" in page.url, f"Expected navigation to visit={v1.id}, got {page.url}"
        body_text_nav_p1 = page.locator("body").inner_text()
        assert p1.name in body_text_nav_p1, f"Expected {p1.name} after clicking Previous Patient!"
        log("STEP 4", f"Verified Previous Patient navigation: transitioned to Patient 1 ({p1.name})")

        # Now click Next Patient to transition back to Patient 2
        log("STEP 4", "Testing Next Patient navigation back to Patient 2...")
        page.click("#next-patient-btn")
        time.sleep(1.5)
        page.wait_for_load_state("networkidle")

        assert f"visit={v2.id}" in page.url, f"Expected navigation to visit={v2.id}, got {page.url}"
        body_text_nav_p2 = page.locator("body").inner_text()
        assert p2.name in body_text_nav_p2, f"Expected {p2.name} after clicking Next Patient!"
        log("STEP 4", f"Verified Next Patient navigation: transitioned to Patient 2 ({p2.name})")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_previous_next_navigation.png"))

        # 7. Step 5: Verify Role Authorization (Doctor forbidden from /triage)
        log("STEP 5", "Testing Role Authorization: Doctor cannot access /triage...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("#login-username", timeout=10000)
        page.fill("#login-username", "localdoc")
        page.fill("#login-password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(lambda u: "/dashboard" in u or "/consultation" in u, timeout=10000)
        page.wait_for_load_state("networkidle")

        page.goto(f"{BASE_URL}/triage?visit={v1.id}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        doc_body = page.locator("body").inner_text()
        assert "Access Denied" in doc_body or "Forbidden" in doc_body or "/dashboard" in page.url, "Doctor must not access Nurse triage!"
        log("STEP 5", "Verified: Doctor is strictly blocked from Nurse triage.")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_doctor_blocked_from_triage.png"))

        browser.close()
        log("SUCCESS", "ALL PATIENT SELECTION, NAVIGATION, REFRESH, AND AUTHORIZATION TESTS PASSED!")

if __name__ == "__main__":
    run_tests()

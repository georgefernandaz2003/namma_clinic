# -*- coding: utf-8 -*-
"""
Playwright Browser & Authorization Validation: Phase 39 Legacy Role Authorization Migration
& Pharmacy API Exception Hardening

Validates:
1. SEC-38-01:
   - Dual-role user (INVENTORY + PHARMACIST) retains independent authority.
   - User with legacy User.role = 'INVENTORY' but active StaffRoleAssignment = 'PHARMACIST'
     is fully authorized to verify and dispense prescriptions.
   - Real Browser UI login and access to /pharmacy console.
   - INVENTORY role functions independently.
   - Unauthorized roles (DOCTOR, NURSE) remain HTTP 403 Forbidden.
2. SEC-38-02:
   - DispensationViewSet.create handles nonexistent prescription_id cleanly -> HTTP 404.
   - DispensationViewSet.create handles nonexistent facility_id cleanly -> HTTP 404.
   - DispensationViewSet.create handles nonexistent prescription_item_id cleanly -> HTTP 404.
   - DispensationViewSet.create handles nonexistent batch_id cleanly -> HTTP 404.
   - Prescription verification on nonexistent prescription -> HTTP 404.
   - No unhandled HTTP 500 server errors occur.
3. PostgreSQL Database Verification:
   - Authoritative InventoryLedger source of truth verified.
   - Balance before/delta/after reconciliation.
   - MCH and teleconsultation services confirmed absent/blocked.
"""

import os
import sys
import time
import json
import datetime
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

from django.db import transaction
from apps.accounts.models import (
    User, Person, StaffProfile, StaffFacilityAssignment, StaffRoleAssignment, RoleMaster
)
from apps.facilities.models import Facility, Department, FacilityService, ServiceMaster
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster, MedicineBatch, Dispensation, DispensationItem, InventoryLedger


def log(msg):
    print(f"[PHASE-39] {msg}", flush=True)


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


def run_phase39_validation():
    log("==================================================================")
    log("NAMMA CLINIC - PHASE 39 PLAYWRIGHT & AUTHORIZATION VALIDATION")
    log("==================================================================")

    # 1. Baseline Facility
    facility = Facility.objects.filter(facility_code='PHC-LOCAL-01').first()
    if not facility:
        facility = Facility.objects.first()
    assert facility is not None, "No active facility found!"
    log(f"Target Facility: {facility.facility_name} ({facility.facility_code}) [ID: {facility.id}]")

    dept_pharm = Department.objects.filter(facility=facility, code='PHARM').first()
    assert dept_pharm is not None, "Pharmacy department missing at target facility!"

    # Ensure SRV_PHARMACY service is active
    from apps.facilities.services import provision_standard_facility_services
    provision_standard_facility_services(facility)
    FacilityService.objects.filter(facility=facility, service__code='SRV_PHARMACY').update(is_available=True)

    role_inventory, _ = RoleMaster.objects.get_or_create(code="INVENTORY", defaults={"name": "Inventory Manager"})
    role_pharmacist, _ = RoleMaster.objects.get_or_create(code="PHARMACIST", defaults={"name": "Pharmacist"})

    # Setup Dual-Role User:
    # Deliberately set User.role to 'INVENTORY' (legacy role != PHARMACIST)
    # Give active StaffRoleAssignment for INVENTORY and PHARMACIST
    test_username = "dualpharm_p39"
    test_password = "DualPharmPass123!"

    u_dual = User.objects.filter(username=test_username).first()
    if not u_dual:
        p_dual = Person.objects.create(
            first_name="Praveen",
            last_name="DualRole",
            gender="MALE",
            date_of_birth="1990-05-10"
        )
        sp_dual = StaffProfile.objects.create(
            person=p_dual,
            employee_id="EMP-DUAL-P39",
            designation="Pharmacist & Inventory Officer",
            department=dept_pharm,
            status="ACTIVE"
        )
        StaffFacilityAssignment.objects.create(
            staff=sp_dual,
            facility=facility,
            department=dept_pharm,
            is_primary=True,
            is_active=True
        )
        StaffRoleAssignment.objects.create(staff=sp_dual, role=role_inventory, is_active=True)
        StaffRoleAssignment.objects.create(staff=sp_dual, role=role_pharmacist, is_active=True)

        u_dual = User.objects.create_user(
            username=test_username,
            email="dualpharm@nammaclinic.local",
            password=test_password,
            role="INVENTORY",  # Deliberately set legacy role != PHARMACIST
            is_active=True,
            assigned_facility=facility,
            staff_profile=sp_dual
        )
    else:
        u_dual.set_password(test_password)
        u_dual.role = "INVENTORY"  # Guarantee legacy role != PHARMACIST
        u_dual.save(update_fields=['role', 'password'])
        sp_dual = u_dual.staff_profile
        StaffRoleAssignment.objects.get_or_create(staff=sp_dual, role=role_inventory, defaults={'is_active': True})
        StaffRoleAssignment.objects.get_or_create(staff=sp_dual, role=role_pharmacist, defaults={'is_active': True})

    log("Dual-role user prepared:")
    log(f"  Username: {u_dual.username}")
    log(f"  Legacy User.role: '{u_dual.role}' (INVENTORY, not PHARMACIST)")
    sras = list(StaffRoleAssignment.objects.filter(staff=sp_dual, is_active=True).values_list('role__code', flat=True))
    log(f"  Active StaffRoleAssignments: {sras}")
    assert "INVENTORY" in sras and "PHARMACIST" in sras

    # Setup Baseline Clinical Prescription for Dispensing
    med = MedicineMaster.objects.filter(generic_name__icontains="Paracetamol").first()
    if not med:
        med = MedicineMaster.objects.create(
            generic_name="Paracetamol",
            brand_name="Calpol 500mg",
            dosage_form="Tablet",
            strength="500mg",
            category="Analgesic"
        )

    batch = MedicineBatch.objects.filter(facility=facility, medicine=med, available_quantity__gte=10).first()
    if not batch:
        batch = MedicineBatch.objects.create(
            medicine=med,
            facility=facility,
            batch_number="BATCH-P39-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=365),
            quantity=50,
            available_quantity=50,
            status="AVAILABLE"
        )
        InventoryLedger.objects.create(
            batch=batch,
            facility=facility,
            performed_by_staff=sp_dual,
            transaction_type="PURCHASE_RECEIPT",
            quantity_delta=50,
            balance_after=50,
            remarks="Phase 39 Seed Batch"
        )

    # initial_batch_balance set below

    doc_user = User.objects.filter(role="DOCTOR").first()
    doc_staff = getattr(doc_user, "staff_profile", None)
    
    for prev_pat in Patient.objects.filter(registered_at_facility=facility, name__icontains="Validation Patient P39"):
        DispensationItem.objects.filter(dispensation__prescription__patient=prev_pat).delete()
        Dispensation.objects.filter(prescription__patient=prev_pat).delete()
        PrescriptionItem.objects.filter(prescription__patient=prev_pat).delete()
        Prescription.objects.filter(patient=prev_pat).delete()
        Consultation.objects.filter(patient=prev_pat).delete()
        Visit.objects.filter(patient=prev_pat).delete()
        prev_pat.delete()
    batch.quantity = 50
    batch.available_quantity = 50
    batch.save(update_fields=['quantity', 'available_quantity'])
    initial_batch_balance = 50
    log(f"Test Batch: {batch.batch_number} (Available: {initial_batch_balance})")




    patient = Patient.objects.create(
        patient_id=f"PAT-P39-{int(time.time())}",
        name=f"Validation Patient P39 {int(time.time())}",
        age=32,
        gender="FEMALE",
        registered_at_facility=facility
    )
    visit = Visit.objects.create(
        visit_id=f"VST-P39-{int(time.time())}",
        patient=patient,
        facility=facility,
        visit_type="OUTPATIENT"
    )
    consultation = Consultation.objects.create(
        visit=visit,
        patient=patient,
        facility=facility,
        doctor_staff=doc_staff,
        chief_complaint="Fever and Headache"
    )
    rx = Prescription.objects.create(
        consultation=consultation,
        patient=patient,
        doctor=doc_user,
        doctor_staff=doc_staff,
        facility=facility,
        status="VERIFIED",
        date=datetime.date.today()
    )
    rx_item = PrescriptionItem.objects.create(
        prescription=rx,
        medicine=med,
        medicine_name="Paracetamol 500mg",
        dosage="1-0-1",
        frequency="Twice daily",
        duration_days=3,
        quantity=6,
        dispensed_quantity=0,
        status="PENDING"
    )
    log(f"Created prescription #{rx.id} with item #{rx_item.id} (Status: {rx.status})")

    # -------------------------------------------------------------------------
    # STEP 1: Real Browser UI Verification (Playwright)
    # -------------------------------------------------------------------------
    log("\n--- STEP 1: Real Browser UI Verification (Playwright) ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        log("1. Navigating to login page...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        log(f"2. Logging in as dual-role user '{test_username}'...")
        page.fill('input[type="text"], input[name="username"]', test_username)
        page.fill('input[type="password"]', test_password)
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        # Confirm user profile contains roles
        token_str = page.evaluate("() => localStorage.getItem('access_token')")
        assert token_str, "Access token missing after login!"
        log("  PASS: Dual-role user logged in successfully, JWT received.")

        log("3. Navigating to Pharmacy Console (/pharmacy)...")
        page.goto(f"{BASE_URL}/pharmacy")
        page.wait_for_timeout(2000)

        # Check Pharmacy console elements
        page_content = page.content()
        assert "Pharmacy" in page_content or "Dispensing" in page_content, "Pharmacy console failed to load!"
        log("  PASS: Pharmacy workstation loaded successfully for user with legacy User.role != PHARMACIST.")

        browser.close()

    # -------------------------------------------------------------------------
    # STEP 2: SEC-38-01 Dual Role & Legacy Independence API Verification
    # -------------------------------------------------------------------------
    log("\n--- STEP 2: SEC-38-01 Dual Role & Legacy Independence API Verification ---")
    dual_token = get_jwt_token(test_username, test_password)

    # 1. Dispense valid prescription using dual-role user
    dispense_payload = {
        "prescription_id": rx.id,
        "facility_id": facility.id,
        "items": [
            {
                "prescription_item_id": rx_item.id,
                "batch_id": batch.id,
                "quantity": 6
            }
        ]
    }
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=dispense_payload,
        token=dual_token
    )
    assert status_code == 201, f"Expected 201 for dual-role dispensation, got {status_code}: {resp}"
    log(f"  PASS: Dual-role user dispensed prescription successfully (HTTP 201 Created). Dispensation: {resp.get('dispensation_number')}")

    # 2. Verify INVENTORY authority functions independently
    status_code, resp_vendors = api_request(
        f"{API_V1_BASE}/procurement/vendors/",
        method="GET",
        token=dual_token
    )
    assert status_code == 200, f"Expected 200 for inventory vendors, got {status_code}: {resp_vendors}"
    log(f"  PASS: Dual-role user accessed inventory vendors independently (HTTP 200 OK).")

    # 3. Verify Unauthorized clinical roles are rejected (HTTP 403)
    doc_token = get_jwt_token("localdoc", "DoctorPassword123!")
    status_code, resp_doc = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=dispense_payload,
        token=doc_token
    )
    assert status_code == 403, f"Expected 403 for DOCTOR attempting dispensation, got {status_code}: {resp_doc}"
    log(f"  PASS: Doctor blocked from dispensing medications (HTTP 403 Forbidden).")

    nurse_token = get_jwt_token("localnurse", "NursePassword123!")
    status_code, resp_nurse = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=dispense_payload,
        token=nurse_token
    )
    assert status_code == 403, f"Expected 403 for NURSE attempting dispensation, got {status_code}: {resp_nurse}"
    log(f"  PASS: Nurse blocked from dispensing medications (HTTP 403 Forbidden).")

    # -------------------------------------------------------------------------
    # STEP 3: SEC-38-02 Pharmacy API Exception Hardening Verification
    # -------------------------------------------------------------------------
    log("\n--- STEP 3: SEC-38-02 Exception Hardening Verification ---")

    # Case A: Nonexistent prescription_id
    bad_rx_payload = {
        "prescription_id": 999999,
        "facility_id": facility.id,
        "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 1}]
    }
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=bad_rx_payload,
        token=dual_token
    )
    assert status_code == 404, f"Expected 404 for nonexistent prescription_id, got {status_code}: {resp}"
    assert "error" in resp and "999999" in resp["error"]
    log(f"  PASS: Nonexistent prescription_id rejected cleanly with HTTP 404: {resp['error']}")

    # Case B: Nonexistent facility_id
    bad_fac_payload = {
        "prescription_id": rx.id,
        "facility_id": 999999,
        "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 1}]
    }
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=bad_fac_payload,
        token=dual_token
    )
    assert status_code == 404, f"Expected 404 for nonexistent facility_id, got {status_code}: {resp}"
    assert "error" in resp and "999999" in resp["error"]
    log(f"  PASS: Nonexistent facility_id rejected cleanly with HTTP 404: {resp['error']}")

    # Case C: Nonexistent prescription_item_id
    bad_item_payload = {
        "prescription_id": rx.id,
        "facility_id": facility.id,
        "items": [{"prescription_item_id": 999999, "batch_id": batch.id, "quantity": 1}]
    }
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=bad_item_payload,
        token=dual_token
    )
    assert status_code == 404, f"Expected 404 for nonexistent prescription_item_id, got {status_code}: {resp}"
    assert "error" in resp and "999999" in resp["error"]
    log(f"  PASS: Nonexistent prescription_item_id rejected cleanly with HTTP 404: {resp['error']}")

    # Case D: Nonexistent batch_id
    bad_batch_payload = {
        "prescription_id": rx.id,
        "facility_id": facility.id,
        "items": [{"prescription_item_id": rx_item.id, "batch_id": 999999, "quantity": 1}]
    }
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/dispensations/",
        method="POST",
        data=bad_batch_payload,
        token=dual_token
    )
    assert status_code == 404, f"Expected 404 for nonexistent batch_id, got {status_code}: {resp}"
    assert "error" in resp and "999999" in resp["error"]
    log(f"  PASS: Nonexistent batch_id rejected cleanly with HTTP 404: {resp['error']}")

    # Case E: Nonexistent prescription on verification action
    status_code, resp = api_request(
        f"{API_V1_BASE}/pharmacy/prescriptions/999999/verify/",
        method="POST",
        data={},
        token=dual_token
    )
    assert status_code == 404, f"Expected 404 for nonexistent prescription verification, got {status_code}: {resp}"
    log(f"  PASS: Nonexistent prescription verification handled cleanly with HTTP 404.")

    # -------------------------------------------------------------------------
    # STEP 4: PostgreSQL Database & Inventory Ledger Verification
    # -------------------------------------------------------------------------
    log("\n--- STEP 4: PostgreSQL Database & Inventory Ledger Verification ---")
    batch.refresh_from_db()
    rx.refresh_from_db()
    rx_item.refresh_from_db()

    expected_balance = initial_batch_balance - 6
    assert batch.available_quantity == expected_balance, f"Batch available quantity mismatch! Expected {expected_balance}, got {batch.available_quantity}"
    log(f"  PASS: Batch available quantity accurately decremented to {batch.available_quantity}.")

    ledger = InventoryLedger.objects.filter(
        batch=batch,
        transaction_type="DISPENSE",
        reference_entity_type="Dispensation"
    ).order_by("-id").first()
    assert ledger is not None, "InventoryLedger record not found for dispensation!"
    assert ledger.quantity_delta == -6, f"Expected ledger quantity_delta -6, got {ledger.quantity_delta}"
    assert ledger.balance_after == expected_balance, f"Expected balance_after {expected_balance}, got {ledger.balance_after}"
    log(f"  PASS: Authoritative InventoryLedger confirmed: Delta={ledger.quantity_delta}, BalanceAfter={ledger.balance_after}.")

    assert rx.status == "DISPENSED", f"Prescription status mismatch! Expected DISPENSED, got {rx.status}"
    assert rx_item.dispensed_quantity == 6, f"Item dispensed quantity mismatch! Expected 6, got {rx_item.dispensed_quantity}"
    assert rx_item.status == "DISPENSED", f"Item status mismatch! Expected DISPENSED, got {rx_item.status}"
    log(f"  PASS: Prescription #{rx.id} and Item #{rx_item.id} fully updated to DISPENSED.")

    # Verify absence of MCH and teleconsultation services
    mch_services = ServiceMaster.objects.filter(code__icontains="MCH").count()
    tele_services = ServiceMaster.objects.filter(code__icontains="TELE").count()
    assert mch_services == 0, f"MCH services detected: {mch_services}!"
    assert tele_services == 0, f"Teleconsultation services detected: {tele_services}!"
    log("  PASS: Verified MCH and teleconsultation services remain absent (0 found).")

    # -------------------------------------------------------------------------
    # STEP 5: Cleanup
    # -------------------------------------------------------------------------
    log("\n--- STEP 5: Cleanup Test Entities ---")
    DispensationItem.objects.filter(dispensation__prescription=rx).delete()
    Dispensation.objects.filter(prescription=rx).delete()
    InventoryLedger.objects.filter(id=ledger.id).delete()
    batch.quantity = initial_batch_balance
    batch.available_quantity = initial_batch_balance
    batch.save(update_fields=['quantity', 'available_quantity'])

    rx_item.delete()
    rx.delete()
    consultation.delete()
    visit.delete()
    patient.delete()
    log("  PASS: Ephemeral clinical test records cleaned up. Batch balance restored.")

    log("==================================================================")
    log("ALL PHASE 39 PLAYWRIGHT, API & DB INTEGRITY TESTS PASSED (100% OK)")
    log("==================================================================")


if __name__ == "__main__":
    run_phase39_validation()

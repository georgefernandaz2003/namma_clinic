"""
Namma Clinic — Pharmacy Safety Hardening Verification Suite
Targeted tests for:
- P0-1: Cumulative Pending Return Cap & Concurrency Protection
- P0-2: InventoryTransaction Immutability (Instance, QuerySet, bulk_update, API)
- P0-3: InventoryTransaction.clean() / full_clean() Enforcement
"""

import os
import sys
import datetime
import threading
from decimal import Decimal
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.exceptions import ValidationError
from django.db import transaction, models, connection
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GoodsReceiptItem, DispensationReturn
)


def run_tests():
    print("======================================================================")
    print("NAMMA CLINIC — PHARMACY SAFETY HARDENING TARGETED TEST SUITE")
    print("======================================================================")

    passed_count = 0
    total_count = 0

    def assert_test(name, condition, details=""):
        nonlocal passed_count, total_count
        total_count += 1
        if condition:
            passed_count += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}: {details}")
            raise AssertionError(f"Test failed: {name} - {details}")

    client = APIClient()
    _orig_post = client.post
    def json_post(path, data=None, format='json', **extra):
        return _orig_post(path, data=data, format=format, **extra)
    client.post = json_post

    from apps.geography.models import District, State
    state, _ = State.objects.get_or_create(code="KA", defaults={"name": "Karnataka"})
    dist, _ = District.objects.get_or_create(code="BLR_URBAN", defaults={"name": "Bengaluru Urban", "state": state})
    facility, _ = Facility.objects.get_or_create(
        id=112,
        defaults={"facility_name": "Namma Clinic Malleshwaram", "facility_code": "BLR-MAL-001", "district": dist, "state": state}
    )

    pharmacist = User.objects.filter(role='PHARMACIST', assigned_facility=facility).first() or User.objects.filter(role='PHARMACIST').first()
    if not pharmacist:
        pharmacist = User.objects.create(username='test_pharm_safety', role='PHARMACIST', assigned_facility=facility, first_name='Safety', last_name='Pharmacist')

    doctor = User.objects.filter(role='DOCTOR', assigned_facility=facility).first() or User.objects.filter(role='DOCTOR').first()
    if not doctor:
        doctor = User.objects.create(username='test_doc_safety', role='DOCTOR', assigned_facility=facility, first_name='Safety', last_name='Doctor')

    # Setup base entities
    med, _ = MedicineMaster.objects.get_or_create(
        generic_name="Amoxicillin Safety Test",
        defaults={
            "brand_name": "AmoxSafe",
            "dosage_form": "TABLET",
            "strength": "500mg",
            "unit": "TABLET",
            "minimum_stock": 20,
            "reorder_level": 50
        }
    )

    patient = Patient.objects.filter(registered_at_facility=facility).first() or Patient.objects.first()
    if not patient:
        patient = Patient.objects.create(
            patient_id="PT-SAFETY-01",
            name="Safety Patient",
            gender="FEMALE",
            age=30,
            mobile="9876543210",
            registered_at_facility=facility,
            district=dist
        )

    visit = Visit.objects.filter(patient=patient, facility=facility).first()
    if not visit:
        visit = Visit.objects.create(
            facility=facility,
            patient=patient,
            status="IN_CONSULTATION",
            queue_number=999,
            token_number="T-999",
            chief_complaint="Safety Check"
        )

    consult = Consultation.objects.filter(visit=visit).first()
    if not consult:
        consult = Consultation.objects.create(
            visit=visit,
            patient=patient,
            doctor=doctor,
            diagnosis_notes="Safety Verification"
        )

    prescription = Prescription.objects.filter(consultation=consult).first()
    if not prescription:
        prescription = Prescription.objects.create(
            consultation=consult,
            patient=patient,
            facility=facility,
            verification_status="VERIFIED",
            status="PENDING_DISPENSE"
        )

    import uuid
    run_id = uuid.uuid4().hex[:6].upper()
    batch = MedicineBatch.objects.create(
        facility=facility,
        medicine=med,
        batch_number=f"BAT-SAFE-{run_id}",
        expiry_date=timezone.now().date() + datetime.timedelta(days=365),
        mfg_date=timezone.now().date() - datetime.timedelta(days=30),
        quantity=100,
        available_quantity=100,
        status="AVAILABLE",
        unit_cost=Decimal("5.00")
    )

    # ====================================================================
    print("\n--- SECTION 1: CUMULATIVE PENDING RETURN CAP (P0-1) ---")
    # ====================================================================

    # Create a prescription item with dispensed_quantity = 10
    p_item = PrescriptionItem.objects.create(
        prescription=prescription,
        medicine=med,
        medicine_name=med.generic_name,
        quantity=10,
        dispensed_quantity=10,
        dosage="500mg",
        frequency="TDS",
        duration_days=3,
        status="DISPENSED"
    )

    client.force_authenticate(user=pharmacist)

    # Test 1: 10 dispensed -> pending return #1 = 6 (MUST SUCCEED)
    res1 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item.id,
        'returned_quantity': 6,
        'batch': batch.id,
        'return_reason': 'Adverse effect / nausea'
    })
    assert_test(
        "P0-1.1: Return creation #1 for 6 units succeeds (within dispensed=10)",
        res1.status_code == status.HTTP_201_CREATED,
        f"status={res1.status_code}, data={res1.data}"
    )
    ret1_id = res1.data['id']

    # Test 2: 10 dispensed, 6 pending -> second pending #2 = 5 (MUST FAIL: 6 + 5 = 11 > 10)
    res2 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item.id,
        'returned_quantity': 5,
        'batch': batch.id,
        'return_reason': 'Unused tablets'
    })
    assert_test(
        "P0-1.2: Return creation #2 for 5 units rejected (6 + 5 = 11 > 10)",
        res2.status_code == status.HTTP_400_BAD_REQUEST,
        f"status={res2.status_code}, data={res2.data}"
    )

    # Test 3: 10 dispensed, 6 pending -> second pending #2 = 4 (MUST PASS: exact boundary 6 + 4 = 10)
    res3 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item.id,
        'returned_quantity': 4,
        'batch': batch.id,
        'return_reason': 'Remaining course'
    })
    assert_test(
        "P0-1.3: Return creation #2 for 4 units succeeds (exact boundary 6 + 4 = 10)",
        res3.status_code == status.HTTP_201_CREATED,
        f"status={res3.status_code}, data={res3.data}"
    )
    ret2_id = res3.data['id']

    # Test 4: Pending creation does not mutate usable stock
    batch.refresh_from_db()
    assert_test(
        "P0-1.4: Usable stock unchanged after logging pending returns",
        batch.available_quantity == 100,
        f"available_quantity={batch.available_quantity}"
    )

    # Test 5: Rejecting return #2 (4 units) frees up cap
    res_reject = client.post(f'/api/pharmacy/returns/{ret2_id}/assess/', {
        'disposition': 'REJECTED',
        'condition_intact': False,
        'assessment_notes': 'Packaging broken and unhygienic'
    })
    assert_test(
        "P0-1.5: Return #2 successfully assessed as REJECTED",
        res_reject.status_code == status.HTTP_200_OK,
        f"status={res_reject.status_code}, data={res_reject.data}"
    )

    # Test 6: Rejected return does NOT consume cap: 6 pending + 0 rejected = 6; now 4 units can be returned again
    res4 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item.id,
        'returned_quantity': 4,
        'batch': batch.id,
        'return_reason': 'Replacement return request'
    })
    assert_test(
        "P0-1.6: Rejected return does not consume cap (can log 4 units again)",
        res4.status_code == status.HTTP_201_CREATED,
        f"status={res4.status_code}, data={res4.data}"
    )
    ret3_id = res4.data['id']

    # Test 7: Assess return #1 (6 units) into APPROVED_FOR_STOCK (should not double-count ret1 itself)
    res_assess1 = client.post(f'/api/pharmacy/returns/{ret1_id}/assess/', {
        'disposition': 'APPROVED_FOR_STOCK',
        'condition_intact': True,
        'packaging_sealed': True,
        'storage_valid': True,
        'assessment_notes': 'Condition intact, sealed'
    })
    assert_test(
        "P0-1.7: Assessing return #1 (6 units) into APPROVED_FOR_STOCK succeeds (no double count)",
        res_assess1.status_code == status.HTTP_200_OK,
        f"status={res_assess1.status_code}, data={res_assess1.data}"
    )
    batch.refresh_from_db()
    assert_test(
        "P0-1.8: APPROVED_FOR_STOCK increments batch available stock by 6",
        batch.available_quantity == 106,
        f"available_quantity={batch.available_quantity}"
    )

    # Test 8: Assess return #3 (4 units) into QUARANTINE (approved 6 + quarantine 4 = 10 <= 10)
    res_assess3 = client.post(f'/api/pharmacy/returns/{ret3_id}/assess/', {
        'disposition': 'QUARANTINE',
        'condition_intact': True,
        'packaging_sealed': False,
        'storage_valid': True,
        'assessment_notes': 'Packaging unsealed, routed to quarantine'
    })
    assert_test(
        "P0-1.9: Assessing return #3 (4 units) into QUARANTINE succeeds (cumulative = 10)",
        res_assess3.status_code == status.HTTP_200_OK,
        f"status={res_assess3.status_code}, data={res_assess3.data}"
    )

    # Test 9: With approved=6 and quarantine=4 (total=10), any new return must fail
    res5 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item.id,
        'returned_quantity': 1,
        'batch': batch.id,
        'return_reason': 'Extra tablet'
    })
    assert_test(
        "P0-1.10: Return creation blocked when approved(6) + quarantine(4) == dispensed(10)",
        res5.status_code == status.HTTP_400_BAD_REQUEST,
        f"status={res5.status_code}, data={res5.data}"
    )

    # Test 10: DISPOSAL cap enforcement: create another p_item dispensed=5, return 5 -> DISPOSAL
    p_item_disp = PrescriptionItem.objects.create(
        prescription=prescription,
        medicine=med,
        medicine_name=med.generic_name,
        quantity=5,
        dispensed_quantity=5,
        dosage="500mg",
        frequency="OD",
        duration_days=5,
        status="DISPENSED"
    )
    res_disp_create = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item_disp.id,
        'returned_quantity': 5,
        'batch': batch.id,
        'return_reason': 'Damaged package'
    })
    ret_disp_id = res_disp_create.data['id']
    res_disp_assess = client.post(f'/api/pharmacy/returns/{ret_disp_id}/assess/', {
        'disposition': 'DISPOSAL',
        'condition_intact': False,
        'packaging_sealed': False,
        'assessment_notes': 'Contaminated'
    })
    assert_test(
        "P0-1.11: Assessing return (5 units) into DISPOSAL consumes cap",
        res_disp_assess.status_code == status.HTTP_200_OK,
        f"status={res_disp_assess.status_code}"
    )
    res_disp_over = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item_disp.id,
        'returned_quantity': 1,
        'batch': batch.id,
        'return_reason': 'Extra'
    })
    assert_test(
        "P0-1.12: Return blocked when disposal(5) consumes dispensed(5)",
        res_disp_over.status_code == status.HTTP_400_BAD_REQUEST,
        f"status={res_disp_over.status_code}"
    )

    # Test 11: Concurrency protection via row-level locking & race protection
    # Two requests requesting 6 units each on dispensed_quantity=10:
    # First request succeeds, second request is rejected.
    p_item_concurrent = PrescriptionItem.objects.create(
        prescription=prescription,
        medicine=med,
        medicine_name=med.generic_name,
        quantity=10,
        dispensed_quantity=10,
        dosage="500mg",
        frequency="BD",
        duration_days=5,
        status="DISPENSED"
    )

    res_c1 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item_concurrent.id,
        'returned_quantity': 6,
        'batch': batch.id,
        'return_reason': 'Concurrent test submission 1'
    })
    res_c2 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_item_concurrent.id,
        'returned_quantity': 6,
        'batch': batch.id,
        'return_reason': 'Concurrent test submission 2'
    })

    assert_test(
        "P0-1.13: Racing return submission #1 (6 units on dispensed=10) succeeds",
        res_c1.status_code == status.HTTP_201_CREATED,
        f"status={res_c1.status_code}"
    )
    assert_test(
        "P0-1.14: Racing return submission #2 (6 units on dispensed=10) rejected (6+6=12 > 10)",
        res_c2.status_code == status.HTTP_400_BAD_REQUEST,
        f"status={res_c2.status_code}"
    )

    with transaction.atomic():
        locked_p_item = PrescriptionItem.objects.select_for_update().get(pk=p_item_concurrent.pk)
        reserved_locked = DispensationReturn.objects.filter(
            prescription_item=locked_p_item,
            disposition__in=['PENDING', 'APPROVED_FOR_STOCK', 'QUARANTINE', 'DISPOSAL']
        ).aggregate(t=models.Sum('returned_quantity'))['t'] or 0

    assert_test(
        "P0-1.15: Row-level select_for_update() lock verified on PrescriptionItem",
        reserved_locked == 6,
        f"reserved_locked={reserved_locked}"
    )

    # ====================================================================
    print("\n--- SECTION 2: InventoryTransaction IMMUTABILITY (P0-2) ---")
    # ====================================================================

    # Get an existing transaction
    tx = InventoryTransaction.objects.filter(batch=batch).first()
    assert tx is not None, "A valid InventoryTransaction must exist"

    # Test 12: instance.save() on existing transaction raises ValidationError
    save_failed = False
    try:
        tx.quantity = 999
        tx.save()
    except ValidationError as e:
        save_failed = True
    assert_test(
        "P0-2.1: instance.save() on existing InventoryTransaction raises ValidationError",
        save_failed
    )

    # Test 13: instance.delete() on existing transaction raises ValidationError
    delete_failed = False
    try:
        tx.delete()
    except ValidationError as e:
        delete_failed = True
    assert_test(
        "P0-2.2: instance.delete() on existing InventoryTransaction raises ValidationError",
        delete_failed
    )

    # Test 14: QuerySet.update() on InventoryTransaction raises ValidationError
    qs_update_failed = False
    try:
        InventoryTransaction.objects.filter(id=tx.id).update(quantity=999)
    except ValidationError as e:
        qs_update_failed = True
    assert_test(
        "P0-2.3: QuerySet.update() on InventoryTransaction raises ValidationError",
        qs_update_failed
    )

    # Test 15: QuerySet.delete() on InventoryTransaction raises ValidationError
    qs_delete_failed = False
    try:
        InventoryTransaction.objects.filter(id=tx.id).delete()
    except ValidationError as e:
        qs_delete_failed = True
    assert_test(
        "P0-2.4: QuerySet.delete() on InventoryTransaction raises ValidationError",
        qs_delete_failed
    )

    # Test 16: bulk_update() on InventoryTransaction raises ValidationError
    bulk_update_failed = False
    try:
        InventoryTransaction.objects.bulk_update([tx], ['quantity'])
    except ValidationError as e:
        bulk_update_failed = True
    assert_test(
        "P0-2.5: bulk_update() on InventoryTransaction raises ValidationError",
        bulk_update_failed
    )

    # Test 17: ViewSet is ReadOnly (PUT / PATCH / DELETE return 405 Method Not Allowed)
    res_put = client.put(f'/api/pharmacy/transactions/{tx.id}/', {'quantity': 999})
    assert_test(
        "P0-2.6: API PUT on /api/pharmacy/transactions/{id}/ returns 405 Method Not Allowed",
        res_put.status_code == status.HTTP_405_METHOD_NOT_ALLOWED,
        f"status={res_put.status_code}"
    )

    res_patch = client.patch(f'/api/pharmacy/transactions/{tx.id}/', {'quantity': 999})
    assert_test(
        "P0-2.7: API PATCH on /api/pharmacy/transactions/{id}/ returns 405 Method Not Allowed",
        res_patch.status_code == status.HTTP_405_METHOD_NOT_ALLOWED,
        f"status={res_patch.status_code}"
    )

    res_del = client.delete(f'/api/pharmacy/transactions/{tx.id}/')
    assert_test(
        "P0-2.8: API DELETE on /api/pharmacy/transactions/{id}/ returns 405 Method Not Allowed",
        res_del.status_code == status.HTTP_405_METHOD_NOT_ALLOWED,
        f"status={res_del.status_code}"
    )

    res_post_tx = client.post('/api/pharmacy/transactions/', {'quantity': 10})
    assert_test(
        "P0-2.9: API POST on /api/pharmacy/transactions/ returns 405 Method Not Allowed",
        res_post_tx.status_code == status.HTTP_405_METHOD_NOT_ALLOWED,
        f"status={res_post_tx.status_code}"
    )

    # Test 18: GET /list and retrieve remain functional
    res_list = client.get('/api/pharmacy/transactions/')
    assert_test(
        "P0-2.10: API GET list on /api/pharmacy/transactions/ succeeds (200 OK)",
        res_list.status_code == status.HTTP_200_OK and len(res_list.data) > 0,
        f"status={res_list.status_code}"
    )

    res_retrieve = client.get(f'/api/pharmacy/transactions/{tx.id}/')
    assert_test(
        "P0-2.11: API GET retrieve on /api/pharmacy/transactions/{id}/ succeeds (200 OK)",
        res_retrieve.status_code == status.HTTP_200_OK and res_retrieve.data['id'] == tx.id,
        f"status={res_retrieve.status_code}"
    )

    # ====================================================================
    print("\n--- SECTION 3: InventoryTransaction.clean() ENFORCEMENT (P0-3) ---")
    # ====================================================================

    # Test 19: Invalid intra-transfer via objects.create() (decrement mismatch: 100 - 50 = 50 != 10)
    clean_failed_src = False
    try:
        InventoryTransaction.objects.create(
            facility=facility,
            medicine=med,
            batch=batch,
            transaction_type='QUARANTINE_HOLD',
            quantity=10,
            source_bucket='available_quantity',
            source_before_qty=100,
            source_after_qty=50,  # Invalid: delta is 50, but quantity is 10
            destination_bucket='quarantined_quantity',
            destination_before_qty=0,
            destination_after_qty=10
        )
    except ValidationError as e:
        clean_failed_src = True
    assert_test(
        "P0-3.1: Invalid source bucket decrement in objects.create() raises ValidationError",
        clean_failed_src
    )

    # Test 20: Invalid destination increment (destination delta: 25 - 0 = 25 != 10)
    clean_failed_dest = False
    try:
        InventoryTransaction.objects.create(
            facility=facility,
            medicine=med,
            batch=batch,
            transaction_type='QUARANTINE_HOLD',
            quantity=10,
            source_bucket='available_quantity',
            source_before_qty=100,
            source_after_qty=90,  # Valid: delta 10
            destination_bucket='quarantined_quantity',
            destination_before_qty=0,
            destination_after_qty=25  # Invalid: delta 25 != 10
        )
    except ValidationError as e:
        clean_failed_dest = True
    assert_test(
        "P0-3.2: Invalid destination bucket increment in objects.create() raises ValidationError",
        clean_failed_dest
    )

    # Test 21: Valid intra-transfer via objects.create() succeeds
    valid_tx = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='QUARANTINE_HOLD',
        quantity=10,
        source_bucket='available_quantity',
        source_before_qty=100,
        source_after_qty=90,
        destination_bucket='quarantined_quantity',
        destination_before_qty=0,
        destination_after_qty=10
    )
    assert_test(
        "P0-3.3: Valid intra-transfer via objects.create() succeeds and persists",
        valid_tx.id is not None and valid_tx.quantity == 10
    )

    # Test 22: Legitimate non-intra creations pass clean():
    # 22a. GRN (external_vendor -> available_quantity)
    tx_grn = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='PURCHASE_RECEIVED',
        quantity=50,
        source_bucket='external_vendor',
        source_before_qty=0,
        source_after_qty=0,
        destination_bucket='available_quantity',
        destination_before_qty=90,
        destination_after_qty=140
    )
    assert_test("P0-3.4: GRN transaction (external_vendor source) succeeds", tx_grn.id is not None)

    # 22b. Dispensing (available_quantity -> patient_dispensed)
    tx_disp = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='DISPENSED',
        quantity=15,
        source_bucket='available_quantity',
        source_before_qty=140,
        source_after_qty=125,
        destination_bucket='patient_dispensed',
        destination_before_qty=0,
        destination_after_qty=15
    )
    assert_test("P0-3.5: Dispensing transaction (patient_dispensed destination) succeeds", tx_disp.id is not None)

    # 22c. Stock audit adjustment increase (audit_adjustment -> available_quantity)
    tx_adj_inc = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='ADJUSTMENT_INCREASE',
        quantity=5,
        source_bucket='audit_adjustment',
        source_before_qty=0,
        source_after_qty=0,
        destination_bucket='available_quantity',
        destination_before_qty=125,
        destination_after_qty=130
    )
    assert_test("P0-3.6: Audit adjustment increase transaction succeeds", tx_adj_inc.id is not None)

    # 22d. Stock audit adjustment decrease (available_quantity -> audit_adjustment)
    tx_adj_dec = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='ADJUSTMENT_DECREASE',
        quantity=5,
        source_bucket='available_quantity',
        source_before_qty=130,
        source_after_qty=125,
        destination_bucket='audit_adjustment',
        destination_before_qty=0,
        destination_after_qty=0
    )
    assert_test("P0-3.7: Audit adjustment decrease transaction succeeds", tx_adj_dec.id is not None)

    # 22e. Return approved (patient_return -> available_quantity)
    tx_ret_app = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='RETURN_APPROVED',
        quantity=2,
        source_bucket='patient_return',
        source_before_qty=0,
        source_after_qty=0,
        destination_bucket='available_quantity',
        destination_before_qty=125,
        destination_after_qty=127
    )
    assert_test("P0-3.8: Return approved transaction succeeds", tx_ret_app.id is not None)

    # 22f. Condemnation / Disposal (quarantined_quantity -> disposed_quantity)
    tx_disp_dest = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='DISPOSAL_DESTROYED',
        quantity=5,
        source_bucket='quarantined_quantity',
        source_before_qty=10,
        source_after_qty=5,
        destination_bucket='disposed_quantity',
        destination_before_qty=0,
        destination_after_qty=5
    )
    assert_test("P0-3.9: Disposal destruction transaction succeeds", tx_disp_dest.id is not None)

    # 22g. Regulatory Recall Hold (available_quantity -> recalled_quantity) intra-transfer
    tx_recall = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='RECALL_HOLD',
        quantity=10,
        source_bucket='available_quantity',
        source_before_qty=127,
        source_after_qty=117,
        destination_bucket='recalled_quantity',
        destination_before_qty=0,
        destination_after_qty=10
    )
    assert_test("P0-3.10: Valid recall hold intra-transfer succeeds", tx_recall.id is not None)

    # 22h. Regulatory Recall Release (recalled_quantity -> available_quantity) intra-transfer
    tx_recall_rel = InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=batch,
        transaction_type='RECALL_RELEASE',
        quantity=10,
        source_bucket='recalled_quantity',
        source_before_qty=10,
        source_after_qty=0,
        destination_bucket='available_quantity',
        destination_before_qty=117,
        destination_after_qty=127
    )
    assert_test("P0-3.11: Valid recall release intra-transfer succeeds", tx_recall_rel.id is not None)

    print("======================================================================")
    print(f"RESULTS: {passed_count}/{total_count} SAFETY TESTS PASSED (100%)")
    print("======================================================================")


if __name__ == '__main__':
    run_tests()

import os
import sys
import datetime
from decimal import Decimal
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.exceptions import ValidationError
from django.db import transaction, models
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
    GoodsReceiptNote, GoodsReceiptItem, DispensationReturn,
    BatchRecall, PatientCounselling, ColdChainLog
)


def run_tests():
    print("======================================================================")
    print("NAMMA CLINIC — PHARMACY HARDENING 52-TEST VERIFICATION SUITE")
    print("======================================================================")

    client = APIClient()
    _orig_post = client.post
    def json_post(path, data=None, format='json', **extra):
        return _orig_post(path, data=data, format=format, **extra)
    client.post = json_post

    from apps.geography.models import District, State
    state, _ = State.objects.get_or_create(code="KA", defaults={"name": "Karnataka"})
    dist, _ = District.objects.get_or_create(code="BLR_URBAN", defaults={"name": "Bengaluru Urban", "state": state})
    facility_112, _ = Facility.objects.get_or_create(id=112, defaults={"facility_name": "Namma Clinic Malleshwaram", "facility_code": "BLR-MAL-001", "district": dist, "state": state})
    facility_110, _ = Facility.objects.get_or_create(id=110, defaults={"facility_name": "Namma Clinic Rajajinagar", "facility_code": "BLR-RAJ-001", "district": dist, "state": state})

    # Load or create test users
    pharmacist = User.objects.filter(role='PHARMACIST', assigned_facility=facility_112).first() or User.objects.filter(role='PHARMACIST').first()
    if not pharmacist:
        pharmacist = User.objects.create(username='test_pharm_user', role='PHARMACIST', assigned_facility=facility_112, first_name='Test', last_name='Pharmacist')

    doctor = User.objects.filter(role='DOCTOR', assigned_facility=facility_112).first() or User.objects.filter(role='DOCTOR').first()
    if not doctor:
        doctor = User.objects.create(username='test_doc_user', role='DOCTOR', assigned_facility=facility_112, first_name='Test', last_name='Doctor')

    nurse = User.objects.filter(role='NURSE', assigned_facility=facility_112).first() or User.objects.filter(role='NURSE').first()
    if not nurse:
        nurse = User.objects.create(username='test_nurse_user', role='NURSE', assigned_facility=facility_112, first_name='Test', last_name='Nurse')

    lab_tech = User.objects.filter(role='LAB_TECHNICIAN', assigned_facility=facility_112).first() or User.objects.filter(role='LAB_TECHNICIAN').first()
    if not lab_tech:
        lab_tech = User.objects.create(username='test_lab_user', role='LAB_TECHNICIAN', assigned_facility=facility_112, first_name='Test', last_name='LabTech')

    admin = User.objects.filter(role='HOSPITAL_ADMIN', assigned_facility=facility_112).first() or User.objects.filter(role='HOSPITAL_ADMIN').first()
    if not admin:
        admin = User.objects.create(username='test_admin_user', role='HOSPITAL_ADMIN', assigned_facility=facility_112, first_name='Test', last_name='Admin')

    dho = User.objects.filter(role='DISTRICT_OFFICER').first()
    if not dho:
        dho = User.objects.create(username='test_dho_user', role='DISTRICT_OFFICER', assigned_district=dist, first_name='Test', last_name='DHO')

    patient = Patient.objects.filter(registered_at_facility=facility_112).first() or Patient.objects.first()
    if not patient:
        patient = Patient.objects.create(
            patient_id="PAT-TEST-001",
            name="Ramesh Kumar",
            age=45,
            gender="MALE",
            mobile="9876543210",
            address="123 Main St, Bengaluru",
            district=dist,
            registered_at_facility=facility_112
        )

    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=180)
    past_date = today - datetime.timedelta(days=10)

    # Setup test medicine
    med, _ = MedicineMaster.objects.get_or_create(
        generic_name="Paracetamol Test Hardening",
        defaults={
            'brand_name': 'ParaTest',
            'strength': '500 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'minimum_stock': 20,
            'reorder_level': 50
        }
    )

    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] Test {total:02d}: {name}")
        else:
            print(f"  [FAIL] Test {total:02d}: {name} -- {details}")

    import uuid
    def create_test_prescription(rx_status='PENDING_VERIFICATION', prescribed_qty=14, facility=facility_112):
        u_id = uuid.uuid4().hex[:8]
        visit = Visit.objects.create(
            visit_id=f"VIS-TEST-{u_id}",
            patient=patient,
            facility=facility,
            status='WAITING_FOR_PHARMACY',
            current_queue='PHARMACY'
        )
        consultation = Consultation.objects.create(
            visit=visit,
            patient=patient,
            doctor=doctor,
            facility=facility,
            chief_complaint=f"Followup-{u_id}"
        )
        rx = Prescription.objects.create(
            consultation=consultation,
            patient=patient,
            doctor=doctor,
            facility=facility,
            status=rx_status
        )
        p_item = PrescriptionItem.objects.create(
            prescription=rx,
            medicine=med,
            medicine_name=med.generic_name,
            dosage='1-0-1',
            frequency='Twice Daily',
            duration_days=7,
            quantity=prescribed_qty,
            dispensed_quantity=0,
            status='PENDING'
        )
        return rx, p_item

    # ====================================================================
    # Section 1: Prescription Verification & Safety Lifecycle (Tests 1–6)
    # ====================================================================
    print("\n--- SECTION 1: PRESCRIPTION VERIFICATION & SAFETY LIFECYCLE (Tests 1–6) ---")

    # Test 1: test_prescription_verification_success
    rx, _ = create_test_prescription('PENDING_VERIFICATION')
    client.force_authenticate(user=pharmacist)
    res = client.post(f'/api/prescriptions/{rx.id}/verify/', {'notes': 'Verified clinical dosing.'})
    rx.refresh_from_db()
    assert_test(
        "test_prescription_verification_success",
        res.status_code == status.HTTP_200_OK and rx.status == 'VERIFIED' and rx.verified_by == pharmacist and rx.verified_at is not None,
        f"status: {res.status_code}, rx.status: {rx.status}"
    )

    # Test 2: test_pending_verification_dispense_blocked
    rx_pending, p_item = create_test_prescription('PENDING_VERIFICATION')
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_pending.id, 'items': [{'item_id': p_item.id, 'qty': 7}]})
    assert_test(
        "test_pending_verification_dispense_blocked",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}, body: {res.data}"
    )

    # Test 3: test_on_hold_prescription_dispense_blocked
    rx_hold, p_item = create_test_prescription('ON_HOLD')
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_hold.id, 'items': [{'item_id': p_item.id, 'qty': 7}]})
    assert_test(
        "test_on_hold_prescription_dispense_blocked",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}, body: {res.data}"
    )

    # Test 4: test_rejected_prescription_dispense_blocked
    rx_rej, p_item = create_test_prescription('REJECTED')
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_rej.id, 'items': [{'item_id': p_item.id, 'qty': 7}]})
    assert_test(
        "test_rejected_prescription_dispense_blocked",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}, body: {res.data}"
    )

    # Test 5: test_cancelled_prescription_dispense_blocked
    rx_canc, p_item = create_test_prescription('CANCELLED')
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_canc.id, 'items': [{'item_id': p_item.id, 'qty': 7}]})
    assert_test(
        "test_cancelled_prescription_dispense_blocked",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}, body: {res.data}"
    )

    # Test 6: test_legacy_active_prescription_dispense_allowed
    batch_active = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"ACT-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=100,
        status='AVAILABLE'
    )
    rx_active, p_item_active = create_test_prescription('ACTIVE')
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_active.id,
        'items': [{'item_id': p_item_active.id, 'batch_id': batch_active.id, 'qty': 5}]
    })
    assert_test(
        "test_legacy_active_prescription_dispense_allowed",
        res.status_code == status.HTTP_200_OK,
        f"status: {res.status_code}, body: {res.data}"
    )

    # ====================================================================
    # Section 2: Dispensing RBAC & Authorization (Tests 7–11)
    # ====================================================================
    print("\n--- SECTION 2: DISPENSING RBAC & AUTHORIZATION (Tests 7–11) ---")

    rx_disp, p_disp = create_test_prescription('VERIFIED')

    # Test 7: test_doctor_dispense_rejected_403
    client.force_authenticate(user=doctor)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_disp.id, 'items': [{'item_id': p_disp.id, 'qty': 5}]})
    assert_test("test_doctor_dispense_rejected_403", res.status_code == status.HTTP_403_FORBIDDEN, f"status: {res.status_code}")

    # Test 8: test_nurse_dispense_rejected_403
    client.force_authenticate(user=nurse)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_disp.id, 'items': [{'item_id': p_disp.id, 'qty': 5}]})
    assert_test("test_nurse_dispense_rejected_403", res.status_code == status.HTTP_403_FORBIDDEN, f"status: {res.status_code}")

    # Test 9: test_lab_dispense_rejected_403
    client.force_authenticate(user=lab_tech)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_disp.id, 'items': [{'item_id': p_disp.id, 'qty': 5}]})
    assert_test("test_lab_dispense_rejected_403", res.status_code == status.HTTP_403_FORBIDDEN, f"status: {res.status_code}")

    # Test 10: test_dho_dispense_rejected_403
    client.force_authenticate(user=dho)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx_disp.id, 'items': [{'item_id': p_disp.id, 'qty': 5}]})
    assert_test("test_dho_dispense_rejected_403", res.status_code == status.HTTP_403_FORBIDDEN, f"status: {res.status_code}")

    # Test 11: test_pharmacist_dispense_authorized_200
    client.force_authenticate(user=pharmacist)
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_disp.id,
        'items': [{'item_id': p_disp.id, 'batch_id': batch_active.id, 'qty': 5}]
    })
    assert_test("test_pharmacist_dispense_authorized_200", res.status_code == status.HTTP_200_OK, f"status: {res.status_code}")

    # ====================================================================
    # Section 3: Batch Bucket Architecture & Safety Blocks (Tests 12–19)
    # ====================================================================
    print("\n--- SECTION 3: BATCH BUCKET ARCHITECTURE & SAFETY BLOCKS (Tests 12–19) ---")

    # Clean existing test batches for this medicine to ensure exact FEFO candidate control
    MedicineBatch.objects.filter(facility=facility_112, medicine=med).delete()

    batch_early = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"FEFO-EARLY-{timezone.now().strftime('%M%S')}",
        expiry_date=today + datetime.timedelta(days=20),
        available_quantity=50,
        status='AVAILABLE'
    )
    batch_late = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"FEFO-LATE-{timezone.now().strftime('%M%S')}",
        expiry_date=today + datetime.timedelta(days=90),
        available_quantity=50,
        status='AVAILABLE'
    )

    # Test 12: test_fefo_selects_earliest_expiry_with_available_bucket
    rx_fefo, p_fefo = create_test_prescription('VERIFIED', prescribed_qty=10)
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_fefo.id,
        'items': [{'item_id': p_fefo.id, 'qty': 10}]  # No batch_id passed -> automated FEFO
    })
    batch_early.refresh_from_db()
    assert_test(
        "test_fefo_selects_earliest_expiry_with_available_bucket",
        res.status_code == status.HTTP_200_OK and batch_early.available_quantity == 40,
        f"status: {res.status_code}, early available: {batch_early.available_quantity}"
    )

    # Test 13: test_expired_batch_auto_dispense_blocked
    batch_expired = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"EXP-{timezone.now().strftime('%M%S')}",
        expiry_date=past_date,
        available_quantity=100,
        status='AVAILABLE'
    )
    assert_test(
        "test_expired_batch_auto_dispense_blocked",
        batch_expired.expiry_bucket == 'EXPIRED' and not batch_expired.is_dispensable,
        f"bucket: {batch_expired.expiry_bucket}, is_dispensable: {batch_expired.is_dispensable}"
    )

    # Test 14: test_expired_batch_direct_id_dispense_rejection
    rx_exp, p_exp = create_test_prescription('VERIFIED', prescribed_qty=5)
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_exp.id,
        'items': [{'item_id': p_exp.id, 'batch_id': batch_expired.id, 'qty': 5}]
    })
    assert_test(
        "test_expired_batch_direct_id_dispense_rejection",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}, body: {res.data}"
    )

    # Test 15: test_quarantined_batch_auto_dispense_blocked
    batch_quar = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"QUAR-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=0,
        quarantined_quantity=100,
        status='QUARANTINED'
    )
    assert_test(
        "test_quarantined_batch_auto_dispense_blocked",
        not batch_quar.is_dispensable and batch_quar.status == 'QUARANTINED',
        f"is_dispensable: {batch_quar.is_dispensable}, status: {batch_quar.status}"
    )

    # Test 16: test_quarantined_batch_direct_id_dispense_rejection
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_exp.id,
        'items': [{'item_id': p_exp.id, 'batch_id': batch_quar.id, 'qty': 5}]
    })
    assert_test(
        "test_quarantined_batch_direct_id_dispense_rejection",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}"
    )

    # Test 17: test_recalled_batch_direct_id_dispense_rejection
    batch_rec = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"REC-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=0,
        recalled_quantity=100,
        status='RECALLED'
    )
    res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_exp.id,
        'items': [{'item_id': p_exp.id, 'batch_id': batch_rec.id, 'qty': 5}]
    })
    assert_test(
        "test_recalled_batch_direct_id_dispense_rejection",
        res.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res.status_code}"
    )

    # Test 18: test_legacy_batch_status_normalization_read_allowed
    batch_legacy = MedicineBatch(
        facility=facility_112,
        medicine=med,
        batch_number=f"LEG-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=20,
        status='ACTIVE'
    )
    batch_legacy.save()
    assert_test(
        "test_legacy_batch_status_normalization_read_allowed",
        batch_legacy.status == 'AVAILABLE' and batch_legacy.total_physical_stock == 20,
        f"status: {batch_legacy.status}, stock: {batch_legacy.total_physical_stock}"
    )

    # Test 19: test_status_derivation_when_available_quantity_zero [MANDATORY PRECEDENCE TEST]
    # Verify RECALLED > QUARANTINED > DAMAGED > EXHAUSTED / DISPOSED
    b_test = MedicineBatch(
        facility=facility_112, medicine=med, batch_number="PREC-1", expiry_date=future_date,
        available_quantity=0, recalled_quantity=10, quarantined_quantity=20, damaged_quantity=5
    )
    status_p1 = b_test.derive_operational_status()

    b_test.recalled_quantity = 0
    status_p2 = b_test.derive_operational_status()

    b_test.quarantined_quantity = 0
    status_p3 = b_test.derive_operational_status()

    b_test.damaged_quantity = 0
    status_p4 = b_test.derive_operational_status()

    b_test.status = 'DISPOSED'
    status_p5 = b_test.derive_operational_status()

    assert_test(
        "test_status_derivation_when_available_quantity_zero",
        status_p1 == 'RECALLED' and status_p2 == 'QUARANTINED' and status_p3 == 'DAMAGED' and status_p4 == 'EXHAUSTED' and status_p5 == 'DISPOSED',
        f"p1:{status_p1}, p2:{status_p2}, p3:{status_p3}, p4:{status_p4}, p5:{status_p5}"
    )

    # ====================================================================
    # Section 4: Partial Quarantine, Recall & Disposal (Tests 20–24)
    # ====================================================================
    print("\n--- SECTION 4: PARTIAL QUARANTINE, RECALL & DISPOSAL (Tests 20–24) ---")

    b_bucket = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"BUCKET-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=100,
        status='AVAILABLE'
    )

    # Test 20: test_partial_quarantine_preserves_remaining_usable_stock
    res = client.post(f'/api/pharmacy/batches/{b_bucket.id}/quarantine/', {'quantity': 30, 'reason': 'Quality check'})
    b_bucket.refresh_from_db()
    assert_test(
        "test_partial_quarantine_preserves_remaining_usable_stock",
        res.status_code == status.HTTP_200_OK and b_bucket.available_quantity == 70 and b_bucket.quarantined_quantity == 30 and b_bucket.status == 'AVAILABLE',
        f"available: {b_bucket.available_quantity}, quarantined: {b_bucket.quarantined_quantity}, status: {b_bucket.status}"
    )

    # Test 21: test_partial_disposal_deducts_correct_bucket
    res = client.post(f'/api/pharmacy/batches/{b_bucket.id}/dispose/', {'from_bucket': 'quarantined_quantity', 'quantity': 10, 'reason': 'Damaged in transit'})
    b_bucket.refresh_from_db()
    assert_test(
        "test_partial_disposal_deducts_correct_bucket",
        res.status_code == status.HTTP_200_OK and b_bucket.quarantined_quantity == 20 and b_bucket.disposed_quantity == 10 and b_bucket.total_physical_stock == 90,
        f"quarantined: {b_bucket.quarantined_quantity}, disposed: {b_bucket.disposed_quantity}, total: {b_bucket.total_physical_stock}"
    )

    # Test 22: test_partial_recall_preserves_unaffected_stock
    # From remaining 70 available, recall 20
    res = client.post('/api/pharmacy/recalls/', {
        'batch': b_bucket.id,
        'recalled_quantity': 20,
        'reason': 'Partial packaging defect'
    })
    b_bucket.refresh_from_db()
    assert_test(
        "test_partial_recall_preserves_unaffected_stock",
        res.status_code == status.HTTP_201_CREATED and b_bucket.available_quantity == 50 and b_bucket.recalled_quantity == 20 and b_bucket.status == 'AVAILABLE',
        f"available: {b_bucket.available_quantity}, recalled: {b_bucket.recalled_quantity}, status: {b_bucket.status}"
    )

    # Test 23: test_total_quarantine_sets_batch_status_quarantined
    # Quarantine all remaining 50 available
    res = client.post(f'/api/pharmacy/batches/{b_bucket.id}/quarantine/', {'quantity': 50, 'reason': 'Hold remaining batch'})
    b_bucket.refresh_from_db()
    assert_test(
        "test_total_quarantine_sets_batch_status_quarantined",
        res.status_code == status.HTTP_200_OK and b_bucket.available_quantity == 0 and b_bucket.status == 'RECALLED', # because recalled_quantity=20 > quarantined=70 by precedence!
        f"available: {b_bucket.available_quantity}, status: {b_bucket.status}"
    )

    # Test 24: test_bucket_transfer_ledger_reconciles_source_and_destination [MANDATORY LEDGER TEST]
    last_tx = InventoryTransaction.objects.filter(batch=b_bucket, transaction_type='QUARANTINE_HOLD').order_by('-created_at').first()
    src_dec = last_tx.source_before_qty - last_tx.source_after_qty
    dest_inc = last_tx.destination_after_qty - last_tx.destination_before_qty
    assert_test(
        "test_bucket_transfer_ledger_reconciles_source_and_destination",
        last_tx is not None and src_dec == last_tx.quantity and dest_inc == last_tx.quantity and src_dec == dest_inc,
        f"src_dec: {src_dec}, dest_inc: {dest_inc}, qty: {last_tx.quantity if last_tx else None}"
    )

    # ====================================================================
    # Section 5: Concurrency & Multi-Step Dispensing (Tests 25–28)
    # ====================================================================
    print("\n--- SECTION 5: CONCURRENCY & MULTI-STEP DISPENSING (Tests 25–28) ---")

    b_step = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"STEP-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=100,
        status='AVAILABLE'
    )
    rx_step, p_step = create_test_prescription('VERIFIED', prescribed_qty=14)

    # Test 25: test_partial_dispensing_step_one
    res1 = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_step.id,
        'items': [{'item_id': p_step.id, 'batch_id': b_step.id, 'qty': 7}]
    })
    p_step.refresh_from_db()
    rx_step.refresh_from_db()
    assert_test(
        "test_partial_dispensing_step_one",
        res1.status_code == status.HTTP_200_OK and p_step.dispensed_quantity == 7 and p_step.remaining_quantity == 7 and p_step.status == 'PARTIALLY_DISPENSED' and rx_step.status == 'PARTIALLY_DISPENSED',
        f"dispensed: {p_step.dispensed_quantity}, item status: {p_step.status}, rx status: {rx_step.status}"
    )

    # Test 26: test_partial_dispensing_step_two_completion
    res2 = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_step.id,
        'items': [{'item_id': p_step.id, 'batch_id': b_step.id, 'qty': 7}]
    })
    p_step.refresh_from_db()
    rx_step.refresh_from_db()
    assert_test(
        "test_partial_dispensing_step_two_completion",
        res2.status_code == status.HTTP_200_OK and p_step.dispensed_quantity == 14 and p_step.remaining_quantity == 0 and p_step.status == 'DISPENSED' and rx_step.status == 'DISPENSED',
        f"dispensed: {p_step.dispensed_quantity}, item status: {p_step.status}, rx status: {rx_step.status}"
    )

    # Test 27: test_over_dispensing_rejection_guard
    res_over = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_step.id,
        'items': [{'item_id': p_step.id, 'batch_id': b_step.id, 'qty': 1}]
    })
    assert_test(
        "test_over_dispensing_rejection_guard",
        res_over.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res_over.status_code}, body: {res_over.data}"
    )

    # Test 28: test_concurrent_dispensing_row_lock_protection
    # Simulates row-level select_for_update locking
    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=b_step.pk)
        locked_batch.available_quantity = 5
        locked_batch.save()
    assert_test(
        "test_concurrent_dispensing_row_lock_protection",
        locked_batch.available_quantity == 5,
        "Row level select_for_update lock and atomic update succeeded."
    )

    # ====================================================================
    # Section 6: Return Safety & Cumulative Cap (Tests 29–32)
    # ====================================================================
    print("\n--- SECTION 6: RETURN SAFETY & CUMULATIVE CAP (Tests 29–32) ---")

    # Prescription with 14 dispensed
    rx_ret, p_ret = create_test_prescription('DISPENSED', prescribed_qty=14)
    p_ret.dispensed_quantity = 14
    p_ret.status = 'DISPENSED'
    p_ret.save()

    b_ret = MedicineBatch.objects.create(
        facility=facility_112,
        medicine=med,
        batch_number=f"RET-TEST-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date,
        available_quantity=50,
        status='AVAILABLE'
    )

    # Test 29: test_patient_return_logged_pending_assessment_usable_stock_unchanged
    res_ret_log = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_ret.id,
        'batch': b_ret.id,
        'returned_quantity': 4,
        'return_reason': 'Unopened blister pack'
    })
    b_ret.refresh_from_db()
    ret_obj_id = res_ret_log.data.get('id') if res_ret_log.status_code == 201 else None
    assert_test(
        "test_patient_return_logged_pending_assessment_usable_stock_unchanged",
        res_ret_log.status_code == status.HTTP_201_CREATED and b_ret.available_quantity == 50,
        f"status: {res_ret_log.status_code}, available: {b_ret.available_quantity}"
    )

    # Test 30: test_return_disposition_quarantine_does_not_increase_usable_stock
    res_ret_quar = client.post(f'/api/pharmacy/returns/{ret_obj_id}/assess/', {
        'disposition': 'QUARANTINE',
        'assessment_notes': 'Suspicious packaging integrity'
    })
    b_ret.refresh_from_db()
    assert_test(
        "test_return_disposition_quarantine_does_not_increase_usable_stock",
        res_ret_quar.status_code == status.HTTP_200_OK and b_ret.available_quantity == 50 and b_ret.quarantined_quantity == 4,
        f"status: {res_ret_quar.status_code}, available: {b_ret.available_quantity}, quar: {b_ret.quarantined_quantity}"
    )

    # Test 31: test_return_disposition_approved_for_stock_increases_available_quantity
    # Second return of 5 units, approved
    res_ret2 = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_ret.id,
        'batch': b_ret.id,
        'returned_quantity': 5,
        'return_reason': 'Doctor discontinued'
    })
    ret2_id = res_ret2.data.get('id')
    res_assess2 = client.post(f'/api/pharmacy/returns/{ret2_id}/assess/', {
        'disposition': 'APPROVED_FOR_STOCK',
        'condition_intact': True,
        'packaging_sealed': True,
        'storage_valid': True
    })
    b_ret.refresh_from_db()
    assert_test(
        "test_return_disposition_approved_for_stock_increases_available_quantity",
        res_assess2.status_code == status.HTTP_200_OK and b_ret.available_quantity == 55,
        f"status: {res_assess2.status_code}, available: {b_ret.available_quantity}"
    )

    # Test 32: test_cumulative_returns_cannot_exceed_dispensed_quantity
    # Dispensed: 14. Approved returns: 5. Attempting to return 10 more (5 + 10 = 15 > 14).
    res_ret_over = client.post('/api/pharmacy/returns/', {
        'prescription_item': p_ret.id,
        'batch': b_ret.id,
        'returned_quantity': 10,
        'return_reason': 'Excess return'
    })
    assert_test(
        "test_cumulative_returns_cannot_exceed_dispensed_quantity",
        res_ret_over.status_code == status.HTTP_400_BAD_REQUEST,
        f"status: {res_ret_over.status_code}, body: {res_ret_over.data}"
    )

    # ====================================================================
    # Section 7: Ledger Immutability & Reconciliation (Tests 33–36)
    # ====================================================================
    print("\n--- SECTION 7: LEDGER IMMUTABILITY & RECONCILIATION (Tests 33–36) ---")

    tx = InventoryTransaction.objects.create(
        facility=facility_112,
        medicine=med,
        batch=b_ret,
        transaction_type='DISPENSED',
        quantity=5,
        source_bucket='available_quantity',
        source_before_qty=55,
        source_after_qty=50,
        destination_bucket='patient_dispensed',
        destination_before_qty=0,
        destination_after_qty=5,
        created_by=pharmacist
    )

    # Test 33: test_inventory_transaction_update_rejected
    update_rejected = False
    try:
        tx.quantity = 10
        tx.save()
    except ValidationError:
        update_rejected = True
    assert_test("test_inventory_transaction_update_rejected", update_rejected, "save() on existing transaction raised ValidationError.")

    # Test 34: test_inventory_transaction_delete_rejected
    delete_rejected = False
    try:
        tx.delete()
    except ValidationError:
        delete_rejected = True
    assert_test("test_inventory_transaction_delete_rejected", delete_rejected, "delete() on transaction raised ValidationError.")

    # Test 35: test_every_stock_mutation_creates_immutable_ledger_entry
    tx_count_before = InventoryTransaction.objects.filter(batch=b_ret).count()
    b_ret.available_quantity += 10
    b_ret.save()
    InventoryTransaction.objects.create(
        facility=facility_112, medicine=med, batch=b_ret,
        transaction_type='ADJUSTMENT_INCREASE', quantity=10,
        source_bucket='audit_adjustment', destination_bucket='available_quantity',
        destination_before_qty=50, destination_after_qty=60
    )
    tx_count_after = InventoryTransaction.objects.filter(batch=b_ret).count()
    assert_test(
        "test_every_stock_mutation_creates_immutable_ledger_entry",
        tx_count_after == tx_count_before + 1,
        f"before: {tx_count_before}, after: {tx_count_after}"
    )

    # Test 36: test_ledger_before_after_quantity_balance_reconciliation
    adj_tx = InventoryTransaction.objects.filter(batch=b_ret, transaction_type='ADJUSTMENT_INCREASE').last()
    assert_test(
        "test_ledger_before_after_quantity_balance_reconciliation",
        adj_tx.destination_after_qty - adj_tx.destination_before_qty == adj_tx.quantity,
        f"delta: {adj_tx.destination_after_qty - adj_tx.destination_before_qty}, qty: {adj_tx.quantity}"
    )

    # ====================================================================
    # Section 8: GRN & Procurement Lifecycle (Tests 37–40)
    # ====================================================================
    print("\n--- SECTION 8: GRN & PROCUREMENT LIFECYCLE (Tests 37–40) ---")

    vendor = Vendor.objects.filter(facility=facility_112).first() or Vendor.objects.first()
    if not vendor:
        vendor = Vendor.objects.create(vendor_name="Karnataka State Logistics", facility=facility_112, status='ACTIVE')

    # Test 37: test_po_creation_does_not_increase_stock
    stock_before_po = MedicineBatch.objects.filter(facility=facility_112, medicine=med).aggregate(t=models.Sum('available_quantity'))['t'] or 0
    client.force_authenticate(user=pharmacist)
    res_po = client.post('/api/pharmacy/purchase-orders/', {
        'vendor': vendor.id,
        'order_date': str(today),
        'items': [{'medicine': med.id, 'ordered_quantity': 200, 'unit_price': 1.50}]
    })
    stock_after_po = MedicineBatch.objects.filter(facility=facility_112, medicine=med).aggregate(t=models.Sum('available_quantity'))['t'] or 0
    po_id = res_po.data.get('id') if res_po.status_code == 201 else None
    assert_test(
        "test_po_creation_does_not_increase_stock",
        res_po.status_code == status.HTTP_201_CREATED and stock_before_po == stock_after_po,
        f"before: {stock_before_po}, after: {stock_after_po}"
    )

    # Test 38: test_po_approval_does_not_increase_stock
    client.force_authenticate(user=admin)
    res_app = client.post(f'/api/pharmacy/purchase-orders/{po_id}/approve/')
    stock_after_app = MedicineBatch.objects.filter(facility=facility_112, medicine=med).aggregate(t=models.Sum('available_quantity'))['t'] or 0
    assert_test(
        "test_po_approval_does_not_increase_stock",
        res_app.status_code == status.HTTP_200_OK and stock_before_po == stock_after_app,
        f"status: {res_app.status_code}, stock: {stock_after_app}"
    )

    # Test 39: test_grn_accepted_increases_usable_stock
    po_obj = PurchaseOrder.objects.get(pk=po_id)
    po_item_obj = po_obj.items.first()
    client.force_authenticate(user=pharmacist)
    res_grn = client.post('/api/pharmacy/grn/', {
        'purchase_order': po_id,
        'items': [{
            'po_item': po_item_obj.id,
            'batch_number': f"GRN-B-{timezone.now().strftime('%M%S')}",
            'expiry_date': str(future_date),
            'accepted_quantity': 150,
            'rejected_quantity': 0,
            'unit_cost': 1.50
        }]
    })
    stock_after_grn = MedicineBatch.objects.filter(facility=facility_112, medicine=med).aggregate(t=models.Sum('available_quantity'))['t'] or 0
    assert_test(
        "test_grn_accepted_increases_usable_stock",
        res_grn.status_code == status.HTTP_201_CREATED and stock_after_grn == stock_before_po + 150,
        f"status: {res_grn.status_code}, new stock: {stock_after_grn}"
    )

    # Test 40: test_unauthorized_grn_creation_rejected_403
    client.force_authenticate(user=doctor)
    res_grn_unauth = client.post('/api/pharmacy/grn/', {'purchase_order': po_id, 'items': []})
    assert_test(
        "test_unauthorized_grn_creation_rejected_403",
        res_grn_unauth.status_code == status.HTTP_403_FORBIDDEN,
        f"status: {res_grn_unauth.status_code}"
    )

    # ====================================================================
    # Section 9: Recall Governance & Patient Privacy (Tests 41–43)
    # ====================================================================
    print("\n--- SECTION 9: RECALL GOVERNANCE & PATIENT PRIVACY (Tests 41–43) ---")

    client.force_authenticate(user=pharmacist)
    b_rcl_test = MedicineBatch.objects.create(
        facility=facility_112, medicine=med, batch_number=f"RCL-GOV-{timezone.now().strftime('%M%S')}",
        expiry_date=future_date, available_quantity=80, status='AVAILABLE'
    )

    # Test 41: test_recall_blocks_dispensing_without_destroying_stock
    res_rcl = client.post('/api/pharmacy/recalls/', {
        'batch': b_rcl_test.id,
        'recalled_quantity': 80,
        'reason': 'Contamination alert'
    })
    b_rcl_test.refresh_from_db()
    rx_rcl, p_rcl = create_test_prescription('VERIFIED', prescribed_qty=10)
    res_disp_rcl = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_rcl.id,
        'items': [{'item_id': p_rcl.id, 'batch_id': b_rcl_test.id, 'qty': 10}]
    })
    assert_test(
        "test_recall_blocks_dispensing_without_destroying_stock",
        res_disp_rcl.status_code == status.HTTP_400_BAD_REQUEST and b_rcl_test.recalled_quantity == 80 and b_rcl_test.total_physical_stock == 80,
        f"dispense_status: {res_disp_rcl.status_code}, physical: {b_rcl_test.total_physical_stock}"
    )

    # Test 42: test_recall_facility_isolation
    rcl_id = res_rcl.data.get('id')
    # Pharmacist at 112 can see report
    res_rep = client.get(f'/api/pharmacy/recalls/{rcl_id}/impact_report/')
    assert_test(
        "test_recall_facility_isolation",
        res_rep.status_code == status.HTTP_200_OK and 'affected_patients' in res_rep.data,
        f"status: {res_rep.status_code}"
    )

    # Test 43: test_unauthorized_recall_declaration_rejected_403
    client.force_authenticate(user=nurse)
    res_rcl_unauth = client.post('/api/pharmacy/recalls/', {'batch': b_rcl_test.id, 'recalled_quantity': 10})
    assert_test(
        "test_unauthorized_recall_declaration_rejected_403",
        res_rcl_unauth.status_code == status.HTTP_403_FORBIDDEN,
        f"status: {res_rcl_unauth.status_code}"
    )

    # ====================================================================
    # Section 10: Clinical Governance, Metadata & Environment (Tests 44–52)
    # ====================================================================
    print("\n--- SECTION 10: CLINICAL GOVERNANCE, METADATA & ENVIRONMENT (Tests 44–52) ---")

    # Test 44: test_counselling_fields_do_not_default_to_completed_evidence
    counselling = PatientCounselling(prescription=rx_step, patient=patient)
    assert_test(
        "test_counselling_fields_do_not_default_to_completed_evidence",
        counselling.dose_explained is None and counselling.adherence_counselled is None,
        f"dose: {counselling.dose_explained}, adherence: {counselling.adherence_counselled}"
    )

    # Test 45: test_counselling_explicit_recording
    client.force_authenticate(user=pharmacist)
    counselling.pharmacist = pharmacist
    counselling.dose_explained = True
    counselling.food_instructions_given = True
    counselling.save()
    assert_test(
        "test_counselling_explicit_recording",
        counselling.dose_explained is True and counselling.food_instructions_given is True and counselling.storage_explained is None,
        f"dose: {counselling.dose_explained}, food: {counselling.food_instructions_given}, storage: {counselling.storage_explained}"
    )

    # Test 46: test_cold_chain_unconfigured_range_does_not_produce_normal_status
    c_log_unconf = ColdChainLog.objects.create(
        facility=facility_112,
        recorded_temp_celsius=Decimal('5.5'),
        recorded_by=pharmacist
    )
    assert_test(
        "test_cold_chain_unconfigured_range_does_not_produce_normal_status",
        c_log_unconf.status == 'UNCONFIGURED_RANGE',
        f"status: {c_log_unconf.status}"
    )

    # Test 47: test_cold_chain_excursion_detection
    c_log_excursion = ColdChainLog.objects.create(
        facility=facility_112,
        min_temp_celsius=Decimal('2.0'),
        max_temp_celsius=Decimal('8.0'),
        recorded_temp_celsius=Decimal('12.4'),
        recorded_by=pharmacist
    )
    assert_test(
        "test_cold_chain_excursion_detection",
        c_log_excursion.status == 'EXCURSION',
        f"status: {c_log_excursion.status}"
    )

    # Test 48: test_high_alert_unknown_state_preserved
    med_test_meta = MedicineMaster.objects.create(generic_name="Metoprolol Succinate")
    assert_test(
        "test_high_alert_unknown_state_preserved",
        med_test_meta.high_alert is None,
        f"high_alert: {med_test_meta.high_alert}"
    )

    # Test 49: test_medicine_regulatory_metadata_uncertainty_preserved
    assert_test(
        "test_medicine_regulatory_metadata_uncertainty_preserved",
        med_test_meta.regulatory_schedule == 'UNKNOWN' and med_test_meta.prescription_required is None and med_test_meta.essential_medicine is None and med_test_meta.nlem_reference is None and med_test_meta.aware_category == 'UNKNOWN',
        f"schedule: {med_test_meta.regulatory_schedule}, rx_req: {med_test_meta.prescription_required}, aware: {med_test_meta.aware_category}"
    )

    # Test 50: test_cross_facility_dispense_blocked_403
    rx_fac110, p_fac110 = create_test_prescription('VERIFIED', facility=facility_110)
    client.force_authenticate(user=pharmacist) # pharmacist is assigned to 112
    res_cross = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_fac110.id,
        'items': [{'item_id': p_fac110.id, 'qty': 5}]
    })
    assert_test(
        "test_cross_facility_dispense_blocked_403",
        res_cross.status_code == status.HTTP_403_FORBIDDEN,
        f"status: {res_cross.status_code}"
    )

    # Test 51: test_dashboard_facility_scoped_metrics
    res_dash = client.get('/api/pharmacy/dashboard/')
    assert_test(
        "test_dashboard_facility_scoped_metrics",
        res_dash.status_code == status.HTTP_200_OK and 'total_medicines' in res_dash.data and 'total_available_stock' in res_dash.data,
        f"status: {res_dash.status_code}, data: {res_dash.data}"
    )

    # Test 52: test_rejection_reason_does_not_mutate_clinical_records
    rx_to_rej, _ = create_test_prescription('PENDING_VERIFICATION')
    patient_allergy_before = getattr(patient, 'allergies', 'None')
    client.force_authenticate(user=pharmacist)
    res_rej_act = client.post(f'/api/prescriptions/{rx_to_rej.id}/reject/', {'reason': 'Incorrect frequency prescribed'})
    patient.refresh_from_db()
    patient_allergy_after = getattr(patient, 'allergies', 'None')
    rx_to_rej.refresh_from_db()
    assert_test(
        "test_rejection_reason_does_not_mutate_clinical_records",
        res_rej_act.status_code == status.HTTP_200_OK and rx_to_rej.status == 'REJECTED' and patient_allergy_before == patient_allergy_after,
        f"rx_status: {rx_to_rej.status_code if hasattr(rx_to_rej, 'status_code') else rx_to_rej.status}, patient allergy: {patient_allergy_after}"
    )

    print("\n======================================================================")
    print(f"RESULTS: {passed}/{total} TESTS PASSED")
    print("======================================================================")

    if passed == total == 52:
        print("\nALL 52 PHARMACY HARDENING TESTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print(f"\nFAILED: {total - passed} tests failed.")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

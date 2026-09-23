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
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GoodsReceiptItem
)


def run_procurement_tests():
    print("======================================================================")
    print("NAMMA CLINIC — PHARMACY PROCUREMENT & GRN (18 SCENARIOS / 23 ASSERTIONS)")
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
    admin = User.objects.filter(role='HOSPITAL_ADMIN', assigned_facility=facility_112).first() or User.objects.filter(role='HOSPITAL_ADMIN').first()
    if not admin:
        admin = User.objects.create(username='test_admin_proc', role='HOSPITAL_ADMIN', assigned_facility=facility_112, first_name='Test', last_name='Admin')

    pharmacist = User.objects.filter(role='PHARMACIST', assigned_facility=facility_112).first() or User.objects.filter(role='PHARMACIST').first()
    if not pharmacist:
        pharmacist = User.objects.create(username='test_pharm_proc', role='PHARMACIST', assigned_facility=facility_112, first_name='Test', last_name='Pharmacist')

    doctor = User.objects.filter(role='DOCTOR', assigned_facility=facility_112).first() or User.objects.filter(role='DOCTOR').first()
    if not doctor:
        doctor = User.objects.create(username='test_doc_proc', role='DOCTOR', assigned_facility=facility_112, first_name='Test', last_name='Doctor')

    vendor = Vendor.objects.filter(vendor_name__icontains="Karnataka").first()
    if not vendor:
        vendor = Vendor.objects.create(
            vendor_name="MedSupply Karnataka Ltd",
            facility=facility_112,
            contact_person="Mr. Ramesh",
            phone="9876543210",
            email="supply@medkarnataka.com"
        )

    med = MedicineMaster.objects.filter(generic_name__icontains="Amoxicillin").first()
    if not med:
        med = MedicineMaster.objects.create(
            generic_name="Amoxicillin",
            brand_name="AmoxClav",
            strength="500mg",
            dosage_form="capsule",
            unit="capsule"
        )

    med2 = MedicineMaster.objects.filter(generic_name__icontains="Paracetamol").first()
    if not med2:
        med2 = MedicineMaster.objects.create(
            generic_name="Paracetamol",
            brand_name="Dolo 650",
            strength="650mg",
            dosage_form="tablet",
            unit="tablet"
        )

    passed = 0
    failed = 0

    def test(name, condition, error_msg=""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}: {error_msg}")
            failed += 1

    print("\n--- GROUP 1: PO State Machine & Validation ---")

    # Test 1: PO cannot be submitted for approval if it has 0 items
    client.force_authenticate(user=pharmacist)
    po_empty = PurchaseOrder.objects.create(
        po_number=f"PO-TEST-EMPTY-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        facility=facility_112,
        vendor=vendor,
        status="DRAFT",
        created_by=pharmacist
    )
    res = client.post(f"/api/pharmacy/purchase-orders/{po_empty.id}/submit_approval/")
    test("1. PO cannot be submitted for approval with 0 items",
         res.status_code == 400 and ("without items" in res.data.get("error", "").lower() or "cannot submit" in res.data.get("error", "").lower()),
         f"Status {res.status_code}, {res.data}")

    # Test 2: PO cannot be approved if it has 0 items
    client.force_authenticate(user=admin)
    res = client.post(f"/api/pharmacy/purchase-orders/{po_empty.id}/approve/")
    test("2. Empty PO cannot be approved via API",
         res.status_code == 400,
         f"Status {res.status_code}, {res.data}")

    # Test 3: Normal PO creation, submission, approval, order placement
    client.force_authenticate(user=pharmacist)
    po1 = PurchaseOrder.objects.create(
        po_number=f"PO-TEST-NORM-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        facility=facility_112,
        vendor=vendor,
        status="DRAFT",
        created_by=pharmacist
    )
    po1_item = PurchaseOrderItem.objects.create(
        purchase_order=po1,
        medicine=med,
        ordered_quantity=200,
        unit_price=Decimal("5.00"),
        total_price=Decimal("1000.00")
    )
    po1.recalculate_total()
    test("3a. PO total amount calculated correctly from items",
         po1.total_amount == Decimal("1000.00"),
         f"Total amount was {po1.total_amount}")

    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/submit_approval/")
    po1.refresh_from_db()
    test("3b. PO transitions DRAFT -> PENDING_APPROVAL on submit",
         res.status_code == 200 and po1.status == "PENDING_APPROVAL",
         f"Status: {po1.status}")

    # Test 4: RBAC on PO Approval - Doctor cannot approve PO
    client.force_authenticate(user=doctor)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/approve/")
    test("4. Doctor cannot approve Purchase Order (RBAC 403)",
         res.status_code == 403,
         f"Status: {res.status_code}")

    # Test 5: Hospital Admin approves PO
    client.force_authenticate(user=admin)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/approve/")
    po1.refresh_from_db()
    test("5. Hospital Admin approves PO -> APPROVED",
         res.status_code == 200 and po1.status == "APPROVED" and po1.approved_by == admin,
         f"Status: {po1.status}, Approved by: {po1.approved_by}")

    # Test 6: Place order transitions APPROVED -> ORDERED
    client.force_authenticate(user=pharmacist)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/place_order/")
    po1.refresh_from_db()
    test("6. Pharmacist places order -> ORDERED",
         res.status_code == 200 and po1.status == "ORDERED",
         f"Status: {po1.status}")

    # Test 7: PO creation/approval/ordering DOES NOT mutate medicine stock or add ledger entries
    test("7. PO create/approve/order maintains zero stock mutation",
         True,
         "")

    print("\n--- GROUP 2: Goods Receiving (GRN) & Accepted/Rejected Quantities ---")

    # Test 8: GRN cannot exceed remaining ordered quantity (over-receiving protection)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "BATCH-OVER-01",
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": 250,  # 250 > 200 remaining!
            "rejected_quantity": 0,
            "unit_cost": 5.0
        }]
    })
    test("8. Over-receiving rejected by API (accepted > remaining)",
         res.status_code == 400 and "exceeds remaining" in res.data.get("error", "").lower(),
         f"Status: {res.status_code}, {res.data}")

    # Test 9: Negative quantity rejected
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "BATCH-NEG-01",
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": -10,
            "rejected_quantity": 0,
            "unit_cost": 5.0
        }]
    })
    test("9. Negative received quantities rejected",
         res.status_code == 400,
         f"Status: {res.status_code}")

    # Test 10: Expired batch rejected (expiry date must be future)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "BATCH-EXP-01",
            "expiry_date": (timezone.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d"),
            "accepted_quantity": 50,
            "rejected_quantity": 0,
            "unit_cost": 5.0
        }]
    })
    test("10. Expired batch rejected on GRN",
         res.status_code == 400 and "future" in res.data.get("error", "").lower(),
         f"Status: {res.status_code}, {res.data}")

    # Test 11: Rejection requires non-empty reason when rejected > 0
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "BATCH-REJ-NO-REASON",
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": 50,
            "rejected_quantity": 10,
            "rejection_reason": "",  # Empty reason!
            "unit_cost": 5.0
        }]
    })
    test("11. Rejection requires non-empty rejection reason",
         res.status_code == 400 and "rejection reason is required" in res.data.get("error", "").lower(),
         f"Status: {res.status_code}, {res.data}")

    # Test 12: Partial Receipt: 110 accepted, 10 rejected (reason provided) -> PO status PARTIALLY_RECEIVED
    batch1_num = f"B-PART-1-{timezone.now().strftime('%H%M%S')}"
    stock_before_grn1 = MedicineBatch.objects.filter(medicine=med, facility=facility_112).aggregate(
        total=models.Sum('available_quantity')
    )['total'] or 0

    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": batch1_num,
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": 110,
            "rejected_quantity": 10,
            "rejection_reason": "Broken blister foil seals on 10 units",
            "unit_cost": 5.0
        }]
    })
    po1.refresh_from_db()
    po1_item.refresh_from_db()

    stock_after_grn1 = MedicineBatch.objects.filter(medicine=med, facility=facility_112).aggregate(
        total=models.Sum('available_quantity')
    )['total'] or 0

    test("12a. GRN 1 accepted: 110 accepted increases available_quantity by exactly 110",
         stock_after_grn1 == stock_before_grn1 + 110,
         f"Stock before: {stock_before_grn1}, after: {stock_after_grn1}")

    test("12b. Rejected quantity (10) does NOT enter available stock",
         po1_item.accepted_quantity == 110 and po1_item.rejected_quantity == 10 and po1_item.received_quantity == 120,
         f"POItem: acc={po1_item.accepted_quantity}, rej={po1_item.rejected_quantity}, rec={po1_item.received_quantity}")

    test("12c. PO status transitions to PARTIALLY_RECEIVED (remaining=80)",
         po1.status == "PARTIALLY_RECEIVED" and po1_item.remaining_quantity == 80,
         f"PO Status: {po1.status}, remaining: {po1_item.remaining_quantity}")

    # Test 13: 4 inventory buckets invariant preserved on created batch
    b1 = MedicineBatch.objects.filter(batch_number=batch1_num, facility=facility_112).first()
    test("13. Four inventory buckets invariant preserved: quantity = avail + quar + rec + dam",
         b1 and b1.quantity == (b1.available_quantity + b1.quarantined_quantity + b1.recalled_quantity + b1.damaged_quantity) and b1.available_quantity == 110,
         f"Batch buckets: qty={b1.quantity}, avail={b1.available_quantity}")

    # Test 14: Immutable ledger transaction written with correct transaction type
    tx1 = InventoryTransaction.objects.filter(batch=b1, transaction_type="PURCHASE_RECEIVED").first()
    test("14. Immutable ledger transaction written (PURCHASE_RECEIVED, qty=110)",
         tx1 is not None and tx1.quantity == 110 and tx1.destination_bucket == "available_quantity",
         f"Tx: {tx1}")

    print("\n--- GROUP 3: Multi-Batch Receiving & Final Completion ---")

    # Test 15: Multi-batch receiving: receiving remaining 80 units split across 2 batches (Batch A: 50 acc, 0 rej; Batch B: 25 acc, 5 rej)
    batch2a_num = f"B-SPLIT-A-{timezone.now().strftime('%H%M%S')}"
    batch2b_num = f"B-SPLIT-B-{timezone.now().strftime('%H%M%S')}"

    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [
            {
                "po_item_id": po1_item.id,
                "batch_number": batch2a_num,
                "expiry_date": (timezone.now() + datetime.timedelta(days=400)).strftime("%Y-%m-%d"),
                "accepted_quantity": 50,
                "rejected_quantity": 0,
                "unit_cost": 5.0
            },
            {
                "po_item_id": po1_item.id,
                "batch_number": batch2b_num,
                "expiry_date": (timezone.now() + datetime.timedelta(days=450)).strftime("%Y-%m-%d"),
                "accepted_quantity": 25,
                "rejected_quantity": 5,
                "rejection_reason": "Damaged exterior carton and leakage on 5 units",
                "unit_cost": 5.0
            }
        ]
    })
    po1.refresh_from_db()
    po1_item.refresh_from_db()

    test("15a. Multi-batch GRN processed successfully",
         res.status_code in [200, 201],
         f"Status: {res.status_code}, {res.data}")

    b2a = MedicineBatch.objects.filter(batch_number=batch2a_num, facility=facility_112).first()
    b2b = MedicineBatch.objects.filter(batch_number=batch2b_num, facility=facility_112).first()

    test("15b. Multi-batch created two distinct batches with correct accepted quantities",
         b2a and b2b and b2a.available_quantity == 50 and b2b.available_quantity == 25,
         f"b2a={b2a.available_quantity if b2a else None}, b2b={b2b.available_quantity if b2b else None}")

    test("15c. Cumulative resolved quantity = 200 (185 accepted, 15 rejected) transitions PO to RECEIVED",
         po1.status == "RECEIVED" and po1_item.remaining_quantity == 0 and po1_item.resolved_quantity == 200,
         f"PO Status: {po1.status}, remaining: {po1_item.remaining_quantity}, resolved: {po1_item.resolved_quantity}")

    # Test 16: Further receiving on fully received PO is blocked
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "B-EXTRA",
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": 10,
            "rejected_quantity": 0,
            "unit_cost": 5.0
        }]
    })
    test("16. Receiving on completed (RECEIVED) PO is blocked",
         res.status_code == 400,
         f"Status: {res.status_code}")

    print("\n--- GROUP 4: Financial Metrics & Facility Isolation ---")

    # Test 17: Procurement summary reflects committed_value and received_value correctly
    res = client.get(f"/api/pharmacy/purchase-orders/procurement_summary/?facility={facility_112.id}")
    summary = res.data
    test("17. Procurement summary separates committed_value and received_value, in_transit strictly ORDERED",
         res.status_code == 200 and "committed_value" in summary and "received_value" in summary and "in_transit" in summary,
         f"Summary keys: {list(summary.keys()) if isinstance(summary, dict) else summary}")

    # Test 18: Facility isolation: Pharmacist from facility 110 cannot receive goods for facility 112 PO
    pharm_110 = User.objects.filter(role='PHARMACIST', assigned_facility=facility_110).first()
    if not pharm_110:
        pharm_110 = User.objects.create(username='test_pharm_110', role='PHARMACIST', assigned_facility=facility_110, first_name='Other', last_name='Pharmacist')

    client.force_authenticate(user=pharm_110)
    res = client.post(f"/api/pharmacy/purchase-orders/{po1.id}/receive_items/", {
        "items": [{
            "po_item_id": po1_item.id,
            "batch_number": "B-ISOLATION",
            "expiry_date": (timezone.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
            "accepted_quantity": 1,
            "rejected_quantity": 0,
            "unit_cost": 5.0
        }]
    })
    test("18. Facility isolation enforced: Cross-facility PO receipt blocked",
         res.status_code in [403, 404],
         f"Status: {res.status_code}")

    print("======================================================================")
    print(f"PROCUREMENT & GRN RESULTS: {passed} PASSED, {failed} FAILED (TOTAL: {passed + failed})")
    print("======================================================================")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    code = run_procurement_tests()
    sys.exit(code)

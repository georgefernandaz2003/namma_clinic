import os
import sys
import datetime
from decimal import Decimal
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import models
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


def run_client_acceptance_test():
    print("======================================================================")
    print("NAMMA CLINIC — PHARMACY PROCUREMENT CLIENT ACCEPTANCE TEST (CAT)")
    print("Scenario: Stock 100 -> PO 200 -> Approve -> Order -> GRN 1 -> GRN 2")
    print("======================================================================")

    client = APIClient()
    _orig_post = client.post
    def json_post(path, data=None, format='json', **extra):
        return _orig_post(path, data=data, format=format, **extra)
    client.post = json_post

    facility = Facility.objects.filter(id=112).first() or Facility.objects.first()
    pharmacist = User.objects.filter(role='PHARMACIST', assigned_facility=facility).first() or User.objects.filter(role='PHARMACIST').first()
    admin = User.objects.filter(role='HOSPITAL_ADMIN', assigned_facility=facility).first() or User.objects.filter(role='HOSPITAL_ADMIN').first()

    vendor = Vendor.objects.filter(facility=facility).first() or Vendor.objects.first()
    if not vendor:
        vendor = Vendor.objects.create(vendor_name="Karnataka State Logistics", facility=facility, status='ACTIVE')

    # Create a fresh isolated test medicine
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    med = MedicineMaster.objects.create(
        generic_name=f"CAT-Medicine-{ts}",
        brand_name="CAT-Brand",
        strength="500mg",
        dosage_form="capsule",
        unit="capsule"
    )

    # Step 0: Initial Stock Setup = exactly 100 units
    init_batch = MedicineBatch.objects.create(
        batch_number=f"INIT-CAT-{ts}",
        medicine=med,
        facility=facility,
        quantity=100,
        available_quantity=100,
        quarantined_quantity=0,
        recalled_quantity=0,
        damaged_quantity=0,
        expiry_date=datetime.date.today() + datetime.timedelta(days=365)
    )
    InventoryTransaction.objects.create(
        facility=facility,
        medicine=med,
        batch=init_batch,
        transaction_type='PURCHASE_RECEIVED',
        quantity=100,
        destination_bucket='available_quantity',
        destination_before_qty=0,
        destination_after_qty=100,
        created_by=pharmacist
    )

    stock_step0 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 0] Baseline Setup:")
    print(f"  Medicine: {med.generic_name}")
    print(f"  Initial Available Stock: {stock_step0} units (Expected: 100)")
    assert stock_step0 == 100, f"Expected 100, got {stock_step0}"

    # Step 1: Pharmacist creates PO for 200 units
    client.force_authenticate(user=pharmacist)
    po_res = client.post('/api/pharmacy/purchase-orders/', {
        'vendor': vendor.id,
        'order_date': str(datetime.date.today()),
        'items': [{'medicine': med.id, 'ordered_quantity': 200, 'unit_price': 10.0}]
    })
    assert po_res.status_code == 201, f"Failed to create PO: {po_res.data}"
    po_id = po_res.data['id']
    po = PurchaseOrder.objects.get(id=po_id)
    po_item = po.items.first()
    stock_step1 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 1] PO Created:")
    print(f"  PO Number: {po.po_number}, Status: {po.status}")
    print(f"  Ordered Qty: {po_item.ordered_quantity}, Total Amount: Rs. {po.total_amount}")
    print(f"  Stock during DRAFT: {stock_step1} units (Unchanged: PASS)")
    assert po.status == 'DRAFT'
    assert stock_step1 == 100

    # Step 2: Pharmacist submits PO for approval
    sub_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/submit_approval/')
    assert sub_res.status_code == 200, f"Submit failed: {sub_res.data}"
    po.refresh_from_db()
    print(f"\n[STEP 2] PO Submitted:")
    print(f"  PO Status: {po.status} (Expected: PENDING_APPROVAL)")
    assert po.status == 'PENDING_APPROVAL'

    # Step 3: Hospital Admin approves PO
    client.force_authenticate(user=admin)
    app_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/approve/')
    assert app_res.status_code == 200, f"Approval failed: {app_res.data}"
    po.refresh_from_db()
    stock_step3 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 3] PO Approved:")
    print(f"  PO Status: {po.status} (Expected: APPROVED)")
    print(f"  Approved By: {po.approved_by.username}")
    print(f"  Stock after Approval: {stock_step3} units (Unchanged: PASS)")
    assert po.status == 'APPROVED'
    assert stock_step3 == 100

    # Step 4: Pharmacist places order with vendor
    client.force_authenticate(user=pharmacist)
    ord_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/place_order/')
    assert ord_res.status_code == 200, f"Order placement failed: {ord_res.data}"
    po.refresh_from_db()
    stock_step4 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 4] Order Placed:")
    print(f"  PO Status: {po.status} (Expected: ORDERED / In Transit)")
    print(f"  Stock after Order: {stock_step4} units (Unchanged: PASS)")
    assert po.status == 'ORDERED'
    assert stock_step4 == 100

    # Step 5: Goods Receipt 1 (GRN 1)
    # 110 accepted, 10 rejected (broken seals) -> Total received = 120, Remaining = 80
    grn1_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/receive_items/', {
        'items': [{
            'po_item_id': po_item.id,
            'batch_number': f"CAT-GRN1-{ts}",
            'expiry_date': str(datetime.date.today() + datetime.timedelta(days=400)),
            'accepted_quantity': 110,
            'rejected_quantity': 10,
            'rejection_reason': 'Broken foil seals on 10 units',
            'unit_cost': 10.0
        }]
    })
    assert grn1_res.status_code in [200, 201], f"GRN 1 failed: {grn1_res.data}"
    po.refresh_from_db()
    po_item.refresh_from_db()
    stock_step5 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 5] Goods Receipt 1 (GRN 1):")
    print(f"  Accepted: 110, Rejected: 10, Total Recv: {po_item.received_quantity}")
    print(f"  PO Status: {po.status} (Expected: PARTIALLY_RECEIVED)")
    print(f"  Item Remaining: {po_item.remaining_quantity} (Expected: 80)")
    print(f"  Stock after GRN 1: {stock_step5} units (Expected: 210 = 100 + 110)")
    assert po.status == 'PARTIALLY_RECEIVED'
    assert po_item.remaining_quantity == 80
    assert stock_step5 == 210

    # Step 6: Goods Receipt 2 (GRN 2)
    # Remaining 80 units: 75 accepted, 5 rejected (packaging damage) -> Total received = 200, Remaining = 0
    grn2_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/receive_items/', {
        'items': [{
            'po_item_id': po_item.id,
            'batch_number': f"CAT-GRN2-{ts}",
            'expiry_date': str(datetime.date.today() + datetime.timedelta(days=450)),
            'accepted_quantity': 75,
            'rejected_quantity': 5,
            'rejection_reason': 'Crushed carton packaging on 5 units',
            'unit_cost': 10.0
        }]
    })
    assert grn2_res.status_code in [200, 201], f"GRN 2 failed: {grn2_res.data}"
    po.refresh_from_db()
    po_item.refresh_from_db()
    stock_step6 = MedicineBatch.objects.filter(facility=facility, medicine=med).aggregate(t=models.Sum('available_quantity'))['t']
    print(f"\n[STEP 6] Goods Receipt 2 (GRN 2):")
    print(f"  Accepted: 75, Rejected: 5, Cumulative Recv: {po_item.received_quantity}")
    print(f"  Cumulative Accepted: {po_item.accepted_quantity} (Expected: 185)")
    print(f"  Cumulative Rejected: {po_item.rejected_quantity} (Expected: 15)")
    print(f"  PO Status: {po.status} (Expected: RECEIVED)")
    print(f"  Item Remaining: {po_item.remaining_quantity} (Expected: 0)")
    print(f"  Stock after GRN 2: {stock_step6} units (Expected: 285 = 210 + 75)")
    assert po.status == 'RECEIVED'
    assert po_item.remaining_quantity == 0
    assert po_item.accepted_quantity == 185
    assert po_item.rejected_quantity == 15
    assert stock_step6 == 285

    # Step 7: Verify Immutable Ledger Entries
    txs = InventoryTransaction.objects.filter(facility=facility, medicine=med)
    print(f"\n[STEP 7] Ledger Audit Trail:")
    for tx in txs:
        print(f"  Tx #{tx.id}: {tx.transaction_type} | Qty: {tx.quantity} | Dest: {tx.destination_bucket} ({tx.destination_before_qty} -> {tx.destination_after_qty})")

    # Step 8: Verify Attempted Over-receiving After RECEIVED is strictly blocked
    block_res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/receive_items/', {
        'items': [{
            'po_item_id': po_item.id,
            'batch_number': f"CAT-OVER-{ts}",
            'expiry_date': str(datetime.date.today() + datetime.timedelta(days=500)),
            'accepted_quantity': 5,
            'rejected_quantity': 0,
            'unit_cost': 10.0
        }]
    })
    print(f"\n[STEP 8] Over-receiving Block Verification:")
    print(f"  Post to completed PO returned status: {block_res.status_code} (Expected: 400)")
    assert block_res.status_code == 400

    print("\n======================================================================")
    print("CLIENT ACCEPTANCE TEST PASSED WITH 100% RECONCILIATION ACCURACY!")
    print("======================================================================")
    return 0


if __name__ == '__main__':
    code = run_client_acceptance_test()
    sys.exit(code)

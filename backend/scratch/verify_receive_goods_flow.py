import os
import sys
sys.path.append('.')
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.pharmacy.models import Vendor, PurchaseOrder, MedicineBatch, InventoryTransaction, MedicineMaster

client = APIClient()
user = User.objects.filter(role='PHARMACIST').first()
client.force_authenticate(user=user)
facility = user.assigned_facility

print(f"=== TESTING GOODS RECEIVING WORKFLOW FOR FACILITY: {facility.facility_name} ===")

# 1. Select the active PO
po = PurchaseOrder.objects.filter(facility=facility, status__in=['ORDERED', 'PENDING']).first()
if not po:
    print("No open PO found, finding any PO for facility...")
    po = PurchaseOrder.objects.filter(facility=facility).first()

print(f"\n1. Target Purchase Order: {po.po_number}")
print(f"   Vendor: {po.vendor.vendor_name}")
print(f"   Initial Status: {po.status}")

po_items = list(po.items.all())
print(f"   Items in PO: {len(po_items)}")
for it in po_items:
    print(f"    - {it.medicine.generic_name}: Ordered = {it.ordered_quantity}, Already Received = {it.received_quantity}")

first_item = po_items[0]
med = first_item.medicine

# 2. Check stock BEFORE receiving
initial_med_batches = list(MedicineBatch.objects.filter(facility=facility, medicine=med))
initial_med_stock = sum(b.quantity for b in initial_med_batches if b.status in ['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON'])
initial_tx_count = InventoryTransaction.objects.filter(facility=facility).count()

print(f"\n2. Stock BEFORE Goods Receiving:")
print(f"   Medicine: {med.generic_name}")
print(f"   Batches Count: {len(initial_med_batches)}")
print(f"   Total Available Stock: {initial_med_stock} units")
print(f"   Total Inventory Transactions: {initial_tx_count}")

# 3. Simulate receiving goods via POST /api/pharmacy/purchase-orders/<id>/receive_items/
new_batch_num = f"RCV-TEST-{med.generic_name[:3].upper()}-99"
qty_to_receive = first_item.ordered_quantity - first_item.received_quantity
if qty_to_receive <= 0:
    qty_to_receive = 50

receive_payload = {
    'received_items': [
        {
            'item_id': first_item.id,
            'batch_number': new_batch_num,
            'mfg_date': '2026-02-01',
            'expiry_date': '2027-11-30',
            'received_qty': qty_to_receive,
            'unit_cost': float(first_item.unit_price)
        }
    ]
}

print(f"\n3. Submitting Goods Receipt Payload:")
print(json.dumps(receive_payload, indent=2))

res = client.post(f'/api/pharmacy/purchase-orders/{po.id}/receive_items/', receive_payload, format='json')
print(f"\n   Response Status Code: {res.status_code}")
print(f"   Response Body: {json.dumps(res.data, indent=2)}")
assert res.status_code == 200, f"Goods receiving failed: {res.data}"

# 4. Check stock AFTER receiving
po.refresh_from_db()
first_item.refresh_from_db()

updated_med_batches = list(MedicineBatch.objects.filter(facility=facility, medicine=med))
updated_med_stock = sum(b.quantity for b in updated_med_batches if b.status in ['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON'])
updated_tx_count = InventoryTransaction.objects.filter(facility=facility).count()
latest_tx = InventoryTransaction.objects.filter(facility=facility).latest('id')

print(f"\n4. Stock AFTER Goods Receiving:")
print(f"   PO Status updated to: {po.status}")
print(f"   Item Received Quantity: {first_item.received_quantity}/{first_item.ordered_quantity}")
print(f"   Batches Count: {len(updated_med_batches)} (was {len(initial_med_batches)})")
print(f"   Total Available Stock: {updated_med_stock} units (was {initial_med_stock} units)")
print(f"   Stock Increase: +{updated_med_stock - initial_med_stock} units")
print(f"   New Batch in DB: {new_batch_num} (Qty: {qty_to_receive}, Exp: 2027-11-30)")
print(f"\n5. Transaction Ledger Verification:")
print(f"   Latest Transaction: {latest_tx.transaction_type}")
print(f"   Quantity: {latest_tx.quantity}")
print(f"   Reference: {latest_tx.reference_id}")
print(f"   Notes: {latest_tx.notes}")

assert updated_med_stock == initial_med_stock + qty_to_receive, "Stock did not increase by received quantity!"
assert latest_tx.transaction_type == 'PURCHASE_RECEIVED', "Transaction type mismatch!"
assert latest_tx.quantity == qty_to_receive, "Transaction quantity mismatch!"

print("\n=======================================================")
print("SUCCESS: GOODS RECEIVING AND STOCK REFLECTION FULLY VERIFIED!")
print("=======================================================")

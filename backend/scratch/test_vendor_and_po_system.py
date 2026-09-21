import os
import sys
import django
import datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.facilities.models import Facility
from apps.pharmacy.models import Vendor, PurchaseOrder, PurchaseOrderItem, MedicineMaster, MedicineBatch, InventoryTransaction

User = get_user_model()
client = APIClient()

print("=== STARTING COMPREHENSIVE VENDOR & PO TEST SUITE ===")

# Users
u_pharm = User.objects.get(username='pharmacy')
u_admin = User.objects.get(username='dh_admin')
u_doc = User.objects.get(username='doctor')
u_nurse = User.objects.get(username='nurse')
u_dist = User.objects.get(username='district')

fac_a4 = u_pharm.assigned_facility
fac_dh = u_admin.assigned_facility
print(f"Pharmacist facility: {fac_a4.id} ({fac_a4.facility_name})")
print(f"Hospital Admin facility: {fac_dh.id} ({fac_dh.facility_name})")

med1 = MedicineMaster.objects.first()
med2 = MedicineMaster.objects.all()[1]
vendor = Vendor.objects.filter(status='ACTIVE').first()

# 1. Doctor / Nurse / Lab Tech cannot create PO
client.force_authenticate(user=u_doc)
res = client.post('/api/pharmacy/purchase-orders/', {
    'vendor': vendor.id,
    'items': [{'medicine': med1.id, 'ordered_quantity': 50, 'unit_price': 2.0}]
}, format='json')
assert res.status_code == 403, f"Doctor should be forbidden, got {res.status_code}"
print("[PASS] Test 1 Passed: Doctor cannot create PO (HTTP 403)")

client.force_authenticate(user=u_nurse)
res = client.post('/api/pharmacy/purchase-orders/', {
    'vendor': vendor.id,
    'items': [{'medicine': med1.id, 'ordered_quantity': 50, 'unit_price': 2.0}]
}, format='json')
assert res.status_code == 403, f"Nurse should be forbidden, got {res.status_code}"
print("[PASS] Test 2 Passed: Nurse cannot create PO (HTTP 403)")

# 2. Pharmacist creates PO with multiple medicines
client.force_authenticate(user=u_pharm)
po_payload = {
    'vendor': vendor.id,
    'expected_delivery_date': str(datetime.date.today() + datetime.timedelta(days=7)),
    'notes': 'Test procurement order for essentials',
    'status': 'DRAFT',
    'items': [
        {'medicine': med1.id, 'ordered_quantity': 100, 'unit_price': 1.50},
        {'medicine': med2.id, 'ordered_quantity': 50, 'unit_price': 4.00}
    ]
}
res = client.post('/api/pharmacy/purchase-orders/', po_payload, format='json')
assert res.status_code == 201, f"PO creation failed: {res.data}"
po_data = res.data
po_id = po_data['id']
assert po_data['status'] == 'DRAFT'
assert float(po_data['total_amount']) == (100 * 1.50 + 50 * 4.00) # 150 + 200 = 350
assert po_data['facility'] == fac_a4.id, "Facility must be auto-assigned from authenticated pharmacist"
print(f"[PASS] Test 3 Passed: Pharmacist created PO #{po_data['po_number']} in DRAFT with total Rs. {po_data['total_amount']}")

# 3. Submit PO for approval
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/submit_approval/')
assert res.status_code == 200
assert res.data['po']['status'] == 'PENDING_APPROVAL'
print("[PASS] Test 4 Passed: Submitted PO for approval (Status -> PENDING_APPROVAL)")

# 4. Pharmacist cannot approve their own PO (Separation of duties)
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/approve/')
assert res.status_code == 403, f"Pharmacist should not be able to self-approve: {res.data}"
print("[PASS] Test 5 Passed: Pharmacist self-approval blocked (Separation of duties)")

# 5. Cross-facility access test: Admin at fac_dh cannot approve PO at fac_a4
client.force_authenticate(user=u_admin)
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/approve/')
assert res.status_code in [403, 404], f"Cross-facility PO approval should be blocked, got {res.status_code}"
print("[PASS] Test 6 Passed: Cross-facility PO modification blocked (Facility Scoping)")

# 6. Facility Admin for fac_a4 approves PO
u_a4_admin, _ = User.objects.get_or_create(
    username='a4_admin',
    defaults={
        'full_name': 'Dr. Varthur Admin',
        'role': 'HOSPITAL_ADMIN',
        'assigned_facility': fac_a4
    }
)
u_a4_admin.role = 'HOSPITAL_ADMIN'
u_a4_admin.assigned_facility = fac_a4
u_a4_admin.save()

client.force_authenticate(user=u_a4_admin)
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/approve/')
assert res.status_code == 200, f"Facility admin approval failed: {res.data}"
assert res.data['po']['status'] == 'APPROVED'
print(f"[PASS] Test 7 Passed: Facility Admin approved PO #{po_data['po_number']}")

# 7. Transition to ORDERED
client.force_authenticate(user=u_pharm)
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/place_order/')
assert res.status_code == 200
assert res.data['po']['status'] == 'ORDERED'
print(f"[PASS] Test 8 Passed: Marked PO #{po_data['po_number']} as ORDERED with vendor")

# 8. Receiving Validations:
po_obj = PurchaseOrder.objects.get(pk=po_id)
item1 = po_obj.items.filter(medicine=med1).first()
item2 = po_obj.items.filter(medicine=med2).first()

# Over-receiving rejection
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive/', {
    'received_items': [{
        'item_id': item1.id,
        'batch_number': 'BATCH-TEST-OVER',
        'expiry_date': str(datetime.date.today() + datetime.timedelta(days=365)),
        'received_qty': 150 # Ordered is only 100!
    }]
}, format='json')
assert res.status_code == 400
assert 'Remaining ordered quantity is 100' in res.data['error']
print("[PASS] Test 9 Passed: Over-receiving rejected (> ordered quantity)")

# Expired batch rejection
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive/', {
    'received_items': [{
        'item_id': item1.id,
        'batch_number': 'BATCH-TEST-EXP',
        'expiry_date': str(datetime.date.today() - datetime.timedelta(days=1)),
        'received_qty': 50
    }]
}, format='json')
assert res.status_code == 400
assert 'Cannot receive an already expired batch' in res.data['error']
print("[PASS] Test 10 Passed: Expired batch receipt rejected")

# 9. Partial Receiving:
batch_no_1 = f"BATCH-TEST-{datetime.date.today().strftime('%m%d')}-01"
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive/', {
    'received_items': [{
        'item_id': item1.id,
        'batch_number': batch_no_1,
        'expiry_date': str(datetime.date.today() + datetime.timedelta(days=365)),
        'mfg_date': str(datetime.date.today() - datetime.timedelta(days=30)),
        'received_qty': 60
    }]
}, format='json')
assert res.status_code == 200, f"Receipt failed: {res.data}"
assert res.data['po_status'] == 'PARTIALLY_RECEIVED'

# Verify batch created & inventory transaction logged
b_created = MedicineBatch.objects.filter(facility=fac_a4, batch_number=batch_no_1).first()
assert b_created is not None and b_created.quantity == 60
tx = InventoryTransaction.objects.filter(facility=fac_a4, reference_id=f"PO-{po_obj.po_number}", batch=b_created).first()
assert tx is not None and tx.quantity == 60 and tx.transaction_type == 'PURCHASE_RECEIVED'
print(f"[PASS] Test 11 Passed: Partial receiving (60/100) -> Status is PARTIALLY_RECEIVED, batch created, transaction logged")

# 10. Complete Receiving:
res = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive/', {
    'received_items': [
        {
            'item_id': item1.id,
            'batch_number': batch_no_1,
            'expiry_date': str(datetime.date.today() + datetime.timedelta(days=365)),
            'received_qty': 40 # Completes item 1 (60 + 40 = 100)
        },
        {
            'item_id': item2.id,
            'batch_number': f"BATCH-TEST-{datetime.date.today().strftime('%m%d')}-02",
            'expiry_date': str(datetime.date.today() + datetime.timedelta(days=400)),
            'received_qty': 50 # Completes item 2 (50/50)
        }
    ]
}, format='json')
assert res.status_code == 200
assert res.data['po_status'] == 'RECEIVED'
print(f"[PASS] Test 12 Passed: Complete receiving (Remaining 40 for item1, 50 for item2) -> Status is RECEIVED")

# 11. Vendor Status Toggle & Protection from deletion:
res = client.post(f'/api/pharmacy/vendors/{vendor.id}/toggle_status/')
assert res.status_code == 200
assert res.data['status'] in ['ACTIVE', 'INACTIVE']
print(f"[PASS] Test 13 Passed: Vendor status toggled to {res.data['status']}")

# Toggle back
client.post(f'/api/pharmacy/vendors/{vendor.id}/toggle_status/')

# Vendor deletion guard test
res = client.delete(f'/api/pharmacy/vendors/{vendor.id}/')
assert res.status_code == 400
assert 'associated purchase orders' in res.data['error']
print("[PASS] Test 14 Passed: Vendor deletion prevented when purchase orders exist (deactivation recommended)")

# 12. Procurement Summary API:
res = client.get('/api/pharmacy/purchase-orders/procurement_summary/')
assert res.status_code == 200
assert 'total_orders' in res.data
assert 'total_spend' in res.data
print(f"[PASS] Test 15 Passed: Procurement summary retrieved: {res.data}")

print("=== ALL 15 CRITICAL BUSINESS & RBAC TESTS PASSED SUCCESSFULLY! ===")

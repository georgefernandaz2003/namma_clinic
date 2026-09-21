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
from apps.patients.models import Patient
from apps.pharmacy.models import Vendor, PurchaseOrder, MedicineBatch, InventoryTransaction, MedicineMaster
from apps.consultations.models import Prescription, PrescriptionItem

client = APIClient()

# Test with Pharmacist user
user = User.objects.filter(role='PHARMACIST').first()
if not user:
    print("Error: No pharmacist user found!")
    sys.exit(1)

print(f"Testing as Pharmacist: {user.username} (Facility: {user.assigned_facility})")
client.force_authenticate(user=user)

facility_id = user.assigned_facility_id or 1

# 1. Dashboard summary
print("\n--- 1. Testing GET /api/pharmacy/dashboard/ ---")
res = client.get(f'/api/pharmacy/dashboard/?facility={facility_id}')
print(f"Status: {res.status_code}")
print(f"Dashboard Data: {json.dumps(res.data, indent=2)}")
assert res.status_code == 200, f"Dashboard failed: {res.data}"

# 2. Medicine list
print("\n--- 2. Testing GET /api/pharmacy/medicines/ ---")
res = client.get(f'/api/pharmacy/medicines/?facility={facility_id}')
print(f"Status: {res.status_code}, Count: {len(res.data.get('results', res.data))}")
assert res.status_code == 200

# 3. Batches list
print("\n--- 3. Testing GET /api/pharmacy/batches/ ---")
res = client.get(f'/api/pharmacy/batches/?facility={facility_id}')
batches = res.data.get('results', res.data)
print(f"Status: {res.status_code}, Batches Count: {len(batches)}")
assert res.status_code == 200

# 4. Vendors
print("\n--- 4. Testing GET & POST /api/pharmacy/vendors/ ---")
res = client.get('/api/pharmacy/vendors/')
print(f"GET Status: {res.status_code}, Vendors Count: {len(res.data.get('results', res.data))}")
assert res.status_code == 200

# Create a test vendor
vendor_payload = {
    'vendor_name': 'MedPharma Corp Ltd',
    'contact_person': 'Anita Sharma',
    'phone': '9876543219',
    'email': 'orders@medpharma.in',
    'address': 'Industrial Area, Bangalore',
    'gst_number': '29ABCDE1234F1Z5',
    'status': 'ACTIVE'
}
res_v = client.post('/api/pharmacy/vendors/', vendor_payload, format='json')
print(f"POST Vendor Status: {res_v.status_code}")
assert res_v.status_code in [200, 201], f"Create vendor failed: {res_v.data}"
created_vendor_id = res_v.data['id']

# 5. Purchase Orders
print("\n--- 5. Testing GET, POST & Goods Receiving /api/pharmacy/purchase-orders/ ---")
res_po = client.get(f'/api/pharmacy/purchase-orders/?facility={facility_id}')
print(f"GET PO Status: {res_po.status_code}, PO Count: {len(res_po.data.get('results', res_po.data))}")
assert res_po.status_code == 200

# Create PO
med = MedicineMaster.objects.first()
po_payload = {
    'vendor': created_vendor_id,
    'facility': facility_id,
    'notes': 'Urgent restock test PO',
    'items': [
        {
            'medicine': med.id,
            'ordered_quantity': 50,
            'unit_price': 2.50
        }
    ]
}
res_po_create = client.post('/api/pharmacy/purchase-orders/', po_payload, format='json')
print(f"POST PO Status: {res_po_create.status_code}")
assert res_po_create.status_code in [200, 201], f"Create PO failed: {res_po_create.data}"
po_id = res_po_create.data['id']
po_item_id = res_po_create.data['items'][0]['id']

# Receive Items for PO
receive_payload = {
    'received_items': [
        {
            'item_id': po_item_id,
            'batch_number': 'TEST-BATCH-2026',
            'mfg_date': '2026-01-01',
            'expiry_date': '2027-12-31',
            'received_qty': 50,
            'unit_cost': 2.50
        }
    ]
}
res_receive = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive_items/', receive_payload, format='json')
print(f"POST Receive Items Status: {res_receive.status_code}")
assert res_receive.status_code == 200, f"Receive items failed: {res_receive.data}"

# 6. Prescriptions and Controlled FEFO Dispensing
print("\n--- 6. Testing Prescriptions & Controlled Dispense ---")

from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.visits.models import Visit

# Create a test pending prescription with a new visit and consultation
import uuid
p = Patient.objects.filter(registered_at_facility_id=facility_id).first() or Patient.objects.first()
v = Visit.objects.create(
    patient=p,
    facility_id=facility_id,
    visit_id=f"V-{uuid.uuid4().hex[:8].upper()}",
    chief_complaint='Acute fever and body ache',
    status='COMPLETED'
)
cons = Consultation.objects.create(
    visit=v,
    patient=p,
    facility_id=facility_id,
    diagnosis_name='Viral Fever',
    treatment_plan='Prescription issued'
)

rx = Prescription.objects.create(
    consultation=cons,
    patient=p,
    facility_id=facility_id,
    status='PENDING'
)
PrescriptionItem.objects.create(
    prescription=rx,
    medicine_name='Paracetamol',
    dosage='500mg',
    quantity=10,
    status='PENDING'
)

dispense_payload = {
    'prescription_id': rx.id
}
res_dispense = client.post('/api/pharmacy/dispense/', dispense_payload, format='json')
print(f"POST Dispense Status: {res_dispense.status_code}")
print(f"Dispense Result: {res_dispense.data}")
assert res_dispense.status_code == 200, f"Dispense failed: {res_dispense.data}"

rx.refresh_from_db()
print(f"Prescription Status after dispense: {rx.status}")
assert rx.status in ['DISPENSED', 'PARTIALLY_DISPENSED']

# 7. Alerts
print("\n--- 7. Testing GET /api/pharmacy/alerts/ ---")
res_alerts = client.get(f'/api/pharmacy/alerts/?facility={facility_id}')
alerts_list = res_alerts.data.get('alerts', res_alerts.data) if isinstance(res_alerts.data, dict) else res_alerts.data
print(f"GET Alerts Status: {res_alerts.status_code}, Alerts Count: {len(alerts_list)}")
assert res_alerts.status_code == 200

# 8. Reports
print("\n--- 8. Testing GET /api/pharmacy/reports/ ---")
res_reports = client.get(f'/api/pharmacy/reports/?facility={facility_id}')
print(f"GET Reports Status: {res_reports.status_code}, Report Keys: {list(res_reports.data.keys())}")
assert res_reports.status_code == 200

# 9. Stock Transactions
print("\n--- 9. Testing GET /api/pharmacy/transactions/ ---")
res_tx = client.get(f'/api/pharmacy/transactions/?facility={facility_id}')
print(f"GET Transactions Status: {res_tx.status_code}, Count: {len(res_tx.data.get('results', res_tx.data))}")
assert res_tx.status_code == 200

print("\n=======================================================")
print("ALL PHARMACY MODULE BACKEND OPERATIONS PASSED SUCCESSFULLY!")
print("=======================================================")

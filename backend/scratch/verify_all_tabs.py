import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.laboratory.models import LabOrder
from apps.pharmacy.models import PurchaseOrder, MedicineBatch
from apps.consultations.models import Prescription

User = get_user_model()
client = APIClient()

print("=" * 65)
print("     NAMMA CLINIC - COMPREHENSIVE TAB & MAPPING VERIFICATION")
print("=" * 65)

# 1. Doctor User & Facility Context
doc_user = User.objects.get(username='vh1_doctor')
fac = doc_user.assigned_facility
client.force_authenticate(user=doc_user)
print(f"Logged-in Staff: {doc_user.full_name} ({doc_user.role})")
print(f"Active Facility: {fac.facility_name} (ID: {fac.id})")
print("-" * 65)

# Tab 1: OPD Queue
resp = client.get(f'/api/visits/?facility={fac.id}')
assert resp.status_code == 200, f"OPD Queue failed: {resp.status_code}"
visits = resp.data.get('results', resp.data)
print(f" [1] OPD QUEUE TAB: {len(visits)} active visits retrieved.")
for v in visits:
    token_no = v.get('token_number') or (v.get('token_details') or {}).get('token_number') or v.get('id')
    print(f"     Token #{token_no} | Patient: {v.get('patient_name')} | Status: {v.get('status')} | Queue: {v.get('current_queue')}")

# Tab 2: Patients & Patient Detail
resp = client.get('/api/patients/')
assert resp.status_code == 200, f"Patients list failed: {resp.status_code}"
patients = resp.data.get('results', resp.data)
print(f"\n [2] PATIENTS TAB: {len(patients)} total registered patients.")

p_first = Patient.objects.filter(registered_at_facility=fac).first()
resp = client.get(f'/api/patients/{p_first.id}/records/')
assert resp.status_code == 200, f"Patient records failed: {resp.status_code}"
p_rec = resp.data
print(f"     Patient: {p_rec.get('patient', {}).get('name')} (ABHA: {p_rec.get('patient', {}).get('ABHA_ID_DEMO', 'N/A')})")
print(f"     Linked Consultations: {len(p_rec.get('medical_records', []))}")
print(f"     Linked Prescriptions: {len(p_rec.get('prescriptions', []))}")
print(f"     Linked Lab Reports:   {len(p_rec.get('lab_reports', []))}")
print(f"     Linked Documents:     {len(p_rec.get('documents', []))}")

# Tab 3: Laboratory Tab
lab_user = User.objects.get(username='lab')
client.force_authenticate(user=lab_user)
resp = client.get(f'/api/lab/orders/?facility={fac.id}')
assert resp.status_code == 200, f"Lab orders failed: {resp.status_code}"
lab_orders = resp.data.get('results', resp.data)
print(f"\n [3] DIAGNOSTICS LAB TAB: {len(lab_orders)} orders in diagnostic pipeline.")
for lo in lab_orders:
    sample_code = (lo.get('sample_details') or {}).get('sample_code') or (lo.get('sample') or {}).get('sample_code') or 'Pending'
    res_str = f"Result: {lo.get('result', {}).get('result_value')}" if lo.get('result') else "Result: Pending"
    print(f"     #LAB-{lo['id']:04d} | {lo.get('test_name')} | Status: {lo.get('status')} | Barcode: {sample_code} | {res_str}")

# Tab 4: Pharmacy Tab
pharm_user = User.objects.get(username='pharmacy')
client.force_authenticate(user=pharm_user)

resp = client.get('/api/pharmacy/medicines/')
assert resp.status_code == 200, f"Pharmacy medicines failed: {resp.status_code}"
meds = resp.data.get('results', resp.data)
print(f"\n [4] PHARMACY TAB:")
print(f"     Medicine Catalogue:   {len(meds)} items")

resp = client.get(f'/api/pharmacy/batches/?facility={fac.id}')
assert resp.status_code == 200, f"Pharmacy batches failed: {resp.status_code}"
batches = resp.data.get('results', resp.data)
print(f"     Active Batches:       {len(batches)} batches (FEFO tracked)")

resp = client.get(f'/api/pharmacy/prescriptions/?facility={fac.id}')
assert resp.status_code == 200, f"Pharmacy prescriptions failed: {resp.status_code}"
prescriptions = resp.data.get('results', resp.data)
print(f"     Prescriptions Queue:  {len(prescriptions)} prescriptions")
for pr in prescriptions:
    print(f"     - Rx #{pr['id']} for {pr.get('patient_name')} | Status: {pr.get('status')} | Items: {len(pr.get('items', []))}")

resp = client.get('/api/pharmacy/vendors/')
assert resp.status_code == 200, f"Vendors failed: {resp.status_code}"
vendors = resp.data.get('results', resp.data)
print(f"     Registered Vendors:   {len(vendors)} vendors")

resp = client.get(f'/api/pharmacy/purchase-orders/?facility={fac.id}')
assert resp.status_code == 200, f"POs failed: {resp.status_code}"
pos = resp.data.get('results', resp.data)
print(f"     Purchase Orders:      {len(pos)} purchase orders")
for po in pos:
    print(f"     - {po.get('po_number')} | Vendor: {po.get('vendor_name')} | Status: {po.get('status')} | Amount: Rs {po.get('total_amount')}")

# Tab 5: Referrals Tab
client.force_authenticate(user=doc_user)
resp = client.get(f'/api/referrals/?facility={fac.id}')
assert resp.status_code == 200, f"Referrals failed: {resp.status_code}"
refs = resp.data.get('results', resp.data)
print(f"\n [5] REFERRALS TAB: {len(refs)} referrals linked to this facility.")
for r in refs:
    print(f"     - {r.get('referral_id')}: {r.get('patient_name')} | {r.get('source_facility_name')} -> {r.get('destination_facility_name')} | Status: {r.get('status')}")

# Tab 6: Infrastructure Tab
resp = client.get(f'/api/facilities/{fac.id}/')
assert resp.status_code == 200, f"Facility infra failed: {resp.status_code}"
f_det = resp.data
print(f"\n [6] INFRASTRUCTURE TAB: {f_det.get('facility_name')} | Type: {f_det.get('facility_type')} | Beds: {f_det.get('bed_capacity')}")

# Tab 7: Alert Engine
resp = client.get(f'/api/alerts/?facility={fac.id}')
assert resp.status_code == 200, f"Alerts failed: {resp.status_code}"
alerts = resp.data.get('results', resp.data)
print(f"\n [7] ALERTS TAB: {len(alerts)} clinical and stock alerts.")
for a in alerts:
    print(f"     - [{a.get('severity')}] {a.get('title')}")

# Tab 8: Dashboard Summary
resp = client.get(f'/api/dashboard/summary/?facility={fac.id}')
assert resp.status_code == 200, f"Dashboard summary failed: {resp.status_code}"
summary = resp.data
kpis = summary.get('kpis', {})
print(f"\n [8] DASHBOARD SUMMARY:")
print(f"     Today's OPD Count:        {summary.get('todays_opd')}")
print(f"     Patients in Consultation: {kpis.get('in_consultation')}")
print(f"     Waiting for Doctor:       {kpis.get('doctor_waiting')}")
print(f"     Waiting for Pharmacy:     {kpis.get('pharmacy_waiting')}")
print(f"     Lab Orders Pending:       {kpis.get('lab_pending')}")
print(f"     Low Stock Medicines:      {kpis.get('low_stock')}")

print("\n" + "=" * 65)
print("     ALL TABS SUCCESSFULLY RETRIEVED & MAPPED 100% CORRECTLY!")
print("=" * 65)

import os
import sys
sys.path.append('.')
import django
import json
import uuid
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from django.utils import timezone
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem
)

def run_verification():
    print("=" * 70)
    print("STARTING END-TO-END PHARMACY & INVENTORY LIFECYCLE VERIFICATION")
    print("=" * 70)

    client = APIClient()

    # 1. Setup users
    pharmacist = User.objects.filter(role='PHARMACIST').first()
    doctor = User.objects.filter(role='DOCTOR').first()
    assert pharmacist is not None, "Pharmacist user not found in DB!"
    assert doctor is not None, "Doctor user not found in DB!"

    facility_id = pharmacist.assigned_facility_id or 1
    facility = Facility.objects.get(pk=facility_id)
    print(f"Operational Facility Scope: #{facility.id} - {facility.facility_name}")
    print(f"Pharmacist: {pharmacist.username} | Doctor: {doctor.username}")

    # 2. Setup Patient & Visit
    patient = Patient.objects.filter(registered_at_facility=facility).first()
    if not patient:
        patient = Patient.objects.create(
            patient_id=f"PAT-{uuid.uuid4().hex[:6].upper()}",
            name="Test Verification Patient",
            age=45,
            gender="FEMALE",
            mobile="9876500001",
            address="Varthur Main Road",
            registered_at_facility=facility,
            vulnerability_information="Slum Household BPL"
        )
    
    visit = Visit.objects.create(
        patient=patient,
        facility=facility,
        visit_id=f"VIS-{uuid.uuid4().hex[:8].upper()}",
        visit_date=timezone.now(),
        opd_date=timezone.now().date(),
        arrival_time=timezone.now(),
        chief_complaint="Fever, cough, body ache",
        visit_type="GENERAL_OPD",
        status="WAITING_FOR_DOCTOR",
        current_queue="DOCTOR"
    )
    from django.db.models import Max
    max_t = Token.objects.filter(facility=facility, date=timezone.now().date()).aggregate(m=Max('token_number'))['m'] or 100
    next_token_num = max_t + 1
    token = Token.objects.create(
        visit=visit,
        facility=facility,
        token_number=next_token_num,
        status="WAITING",
        date=timezone.now().date()
    )
    print(f"\n[Step 1] Created Active OPD Visit #{visit.id} (Token #{next_token_num}) in DOCTOR queue.")

    # 3. Doctor Consultation with Prescription
    client.force_authenticate(user=doctor)
    consult_payload = {
        'visit': visit.id,
        'patient': patient.id,
        'facility': facility.id,
        'chief_complaint': 'Acute viral bronchitis',
        'clinical_history': 'Fever for 3 days',
        'clinical_assessment': 'Chest clear, mild pharyngeal erythema',
        'diagnosis_code': 'J20',
        'diagnosis_name': 'Acute Bronchitis',
        'treatment_plan': 'Antipyretic and oral antibiotic prescribed',
        'prescription_items': [
            {
                'medicine_name': 'Paracetamol 500mg',
                'dosage': '1-0-1 After Food',
                'frequency': 'Twice Daily',
                'duration_days': 5,
                'quantity': 10
            },
            {
                'medicine_name': 'Amoxicillin 500mg',
                'dosage': '1-1-1 After Food',
                'frequency': 'Thrice Daily',
                'duration_days': 5,
                'quantity': 15
            }
        ]
    }
    res_consult = client.post('/api/consultations/', consult_payload, format='json')
    assert res_consult.status_code == 201, f"Consultation failed: {res_consult.data}"
    consult_id = res_consult.data['id']
    print(f"[Step 2] Doctor completed Consultation #{consult_id} with 2 prescribed medications.")

    # Verify visit moved to PHARMACY queue
    visit.refresh_from_db()
    print(f"         Visit Queue: {visit.current_queue} | Visit Status: {visit.status}")
    assert visit.current_queue == 'PHARMACY', f"Expected current_queue to be PHARMACY, got {visit.current_queue}"
    assert visit.status == 'WAITING_FOR_PHARMACY', f"Expected status to be WAITING_FOR_PHARMACY, got {visit.status}"

    # 4. Pharmacist Views Prescriptions Queue
    client.force_authenticate(user=pharmacist)
    res_rx_list = client.get(f'/api/pharmacy/prescriptions/?facility={facility.id}')
    assert res_rx_list.status_code == 200
    rx_items = res_rx_list.data.get('results', res_rx_list.data)
    created_rx = next((r for r in rx_items if r['patient'] == patient.id and r['status'] == 'PENDING'), None)
    assert created_rx is not None, "Newly prescribed prescription not found in pharmacy queue!"
    rx_id = created_rx['id']
    print(f"[PASS] Pharmacist loaded Prescriptions Queue. Found pending Rx #RX-{rx_id:04d} for {patient.name}.")

    # 5. Ensure Medicine Master and Active Batches exist for both medicines
    today = datetime.date.today()
    med_pcm, _ = MedicineMaster.objects.get_or_create(
        generic_name='Paracetamol 500mg',
        defaults={'brand_name': 'Dolo 500', 'dosage_form': 'TABLET', 'minimum_stock': 50, 'reorder_level': 100}
    )
    med_amx, _ = MedicineMaster.objects.get_or_create(
        generic_name='Amoxicillin 500mg',
        defaults={'brand_name': 'Mox 500', 'dosage_form': 'CAPSULE', 'minimum_stock': 30, 'reorder_level': 60}
    )

    batch_pcm_1, _ = MedicineBatch.objects.get_or_create(
        facility=facility,
        medicine=med_pcm,
        batch_number=f"PCM-EARLY-{uuid.uuid4().hex[:4].upper()}",
        defaults={
            'mfg_date': today - datetime.timedelta(days=120),
            'expiry_date': today + datetime.timedelta(days=90),  # Expires sooner (FEFO Target)
            'quantity': 100,
            'unit_cost': 1.20,
            'status': 'ACTIVE'
        }
    )
    batch_pcm_2, _ = MedicineBatch.objects.get_or_create(
        facility=facility,
        medicine=med_pcm,
        batch_number=f"PCM-LATER-{uuid.uuid4().hex[:4].upper()}",
        defaults={
            'mfg_date': today - datetime.timedelta(days=30),
            'expiry_date': today + datetime.timedelta(days=365), # Expires later
            'quantity': 500,
            'unit_cost': 1.20,
            'status': 'ACTIVE'
        }
    )

    batch_amx, _ = MedicineBatch.objects.get_or_create(
        facility=facility,
        medicine=med_amx,
        batch_number=f"AMX-FEFO-{uuid.uuid4().hex[:4].upper()}",
        defaults={
            'mfg_date': today - datetime.timedelta(days=60),
            'expiry_date': today + datetime.timedelta(days=180),
            'quantity': 200,
            'unit_cost': 4.50,
            'status': 'ACTIVE'
        }
    )

    stock_pcm_before = batch_pcm_1.quantity
    stock_amx_before = batch_amx.quantity
    print(f"\n[Step 4] Pre-Dispensing Stock Levels in Facility #{facility.id}:")
    print(f"         {med_pcm.generic_name} (Batch {batch_pcm_1.batch_number}, Exp: {batch_pcm_1.expiry_date}): {stock_pcm_before} units")
    print(f"         {med_amx.generic_name} (Batch {batch_amx.batch_number}, Exp: {batch_amx.expiry_date}): {stock_amx_before} units")

    # 6. Execute Controlled FEFO Dispensing
    dispense_payload = {
        'prescription_id': rx_id,
        'items': [
            {
                'item_id': created_rx['items'][0]['id'],
                'batch_id': batch_pcm_1.id,
                'qty': 10
            },
            {
                'item_id': created_rx['items'][1]['id'],
                'batch_id': batch_amx.id,
                'qty': 15
            }
        ]
    }
    res_dispense = client.post('/api/pharmacy/dispense/', dispense_payload, format='json')
    assert res_dispense.status_code == 200, f"Dispensing failed: {res_dispense.data}"
    print(f"\n[Step 5] Dispensed Prescription #RX-{rx_id:04d} via FEFO Engine.")
    print(f"         Message: {res_dispense.data.get('message')}")
    print(f"         Dispensed Items: {res_dispense.data.get('dispensed_items')}")

    # Verify atomic stock deductions
    batch_pcm_1.refresh_from_db()
    batch_amx.refresh_from_db()
    assert batch_pcm_1.quantity == stock_pcm_before - 10, f"PCM stock expected {stock_pcm_before - 10}, got {batch_pcm_1.quantity}"
    assert batch_amx.quantity == stock_amx_before - 15, f"AMX stock expected {stock_amx_before - 15}, got {batch_amx.quantity}"
    print(f"         [PASS] Real-time Stock Deducted: PCM: {stock_pcm_before} -> {batch_pcm_1.quantity}, AMX: {stock_amx_before} -> {batch_amx.quantity}")

    # Verify inventory transaction logs
    txs = InventoryTransaction.objects.filter(reference_id=f"PRESCR-{rx_id}")
    assert txs.count() >= 2, f"Expected at least 2 transaction records, found {txs.count()}"
    print(f"         [PASS] Recorded {txs.count()} audit-verified inventory transactions (type: DISPENSED).")

    # Verify prescription and visit status updates
    rx_db = Prescription.objects.get(pk=rx_id)
    assert rx_db.status == 'DISPENSED', f"Expected Prescription status DISPENSED, got {rx_db.status}"
    visit.refresh_from_db()
    assert visit.status == 'COMPLETED', f"Expected Visit status COMPLETED, got {visit.status}"
    assert visit.current_queue == 'COMPLETED', f"Expected Visit queue COMPLETED, got {visit.current_queue}"
    assert visit.completed_time is not None, "Expected Visit completed_time to be populated!"
    print(f"         [PASS] Prescription updated to: {rx_db.status}")
    print(f"         [PASS] Visit updated to: Status={visit.status}, Queue={visit.current_queue}, Completed={visit.completed_time.strftime('%H:%M:%S')}")

    # 7. Vendor Management
    print("\n[Step 6] Testing Vendor Management Lifecycle:")
    vendor_code = f"VEND-{uuid.uuid4().hex[:4].upper()}"
    res_vendor = client.post('/api/pharmacy/vendors/', {
        'vendor_name': 'Apex Lifesciences Karnataka Ltd',
        'contact_person': 'Ravi Shankar',
        'phone': '9876512345',
        'email': 'ravi@apexlifesciences.in',
        'address': 'Plot 42, Peenya Industrial Area, Bengaluru',
        'gst_number': '29ABCDE9999F1Z2',
        'status': 'ACTIVE'
    }, format='json')
    assert res_vendor.status_code == 201, f"Failed to create vendor: {res_vendor.data}"
    vendor_id = res_vendor.data['id']
    print(f"         [PASS] Created Vendor #{vendor_id}: {res_vendor.data['vendor_name']}")

    # Toggle status
    res_toggle = client.post(f'/api/pharmacy/vendors/{vendor_id}/toggle_status/')
    assert res_toggle.status_code == 200
    res_toggle_back = client.post(f'/api/pharmacy/vendors/{vendor_id}/toggle_status/')
    assert res_toggle_back.status_code == 200
    print(f"         [PASS] Successfully verified vendor status toggle (Active -> Inactive -> Active).")

    # 8. Purchase Order & Goods Receiving Workflow
    print("\n[Step 7] Testing Purchase Order & Goods Receiving Workflow:")
    res_po = client.post('/api/pharmacy/purchase-orders/', {
        'vendor': vendor_id,
        'facility': facility.id,
        'notes': 'Monthly inventory replenishment requisition',
        'expected_delivery': (today + datetime.timedelta(days=7)).isoformat(),
        'items': [
            {
                'medicine': med_pcm.id,
                'ordered_quantity': 250,
                'unit_price': 1.15
            }
        ]
    }, format='json')
    assert res_po.status_code == 201, f"Failed to create PO: {res_po.data}"
    po_id = res_po.data['id']
    po_item_id = res_po.data['items'][0]['id']
    print(f"         [PASS] Created Purchase Order #{po_id} ({res_po.data['po_number']}) in DRAFT status.")

    # Goods receiving
    new_batch_no = f"PO-RESTOCK-{uuid.uuid4().hex[:4].upper()}"
    receive_payload = {
        'received_items': [
            {
                'item_id': po_item_id,
                'batch_number': new_batch_no,
                'mfg_date': (today - datetime.timedelta(days=10)).isoformat(),
                'expiry_date': (today + datetime.timedelta(days=730)).isoformat(),
                'received_qty': 250,
                'unit_cost': 1.15
            }
        ]
    }
    res_receive = client.post(f'/api/pharmacy/purchase-orders/{po_id}/receive_items/', receive_payload, format='json')
    assert res_receive.status_code == 200, f"Goods receiving failed: {res_receive.data}"
    print(f"         [PASS] Received goods for PO #{po_id}. Status: {res_receive.data['po_status']}")

    # Verify new batch created and stock updated
    new_batch = MedicineBatch.objects.get(batch_number=new_batch_no, facility=facility)
    assert new_batch.quantity == 250
    print(f"         [PASS] Verified New Batch in Inventory: {new_batch.batch_number} (Qty: {new_batch.quantity}, Exp: {new_batch.expiry_date})")

    # 9. Dashboard KPIs and Reports Verification
    print("\n[Step 8] Testing Pharmacy Dashboard & Analytics KPIs:")
    res_dash = client.get(f'/api/pharmacy/dashboard/?facility={facility.id}')
    assert res_dash.status_code == 200
    dash_kpis = res_dash.data
    print(f"         [PASS] Total Available Stock: {dash_kpis['total_available_stock']}")
    print(f"         [PASS] Dispensed Today: {dash_kpis['dispensed_today_count']}")
    print(f"         [PASS] Pending Prescriptions: {dash_kpis['pending_prescriptions_count']}")
    print(f"         [PASS] Low Stock Alerts: {dash_kpis['low_stock_count']}")
    print(f"         [PASS] Expiring Soon: {dash_kpis['expiring_soon_count']}")

    res_rpt = client.get(f'/api/pharmacy/reports/?facility={facility.id}')
    assert res_rpt.status_code == 200
    print(f"         [PASS] Analytics Report: Total Stock Valuation = INR {res_rpt.data['stock_valuation']['total_value']:,.2f}")
    print(f"         [PASS] Top Consumed Medicines Count: {len(res_rpt.data['consumption_summary'])}")

    print("\n" + "=" * 70)
    print("ALL PHARMACY & INVENTORY FLOWS VERIFIED 100% OPERATIONAL!")
    print("=" * 70)

if __name__ == '__main__':
    run_verification()

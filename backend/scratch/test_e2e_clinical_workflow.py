import os, sys, django, datetime, uuid
sys.path.insert(0, os.path.abspath('backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.patients.models import Patient
from apps.facilities.models import Facility
from apps.accounts.models import User
from apps.visits.models import Visit, Token
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabOrder, LabTestMaster, LabSample, LabResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from rest_framework.test import APIClient

fac = Facility.objects.filter(pk=116).first() or Facility.objects.first()
doctor_user = User.objects.filter(assigned_facility=fac, role='DOCTOR').first()
lab_user = User.objects.filter(assigned_facility=fac, role='LAB_TECHNICIAN').first()
pharm_user = User.objects.filter(assigned_facility=fac, role='PHARMACIST').first()
patient = Patient.objects.filter(registered_at_facility=fac).first() or Patient.objects.first()
test_master = LabTestMaster.objects.first()
medicine = MedicineMaster.objects.first()

today = datetime.date.today()
batch, _ = MedicineBatch.objects.get_or_create(
    facility=fac,
    medicine=medicine,
    batch_number='TEST-BATCH-888',
    defaults={
        'expiry_date': today + datetime.timedelta(days=180),
        'quantity': 500,
        'status': 'ACTIVE'
    }
)
batch.quantity = 500
batch.status = 'ACTIVE'
batch.save()

client = APIClient()

print("Starting Full End-to-End Clinical Flow Test...")
print(f"Facility: {fac.facility_name} (ID: {fac.id})")
print(f"Patient: {patient.name} (ID: {patient.id})")

# Cleanup any previous test token
Token.objects.filter(token_number=8888).delete()
Visit.objects.filter(visit_id__startswith='TEST-E2E-').delete()

from django.utils import timezone

visit = None
try:
    # 1. OPD Registration
    client.force_authenticate(user=doctor_user)
    visit_id = f"TEST-E2E-{uuid.uuid4().hex[:6]}"
    visit = Visit.objects.create(
        visit_id=visit_id,
        facility=fac,
        patient=patient,
        opd_date=today,
        arrival_time=timezone.now(),
        current_queue='DOCTOR',
        status='WAITING_FOR_DOCTOR',
        priority='NORMAL',
        chief_complaint='Fever & Cough'
    )
    token = Token.objects.create(
        facility=fac,
        visit=visit,
        token_number=8888,
        date=today,
        status='WAITING'
    )
    print(f"Step 1: Patient registered. Visit #{visit.id}, Token #{token.token_number}, status={visit.status}, queue={visit.current_queue}")

    # Check Dashboard API
    dash_res = client.get(f'/api/dashboard/summary/?facility={fac.id}&date={today}')
    assert dash_res.status_code == 200
    kpis = dash_res.data.get('kpis', {})
    print(f"Dashboard Initial -> Doctor Waiting: {kpis.get('doctor_waiting')}, Lab Pending: {kpis.get('lab_pending')}, Pharmacy Waiting: {kpis.get('pharmacy_waiting')}")

    # 2. Doctor Consultation with Lab Order
    client.force_authenticate(user=doctor_user)
    consult_payload = {
        'visit': visit.id,
        'patient': patient.id,
        'facility': fac.id,
        'chief_complaint': 'High fever 3 days',
        'diagnosis_name': 'Suspected Dengue / Viral Infection',
        'lab_test_ids': [test_master.id],
        'prescription_items': []
    }
    c_res = client.post('/api/consultations/', consult_payload, format='json')
    assert c_res.status_code in [200, 201], f"Consultation save failed: {c_res.data}"
    visit.refresh_from_db()
    print(f"Step 2: Doctor ordered lab test. Visit #{visit.id}, Token #{visit.token.token_number}, status={visit.status}, queue={visit.current_queue}")
    assert visit.current_queue == 'LAB', f"Expected LAB queue, got {visit.current_queue}"
    assert visit.status == 'LAB_PENDING', f"Expected LAB_PENDING, got {visit.status}"
    assert visit.token.token_number == 8888, f"Token number must remain 8888!"

    # Check Lab Orders created
    lab_orders = LabOrder.objects.filter(visit=visit)
    assert lab_orders.count() == 1, "Lab order should exist"
    lab_order = lab_orders.first()
    print(f"Lab Order #{lab_order.id} ({lab_order.test_master.name}) created with status={lab_order.status}, token={lab_order.visit.token.token_number}")

    # Check Dashboard reflects lab_pending
    dash_lab = client.get(f'/api/dashboard/summary/?facility={fac.id}&date={today}')
    k_lab = dash_lab.data.get('kpis', {})
    print(f"Dashboard During Lab -> Lab Pending: {k_lab.get('lab_pending')}, Doctor Waiting: {k_lab.get('doctor_waiting')}")

    # 3. Lab Specimen Collection
    client.force_authenticate(user=lab_user)
    col_res = client.post(f'/api/lab/orders/{lab_order.id}/collect-sample/', {'sample_type': 'Blood', 'sample_code': 'SMP-8888'}, format='json')
    assert col_res.status_code == 200, f"Sample collection failed: {col_res.data}"
    visit.refresh_from_db()
    print(f"Step 3: Lab collected sample. Visit status={visit.status}, queue={visit.current_queue}")
    assert visit.status == 'LAB_IN_PROGRESS'

    # 4. Lab Result Verification
    save_res = client.post(f'/api/lab/orders/{lab_order.id}/save-result/', {
        'result_value': 'Negative',
        'interpretation_flag': 'NORMAL',
        'notes': 'Verified normal'
    }, format='json')
    assert save_res.status_code == 200, f"Save result failed: {save_res.data}"
    visit.refresh_from_db()
    print(f"Step 4: Lab verified results. Visit status={visit.status}, queue={visit.current_queue}, Token #{visit.token.token_number}")
    assert visit.current_queue == 'DOCTOR', f"Expected DOCTOR queue, got {visit.current_queue}"
    assert visit.status == 'LAB_COMPLETED', f"Expected LAB_COMPLETED, got {visit.status}"
    assert visit.token.token_number == 8888

    # Check Dashboard API reflects re-consultation waiting
    client.force_authenticate(user=doctor_user)
    dash_res2 = client.get(f'/api/dashboard/summary/?facility={fac.id}&date={today}')
    kpis2 = dash_res2.data.get('kpis', {})
    print(f"Dashboard Post-Lab -> Doctor Waiting: {kpis2.get('doctor_waiting')}, Lab Pending: {kpis2.get('lab_pending')}")

    # 5. Doctor Re-consultation & Medicine Prescription
    reconsult_payload = {
        'visit': visit.id,
        'patient': patient.id,
        'facility': fac.id,
        'chief_complaint': 'High fever responding to hydration, lab normal',
        'diagnosis_name': 'Acute Viral Pyrexia',
        'prescription_items': [{
            'medicine_name': medicine.generic_name,
            'dosage': '1-0-1',
            'quantity': 10
        }],
        'lab_test_ids': []
    }
    re_res = client.post('/api/consultations/', reconsult_payload, format='json')
    assert re_res.status_code in [200, 201], f"Re-consultation save failed: {re_res.data}"
    visit.refresh_from_db()
    print(f"Step 5: Doctor re-consulted and prescribed medicine. Visit status={visit.status}, queue={visit.current_queue}, Token #{visit.token.token_number}")
    assert visit.current_queue == 'PHARMACY', f"Expected PHARMACY queue, got {visit.current_queue}"
    assert visit.status == 'WAITING_FOR_PHARMACY', f"Expected WAITING_FOR_PHARMACY, got {visit.status}"
    assert visit.token.token_number == 8888

    # Check Pharmacy Prescriptions API
    client.force_authenticate(user=pharm_user)
    rx_res = client.get(f'/api/pharmacy/prescriptions/?facility={fac.id}&date={today}')
    assert rx_res.status_code == 200, f"Get prescriptions failed: {rx_res.data}"
    rx_list = rx_res.data.get('results', rx_res.data)
    matching_rx = [r for r in rx_list if r.get('visit_id') == visit.id or r.get('patient') == patient.id]
    assert len(matching_rx) > 0, "Prescription must be visible in pharmacy prescriptions list"
    rx_item = matching_rx[0]
    print(f"Pharmacy Prescriptions API sees Rx #{rx_item['id']}, Token #{rx_item.get('token_number')}, status={rx_item.get('status')}")
    assert rx_item.get('token_number') == 8888, f"Expected token 8888 in prescription, got {rx_item.get('token_number')}"

    # Check Dashboard reflects pharmacy_waiting
    dash_pharm = client.get(f'/api/dashboard/summary/?facility={fac.id}&date={today}')
    k_pharm = dash_pharm.data.get('kpis', {})
    print(f"Dashboard During Pharmacy -> Pharmacy Waiting: {k_pharm.get('pharmacy_waiting')}, Doctor Waiting: {k_pharm.get('doctor_waiting')}")

    # 6. Pharmacist Controlled Dispense
    disp_res = client.post('/api/pharmacy/dispense/', {
        'prescription_id': rx_item['id'],
        'items': [{
            'item_id': rx_item['items'][0]['id'],
            'batch_id': batch.id,
            'qty': 10
        }]
    }, format='json')
    assert disp_res.status_code == 200, f"Dispense failed: {disp_res.data}"
    print(f"Step 6: Pharmacist dispensed prescription: {disp_res.data.get('message')}")

    visit.refresh_from_db()
    print(f"Final Visit Status: {visit.status}, Queue: {visit.current_queue}, Token Status: {visit.token.status}, Token #{visit.token.token_number}")
    assert visit.status == 'COMPLETED'
    assert visit.current_queue == 'COMPLETED'
    assert visit.token.status == 'COMPLETED'
    assert visit.token.token_number == 8888

    # Final Dashboard Check
    dash_res3 = client.get(f'/api/dashboard/summary/?facility={fac.id}&date={today}')
    kpis3 = dash_res3.data.get('kpis', {})
    print(f"Dashboard Final -> Completed: {kpis3.get('completed')}, Pharmacy Waiting: {kpis3.get('pharmacy_waiting')}")

    print("\n>>> ALL 6 STAGES OF THE CLINICAL WORKFLOW PASSED WITH 100% ACCURACY & DATA INTEGRITY! <<<")

finally:
    if visit:
        LabOrder.objects.filter(visit=visit).delete()
        consult = getattr(visit, 'consultation', None)
        if consult:
            rx = getattr(consult, 'prescription', None)
            if rx:
                rx.items.all().delete()
                rx.delete()
            consult.delete()
        Token.objects.filter(visit=visit).delete()
        visit.delete()
    print("Cleaned up test data.")

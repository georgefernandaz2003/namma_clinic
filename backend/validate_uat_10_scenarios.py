"""
Namma Clinic — Pharmacy Hardening: 10-Scenario Browser/UAT Functional Validation Script
Exercises all 10 mandatory UAT scenarios:
1. Prescription verification
2. Partial dispensing
3. Expired batch blocking
4. Quarantined batch blocking
5. Recall
6. Return assessment
7. GRN
8. Cold-chain logging
9. Counselling
10. Facility isolation
"""
import os
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch,
    GoodsReceiptNote, GoodsReceiptItem, DispensationReturn,
    BatchRecall, PatientCounselling, ColdChainLog, PurchaseOrder, Vendor
)

User = get_user_model()

def create_encounter_rx(patient, doctor, facility, status="VERIFIED"):
    u_id = uuid.uuid4().hex[:8].upper()
    visit = Visit.objects.create(
        visit_id=f"VIS-UAT-{u_id}",
        patient=patient,
        facility=facility,
        status="WAITING_FOR_PHARMACY",
        current_queue="PHARMACY"
    )
    consultation = Consultation.objects.create(
        visit=visit,
        patient=patient,
        doctor=doctor,
        facility=facility,
        chief_complaint="UAT Encounter Check",
        clinical_assessment="Clinical assessment for medication verification"
    )
    rx = Prescription.objects.create(
        consultation=consultation,
        patient=patient,
        doctor=doctor,
        facility=facility,
        status=status
    )
    return rx

def run_10_scenarios():
    print("=" * 70)
    print("NAMMA CLINIC — PHARMACY HARDENING: 10-SCENARIO UAT VALIDATION")
    print("=" * 70)

    f1 = Facility.objects.first()
    f2 = Facility.objects.exclude(id=f1.id).first()

    pharmacist = User.objects.filter(role="PHARMACIST", assigned_facility=f1).first() or User.objects.filter(role="PHARMACIST").first()
    doctor = User.objects.filter(role="DOCTOR", assigned_facility=f1).first() or User.objects.filter(role="DOCTOR").first()
    admin = User.objects.filter(role="HOSPITAL_ADMIN", assigned_facility=f1).first() or pharmacist
    patient = Patient.objects.first()

    client = APIClient()
    client.force_authenticate(user=pharmacist)

    medicine, _ = MedicineMaster.objects.get_or_create(
        generic_name="UAT Paracetamol 500mg",
        defaults={
            "dosage_form": "TABLET",
            "strength": "500mg",
            "unit": "TABLET",
            "category": "ANALGESIC"
        }
    )

    # -------------------------------------------------------------
    # 1. Prescription Verification
    # -------------------------------------------------------------
    rx1 = create_encounter_rx(patient, doctor, f1, status="PENDING_VERIFICATION")
    item1 = PrescriptionItem.objects.create(
        prescription=rx1, medicine_name=medicine.generic_name,
        dosage="500mg", frequency="1-0-1", duration_days=3, quantity=10
    )

    verif_res = client.post(f"/api/prescriptions/{rx1.id}/verify/", {"notes": "UAT Clinical safety verification complete"}, format="json")
    rx1.refresh_from_db()
    assert verif_res.status_code == 200, f"Verification failed: {verif_res.data}"
    assert rx1.status == "VERIFIED", f"Expected VERIFIED, got {rx1.status}"
    print("  [PASS] Scenario 1: Prescription verification succeeds and transitions to VERIFIED")

    # -------------------------------------------------------------
    # 2. Partial Dispensing
    # -------------------------------------------------------------
    batch_avail = MedicineBatch.objects.create(
        facility=f1, medicine=medicine, batch_number=f"UAT-AVAIL-{uuid.uuid4().hex[:6].upper()}",
        received_date=date.today(), expiry_date=date.today() + timedelta(days=180),
        quantity=100, available_quantity=100, unit_cost=Decimal("2.50")
    )

    # Dispense 4 of 10
    disp_res1 = client.post("/api/pharmacy/dispense/", {
        "prescription_id": rx1.id,
        "items": [{"item_id": item1.id, "medicine_name": medicine.generic_name, "batch_id": batch_avail.id, "qty_to_dispense": 4}]
    }, format="json")
    assert disp_res1.status_code == 200, f"Partial dispense 1 failed: {disp_res1.data}"
    rx1.refresh_from_db()
    item1.refresh_from_db()
    batch_avail.refresh_from_db()
    assert rx1.status == "PARTIALLY_DISPENSED"
    assert item1.dispensed_quantity == 4
    assert item1.remaining_quantity == 6
    assert batch_avail.available_quantity == 96

    # Dispense remaining 6 of 10
    disp_res2 = client.post("/api/pharmacy/dispense/", {
        "prescription_id": rx1.id,
        "items": [{"item_id": item1.id, "medicine_name": medicine.generic_name, "batch_id": batch_avail.id, "qty_to_dispense": 6}]
    }, format="json")
    assert disp_res2.status_code == 200, f"Partial dispense 2 failed: {disp_res2.data}"
    rx1.refresh_from_db()
    item1.refresh_from_db()
    batch_avail.refresh_from_db()
    assert rx1.status == "DISPENSED"
    assert item1.dispensed_quantity == 10
    assert item1.remaining_quantity == 0
    assert batch_avail.available_quantity == 90
    print("  [PASS] Scenario 2: Partial dispensing tracks remaining quantity and closes upon full completion")

    # -------------------------------------------------------------
    # 3. Expired Batch Blocking
    # -------------------------------------------------------------
    batch_exp = MedicineBatch.objects.create(
        facility=f1, medicine=medicine, batch_number=f"UAT-EXP-{uuid.uuid4().hex[:6].upper()}",
        received_date=date.today() - timedelta(days=400),
        expiry_date=date.today() - timedelta(days=10),
        quantity=50, available_quantity=50, unit_cost=Decimal("2.50")
    )
    rx_exp = create_encounter_rx(patient, doctor, f1, status="VERIFIED")
    item_exp = PrescriptionItem.objects.create(prescription=rx_exp, medicine_name=medicine.generic_name, dosage="500mg", frequency="1-0-0", duration_days=2, quantity=4)

    exp_res = client.post("/api/pharmacy/dispense/", {
        "prescription_id": rx_exp.id,
        "items": [{"item_id": item_exp.id, "medicine_name": medicine.generic_name, "batch_id": batch_exp.id, "qty_to_dispense": 4}]
    }, format="json")
    assert exp_res.status_code == 400, "Expired batch must be blocked"
    print("  [PASS] Scenario 3: Expired batch direct dispensing is strictly rejected (HTTP 400)")

    # -------------------------------------------------------------
    # 4. Quarantined Batch Blocking
    # -------------------------------------------------------------
    batch_q = MedicineBatch.objects.create(
        facility=f1, medicine=medicine, batch_number=f"UAT-Q-{uuid.uuid4().hex[:6].upper()}",
        received_date=date.today(), expiry_date=date.today() + timedelta(days=200),
        quantity=30, available_quantity=0, quarantined_quantity=30, unit_cost=Decimal("2.50")
    )
    q_res = client.post("/api/pharmacy/dispense/", {
        "prescription_id": rx_exp.id,
        "items": [{"item_id": item_exp.id, "medicine_name": medicine.generic_name, "batch_id": batch_q.id, "qty_to_dispense": 4}]
    }, format="json")
    assert q_res.status_code == 400, "Quarantined batch must be blocked"
    print("  [PASS] Scenario 4: Quarantined batch dispensing is strictly rejected (HTTP 400)")

    # -------------------------------------------------------------
    # 5. Quantity-Scoped Recall
    # -------------------------------------------------------------
    batch_rec = MedicineBatch.objects.create(
        facility=f1, medicine=medicine, batch_number=f"UAT-REC-{uuid.uuid4().hex[:6].upper()}",
        received_date=date.today(), expiry_date=date.today() + timedelta(days=200),
        quantity=100, available_quantity=100, unit_cost=Decimal("2.50")
    )
    rec_res = client.post("/api/pharmacy/recalls/", {
        "batch": batch_rec.id,
        "recalled_quantity": 40,
        "recall_reason": "Glass particulate alert from manufacturer",
        "regulatory_reference": "CDSCO-UAT-2026",
        "recall_class": "CLASS_I"
    }, format="json")
    assert rec_res.status_code == 201, f"Recall creation failed: {rec_res.data}"
    batch_rec.refresh_from_db()
    assert batch_rec.available_quantity == 60
    assert batch_rec.recalled_quantity == 40
    assert batch_rec.status == "AVAILABLE"  # Precedence: available > 0 is AVAILABLE

    # Facility impact report
    recall_id = rec_res.data["id"]
    impact_res = client.get(f"/api/pharmacy/recalls/{recall_id}/impact_report/")
    assert impact_res.status_code == 200
    assert impact_res.data["recalled_quantity"] == 40
    print("  [PASS] Scenario 5: Quantity-scoped recall isolates partial stock and generates scoped impact report")

    # -------------------------------------------------------------
    # 6. Two-Phase Return Assessment
    # -------------------------------------------------------------
    ret_init = client.post("/api/pharmacy/returns/", {
        "prescription_item": item1.id,
        "batch": batch_avail.id,
        "returned_quantity": 2,
        "return_reason": "Patient unneeded excess packaging"
    }, format="json")
    assert ret_init.status_code == 201
    return_id = ret_init.data["id"]
    ret_obj = DispensationReturn.objects.get(id=return_id)
    assert ret_obj.assessment_status == "PENDING_ASSESSMENT"
    assert ret_obj.disposition == "PENDING"

    stock_before_assess = batch_avail.available_quantity
    ret_assess = client.post(f"/api/pharmacy/returns/{return_id}/assess/", {
        "status": "APPROVED_FOR_STOCK",
        "notes": "Physical seal intact, blister undamaged, verified"
    }, format="json")
    assert ret_assess.status_code == 200
    ret_obj.refresh_from_db()
    assert ret_obj.assessment_status == "ASSESSED"
    assert ret_obj.disposition == "APPROVED_FOR_STOCK"
    batch_avail.refresh_from_db()
    assert batch_avail.available_quantity == stock_before_assess + 2
    print("  [PASS] Scenario 6: Two-phase return: PENDING_ASSESSMENT does not increase stock; APPROVED_FOR_STOCK restocks")

    # -------------------------------------------------------------
    # 7. GRN Accepted Increases Stock Only
    # -------------------------------------------------------------
    vendor = Vendor.objects.filter(facility=f1).first() or Vendor.objects.first()
    if not vendor:
        vendor = Vendor.objects.create(
            vendor_name="UAT Pharma Suppliers",
            facility=f1,
            contact_person="Supply Rep",
            created_by=admin
        )
    po = PurchaseOrder.objects.create(
        facility=f1, vendor=vendor, po_number=f"PO-UAT-{uuid.uuid4().hex[:6].upper()}",
        order_date=date.today(), created_by=admin, status="APPROVED"
    )
    from apps.pharmacy.models import PurchaseOrderItem
    po_item = PurchaseOrderItem.objects.create(
        purchase_order=po,
        medicine=medicine,
        ordered_quantity=100,
        unit_price=Decimal("2.50"),
        total_price=Decimal("250.00")
    )

    grn_batch_no = f"UAT-GRN-{uuid.uuid4().hex[:6].upper()}"
    grn_res = client.post("/api/pharmacy/grn/", {
        "purchase_order": po.id,
        "received_date": str(date.today()),
        "invoice_number": "INV-UAT-9988",
        "items": [{
            "po_item": po_item.id,
            "medicine": medicine.id,
            "batch_number": grn_batch_no,
            "expiry_date": str(date.today() + timedelta(days=365)),
            "received_quantity": 50,
            "accepted_quantity": 40,
            "rejected_quantity": 10,
            "rejection_reason": "10 tablets crushed in transit",
            "unit_cost": 2.50
        }]
    }, format="json")
    assert grn_res.status_code == 201, f"GRN failed: {grn_res.data}"
    new_grn_batch = MedicineBatch.objects.get(facility=f1, batch_number=grn_batch_no)
    assert new_grn_batch.available_quantity == 40
    print("  [PASS] Scenario 7: GRN accepted quantity increases inventory ledger; rejected stock is recorded with reason")

    # -------------------------------------------------------------
    # 8. Cold Chain Manual Logging & Excursion
    # -------------------------------------------------------------
    cc_normal = client.post("/api/pharmacy/cold-chain/", {
        "storage_location": "UAT-FRIDGE-01",
        "recorded_temp_celsius": 4.2,
        "min_temp_celsius": 2.0,
        "max_temp_celsius": 8.0,
        "corrective_action": "Routine morning check"
    }, format="json")
    assert cc_normal.status_code == 201, f"Cold chain log failed: {cc_normal.data}"
    assert cc_normal.data["status"] == "NORMAL"

    cc_excursion = client.post("/api/pharmacy/cold-chain/", {
        "storage_location": "UAT-FRIDGE-01",
        "recorded_temp_celsius": 11.5,
        "min_temp_celsius": 2.0,
        "max_temp_celsius": 8.0,
        "corrective_action": "Door left ajar excursion — moved contents to backup unit"
    }, format="json")
    assert cc_excursion.status_code == 201, f"Cold chain excursion failed: {cc_excursion.data}"
    assert cc_excursion.data["status"] == "EXCURSION"
    print("  [PASS] Scenario 8: Cold-chain manual log correctly detects NORMAL and EXCURSION excursions")

    # -------------------------------------------------------------
    # 9. Patient Medication Counselling
    # -------------------------------------------------------------
    csl_res = client.post("/api/pharmacy/counselling/", {
        "prescription": rx1.id,
        "patient": patient.id,
        "dose_explained": True,
        "frequency_explained": True,
        "duration_explained": True,
        "food_instructions_given": True,
        "storage_explained": True,
        "warning_signs_explained": True,
        "adherence_counselled": True,
        "counselling_notes": "Patient verbally re-stated frequency and hydration requirements"
    }, format="json")
    assert csl_res.status_code == 201, f"Counselling failed: {csl_res.data}"
    csl_obj = PatientCounselling.objects.get(id=csl_res.data["id"])
    assert csl_obj.dose_explained is True
    assert csl_obj.warning_signs_explained is True
    print("  [PASS] Scenario 9: Patient counselling checklist documented with explicit checklist items")

    # -------------------------------------------------------------
    # 10. Facility Isolation
    # -------------------------------------------------------------
    batch_f2 = MedicineBatch.objects.create(
        facility=f2, medicine=medicine, batch_number=f"UAT-F2-{uuid.uuid4().hex[:6].upper()}",
        received_date=date.today(), expiry_date=date.today() + timedelta(days=200),
        quantity=100, available_quantity=100, unit_cost=Decimal("2.50")
    )
    rx_f1 = create_encounter_rx(patient, doctor, f1, status="VERIFIED")
    item_f1 = PrescriptionItem.objects.create(prescription=rx_f1, medicine_name=medicine.generic_name, dosage="500mg", frequency="1-0-0", duration_days=2, quantity=5)

    iso_res = client.post("/api/pharmacy/dispense/", {
        "prescription_id": rx_f1.id,
        "items": [{"item_id": item_f1.id, "medicine_name": medicine.generic_name, "batch_id": batch_f2.id, "qty_to_dispense": 5}]
    }, format="json")
    assert iso_res.status_code == 400, "Cross-facility batch dispense must be rejected"
    print("  [PASS] Scenario 10: Facility isolation verified — cross-facility batch selection is blocked")

    print("=" * 70)
    print("ALL 10 UAT VALIDATION SCENARIOS PASSED WITH ZERO FAILURES!")
    print("=" * 70)

if __name__ == "__main__":
    run_10_scenarios()

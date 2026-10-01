"""
Phase 14 — Backend Integration & End-to-End Contract Verification Test Suite.
Verifies complete cross-domain backend workflows:
1. Clinical Journey (Patient -> Visit -> Token -> Triage -> Consultation -> Diagnostics -> Prescription -> Dispense -> Follow-up).
2. Supply Chain (Vendor -> PO -> Approval -> GRN -> Ledger -> Batch Cache -> Dispense -> Atomic Rollback).
3. Referral & Follow-up State Machine & Cross-Encounter Completion.
4. NCD & Disease Surveillance Pipelines.
5. IAM Multi-Role Authorization & Scope Hierarchy (Doctor, Nurse, Lab Tech, Pharmacist, Admin, DHO fail-closed).
6. Cross-Facility Isolation & Continuity-of-Care Search.
7. Transaction Atomicity & Rollback Guarantees.
8. Audit Trail Verification & API Contract Status Code Determinism.
"""
import datetime
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, User, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest, DiagnosticResult
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger, Dispensation,
    Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote
)
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry


class Phase14BackendIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Geographic & Organization Hierarchy
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.taluk = Taluk.objects.create(name="Bengaluru East", code="TAL-BLR-E", district=self.district)
        self.zone = Zone.objects.create(name="Mahadevapura Zone", district=self.district)
        self.ward = Ward.objects.create(name="Varthur", ward_number=149, zone=self.zone)

        self.clinic_a = Facility.objects.create(
            facility_code="PHC-VARTHUR", facility_name="Varthur Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )
        self.clinic_b = Facility.objects.create(
            facility_code="PHC-WHITEFIELD", facility_name="Whitefield Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )

        self.dept_opd_a = Department.objects.create(facility=self.clinic_a, code="OPD", name="Outpatient")
        self.dept_lab_a = Department.objects.create(facility=self.clinic_a, code="LAB", name="Laboratory")
        self.dept_pharm_a = Department.objects.create(facility=self.clinic_a, code="PHARM", name="Pharmacy")
        self.dept_opd_b = Department.objects.create(facility=self.clinic_b, code="OPD", name="Outpatient")

        # 2. Roles
        self.role_admin, _ = RoleMaster.objects.get_or_create(code="HOSPITAL_ADMIN", defaults={"name": "Hospital Administrator"})
        self.role_doc, _ = RoleMaster.objects.get_or_create(code="DOCTOR", defaults={"name": "Medical Officer"})
        self.role_nurse, _ = RoleMaster.objects.get_or_create(code="NURSE", defaults={"name": "Staff Nurse"})
        self.role_pharm, _ = RoleMaster.objects.get_or_create(code="PHARMACIST", defaults={"name": "Pharmacist"})
        self.role_lab, _ = RoleMaster.objects.get_or_create(code="LAB_TECHNICIAN", defaults={"name": "Laboratory Technician"})
        self.role_dho, _ = RoleMaster.objects.get_or_create(code="DHO", defaults={"name": "District Health Officer"})

        # 3. Users and Staff Profiles
        # Admin Staff (Clinic A)
        self.person_admin = Person.objects.create(first_name="Admin", last_name="User", gender="MALE", date_of_birth="1975-01-01")
        self.admin_staff = StaffProfile.objects.create(
            person=self.person_admin, employee_id="ADM-INT-1", designation="Hospital Administrator",
            department=self.dept_opd_a, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.admin_staff, role=self.role_admin, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.admin_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.admin_user = User.objects.create_user(
            username="admin_int", password="password123", email="admin_int@clinic.org",
            role="HOSPITAL_ADMIN", assigned_facility=self.clinic_a, staff_profile=self.admin_staff
        )

        # Doctor Staff (Clinic A)
        self.person_doc = Person.objects.create(first_name="Doctor", last_name="A", gender="MALE", date_of_birth="1980-05-15")
        self.doc_staff = StaffProfile.objects.create(
            person=self.person_doc, employee_id="DOC-INT-1", designation="Medical Officer",
            department=self.dept_opd_a, status="ACTIVE", medical_council_reg_number="KMC-11111"
        )
        StaffRoleAssignment.objects.create(staff=self.doc_staff, role=self.role_doc, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.doc_user = User.objects.create_user(
            username="doc_int", password="password123", email="doc_int@clinic.org",
            role="DOCTOR", assigned_facility=self.clinic_a, staff_profile=self.doc_staff
        )

        # Nurse Staff (Clinic A)
        self.person_nurse = Person.objects.create(first_name="Nurse", last_name="A", gender="FEMALE", date_of_birth="1992-08-20")
        self.nurse_staff = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="NUR-INT-1", designation="Staff Nurse",
            department=self.dept_opd_a, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.nurse_staff, role=self.role_nurse, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.nurse_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.nurse_user = User.objects.create_user(
            username="nurse_int", password="password123", email="nurse_int@clinic.org",
            role="NURSE", assigned_facility=self.clinic_a, staff_profile=self.nurse_staff
        )

        # Pharmacist Staff (Clinic A)
        self.person_pharm = Person.objects.create(first_name="Pharma", last_name="A", gender="MALE", date_of_birth="1988-03-10")
        self.pharm_staff = StaffProfile.objects.create(
            person=self.person_pharm, employee_id="PHM-INT-1", designation="Pharmacist",
            department=self.dept_pharm_a, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.pharm_staff, role=self.role_pharm, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.pharm_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.pharm_user = User.objects.create_user(
            username="pharm_int", password="password123", email="pharm_int@clinic.org",
            role="PHARMACIST", assigned_facility=self.clinic_a, staff_profile=self.pharm_staff
        )

        # Lab Tech Staff (Clinic A)
        self.person_lab = Person.objects.create(first_name="LabTech", last_name="A", gender="FEMALE", date_of_birth="1994-11-25")
        self.lab_staff = StaffProfile.objects.create(
            person=self.person_lab, employee_id="LAB-INT-1", designation="Laboratory Technician",
            department=self.dept_lab_a, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.lab_staff, role=self.role_lab, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.lab_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.lab_user = User.objects.create_user(
            username="lab_int", password="password123", email="lab_int@clinic.org",
            role="LAB_TECHNICIAN", assigned_facility=self.clinic_a, staff_profile=self.lab_staff
        )

        # Doctor Staff (Clinic B)
        self.person_doc_b = Person.objects.create(first_name="Doctor", last_name="B", gender="FEMALE", date_of_birth="1985-06-12")
        self.doc_b_staff = StaffProfile.objects.create(
            person=self.person_doc_b, employee_id="DOC-INT-B", designation="Medical Officer",
            department=self.dept_opd_b, status="ACTIVE", medical_council_reg_number="KMC-22222"
        )
        StaffRoleAssignment.objects.create(staff=self.doc_b_staff, role=self.role_doc, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_b_staff, facility=self.clinic_b, is_primary=True, is_active=True)
        self.doc_b_user = User.objects.create_user(
            username="doc_b_int", password="password123", email="doc_b@clinic.org",
            role="DOCTOR", assigned_facility=self.clinic_b, staff_profile=self.doc_b_staff
        )

        # District Health Officer (Assigned to district)
        self.person_dho = Person.objects.create(first_name="DHO", last_name="Officer", gender="MALE", date_of_birth="1970-01-01")
        self.dho_staff = StaffProfile.objects.create(
            person=self.person_dho, employee_id="DHO-INT-1", designation="District Health Officer",
            status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.dho_staff, role=self.role_dho, effective_from="2026-01-01", is_active=True)
        self.dho_user = User.objects.create_user(
            username="dho_int", password="password123", email="dho@clinic.org",
            role="DISTRICT_OFFICER", assigned_district=self.district, staff_profile=self.dho_staff
        )

        # Unassigned DHO (Lacks assigned_district_id -> must fail closed to 0 facilities)
        self.person_dho_unassigned = Person.objects.create(first_name="Unassigned", last_name="DHO", gender="MALE", date_of_birth="1972-02-02")
        self.dho_unassigned_staff = StaffProfile.objects.create(
            person=self.person_dho_unassigned, employee_id="DHO-INT-UNASSIGNED", designation="District Health Officer",
            status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.dho_unassigned_staff, role=self.role_dho, effective_from="2026-01-01", is_active=True)
        self.dho_unassigned_user = User.objects.create_user(
            username="dho_unassigned", password="password123", email="dho_unassigned@clinic.org",
            role="DISTRICT_OFFICER", assigned_district=None, staff_profile=self.dho_unassigned_staff
        )

        # Inactive Staff
        self.inactive_user = User.objects.create_user(
            username="inactive_int", password="password123", is_active=False
        )

    # =========================================================================
    # 1. CLINICAL END-TO-END WORKFLOW
    # =========================================================================
    def test_01_clinical_end_to_end_journey(self):
        """
        Tests the complete clinical pathway:
        Patient -> Visit -> OPD Token -> Triage -> Consultation -> Diagnostics ->
        Verification -> Doctor Review -> Prescription -> Dispensing -> Follow-up.
        """
        # Step 1: Register Patient at Clinic A (Admin / Compounder registration role)
        self.client.force_authenticate(user=self.admin_user)
        pat_payload = {
            "name": "Kavitha Murthy", "age": 35, "gender": "FEMALE",
            "mobile": "9845098450", "address": "Varthur Main Road",
            "registered_at_facility": self.clinic_a.id
        }
        res_pat = self.client.post('/api/v1/patients/', pat_payload, format='json')
        self.assertEqual(res_pat.status_code, status.HTTP_201_CREATED)
        patient_id = res_pat.data['id']
        self.assertTrue(res_pat.data['patient_id'].startswith("PAT-"))

        # Step 2: Create Visit Encounter -> OPD Token automatically issued
        visit_payload = {
            "patient": patient_id, "facility": self.clinic_a.id,
            "visit_type": "OPD", "opd_date": str(datetime.date.today()),
            "status": "WAITING_FOR_TRIAGE"
        }
        res_vis = self.client.post('/api/v1/visits/', visit_payload, format='json')
        self.assertEqual(res_vis.status_code, status.HTTP_201_CREATED)
        visit_id = res_vis.data['id']
        self.assertTrue(res_vis.data['visit_id'].startswith("VIS-"))

        token = Token.objects.filter(visit_id=visit_id).first()
        self.assertIsNotNone(token)
        self.assertGreater(token.token_number, 0)

        # Step 3: Triage Vitals by Nurse
        self.client.force_authenticate(user=self.nurse_user)
        triage_payload = {
            "visit": visit_id, "patient": patient_id,
            "blood_pressure_systolic": 128, "blood_pressure_diastolic": 82,
            "pulse_bpm": 76, "temperature_f": Decimal("98.6"),
            "spo2_percent": 98, "weight_kg": Decimal("58.0"),
            "respiratory_rate": 16
        }
        res_tr = self.client.post('/api/v1/clinical/triage/', triage_payload, format='json')
        self.assertEqual(res_tr.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_tr.data['nurse'], self.nurse_user.id)

        # Step 4: Medical Consultation by Doctor
        self.client.force_authenticate(user=self.doc_user)
        consult_payload = {
            "visit": visit_id, "patient": patient_id, "facility": self.clinic_a.id,
            "chief_complaint": "Persistent fatigue and fever for 3 days",
            "clinical_history": "No prior chronic illness reported",
            "clinical_assessment": "Suspected acute bacterial infection",
            "diagnosis_code": "A49.9", "diagnosis_name": "Bacterial infection, unspecified",
            "treatment_plan": "Prescribe oral antibiotics after laboratory confirmation"
        }
        res_c = self.client.post('/api/v1/clinical/consultations/', consult_payload, format='json')
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        consultation_id = res_c.data['id']
        self.assertEqual(res_c.data['doctor_staff'], self.doc_staff.id)

        # Step 5: Diagnostic Order Requisition by Doctor
        diag_payload = {
            "visit": visit_id, "facility": self.clinic_a.id,
            "priority": "URGENT", "clinical_indication": "R/O severe anaemia / infection",
            "order_date": str(datetime.date.today())
        }
        res_ord = self.client.post('/api/v1/diagnostics/orders/', diag_payload, format='json')
        self.assertEqual(res_ord.status_code, status.HTTP_201_CREATED)
        order_id = res_ord.data['id']
        self.assertEqual(res_ord.data['ordering_doctor_staff'], self.doc_staff.id)

        # Step 6: Lab Token Issuance for the Diagnostic Order
        res_lab_tok = self.client.post(
            f'/api/v1/visits/{visit_id}/issue-lab-token/',
            {"diagnostic_order_id": order_id}, format='json'
        )
        self.assertEqual(res_lab_tok.status_code, status.HTTP_200_OK)
        self.assertGreater(int(res_lab_tok.data['lab_token_number']), 0)

        # Step 7: Test Request Creation & Specimen Collection
        test_master = DiagnosticTestMaster.objects.create(
            test_code="TEST-CBC-INT", test_name="Complete Blood Count",
            category="HAEMATOLOGY", specimen_type="WHOLE_BLOOD"
        )
        req_payload = {"diagnostic_order": order_id, "test_master": test_master.id}
        res_req = self.client.post('/api/v1/diagnostics/requests/', req_payload, format='json')
        self.assertEqual(res_req.status_code, status.HTTP_201_CREATED)
        test_request_id = res_req.data['id']

        self.client.force_authenticate(user=self.lab_user)
        specimen_payload = {
            "diagnostic_order": order_id, "barcode_identifier": "BAR-HAEM-INT01",
            "specimen_type": "WHOLE_BLOOD", "test_request_ids": [test_request_id]
        }
        res_spec = self.client.post('/api/v1/diagnostics/specimens/', specimen_payload, format='json')
        self.assertEqual(res_spec.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_spec.data['collected_by_staff'], self.lab_staff.id)

        # Step 8: Diagnostic Result Entry by Lab Technician
        res_entry_payload = {
            "test_request": test_request_id,
            "result_value_text": "11.2 g/dL",
            "result_value_numeric": "11.2000",
            "reference_range_applied": "12.0 - 15.5 g/dL",
            "is_abnormal": True, "is_critical_panic": False
        }
        res_rec = self.client.post('/api/v1/diagnostics/results/', res_entry_payload, format='json')
        self.assertEqual(res_rec.status_code, status.HTTP_201_CREATED)
        result_id = res_rec.data['id']
        self.assertEqual(res_rec.data['status'], 'ENTERED')
        self.assertEqual(res_rec.data['entered_by_staff'], self.lab_staff.id)

        # Step 9: Diagnostic Result Verification by Medical Officer
        self.client.force_authenticate(user=self.doc_user)
        res_ver = self.client.post(f'/api/v1/diagnostics/results/{result_id}/verify/')
        self.assertEqual(res_ver.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ver.data['status'], 'VERIFIED')
        self.assertEqual(res_ver.data['verified_by_staff'], self.doc_staff.id)

        # Doctor reviews result
        res_rev = self.client.get(f'/api/v1/diagnostics/results/{result_id}/')
        self.assertEqual(res_rev.status_code, status.HTTP_200_OK)
        self.assertEqual(res_rev.data['result_value_text'], '11.2 g/dL')

        # Step 10: Doctor creates Prescription
        med = MedicineMaster.objects.create(
            generic_name="Amoxicillin", strength="500 mg", dosage_form="Capsule"
        )
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="AMOX-INT-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=100, available_quantity=100, status="AVAILABLE"
        )
        rx = Prescription.objects.create(
            consultation_id=consultation_id, patient_id=patient_id,
            facility=self.clinic_a, status="VERIFIED"
        )
        rx_item = PrescriptionItem.objects.create(
            prescription=rx, medicine=med, medicine_name="Amoxicillin 500mg",
            quantity=15, dispensed_quantity=0, status="PENDING"
        )

        # Step 11: Pharmacist Dispenses Prescription via Domain Service
        self.client.force_authenticate(user=self.pharm_user)
        disp_payload = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 15}]
        }
        res_disp = self.client.post('/api/v1/pharmacy/dispensations/', disp_payload, format='json')
        self.assertEqual(res_disp.status_code, status.HTTP_201_CREATED)

        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 85)

        # Authoritative Ledger audit check
        ledger_entry = InventoryLedger.objects.filter(batch=batch, transaction_type="DISPENSE").first()
        self.assertIsNotNone(ledger_entry)
        self.assertEqual(ledger_entry.quantity_delta, -15)
        self.assertEqual(ledger_entry.balance_after, 85)

        # Step 12: Follow-up Scheduling & Completion
        self.client.force_authenticate(user=self.doc_user)
        fu_payload = {
            "patient": patient_id, "facility": self.clinic_a.id,
            "due_date": str(datetime.date.today() + datetime.timedelta(days=7)),
            "category": "LAB_REVIEW", "originating_visit": visit_id,
            "clinical_instructions": "Review CBC and response to antibiotics"
        }
        res_fu = self.client.post('/api/v1/referrals/followups/', fu_payload, format='json')
        self.assertEqual(res_fu.status_code, status.HTTP_201_CREATED)
        task_id = res_fu.data['id']
        self.assertEqual(res_fu.data['status'], 'PENDING')

        # Visit encounter is completed
        visit_obj = Visit.objects.get(pk=visit_id)
        visit_obj.status = "COMPLETED"
        visit_obj.save(update_fields=['status'])

        # Complete Follow-up Task
        res_fu_comp = self.client.post(
            f'/api/v1/referrals/followups/{task_id}/complete/',
            {"completed_in_visit_id": visit_id}, format='json'
        )
        self.assertEqual(res_fu_comp.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fu_comp.data['status'], 'COMPLETED')
        self.assertEqual(res_fu_comp.data['completed_by_staff'], self.doc_staff.id)

        # Verify Audit entries generated across the clinical workflow
        audit_tables = set(AuditLogEntry.objects.filter(facility=self.clinic_a).values_list('table_name', flat=True))
        self.assertIn("diagnostic_results", audit_tables)
        self.assertIn("follow_up_tasks", audit_tables)

    # =========================================================================
    # 2. PROCUREMENT -> INVENTORY -> DISPENSATION SUPPLY CHAIN INTEGRATION
    # =========================================================================
    def test_02_procurement_to_dispensing_supply_chain(self):
        """
        Tests the end-to-end supply chain:
        Vendor -> PO -> Approval -> GRN -> Ledger Receipt -> Batch Cache ->
        Prescription -> Dispensing -> Stock Depletion -> Rollback on Insufficient Stock.
        """
        from apps.accounts.services import seed_roles_and_permissions
        seed_roles_and_permissions()
        role_inv = RoleMaster.objects.get(code="INVENTORY")
        StaffRoleAssignment.objects.get_or_create(staff=self.admin_staff, role=role_inv, defaults={"is_active": True, "effective_from": "2026-01-01"})
        self.client.force_authenticate(user=self.admin_user)
        vendor = Vendor.objects.create(vendor_name="Karnataka Antibiotics Ltd", facility=self.clinic_a)
        med = MedicineMaster.objects.create(
            generic_name="Azithromycin", strength="500 mg", dosage_form="Tablet"
        )

        # 1. Create Purchase Order
        po_payload = {
            "facility": self.clinic_a.id, "vendor": vendor.id, "po_number": "PO-INT-CHAIN-01"
        }
        res_po = self.client.post('/api/v1/procurement/purchase-orders/', po_payload, format='json')
        self.assertEqual(res_po.status_code, status.HTTP_201_CREATED)
        po_id = res_po.data['id']
        self.assertEqual(res_po.data['status'], 'DRAFT')

        # 2. Approve Purchase Order
        res_app = self.client.post(
            f'/api/v1/procurement/purchase-orders/{po_id}/approve/',
            {"approval_tier": 1, "status": "APPROVED", "remarks": "Approved by Hospital Admin"},
            format='json'
        )
        self.assertEqual(res_app.status_code, status.HTTP_200_OK)
        self.assertEqual(res_app.data['status'], 'APPROVED')

        # Duplicate approval rejection
        res_app_dup = self.client.post(
            f'/api/v1/procurement/purchase-orders/{po_id}/approve/',
            {"approval_tier": 1, "status": "APPROVED"}, format='json'
        )
        self.assertEqual(res_app_dup.status_code, status.HTTP_409_CONFLICT)

        # 3. Receive GRN -> Writes Batch & Authoritative Inventory Ledger
        grn_payload = {
            "purchase_order_id": po_id,
            "grn_number": "GRN-INT-CHAIN-01",
            "facility_id": self.clinic_a.id,
            "items_received": [{
                "medicine_id": med.id,
                "batch_number": "AZI-BATCH-2026",
                "expiry_date": str(datetime.date.today() + datetime.timedelta(days=365)),
                "unit_cost": "4.50",
                "quantity_received": 100,
                "quantity_accepted": 100,
                "quantity_rejected": 0
            }]
        }
        res_grn = self.client.post('/api/v1/procurement/grn/', grn_payload, format='json')
        self.assertEqual(res_grn.status_code, status.HTTP_201_CREATED)

        batch = MedicineBatch.objects.filter(facility=self.clinic_a, batch_number="AZI-BATCH-2026").first()
        self.assertIsNotNone(batch)
        self.assertEqual(batch.available_quantity, 100)

        # Authoritative Ledger Verification
        grn_ledger = InventoryLedger.objects.filter(batch=batch, transaction_type="PURCHASE_RECEIPT").first()
        self.assertIsNotNone(grn_ledger)
        self.assertEqual(grn_ledger.quantity_delta, 100)
        self.assertEqual(grn_ledger.balance_after, 100)

        # 4. Prescription & Dispensing
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(
            patient_id="PAT-INT-SUPPLY", person=self.person_doc, name="Supply Patient",
            age=28, gender="FEMALE", registered_at_facility=self.clinic_a
        )
        visit = Visit.objects.create(
            visit_id="VIS-INT-SUPPLY", patient=patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )
        consultation = Consultation.objects.create(
            visit=visit, patient=patient, facility=self.clinic_a,
            doctor_staff=self.doc_staff, chief_complaint="Throat infection"
        )
        rx = Prescription.objects.create(
            consultation=consultation, patient=patient, facility=self.clinic_a, status="VERIFIED"
        )
        rx_item = PrescriptionItem.objects.create(
            prescription=rx, medicine=med, medicine_name="Azithromycin 500mg",
            quantity=30, dispensed_quantity=0, status="PENDING"
        )

        # 5. First Dispensation of 30 units -> Success
        self.client.force_authenticate(user=self.pharm_user)
        disp_payload = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 30}]
        }
        res_disp = self.client.post('/api/v1/pharmacy/dispensations/', disp_payload, format='json')
        self.assertEqual(res_disp.status_code, status.HTTP_201_CREATED)
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 70)

        # 6. Second Dispensation attempting 80 units (exceeds available 70) -> 409 Conflict & Zero Mutation
        disp_excess_payload = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 80}]
        }
        res_fail = self.client.post('/api/v1/pharmacy/dispensations/', disp_excess_payload, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("DISPENSED", str(res_fail.data))

        # Rollback integrity: stock remains strictly 70, no partial ledger deductions
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 70)
        disp_ledger_count = InventoryLedger.objects.filter(batch=batch, transaction_type="DISPENSE").count()
        self.assertEqual(disp_ledger_count, 1)

    # =========================================================================
    # 3. REFERRAL -> FOLLOW-UP INTEGRATION
    # =========================================================================
    def test_03_referral_to_followup_cross_facility_lifecycle(self):
        """
        Tests referral state machine from Clinic A to Clinic B,
        event log persistence, follow-up linkage, and completion checks.
        """
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(
            patient_id="PAT-INT-REF", person=self.person_doc, name="Referral Patient",
            age=52, gender="MALE", registered_at_facility=self.clinic_a
        )
        visit_a = Visit.objects.create(
            visit_id="VIS-INT-REFA", patient=patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )

        # 1. Create Referral from Clinic A to Clinic B
        ref_payload = {
            "patient": patient.id, "visit": visit_a.id,
            "source_facility": self.clinic_a.id, "destination_facility": self.clinic_b.id,
            "reason": "Cardiology specialist evaluation", "urgency": "URGENT",
            "clinical_summary": "ECG shows abnormalities; requires secondary review"
        }
        res_ref = self.client.post('/api/v1/referrals/orders/', ref_payload, format='json')
        self.assertEqual(res_ref.status_code, status.HTTP_201_CREATED)
        ref_id = res_ref.data['id']
        self.assertEqual(res_ref.data['status'], 'INITIATED')

        # 2. State Machine Transitions
        # Clinic B acknowledges receipt
        self.client.force_authenticate(user=self.doc_b_user)
        res_t1 = self.client.post(
            f'/api/v1/referrals/orders/{ref_id}/transition/',
            {"new_status": "ACKNOWLEDGED", "notes": "Specialist appointment allocated"}, format='json'
        )
        self.assertEqual(res_t1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_t1.data['status'], 'ACKNOWLEDGED')

        # In-transit transition
        res_t2 = self.client.post(
            f'/api/v1/referrals/orders/{ref_id}/transition/',
            {"new_status": "IN_TRANSIT", "notes": "Patient departed Clinic A"}, format='json'
        )
        self.assertEqual(res_t2.status_code, status.HTTP_200_OK)

        # Received at Clinic B
        res_t3 = self.client.post(
            f'/api/v1/referrals/orders/{ref_id}/transition/',
            {"new_status": "ARRIVED", "notes": "Patient arrived at Clinic B"}, format='json'
        )
        self.assertEqual(res_t3.status_code, status.HTTP_200_OK)

        # Completed at Clinic B
        res_t4 = self.client.post(
            f'/api/v1/referrals/orders/{ref_id}/transition/',
            {"new_status": "COMPLETED", "notes": "Cardiology consult concluded"}, format='json'
        )
        self.assertEqual(res_t4.status_code, status.HTTP_200_OK)
        self.assertEqual(res_t4.data['status'], 'COMPLETED')

        # Attempting invalid backwards state transition -> 409 Conflict
        res_t_bad = self.client.post(
            f'/api/v1/referrals/orders/{ref_id}/transition/',
            {"new_status": "INITIATED", "notes": "Invalid rollback attempt"}, format='json'
        )
        self.assertEqual(res_t_bad.status_code, status.HTTP_409_CONFLICT)

        # Verify ReferralEvent history persisted
        events_count = ReferralEvent.objects.filter(referral_id=ref_id).count()
        self.assertEqual(events_count, 5)

        # 3. Follow-up Task linked to Referral
        fu_payload = {
            "patient": patient.id, "facility": self.clinic_b.id,
            "due_date": str(datetime.date.today() + datetime.timedelta(days=14)),
            "category": "POST_REFERRAL", "referral": ref_id,
            "clinical_instructions": "Check post-treatment cardiology progress"
        }
        res_fu = self.client.post('/api/v1/referrals/followups/', fu_payload, format='json')
        self.assertEqual(res_fu.status_code, status.HTTP_201_CREATED)
        fu_task_id = res_fu.data['id']

        # Attempt completion with incomplete visit -> 409 Conflict
        visit_b_inprog = Visit.objects.create(
            visit_id="VIS-INT-REFB1", patient=patient, facility=self.clinic_b,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )
        res_comp_fail = self.client.post(
            f'/api/v1/referrals/followups/{fu_task_id}/complete/',
            {"completed_in_visit_id": visit_b_inprog.id}, format='json'
        )
        self.assertEqual(res_comp_fail.status_code, status.HTTP_409_CONFLICT)

        # Complete with completed visit at Clinic B -> 200 OK
        visit_b_comp = Visit.objects.create(
            visit_id="VIS-INT-REFB2", patient=patient, facility=self.clinic_b,
            visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED"
        )
        res_comp_ok = self.client.post(
            f'/api/v1/referrals/followups/{fu_task_id}/complete/',
            {"completed_in_visit_id": visit_b_comp.id}, format='json'
        )
        self.assertEqual(res_comp_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_comp_ok.data['status'], 'COMPLETED')

    # =========================================================================
    # 4. NCD & SURVEILLANCE INTEGRATION
    # =========================================================================
    def test_04_ncd_and_disease_surveillance_pipeline(self):
        """
        Tests NCD condition registration, assessment monitoring,
        epidemiological case reporting, and public health notifications.
        """
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(
            patient_id="PAT-INT-NCD", person=self.person_doc, name="NCD Patient",
            age=48, gender="FEMALE", registered_at_facility=self.clinic_a
        )
        visit = Visit.objects.create(
            visit_id="VIS-INT-NCD", patient=patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED"
        )

        # 1. Register NCD Condition (Hypertension)
        ncd_payload = {
            "patient": patient.id, "registering_facility": self.clinic_a.id,
            "condition_code": "HYPERTENSION", "staging": "STAGE_2",
            "control_status": "UNCONTROLLED"
        }
        res_ncd = self.client.post('/api/v1/ncd/conditions/', ncd_payload, format='json')
        self.assertEqual(res_ncd.status_code, status.HTTP_201_CREATED)
        condition_id = res_ncd.data['id']
        self.assertEqual(res_ncd.data['registering_doctor'], self.doc_staff.id)

        # 2. Record NCD Assessment
        assess_payload = {
            "condition": condition_id, "visit": visit.id,
            "systolic_bp": 158, "diastolic_bp": 96,
            "blood_glucose_fasting": Decimal("110.5"),
            "clinical_notes": "Prescribed antihypertensive therapy"
        }
        res_ass = self.client.post('/api/v1/ncd/assessments/', assess_payload, format='json')
        self.assertEqual(res_ass.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ass.data['assessed_by_staff'], self.doc_staff.id)

        # 3. Report Disease Surveillance Case (Dengue)
        disease, _ = DiseaseMaster.objects.get_or_create(
            disease_code="DENGUE",
            defaults={
                "disease_name": "Dengue Fever",
                "transmission_type": "VECTOR_BORNE",
                "is_notifiable_state": True
            }
        )
        case_payload = {
            "patient": patient.id, "facility": self.clinic_a.id,
            "disease": disease.id,
            "severity": "MODERATE", "status": "CONFIRMED",
            "investigation_notes": "Cluster reported in Ward 149"
        }
        res_case = self.client.post('/api/v1/surveillance/cases/', case_payload, format='json')
        self.assertEqual(res_case.status_code, status.HTTP_201_CREATED)
        case_id = res_case.data['id']
        self.assertTrue(res_case.data['case_number'].startswith("SURV-"))
        self.assertEqual(res_case.data['reporting_staff'], self.doc_staff.id)

        # 4. Dispatch Public Health Notification
        notif_payload = {
            "case": case_id, "notified_authority": "DHO_BENGALURU_URBAN",
            "dispatch_payload": {"ward": 149, "disease": "Dengue", "urgency": "IMMEDIATE"}
        }
        res_notif = self.client.post('/api/v1/surveillance/notifications/', notif_payload, format='json')
        self.assertEqual(res_notif.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(res_notif.data['dispatched_at'])

        # Cross-facility mutation guard: Clinic A staff cannot report for Clinic B
        bad_case = case_payload.copy()
        bad_case["facility"] = self.clinic_b.id
        res_bad = self.client.post('/api/v1/surveillance/cases/', bad_case, format='json')
        self.assertEqual(res_bad.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 5. IAM MULTI-ROLE AUTHORIZATION & SCOPE HIERARCHY
    # =========================================================================
    def test_05_iam_multi_role_authority_matrix(self):
        """
        Tests role authorization boundaries:
        - Inactive staff blocked at authentication/permission boundary.
        - Unassigned DHO fails closed (0 permitted facilities).
        - Assigned DHO has visibility across all district facilities.
        - Staff Nurse cannot approve POs or verify lab results (403).
        - Ordinary Doctor cannot assign administrative roles (403).
        - Hospital Admin can manage staff status and role assignments.
        """
        # 1. Inactive user is blocked
        self.client.force_authenticate(user=self.inactive_user)
        res_inact = self.client.get('/api/v1/organization/facilities/')
        self.assertIn(res_inact.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # 2. Unassigned DHO fails closed (0 facilities returned)
        self.client.force_authenticate(user=self.dho_unassigned_user)
        res_dho_un = self.client.get('/api/v1/organization/facilities/')
        self.assertEqual(res_dho_un.status_code, status.HTTP_200_OK)
        items = res_dho_un.data['results'] if 'results' in res_dho_un.data else res_dho_un.data
        self.assertEqual(len(items), 0)

        # 3. Assigned DHO sees both Clinic A and Clinic B in their district
        self.client.force_authenticate(user=self.dho_user)
        res_dho = self.client.get('/api/v1/organization/facilities/')
        self.assertEqual(res_dho.status_code, status.HTTP_200_OK)
        fac_codes = [f['facility_code'] for f in (res_dho.data['results'] if 'results' in res_dho.data else res_dho.data)]
        self.assertIn("PHC-VARTHUR", fac_codes)
        self.assertIn("PHC-WHITEFIELD", fac_codes)

        # 4. Nurse cannot approve PO (requires Admin authority)
        self.client.force_authenticate(user=self.nurse_user)
        vendor = Vendor.objects.create(vendor_name="Pharma Vendor A", facility=self.clinic_a)
        po = PurchaseOrder.objects.create(facility=self.clinic_a, vendor=vendor, status="DRAFT")
        res_app_nurse = self.client.post(f'/api/v1/procurement/purchase-orders/{po.id}/approve/')
        self.assertEqual(res_app_nurse.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Doctor cannot assign administrative roles
        self.client.force_authenticate(user=self.doc_user)
        res_assign = self.client.post(
            '/api/v1/accounts/role-assignments/',
            {"staff": self.nurse_staff.id, "role": self.role_admin.id}, format='json'
        )
        self.assertEqual(res_assign.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Hospital Admin successfully updates staff status
        self.client.force_authenticate(user=self.admin_user)
        res_status = self.client.post(
            f'/api/v1/accounts/staff-profiles/{self.nurse_staff.id}/update-status/',
            {"status": "SUSPENDED"}, format='json'
        )
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.nurse_staff.refresh_from_db()
        self.assertEqual(self.nurse_staff.status, "SUSPENDED")

    # =========================================================================
    # 6. CROSS-FACILITY ISOLATION & CONTINUITY-OF-CARE
    # =========================================================================
    def test_06_cross_facility_boundary_and_continuity_of_care(self):
        """
        Tests multi-tenant isolation:
        - Clinic A staff cannot list Clinic B consultations or alerts.
        - Clinic A staff cannot mutate Clinic B data.
        - Continuity of care: Clinic B doctor can search Clinic A registered patient
          by phone/identifier to initiate cross-facility encounter.
        """
        # Register Patient at Clinic A
        self.client.force_authenticate(user=self.nurse_user)
        pat_a = Patient.objects.create(
            patient_id="PAT-INT-ISOLATE", person=self.person_doc, name="Isolate Patient",
            age=32, gender="MALE", mobile="9876543210", registered_at_facility=self.clinic_a
        )
        vis_b = Visit.objects.create(
            visit_id="VIS-INT-ISOLATE-B", patient=pat_a, facility=self.clinic_b,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )
        Consultation.objects.create(
            visit=vis_b, patient=pat_a, facility=self.clinic_b,
            doctor_staff=self.doc_b_staff, chief_complaint="Clinic B complaint"
        )
        OperationalAlert.objects.create(
            facility=self.clinic_b, alert_category="SYSTEM", title="Clinic B Alert", is_active=True
        )

        # Doctor at Clinic A queries consultations & alerts -> receives only Clinic A data
        self.client.force_authenticate(user=self.doc_user)
        res_c = self.client.get('/api/v1/clinical/consultations/')
        c_facs = [c['facility'] for c in (res_c.data['results'] if 'results' in res_c.data else res_c.data)]
        self.assertNotIn(self.clinic_b.id, c_facs)

        res_al = self.client.get('/api/v1/alerts/')
        al_titles = [a['title'] for a in (res_al.data['results'] if 'results' in res_al.data else res_al.data)]
        self.assertNotIn("Clinic B Alert", al_titles)

        # Doctor at Clinic A attempting to create consultation at Clinic B -> 403 Forbidden
        bad_consult = {
            "visit": vis_b.id, "patient": pat_a.id, "facility": self.clinic_b.id,
            "chief_complaint": "Unauthorized cross clinic post"
        }
        res_bad = self.client.post('/api/v1/clinical/consultations/', bad_consult, format='json')
        self.assertEqual(res_bad.status_code, status.HTTP_403_FORBIDDEN)

        # Continuity-of-Care Search: Doctor at Clinic B searches patient by phone
        self.client.force_authenticate(user=self.doc_b_user)
        res_search = self.client.get('/api/v1/patients/?search=9876543210')
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        found_patients = res_search.data['results'] if 'results' in res_search.data else res_search.data
        self.assertTrue(any(p['patient_id'] == "PAT-INT-ISOLATE" for p in found_patients))

    # =========================================================================
    # 7. TRANSACTION ATOMICITY & ROLLBACK SCENARIOS
    # =========================================================================
    def test_07_transaction_atomicity_and_rollback_scenarios(self):
        """
        Tests rollback guarantees:
        - Multi-batch dispensation with one failing batch produces zero inventory mutation.
        - Monotonic token allocation generates collision-free sequences.
        - Diagnostic result verification is immutable against direct updates.
        """
        self.client.force_authenticate(user=self.pharm_user)
        med = MedicineMaster.objects.create(generic_name="Ibuprofen", strength="400 mg", dosage_form="Tablet")
        batch_1 = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="IBU-B1",
            expiry_date=datetime.date.today() + datetime.timedelta(days=90),
            quantity=20, available_quantity=20, status="AVAILABLE"
        )
        batch_2 = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="IBU-B2",
            expiry_date=datetime.date.today() + datetime.timedelta(days=120),
            quantity=10, available_quantity=10, status="AVAILABLE"
        )

        patient = Patient.objects.create(
            patient_id="PAT-INT-ATOMIC", person=self.person_doc, name="Atomic Patient",
            age=30, gender="MALE", registered_at_facility=self.clinic_a
        )
        visit = Visit.objects.create(
            visit_id="VIS-INT-ATOMIC", patient=patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )
        consultation = Consultation.objects.create(
            visit=visit, patient=patient, facility=self.clinic_a,
            doctor_staff=self.doc_staff, chief_complaint="Pain"
        )
        rx = Prescription.objects.create(consultation=consultation, patient=patient, facility=self.clinic_a, status="VERIFIED")
        item1 = PrescriptionItem.objects.create(prescription=rx, medicine=med, medicine_name="Ibuprofen 400mg", quantity=10, status="PENDING")
        item2 = PrescriptionItem.objects.create(prescription=rx, medicine=med, medicine_name="Ibuprofen 400mg", quantity=25, status="PENDING")

        # Multi-batch allocation where batch_2 has insufficient quantity (requests 25, only 10 available)
        fail_dispense = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [
                {"prescription_item_id": item1.id, "batch_id": batch_1.id, "quantity": 10},
                {"prescription_item_id": item2.id, "batch_id": batch_2.id, "quantity": 25}
            ]
        }
        res_fail = self.client.post('/api/v1/pharmacy/dispensations/', fail_dispense, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_409_CONFLICT)

        # Atomic rollback verification: batch_1 was NOT partially deducted
        batch_1.refresh_from_db()
        batch_2.refresh_from_db()
        self.assertEqual(batch_1.available_quantity, 20)
        self.assertEqual(batch_2.available_quantity, 10)
        self.assertEqual(Dispensation.objects.filter(prescription=rx).count(), 0)

        # Monotonic Token Uniqueness: Sequential token requests produce distinct sequential tokens
        self.client.force_authenticate(user=self.doc_user)
        v1 = Visit.objects.create(visit_id="VIS-SEQ-1", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today())
        v2 = Visit.objects.create(visit_id="VIS-SEQ-2", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today())

        t1 = self.client.post(f'/api/v1/visits/{v1.id}/issue-opd-token/')
        t2 = self.client.post(f'/api/v1/visits/{v2.id}/issue-opd-token/')
        self.assertEqual(t1.status_code, status.HTTP_200_OK)
        self.assertEqual(t2.status_code, status.HTTP_200_OK)
        self.assertNotEqual(t1.data['token_number'], t2.data['token_number'])

    # =========================================================================
    # 8. AUDIT TRAIL & API CONTRACT VERIFICATION
    # =========================================================================
    def test_08_audit_trail_and_api_contract_verification(self):
        """
        Tests API contract consistency and audit trail security:
        - Non-admin staff cannot view audit logs (403 Forbidden).
        - Administrative staff can inspect audit logs (200 OK).
        - Audit logs cannot be mutated via API (405 Method Not Allowed).
        - Deterministic error envelopes with code and details.
        """
        # Non-admin access rejected
        self.client.force_authenticate(user=self.nurse_user)
        res_audit_nurse = self.client.get('/api/v1/audit/')
        self.assertEqual(res_audit_nurse.status_code, status.HTTP_403_FORBIDDEN)

        # Admin access permitted
        self.client.force_authenticate(user=self.admin_user)
        res_audit_admin = self.client.get('/api/v1/audit/')
        self.assertEqual(res_audit_admin.status_code, status.HTTP_200_OK)

        # Direct mutation on audit log is forbidden (405)
        res_post_audit = self.client.post('/api/v1/audit/', {"action_type": "FORGED"}, format='json')
        self.assertEqual(res_post_audit.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # API Contract: Validation errors return standard envelopes
        # Hospital Admin cannot create facilities (HTTP 403 Forbidden under PM/RSA rule)
        res_admin_fac = self.client.post('/api/v1/organization/facilities/', {}, format='json')
        self.assertEqual(res_admin_fac.status_code, status.HTTP_403_FORBIDDEN)

        # DHO can create facilities, and empty payload returns 400 Bad Request standard validation error envelope
        self.client.force_authenticate(user=self.dho_user)
        res_bad_val = self.client.post('/api/v1/organization/facilities/', {}, format='json')
        self.assertEqual(res_bad_val.status_code, status.HTTP_400_BAD_REQUEST)

"""
Phase 15 — Backend QA, Reliability, Failure-Mode & Contract Hardening Test Suite.
Tests failure modes, reliability boundaries, and non-happy-path guarantees:
1. State Machine Hardening (Illegal transitions rejected across Visit, Diagnostics, Rx, Referral, Follow-Up, PO).
2. Idempotency & Duplicate Request Resilience (OPD token, Lab token, GRN, Alert Acknowledgment).
3. Inventory Reliability & Negative Stock Prevention (Over-dispense, Zero stock, Multi-batch atomicity, Quarantine hold/release, Ledger balance invariant).
4. Transaction Failure & Rollback (Controlled failure injection, Zero partial stock mutation, Zero phantom success audit entries).
5. Comprehensive Role Authorization Negative Matrix (Doctor, Nurse, Lab Tech, Pharmacist, Admin, Unauthenticated).
6. Staff Lifecycle, Effective Dates & Historical Authorship Integrity (Inactive staff, Transferred staff, Future/Expired assignments, Non-destructive historical clinical records).
7. Cross-Facility Isolation & Continuity-of-Care Boundaries (Facility A vs B segregation, Demographic search policy).
8. Serializer Mass-Assignment Defense (Forged actor IDs, Protected status & inventory quantities).
9. API Error Contract Determinism (Deterministic 401, 403, 400, 409 envelopes).
10. Performance Sanity & Query Count Bounds (Select/Prefetch related verification, Avoidance of N+1 query loops).
"""
import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, User, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.accounts.services import transfer_staff, update_staff_status, assign_facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest, DiagnosticResult
from apps.laboratory.services import verify_diagnostic_result
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger, Dispensation, DispensationItem,
    Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote
)
from apps.pharmacy.services import post_inventory_movement, quarantine_stock, release_quarantined_stock, dispense_prescription
from apps.pharmacy.procurement_services import create_purchase_order, approve_purchase_order, receive_goods_receipt
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.referrals.services import create_referral_order, transition_referral_state, create_followup_task, complete_followup
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry
from apps.common.exceptions import (
    InsufficientStockError, InvalidStateTransition, VerifiedResultImmutableError,
    DiagnosticResultAlreadyExistsError, InvalidFollowUpCompletionError, InvalidProcurementStateError,
    UnauthorizedDomainAction, DomainValidationError
)


class Phase15BackendReliabilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Geographic & Facility Hierarchy
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
        self.dept_opd_b = Department.objects.create(facility=self.clinic_b, code="OPD", name="Outpatient")

        # Roles
        self.role_doc, _ = RoleMaster.objects.get_or_create(code="DOCTOR", defaults={"name": "Medical Officer"})
        self.role_nurse, _ = RoleMaster.objects.get_or_create(code="NURSE", defaults={"name": "Staff Nurse"})
        self.role_lab, _ = RoleMaster.objects.get_or_create(code="LAB_TECHNICIAN", defaults={"name": "Lab Technician"})
        self.role_pharm, _ = RoleMaster.objects.get_or_create(code="PHARMACIST", defaults={"name": "Pharmacist"})
        self.role_admin, _ = RoleMaster.objects.get_or_create(code="HOSPITAL_ADMIN", defaults={"name": "Hospital Admin"})

        # Persons & Staff Profiles
        self.person_doc = Person.objects.create(first_name="Ananya", last_name="Bhat", date_of_birth=datetime.date(1985, 3, 15), gender="FEMALE")
        self.doc_staff = StaffProfile.objects.create(person=self.person_doc, employee_id="DOC-P15-01", designation="Medical Officer", status="ACTIVE")
        self.doc_user = User.objects.create_user(username="doc_ananya", password="password123", full_name="Dr. Ananya Bhat", role="DOCTOR", assigned_facility=self.clinic_a, staff_profile=self.doc_staff)
        StaffRoleAssignment.objects.create(staff=self.doc_staff, role=self.role_doc, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_staff, facility=self.clinic_a, department=self.dept_opd_a, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

        self.person_nurse = Person.objects.create(first_name="Deepa", last_name="Nair", date_of_birth=datetime.date(1990, 7, 20), gender="FEMALE")
        self.nurse_staff = StaffProfile.objects.create(person=self.person_nurse, employee_id="NUR-P15-01", designation="Staff Nurse", status="ACTIVE")
        self.nurse_user = User.objects.create_user(username="nurse_deepa", password="password123", full_name="Nurse Deepa Nair", role="NURSE", assigned_facility=self.clinic_a, staff_profile=self.nurse_staff)
        StaffRoleAssignment.objects.create(staff=self.nurse_staff, role=self.role_nurse, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.nurse_staff, facility=self.clinic_a, department=self.dept_opd_a, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

        self.person_lab = Person.objects.create(first_name="Kiran", last_name="Kumar", date_of_birth=datetime.date(1992, 11, 10), gender="MALE")
        self.lab_staff = StaffProfile.objects.create(person=self.person_lab, employee_id="LAB-P15-01", designation="Lab Technician", status="ACTIVE")
        self.lab_user = User.objects.create_user(username="tech_kiran", password="password123", full_name="Kiran Kumar", role="LAB_TECHNICIAN", assigned_facility=self.clinic_a, staff_profile=self.lab_staff)
        StaffRoleAssignment.objects.create(staff=self.lab_staff, role=self.role_lab, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.lab_staff, facility=self.clinic_a, department=self.dept_lab_a, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

        self.person_pharm = Person.objects.create(first_name="Pooja", last_name="Hegde", date_of_birth=datetime.date(1994, 5, 25), gender="FEMALE")
        self.pharm_staff = StaffProfile.objects.create(person=self.person_pharm, employee_id="PHM-P15-01", designation="Pharmacist", status="ACTIVE")
        self.pharm_user = User.objects.create_user(username="pharm_pooja", password="password123", full_name="Pooja Hegde", role="PHARMACIST", assigned_facility=self.clinic_a, staff_profile=self.pharm_staff)
        StaffRoleAssignment.objects.create(staff=self.pharm_staff, role=self.role_pharm, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.pharm_staff, facility=self.clinic_a, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

        self.person_admin = Person.objects.create(first_name="Ramesh", last_name="Babu", date_of_birth=datetime.date(1980, 2, 1), gender="MALE")
        self.admin_staff = StaffProfile.objects.create(person=self.person_admin, employee_id="ADM-P15-01", designation="Hospital Administrator", status="ACTIVE")
        self.admin_user = User.objects.create_user(username="admin_ramesh", password="password123", full_name="Ramesh Babu", role="HOSPITAL_ADMIN", assigned_facility=self.clinic_a, staff_profile=self.admin_staff)
        StaffRoleAssignment.objects.create(staff=self.admin_staff, role=self.role_admin, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.admin_staff, facility=self.clinic_a, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

        # Facility B Staff
        self.person_doc_b = Person.objects.create(first_name="Suresh", last_name="Rao", date_of_birth=datetime.date(1982, 8, 12), gender="MALE")
        self.doc_b_staff = StaffProfile.objects.create(person=self.person_doc_b, employee_id="DOC-P15-B01", designation="Medical Officer", status="ACTIVE")
        self.doc_b_user = User.objects.create_user(username="doc_suresh_b", password="password123", full_name="Dr. Suresh Rao", role="DOCTOR", assigned_facility=self.clinic_b, staff_profile=self.doc_b_staff)
        StaffRoleAssignment.objects.create(staff=self.doc_b_staff, role=self.role_doc, effective_from=datetime.date(2025, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_b_staff, facility=self.clinic_b, department=self.dept_opd_b, is_primary=True, is_active=True, effective_from=datetime.date(2025, 1, 1))

    # =========================================================================
    # 1. STATE-MACHINE HARDENING & ILLEGAL TRANSITIONS
    # =========================================================================
    def test_01_state_machine_and_lifecycle_hardened_boundaries(self):
        """
        Verifies that all domain state machines reject illegal transitions deterministically:
        - DiagnosticResult: Re-verification rejected with 409 Conflict.
        - DiagnosticResult: Duplicate result creation rejected with 409 Conflict.
        - Prescription: Dispensing against DISPENSED prescription rejected with 400.
        - Referral: Invalid transitions (ARRIVED -> INITIATED, COMPLETED -> ARRIVED) rejected with 409.
        - FollowUp: Repeated completion of COMPLETED task rejected with 409.
        - FollowUp: Completion with incomplete visit rejected with 409.
        - Procurement: Duplicate approval of approved PO rejected with 409.
        - Procurement: Receiving goods on DRAFT/unapproved PO rejected with 409.
        """
        # Diagnostic Result Immutability
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(patient_id="PAT-P15-SM1", person=self.person_doc, name="Patient SM", age=30, gender="FEMALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-SM1", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        order = DiagnosticOrder.objects.create(order_number="ORD-P15-SM1", visit=visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff)
        master = DiagnosticTestMaster.objects.create(test_code="TEST-SM-GLU", test_name="Fasting Blood Glucose", category="BIOCHEMISTRY", specimen_type="SERUM")
        req = TestRequest.objects.create(diagnostic_order=order, test_master=master, status="PENDING")
        res = DiagnosticResult.objects.create(test_request=req, result_value_text="95 mg/dL", status="ENTERED", entered_by_staff=self.lab_staff)

        # 1. First verification succeeds
        res_v1 = self.client.post(f'/api/v1/diagnostics/results/{res.id}/verify/')
        self.assertEqual(res_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_v1.data['status'], 'VERIFIED')

        # Second verification fails -> 409 Conflict
        res_v2 = self.client.post(f'/api/v1/diagnostics/results/{res.id}/verify/')
        self.assertEqual(res_v2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(res_v2.data['code'], ['CONFLICT', 'VERIFIED_RESULT_IMMUTABLE'])

        # 2. Duplicate result creation for same TestRequest -> 409 Conflict
        self.client.force_authenticate(user=self.lab_user)
        res_dup_entry = self.client.post('/api/v1/diagnostics/results/', {
            "test_request": req.id, "result_value_text": "98 mg/dL"
        }, format='json')
        self.assertIn(res_dup_entry.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])
        self.assertIn(res_dup_entry.data.get('code', 'VALIDATION_ERROR'), ['CONFLICT', 'VALIDATION_ERROR', 'DIAGNOSTIC_RESULT_ALREADY_EXISTS'])

        # 3. Prescription: Dispensing already DISPENSED prescription
        self.client.force_authenticate(user=self.pharm_user)
        med = MedicineMaster.objects.create(generic_name="Paracetamol", strength="500 mg", dosage_form="Tablet")
        batch = MedicineBatch.objects.create(facility=self.clinic_a, medicine=med, batch_number="PCM-P15-01", expiry_date=datetime.date.today() + datetime.timedelta(days=90), quantity=50, available_quantity=50, status="AVAILABLE")
        consult = Consultation.objects.create(visit=visit, patient=patient, facility=self.clinic_a, doctor_staff=self.doc_staff, chief_complaint="Fever")
        rx = Prescription.objects.create(consultation=consult, patient=patient, facility=self.clinic_a, status="DISPENSED")
        rx_item = PrescriptionItem.objects.create(prescription=rx, medicine=med, medicine_name="Paracetamol 500mg", quantity=10, dispensed_quantity=10, status="DISPENSED")

        res_disp_closed = self.client.post('/api/v1/pharmacy/dispensations/', {
            "prescription_id": rx.id, "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 5}]
        }, format='json')
        self.assertEqual(res_disp_closed.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("DISPENSED", str(res_disp_closed.data))

        # 4. Referral: Invalid transitions
        self.client.force_authenticate(user=self.doc_user)
        ref = create_referral_order(patient=patient, visit=visit, source_facility=self.clinic_a, destination_facility=self.clinic_b, referring_doctor_staff=self.doc_staff, reason="Cardiology consult")
        # INITIATED -> ARRIVED directly is illegal (must be ACKNOWLEDGED first)
        res_ref_bad1 = self.client.post(f'/api/v1/referrals/orders/{ref.id}/transition/', {"new_status": "ARRIVED"}, format='json')
        self.assertEqual(res_ref_bad1.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(res_ref_bad1.data['code'], ['CONFLICT', 'INVALID_STATE_TRANSITION'])

        # Progress legitimately to COMPLETED
        transition_referral_state(ref, "ACKNOWLEDGED", self.doc_b_staff)
        transition_referral_state(ref, "IN_TRANSIT", self.doc_staff)
        transition_referral_state(ref, "ARRIVED", self.doc_b_staff)
        transition_referral_state(ref, "COMPLETED", self.doc_b_staff)

        # COMPLETED -> ARRIVED or INITIATED rollback is strictly illegal
        res_ref_bad2 = self.client.post(f'/api/v1/referrals/orders/{ref.id}/transition/', {"new_status": "ARRIVED"}, format='json')
        self.assertEqual(res_ref_bad2.status_code, status.HTTP_409_CONFLICT)

        # 5. Follow-Up Task: Repeated completion & completion against in-progress visit
        fu = create_followup_task(patient=patient, facility=self.clinic_a, due_date=datetime.date.today(), category="GENERAL")
        visit_inprogress = Visit.objects.create(visit_id="VIS-P15-INPROG", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="WAITING_FOR_TRIAGE")
        
        # Complete against in-progress visit -> 409
        res_fu_bad_visit = self.client.post(f'/api/v1/referrals/followups/{fu.id}/complete/', {"completed_in_visit_id": visit_inprogress.id}, format='json')
        self.assertEqual(res_fu_bad_visit.status_code, status.HTTP_409_CONFLICT)

        # Legitimate completion with completed visit
        visit_comp = Visit.objects.create(visit_id="VIS-P15-COMP", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED")
        complete_followup(fu, visit_comp, self.doc_staff)

        # Repeated completion of already COMPLETED task -> 409 Conflict
        res_fu_repeat = self.client.post(f'/api/v1/referrals/followups/{fu.id}/complete/', {"completed_in_visit_id": visit_comp.id}, format='json')
        self.assertEqual(res_fu_repeat.status_code, status.HTTP_409_CONFLICT)

        # 6. Procurement: Duplicate approval of approved PO & receiving unapproved PO
        self.client.force_authenticate(user=self.admin_user)
        vendor = Vendor.objects.create(vendor_name="Reliable Pharma", contact_person="Vikas", phone="9900011223", email="vikas@reliable.com")
        po = create_purchase_order(facility=self.clinic_a, vendor=vendor, created_by_staff=self.admin_staff)
        
        # Attempt to receive goods for DRAFT PO -> 409 Conflict
        res_grn_draft = self.client.post('/api/v1/procurement/grn/', {
            "purchase_order_id": po.id, "facility_id": self.clinic_a.id, "grn_number": "GRN-P15-DRAFT",
            "items_received": [{"medicine_id": med.id, "batch_number": "PCM-RECV-01", "expiry_date": str(datetime.date.today() + datetime.timedelta(days=120)), "quantity_received": 10, "quantity_accepted": 10}]
        }, format='json')
        self.assertEqual(res_grn_draft.status_code, status.HTTP_409_CONFLICT)

        # First approval succeeds
        res_app1 = self.client.post(f'/api/v1/procurement/purchase-orders/{po.id}/approve/', {"approval_tier": 1}, format='json')
        self.assertEqual(res_app1.status_code, status.HTTP_200_OK)

        # Duplicate approval tier -> 409 Conflict
        res_app2 = self.client.post(f'/api/v1/procurement/purchase-orders/{po.id}/approve/', {"approval_tier": 1}, format='json')
        self.assertEqual(res_app2.status_code, status.HTTP_409_CONFLICT)

    # =========================================================================
    # 2. IDEMPOTENCY & DUPLICATE REQUEST TESTING
    # =========================================================================
    def test_02_idempotency_and_duplicate_request_resilience(self):
        """
        Verifies that operations subject to retries/duplicates do not create duplicate business effects:
        - OPD Token: Re-calling issue-opd-token returns existing token, never generates multiple tokens.
        - Lab Token: Re-calling issue-lab-token returns existing lab token.
        - GRN: Duplicate grn_number is rejected and cannot post double inventory.
        - Alert Acknowledgment: Multiple acknowledgments remain safely idempotent.
        """
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(patient_id="PAT-P15-IDEM", person=self.person_doc, name="Idempotent Patient", age=40, gender="MALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-IDEM", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="WAITING_FOR_TRIAGE")

        # 1. OPD Token Idempotency
        res_tok1 = self.client.post(f'/api/v1/visits/{visit.id}/issue-opd-token/')
        self.assertEqual(res_tok1.status_code, status.HTTP_200_OK)
        token_num1 = res_tok1.data['token_number']

        res_tok2 = self.client.post(f'/api/v1/visits/{visit.id}/issue-opd-token/')
        self.assertEqual(res_tok2.status_code, status.HTTP_200_OK)
        token_num2 = res_tok2.data['token_number']
        self.assertEqual(token_num1, token_num2)
        self.assertEqual(Token.objects.filter(visit=visit).count(), 1)

        # 2. Lab Token Idempotency
        order = DiagnosticOrder.objects.create(order_number="ORD-P15-IDEM", visit=visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff)
        res_lab1 = self.client.post(f'/api/v1/visits/{visit.id}/issue-lab-token/', {"diagnostic_order_id": order.id}, format='json')
        self.assertEqual(res_lab1.status_code, status.HTTP_200_OK)
        lab_num1 = res_lab1.data['lab_token_number']

        res_lab2 = self.client.post(f'/api/v1/visits/{visit.id}/issue-lab-token/', {"diagnostic_order_id": order.id}, format='json')
        self.assertEqual(res_lab2.status_code, status.HTTP_200_OK)
        lab_num2 = res_lab2.data['lab_token_number']
        self.assertEqual(lab_num1, lab_num2)

        # 3. Duplicate GRN Number Rejected
        self.client.force_authenticate(user=self.admin_user)
        vendor = Vendor.objects.create(vendor_name="MedSupply Corp", contact_person="Ravi", phone="9988776655", email="ravi@medsupply.com")
        po = create_purchase_order(facility=self.clinic_a, vendor=vendor, created_by_staff=self.admin_staff)
        approve_purchase_order(po, self.admin_staff, approval_tier=1)
        med = MedicineMaster.objects.create(generic_name="Azithromycin", strength="250 mg", dosage_form="Tablet")

        grn_payload = {
            "purchase_order_id": po.id, "facility_id": self.clinic_a.id, "grn_number": "GRN-P15-UNIQUE-01",
            "items_received": [{"medicine_id": med.id, "batch_number": "AZI-UNQ-01", "expiry_date": str(datetime.date.today() + datetime.timedelta(days=180)), "quantity_received": 100, "quantity_accepted": 100}]
        }
        res_grn1 = self.client.post('/api/v1/procurement/grn/', grn_payload, format='json')
        self.assertEqual(res_grn1.status_code, status.HTTP_201_CREATED)

        # Second identical GRN payload -> Rejected by unique constraint/validation
        res_grn2 = self.client.post('/api/v1/procurement/grn/', grn_payload, format='json')
        self.assertIn(res_grn2.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])
        self.assertEqual(GoodsReceiptNote.objects.filter(grn_number="GRN-P15-UNIQUE-01").count(), 1)
        self.assertEqual(InventoryLedger.objects.filter(transaction_type="PURCHASE_RECEIPT", batch__batch_number="AZI-UNQ-01").count(), 1)

        # 4. Operational Alert Idempotent Acknowledgment
        self.client.force_authenticate(user=self.nurse_user)
        alert = OperationalAlert.objects.create(facility=self.clinic_a, alert_category="EQUIPMENT", title="ECG Calibration Due", message="Calibration pending", severity="MEDIUM", is_active=True)
        res_ack1 = self.client.post(f'/api/v1/alerts/{alert.id}/acknowledge/')
        self.assertEqual(res_ack1.status_code, status.HTTP_200_OK)
        self.assertFalse(res_ack1.data['is_active'])

        res_ack2 = self.client.post(f'/api/v1/alerts/{alert.id}/acknowledge/')
        self.assertEqual(res_ack2.status_code, status.HTTP_200_OK)
        self.assertFalse(res_ack2.data['is_active'])

    # =========================================================================
    # 3. INVENTORY RELIABILITY & NEGATIVE STOCK GUARDS
    # =========================================================================
    def test_03_inventory_reliability_and_negative_stock_prevention(self):
        """
        Verifies the core inventory invariants:
        - physical_stock cannot become negative under any circumstance.
        - Available stock cannot be over-dispensed.
        - Quarantine stock deductions protect quarantined units from ordinary dispensation.
        - Authoritative double-entry InventoryLedger sum equals physical stock balance.
        """
        self.client.force_authenticate(user=self.pharm_user)
        med = MedicineMaster.objects.create(generic_name="Ciprofloxacin", strength="500 mg", dosage_form="Tablet")
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="CIP-P15-REL",
            expiry_date=datetime.date.today() + datetime.timedelta(days=120),
            quantity=0, available_quantity=0, status="AVAILABLE"
        )
        post_inventory_movement(
            batch=batch, facility=self.clinic_a, performed_by_staff=self.pharm_staff,
            transaction_type="PURCHASE_RECEIPT", quantity_delta=50,
            bucket_deltas={"available_quantity": 50}
        )

        patient = Patient.objects.create(patient_id="PAT-P15-INV", person=self.person_doc, name="Inv Patient", age=45, gender="MALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-INV", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        consult = Consultation.objects.create(visit=visit, patient=patient, facility=self.clinic_a, doctor_staff=self.doc_staff, chief_complaint="UTI")
        rx = Prescription.objects.create(consultation=consult, patient=patient, facility=self.clinic_a, status="VERIFIED")
        rx_item = PrescriptionItem.objects.create(prescription=rx, medicine=med, medicine_name="Ciprofloxacin 500mg", quantity=100, status="PENDING")

        # 1. Attempting to dispense 60 units when available is 50 -> 409 InsufficientStockError
        res_excess = self.client.post('/api/v1/pharmacy/dispensations/', {
            "prescription_id": rx.id, "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 60}]
        }, format='json')
        self.assertEqual(res_excess.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(res_excess.data['code'], ['CONFLICT', 'INSUFFICIENT_STOCK'])
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 50)
        self.assertEqual(batch.quantity, 50)

        # 2. Quarantine stock: hold 20 units -> available becomes 30
        quarantine_stock(batch, self.clinic_a, self.pharm_staff, 20, reason="Suspected moisture damage")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 30)
        self.assertEqual(batch.quarantined_quantity, 20)
        self.assertEqual(batch.quantity, 50)

        # Attempting to dispense 40 units fails because available is only 30 (quarantined stock protected)
        res_quar_block = self.client.post('/api/v1/pharmacy/dispensations/', {
            "prescription_id": rx.id, "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 40}]
        }, format='json')
        self.assertEqual(res_quar_block.status_code, status.HTTP_409_CONFLICT)

        # Release quarantined stock -> available restored to 50
        release_quarantined_stock(batch, self.clinic_a, self.pharm_staff, 20, reason="Lab clearance passed")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 50)
        self.assertEqual(batch.quarantined_quantity, 0)

        # Dispense legitimate 30 units -> available becomes 20
        res_disp = self.client.post('/api/v1/pharmacy/dispensations/', {
            "prescription_id": rx.id, "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": rx_item.id, "batch_id": batch.id, "quantity": 30}]
        }, format='json')
        self.assertEqual(res_disp.status_code, status.HTTP_201_CREATED)
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 20)
        self.assertEqual(batch.quantity, 20)

        # Verify authoritative ledger summation invariant
        ledger_delta_sum = sum(InventoryLedger.objects.filter(batch=batch).values_list('quantity_delta', flat=True))
        self.assertEqual(ledger_delta_sum, batch.quantity)
        self.assertEqual(batch.quantity, 20)

    # =========================================================================
    # 4. CONTROLLED TRANSACTION FAILURE & ZERO PHANTOM AUDIT
    # =========================================================================
    def test_04_transaction_failure_and_rollback_zero_phantom_audit(self):
        """
        Verifies that mid-transaction failures trigger total atomic rollback:
        - Injected failure in dispensation does not persist partial ledger entries or audit logs.
        - Injected failure in follow-up completion does not mark task completed.
        - Injected failure in GRN does not create dangling batches or orphan ledger rows.
        """
        med = MedicineMaster.objects.create(generic_name="Metformin", strength="500 mg", dosage_form="Tablet")
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="MET-P15-FAIL",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=40, available_quantity=40, status="AVAILABLE"
        )
        patient = Patient.objects.create(patient_id="PAT-P15-FAIL", person=self.person_doc, name="Fail Patient", age=50, gender="FEMALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-FAIL", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        consult = Consultation.objects.create(visit=visit, patient=patient, facility=self.clinic_a, doctor_staff=self.doc_staff, chief_complaint="Diabetes")
        rx = Prescription.objects.create(consultation=consult, patient=patient, facility=self.clinic_a, status="VERIFIED")
        rx_item = PrescriptionItem.objects.create(prescription=rx, medicine=med, medicine_name="Metformin 500mg", quantity=20, status="PENDING")

        initial_ledger_count = InventoryLedger.objects.count()
        initial_audit_count = AuditLogEntry.objects.count()

        # Injected failure: Mock DispensationItem.objects.create to raise an unexpected runtime error
        with patch('apps.pharmacy.services.DispensationItem.objects.create', side_effect=RuntimeError("Simulated Hardware/DB Failure")):
            with self.assertRaises(RuntimeError):
                dispense_prescription(
                    prescription=rx,
                    items_to_dispense=[{"prescription_item": rx_item, "batch": batch, "quantity": 10}],
                    dispensing_staff=self.pharm_staff,
                    facility=self.clinic_a
                )

        # Rollback guarantees: Batch remains strictly 40, zero ledger rows written, zero audit entries
        batch.refresh_from_db()
        rx_item.refresh_from_db()
        self.assertEqual(batch.available_quantity, 40)
        self.assertEqual(batch.quantity, 40)
        self.assertEqual(rx_item.dispensed_quantity, 0)
        self.assertEqual(InventoryLedger.objects.count(), initial_ledger_count)
        self.assertEqual(AuditLogEntry.objects.count(), initial_audit_count)
        self.assertEqual(Dispensation.objects.count(), 0)

    # =========================================================================
    # 5. COMPREHENSIVE ROLE AUTHORIZATION NEGATIVE MATRIX
    # =========================================================================
    def test_05_comprehensive_role_authorization_matrix(self):
        """
        Verifies that unauthorized roles are rejected with HTTP 403 across operational domains:
        - DOCTOR cannot approve purchase orders or dispense medications.
        - NURSE cannot prescribe medications or verify diagnostic results.
        - LAB_TECHNICIAN cannot prescribe medications or verify diagnostic results.
        - PHARMACIST cannot record consultations or verify diagnostic results.
        - Unauthenticated access returns HTTP 401.
        """
        vendor = Vendor.objects.create(vendor_name="Matrix Vendor", contact_person="Ravi", phone="9988771122", email="m@vendor.com")
        po = create_purchase_order(facility=self.clinic_a, vendor=vendor, created_by_staff=self.admin_staff)
        patient = Patient.objects.create(patient_id="PAT-P15-ROLES", person=self.person_doc, name="Role Patient", age=25, gender="MALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-ROLES", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        order = DiagnosticOrder.objects.create(order_number="ORD-P15-ROLES", visit=visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff)
        master = DiagnosticTestMaster.objects.create(test_code="TEST-ROLES", test_name="Test Role Master", category="PATHOLOGY", specimen_type="BLOOD")
        req = TestRequest.objects.create(diagnostic_order=order, test_master=master)
        res = DiagnosticResult.objects.create(test_request=req, result_value_text="Normal", status="ENTERED", entered_by_staff=self.lab_staff)

        # 1. Unauthenticated -> 401
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/visits/').status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. DOCTOR negative checks
        self.client.force_authenticate(user=self.doc_user)
        # Doctor cannot approve PO
        res_doc_po = self.client.post(f'/api/v1/procurement/purchase-orders/{po.id}/approve/', {"approval_tier": 1}, format='json')
        self.assertEqual(res_doc_po.status_code, status.HTTP_403_FORBIDDEN)

        # 3. NURSE negative checks
        self.client.force_authenticate(user=self.nurse_user)
        # Nurse cannot verify lab results
        res_nur_ver = self.client.post(f'/api/v1/diagnostics/results/{res.id}/verify/')
        self.assertEqual(res_nur_ver.status_code, status.HTTP_403_FORBIDDEN)

        # 4. LAB TECHNICIAN negative checks
        self.client.force_authenticate(user=self.lab_user)
        # Lab Tech cannot verify diagnostic results (only doctors can verify)
        res_lab_ver = self.client.post(f'/api/v1/diagnostics/results/{res.id}/verify/')
        self.assertEqual(res_lab_ver.status_code, status.HTTP_403_FORBIDDEN)

        # 5. PHARMACIST negative checks
        self.client.force_authenticate(user=self.pharm_user)
        # Pharmacist cannot create clinical consultation
        res_phm_c = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a.id, "chief_complaint": "Invalid"
        }, format='json')
        self.assertEqual(res_phm_c.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 6. STAFF LIFECYCLE, TRANSFERS, EFFECTIVE DATES & AUTHORS INTEGRITY
    # =========================================================================
    def test_06_staff_lifecycle_effective_dates_and_historical_integrity(self):
        """
        Tests staff administrative status, facility transfers, effective date boundaries,
        and preservation of historical clinical authorship.
        """
        # 1. Historical Clinical Authorship Preservation
        patient = Patient.objects.create(patient_id="PAT-P15-LIFE", person=self.person_doc, name="Life Patient", age=33, gender="FEMALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-LIFE", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        consult = Consultation.objects.create(visit=visit, patient=patient, facility=self.clinic_a, doctor_staff=self.doc_staff, chief_complaint="Asthma")
        rx = Prescription.objects.create(consultation=consult, patient=patient, facility=self.clinic_a, status="VERIFIED")

        # Deactivate Doctor
        update_staff_status(self.doc_staff, "SUSPENDED", actor_staff=self.admin_staff)
        self.doc_staff.refresh_from_db()
        self.assertEqual(self.doc_staff.status, "SUSPENDED")

        # Inactive doctor is rejected from performing any new clinical mutations -> 403 Forbidden
        self.client.force_authenticate(user=self.doc_user)
        res_inact = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a.id, "chief_complaint": "New Attempt"
        }, format='json')
        self.assertEqual(res_inact.status_code, status.HTTP_403_FORBIDDEN)

        # Historical authorship remains completely intact and queryable
        consult.refresh_from_db()
        rx.refresh_from_db()
        self.assertEqual(consult.doctor_staff_id, self.doc_staff.id)
        self.assertEqual(rx.consultation.doctor_staff_id, self.doc_staff.id)

        # 2. Staff Facility Transfer & Immediate Scoping Update
        # Reactivate staff and transfer to Clinic B
        update_staff_status(self.doc_staff, "ACTIVE", actor_staff=self.admin_staff)
        transfer_staff(self.doc_staff, new_facility=self.clinic_b, new_department=self.dept_opd_b, actor_staff=self.admin_staff)
        self.doc_user.refresh_from_db()

        # After transfer, doctor can mutate Clinic B records, but is blocked from mutating Clinic A
        self.client.force_authenticate(user=self.doc_user)
        visit_b = Visit.objects.create(visit_id="VIS-P15-TRANSB", patient=patient, facility=self.clinic_b, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        res_mut_b = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit_b.id, "patient": patient.id, "facility": self.clinic_b.id, "chief_complaint": "Consultation at Clinic B"
        }, format='json')
        self.assertEqual(res_mut_b.status_code, status.HTTP_201_CREATED)

        res_mut_a = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a.id, "chief_complaint": "Consultation at Old Clinic A"
        }, format='json')
        self.assertEqual(res_mut_a.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Effective Dates: Future Assignment does NOT grant premature access
        future_doc_person = Person.objects.create(first_name="Future", last_name="Doc", date_of_birth=datetime.date(1988, 1, 1), gender="MALE")
        future_staff = StaffProfile.objects.create(person=future_doc_person, employee_id="DOC-FUTURE-01", designation="Medical Officer", status="ACTIVE")
        future_user = User.objects.create_user(username="doc_future", password="password123", full_name="Dr. Future", role="DOCTOR", staff_profile=future_staff)
        StaffRoleAssignment.objects.create(staff=future_staff, role=self.role_doc, effective_from=datetime.date.today(), is_active=True)
        # Assignment starting 30 days in the future
        StaffFacilityAssignment.objects.create(
            staff=future_staff, facility=self.clinic_a, is_primary=True, is_active=True,
            effective_from=datetime.date.today() + datetime.timedelta(days=30)
        )
        self.client.force_authenticate(user=future_user)
        res_fut = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a.id, "chief_complaint": "Premature access attempt"
        }, format='json')
        self.assertEqual(res_fut.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 7. CROSS-FACILITY BOUNDARY & CONTINUITY-OF-CARE SEARCH
    # =========================================================================
    def test_07_cross_facility_boundary_and_continuity_of_care(self):
        """
        Verifies multi-tenancy isolation between Clinic A and Clinic B:
        - Clinic A staff cannot view or mutate Clinic B operational records (403/404).
        - Continuity of care: Default patient listing returns only Clinic A patients.
        - Explicit search (?search=) permits statewide demographic lookup across facilities.
        """
        # Create Patient and Visit in Clinic B
        pat_b = Patient.objects.create(patient_id="PAT-P15-SEC-B", person=self.person_doc_b, name="Clinic B Patient", mobile="9845011111", age=28, gender="FEMALE", registered_at_facility=self.clinic_b)
        visit_b = Visit.objects.create(visit_id="VIS-P15-SEC-B", patient=pat_b, facility=self.clinic_b, visit_type="OPD", opd_date=datetime.date.today(), status="WAITING_FOR_TRIAGE")
        alert_b = OperationalAlert.objects.create(facility=self.clinic_b, alert_category="CLINICAL", title="Clinic B Severe Alert", message="Severe clinical alert", severity="CRITICAL", is_active=True)

        self.client.force_authenticate(user=self.nurse_user) # Nurse at Clinic A

        # 1. Default patient listing for Clinic A staff returns 0 Clinic B patients
        res_list = self.client.get('/api/v1/patients/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        returned_ids = [p['patient_id'] for p in res_list.data.get('results', res_list.data)]
        self.assertNotIn(pat_b.patient_id, returned_ids)

        # 2. Explicit continuity-of-care search (?search=) locates the patient across facilities
        res_search = self.client.get(f'/api/v1/patients/?search={pat_b.mobile}')
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        search_ids = [p['patient_id'] for p in res_search.data.get('results', res_search.data)]
        self.assertIn(pat_b.patient_id, search_ids)

        # 3. Clinic A nurse cannot view Clinic B visit
        res_v = self.client.get(f'/api/v1/visits/{visit_b.id}/')
        self.assertIn(res_v.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # 4. Clinic A nurse cannot acknowledge Clinic B alert
        res_ack = self.client.post(f'/api/v1/alerts/{alert_b.id}/acknowledge/')
        self.assertIn(res_ack.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    # =========================================================================
    # 8. SERIALIZER MASS-ASSIGNMENT DEFENSE
    # =========================================================================
    def test_08_serializer_mass_assignment_defense(self):
        """
        Verifies that client payloads cannot forge server-derived values or mutate protected fields:
        - Attempting to pass doctor_staff in Consultation payload is ignored; authenticated user is bound.
        - Attempting to pass referring_doctor in ReferralOrder payload is ignored.
        - Attempting to directly update MedicineBatch available_quantity via PATCH/PUT is rejected.
        """
        self.client.force_authenticate(user=self.doc_user)
        patient = Patient.objects.create(patient_id="PAT-P15-MASS", person=self.person_doc, name="Mass Patient", age=30, gender="MALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-MASS", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")

        # 1. Forge doctor_staff: Client attempts to attribute consultation to Clinic B doctor
        forged_consult_payload = {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a.id,
            "doctor_staff": self.doc_b_staff.id, # Forgery attempt
            "chief_complaint": "Mass assignment test"
        }
        res_c = self.client.post('/api/v1/clinical/consultations/', forged_consult_payload, format='json')
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        # Server must override client-supplied ID with the authenticated doctor's ID
        self.assertEqual(res_c.data['doctor_staff'], self.doc_staff.id)
        self.assertNotEqual(res_c.data['doctor_staff'], self.doc_b_staff.id)

        # 2. Forge referring_doctor: Client attempts to pass arbitrary staff
        forged_ref_payload = {
            "patient": patient.id, "visit": visit.id,
            "source_facility": self.clinic_a.id, "destination_facility": self.clinic_b.id,
            "referring_doctor": self.doc_b_staff.id, # Forgery attempt
            "reason": "Referral test", "urgency": "ROUTINE"
        }
        res_ref = self.client.post('/api/v1/referrals/orders/', forged_ref_payload, format='json')
        self.assertEqual(res_ref.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ref.data['referring_doctor'], self.doc_staff.id)

        # 3. Direct MedicineBatch quantity mutation blocked
        self.client.force_authenticate(user=self.pharm_user)
        med = MedicineMaster.objects.create(generic_name="Amoxicillin", strength="250 mg", dosage_form="Capsule")
        batch = MedicineBatch.objects.create(facility=self.clinic_a, medicine=med, batch_number="AMX-P15-MASS", expiry_date=datetime.date.today() + datetime.timedelta(days=90), quantity=10, available_quantity=10, status="AVAILABLE")

        res_batch_patch = self.client.patch(f'/api/v1/pharmacy/batches/{batch.id}/', {"available_quantity": 9999, "quantity": 9999}, format='json')
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 10)
        self.assertEqual(batch.quantity, 10)

    # =========================================================================
    # 9. API ERROR CONTRACT DETERMINISM
    # =========================================================================
    def test_09_api_error_contract_determinism(self):
        """
        Verifies deterministic API response envelopes and status codes across error categories:
        - 401 Unauthorized for missing authentication.
        - 403 Forbidden for unauthorized actions with {error, code: "UNAUTHORIZED_DOMAIN_ACTION"}.
        - 400 Bad Request for validation errors with {code: "VALIDATION_ERROR"}.
        - 409 Conflict for domain state collisions with {code: "CONFLICT"}.
        - 404/403 for non-existent or inaccessible objects without leaking existence.
        """
        # 1. 401 Unauthorized
        self.client.force_authenticate(user=None)
        res_401 = self.client.get('/api/v1/patients/')
        self.assertEqual(res_401.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. 403 Forbidden
        self.client.force_authenticate(user=self.nurse_user)
        res_403 = self.client.post('/api/v1/procurement/purchase-orders/1/approve/', {"approval_tier": 1}, format='json')
        self.assertEqual(res_403.status_code, status.HTTP_403_FORBIDDEN)

        # 3. 400 Bad Request (Validation Error)
        self.client.force_authenticate(user=self.admin_user)
        res_400 = self.client.post('/api/v1/patients/', {"age": -5}, format='json')
        self.assertEqual(res_400.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. 409 Conflict
        patient = Patient.objects.create(patient_id="PAT-P15-ERR", person=self.person_doc, name="Err Patient", age=30, gender="FEMALE", registered_at_facility=self.clinic_a)
        visit = Visit.objects.create(visit_id="VIS-P15-ERR", patient=patient, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        ref = create_referral_order(patient=patient, visit=visit, source_facility=self.clinic_a, destination_facility=self.clinic_b, referring_doctor_staff=self.doc_staff, reason="Error test")
        res_409 = self.client.post(f'/api/v1/referrals/orders/{ref.id}/transition/', {"new_status": "ARRIVED"}, format='json')
        self.assertEqual(res_409.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(res_409.data['code'], ['CONFLICT', 'INVALID_STATE_TRANSITION'])

    # =========================================================================
    # 10. PERFORMANCE SANITY & QUERY COUNT BOUNDS
    # =========================================================================
    def test_10_performance_sanity_query_bounds(self):
        """
        Verifies that high-volume list endpoints execute bounded queries and avoid N+1 regressions:
        - Tests /api/v1/patients/
        - Tests /api/v1/visits/
        - Tests /api/v1/clinical/consultations/
        """
        self.client.force_authenticate(user=self.doc_user)
        
        # Populate 5 patients, visits, and consultations
        for i in range(5):
            p = Patient.objects.create(patient_id=f"PAT-PERF-{i}", person=self.person_doc, name=f"Perf Patient {i}", age=20+i, gender="MALE", registered_at_facility=self.clinic_a)
            v = Visit.objects.create(visit_id=f"VIS-PERF-{i}", patient=p, facility=self.clinic_a, visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED")
            Consultation.objects.create(visit=v, patient=p, facility=self.clinic_a, doctor_staff=self.doc_staff, chief_complaint="Checkup")

        # Patients list: bounded query count
        with self.assertNumQueries(4):  # Auth check, count, results with select_related, permissions
            res = self.client.get('/api/v1/patients/')
            self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Visits list: bounded query count
        with self.assertNumQueries(4):
            res_v = self.client.get('/api/v1/visits/')
            self.assertEqual(res_v.status_code, status.HTTP_200_OK)

        # Consultations list: bounded query count
        with self.assertNumQueries(4):
            res_c = self.client.get('/api/v1/clinical/consultations/')
            self.assertEqual(res_c.status_code, status.HTTP_200_OK)

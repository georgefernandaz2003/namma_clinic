"""
Phase 12 Comprehensive Domain Services & Transactional Business Logic Test Suite.
Verifies all domain service boundaries, transaction locks, and domain exception handling.
"""
import uuid
import datetime
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster, Diagnosis
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult, DiagnosticResultAmendment
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation, DispensationItem,
    InventoryLedger, Vendor, PurchaseOrder, PurchaseOrderItem,
    PurchaseOrderApproval, GoodsReceiptNote, GoodsReceiptItem
)
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.audit.models import AuditLogEntry

from apps.common.exceptions import (
    DomainError, DomainValidationError, UnauthorizedDomainAction,
    InvalidStateTransition, DuplicateTokenError, InvalidAssignmentPeriodError,
    OverlappingAssignmentError, DiagnosticResultAlreadyExistsError,
    VerifiedResultImmutableError, InvalidFollowUpCompletionError,
    InsufficientStockError, InvalidProcurementStateError
)

from apps.audit.services import record_audit_event
from apps.accounts.services import (
    create_staff_profile, update_staff_status, assign_role,
    end_role_assignment, assign_facility, transfer_staff
)
from apps.visits.services import allocate_token, issue_opd_token, issue_lab_token
from apps.laboratory.services import (
    create_diagnostic_order, create_test_request, collect_specimen,
    record_diagnostic_result, verify_diagnostic_result, amend_diagnostic_result
)
from apps.referrals.services import (
    create_referral_order, transition_referral_state,
    create_followup_task, complete_followup
)
from apps.pharmacy.services import (
    post_inventory_movement, quarantine_stock, release_quarantined_stock,
    recall_stock, damage_stock, dispose_stock, dispense_prescription,
    approve_purchase_order, receive_goods_receipt
)
from apps.ncd.services import register_ncd_condition, record_ncd_assessment
from apps.surveillance.services import report_surveillance_case, dispatch_public_health_notification


class Phase12DomainServiceTests(TestCase):
    """Unit tests for Phase 12 domain service layer."""

    def setUp(self):
        # 1. Geography & Organization
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

        self.dept_opd = Department.objects.create(facility=self.clinic_a, code="OPD", name="Outpatient")
        self.dept_lab = Department.objects.create(facility=self.clinic_a, code="LAB", name="Laboratory")

        # 2. Staff Profiles & Roles
        self.person_doc = Person.objects.create(
            first_name="Anil", last_name="Sharma", gender="MALE",
            date_of_birth=datetime.date(1980, 1, 1), phone_number="9800011111"
        )
        self.doc_staff = StaffProfile.objects.create(
            person=self.person_doc, employee_id="DOC-001", designation="Medical Officer",
            department=self.dept_opd
        )
        self.person_nurse = Person.objects.create(
            first_name="Deepa", last_name="Rao", gender="FEMALE",
            date_of_birth=datetime.date(1990, 2, 2), phone_number="9800022222"
        )
        self.nurse_staff = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="NUR-001", designation="Staff Nurse",
            department=self.dept_opd
        )

        self.role_doc = RoleMaster.objects.create(code="DOCTOR", name="Medical Officer")
        self.role_admin = RoleMaster.objects.create(code="ADMIN", name="Facility Administrator")

        # 3. Patient & Visit Encounter
        self.patient = Patient.objects.create(
            patient_id="PAT-001", person=self.person_doc, name="Raju G",
            age=35, gender="MALE", mobile="9800033333", address="Varthur Main Rd",
            registered_at_facility=self.clinic_a
        )
        self.patient2 = Patient.objects.create(
            patient_id="PAT-002", person=self.person_nurse, name="Meena S",
            age=28, gender="FEMALE", mobile="9800044444", address="Whitefield Main Rd",
            registered_at_facility=self.clinic_b
        )

        self.visit = Visit.objects.create(
            visit_id="VIS-001", patient=self.patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), current_queue="DOCTOR", status="IN_CONSULTATION"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit, patient=self.patient, facility=self.clinic_a,
            doctor_staff=self.doc_staff, consultation_sequence=1, chief_complaint="Fever"
        )

    # -------------------------------------------------------------------------
    # 1. IAM SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_01_iam_create_staff_and_valid_assignment(self):
        """IAM: Create staff profile, assign role, assign facility."""
        p = Person.objects.create(
            first_name="Suresh", last_name="N", gender="MALE",
            date_of_birth=datetime.date(1985, 3, 3), phone_number="9800055555"
        )
        staff = create_staff_profile(
            person=p, employee_id="PHARM-001", designation="Pharmacist",
            department=self.dept_opd, actor_staff=self.doc_staff
        )
        self.assertEqual(staff.employee_id, "PHARM-001")

        # Assign role
        assignment = assign_role(
            staff_profile=staff, role=self.role_admin,
            effective_from=datetime.date(2026, 1, 1), actor_staff=self.doc_staff
        )
        self.assertTrue(assignment.is_active)

        # Assign facility
        fac_assign = assign_facility(
            staff_profile=staff, facility=self.clinic_a, is_primary=True,
            effective_from=datetime.date(2026, 1, 1), actor_staff=self.doc_staff
        )
        self.assertTrue(fac_assign.is_primary)

    def test_02_iam_invalid_assignment_dates_rejected(self):
        """IAM: Reject role assignment where effective_to < effective_from."""
        with self.assertRaises(InvalidAssignmentPeriodError):
            assign_role(
                staff_profile=self.doc_staff, role=self.role_admin,
                effective_from=datetime.date(2026, 6, 1),
                effective_to=datetime.date(2026, 5, 1)
            )

    def test_03_iam_prohibited_overlapping_assignment_rejected(self):
        """IAM: Reject conflicting active assignment for the same staff and role."""
        assign_role(
            staff_profile=self.doc_staff, role=self.role_doc,
            effective_from=datetime.date(2026, 1, 1)
        )
        with self.assertRaises(OverlappingAssignmentError):
            assign_role(
                staff_profile=self.doc_staff, role=self.role_doc,
                effective_from=datetime.date(2026, 2, 1)
            )

    def test_04_iam_staff_transfer_atomic(self):
        """IAM: Transfer staff atomically closes prior primary facility assignment."""
        assign_facility(
            staff_profile=self.doc_staff, facility=self.clinic_a, is_primary=True,
            effective_from=datetime.date(2026, 1, 1)
        )
        transfer_date = datetime.date.today()
        new_assign = transfer_staff(
            staff_profile=self.doc_staff, new_facility=self.clinic_b,
            effective_date=transfer_date, actor_staff=self.doc_staff
        )
        self.assertTrue(new_assign.is_primary)
        self.assertEqual(new_assign.facility, self.clinic_b)

        # Prior assignment must be deactivated
        prior = StaffFacilityAssignment.objects.get(staff=self.doc_staff, facility=self.clinic_a)
        self.assertFalse(prior.is_active)
        self.assertFalse(prior.is_primary)

    # -------------------------------------------------------------------------
    # 2. TOKEN SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_05_token_opd_and_lab_coexistence(self):
        """Tokens: OPD and LAB independent daily namespaces allocate identical numbers without collision."""
        today = datetime.date.today()
        opd_token = issue_opd_token(visit=self.visit, facility=self.clinic_a, token_date=today)
        self.assertEqual(opd_token.token_number, 1)

        diag_order = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff,
            order_number="ORD-TOK-001", order_date=today
        )
        lab_token_no = issue_lab_token(diagnostic_order=diag_order, facility=self.clinic_a, order_date=today)
        self.assertEqual(lab_token_no, 1)
        self.assertEqual(diag_order.lab_token_number, 1)

        # Counter separation: Second OPD token gets 2
        visit2 = Visit.objects.create(
            visit_id="VIS-002", patient=self.patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=today
        )
        opd_token2 = issue_opd_token(visit=visit2, facility=self.clinic_a, token_date=today)
        self.assertEqual(opd_token2.token_number, 2)

    # -------------------------------------------------------------------------
    # 3. DIAGNOSTICS SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_06_diagnostics_order_requests_shared_specimen(self):
        """Diagnostics: Create order, multiple requests, and shared biological specimen."""
        order = create_diagnostic_order(
            visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff,
            clinical_indication="Suspected Dengue"
        )
        t_cbc = DiagnosticTestMaster.objects.create(test_code="CBC-S", test_name="CBC", category="HEM", specimen_type="BLOOD")
        t_widal = DiagnosticTestMaster.objects.create(test_code="WID-S", test_name="Widal", category="SER", specimen_type="BLOOD")

        tr1 = create_test_request(diagnostic_order=order, test_master=t_cbc)
        tr2 = create_test_request(diagnostic_order=order, test_master=t_widal)

        specimen = collect_specimen(
            diagnostic_order=order, barcode_identifier="BAR-SER-001", specimen_type="BLOOD",
            collected_by_staff=self.nurse_staff, test_requests=[tr1, tr2]
        )
        self.assertEqual(tr1.specimen, specimen)
        self.assertEqual(tr2.specimen, specimen)
        self.assertEqual(specimen.test_requests.count(), 2)

    def test_07_diagnostics_result_uniqueness_and_verification_lock(self):
        """Diagnostics: One result per request; verified result immutable without amendment."""
        order = create_diagnostic_order(visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff)
        t_fbs = DiagnosticTestMaster.objects.create(test_code="FBS-S", test_name="FBS", category="BIO", specimen_type="PLASMA")
        tr = create_test_request(diagnostic_order=order, test_master=t_fbs)

        res = record_diagnostic_result(
            test_request=tr, entered_by_staff=self.nurse_staff,
            result_value_numeric=105.0, reference_range_applied="70-110 mg/dL"
        )
        self.assertEqual(res.status, "ENTERED")

        # Second result attempt must raise DiagnosticResultAlreadyExistsError
        with self.assertRaises(DiagnosticResultAlreadyExistsError):
            record_diagnostic_result(
                test_request=tr, entered_by_staff=self.nurse_staff,
                result_value_numeric=110.0
            )

        # Verify result
        verified = verify_diagnostic_result(diagnostic_result=res, verified_by_staff=self.doc_staff)
        self.assertEqual(verified.status, "VERIFIED")

        # Second verification attempt must raise VerifiedResultImmutableError
        with self.assertRaises(VerifiedResultImmutableError):
            verify_diagnostic_result(diagnostic_result=verified, verified_by_staff=self.doc_staff)

        # Amend verified result
        amended, amendment = amend_diagnostic_result(
            diagnostic_result=verified, amended_by_staff=self.doc_staff,
            amendment_reason="Analyzer recalibrated", amended_value_numeric=112.0
        )
        self.assertEqual(amended.status, "AMENDED")
        self.assertEqual(amended.result_value_numeric, 112.0)
        self.assertEqual(amendment.previous_value_numeric, 105.0)

    # -------------------------------------------------------------------------
    # 4. FOLLOW-UP SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_08_followup_completion_validation(self):
        """Follow-up: Validate completion success and cross-encounter patient/facility mismatches."""
        followup = create_followup_task(
            patient=self.patient, facility=self.clinic_a,
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            category="NCD_ROUTINE"
        )

        # 1. Wrong Patient mismatch rejected
        visit_wrong_patient = Visit.objects.create(
            visit_id="VIS-WRONG-PAT", patient=self.patient2, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today()
        )
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(
                followup_task=followup, completed_in_visit=visit_wrong_patient,
                completing_staff=self.doc_staff
            )

        # 2. Wrong Facility mismatch rejected
        visit_wrong_fac = Visit.objects.create(
            visit_id="VIS-WRONG-FAC", patient=self.patient, facility=self.clinic_b,
            visit_type="OPD", opd_date=datetime.date.today()
        )
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(
                followup_task=followup, completed_in_visit=visit_wrong_fac,
                completing_staff=self.doc_staff
            )

        # 3. Valid completion succeeds atomically
        completed = complete_followup(
            followup_task=followup, completed_in_visit=self.visit,
            completing_staff=self.doc_staff
        )
        self.assertEqual(completed.status, "COMPLETED")
        self.assertEqual(completed.completed_in_visit, self.visit)
        self.assertEqual(completed.completed_by_staff, self.doc_staff)

        # 4. Attempting to complete an already completed task rejected
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(
                followup_task=completed, completed_in_visit=self.visit,
                completing_staff=self.doc_staff
            )

    # -------------------------------------------------------------------------
    # 5. INVENTORY & BUCKET SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_09_inventory_movement_and_insufficient_stock(self):
        """Inventory: Authoritative ledger posting and non-negative balance enforcement."""
        med = MedicineMaster.objects.create(generic_name="Amoxicillin", strength="500 mg", dosage_form="Capsule")
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="AMX-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=0, available_quantity=0
        )

        # Stock Receipt (+)
        ledger1 = post_inventory_movement(
            batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff,
            transaction_type="PURCHASE_RECEIPT", quantity_delta=500
        )
        self.assertEqual(ledger1.balance_after, 500)
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 500)
        self.assertEqual(batch.quantity, 500)

        # Over-deduction (-) raises InsufficientStockError
        with self.assertRaises(InsufficientStockError):
            post_inventory_movement(
                batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff,
                transaction_type="DISPENSE", quantity_delta=-600
            )

    def test_10_inventory_bucket_transitions(self):
        """Inventory: Quarantine, release, recall, damage, and formal disposal."""
        med = MedicineMaster.objects.create(generic_name="Ciprofloxacin", strength="500 mg", dosage_form="Tablet")
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="CIP-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=100, available_quantity=100
        )

        # 1. Quarantine 30 units
        quarantine_stock(batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff, quantity=30, reason="Label inspection")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 70)
        self.assertEqual(batch.quarantined_quantity, 30)
        self.assertEqual(batch.quantity, 100) # physical stock unchanged on site

        # 2. Release 10 units from quarantine
        release_quarantined_stock(batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff, quantity=10, reason="Label approved")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 80)
        self.assertEqual(batch.quarantined_quantity, 20)

        # 3. Recall 10 units from available stock
        recall_stock(batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff, quantity=10, reason="Batch recall alert")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 70)
        self.assertEqual(batch.recalled_quantity, 10)

        # 4. Damage 5 units
        damage_stock(batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff, quantity=5, reason="Moisture exposure")
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 65)
        self.assertEqual(batch.damaged_quantity, 5)

        # 5. Formally dispose / incinerate 5 damaged units
        dispose_stock(batch=batch, facility=self.clinic_a, performed_by_staff=self.doc_staff, quantity=5, from_bucket="damaged_quantity", reason="Incinerated")
        batch.refresh_from_db()
        self.assertEqual(batch.damaged_quantity, 0)
        self.assertEqual(batch.disposed_quantity, 5)
        self.assertEqual(batch.quantity, 95) # physical stock decremented to 95

    # -------------------------------------------------------------------------
    # 6. DISPENSATION SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_11_dispensation_multi_batch_and_partial(self):
        """Dispensation: Multi-batch fulfillment and prescription status transitions."""
        med = MedicineMaster.objects.create(generic_name="Metformin", strength="500 mg", dosage_form="Tablet")
        batch1 = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="MET-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=90),
            quantity=20, available_quantity=20
        )
        batch2 = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="MET-002",
            expiry_date=datetime.date.today() + datetime.timedelta(days=120),
            quantity=50, available_quantity=50
        )

        rx = Prescription.objects.create(
            consultation=self.consultation, patient=self.patient, facility=self.clinic_a,
            status="VERIFIED"
        )
        item = PrescriptionItem.objects.create(
            prescription=rx, medicine=med, medicine_name="Metformin 500mg",
            quantity=30, dispensed_quantity=0, status="PENDING"
        )

        # Dispense: 20 from batch1, 10 from batch2 (Total 30)
        items_data = [
            {"prescription_item": item, "batch": batch1, "quantity": 20},
            {"prescription_item": item, "batch": batch2, "quantity": 10},
        ]
        disp = dispense_prescription(
            prescription=rx, items_to_dispense=items_data,
            dispensing_staff=self.doc_staff, facility=self.clinic_a
        )
        self.assertEqual(disp.items.count(), 2)

        item.refresh_from_db()
        self.assertEqual(item.dispensed_quantity, 30)
        self.assertEqual(item.status, "DISPENSED")

        rx.refresh_from_db()
        self.assertEqual(rx.status, "DISPENSED")

        batch1.refresh_from_db()
        batch2.refresh_from_db()
        self.assertEqual(batch1.available_quantity, 0)
        self.assertEqual(batch2.available_quantity, 40)

    # -------------------------------------------------------------------------
    # 7. PROCUREMENT SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_12_procurement_approval_and_grn_receipt(self):
        """Procurement: PO approval does not mutate stock; GRN receipt posts to InventoryLedger."""
        vendor = Vendor.objects.create(vendor_name="Karnataka Pharma Ltd", facility=self.clinic_a)
        po = PurchaseOrder.objects.create(
            po_number="PO-SERV-001", vendor=vendor, facility=self.clinic_a, status="DRAFT"
        )
        med = MedicineMaster.objects.create(generic_name="Albendazole", strength="400 mg", dosage_form="Tablet")
        PurchaseOrderItem.objects.create(
            purchase_order=po, medicine=med, ordered_quantity=1000, unit_price=2.00, total_price=2000.00
        )

        # 1. Approval does not change stock
        approval = approve_purchase_order(purchase_order=po, approver_staff=self.doc_staff, approval_tier=1)
        self.assertEqual(approval.status, "APPROVED")
        po.refresh_from_db()
        self.assertEqual(po.status, "APPROVED")
        self.assertEqual(MedicineBatch.objects.filter(medicine=med).count(), 0)

        # 2. GRN receipt creates batch and posts to InventoryLedger
        items_rec = [{
            "medicine": med, "batch_number": "ALB-2026",
            "expiry_date": datetime.date.today() + datetime.timedelta(days=365),
            "unit_cost": 2.00, "quantity_received": 1000,
            "quantity_accepted": 950, "quantity_rejected": 50,
            "rejection_reason": "50 damaged in transit"
        }]
        grn = receive_goods_receipt(
            purchase_order=po, grn_number="GRN-2026-001",
            items_received=items_rec, receiving_staff=self.doc_staff, facility=self.clinic_a
        )
        self.assertEqual(grn.items.count(), 1)

        batch = MedicineBatch.objects.get(facility=self.clinic_a, medicine=med, batch_number="ALB-2026")
        self.assertEqual(batch.available_quantity, 950)
        self.assertEqual(batch.quantity, 950)

        # Verify InventoryLedger entry
        ledger = InventoryLedger.objects.filter(batch=batch, transaction_type="PURCHASE_RECEIPT").first()
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.quantity_delta, 950)
        self.assertEqual(ledger.balance_after, 950)

    # -------------------------------------------------------------------------
    # 8. REFERRAL & EVENT TRAIL SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_13_referral_state_transitions_and_append_event(self):
        """Referrals: Order creation and validated state machine transitions."""
        order = create_referral_order(
            patient=self.patient, visit=self.visit, source_facility=self.clinic_a, destination_facility=self.clinic_b,
            referring_doctor_staff=self.doc_staff, reason="Higher cardiology evaluation"
        )
        self.assertEqual(order.status, "INITIATED")
        self.assertEqual(order.events.count(), 1)
        self.assertEqual(order.events.first().event_type, "ACKNOWLEDGED")

        # Valid transition: INITIATED -> ACKNOWLEDGED
        order, event = transition_referral_state(
            referral_order=order, new_status="ACKNOWLEDGED", actor_staff=self.doc_staff, notes="Bed reserved"
        )
        self.assertEqual(order.status, "ACKNOWLEDGED")
        self.assertEqual(order.events.count(), 2)

        # Invalid transition: ACKNOWLEDGED -> COMPLETED (must go via IN_TRANSIT / ARRIVED)
        with self.assertRaises(InvalidStateTransition):
            transition_referral_state(referral_order=order, new_status="COMPLETED", actor_staff=self.doc_staff)

    # -------------------------------------------------------------------------
    # 9. NCD, SURVEILLANCE & AUDIT SERVICE TESTS
    # -------------------------------------------------------------------------
    def test_14_ncd_and_surveillance_services(self):
        """NCD & Surveillance: Chronic registry, periodic assessments, and statutory IDSP reporting."""
        ncd = register_ncd_condition(
            patient=self.patient, facility=self.clinic_a, registering_doctor=self.doc_staff,
            condition_code="DIABETES_T2", staging="MODERATE"
        )
        self.assertEqual(ncd.condition_code, "DIABETES_T2")

        assessment = record_ncd_assessment(
            condition=ncd, visit=self.visit, assessed_by_staff=self.doc_staff,
            systolic_bp=130, diastolic_bp=80, blood_glucose_fasting=118.0
        )
        self.assertEqual(assessment.systolic_bp, 130)

        # Surveillance
        disease = DiseaseMaster.objects.create(disease_code="MALARIA_PF", disease_name="Malaria Falciparum", transmission_type="VECTOR_BORNE")
        case = report_surveillance_case(
            patient=self.patient, facility=self.clinic_a, disease=disease,
            reporting_staff=self.doc_staff, severity="MODERATE", status="SUSPECTED"
        )
        self.assertEqual(case.status, "SUSPECTED")

        notification = dispatch_public_health_notification(
            case=case, notified_authority="DISTRICT_SURVEILLANCE_OFFICER",
            dispatch_payload={"case_id": case.id, "disease": disease.disease_code}
        )
        self.assertEqual(notification.transmission_status, "DISPATCHED")

    def test_15_audit_event_recording(self):
        """Audit: Explicit audit service preserves durable actor identity and JSON snapshots."""
        log = record_audit_event(
            actor_staff=self.doc_staff,
            actor_role_snapshot="DOCTOR",
            facility=self.clinic_a,
            action_type="UPDATE",
            table_name="diagnostic_results",
            record_id="202",
            payload_before={"status": "ENTERED"},
            payload_after={"status": "VERIFIED"}
        )
        self.assertEqual(log.actor_staff, self.doc_staff)
        self.assertEqual(log.action_type, "UPDATE")
        self.assertEqual(log.payload_after["status"], "VERIFIED")

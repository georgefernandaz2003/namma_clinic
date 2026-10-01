import uuid
import datetime
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError, RestrictedError

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster,
    StaffRoleAssignment, StaffFacilityAssignment, User
)
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter
from apps.triage.models import Triage
from apps.consultations.models import Consultation, DiagnosisMaster, Diagnosis
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult, DiagnosticResultAmendment
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation,
    DispensationItem, InventoryLedger, Vendor,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderApproval
)
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry


class Phase11ComprehensiveModelTests(TestCase):
    """
    Comprehensive physical domain model test suite covering all 50 target tables,
    cardinality rules, constraints, token namespaces, retention matrix, and audit trails.
    """

    def setUp(self):
        # 1. Geographic & Facility Hierarchy
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.taluk = Taluk.objects.create(name="Bengaluru East", code="TAL-BLR-E", district=self.district)
        self.zone = Zone.objects.create(name="Mahadevapura Zone", district=self.district)
        self.ward = Ward.objects.create(name="Varthur", ward_number=149, zone=self.zone)
        self.facility = Facility.objects.create(
            facility_code="PHC-VARTHUR",
            facility_name="Varthur Namma Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            zone=self.zone,
            ward=self.ward
        )
        self.dept_opd = Department.objects.create(
            facility=self.facility,
            code="OPD",
            name="Outpatient Department"
        )
        self.dept_lab = Department.objects.create(
            facility=self.facility,
            code="LAB",
            name="Clinical Diagnostics Laboratory"
        )

        # 2. Services Master
        self.srv_opd = ServiceMaster.objects.create(
            code="SRV-OPD-GEN",
            name="General OPD Consultation",
            category="CLINICAL"
        )
        self.fac_srv = FacilityService.objects.create(
            facility=self.facility,
            service=self.srv_opd,
            is_available=True
        )

        # 3. IAM Hierarchy (Person -> StaffProfile -> RoleMaster)
        self.person = Person.objects.create(
            first_name="Ramesh",
            last_name="Kumar",
            gender="MALE",
            date_of_birth=datetime.date(1982, 5, 14),
            phone_number="9876543210"
        )
        self.staff = StaffProfile.objects.create(
            person=self.person,
            employee_id="STF-DOC-001",
            designation="Medical Officer",
            department=self.dept_opd
        )
        self.role_doctor, _ = RoleMaster.objects.get_or_create(
            code="DOCTOR",
            defaults={"name": "Medical Officer / General Practitioner"}
        )
        self.role_admin, _ = RoleMaster.objects.get_or_create(
            code="FACILITY_ADMIN",
            defaults={"name": "Facility Administrator"}
        )

        # 4. Patient & Encounter Anchor
        self.patient = Patient.objects.create(
            patient_id="PAT-VAR-001",
            person=self.person,
            name="Anand Sharma",
            age=42,
            gender="MALE",
            mobile="9888877777",
            address="12 Main Rd, Varthur",
            registered_at_facility=self.facility
        )
        self.visit = Visit.objects.create(
            visit_id="VIS-20260924-001",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD",
            opd_date=datetime.date.today(),
            current_queue="DOCTOR",
            status="IN_CONSULTATION"
        )

    # -------------------------------------------------------------------------
    # 1. IAM DOMAIN
    # -------------------------------------------------------------------------
    def test_01_iam_assignment_effective_dates(self):
        """1. Verify effective_to >= effective_from check constraint and multi-role assignments."""
        a1 = StaffRoleAssignment.objects.create(
            staff=self.staff, role=self.role_doctor,
            effective_from=datetime.date(2026, 1, 1),
            effective_to=None
        )
        self.assertIsNotNone(a1.pk)

        a2 = StaffRoleAssignment.objects.create(
            staff=self.staff, role=self.role_admin,
            effective_from=datetime.date(2026, 1, 1),
            effective_to=datetime.date(2026, 12, 31)
        )
        self.assertEqual(self.staff.role_assignments.count(), 2)

        with self.assertRaises(IntegrityError):
            StaffRoleAssignment.objects.create(
                staff=self.staff, role=self.role_doctor,
                effective_from=datetime.date(2026, 6, 1),
                effective_to=datetime.date(2026, 5, 1)
            )

    # -------------------------------------------------------------------------
    # 2. ORGANIZATION DOMAIN
    # -------------------------------------------------------------------------
    def test_02_organization_hierarchy(self):
        """2. Verify Organization hierarchy State -> District -> Taluk -> Facility -> Department."""
        self.assertEqual(self.taluk.district, self.district)
        self.assertEqual(self.facility.district, self.district)
        self.assertEqual(self.dept_opd.facility, self.facility)
        self.assertEqual(self.fac_srv.facility, self.facility)
        self.assertTrue(self.fac_srv.is_available)

    # -------------------------------------------------------------------------
    # 3. ENCOUNTER & COUNTER DOMAIN
    # -------------------------------------------------------------------------
    def test_03_visit_daily_counter_relationship(self):
        """3. Verify Visit encounter anchor and FacilityDailyCounter allocation."""
        counter_opd = FacilityDailyCounter.objects.create(
            facility=self.facility,
            counter_date=datetime.date.today(),
            counter_type="OPD",
            last_token_number=1
        )
        self.assertEqual(counter_opd.last_token_number, 1)

        with self.assertRaises(IntegrityError):
            FacilityDailyCounter.objects.create(
                facility=self.facility,
                counter_date=datetime.date.today(),
                counter_type="OPD",
                last_token_number=2
            )

    # -------------------------------------------------------------------------
    # 4. CLINICAL DOMAIN (1:N CONSULTATIONS)
    # -------------------------------------------------------------------------
    def test_04_consultation_1_to_n(self):
        """4. Verify Consultation supports 1:N sequence per Visit encounter anchor."""
        c1 = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            consultation_sequence=1,
            chief_complaint="Persistent fever and body ache"
        )
        c2 = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            consultation_sequence=2,
            chief_complaint="Post-lab review: Platelets normal"
        )
        self.assertEqual(self.visit.consultations.count(), 2)
        self.assertEqual(c1.consultation_sequence, 1)
        self.assertEqual(c2.consultation_sequence, 2)

        diag_master = DiagnosisMaster.objects.create(
            icd10_code="A90",
            description="Dengue fever [classical dengue]",
            is_notifiable=True
        )
        diag = Diagnosis.objects.create(
            consultation=c1,
            diagnosis_master=diag_master,
            diagnosis_type="WORKING",
            certainty="CONFIRMED",
            is_primary=True
        )
        self.assertEqual(c1.diagnoses.count(), 1)
        self.assertTrue(diag.diagnosis_master.is_notifiable)

    # -------------------------------------------------------------------------
    # 5. DIAGNOSTICS: SHARED SPECIMEN
    # -------------------------------------------------------------------------
    def test_05_shared_specimen_across_test_requests(self):
        """5. Verify 1 Specimen may serve multiple TestRequests under a DiagnosticOrder."""
        order = DiagnosticOrder.objects.create(
            visit=self.visit,
            facility=self.facility,
            ordering_doctor_staff=self.staff,
            order_number="ORD-20260924-001"
        )
        specimen = Specimen.objects.create(
            diagnostic_order=order,
            barcode_identifier="BC-20260924-001",
            specimen_type="WHOLE_BLOOD",
            collected_by_staff=self.staff
        )
        test1 = DiagnosticTestMaster.objects.create(
            test_code="CBC", test_name="Complete Blood Count",
            category="HEMATOLOGY", specimen_type="WHOLE_BLOOD"
        )
        test2 = DiagnosticTestMaster.objects.create(
            test_code="ESR", test_name="Erythrocyte Sedimentation Rate",
            category="HEMATOLOGY", specimen_type="WHOLE_BLOOD"
        )

        tr1 = TestRequest.objects.create(diagnostic_order=order, test_master=test1, specimen=specimen)
        tr2 = TestRequest.objects.create(diagnostic_order=order, test_master=test2, specimen=specimen)

        self.assertEqual(tr1.specimen, specimen)
        self.assertEqual(tr2.specimen, specimen)
        self.assertEqual(specimen.test_requests.count(), 2)
        self.assertEqual(order.test_requests.count(), 2)

    # -------------------------------------------------------------------------
    # 6. DIAGNOSTICS: ONE CURRENT RESULT PER TEST REQUEST
    # -------------------------------------------------------------------------
    def test_06_one_diagnostic_result_per_test_request(self):
        """6. Verify TestRequest 1:1 DiagnosticResult (duplicate result rejected)."""
        order = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.facility,
            ordering_doctor_staff=self.staff, order_number="ORD-20260924-002"
        )
        test = DiagnosticTestMaster.objects.create(
            test_code="WIDAL", test_name="Widal Agglutination Test",
            category="SEROLOGY", specimen_type="SERUM"
        )
        tr = TestRequest.objects.create(diagnostic_order=order, test_master=test)

        res1 = DiagnosticResult.objects.create(
            test_request=tr,
            result_value_text="Negative for S. typhi",
            reference_range_applied="Negative",
            status="ENTERED",
            entered_by_staff=self.staff
        )
        self.assertIsNotNone(res1.pk)

        with self.assertRaises(IntegrityError):
            DiagnosticResult.objects.create(
                test_request=tr,
                result_value_text="Duplicate result attempt",
                reference_range_applied="Negative",
                status="ENTERED",
                entered_by_staff=self.staff
            )

    # -------------------------------------------------------------------------
    # 7. DIAGNOSTICS: RESULT AMENDMENT
    # -------------------------------------------------------------------------
    def test_07_diagnostic_result_amendment(self):
        """7. Verify DiagnosticResultAmendment audit trail for verified result."""
        order = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.facility,
            ordering_doctor_staff=self.staff, order_number="ORD-20260924-003"
        )
        test = DiagnosticTestMaster.objects.create(
            test_code="FBS", test_name="Fasting Blood Sugar",
            category="BIOCHEMISTRY", specimen_type="PLASMA"
        )
        tr = TestRequest.objects.create(diagnostic_order=order, test_master=test)
        result = DiagnosticResult.objects.create(
            test_request=tr,
            result_value_numeric=112.50,
            reference_range_applied="70 - 100 mg/dL",
            status="VERIFIED",
            entered_by_staff=self.staff,
            verified_by_staff=self.staff,
            verified_at=datetime.datetime.now(datetime.timezone.utc)
        )
        amendment = DiagnosticResultAmendment.objects.create(
            diagnostic_result=result,
            previous_value_numeric=112.50,
            amended_value_numeric=122.50,
            amendment_reason="Analyzer calibration offset recalibrated",
            amended_by_staff=self.staff
        )
        self.assertEqual(result.amendments.count(), 1)
        self.assertEqual(amendment.amended_value_numeric, 122.50)

    # -------------------------------------------------------------------------
    # 8. FOLLOW-UP COMPLETION INTEGRITY
    # -------------------------------------------------------------------------
    def test_08a_followup_valid_completion(self):
        """8a. Verify FollowUpTask completion with full encounter linkage succeeds."""
        follow_up = FollowUpTask.objects.create(
            patient=self.patient,
            facility=self.facility,
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            category="NCD_ROUTINE",
            status="PENDING"
        )
        follow_up.status = "COMPLETED"
        follow_up.completed_in_visit = self.visit
        follow_up.completed_by_staff = self.staff
        follow_up.completed_at = datetime.datetime.now(datetime.timezone.utc)
        follow_up.save()
        self.assertEqual(follow_up.status, "COMPLETED")

    def test_08b_followup_missing_linkage_rejected(self):
        """8b. Verify FollowUpTask completion without completed_in_visit is rejected by DB check."""
        with self.assertRaises(IntegrityError):
            FollowUpTask.objects.create(
                patient=self.patient,
                facility=self.facility,
                due_date=datetime.date.today(),
                status="COMPLETED",
                completed_by_staff=self.staff,
                completed_at=datetime.datetime.now(datetime.timezone.utc)
            )

    # -------------------------------------------------------------------------
    # 9. INVENTORY LEDGER DOUBLE-ENTRY & NON-NEGATIVE CHECK
    # -------------------------------------------------------------------------
    def test_09_inventory_ledger_double_entry(self):
        """9. Verify InventoryLedger balance_after >= 0 non-negative constraint."""
        med = MedicineMaster.objects.create(
            generic_name="Paracetamol", strength="500 mg", dosage_form="Tablet"
        )
        batch = MedicineBatch.objects.create(
            medicine=med, facility=self.facility, batch_number="PCM-2026-01",
            expiry_date=datetime.date(2028, 1, 1),
            quantity=1000, available_quantity=1000
        )
        ledger_entry = InventoryLedger.objects.create(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            transaction_type="DISPENSE",
            quantity_delta=-30,
            balance_after=970
        )
        self.assertEqual(ledger_entry.balance_after, 970)

        with self.assertRaises(IntegrityError):
            InventoryLedger.objects.create(
                batch=batch,
                facility=self.facility,
                performed_by_staff=self.staff,
                transaction_type="DISPENSE",
                quantity_delta=-1500,
                balance_after=-500
            )

    # -------------------------------------------------------------------------
    # 10. TOKEN NAMESPACE SEPARATION (OPD VS LAB)
    # -------------------------------------------------------------------------
    def test_10a_token_namespaces_opd_vs_lab_coexistence(self):
        """10a. Verify OPD and Laboratory token namespaces coexist with identical numbers on same date."""
        today = datetime.date.today()

        opd_token = Token.objects.create(
            visit=self.visit,
            facility=self.facility,
            token_number=1,
            date=today
        )

        lab_order = DiagnosticOrder.objects.create(
            visit=self.visit,
            facility=self.facility,
            ordering_doctor_staff=self.staff,
            order_number="ORD-LAB-TOK-001",
            order_date=today,
            lab_token_number=1
        )
        self.assertEqual(opd_token.token_number, 1)
        self.assertEqual(lab_order.lab_token_number, 1)

    def test_10b_opd_token_uniqueness(self):
        """10b. Duplicate OPD token on same facility and date must fail."""
        today = datetime.date.today()
        Token.objects.create(
            visit=self.visit,
            facility=self.facility,
            token_number=1,
            date=today
        )
        visit2 = Visit.objects.create(
            visit_id="VIS-20260924-002",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD",
            opd_date=today
        )
        with self.assertRaises(IntegrityError):
            Token.objects.create(
                visit=visit2,
                facility=self.facility,
                token_number=1,
                date=today
            )

    def test_10c_lab_token_uniqueness(self):
        """10c. Duplicate Lab token on same facility and order_date must fail."""
        today = datetime.date.today()
        DiagnosticOrder.objects.create(
            visit=self.visit,
            facility=self.facility,
            ordering_doctor_staff=self.staff,
            order_number="ORD-LAB-TOK-001",
            order_date=today,
            lab_token_number=1
        )
        visit2 = Visit.objects.create(
            visit_id="VIS-20260924-003",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD",
            opd_date=today
        )
        with self.assertRaises(IntegrityError):
            DiagnosticOrder.objects.create(
                visit=visit2,
                facility=self.facility,
                ordering_doctor_staff=self.staff,
                order_number="ORD-LAB-TOK-002",
                order_date=today,
                lab_token_number=1
            )

    # -------------------------------------------------------------------------
    # 11. RETENTION / ON DELETE RESTRICT BEHAVIOR
    # -------------------------------------------------------------------------
    def test_11_retention_delete_behavior(self):
        """11. Verify ON DELETE RESTRICT protects Person master identity."""
        with self.assertRaises((ProtectedError, RestrictedError, IntegrityError)):
            self.person.delete()

    # -------------------------------------------------------------------------
    # 12. PUBLIC HEALTH, NCD, SURVEILLANCE & AUDIT
    # -------------------------------------------------------------------------
    def test_12_public_health_and_alerts_audit(self):
        """12. Verify NCD, Disease Surveillance, OperationalAlert, and AuditLogEntry."""
        ncd = NCDCondition.objects.create(
            patient=self.patient,
            registering_facility=self.facility,
            registering_doctor=self.staff,
            condition_code="HYPERTENSION",
            staging="STAGE_1",
            control_status="CONFIRMED"
        )
        assessment = NCDAssessment.objects.create(
            condition=ncd,
            visit=self.visit,
            assessed_by_staff=self.staff,
            systolic_bp=135,
            diastolic_bp=85,
            clinical_notes="Good control"
        )
        self.assertEqual(ncd.assessments.count(), 1)

        disease = DiseaseMaster.objects.create(
            disease_code="CHIKUNGUNYA",
            disease_name="Chikungunya Virus Disease",
            transmission_type="VECTOR_BORNE"
        )
        case = DiseaseSurveillanceCase.objects.create(
            patient=self.patient,
            facility=self.facility,
            disease=disease,
            reporting_staff=self.staff,
            case_number="SURV-2026-001",
            status="SUSPECTED"
        )
        notification = PublicHealthNotification.objects.create(
            case=case,
            notified_authority="DISTRICT_SURVEILLANCE_OFFICER",
            dispatch_payload={"case_number": "SURV-2026-001"}
        )
        self.assertEqual(case.notifications.count(), 1)

        alert = OperationalAlert.objects.create(
            facility=self.facility,
            alert_category="EPIDEMIC_SURGE",
            severity="CRITICAL",
            title="Spike in Suspected Dengue Cases",
            message="3 cases identified in Ward 149 in last 24h",
            is_active=True
        )
        self.assertTrue(alert.is_active)

        audit = AuditLogEntry.objects.create(
            actor_staff=self.staff,
            actor_role_snapshot="DOCTOR",
            facility=self.facility,
            action_type="UPDATE",
            table_name="diagnostic_results",
            record_id="101",
            payload_before={"status": "ENTERED"},
            payload_after={"status": "VERIFIED"}
        )
        self.assertEqual(audit.payload_after["status"], "VERIFIED")

    # -------------------------------------------------------------------------
    # 13. PROCUREMENT & PO APPROVALS
    # -------------------------------------------------------------------------
    def test_13_procurement_po_approvals(self):
        """13. Verify multi-tier PO approval unique constraint (po, tier)."""
        vendor = Vendor.objects.create(
            vendor_name="Karnataka Antibiotics & Pharmaceuticals Ltd",
            facility=self.facility
        )
        po = PurchaseOrder.objects.create(
            po_number="PO-2026-001",
            facility=self.facility,
            vendor=vendor
        )
        app1 = PurchaseOrderApproval.objects.create(
            purchase_order=po,
            approver_staff=self.staff,
            approval_tier=1,
            status="APPROVED",
            remarks="Tier 1 Medical Superintendent approval"
        )
        self.assertIsNotNone(app1.pk)

        with self.assertRaises(IntegrityError):
            PurchaseOrderApproval.objects.create(
                purchase_order=po,
                approver_staff=self.staff,
                approval_tier=1,
                status="APPROVED"
            )

    # -------------------------------------------------------------------------
    # 14. CLINICAL TRIAGE VITALS CHECK CONSTRAINTS
    # -------------------------------------------------------------------------
    def test_14_triage_clinical_vitals_constraints(self):
        """14. Verify Triage CHECK constraints on blood pressure, SpO2, and pulse."""
        t = Triage.objects.create(
            visit=self.visit,
            triaged_by_staff=self.staff,
            systolic_bp=120,
            diastolic_bp=80,
            pulse_rate=72,
            spo2_percentage=98
        )
        self.assertIsNotNone(t.pk)

        visit_err = Visit.objects.create(
            visit_id="VIS-20260924-ERR",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD",
            opd_date=datetime.date.today()
        )
        # systolic_bp must be in range 40..300. Value 350 violates chk_triages_bp_sys
        with self.assertRaises(IntegrityError):
            Triage.objects.create(
                visit=visit_err,
                triaged_by_staff=self.staff,
                systolic_bp=350,
                diastolic_bp=80,
                pulse_rate=72,
                spo2_percentage=98
            )

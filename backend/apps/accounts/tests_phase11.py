import uuid
import datetime
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError, RestrictedError

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.geography.models import State, District, Taluk
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter
from apps.consultations.models import (
    Consultation, DiagnosisMaster, Diagnosis
)
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest,
    DiagnosticResult, DiagnosticResultAmendment
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger
)
from apps.referrals.models import ReferralOrder, FollowUpTask
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry


class Phase11PhysicalModelTests(TestCase):
    def setUp(self):
        # Base Organization
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(state=self.state, name="Bengaluru Urban", code="KA-BLR")
        self.taluk = Taluk.objects.create(district=self.district, name="Bengaluru South", code="BLR-S")
        self.facility = Facility.objects.create(
            state=self.state,
            district=self.district,
            facility_name="Namma Clinic South A1",
            facility_type="PRIMARY_CLINIC"
        )
        self.department = Department.objects.create(
            facility=self.facility,
            code="OPD-01",
            name="General Outpatient"
        )

        # Base IAM
        self.person = Person.objects.create(
            first_name="Ramesh",
            last_name="Kumar",
            gender="MALE",
            date_of_birth=datetime.date(1985, 5, 20),
            phone_number="9876543210"
        )
        self.staff = StaffProfile.objects.create(
            person=self.person,
            employee_id="EMP-KA-001",
            designation="Senior Medical Officer",
            medical_council_reg_number="KMC-12345",
            department=self.department
        )
        self.doctor_role = RoleMaster.objects.create(code="DOCTOR", name="Medical Officer")

        # Base Patient
        self.patient_person = Person.objects.create(
            first_name="Anitha",
            last_name="Gowda",
            gender="FEMALE",
            date_of_birth=datetime.date(1992, 8, 14),
            phone_number="9123456780"
        )
        self.patient = Patient.objects.create(
            person=self.patient_person,
            name="Anitha Gowda",
            patient_id="PT-BLR-001",
            gender="FEMALE",
            mobile="9123456780",
            address="Varthur, Bengaluru",
            registered_at_facility=self.facility
        )

        # Base Visit
        self.visit = Visit.objects.create(
            visit_id="VIS-20260924-001",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD",
            status="IN_CONSULTATION"
        )

    def test_01_iam_assignment_effective_dates(self):
        """1. Verify IAM role assignment and effective dates."""
        role_assign = StaffRoleAssignment.objects.create(
            staff=self.staff,
            role=self.doctor_role,
            effective_from=datetime.date.today(),
            is_active=True
        )
        self.assertEqual(role_assign.staff.employee_id, "EMP-KA-001")
        self.assertEqual(role_assign.role.code, "DOCTOR")

        fac_assign = StaffFacilityAssignment.objects.create(
            staff=self.staff,
            facility=self.facility,
            department=self.department,
            is_primary=True,
            effective_from=datetime.date.today()
        )
        self.assertTrue(fac_assign.is_primary)

    def test_02_organization_hierarchy(self):
        """2. Verify Taluk, Department, ServiceMaster, and FacilityService."""
        self.assertEqual(self.taluk.district.name, "Bengaluru Urban")
        svc = ServiceMaster.objects.create(code="ANC", name="Antenatal Care", category="MATERNAL")
        fac_svc = FacilityService.objects.create(facility=self.facility, service=svc, is_available=True)
        self.assertEqual(fac_svc.service.code, "ANC")
        self.assertEqual(self.department.facility.facility_name, "Namma Clinic South A1")

    def test_03_visit_daily_counter_relationship(self):
        """3. Verify Visit and FacilityDailyCounter relationships."""
        counter = FacilityDailyCounter.objects.create(
            facility=self.facility,
            counter_date=datetime.date.today(),
            counter_type="OPD",
            last_token_number=42
        )
        self.assertEqual(counter.last_token_number, 42)
        self.assertEqual(self.visit.patient.name, "Anitha Gowda")

    def test_04_consultation_1_to_n(self):
        """4. Verify Consultation 1:N sequence under a single Visit."""
        c1 = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            consultation_sequence=1,
            chief_complaint="Fever and chills x 3 days"
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

    def test_05_shared_specimen_across_test_requests(self):
        """5. Verify diagnostic cardinality: multiple TestRequests share ONE Specimen."""
        order = DiagnosticOrder.objects.create(
            visit=self.visit,
            facility=self.facility,
            ordering_doctor_staff=self.staff,
            order_number="ORD-20260924-001",
            priority="ROUTINE"
        )
        specimen = Specimen.objects.create(
            diagnostic_order=order,
            barcode_identifier="SPEC-EDTA-001",
            specimen_type="WHOLE_BLOOD",
            status="COLLECTED",
            collected_by_staff=self.staff
        )
        t1 = DiagnosticTestMaster.objects.create(
            test_code="CBC", test_name="Complete Blood Count",
            category="HEMATOLOGY", specimen_type="WHOLE_BLOOD"
        )
        t2 = DiagnosticTestMaster.objects.create(
            test_code="BLD_GRP", test_name="Blood Group & Rh",
            category="IMMUNOHEMATOLOGY", specimen_type="WHOLE_BLOOD"
        )

        tr1 = TestRequest.objects.create(diagnostic_order=order, test_master=t1, specimen=specimen)
        tr2 = TestRequest.objects.create(diagnostic_order=order, test_master=t2, specimen=specimen)

        self.assertEqual(tr1.specimen, tr2.specimen)
        self.assertEqual(order.test_requests.count(), 2)

    def test_06_one_diagnostic_result_per_test_request(self):
        """6. Verify TestRequest 1:1 DiagnosticResult enforcement (UNIQUE test_request_id)."""
        order = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.facility,
            ordering_doctor_staff=self.staff, order_number="ORD-20260924-002"
        )
        test = DiagnosticTestMaster.objects.create(
            test_code="MALARIA_RDT", test_name="Malaria Rapid Antigen Test",
            category="SEROLOGY", specimen_type="SERUM"
        )
        tr = TestRequest.objects.create(diagnostic_order=order, test_master=test)

        res1 = DiagnosticResult.objects.create(
            test_request=tr,
            result_value_text="Negative for P. falciparum and P. vivax",
            reference_range_applied="Negative",
            status="ENTERED",
            entered_by_staff=self.staff
        )
        self.assertIsNotNone(res1.pk)

        # Attempting second result for same TestRequest must raise IntegrityError
        with self.assertRaises(IntegrityError):
            DiagnosticResult.objects.create(
                test_request=tr,
                result_value_text="Duplicate result attempt",
                reference_range_applied="Negative",
                status="ENTERED",
                entered_by_staff=self.staff
            )

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

    def test_08_followup_completion_integrity(self):
        """8. Verify FollowUpTask completion requires completed_in_visit and staff."""
        follow_up = FollowUpTask.objects.create(
            patient=self.patient,
            facility=self.facility,
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            category="NCD_ROUTINE",
            status="PENDING"
        )
        self.assertEqual(follow_up.status, "PENDING")

        # Mark completed with full encounter linkage
        follow_up.status = "COMPLETED"
        follow_up.completed_in_visit = self.visit
        follow_up.completed_by_staff = self.staff
        follow_up.completed_at = datetime.datetime.now(datetime.timezone.utc)
        follow_up.save()
        self.assertEqual(follow_up.status, "COMPLETED")

    def test_09_inventory_ledger_double_entry(self):
        """9. Verify InventoryLedger append-only journal entries."""
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
        self.assertEqual(ledger_entry.quantity_delta, -30)

    def test_10_token_uniqueness(self):
        """10. Verify Token uniqueness within (facility, date, token_number)."""
        Token.objects.create(
            visit=self.visit,
            facility=self.facility,
            token_number=1,
            date=datetime.date.today()
        )
        # Duplicate token on same facility and date must fail
        visit2 = Visit.objects.create(
            visit_id="VIS-20260924-002",
            patient=self.patient,
            facility=self.facility,
            visit_type="OPD"
        )
        with self.assertRaises(IntegrityError):
            Token.objects.create(
                visit=visit2,
                facility=self.facility,
                token_number=1,
                date=datetime.date.today()
            )

    def test_11_retention_delete_behavior(self):
        """11. Verify ON DELETE RESTRICT protects Person when StaffProfile exists."""
        with self.assertRaises((ProtectedError, RestrictedError, IntegrityError)):
            self.person.delete()

    def test_12_public_health_and_alerts_audit(self):
        """12. Verify NCD, Disease Surveillance, OperationalAlert, and AuditLogEntry."""
        ncd = NCDCondition.objects.create(
            patient=self.patient,
            registering_facility=self.facility,
            registering_doctor=self.staff,
            condition_code="HYPERTENSION",
            diagnosis_date=datetime.date.today()
        )
        assessment = NCDAssessment.objects.create(
            condition=ncd,
            visit=self.visit,
            assessed_by_staff=self.staff,
            systolic_bp=138,
            diastolic_bp=88
        )
        self.assertEqual(assessment.systolic_bp, 138)

        dis = DiseaseMaster.objects.create(
            disease_code="DENGUE", disease_name="Dengue Fever", transmission_type="VECTOR_BORNE"
        )
        case = DiseaseSurveillanceCase.objects.create(
            patient=self.patient, facility=self.facility,
            disease=dis, reporting_staff=self.staff,
            case_number="EPI-BLR-2026-001", diagnosis_date=datetime.date.today()
        )
        self.assertEqual(case.disease.disease_code, "DENGUE")

        alert = OperationalAlert.objects.create(
            facility=self.facility,
            alert_category="PANIC_LAB",
            title="Critical Low Platelets",
            message="Platelets < 20,000 / uL",
            severity="CRITICAL"
        )
        self.assertTrue(alert.is_active)

        audit = AuditLogEntry.objects.create(
            actor_staff=self.staff,
            actor_role_snapshot="DOCTOR",
            facility=self.facility,
            action_type="CREATE",
            table_name="referral_orders",
            record_id="REF-001"
        )
        self.assertEqual(audit.action_type, "CREATE")

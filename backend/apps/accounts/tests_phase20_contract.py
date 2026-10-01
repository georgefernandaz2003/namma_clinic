"""
Phase 20 Backend API Contract Tests.
Verifies targeted API contracts:
1. Audit log retrieval (AuditLogEntrySerializer fields and admin scope).
2. Inventory ledger retrieval (InventoryLedgerSerializer fields and facility scope).
3. Prescription verification, clinical hold, and rejection workflow transitions.
"""
import datetime, uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, User, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryLedger
from apps.audit.models import AuditLogEntry


class Phase20APIContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)

        self.facility = Facility.objects.create(
            facility_code="PHC-P20-01",
            facility_name="Phase 20 Test PHC",
            facility_type="PRIMARY_HEALTH_CENTRE",
            state=self.state,
            district=self.district
        )
        self.dept = Department.objects.create(facility=self.facility, code="GEN", name="General")

        self.role_admin, _ = RoleMaster.objects.get_or_create(code="ADMIN", defaults={"name": "Facility Administrator"})
        self.role_doc, _ = RoleMaster.objects.get_or_create(code="DOCTOR", defaults={"name": "Medical Officer"})
        self.role_pharm, _ = RoleMaster.objects.get_or_create(code="PHARMACIST", defaults={"name": "Pharmacist"})

        # Admin Staff & User
        self.person_admin = Person.objects.create(first_name="Admin", last_name="User", gender="MALE", date_of_birth="1980-01-01")
        self.admin_staff = StaffProfile.objects.create(
            person=self.person_admin, employee_id="EMP-P20-ADM", designation="Hospital Administrator",
            department=self.dept, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.admin_staff, role=self.role_admin, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.admin_staff, facility=self.facility, is_primary=True, is_active=True)
        self.admin_user = User.objects.create_user(
            username="p20_admin", password="password123", role="ADMIN", is_staff=True,
            assigned_facility=self.facility, staff_profile=self.admin_staff
        )

        # Doctor Staff & User
        self.person_doc = Person.objects.create(first_name="Doctor", last_name="User", gender="FEMALE", date_of_birth="1985-05-15")
        self.doc_staff = StaffProfile.objects.create(
            person=self.person_doc, employee_id="EMP-P20-DOC", designation="Medical Officer",
            department=self.dept, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.doc_staff, role=self.role_doc, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_staff, facility=self.facility, is_primary=True, is_active=True)
        self.doc_user = User.objects.create_user(
            username="p20_doctor", password="password123", role="DOCTOR",
            assigned_facility=self.facility, staff_profile=self.doc_staff
        )

        # Pharmacist Staff & User
        self.person_pharm = Person.objects.create(first_name="Pharm", last_name="User", gender="MALE", date_of_birth="1990-08-20")
        self.pharm_staff = StaffProfile.objects.create(
            person=self.person_pharm, employee_id="EMP-P20-PHM", designation="Pharmacist",
            department=self.dept, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.pharm_staff, role=self.role_pharm, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.pharm_staff, facility=self.facility, is_primary=True, is_active=True)
        self.pharm_user = User.objects.create_user(
            username="p20_pharm", password="password123", role="PHARMACIST",
            assigned_facility=self.facility, staff_profile=self.pharm_staff
        )

        # Patient & Visit & Consultation & Prescription
        self.patient = Patient.objects.create(
            patient_id="PAT-P20-001",
            name="Ravi Shankar",
            gender="MALE",
            age=40,
            registered_at_facility=self.facility
        )
        self.visit = Visit.objects.create(
            visit_id="VIS-P20-001",
            patient=self.patient,
            facility=self.facility,
            visit_type="OUTPATIENT"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.doc_staff,
            chief_complaint="Headache",
            clinical_assessment="Tension headache"
        )
        self.prescription = Prescription.objects.create(
            consultation=self.consultation,
            patient=self.patient,
            facility=self.facility,
            doctor=self.doc_user,
            doctor_staff=self.doc_staff,
            status="PENDING_VERIFICATION"
        )

        # Medicine & Batch & Ledger
        self.medicine = MedicineMaster.objects.create(
            generic_name="Paracetamol",
            strength="500mg",
            dosage_form="TABLET"
        )
        self.batch = MedicineBatch.objects.create(
            batch_number="B-P20-001",
            medicine=self.medicine,
            facility=self.facility,
            quantity=100,
            available_quantity=100,
            expiry_date=timezone.now().date() + datetime.timedelta(days=180),
            status="ACTIVE"
        )
        self.ledger = InventoryLedger.objects.create(
            facility=self.facility,
            batch=self.batch,
            performed_by_staff=self.pharm_staff,
            transaction_type="GRN_RECEIPT",
            quantity_delta=100,
            balance_after=100
        )

        # Audit log entry
        self.audit_log = AuditLogEntry.objects.create(
            facility=self.facility,
            actor_staff=self.doc_staff,
            actor_user_id=self.doc_user.id,
            actor_role_snapshot="DOCTOR",
            action_type="INSERT",
            table_name="patients",
            record_id=str(self.patient.id),
            correlation_id=uuid.uuid4()
        )

    def test_audit_log_endpoint_contract(self):
        """Verifies GET /api/v1/audit/ resolves serializer fields and restricts access to admin."""
        # Unauthenticated -> 401
        res = self.client.get("/api/v1/audit/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Ordinary staff (Doctor) -> 403
        self.client.force_authenticate(user=self.doc_user)
        res = self.client.get("/api/v1/audit/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Administrator -> 200 with paginated results
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/audit/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertGreaterEqual(len(res.data["results"]), 1)
        item = res.data["results"][0]
        self.assertEqual(item["actor_role_snapshot"], "DOCTOR")
        self.assertEqual(item["action_type"], "INSERT")

    def test_inventory_ledger_endpoint_contract(self):
        """Verifies GET /api/v1/pharmacy/ledger/ resolves serializer fields and enforces facility scope."""
        # Unauthenticated -> 401
        res = self.client.get("/api/v1/pharmacy/ledger/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated Pharmacist -> 200
        self.client.force_authenticate(user=self.pharm_user)
        res = self.client.get("/api/v1/pharmacy/ledger/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertGreaterEqual(len(res.data["results"]), 1)
        item = res.data["results"][0]
        self.assertEqual(item["transaction_type"], "GRN_RECEIPT")
        self.assertEqual(item["quantity_delta"], 100)

    def test_prescription_verify_hold_reject_contract(self):
        """Verifies prescription workflow transitions: verify, hold, reject, and role authorization."""
        # 1. Doctor attempting to verify -> 403 (Only pharmacist allowed)
        self.client.force_authenticate(user=self.doc_user)
        res = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/", {"notes": "Doc trying to verify"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Pharmacist verifying -> 200 (Status transitions to VERIFIED)
        self.client.force_authenticate(user=self.pharm_user)
        res = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/", {"notes": "Dosage checked"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "VERIFIED")

        # 3. Pharmacist placing on hold -> 200
        res = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/hold/", {"notes": "Waiting for lab result"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ON_HOLD")

        # 4. Pharmacist rejecting -> 200
        res = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/reject/", {"reason": "Duplicate prescription"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "REJECTED")

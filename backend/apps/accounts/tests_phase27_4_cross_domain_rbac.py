import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    User, RoleChoices, RoleMaster, Person,
    StaffProfile, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.accounts.services import seed_roles_and_permissions
from apps.facilities.models import Facility
from apps.geography.models import State, District
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription
from apps.laboratory.models import DiagnosticOrder
from apps.pharmacy.models import MedicineMaster, MedicineBatch, Vendor, PurchaseOrder


class Phase274CrossDomainRBACAuditTests(TestCase):
    """
    Phase 27.4 Cross-Domain RBAC and Privacy Regression Test Suite.
    Validates all 8 operational roles and strict boundary enforcement:
    1. Compounder cannot access clinical EMR.
    2. Nurse cannot perform Compounder registration/queue-authoring actions.
    3. Inventory cannot access clinical pharmacy actions.
    4. Pharmacist cannot perform Inventory administration.
    5. Doctor/Nurse/Compounder/Lab cannot access Inventory administration.
    6. Staff administration cannot be escalated by operational roles.
    7. Multi-role users receive only the union of their assigned permissions.
    8. Inactive/ended assignments immediately lose authorization.
    9. Facility isolation enforced across domains.
    """

    def setUp(self):
        seed_roles_and_permissions()

        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)

        self.facility_1 = Facility.objects.create(
            facility_name="Namma Central PHC",
            facility_code="PHC-BLR-01",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )
        self.facility_2 = Facility.objects.create(
            facility_name="Namma Rural Clinic 2",
            facility_code="PHC-BLR-02",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )

        # Helper to create user with StaffProfile & StaffRoleAssignment
        def make_staff(username, role_code, fac=self.facility_1):
            p = Person.objects.create(
                first_name=username, last_name="User", gender="MALE",
                date_of_birth=datetime.date(1985, 1, 1), phone_number=f"98450{hash(username) % 100000:05d}"
            )
            staff = StaffProfile.objects.create(
                person=p, employee_id=f"STF-{username.upper()[:8]}", designation=role_code, status="ACTIVE"
            )
            u = User.objects.create_user(
                username=username, password="Password123!",
                staff_profile=staff, assigned_facility=fac, role=role_code
            )
            rm = RoleMaster.objects.get(code=role_code)
            StaffRoleAssignment.objects.create(staff=staff, role=rm, facility=fac, is_active=True)
            if fac:
                StaffFacilityAssignment.objects.create(staff=staff, facility=fac, is_primary=True, is_active=True)
            return u, staff

        self.u_dho, self.stf_dho = make_staff("audit_dho", RoleChoices.DISTRICT_OFFICER, fac=None)
        self.u_admin, self.stf_admin = make_staff("audit_admin", RoleChoices.HOSPITAL_ADMIN)
        self.u_doc, self.stf_doc = make_staff("audit_doc", RoleChoices.DOCTOR)
        self.u_nurse, self.stf_nurse = make_staff("audit_nurse", RoleChoices.NURSE)
        self.u_comp, self.stf_comp = make_staff("audit_comp", RoleChoices.FRONT_DESK_OFFICER)
        self.u_lab, self.stf_lab = make_staff("audit_lab", RoleChoices.LAB_TECHNICIAN)
        self.u_phm, self.stf_phm = make_staff("audit_phm", RoleChoices.PHARMACIST)
        self.u_inv, self.stf_inv = make_staff("audit_inv", RoleChoices.INVENTORY)
        self.u_fac2_inv, self.stf_fac2_inv = make_staff("audit_fac2_inv", RoleChoices.INVENTORY, fac=self.facility_2)

        # Dual role: INVENTORY + PHARMACIST
        self.u_dual, self.stf_dual = make_staff("audit_dual", RoleChoices.INVENTORY)
        rm_phm = RoleMaster.objects.get(code=RoleChoices.PHARMACIST)
        StaffRoleAssignment.objects.create(staff=self.stf_dual, role=rm_phm, facility=self.facility_1, is_active=True)

        # Test Domain Entities
        self.patient = Patient.objects.create(
            patient_id="PAT-BLR-001", name="Ravi Kumar", age=35, gender="MALE", registered_at_facility=self.facility_1
        )
        self.visit = Visit.objects.create(
            visit_id="VIS-BLR-001", patient=self.patient, facility=self.facility_1, visit_type="OUTPATIENT"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit, patient=self.patient, facility=self.facility_1, doctor=self.u_doc, doctor_staff=self.stf_doc,
            chief_complaint="Chest congestion", clinical_notes="Prescribing antibiotics"
        )
        self.medicine = MedicineMaster.objects.create(
            generic_name="Amoxicillin", brand_name="Amox-500", strength="500mg", dosage_form="CAPSULE", unit="CAPSULE"
        )
        self.batch = MedicineBatch.objects.create(
            medicine=self.medicine, facility=self.facility_1, batch_number="AMX-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=300),
            quantity=100, available_quantity=100, status="AVAILABLE"
        )
        self.rx = Prescription.objects.create(
            consultation=self.consultation, patient=self.patient, facility=self.facility_1,
            doctor=self.u_doc, doctor_staff=self.stf_doc, status="VERIFIED"
        )

    def test_compounder_cannot_access_clinical_emr(self):
        c = APIClient()
        c.force_authenticate(user=self.u_comp)

        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/clinical/triage/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/pharmacy/prescriptions/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/diagnostics/orders/").status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_cannot_perform_registration_and_queue_authoring(self):
        c = APIClient()
        c.force_authenticate(user=self.u_nurse)

        res_pat = c.post("/api/v1/patients/", {"name": "Unauth", "mobile": "9845011111", "registered_at_facility": self.facility_1.id})
        self.assertEqual(res_pat.status_code, status.HTTP_403_FORBIDDEN)

        res_vis = c.post("/api/v1/visits/", {"patient": self.patient.id, "facility": self.facility_1.id})
        self.assertEqual(res_vis.status_code, status.HTTP_403_FORBIDDEN)

        res_void = c.post("/api/v1/visits/void-token/", {"visit_id": self.visit.id, "reason": "Unauth void"})
        self.assertEqual(res_void.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_cannot_access_clinical_pharmacy_and_diagnostics(self):
        c = APIClient()
        c.force_authenticate(user=self.u_inv)

        self.assertEqual(c.get("/api/v1/pharmacy/prescriptions/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.post(f"/api/v1/pharmacy/prescriptions/{self.rx.id}/verify/", {"notes": "test"}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.post("/api/v1/pharmacy/dispensations/", {"prescription_id": self.rx.id, "facility_id": self.facility_1.id, "items": []}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/diagnostics/orders/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)

    def test_pharmacist_cannot_perform_inventory_administration(self):
        c = APIClient()
        c.force_authenticate(user=self.u_phm)

        self.assertEqual(c.post("/api/v1/procurement/purchase-orders/", {"facility": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.post("/api/v1/procurement/grn/", {"facility_id": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.post(f"/api/v1/pharmacy/batches/{self.batch.id}/adjust/", {"quantity_delta": 5}).status_code, status.HTTP_403_FORBIDDEN)

    def test_clinical_roles_cannot_access_inventory_administration(self):
        for u in [self.u_doc, self.u_nurse, self.u_comp, self.u_lab]:
            c = APIClient()
            c.force_authenticate(user=u)
            self.assertEqual(c.post("/api/v1/procurement/purchase-orders/", {"facility": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.post("/api/v1/procurement/grn/", {"facility_id": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.post(f"/api/v1/pharmacy/batches/{self.batch.id}/adjust/", {"quantity_delta": 5}).status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_administration_escalation_blocked_for_operational_roles(self):
        for u in [self.u_doc, self.u_nurse, self.u_comp, self.u_lab, self.u_phm, self.u_inv]:
            c = APIClient()
            c.force_authenticate(user=u)
            self.assertEqual(c.get("/api/v1/accounts/staff-profiles/").status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.post("/api/v1/accounts/role-assignments/", {"staff": 1, "role": 1, "facility": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)

    def test_multi_role_union_and_strict_boundaries(self):
        c = APIClient()
        c.force_authenticate(user=self.u_dual)

        # Dual INVENTORY + PHARMACIST can access procurement and pharmacy
        self.assertEqual(c.get("/api/v1/procurement/purchase-orders/").status_code, status.HTTP_200_OK)
        self.assertEqual(c.get("/api/v1/pharmacy/prescriptions/").status_code, status.HTTP_200_OK)

        # But CANNOT access doctor consultations or staff administration
        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.get("/api/v1/accounts/staff-profiles/").status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_and_ended_assignments_immediately_lose_authorization(self):
        c = APIClient()
        c.force_authenticate(user=self.u_doc)
        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_200_OK)

        # Deactivate role assignment
        asgn = self.stf_doc.role_assignments.first()
        asgn.is_active = False
        asgn.save()

        # Immediate revocation on safe and mutation endpoints
        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(c.post("/api/v1/clinical/consultations/", {"facility": self.facility_1.id}).status_code, status.HTTP_403_FORBIDDEN)

        # Expired assignment (ended yesterday)
        asgn.is_active = True
        asgn.effective_from = datetime.date.today() - datetime.timedelta(days=10)
        asgn.effective_to = datetime.date.today() - datetime.timedelta(days=1)
        asgn.save()

        self.assertEqual(c.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)

    def test_facility_isolation_enforced_across_domains(self):
        c_fac2 = APIClient()
        c_fac2.force_authenticate(user=self.u_fac2_inv)

        # Facility 2 user cannot access Facility 1 batch
        res_batch = c_fac2.get(f"/api/v1/pharmacy/batches/{self.batch.id}/")
        self.assertIn(res_batch.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Facility 2 user cannot adjust Facility 1 batch
        res_adj = c_fac2.post(f"/api/v1/pharmacy/batches/{self.batch.id}/adjust/", {"quantity_delta": 1})
        self.assertIn(res_adj.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_patient_payload_privacy_verification(self):
        """
        Phase 27.4A: Verify exact payload privacy and role-appropriate boundaries.
        INVENTORY receives NO patient identifiers or clinical data (403 Forbidden).
        Authorized roles receive demographic records without clinical data.
        """
        c_inv = APIClient()
        c_inv.force_authenticate(user=self.u_inv)

        # INVENTORY blocked from patient registry
        res_inv = c_inv.get("/api/v1/patients/")
        self.assertEqual(res_inv.status_code, status.HTTP_403_FORBIDDEN)
        res_inv_alias = c_inv.get("/api/v1/patients/patients/")
        self.assertEqual(res_inv_alias.status_code, status.HTTP_403_FORBIDDEN)

        # Authorized roles can read demographic registry
        for user, role_code in [
            (self.u_doc, "DOCTOR"),
            (self.u_nurse, "NURSE"),
            (self.u_comp, "FRONT_DESK_OFFICER"),
            (self.u_lab, "LAB_TECHNICIAN"),
            (self.u_phm, "PHARMACIST"),
            (self.u_admin, "HOSPITAL_ADMIN"),
        ]:
            c_auth = APIClient()
            c_auth.force_authenticate(user=user)
            res = c_auth.get("/api/v1/patients/")
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Failed for {role_code}")
            data = res.json()
            items = data.get("results", data) if isinstance(data, dict) else data
            self.assertTrue(len(items) > 0)
            first = items[0]
            # Verify patient demographic fields
            self.assertIn("patient_id", first)
            self.assertIn("name", first)
            # Verify ZERO clinical data leakage in patient payload
            self.assertNotIn("diagnosis", first)
            self.assertNotIn("vitals", first)
            self.assertNotIn("clinical_notes", first)
            self.assertNotIn("prescription", first)

        # Verify clinical EMR boundary: Compounder & Pharmacist strictly denied consultation notes
        c_comp = APIClient()
        c_comp.force_authenticate(user=self.u_comp)
        self.assertEqual(c_comp.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)

        c_phm = APIClient()
        c_phm.force_authenticate(user=self.u_phm)
        self.assertEqual(c_phm.get("/api/v1/clinical/consultations/").status_code, status.HTTP_403_FORBIDDEN)

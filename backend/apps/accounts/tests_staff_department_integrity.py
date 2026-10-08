# Phase 37 - Staff -> Department Integrity Hardening Tests

import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment,
    StaffFacilityAssignment, StaffStatusChoices
)
from apps.accounts.services import (
    validate_staff_department_assignment, invite_staff, assign_facility, transfer_staff
)
from apps.common.exceptions import DomainValidationError, UnauthorizedDomainAction
from apps.geography.models import State, District
from apps.facilities.models import Facility, Department


class StaffDepartmentIntegrityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Geography
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.dist1 = District.objects.create(name="District Central", code="DIST-C", state=self.state)
        self.dist2 = District.objects.create(name="District North", code="DIST-N", state=self.state)

        # Facilities
        self.facility_a = Facility.objects.create(
            facility_code="FAC-A",
            facility_name="Clinic Alpha",
            state=self.state,
            district=self.dist1
        )
        self.facility_b = Facility.objects.create(
            facility_code="FAC-B",
            facility_name="Clinic Beta",
            state=self.state,
            district=self.dist1
        )
        self.facility_c_foreign_dist = Facility.objects.create(
            facility_code="FAC-C",
            facility_name="Clinic Gamma Foreign",
            state=self.state,
            district=self.dist2
        )

        # Active & Inactive Departments for Facility A
        self.dept_a_opd = Department.objects.create(
            facility=self.facility_a,
            code="OPD",
            name="General OPD Alpha",
            is_active=True
        )
        self.dept_a_pharm = Department.objects.create(
            facility=self.facility_a,
            code="PHARM",
            name="Pharmacy Alpha",
            is_active=True
        )
        self.dept_a_inactive = Department.objects.create(
            facility=self.facility_a,
            code="INACT",
            name="Inactive Department Alpha",
            is_active=False
        )

        # Active & Inactive Departments for Facility B
        self.dept_b_opd = Department.objects.create(
            facility=self.facility_b,
            code="OPD",
            name="General OPD Beta",
            is_active=True
        )
        self.dept_b_lab = Department.objects.create(
            facility=self.facility_b,
            code="LAB",
            name="Laboratory Beta",
            is_active=True
        )
        self.dept_b_inactive = Department.objects.create(
            facility=self.facility_b,
            code="INACT",
            name="Inactive Department Beta",
            is_active=False
        )

        # Roles
        self.role_admin = RoleMaster.objects.get_or_create(code="HOSPITAL_ADMIN", defaults={"name": "Hospital Admin", "category": "ADMINISTRATIVE"})[0]
        self.role_dho = RoleMaster.objects.get_or_create(code="DISTRICT_OFFICER", defaults={"name": "District Officer", "category": "ADMINISTRATIVE"})[0]
        self.role_doctor = RoleMaster.objects.get_or_create(code="DOCTOR", defaults={"name": "Doctor", "category": "CLINICAL"})[0]
        self.role_pharmacist = RoleMaster.objects.get_or_create(code="PHARMACIST", defaults={"name": "Pharmacist", "category": "CLINICAL"})[0]
        self.role_lab = RoleMaster.objects.get_or_create(code="LAB_TECHNICIAN", defaults={"name": "Lab Technician", "category": "CLINICAL"})[0]

        # Hospital Admin for Facility A
        self.person_ha = Person.objects.create(first_name="Admin", last_name="Alpha", date_of_birth="1980-01-01", gender="MALE")
        self.staff_ha = StaffProfile.objects.create(person=self.person_ha, employee_id="EMP-HA-A", designation="Clinic Admin", status="ACTIVE")
        self.user_ha = User.objects.create_user(
            username="admin_alpha",
            password="AdminPassword123!",
            role="HOSPITAL_ADMIN",
            assigned_facility=self.facility_a,
            staff_profile=self.staff_ha
        )
        StaffRoleAssignment.objects.create(staff=self.staff_ha, role=self.role_admin, effective_from=datetime.date.today(), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_ha, facility=self.facility_a, is_primary=True, effective_from=datetime.date.today(), is_active=True)

        # DHO for District 1
        self.person_dho = Person.objects.create(first_name="Officer", last_name="District", date_of_birth="1975-01-01", gender="MALE")
        self.staff_dho = StaffProfile.objects.create(person=self.person_dho, employee_id="EMP-DHO-1", designation="District Officer", status="ACTIVE")
        self.user_dho = User.objects.create_user(
            username="dho_dist1",
            password="DhoPassword123!",
            role="DISTRICT_OFFICER",
            assigned_district=self.dist1,
            staff_profile=self.staff_dho
        )
        StaffRoleAssignment.objects.create(staff=self.staff_dho, role=self.role_dho, effective_from=datetime.date.today(), is_active=True)

        # Existing Doctor in Facility A
        self.person_doc = Person.objects.create(first_name="Doctor", last_name="One", date_of_birth="1985-01-01", gender="FEMALE")
        self.staff_doc = StaffProfile.objects.create(person=self.person_doc, employee_id="EMP-DOC-A", designation="Medical Officer", status="ACTIVE", department=self.dept_a_opd)
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=self.role_doctor, effective_from=datetime.date.today(), is_active=True)
        self.fa_doc = StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, department=self.dept_a_opd, is_primary=True, effective_from=datetime.date.today(), is_active=True)

    # -------------------------------------------------------------------------
    # 1. Staff Invitation Integrity Tests
    # -------------------------------------------------------------------------
    def test_invite_staff_cross_facility_department_rejected_400(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "first_name": "Ravi",
            "last_name": "Kumar",
            "gender": "MALE",
            "date_of_birth": "1992-05-10",
            "employee_id": "EMP-INV-X1",
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": self.facility_a.id,
            "department_id": self.dept_b_lab.id,  # Department of Facility B!
            "password": "ValidPassword123!"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong to facility", str(res.data))

    def test_invite_staff_inactive_department_rejected_400(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "first_name": "Ravi",
            "last_name": "Kumar",
            "gender": "MALE",
            "date_of_birth": "1992-05-10",
            "employee_id": "EMP-INV-X2",
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": self.facility_a.id,
            "department_id": self.dept_a_inactive.id,  # Inactive department
            "password": "ValidPassword123!"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactive department", str(res.data))

    def test_invite_staff_valid_assignment_syncs_staff_profile_department_201(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "first_name": "Lakshmi",
            "last_name": "Devi",
            "gender": "FEMALE",
            "date_of_birth": "1991-03-15",
            "employee_id": "EMP-INV-OK1",
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": self.facility_a.id,
            "department_id": self.dept_a_pharm.id,
            "password": "ValidPassword123!"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        stf = StaffProfile.objects.get(employee_id="EMP-INV-OK1")
        pfa = StaffFacilityAssignment.objects.get(staff=stf, is_primary=True)
        self.assertEqual(pfa.facility_id, self.facility_a.id)
        self.assertEqual(pfa.department_id, self.dept_a_pharm.id)
        # Verify StaffProfile.department is in sync
        self.assertEqual(stf.department_id, self.dept_a_pharm.id)

    # -------------------------------------------------------------------------
    # 2. Facility Assignment Endpoint Integrity Tests
    # -------------------------------------------------------------------------
    def test_assign_facility_action_cross_facility_department_rejected_400(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "facility_id": self.facility_a.id,
            "department_id": self.dept_b_opd.id,  # Dept from Beta
            "is_primary": True
        }
        res = self.client.post(f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/assign-facility/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong to facility", str(res.data))

    def test_assign_facility_action_inactive_department_rejected_400(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "facility_id": self.facility_a.id,
            "department_id": self.dept_a_inactive.id,
            "is_primary": True
        }
        res = self.client.post(f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/assign-facility/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactive department", str(res.data))

    def test_direct_facility_assignment_cross_facility_rejected_400(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "staff": self.staff_doc.id,
            "facility": self.facility_a.id,
            "department": self.dept_b_lab.id,  # Dept from Beta
            "is_primary": True,
            "effective_from": str(datetime.date.today())
        }
        res = self.client.post("/api/v1/accounts/facility-assignments/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong to facility", str(res.data))

    # -------------------------------------------------------------------------
    # 3. Transfer Endpoint Integrity Tests
    # -------------------------------------------------------------------------
    def test_transfer_staff_cross_facility_department_rejected_400(self):
        # DHO initiates transfer
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "new_facility_id": self.facility_b.id,
            "new_department_id": self.dept_a_pharm.id,  # Belongs to Alpha, not Beta!
            "effective_date": str(datetime.date.today())
        }
        res = self.client.post(f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/transfer/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong to target facility", str(res.data))

    def test_transfer_staff_inactive_department_rejected_400(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "new_facility_id": self.facility_b.id,
            "new_department_id": self.dept_b_inactive.id,  # Inactive in Beta
            "effective_date": str(datetime.date.today())
        }
        res = self.client.post(f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/transfer/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactive department", str(res.data))

    def test_transfer_staff_valid_assignment_syncs_staff_profile_department_200(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "new_facility_id": self.facility_b.id,
            "new_department_id": self.dept_b_opd.id,
            "effective_date": str(datetime.date.today())
        }
        res = self.client.post(f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/transfer/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.staff_doc.refresh_from_db()
        pfa = self.staff_doc.facility_assignments.get(is_primary=True, is_active=True)
        self.assertEqual(pfa.facility_id, self.facility_b.id)
        self.assertEqual(pfa.department_id, self.dept_b_opd.id)
        self.assertEqual(self.staff_doc.department_id, self.dept_b_opd.id)

    # -------------------------------------------------------------------------
    # 4. Scope Authorization Tests (Hospital Admin & DHO)
    # -------------------------------------------------------------------------
    def test_hospital_admin_cannot_administer_foreign_facility_403(self):
        self.client.force_authenticate(user=self.user_ha)
        payload = {
            "first_name": "Intruder",
            "last_name": "Staff",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "employee_id": "EMP-FOREIGN-1",
            "designation": "Doctor",
            "role_code": "DOCTOR",
            "facility_id": self.facility_b.id,  # Facility Beta outside HA Alpha's scope
            "department_id": self.dept_b_opd.id,
            "password": "ValidPassword123!"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Clinic Admin of facility", str(res.data))

    def test_dho_cannot_administer_foreign_district_facility_403(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "first_name": "Foreign",
            "last_name": "Doc",
            "gender": "MALE",
            "date_of_birth": "1988-02-02",
            "employee_id": "EMP-FDIST-1",
            "designation": "Doctor",
            "role_code": "DOCTOR",
            "facility_id": self.facility_c_foreign_dist.id,  # Outside DHO's district!
            "password": "ValidPassword123!"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("District Officer cannot administer facility", str(res.data))

    # -------------------------------------------------------------------------
    # 5. Direct Domain Service Bypass Tests
    # -------------------------------------------------------------------------
    def test_domain_service_validate_staff_department_assignment_checks(self):
        # 1. Cross-facility department raises DomainValidationError
        with self.assertRaises(DomainValidationError) as ctx:
            validate_staff_department_assignment(self.facility_a, self.dept_b_opd)
        self.assertEqual(ctx.exception.code, "CROSS_FACILITY_DEPARTMENT")

        # 2. Inactive department raises DomainValidationError
        with self.assertRaises(DomainValidationError) as ctx:
            validate_staff_department_assignment(self.facility_a, self.dept_a_inactive)
        self.assertEqual(ctx.exception.code, "INACTIVE_DEPARTMENT")

        # 3. None department passes cleanly
        validate_staff_department_assignment(self.facility_a, None)

        # 4. Valid matching active department passes cleanly
        validate_staff_department_assignment(self.facility_a, self.dept_a_opd)

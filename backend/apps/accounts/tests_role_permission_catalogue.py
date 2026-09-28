"""
Role & Permission Catalogue Test Suite.
Verifies the 14 IAM Authorization Source-of-Truth Hardening requirements:
1. RoleMaster/RolePermission is authoritative.
2. User.role alone cannot grant a permission absent from the catalogue.
3. Inactive RoleMaster denies permission.
4. Inactive PermissionMaster denies permission.
5. Inactive RolePermission denies permission.
6. Existing seven roles remain intact.
7. No SYSTEM_ADMIN operational role exists.
8. No NURSE_COMPOUNDER role exists.
9. Compounder still has exactly the approved seven permissions.
10. Nurse does not gain Compounder registration permissions.
11. DHO NULL district fails closed.
12. Facility scope remains enforced.
13. Operational roles cannot mutate catalogue definitions.
14. Existing approved authorization tests continue to pass (including Multi-Role union resolution).
"""
from django.test import TestCase
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status
import datetime

from apps.accounts.models import (
    User, RoleChoices, ScopeLevelChoices, Person, StaffProfile,
    RoleMaster, PermissionMaster, RolePermission, StaffRoleAssignment
)
from apps.accounts.constants import (
    SEEDED_ROLES, SEEDED_PERMISSIONS, ROLE_PERMISSION_MAP,
    generate_role_permission_matrix
)
from apps.accounts.services import seed_roles_and_permissions
from apps.accounts.permissions import (
    has_role_permission, can_access_facility, get_accessible_facility_ids_for_user,
    get_user_role_permissions, get_user_active_role_codes
)
from apps.facilities.models import Facility
from apps.geography.models import State, District


class RolePermissionCatalogueHardeningTests(TestCase):
    """
    Comprehensive verification of the 14 IAM Source of Truth Hardening points.
    """

    def setUp(self):
        self.client = APIClient()
        # Seed catalogue
        seed_roles_and_permissions()

        # Geography & Facilities
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.other_district = District.objects.create(name="Mysuru", code="KA-MYS", state=self.state)

        self.clinic = Facility.objects.create(
            facility_code="PHC-TEST-01",
            facility_name="Namma Clinic Test",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )
        self.other_clinic = Facility.objects.create(
            facility_code="PHC-TEST-02",
            facility_name="Other Clinic Test",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.other_district,
            state=self.state
        )

        # Operational Users for each of the 7 roles
        self.user_dho = User.objects.create_user(
            username="test_dho", password="password123",
            role=RoleChoices.DISTRICT_OFFICER, assigned_district=self.district
        )
        self.user_hospital_admin = User.objects.create_user(
            username="test_hosp_admin", password="password123",
            role=RoleChoices.HOSPITAL_ADMIN, assigned_facility=self.clinic
        )
        self.user_doctor = User.objects.create_user(
            username="test_doc", password="password123",
            role=RoleChoices.DOCTOR, assigned_facility=self.clinic
        )
        self.user_nurse = User.objects.create_user(
            username="test_nurse", password="password123",
            role=RoleChoices.NURSE, assigned_facility=self.clinic
        )
        self.user_compounder = User.objects.create_user(
            username="test_compounder", password="password123",
            role=RoleChoices.COMPOUNDER, assigned_facility=self.clinic
        )
        self.user_lab_tech = User.objects.create_user(
            username="test_lab", password="password123",
            role=RoleChoices.LAB_TECHNICIAN, assigned_facility=self.clinic
        )
        self.user_pharmacist = User.objects.create_user(
            username="test_pharm", password="password123",
            role=RoleChoices.PHARMACIST, assigned_facility=self.clinic
        )

        # Django Superuser (trusted system administrator)
        self.superuser = User.objects.create_superuser(
            username="system_admin", password="password123", email="sysadmin@example.com"
        )

    # 1. RoleMaster/RolePermission is authoritative
    def test_01_rolemaster_rolepermission_is_authoritative(self):
        doc_perms = get_user_role_permissions(self.user_doctor)
        self.assertTrue(len(doc_perms) > 0)
        # Verify permissions come from RolePermission table
        db_doc_perms = set(RolePermission.objects.filter(
            role__code="DOCTOR", is_active=True, permission__is_active=True, role__is_active=True
        ).values_list('permission__code', flat=True))
        self.assertEqual(doc_perms, db_doc_perms)

    # 2. User.role alone cannot grant a permission absent from the catalogue
    def test_02_user_role_alone_cannot_grant_permission_absent_from_catalogue(self):
        # DOCTOR does not have staff.create in RolePermission
        self.assertFalse(has_role_permission(self.user_doctor, "staff.create"))
        self.assertFalse(has_role_permission(self.user_doctor, "arbitrary.unseeded_perm"))

        # User with role that has NO RoleMaster entry
        rogue_user = User.objects.create_user(
            username="rogue_user", role="NONEXISTENT_ROLE"
        )
        self.assertEqual(get_user_role_permissions(rogue_user), set())
        self.assertFalse(has_role_permission(rogue_user, "patients.read"))

    # 3. Inactive RoleMaster denies permission
    def test_03_inactive_rolemaster_denies_permission(self):
        role_doc = RoleMaster.objects.get(code="DOCTOR")
        self.assertTrue(has_role_permission(self.user_doctor, "consultation.create"))

        # Deactivate RoleMaster
        role_doc.is_active = False
        role_doc.save()

        # Doctor must now be denied all permissions
        self.assertFalse(has_role_permission(self.user_doctor, "consultation.create"))
        self.assertFalse(has_role_permission(self.user_doctor, "patients.read"))
        self.assertEqual(get_user_role_permissions(self.user_doctor), set())

        # Reactivate
        role_doc.is_active = True
        role_doc.save()
        self.assertTrue(has_role_permission(self.user_doctor, "consultation.create"))

    # 4. Inactive PermissionMaster denies permission
    def test_04_inactive_permissionmaster_denies_permission(self):
        perm_rx = PermissionMaster.objects.get(code="prescription.create")
        self.assertTrue(has_role_permission(self.user_doctor, "prescription.create"))

        # Deactivate PermissionMaster
        perm_rx.is_active = False
        perm_rx.save()

        # Doctor must now be denied this specific permission
        self.assertFalse(has_role_permission(self.user_doctor, "prescription.create"))
        # But doctor retains other active permissions
        self.assertTrue(has_role_permission(self.user_doctor, "consultation.create"))

        # Reactivate
        perm_rx.is_active = True
        perm_rx.save()
        self.assertTrue(has_role_permission(self.user_doctor, "prescription.create"))

    # 5. Inactive RolePermission denies permission
    def test_05_inactive_rolepermission_denies_permission(self):
        mapping = RolePermission.objects.get(
            role__code="DOCTOR", permission__code="lab_order.create"
        )
        self.assertTrue(has_role_permission(self.user_doctor, "lab_order.create"))

        # Deactivate the RolePermission mapping
        mapping.is_active = False
        mapping.save()

        self.assertFalse(has_role_permission(self.user_doctor, "lab_order.create"))
        # Other mappings remain active
        self.assertTrue(has_role_permission(self.user_doctor, "consultation.create"))

        # Reactivate
        mapping.is_active = True
        mapping.save()
        self.assertTrue(has_role_permission(self.user_doctor, "lab_order.create"))

    # 6. Existing seven roles remain intact
    def test_06_existing_seven_roles_remain_intact(self):
        expected_roles = {
            "DISTRICT_OFFICER", "HOSPITAL_ADMIN", "DOCTOR",
            "NURSE", "COMPOUNDER", "LAB_TECHNICIAN", "PHARMACIST"
        }
        roles = set(RoleMaster.objects.values_list('code', flat=True))
        self.assertEqual(roles, expected_roles)
        self.assertEqual(RoleMaster.objects.count(), 7)

    # 7. No SYSTEM_ADMIN operational role exists
    def test_07_no_system_admin_operational_role(self):
        self.assertFalse(RoleMaster.objects.filter(code="SYSTEM_ADMIN").exists())
        self.assertFalse(RoleMaster.objects.filter(code="SUPER_ADMIN").exists())
        self.assertNotIn("SYSTEM_ADMIN", [c[0] for c in RoleChoices.choices])
        self.assertNotIn("SUPER_ADMIN", [c[0] for c in RoleChoices.choices])

    # 8. No NURSE_COMPOUNDER role exists
    def test_08_no_nurse_compounder_role(self):
        self.assertFalse(RoleMaster.objects.filter(code="NURSE_COMPOUNDER").exists())
        self.assertFalse(RoleMaster.objects.filter(code="CLINIC_ADMIN").exists())
        self.assertNotIn("NURSE_COMPOUNDER", [c[0] for c in RoleChoices.choices])
        self.assertNotIn("CLINIC_ADMIN", [c[0] for c in RoleChoices.choices])

    # 9. Compounder still has exactly the approved seven permissions
    def test_09_compounder_has_exactly_approved_seven_permissions(self):
        compounder_perms = set(RolePermission.objects.filter(
            role__code="COMPOUNDER", is_active=True
        ).values_list('permission__code', flat=True))

        expected = {
            "patients.read", "patients.create", "patients.update_demographics",
            "queue.view", "queue.create", "queue.issue_token", "queue.void"
        }
        self.assertEqual(compounder_perms, expected)

        # Prohibited domains for Compounder
        prohibited = [
            "vitals.create", "vitals.update", "triage.create", "triage.update",
            "consultation.create", "diagnosis.create", "prescription.create",
            "lab_result.create", "specimen.collect", "inventory.adjust",
            "dispensation.create", "purchase_order.create", "staff.create",
            "facility.create", "audit.read"
        ]
        for p in prohibited:
            self.assertFalse(has_role_permission(self.user_compounder, p))

    # 10. Nurse does not gain Compounder registration permissions
    def test_10_nurse_does_not_gain_compounder_registration_permissions(self):
        nurse_perms = get_user_role_permissions(self.user_nurse)

        # Strictly denied registration & token capabilities
        self.assertNotIn("patients.create", nurse_perms)
        self.assertNotIn("patients.update_demographics", nurse_perms)
        self.assertNotIn("queue.create", nurse_perms)
        self.assertNotIn("queue.issue_token", nurse_perms)
        self.assertNotIn("queue.void", nurse_perms)

        self.assertFalse(has_role_permission(self.user_nurse, "patients.create"))
        self.assertFalse(has_role_permission(self.user_nurse, "queue.create"))

        # Retains clinical/triage permissions
        self.assertTrue(has_role_permission(self.user_nurse, "vitals.create"))
        self.assertTrue(has_role_permission(self.user_nurse, "triage.create"))
        self.assertTrue(has_role_permission(self.user_nurse, "patients.read"))

    # 11. DHO NULL district fails closed
    def test_11_dho_null_district_fails_closed(self):
        unassigned_dho = User.objects.create_user(
            username="unassigned_dho", role="DISTRICT_OFFICER", assigned_district=None
        )
        self.assertEqual(get_accessible_facility_ids_for_user(unassigned_dho), [])
        self.assertFalse(can_access_facility(unassigned_dho, self.clinic.id))

        # Assigned DHO can access facility in their district, but not outside
        self.assertTrue(can_access_facility(self.user_dho, self.clinic.id))
        self.assertFalse(can_access_facility(self.user_dho, self.other_clinic.id))

    # 12. Facility scope remains enforced
    def test_12_facility_scope_remains_enforced(self):
        # Doctor scoped to self.clinic cannot access self.other_clinic
        self.assertTrue(can_access_facility(self.user_doctor, self.clinic.id))
        self.assertFalse(can_access_facility(self.user_doctor, self.other_clinic.id))

        # Nurse scoped to self.clinic cannot access self.other_clinic
        self.assertTrue(can_access_facility(self.user_nurse, self.clinic.id))
        self.assertFalse(can_access_facility(self.user_nurse, self.other_clinic.id))

        # Pharmacist scoped to self.clinic cannot access self.other_clinic
        self.assertTrue(can_access_facility(self.user_pharmacist, self.clinic.id))
        self.assertFalse(can_access_facility(self.user_pharmacist, self.other_clinic.id))

    # 13. Operational roles cannot mutate catalogue definitions
    def test_13_operational_roles_cannot_mutate_catalogue_definitions(self):
        operational_users = [
            self.user_dho, self.user_hospital_admin, self.user_doctor,
            self.user_nurse, self.user_compounder, self.user_lab_tech, self.user_pharmacist
        ]
        role = RoleMaster.objects.first()
        perm = PermissionMaster.objects.first()

        for u in operational_users:
            self.client.force_authenticate(user=u)
            # Create role attempt
            res = self.client.post('/api/v1/accounts/roles/', {'code': 'HACK_ROLE', 'name': 'Hack'})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
            # Modify role attempt
            res = self.client.patch(f'/api/v1/accounts/roles/{role.id}/', {'name': 'Altered'})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
            # Modify perm attempt
            res = self.client.patch(f'/api/v1/accounts/permissions/{perm.id}/', {'name': 'Altered'})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Superuser IS permitted
        self.client.force_authenticate(user=self.superuser)
        res_ok = self.client.post('/api/v1/accounts/roles/', {
            'code': 'SYS_TEMP_ROLE', 'name': 'Sys Role', 'scope_level': 'GLOBAL'
        })
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)

    # 14. Existing approved authorization tests continue to pass and Multi-Role readiness
    def test_14_multi_role_readiness_and_matrix_completeness(self):
        # 1. Multi-role resolution: User with StaffProfile having both NURSE and COMPOUNDER roles
        person = Person.objects.create(
            first_name="Radha", last_name="Sharma", gender="FEMALE",
            date_of_birth=datetime.date(1992, 5, 10), phone_number="9876500001"
        )
        staff_prof = StaffProfile.objects.create(
            person=person, employee_id="STF-MULTI-01", designation="Staff Nurse & Compounder", status="ACTIVE"
        )
        multi_user = User.objects.create_user(
            username="multi_role_staff", password="password123",
            staff_profile=staff_prof, assigned_facility=self.clinic, role=""
        )

        role_nurse = RoleMaster.objects.get(code="NURSE")
        role_compounder = RoleMaster.objects.get(code="COMPOUNDER")

        StaffRoleAssignment.objects.create(
            staff=staff_prof, role=role_nurse, is_active=True
        )
        StaffRoleAssignment.objects.create(
            staff=staff_prof, role=role_compounder, is_active=True
        )

        # Active role codes must reflect both roles
        active_roles = get_user_active_role_codes(multi_user)
        self.assertEqual(active_roles, {"NURSE", "COMPOUNDER"})

        # Multi-role user has UNION of both roles
        # From NURSE: vitals.create
        self.assertTrue(has_role_permission(multi_user, "vitals.create"))
        # From COMPOUNDER: patients.create
        self.assertTrue(has_role_permission(multi_user, "patients.create"))
        # Prohibited for both: consultation.create
        self.assertFalse(has_role_permission(multi_user, "consultation.create"))

        # 2. Complete explicit matrix generation (399 cells)
        matrix = generate_role_permission_matrix()
        self.assertEqual(len(matrix), 7 * 57)
        for cell in matrix:
            self.assertIn(cell["access"], ["ALLOW", "DENY"])
            self.assertTrue(bool(cell["reason"]))

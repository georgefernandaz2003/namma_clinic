"""
Role & Permission Catalogue Test Suite.
Verifies the 18 specific requirements for the normalized database-backed
Role and Permission catalogue for Namma Clinic.
"""
from django.test import TestCase
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    User, RoleChoices, ScopeLevelChoices,
    RoleMaster, PermissionMaster, RolePermission
)
from apps.accounts.constants import (
    SEEDED_ROLES, SEEDED_PERMISSIONS, ROLE_PERMISSION_MAP,
    generate_role_permission_matrix
)
from apps.accounts.services import seed_roles_and_permissions
from apps.accounts.permissions import has_role_permission, can_access_facility, get_accessible_facility_ids_for_user
from apps.facilities.models import Facility
from apps.geography.models import State, District


class RolePermissionCatalogueTestSuite(TestCase):
    """
    Comprehensive verification covering requirements 1 through 18.
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

    # 1. Seven roles exist
    def test_01_seven_roles_exist(self):
        expected_roles = {
            "DISTRICT_OFFICER", "HOSPITAL_ADMIN", "DOCTOR",
            "NURSE", "COMPOUNDER", "LAB_TECHNICIAN", "PHARMACIST"
        }
        roles = set(RoleMaster.objects.values_list('code', flat=True))
        self.assertEqual(roles, expected_roles)
        self.assertEqual(RoleMaster.objects.count(), 7)

    # 2. No SYSTEM_ADMIN operational role exists
    def test_02_no_system_admin_operational_role(self):
        self.assertFalse(RoleMaster.objects.filter(code="SYSTEM_ADMIN").exists())
        self.assertFalse(RoleMaster.objects.filter(code="SUPER_ADMIN").exists())
        self.assertNotIn("SYSTEM_ADMIN", [c[0] for c in RoleChoices.choices])
        self.assertNotIn("SUPER_ADMIN", [c[0] for c in RoleChoices.choices])

    # 3. No NURSE_COMPOUNDER role exists
    def test_03_no_nurse_compounder_role(self):
        self.assertFalse(RoleMaster.objects.filter(code="NURSE_COMPOUNDER").exists())
        self.assertFalse(RoleMaster.objects.filter(code="CLINIC_ADMIN").exists())
        self.assertNotIn("NURSE_COMPOUNDER", [c[0] for c in RoleChoices.choices])
        self.assertNotIn("CLINIC_ADMIN", [c[0] for c in RoleChoices.choices])

    # 4. Role codes are unique
    def test_04_role_codes_unique(self):
        codes = list(RoleMaster.objects.values_list('code', flat=True))
        self.assertEqual(len(codes), len(set(codes)))
        with self.assertRaises(IntegrityError):
            RoleMaster.objects.create(code="DOCTOR", name="Duplicate Doctor")

    # 5. Permission codes are unique
    def test_05_permission_codes_unique(self):
        codes = list(PermissionMaster.objects.values_list('code', flat=True))
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(codes), 57)
        with self.assertRaises(IntegrityError):
            PermissionMaster.objects.create(code="patients.read", name="Duplicate Perm", domain="PATIENT", action="read")

    # 6. RolePermission pairs are unique
    def test_06_role_permission_pairs_unique(self):
        pairs = list(RolePermission.objects.values_list('role_id', 'permission_id'))
        self.assertEqual(len(pairs), len(set(pairs)))
        first = RolePermission.objects.first()
        with self.assertRaises(IntegrityError):
            RolePermission.objects.create(role=first.role, permission=first.permission)

    # 7. Seed is idempotent
    def test_07_seed_is_idempotent(self):
        initial_roles = RoleMaster.objects.count()
        initial_perms = PermissionMaster.objects.count()
        initial_mappings = RolePermission.objects.count()

        result = seed_roles_and_permissions()
        self.assertEqual(result["roles_created"], 0)
        self.assertEqual(result["perms_created"], 0)
        self.assertEqual(result["mappings_created"], 0)

        self.assertEqual(RoleMaster.objects.count(), initial_roles)
        self.assertEqual(PermissionMaster.objects.count(), initial_perms)
        self.assertEqual(RolePermission.objects.count(), initial_mappings)

    # 8. Compounder permission set is correct
    def test_08_compounder_permission_set_correct(self):
        compounder_perms = set(RolePermission.objects.filter(
            role__code="COMPOUNDER", is_active=True
        ).values_list('permission__code', flat=True))

        expected = {
            "patients.read", "patients.create", "patients.update_demographics",
            "queue.view", "queue.create", "queue.issue_token", "queue.void"
        }
        self.assertEqual(compounder_perms, expected)

        # Explicit negative verification
        prohibited_domains = ["vitals", "triage", "consultation", "diagnosis", "prescription",
                              "lab_result", "specimen", "inventory", "dispensation", "purchase_order", "staff", "facility"]
        for perm in compounder_perms:
            domain = perm.split('.')[0]
            self.assertNotIn(domain, prohibited_domains)
        self.assertNotIn("audit.read", compounder_perms)

    # 9. Nurse baseline permission set is correct
    def test_09_nurse_baseline_permission_set_correct(self):
        nurse_perms = set(RolePermission.objects.filter(
            role__code="NURSE", is_active=True
        ).values_list('permission__code', flat=True))

        # Explicit exclusions
        self.assertNotIn("patients.create", nurse_perms)
        self.assertNotIn("patients.update_demographics", nurse_perms)
        self.assertNotIn("queue.create", nurse_perms)
        self.assertNotIn("queue.issue_token", nurse_perms)

        # Baseline inclusions
        expected_subset = {
            "patients.read", "queue.view", "queue.call_next", "queue.transition",
            "vitals.create", "vitals.update", "triage.create", "triage.update",
            "consultation.read", "diagnosis.read", "prescription.read",
            "lab_order.read", "lab_result.read", "specimen.collect", "medicine_batch.read"
        }
        self.assertEqual(nurse_perms, expected_subset)

    # 10. Doctor permission set is correct
    def test_10_doctor_permission_set_correct(self):
        doc_perms = set(RolePermission.objects.filter(
            role__code="DOCTOR", is_active=True
        ).values_list('permission__code', flat=True))

        required = {
            "patients.read", "consultation.create", "consultation.read", "consultation.update",
            "diagnosis.create", "diagnosis.read", "diagnosis.update",
            "prescription.create", "prescription.read", "prescription.update",
            "lab_order.create", "lab_order.read", "lab_result.read", "lab_result.verify",
            "medicine_batch.read"
        }
        self.assertTrue(required.issubset(doc_perms))

        # Doctors cannot administer staff, facilities, procurement, or dispensing
        for p in doc_perms:
            self.assertFalse(p.startswith("staff."))
            self.assertFalse(p.startswith("facility."))
            self.assertFalse(p.startswith("purchase_order."))
        self.assertNotIn("dispensation.create", doc_perms)
        self.assertNotIn("inventory.adjust", doc_perms)

    # 11. Lab Technician permission set is correct
    def test_11_lab_technician_permission_set_correct(self):
        lab_perms = set(RolePermission.objects.filter(
            role__code="LAB_TECHNICIAN", is_active=True
        ).values_list('permission__code', flat=True))

        expected = {
            "patients.read", "queue.view", "queue.call_next", "queue.transition",
            "lab_order.read", "specimen.collect",
            "lab_result.create", "lab_result.read", "lab_result.update", "lab_result.amend"
        }
        self.assertEqual(lab_perms, expected)

        # Boundaries
        self.assertNotIn("lab_result.verify", lab_perms)  # Doctor boundary
        self.assertNotIn("prescription.verify", lab_perms)
        self.assertNotIn("dispensation.create", lab_perms)
        self.assertNotIn("inventory.adjust", lab_perms)

    # 12. Pharmacist permission set is correct
    def test_12_pharmacist_permission_set_correct(self):
        pharm_perms = set(RolePermission.objects.filter(
            role__code="PHARMACIST", is_active=True
        ).values_list('permission__code', flat=True))

        expected = {
            "patients.read", "queue.view", "queue.call_next", "queue.transition",
            "prescription.read", "prescription.verify", "prescription.hold", "prescription.reject",
            "dispensation.create", "dispensation.read",
            "inventory.read", "inventory.adjust", "medicine_batch.read",
            "purchase_order.create", "purchase_order.read", "purchase_order.update", "goods_receipt.create"
        }
        self.assertEqual(pharm_perms, expected)

        # Boundaries
        for p in pharm_perms:
            self.assertFalse(p.startswith("diagnosis."))
            self.assertFalse(p.startswith("consultation."))
            self.assertFalse(p.startswith("triage."))
            self.assertFalse(p.startswith("staff."))

    # 13. Hospital Admin cannot create roles
    def test_13_hospital_admin_cannot_create_roles(self):
        self.client.force_authenticate(user=self.user_hospital_admin)
        res = self.client.post('/api/v1/accounts/roles/', {
            'code': 'CUSTOM_ROLE', 'name': 'Custom Role', 'scope_level': 'FACILITY'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(RoleMaster.objects.filter(code='CUSTOM_ROLE').exists())

    # 14. DHO cannot create roles
    def test_14_dho_cannot_create_roles(self):
        self.client.force_authenticate(user=self.user_dho)
        res = self.client.post('/api/v1/accounts/roles/', {
            'code': 'CUSTOM_DHO_ROLE', 'name': 'Custom DHO Role', 'scope_level': 'DISTRICT'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(RoleMaster.objects.filter(code='CUSTOM_DHO_ROLE').exists())

    # 15. Operational staff cannot modify role definitions
    def test_15_operational_staff_cannot_modify_role_definitions(self):
        role = RoleMaster.objects.get(code="DOCTOR")
        operational_users = [
            self.user_doctor, self.user_nurse, self.user_compounder,
            self.user_lab_tech, self.user_pharmacist, self.user_hospital_admin, self.user_dho
        ]
        for u in operational_users:
            self.client.force_authenticate(user=u)
            res_patch = self.client.patch(f'/api/v1/accounts/roles/{role.id}/', {'name': 'Hacked Role'})
            self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)
            res_delete = self.client.delete(f'/api/v1/accounts/roles/{role.id}/')
            self.assertEqual(res_delete.status_code, status.HTTP_403_FORBIDDEN)

    # 16. Operational staff cannot modify permission definitions
    def test_16_operational_staff_cannot_modify_permission_definitions(self):
        perm = PermissionMaster.objects.first()
        operational_users = [
            self.user_doctor, self.user_nurse, self.user_compounder,
            self.user_lab_tech, self.user_pharmacist, self.user_hospital_admin, self.user_dho
        ]
        for u in operational_users:
            self.client.force_authenticate(user=u)
            res_post = self.client.post('/api/v1/accounts/permissions/', {
                'code': 'hacked.perm', 'name': 'Hacked', 'domain': 'HACK', 'action': 'do'
            })
            self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)
            res_patch = self.client.patch(f'/api/v1/accounts/permissions/{perm.id}/', {'name': 'Altered'})
            self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)
            res_del = self.client.delete(f'/api/v1/accounts/permissions/{perm.id}/')
            self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    # 17. Role definitions cannot be self-created through API
    def test_17_role_definitions_cannot_be_self_created_through_api(self):
        # Unauthenticated request rejected
        self.client.logout()
        res_anon = self.client.post('/api/v1/accounts/roles/', {'code': 'ANON', 'name': 'Anon'})
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Superuser IS authorized to create/manage catalogue
        self.client.force_authenticate(user=self.superuser)
        res_super = self.client.post('/api/v1/accounts/roles/', {
            'code': 'TEMP_SYS_ROLE', 'name': 'Temp System Role',
            'display_name': 'Temp System Role', 'scope_level': 'GLOBAL'
        })
        self.assertEqual(res_super.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RoleMaster.objects.filter(code='TEMP_SYS_ROLE').exists())

    # 18. Existing approved authorization tests remain passing and matrix integrity
    def test_18_existing_approved_authorization_and_matrix_integrity(self):
        # Verify matrix generator generates complete explicit ALLOW / DENY matrix
        matrix = generate_role_permission_matrix()
        # 7 roles * 57 permissions = 399 explicit cells
        self.assertEqual(len(matrix), 7 * 57)
        for cell in matrix:
            self.assertIn(cell["access"], ["ALLOW", "DENY"])
            self.assertTrue(bool(cell["reason"]))
            self.assertIn(cell["scope"], ["GLOBAL", "DISTRICT", "FACILITY"])

        # Verify DHO fail-closed scoping when assigned_district IS NULL
        unassigned_dho = User.objects.create_user(
            username="unassigned_dho", role="DISTRICT_OFFICER", assigned_district=None
        )
        self.assertEqual(get_accessible_facility_ids_for_user(unassigned_dho), [])
        self.assertFalse(can_access_facility(unassigned_dho, self.clinic.id))

        # Assigned DHO can access facility in their district, but not outside
        self.assertTrue(can_access_facility(self.user_dho, self.clinic.id))
        outside_clinic = Facility.objects.create(
            facility_code="PHC-OUTSIDE-01", facility_name="Outside Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.other_district, state=self.state
        )
        self.assertFalse(can_access_facility(self.user_dho, outside_clinic.id))

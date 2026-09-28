"""
Targeted Verification Suite: Staff Identity, Account Lifecycle, Multi-Role & Anti-Privilege Escalation.
Validates the database-backed StaffRoleAssignment foundation across all 20 required points.
"""
import datetime
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import (
    Person, StaffProfile, StaffStatusChoices, RoleMaster, PermissionMaster,
    RolePermission, StaffRoleAssignment, StaffFacilityAssignment, User, RoleChoices
)
from apps.accounts.services import (
    seed_roles_and_permissions, invite_staff, activate_staff, assign_role,
    end_role_assignment, assign_facility, transfer_staff, suspend_staff,
    deactivate_staff
)
from apps.accounts.permissions import (
    get_user_active_role_codes, get_user_role_permissions, has_role_permission,
    get_accessible_facility_ids_for_user, can_access_facility,
    HasPermission, HasFacilityScope, IsAuthenticatedAndRoleAuthorized
)
from apps.common.exceptions import UnauthorizedDomainAction, InvalidStateTransition
from apps.audit.models import AuditLogEntry


class StaffLifecycleAndRoleAssignmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        seed_roles_and_permissions()

        # Geography
        cls.state = State.objects.create(name="Karnataka", code="KA")
        cls.district_blr = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=cls.state)
        cls.district_mys = District.objects.create(name="Mysuru", code="KA-MYS", state=cls.state)

        # Facilities
        cls.clinic_a = Facility.objects.create(
            facility_code="PHC-VARTHUR", facility_name="Varthur Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=cls.district_blr, state=cls.state
        )
        cls.clinic_b = Facility.objects.create(
            facility_code="PHC-WHITEFIELD", facility_name="Whitefield Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=cls.district_blr, state=cls.state
        )
        cls.clinic_mysuru = Facility.objects.create(
            facility_code="PHC-MYS-01", facility_name="Mysuru Urban Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=cls.district_mys, state=cls.state
        )

        cls.dept_opd = Department.objects.create(facility=cls.clinic_a, code="OPD", name="Outpatient")

    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

        # Standard test staff person and profile
        self.person_jane = Person.objects.create(
            first_name="Jane", last_name="Nurse", gender="FEMALE",
            date_of_birth=datetime.date(1990, 5, 15), phone_number="9876543210"
        )
        self.staff_jane = StaffProfile.objects.create(
            person=self.person_jane, employee_id="STF-NURSE-01", designation="Staff Nurse",
            department=self.dept_opd, status=StaffStatusChoices.ACTIVE
        )
        self.user_jane = User.objects.create_user(
            username="jane_nurse", email="jane@clinic.org", password="TestPass123!",
            role=RoleChoices.NURSE, assigned_facility=self.clinic_a, staff_profile=self.staff_jane
        )
        StaffFacilityAssignment.objects.create(
            staff=self.staff_jane, facility=self.clinic_a, is_primary=True,
            effective_from=datetime.date.today(), is_active=True
        )

        # Admin user for clinic_a
        self.person_admin = Person.objects.create(
            first_name="Admin", last_name="User", gender="MALE",
            date_of_birth=datetime.date(1980, 1, 1), phone_number="9876500000"
        )
        self.admin_staff = StaffProfile.objects.create(
            person=self.person_admin, employee_id="ADM-001", designation="Hospital Administrator",
            department=self.dept_opd, status=StaffStatusChoices.ACTIVE
        )
        self.admin_user = User.objects.create_user(
            username="clinic_admin", email="admin@clinic.org", password="TestPass123!",
            role=RoleChoices.HOSPITAL_ADMIN, assigned_facility=self.clinic_a, staff_profile=self.admin_staff
        )
        StaffFacilityAssignment.objects.create(
            staff=self.admin_staff, facility=self.clinic_a, is_primary=True,
            effective_from=datetime.date.today(), is_active=True
        )

        # DHO user for Bengaluru Urban district
        self.person_dho = Person.objects.create(
            first_name="Dr. Suresh", last_name="DHO", gender="MALE",
            date_of_birth=datetime.date(1970, 3, 20), phone_number="9844001122"
        )
        self.staff_dho = StaffProfile.objects.create(
            person=self.person_dho, employee_id="DHO-BLR-01", designation="District Health Officer",
            status=StaffStatusChoices.ACTIVE
        )
        self.dho_user = User.objects.create_user(
            username="dho_blr", email="dho@karnataka.gov.in", password="TestPass123!",
            role=RoleChoices.DISTRICT_OFFICER, assigned_district=self.district_blr, staff_profile=self.staff_dho
        )

    # 1. StaffRoleAssignment creates valid role assignment
    def test_01_staff_role_assignment_creates_valid_assignment(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        assignment = assign_role(
            staff_profile=self.staff_jane,
            role=role_nurse,
            facility=self.clinic_a,
            actor=self.admin_user
        )
        self.assertIsNotNone(assignment.id)
        self.assertEqual(assignment.staff, self.staff_jane)
        self.assertEqual(assignment.staff_profile, self.staff_jane)
        self.assertEqual(assignment.role.code, 'NURSE')
        self.assertEqual(assignment.facility, self.clinic_a)
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.effective_from, datetime.date.today())
        self.assertIsNone(assignment.effective_to)

    # 2. Multiple active roles resolve as union
    def test_02_multiple_active_roles_resolve_as_union(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        role_compounder = RoleMaster.objects.get(code='COMPOUNDER')

        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a,
            effective_from=datetime.date.today(), is_active=True
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_compounder, facility=self.clinic_a,
            effective_from=datetime.date.today(), is_active=True
        )

        active_roles = get_user_active_role_codes(self.user_jane)
        self.assertEqual(active_roles, {'NURSE', 'COMPOUNDER'})

        perms = get_user_role_permissions(self.user_jane)
        # Nurse permissions
        self.assertIn('triage.create', perms)
        self.assertIn('vitals.create', perms)
        # Compounder permissions
        self.assertIn('patients.create', perms)
        self.assertIn('queue.create', perms)
        self.assertIn('queue.issue_token', perms)

    # 3. NURSE + COMPOUNDER works
    def test_03_nurse_plus_compounder_works(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        role_compounder = RoleMaster.objects.get(code='COMPOUNDER')

        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=True
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_compounder, facility=self.clinic_a, is_active=True
        )

        # Has both triage and intake capability
        self.assertTrue(has_role_permission(self.user_jane, 'triage.create'))
        self.assertTrue(has_role_permission(self.user_jane, 'patients.create'))
        self.assertTrue(has_role_permission(self.user_jane, 'queue.issue_token'))
        # Does NOT have doctor consultation or pharmacist dispensing capability
        self.assertFalse(has_role_permission(self.user_jane, 'consultation.create'))
        self.assertFalse(has_role_permission(self.user_jane, 'pharmacy.dispense'))

    # 4. NURSE_COMPOUNDER does not exist
    def test_04_nurse_compounder_role_does_not_exist(self):
        self.assertFalse(RoleMaster.objects.filter(code='NURSE_COMPOUNDER').exists())
        self.assertNotIn('NURSE_COMPOUNDER', RoleChoices.values)

    # 5. User.role cannot add an unauthorized role when StaffRoleAssignment exists
    def test_05_user_role_cannot_add_unauthorized_role_when_sra_exists(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=True
        )
        # Attempted spoofing: set legacy user.role to DOCTOR
        self.user_jane.role = RoleChoices.DOCTOR
        self.user_jane.save()

        # Effective roles MUST only be NURSE, not DOCTOR
        active_roles = get_user_active_role_codes(self.user_jane)
        self.assertEqual(active_roles, {'NURSE'})
        self.assertNotIn('DOCTOR', active_roles)

    # 6. User.role is ignored for authorization when StaffRoleAssignment exists
    def test_06_user_role_is_ignored_for_authorization_when_sra_exists(self):
        role_compounder = RoleMaster.objects.get(code='COMPOUNDER')
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_compounder, facility=self.clinic_a, is_active=True
        )
        self.user_jane.role = RoleChoices.DOCTOR
        self.user_jane.save()

        # Authorization check: Jane has compounder perms, NOT doctor perms
        self.assertTrue(has_role_permission(self.user_jane, 'patients.create'))
        self.assertFalse(has_role_permission(self.user_jane, 'consultation.create'))
        self.assertFalse(has_role_permission(self.user_jane, 'diagnosis.create'))

    # 7. Inactive role assignment denies that role
    def test_07_inactive_role_assignment_denies_role(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=False
        )
        active_roles = get_user_active_role_codes(self.user_jane)
        self.assertEqual(active_roles, set())
        self.assertFalse(has_role_permission(self.user_jane, 'triage.create'))

    # 8. Ended role assignment denies that role
    def test_08_ended_role_assignment_denies_role(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a,
            effective_from=datetime.date(2025, 1, 1), effective_to=yesterday, is_active=True
        )
        active_roles = get_user_active_role_codes(self.user_jane)
        self.assertEqual(active_roles, set())
        self.assertFalse(has_role_permission(self.user_jane, 'triage.create'))

    # 9. Suspended account denies operational access
    def test_09_suspended_account_denies_operational_access(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=True
        )
        suspend_staff(self.staff_jane, reason="Disciplinary inquiry", actor=self.admin_user)

        self.staff_jane.refresh_from_db()
        self.user_jane.refresh_from_db()
        self.assertEqual(self.staff_jane.status, StaffStatusChoices.SUSPENDED)
        self.assertFalse(self.user_jane.is_active)

        self.assertEqual(get_user_active_role_codes(self.user_jane), set())
        self.assertFalse(has_role_permission(self.user_jane, 'triage.create'))
        self.assertFalse(can_access_facility(self.user_jane, self.clinic_a.id))

    # 10. Deactivated account denies operational access
    def test_10_deactivated_account_denies_operational_access(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        sra = StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=True
        )
        deactivate_staff(self.staff_jane, reason="Resignation", actor=self.admin_user)

        self.staff_jane.refresh_from_db()
        self.user_jane.refresh_from_db()
        sra.refresh_from_db()
        self.assertEqual(self.staff_jane.status, StaffStatusChoices.DEACTIVATED)
        self.assertFalse(self.user_jane.is_active)
        self.assertFalse(sra.is_active)

        self.assertEqual(get_user_active_role_codes(self.user_jane), set())
        self.assertFalse(has_role_permission(self.user_jane, 'triage.create'))

    # 11. Invited account cannot perform operational actions
    def test_11_invited_account_cannot_perform_operational_actions(self):
        prof, user = invite_staff(
            email="invitee@clinic.org",
            first_name="Ramesh",
            last_name="Kumar",
            gender="MALE",
            date_of_birth=datetime.date(1995, 8, 10),
            employee_id="STF-INV-01",
            designation="Staff Nurse",
            facility=self.clinic_a,
            role_code="NURSE",
            actor=self.admin_user
        )
        self.assertEqual(prof.status, StaffStatusChoices.INVITED)
        self.assertFalse(user.is_active)
        self.assertEqual(get_user_active_role_codes(user), set())
        self.assertFalse(has_role_permission(user, 'triage.create'))

    # 12. Facility scope is enforced
    def test_12_facility_scope_is_enforced(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        StaffRoleAssignment.objects.create(
            staff=self.staff_jane, role=role_nurse, facility=self.clinic_a, is_active=True
        )
        # Jane is assigned to clinic_a
        self.assertTrue(can_access_facility(self.user_jane, self.clinic_a.id))
        # Jane is NOT assigned to clinic_b or clinic_mysuru
        self.assertFalse(can_access_facility(self.user_jane, self.clinic_b.id))
        self.assertFalse(can_access_facility(self.user_jane, self.clinic_mysuru.id))

    # 13. DHO district scope is enforced
    def test_13_dho_district_scope_is_enforced(self):
        # DHO is assigned to Bengaluru Urban district (clinic_a and clinic_b)
        self.assertTrue(can_access_facility(self.dho_user, self.clinic_a.id))
        self.assertTrue(can_access_facility(self.dho_user, self.clinic_b.id))
        # Clinic Mysuru is in Mysuru district -> Denied!
        self.assertFalse(can_access_facility(self.dho_user, self.clinic_mysuru.id))

    # 14. DHO NULL district fails closed
    def test_14_dho_null_district_fails_closed(self):
        self.dho_user.assigned_district = None
        self.dho_user.save()

        accessible_ids = get_accessible_facility_ids_for_user(self.dho_user)
        self.assertEqual(accessible_ids, [])
        self.assertFalse(can_access_facility(self.dho_user, self.clinic_a.id))

    # 15. Clinic Admin cannot assign DHO
    def test_15_clinic_admin_cannot_assign_dho(self):
        role_dho = RoleMaster.objects.get(code='DISTRICT_OFFICER')
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(
                staff_profile=self.staff_jane,
                role=role_dho,
                facility=self.clinic_a,
                actor=self.admin_user
            )

    # 16. Clinic Admin cannot assign outside own facility
    def test_16_clinic_admin_cannot_assign_outside_own_facility(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(
                staff_profile=self.staff_jane,
                role=role_nurse,
                facility=self.clinic_mysuru,
                actor=self.admin_user
            )

    # 17. Operational users cannot modify role catalogue
    def test_17_operational_users_cannot_modify_role_catalogue(self):
        role_nurse = RoleMaster.objects.get(code='NURSE')
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(
                staff_profile=self.admin_staff,
                role=role_nurse,
                actor=self.user_jane
            )

    # 18. Users cannot self-escalate
    def test_18_users_cannot_self_escalate(self):
        role_admin = RoleMaster.objects.get(code='HOSPITAL_ADMIN')
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(
                staff_profile=self.staff_jane,
                role=role_admin,
                actor=self.user_jane
            )

    # 19. Staff lifecycle mutations create audit records
    def test_19_staff_lifecycle_mutations_create_audit_records(self):
        initial_count = AuditLogEntry.objects.count()

        # 1. Invite
        prof, user = invite_staff(
            email="audit_test@clinic.org",
            first_name="Audit",
            last_name="Test",
            gender="FEMALE",
            date_of_birth=datetime.date(1992, 1, 1),
            employee_id="STF-AUDIT-01",
            designation="Pharmacist",
            facility=self.clinic_a,
            role_code="PHARMACIST",
            actor=self.admin_user
        )
        self.assertTrue(AuditLogEntry.objects.filter(action_type="INVITE_STAFF", record_id=str(prof.id)).exists())

        # 2. Activate
        activate_staff(prof, actor=self.admin_user)
        self.assertTrue(AuditLogEntry.objects.filter(action_type="ACTIVATE_STAFF", record_id=str(prof.id)).exists())

        # 3. Suspend
        suspend_staff(prof, reason="Audit Test Suspension", actor=self.admin_user)
        self.assertTrue(AuditLogEntry.objects.filter(action_type="SUSPEND_STAFF", record_id=str(prof.id)).exists())

        # 4. Deactivate
        deactivate_staff(prof, reason="Audit Test Deactivation", actor=self.admin_user)
        self.assertTrue(AuditLogEntry.objects.filter(action_type="DEACTIVATE_STAFF", record_id=str(prof.id)).exists())

        self.assertGreater(AuditLogEntry.objects.count(), initial_count)

    # 20. Existing seven roles remain exactly seven
    def test_20_existing_seven_roles_remain_exactly_seven(self):
        expected_roles = {
            'DISTRICT_OFFICER',
            'HOSPITAL_ADMIN',
            'DOCTOR',
            'NURSE',
            'COMPOUNDER',
            'LAB_TECHNICIAN',
            'PHARMACIST'
        }
        actual_roles = set(RoleMaster.objects.values_list('code', flat=True))
        self.assertEqual(actual_roles, expected_roles)
        self.assertEqual(RoleMaster.objects.count(), 7)
        self.assertEqual(len(RoleChoices.values), 7)

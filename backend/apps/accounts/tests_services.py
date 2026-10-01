"""
IAM Domain Service Tests (apps/accounts/tests_services.py).
Tests staff profile lifecycle, role assignments, facility assignments, transfers,
and authorization checks (non-admin privilege escalation, inactive actor rejection).
"""
import datetime
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.accounts.models import Person, StaffProfile, StaffRoleAssignment, StaffFacilityAssignment
from apps.accounts.services import (
    create_staff_profile, update_staff_status, assign_role,
    end_role_assignment, assign_facility, transfer_staff
)
from apps.common.exceptions import (
    UnauthorizedDomainAction, InvalidAssignmentPeriodError, OverlappingAssignmentError
)

class IAMDomainServiceTests(DomainServiceBaseTestCase):
    def test_valid_staff_profile_and_role_assignment(self):
        p = Person.objects.create(first_name="Radha", last_name="Devi", gender="FEMALE", date_of_birth="1992-04-10")
        staff = create_staff_profile(person=p, employee_id="DOC-999", designation="Medical Officer", department=self.dept_opd, actor_staff=self.admin_staff)
        self.assertEqual(staff.employee_id, "DOC-999")

        assignment = assign_role(staff, self.role_doc, effective_from=datetime.date.today(), actor_staff=self.admin_staff)
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.role.code, "DOCTOR")

    def test_unauthorized_role_assignment_non_admin(self):
        """Failure 1: Non-admin staff attempting to assign privileged ADMIN role is rejected."""
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.doc_staff, self.role_admin, actor_staff=self.nurse_staff)

    def test_unauthorized_role_assignment_inactive_actor(self):
        """Failure: Inactive (suspended) staff cannot perform role assignment."""
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.doc_staff, self.role_doc, actor_staff=self.suspended_staff)

    def test_unauthorized_facility_assignment_inactive_actor(self):
        """Failure 2: Inactive staff cannot assign facilities."""
        with self.assertRaises(UnauthorizedDomainAction):
            assign_facility(self.doc_staff, self.clinic_a, actor_staff=self.suspended_staff)

    def test_invalid_assignment_period_rejected(self):
        """Failure: effective_to preceding effective_from is rejected."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        with self.assertRaises(InvalidAssignmentPeriodError):
            assign_role(self.doc_staff, self.role_doc, effective_from=today, effective_to=yesterday, actor_staff=self.admin_staff)

    def test_overlapping_role_assignment_rejected(self):
        """Failure: Overlapping active role assignment for the same role is rejected."""
        with self.assertRaises(OverlappingAssignmentError):
            assign_role(self.doc_staff, self.role_doc, actor_staff=self.admin_staff)

    def test_facility_transfer_demotes_prior_primary(self):
        """Transfer atomically terminates prior primary facility assignment."""
        assign_facility(self.doc_staff, self.clinic_a, is_primary=True, actor_staff=self.admin_staff)
        self.assertTrue(StaffFacilityAssignment.objects.get(staff=self.doc_staff, facility=self.clinic_a).is_primary)

        transfer_staff(self.doc_staff, self.clinic_b, actor_staff=self.admin_staff)
        old_a = StaffFacilityAssignment.objects.get(staff=self.doc_staff, facility=self.clinic_a)
        self.assertFalse(old_a.is_primary)
        self.assertFalse(old_a.is_active)

        new_b = StaffFacilityAssignment.objects.get(staff=self.doc_staff, facility=self.clinic_b)
        self.assertTrue(new_b.is_primary)
        self.assertTrue(new_b.is_active)

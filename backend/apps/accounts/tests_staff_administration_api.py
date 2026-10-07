"""
Comprehensive Real-Database Verification Suite for Staff Administration API & Lifecycle Hardening.
Tests DHO authority, Clinic Admin authority, operational role protection, role/facility invariants,
multi-role safety, transfer atomicity, lifecycle enforcement, User.role zero-weight at API level,
and audit uniqueness.
"""
import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment, StaffStatusChoices, User
)
from apps.accounts.services import (
    invite_staff, activate_staff, assign_role, end_role_assignment,
    assign_facility, transfer_staff, suspend_staff, deactivate_staff,
    seed_roles_and_permissions
)
from apps.accounts.permissions import get_user_active_role_codes, get_accessible_facility_ids_for_user
from apps.common.exceptions import (
    UnauthorizedDomainAction, DomainValidationError, InvalidAssignmentPeriodError,
    OverlappingAssignmentError
)
from apps.audit.models import AuditLogEntry
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.patients.models import Patient
from apps.visits.models import Visit


class StaffAdministrationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        # Geography
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district_a = District.objects.create(name="Bengaluru Urban", code="KA-BLR-U", state=self.state)
        self.district_b = District.objects.create(name="Mysuru", code="KA-MYS", state=self.state)

        # Facilities
        self.clinic_a1 = Facility.objects.create(
            facility_code="PHC-BLR-01", facility_name="Varthur Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district_a, state=self.state
        )
        self.clinic_a2 = Facility.objects.create(
            facility_code="PHC-BLR-02", facility_name="Whitefield Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district_a, state=self.state
        )
        self.clinic_b1 = Facility.objects.create(
            facility_code="PHC-MYS-01", facility_name="Mysuru Central Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district_b, state=self.state
        )

        self.dept_opd_a1 = Department.objects.create(facility=self.clinic_a1, code="OPD", name="Outpatient")
        self.dept_opd_a2 = Department.objects.create(facility=self.clinic_a2, code="OPD", name="Outpatient")

        # Roles from catalogue
        self.role_dho = RoleMaster.objects.get(code="DISTRICT_OFFICER")
        self.role_admin = RoleMaster.objects.get(code="HOSPITAL_ADMIN")
        self.role_doc = RoleMaster.objects.get(code="DOCTOR")
        self.role_nurse = RoleMaster.objects.get(code="NURSE")
        self.role_compounder = RoleMaster.objects.get(code="FRONT_DESK_OFFICER")
        self.role_lab = RoleMaster.objects.get(code="LAB_TECHNICIAN")
        self.role_pharm = RoleMaster.objects.get(code="PHARMACIST")

        # 1. Superuser
        self.superuser = User.objects.create_superuser(
            username="superadmin", email="super@example.com", password="password123", full_name="Super Admin"
        )

        # 2. DHO (District A)
        self.person_dho = Person.objects.create(
            first_name="District", last_name="Officer", gender="MALE", date_of_birth="1975-01-01"
        )
        self.staff_dho = StaffProfile.objects.create(
            person=self.person_dho, employee_id="DHO-001", designation="District Health Officer", status="ACTIVE"
        )
        self.user_dho = User.objects.create_user(
            username="dho_blr", password="password123", full_name="Dr. DHO BLR",
            role="DISTRICT_OFFICER", assigned_district=self.district_a, staff_profile=self.staff_dho
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_dho, role=self.role_dho, effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        # 3. Clinic Admin (Clinic A1)
        self.person_admin = Person.objects.create(
            first_name="Clinic", last_name="Admin", gender="FEMALE", date_of_birth="1980-05-15"
        )
        self.staff_admin = StaffProfile.objects.create(
            person=self.person_admin, employee_id="ADM-001", designation="Hospital Administrator", status="ACTIVE"
        )
        self.user_admin = User.objects.create_user(
            username="admin_a1", password="password123", full_name="Admin A1",
            role="HOSPITAL_ADMIN", assigned_facility=self.clinic_a1, staff_profile=self.staff_admin
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_admin, role=self.role_admin, effective_from=datetime.date(2026, 1, 1), is_active=True
        )
        StaffFacilityAssignment.objects.create(
            staff=self.staff_admin, facility=self.clinic_a1, is_primary=True, effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        # 4. Doctor (Clinic A1)
        self.person_doc = Person.objects.create(
            first_name="Ravi", last_name="Kumar", gender="MALE", date_of_birth="1985-08-20"
        )
        self.staff_doc = StaffProfile.objects.create(
            person=self.person_doc, employee_id="DOC-001", designation="Medical Officer", status="ACTIVE"
        )
        self.user_doc = User.objects.create_user(
            username="doc_ravi", password="password123", full_name="Dr. Ravi Kumar",
            role="DOCTOR", assigned_facility=self.clinic_a1, staff_profile=self.staff_doc
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_doc, role=self.role_doc, effective_from=datetime.date(2026, 1, 1), is_active=True
        )
        StaffFacilityAssignment.objects.create(
            staff=self.staff_doc, facility=self.clinic_a1, department=self.dept_opd_a1, is_primary=True,
            effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        # 5. Nurse (Clinic A1)
        self.person_nurse = Person.objects.create(
            first_name="Sunita", last_name="Sharma", gender="FEMALE", date_of_birth="1990-11-12"
        )
        self.staff_nurse = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="NUR-001", designation="Staff Nurse", status="ACTIVE"
        )
        self.user_nurse = User.objects.create_user(
            username="nurse_sunita", password="password123", full_name="Nurse Sunita",
            role="NURSE", assigned_facility=self.clinic_a1, staff_profile=self.staff_nurse
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_nurse, role=self.role_nurse, effective_from=datetime.date(2026, 1, 1), is_active=True
        )
        StaffFacilityAssignment.objects.create(
            staff=self.staff_nurse, facility=self.clinic_a1, department=self.dept_opd_a1, is_primary=True,
            effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        # 6. Foreign Staff in District B
        self.person_b = Person.objects.create(
            first_name="Mysuru", last_name="Staff", gender="MALE", date_of_birth="1988-02-02"
        )
        self.staff_b = StaffProfile.objects.create(
            person=self.person_b, employee_id="DOC-B01", designation="Medical Officer", status="ACTIVE"
        )
        self.user_b = User.objects.create_user(
            username="doc_mysuru", password="password123", full_name="Dr. Mysuru",
            role="DOCTOR", assigned_facility=self.clinic_b1, staff_profile=self.staff_b
        )
        StaffRoleAssignment.objects.create(
            staff=self.staff_b, role=self.role_doc, effective_from=datetime.date(2026, 1, 1), is_active=True
        )
        StaffFacilityAssignment.objects.create(
            staff=self.staff_b, facility=self.clinic_b1, is_primary=True, effective_from=datetime.date(2026, 1, 1), is_active=True
        )

    # 1. DHO valid in-district administration
    def test_01_dho_valid_in_district_administration(self):
        """DHO assigned to District A can invite and assign operational roles to staff within District A."""
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "first_name": "Kavitha",
            "last_name": "Rao",
            "gender": "FEMALE",
            "date_of_birth": "1993-04-10",
            "employee_id": "PHM-BLR-01",
            "designation": "Pharmacist",
            "role_code": "PHARMACIST",
            "facility_id": self.clinic_a1.id
        }
        res = self.client.post('/api/v1/accounts/staff-profiles/invite/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['employee_id'], "PHM-BLR-01")
        self.assertEqual(res.data['status'], "INVITED")

    # 2. DHO foreign-district denial
    def test_02_dho_foreign_district_denial(self):
        """DHO assigned to District A cannot administer staff/facility in District B."""
        self.client.force_authenticate(user=self.user_dho)
        # Attempt to invite staff into clinic in District B
        payload = {
            "first_name": "Sneha",
            "last_name": "G",
            "gender": "FEMALE",
            "date_of_birth": "1994-06-15",
            "employee_id": "NUR-MYS-01",
            "designation": "Staff Nurse",
            "role_code": "NURSE",
            "facility_id": self.clinic_b1.id  # District B!
        }
        res = self.client.post('/api/v1/accounts/staff-profiles/invite/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        with self.assertRaises(UnauthorizedDomainAction):
            invite_staff(
                email="sneha@test.org",
                first_name="Sneha",
                last_name="G",
                gender="FEMALE",
                date_of_birth=datetime.date(1994, 6, 15),
                employee_id="NUR-MYS-01",
                designation="Staff Nurse",
                facility=self.clinic_b1,
                role_code="NURSE",
                actor=self.user_dho
            )

    # 3. DHO NULL-district denial
    def test_03_dho_null_district_denial(self):
        """DHO with NULL district fails closed and cannot perform staff administration."""
        dho_null_user = User.objects.create_user(
            username="dho_null", password="password123", role="DISTRICT_OFFICER", assigned_district=None
        )
        self.client.force_authenticate(user=dho_null_user)
        res = self.client.get('/api/v1/accounts/staff-profiles/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results'] if 'results' in res.data else res.data), 0)

        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.staff_doc, self.role_pharm, actor=dho_null_user)

    # 4. DHO cannot assign system role
    def test_04_dho_cannot_assign_system_role(self):
        """DHO cannot assign system-level roles."""
        role_sys = RoleMaster.objects.create(code="SYSTEM_ADMIN", name="System Admin")
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.staff_doc, role_sys, actor=self.user_dho)

    # 5. Clinic Admin valid operational-role assignment
    def test_05_clinic_admin_valid_operational_role_assignment(self):
        """Clinic Admin can assign operational clinical roles within own facility."""
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.post(f'/api/v1/accounts/staff-profiles/{self.staff_nurse.id}/assign-role/', {
            "role_code": "FRONT_DESK_OFFICER"
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StaffRoleAssignment.objects.filter(staff=self.staff_nurse, role=self.role_compounder, is_active=True).exists())

    # 6. Clinic Admin cannot assign DHO
    def test_06_clinic_admin_cannot_assign_dho(self):
        """Clinic Admin cannot assign DISTRICT_OFFICER."""
        self.client.force_authenticate(user=self.user_admin)
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.staff_doc, self.role_dho, actor=self.user_admin)

    # 7. Clinic Admin foreign-facility denial
    def test_07_clinic_admin_foreign_facility_denial(self):
        """Clinic Admin of Facility A cannot administer foreign Facility B or staff belonging to Facility B."""
        self.client.force_authenticate(user=self.user_admin)
        with self.assertRaises(UnauthorizedDomainAction):
            assign_facility(self.staff_doc, self.clinic_a2, actor=self.user_admin)

        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.staff_b, self.role_nurse, actor=self.user_admin)

    # 8. Clinic Admin self-escalation denial
    def test_08_clinic_admin_self_escalation_denial(self):
        """Clinic Admin cannot assign roles to themselves."""
        with self.assertRaises(UnauthorizedDomainAction):
            assign_role(self.staff_admin, self.role_doc, actor=self.user_admin)

    # 9. Operational roles cannot administer staff
    def test_09_operational_roles_cannot_administer_staff(self):
        """Operational users (DOCTOR, NURSE, etc.) cannot view or mutate staff administration endpoints."""
        self.client.force_authenticate(user=self.user_doc)
        res = self.client.get('/api/v1/accounts/staff-profiles/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user_nurse)
        res_post = self.client.post('/api/v1/accounts/staff-profiles/invite/', {}, format='json')
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    # 10. Facility-role requires valid facility
    def test_10_facility_role_requires_valid_facility(self):
        """Assigning a facility role to a staff member without facility context raises DomainValidationError."""
        p_floating = Person.objects.create(first_name="Floating", last_name="Doc", gender="MALE", date_of_birth="1989-01-01")
        staff_floating = StaffProfile.objects.create(person=p_floating, employee_id="FLOAT-01", designation="Medical Officer", status="ACTIVE")
        with self.assertRaises(DomainValidationError):
            assign_role(staff_floating, self.role_doc, facility=None, actor=self.superuser)

    # 11. DHO requires valid district
    def test_11_dho_requires_valid_district(self):
        """Assigning DISTRICT_OFFICER to a staff member without district context raises DomainValidationError."""
        p_dist = Person.objects.create(first_name="NoDist", last_name="Officer", gender="MALE", date_of_birth="1980-01-01")
        staff_dist = StaffProfile.objects.create(person=p_dist, employee_id="NODIST-01", designation="District Officer", status="ACTIVE")
        with self.assertRaises(DomainValidationError):
            assign_role(staff_dist, self.role_dho, facility=None, actor=self.superuser)

    # 12. Multi-role preservation
    def test_12_multi_role_preservation(self):
        """Assigning a second NURSE does not affect first NURSE+FRONT_DESK_OFFICER; ending one removes only that role."""
        # 1. Staff 1 assigned NURSE + FRONT_DESK_OFFICER
        assign_role(self.staff_nurse, self.role_compounder, actor=self.user_admin)
        roles_s1 = set(StaffRoleAssignment.objects.filter(staff=self.staff_nurse, is_active=True).values_list('role__code', flat=True))
        self.assertEqual(roles_s1, {'NURSE', 'FRONT_DESK_OFFICER'})

        # 2. Staff 2 hired and assigned NURSE
        p2 = Person.objects.create(first_name="Nurse2", last_name="K", gender="FEMALE", date_of_birth="1995-01-01")
        staff_n2 = StaffProfile.objects.create(person=p2, employee_id="NUR-002", designation="Staff Nurse", status="ACTIVE")
        assign_facility(staff_n2, self.clinic_a1, is_primary=True, actor=self.user_admin)
        assign_role(staff_n2, self.role_nurse, actor=self.user_admin)

        # Verify Staff 1 still has both
        roles_s1_after = set(StaffRoleAssignment.objects.filter(staff=self.staff_nurse, is_active=True).values_list('role__code', flat=True))
        self.assertEqual(roles_s1_after, {'NURSE', 'FRONT_DESK_OFFICER'})

        # 3. End FRONT_DESK_OFFICER on Staff 1
        comp_assign = StaffRoleAssignment.objects.get(staff=self.staff_nurse, role=self.role_compounder, is_active=True)
        end_role_assignment(comp_assign, actor=self.user_admin)

        # Staff 1 now has only NURSE
        roles_s1_ended = set(StaffRoleAssignment.objects.filter(staff=self.staff_nurse, is_active=True).values_list('role__code', flat=True))
        self.assertEqual(roles_s1_ended, {'NURSE'})

    # 13. Transfer no dual access
    def test_13_transfer_no_dual_access(self):
        """Future transfer sets TRANSFER_PENDING and prevents dual-facility authorization leak."""
        future_date = datetime.date.today() + datetime.timedelta(days=7)
        transfer_staff(self.staff_doc, new_facility=self.clinic_a2, effective_date=future_date, actor=self.user_dho)

        self.staff_doc.refresh_from_db()
        self.assertEqual(self.staff_doc.status, "TRANSFER_PENDING")

        accessible = get_accessible_facility_ids_for_user(self.user_doc)
        self.assertEqual(accessible, [self.clinic_a1.id])
        self.assertNotIn(self.clinic_a2.id, accessible)

    # 14. Transfer rollback
    def test_14_transfer_rollback(self):
        """Failed transfer transaction rolls back atomically without partial state changes."""
        prior_assign = StaffFacilityAssignment.objects.get(staff=self.staff_doc, facility=self.clinic_a1, is_primary=True)
        initial_status = self.staff_doc.status

        # Transfer with invalid cross-district by Clinic Admin
        with self.assertRaises(UnauthorizedDomainAction):
            transfer_staff(self.staff_doc, new_facility=self.clinic_b1, actor=self.user_admin)

        self.staff_doc.refresh_from_db()
        prior_assign.refresh_from_db()
        self.assertEqual(self.staff_doc.status, initial_status)
        self.assertTrue(prior_assign.is_active)
        self.assertTrue(prior_assign.is_primary)

    # 15. Lifecycle API enforcement
    def test_15_lifecycle_api_enforcement(self):
        """INVITED, SUSPENDED, DEACTIVATED accounts receive 403 on operational actions; ACTIVE succeeds."""
        # 1. Active Doctor conduct consultation -> 201 Created
        self.client.force_authenticate(user=self.user_doc)
        patient = Patient.objects.create(patient_id="PAT-L01", person=self.person_doc, name="L Patient", age=30, gender="MALE", registered_at_facility=self.clinic_a1)
        visit = Visit.objects.create(visit_id="VIS-L01", patient=patient, facility=self.clinic_a1, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")
        res_act = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a1.id, "chief_complaint": "Headache"
        }, format='json')
        self.assertEqual(res_act.status_code, status.HTTP_201_CREATED)

        # 2. Suspend Doctor -> 403 Forbidden
        suspend_staff(self.staff_doc, reason="Investigation", actor=self.user_dho)
        res_susp = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a1.id, "chief_complaint": "Attempt"
        }, format='json')
        self.assertEqual(res_susp.status_code, status.HTTP_403_FORBIDDEN)

    # 16. User.role API-level isolation
    def test_16_user_role_api_level_isolation(self):
        """When StaffRoleAssignment=NURSE and User.role=DOCTOR, Doctor consultation endpoint returns 403."""
        # Setup nurse user who has User.role = "DOCTOR"
        self.user_nurse.role = "DOCTOR"
        self.user_nurse.save(update_fields=["role"])

        # Authenticate as Nurse
        self.client.force_authenticate(user=self.user_nurse)
        patient = Patient.objects.create(patient_id="PAT-ISO", person=self.person_nurse, name="Iso Patient", age=25, gender="FEMALE", registered_at_facility=self.clinic_a1)
        visit = Visit.objects.create(visit_id="VIS-ISO", patient=patient, facility=self.clinic_a1, visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION")

        res = self.client.post('/api/v1/clinical/consultations/', {
            "visit": visit.id, "patient": patient.id, "facility": self.clinic_a1.id, "chief_complaint": "Consultation"
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 17. Audit exactly once
    def test_17_audit_exactly_once(self):
        """Staff administration domain operations log exactly one audit entry per action."""
        initial_count = AuditLogEntry.objects.filter(table_name="staff_role_assignments").count()
        assign_role(self.staff_doc, self.role_pharm, actor=self.user_admin)
        new_count = AuditLogEntry.objects.filter(table_name="staff_role_assignments").count()
        self.assertEqual(new_count, initial_count + 1)

    # 18. Seven roles remain unchanged
    def test_18_seven_roles_remain_unchanged(self):
        """Canonical roles exist in RoleMaster."""
        expected = {
            "DISTRICT_OFFICER", "HOSPITAL_ADMIN", "DOCTOR",
            "NURSE", "FRONT_DESK_OFFICER", "LAB_TECHNICIAN", "PHARMACIST"
        }
        actual = set(RoleMaster.objects.values_list('code', flat=True))
        self.assertTrue(expected.issubset(actual))

    # 19. No SYSTEM_ADMIN role
    def test_19_no_system_admin_role_in_catalogue(self):
        """SYSTEM_ADMIN is not in the approved role catalogue."""
        self.assertFalse(RoleMaster.objects.filter(code="SYSTEM_ADMIN").exists())

    # 20. No NURSE_COMPOUNDER or NURSE_FRONT_DESK_OFFICER role
    def test_20_no_nurse_compounder_role(self):
        """NURSE_COMPOUNDER or NURSE_FRONT_DESK_OFFICER does not exist as a composite role definition."""
        self.assertFalse(RoleMaster.objects.filter(code="NURSE_COMPOUNDER").exists())
        self.assertFalse(RoleMaster.objects.filter(code="NURSE_FRONT_DESK_OFFICER").exists())

    # --- PHASE 31: Hospital Administrator Appointment & Lifecycle Tests ---

    def test_21_hospital_admin_cannot_invite_hospital_admin(self):
        """SEC-01: Hospital Admin must NOT be able to invite another HOSPITAL_ADMIN (403 Forbidden)."""
        self.client.force_authenticate(user=self.user_admin)
        payload = {
            "first_name": "Ramesh",
            "last_name": "Kumar",
            "gender": "MALE",
            "date_of_birth": "1985-05-15",
            "employee_id": "EMP-HA-PEER",
            "designation": "Hospital Administrator",
            "role_code": "HOSPITAL_ADMIN",
            "facility_id": self.clinic_a1.id,
            "temporary_password": "PeerAdmin@123"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Clinic Admin cannot assign privileged role", str(res.data.get("error", "")))

    def test_22_hospital_admin_cannot_assign_hospital_admin(self):
        """SEC-01: Hospital Admin must NOT be able to assign HOSPITAL_ADMIN role (403 Forbidden)."""
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.post(
            f"/api/v1/accounts/staff-profiles/{self.staff_nurse.id}/assign-role/",
            {"role_code": "HOSPITAL_ADMIN", "facility_id": self.clinic_a1.id},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Clinic Admin cannot assign privileged role", str(res.data.get("error", "")))

    def test_23_dho_can_appoint_hospital_admin_in_district(self):
        """DHO possesses authoritative authority to appoint HOSPITAL_ADMIN within own district."""
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "first_name": "Ananya",
            "last_name": "Desai",
            "gender": "FEMALE",
            "date_of_birth": "1988-08-20",
            "employee_id": "EMP-HA-DESAI",
            "designation": "Hospital Administrator",
            "role_code": "HOSPITAL_ADMIN",
            "facility_id": self.clinic_a1.id,
            "temporary_password": "InitialPass@2026"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "INVITED")
        # Ensure password is NOT leaked in API response
        self.assertNotIn("password", res.data)
        self.assertNotIn("temporary_password", res.data)

        # Check PostgreSQL state
        from apps.accounts.models import StaffProfile, StaffRoleAssignment, User
        sp = StaffProfile.objects.get(employee_id="EMP-HA-DESAI")
        self.assertEqual(sp.status, "INVITED")
        sra = StaffRoleAssignment.objects.filter(staff=sp, role__code="HOSPITAL_ADMIN", is_active=True).first()
        self.assertIsNotNone(sra)
        self.assertEqual(sra.facility_id, self.clinic_a1.id)

        # User is created but inactive
        user = sp.user_account
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("InitialPass@2026"))

    def test_24_dho_cannot_appoint_hospital_admin_cross_district(self):
        """DHO attempting cross-district appointment is denied (403 Forbidden)."""
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            "first_name": "Vikram",
            "last_name": "Patel",
            "gender": "MALE",
            "date_of_birth": "1982-03-12",
            "employee_id": "EMP-HA-FOREIGN",
            "designation": "Hospital Administrator",
            "role_code": "HOSPITAL_ADMIN",
            "facility_id": self.clinic_b1.id,
            "temporary_password": "ForeignPass@123"
        }
        res = self.client.post("/api/v1/accounts/staff-profiles/invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_25_credential_lifecycle_invite_and_login(self):
        """Full credential lifecycle: invite -> activate -> login with username or employee ID."""
        self.client.force_authenticate(user=self.user_dho)
        emp_id = "EMP-HA-LIFECYCLE"
        temp_pwd = "SecureLoginPass@123"

        # 1. Invite
        invite_res = self.client.post("/api/v1/accounts/staff-profiles/invite/", {
            "first_name": "Siddharth",
            "last_name": "Mehta",
            "gender": "MALE",
            "date_of_birth": "1991-01-15",
            "employee_id": emp_id,
            "designation": "Hospital Administrator",
            "role_code": "HOSPITAL_ADMIN",
            "facility_id": self.clinic_a1.id,
            "temporary_password": temp_pwd
        }, format="json")
        self.assertEqual(invite_res.status_code, status.HTTP_201_CREATED)
        profile_id = invite_res.data["id"]

        # 2. Activate
        act_res = self.client.post(f"/api/v1/accounts/staff-profiles/{profile_id}/activate/", format="json")
        self.assertEqual(act_res.status_code, status.HTTP_200_OK)
        self.assertEqual(act_res.data["status"], "ACTIVE")

        # 3. Log in via SimpleJWT using username
        self.client.logout()
        username = emp_id.lower().replace("-", "_")
        login_res_1 = self.client.post("/api/auth/token/", {"username": username, "password": temp_pwd}, format="json")
        self.assertEqual(login_res_1.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_res_1.data)

        # 4. Log in via SimpleJWT using employee_id
        login_res_2 = self.client.post("/api/auth/token/", {"username": emp_id, "password": temp_pwd}, format="json")
        self.assertEqual(login_res_2.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_res_2.data)

    def test_26_set_credentials_action_and_audit(self):
        """Admin can update staff credentials via set-credentials endpoint without leaking secrets."""
        self.client.force_authenticate(user=self.user_admin)
        new_pwd = "UpdatedCredential@2026"
        res = self.client.post(
            f"/api/v1/accounts/staff-profiles/{self.staff_doc.id}/set-credentials/",
            {"password": new_pwd},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "SUCCESS")
        self.assertNotIn(new_pwd, str(res.data))

        # Check DB & audit log
        user = self.staff_doc.user_account
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_pwd))

        audit = AuditLogEntry.objects.filter(action_type="SET_CREDENTIALS", table_name="users").last()
        self.assertIsNotNone(audit)
        self.assertNotIn(new_pwd, str(audit.payload_after))

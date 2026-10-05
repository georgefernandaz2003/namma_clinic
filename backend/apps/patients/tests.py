"""
Authoritative Regression Test Suite for Patient Intake & Registration (Phase 27A).
Tests:
1. Compounder can create patient in assigned facility (201).
2. Hospital Admin can create patient in assigned facility (201).
3. Nurse receives 403 Forbidden on patient creation.
4. Doctor receives 403 Forbidden on patient creation.
5. Lab Technician receives 403 Forbidden on patient creation.
6. Pharmacist receives 403 Forbidden on patient creation.
7. Unauthenticated/unauthorized request receives 401/403.
8. Compounder can update permitted demographic fields (address, mobile, emergency_contact, ward).
9. Compounder cannot update protected clinical or identity fields (400 Bad Request).
10. Hospital Admin demographic update works within assigned facility scope.
11. Cross-facility demographic mutation is rejected (403 Forbidden).
12. Duplicate patient creation (same facility + normalized mobile + normalized name) returns 409 Conflict.
13. Blank ABHA submission remains blank without synthetic generation.
14. Existing patient search continues working across facilities.
"""
import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Ward, Zone
from apps.facilities.models import Facility, Department
from apps.accounts.models import (
    Person, StaffProfile, User, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment
)
from apps.accounts.services import seed_roles_and_permissions
from apps.patients.models import Patient


class PatientAuthorizationAndIntakeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed authoritative IAM catalogue
        seed_roles_and_permissions()

        # 1. Geographic Hierarchy
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.zone = Zone.objects.create(name="East Zone", district=self.district)
        self.ward_1 = Ward.objects.create(name="Ward 101", ward_number=101, zone=self.zone)
        self.ward_2 = Ward.objects.create(name="Ward 102", ward_number=102, zone=self.zone)

        # 2. Facilities
        self.facility_a = Facility.objects.create(
            facility_code="PHC-VARTHUR-01",
            facility_name="Varthur Primary Health Centre",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            ward=self.ward_1,
            status="ACTIVE"
        )
        self.facility_b = Facility.objects.create(
            facility_code="PHC-WHITEFIELD-02",
            facility_name="Whitefield Community Health Centre",
            facility_type="COMMUNITY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            ward=self.ward_2,
            status="ACTIVE"
        )

        # 3. Roles from catalogue
        self.role_compounder = RoleMaster.objects.get(code="FRONT_DESK_OFFICER")
        self.role_admin = RoleMaster.objects.get(code="HOSPITAL_ADMIN")
        self.role_nurse = RoleMaster.objects.get(code="NURSE")
        self.role_doctor = RoleMaster.objects.get(code="DOCTOR")
        self.role_lab = RoleMaster.objects.get(code="LAB_TECHNICIAN")
        self.role_pharm = RoleMaster.objects.get(code="PHARMACIST")

        # 4. Users
        # Front Desk Officer (Facility A)
        p_cmp = Person.objects.create(first_name="Ravi", last_name="Kumar", gender="MALE", date_of_birth="1990-01-01")
        self.staff_cmp = StaffProfile.objects.create(person=p_cmp, employee_id="EMP-CMP-TEST", designation="Front Desk Officer", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_cmp, role=self.role_compounder, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_cmp, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_cmp = User.objects.create_user(username="test_cmp", password="password123", role="FRONT_DESK_OFFICER", assigned_facility=self.facility_a, staff_profile=self.staff_cmp)

        # Hospital Admin (Facility A)
        p_adm = Person.objects.create(first_name="Admin", last_name="Staff", gender="FEMALE", date_of_birth="1980-02-02")
        self.staff_adm = StaffProfile.objects.create(person=p_adm, employee_id="EMP-ADM-TEST", designation="Hospital Administrator", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_adm, role=self.role_admin, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_adm, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_adm = User.objects.create_user(username="test_adm", password="password123", role="HOSPITAL_ADMIN", assigned_facility=self.facility_a, staff_profile=self.staff_adm)

        # Nurse (Facility A)
        p_nur = Person.objects.create(first_name="Nurse", last_name="Staff", gender="FEMALE", date_of_birth="1992-03-03")
        self.staff_nur = StaffProfile.objects.create(person=p_nur, employee_id="EMP-NUR-TEST", designation="Staff Nurse", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_nur, role=self.role_nurse, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_nur, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_nur = User.objects.create_user(username="test_nur", password="password123", role="NURSE", assigned_facility=self.facility_a, staff_profile=self.staff_nur)

        # Doctor (Facility A)
        p_doc = Person.objects.create(first_name="Doctor", last_name="Staff", gender="MALE", date_of_birth="1982-04-04")
        self.staff_doc = StaffProfile.objects.create(person=p_doc, employee_id="EMP-DOC-TEST", designation="Medical Officer", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=self.role_doctor, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_doc = User.objects.create_user(username="test_doc", password="password123", role="DOCTOR", assigned_facility=self.facility_a, staff_profile=self.staff_doc)

        # Lab Tech (Facility A)
        p_lab = Person.objects.create(first_name="Lab", last_name="Staff", gender="FEMALE", date_of_birth="1993-05-05")
        self.staff_lab = StaffProfile.objects.create(person=p_lab, employee_id="EMP-LAB-TEST", designation="Lab Technician", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_lab, role=self.role_lab, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_lab, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_lab = User.objects.create_user(username="test_lab", password="password123", role="LAB_TECHNICIAN", assigned_facility=self.facility_a, staff_profile=self.staff_lab)

        # Pharmacist (Facility A)
        p_phm = Person.objects.create(first_name="Pharm", last_name="Staff", gender="MALE", date_of_birth="1987-06-06")
        self.staff_phm = StaffProfile.objects.create(person=p_phm, employee_id="EMP-PHM-TEST", designation="Pharmacist", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=self.staff_phm, role=self.role_pharm, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_phm, facility=self.facility_a, is_primary=True, is_active=True)
        self.user_phm = User.objects.create_user(username="test_phm", password="password123", role="PHARMACIST", assigned_facility=self.facility_a, staff_profile=self.staff_phm)

        # Baseline Patient at Facility A
        self.existing_patient = Patient.objects.create(
            patient_id="PAT-BASE-001",
            name="Aarav Sharma",
            age=28,
            gender="MALE",
            mobile="9876500001",
            address="12 Main Road, Varthur",
            registered_at_facility=self.facility_a,
            ward=self.ward_1,
            district=self.district,
            ABHA_ID_DEMO=""
        )

    def test_01_compounder_can_create_patient(self):
        self.client.force_authenticate(user=self.user_cmp)
        payload = {
            "name": "Sunita Rao",
            "age": 34,
            "gender": "FEMALE",
            "mobile": "9876500002",
            "address": "45 Lakeview Layout",
            "registered_at_facility": self.facility_a.id,
            "ward": self.ward_1.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['patient_id'].startswith("PAT-"))
        self.assertEqual(res.data['name'], "Sunita Rao")

    def test_02_hospital_admin_can_create_patient_if_permission_exists(self):
        self.client.force_authenticate(user=self.user_adm)
        payload = {
            "name": "Deepak Verma",
            "age": 42,
            "gender": "MALE",
            "mobile": "9876500003",
            "address": "88 Central Avenue",
            "registered_at_facility": self.facility_a.id,
            "ward": self.ward_1.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['patient_id'].startswith("PAT-"))
        self.assertEqual(res.data['name'], "Deepak Verma")

    def test_03_nurse_cannot_create_patient(self):
        self.client.force_authenticate(user=self.user_nur)
        payload = {
            "name": "Unauthorized Nurse Patient",
            "age": 25,
            "gender": "FEMALE",
            "mobile": "9876500004",
            "address": "Some Road",
            "registered_at_facility": self.facility_a.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_04_doctor_cannot_create_patient_unless_permission_exists(self):
        self.client.force_authenticate(user=self.user_doc)
        payload = {
            "name": "Unauthorized Doc Patient",
            "age": 50,
            "gender": "MALE",
            "mobile": "9876500005",
            "address": "Some Road",
            "registered_at_facility": self.facility_a.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_05_lab_technician_cannot_create_patient(self):
        self.client.force_authenticate(user=self.user_lab)
        payload = {
            "name": "Unauthorized Lab Patient",
            "age": 30,
            "gender": "OTHER",
            "mobile": "9876500006",
            "address": "Some Road",
            "registered_at_facility": self.facility_a.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_pharmacist_cannot_create_patient(self):
        self.client.force_authenticate(user=self.user_phm)
        payload = {
            "name": "Unauthorized Pharm Patient",
            "age": 45,
            "gender": "MALE",
            "mobile": "9876500007",
            "address": "Some Road",
            "registered_at_facility": self.facility_a.id
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_unauthorized_post_returns_http_403(self):
        # Anonymous user returns 401
        self.client.force_authenticate(user=None)
        res_anon = self.client.post('/api/v1/patients/', {"name": "Anon"}, format='json')
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated user without active staff profile returns 403
        inactive_user = User.objects.create_user(username="no_staff", password="password123")
        self.client.force_authenticate(user=inactive_user)
        res_no_staff = self.client.post('/api/v1/patients/', {"name": "NoStaff"}, format='json')
        self.assertEqual(res_no_staff.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_compounder_can_update_permitted_demographics(self):
        self.client.force_authenticate(user=self.user_cmp)
        patch_payload = {
            "address": "Updated Address 99, Varthur Colony",
            "mobile": "9876599999",
            "emergency_contact": "Father - 9876588888",
            "ward": self.ward_1.id
        }
        res = self.client.patch(f'/api/v1/patients/{self.existing_patient.id}/', patch_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.existing_patient.refresh_from_db()
        self.assertEqual(self.existing_patient.address, "Updated Address 99, Varthur Colony")
        self.assertEqual(self.existing_patient.mobile, "9876599999")
        self.assertEqual(self.existing_patient.emergency_contact, "Father - 9876588888")

    def test_09_compounder_cannot_update_protected_clinical_fields(self):
        self.client.force_authenticate(user=self.user_cmp)
        # Attempt to modify name, patient_id, or injection of clinical fields
        illegal_payload = {
            "name": "Tampered Name",
            "diagnosis": "Forged Diagnosis"
        }
        res = self.client.patch(f'/api/v1/patients/{self.existing_patient.id}/', illegal_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)
        self.existing_patient.refresh_from_db()
        self.assertEqual(self.existing_patient.name, "Aarav Sharma")

    def test_10_hospital_admin_demographic_update_works_within_facility_scope(self):
        self.client.force_authenticate(user=self.user_adm)
        res = self.client.patch(
            f'/api/v1/patients/{self.existing_patient.id}/',
            {"address": "Admin Verified Address"},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.existing_patient.refresh_from_db()
        self.assertEqual(self.existing_patient.address, "Admin Verified Address")

    def test_11_cross_facility_demographic_mutation_is_rejected(self):
        # Patient registered at Facility B
        patient_b = Patient.objects.create(
            patient_id="PAT-BASE-002",
            name="Whitefield Resident",
            age=35,
            gender="FEMALE",
            mobile="9876500099",
            address="Whitefield Road",
            registered_at_facility=self.facility_b,
            ward=self.ward_2,
            district=self.district
        )
        # Compounder assigned strictly to Facility A tries to mutate patient at Facility B
        self.client.force_authenticate(user=self.user_cmp)
        res = self.client.patch(
            f'/api/v1/patients/{patient_b.id}/',
            {"address": "Cross Facility Hijack"},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        patient_b.refresh_from_db()
        self.assertEqual(patient_b.address, "Whitefield Road")

    def test_12_duplicate_patient_returns_http_409(self):
        self.client.force_authenticate(user=self.user_cmp)
        # Existing patient has: name="Aarav Sharma", mobile="9876500001", facility=self.facility_a
        # Duplicate with different whitespace and formatting
        duplicate_payload = {
            "name": "  aarav   sharma  ",
            "age": 28,
            "gender": "MALE",
            "mobile": " 98765-00001 ",
            "address": "Duplicate Address",
            "registered_at_facility": self.facility_a.id,
            "ward": self.ward_1.id
        }
        res = self.client.post('/api/v1/patients/', duplicate_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already registered", res.data['detail'])

    def test_13_blank_abha_remains_blank(self):
        self.client.force_authenticate(user=self.user_cmp)
        payload = {
            "name": "Gita Devi",
            "age": 60,
            "gender": "FEMALE",
            "mobile": "9876500111",
            "address": "Slum Colony 4",
            "registered_at_facility": self.facility_a.id,
            "ward": self.ward_1.id,
            "ABHA_ID_DEMO": ""  # Explicit blank
        }
        res = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['ABHA_ID_DEMO'], "")
        p = Patient.objects.get(pk=res.data['id'])
        self.assertEqual(p.ABHA_ID_DEMO, "")

    def test_14_existing_patient_search_continues_working(self):
        self.client.force_authenticate(user=self.user_cmp)
        # Search by mobile number
        res_search_mob = self.client.get('/api/v1/patients/?search=9876500001')
        self.assertEqual(res_search_mob.status_code, status.HTTP_200_OK)
        results = res_search_mob.data['results'] if 'results' in res_search_mob.data else res_search_mob.data
        self.assertTrue(any(p['name'] == "Aarav Sharma" for p in results))

        # Search by name
        res_search_name = self.client.get('/api/v1/patients/?search=Aarav')
        self.assertEqual(res_search_name.status_code, status.HTTP_200_OK)
        results_name = res_search_name.data['results'] if 'results' in res_search_name.data else res_search_name.data
        self.assertTrue(any(p['name'] == "Aarav Sharma" for p in results_name))


import concurrent.futures
from django.test import TransactionTestCase
from django.db import connection


class PatientConcurrencyAndDuplicateRegressionTests(TransactionTestCase):
    """
    Real PostgreSQL Concurrency and Duplicate Boundary Regression Suite (Phase 27A-R1).
    Runs with TransactionTestCase to permit multi-threaded concurrent database connections.
    """

    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        # Geography & Facilities
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.zone = Zone.objects.create(name="East Zone", district=self.district)
        self.ward_1 = Ward.objects.create(name="Ward 201", ward_number=201, zone=self.zone)
        self.ward_2 = Ward.objects.create(name="Ward 202", ward_number=202, zone=self.zone)

        self.facility_1 = Facility.objects.create(
            facility_code="PHC-CONC-01",
            facility_name="Concurrency PHC 1",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            ward=self.ward_1,
            status="ACTIVE"
        )
        self.facility_2 = Facility.objects.create(
            facility_code="PHC-CONC-02",
            facility_name="Concurrency PHC 2",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            ward=self.ward_2,
            status="ACTIVE"
        )

        # Front Desk Officer assigned to Facility 1
        role_compounder = RoleMaster.objects.get(code="FRONT_DESK_OFFICER")
        p_cmp1 = Person.objects.create(first_name="Comp", last_name="One", gender="MALE", date_of_birth="1991-01-01")
        staff_cmp1 = StaffProfile.objects.create(person=p_cmp1, employee_id="EMP-CMP-C1", designation="Front Desk Officer", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=staff_cmp1, role=role_compounder, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=staff_cmp1, facility=self.facility_1, is_primary=True, is_active=True)
        self.user_cmp1 = User.objects.create_user(
            username="test_cmp_c1", password="password123",
            role="FRONT_DESK_OFFICER", assigned_facility=self.facility_1, staff_profile=staff_cmp1
        )

        # Front Desk Officer assigned to Facility 2
        p_cmp2 = Person.objects.create(first_name="Comp", last_name="Two", gender="FEMALE", date_of_birth="1992-02-02")
        staff_cmp2 = StaffProfile.objects.create(person=p_cmp2, employee_id="EMP-CMP-C2", designation="Front Desk Officer", status="ACTIVE")
        StaffRoleAssignment.objects.create(staff=staff_cmp2, role=role_compounder, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=staff_cmp2, facility=self.facility_2, is_primary=True, is_active=True)
        self.user_cmp2 = User.objects.create_user(
            username="test_cmp_c2", password="password123",
            role="FRONT_DESK_OFFICER", assigned_facility=self.facility_2, staff_profile=staff_cmp2
        )

    def test_same_facility_same_name_same_mobile_duplicate_returns_409(self):
        self.client.force_authenticate(user=self.user_cmp1)
        payload = {
            "name": "Kavitha Ramesh",
            "age": 29,
            "gender": "FEMALE",
            "mobile": "9812300001",
            "address": "100 MG Road",
            "registered_at_facility": self.facility_1.id
        }
        res1 = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second attempt with same normalized identity at same facility
        res2 = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already registered", res2.data['detail'])

    def test_same_facility_different_mobile_allowed(self):
        self.client.force_authenticate(user=self.user_cmp1)
        payload1 = {
            "name": "Same Name Person",
            "age": 40,
            "gender": "MALE",
            "mobile": "9812300002",
            "address": "Addr 1",
            "registered_at_facility": self.facility_1.id
        }
        res1 = self.client.post('/api/v1/patients/', payload1, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        payload2 = {
            "name": "Same Name Person",
            "age": 42,
            "gender": "MALE",
            "mobile": "9812300003",  # Different mobile
            "address": "Addr 2",
            "registered_at_facility": self.facility_1.id
        }
        res2 = self.client.post('/api/v1/patients/', payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_same_facility_different_name_allowed(self):
        self.client.force_authenticate(user=self.user_cmp1)
        payload1 = {
            "name": "First Family Member",
            "age": 30,
            "gender": "FEMALE",
            "mobile": "9812300004",  # Shared household mobile
            "address": "Addr 1",
            "registered_at_facility": self.facility_1.id
        }
        res1 = self.client.post('/api/v1/patients/', payload1, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        payload2 = {
            "name": "Second Family Member",
            "age": 10,
            "gender": "MALE",
            "mobile": "9812300004",  # Same mobile, different name
            "address": "Addr 1",
            "registered_at_facility": self.facility_1.id
        }
        res2 = self.client.post('/api/v1/patients/', payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_different_facility_same_identity_allowed(self):
        # Patient registered at Facility 1
        self.client.force_authenticate(user=self.user_cmp1)
        payload = {
            "name": "Statewide Resident",
            "age": 35,
            "gender": "FEMALE",
            "mobile": "9812300005",
            "address": "Common Street",
            "registered_at_facility": self.facility_1.id
        }
        res1 = self.client.post('/api/v1/patients/', payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Patient registered at Facility 2 with same name and mobile
        self.client.force_authenticate(user=self.user_cmp2)
        payload2 = dict(payload)
        payload2["registered_at_facility"] = self.facility_2.id
        res2 = self.client.post('/api/v1/patients/', payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_name_and_mobile_normalization_variants_rejected_as_conflict(self):
        self.client.force_authenticate(user=self.user_cmp1)
        base_payload = {
            "name": "Venkatesh Prasad",
            "age": 48,
            "gender": "MALE",
            "mobile": "9812300006",
            "address": "Koramangala 4th Block",
            "registered_at_facility": self.facility_1.id
        }
        res1 = self.client.post('/api/v1/patients/', base_payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Variant with whitespace and case differences in name
        variant_name_payload = {
            "name": "   venkatesh     PRASAD  ",
            "age": 48,
            "gender": "MALE",
            "mobile": "9812300006",
            "address": "Koramangala 4th Block",
            "registered_at_facility": self.facility_1.id
        }
        res2 = self.client.post('/api/v1/patients/', variant_name_payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already registered", res2.data['detail'])

        # Variant with country code +91 and dashes in mobile
        variant_mobile_payload = {
            "name": "Venkatesh Prasad",
            "age": 48,
            "gender": "MALE",
            "mobile": "+91-98123-00006",
            "address": "Koramangala 4th Block",
            "registered_at_facility": self.facility_1.id
        }
        res3 = self.client.post('/api/v1/patients/', variant_mobile_payload, format='json')
        self.assertEqual(res3.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already registered", res3.data['detail'])

    def test_concurrent_duplicate_registration_real_postgresql(self):
        """
        Spawns multiple simultaneous threads attempting to register the exact same patient.
        PostgreSQL advisory xact lock and UniqueConstraint guarantee exactly 1 succeeds and
        all other concurrent attempts receive HTTP 409 Conflict.
        """
        target_name = "Concurrent Race Patient"
        target_mobile = "9812300099"
        num_workers = 5

        def submit_registration(worker_id):
            connection.close()
            worker_client = APIClient()
            worker_client.force_authenticate(user=self.user_cmp1)
            payload = {
                "name": f"  {target_name.upper()}  ",
                "age": 32,
                "gender": "OTHER",
                "mobile": f"+91-{target_mobile[:5]}-{target_mobile[5:]}",
                "address": f"Worker {worker_id} concurrency road",
                "registered_at_facility": self.facility_1.id
            }
            res = worker_client.post('/api/v1/patients/', payload, format='json')
            return worker_id, res.status_code, res.data

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(submit_registration, i) for i in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        status_codes = [r[1] for r in results]
        count_201 = status_codes.count(status.HTTP_201_CREATED)
        count_409 = status_codes.count(status.HTTP_409_CONFLICT)

        self.assertEqual(count_201, 1, f"Exactly one request must succeed with 201 Created. Got: {status_codes}")
        self.assertEqual(count_409, num_workers - 1, f"All other {num_workers - 1} requests must receive 409 Conflict. Got: {status_codes}")

        # Invariant verification: Exactly ONE patient exists matching normalized identity
        matching_patients = Patient.objects.filter(
            registered_at_facility=self.facility_1,
            normalized_name="concurrent race patient",
            normalized_mobile="9812300099"
        )
        self.assertEqual(matching_patients.count(), 1, "Database must contain exactly 1 patient matching normalized identity")

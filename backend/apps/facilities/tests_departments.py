import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment, User
)
from apps.accounts.services import seed_roles_and_permissions
from apps.geography.models import State, District
from apps.facilities.models import Facility, Department


class DepartmentAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        # Geography
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_a = District.objects.create(name='Bengaluru Urban', code='KA-BLR-U', state=self.state)
        self.district_b = District.objects.create(name='Mysuru', code='KA-MYS', state=self.state)

        # Facilities
        self.facility_a = Facility.objects.create(
            facility_code='FAC-BLR-01',
            facility_name='Bengaluru Core PHC',
            facility_type='NAMMA_CLINIC',
            district=self.district_a,
            state=self.state,
            status='ACTIVE'
        )
        self.facility_b = Facility.objects.create(
            facility_code='FAC-MYS-01',
            facility_name='Mysuru Core PHC',
            facility_type='NAMMA_CLINIC',
            district=self.district_b,
            state=self.state,
            status='ACTIVE'
        )

        # Existing departments
        self.dept_a = Department.objects.create(facility=self.facility_a, code='OPD', name='General OPD')
        self.dept_b = Department.objects.create(facility=self.facility_b, code='OPD', name='General OPD')

        # DHO User (District A)
        self.person_dho = Person.objects.create(first_name='District', last_name='Officer', date_of_birth=datetime.date(1980, 1, 1), gender='MALE')
        self.staff_dho = StaffProfile.objects.create(person=self.person_dho, employee_id='EMP-DHO-01', designation='District Health Officer', status='ACTIVE')
        self.user_dho = User.objects.create_user(username='dho_blr', password='Password123!', role='DISTRICT_OFFICER', assigned_district=self.district_a, staff_profile=self.staff_dho)
        role_dho = RoleMaster.objects.get(code='DISTRICT_OFFICER')
        StaffRoleAssignment.objects.create(staff=self.staff_dho, role=role_dho, is_active=True)

        # Hospital Admin User (Facility A)
        self.person_admin = Person.objects.create(first_name='Hospital', last_name='Admin', date_of_birth=datetime.date(1985, 1, 1), gender='MALE')
        self.staff_admin = StaffProfile.objects.create(person=self.person_admin, employee_id='EMP-ADMIN-01', designation='Hospital Administrator', status='ACTIVE')
        self.user_admin = User.objects.create_user(username='admin_fac_a', password='Password123!', role='HOSPITAL_ADMIN', assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_admin)
        role_admin = RoleMaster.objects.get(code='HOSPITAL_ADMIN')
        StaffRoleAssignment.objects.create(staff=self.staff_admin, role=role_admin, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_admin, facility=self.facility_a, is_primary=True, is_active=True)

        # Clinical Doctor User (Facility A)
        self.person_doc = Person.objects.create(first_name='Clinical', last_name='Doctor', date_of_birth=datetime.date(1990, 1, 1), gender='FEMALE')
        self.staff_doc = StaffProfile.objects.create(person=self.person_doc, employee_id='EMP-DOC-01', designation='Medical Officer', status='ACTIVE')
        self.user_doc = User.objects.create_user(username='doc_fac_a', password='Password123!', role='DOCTOR', assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_doc)
        role_doc = RoleMaster.objects.get(code='DOCTOR')
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=role_doc, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)

    def test_01_standard_departments_auto_provisioned_on_facility_create(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            'facility_code': 'FAC-BLR-NEW-01',
            'facility_name': 'New Jayanagar Clinic',
            'facility_type': 'NAMMA_CLINIC',
            'district': self.district_a.id,
            'status': 'ACTIVE'
        }
        res = self.client.post('/api/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_fac = Facility.objects.get(facility_code='FAC-BLR-NEW-01')

        # Check standard 4 departments provisioned
        depts = Department.objects.filter(facility=new_fac)
        dept_codes = set(depts.values_list('code', flat=True))
        self.assertEqual(dept_codes, {'OPD', 'PHARM', 'LAB', 'TRIAGE'})

    def test_02_hospital_admin_can_create_department_for_own_facility(self):
        self.client.force_authenticate(user=self.user_admin)
        payload = {
            'facility': self.facility_a.id,
            'code': 'DENTAL',
            'name': 'Dental Clinic',
            'is_active': True
        }
        res = self.client.post('/api/v1/organization/departments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Department.objects.filter(facility=self.facility_a, code='DENTAL').exists())

    def test_03_hospital_admin_cannot_create_department_for_foreign_facility_403(self):
        self.client.force_authenticate(user=self.user_admin)
        payload = {
            'facility': self.facility_b.id,
            'code': 'DENTAL',
            'name': 'Dental Clinic',
            'is_active': True
        }
        res = self.client.post('/api/v1/organization/departments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Department.objects.filter(facility=self.facility_b, code='DENTAL').exists())

    def test_04_hospital_admin_can_update_own_department(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.patch(f'/api/v1/organization/departments/{self.dept_a.id}/', {'name': 'General Medicine & OPD'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.dept_a.refresh_from_db()
        self.assertEqual(self.dept_a.name, 'General Medicine & OPD')

    def test_05_hospital_admin_cannot_update_foreign_department_403(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.patch(f'/api/v1/organization/departments/{self.dept_b.id}/', {'name': 'Hacked Department'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.dept_b.refresh_from_db()
        self.assertEqual(self.dept_b.name, 'General OPD')

    def test_06_hospital_admin_cannot_delete_foreign_department_403(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.delete(f'/api/v1/organization/departments/{self.dept_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Department.objects.filter(id=self.dept_b.id).exists())

    def test_07_hospital_admin_can_delete_own_department(self):
        dept_to_delete = Department.objects.create(facility=self.facility_a, code='TEMP', name='Temporary Dept')
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.delete(f'/api/v1/organization/departments/{dept_to_delete.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Department.objects.filter(id=dept_to_delete.id).exists())

    def test_08_clinical_staff_cannot_create_or_mutate_departments_403(self):
        self.client.force_authenticate(user=self.user_doc)
        res = self.client.post('/api/v1/organization/departments/', {'facility': self.facility_a.id, 'code': 'NEW', 'name': 'New'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/v1/organization/departments/{self.dept_a.id}/', {'name': 'Doc Mod'}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_dho_cannot_create_department_outside_district_403(self):
        self.client.force_authenticate(user=self.user_dho)
        # Facility B is in District B (Mysuru); DHO is assigned to District A (Bengaluru Urban)
        payload = {
            'facility': self.facility_b.id,
            'code': 'DHO-CROSS',
            'name': 'Cross District Dept'
        }
        res = self.client.post('/api/v1/organization/departments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_10_hospital_admin_department_list_scoped_to_own_facility(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.get('/api/v1/organization/departments/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        fac_ids = {d['facility'] for d in results}
        self.assertEqual(fac_ids, {self.facility_a.id})

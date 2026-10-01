import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment, User
)
from apps.accounts.services import seed_roles_and_permissions
from apps.geography.models import State, District
from apps.facilities.models import Facility


class FacilityAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        # Geography
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_a = District.objects.create(name='Bengaluru Urban', code='KA-BLR-U', state=self.state)
        self.district_b = District.objects.create(name='Mysuru', code='KA-MYS', state=self.state)

        # Baseline Facilities
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

        # Role Master
        self.role_dho = RoleMaster.objects.get(code='DISTRICT_OFFICER')
        self.role_admin = RoleMaster.objects.get(code='HOSPITAL_ADMIN')
        self.role_doc = RoleMaster.objects.get(code='DOCTOR')
        self.role_nurse = RoleMaster.objects.get(code='NURSE')
        self.role_compounder = RoleMaster.objects.get(code='COMPOUNDER')
        self.role_lab = RoleMaster.objects.get(code='LAB_TECHNICIAN')
        self.role_pharm = RoleMaster.objects.get(code='PHARMACIST')

        # 1. DHO User (District A)
        p_dho = Person.objects.create(first_name='DHO', last_name='User', gender='MALE', date_of_birth='1975-01-01')
        self.staff_dho = StaffProfile.objects.create(person=p_dho, employee_id='EMP-DHO-01', designation='District Health Officer', status='ACTIVE')
        self.user_dho = User.objects.create_user(
            username='test_dho', password='password123', full_name='Dr. DHO',
            role='DISTRICT_OFFICER', assigned_district=self.district_a, staff_profile=self.staff_dho
        )
        StaffRoleAssignment.objects.create(staff=self.staff_dho, role=self.role_dho, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 2. Hospital Admin User (Assigned to Facility A)
        p_adm = Person.objects.create(first_name='Hospital', last_name='Admin', gender='FEMALE', date_of_birth='1980-05-15')
        self.staff_admin = StaffProfile.objects.create(person=p_adm, employee_id='EMP-ADM-01', designation='Hospital Administrator', status='ACTIVE')
        self.user_admin = User.objects.create_user(
            username='test_admin', password='password123', full_name='Clinic Admin',
            role='HOSPITAL_ADMIN', assigned_facility=self.facility_a, staff_profile=self.staff_admin
        )
        StaffRoleAssignment.objects.create(staff=self.staff_admin, role=self.role_admin, effective_from=datetime.date(2026, 1, 1), is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_admin, facility=self.facility_a, is_primary=True, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 3. Nurse User
        p_nurse = Person.objects.create(first_name='Nurse', last_name='Staff', gender='FEMALE', date_of_birth='1990-02-02')
        self.staff_nurse = StaffProfile.objects.create(person=p_nurse, employee_id='EMP-NURSE-01', designation='Staff Nurse', status='ACTIVE')
        self.user_nurse = User.objects.create_user(
            username='test_nurse', password='password123', full_name='Staff Nurse',
            role='NURSE', assigned_facility=self.facility_a, staff_profile=self.staff_nurse
        )
        StaffRoleAssignment.objects.create(staff=self.staff_nurse, role=self.role_nurse, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 4. Doctor User
        p_doc = Person.objects.create(first_name='Doctor', last_name='Staff', gender='MALE', date_of_birth='1985-03-03')
        self.staff_doc = StaffProfile.objects.create(person=p_doc, employee_id='EMP-DOC-01', designation='Medical Officer', status='ACTIVE')
        self.user_doc = User.objects.create_user(
            username='test_doc', password='password123', full_name='Dr. Staff',
            role='DOCTOR', assigned_facility=self.facility_a, staff_profile=self.staff_doc
        )
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=self.role_doc, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 5. Compounder User
        p_cmp = Person.objects.create(first_name='Compounder', last_name='Staff', gender='MALE', date_of_birth='1992-04-04')
        self.staff_cmp = StaffProfile.objects.create(person=p_cmp, employee_id='EMP-CMP-01', designation='Compounder', status='ACTIVE')
        self.user_cmp = User.objects.create_user(
            username='test_cmp', password='password123', full_name='Compounder Staff',
            role='COMPOUNDER', assigned_facility=self.facility_a, staff_profile=self.staff_cmp
        )
        StaffRoleAssignment.objects.create(staff=self.staff_cmp, role=self.role_compounder, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 6. Lab Technician User
        p_lab = Person.objects.create(first_name='Lab', last_name='Tech', gender='FEMALE', date_of_birth='1988-06-06')
        self.staff_lab = StaffProfile.objects.create(person=p_lab, employee_id='EMP-LAB-01', designation='Lab Technician', status='ACTIVE')
        self.user_lab = User.objects.create_user(
            username='test_lab', password='password123', full_name='Lab Tech',
            role='LAB_TECHNICIAN', assigned_facility=self.facility_a, staff_profile=self.staff_lab
        )
        StaffRoleAssignment.objects.create(staff=self.staff_lab, role=self.role_lab, effective_from=datetime.date(2026, 1, 1), is_active=True)

        # 7. Pharmacist User
        p_pharm = Person.objects.create(first_name='Pharma', last_name='Staff', gender='FEMALE', date_of_birth='1987-07-07')
        self.staff_pharm = StaffProfile.objects.create(person=p_pharm, employee_id='EMP-PHARM-01', designation='Pharmacist', status='ACTIVE')
        self.user_pharm = User.objects.create_user(
            username='test_pharm', password='password123', full_name='Pharmacist',
            role='PHARMACIST', assigned_facility=self.facility_a, staff_profile=self.staff_pharm
        )
        StaffRoleAssignment.objects.create(staff=self.staff_pharm, role=self.role_pharm, effective_from=datetime.date(2026, 1, 1), is_active=True)

    def test_01_dho_can_create_facility_in_assigned_district(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            'facility_code': 'NC-DHO-01',
            'facility_name': 'Namma Clinic Ward 101',
            'facility_type': 'NAMMA_CLINIC',
            'district': self.district_a.id,
            'state': self.state.id,
            'status': 'ACTIVE'
        }
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        fac = Facility.objects.get(facility_code='NC-DHO-01')
        self.assertEqual(fac.district_id, self.district_a.id)

    def test_02_dho_cannot_create_facility_outside_assigned_district(self):
        self.client.force_authenticate(user=self.user_dho)
        payload = {
            'facility_code': 'NC-DHO-OUTSIDE',
            'facility_name': 'Unauthorized Dist Clinic',
            'facility_type': 'NAMMA_CLINIC',
            'district': self.district_b.id,
            'state': self.state.id,
            'status': 'ACTIVE'
        }
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Facility.objects.filter(facility_code='NC-DHO-OUTSIDE').exists())

    def test_03_hospital_admin_receives_403_on_facility_create(self):
        self.client.force_authenticate(user=self.user_admin)
        payload = {
            'facility_code': 'NC-HA-FORBIDDEN',
            'facility_name': 'Admin Attempted Clinic',
            'facility_type': 'NAMMA_CLINIC',
            'district': self.district_a.id,
            'state': self.state.id,
            'status': 'ACTIVE'
        }
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Facility.objects.filter(facility_code='NC-HA-FORBIDDEN').exists())

    def test_04_hospital_admin_receives_403_on_unauthorized_facility_mutation(self):
        self.client.force_authenticate(user=self.user_admin)
        res_patch = self.client.patch(
            f'/api/v1/organization/facilities/{self.facility_a.id}/',
            {'facility_name': 'Tampered Facility Name'},
            format='json'
        )
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f'/api/v1/organization/facilities/{self.facility_a.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    def test_05_nurse_receives_403(self):
        self.client.force_authenticate(user=self.user_nurse)
        payload = {'facility_code': 'NC-NURSE-01', 'facility_name': 'Nurse Clinic', 'district': self.district_a.id}
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_doctor_receives_403(self):
        self.client.force_authenticate(user=self.user_doc)
        payload = {'facility_code': 'NC-DOC-01', 'facility_name': 'Doc Clinic', 'district': self.district_a.id}
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_compounder_receives_403(self):
        self.client.force_authenticate(user=self.user_cmp)
        payload = {'facility_code': 'NC-CMP-01', 'facility_name': 'Cmp Clinic', 'district': self.district_a.id}
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_lab_technician_receives_403(self):
        self.client.force_authenticate(user=self.user_lab)
        payload = {'facility_code': 'NC-LAB-01', 'facility_name': 'Lab Clinic', 'district': self.district_a.id}
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_pharmacist_receives_403(self):
        self.client.force_authenticate(user=self.user_pharm)
        payload = {'facility_code': 'NC-PHARM-01', 'facility_name': 'Pharm Clinic', 'district': self.district_a.id}
        res = self.client.post('/api/v1/organization/facilities/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_10_dho_can_mutate_facility_in_assigned_district(self):
        self.client.force_authenticate(user=self.user_dho)
        res = self.client.patch(
            f'/api/v1/organization/facilities/{self.facility_a.id}/',
            {'facility_name': 'Updated Bengaluru PHC'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.facility_a.refresh_from_db()
        self.assertEqual(self.facility_a.facility_name, 'Updated Bengaluru PHC')

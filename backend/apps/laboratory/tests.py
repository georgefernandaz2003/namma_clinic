from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.laboratory.models import LabTestMaster

User = get_user_model()

class LabTestMasterRBACSecurityTests(APITestCase):
    def setUp(self):
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.facility = Facility.objects.create(
            facility_code='FAC-LAB-01',
            facility_name='Namma Clinic Lab Facility',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district
        )

        self.hospital_admin = User.objects.create_user(
            username='admin_user',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility,
            full_name='Hospital Admin User'
        )

        self.lab_tech = User.objects.create_user(
            username='lab_tech_user',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility,
            full_name='Lab Tech User'
        )

        self.doctor = User.objects.create_user(
            username='doctor_user',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility,
            full_name='Doctor User'
        )

        self.nurse = User.objects.create_user(
            username='nurse_user',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility,
            full_name='Nurse User'
        )

        self.pharmacist = User.objects.create_user(
            username='pharmacist_user',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility,
            full_name='Pharmacist User'
        )

        self.district_officer = User.objects.create_user(
            username='district_officer_user',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district,
            full_name='District Officer User'
        )

        self.test_master = LabTestMaster.objects.create(
            code='LBN-001',
            name='Complete Blood Count',
            category='Hematology',
            reference_range='12 - 16 g/dL',
            unit='g/dL'
        )

    # A. Anonymous user cannot access LabTestMaster
    def test_anonymous_user_cannot_list_lab_tests(self):
        res = self.client.get('/api/lab/tests/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_create_lab_test(self):
        res = self.client.post('/api/lab/tests/', {
            'code': 'LBN-ANON',
            'name': 'Anon Test'
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_get_detail_lab_test(self):
        res = self.client.get(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # B. Hospital Admin: can list/view, create, update, partially update, delete
    def test_hospital_admin_can_list_and_view_lab_tests(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res_list = self.client.get('/api/lab/tests/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_detail = self.client.get(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['code'], 'LBN-001')

    def test_hospital_admin_can_create_lab_test(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.post('/api/lab/tests/', {
            'code': 'LBN-002',
            'name': 'Fasting Blood Sugar',
            'category': 'Biochemistry',
            'reference_range': '70 - 100 mg/dL',
            'unit': 'mg/dL'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(LabTestMaster.objects.filter(code='LBN-002').exists())

    def test_hospital_admin_can_update_lab_test(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.put(f'/api/lab/tests/{self.test_master.id}/', {
            'code': 'LBN-001',
            'name': 'Complete Blood Count Updated',
            'category': 'Hematology',
            'reference_range': '11.5 - 16.5 g/dL',
            'unit': 'g/dL'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.test_master.refresh_from_db()
        self.assertEqual(self.test_master.name, 'Complete Blood Count Updated')

    def test_hospital_admin_can_partially_update_lab_test(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {
            'reference_range': '13 - 17 g/dL'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.test_master.refresh_from_db()
        self.assertEqual(self.test_master.reference_range, '13 - 17 g/dL')

    def test_hospital_admin_can_delete_lab_test(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LabTestMaster.objects.filter(id=self.test_master.id).exists())

    # C. Lab Technician: can view/list, cannot create, update, delete
    def test_lab_technician_can_view_and_list_lab_tests(self):
        self.client.force_authenticate(user=self.lab_tech)
        res_list = self.client.get('/api/lab/tests/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_detail = self.client.get(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)

    def test_lab_technician_cannot_create_lab_test(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.post('/api/lab/tests/', {
            'code': 'LBN-003',
            'name': 'Serum Creatinine',
            'category': 'Biochemistry'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(LabTestMaster.objects.filter(code='LBN-003').exists())

    def test_lab_technician_cannot_update_lab_test(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.put(f'/api/lab/tests/{self.test_master.id}/', {
            'code': 'LBN-001',
            'name': 'Hacked by Lab Tech'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.test_master.refresh_from_db()
        self.assertEqual(self.test_master.name, 'Complete Blood Count')

    def test_lab_technician_cannot_partially_update_lab_test(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {
            'name': 'Hacked by Lab Tech'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.test_master.refresh_from_db()
        self.assertEqual(self.test_master.name, 'Complete Blood Count')

    def test_lab_technician_cannot_delete_lab_test(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(LabTestMaster.objects.filter(id=self.test_master.id).exists())

    # D. Doctor: cannot mutate LabTestMaster, existing lab_orders/lab_results intact
    def test_doctor_cannot_mutate_lab_test(self):
        self.client.force_authenticate(user=self.doctor)
        res_post = self.client.post('/api/lab/tests/', {'code': 'LBN-DOC', 'name': 'Doc Test'})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_put = self.client.put(f'/api/lab/tests/{self.test_master.id}/', {'code': 'LBN-001', 'name': 'Doc Update'})
        self.assertEqual(res_put.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {'name': 'Doc Patch'})
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_existing_lab_orders_permissions_intact(self):
        self.assertIn('lab_orders.view', ROLE_PERMISSIONS['DOCTOR'])
        self.assertIn('lab_orders.create', ROLE_PERMISSIONS['DOCTOR'])
        self.assertIn('lab_orders.update', ROLE_PERMISSIONS['DOCTOR'])
        self.assertIn('lab_results.view', ROLE_PERMISSIONS['DOCTOR'])

    # E. Nurse: cannot mutate LabTestMaster
    def test_nurse_cannot_mutate_lab_test(self):
        self.client.force_authenticate(user=self.nurse)
        res_post = self.client.post('/api/lab/tests/', {'code': 'LBN-NURSE', 'name': 'Nurse Test'})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {'name': 'Nurse Patch'})
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    # F. Pharmacist: cannot mutate LabTestMaster
    def test_pharmacist_cannot_mutate_lab_test(self):
        self.client.force_authenticate(user=self.pharmacist)
        res_post = self.client.post('/api/lab/tests/', {'code': 'LBN-PHARM', 'name': 'Pharm Test'})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {'name': 'Pharm Patch'})
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    # G. District Officer: cannot mutate LabTestMaster
    def test_district_officer_cannot_mutate_lab_test(self):
        self.client.force_authenticate(user=self.district_officer)
        res_post = self.client.post('/api/lab/tests/', {'code': 'LBN-DO', 'name': 'DO Test'})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/lab/tests/{self.test_master.id}/', {'name': 'DO Patch'})
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f'/api/lab/tests/{self.test_master.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    # H. Permission mapping verification: create/update/delete granted ONLY to HOSPITAL_ADMIN
    def test_lab_test_master_permission_mapping(self):
        # View permission: HOSPITAL_ADMIN and LAB_TECHNICIAN only
        self.assertIn('lab_test_master.view', ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
        self.assertIn('lab_test_master.view', ROLE_PERMISSIONS['LAB_TECHNICIAN'])
        self.assertNotIn('lab_test_master.view', ROLE_PERMISSIONS['DISTRICT_OFFICER'])
        self.assertNotIn('lab_test_master.view', ROLE_PERMISSIONS['DOCTOR'])
        self.assertNotIn('lab_test_master.view', ROLE_PERMISSIONS['NURSE'])
        self.assertNotIn('lab_test_master.view', ROLE_PERMISSIONS['PHARMACIST'])

        # Mutation permissions: HOSPITAL_ADMIN ONLY
        for perm in ['lab_test_master.create', 'lab_test_master.update', 'lab_test_master.delete']:
            self.assertIn(perm, ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['LAB_TECHNICIAN'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DISTRICT_OFFICER'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DOCTOR'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['NURSE'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['PHARMACIST'])

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.pharmacy.models import MedicineMaster

User = get_user_model()

class MedicineMasterRBACSecurityTests(APITestCase):
    def setUp(self):
        # Setup Geography & Facility
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.facility = Facility.objects.create(
            facility_code='FAC-001',
            facility_name='Namma Clinic Jayanagar',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district
        )

        # Setup Users for each role
        self.pharmacist = User.objects.create_user(
            username='pharmacist_user',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility,
            full_name='Pharmacist User'
        )

        self.hospital_admin = User.objects.create_user(
            username='hospital_admin_user',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility,
            full_name='Hospital Admin User'
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

        self.lab_tech = User.objects.create_user(
            username='lab_tech_user',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility,
            full_name='Lab Technician User'
        )

        self.district_officer = User.objects.create_user(
            username='district_officer_user',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district,
            full_name='District Officer User'
        )

        # Create baseline MedicineMaster
        self.medicine = MedicineMaster.objects.create(
            generic_name='Paracetamol',
            brand_name='Dolo 650',
            strength='650 mg',
            dosage_form='Tablet',
            unit='Tablets',
            category='Analgesic',
            minimum_stock=50,
            reorder_level=100
        )

    # 1. Unauthenticated user checks
    def test_unauthenticated_user_cannot_create_medicine(self):
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Ibuprofen',
            'brand_name': 'Brufen',
            'strength': '400 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'NSAID',
            'minimum_stock': 20,
            'reorder_level': 40
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_list_medicines(self):
        res = self.client.get('/api/pharmacy/medicines/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. DOCTOR cannot mutate medicine master
    def test_doctor_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox',
            'strength': '500 mg',
            'dosage_form': 'Capsule',
            'unit': 'Capsules',
            'category': 'Antibiotic',
            'minimum_stock': 30,
            'reorder_level': 60
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'brand_name': 'Hacked Brand'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.brand_name, 'Dolo 650')

    def test_doctor_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MedicineMaster.objects.filter(id=self.medicine.id).exists())

    # 3. NURSE cannot mutate medicine master
    def test_nurse_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'Modified by Nurse'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 4. LAB_TECHNICIAN cannot mutate medicine master
    def test_lab_technician_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_technician_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'Modified by Lab'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_technician_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 5. Authorized role (PHARMACIST) can create, update, delete
    def test_pharmacist_can_create_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Metformin HCl',
            'brand_name': 'Glycomet',
            'strength': '500 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'Anti-Diabetic',
            'minimum_stock': 50,
            'reorder_level': 100
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MedicineMaster.objects.filter(generic_name='Metformin HCl').exists())

    def test_pharmacist_can_patch_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'brand_name': 'Calpol 650',
            'reorder_level': 150
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.brand_name, 'Calpol 650')
        self.assertEqual(self.medicine.reorder_level, 150)

    def test_pharmacist_can_delete_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MedicineMaster.objects.filter(id=self.medicine.id).exists())

    # 5b. Authorized role (HOSPITAL_ADMIN) can create, update, delete
    def test_hospital_admin_can_manage_medicine(self):
        self.client.force_authenticate(user=self.hospital_admin)
        # Create
        res_post = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amlodipine',
            'brand_name': 'Amlopres',
            'strength': '5 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'Anti-Hypertensive',
            'minimum_stock': 20,
            'reorder_level': 40
        })
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        med_id = res_post.data['id']

        # Patch
        res_patch = self.client.patch(f'/api/pharmacy/medicines/{med_id}/', {
            'strength': '10 mg'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)

        # Delete
        res_del = self.client.delete(f'/api/pharmacy/medicines/{med_id}/')
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)

    # 6. Unauthorized role (DISTRICT_OFFICER) direct object mutation is blocked
    def test_district_officer_cannot_patch_or_delete_medicine(self):
        self.client.force_authenticate(user=self.district_officer)
        res_patch = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'DO Mutated'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_delete = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Permission mapping verification
    def test_medicine_master_permission_mapping(self):
        # View permission
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['DISTRICT_OFFICER'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['DOCTOR'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['PHARMACIST'])
        self.assertNotIn('medicine_master.view', ROLE_PERMISSIONS['NURSE'])
        self.assertNotIn('medicine_master.view', ROLE_PERMISSIONS['LAB_TECHNICIAN'])

        # Create/Update/Delete permissions exist only for authorized roles
        for perm in ['medicine_master.create', 'medicine_master.update', 'medicine_master.delete']:
            self.assertIn(perm, ROLE_PERMISSIONS['PHARMACIST'])
            self.assertIn(perm, ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DISTRICT_OFFICER'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DOCTOR'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['NURSE'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['LAB_TECHNICIAN'])

    # 8. Read access verification across roles
    def test_read_access_for_authorized_readers(self):
        for user in [self.doctor, self.pharmacist, self.hospital_admin, self.district_officer]:
            self.client.force_authenticate(user=user)
            res = self.client.get('/api/pharmacy/medicines/')
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Failed for {user.role}")
            res_detail = self.client.get(f'/api/pharmacy/medicines/{self.medicine.id}/')
            self.assertEqual(res_detail.status_code, status.HTTP_200_OK, f"Detail failed for {user.role}")

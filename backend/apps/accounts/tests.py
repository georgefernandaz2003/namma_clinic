from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices

User = get_user_model()

class UserManagementRBACSecurityTests(APITestCase):
    def setUp(self):
        # Setup Geography
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_1 = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.district_2 = District.objects.create(name='Mysuru', code='MYS', state=self.state)

        # Setup Facilities
        self.facility_a = Facility.objects.create(
            facility_code='FAC-001',
            facility_name='Facility A (District 1)',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_1
        )
        self.facility_b = Facility.objects.create(
            facility_code='FAC-002',
            facility_name='Facility B (District 1)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district_1
        )
        self.facility_c = Facility.objects.create(
            facility_code='FAC-003',
            facility_name='Facility C (District 2)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district_2
        )

        # Setup Users
        self.do_user = User.objects.create_user(
            username='district_officer',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district_1,
            full_name='District Officer 1'
        )

        self.admin_a = User.objects.create_user(
            username='admin_a',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility_a,
            full_name='Admin Facility A'
        )

        self.doctor_a = User.objects.create_user(
            username='doctor_a',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_a,
            full_name='Dr. Facility A'
        )

        self.nurse_a = User.objects.create_user(
            username='nurse_a',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility_a,
            full_name='Nurse Facility A'
        )

        self.lab_a = User.objects.create_user(
            username='lab_a',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility_a,
            full_name='Lab Tech Facility A'
        )

        self.pharm_a = User.objects.create_user(
            username='pharm_a',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility_a,
            full_name='Pharmacist Facility A'
        )

        self.staff_b = User.objects.create_user(
            username='doctor_b',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_b,
            full_name='Dr. Facility B'
        )

        self.staff_c = User.objects.create_user(
            username='doctor_c',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_c,
            full_name='Dr. Facility C'
        )

    # 1. Unauthenticated request is rejected
    def test_unauthenticated_request_is_rejected(self):
        res_list = self.client.get('/api/users/')
        self.assertEqual(res_list.status_code, status.HTTP_401_UNAUTHORIZED)

        res_post = self.client.post('/api/users/', {'username': 'random', 'role': 'DOCTOR'})
        self.assertEqual(res_post.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. Doctor cannot create user
    def test_doctor_cannot_create_user(self):
        self.client.force_authenticate(user=self.doctor_a)
        res = self.client.post('/api/users/', {
            'username': 'new_staff',
            'role': RoleChoices.NURSE,
            'full_name': 'New Nurse'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 3. Nurse cannot create user
    def test_nurse_cannot_create_user(self):
        self.client.force_authenticate(user=self.nurse_a)
        res = self.client.post('/api/users/', {
            'username': 'new_staff',
            'role': RoleChoices.DOCTOR,
            'full_name': 'New Doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 4. Lab Technician cannot create user
    def test_lab_technician_cannot_create_user(self):
        self.client.force_authenticate(user=self.lab_a)
        res = self.client.post('/api/users/', {
            'username': 'new_staff',
            'role': RoleChoices.DOCTOR,
            'full_name': 'New Doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 5. Pharmacist cannot create user
    def test_pharmacist_cannot_create_user(self):
        self.client.force_authenticate(user=self.pharm_a)
        res = self.client.post('/api/users/', {
            'username': 'new_staff',
            'role': RoleChoices.DOCTOR,
            'full_name': 'New Doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 6. Hospital Admin can create permitted staff
    def test_hospital_admin_can_create_permitted_staff(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.post('/api/users/', {
            'username': 'created_dr_1',
            'password': 'StrongPassword123!',
            'role': RoleChoices.DOCTOR,
            'full_name': 'Dr. Created Staff',
            'email': 'dr.created@clinic.org'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username='created_dr_1')
        self.assertEqual(new_user.assigned_facility, self.facility_a)
        self.assertEqual(new_user.role, RoleChoices.DOCTOR)
        self.assertTrue(new_user.check_password('StrongPassword123!'))

    # 7. Hospital Admin cannot assign another facility
    def test_hospital_admin_cannot_assign_another_facility(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.post('/api/users/', {
            'username': 'cross_fac_staff',
            'role': RoleChoices.DOCTOR,
            'assigned_facility': self.facility_b.id,
            'full_name': 'Cross Facility Staff'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assigned_facility', res.data)

    # 8. Hospital Admin cannot create District Officer
    def test_hospital_admin_cannot_create_district_officer(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.post('/api/users/', {
            'username': 'new_district_boss',
            'role': RoleChoices.DISTRICT_OFFICER,
            'full_name': 'Fake District Officer'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', res.data)

    # 9. Hospital Admin cannot modify another facility's staff
    def test_hospital_admin_cannot_modify_another_facility_staff(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.patch(f'/api/users/{self.staff_b.id}/', {
            'full_name': 'Illegally Modified Name'
        })
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.staff_b.refresh_from_db()
        self.assertEqual(self.staff_b.full_name, 'Dr. Facility B')

    # 10. Hospital Admin cannot transfer own facility staff to another facility
    def test_hospital_admin_cannot_transfer_staff_to_another_facility(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.patch(f'/api/users/{self.doctor_a.id}/', {
            'assigned_facility': self.facility_b.id
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.doctor_a.refresh_from_db()
        self.assertEqual(self.doctor_a.assigned_facility, self.facility_a)

    # 11. User cannot modify own role via arbitrary PATCH
    def test_user_cannot_modify_own_role(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.patch(f'/api/users/{self.admin_a.id}/', {
            'role': RoleChoices.DISTRICT_OFFICER
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin_a.refresh_from_db()
        self.assertEqual(self.admin_a.role, RoleChoices.HOSPITAL_ADMIN)

    # 12. District Officer cannot perform prohibited mutations
    def test_district_officer_cannot_perform_prohibited_mutations(self):
        self.client.force_authenticate(user=self.do_user)

        # POST rejected
        res_post = self.client.post('/api/users/', {
            'username': 'do_created_user',
            'role': RoleChoices.DOCTOR,
            'full_name': 'DO User'
        })
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        # PATCH rejected
        res_patch = self.client.patch(f'/api/users/{self.doctor_a.id}/', {
            'full_name': 'DO Altered Doctor'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE rejected
        res_del = self.client.delete(f'/api/users/{self.doctor_a.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    # 13. District Officer can view users in district scope but not other districts
    def test_district_officer_scoped_view(self):
        self.client.force_authenticate(user=self.do_user)
        res = self.client.get('/api/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user_ids = [u['id'] for u in (res.data.get('results', res.data) if isinstance(res.data, dict) else res.data)]

        # Should contain district 1 users
        self.assertIn(self.admin_a.id, user_ids)
        self.assertIn(self.doctor_a.id, user_ids)
        self.assertIn(self.staff_b.id, user_ids)

        # Must not contain user from District 2
        self.assertNotIn(self.staff_c.id, user_ids)

    # 14. Cross-facility GET is blocked
    def test_cross_facility_get_is_blocked(self):
        self.client.force_authenticate(user=self.admin_a)

        # GET list only returns facility A staff
        res_list = self.client.get('/api/users/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        user_ids = [u['id'] for u in (res_list.data.get('results', res_list.data) if isinstance(res_list.data, dict) else res_list.data)]
        self.assertIn(self.doctor_a.id, user_ids)
        self.assertNotIn(self.staff_b.id, user_ids)
        self.assertNotIn(self.staff_c.id, user_ids)

        # Querying with ?facility=B returns empty list (no leakage)
        res_fac_query = self.client.get(f'/api/users/?facility={self.facility_b.id}')
        self.assertEqual(res_fac_query.status_code, status.HTTP_200_OK)
        queried_ids = [u['id'] for u in (res_fac_query.data.get('results', res_fac_query.data) if isinstance(res_fac_query.data, dict) else res_fac_query.data)]
        self.assertEqual(len(queried_ids), 0)

        # Direct GET on other facility user is blocked (403 or 404)
        res_detail = self.client.get(f'/api/users/{self.staff_b.id}/')
        self.assertIn(res_detail.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

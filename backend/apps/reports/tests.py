from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.audit.models import AuditLog

User = get_user_model()

class ResetDemoSecurityTests(APITestCase):
    def setUp(self):
        # Setup Geography
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)

        # Setup Facility
        self.facility = Facility.objects.create(
            facility_code='FAC-001',
            facility_name='Facility A',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district
        )

        # Setup Users for all 6 active roles
        self.district_officer = User.objects.create_user(
            username='district_officer',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district,
            full_name='District Officer'
        )

        self.hospital_admin = User.objects.create_user(
            username='hospital_admin',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility,
            full_name='Hospital Admin'
        )

        self.doctor = User.objects.create_user(
            username='doctor',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility,
            full_name='Dr. Test'
        )

        self.nurse = User.objects.create_user(
            username='nurse',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility,
            full_name='Nurse Test'
        )

        self.lab_tech = User.objects.create_user(
            username='lab_tech',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility,
            full_name='Lab Tech Test'
        )

        self.pharmacist = User.objects.create_user(
            username='pharmacist',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility,
            full_name='Pharmacist Test'
        )

    # 1. Unauthenticated request -> 401
    def test_reset_demo_requires_authentication(self):
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. Doctor cannot reset demo -> 403
    def test_doctor_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 3. Nurse cannot reset demo -> 403
    def test_nurse_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 4. Lab Technician cannot reset demo -> 403
    def test_lab_technician_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 5. Pharmacist cannot reset demo -> 403
    def test_pharmacist_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 6. Unauthorized roles cannot reset demo (Hospital Admin) -> 403
    def test_unauthorized_roles_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Authorized role (District Officer) can reset demo -> 200 OK + AuditLog
    @patch('apps.reports.views.call_command')
    def test_authorized_role_can_reset_demo(self, mock_call_command):
        self.client.force_authenticate(user=self.district_officer)
        initial_log_count = AuditLog.objects.filter(action='RESET_DEMO').count()

        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('status'), 'SUCCESS')

        # Verify call_command was invoked with 'seed_demo'
        mock_call_command.assert_called_once_with('seed_demo')

        # Verify AuditLog recorded
        self.assertEqual(AuditLog.objects.filter(action='RESET_DEMO').count(), initial_log_count + 1)
        latest_log = AuditLog.objects.filter(action='RESET_DEMO').latest('timestamp')
        self.assertEqual(latest_log.user, self.district_officer)
        self.assertEqual(latest_log.username_snapshot, 'district_officer')

    # 8. Reset Demo only allows POST (GET/PUT/PATCH/DELETE return 405 Method Not Allowed)
    @patch('apps.reports.views.call_command')
    def test_reset_demo_only_allows_post(self, mock_call_command):
        self.client.force_authenticate(user=self.district_officer)

        res_get = self.client.get('/api/admin/reset-demo/')
        self.assertEqual(res_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_put = self.client.put('/api/admin/reset-demo/', {})
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_patch = self.client.patch('/api/admin/reset-demo/', {})
        self.assertEqual(res_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_delete = self.client.delete('/api/admin/reset-demo/')
        self.assertEqual(res_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        mock_call_command.assert_not_called()

    # 9. Verify demo.reset permission is explicit and only assigned to intended role(s)
    def test_reset_demo_permission_is_explicit(self):
        self.assertIn('demo.reset', ROLE_PERMISSIONS['DISTRICT_OFFICER'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['DOCTOR'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['NURSE'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['LAB_TECHNICIAN'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['PHARMACIST'])

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

    # 2. District Officer cannot reset demo -> 403
    def test_district_officer_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.district_officer)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 3. Doctor cannot reset demo -> 403
    def test_doctor_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 4. Nurse cannot reset demo -> 403
    def test_nurse_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 5. Lab Technician cannot reset demo -> 403
    def test_lab_technician_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 6. Pharmacist cannot reset demo -> 403
    def test_pharmacist_cannot_reset_demo(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Authorized role (Hospital Admin) can reset demo -> 200 OK + AuditLog
    @patch('apps.reports.views.call_command')
    def test_authorized_role_can_reset_demo(self, mock_call_command):
        self.client.force_authenticate(user=self.hospital_admin)
        initial_log_count = AuditLog.objects.filter(action='RESET_DEMO').count()

        res = self.client.post('/api/admin/reset-demo/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('status'), 'SUCCESS')

        # Verify call_command was invoked with 'seed_demo' exactly once
        mock_call_command.assert_called_once_with('seed_demo')

        # Verify AuditLog recorded
        self.assertEqual(AuditLog.objects.filter(action='RESET_DEMO').count(), initial_log_count + 1)
        latest_log = AuditLog.objects.filter(action='RESET_DEMO').latest('timestamp')
        self.assertEqual(latest_log.user, self.hospital_admin)
        self.assertEqual(latest_log.username_snapshot, 'hospital_admin')

    # 8. Reset Demo only allows POST (GET/PUT/PATCH/DELETE return 405 Method Not Allowed)
    @patch('apps.reports.views.call_command')
    def test_reset_demo_only_allows_post(self, mock_call_command):
        self.client.force_authenticate(user=self.hospital_admin)

        res_get = self.client.get('/api/admin/reset-demo/')
        self.assertEqual(res_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_put = self.client.put('/api/admin/reset-demo/', {})
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_patch = self.client.patch('/api/admin/reset-demo/', {})
        self.assertEqual(res_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res_delete = self.client.delete('/api/admin/reset-demo/')
        self.assertEqual(res_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        mock_call_command.assert_not_called()

    # 9. Verify demo.reset permission is explicit and only assigned to intended role (HOSPITAL_ADMIN)
    def test_reset_demo_permission_is_explicit(self):
        self.assertIn('demo.reset', ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['DISTRICT_OFFICER'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['DOCTOR'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['NURSE'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['LAB_TECHNICIAN'])
        self.assertNotIn('demo.reset', ROLE_PERMISSIONS['PHARMACIST'])


import datetime
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.pharmacy.models import MedicineMaster, MedicineBatch

class DashboardSummaryViewTests(APITestCase):
    def setUp(self):
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_1 = District.objects.create(name='District 1', code='D1', state=self.state)
        self.district_2 = District.objects.create(name='District 2', code='D2', state=self.state)

        self.fac_1a = Facility.objects.create(
            facility_code='F-1A',
            facility_name='Facility 1A',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_1
        )
        self.fac_1b = Facility.objects.create(
            facility_code='F-1B',
            facility_name='Facility 1B',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_1
        )
        self.fac_2 = Facility.objects.create(
            facility_code='F-2',
            facility_name='Facility 2',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_2
        )

        self.district_officer = User.objects.create_user(
            username='do_d1',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district_1,
            full_name='District Officer 1'
        )

        self.hospital_admin = User.objects.create_user(
            username='admin_1a',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.fac_1a,
            full_name='Admin 1A'
        )

        self.doctor = User.objects.create_user(
            username='doc_1a',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.fac_1a,
            full_name='Dr. 1A'
        )

        self.nurse = User.objects.create_user(
            username='nurse_1a',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.fac_1a,
            full_name='Nurse 1A'
        )

        self.lab_tech = User.objects.create_user(
            username='lab_1a',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.fac_1a,
            full_name='Lab 1A'
        )

        self.pharmacist = User.objects.create_user(
            username='pharm_1a',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.fac_1a,
            full_name='Pharm 1A'
        )

    def test_unauthenticated_request_returns_401(self):
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_authenticated_roles_can_access_dashboard(self):
        roles = [
            self.district_officer,
            self.hospital_admin,
            self.doctor,
            self.nurse,
            self.lab_tech,
            self.pharmacist,
        ]
        for u in roles:
            self.client.force_authenticate(user=u)
            res = self.client.get('/api/dashboard/summary/')
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Failed for {u.role}")

    def test_district_officer_defaults_to_district_wide_and_clamps_other_districts(self):
        self.client.force_authenticate(user=self.district_officer)
        # Default request without facility query param
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data.get('active_facility_id'))
        self.assertEqual(res.data.get('total_facilities'), 2)

        # Explicit request with facility in district
        res_fac1a = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}')
        self.assertEqual(res_fac1a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fac1a.data.get('active_facility_id'), self.fac_1a.id)
        self.assertEqual(res_fac1a.data.get('active_facility'), self.fac_1a.facility_name)

        # Request with facility outside district (clamped back to district)
        res_fac2 = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
        self.assertEqual(res_fac2.status_code, status.HTTP_200_OK)
        self.assertIsNone(res_fac2.data.get('active_facility_id'))
        self.assertEqual(res_fac2.data.get('total_facilities'), 2)

    def test_hospital_admin_locked_to_assigned_facility(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('active_facility_id'), self.fac_1a.id)

        # Attempt to view another facility
        res_fac1b = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1b.id}')
        self.assertEqual(res_fac1b.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fac1b.data.get('active_facility_id'), self.fac_1a.id)

    def test_operational_roles_locked_to_assigned_facility(self):
        roles = [self.doctor, self.nurse, self.lab_tech, self.pharmacist]
        for u in roles:
            self.client.force_authenticate(user=u)
            res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1b.id}')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data.get('active_facility_id'), self.fac_1a.id)

    def test_registered_today_vs_new_opd_patients_independent(self):
        # Patient 1: registered today at fac_1a
        p1 = Patient.objects.create(
            patient_id='P001',
            name='Patient Today',
            mobile='9000000001',
            address='Addr 1',
            registered_at_facility=self.fac_1a
        )
        # Patient 2: registered yesterday at fac_1a
        p2 = Patient.objects.create(
            patient_id='P002',
            name='Patient Yesterday',
            mobile='9000000002',
            address='Addr 2',
            registered_at_facility=self.fac_1a
        )
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        Patient.objects.filter(pk=p2.pk).update(registration_date=yesterday)

        # Create visit for Patient 2 today
        Visit.objects.create(
            visit_id='V002',
            patient=p2,
            facility=self.fac_1a,
            opd_date=datetime.date.today(),
            status='WAITING_FOR_TRIAGE'
        )

        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Only Patient 1 was registered today
        self.assertEqual(res.data.get('registered_today'), 1)
        # Patient 2 had a visit today
        self.assertEqual(res.data.get('todays_opd'), 1)

    def test_staff_status_active_and_total(self):
        User.objects.create_user(
            username='doc_inactive',
            password='pwd',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.fac_1a,
            is_active=False
        )
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        doctors_stat = res.data.get('staff_status', {}).get('doctors', {})
        self.assertEqual(doctors_stat.get('active'), 1)
        self.assertEqual(doctors_stat.get('total'), 2)

    def test_inventory_low_stock_and_expiry_metrics(self):
        med1 = MedicineMaster.objects.create(
            generic_name='Paracetamol',
            minimum_stock=100,
            reorder_level=150
        )
        med2 = MedicineMaster.objects.create(
            generic_name='Amoxicillin',
            minimum_stock=50,
            reorder_level=60
        )
        today = datetime.date.today()
        # Active batch for med1: 200 units (above minimum_stock)
        MedicineBatch.objects.create(
            facility=self.fac_1a,
            medicine=med1,
            batch_number='B1',
            quantity=200,
            expiry_date=today + datetime.timedelta(days=180)
        )
        # Active batch for med2: 20 units (low stock: 20 <= 50) and expiring in 30 days
        MedicineBatch.objects.create(
            facility=self.fac_1a,
            medicine=med2,
            batch_number='B2',
            quantity=20,
            expiry_date=today + datetime.timedelta(days=30)
        )
        # Expired batch for med2
        MedicineBatch.objects.create(
            facility=self.fac_1a,
            medicine=med2,
            batch_number='B3',
            quantity=10,
            expiry_date=today - datetime.timedelta(days=5),
            status='EXPIRED'
        )

        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        inv = res.data.get('inventory_summary', {})
        self.assertEqual(inv.get('low_stock'), 1)
        self.assertEqual(inv.get('expiring_soon'), 1)
        self.assertEqual(inv.get('expired_batches'), 1)

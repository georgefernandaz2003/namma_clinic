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
from apps.laboratory.models import LabTestMaster, LabOrder
from apps.consultations.models import Consultation, Prescription
from apps.referrals.models import Referral
from apps.alerts.models import Alert

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

    def test_unified_contract_structure(self):
        """Verify the unified contract structure has all required top-level and nested keys."""
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        # Top-level keys
        for key in ['scope', 'patients', 'visits_and_queue', 'laboratory', 'pharmacy', 'referrals', 'staff', 'alerts', 'action_required']:
            self.assertIn(key, data, f"Missing key '{key}' in dashboard contract")

        # Patients subkeys
        for sub in ['total', 'registered_today', 'male', 'female', 'other', 'by_age_group']:
            self.assertIn(sub, data['patients'])

        # Visits and queue subkeys
        for sub in ['todays_opd', 'completed_today', 'waiting_triage', 'waiting_doctor', 'in_consultation', 'avg_wait_time_minutes']:
            self.assertIn(sub, data['visits_and_queue'])

        # Laboratory subkeys
        for sub in ['total_orders', 'ordered', 'sample_collected', 'in_progress', 'completed', 'verified', 'cancelled', 'pending_verification']:
            self.assertIn(sub, data['laboratory'])

        # Pharmacy subkeys
        for sub in ['total_medicines', 'active_batches', 'low_stock_medicines', 'out_of_stock_medicines', 'expiring_soon_batches', 'expired_batches', 'prescriptions_pending', 'prescriptions_dispensed']:
            self.assertIn(sub, data['pharmacy'])

        # Referrals subkeys
        for sub in ['total', 'pending', 'accepted', 'completed', 'rejected']:
            self.assertIn(sub, data['referrals'])

        # Staff subkeys
        for sub in ['doctors', 'nurses', 'lab_technicians', 'pharmacists', 'admins', 'total_active_staff']:
            self.assertIn(sub, data['staff'])
            if sub != 'total_active_staff':
                self.assertIn('active', data['staff'][sub])
                self.assertIn('total', data['staff'][sub])

        # Alerts subkeys
        for sub in ['total', 'active', 'resolved', 'by_severity']:
            self.assertIn(sub, data['alerts'])

        # Action required
        self.assertIsInstance(data['action_required'], list)

    def test_zero_data_handling_empty_facility(self):
        """Verify that an empty facility returns clean 0s with no exceptions, nulls, or NaNs."""
        # fac_1b has no patients, visits, orders, or alerts
        self.client.force_authenticate(user=self.district_officer)
        res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1b.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        self.assertEqual(data['patients']['total'], 0)
        self.assertEqual(data['patients']['registered_today'], 0)
        self.assertEqual(data['visits_and_queue']['todays_opd'], 0)
        self.assertEqual(data['visits_and_queue']['completed_today'], 0)
        self.assertEqual(data['visits_and_queue']['avg_wait_time_minutes'], 0)
        self.assertEqual(data['laboratory']['total_orders'], 0)
        self.assertEqual(data['pharmacy']['low_stock_medicines'], 0)
        self.assertEqual(data['pharmacy']['expired_batches'], 0)
        self.assertEqual(data['referrals']['total'], 0)
        self.assertEqual(data['alerts']['active'], 0)
        self.assertEqual(len(data['action_required']), 0)

    def test_historical_date_filtering(self):
        """Verify that ?date= strictly filters metrics to the requested date."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        p = Patient.objects.create(
            patient_id='P-HIST',
            name='Hist Patient',
            mobile='9111111111',
            registered_at_facility=self.fac_1a
        )
        # Visit yesterday
        Visit.objects.create(
            visit_id='V-YEST',
            patient=p,
            facility=self.fac_1a,
            opd_date=yesterday,
            status='COMPLETED'
        )
        # Visit today
        Visit.objects.create(
            visit_id='V-TODAY',
            patient=p,
            facility=self.fac_1a,
            opd_date=today,
            status='WAITING_FOR_TRIAGE'
        )

        self.client.force_authenticate(user=self.hospital_admin)

        # Query for yesterday
        res_yest = self.client.get(f'/api/dashboard/summary/?date={yesterday.isoformat()}')
        self.assertEqual(res_yest.status_code, status.HTTP_200_OK)
        self.assertEqual(res_yest.data['visits_and_queue']['todays_opd'], 1)
        self.assertEqual(res_yest.data['visits_and_queue']['completed_today'], 1)
        self.assertEqual(res_yest.data['visits_and_queue']['waiting_triage'], 0)

        # Query for today
        res_today = self.client.get(f'/api/dashboard/summary/?date={today.isoformat()}')
        self.assertEqual(res_today.status_code, status.HTTP_200_OK)
        self.assertEqual(res_today.data['visits_and_queue']['todays_opd'], 1)
        self.assertEqual(res_today.data['visits_and_queue']['completed_today'], 0)
        self.assertEqual(res_today.data['visits_and_queue']['waiting_triage'], 1)

    def test_cross_facility_isolation_all_roles(self):
        """Verify district officer can see all facilities in district, but operational roles are locked to assigned facility."""
        # Create a patient and visit in fac_1a, fac_1b, and fac_2
        p1a = Patient.objects.create(patient_id='P1A', name='P1A', registered_at_facility=self.fac_1a)
        p1b = Patient.objects.create(patient_id='P1B', name='P1B', registered_at_facility=self.fac_1b)
        p2 = Patient.objects.create(patient_id='P2', name='P2', registered_at_facility=self.fac_2)

        # 1. District Officer (District 1) sees fac_1a and fac_1b (total 2 patients), but NEVER fac_2
        self.client.force_authenticate(user=self.district_officer)
        res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['patients']['total'], 2)
        self.assertEqual(res.data['total_facilities'], 2)

        # District Officer querying fac_2 outside their district is clamped back to district 1
        res_clamped = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
        self.assertEqual(res_clamped.status_code, status.HTTP_200_OK)
        self.assertEqual(res_clamped.data['patients']['total'], 2)

        # 2. Operational roles (Hospital Admin, Doctor, Nurse, Lab Tech, Pharmacist) see ONLY fac_1a (1 patient)
        operational_users = [self.hospital_admin, self.doctor, self.nurse, self.lab_tech, self.pharmacist]
        for u in operational_users:
            self.client.force_authenticate(user=u)
            # Normal call
            res_op = self.client.get('/api/dashboard/summary/')
            self.assertEqual(res_op.status_code, status.HTTP_200_OK)
            self.assertEqual(res_op.data['patients']['total'], 1, f"Failed for role {u.role}")

            # Tampering attempt with fac_1b or fac_2
            res_tamper = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
            self.assertEqual(res_tamper.status_code, status.HTTP_200_OK)
            self.assertEqual(res_tamper.data['patients']['total'], 1, f"Tamper bypass succeeded for role {u.role}")

    def test_table_by_table_reconciliation(self):
        """Verify dashboard KPIs match the exact count from list endpoints."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='PREC', name='Reconcile Pt', registered_at_facility=self.fac_1a)
        v = Visit.objects.create(visit_id='VREC', patient=p, facility=self.fac_1a, opd_date=today, status='WAITING_FOR_TRIAGE')
        test_m = LabTestMaster.objects.create(test_name='CBC', test_code='CBC', category='PATHOLOGY', cost=100)
        lab_o = LabOrder.objects.create(visit=v, facility=self.fac_1a, test=test_m, status='ORDERED')
        alert = Alert.objects.create(facility=self.fac_1a, title='Test Alert', alert_type='LOW_STOCK', severity='HIGH', status='NEW')
        referral = Referral.objects.create(visit=v, referring_facility=self.fac_1a, reason='Specialist', referral_type='UPWARD', status='PENDING')

        self.client.force_authenticate(user=self.hospital_admin)

        # Get dashboard summary
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash = dash_res.data

        # 1. Patients endpoint
        pt_res = self.client.get('/api/patients/')
        self.assertEqual(pt_res.status_code, status.HTTP_200_OK)
        pt_count = pt_res.data['count'] if 'count' in pt_res.data else len(pt_res.data)
        self.assertEqual(dash['patients']['total'], pt_count)

        # 2. Visits endpoint
        v_res = self.client.get(f'/api/visits/?opd_date={today.isoformat()}')
        self.assertEqual(v_res.status_code, status.HTTP_200_OK)
        v_count = v_res.data['count'] if 'count' in v_res.data else len(v_res.data)
        self.assertEqual(dash['visits_and_queue']['todays_opd'], v_count)

        # 3. Lab Orders endpoint
        lab_res = self.client.get(f'/api/lab/orders/?order_date={today.isoformat()}')
        self.assertEqual(lab_res.status_code, status.HTTP_200_OK)
        lab_count = lab_res.data['count'] if 'count' in lab_res.data else len(lab_res.data)
        self.assertEqual(dash['laboratory']['total_orders'], lab_count)

        # 4. Alerts endpoint (Active)
        al_res = self.client.get('/api/alerts/?status=ACTIVE')
        self.assertEqual(al_res.status_code, status.HTTP_200_OK)
        al_count = al_res.data['count'] if 'count' in al_res.data else len(al_res.data)
        self.assertEqual(dash['alerts']['active'], al_count)

        # 5. Referrals endpoint
        ref_res = self.client.get('/api/referrals/')
        self.assertEqual(ref_res.status_code, status.HTTP_200_OK)
        ref_count = ref_res.data['count'] if 'count' in ref_res.data else len(ref_res.data)
        self.assertEqual(dash['referrals']['total'], ref_count)

    def test_alert_scoping_enforced(self):
        """Verify AlertViewSet restricts access based on facility scope."""
        al_1a = Alert.objects.create(facility=self.fac_1a, title='Alert 1A', alert_type='LOW_STOCK', severity='HIGH')
        al_2 = Alert.objects.create(facility=self.fac_2, title='Alert 2', alert_type='LOW_STOCK', severity='HIGH')

        # Hospital admin of 1A should only see Alert 1A
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get('/api/alerts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in (res.data['results'] if 'results' in res.data else res.data)]
        self.assertIn(al_1a.id, ids)
        self.assertNotIn(al_2.id, ids)

    def test_facility_scoping_no_bypass(self):
        """Verify ?all=true does not bypass district scoping for District Officer or facility scoping for Hospital Admin."""
        self.client.force_authenticate(user=self.district_officer)
        res = self.client.get('/api/facilities/?all=true')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        fac_ids = [item['id'] for item in (res.data['results'] if 'results' in res.data else res.data)]
        self.assertIn(self.fac_1a.id, fac_ids)
        self.assertIn(self.fac_1b.id, fac_ids)
        self.assertNotIn(self.fac_2.id, fac_ids)


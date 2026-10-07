from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.audit.models import AuditLog
from django.db.models import Sum

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
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
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

    # =========================================================================
    # 18 SPECIFIC TESTS DEMONSTRATING EXACT RECONCILIATION AND ROLE SCOPING
    # =========================================================================

    def test_01_dashboard_kpi_equals_queue_table_queryset_count(self):
        """1. Dashboard KPI equals queue table queryset count."""
        today = datetime.date.today()
        p1 = Patient.objects.create(patient_id='P01', name='Patient 1', registered_at_facility=self.fac_1a)
        p2 = Patient.objects.create(patient_id='P02', name='Patient 2', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V01', patient=p1, facility=self.fac_1a, opd_date=today, status='WAITING_FOR_TRIAGE')
        Visit.objects.create(visit_id='V02', patient=p2, facility=self.fac_1a, opd_date=today, status='IN_CONSULTATION')

        self.client.force_authenticate(user=self.hospital_admin)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_opd = dash_res.data['visits']['total']

        # Queue table endpoint count
        table_res = self.client.get(f'/api/visits/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(table_res.status_code, status.HTTP_200_OK)
        table_count = table_res.data.get('count', len(table_res.data.get('results', table_res.data)))

        self.assertEqual(dash_opd, table_count)
        self.assertEqual(dash_opd, 2)

    def test_02_dashboard_pharmacy_total_equals_prescription_queryset_count(self):
        """2. Dashboard pharmacy total equals prescription queryset count."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P02_RX', name='RX Patient', registered_at_facility=self.fac_1a)
        v = Visit.objects.create(visit_id='V02_RX', patient=p, facility=self.fac_1a, opd_date=today)
        c = Consultation.objects.create(visit=v, patient=p, facility=self.fac_1a, chief_complaint='Fever')
        Prescription.objects.create(consultation=c, patient=p, doctor=self.doctor, facility=self.fac_1a, status='PENDING')

        self.client.force_authenticate(user=self.pharmacist)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_rx_total = dash_res.data['pharmacy']['total_prescriptions']

        rx_res = self.client.get(f'/api/prescriptions/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(rx_res.status_code, status.HTTP_200_OK)
        rx_count = rx_res.data.get('count', len(rx_res.data.get('results', rx_res.data)))

        self.assertEqual(dash_rx_total, rx_count)
        self.assertEqual(dash_rx_total, 1)

    def test_03_dashboard_lab_count_equals_lab_queue_count(self):
        """3. Dashboard lab count equals lab queue count."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P03_LAB', name='Lab Patient', registered_at_facility=self.fac_1a)
        test_m = LabTestMaster.objects.create(code='HB', name='Hemoglobin', category='HEMATOLOGY')
        LabOrder.objects.create(patient=p, facility=self.fac_1a, test_master=test_m, status='ORDERED')

        self.client.force_authenticate(user=self.lab_tech)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_lab_total = dash_res.data['laboratory']['total_orders']

        lab_res = self.client.get(f'/api/lab/orders/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(lab_res.status_code, status.HTTP_200_OK)
        lab_count = lab_res.data.get('count', len(lab_res.data.get('results', lab_res.data)))

        self.assertEqual(dash_lab_total, lab_count)
        self.assertEqual(dash_lab_total, 1)

    def test_04_dashboard_triage_count_equals_triage_queue_count(self):
        """4. Dashboard triage count equals triage queue count."""
        today = datetime.date.today()
        p1 = Patient.objects.create(patient_id='P04_1', name='Triage 1', registered_at_facility=self.fac_1a)
        p2 = Patient.objects.create(patient_id='P04_2', name='Triage 2', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='VT01', patient=p1, facility=self.fac_1a, opd_date=today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE')
        Visit.objects.create(visit_id='VT02', patient=p2, facility=self.fac_1a, opd_date=today, current_queue='TRIAGE', status='IN_TRIAGE')

        self.client.force_authenticate(user=self.nurse)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_waiting = dash_res.data['queues']['triage_waiting']
        dash_in_progress = dash_res.data['queues']['triage_in_progress']

        # Waiting rows in triage
        res_waiting = self.client.get(f'/api/visits/?facility={self.fac_1a.id}&date={today.isoformat()}&queue=TRIAGE&status=WAITING')
        count_waiting = res_waiting.data.get('count', len(res_waiting.data.get('results', res_waiting.data)))
        self.assertEqual(dash_waiting, count_waiting)
        self.assertEqual(dash_waiting, 1)

        # In-progress rows in triage
        res_in_prog = self.client.get(f'/api/visits/?facility={self.fac_1a.id}&date={today.isoformat()}&queue=TRIAGE&status=IN_TRIAGE')
        count_in_prog = res_in_prog.data.get('count', len(res_in_prog.data.get('results', res_in_prog.data)))
        self.assertEqual(dash_in_progress, count_in_prog)
        self.assertEqual(dash_in_progress, 1)

    def test_05_dashboard_doctor_count_equals_doctor_queue_count(self):
        """5. Dashboard doctor count equals doctor queue count."""
        today = datetime.date.today()
        p1 = Patient.objects.create(patient_id='P05_1', name='Doc Pt 1', registered_at_facility=self.fac_1a)
        p2 = Patient.objects.create(patient_id='P05_2', name='Doc Pt 2', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='VD01', patient=p1, facility=self.fac_1a, opd_date=today, current_queue='DOCTOR', status='WAITING_FOR_DOCTOR')
        Visit.objects.create(visit_id='VD02', patient=p2, facility=self.fac_1a, opd_date=today, current_queue='DOCTOR', status='IN_CONSULTATION')

        self.client.force_authenticate(user=self.doctor)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_doc_waiting = dash_res.data['queues']['doctor_waiting']
        dash_in_consult = dash_res.data['queues']['doctor_in_consultation']

        res_waiting = self.client.get(f'/api/visits/?facility={self.fac_1a.id}&date={today.isoformat()}&queue=DOCTOR&status=WAITING_FOR_DOCTOR')
        count_waiting = res_waiting.data.get('count', len(res_waiting.data.get('results', res_waiting.data)))
        self.assertEqual(dash_doc_waiting, count_waiting)

        res_in_consult = self.client.get(f'/api/visits/?facility={self.fac_1a.id}&date={today.isoformat()}&queue=DOCTOR&status=IN_CONSULTATION')
        count_in_consult = res_in_consult.data.get('count', len(res_in_consult.data.get('results', res_in_consult.data)))
        self.assertEqual(dash_in_consult, count_in_consult)

    def test_06_facility_overview_waiting_equals_dashboard_waiting_definition(self):
        """6. Facility overview waiting equals dashboard waiting definition."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P06', name='Pt 6', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V06', patient=p, facility=self.fac_1a, opd_date=today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE')

        self.client.force_authenticate(user=self.district_officer)
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_waiting = dash_res.data['visits']['waiting']

        fac_overview = dash_res.data['facility_overview']
        fac_1a_entry = next((f for f in fac_overview if f['id'] == self.fac_1a.id), None)
        self.assertIsNotNone(fac_1a_entry)
        self.assertEqual(fac_1a_entry['waiting'], dash_waiting)

    def test_07_inventory_dashboard_equals_inventory_queryset_definition(self):
        """7. Inventory dashboard equals inventory queryset definition."""
        med = MedicineMaster.objects.create(generic_name='Paracetamol 500mg', minimum_stock=50)
        today = datetime.date.today()
        # Create low stock batch: quantity 20 <= minimum_stock 50
        MedicineBatch.objects.create(
            facility=self.fac_1a, medicine=med, batch_number='B07',
            quantity=20, expiry_date=today + datetime.timedelta(days=120)
        )

        self.client.force_authenticate(user=self.pharmacist)
        dash_res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_low_stock = dash_res.data['pharmacy']['low_stock_medicines']

        # Queryset low stock calculation
        batch_qs = MedicineBatch.objects.filter(facility=self.fac_1a)
        qs_low_stock = 0
        for m in MedicineMaster.objects.all():
            tot = batch_qs.filter(medicine=m).aggregate(t=Sum('quantity'))['t'] or 0
            if 0 < tot <= (m.minimum_stock or 0):
                qs_low_stock += 1

        self.assertEqual(dash_low_stock, qs_low_stock)
        self.assertEqual(dash_low_stock, 1)

    def test_08_referral_dashboard_equals_referral_table_definition(self):
        """8. Referral dashboard equals referral table definition."""
        p = Patient.objects.create(patient_id='P08', name='Ref Pt', registered_at_facility=self.fac_1a)
        Referral.objects.create(
            referral_id='REF08', patient=p, source_facility=self.fac_1a,
            destination_facility=self.fac_1b, referring_doctor=self.doctor,
            reason='Specialist consultation', clinical_summary='Cardiology review', status='CREATED'
        )

        self.client.force_authenticate(user=self.hospital_admin)
        dash_res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_ref_pending = dash_res.data['referrals']['pending_outgoing']

        ref_res = self.client.get('/api/referrals/?status=CREATED')
        self.assertEqual(ref_res.status_code, status.HTTP_200_OK)
        ref_count = ref_res.data.get('count', len(ref_res.data.get('results', ref_res.data)))

        self.assertEqual(dash_ref_pending, ref_count)
        self.assertEqual(dash_ref_pending, 1)

    def test_09_active_staff_plus_inactive_staff_equals_total_staff(self):
        """9. Active staff + inactive staff = total staff for all roles."""
        User.objects.create_user(username='doc_inact_09', password='pwd', role=RoleChoices.DOCTOR, assigned_facility=self.fac_1a, is_active=False)
        User.objects.create_user(username='nur_inact_09', password='pwd', role=RoleChoices.NURSE, assigned_facility=self.fac_1a, is_active=False)

        self.client.force_authenticate(user=self.hospital_admin)
        dash_res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        staff = dash_res.data['staff']

        for role_key in ['doctors', 'nurses', 'lab_technicians', 'pharmacists']:
            stat = staff[role_key]
            self.assertEqual(stat['active'] + stat['inactive'], stat['total'], f"Mismatch in {role_key}")

    def test_10_district_officer_sees_only_assigned_district(self):
        """10. District Officer sees only assigned district facilities."""
        self.client.force_authenticate(user=self.district_officer)
        dash_res = self.client.get('/api/dashboard/summary/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        scope = dash_res.data['scope']
        self.assertEqual(scope['district'], self.district_1.name)
        self.assertEqual(scope['total_facilities'], 2)  # fac_1a and fac_1b
        self.assertIn(self.fac_1a.id, scope['facility_ids'])
        self.assertIn(self.fac_1b.id, scope['facility_ids'])
        self.assertNotIn(self.fac_2.id, scope['facility_ids'])

    def test_11_district_officer_cannot_see_another_district(self):
        """11. District Officer cannot see another district by passing facility param."""
        self.client.force_authenticate(user=self.district_officer)
        # Attempt to access fac_2 in District 2
        dash_res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        # Must be clamped back to district network of district 1
        self.assertIsNone(dash_res.data['scope']['active_facility_id'])
        self.assertNotIn(self.fac_2.id, dash_res.data['scope']['facility_ids'])

    def test_12_operational_roles_see_only_assigned_facility(self):
        """12. Operational roles see only assigned facility."""
        operational_users = [self.hospital_admin, self.doctor, self.nurse, self.lab_tech, self.pharmacist]
        for u in operational_users:
            self.client.force_authenticate(user=u)
            # Try to tamper by passing fac_1b or fac_2
            res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data['scope']['active_facility_id'], self.fac_1a.id)
            self.assertEqual(res.data['scope']['facility_ids'], [self.fac_1a.id])

    def test_13_historical_date_returns_historical_metrics(self):
        """13. Historical date returns historical metrics."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        p = Patient.objects.create(patient_id='P13', name='Pt 13', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V13_YEST', patient=p, facility=self.fac_1a, opd_date=yesterday, status='COMPLETED')

        self.client.force_authenticate(user=self.hospital_admin)
        res_yest = self.client.get(f'/api/dashboard/summary/?date={yesterday.isoformat()}')
        self.assertEqual(res_yest.status_code, status.HTTP_200_OK)
        self.assertEqual(res_yest.data['date'], yesterday.isoformat())
        self.assertFalse(res_yest.data['is_today'])
        self.assertEqual(res_yest.data['visits']['total'], 1)
        self.assertEqual(res_yest.data['visits']['completed'], 1)

    def test_14_today_returns_todays_metrics(self):
        """14. Today returns today's metrics."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P14', name='Pt 14', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V14_TODAY', patient=p, facility=self.fac_1a, opd_date=today, status='WAITING_FOR_TRIAGE')

        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get(f'/api/dashboard/summary/?date={today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['date'], today.isoformat())
        self.assertTrue(res.data['is_today'])
        self.assertEqual(res.data['visits']['total'], 1)
        self.assertEqual(res.data['queues']['triage_waiting'], 1)

    def test_15_zero_data_facility_returns_zero_consistently(self):
        """15. Zero-data facility returns zero consistently."""
        self.client.force_authenticate(user=self.district_officer)
        # fac_1b has no visits or orders
        res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1b.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        d = res.data
        self.assertEqual(d['patients']['total'], 0)
        self.assertEqual(d['visits']['total'], 0)
        self.assertEqual(d['visits']['waiting'], 0)
        self.assertEqual(d['laboratory']['total_orders'], 0)
        self.assertEqual(d['pharmacy']['total_prescriptions'], 0)
        self.assertEqual(d['referrals']['total'], 0)

    def test_16_one_visit_with_multiple_lab_orders_handled_correctly(self):
        """16. One visit with multiple lab orders is handled correctly."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P16', name='Pt 16', registered_at_facility=self.fac_1a)
        v = Visit.objects.create(visit_id='V16', patient=p, facility=self.fac_1a, opd_date=today, current_queue='LAB', status='LAB_PENDING')

        m1 = LabTestMaster.objects.create(code='L16_1', name='Test 1')
        m2 = LabTestMaster.objects.create(code='L16_2', name='Test 2')
        LabOrder.objects.create(visit=v, patient=p, facility=self.fac_1a, test_master=m1, status='ORDERED')
        LabOrder.objects.create(visit=v, patient=p, facility=self.fac_1a, test_master=m2, status='SAMPLE_COLLECTED')

        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.get(f'/api/dashboard/summary/?date={today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Total lab orders = 2
        self.assertEqual(res.data['laboratory']['total_orders'], 2)
        # Pending lab orders = 2
        self.assertEqual(res.data['laboratory']['lab_pending_orders'], 2)
        # Lab pending visits = 1
        self.assertEqual(res.data['laboratory']['lab_pending_visits'], 1)
        self.assertEqual(res.data['queues']['lab_pending'], 1)

    def test_17_lab_completion_and_reconsultation_counted_correctly(self):
        """17. Lab completion/re-consultation is counted correctly."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P17', name='Pt 17', registered_at_facility=self.fac_1a)
        v = Visit.objects.create(visit_id='V17', patient=p, facility=self.fac_1a, opd_date=today, current_queue='DOCTOR', status='LAB_COMPLETED', assigned_doctor=self.doctor)
        m = LabTestMaster.objects.create(code='L17', name='Test 17')
        LabOrder.objects.create(visit=v, patient=p, facility=self.fac_1a, test_master=m, status='VERIFIED')

        self.client.force_authenticate(user=self.doctor)
        res = self.client.get(f'/api/dashboard/summary/?date={today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Doctor waiting queue includes LAB_COMPLETED for re-consultation
        self.assertEqual(res.data['queues']['doctor_waiting'], 1)
        # Lab queue is 0 since all orders verified
        self.assertEqual(res.data['queues']['lab_pending'], 0)
        self.assertEqual(res.data['laboratory']['verified'], 1)

    def test_18_paginated_prescription_api_total_not_based_on_page_length(self):
        """18. Paginated prescription API total is not based on page length."""
        today = datetime.date.today()
        p = Patient.objects.create(patient_id='P18', name='Pt 18', registered_at_facility=self.fac_1a)
        v = Visit.objects.create(visit_id='V18', patient=p, facility=self.fac_1a, opd_date=today)
        c = Consultation.objects.create(visit=v, patient=p, facility=self.fac_1a, chief_complaint='Review')
        Prescription.objects.create(consultation=c, patient=p, doctor=self.doctor, facility=self.fac_1a, status='PENDING')

        self.client.force_authenticate(user=self.pharmacist)
        dash_res = self.client.get(f'/api/dashboard/summary/?date={today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_rx_count = dash_res.data['pharmacy']['total_prescriptions']

        rx_res = self.client.get(f'/api/prescriptions/?date={today.isoformat()}')
        self.assertEqual(rx_res.status_code, status.HTTP_200_OK)
        self.assertIn('count', rx_res.data)
        # Authoritative count matches exactly
        self.assertEqual(dash_rx_count, rx_res.data['count'])


class HospitalAdminReportTests(APITestCase):
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
        self.fac_2 = Facility.objects.create(
            facility_code='F-2',
            facility_name='Facility 2',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_2
        )

        self.hospital_admin = User.objects.create_user(
            username='admin_1a_rep',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.fac_1a,
            full_name='Admin 1A'
        )

        self.doctor = User.objects.create_user(
            username='doc_1a_rep',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.fac_1a,
            full_name='Dr. Test Doc'
        )

        # Facility 2 Doctor & Admin
        self.admin_fac2 = User.objects.create_user(
            username='admin_fac2_rep',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.fac_2,
            full_name='Admin Fac 2'
        )

        self.today = datetime.date.today()

    def test_unauthenticated_request_returns_401(self):
        res = self.client.get('/api/reports/hospital/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hospital_admin_day_report(self):
        self.client.force_authenticate(user=self.hospital_admin)

        p1 = Patient.objects.create(patient_id='P-REP-1', name='Patient One', age=25, gender='MALE', registered_at_facility=self.fac_1a)
        p2 = Patient.objects.create(patient_id='P-REP-2', name='Patient Two', age=65, gender='FEMALE', registered_at_facility=self.fac_1a)

        v1 = Visit.objects.create(visit_id='V-REP-1', patient=p1, facility=self.fac_1a, opd_date=self.today, status='COMPLETED', assigned_doctor=self.doctor)
        v2 = Visit.objects.create(visit_id='V-REP-2', patient=p2, facility=self.fac_1a, opd_date=self.today, priority='EMERGENCY', status='WAITING_FOR_TRIAGE')

        res = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        self.assertEqual(data['facility']['id'], self.fac_1a.id)
        self.assertEqual(data['period']['type'], 'day')
        self.assertEqual(data['opd_patient']['total_registered_patients'], 2)
        self.assertEqual(data['opd_patient']['total_opd_visits'], 2)
        self.assertEqual(data['opd_patient']['completed_visits'], 1)
        self.assertEqual(data['opd_patient']['emergency_visits'], 1)
        self.assertEqual(data['opd_patient']['demographics']['male'], 1)
        self.assertEqual(data['opd_patient']['demographics']['female'], 1)
        self.assertEqual(data['opd_patient']['age_groups']['19_30'], 1)
        self.assertEqual(data['opd_patient']['age_groups']['60_plus'], 1)

    def test_cross_facility_isolation(self):
        """Hospital Admin Facility 1A must NOT see Facility 2 data even if requested."""
        self.client.force_authenticate(user=self.hospital_admin)

        # Create record in Facility 2
        p_fac2 = Patient.objects.create(patient_id='P-FAC2-1', name='Fac2 Patient', registered_at_facility=self.fac_2)
        Visit.objects.create(visit_id='V-FAC2-1', patient=p_fac2, facility=self.fac_2, opd_date=self.today)

        # Attempt to request facility 2
        res = self.client.get(f'/api/reports/hospital/?facility={self.fac_2.id}&period=day&date={self.today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Scoped strictly to Fac 1A, does NOT see Fac 2 data
        self.assertEqual(res.data['facility']['id'], self.fac_1a.id)
        self.assertEqual(res.data['opd_patient']['total_opd_visits'], 0)

    def test_pharmacy_and_dashboard_reconciliation(self):
        """Dashboard and Reports must calculate identical numbers for low stock, out of stock, expiring."""
        med1 = MedicineMaster.objects.create(generic_name='Paracetamol', minimum_stock=50, reorder_level=100)
        med2 = MedicineMaster.objects.create(generic_name='Amoxicillin', minimum_stock=30, reorder_level=60)

        # Low stock batch for med1 (qty 20 <= 50)
        MedicineBatch.objects.create(
            facility=self.fac_1a, medicine=med1, batch_number='B-01',
            quantity=20, expiry_date=self.today + datetime.timedelta(days=120), status='ACTIVE'
        )
        # med2 has no batch -> OUT_OF_STOCK

        self.client.force_authenticate(user=self.hospital_admin)

        # Dashboard check
        dash_res = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_low = dash_res.data['pharmacy']['low_stock']
        dash_out = dash_res.data['pharmacy']['out_of_stock']

        # Reports check
        rep_res = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}')
        self.assertEqual(rep_res.status_code, status.HTTP_200_OK)
        rep_low = rep_res.data['pharmacy']['inventory']['low_stock_medicines']
        rep_out = rep_res.data['pharmacy']['inventory']['out_of_stock_medicines']

        # 100% Reconciliation
        self.assertEqual(dash_low, rep_low)
        self.assertEqual(dash_out, rep_out)
        self.assertEqual(rep_low, 1)
        self.assertEqual(rep_out, 1)

    def test_reconciled_stock_movement(self):
        """Opening Stock + Received - Dispensed + Adjusted == Closing Stock."""
        med = MedicineMaster.objects.create(generic_name='Metformin', minimum_stock=10, reorder_level=20)
        batch = MedicineBatch.objects.create(
            facility=self.fac_1a, medicine=med, batch_number='B-MET-1',
            quantity=100, expiry_date=self.today + datetime.timedelta(days=180), status='ACTIVE'
        )

        InventoryTransaction.objects.create(
            facility=self.fac_1a, medicine=med, batch=batch,
            transaction_type='PURCHASE_RECEIVED', quantity=50
        )
        InventoryTransaction.objects.create(
            facility=self.fac_1a, medicine=med, batch=batch,
            transaction_type='DISPENSED', quantity=20, reference_id='RX-101'
        )

        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        items = res.data['pharmacy']['stock_movement']['items']
        self.assertTrue(len(items) > 0)
        m_item = next(it for it in items if it['medicine_id'] == med.id)

        opening = m_item['opening_stock']
        rec = m_item['received']
        disp = m_item['dispensed']
        adj = m_item['adjusted']
        closing = m_item['closing_stock']

        # Mathematical reconciliation check
        self.assertEqual(opening + rec - disp + adj, closing)
        self.assertEqual(rec, 50)
        self.assertEqual(disp, 20)
        self.assertEqual(closing, 100)

    def test_zero_data_handling(self):
        """Zero data results in clean 0 values and no division by zero errors in comparisons."""
        self.client.force_authenticate(user=self.hospital_admin)
        past_date = self.today - datetime.timedelta(days=300)
        res = self.client.get(f'/api/reports/hospital/?period=day&date={past_date.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['opd_patient']['total_opd_visits'], 0)
        # Comparison percentage is safely None or string, not crashing
        self.assertEqual(res.data['comparison']['metrics']['opd_visits']['current'], 0)

    def test_hospital_admin_week_and_month_and_year_reports(self):
        self.client.force_authenticate(user=self.hospital_admin)

        res_week = self.client.get(f'/api/reports/hospital/?period=week&date={self.today.isoformat()}')
        self.assertEqual(res_week.status_code, status.HTTP_200_OK)
        self.assertEqual(res_week.data['period']['type'], 'week')

        res_month = self.client.get(f'/api/reports/hospital/?period=month&date={self.today.isoformat()}')
        self.assertEqual(res_month.status_code, status.HTTP_200_OK)
        self.assertEqual(res_month.data['period']['type'], 'month')

        res_year = self.client.get(f'/api/reports/hospital/?period=year&date={self.today.isoformat()}')
        self.assertEqual(res_year.status_code, status.HTTP_200_OK)
        self.assertEqual(res_year.data['period']['type'], 'year')

    def test_csv_export_endpoint(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get(f'/api/reports/export/?type=opd&period=day&date={self.today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'text/csv')

        res_pharm = self.client.get(f'/api/reports/export/?type=pharmacy&period=day&date={self.today.isoformat()}')
        self.assertEqual(res_pharm.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pharm['Content-Type'], 'text/csv')

        res_stock = self.client.get(f'/api/reports/export/?type=stock_consumption&period=day&date={self.today.isoformat()}')
        self.assertEqual(res_stock.status_code, status.HTTP_200_OK)
        self.assertEqual(res_stock['Content-Type'], 'text/csv')


class ReconciledDashboardAndReportsTests(APITestCase):
    """
    Authoritative test suite verifying Step 5 reconciliation between Dashboard
    and Hospital Admin Reports (Requirements A through M).
    """
    def setUp(self):
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_1 = District.objects.create(name='District 1', code='D1', state=self.state)
        self.district_2 = District.objects.create(name='District 2', code='D2', state=self.state)

        self.fac_1a = Facility.objects.create(
            facility_code='F-1A', facility_name='Facility 1A',
            facility_type=FacilityTypeChoices.UPHC, state=self.state, district=self.district_1
        )
        self.fac_1b = Facility.objects.create(
            facility_code='F-1B', facility_name='Facility 1B',
            facility_type=FacilityTypeChoices.UPHC, state=self.state, district=self.district_1
        )
        self.fac_2 = Facility.objects.create(
            facility_code='F-2', facility_name='Facility 2',
            facility_type=FacilityTypeChoices.UPHC, state=self.state, district=self.district_2
        )

        self.district_officer = User.objects.create_user(
            username='do_recon', password='password123',
            role=RoleChoices.DISTRICT_OFFICER, assigned_district=self.district_1
        )
        self.hospital_admin = User.objects.create_user(
            username='ha_recon_1a', password='password123',
            role=RoleChoices.HOSPITAL_ADMIN, assigned_facility=self.fac_1a
        )
        self.doctor = User.objects.create_user(
            username='doc_recon_1a', password='password123',
            role=RoleChoices.DOCTOR, assigned_facility=self.fac_1a
        )

        self.today = datetime.date.today()
        self.past_date = self.today - datetime.timedelta(days=10)

    # A. Same facility + same date: Dashboard and corresponding report KPI match.
    def test_a_same_facility_same_date_kpis_match(self):
        p1 = Patient.objects.create(patient_id='P1-RECON', name='Pat 1', registered_at_facility=self.fac_1a, registration_date=self.today)
        p2 = Patient.objects.create(patient_id='P2-RECON', name='Pat 2', registered_at_facility=self.fac_1a, registration_date=self.today)
        Visit.objects.create(visit_id='V1-RECON', patient=p1, facility=self.fac_1a, opd_date=self.today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE', priority='EMERGENCY')
        Visit.objects.create(visit_id='V2-RECON', patient=p2, facility=self.fac_1a, opd_date=self.today, current_queue='COMPLETED', status='COMPLETED', priority='NORMAL')

        self.client.force_authenticate(user=self.hospital_admin)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        self.assertEqual(dash['visits']['total'], rep['opd_patient']['total_opd_visits'])
        self.assertEqual(dash['visits']['emergency'], rep['opd_patient']['emergency_visits'])
        self.assertEqual(dash['visits']['completed'], rep['opd_patient']['completed_visits'])
        self.assertEqual(dash['patients']['registered_today'], rep['opd_patient']['new_patients'])
        self.assertEqual(dash['visits']['total'], rep['summary_cards']['patients']['total_visits'])
        self.assertEqual(dash['visits']['emergency'], rep['summary_cards']['patients']['emergency'])
        self.assertEqual(dash['visits']['completed'], rep['summary_cards']['patients']['completed'])

    # B. Historical dashboard date: No accidental use of today's OPD data.
    def test_b_historical_dashboard_date_no_todays_opd(self):
        p_today = Patient.objects.create(patient_id='P-TODAY', name='Today Pat', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V-TODAY', patient=p_today, facility=self.fac_1a, opd_date=self.today)

        p_past = Patient.objects.create(patient_id='P-PAST', name='Past Pat', registered_at_facility=self.fac_1a)
        Patient.objects.filter(pk=p_past.pk).update(registration_date=self.past_date)
        Visit.objects.create(visit_id='V-PAST-1', patient=p_past, facility=self.fac_1a, opd_date=self.past_date)
        Visit.objects.create(visit_id='V-PAST-2', patient=p_past, facility=self.fac_1a, opd_date=self.past_date)

        self.client.force_authenticate(user=self.hospital_admin)
        dash_past = self.client.get(f'/api/dashboard/summary/?date={self.past_date.isoformat()}').data

        self.assertEqual(dash_past['visits']['total'], 2)
        self.assertEqual(dash_past['todays_opd'], 2)
        self.assertEqual(dash_past['patients']['registered_today'], 1)
        self.assertFalse(dash_past['is_today'])

    # C. Pharmacy: Dashboard pharmacy counts match authoritative pharmacy calculations.
    def test_c_pharmacy_dashboard_and_report_match(self):
        med = MedicineMaster.objects.create(generic_name='Amoxicillin', minimum_stock=20)
        p = Patient.objects.create(patient_id='P-RX', name='Rx Pat', registered_at_facility=self.fac_1a)
        v1 = Visit.objects.create(visit_id='V-RX-1', patient=p, facility=self.fac_1a, opd_date=self.today)
        c1 = Consultation.objects.create(visit=v1, patient=p, doctor=self.doctor, facility=self.fac_1a, chief_complaint='Fever')
        Prescription.objects.create(consultation=c1, patient=p, doctor=self.doctor, facility=self.fac_1a, status='PENDING')

        v2 = Visit.objects.create(visit_id='V-RX-2', patient=p, facility=self.fac_1a, opd_date=self.today)
        c2 = Consultation.objects.create(visit=v2, patient=p, doctor=self.doctor, facility=self.fac_1a, chief_complaint='Cough')
        Prescription.objects.create(consultation=c2, patient=p, doctor=self.doctor, facility=self.fac_1a, status='DISPENSED')

        batch = MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-01', quantity=100, expiry_date=self.today + datetime.timedelta(days=90))
        InventoryTransaction.objects.create(facility=self.fac_1a, medicine=med, batch=batch, transaction_type='DISPENSED', quantity=15, reference_id='RX-2')

        self.client.force_authenticate(user=self.hospital_admin)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        self.assertEqual(dash['pharmacy']['total_prescriptions'], rep['pharmacy']['prescriptions']['total_prescriptions'])
        self.assertEqual(dash['pharmacy']['pending_prescriptions'], rep['pharmacy']['prescriptions']['pending'])
        self.assertEqual(dash['pharmacy']['dispensed_prescriptions'], rep['pharmacy']['prescriptions']['dispensed'])
        self.assertEqual(dash['pharmacy']['total_medicines_dispensed'], rep['pharmacy']['dispensing']['total_medicines_dispensed'])
        self.assertEqual(dash['pharmacy']['total_medicines_dispensed'], rep['summary_cards']['pharmacy']['dispensed_units'])

    # D. Queue: Dashboard queue counts match Report queue counts.
    def test_d_queue_counts_match(self):
        p = Patient.objects.create(patient_id='P-Q', name='Queue Pat', registered_at_facility=self.fac_1a)
        Visit.objects.create(visit_id='V-T', patient=p, facility=self.fac_1a, opd_date=self.today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE')
        Visit.objects.create(visit_id='V-D', patient=p, facility=self.fac_1a, opd_date=self.today, current_queue='DOCTOR', status='WAITING_FOR_DOCTOR')
        Visit.objects.create(visit_id='V-L', patient=p, facility=self.fac_1a, opd_date=self.today, current_queue='LAB', status='LAB_PENDING')
        Visit.objects.create(visit_id='V-P', patient=p, facility=self.fac_1a, opd_date=self.today, current_queue='PHARMACY', status='WAITING_FOR_PHARMACY')

        self.client.force_authenticate(user=self.hospital_admin)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        self.assertEqual(dash['queues']['triage_waiting'], rep['queue_service']['stages']['triage']['waiting'])
        self.assertEqual(dash['queues']['doctor_waiting'], rep['queue_service']['stages']['doctor']['waiting'])
        self.assertEqual(dash['queues']['lab_pending'], rep['summary_cards']['services']['lab_pending'])
        self.assertEqual(dash['queues']['pharmacy_waiting'], rep['queue_service']['stages']['pharmacy']['waiting'])
        self.assertEqual(dash['queues']['pharmacy_waiting'], rep['summary_cards']['services']['pharmacy_waiting'])

    # E. Low stock: Dashboard and Reports use identical threshold logic.
    def test_e_low_stock_threshold_identical(self):
        med_low = MedicineMaster.objects.create(generic_name='Paracetamol-Recon', minimum_stock=50, reorder_level=100)
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med_low, batch_number='B-LOW-R', quantity=30, expiry_date=self.today + datetime.timedelta(days=120))

        med_normal = MedicineMaster.objects.create(generic_name='Ibuprofen-Recon', minimum_stock=20, reorder_level=40)
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med_normal, batch_number='B-NORM-R', quantity=80, expiry_date=self.today + datetime.timedelta(days=120))

        self.client.force_authenticate(user=self.hospital_admin)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        self.assertEqual(dash['pharmacy']['low_stock'], rep['pharmacy']['inventory']['low_stock_medicines'])
        self.assertEqual(dash['pharmacy']['low_stock'], rep['summary_cards']['pharmacy']['low_stock_medicines'])

    # F. Expiry: Dashboard and Reports use identical expiry definition.
    def test_f_expiry_window_identical(self):
        med = MedicineMaster.objects.create(generic_name='Cough Syrup-Recon', minimum_stock=10)
        # Expired batch
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-EXP-R', quantity=10, expiry_date=self.today - datetime.timedelta(days=1))
        # Expiring soon batch (within 60 days)
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-SOON-R', quantity=10, expiry_date=self.today + datetime.timedelta(days=30))
        # Active batch (> 60 days)
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-ACT-R', quantity=50, expiry_date=self.today + datetime.timedelta(days=150))

        self.client.force_authenticate(user=self.hospital_admin)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        self.assertEqual(dash['pharmacy']['expired'], rep['pharmacy']['inventory']['expired_batches'])
        self.assertEqual(dash['pharmacy']['expiring_soon'], rep['pharmacy']['inventory']['expiring_soon_batches'])
        self.assertEqual(dash['pharmacy']['expiring_soon'], rep['summary_cards']['pharmacy']['expiring_soon_batches'])

    # G. Inventory movement: opening + received - dispensed +/- adjustment = closing where historical data is reconstructable.
    def test_g_inventory_movement_reconstructable(self):
        med = MedicineMaster.objects.create(generic_name='Azithromycin-Recon', minimum_stock=10)
        batch = MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-AZ-R', quantity=100, expiry_date=self.today + datetime.timedelta(days=200))

        InventoryTransaction.objects.create(facility=self.fac_1a, medicine=med, batch=batch, transaction_type='PURCHASE_RECEIVED', quantity=40)
        InventoryTransaction.objects.create(facility=self.fac_1a, medicine=med, batch=batch, transaction_type='DISPENSED', quantity=15)
        InventoryTransaction.objects.create(facility=self.fac_1a, medicine=med, batch=batch, transaction_type='ADJUSTMENT', quantity=-5)

        self.client.force_authenticate(user=self.hospital_admin)
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}').data

        item = next(it for it in rep['pharmacy']['stock_movement']['items'] if it['medicine_id'] == med.id)
        self.assertTrue(item['reconstructable'])
        self.assertTrue(item['historical_opening_exact'])
        self.assertEqual(item['derivation_status'], 'EXACT')

        opening = item['opening_stock']
        received = item['received']
        dispensed = item['dispensed']
        adjusted = item['adjusted']
        closing = item['closing_stock']

        self.assertEqual(opening + received - dispensed + adjusted, closing)

    # H. Insufficient transaction history: System does not fabricate an exact historical opening balance.
    def test_h_insufficient_transaction_history_no_fabrication(self):
        med = MedicineMaster.objects.create(generic_name='Old Drug-Recon', minimum_stock=10)
        # Batch exists with quantity 100, but ZERO transactions were ever recorded in InventoryTransaction
        MedicineBatch.objects.create(facility=self.fac_1a, medicine=med, batch_number='B-OLD-R', quantity=100, expiry_date=self.today + datetime.timedelta(days=200))

        self.client.force_authenticate(user=self.hospital_admin)
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.past_date.isoformat()}').data

        item = next(it for it in rep['pharmacy']['stock_movement']['items'] if it['medicine_id'] == med.id)
        # Must NOT fabricate an exact opening stock
        self.assertFalse(item['historical_opening_exact'])
        self.assertFalse(item['reconstructable'])
        self.assertIsNone(item['opening_stock'])
        self.assertEqual(item['derivation_status'], 'UNAVAILABLE')

    # I. Hospital Admin: cannot access another facility.
    def test_i_hospital_admin_cannot_access_another_facility(self):
        self.client.force_authenticate(user=self.hospital_admin)
        res = self.client.get(f'/api/reports/hospital/?facility={self.fac_2.id}&period=day&date={self.today.isoformat()}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Strictly locked to Facility 1A
        self.assertEqual(res.data['facility']['id'], self.fac_1a.id)

    # J. District Officer: cannot access another district.
    def test_j_district_officer_cannot_access_another_district(self):
        self.client.force_authenticate(user=self.district_officer)
        # Request facility in District 2
        res = self.client.get(f'/api/dashboard/summary/?facility={self.fac_2.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Clamped to District 1 scope (2 facilities in District 1)
        self.assertIsNone(res.data.get('active_facility_id'))
        self.assertEqual(res.data.get('total_facilities'), 2)
        self.assertEqual(res.data['scope']['district'], 'District 1')

    # K. Invalid facility: must not silently broaden the user's scope.
    def test_k_invalid_facility_does_not_broaden_scope(self):
        self.client.force_authenticate(user=self.district_officer)
        res = self.client.get('/api/dashboard/summary/?facility=99999999')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Remains clamped to District 1, not all facilities in DB
        self.assertEqual(res.data.get('total_facilities'), 2)
        self.assertEqual(res.data['scope']['district'], 'District 1')

    # L. Zero-data facility: all metrics return valid zero/empty values without errors.
    def test_l_zero_data_facility_returns_valid_empty_metrics(self):
        zero_fac = Facility.objects.create(facility_code='F-ZERO-R', facility_name='Zero Facility Recon', state=self.state, district=self.district_1)
        ha_zero = User.objects.create_user(username='ha_zero_r', password='password123', role=RoleChoices.HOSPITAL_ADMIN, assigned_facility=zero_fac)

        self.client.force_authenticate(user=ha_zero)
        dash = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}')
        rep = self.client.get(f'/api/reports/hospital/?period=day&date={self.today.isoformat()}')

        self.assertEqual(dash.status_code, status.HTTP_200_OK)
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        self.assertEqual(dash.data['visits']['total'], 0)
        self.assertEqual(rep.data['opd_patient']['total_opd_visits'], 0)
        self.assertEqual(rep.data['summary_cards']['patients']['total_visits'], 0)
        self.assertEqual(rep.data['pharmacy']['dispensing']['total_medicines_dispensed'], 0)

    # M. Multi-facility District Officer: district totals equal the sum of the selected facility-level metrics where aggregation is mathematically applicable.
    def test_m_multi_facility_district_officer_sum_aggregation(self):
        p1 = Patient.objects.create(patient_id='P-1A-R', name='Pat 1A', registered_at_facility=self.fac_1a, registration_date=self.today)
        p2 = Patient.objects.create(patient_id='P-1B-R', name='Pat 1B', registered_at_facility=self.fac_1b, registration_date=self.today)
        Visit.objects.create(visit_id='V-1A-R', patient=p1, facility=self.fac_1a, opd_date=self.today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE')
        Visit.objects.create(visit_id='V-1B-R', patient=p2, facility=self.fac_1b, opd_date=self.today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE')

        self.client.force_authenticate(user=self.district_officer)

        # Facility 1A request
        res_1a = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1a.id}&date={self.today.isoformat()}').data
        # Facility 1B request
        res_1b = self.client.get(f'/api/dashboard/summary/?facility={self.fac_1b.id}&date={self.today.isoformat()}').data
        # District-wide request
        res_dist = self.client.get(f'/api/dashboard/summary/?date={self.today.isoformat()}').data

        self.assertEqual(res_1a['visits']['total'], 1)
        self.assertEqual(res_1b['visits']['total'], 1)
        self.assertEqual(res_dist['visits']['total'], 2)
        # Sum equality check
        self.assertEqual(res_dist['visits']['total'], res_1a['visits']['total'] + res_1b['visits']['total'])
        self.assertEqual(res_dist['queues']['triage_waiting'], res_1a['queues']['triage_waiting'] + res_1b['queues']['triage_waiting'])





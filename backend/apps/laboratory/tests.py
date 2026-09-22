import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.geography.models import State, District, Zone, Ward
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabTestMaster, LabToken, LabOrder, LabSample, LabResult
from apps.pharmacy.models import MedicineMaster


class DoctorLabDoctorWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Geography
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR', state=self.state)
        self.zone = Zone.objects.create(name='South Zone', code='SZ', district=self.district)
        self.ward = Ward.objects.create(name='Jayanagar', ward_number='153', zone=self.zone)

        # Facilities
        self.facility_a = Facility.objects.create(
            facility_name='Namma Clinic Jayanagar', facility_code='NC-JAY-01',
            facility_type='URBAN_PHC', state=self.state, district=self.district, ward=self.ward
        )
        self.facility_b = Facility.objects.create(
            facility_name='Namma Clinic Malleshwaram', facility_code='NC-MAL-02',
            facility_type='URBAN_PHC', state=self.state, district=self.district, ward=self.ward
        )

        # Users
        self.doctor_a = User.objects.create_user(
            username='doctor_a', password='password123', role='DOCTOR',
            assigned_facility=self.facility_a, full_name='Dr. Anjali Rao'
        )
        self.doctor_b = User.objects.create_user(
            username='doctor_b', password='password123', role='DOCTOR',
            assigned_facility=self.facility_b, full_name='Dr. Vikram Hegde'
        )
        self.nurse_a = User.objects.create_user(
            username='nurse_a', password='password123', role='NURSE',
            assigned_facility=self.facility_a, full_name='Nurse Priya'
        )
        self.lab_tech_a = User.objects.create_user(
            username='lab_tech_a', password='password123', role='LAB_TECHNICIAN',
            assigned_facility=self.facility_a, full_name='Lab Tech Rajesh'
        )
        self.lab_tech_b = User.objects.create_user(
            username='lab_tech_b', password='password123', role='LAB_TECHNICIAN',
            assigned_facility=self.facility_b, full_name='Lab Tech Sunil'
        )

        # Patients
        self.patient_1 = Patient.objects.create(
            patient_id='PAT-BLR-001', name='Suresh Gowda', age=45, gender='MALE',
            mobile='9880011223', address='Jayanagar 4th Block', registered_at_facility=self.facility_a,
            district=self.district, ward=self.ward, registration_date=datetime.date.today()
        )
        self.patient_2 = Patient.objects.create(
            patient_id='PAT-BLR-002', name='Lakshmi Devi', age=38, gender='FEMALE',
            mobile='9880044556', address='Jayanagar 9th Block', registered_at_facility=self.facility_a,
            district=self.district, ward=self.ward, registration_date=datetime.date.today()
        )

        # Lab Tests Master
        self.test_fbg = LabTestMaster.objects.create(
            code='FBG', name='Fasting Blood Glucose', category='Biochemistry',
            reference_range='70 - 100 mg/dL', unit='mg/dL'
        )
        self.test_hba1c = LabTestMaster.objects.create(
            code='HBA1C', name='Glycated Hemoglobin (HbA1c)', category='Biochemistry',
            reference_range='4.0 - 5.6 %', unit='%'
        )
        self.test_lipid = LabTestMaster.objects.create(
            code='LIPID', name='Lipid Profile', category='Biochemistry',
            reference_range='< 200 mg/dL', unit='mg/dL'
        )

        # Medicine Master
        self.med_metformin = MedicineMaster.objects.create(
            generic_name='Metformin 500mg', brand_name='Glycomet', strength='500 mg',
            dosage_form='Tablet', category='Anti-Diabetic'
        )

    def _create_triaged_visit(self, patient, facility, doctor):
        """Helper to create a normal OPD visit with triage completed."""
        today = datetime.date.today()
        tok_num = Token.objects.filter(facility=facility, date=today).count() + 1
        visit = Visit.objects.create(
            visit_id=f"VIS-{facility.id}-{today.strftime('%Y%m%d')}-{tok_num:03d}",
            patient=patient, facility=facility, opd_date=today,
            current_queue='DOCTOR', status='WAITING_FOR_DOCTOR',
            chief_complaint='Routine evaluation'
        )
        token = Token.objects.create(
            token_number=tok_num, visit=visit, facility=facility, date=today,
            status='WAITING'
        )
        TriageVitals.objects.create(
            visit=visit, patient=patient, nurse=self.nurse_a,
            blood_pressure_systolic=120, blood_pressure_diastolic=80, pulse_bpm=72,
            temperature_f=98.6, blood_glucose_mgdl=110
        )
        return visit, token

    def test_01_one_visit_one_opd_token(self):
        """1. One clinical Visit has exactly one OPD Token."""
        visit, token = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        self.assertEqual(Token.objects.filter(visit=visit).count(), 1)
        self.assertEqual(visit.token.token_number, token.token_number)

    def test_02_doctor_orders_one_lab_test_and_links_consultation(self):
        """2, 7, 8. Doctor orders one lab test; links to consultation; enters WAITING_FOR_LAB."""
        visit, token = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        self.client.force_authenticate(user=self.doctor_a)

        # Create consultation
        c_res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'chief_complaint': 'Elevated fasting glucose',
            'has_lab_orders': True,
            'lab_test_ids': [self.test_fbg.id]
        }, format='json')
        self.assertEqual(c_res.status_code, status.HTTP_201_CREATED)
        consultation_id = c_res.data['id']

        # Verify Visit transitioned to WAITING_FOR_LAB, queue LAB, not COMPLETED
        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'LAB')
        self.assertEqual(visit.status, 'WAITING_FOR_LAB')

        # Verify LabOrder and LabToken created
        order = LabOrder.objects.filter(consultation_id=consultation_id).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.test_master, self.test_fbg)
        self.assertEqual(order.visit, visit)
        self.assertEqual(order.consultation_id, consultation_id)
        self.assertIsNotNone(order.lab_token)
        self.assertEqual(order.lab_token.status, 'ORDERED')

    def test_03_and_04_multiple_tests_use_one_lab_token(self):
        """3, 4, 5, 6. Doctor orders multiple lab tests; exactly ONE LabToken is created; no new Visit/OPD token."""
        visit, opd_token = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        self.client.force_authenticate(user=self.doctor_a)

        initial_visit_count = Visit.objects.count()
        initial_token_count = Token.objects.count()

        # Doctor creates consultation
        c_res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'chief_complaint': 'Suspected diabetes and dyslipidemia',
            'has_lab_orders': True
        }, format='json')
        self.assertEqual(c_res.status_code, status.HTTP_201_CREATED)
        consultation_id = c_res.data['id']

        # Doctor orders 3 tests under active consultation
        l_res = self.client.post('/api/lab/orders/', {
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'visit': visit.id,
            'consultation': consultation_id,
            'test_ids': [self.test_fbg.id, self.test_hba1c.id, self.test_lipid.id]
        }, format='json')
        self.assertEqual(l_res.status_code, status.HTTP_201_CREATED)

        # Assert exactly ONE Lab Token was created
        lab_tokens = LabToken.objects.filter(visit=visit)
        self.assertEqual(lab_tokens.count(), 1)
        active_lab_token = lab_tokens.first()
        self.assertTrue(active_lab_token.token_code.startswith('LAB-'))

        # Assert all 3 LabOrders are linked to the SAME Lab Token and active Consultation
        orders = LabOrder.objects.filter(visit=visit)
        self.assertEqual(orders.count(), 3)
        for ord_obj in orders:
            self.assertEqual(ord_obj.lab_token, active_lab_token)
            self.assertEqual(ord_obj.consultation_id, consultation_id)
            self.assertEqual(ord_obj.visit, visit)

        # 5, 6: Invariant: Lab Token does NOT create another Visit or another OPD Token
        self.assertEqual(Visit.objects.count(), initial_visit_count)
        self.assertEqual(Token.objects.count(), initial_token_count)

    def test_09_to_17_full_doctor_lab_doctor_flow_with_prescription_and_completion(self):
        """
        Tests complete workflow:
        Doctor order -> WAITING_FOR_LAB -> Sample Collection -> Result Entry -> Verification
        -> DOCTOR_REVIEW -> Doctor consult -> Prescription -> COMPLETED
        Retains SAME Visit, SAME OPD Token, SAME Consultation.
        """
        visit, opd_token = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        initial_visit_id = visit.visit_id
        initial_opd_token_num = opd_token.token_number

        # --- STEP A: Doctor starts consultation & orders 2 tests ---
        self.client.force_authenticate(user=self.doctor_a)
        c_res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'chief_complaint': 'Polyuria, polydipsia',
            'clinical_history': 'No prior chronic conditions',
            'has_lab_orders': True,
            'lab_test_ids': [self.test_fbg.id, self.test_hba1c.id]
        }, format='json')
        self.assertEqual(c_res.status_code, status.HTTP_201_CREATED)
        consultation_id = c_res.data['id']

        # Visit state: WAITING_FOR_LAB
        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'LAB')
        self.assertEqual(visit.status, 'WAITING_FOR_LAB')

        lab_token = LabToken.objects.get(visit=visit)
        self.assertEqual(lab_token.status, 'ORDERED')
        orders = list(LabOrder.objects.filter(lab_token=lab_token).order_by('id'))
        self.assertEqual(len(orders), 2)

        # --- STEP B: Lab Tech collects samples ---
        self.client.force_authenticate(user=self.lab_tech_a)
        for ord_item in orders:
            col_res = self.client.post(f'/api/lab/orders/{ord_item.id}/collect-sample/', {
                'sample_type': 'Venous Blood',
                'sample_code': f"SMP-TEST-{ord_item.id}"
            }, format='json')
            self.assertEqual(col_res.status_code, status.HTTP_200_OK)

        lab_token.refresh_from_db()
        self.assertEqual(lab_token.status, 'IN_PROGRESS')

        visit.refresh_from_db()
        self.assertEqual(visit.status, 'LAB_IN_PROGRESS')

        # --- STEP C: Lab Tech verifies results for first test ---
        res1 = self.client.post(f'/api/lab/orders/{orders[0].id}/save-result/', {
            'result_value': '142',
            'unit': 'mg/dL',
            'reference_range': '70 - 100 mg/dL',
            'interpretation_flag': 'HIGH',
            'notes': 'Fasting blood glucose elevated.'
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # First test verified, but second remains pending -> Visit still in LAB
        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'LAB')
        lab_token.refresh_from_db()
        self.assertEqual(lab_token.status, 'IN_PROGRESS')

        # --- STEP D: Lab Tech verifies results for second test ---
        res2 = self.client.post(f'/api/lab/orders/{orders[1].id}/save-result/', {
            'result_value': '7.4',
            'unit': '%',
            'reference_range': '4.0 - 5.6 %',
            'interpretation_flag': 'HIGH',
            'notes': 'HbA1c diagnostic of diabetes.'
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # All tests verified: LabToken becomes COMPLETED and Visit transitions to DOCTOR / DOCTOR_REVIEW!
        lab_token.refresh_from_db()
        self.assertEqual(lab_token.status, 'COMPLETED')

        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'DOCTOR')
        self.assertEqual(visit.status, 'DOCTOR_REVIEW')

        # --- STEP E: Doctor returns, reviews results, prescribes and finalizes encounter ---
        self.client.force_authenticate(user=self.doctor_a)

        # Doctor fetches orders and results for this visit
        fetch_res = self.client.get(f'/api/lab/orders/?visit={visit.id}')
        self.assertEqual(fetch_res.status_code, status.HTTP_200_OK)
        fetched_orders = fetch_res.data.get('results', fetch_res.data)
        self.assertEqual(len(fetched_orders), 2)
        for fo in fetched_orders:
            self.assertEqual(fo['status'], 'VERIFIED')
            self.assertIsNotNone(fo['result'])

        # Doctor updates the SAME consultation (idempotent, no duplicate) with diagnosis and prescription
        con_update_res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'chief_complaint': 'Polyuria, polydipsia',
            'diagnosis_code': 'E11.9',
            'diagnosis_name': 'Type 2 Diabetes Mellitus without complications',
            'treatment_plan': 'Start Metformin 500mg, low carbohydrate diet',
            'prescription_items': [
                {
                    'medicine_id': self.med_metformin.id,
                    'dosage': '1-0-1 After Food',
                    'quantity': 14
                }
            ]
        }, format='json')
        self.assertEqual(con_update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(con_update_res.data['id'], consultation_id)

        # Assert no duplicate consultation was created
        self.assertEqual(Consultation.objects.filter(visit=visit).count(), 1)

        # Visit now advances to PHARMACY for drug dispensing
        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'PHARMACY')
        self.assertEqual(visit.status, 'WAITING_FOR_PHARMACY')

        # Assert SAME Visit and SAME OPD Token were retained throughout
        self.assertEqual(visit.visit_id, initial_visit_id)
        self.assertEqual(visit.token.token_number, initial_opd_token_num)
        self.assertEqual(Token.objects.filter(visit=visit).count(), 1)

    def test_18_cross_patient_result_isolation(self):
        """18. Lab results for patient 1 are isolated from patient 2."""
        visit1, _ = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        visit2, _ = self._create_triaged_visit(self.patient_2, self.facility_a, self.doctor_a)

        self.client.force_authenticate(user=self.doctor_a)
        # Order test for patient 1
        self.client.post('/api/lab/orders/', {
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'visit': visit1.id,
            'test_ids': [self.test_fbg.id]
        }, format='json')

        # Query orders for patient 2
        res = self.client.get(f'/api/lab/orders/?patient={self.patient_2.id}')
        orders_p2 = res.data.get('results', res.data)
        self.assertEqual(len(orders_p2), 0)

        # Query orders for visit 2
        res_v2 = self.client.get(f'/api/lab/orders/?visit={visit2.id}')
        orders_v2 = res_v2.data.get('results', res_v2.data)
        self.assertEqual(len(orders_v2), 0)

    def test_19_cross_facility_result_isolation(self):
        """19. Doctor at Facility B cannot access lab orders of Facility A."""
        visit_a, _ = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        self.client.force_authenticate(user=self.doctor_a)
        self.client.post('/api/lab/orders/', {
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'visit': visit_a.id,
            'test_ids': [self.test_fbg.id]
        }, format='json')

        # Authenticate as Doctor B at Facility B
        self.client.force_authenticate(user=self.doctor_b)
        res = self.client.get(f'/api/lab/orders/?facility={self.facility_a.id}')
        # Should be filtered out or empty due to facility scoping
        orders = res.data.get('results', res.data)
        self.assertEqual(len(orders), 0)

    def test_20_and_21_non_lab_consultation_flow_remains_functional(self):
        """20, 21. Standard consultation without lab tests works directly to Pharmacy or Completion."""
        visit, opd_token = self._create_triaged_visit(self.patient_1, self.facility_a, self.doctor_a)
        self.client.force_authenticate(user=self.doctor_a)

        # Consultation with no lab and no prescription -> COMPLETED
        c_res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient_1.id,
            'facility': self.facility_a.id,
            'chief_complaint': 'Mild headache, tension',
            'diagnosis_name': 'Tension Headache'
        }, format='json')
        self.assertEqual(c_res.status_code, status.HTTP_201_CREATED)

        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'COMPLETED')
        self.assertEqual(visit.status, 'COMPLETED')
        self.assertEqual(visit.token.status, 'COMPLETED')

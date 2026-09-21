import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.geography.models import District, Ward, Zone, State

class PhaseABRegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Geography setup
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR', state=self.state)
        self.zone = Zone.objects.create(name='South Zone', code='SZ', district=self.district)
        self.ward = Ward.objects.create(name='Jayanagar', ward_number='153', zone=self.zone)

        # Facilities
        self.hosp = Facility.objects.create(
            facility_name='District Hospital', facility_code='DH-01',
            facility_type='DISTRICT_HOSPITAL', state=self.state, district=self.district, ward=self.ward
        )
        self.clinic = Facility.objects.create(
            facility_name='Namma Clinic Jayanagar', facility_code='NC-01',
            facility_type='URBAN_PHC', state=self.state, district=self.district, ward=self.ward, parent_facility=self.hosp
        )


        # Users
        self.dho = User.objects.create_user(
            username='dho_user', password='password123', role='DISTRICT_OFFICER',
            assigned_district=self.district, full_name='Dr. District Officer'
        )
        self.doctor = User.objects.create_user(
            username='doc_user', password='password123', role='DOCTOR',
            assigned_facility=self.clinic, full_name='Dr. Clinic Doctor'
        )
        self.nurse = User.objects.create_user(
            username='nurse_user', password='password123', role='NURSE',
            assigned_facility=self.clinic, full_name='Nurse Ananya'
        )
        self.pharmacist = User.objects.create_user(
            username='pharm_user', password='password123', role='PHARMACIST',
            assigned_facility=self.clinic, full_name='Pharmacist Suresh'
        )
        self.lab_tech = User.objects.create_user(
            username='lab_user', password='password123', role='LAB_TECHNICIAN',
            assigned_facility=self.clinic, full_name='Lab Tech Rajesh'
        )

        # Patient
        self.patient = Patient.objects.create(
            patient_id='PAT-2026-0001', name='Ramesh Kumar Gowda', age=52, gender='MALE',
            mobile='9876543210', address='Jayanagar 4th Block', registered_at_facility=self.clinic,
            district=self.district, ward=self.ward, registration_date=datetime.date.today()
        )

        # Medicine Master
        self.med_met = MedicineMaster.objects.create(
            generic_name='Metformin HCl', brand_name='Glycomet', strength='500 mg',
            dosage_form='Tablet', category='Anti-Diabetic', minimum_stock=50, reorder_level=100
        )
        self.med_amlo = MedicineMaster.objects.create(
            generic_name='Amlodipine Besylate', brand_name='Amlopres', strength='5 mg',
            dosage_form='Tablet', category='Anti-Hypertensive', minimum_stock=50, reorder_level=100
        )

        # Stock Batches (FEFO: Batch 1 expires earlier than Batch 2)
        today = datetime.date.today()
        self.batch_met_early = MedicineBatch.objects.create(
            facility=self.clinic, medicine=self.med_met, batch_number='MET-2026-EARLY',
            received_date=today, expiry_date=today + datetime.timedelta(days=30),
            quantity=100, unit_cost=2.5, status='ACTIVE'
        )
        self.batch_met_late = MedicineBatch.objects.create(
            facility=self.clinic, medicine=self.med_met, batch_number='MET-2026-LATE',
            received_date=today, expiry_date=today + datetime.timedelta(days=180),
            quantity=200, unit_cost=2.5, status='ACTIVE'
        )

    # =========================================================================
    # PHASE A: RBAC & DHO ROUTE ACCESS & MUTATION RESTRICTION (NEGATIVE TESTS)
    # =========================================================================

    def test_dho_can_access_patient_ncd_and_surveillance_read_endpoints(self):
        """DHO must have read access to /patients, /ncd, /surveillance."""
        NCDRecord.objects.create(
            patient=self.patient, facility=self.clinic, hypertension_diagnosed=True,
            risk_level='HIGH', control_status='UNCONTROLLED', last_bp='150/96'
        )
        DiseaseCase.objects.create(
            patient=self.patient, facility=self.clinic, ward=self.ward,
            disease_name='Dengue', severity='MODERATE'
        )


        self.client.force_authenticate(user=self.dho)

        res_patients = self.client.get('/api/patients/')
        self.assertEqual(res_patients.status_code, status.HTTP_200_OK)

        res_ncd = self.client.get('/api/ncd/')
        self.assertEqual(res_ncd.status_code, status.HTTP_200_OK)

        res_surv = self.client.get('/api/surveillance/')
        self.assertEqual(res_surv.status_code, status.HTTP_200_OK)

    def test_negative_dho_blocked_from_patient_and_clinical_mutations(self):
        """DHO must be strictly rejected (403 Forbidden) on write operations."""
        self.client.force_authenticate(user=self.dho)

        # 1. Attempt to create patient
        res_pat = self.client.post('/api/patients/', {
            'name': 'Unauthorized Patient', 'age': 40, 'gender': 'FEMALE',
            'mobile': '9999988888', 'registered_at_facility': self.clinic.id
        })
        self.assertEqual(res_pat.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Attempt to create NCD record
        res_ncd = self.client.post('/api/ncd/', {
            'patient': self.patient.id, 'facility': self.clinic.id, 'risk_level': 'HIGH'
        })
        self.assertEqual(res_ncd.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Attempt to create surveillance case
        res_surv = self.client.post('/api/surveillance/', {
            'patient': self.patient.id, 'facility': self.clinic.id, 'ward': self.ward.id,
            'disease_name': 'Cholera'
        })
        self.assertEqual(res_surv.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Attempt to create consultation
        res_cons = self.client.post('/api/consultations/', {
            'patient': self.patient.id, 'facility': self.clinic.id, 'chief_complaint': 'Unauthorized'
        })
        self.assertEqual(res_cons.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Attempt to dispense medicine
        res_disp = self.client.post('/api/pharmacy/dispense/', {'prescription_id': 1})
        self.assertEqual(res_disp.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Attempt to create referral
        res_ref = self.client.post('/api/referrals/', {
            'patient': self.patient.id, 'source_facility': self.clinic.id,
            'destination_facility': self.hosp.id, 'reason': 'Unauthorized'
        })
        self.assertEqual(res_ref.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_unauthorized_role_access(self):
        """Lab technician cannot dispense medicine or create clinical consultations."""
        self.client.force_authenticate(user=self.lab_tech)

        res_disp = self.client.post('/api/pharmacy/dispense/', {'prescription_id': 1})
        self.assertEqual(res_disp.status_code, status.HTTP_403_FORBIDDEN)

        res_cons = self.client.post('/api/consultations/', {
            'patient': self.patient.id, 'facility': self.clinic.id, 'chief_complaint': 'Unauthorized'
        })
        self.assertEqual(res_cons.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # PHASE B1: PRESCRIPTIONITEM -> MEDICINEMASTER INTEGRITY & SET_NULL
    # =========================================================================

    def test_prescription_item_medicine_foreign_key_and_set_null(self):
        """PrescriptionItem must link to MedicineMaster. Deleting medicine must SET_NULL."""
        visit = Visit.objects.create(
            visit_id='VST-001', patient=self.patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='DOCTOR', status='IN_CONSULTATION'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=self.patient, doctor=self.doctor, facility=self.clinic,
            chief_complaint='Elevated blood sugar'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=self.patient, doctor=self.doctor,
            facility=self.clinic, status='ACTIVE'
        )
        item = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_met, medicine_name='Metformin HCl 500mg',
            dosage='1-0-1', quantity=20, status='PENDING'
        )

        # Verify FK
        self.assertEqual(item.medicine, self.med_met)
        self.assertEqual(item.medicine.id, self.med_met.id)

        # Verify SET_NULL on delete
        temp_med = MedicineMaster.objects.create(
            generic_name='Temporary Drug', brand_name='Temp', strength='10 mg',
            dosage_form='Tablet', category='Other', minimum_stock=10, reorder_level=20
        )
        item2 = PrescriptionItem.objects.create(
            prescription=rx, medicine=temp_med, medicine_name='Temporary Drug 10mg',
            dosage='1-0-0', quantity=10, status='PENDING'
        )
        temp_med.delete()

        item2.refresh_from_db()
        self.assertIsNone(item2.medicine)
        self.assertEqual(item2.medicine_name, 'Temporary Drug 10mg')
        self.assertTrue(Prescription.objects.filter(id=rx.id).exists())

    def test_consultation_creation_links_medicine_foreign_key(self):
        """Consultation API creates PrescriptionItem with medicine ForeignKey."""
        visit = Visit.objects.create(
            visit_id='VST-002', patient=self.patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='DOCTOR', status='IN_CONSULTATION'
        )
        self.client.force_authenticate(user=self.doctor)

        res = self.client.post('/api/consultations/', {
            'visit': visit.id,
            'patient': self.patient.id,
            'facility': self.clinic.id,
            'chief_complaint': 'Uncontrolled diabetes',
            'prescription_items': [
                {
                    'medicine_id': self.med_met.id,
                    'dosage': '1-0-1 After Food',
                    'quantity': 28
                }
            ]
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        created_item = PrescriptionItem.objects.filter(prescription__consultation__visit=visit).first()
        self.assertIsNotNone(created_item)
        self.assertEqual(created_item.medicine_id, self.med_met.id)
        self.assertEqual(created_item.medicine.generic_name, 'Metformin HCl')

    # =========================================================================
    # PHASE B1 & FEFO: STOCK DEDUCTION USES REFERENCED MEDICINE
    # =========================================================================

    def test_fefo_stock_deduction_uses_medicine_foreign_key(self):
        """DispenseMedicineView must deduct from earliest-expiry batch of referenced medicine."""
        visit = Visit.objects.create(
            visit_id='VST-003', patient=self.patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='PHARMACY', status='WAITING_FOR_PHARMACY'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=self.patient, doctor=self.doctor, facility=self.clinic,
            chief_complaint='Diabetes routine review'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=self.patient, doctor=self.doctor,
            facility=self.clinic, status='ACTIVE'
        )
        p_item = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_met, medicine_name='Metformin HCl 500mg',
            dosage='1-0-1', quantity=20, status='PENDING'
        )

        initial_early_qty = self.batch_met_early.quantity
        initial_late_qty = self.batch_met_late.quantity

        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.batch_met_early.refresh_from_db()
        self.batch_met_late.refresh_from_db()
        p_item.refresh_from_db()

        # FEFO check: earliest batch deducted by 20, late batch untouched
        self.assertEqual(self.batch_met_early.quantity, initial_early_qty - 20)
        self.assertEqual(self.batch_met_late.quantity, initial_late_qty)
        self.assertEqual(p_item.status, 'DISPENSED')

    # =========================================================================
    # PHASE B2: REFERRAL ENCOUNTER INTEGRITY (VISIT & CONSULTATION)
    # =========================================================================

    def test_referral_links_to_authoritative_visit_and_consultation(self):
        """Referral must record visit, consultation, patient, source and destination facilities."""
        visit = Visit.objects.create(
            visit_id='VST-004', patient=self.patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='DOCTOR', status='IN_CONSULTATION'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=self.patient, doctor=self.doctor, facility=self.clinic,
            chief_complaint='Suspected angina and hypertension'
        )

        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/referrals/', {
            'patient': self.patient.id,
            'visit': visit.id,
            'consultation': consult.id,
            'source_facility': self.clinic.id,
            'destination_facility': self.hosp.id,
            'reason': 'Specialist cardiology evaluation',
            'clinical_summary': 'Hypertension with chest pain',
            'required_service': 'Cardiology Specialist Consult',
            'urgency': 'HIGH'
        })

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ref_id = res.data['id']
        ref = Referral.objects.get(id=ref_id)
        self.assertEqual(ref.patient, self.patient)
        self.assertEqual(ref.visit, visit)
        self.assertEqual(ref.consultation, consult)
        self.assertEqual(ref.source_facility, self.clinic)
        self.assertEqual(ref.destination_facility, self.hosp)
        self.assertEqual(ref.referring_doctor, self.doctor)

    # =========================================================================
    # PHASE B3: DASHBOARD FALLBACK REMOVAL & ZERO INTEGRITY
    # =========================================================================

    def test_dashboard_medicine_count_zero_when_no_stock_without_fallback(self):
        """Dashboard must return 0 for total_medicines when no stock batches exist (no 'or 14')."""
        empty_facility = Facility.objects.create(
            facility_name='Empty Clinic', facility_code='EC-01',
            facility_type='URBAN_PHC', state=self.state, district=self.district, ward=self.ward
        )

        admin_empty = User.objects.create_user(
            username='admin_empty', password='password123', role='HOSPITAL_ADMIN',
            assigned_facility=empty_facility
        )

        self.client.force_authenticate(user=admin_empty)
        res = self.client.get(f'/api/dashboard/summary/?facility={empty_facility.id}')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Authoritative: exactly 0, not 14
        self.assertEqual(res.data['inventory_summary']['total_medicines'], 0)

    def test_dashboard_registration_count_zero_when_none_registered_today(self):
        """Dashboard registration count must return 0 when 0 registrations today (no 'or todays_opd')."""
        # Create an OPD visit on today for an existing patient registered in the past
        past_date = datetime.date.today() - datetime.timedelta(days=10)
        past_patient = Patient.objects.create(
            patient_id='PAT-PAST-001', name='Past Patient', age=45, gender='FEMALE',
            mobile='9111122222', address='Old Town', registered_at_facility=self.clinic,
            district=self.district, ward=self.ward, registration_date=past_date
        )
        Visit.objects.create(
            visit_id='VST-OPD-TODAY', patient=past_patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='TRIAGE', status='WAITING_FOR_TRIAGE'
        )

        # Clear any patient registered today at clinic for this test
        Patient.objects.filter(registered_at_facility=self.clinic, registration_date=datetime.date.today()).update(registration_date=past_date)

        self.client.force_authenticate(user=self.doctor)
        res = self.client.get(f'/api/dashboard/summary/?facility={self.clinic.id}&date={datetime.date.today()}')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['registered_today'], 0)
        self.assertGreater(res.data['todays_opd'], 0)
        # OPD stage flow registration must NOT fall back to todays_opd!
        self.assertEqual(res.data['opd_stage_flow']['registration'], 0)

    # =========================================================================
    # PHASE B4 & B5: DOCTOR FOLLOW-UP KPI & PHARMACIST GLOBAL AGGREGATION
    # =========================================================================

    def test_doctor_followup_kpi_derived_from_followup_model(self):
        """Follow-up KPI must reflect FollowUp records due today, not referrals completed."""
        today = datetime.date.today()
        FollowUp.objects.create(
            patient=self.patient, facility=self.clinic, category='NCD',
            due_date=today, status='PENDING', notes='BP check'
        )

        self.client.force_authenticate(user=self.doctor)
        res = self.client.get(f'/api/dashboard/summary/?facility={self.clinic.id}&date={today}')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('followups_summary', res.data)
        self.assertEqual(res.data['followups_summary']['due_today'], 1)
        self.assertEqual(res.data['kpis']['followups_due'], 1)

    def test_pharmacist_global_kpis_returned_authoritatively(self):
        """Pharmacy summary counts must be provided by backend to prevent pagination bugs."""
        # Create 3 prescriptions
        for i in range(3):
            v = Visit.objects.create(
                visit_id=f'VST-RX-{i}', patient=self.patient, facility=self.clinic,
                visit_date=datetime.date.today(), opd_date=datetime.date.today(),
                current_queue='PHARMACY', status='WAITING_FOR_PHARMACY'
            )
            c = Consultation.objects.create(
                visit=v, patient=self.patient, doctor=self.doctor, facility=self.clinic,
                chief_complaint=f'Issue {i}'
            )
            Prescription.objects.create(
                consultation=c, patient=self.patient, doctor=self.doctor,
                facility=self.clinic, status='PENDING' if i < 2 else 'DISPENSED',
                date=datetime.date.today()
            )

        self.client.force_authenticate(user=self.pharmacist)

        # 1. Check dashboard/summary
        res_dash = self.client.get(f'/api/dashboard/summary/?facility={self.clinic.id}')
        self.assertEqual(res_dash.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dash.data['pharmacy_summary']['total_prescriptions'], 3)
        self.assertEqual(res_dash.data['pharmacy_summary']['pending'], 2)
        self.assertEqual(res_dash.data['pharmacy_summary']['dispensed_today'], 1)

        # 2. Check pharmacy/dashboard endpoint
        res_pharm = self.client.get(f'/api/pharmacy/dashboard/?facility={self.clinic.id}')
        self.assertEqual(res_pharm.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pharm.data['total_prescriptions_count'], 3)
        self.assertEqual(res_pharm.data['pending_prescriptions_count'], 2)
        self.assertEqual(res_pharm.data['dispensed_today_count'], 1)

    # =========================================================================
    # END-TO-END DEMO JOURNEY: RAMESH KUMAR GOWDA
    # =========================================================================

    def test_ramesh_kumar_gowda_end_to_end_journey(self):
        """Verify complete clinical lifecycle for Ramesh Kumar Gowda:
        Registration -> Visit -> Token -> Triage -> Consultation -> Prescription (Medicine FK)
        -> FEFO Dispensation -> Referral (Encounter FK) -> FollowUp.
        """
        # 1. Visit & Token
        v = Visit.objects.create(
            visit_id='VST-RAMESH-DEMO', patient=self.patient, facility=self.clinic,
            visit_date=datetime.date.today(), opd_date=datetime.date.today(),
            current_queue='TRIAGE', status='WAITING_FOR_TRIAGE'
        )
        Token.objects.create(visit=v, token_number=1, facility=self.clinic, priority='NORMAL', status='WAITING')

        # 2. Nurse Triage
        v.current_queue = 'TRIAGE'
        v.status = 'IN_TRIAGE'
        v.save()
        triage = TriageVitals.objects.create(
            visit=v, patient=self.patient, nurse=self.nurse,
            blood_pressure_systolic=148, blood_pressure_diastolic=96,
            pulse_bpm=82, temperature_f=98.4, blood_glucose_mgdl=185
        )

        v.current_queue = 'DOCTOR'
        v.status = 'WAITING_FOR_DOCTOR'
        v.save()

        # 3. Doctor Consultation
        v.status = 'IN_CONSULTATION'
        v.save()
        consult = Consultation.objects.create(
            visit=v, patient=self.patient, doctor=self.doctor, facility=self.clinic,
            chief_complaint='Dizziness & elevated glucose',
            diagnosis_code='E11.9 / I10', diagnosis_name='Type 2 Diabetes Mellitus with Essential Hypertension'
        )

        # 4. Prescription with Medicine FK
        rx = Prescription.objects.create(
            consultation=consult, patient=self.patient, doctor=self.doctor,
            facility=self.clinic, status='ACTIVE'
        )
        p_item1 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_met, medicine_name='Metformin HCl 500 mg Tablet',
            dosage='1-0-1 After Food', quantity=14, status='PENDING'
        )
        p_item2 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_amlo, medicine_name='Amlodipine Besylate 5 mg Tablet',
            dosage='1-0-0 Morning', quantity=14, status='PENDING'
        )
        v.current_queue = 'PHARMACY'
        v.status = 'WAITING_FOR_PHARMACY'
        v.save()

        # 5. Pharmacist FEFO Dispensation
        self.client.force_authenticate(user=self.pharmacist)
        # Add stock for Amlodipine
        MedicineBatch.objects.create(
            facility=self.clinic, medicine=self.med_amlo, batch_number='AML-2026-01',
            received_date=datetime.date.today(), expiry_date=datetime.date.today() + datetime.timedelta(days=90),
            quantity=50, unit_cost=1.5, status='ACTIVE'
        )
        disp_res = self.client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
        self.assertEqual(disp_res.status_code, status.HTTP_200_OK)

        rx.refresh_from_db()
        v.refresh_from_db()
        self.assertEqual(rx.status, 'DISPENSED')
        self.assertEqual(v.status, 'COMPLETED')

        # 6. Referral linked to Visit and Consultation
        ref = Referral.objects.create(
            referral_id='REF-RAMESH-DEMO-001', patient=self.patient, visit=v, consultation=consult,
            source_facility=self.clinic, destination_facility=self.hosp, referring_doctor=self.doctor,
            reason='Specialist cardiology review for uncontrolled hypertension',
            clinical_summary='52/M BP 148/96, glucose 185', required_service='Cardiology',
            urgency='HIGH', status='COMPLETED'
        )
        self.assertEqual(ref.visit_id, v.id)
        self.assertEqual(ref.consultation_id, consult.id)

        # 7. Follow-up
        fu = FollowUp.objects.create(
            patient=self.patient, referral=ref, visit=v, facility=self.clinic,
            category='REFERRAL', due_date=datetime.date.today() + datetime.timedelta(days=14),
            status='PENDING', notes='Post cardiology specialist follow-up'
        )
        self.assertEqual(fu.patient_id, self.patient.id)
        self.assertEqual(fu.visit_id, v.id)
        self.assertEqual(fu.referral_id, ref.id)

import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.patients.models import Patient, PatientDocument
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction, Vendor, PurchaseOrder, PurchaseOrderItem
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
            'urgency': 'URGENT'
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

    def test_dho_cross_district_read_isolation(self):
        """
        DHO Data-Scope Security:
        Verify DHO District A can access District A data, but is strictly isolated from District B data.
        """
        # Create District B and its entities
        district_b = District.objects.create(name='Mysuru District', code='MYS', state=self.state)
        zone_b = Zone.objects.create(name='Mysuru Central Zone', code='MCZ', district=district_b)
        ward_b = Ward.objects.create(name='KRS Ward', ward_number='101', zone=zone_b)
        clinic_b = Facility.objects.create(
            facility_name='Mysuru Central Clinic', facility_code='MYS-CLINIC-01',
            facility_type='URBAN_PHC', state=self.state, district=district_b, ward=ward_b
        )
        patient_b = Patient.objects.create(
            patient_id='PAT-MYS-0001', name='Basavaraj Bommai', age=45, gender='MALE',
            mobile='9123456780', address='KRS Road Mysuru', registered_at_facility=clinic_b,
            district=district_b, ward=ward_b, registration_date=datetime.date.today()
        )
        ncd_b = NCDRecord.objects.create(
            patient=patient_b, facility=clinic_b, hypertension_diagnosed=True,
            risk_level='MEDIUM', control_status='CONTROLLED', treatment_status='UNDER_TREATMENT'
        )
        case_b = DiseaseCase.objects.create(
            patient=patient_b, facility=clinic_b, ward=ward_b,
            disease_name='Dengue Fever', severity='MODERATE', status='CONFIRMED',
            report_date=datetime.date.today()
        )
        ref_b = Referral.objects.create(
            referral_id='REF-MYS-0001', patient=patient_b,
            source_facility=clinic_b, destination_facility=clinic_b, referring_doctor=self.doctor,
            reason='Specialist consult in Mysuru', clinical_summary='Dengue management',
            required_service='General Medicine', urgency='MEDIUM', status='CREATED'
        )
        batch_b = MedicineBatch.objects.create(
            facility=clinic_b, medicine=self.med_met, batch_number='MYS-MET-01',
            received_date=datetime.date.today(), expiry_date=datetime.date.today() + datetime.timedelta(days=120),
            quantity=150, unit_cost=3.0, status='ACTIVE'
        )

        # 1. Test DHO of District A (self.dho)
        self.client.force_authenticate(user=self.dho)

        # Patients isolation
        res_patients = self.client.get('/api/patients/')
        self.assertEqual(res_patients.status_code, status.HTTP_200_OK)
        patient_ids = [p['id'] for p in res_patients.data.get('results', res_patients.data)]
        self.assertIn(self.patient.id, patient_ids)
        self.assertNotIn(patient_b.id, patient_ids)

        # Direct detail access to District B patient should be blocked (404/403)
        res_patient_b_detail = self.client.get(f'/api/patients/{patient_b.id}/')
        self.assertIn(res_patient_b_detail.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        # NCD isolation
        res_ncd = self.client.get('/api/ncd/')
        self.assertEqual(res_ncd.status_code, status.HTTP_200_OK)
        ncd_ids = [n['id'] for n in res_ncd.data.get('results', res_ncd.data)]
        self.assertNotIn(ncd_b.id, ncd_ids)

        # Surveillance isolation
        res_surv = self.client.get('/api/surveillance/')
        self.assertEqual(res_surv.status_code, status.HTTP_200_OK)
        case_ids = [c['id'] for c in res_surv.data.get('results', res_surv.data)]
        self.assertNotIn(case_b.id, case_ids)

        # Referral isolation
        res_ref = self.client.get('/api/referrals/')
        self.assertEqual(res_ref.status_code, status.HTTP_200_OK)
        ref_ids = [r['id'] for r in res_ref.data.get('results', res_ref.data)]
        self.assertNotIn(ref_b.id, ref_ids)

        # Pharmacy batches isolation
        res_batch = self.client.get('/api/pharmacy/batches/')
        self.assertEqual(res_batch.status_code, status.HTTP_200_OK)
        batch_ids = [b['id'] for b in res_batch.data.get('results', res_batch.data)]
        self.assertNotIn(batch_b.id, batch_ids)

        # Reporting summary for District B facility should yield 0 for District A DHO
        res_summary = self.client.get(f'/api/dashboard/summary/?facility={clinic_b.id}')
        self.assertEqual(res_summary.status_code, status.HTTP_200_OK)
        self.assertEqual(res_summary.data['total_patients'], 0)
        self.assertEqual(res_summary.data['todays_opd'], 0)

        # 2. Test DHO of District B
        dho_b = User.objects.create_user(
            username='dho_mysuru', password='password123', role='DISTRICT_OFFICER',
            assigned_district=district_b, full_name='Dr. Mysuru DHO'
        )
        self.client.force_authenticate(user=dho_b)

        # District B DHO should see District B patient, and NOT see District A patient
        res_b_patients = self.client.get('/api/patients/')
        self.assertEqual(res_b_patients.status_code, status.HTTP_200_OK)
        b_patient_ids = [p['id'] for p in res_b_patients.data.get('results', res_b_patients.data)]
        self.assertIn(patient_b.id, b_patient_ids)
        self.assertNotIn(self.patient.id, b_patient_ids)

        # District B DHO can see District B NCD, surveillance, referrals, batches
        res_b_ncd = self.client.get('/api/ncd/')
        b_ncd_ids = [n['id'] for n in res_b_ncd.data.get('results', res_b_ncd.data)]
        self.assertIn(ncd_b.id, b_ncd_ids)

        res_b_surv = self.client.get('/api/surveillance/')
        b_case_ids = [c['id'] for c in res_b_surv.data.get('results', res_b_surv.data)]
        self.assertIn(case_b.id, b_case_ids)

        res_b_batch = self.client.get('/api/pharmacy/batches/')
        b_batch_ids = [b['id'] for b in res_b_batch.data.get('results', res_b_batch.data)]
        self.assertIn(batch_b.id, b_batch_ids)


class PhaseC1RegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Geography setup
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR', state=self.state)
        self.zone = Zone.objects.create(name='South Zone', code='SZ', district=self.district)
        self.ward = Ward.objects.create(name='Jayanagar', ward_number='153', zone=self.zone)

        # Facilities
        self.hosp = Facility.objects.create(
            facility_name='Victoria District Hospital', facility_code='HOSP-01',
            facility_type='MAIN_HOSPITAL', state=self.state, district=self.district, ward=self.ward
        )
        self.clinic = Facility.objects.create(
            facility_name='Varthur Rural Primary Clinic', facility_code='CLINIC-01',
            facility_type='RURAL_CLINIC', state=self.state, district=self.district, ward=self.ward,
            parent_facility=self.hosp
        )

        # Users
        self.dho = User.objects.create_user(
            username='dho_c1', password='password123', role='DISTRICT_OFFICER',
            assigned_district=self.district, full_name='Dr. District Officer'
        )
        self.admin = User.objects.create_user(
            username='admin_c1', password='password123', role='HOSPITAL_ADMIN',
            assigned_facility=self.clinic, full_name='Hospital Admin'
        )
        self.doctor = User.objects.create_user(
            username='doc_c1', password='password123', role='DOCTOR',
            assigned_facility=self.clinic, full_name='Dr. Clinic Doctor'
        )
        self.nurse = User.objects.create_user(
            username='nurse_c1', password='password123', role='NURSE',
            assigned_facility=self.clinic, full_name='Nurse Ananya'
        )

        # Patient
        self.patient = Patient.objects.create(
            patient_id='PAT-C1-001', name='Ramesh Kumar', age=52, gender='MALE',
            mobile='9876543210', address='Varthur Road', registered_at_facility=self.clinic,
            district=self.district, ward=self.ward, registration_date=datetime.date.today()
        )

        # Visits
        today = datetime.date.today()
        self.visit_doc = Visit.objects.create(
            visit_id='VIS-C1-DOC-01', patient=self.patient, facility=self.clinic,
            opd_date=today, current_queue='DOCTOR', status='WAITING_FOR_DOCTOR', priority='NORMAL'
        )
        self.token_doc = Token.objects.create(
            token_number=1, visit=self.visit_doc, facility=self.clinic, date=today, status='WAITING'
        )

        self.visit_triage = Visit.objects.create(
            visit_id='VIS-C1-TRI-01', patient=self.patient, facility=self.clinic,
            opd_date=today, current_queue='TRIAGE', status='WAITING_FOR_TRIAGE', priority='NORMAL'
        )
        self.token_triage = Token.objects.create(
            token_number=2, visit=self.visit_triage, facility=self.clinic, date=today, status='WAITING'
        )

    # =========================================================================
    # FND-01: ROUTE GUARD PERMISSIONS (ARS, Quality, Integrations)
    # =========================================================================

    def test_fnd01_dho_and_admin_have_access_to_ars_quality_and_integrations(self):
        """DHO and Hospital Admin must be authorized to access ARS, Quality, and Integrations."""
        from apps.ars.models import ARSMeeting
        from apps.quality.models import QualityChecklist, BiomedicalWasteLog
        from apps.integrations.models import IntegrationConfiguration

        ARSMeeting.objects.create(facility=self.clinic, meeting_date=datetime.date.today(), chairperson_name='Corporator Ramesh', agenda='Primary Care Review')
        QualityChecklist.objects.create(facility=self.clinic, cleanliness_score=92)
        BiomedicalWasteLog.objects.create(facility=self.clinic, yellow_bag_kg=4.5)
        IntegrationConfiguration.objects.get_or_create(system_name='ABDM_TEST', defaults={'display_name': 'ABDM M1/M2 Connector'})

        for user in [self.dho, self.admin]:
            self.client.force_authenticate(user=user)
            res_ars = self.client.get('/api/ars/meetings/')
            self.assertEqual(res_ars.status_code, status.HTTP_200_OK)

            res_qc = self.client.get('/api/quality/checklists/')
            self.assertEqual(res_qc.status_code, status.HTTP_200_OK)

            res_waste = self.client.get('/api/quality/waste-logs/')
            self.assertEqual(res_waste.status_code, status.HTTP_200_OK)

            res_int = self.client.get('/api/integrations/')
            self.assertEqual(res_int.status_code, status.HTTP_200_OK)

    # =========================================================================
    # FND-02: DOCTOR QUEUE ACTIONS & PRIVILEGE ENFORCEMENT
    # =========================================================================

    def test_fnd02_doctor_can_call_next_patient_in_doctor_queue(self):
        """Doctor can call the next patient waiting in the DOCTOR queue."""
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/visits/call-next/', {
            'facility': self.clinic.id,
            'queue': 'DOCTOR'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'IN_CONSULTATION')
        self.assertEqual(res.data['assigned_doctor_name'], self.doctor.full_name)

    def test_fnd02_doctor_cannot_call_triage_queue(self):
        """Doctor is forbidden from calling patients from the TRIAGE queue."""
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/visits/call-next/', {
            'facility': self.clinic.id,
            'queue': 'TRIAGE'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_fnd02_doctor_cannot_create_arbitrary_visits(self):
        """Doctor does not have queue.create permission and cannot create new OPD visits."""
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/visits/', {
            'patient': self.patient.id,
            'facility': self.clinic.id,
            'visit_type': 'GENERAL_OPD'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_fnd02_nurse_can_call_triage_queue_but_not_doctor_queue(self):
        """Nurse can call TRIAGE queue, but is blocked from calling DOCTOR queue."""
        self.client.force_authenticate(user=self.nurse)
        res_triage = self.client.post('/api/visits/call-next/', {
            'facility': self.clinic.id,
            'queue': 'TRIAGE'
        })
        self.assertEqual(res_triage.status_code, status.HTTP_200_OK)
        self.assertEqual(res_triage.data['status'], 'IN_TRIAGE')

        res_doc = self.client.post('/api/visits/call-next/', {
            'facility': self.clinic.id,
            'queue': 'DOCTOR'
        })
        self.assertEqual(res_doc.status_code, status.HTTP_403_FORBIDDEN)

    def test_fnd02_dho_cannot_call_next_patient(self):
        """DHO has read-only oversight and cannot call patients in active queues."""
        self.client.force_authenticate(user=self.dho)
        res = self.client.post('/api/visits/call-next/', {
            'facility': self.clinic.id,
            'queue': 'DOCTOR'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # FND-04: NCD AND SURVEILLANCE EXPORT
    # =========================================================================

    def test_fnd04_ncd_export_returns_ncd_records_not_patient_master(self):
        """Exporting NCD report must output NCDRecord dataset with screening columns."""
        NCDRecord.objects.create(
            patient=self.patient, facility=self.clinic, hypertension_diagnosed=True,
            diabetes_diagnosed=True, risk_level='HIGH', control_status='UNCONTROLLED',
            last_bp='150/96', last_glucose=185
        )
        self.client.force_authenticate(user=self.dho)
        res = self.client.get(f'/api/reports/export/?type=ncd&facility={self.clinic.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.content.decode('utf-8')
        self.assertIn('Hypertension Diagnosed', content)
        self.assertIn('Diabetes Diagnosed', content)
        self.assertIn('150/96', content)
        self.assertIn('185', content)
        self.assertIn(self.patient.name, content)

    def test_fnd04_surveillance_export_returns_disease_cases_not_patient_master(self):
        """Exporting Surveillance report must output DiseaseCase dataset with disease columns."""
        DiseaseCase.objects.create(
            disease_name='Dengue Fever', patient=self.patient, facility=self.clinic,
            ward=self.ward, severity='SEVERE', status='CONFIRMED', notes='Platelet drop below 50k'
        )
        self.client.force_authenticate(user=self.dho)
        res = self.client.get(f'/api/reports/export/?type=surveillance&facility={self.clinic.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.content.decode('utf-8')
        self.assertIn('Disease Name', content)
        self.assertIn('Dengue Fever', content)
        self.assertIn('Platelet drop below 50k', content)
        self.assertIn(self.ward.name, content)

    def test_fnd04_patients_export_returns_patient_directory(self):
        """Exporting patients report must output patient demographic columns."""
        self.client.force_authenticate(user=self.dho)
        res = self.client.get(f'/api/reports/export/?type=patients&facility={self.clinic.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = res.content.decode('utf-8')
        self.assertIn('Patient ID', content)
        self.assertIn('Registration Date', content)
        self.assertIn(self.patient.patient_id, content)

    def test_fnd04_dho_cross_district_export_isolation(self):
        """
        DHO for District A must NOT be able to export records from District B,
        even if explicitly passing ?facility=<DistrictB_Facility_ID>.
        """
        district_b = District.objects.create(name='Mysuru District', code='KA-MYS', state=self.state)
        zone_b = Zone.objects.create(name='Mysuru City Zone', district=district_b)
        ward_b = Ward.objects.create(name='KRP', ward_number=1, zone=zone_b)
        fac_b = Facility.objects.create(
            facility_name='Mysuru Community Hospital', facility_type='COMMUNITY_HEALTH',
            district=district_b, state=self.state, zone=zone_b, ward=ward_b
        )
        patient_b = Patient.objects.create(
            patient_id='PAT-MYS-001', name='Anand Kumar Mysuru', age=50, gender='MALE',
            mobile='9123456780', registered_at_facility=fac_b, district=district_b
        )

        # Create records in District A
        NCDRecord.objects.create(
            patient=self.patient, facility=self.clinic, hypertension_diagnosed=True,
            diabetes_diagnosed=False, risk_level='MODERATE', control_status='CONTROLLED',
            last_bp='130/84', last_glucose=110
        )
        DiseaseCase.objects.create(
            disease_name='Acute Gastroenteritis', patient=self.patient, facility=self.clinic,
            ward=self.ward, severity='MILD', status='CONFIRMED', notes='District A case'
        )

        # Create records in District B
        NCDRecord.objects.create(
            patient=patient_b, facility=fac_b, hypertension_diagnosed=True,
            diabetes_diagnosed=True, risk_level='HIGH', control_status='UNCONTROLLED',
            last_bp='170/110', last_glucose=250
        )
        DiseaseCase.objects.create(
            disease_name='Cholera Outbreak', patient=patient_b, facility=fac_b,
            ward=ward_b, severity='SEVERE', status='CONFIRMED', notes='District B epidemic alert'
        )

        # Authenticate as DHO for District A
        self.client.force_authenticate(user=self.dho)

        # 1. Attacking/cross-district NCD export by supplying District B facility parameter
        res_ncd_b = self.client.get(f'/api/reports/export/?type=ncd&facility={fac_b.id}')
        self.assertEqual(res_ncd_b.status_code, status.HTTP_200_OK)
        content_ncd_b = res_ncd_b.content.decode('utf-8')
        self.assertNotIn('Anand Kumar Mysuru', content_ncd_b)
        self.assertNotIn('170/110', content_ncd_b)
        self.assertNotIn('Mysuru Community Hospital', content_ncd_b)
        # Verify only header line was written (0 data records)
        lines_ncd = [line.strip() for line in content_ncd_b.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines_ncd), 1, "Should contain only CSV header row")

        # 2. Attacking/cross-district Surveillance export by supplying District B facility parameter
        res_surv_b = self.client.get(f'/api/reports/export/?type=surveillance&facility={fac_b.id}')
        self.assertEqual(res_surv_b.status_code, status.HTTP_200_OK)
        content_surv_b = res_surv_b.content.decode('utf-8')
        self.assertNotIn('Cholera Outbreak', content_surv_b)
        self.assertNotIn('Anand Kumar Mysuru', content_surv_b)
        self.assertNotIn('District B epidemic alert', content_surv_b)
        lines_surv = [line.strip() for line in content_surv_b.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines_surv), 1, "Should contain only CSV header row")

        # 3. Requesting NCD export without facility param: District A returned, District B excluded
        res_ncd_all = self.client.get('/api/reports/export/?type=ncd')
        self.assertEqual(res_ncd_all.status_code, status.HTTP_200_OK)
        content_ncd_all = res_ncd_all.content.decode('utf-8')
        self.assertIn(self.patient.name, content_ncd_all)
        self.assertIn('130/84', content_ncd_all)
        self.assertNotIn('Anand Kumar Mysuru', content_ncd_all)
        self.assertNotIn('170/110', content_ncd_all)

        # 4. Requesting Surveillance export without facility param: District A returned, District B excluded
        res_surv_all = self.client.get('/api/reports/export/?type=surveillance')
        self.assertEqual(res_surv_all.status_code, status.HTTP_200_OK)
        content_surv_all = res_surv_all.content.decode('utf-8')
        self.assertIn('Acute Gastroenteritis', content_surv_all)
        self.assertIn('District A case', content_surv_all)
        self.assertNotIn('Cholera Outbreak', content_surv_all)
        self.assertNotIn('District B epidemic alert', content_surv_all)

    # =========================================================================
    # FND-07: CLINICAL RE-SAVE IDEMPOTENCY (No HTTP 500 on Re-save)
    # =========================================================================

    def test_fnd07_triage_resave_updates_existing_record_without_500(self):
        """Re-saving triage vitals on the same visit must update and return HTTP 200, never 500."""
        self.client.force_authenticate(user=self.nurse)
        # 1. Initial save
        res1 = self.client.post('/api/triage/', {
            'visit': self.visit_triage.id,
            'patient': self.patient.id,
            'blood_pressure_systolic': 130,
            'blood_pressure_diastolic': 85,
            'pulse_bpm': 75,
            'temperature_f': 98.6
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res1.data['blood_pressure_systolic'], 130)

        # 2. Re-save / update with revised systolic BP
        res2 = self.client.post('/api/triage/', {
            'visit': self.visit_triage.id,
            'patient': self.patient.id,
            'blood_pressure_systolic': 145,
            'blood_pressure_diastolic': 90,
            'pulse_bpm': 80,
            'temperature_f': 99.1
        })
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['blood_pressure_systolic'], 145)
        self.assertEqual(TriageVitals.objects.filter(visit=self.visit_triage).count(), 1)

    def test_fnd07_consultation_resave_updates_existing_record_without_500(self):
        """Re-saving consultation on the same visit must update and return HTTP 200, never 500."""
        self.client.force_authenticate(user=self.doctor)
        # 1. Initial consultation save
        res1 = self.client.post('/api/consultations/', {
            'visit': self.visit_doc.id,
            'patient': self.patient.id,
            'facility': self.clinic.id,
            'chief_complaint': 'Severe headache',
            'diagnosis_name': 'Essential Hypertension'
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 2. Re-save / update with revised diagnosis
        res2 = self.client.post('/api/consultations/', {
            'visit': self.visit_doc.id,
            'patient': self.patient.id,
            'facility': self.clinic.id,
            'chief_complaint': 'Severe headache and blurred vision',
            'diagnosis_name': 'Hypertensive Urgency with Type 2 Diabetes'
        })
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['diagnosis_name'], 'Hypertensive Urgency with Type 2 Diabetes')
        self.assertEqual(Consultation.objects.filter(visit=self.visit_doc).count(), 1)

    # =========================================================================
    # FND-03: FOLLOWUP CROSS-ENCOUNTER INTEGRITY
    # =========================================================================

    def test_fnd03_followup_consistent_with_referral_succeeds(self):
        """Creating FollowUp matching Referral patient, visit, and facility succeeds."""
        referral = Referral.objects.create(
            referral_id='REF-TEST-001', patient=self.patient, visit=self.visit_doc,
            source_facility=self.clinic, destination_facility=self.hosp, referring_doctor=self.doctor,
            reason='Specialist cardiology consult'
        )

        followup = FollowUp.objects.create(
            patient=self.patient, referral=referral, visit=self.visit_doc,
            facility=self.clinic, category='REFERRAL', due_date=datetime.date.today() + datetime.timedelta(days=14)
        )
        self.assertEqual(followup.patient, referral.patient)
        self.assertEqual(followup.visit, referral.visit)
        self.assertEqual(followup.facility, referral.source_facility)

    def test_fnd03_followup_cross_encounter_mismatch_rejected(self):
        """Creating FollowUp referencing Referral from a different visit is rejected by validation."""
        other_visit = Visit.objects.create(
            visit_id='VIS-OTHER-999', patient=self.patient, facility=self.clinic,
            opd_date=datetime.date.today() - datetime.timedelta(days=7),
            current_queue='COMPLETED', status='COMPLETED'
        )
        referral = Referral.objects.create(
            referral_id='REF-TEST-002', patient=self.patient, visit=self.visit_doc,
            source_facility=self.clinic, destination_facility=self.hosp, referring_doctor=self.doctor,
            reason='Specialist cardiology consult'
        )

        # 1. Serializer validation check
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/followups/', {
            'patient': self.patient.id,
            'referral': referral.id,
            'visit': other_visit.id,  # Mismatch!
            'facility': self.clinic.id,
            'category': 'REFERRAL',
            'due_date': str(datetime.date.today() + datetime.timedelta(days=14))
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('visit', str(res.data))

        # 2. Model clean validation check
        from django.core.exceptions import ValidationError
        bad_fu = FollowUp(
            patient=self.patient, referral=referral, visit=other_visit,
            facility=self.clinic, category='REFERRAL', due_date=datetime.date.today()
        )
        with self.assertRaises(ValidationError):
            bad_fu.clean()


# =============================================================================
# PHASE C2 REGRESSION SUITE: DATA INTEGRITY & PATIENT JOURNEY CONSISTENCY
# =============================================================================

class PhaseC2RegressionTests(TestCase):
    """
    Controlled regression suite for approved Phase C2 findings:
    - FND-08: Patient facility/district integrity and DHO visibility
    - FND-09: Triage requirement before doctor consultation queue
    - FND-10: Coherent Visit status vs queue state
    - FND-11: Prescription header vs line item consistency
    - FND-12: Atomic pharmacy dispensing and inventory transactions
    """

    def setUp(self):
        self.client = APIClient()
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_a = District.objects.create(name='Bengaluru Urban', code='KA-BU', state=self.state)
        self.district_b = District.objects.create(name='Mysuru District', code='KA-MYS', state=self.state)

        self.zone_a = Zone.objects.create(name='East Zone', district=self.district_a)
        self.ward_a = Ward.objects.create(name='Varthur Ward', ward_number=149, zone=self.zone_a)

        self.clinic_a = Facility.objects.create(
            facility_code='FAC-C2-A',
            facility_name='Varthur Primary Health Clinic', facility_type='PRIMARY_HEALTH_CENTRE',
            district=self.district_a, state=self.state, zone=self.zone_a, ward=self.ward_a
        )

        self.zone_b = Zone.objects.create(name='Mysuru Zone', district=self.district_b)
        self.ward_b = Ward.objects.create(name='KRP Ward', ward_number=1, zone=self.zone_b)
        self.clinic_b = Facility.objects.create(
            facility_code='FAC-C2-B',
            facility_name='Mysuru Clinic', facility_type='PRIMARY_HEALTH_CENTRE',
            district=self.district_b, state=self.state, zone=self.zone_b, ward=self.ward_b
        )

        # Users
        self.dho_a = User.objects.create_user(
            username='dho_a', role='DISTRICT_OFFICER', assigned_district=self.district_a
        )
        self.dho_b = User.objects.create_user(
            username='dho_b', role='DISTRICT_OFFICER', assigned_district=self.district_b
        )
        self.nurse = User.objects.create_user(
            username='nurse_c2', role='NURSE', assigned_facility=self.clinic_a
        )
        self.doctor = User.objects.create_user(
            username='doctor_c2', role='DOCTOR', assigned_facility=self.clinic_a
        )
        self.pharmacist = User.objects.create_user(
            username='pharm_c2', role='PHARMACIST', assigned_facility=self.clinic_a
        )

        # Medicine & Batch
        self.med_aml = MedicineMaster.objects.create(
            generic_name='Amlodipine Besylate', brand_name='Amlopres', strength='5 mg', dosage_form='Tablet'
        )
        self.med_met = MedicineMaster.objects.create(
            generic_name='Metformin HCl', brand_name='Glycomet', strength='500 mg', dosage_form='Tablet'
        )
        self.batch_aml = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=self.med_aml, batch_number='AML-C2-01',
            quantity=50, unit_cost=1.20, expiry_date=datetime.date.today() + datetime.timedelta(days=90), status='ACTIVE'
        )
        self.batch_met = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=self.med_met, batch_number='MET-C2-01',
            quantity=100, unit_cost=0.80, expiry_date=datetime.date.today() + datetime.timedelta(days=120), status='ACTIVE'
        )

    # -------------------------------------------------------------------------
    # FND-08: Patient Facility / District Integrity
    # -------------------------------------------------------------------------

    def test_fnd08_patient_facility_populates_district_and_dho_visibility(self):
        """Registering a patient with facility auto-populates district and is visible to DHO."""
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post('/api/patients/', {
            'name': 'Gowramma Test',
            'age': 45,
            'gender': 'FEMALE',
            'mobile': '9845112233',
            'address': 'Varthur Village',
            'registered_at_facility': self.clinic_a.id
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['district'], self.district_a.id)

        # DHO A can see this patient
        self.client.force_authenticate(user=self.dho_a)
        res_dho = self.client.get('/api/patients/')
        self.assertEqual(res_dho.status_code, status.HTTP_200_OK)
        results = res_dho.data if isinstance(res_dho.data, list) else res_dho.data.get('results', [])
        p_ids = [p['id'] for p in results]
        self.assertIn(res.data['id'], p_ids)

    def test_fnd08_patient_facility_district_mismatch_rejected(self):
        """Attempting to set patient district different from facility district is rejected."""
        self.client.force_authenticate(user=self.nurse)
        # Serializer level
        res = self.client.post('/api/patients/', {
            'name': 'Mismatch Test',
            'age': 30,
            'gender': 'MALE',
            'mobile': '9845999888',
            'address': 'Test',
            'registered_at_facility': self.clinic_a.id,
            'district': self.district_b.id  # Mismatch! Clinic A is in District A
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('district', str(res.data))

        # Model clean level
        from django.core.exceptions import ValidationError
        bad_p = Patient(
            patient_id='PAT-ERR-001', name='Bad Mismatch', age=25, gender='MALE',
            mobile='9888000111', address='Bad Addr', registered_at_facility=self.clinic_a,
            district=self.district_b
        )
        with self.assertRaises(ValidationError):
            bad_p.clean()

    def test_fnd08_no_cross_district_leakage(self):
        """DHO of District A cannot see Patient registered in District B."""
        patient_b = Patient.objects.create(
            patient_id='PAT-B-001', name='Mysuru Citizen', age=40, gender='MALE',
            mobile='9777112233', address='Mysuru Ward 1', registered_at_facility=self.clinic_b,
            district=self.district_b
        )
        self.client.force_authenticate(user=self.dho_a)
        res = self.client.get('/api/patients/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        p_ids = [p['id'] for p in results]
        self.assertNotIn(patient_b.id, p_ids)

    # -------------------------------------------------------------------------
    # FND-09: Triage before Doctor Consultation
    # -------------------------------------------------------------------------

    def test_fnd09_untriaged_visit_cannot_advance_to_doctor_queue(self):
        """Untriaged visit cannot be advanced to DOCTOR queue via transition_status."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-T01', name='Triage Test Patient', age=32, gender='FEMALE',
            mobile='9666112233', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-T01', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='TRIAGE', status='WAITING_FOR_TRIAGE'
        )

        self.client.force_authenticate(user=self.nurse)
        # Attempt advancing without triage vitals
        res = self.client.post(f'/api/visits/{visit.id}/transition-status/', {
            'to_status': 'WAITING_FOR_DOCTOR',
            'queue': 'DOCTOR'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('triage', str(res.data['error']).lower())

    def test_fnd09_triaged_visit_can_advance_to_doctor_queue(self):
        """Visit with recorded triage vitals can advance to DOCTOR queue."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-T02', name='Triaged Patient', age=28, gender='FEMALE',
            mobile='9666112244', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-T02', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='TRIAGE', status='IN_TRIAGE'
        )
        TriageVitals.objects.create(
            visit=visit, patient=patient, nurse=self.nurse,
            blood_pressure_systolic=120, blood_pressure_diastolic=80, pulse_bpm=72
        )

        self.client.force_authenticate(user=self.nurse)
        res = self.client.post(f'/api/visits/{visit.id}/transition-status/', {
            'to_status': 'WAITING_FOR_DOCTOR',
            'queue': 'DOCTOR'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        visit.refresh_from_db()
        self.assertEqual(visit.current_queue, 'DOCTOR')
        self.assertEqual(visit.status, 'WAITING_FOR_DOCTOR')

    def test_fnd09_unauthorized_role_cannot_transition_to_doctor_queue(self):
        """Pharmacist or unauthorized role cannot transition visit to DOCTOR queue."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-T03', name='Auth Patient', age=29, gender='MALE',
            mobile='9666112255', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-T03', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='TRIAGE', status='WAITING_FOR_TRIAGE'
        )

        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post(f'/api/visits/{visit.id}/transition-status/', {
            'to_status': 'WAITING_FOR_DOCTOR',
            'queue': 'DOCTOR'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # FND-10: Visit Status vs Queue State
    # -------------------------------------------------------------------------

    def test_fnd10_completed_visit_queue_synchronized(self):
        """A completed visit must have its queue synchronized to COMPLETED."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-Q01', name='Queue Patient', age=50, gender='MALE',
            mobile='9555112233', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-Q01', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='TRIAGE', status='WAITING_FOR_TRIAGE'
        )

        # 1. API transition to COMPLETED sets queue to COMPLETED
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post(f'/api/visits/{visit.id}/transition-status/', {
            'to_status': 'COMPLETED'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        visit.refresh_from_db()
        self.assertEqual(visit.status, 'COMPLETED')
        self.assertEqual(visit.current_queue, 'COMPLETED')

        # 2. Model level: status=COMPLETED cannot coexist with queue=DOCTOR in clean()
        from django.core.exceptions import ValidationError
        bad_visit = Visit(
            visit_id='VIS-C2-BAD', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='DOCTOR', status='COMPLETED'
        )
        with self.assertRaises(ValidationError):
            bad_visit.clean()

    # -------------------------------------------------------------------------
    # FND-11: Prescription Header vs Item Status
    # -------------------------------------------------------------------------

    def test_fnd11_prescription_header_cannot_be_dispensed_with_pending_items(self):
        """Prescription status cannot be set to DISPENSED while items remain PENDING."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-RX01', name='Rx Patient', age=42, gender='FEMALE',
            mobile='9444112233', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-RX01', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='DOCTOR', status='IN_CONSULTATION'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            chief_complaint='Hypertension'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            status='ACTIVE'
        )
        PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_aml, medicine_name='Amlodipine 5mg',
            quantity=14, status='PENDING'
        )

        # 1. Direct model save check
        from django.core.exceptions import ValidationError
        rx.status = 'DISPENSED'
        with self.assertRaises(ValidationError):
            rx.clean()

        # 2. Serializer validation check
        from apps.consultations.views import PrescriptionSerializer
        serializer = PrescriptionSerializer(instance=rx, data={'status': 'DISPENSED'}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_fnd11_prescription_partially_dispensed_when_some_items_remain(self):
        """When some items are dispensed and others remain pending, header is PARTIALLY_DISPENSED."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-RX02', name='Partial Rx Patient', age=44, gender='MALE',
            mobile='9444112244', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-RX02', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='PHARMACY', status='WAITING_FOR_PHARMACY'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            chief_complaint='Diabetes and Hypertension'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            status='ACTIVE'
        )
        it1 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_aml, medicine_name='Amlodipine 5mg',
            quantity=14, status='PENDING'
        )
        it2 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_met, medicine_name='Metformin 500mg',
            quantity=28, status='PENDING'
        )

        self.client.force_authenticate(user=self.pharmacist)
        # Dispense only item 1
        res = self.client.post('/api/pharmacy/dispense/', {
            'prescription_id': rx.id,
            'items': [{'item_id': it1.id, 'batch_id': self.batch_aml.id, 'qty': 14}]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        rx.refresh_from_db()
        self.assertEqual(rx.status, 'PARTIALLY_DISPENSED')
        it1.refresh_from_db()
        self.assertEqual(it1.status, 'DISPENSED')
        it2.refresh_from_db()
        self.assertEqual(it2.status, 'PENDING')

    # -------------------------------------------------------------------------
    # FND-12: Inventory Transaction Consistency
    # -------------------------------------------------------------------------

    def test_fnd12_dispensing_creates_authoritative_inventory_transaction(self):
        """Dispensing decrements batch stock and creates InventoryTransaction atomically."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-INV01', name='Inventory Patient', age=35, gender='FEMALE',
            mobile='9333112233', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-INV01', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='PHARMACY', status='WAITING_FOR_PHARMACY'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            chief_complaint='Hypertension'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            status='ACTIVE'
        )
        it = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_aml, medicine_name='Amlodipine 5mg',
            quantity=10, status='PENDING'
        )

        initial_stock = self.batch_aml.quantity
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/pharmacy/dispense/', {
            'prescription_id': rx.id,
            'items': [{'item_id': it.id, 'batch_id': self.batch_aml.id, 'qty': 10}]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.batch_aml.refresh_from_db()
        self.assertEqual(self.batch_aml.quantity, initial_stock - 10)

        tx = InventoryTransaction.objects.filter(reference_id=f"PRESCR-{rx.id}").first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.facility, self.clinic_a)
        self.assertEqual(tx.medicine, self.med_aml)
        self.assertEqual(tx.batch, self.batch_aml)
        self.assertEqual(tx.transaction_type, 'DISPENSED')
        self.assertEqual(tx.quantity, 10)

    def test_fnd12_cannot_double_dispense_item(self):
        """Attempting to dispense an already dispensed item is rejected and does not double decrement."""
        patient = Patient.objects.create(
            patient_id='PAT-C2-INV02', name='Double Dispense Patient', age=37, gender='MALE',
            mobile='9333112244', address='Varthur Colony', registered_at_facility=self.clinic_a,
            district=self.district_a
        )
        visit = Visit.objects.create(
            visit_id='VIS-C2-INV02', patient=patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='PHARMACY', status='WAITING_FOR_PHARMACY'
        )
        consult = Consultation.objects.create(
            visit=visit, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            chief_complaint='Hypertension'
        )
        rx = Prescription.objects.create(
            consultation=consult, patient=patient, doctor=self.doctor, facility=self.clinic_a,
            status='ACTIVE'
        )
        it = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_aml, medicine_name='Amlodipine 5mg',
            quantity=10, status='PENDING'
        )

        self.client.force_authenticate(user=self.pharmacist)
        # 1. First dispensation succeeds
        res1 = self.client.post('/api/pharmacy/dispense/', {
            'prescription_id': rx.id,
            'items': [{'item_id': it.id, 'batch_id': self.batch_aml.id, 'qty': 10}]
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        self.batch_aml.refresh_from_db()
        stock_after_first = self.batch_aml.quantity

        # 2. Second dispensation attempt must be rejected
        res2 = self.client.post('/api/pharmacy/dispense/', {
            'prescription_id': rx.id,
            'items': [{'item_id': it.id, 'batch_id': self.batch_aml.id, 'qty': 10}]
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been fully dispensed', str(res2.data['error']))

        self.batch_aml.refresh_from_db()
        self.assertEqual(self.batch_aml.quantity, stock_after_first, "Stock must NOT be decremented again!")


class PhaseC3RegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_a = District.objects.create(name='Bengaluru Urban', code='BLR-C3', state=self.state)
        self.district_b = District.objects.create(name='Mysuru District', code='MYS-C3', state=self.state)

        self.clinic_a = Facility.objects.create(
            facility_name='Clinic A', facility_code='NC-A-C3',
            facility_type='URBAN_PHC', state=self.state, district=self.district_a
        )
        self.clinic_b = Facility.objects.create(
            facility_name='Clinic B', facility_code='NC-B-C3',
            facility_type='URBAN_PHC', state=self.state, district=self.district_b
        )

        self.dho = User.objects.create_user(
            username='dho_c3', password='password', role='DISTRICT_OFFICER',
            assigned_district=self.district_a
        )
        self.doctor = User.objects.create_user(
            username='doc_c3', password='password', role='DOCTOR',
            assigned_facility=self.clinic_a
        )
        self.nurse = User.objects.create_user(
            username='nurse_c3', password='password', role='NURSE',
            assigned_facility=self.clinic_a
        )
        self.pharmacist = User.objects.create_user(
            username='pharm_c3', password='password', role='PHARMACIST',
            assigned_facility=self.clinic_a
        )

        self.patient = Patient.objects.create(
            patient_id='PAT-C3-001', name='C3 Test Patient', age=35, gender='FEMALE',
            mobile='9876543210', address='Koramangala Ward', registered_at_facility=self.clinic_a,
            district=self.district_a, vulnerability_information='Slum Resident BPL'
        )
        self.visit = Visit.objects.create(
            visit_id='VIS-C3-001', patient=self.patient, facility=self.clinic_a,
            opd_date=datetime.date.today(), current_queue='DOCTOR', status='WAITING_FOR_DOCTOR',
            chief_complaint='Severe fever and headache'
        )
        self.triage = TriageVitals.objects.create(
            visit=self.visit, patient=self.patient, nurse=self.nurse,
            blood_pressure_systolic=120, blood_pressure_diastolic=80, pulse_bpm=76, temperature_f=101.2
        )
        self.med_pcm = MedicineMaster.objects.create(
            generic_name='Paracetamol', strength='650 mg', dosage_form='Tablet', category='Analgesic'
        )
        self.batch_pcm = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=self.med_pcm, batch_number='BAT-C3-PCM',
            expiry_date=datetime.date.today() + datetime.timedelta(days=180), quantity=500
        )

    def test_fnd16_referral_urgency_choices(self):
        """FND-16: Referral urgency choices must accept ROUTINE, URGENT, EMERGENCY, and reject invalid choices (e.g. HIGH)."""
        self.client.force_authenticate(user=self.doctor)

        # 1. Valid urgency 'URGENT' must succeed
        res_urgent = self.client.post('/api/referrals/', {
            'patient': self.patient.id,
            'visit': self.visit.id,
            'source_facility': self.clinic_a.id,
            'destination_facility': self.clinic_a.id,
            'reason': 'Specialist evaluation',
            'urgency': 'URGENT'
        }, format='json')
        self.assertEqual(res_urgent.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_urgent.data['urgency'], 'URGENT')

        # 2. Valid urgency 'ROUTINE' and 'EMERGENCY' must succeed
        res_routine = self.client.post('/api/referrals/', {
            'patient': self.patient.id,
            'visit': self.visit.id,
            'source_facility': self.clinic_a.id,
            'destination_facility': self.clinic_a.id,
            'reason': 'Routine review',
            'urgency': 'ROUTINE'
        }, format='json')
        self.assertEqual(res_routine.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_routine.data['urgency'], 'ROUTINE')

        # 3. Invalid urgency 'HIGH' must be rejected with HTTP 400
        res_high = self.client.post('/api/referrals/', {
            'patient': self.patient.id,
            'visit': self.visit.id,
            'source_facility': self.clinic_a.id,
            'destination_facility': self.clinic_a.id,
            'reason': 'High priority referral',
            'urgency': 'HIGH'
        }, format='json')
        self.assertEqual(res_high.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('urgency', res_high.data)

    def test_fnd13_consultation_dynamic_fields(self):
        """FND-13: Consultation creation must persist dynamic, patient-specific clinical data without fabricated defaults."""
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/consultations/', {
            'visit': self.visit.id,
            'patient': self.patient.id,
            'facility': self.clinic_a.id,
            'chief_complaint': 'Acute fever for 2 days',
            'clinical_history': 'No previous drug allergies. Non-diabetic.',
            'clinical_assessment': 'Febrile, alert. Pharyngeal congestion noted.',
            'diagnosis_code': 'J06.9',
            'diagnosis_name': 'Acute Upper Respiratory Infection',
            'clinical_notes': 'Advised rest, oral hydration, and review if fever persists > 48h.',
            'prescription_items': [{
                'medicine_id': self.med_pcm.id,
                'medicine_name': 'Paracetamol 650 mg Tablet',
                'dosage': '1-1-1 After Food',
                'quantity': 10
            }]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        consult = Consultation.objects.get(visit=self.visit)
        self.assertEqual(consult.diagnosis_name, 'Acute Upper Respiratory Infection')
        self.assertEqual(consult.clinical_history, 'No previous drug allergies. Non-diabetic.')
        self.assertEqual(consult.prescription.items.count(), 1)

    def test_fnd17_followup_status_patch(self):
        """FND-17: FollowUp status can be updated to COMPLETED via PATCH /api/followups/{id}/."""
        fu = FollowUp.objects.create(
            patient=self.patient, facility=self.clinic_a, visit=self.visit,
            category='ROUTINE', due_date=datetime.date.today(), status='PENDING',
            notes='Check recovery from viral fever.'
        )
        # 1. Unauthorized role (PHARMACIST) must receive 403
        self.client.force_authenticate(user=self.pharmacist)
        res_pharm = self.client.patch(f'/api/followups/{fu.id}/', {'status': 'COMPLETED'}, format='json')
        self.assertEqual(res_pharm.status_code, status.HTTP_403_FORBIDDEN)

        # 2. DHO (read-only oversight) must receive 403
        self.client.force_authenticate(user=self.dho)
        res_dho = self.client.patch(f'/api/followups/{fu.id}/', {'status': 'COMPLETED'}, format='json')
        self.assertEqual(res_dho.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Authorized role (DOCTOR) succeeds
        self.client.force_authenticate(user=self.doctor)
        res = self.client.patch(f'/api/followups/{fu.id}/', {'status': 'COMPLETED'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        fu.refresh_from_db()
        self.assertEqual(fu.status, 'COMPLETED')

    def test_fnd19_dho_infrastructure_access(self):
        """FND-19: DHO can access facility infrastructure data within their authorized district."""
        from apps.facilities.models import FacilityOxygenSupply
        FacilityOxygenSupply.objects.create(
            facility=self.clinic_a, oxygen_source='CYLINDERS', total_cylinders=6,
            active_cylinders=4, status='ADEQUATE'
        )
        self.client.force_authenticate(user=self.dho)
        res = self.client.get('/api/facilities-infra/oxygen-supplies/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['facility'], self.clinic_a.id)

    def test_fnd20_patient_vulnerability_categories(self):
        """FND-20: Patient registration accepts and persists specific vulnerability categories."""
        self.client.force_authenticate(user=self.nurse)
        categories = [
            'General Population',
            'Slum Resident / Low Income Group',
            'Urban Slum Resident BPL',
            'Senior Citizen / Diabetic',
            'Senior Citizen / Cardiac History',
            'Slum Household BPL'
        ]
        for idx, cat in enumerate(categories):
            res = self.client.post('/api/patients/', {
                'name': f'Vulnerable Citizen {idx}',
                'age': 40 + idx,
                'gender': 'MALE',
                'mobile': f'988877766{idx}',
                'address': f'Ward Camp Site {idx}',
                'vulnerability_information': cat,
                'registered_at_facility': self.clinic_a.id
            }, format='json')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertEqual(res.data['vulnerability_information'], cat)

    def test_fnd15_vendors_and_purchase_orders_access(self):
        """FND-15: Vendors and Purchase Orders endpoints return authoritative data scoped to facility."""
        vendor = Vendor.objects.create(
            vendor_name='Test Vendor KSDLWC', contact_person='Shri R. Anjanappa',
            phone='+91-80-22221111', facility=self.clinic_a, created_by=self.pharmacist
        )
        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-001', vendor=vendor, facility=self.clinic_a,
            status='RECEIVED', total_amount=1500.00, created_by=self.pharmacist
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po, medicine=self.med_pcm, ordered_quantity=1000,
            received_quantity=1000, unit_price=1.50, total_price=1500.00
        )
        self.client.force_authenticate(user=self.pharmacist)
        res_v = self.client.get('/api/pharmacy/vendors/')
        self.assertEqual(res_v.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_v.data.get('results', res_v.data)), 1)

        res_po = self.client.get('/api/pharmacy/purchase-orders/')
        self.assertEqual(res_po.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_po.data.get('results', res_po.data)), 1)



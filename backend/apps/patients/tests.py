import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.patients.models import Patient, PatientDocument
from apps.visits.models import Visit
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabTestMaster, LabOrder, LabSample, LabResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from apps.referrals.models import Referral, ReferralResponse, FollowUp

User = get_user_model()

class PatientLongitudinalEMRTests(APITestCase):
    def setUp(self):
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.zone = Zone.objects.create(name='South Zone', code='SZ', district=self.district)
        self.ward = Ward.objects.create(name='Ward 100', ward_number=100, zone=self.zone)

        self.facility_1 = Facility.objects.create(
            facility_code='NC-BLR-001',
            facility_name='Namma Clinic Jayanagar',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district,
            zone=self.zone,
            ward=self.ward
        )
        self.facility_2 = Facility.objects.create(
            facility_code='HOSP-BLR-001',
            facility_name='Victoria Hospital Super Specialty',
            facility_type=FacilityTypeChoices.REFERRAL_HOSPITAL,
            state=self.state,
            district=self.district,
            zone=self.zone,
            ward=self.ward
        )

        # Users
        self.doctor = User.objects.create_user(
            username='doctor_emr',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_1,
            full_name='Dr. Ramesh Rao'
        )
        self.nurse = User.objects.create_user(
            username='nurse_emr',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility_1,
            full_name='Nurse Anitha'
        )
        self.lab_tech = User.objects.create_user(
            username='labtech_emr',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility_1,
            full_name='Tech Prakash'
        )
        self.pharmacist = User.objects.create_user(
            username='pharma_emr',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility_1,
            full_name='Pharma Sunil'
        )
        self.district_officer = User.objects.create_user(
            username='do_emr',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            full_name='Dr. Suma DO'
        )
        self.unauthorized_doctor = User.objects.create_user(
            username='other_doctor',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_2,
            full_name='Dr. Victoria External'
        )

        # Patient Registration
        self.patient = Patient.objects.create(
            patient_id='NC-KA-2026-9999',
            name='Rajesh Kumar',
            age=48,
            gender='MALE',
            mobile='9876543210',
            address='12th Cross, Jayanagar, Bengaluru',
            ward=self.ward,
            district=self.district,
            registered_at_facility=self.facility_1,
            ABHA_ID_DEMO='ABHA-9999-KARNATAKA',
            vulnerability_information='BPL Card Holder'
        )

    def test_complete_longitudinal_emr_lifecycle(self):
        """
        Verify that a complete end-to-end patient clinical workflow produces
        all longitudinal EMR events with correct timestamps and complete structured data.
        """
        now = timezone.now()
        t1_arrival = now - datetime.timedelta(hours=4)
        t2_triage = now - datetime.timedelta(hours=3, minutes=45)
        t3_consult = now - datetime.timedelta(hours=3, minutes=30)
        t4_lab_order = now - datetime.timedelta(hours=3, minutes=20)
        t5_lab_sample = now - datetime.timedelta(hours=3, minutes=10)
        t6_lab_verified = now - datetime.timedelta(hours=2, minutes=30)
        t7_prescription = now - datetime.timedelta(hours=2, minutes=15)
        t8_dispensing = now - datetime.timedelta(hours=2)
        t9_referral = now - datetime.timedelta(hours=1, minutes=45)
        t10_ref_resp = now - datetime.timedelta(hours=1, minutes=30)
        t11_completed = now - datetime.timedelta(hours=1)

        # 1. Visit Check-in
        visit = Visit.objects.create(
            visit_id='VISIT-2026-0001',
            patient=self.patient,
            facility=self.facility_1,
            visit_date=t1_arrival,
            arrival_time=t1_arrival,
            visit_type='GENERAL_OPD',
            priority='HIGH',
            current_queue='COMPLETED',
            status='COMPLETED',
            chief_complaint='Severe fever, body ache and polyuria',
            assigned_doctor=self.doctor,
            completed_time=t11_completed
        )

        # 2. Nurse Triage
        triage = TriageVitals.objects.create(
            visit=visit,
            patient=self.patient,
            nurse=self.nurse,
            blood_pressure_systolic=150,
            blood_pressure_diastolic=95,
            pulse_bpm=88,
            temperature_f=101.5,
            spo2_percent=97,
            respiratory_rate=20,
            height_cm=170,
            weight_kg=78,
            blood_glucose_mgdl=220,
            nurse_notes='Patient presented with high fever and elevated sugar readings.'
        )
        TriageVitals.objects.filter(pk=triage.pk).update(created_at=t2_triage)

        # 3. Doctor Consultation
        consultation = Consultation.objects.create(
            visit=visit,
            patient=self.patient,
            doctor=self.doctor,
            facility=self.facility_1,
            chief_complaint='Fever with polyuria',
            clinical_history='Known diabetic, irregular medication',
            clinical_assessment='Acute febrile illness in uncontrolled Type 2 Diabetes',
            diagnosis_code='E11.65',
            diagnosis_name='Type 2 Diabetes Mellitus with Hyperglycemia',
            treatment_plan='Initiate antipyretics, adjust metformin, obtain stat FBS and CBC',
            clinical_notes='Ordered urgent blood investigations before finalizing discharge.',
            follow_up_date=datetime.date.today() + datetime.timedelta(days=7)
        )
        Consultation.objects.filter(pk=consultation.pk).update(created_at=t3_consult)

        # 4. Lab Investigation Workflow
        test_master = LabTestMaster.objects.create(
            code='GLUC-RBS',
            name='Random Blood Sugar (RBS)',
            category='Biochemistry',
            reference_range='70 - 140 mg/dL',
            unit='mg/dL'
        )
        lab_order = LabOrder.objects.create(
            visit=visit,
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            facility=self.facility_1,
            test_master=test_master,
            status='VERIFIED'
        )
        LabOrder.objects.filter(pk=lab_order.pk).update(order_date=t4_lab_order)

        lab_sample = LabSample.objects.create(
            lab_order=lab_order,
            sample_type='Venous Blood',
            sample_code='SMP-9999-01',
            collected_by=self.lab_tech
        )
        LabSample.objects.filter(pk=lab_sample.pk).update(collected_at=t5_lab_sample)

        lab_result = LabResult.objects.create(
            lab_order=lab_order,
            result_value='245',
            unit='mg/dL',
            reference_range='70 - 140 mg/dL',
            interpretation_flag='HIGH',
            verified_by=self.doctor,
            notes='Significantly elevated glucose level. Verified with duplicate run.'
        )
        LabResult.objects.filter(pk=lab_result.pk).update(verified_at=t6_lab_verified)

        # 5. Prescription
        prescription = Prescription.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            facility=self.facility_1,
            status='DISPENSED',
            notes='Take medicines after food with plenty of water.'
        )
        PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name='Paracetamol 650mg',
            dosage='1-0-1 After Food',
            frequency='Twice Daily',
            duration_days=3,
            quantity=6,
            status='DISPENSED'
        )
        PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name='Metformin 500mg',
            dosage='1-0-1 After Food',
            frequency='Twice Daily',
            duration_days=14,
            quantity=28,
            status='DISPENSED'
        )

        # 6. Pharmacy Dispensing
        med_master = MedicineMaster.objects.create(
            generic_name='Paracetamol',
            brand_name='Dolo 650',
            strength='650 mg',
            dosage_form='Tablet',
            unit='Tablets'
        )
        batch = MedicineBatch.objects.create(
            facility=self.facility_1,
            medicine=med_master,
            batch_number='BATCH-2026-X1',
            expiry_date=datetime.date.today() + datetime.timedelta(days=365),
            quantity=1000
        )
        dispense_tx = InventoryTransaction.objects.create(
            facility=self.facility_1,
            medicine=med_master,
            batch=batch,
            transaction_type='DISPENSED',
            quantity=6,
            reference_id=f"PRESCR-{prescription.id}",
            created_by=self.pharmacist,
            notes=f"Prescription #{prescription.id} for {self.patient.name}"
        )
        InventoryTransaction.objects.filter(pk=dispense_tx.pk).update(created_at=t8_dispensing)

        # 7. Clinical Referral & Response
        referral = Referral.objects.create(
            referral_id='REF-2026-9999',
            patient=self.patient,
            source_facility=self.facility_1,
            destination_facility=self.facility_2,
            referring_doctor=self.doctor,
            reason='Endocrine consultation for brittle glycemic control',
            clinical_summary='Patient with severe post-prandial hyperglycemia requiring insulin titration.',
            required_service='Endocrinology & Diabetology',
            urgency='URGENT',
            status='COMPLETED'
        )
        Referral.objects.filter(pk=referral.pk).update(referral_date=t9_referral)

        ref_response = ReferralResponse.objects.create(
            referral=referral,
            hospital_doctor=self.unauthorized_doctor,
            specialist_findings='HbA1c 9.8%. Recommended basal insulin addition.',
            treatment_summary='Glargine 10 units initiated at bedtime.',
            return_advice='Monitor fasting glucose daily and return to Namma Clinic in 1 week.'
        )
        ReferralResponse.objects.filter(pk=ref_response.pk).update(responded_at=t10_ref_resp)

        # 8. Follow-up
        follow_up = FollowUp.objects.create(
            patient=self.patient,
            facility=self.facility_1,
            category='NCD_DIABETES',
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            status='PENDING',
            notes='Check fasting and post-prandial glucose levels.'
        )

        # 9. Uploaded Medical Document
        test_file = SimpleUploadedFile("discharge_summary.pdf", b"PDF file content test", content_type="application/pdf")
        doc = PatientDocument.objects.create(
            patient=self.patient,
            facility=self.facility_1,
            title='Victoria Hospital Discharge Summary',
            document_type='DISCHARGE_SUMMARY',
            file=test_file,
            file_name='discharge_summary.pdf',
            file_size=2048,
            mime_type='application/pdf',
            uploaded_by=self.doctor,
            description='Endocrine evaluation summary report'
        )

        # Authenticate Doctor & Request Timeline API
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(f"/api/patients/{self.patient.id}/timeline/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('timeline', data)
        timeline = data['timeline']

        # Extract all event types present
        event_types = [ev['type'] for ev in timeline]

        # Verify Minimum Event Types Required:
        self.assertIn('REGISTRATION', event_types)
        self.assertIn('VISIT', event_types)
        self.assertIn('TRIAGE', event_types)
        self.assertIn('CONSULTATION', event_types)
        self.assertIn('RE_CONSULTATION', event_types)
        self.assertIn('LAB_ORDER', event_types)
        self.assertIn('SAMPLE_COLLECTION', event_types)
        self.assertIn('LAB_RESULT', event_types)
        self.assertIn('PRESCRIPTION', event_types)
        self.assertIn('DISPENSING', event_types)
        self.assertIn('REFERRAL', event_types)
        self.assertIn('REFERRAL_RESPONSE', event_types)
        self.assertIn('FOLLOWUP', event_types)
        self.assertIn('DOCUMENT', event_types)
        self.assertIn('VISIT_COMPLETED', event_types)

        # Verify Registration Date & Time:
        reg_ev = next(ev for ev in timeline if ev['type'] == 'REGISTRATION')
        self.assertFalse(reg_ev['has_time'])
        self.assertEqual(reg_ev['time_display'], 'Registration time not recorded')
        self.assertEqual(reg_ev['date'], self.patient.registration_date.strftime('%Y-%m-%d'))
        self.assertNotIn('Invalid Date', reg_ev['details'])

        # Verify Reverse Chronological Order by ISO Timestamp:
        timestamps = [ev['timestamp'] for ev in timeline]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

        # Verify Triage contains full real vitals:
        tr_ev = next(ev for ev in timeline if ev['type'] == 'TRIAGE')
        self.assertEqual(tr_ev['structured_data']['systolic'], 150)
        self.assertEqual(tr_ev['structured_data']['diastolic'], 95)
        self.assertEqual(tr_ev['structured_data']['blood_glucose_mgdl'], 220)
        self.assertIn('Elevated Blood Pressure', tr_ev['structured_data']['active_flags'])

        # Verify Re-consultation distinguished from initial consultation:
        reconsult_ev = next(ev for ev in timeline if ev['type'] == 'RE_CONSULTATION')
        self.assertIn('Consultation updated after lab result', reconsult_ev['details'])
        self.assertIn('E11.65', reconsult_ev['structured_data']['diagnosis'])

        # Verify Dispensing references prescription and actual batch:
        disp_ev = next(ev for ev in timeline if ev['type'] == 'DISPENSING')
        self.assertEqual(disp_ev['structured_data']['batch_number'], 'BATCH-2026-X1')
        self.assertEqual(disp_ev['structured_data']['quantity_dispensed'], 6)
        self.assertEqual(disp_ev['structured_data']['dispensed_by'], 'Pharma Sunil')

    def test_structured_tabs_consistency(self):
        """
        Verify that /api/patients/<id>/records/ returns structured records
        that correspond directly to timeline entities with zero discrepancies.
        """
        now = timezone.now()
        visit = Visit.objects.create(
            visit_id='VISIT-TABS-01',
            patient=self.patient,
            facility=self.facility_1,
            visit_date=now,
            arrival_time=now,
            status='COMPLETED',
            assigned_doctor=self.doctor,
            completed_time=now + datetime.timedelta(minutes=45)
        )
        consultation = Consultation.objects.create(
            visit=visit,
            patient=self.patient,
            doctor=self.doctor,
            facility=self.facility_1,
            diagnosis_code='I10',
            diagnosis_name='Essential Hypertension',
            treatment_plan='Amlodipine 5mg OD'
        )
        test_master = LabTestMaster.objects.create(code='LIPID', name='Lipid Profile')
        lab_order = LabOrder.objects.create(
            visit=visit,
            consultation=consultation,
            patient=self.patient,
            facility=self.facility_1,
            test_master=test_master,
            status='VERIFIED'
        )
        LabResult.objects.create(
            lab_order=lab_order,
            result_value='210',
            unit='mg/dL',
            reference_range='< 200 mg/dL',
            interpretation_flag='HIGH',
            verified_by=self.doctor
        )
        prescription = Prescription.objects.create(
            consultation=consultation,
            patient=self.patient,
            doctor=self.doctor,
            facility=self.facility_1,
            status='ACTIVE'
        )
        PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name='Amlodipine 5mg',
            dosage='1-0-0 After Food',
            frequency='Once Daily',
            duration_days=30,
            quantity=30
        )

        self.client.force_authenticate(user=self.doctor)
        records_res = self.client.get(f"/api/patients/{self.patient.id}/records/")
        timeline_res = self.client.get(f"/api/patients/{self.patient.id}/timeline/")

        self.assertEqual(records_res.status_code, status.HTTP_200_OK)
        self.assertEqual(timeline_res.status_code, status.HTTP_200_OK)

        rec = records_res.data
        tl = timeline_res.data['timeline']

        # 1. Visits tab consistency:
        rec_visit_ids = [v['visit_id'] for v in rec['visits']]
        tl_visit_ids = [ev['structured_data'].get('visit_id') for ev in tl if ev['type'] == 'VISIT']
        self.assertIn('VISIT-TABS-01', rec_visit_ids)
        self.assertIn('VISIT-TABS-01', tl_visit_ids)

        # 2. Consultation consistency:
        rec_diag = [c['diagnosis_code'] for c in rec['medical_records']]
        tl_diag = [ev['structured_data'].get('diagnosis_code') for ev in tl if ev['type'] == 'CONSULTATION']
        self.assertIn('I10', rec_diag)
        self.assertIn('I10', tl_diag)

        # 3. Lab consistency:
        rec_lab = [l['test_code'] for l in rec['lab_reports']]
        tl_lab = [ev['structured_data'].get('test_code') for ev in tl if ev['type'] == 'LAB_ORDER']
        self.assertIn('LIPID', rec_lab)
        self.assertIn('LIPID', tl_lab)

        # 4. Prescription consistency:
        rec_rx = [p['id'] for p in rec['prescriptions']]
        tl_rx = [ev['structured_data'].get('prescription_id') for ev in tl if ev['type'] == 'PRESCRIPTION']
        self.assertIn(prescription.id, rec_rx)
        self.assertIn(prescription.id, tl_rx)

    def test_facility_security_and_district_officer_scoping(self):
        """
        Verify that unauthorized cross-facility access returns 403 Forbidden,
        while District Officers and referral-linked providers can access records.
        """
        # Unauthorized clinician at Facility 2 cannot view Facility 1 patient records without a visit/referral
        self.client.force_authenticate(user=self.unauthorized_doctor)
        res_timeline = self.client.get(f"/api/patients/{self.patient.id}/timeline/")
        self.assertEqual(res_timeline.status_code, status.HTTP_403_FORBIDDEN)

        res_records = self.client.get(f"/api/patients/{self.patient.id}/records/")
        self.assertEqual(res_records.status_code, status.HTTP_403_FORBIDDEN)

        # District Officer can access regardless of assigned facility
        self.client.force_authenticate(user=self.district_officer)
        do_timeline = self.client.get(f"/api/patients/{self.patient.id}/timeline/")
        self.assertEqual(do_timeline.status_code, status.HTTP_200_OK)

        do_records = self.client.get(f"/api/patients/{self.patient.id}/records/")
        self.assertEqual(do_records.status_code, status.HTTP_200_OK)

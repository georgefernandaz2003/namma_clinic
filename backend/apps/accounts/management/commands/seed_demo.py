from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
import datetime

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import (
    Facility, FacilityRelationship, FacilityOxygenSupply,
    FacilityConsumableInventory, FacilityMaintenanceTicket,
    FacilityBedCapacity, FacilityBedAllocation
)
from apps.patients.models import Patient, Household
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabTestMaster, LabOrder, LabSample, LabResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.telemedicine.models import Teleconsultation
from apps.outreach.models import OutreachActivity
from apps.wellness.models import WellnessSession
from apps.ars.models import ARSMember, ARSMeeting, ARSActionItem
from apps.quality.models import QualityChecklist, BiomedicalWasteLog
from apps.alerts.models import Alert
from apps.integrations.models import IntegrationConfiguration
from apps.compliance.models import ComplianceItem
from apps.audit.models import AuditLog

User = get_user_model()

class Command(BaseCommand):
    help = "Seed local SQLite database with realistic Namma Clinic digital healthcare network demo dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Flushing and re-seeding Namma Clinic demo dataset..."))

        # Clear existing data
        AuditLog.objects.all().delete()
        ComplianceItem.objects.all().delete()
        IntegrationConfiguration.objects.all().delete()
        Alert.objects.all().delete()
        BiomedicalWasteLog.objects.all().delete()
        QualityChecklist.objects.all().delete()
        ARSActionItem.objects.all().delete()
        ARSMeeting.objects.all().delete()
        ARSMember.objects.all().delete()
        WellnessSession.objects.all().delete()
        OutreachActivity.objects.all().delete()
        Teleconsultation.objects.all().delete()
        DiseaseCase.objects.all().delete()
        NCDRecord.objects.all().delete()
        FollowUp.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()
        InventoryTransaction.objects.all().delete()
        MedicineBatch.objects.all().delete()
        MedicineMaster.objects.all().delete()
        LabResult.objects.all().delete()
        LabSample.objects.all().delete()
        LabOrder.objects.all().delete()
        LabTestMaster.objects.all().delete()
        PrescriptionItem.objects.all().delete()
        Prescription.objects.all().delete()
        Consultation.objects.all().delete()
        TriageVitals.objects.all().delete()
        Token.objects.all().delete()
        Visit.objects.all().delete()
        Patient.objects.all().delete()
        Household.objects.all().delete()
        FacilityRelationship.objects.all().delete()
        User.objects.all().delete()
        Facility.objects.all().delete()
        Ward.objects.all().delete()
        Zone.objects.all().delete()
        District.objects.all().delete()
        State.objects.all().delete()

        # 1. State & Districts
        karnataka = State.objects.create(name='Karnataka', code='KA')
        dist_central = District.objects.create(state=karnataka, name='BBMP Central (Bengaluru Urban)', code='KA-BU')
        dist_rural = District.objects.create(state=karnataka, name='Bengaluru Rural', code='KA-BR')

        # Zones & Wards
        zone_east = Zone.objects.create(district=dist_central, name='East Zone', code='Z-EAST')
        zone_south = Zone.objects.create(district=dist_central, name='South Zone', code='Z-SOUTH')
        zone_hoskote = Zone.objects.create(district=dist_rural, name='Hoskote Zone', code='Z-HOS')

        ward12 = Ward.objects.create(zone=zone_east, ward_number=12, name='Indiranagar Ward', population=22000, slum_population=6500)
        ward14 = Ward.objects.create(zone=zone_east, ward_number=14, name='Ulsoor Ward', population=19500, slum_population=5200)
        ward45 = Ward.objects.create(zone=zone_south, ward_number=45, name='Jayanagar Ward', population=24000, slum_population=4800)
        ward52 = Ward.objects.create(zone=zone_south, ward_number=52, name='JP Nagar Ward', population=21000, slum_population=4100)
        ward_rural = Ward.objects.create(zone=zone_hoskote, ward_number=1, name='Varthur Rural Ward', population=18000, slum_population=7200)

        # 2. Facilities
        # Main Hospital A
        hosp_a = Facility.objects.create(
            facility_code='HOSP-A-01', facility_name='Victoria Hospital & Medical Center', facility_type='MAIN_HOSPITAL',
            state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP Central', urban_rural='URBAN',
            latitude=12.9634, longitude=77.5750, population_served=500000, emergency_available=True, bed_capacity=750,
            services='Cardiology, Nephrology, General Surgery, Emergency, ICU, Teleconsultation Hub'
        )

        # Main Hospital B
        hosp_b = Facility.objects.create(
            facility_code='HOSP-B-01', facility_name='KC General Secondary Hospital', facility_type='MAIN_HOSPITAL',
            state=karnataka, district=dist_central, zone=zone_south, ward=ward45, city_or_ulb='BBMP South', urban_rural='URBAN',
            latitude=12.9915, longitude=77.5712, population_served=350000, emergency_available=True, bed_capacity=350,
            services='General Medicine, Cardiology Specialist, Pediatrics, Obstetrics, Diagnostics'
        )

        # Diagnostic Center D
        diag_d = Facility.objects.create(
            facility_code='DIAG-D-01', facility_name='BBMP Central Diagnostic Center', facility_type='DIAGNOSTIC_CENTER',
            state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP Central', urban_rural='URBAN',
            latitude=12.9780, longitude=77.5840, population_served=200000, lab_available=True,
            services='Advanced Biochemistry, Pathology, X-Ray, Ultrasound, CT Scan'
        )

        # Namma Clinics under Hosp A
        nc_a1 = Facility.objects.create(
            facility_code='NC-A1-01', facility_name='Indiranagar Namma Clinic (UHWC)', facility_type='NAMMA_CLINIC',
            parent_facility=hosp_a, state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP East',
            latitude=12.9719, longitude=77.6412, population_served=18500, vulnerable_population=6500
        )
        nc_a2 = Facility.objects.create(
            facility_code='NC-A2-02', facility_name='Ulsoor Namma Clinic (UHWC)', facility_type='NAMMA_CLINIC',
            parent_facility=hosp_a, state=karnataka, district=dist_central, zone=zone_east, ward=ward14, city_or_ulb='BBMP East',
            latitude=12.9816, longitude=77.6200, population_served=17000, vulnerable_population=5200
        )

        # Urban & Rural Clinics under Hosp A
        uc_a3 = Facility.objects.create(
            facility_code='UC-A3-03', facility_name='Domlur Urban Primary Clinic', facility_type='URBAN_CLINIC',
            parent_facility=hosp_a, state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP East',
            latitude=12.9600, longitude=77.6380, population_served=21000
        )
        rc_a4 = Facility.objects.create(
            facility_code='RC-A4-04', facility_name='Varthur Rural Primary Clinic A4', facility_type='RURAL_CLINIC',
            parent_facility=hosp_a, state=karnataka, district=dist_central, zone=zone_east, ward=ward_rural, city_or_ulb='BBMP East Peripheral', urban_rural='RURAL',
            latitude=12.9406, longitude=77.7470, population_served=19000, vulnerable_population=7200
        )

        # Satellites under RC A4
        vc_a4_1 = Facility.objects.create(
            facility_code='VC-A4-1', facility_name='Gunjur Village Satellite Clinic', facility_type='VILLAGE_CLINIC',
            parent_facility=rc_a4, state=karnataka, district=dist_central, zone=zone_east, ward=ward_rural, urban_rural='RURAL',
            latitude=12.9300, longitude=77.7550, population_served=8000
        )
        vc_a4_2 = Facility.objects.create(
            facility_code='VC-A4-2', facility_name='Balagere Village Health Post', facility_type='VILLAGE_CLINIC',
            parent_facility=rc_a4, state=karnataka, district=dist_central, zone=zone_east, ward=ward_rural, urban_rural='RURAL',
            latitude=12.9380, longitude=77.7610, population_served=6500
        )

        # Clinics under Hosp B
        nc_b1 = Facility.objects.create(
            facility_code='NC-B1-01', facility_name='Jayanagar Namma Clinic (UHWC)', facility_type='NAMMA_CLINIC',
            parent_facility=hosp_b, state=karnataka, district=dist_central, zone=zone_south, ward=ward45, city_or_ulb='BBMP South',
            latitude=12.9250, longitude=77.5938, population_served=20000, vulnerable_population=4800
        )
        rc_b2 = Facility.objects.create(
            facility_code='RC-B2-02', facility_name='Bannerghatta Rural Clinic', facility_type='RURAL_CLINIC',
            parent_facility=hosp_b, state=karnataka, district=dist_central, zone=zone_south, ward=ward52, urban_rural='RURAL',
            latitude=12.8000, longitude=77.5800, population_served=16000
        )

        # District 2 Facility
        hosp_c = Facility.objects.create(
            facility_code='HOSP-C-01', facility_name='Hoskote District General Hospital', facility_type='MAIN_HOSPITAL',
            state=karnataka, district=dist_rural, zone=zone_hoskote, city_or_ulb='Hoskote Town', urban_rural='RURAL',
            latitude=13.0700, longitude=77.7900, population_served=250000, emergency_available=True, bed_capacity=200
        )
        nc_c1 = Facility.objects.create(
            facility_code='NC-C1-01', facility_name='Hoskote Town Namma Clinic', facility_type='NAMMA_CLINIC',
            parent_facility=hosp_c, state=karnataka, district=dist_rural, zone=zone_hoskote, city_or_ulb='Hoskote Town',
            latitude=13.0720, longitude=77.7950, population_served=18000
        )

        # 3. Facility Relationships (Multi-Destination Referral Graph)
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=nc_a1, relationship_type='REFERRAL', service='Routine Primary Care', priority='PRIMARY', distance_km=4.2
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=hosp_b, relationship_type='SPECIALIST', service='Cardiology & Internal Medicine', priority='SECONDARY', distance_km=8.5
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=hosp_a, relationship_type='EMERGENCY', service='Trauma & Intensive Care', priority='EMERGENCY', distance_km=12.0
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=diag_d, relationship_type='DIAGNOSTIC', service='Advanced Biochemistry & Ultrasound', priority='PRIMARY', distance_km=6.0
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=hosp_a, relationship_type='TELECONSULTATION', service='Specialist Teleconsultation Hub', priority='PRIMARY', distance_km=5.0
        )

        # 4. Users & Roles (Strictly 6 Active Roles)
        u_dist = User.objects.create_user('district', 'district@nammaclinic.gov.in', 'district123', full_name='Dr. Sunita Rao (District Health Officer)', role='DISTRICT_OFFICER', assigned_district=dist_central)
        u_hosp = User.objects.create_user('hospital', 'hospital@nammaclinic.gov.in', 'hospital123', full_name='Dr. K. V. Sharma (Chief Medical Supt)', role='HOSPITAL_ADMIN', assigned_facility=hosp_b)
        u_doc = User.objects.create_user('doctor', 'doctor@nammaclinic.gov.in', 'doctor123', full_name='Dr. Rajesh Kumar (Medical Officer)', role='DOCTOR', assigned_facility=rc_a4)
        u_nurse = User.objects.create_user('nurse', 'nurse@nammaclinic.gov.in', 'nurse123', full_name='Sister Priya Nair', role='NURSE', assigned_facility=rc_a4)
        u_lab = User.objects.create_user('lab', 'lab@nammaclinic.gov.in', 'lab123', full_name='Mr. Suresh Gowda', role='LAB_TECHNICIAN', assigned_facility=rc_a4)
        u_pharm = User.objects.create_user('pharmacy', 'pharmacy@nammaclinic.gov.in', 'pharmacy123', full_name='Mrs. Lakshmi Devi', role='PHARMACIST', assigned_facility=rc_a4)

        # 5. Approved 14 Essential Diagnostic Tests for Namma Clinics / UHWC
        lt_hba1c = LabTestMaster.objects.create(code='L-HBA1C', name='HbA1c Glycated Hemoglobin', category='Diabetes', reference_range='4.0 - 5.6 %', unit='%')
        lt_fbg = LabTestMaster.objects.create(code='L-FBG', name='Fasting Blood Glucose (FBG)', category='Diabetes', reference_range='70 - 100 mg/dL', unit='mg/dL')
        lt_rbg = LabTestMaster.objects.create(code='L-RBG', name='Random Blood Glucose (Rapid Strip)', category='Diabetes', reference_range='70 - 140 mg/dL', unit='mg/dL')
        lt_hb = LabTestMaster.objects.create(code='L-HB', name='Hemoglobin (Hb Estimation)', category='Hematology', reference_range='12.0 - 15.5 g/dL', unit='g/dL')
        lt_lipid = LabTestMaster.objects.create(code='L-LIPID', name='Lipid Profile (Cholesterol & Triglycerides)', category='Biochemistry', reference_range='Desirable < 200 mg/dL', unit='mg/dL')
        lt_dengue = LabTestMaster.objects.create(code='L-DENGUE', name='Dengue NS1 Antigen Rapid Test Card', category='Serology', reference_range='Negative', unit='Result')
        lt_malaria = LabTestMaster.objects.create(code='L-MALARIA', name='Malaria Antigen (Pf/Pv) Rapid Test', category='Serology', reference_range='Negative', unit='Result')
        lt_u_prot = LabTestMaster.objects.create(code='L-URINE-PROT', name='Urine Albumin / Protein Test', category='Urinalysis', reference_range='Nil / Negative', unit='Grade')
        lt_u_sug = LabTestMaster.objects.create(code='L-URINE-SUG', name='Urine Sugar Test', category='Urinalysis', reference_range='Nil / Negative', unit='Grade')
        lt_tb = LabTestMaster.objects.create(code='L-TB-SPUTUM', name='Sputum Smear for AFB (Tuberculosis)', category='Microbiology', reference_range='Negative for AFB', unit='Result')
        lt_hiv = LabTestMaster.objects.create(code='L-HIV-RAPID', name='HIV 1 & 2 Rapid Screening Card', category='Serology', reference_range='Non-Reactive', unit='Result')
        lt_hbsag = LabTestMaster.objects.create(code='L-HBSAG', name='Hepatitis B Surface Antigen (HBsAg)', category='Serology', reference_range='Non-Reactive', unit='Result')
        lt_upt = LabTestMaster.objects.create(code='L-PREG-RAPID', name='Urine Pregnancy Test (UPT Card)', category='Maternal RCH', reference_range='Negative', unit='Result')
        lt_lft = LabTestMaster.objects.create(code='L-LFT', name='Liver Function Test (Bilirubin & Transaminases)', category='Biochemistry', reference_range='Bilirubin < 1.2 mg/dL', unit='mg/dL')

        med_met = MedicineMaster.objects.create(generic_name='Metformin HCl', brand_name='Glycomet', strength='500 mg', dosage_form='Tablet', category='Anti-Diabetic', reorder_level=100)
        med_aml = MedicineMaster.objects.create(generic_name='Amlodipine Besylate', brand_name='Amlopres', strength='5 mg', dosage_form='Tablet', category='Anti-Hypertensive', reorder_level=100)
        med_pcm = MedicineMaster.objects.create(generic_name='Paracetamol', brand_name='Dolo', strength='650 mg', dosage_form='Tablet', category='Analgesic / Antipyretic', reorder_level=200)
        med_amx = MedicineMaster.objects.create(generic_name='Amoxicillin Trihydrate', brand_name='Mox', strength='500 mg', dosage_form='Capsule', category='Antibiotic', reorder_level=100)
        med_tel = MedicineMaster.objects.create(generic_name='Telmisartan', brand_name='Telma', strength='40 mg', dosage_form='Tablet', category='Anti-Hypertensive', reorder_level=80)

        today = datetime.date.today()

        # FEFO Batches for Rural Clinic A4
        b_met1 = MedicineBatch.objects.create(
            facility=rc_a4, medicine=med_met, batch_number='BATCH-MET-2026A', supplier='KSMSCL (E-Aushada)',
            expiry_date=today + datetime.timedelta(days=120), quantity=450, status='ACTIVE'
        )
        b_met2 = MedicineBatch.objects.create(
            facility=rc_a4, medicine=med_met, batch_number='BATCH-MET-2026B', supplier='KSMSCL (E-Aushada)',
            expiry_date=today + datetime.timedelta(days=360), quantity=800, status='ACTIVE'
        )
        b_aml = MedicineBatch.objects.create(
            facility=rc_a4, medicine=med_aml, batch_number='BATCH-AML-2026X', supplier='KSMSCL (E-Aushada)',
            expiry_date=today + datetime.timedelta(days=45), quantity=35, status='LOW_STOCK' # Low stock & Near expiry
        )
        b_pcm = MedicineBatch.objects.create(
            facility=rc_a4, medicine=med_pcm, batch_number='BATCH-PCM-2026P', supplier='KSMSCL (E-Aushada)',
            expiry_date=today + datetime.timedelta(days=200), quantity=1200, status='ACTIVE'
        )
        b_expired = MedicineBatch.objects.create(
            facility=rc_a4, medicine=med_amx, batch_number='BATCH-AMX-OLD', supplier='KSMSCL (E-Aushada)',
            expiry_date=today - datetime.timedelta(days=15), quantity=40, status='EXPIRED' # Demo Expired Batch
        )

        # 6. Primary Demo Patient: Ramesh Kumar
        p_ramesh = Patient.objects.create(
            patient_id='NC-20260901-001', name='Ramesh Kumar', date_of_birth=datetime.date(1974, 5, 12), age=52, gender='MALE',
            mobile='9876543210', address='House #45, Near Govt School, Varthur Slum Area', ward=ward_rural, district=dist_central,
            ABHA_ID_DEMO='91-8765-4321-0987', emergency_contact='9876543211 (Wife - Sunita)', vulnerability_information='Slum Household BPL',
            registered_at_facility=rc_a4
        )

        # Additional Demo Patients
        p_anita = Patient.objects.create(
            patient_id='NC-20260901-002', name='Anita Devi', date_of_birth=datetime.date(1996, 8, 20), age=30, gender='FEMALE',
            mobile='9845012345', address='Cross Road #3, Indiranagar Slum Colony', ward=ward12, district=dist_central,
            ABHA_ID_DEMO='91-1234-5678-9012', vulnerability_information='High Risk Pregnancy ANC', registered_at_facility=nc_a1
        )
        p_suresh = Patient.objects.create(
            patient_id='NC-20260901-003', name='Suresh Patil', date_of_birth=datetime.date(1961, 3, 15), age=65, gender='MALE',
            mobile='9900112233', address='Ward 14 Slum Line, Ulsoor', ward=ward14, district=dist_central,
            ABHA_ID_DEMO='91-9988-7766-5544', vulnerability_information='Senior Citizen / Diabetic', registered_at_facility=nc_a2
        )

        # Create 30 mock patients for analytics depth
        for i in range(4, 35):
            g = 'MALE' if i % 2 == 0 else 'FEMALE'
            Patient.objects.create(
                patient_id=f"NC-20260901-{i:03d}", name=f"Demo Citizen {i}", age=25 + (i * 2) % 40, gender=g,
                mobile=f"980000{i:04d}", address=f"Ward Slum Area Pocket {i % 5 + 1}", ward=ward_rural, district=dist_central,
                registered_at_facility=rc_a4
            )

        # 7. Visit, Token, Triage, Consultation, Lab, Pharmacy for Ramesh Kumar
        v_ramesh = Visit.objects.create(
            visit_id=f"VIS-{today.strftime('%Y%m%d')}-001", patient=p_ramesh, facility=rc_a4,
            opd_date=today, visit_type='GENERAL_OPD', priority='HIGH', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Dizziness, severe fatigue, and blurred vision for 5 days',
            assigned_doctor=u_doc, arrival_time=timezone.now() - datetime.timedelta(hours=2),
            completed_time=timezone.now() - datetime.timedelta(minutes=20)
        )
        t_ramesh = Token.objects.create(token_number=1, visit=v_ramesh, facility=rc_a4, date=today, priority='HIGH', status='COMPLETED')

        # Additional today & historical OPD visits for date-based queue testing
        yest = today - datetime.timedelta(days=1)
        prev = today - datetime.timedelta(days=2)

        # Historical Visits Yesterday (yest) for rc_a4 (Tokens #1, #2, #3)
        v_y1 = Visit.objects.create(
            visit_id=f"VIS-{yest.strftime('%Y%m%d')}-001", patient=p_suresh, facility=rc_a4,
            opd_date=yest, visit_type='GENERAL_OPD', priority='EMERGENCY', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Chest discomfort & palpitations', assigned_doctor=u_doc,
            arrival_time=timezone.make_aware(datetime.datetime.combine(yest, datetime.time(9, 15)))
        )
        Token.objects.create(token_number=1, visit=v_y1, facility=rc_a4, date=yest, priority='EMERGENCY', status='COMPLETED')

        v_y2 = Visit.objects.create(
            visit_id=f"VIS-{yest.strftime('%Y%m%d')}-002", patient=p_anita, facility=rc_a4,
            opd_date=yest, visit_type='MATERNAL_ANC', priority='NORMAL', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Routine 2nd Trimester ANC Checkup', assigned_doctor=u_doc,
            arrival_time=timezone.make_aware(datetime.datetime.combine(yest, datetime.time(9, 30)))
        )
        Token.objects.create(token_number=2, visit=v_y2, facility=rc_a4, date=yest, priority='NORMAL', status='COMPLETED')

        # Today's active queue visits for rc_a4 (Tokens #2, #3)
        v_t2 = Visit.objects.create(
            visit_id=f"VIS-{today.strftime('%Y%m%d')}-002", patient=p_suresh, facility=rc_a4,
            opd_date=today, visit_type='GENERAL_OPD', priority='EMERGENCY', current_queue='TRIAGE',
            status='WAITING_FOR_TRIAGE', chief_complaint='High fever & acute headache',
            arrival_time=timezone.now() - datetime.timedelta(minutes=35)
        )
        Token.objects.create(token_number=2, visit=v_t2, facility=rc_a4, date=today, priority='EMERGENCY', status='WAITING')

        v_t3 = Visit.objects.create(
            visit_id=f"VIS-{today.strftime('%Y%m%d')}-003", patient=p_anita, facility=rc_a4,
            opd_date=today, visit_type='MATERNAL_ANC', priority='NORMAL', current_queue='DOCTOR',
            status='WAITING_FOR_DOCTOR', chief_complaint='Follow-up BP check',
            arrival_time=timezone.now() - datetime.timedelta(minutes=15)
        )
        Token.objects.create(token_number=3, visit=v_t3, facility=rc_a4, date=today, priority='NORMAL', status='WAITING')

        TriageVitals.objects.create(
            visit=v_ramesh, patient=p_ramesh, nurse=u_nurse,
            blood_pressure_systolic=148, blood_pressure_diastolic=96, pulse_bpm=84, temperature_f=99.1,
            spo2_percent=98, respiratory_rate=18, height_cm=168.0, weight_kg=78.0, blood_glucose_mgdl=185,
            high_bp_flag=True, high_glucose_flag=True, ncd_risk_flag=True,
            nurse_notes='Patient presents with high BP and elevated blood sugar. Fast-tracked for doctor consultation.'
        )

        c_ramesh = Consultation.objects.create(
            visit=v_ramesh, patient=p_ramesh, doctor=u_doc, facility=rc_a4,
            chief_complaint='Dizziness and fatigue for 5 days',
            clinical_history='Known history of hypertension for 2 years, irregular medication adherence.',
            clinical_assessment='Elevated BP 148/96 and Random Glucose 185 mg/dL. Suspected uncontrolled Type 2 Diabetes.',
            diagnosis_code='E11.9 / I10', diagnosis_name='Type 2 Diabetes Mellitus with Essential Hypertension',
            treatment_plan='Initiate Metformin 500mg BD, Amlodipine 5mg OD. Refer to Main Hospital B Cardiology Hub.',
            follow_up_date=today + datetime.timedelta(days=14),
            clinical_notes='Advised low sodium diet, exercise, and strict medication adherence.'
        )

        # Prescription
        pr_ramesh = Prescription.objects.create(consultation=c_ramesh, patient=p_ramesh, doctor=u_doc, facility=rc_a4, status='DISPENSED')
        pi1 = PrescriptionItem.objects.create(prescription=pr_ramesh, medicine_name='Metformin 500 mg Tablet', dosage='1-0-1 After Food', frequency='Twice Daily', duration_days=14, quantity=28, status='DISPENSED')
        pi2 = PrescriptionItem.objects.create(prescription=pr_ramesh, medicine_name='Amlodipine 5 mg Tablet', dosage='1-0-0 Morning', frequency='Once Daily', duration_days=14, quantity=14, status='DISPENSED')

        # Record Dispense Transaction
        b_met1.quantity -= 28
        b_met1.save()
        InventoryTransaction.objects.create(facility=rc_a4, medicine=med_met, batch=b_met1, transaction_type='DISPENSED', quantity=28, reference_id=f"PRESCR-{pr_ramesh.id}", created_by=u_pharm)

        # Lab Order
        lo_ramesh = LabOrder.objects.create(consultation=c_ramesh, patient=p_ramesh, doctor=u_doc, facility=rc_a4, test_master=lt_hba1c, status='VERIFIED')
        LabSample.objects.create(lab_order=lo_ramesh, sample_type='Blood', sample_code='SMP-0001', collected_by=u_lab)
        LabResult.objects.create(lab_order=lo_ramesh, result_value='8.4', unit='%', reference_range='4.0 - 5.6 %', interpretation_flag='HIGH', verified_by=u_lab, notes='Uncontrolled HbA1c level')

        # 8. Cross-Facility Referral for Ramesh Kumar
        ref_ramesh = Referral.objects.create(
            referral_id='REF-20260903-0001', patient=p_ramesh, source_facility=rc_a4, destination_facility=hosp_b,
            referring_doctor=u_doc, reason='Specialist evaluation for uncontrolled hypertension and diabetic review',
            clinical_summary='52/M with BP 148/96, HbA1c 8.4%. Referred for secondary hospital cardiology consult.',
            required_service='Cardiology & Endocrine Review', urgency='HIGH', status='COMPLETED'
        )

        ReferralResponse.objects.create(
            referral=ref_ramesh, hospital_doctor=u_hosp,
            specialist_findings='Essential Hypertension with mild ECG changes. Diabetes mellitus uncontrolled.',
            treatment_summary='Continue Metformin 500mg BD. Upgrade Amlodipine to 10mg OD. Added Telmisartan 40mg.',
            return_advice='Patient stable. Return to Rural Clinic A4 for routine follow-up in 14 days.'
        )

        FollowUp.objects.create(
            patient=p_ramesh, referral=ref_ramesh, visit=v_ramesh, facility=rc_a4, category='REFERRAL',
            due_date=today + datetime.timedelta(days=14), status='PENDING', notes='Review post-specialist referral response'
        )

        # 9. NCD & Public Health Surveillance
        NCDRecord.objects.create(patient=p_ramesh, facility=rc_a4, hypertension_diagnosed=True, diabetes_diagnosed=True, risk_level='HIGH', control_status='UNCONTROLLED', last_bp='148/96', last_glucose=185, next_followup_due=today + datetime.timedelta(days=14))
        NCDRecord.objects.create(patient=p_suresh, facility=nc_a2, hypertension_diagnosed=True, diabetes_diagnosed=True, risk_level='MODERATE', control_status='CONTROLLED', last_bp='130/84', last_glucose=125, next_followup_due=today + datetime.timedelta(days=30))

        # Disease Surveillance cases for Ward 12 Fever Spike Alert
        for i in range(15):
            DiseaseCase.objects.create(
                disease_name='Acute Pyrexia / Suspected Viral Fever', patient=p_ramesh if i == 0 else p_suresh,
                facility=rc_a4, ward=ward_rural, severity='MODERATE', status='CONFIRMED', notes='Fever case reported during OPD'
            )

        # 10. Programs: Outreach, Wellness, ARS, Quality, Alerts
        OutreachActivity.objects.create(facility=rc_a4, ward=ward_rural, activity_type='Slum Household NCD & Fever Survey', activity_date=today - datetime.timedelta(days=3), households_covered=65, persons_screened=140, vulnerable_identified=18)
        WellnessSession.objects.create(facility=rc_a4, session_type='Yoga & Meditation', instructor_name='Guru Sri Anand (AYUSH Certified)', session_date=today - datetime.timedelta(days=2), venue='Varthur Clinic Courtyard', participants_count=28)

        # ARS Meeting
        ars_m = ARSMeeting.objects.create(facility=rc_a4, meeting_date=today - datetime.timedelta(days=10), chairperson_name='Corporator Ward 12', attendees_count=8, agenda='Untied Grant allocation for lab consumables & drinking water filter', proceedings_summary='Approved Rs. 8,500 for lab reagents and water purifier maintenance.', untied_funds_spent_rs=8500.00, signed_by_chairman=True)
        ARSMember.objects.create(facility=rc_a4, name='Sri Ward Member', designation='Chairman (Corporator)')
        ARSMember.objects.create(facility=rc_a4, name='Dr. Rajesh Kumar', designation='Member Secretary (MO)')
        ARSActionItem.objects.create(meeting=ars_m, task_description='Procure water purifier cartridge and lab reagent kits', responsible_person='Pharmacist Lakshmi', due_date=today + datetime.timedelta(days=5), status='IN_PROGRESS')

        # Quality & Bio-Medical Waste
        QualityChecklist.objects.create(facility=rc_a4, cleanliness_score=96, infection_control_passed=True, kayakalpa_audit_status='COMPLIANT', inspected_by=u_dist)
        BiomedicalWasteLog.objects.create(facility=rc_a4, yellow_bag_kg=3.20, red_bag_kg=2.10, white_translucent_sharp_kg=0.60, blue_box_glass_kg=1.50, handed_over_by=u_nurse)

        # Automated Demo Alerts
        Alert.objects.create(alert_type='LOW_STOCK', severity='MEDIUM', facility=rc_a4, title='Low Stock: Amlodipine 5mg Tablets', description='Current batch quantity is 35 units (reorder threshold is 80 units).', status='NEW')
        Alert.objects.create(alert_type='EXPIRED', severity='HIGH', facility=rc_a4, title='Expired Stock: Amoxicillin 500mg Batch', description='Batch BATCH-AMX-OLD expired on 15 days ago (40 units remaining).', status='NEW')
        Alert.objects.create(alert_type='DISEASE_THRESHOLD', severity='CRITICAL', facility=rc_a4, title='Public Health Alert: Fever Spike in Varthur Ward', description='15 cases of acute fever reported in last 7 days exceeding threshold.', status='NEW')

        # 11. Mock Integrations Configuration
        IntegrationConfiguration.objects.create(system_name='ABDM', display_name='Ayushman Bharat Digital Mission (ABDM)', status='MOCK', sync_status='SUCCESS', notes='Local ABDM mock connector active.')
        IntegrationConfiguration.objects.create(system_name='ABHA', display_name='ABHA Health ID Gateway', status='MOCK', sync_status='SUCCESS', notes='Local ABHA verification engine.')
        IntegrationConfiguration.objects.create(system_name='HMIS', display_name='Karnataka Health Management Information System', status='MOCK', sync_status='SUCCESS', notes='Periodic HMIS export template ready.')
        IntegrationConfiguration.objects.create(system_name='E_AUSHADA', display_name='KSMSCL E-Aushada Drug Procurement Engine', status='MOCK', sync_status='SUCCESS', notes='Direct indent sync mock interface.')

        # 12. Compliance Matrix Mapping
        ComplianceItem.objects.create(
            requirement_id='REQ-OFF-001', requirement_text='Provide comprehensive primary health care in urban areas',
            source_document='ULB ROK Booklet', classification='OFFICIAL BOOKLET REQUIREMENT',
            application_module='Clinical / Consultation', status='FULLY_COVERED', explanation='Complete 12 service package delivery supported.'
        )
        ComplianceItem.objects.create(
            requirement_id='REQ-KM-003', requirement_text='First-Expiry First-Out (FEFO) batch management and stock alerts',
            source_document='K Mati Proposal', classification='K MATI PROPOSAL',
            application_module='Pharmacy / Inventory', status='FULLY_COVERED', explanation='Automated batch expiry sorting and low stock alerts implemented.'
        )

        # 13. Infrastructure, Oxygen, Consumables, Maintenance Tickets & Beds
        FacilityOxygenSupply.objects.all().delete()
        FacilityConsumableInventory.objects.all().delete()
        FacilityMaintenanceTicket.objects.all().delete()
        FacilityBedCapacity.objects.all().delete()
        FacilityBedAllocation.objects.all().delete()

        # Oxygen Supply
        FacilityOxygenSupply.objects.create(
            facility=rc_a4, oxygen_source='CYLINDER_MANIFOLD', total_cylinders=12, active_cylinders=9, empty_cylinders=3,
            current_pressure_psi=1850, fill_percentage=88, status='OPTIMAL', notes='12-Cylinder B-Type Manifold system tested and functional.'
        )
        FacilityOxygenSupply.objects.create(
            facility=nc_a2, oxygen_source='CONCENTRATOR', total_cylinders=6, active_cylinders=4, empty_cylinders=2,
            current_pressure_psi=1400, fill_percentage=65, status='ADEQUATE', notes='2x 10LPM Oxygen Concentrators online + backup cylinders.'
        )

        # Consumables Inventory (Sanitation, Floor Cleaning & PPE)
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=45, min_threshold=15, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Sodium Hypochlorite 5% (Disinfectant)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=20, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=12, min_threshold=15, reorder_status='LOW_STOCK')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Biohazard Waste Bags (Yellow 50L)', category='INFECTION_CONTROL', unit_of_measure='Packs (100s)', current_stock=8, min_threshold=5, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Biohazard Waste Bags (Red 50L)', category='INFECTION_CONTROL', unit_of_measure='Packs (100s)', current_stock=6, min_threshold=5, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Disposable Nitrile Gloves (M)', category='PERSONAL_PROTECTION', unit_of_measure='Boxes (100s)', current_stock=25, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Surgical Face Masks 3-Ply', category='PERSONAL_PROTECTION', unit_of_measure='Boxes (50s)', current_stock=30, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Paper Towels & Cleaning Wipes', category='GENERAL_FACILITY', unit_of_measure='Rolls', current_stock=18, min_threshold=10, reorder_status='ADEQUATE')

        # Maintenance Tickets (Electrical, Plumbing, Equipment, UPS/Solar)
        FacilityMaintenanceTicket.objects.create(
            facility=rc_a4, ticket_number='MAINT-2026-001', category='ELECTRICAL', equipment_or_area='Main OPD Solar UPS Battery Backup & Inverter',
            priority='HIGH', description='Solar UPS inverter showing battery overload warning during peak hours.', reported_by='Staff Nurse Anitha',
            assigned_technician='BBMP Electrical Division Team - Ward 150', status='IN_PROGRESS'
        )
        FacilityMaintenanceTicket.objects.create(
            facility=rc_a4, ticket_number='MAINT-2026-002', category='PLUMBING', equipment_or_area='Staff Restroom & Handwash Sink Tap',
            priority='MEDIUM', description='Minor leakage in rest room handwash tap replacement needed.', reported_by='Lab Tech Ramesh',
            assigned_technician='Facility Sanitation Team', status='LOGGED'
        )
        FacilityMaintenanceTicket.objects.create(
            facility=rc_a4, ticket_number='MAINT-2026-003', category='OXYGEN_SYSTEM', equipment_or_area='Emergency Oxygen Manifold Pressure Gauge',
            priority='HIGH', description='Secondary regulator pressure gauge calibration verified.', reported_by='Dr. Rajesh Kumar',
            assigned_technician='Karnataka Medical Supplies Oxygen Team', status='RESOLVED', resolved_at=today - datetime.timedelta(days=2)
        )

        # Bed Capacities
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='GENERAL_OBSERVATION', total_beds=6, occupied_beds=2, cleaning_in_progress=1, under_maintenance=0, notes='General OPD observation ward with IV stands and monitors.')
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='EMERGENCY_TRIAGE', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Emergency resuscitation bay bed equipped with defib & suction.')
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='OXYGEN_SUPPORTED', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Dedicated oxygen manifold high-care bed.')

        # Bed Allocations
        FacilityBedAllocation.objects.create(
            facility=rc_a4, bed_number='BED-OBS-01', bed_category='GENERAL_OBSERVATION', patient=p_ramesh, patient_name='Ramesh Kumar (45/M)',
            attending_doctor='Dr. Rajesh Kumar', status='OCCUPIED'
        )
        FacilityBedAllocation.objects.create(
            facility=rc_a4, bed_number='BED-OXY-01', bed_category='OXYGEN_SUPPORTED', patient=p_suresh, patient_name='Suresh Gowda (58/M)',
            attending_doctor='Dr. Rajesh Kumar', status='OCCUPIED'
        )
        FacilityBedAllocation.objects.create(
            facility=rc_a4, bed_number='BED-OBS-02', bed_category='GENERAL_OBSERVATION', patient=None, patient_name='',
            attending_doctor='', status='SANITIZING'
        )
        FacilityBedAllocation.objects.create(
            facility=rc_a4, bed_number='BED-OBS-03', bed_category='GENERAL_OBSERVATION', patient=None, patient_name='',
            attending_doctor='', status='AVAILABLE'
        )

        AuditLog.objects.create(user=u_dist, username_snapshot='district', action='SYSTEM_SEED_DEMO', facility=rc_a4, details='Demo database seeded successfully with infrastructure, oxygen, consumables & beds.')

        self.stdout.write(self.style.SUCCESS("Demo dataset successfully seeded! All credentials and sample data are ready."))


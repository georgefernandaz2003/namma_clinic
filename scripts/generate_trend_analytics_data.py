"""
Namma Clinic - Production-Grade Trend Analytics Dataset Generator
Generates comprehensive historical time-series and multi-scenario clinical data
over a 90-day horizon (July - October 2026) for trend analysis dashboards.

Covers All Scenarios:
1. Outpatient Footfall & Queuing Cycle Times (Arrival -> Triage -> Doctor -> Lab/Pharmacy -> Completed)
2. Triage Vitals & Acuity Distribution (BP, Heart Rate, SpO2, Temp, BMI, Clinical Flags)
3. Epidemiological Surveillance & Monsoon Outbreak Wave (Dengue, Typhoid, Viral Fever, GE, ARI)
4. NCD Longitudinal Chronic Disease Trajectory (Hypertension, T2DM: Uncontrolled -> Controlled)
5. Diagnostic Laboratory Utilization, Specimen Barcoding, & Results (Normal, Abnormal, Panic Critical)
6. Pharmacy Prescription Dispensing, FEFO Batch Movements, & Double-Entry InventoryLedger
7. Multi-Facility Comparison (Urban PHC, Slum Clinic, Rural Clinic, Secondary Hospital)
8. Inter-Facility Referrals (Primary to Secondary Specialist Consultations & Outcomes)
9. Biomedical Waste Generation (Kg by Color Code), Kayakalpa Quality Audits
10. Cold Chain Vaccine Refrigerator Daily Temperature Logs (2°C - 8°C)
11. Community Slum Outreach Screenings & AYUSH Wellness Sessions
12. Operational & Public Health Threshold Alerts
"""

import os
import sys
import random
import datetime
from decimal import Decimal

# Ensure backend path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DATABASE_ENGINE', 'postgresql')

import django
django.setup()

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, RoleMaster, User
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter, VisitStatusHistory
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster, Diagnosis
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest,
    DiagnosticResult, DiagnosticResultAmendment
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Vendor, Dispensation,
    DispensationItem, InventoryLedger, ColdChainLog
)
from apps.ncd.models import NCDRecord, NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.referrals.models import ReferralOrder, ReferralEvent, Referral, ReferralResponse, FollowUp
from apps.alerts.models import Alert, OperationalAlert
from apps.quality.models import QualityChecklist, BiomedicalWasteLog
from apps.outreach.models import OutreachActivity
from apps.wellness.models import WellnessSession

User = get_user_model()


def seed_catalogs():
    """Seed DiagnosisMaster and DiseaseMaster catalogs if empty."""
    print("-> Verifying & Seeding Master Catalogs (ICD-10 & Diseases)...")

    # 1. DiagnosisMaster
    diagnoses_to_seed = [
        ('A90', 'Dengue fever [classical dengue]', 'Infectious / Vector-borne', True),
        ('A01.0', 'Typhoid fever', 'Infectious / Water-borne', True),
        ('A09', 'Infectious gastroenteritis and colitis, unspecified', 'Infectious / Water-borne', True),
        ('B54', 'Unspecified malaria', 'Infectious / Vector-borne', True),
        ('J06.9', 'Acute upper respiratory infection, unspecified', 'Respiratory / Air-borne', False),
        ('J20.9', 'Acute bronchitis, unspecified', 'Respiratory', False),
        ('I10', 'Essential (primary) hypertension', 'Cardiovascular / NCD', False),
        ('E11.9', 'Type 2 diabetes mellitus without complications', 'Endocrine / NCD', False),
        ('E11.2', 'Type 2 diabetes mellitus with diabetic nephropathy', 'Endocrine / NCD', False),
        ('J45.9', 'Asthma, unspecified', 'Respiratory / NCD', False),
        ('K29.7', 'Gastritis, unspecified', 'Gastrointestinal', False),
        ('M25.5', 'Pain in joint, unspecified', 'Musculoskeletal', False),
        ('L30.9', 'Dermatitis, unspecified', 'Dermatology', False),
        ('R50.9', 'Fever, unspecified (Acute Febrile Illness)', 'General Symptoms', False),
        ('D50.9', 'Iron deficiency anemia, unspecified', 'Hematology', False),
    ]

    diag_map = {}
    for code, desc, cat, notif in diagnoses_to_seed:
        dm, _ = DiagnosisMaster.objects.get_or_create(
            icd10_code=code,
            defaults={
                'description': desc,
                'category': cat,
                'is_notifiable': notif,
                'is_active': True
            }
        )
        diag_map[code] = dm

    # 2. DiseaseMaster
    diseases_to_seed = [
        ('DENGUE', 'Dengue Fever', 'VECTOR_BORNE', True),
        ('TYPHOID', 'Typhoid Enteric Fever', 'WATER_BORNE', True),
        ('MALARIA', 'Malaria', 'VECTOR_BORNE', True),
        ('GASTRO', 'Acute Gastroenteritis / Choleraic Diarrhea', 'WATER_BORNE', True),
        ('ARI', 'Severe Acute Respiratory Illness (SARI)', 'AIR_BORNE', True),
    ]

    dis_map = {}
    for code, name, ttype, notif in diseases_to_seed:
        dm, _ = DiseaseMaster.objects.get_or_create(
            disease_code=code,
            defaults={
                'disease_name': name,
                'transmission_type': ttype,
                'is_notifiable_state': notif,
                'is_active': True
            }
        )
        dis_map[code] = dm

    print(f"   [OK] DiagnosisMaster: {DiagnosisMaster.objects.count()} | DiseaseMaster: {DiseaseMaster.objects.count()}")
    return diag_map, dis_map


def generate_trend_dataset():
    random.seed(42)  # Deterministic repeatability

    print("\n======================================================================")
    print("NAMMA CLINIC - PRODUCTION-GRADE TREND ANALYTICS DATASET GENERATOR")
    print("======================================================================")

    diag_map, dis_map = seed_catalogs()

    # Get Core Facilities
    fac_local = Facility.objects.filter(facility_code='PHC-LOCAL-01').first() or Facility.objects.get(id=1)
    fac_lag = Facility.objects.filter(facility_code='NC-LAG-01').first() or fac_local
    fac_rc = Facility.objects.filter(facility_code='RC-A4-01').first() or fac_local
    fac_sub = Facility.objects.filter(facility_code='HOSP-SUB-01').first() or fac_local
    fac_dist = Facility.objects.filter(facility_code='HOSP-DIST-01').first() or fac_local

    facilities = [fac_local, fac_lag, fac_rc]

    # Get Staff Profiles & Users
    staff_doc = StaffProfile.objects.filter(user_account__username__in=['doctor', 'e2e_doctor_user', 'localdoc']).first()
    staff_nurse = StaffProfile.objects.filter(user_account__username__in=['nurse', 'e2e_nurse_user', 'localnurse']).first()
    staff_lab = StaffProfile.objects.filter(user_account__username__in=['lab', 'e2e_lab_user', 'locallab']).first()
    staff_pharm = StaffProfile.objects.filter(user_account__username__in=['pharmacy', 'e2e_pharmacist_user', 'localpharm']).first()

    u_doc = User.objects.filter(username__in=['doctor', 'e2e_doctor_user', 'localdoc']).first()
    u_nurse = User.objects.filter(username__in=['nurse', 'e2e_nurse_user', 'localnurse']).first()
    u_lab = User.objects.filter(username__in=['lab', 'e2e_lab_user', 'locallab']).first()
    u_pharm = User.objects.filter(username__in=['pharmacy', 'e2e_pharmacist_user', 'localpharm']).first()
    u_dho = User.objects.filter(username__in=['district', 'e2e_dho_user', 'localdistrict']).first()

    karnataka = State.objects.filter(code='KA').first()
    dist_central = District.objects.filter(code='KA-BU').first() or District.objects.first()
    ward_lag = Ward.objects.filter(ward_number=68).first() or Ward.objects.first()
    ward_varthur = Ward.objects.filter(name__icontains='Varthur').first() or ward_lag

    # Medicines & Batches
    med_pcm = MedicineMaster.objects.filter(generic_name__icontains='Paracetamol').first()
    med_amx = MedicineMaster.objects.filter(generic_name__icontains='Amoxicillin').first()
    med_met = MedicineMaster.objects.filter(generic_name__icontains='Metformin').first()
    med_aml = MedicineMaster.objects.filter(generic_name__icontains='Amlodipine').first()
    med_ctz = MedicineMaster.objects.filter(generic_name__icontains='Cetirizine').first()
    med_ors = MedicineMaster.objects.filter(generic_name__icontains='ORS').first()

    # Diagnostic Tests
    test_cbc = DiagnosticTestMaster.objects.filter(test_code='CBC').first()
    test_ns1 = DiagnosticTestMaster.objects.filter(test_code='NS1-AG').first()
    test_widal = DiagnosticTestMaster.objects.filter(test_code='WIDAL').first()
    test_fbg = DiagnosticTestMaster.objects.filter(test_code='FBG').first()
    test_ppbg = DiagnosticTestMaster.objects.filter(test_code='PPBG').first()
    test_hba1c = DiagnosticTestMaster.objects.filter(test_code='HBA1C').first()
    test_urine = DiagnosticTestMaster.objects.filter(test_code='URINE-ROUTINE').first()
    test_creat = DiagnosticTestMaster.objects.filter(test_code='CREATININE').first()
    test_lipid = DiagnosticTestMaster.objects.filter(test_code='LIPID-PANEL').first()
    test_malaria = DiagnosticTestMaster.objects.filter(test_code='MAL-RDT').first()

    # -------------------------------------------------------------------------
    # 1. EXPAND PHARMACY BATCHES & INITIALIZE INVENTORY LEDGERS
    # -------------------------------------------------------------------------
    print("-> Initializing Robust Multi-Batch Inventory Stock & Purchase Receipts...")
    med_batches = {}
    vendor = Vendor.objects.first()

    for fac in [fac_local, fac_lag, fac_rc]:
        med_batches[fac.id] = {}
        batch_configs = [
            (med_pcm, f"BATCH-{fac.facility_code[:3]}-PCM-01", 1000, Decimal('1.20')),
            (med_amx, f"BATCH-{fac.facility_code[:3]}-AMX-01", 600, Decimal('3.50')),
            (med_met, f"BATCH-{fac.facility_code[:3]}-MET-01", 800, Decimal('2.10')),
            (med_aml, f"BATCH-{fac.facility_code[:3]}-AML-01", 700, Decimal('1.80')),
            (med_ctz, f"BATCH-{fac.facility_code[:3]}-CTZ-01", 500, Decimal('0.90')),
            (med_ors, f"BATCH-{fac.facility_code[:3]}-ORS-01", 400, Decimal('4.00')),
        ]

        for med, b_num, qty, cost in batch_configs:
            if not med:
                continue
            batch, created = MedicineBatch.objects.get_or_create(
                facility=fac,
                batch_number=b_num,
                defaults={
                    'medicine': med,
                    'vendor': vendor,
                    'supplier': 'Karnataka State Medical Supplies Corp (KSMSCL)',
                    'received_date': datetime.date(2026, 6, 15),
                    'mfg_date': datetime.date(2026, 5, 1),
                    'expiry_date': datetime.date(2028, 4, 30),
                    'unit_cost': cost,
                    'quantity': qty,
                    'available_quantity': qty,
                    'status': 'ACTIVE'
                }
            )
            med_batches[fac.id][med.id] = batch

            # Create Initial Purchase Receipt Ledger if missing
            if not InventoryLedger.objects.filter(batch=batch, transaction_type='PURCHASE_RECEIPT').exists():
                InventoryLedger.objects.create(
                    batch=batch,
                    facility=fac,
                    performed_by_staff=staff_pharm,
                    transaction_type='PURCHASE_RECEIPT',
                    quantity_delta=qty,
                    balance_after=qty,
                    reference_entity_type='PurchaseOrder',
                    reference_entity_id=1,
                    remarks=f"Initial Q3 Bulk Allocation: {med.generic_name} ({qty} units)",
                    transaction_timestamp=timezone.make_aware(datetime.datetime(2026, 6, 15, 9, 30))
                )

    # -------------------------------------------------------------------------
    # 2. GENERATE REALISTIC ADULT PATIENT POPULATION (N = 50)
    # -------------------------------------------------------------------------
    print("-> Ensuring 50 Realistic Adult Demonstration Patients...")

    karnataka_names = [
        ("Naveen Gowda", "MALE", 38, "9845112001"),
        ("Savitri Bai", "FEMALE", 62, "9845112002"),
        ("Ramesh Chandran", "MALE", 49, "9845112003"),
        ("Bhavya Murthy", "FEMALE", 32, "9845112004"),
        ("Girisha K. V.", "MALE", 55, "9845112005"),
        ("Geetha Venkatesh", "FEMALE", 47, "9845112006"),
        ("Harish Kumar", "MALE", 29, "9845112007"),
        ("Indira Priyadarshini", "FEMALE", 58, "9845112008"),
        ("Jagadish Shettar", "MALE", 43, "9845112009"),
        ("Kamala Narayana", "FEMALE", 65, "9845112010"),
        ("Lokesh Gowda", "MALE", 35, "9845112011"),
        ("Madhuri Dixit", "FEMALE", 27, "9845112012"),
        ("Narasimha Murthy", "MALE", 71, "9845112013"),
        ("Padmavathi Amma", "FEMALE", 68, "9845112014"),
        ("Raghavendra Rao", "MALE", 51, "9845112015"),
        ("Shwetha Hegde", "FEMALE", 33, "9845112016"),
        ("Thimme Gowda", "MALE", 64, "9845112017"),
        ("Usha Rani", "FEMALE", 41, "9845112018"),
        ("Venkatesh Prasad", "MALE", 53, "9845112019"),
        ("Vasantha Kumari", "FEMALE", 59, "9845112020"),
        ("Yogesh M.", "MALE", 36, "9845112021"),
        ("Roopa Manjunath", "FEMALE", 44, "9845112022"),
        ("Shankar Nag", "MALE", 61, "9845112023"),
        ("Sunitha Reddy", "FEMALE", 39, "9845112024"),
        ("Pradeep Kumar", "MALE", 48, "9845112025"),
        ("Nandini Gowda", "FEMALE", 26, "9845112026"),
        ("Basavaraj Bommai", "MALE", 67, "9845112027"),
        ("Chaitra K.", "FEMALE", 31, "9845112028"),
        ("Dhananjaya Rao", "MALE", 42, "9845112029"),
        ("Eshwari Devi", "FEMALE", 74, "9845112030"),
        ("Farhan Ahmed", "MALE", 37, "9845112031"),
        ("Gowramma Siddappa", "FEMALE", 69, "9845112032"),
        ("Hanumanthappa K.", "MALE", 56, "9845112033"),
        ("Jayanthi Bai", "FEMALE", 46, "9845112034"),
        ("Kishore Kumar", "MALE", 34, "9845112035"),
        ("Leelavathi Devi", "FEMALE", 63, "9845112036"),
        ("Mohan Das", "MALE", 52, "9845112037"),
        ("Netravathi R.", "FEMALE", 30, "9845112038"),
        ("Omkar Swamy", "MALE", 45, "9845112039"),
        ("Pushpa Latha", "FEMALE", 50, "9845112040"),
    ]

    all_patients = list(Patient.objects.order_by('id')[:10])

    for idx, (pname, gender, age, mobile) in enumerate(karnataka_names, start=11):
        uhid = f"NC-KA-2026-{idx:04d}"
        reg_fac = fac_local
        p, _ = Patient.objects.get_or_create(
            patient_id=uhid,
            defaults={
                'name': pname,
                'age': age,
                'gender': gender,
                'mobile': mobile,
                'date_of_birth': datetime.date(2026 - age, (idx % 12) + 1, (idx % 27) + 1),
                'address': f"House #{100 + idx}, Ward 68 Slum Settlement, Laggere, Bengaluru",
                'district': reg_fac.district or dist_central,
                'ward': reg_fac.ward or ward_lag,
                'registered_at_facility': reg_fac,
                'vulnerability_information': 'Low Income Household / Daily Wage Earner'
            }
        )
        all_patients.append(p)

    print(f"   [OK] Active Patient Directory: {len(all_patients)} Patients Available.")

    # -------------------------------------------------------------------------
    # 3. GENERATE 90-DAY TIME-SERIES VISITS & ENCOUNTERS (July 10 - Oct 07, 2026)
    # -------------------------------------------------------------------------
    print("-> Generating 90-Day Longitudinal Time-Series Visits across All Scenarios...")

    start_date = datetime.date(2026, 7, 10)
    end_date = datetime.date(2026, 10, 7)
    total_days = (end_date - start_date).days

    # Identify Cohorts:
    # 1. Chronic NCD Cohort (16 patients) - regular monthly visits
    ncd_patients = all_patients[2:18]
    for p in ncd_patients:
        NCDCondition.objects.get_or_create(
            patient=p,
            condition_code='HYPERTENSION' if p.id % 2 == 0 else 'DIABETES_T2',
            defaults={
                'registering_facility': fac_local,
                'registering_doctor': staff_doc,
                'diagnosis_date': datetime.date(2026, 6, 1),
                'staging': 'Stage 2 Essential HTN' if p.id % 2 == 0 else 'Type 2 DM with Poor Glycemic Control',
                'control_status': 'UNCONTROLLED',
                'treatment_plan': 'Amlodipine 5mg OD' if p.id % 2 == 0 else 'Metformin 500mg BD + Lifestyle'
            }
        )

    # 2. Outbreak Cohort (Fever / Dengue in August - September)
    outbreak_patients = all_patients[18:38]

    # 3. General Outpatients (remaining)
    general_patients = all_patients[38:] + all_patients[:2]

    # Counters per facility per day
    daily_token_tracker = {}
    created_visits_count = 0
    created_orders_count = 0
    created_prescriptions_count = 0
    created_dispensations_count = 0
    created_surveillance_count = 0

    # Running inventory balance tracker
    batch_balances = {}
    for fac_id in med_batches:
        batch_balances[fac_id] = {}
        for m_id, b in med_batches[fac_id].items():
            last_ledg = InventoryLedger.objects.filter(batch=b).order_by('-id').first()
            batch_balances[fac_id][m_id] = last_ledg.balance_after if last_ledg else b.available_quantity

    # Generate Visits across the timeline
    current_day = start_date
    while current_day <= end_date:
        # Determine day intensity (Monsoonal fever peak between Aug 12 and Sep 18)
        is_fever_surge = datetime.date(2026, 8, 12) <= current_day <= datetime.date(2026, 9, 18)
        day_visits_target = random.randint(4, 7) if is_fever_surge else random.randint(2, 4)

        # Skip heavy traffic on Sundays
        if current_day.weekday() == 6:
            day_visits_target = random.randint(0, 1)

        for _ in range(day_visits_target):
            fac = random.choice([fac_local, fac_local, fac_lag, fac_rc])
            date_key = (fac.id, current_day)
            daily_token_tracker[date_key] = daily_token_tracker.get(date_key, 0) + 1
            tok_num = daily_token_tracker[date_key]

            # Choose clinical scenario for this visit
            scenario_roll = random.random()

            # Scenario A: Fever / Dengue Outbreak (heavy in surge window)
            if is_fever_surge and scenario_roll < 0.65:
                patient = random.choice(outbreak_patients)
                complaint = random.choice([
                    "High acute fever with body rigors and retro-orbital headache for 4 days",
                    "Continuous high grade fever with severe myalgia and nausea",
                    "Fever with vomiting, mild petechiae rash and abdominal discomfort",
                    "Acute febrile illness with chills and joint prostration"
                ])
                diag_code = 'A90' if random.random() < 0.55 else 'R50.9'
                vitals = {
                    'sbp': random.randint(110, 128),
                    'dbp': random.randint(70, 82),
                    'pulse': random.randint(102, 122),
                    'temp': round(random.uniform(101.8, 103.8), 1),
                    'spo2': random.randint(95, 98),
                    'fever_flag': True,
                    'high_bp_flag': False,
                    'is_urgent': True
                }
                needs_lab = True
                lab_test = test_ns1 if diag_code == 'A90' else test_cbc
                prescribe_meds = [med_pcm, med_ors]

            # Scenario B: Chronic NCD Longitudinal Review
            elif scenario_roll < 0.85:
                patient = random.choice(ncd_patients)
                is_htn = (patient.id % 2 == 0)
                # Over time, patient control improves!
                day_progression = (current_day - start_date).days / max(1, total_days)

                if is_htn:
                    complaint = "Routine Hypertension monthly review, checking BP and refilling medication"
                    diag_code = 'I10'
                    sbp = int(162 - (day_progression * 34) + random.randint(-4, 4))
                    dbp = int(98 - (day_progression * 20) + random.randint(-3, 3))
                    vitals = {
                        'sbp': sbp,
                        'dbp': dbp,
                        'pulse': random.randint(72, 84),
                        'temp': 98.4,
                        'spo2': 98,
                        'fever_flag': False,
                        'high_bp_flag': sbp >= 140,
                        'is_urgent': sbp >= 160
                    }
                    needs_lab = (random.random() < 0.35)
                    lab_test = test_creat
                    prescribe_meds = [med_aml]
                else:
                    complaint = "Type 2 Diabetes review, routine blood sugar check"
                    diag_code = 'E11.9'
                    fbg_val = int(185 - (day_progression * 60) + random.randint(-8, 8))
                    vitals = {
                        'sbp': random.randint(118, 132),
                        'dbp': random.randint(76, 84),
                        'pulse': random.randint(74, 82),
                        'temp': 98.4,
                        'spo2': 98,
                        'fever_flag': False,
                        'high_bp_flag': False,
                        'is_urgent': False
                    }
                    needs_lab = True
                    lab_test = test_fbg if random.random() < 0.6 else test_hba1c
                    prescribe_meds = [med_met]

            # Scenario C: General Acute Cough / GI / Musculoskeletal
            else:
                patient = random.choice(general_patients)
                choice_c = random.choice(['URTI', 'GASTRO', 'JOINT'])
                if choice_c == 'URTI':
                    complaint = "Productive cough with sore throat and nasal congestion for 3 days"
                    diag_code = 'J06.9'
                    prescribe_meds = [med_amx, med_ctz, med_pcm]
                elif choice_c == 'GASTRO':
                    complaint = "Watery diarrhea with abdominal cramps and mild dehydration"
                    diag_code = 'A09'
                    prescribe_meds = [med_ors, med_pcm]
                else:
                    complaint = "Bilateral knee joint pain aggravated on walking and climbing stairs"
                    diag_code = 'M25.5'
                    prescribe_meds = [med_pcm]

                vitals = {
                    'sbp': random.randint(114, 130),
                    'dbp': random.randint(72, 84),
                    'pulse': random.randint(74, 88),
                    'temp': 99.2 if choice_c == 'URTI' else 98.4,
                    'spo2': random.randint(97, 99),
                    'fever_flag': False,
                    'high_bp_flag': False,
                    'is_urgent': False
                }
                needs_lab = (choice_c == 'GASTRO' and random.random() < 0.4)
                lab_test = test_widal if needs_lab else None

            # Determine Visit Times
            hour = random.randint(9, 13)
            minute = random.randint(5, 50)
            arr_dt = timezone.make_aware(datetime.datetime.combine(current_day, datetime.time(hour, minute)))
            tri_start = arr_dt + datetime.timedelta(minutes=random.randint(4, 10))
            tri_end = tri_start + datetime.timedelta(minutes=random.randint(3, 5))
            doc_start = tri_end + datetime.timedelta(minutes=random.randint(10, 20))
            doc_end = doc_start + datetime.timedelta(minutes=random.randint(8, 15))
            comp_dt = doc_end + datetime.timedelta(minutes=random.randint(10, 25))

            # Is this historical or today?
            is_today = (current_day == end_date)
            visit_status = 'COMPLETED' if not is_today else random.choice(['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'COMPLETED'])
            queue_state = 'COMPLETED' if visit_status == 'COMPLETED' else ('DOCTOR' if visit_status in ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION'] else 'TRIAGE')

            # Create Visit
            v_id_str = f"VIS-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:03d}"
            visit, created = Visit.objects.get_or_create(
                visit_id=v_id_str,
                defaults={
                    'patient': patient,
                    'facility': fac,
                    'visit_date': arr_dt,
                    'opd_date': current_day,
                    'priority': 'HIGH' if vitals['is_urgent'] else 'NORMAL',
                    'current_queue': queue_state,
                    'status': visit_status,
                    'chief_complaint': complaint,
                    'assigned_doctor': u_doc,
                    'arrival_time': arr_dt,
                    'triage_start_time': tri_start,
                    'triage_end_time': tri_end,
                    'consultation_start_time': doc_start,
                    'consultation_end_time': doc_end,
                    'completed_time': comp_dt if visit_status == 'COMPLETED' else None
                }
            )
            created_visits_count += 1

            # Create Token
            Token.objects.get_or_create(
                facility=fac,
                date=current_day,
                token_number=tok_num,
                defaults={
                    'visit': visit,
                    'priority': visit.priority,
                    'status': 'COMPLETED' if visit_status == 'COMPLETED' else 'WAITING'
                }
            )

            # Create Triage Vitals
            TriageVitals.objects.get_or_create(
                visit=visit,
                defaults={
                    'patient': patient,
                    'nurse': u_nurse,
                    'blood_pressure_systolic': vitals['sbp'],
                    'blood_pressure_diastolic': vitals['dbp'],
                    'pulse_bpm': vitals['pulse'],
                    'temperature_f': Decimal(str(vitals['temp'])),
                    'spo2_percent': vitals['spo2'],
                    'respiratory_rate': random.randint(16, 22),
                    'height_cm': Decimal(str(160 + (patient.id % 20))),
                    'weight_kg': Decimal(str(55 + (patient.id % 30))),
                    'bmi': Decimal('24.2'),
                    'high_bp_flag': vitals['high_bp_flag'],
                    'fever_flag': vitals['fever_flag'],
                    'emergency_flag': vitals['sbp'] >= 180 or vitals['temp'] >= 103.5,
                    'ncd_risk_flag': vitals['high_bp_flag'],
                    'nurse_notes': f"Recorded at {tri_start.strftime('%H:%M')}. Patient alert, complaint noted."
                }
            )

            # Create Modern Triage
            Triage.objects.get_or_create(
                visit=visit,
                defaults={
                    'triaged_by_staff': staff_nurse,
                    'systolic_bp': vitals['sbp'],
                    'diastolic_bp': vitals['dbp'],
                    'pulse_rate': vitals['pulse'],
                    'temperature_celsius': Decimal(str(round((vitals['temp'] - 32) * 5 / 9, 1))),
                    'spo2_percentage': vitals['spo2'],
                    'recorded_at': tri_end
                }
            )

            # Create Consultation
            dm_entry = diag_map.get(diag_code)
            consult, _ = Consultation.objects.get_or_create(
                visit=visit,
                defaults={
                    'patient': patient,
                    'doctor': u_doc,
                    'doctor_staff': staff_doc,
                    'facility': fac,
                    'chief_complaint': complaint,
                    'clinical_history': f"Patient presents with {complaint.lower()}. History reviewed.",
                    'clinical_assessment': f"Clinical impression: {dm_entry.description if dm_entry else diag_code}.",
                    'diagnosis_code': diag_code,
                    'diagnosis_name': dm_entry.description if dm_entry else diag_code,
                    'treatment_plan': "Supportive therapy, prescribed oral medications, hydration, warning signs counselled.",
                    'follow_up_date': current_day + datetime.timedelta(days=7 if vitals['fever_flag'] else 28),
                    'clinical_notes': "Reviewed in OPD. Treatment initiated."
                }
            )

            # Create Diagnosis
            if dm_entry:
                Diagnosis.objects.get_or_create(
                    consultation=consult,
                    diagnosis_master=dm_entry,
                    defaults={
                        'diagnosis_type': 'WORKING',
                        'certainty': 'CONFIRMED' if visit_status == 'COMPLETED' else 'PROVISIONAL',
                        'is_primary': True,
                        'notes': f"Primary diagnosis for {complaint}"
                    }
                )

            # Create Longitudinal NCD Assessment if applicable
            if diag_code in ['I10', 'E11.9'] and patient in ncd_patients:
                ncd_cond = NCDCondition.objects.filter(patient=patient).first()
                if ncd_cond:
                    # Update condition control status dynamically
                    is_controlled = (vitals['sbp'] < 140 and vitals['dbp'] < 90)
                    ncd_cond.control_status = 'CONTROLLED' if is_controlled else 'UNCONTROLLED'
                    ncd_cond.save()

                    NCDAssessment.objects.create(
                        condition=ncd_cond,
                        visit=visit,
                        assessed_by_staff=staff_doc,
                        systolic_bp=vitals['sbp'],
                        diastolic_bp=vitals['dbp'],
                        blood_glucose_fasting=Decimal(str(random.randint(95, 125))) if is_controlled else Decimal(str(random.randint(145, 195))),
                        hba1c=Decimal('6.8') if is_controlled else Decimal('8.6'),
                        bmi=Decimal('25.1'),
                        clinical_notes=f"Follow-up visit {current_day}. Control status: {ncd_cond.control_status}."
                    )

            # Scenario: Laboratory Diagnostic Order
            if needs_lab and lab_test:
                ord_num = f"ORD-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:03d}"
                diag_order, created_ord = DiagnosticOrder.objects.get_or_create(
                    order_number=ord_num,
                    defaults={
                        'visit': visit,
                        'facility': fac,
                        'ordering_doctor_staff': staff_doc,
                        'order_date': current_day,
                        'lab_token_number': tok_num,
                        'priority': 'URGENT' if vitals['is_urgent'] else 'ROUTINE',
                        'status': 'VERIFIED' if visit_status == 'COMPLETED' else 'ORDERED',
                        'clinical_indication': complaint
                    }
                )
                if created_ord:
                    created_orders_count += 1
                    # Create Specimen
                    spec = Specimen.objects.create(
                        diagnostic_order=diag_order,
                        barcode_identifier=f"SMP-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:04d}",
                        specimen_type=lab_test.specimen_type or 'WHOLE_BLOOD',
                        status='COLLECTED' if visit_status == 'COMPLETED' else 'PENDING',
                        collected_by_staff=staff_lab,
                        collected_at=doc_end + datetime.timedelta(minutes=5)
                    )

                    # Create TestRequest
                    tr = TestRequest.objects.create(
                        diagnostic_order=diag_order,
                        test_master=lab_test,
                        specimen=spec,
                        status='COMPLETED' if visit_status == 'COMPLETED' else 'PENDING'
                    )

                    # Create Result if completed
                    if visit_status == 'COMPLETED':
                        # Realistic test results
                        is_abn = False
                        is_crit = False
                        if lab_test.test_code == 'NS1-AG':
                            res_text = "Positive (Reactive)" if diag_code == 'A90' else "Negative (Non-Reactive)"
                            res_num = None
                            is_abn = (res_text == "Positive (Reactive)")
                        elif lab_test.test_code == 'CBC':
                            # Thrombocytopenia during Dengue surge!
                            plt = random.randint(45, 95) if (is_fever_surge and random.random() < 0.5) else random.randint(180, 320)
                            hb = round(random.uniform(12.5, 15.2), 1)
                            wbc = random.randint(3800, 11500)
                            res_text = f"Hb: {hb} g/dL | WBC: {wbc} /mcL | Platelets: {plt}k /mcL"
                            res_num = Decimal(str(plt))
                            is_abn = (plt < 150)
                            is_crit = (plt < 50)
                        elif lab_test.test_code == 'FBG':
                            val = random.randint(95, 195)
                            res_text = f"{val} mg/dL"
                            res_num = Decimal(str(val))
                            is_abn = (val > 126)
                        elif lab_test.test_code == 'HBA1C':
                            val = round(random.uniform(5.4, 9.4), 1)
                            res_text = f"{val} %"
                            res_num = Decimal(str(val))
                            is_abn = (val > 6.5)
                        elif lab_test.test_code == 'WIDAL':
                            res_text = "TO 1:160, TH 1:160 (Significant titer)" if diag_code == 'A01.0' else "TO < 1:80, TH < 1:80"
                            res_num = None
                            is_abn = "Significant" in res_text
                        else:
                            res_text = "Normal limits"
                            res_num = Decimal('1.0')

                        dres = DiagnosticResult.objects.create(
                            test_request=tr,
                            result_value_text=res_text,
                            result_value_numeric=res_num,
                            reference_range_applied=lab_test.reference_range_male,
                            is_abnormal=is_abn,
                            is_critical_panic=is_crit,
                            status='VERIFIED',
                            entered_by_staff=staff_lab,
                            entered_at=doc_end + datetime.timedelta(minutes=15),
                            verified_by_staff=staff_doc,
                            verified_at=comp_dt
                        )

                        # Epidemiological Surveillance Case if notifiable disease
                        if diag_code in ['A90', 'A01.0', 'B54', 'A09']:
                            dis_obj = dis_map.get('DENGUE' if diag_code == 'A90' else ('TYPHOID' if diag_code == 'A01.0' else 'GASTRO'))
                            if dis_obj:
                                c_num = f"DSC-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:03d}"
                                scase, created_sc = DiseaseSurveillanceCase.objects.get_or_create(
                                    case_number=c_num,
                                    defaults={
                                        'patient': patient,
                                        'facility': fac,
                                        'disease': dis_obj,
                                        'reporting_staff': staff_doc,
                                        'ward': patient.ward,
                                        'diagnosis_date': current_day,
                                        'severity': 'SEVERE' if is_crit else ('MODERATE' if is_abn else 'MILD'),
                                        'status': 'CONFIRMED' if is_abn else 'SUSPECTED',
                                        'lab_confirmed': is_abn,
                                        'diagnostic_result': dres,
                                        'investigation_notes': f"Surveillance notification generated for {dis_obj.disease_name}."
                                    }
                                )
                                if created_sc:
                                    created_surveillance_count += 1
                                    # Create PublicHealthNotification
                                    PublicHealthNotification.objects.create(
                                        case=scase,
                                        notified_authority='DISTRICT_SURVEILLANCE_OFFICER',
                                        transmission_status='ACKNOWLEDGED',
                                        dispatch_payload={
                                            'case_number': scase.case_number,
                                            'disease': dis_obj.disease_name,
                                            'ward': patient.ward.name if patient.ward else 'Laggere',
                                            'facility': fac.facility_name,
                                            'lab_result': res_text
                                        },
                                        dispatched_at=comp_dt,
                                        acknowledged_at=comp_dt + datetime.timedelta(minutes=30)
                                    )

            # Scenario: Prescription & Inventory Ledger
            if prescribe_meds and visit_status == 'COMPLETED':
                rx, created_rx = Prescription.objects.get_or_create(
                    consultation=consult,
                    defaults={
                        'patient': patient,
                        'doctor': u_doc,
                        'doctor_staff': staff_doc,
                        'facility': fac,
                        'date': current_day,
                        'status': 'VERIFIED',
                        'notes': "Dispense as written. Complete full course.",
                        'verified_by': u_pharm,
                        'verified_at': comp_dt
                    }
                )
                if created_rx:
                    created_prescriptions_count += 1
                    # Create Dispensation header
                    disp = Dispensation.objects.create(
                        prescription=rx,
                        facility=fac,
                        dispensed_by_staff=staff_pharm,
                        dispensation_number=f"DSP-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:03d}",
                        dispensed_at=comp_dt,
                        remarks="Standard clinical dispense per FEFO protocol."
                    )
                    created_dispensations_count += 1

                    for med in prescribe_meds:
                        if not med:
                            continue
                        qty_to_disp = random.choice([10, 14, 20])
                        p_item = PrescriptionItem.objects.create(
                            prescription=rx,
                            medicine=med,
                            medicine_name=med.generic_name,
                            dosage="1 tablet" if med != med_ors else "1 sachet in 1L water",
                            frequency="TDS" if med == med_pcm else "OD",
                            duration_days=qty_to_disp // 2,
                            quantity=qty_to_disp,
                            dispensed_quantity=qty_to_disp,
                            status='DISPENSED'
                        )

                        # Link DispensationItem & Consume via Double-Entry InventoryLedger
                        batch = med_batches.get(fac.id, {}).get(med.id)
                        if batch:
                            DispensationItem.objects.create(
                                dispensation=disp,
                                prescription_item=p_item,
                                batch=batch,
                                quantity_dispensed=qty_to_disp
                            )

                            current_bal = batch_balances[fac.id].get(med.id, 500)
                            new_bal = max(0, current_bal - qty_to_disp)
                            batch_balances[fac.id][med.id] = new_bal

                            # Decrement batch available quantity
                            batch.available_quantity = new_bal
                            batch.save()

                            # Double-entry InventoryLedger entry
                            InventoryLedger.objects.create(
                                batch=batch,
                                facility=fac,
                                performed_by_staff=staff_pharm,
                                transaction_type='DISPENSE',
                                quantity_delta=-qty_to_disp,
                                balance_after=new_bal,
                                reference_entity_type='DispensationItem',
                                reference_entity_id=p_item.id,
                                remarks=f"Dispensed for Patient {patient.patient_id} (Rx #{rx.id})",
                                transaction_timestamp=comp_dt
                            )

            # Scenario: Inter-Facility Referrals (for high severity cases)
            if vitals['sbp'] >= 170 or (diag_code == 'A90' and vitals.get('is_crit', False)):
                ref_num = f"REF-F{fac.id}-{current_day.strftime('%Y%m%d')}-{tok_num:03d}"
                dest_fac = fac_dist if vitals['sbp'] >= 180 else fac_sub
                urgency = 'EMERGENCY' if vitals['sbp'] >= 180 else 'URGENT'

                ref_order, created_ref = ReferralOrder.objects.get_or_create(
                    referral_number=ref_num,
                    defaults={
                        'visit': visit,
                        'patient': patient,
                        'source_facility': fac,
                        'destination_facility': dest_fac,
                        'referring_doctor': staff_doc,
                        'urgency': urgency,
                        'reason': "Specialist Cardiology Evaluation for Severe Hypertension" if vitals['sbp'] >= 170 else "High Dependency Care for Dengue with Severe Thrombocytopenia",
                        'clinical_summary': f"BP {vitals['sbp']}/{vitals['dbp']}, acute symptoms present.",
                        'status': 'COMPLETED' if current_day < end_date - datetime.timedelta(days=3) else 'INITIATED'
                    }
                )
                if created_ref:
                    ReferralEvent.objects.create(
                        referral=ref_order,
                        recorded_by_staff=staff_doc,
                        event_type='INITIATION',
                        specialist_findings="Referred from primary clinic.",
                        treatment_rendered="Stabilized with oral anti-hypertensives / IV fluids.",
                        return_advice="Follow up at primary clinic after specialist stabilization.",
                        event_timestamp=comp_dt
                    )

        # Update Facility Daily Counter
        for fac in facilities:
            cnt = daily_token_tracker.get((fac.id, current_day), 0)
            if cnt > 0:
                FacilityDailyCounter.objects.update_or_create(
                    facility=fac,
                    counter_date=current_day,
                    counter_type='OPD',
                    defaults={'last_token_number': cnt}
                )

        # ---------------------------------------------------------------------
        # 4. DAILY / PERIODIC OPERATIONAL LOGS
        # ---------------------------------------------------------------------
        # Cold Chain Log: 2 entries per day (Morning 8:30 AM & Evening 5:30 PM)
        for fac in facilities:
            temp_am = round(random.uniform(3.4, 5.2), 1)
            temp_pm = round(random.uniform(4.0, 5.8), 1)
            am_dt = timezone.make_aware(datetime.datetime.combine(current_day, datetime.time(8, 30)))
            pm_dt = timezone.make_aware(datetime.datetime.combine(current_day, datetime.time(17, 30)))

            ColdChainLog.objects.get_or_create(
                facility=fac,
                recorded_at=am_dt,
                defaults={
                    'storage_location': 'Pharmacy Main Vaccine Refrigerator #1',
                    'min_temp_celsius': Decimal('2.0'),
                    'max_temp_celsius': Decimal('8.0'),
                    'recorded_temp_celsius': Decimal(str(temp_am)),
                    'recorded_by': u_pharm,
                    'status': 'NORMAL'
                }
            )
            ColdChainLog.objects.get_or_create(
                facility=fac,
                recorded_at=pm_dt,
                defaults={
                    'storage_location': 'Pharmacy Main Vaccine Refrigerator #1',
                    'min_temp_celsius': Decimal('2.0'),
                    'max_temp_celsius': Decimal('8.0'),
                    'recorded_temp_celsius': Decimal(str(temp_pm)),
                    'recorded_by': u_pharm,
                    'status': 'NORMAL'
                }
            )

        # Weekly Biomedical Waste Log (every Friday)
        if current_day.weekday() == 4:
            for fac in facilities:
                BiomedicalWasteLog.objects.get_or_create(
                    facility=fac,
                    date=current_day,
                    defaults={
                        'yellow_bag_kg': Decimal(str(round(random.uniform(4.5, 9.2), 1))),
                        'red_bag_kg': Decimal(str(round(random.uniform(3.0, 6.5), 1))),
                        'white_translucent_sharp_kg': Decimal(str(round(random.uniform(0.8, 1.8), 1))),
                        'blue_box_glass_kg': Decimal(str(round(random.uniform(1.5, 3.2), 1))),
                        'disposal_agency': 'BBMP Authorized Biomedical Waste Services Pvt Ltd',
                        'handed_over_by': u_nurse
                    }
                )

        # Bi-weekly Outreach and Wellness
        if current_day.day in [5, 20]:
            for fac in [fac_local, fac_rc]:
                OutreachActivity.objects.get_or_create(
                    facility=fac,
                    activity_date=current_day,
                    defaults={
                        'ward': fac.ward or ward_lag,
                        'activity_type': 'Monsoon Fever & Vector-borne Disease Door-to-Door Screening' if is_fever_surge else 'Slum Population NCD Blood Pressure & Glucose Camp',
                        'households_covered': random.randint(45, 90),
                        'persons_screened': random.randint(110, 220),
                        'vulnerable_identified': random.randint(8, 25),
                        'conducted_by': 'Primary Healthcare Outreach Team (Sister Kavitha & ASHA workers)',
                        'summary_notes': "Community screening successfully completed. Suspected fever cases directed to PHC OPD."
                    }
                )
                WellnessSession.objects.get_or_create(
                    facility=fac,
                    session_date=current_day,
                    defaults={
                        'session_type': 'AYUSH Yoga, Pranayama & Stress Management',
                        'instructor_name': 'Certified AYUSH Wellness Instructor Sri Anand',
                        'venue': f"{fac.facility_name} Community Health Hall",
                        'participants_count': random.randint(25, 45)
                    }
                )

        # Monthly Kayakalpa Quality Audit
        if current_day.day == 28:
            for fac in facilities:
                QualityChecklist.objects.get_or_create(
                    facility=fac,
                    inspection_date=current_day,
                    defaults={
                        'cleanliness_score': random.randint(90, 98),
                        'infection_control_passed': True,
                        'kayakalpa_audit_status': 'COMPLIANT',
                        'corrective_actions': "Biomedical waste segregation compliant. Hand hygiene posters maintained.",
                        'inspected_by': u_dho or u_doc
                    }
                )

        # Next day
        current_day += datetime.timedelta(days=1)

    print("\n======================================================================")
    print("TREND DATA GENERATION COMPLETED SUCCESSFULLY!")
    print("======================================================================")
    print(f"Total Visits Seeded:               {Visit.objects.count()} (New: {created_visits_count})")
    print(f"Total Patients Available:          {Patient.objects.count()}")
    print(f"Total Diagnostic Orders:           {DiagnosticOrder.objects.count()} (New: {created_orders_count})")
    print(f"Total Prescriptions:               {Prescription.objects.count()} (New: {created_prescriptions_count})")
    print(f"Total Dispensations:               {Dispensation.objects.count()} (New: {created_dispensations_count})")
    print(f"Total Inventory Ledger Entries:    {InventoryLedger.objects.count()}")
    print(f"Total Surveillance Cases:          {DiseaseSurveillanceCase.objects.count()} (New: {created_surveillance_count})")
    print(f"Total NCD Assessments:             {NCDAssessment.objects.count()}")
    print(f"Total Referral Orders:             {ReferralOrder.objects.count()}")
    print(f"Total Biomedical Waste Logs:       {BiomedicalWasteLog.objects.count()}")
    print(f"Total Cold Chain Refrigerator Logs:{ColdChainLog.objects.count()}")
    print(f"Total Community Outreach Camps:    {OutreachActivity.objects.count()}")
    print("======================================================================\n")


if __name__ == '__main__':
    generate_trend_dataset()

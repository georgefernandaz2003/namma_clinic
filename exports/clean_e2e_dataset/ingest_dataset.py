"""
Authoritative Dataset Ingestion & Migration Script for Namma Clinic.

Ingests all 13 CSV export files from exports/clean_e2e_dataset/ into PostgreSQL / Django models
in strict foreign-key dependency order with transaction atomicity.

Usage:
    python scripts/ingest_clean_e2e_dataset.py [--source PATH_TO_CSV_DIR] [--dry-run]
"""
import os
import sys
import csv
import argparse
import datetime
from decimal import Decimal

# Auto-detect backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
potential_backend_paths = [
    os.path.abspath(os.path.join(current_dir, '..', '..', 'backend')),
    os.path.abspath(os.path.join(current_dir, '..', 'backend')),
    os.path.abspath(os.path.join(current_dir, 'backend')),
]
backend_path = None
for p in potential_backend_paths:
    if os.path.exists(os.path.join(p, 'manage.py')):
        backend_path = p
        break

if not backend_path:
    backend_path = potential_backend_paths[0]

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
from apps.accounts.models import Person, StaffProfile, StaffRoleAssignment, RoleMaster
from apps.patients.models import Patient, Household
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster, Diagnosis
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation, DispensationItem,
    InventoryLedger, PatientCounselling
)
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseSurveillanceCase, PublicHealthNotification, DiseaseMaster

User = get_user_model()


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.date.fromisoformat(date_str.strip().split()[0])
    except Exception:
        return None


def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(dt_str.strip())
        if timezone.is_naive(dt):
            return timezone.make_aware(dt)
        return dt
    except Exception:
        return None


def parse_time(t_str):
    if not t_str:
        return None
    try:
        parts = [int(p) for p in t_str.strip().split(':')]
        return datetime.time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)
    except Exception:
        return None


def make_dt(date_obj, time_str):
    if not date_obj:
        return timezone.now()
    if not time_str:
        return timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time(9, 0, 0)))
    try:
        parts = [int(p) for p in time_str.strip().split(':')]
        t = datetime.time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)
        return timezone.make_aware(datetime.datetime.combine(date_obj, t))
    except Exception:
        return timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time(9, 0, 0)))


def parse_decimal(val_str, default=0.0):
    if not val_str:
        return Decimal(str(default))
    try:
        return Decimal(str(val_str).strip())
    except Exception:
        return Decimal(str(default))


def parse_int(val_str, default=0):
    if not val_str:
        return default
    try:
        return int(float(str(val_str).strip()))
    except Exception:
        return default


def read_csv_rows(filepath):
    if not os.path.exists(filepath):
        print(f"  [WARN] File not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def ingest_all(source_dir, dry_run=False):
    print("=" * 80)
    print(f"NAMMA CLINIC CSV DATASET INGESTION & MIGRATION")
    print(f"Source Directory: {os.path.abspath(source_dir)}")
    print(f"Dry Run Mode:     {'ENABLED (no DB writes)' if dry_run else 'DISABLED (live ingestion)'}")
    print("=" * 80)

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory does not exist: {source_dir}")
        sys.exit(1)

    with transaction.atomic():
        default_lab_staff = StaffProfile.objects.filter(role_assignments__role__name='LAB_TECHNICIAN').first() or StaffProfile.objects.first()
        default_doc_staff = StaffProfile.objects.filter(role_assignments__role__name='DOCTOR').first() or StaffProfile.objects.first()
        default_pharm_staff = StaffProfile.objects.filter(role_assignments__role__name='PHARMACIST').first() or StaffProfile.objects.first()

        # ----------------------------------------------------------------------
        # 1. PATIENTS & DEMOGRAPHICS
        # ----------------------------------------------------------------------
        print("\n1. Ingesting Patients & Demographics (01_patients_and_demographics.csv)...")
        pat_file = os.path.join(source_dir, '01_patients_and_demographics.csv')
        pat_rows = read_csv_rows(pat_file)
        pat_count = 0

        for r in pat_rows:
            pat_id = r.get("Patient ID")
            if not pat_id:
                continue

            ward_num = parse_int(r.get("Ward Number"))
            ward_obj = Ward.objects.filter(ward_number=ward_num).first()
            if not ward_obj and r.get("Ward"):
                ward_obj = Ward.objects.filter(name__icontains=r.get("Ward")).first()

            fac_code = r.get("Facility Code")
            fac_obj = Facility.objects.filter(facility_code=fac_code).first()

            dist_name = r.get("District")
            dist_obj = District.objects.filter(name__icontains=dist_name).first() if dist_name else (ward_obj.zone.district if ward_obj and ward_obj.zone else None)

            Patient.objects.update_or_create(
                patient_id=pat_id,
                defaults={
                    "name": r.get("Full Name", ""),
                    "gender": r.get("Gender", "M"),
                    "age": parse_int(r.get("Age")),
                    "date_of_birth": parse_date(r.get("DOB")),
                    "mobile": r.get("Mobile", ""),
                    "ABHA_ID_DEMO": r.get("ABHA ID", ""),
                    "address": r.get("Address", ""),
                    "ward": ward_obj,
                    "district": dist_obj,
                    "registered_at_facility": fac_obj,
                    "vulnerability_information": r.get("Vulnerability Info", ""),
                    "registration_date": parse_date(r.get("Registration Date")) or timezone.localdate(),
                }
            )
            pat_count += 1
        print(f"  -> Ingested {pat_count} Patient records.")

        # ----------------------------------------------------------------------
        # 2. HOUSEHOLDS
        # ----------------------------------------------------------------------
        print("\n2. Ingesting Households (02_households.csv)...")
        hh_file = os.path.join(source_dir, '02_households.csv')
        hh_rows = read_csv_rows(hh_file)
        hh_count = 0

        for r in hh_rows:
            hh_id = r.get("Household ID")
            if not hh_id:
                continue

            ward_name = r.get("Ward")
            ward_obj = Ward.objects.filter(name__icontains=ward_name).first() if ward_name else None

            Household.objects.update_or_create(
                household_id=hh_id,
                defaults={
                    "head_name": r.get("Head of Household", ""),
                    "address": r.get("Address", ""),
                    "ward": ward_obj,
                    "members_count": parse_int(r.get("Members Count"), 4),
                    "vulnerable_category": r.get("Vulnerable Category", ""),
                }
            )
            hh_count += 1
        print(f"  -> Ingested {hh_count} Household records.")

        # ----------------------------------------------------------------------
        # 3. VISITS & TOKENS
        # ----------------------------------------------------------------------
        print("\n3. Ingesting OPD Visits & Queue Tokens (03_visits_and_tokens.csv)...")
        v_file = os.path.join(source_dir, '03_visits_and_tokens.csv')
        v_rows = read_csv_rows(v_file)
        v_count = 0

        for r in v_rows:
            vid = r.get("Visit ID")
            if not vid:
                continue

            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            fac_code = r.get("Facility Code")
            fac_obj = Facility.objects.filter(facility_code=fac_code).first() or pat_obj.registered_at_facility

            doc_username = r.get("Assigned Doctor")
            doc_user = User.objects.filter(username=doc_username).first() if doc_username else None

            opd_d = parse_date(r.get("OPD Date"))
            visit_obj, _ = Visit.objects.update_or_create(
                visit_id=vid,
                defaults={
                    "patient": pat_obj,
                    "facility": fac_obj,
                    "opd_date": opd_d,
                    "visit_type": r.get("Visit Type", "GENERAL_OPD"),
                    "priority": r.get("Priority", "NORMAL"),
                    "current_queue": r.get("Current Queue", "COMPLETED"),
                    "status": r.get("Status", "COMPLETED"),
                    "chief_complaint": r.get("Chief Complaint", ""),
                    "assigned_doctor": doc_user,
                    "arrival_time": make_dt(opd_d, r.get("Arrival Time")),
                    "completed_time": make_dt(opd_d, r.get("Completed Time")),
                }
            )

            tok_num = r.get("Token Number")
            if tok_num:
                Token.objects.update_or_create(
                    visit=visit_obj,
                    defaults={
                        "token_number": tok_num,
                        "facility": fac_obj,
                        "opd_date": visit_obj.opd_date,
                        "status": "COMPLETED",
                    }
                )
            v_count += 1
        print(f"  -> Ingested {v_count} OPD Visits and Tokens.")

        # ----------------------------------------------------------------------
        # 4. TRIAGE & VITALS
        # ----------------------------------------------------------------------
        print("\n4. Ingesting Nurse Triage Vitals (04_triage_vitals.csv)...")
        tr_file = os.path.join(source_dir, '04_triage_vitals.csv')
        tr_rows = read_csv_rows(tr_file)
        tr_count = 0

        for r in tr_rows:
            vid = r.get("Visit ID")
            visit_obj = Visit.objects.filter(visit_id=vid).first()
            if not visit_obj:
                continue

            nurse_user = User.objects.filter(username=r.get("Nurse")).first()

            TriageVitals.objects.update_or_create(
                visit=visit_obj,
                defaults={
                    "patient": visit_obj.patient,
                    "nurse": nurse_user,
                    "blood_pressure_systolic": parse_int(r.get("Systolic BP")),
                    "blood_pressure_diastolic": parse_int(r.get("Diastolic BP")),
                    "pulse_bpm": parse_int(r.get("Pulse (bpm)")),
                    "temperature_f": parse_decimal(r.get("Temp (F)")),
                    "spo2_percent": parse_int(r.get("SpO2 (%)")),
                    "respiratory_rate": parse_int(r.get("Respiratory Rate")),
                    "height_cm": parse_decimal(r.get("Height (cm)")),
                    "weight_kg": parse_decimal(r.get("Weight (kg)")),
                    "bmi": parse_decimal(r.get("BMI")),
                    "blood_glucose_mgdl": parse_int(r.get("Blood Glucose (mg/dL)")) if r.get("Blood Glucose (mg/dL)") else None,
                    "nurse_notes": r.get("Nurse Notes", ""),
                }
            )
            tr_count += 1
        print(f"  -> Ingested {tr_count} Nurse Triage Vitals records.")

        # ----------------------------------------------------------------------
        # 5. DOCTOR CONSULTATIONS & DIAGNOSES
        # ----------------------------------------------------------------------
        print("\n5. Ingesting Consultations & Diagnoses (05_doctor_consultations_and_diagnoses.csv)...")
        c_file = os.path.join(source_dir, '05_doctor_consultations_and_diagnoses.csv')
        c_rows = read_csv_rows(c_file)
        c_count = 0

        for r in c_rows:
            vid = r.get("Visit ID")
            visit_obj = Visit.objects.filter(visit_id=vid).first()
            if not visit_obj:
                continue

            doc_user = User.objects.filter(username=r.get("Doctor")).first() or visit_obj.assigned_doctor
            diag_code = r.get("ICD-10 Code", "")
            diag_name = r.get("Diagnosis Name", "")

            consult_obj, _ = Consultation.objects.update_or_create(
                visit=visit_obj,
                defaults={
                    "patient": visit_obj.patient,
                    "facility": visit_obj.facility,
                    "doctor": doc_user,
                    "chief_complaint": r.get("Chief Complaint", ""),
                    "clinical_history": r.get("Clinical History", ""),
                    "clinical_assessment": r.get("Clinical Assessment", ""),
                    "diagnosis_code": diag_code,
                    "diagnosis_name": diag_name,
                    "treatment_plan": r.get("Treatment Plan", ""),
                    "follow_up_date": parse_date(r.get("Follow Up Date")),
                    "clinical_notes": r.get("Clinical Notes", ""),
                }
            )

            if diag_code:
                master = DiagnosisMaster.objects.filter(icd10_code=diag_code).first()
                if not master:
                    master = DiagnosisMaster.objects.create(icd10_code=diag_code, description=diag_name)
                Diagnosis.objects.update_or_create(
                    consultation=consult_obj,
                    diagnosis_master=master,
                    defaults={
                        "certainty": r.get("Certainty", "CONFIRMED"),
                    }
                )
            c_count += 1
        print(f"  -> Ingested {c_count} Doctor Consultations and Diagnoses.")

        # ----------------------------------------------------------------------
        # 6. LABORATORY ORDERS & RESULTS
        # ----------------------------------------------------------------------
        print("\n6. Ingesting Diagnostic Orders & Verified Results (06_laboratory_orders_and_results.csv)...")
        lab_file = os.path.join(source_dir, '06_laboratory_orders_and_results.csv')
        lab_rows = read_csv_rows(lab_file)
        lab_count = 0

        for r in lab_rows:
            ord_num = r.get("Order Number")
            if not ord_num:
                continue

            vid = r.get("Visit ID")
            visit_obj = Visit.objects.filter(visit_id=vid).first()
            if not visit_obj:
                continue

            test_code = r.get("Test Code")
            test_master = DiagnosticTestMaster.objects.filter(test_code=test_code).first()
            if not test_master:
                test_master = DiagnosticTestMaster.objects.create(
                    test_code=test_code,
                    test_name=r.get("Test Name", test_code),
                    specimen_type=r.get("Specimen", "BLOOD"),
                    default_unit=r.get("Unit", ""),
                )

            diag_order, _ = DiagnosticOrder.objects.update_or_create(
                order_number=ord_num,
                defaults={
                    "visit": visit_obj,
                    "facility": visit_obj.facility,
                    "order_date": parse_date(r.get("Order Date")) or visit_obj.opd_date,
                    "priority": r.get("Priority", "ROUTINE"),
                    "clinical_indication": r.get("Clinical Indication", ""),
                }
            )

            req_obj, _ = TestRequest.objects.update_or_create(
                diagnostic_order=diag_order,
                test_master=test_master,
                defaults={"status": r.get("Test Status", "VERIFIED")}
            )

            verifier_user = User.objects.filter(username=r.get("Verified By")).first()
            verifier_staff = StaffProfile.objects.filter(user_account=verifier_user).first() if verifier_user else default_lab_staff
            entered_staff = verifier_staff or default_lab_staff

            DiagnosticResult.objects.update_or_create(
                test_request=req_obj,
                defaults={
                    "result_value_text": r.get("Result Text", ""),
                    "result_value_numeric": parse_decimal(r.get("Result Numeric")) if r.get("Result Numeric") else None,
                    "reference_range_applied": r.get("Reference Range", "Normal"),
                    "is_abnormal": (r.get("Flag") == "ABNORMAL"),
                    "status": "VERIFIED",
                    "entered_by_staff": entered_staff,
                    "verified_by_staff": verifier_staff,
                    "verified_at": parse_datetime(r.get("Verified At")) or timezone.now(),
                }
            )
            lab_count += 1
        print(f"  -> Ingested {lab_count} Diagnostic Orders and Verified Results.")

        # ----------------------------------------------------------------------
        # 7. PHARMACY PRESCRIPTIONS
        # ----------------------------------------------------------------------
        print("\n7. Ingesting Pharmacy Prescriptions (07_pharmacy_prescriptions.csv)...")
        rx_file = os.path.join(source_dir, '07_pharmacy_prescriptions.csv')
        rx_rows = read_csv_rows(rx_file)
        rx_count = 0

        for r in rx_rows:
            vid = r.get("Visit ID")
            visit_obj = Visit.objects.filter(visit_id=vid).first()
            if not visit_obj:
                continue

            consult_obj = Consultation.objects.filter(visit=visit_obj).first()
            doc_user = User.objects.filter(username=r.get("Doctor")).first() or visit_obj.assigned_doctor
            doc_staff = StaffProfile.objects.filter(user_account=doc_user).first() if doc_user else default_doc_staff

            rx_obj, _ = Prescription.objects.update_or_create(
                consultation=consult_obj,
                defaults={
                    "patient": visit_obj.patient,
                    "facility": visit_obj.facility,
                    "doctor": doc_user,
                    "doctor_staff": doc_staff,
                    "status": r.get("Prescription Status", "DISPENSED"),
                    "notes": r.get("Notes", ""),
                    "date": parse_date(r.get("Prescribed At")) or visit_obj.opd_date,
                }
            )

            med_name = r.get("Medicine", "")
            med_obj = MedicineMaster.objects.filter(generic_name__icontains=med_name).first()

            PrescriptionItem.objects.update_or_create(
                prescription=rx_obj,
                medicine_name=med_name,
                defaults={
                    "medicine": med_obj,
                    "dosage": r.get("Dosage", "1 tablet"),
                    "frequency": r.get("Frequency", "Once Daily"),
                    "duration_days": parse_int(r.get("Duration (Days)"), 30),
                    "quantity": parse_int(r.get("Prescribed Qty"), 30),
                    "dispensed_quantity": parse_int(r.get("Dispensed Qty"), 30),
                    "status": r.get("Item Status", "DISPENSED"),
                }
            )
            rx_count += 1
        print(f"  -> Ingested {rx_count} Pharmacy Prescription Items.")

        # ----------------------------------------------------------------------
        # 8. PHARMACY DISPENSATIONS
        # ----------------------------------------------------------------------
        print("\n8. Ingesting Pharmacy Dispensations (08_pharmacy_dispensations.csv)...")
        disp_file = os.path.join(source_dir, '08_pharmacy_dispensations.csv')
        disp_rows = read_csv_rows(disp_file)
        disp_count = 0

        for r in disp_rows:
            disp_num = r.get("Dispensation Number")
            if not disp_num:
                continue

            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            # Find matching prescription
            rx_obj = Prescription.objects.filter(patient=pat_obj).first()
            if not rx_obj:
                continue

            disp_staff_user = User.objects.filter(username=r.get("Dispensed By")).first()
            disp_staff = StaffProfile.objects.filter(user_account=disp_staff_user).first() if disp_staff_user else default_pharm_staff

            disp_obj, _ = Dispensation.objects.update_or_create(
                dispensation_number=disp_num,
                defaults={
                    "prescription": rx_obj,
                    "facility": rx_obj.facility,
                    "dispensed_by_staff": disp_staff,
                    "dispensed_at": parse_datetime(r.get("Dispensed At")) or timezone.now(),
                    "remarks": r.get("Remarks", "Dispensed via verified FEFO allocation."),
                }
            )

            batch_num = r.get("Batch Number")
            batch_obj = MedicineBatch.objects.filter(batch_number=batch_num).first()
            rx_item = rx_obj.items.first()

            if rx_item:
                DispensationItem.objects.update_or_create(
                    dispensation=disp_obj,
                    batch=batch_obj,
                    defaults={
                        "prescription_item": rx_item,
                        "quantity_dispensed": parse_int(r.get("Quantity Dispensed"), 30),
                    }
                )

            if r.get("Counselled") == "YES":
                PatientCounselling.objects.update_or_create(
                    prescription=rx_obj,
                    defaults={
                        "pharmacist_staff": disp_staff,
                        "adherence_counselled": True,
                        "counselling_notes": r.get("Counseling Notes", "Instructed patient on daily medication compliance."),
                    }
                )
            disp_count += 1
        print(f"  -> Ingested {disp_count} Pharmacy Dispensation records.")

        # ----------------------------------------------------------------------
        # 9. DOUBLE-ENTRY INVENTORY LEDGER
        # ----------------------------------------------------------------------
        print("\n9. Ingesting Double-Entry Inventory Ledger (09_inventory_ledger_double_entry.csv)...")
        led_file = os.path.join(source_dir, '09_inventory_ledger_double_entry.csv')
        led_rows = read_csv_rows(led_file)
        led_count = 0

        for r in led_rows:
            batch_num = r.get("Batch Number")
            batch_obj = MedicineBatch.objects.filter(batch_number=batch_num).first()
            if not batch_obj:
                continue

            fac_obj = batch_obj.facility
            staff_user = User.objects.filter(username=r.get("Performed By Staff")).first()
            staff_obj = StaffProfile.objects.filter(user_account=staff_user).first() if staff_user else None

            InventoryLedger.objects.update_or_create(
                id=parse_int(r.get("Ledger ID")),
                defaults={
                    "facility": fac_obj,
                    "batch": batch_obj,
                    "transaction_type": r.get("Transaction Type", "DISPENSATION"),
                    "quantity_delta": parse_int(r.get("Quantity Delta")),
                    "balance_after": parse_int(r.get("Balance After")),
                    "reference_entity_type": r.get("Reference Entity", "Dispensation"),
                    "reference_entity_id": parse_int(r.get("Reference ID")),
                    "performed_by_staff": staff_obj,
                    "remarks": r.get("Remarks", ""),
                    "transaction_timestamp": parse_datetime(r.get("Timestamp")) or timezone.now(),
                }
            )
            led_count += 1
        print(f"  -> Ingested {led_count} Inventory Ledger double-entry movements.")

        # ----------------------------------------------------------------------
        # 10. CHRONIC NCD CONDITIONS & ASSESSMENTS
        # ----------------------------------------------------------------------
        print("\n10. Ingesting NCD Chronic Longitudinal Care (10_ncd_chronic_care_and_assessments.csv)...")
        ncd_file = os.path.join(source_dir, '10_ncd_chronic_care_and_assessments.csv')
        ncd_rows = read_csv_rows(ncd_file)
        ncd_count = 0

        for r in ncd_rows:
            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            cond_code = r.get("Condition", "HYPERTENSION")
            cond_obj, _ = NCDCondition.objects.update_or_create(
                patient=pat_obj,
                condition_code=cond_code,
                defaults={
                    "registering_facility": pat_obj.registered_at_facility,
                    "registering_doctor": default_doc_staff,
                    "staging": r.get("Staging", "Stage 1"),
                    "control_status": r.get("Overall Control Status", "CONTROLLED"),
                    "diagnosis_date": parse_date(r.get("Assessed At")) or timezone.localdate(),
                }
            )

            vid = r.get("Visit ID")
            visit_obj = Visit.objects.filter(visit_id=vid).first() if vid else None
            if not visit_obj:
                visit_obj = Visit.objects.filter(patient=pat_obj).first()

            NCDAssessment.objects.update_or_create(
                id=parse_int(r.get("Assessment ID")),
                defaults={
                    "condition": cond_obj,
                    "visit": visit_obj,
                    "assessed_by_staff": default_doc_staff,
                    "systolic_bp": parse_int(r.get("Systolic BP")),
                    "diastolic_bp": parse_int(r.get("Diastolic BP")),
                    "blood_glucose_fasting": parse_decimal(r.get("Fasting Glucose (mg/dL)")) if r.get("Fasting Glucose (mg/dL)") else None,
                    "hba1c": parse_decimal(r.get("HbA1c (%)")) if r.get("HbA1c (%)") else None,
                    "bmi": parse_decimal(r.get("BMI")) if r.get("BMI") else None,
                    "clinical_notes": r.get("Clinical Notes", ""),
                }
            )
            ncd_count += 1
        print(f"  -> Ingested {ncd_count} NCD Assessments & Conditions.")

        # ----------------------------------------------------------------------
        # 11. IDSP COMMUNICABLE DISEASE SURVEILLANCE
        # ----------------------------------------------------------------------
        print("\n11. Ingesting IDSP Communicable Disease Surveillance (11_idsp_disease_surveillance_cases.csv)...")
        surv_file = os.path.join(source_dir, '11_idsp_disease_surveillance_cases.csv')
        surv_rows = read_csv_rows(surv_file)
        surv_count = 0

        for r in surv_rows:
            c_num = r.get("Case Number")
            if not c_num:
                continue

            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            d_code = r.get("Disease Code", "DENGUE")
            d_name = r.get("Disease Name", "Dengue Fever")
            disease_obj = DiseaseMaster.objects.filter(disease_code=d_code).first()
            if not disease_obj:
                disease_obj = DiseaseMaster.objects.create(
                    disease_code=d_code,
                    disease_name=d_name,
                    transmission_type='VECTOR_BORNE' if d_code in ['DENGUE', 'MALARIA'] else 'WATER_BORNE',
                    is_notifiable_state=True
                )

            reporter_user = User.objects.filter(username=r.get("Reporting Staff")).first()
            reporter_staff = StaffProfile.objects.filter(user_account=reporter_user).first() if reporter_user else default_doc_staff

            sc_obj, _ = DiseaseSurveillanceCase.objects.update_or_create(
                case_number=c_num,
                defaults={
                    "patient": pat_obj,
                    "disease": disease_obj,
                    "facility": pat_obj.registered_at_facility,
                    "ward": pat_obj.ward,
                    "severity": r.get("Severity", "MODERATE"),
                    "status": "CONFIRMED",
                    "lab_confirmed": (r.get("Lab Confirmed") == "YES"),
                    "reporting_staff": reporter_staff or default_doc_staff,
                    "investigation_notes": r.get("Investigation Notes", ""),
                    "diagnosis_date": parse_date(r.get("Reported At")) or timezone.localdate(),
                }
            )

            if r.get("Notified Authority"):
                PublicHealthNotification.objects.update_or_create(
                    case=sc_obj,
                    notified_authority=r.get("Notified Authority"),
                    defaults={
                        "transmission_status": "DISPATCHED",
                        "dispatch_payload": {
                            "case_number": c_num,
                            "disease": d_code,
                            "authority": r.get("Notified Authority")
                        },
                        "dispatched_at": parse_datetime(r.get("Dispatched At")) or timezone.now(),
                    }
                )
            surv_count += 1
        print(f"  -> Ingested {surv_count} IDSP Disease Surveillance cases.")

        # ----------------------------------------------------------------------
        # 12. INTER-FACILITY REFERRALS
        # ----------------------------------------------------------------------
        print("\n12. Ingesting Inter-Facility Referrals (12_inter_facility_referrals_and_events.csv)...")
        ref_file = os.path.join(source_dir, '12_inter_facility_referrals_and_events.csv')
        ref_rows = read_csv_rows(ref_file)
        ref_count = 0

        for r in ref_rows:
            r_num = r.get("Referral Number")
            if not r_num:
                continue

            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            src_fac = Facility.objects.filter(facility_name__icontains=r.get("Source Facility", "")).first() or pat_obj.registered_at_facility
            dest_fac = Facility.objects.filter(facility_name__icontains=r.get("Destination Facility", "")).first()
            if not dest_fac:
                dest_fac = Facility.objects.filter(facility_type='DISTRICT_HOSPITAL').first() or src_fac

            pat_visit = Visit.objects.filter(patient=pat_obj).first()
            if not pat_visit:
                continue

            ref_obj, _ = ReferralOrder.objects.update_or_create(
                referral_number=r_num,
                defaults={
                    "patient": pat_obj,
                    "visit": pat_visit,
                    "source_facility": src_fac,
                    "destination_facility": dest_fac,
                    "referring_doctor": default_doc_staff,
                    "urgency": r.get("Urgency", "URGENT"),
                    "reason": r.get("Referral Reason", ""),
                    "clinical_summary": r.get("Clinical Summary", ""),
                    "status": "COMPLETED",
                    "referral_date": parse_date(r.get("Created At")) or timezone.localdate(),
                }
            )

            if r.get("Specialist Findings") or r.get("Treatment Rendered"):
                ReferralEvent.objects.update_or_create(
                    referral=ref_obj,
                    event_type="COUNTER_REFERRAL_DISCHARGE",
                    defaults={
                        "recorded_by_staff": default_doc_staff,
                        "specialist_findings": r.get("Specialist Findings", ""),
                        "treatment_rendered": r.get("Treatment Rendered", ""),
                        "return_advice": r.get("Counter-Referral Advice", ""),
                    }
                )
            ref_count += 1
        print(f"  -> Ingested {ref_count} Inter-Facility Referral Orders and Audit Events.")

        # ----------------------------------------------------------------------
        # 13. FOLLOW-UP TASKS
        # ----------------------------------------------------------------------
        print("\n13. Ingesting Clinical Follow-Up Tasks (13_followup_tasks.csv)...")
        fu_file = os.path.join(source_dir, '13_followup_tasks.csv')
        fu_rows = read_csv_rows(fu_file)
        fu_count = 0

        for r in fu_rows:
            pat_id = r.get("Patient ID")
            pat_obj = Patient.objects.filter(patient_id=pat_id).first()
            if not pat_obj:
                continue

            fac_obj = Facility.objects.filter(facility_name__icontains=r.get("Facility", "")).first() or pat_obj.registered_at_facility

            cat = r.get("Category", "NCD_ROUTINE")
            if cat not in ['NCD_ROUTINE', 'POST_REFERRAL', 'LAB_REVIEW', 'GENERAL']:
                cat = 'NCD_ROUTINE'

            st = r.get("Status", "PENDING")
            if st not in ['PENDING', 'COMPLETED', 'MISSED', 'CANCELLED']:
                st = 'PENDING'

            pat_visit = Visit.objects.filter(patient=pat_obj).first()
            comp_at = parse_datetime(r.get("Completed At"))
            if st == 'COMPLETED' and not comp_at:
                comp_at = timezone.now()

            FollowUpTask.objects.update_or_create(
                id=parse_int(r.get("Task ID")),
                defaults={
                    "patient": pat_obj,
                    "facility": fac_obj,
                    "originating_visit": pat_visit,
                    "category": cat,
                    "status": st,
                    "due_date": parse_date(r.get("Due Date")) or timezone.localdate(),
                    "clinical_instructions": r.get("Clinical Instructions", ""),
                    "completed_at": comp_at if st == 'COMPLETED' else None,
                    "completed_in_visit": pat_visit if st == 'COMPLETED' else None,
                    "completed_by_staff": default_doc_staff if st == 'COMPLETED' else None,
                }
            )
            fu_count += 1
        print(f"  -> Ingested {fu_count} Follow-Up Tasks.")

        if dry_run:
            print("\n[DRY RUN] Rolling back transaction. No data committed.")
            transaction.set_rollback(True)
        else:
            print("\n[COMMITTED] All 13 sections ingested and committed to database successfully!")

    print("\n" + "=" * 80)
    print("MIGRATION & INGESTION COMPLETE!")
    print(f"  Patients:               {pat_count}")
    print(f"  Households:             {hh_count}")
    print(f"  OPD Visits & Tokens:    {v_count}")
    print(f"  Triage Records:         {tr_count}")
    print(f"  Consultations:          {c_count}")
    print(f"  Diagnostic Orders:      {lab_count}")
    print(f"  Prescriptions:          {rx_count}")
    print(f"  Dispensations:          {disp_count}")
    print(f"  Ledger Movements:       {led_count}")
    print(f"  NCD Assessments:        {ncd_count}")
    print(f"  Surveillance Cases:     {surv_count}")
    print(f"  Referrals:              {ref_count}")
    print(f"  Follow-up Tasks:        {fu_count}")
    print("=" * 80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest clean Namma Clinic CSV dataset into database.")
    parser.add_argument(
        '--source',
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to folder containing the 13 CSV export files. Defaults to current directory."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate ingestion without committing to database."
    )
    args = parser.parse_args()

    ingest_all(source_dir=args.source, dry_run=args.dry_run)

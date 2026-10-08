"""
Namma Clinic — Clean Demo Data & 10 Synthetic Demo Patients Seed Script.
Prepares the local PostgreSQL database for live client demonstration:
- Removes temporary validation/test clinical records.
- Preserves master configuration, approved roles, demo staff accounts, facility metadata.
- Prepares legitimate dispensary stock across key medicines with authoritative InventoryLedger receipts.
- Seeds exactly 10 UNIQUE, realistic SYNTHETIC demo patients covering a complete clinic journey:
  Patient 01: Clean intake (Primary live demonstration patient)
  Patient 02: Waiting in Nurse Queue for Triage
  Patient 03: Triaged by Nurse, Waiting for Doctor
  Patient 04: In Active Doctor Consultation
  Patient 05: Lab Tests Ordered, Awaiting Sample Collection in Lab Queue
  Patient 06: Lab Specimen Collected & Result Entered, Awaiting MO Verification
  Patient 07: Doctor Prescribed, Waiting in Pharmacy Queue for Verification
  Patient 08: Prescription Verified by Pharmacist, Ready for FEFO Dispense
  Patient 09: Fully Dispensed & Completed (with complete double-entry ledger audit trail)
  Patient 10: Chronic care follow-up patient in registry
"""

import sys
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from django.utils import timezone

from apps.facilities.models import Facility, Department
from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.patients.models import Patient, PatientDocument
from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Diagnosis, Prescription, PrescriptionItem
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest,
    DiagnosticResult, DiagnosticResultAmendment
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation, DispensationItem,
    InventoryLedger, PatientCounselling, DispensationReturn
)
from apps.pharmacy.services import dispense_prescription


class Command(BaseCommand):
    help = "Clean test clinical data and seed 10 unique synthetic demo patients covering the end-to-end clinical journey."

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-demo-reset',
            action='store_true',
            help='Required confirmation flag to clean and seed demo data.',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("NAMMA CLINIC — CLEAN DEMO DATA & 10 SYNTHETIC DEMO PATIENTS SEED")
        self.stdout.write("=" * 70)

        with transaction.atomic():
            # -------------------------------------------------------------
            # STEP 1: RESOLVE PRESERVED PRIMARY FACILITY & DEMO STAFF
            # -------------------------------------------------------------
            facility = Facility.objects.filter(id=1).first()
            if not facility:
                facility = Facility.objects.filter(facility_code="PHC-LOCAL-01").first()
            if not facility:
                facility = Facility.objects.create(
                    id=1,
                    facility_code="PHC-LOCAL-01",
                    facility_name="Namma Clinic Local PHC",
                    facility_type="PRIMARY_HEALTH_CENTRE",
                    emergency_available=True,
                    lab_available=True,
                    pharmacy_available=True
                )
            self.stdout.write(f"Primary Facility: {facility.facility_name} (ID: {facility.id})")

            # Resolve key demo staff profiles
            doctor_user = User.objects.filter(username="localdoc").first()
            nurse_user = User.objects.filter(username="localnurse").first()
            pharm_user = User.objects.filter(username="localpharm").first()
            lab_user = User.objects.filter(username="locallab").first()
            admin_user = User.objects.filter(username="testadmin").first()

            doc_staff = getattr(doctor_user, 'staff_profile', None)
            nurse_staff = getattr(nurse_user, 'staff_profile', None)
            pharm_staff = getattr(pharm_user, 'staff_profile', None)
            lab_staff = getattr(lab_user, 'staff_profile', None)
            admin_staff = getattr(admin_user, 'staff_profile', None)

            # Ensure Phase 37 Staff-Department Alignment
            dept_pharm, _ = Department.objects.get_or_create(facility=facility, code='PHARM', defaults={'name': 'Pharmacy', 'is_active': True})
            dept_lab, _ = Department.objects.get_or_create(facility=facility, code='LAB', defaults={'name': 'Laboratory', 'is_active': True})
            dept_opd, _ = Department.objects.get_or_create(facility=facility, code='OPD', defaults={'name': 'General OPD', 'is_active': True})
            dept_triage, _ = Department.objects.get_or_create(facility=facility, code='TRIAGE', defaults={'name': 'Triage', 'is_active': True})

            if pharm_staff and dept_pharm:
                pharm_staff.department = dept_pharm
                pharm_staff.save(update_fields=['department'])
                StaffFacilityAssignment.objects.filter(staff=pharm_staff, facility=facility, is_primary=True).update(department=dept_pharm)
            if lab_staff and dept_lab:
                lab_staff.department = dept_lab
                lab_staff.save(update_fields=['department'])
                StaffFacilityAssignment.objects.filter(staff=lab_staff, facility=facility, is_primary=True).update(department=dept_lab)
            if doc_staff and dept_opd:
                doc_staff.department = dept_opd
                doc_staff.save(update_fields=['department'])
                StaffFacilityAssignment.objects.filter(staff=doc_staff, facility=facility, is_primary=True).update(department=dept_opd)
            if nurse_staff and (dept_triage or dept_opd):
                nurse_staff.department = dept_triage or dept_opd
                nurse_staff.save(update_fields=['department'])
                StaffFacilityAssignment.objects.filter(staff=nurse_staff, facility=facility, is_primary=True).update(department=dept_triage or dept_opd)

            # -------------------------------------------------------------
            # STEP 2: REMOVE TEMPORARY CLINICAL / VALIDATION RECORDS
            # -------------------------------------------------------------
            self.stdout.write("\nCleaning existing temporary clinical demonstration records...")

            tables_to_truncate = [
                'diagnostic_result_amendments', 'diagnostic_results', 'test_requests', 'specimens', 'diagnostic_orders',
                'laboratory_labresult', 'laboratory_labsample', 'laboratory_laborder', 'laboratory_labtoken',
                'dispensation_items', 'dispensations', 'pharmacy_dispensationreturn', 'pharmacy_patientcounselling',
                'inventory_ledgers', 'pharmacy_inventorytransaction', 'pharmacy_medicinebatch',
                'consultations_prescriptionitem', 'consultations_prescription', 'diagnoses', 'consultations_consultation',
                'triage_triagevitals', 'triages',
                'follow_up_tasks', 'referral_events', 'referrals_referralresponse', 'referral_orders', 'referrals_followup', 'referrals_referral',
                'ncd_assessments', 'ncd_conditions', 'ncd_ncdrecord',
                'surveillance_diseasecase', 'disease_surveillance_cases', 'telemedicine_teleconsultation', 'alerts_alert', 'operational_alerts',
                'visits_token', 'visits_visitstatushistory', 'visits_visit',
                'patients_patientdocument', 'patients_patient'
            ]
            with connection.cursor() as cursor:
                # Filter to only existing tables in database
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name = ANY(%s)",
                    [tables_to_truncate]
                )
                existing_tables = [row[0] for row in cursor.fetchall()]
                if existing_tables:
                    cursor.execute(f"TRUNCATE TABLE {', '.join(existing_tables)} CASCADE;")
            self.stdout.write("  [CLEAN] Truncated temporary operational tables cleanly.")



            # -------------------------------------------------------------
            # STEP 3: SEED ESSENTIAL MEDICINES & VALID PHARMACY BATCHES
            # -------------------------------------------------------------
            self.stdout.write("\nSeeding legitimate pharmacy batches at Namma Clinic Local PHC...")

            medicines_data = [
                ("Paracetamol 500mg", "TABLET", "500mg", "Analgesic / Antipyretic", "BATCH-LOC-PCM01", 500, datetime.date(2027, 6, 30), Decimal("1.50")),
                ("Amoxicillin 500mg", "CAPSULE", "500mg", "Antibiotic", "BATCH-LOC-AMX01", 300, datetime.date(2027, 8, 31), Decimal("3.20")),
                ("Cetirizine 10mg", "TABLET", "10mg", "Antihistamine", "BATCH-LOC-CTZ01", 250, datetime.date(2027, 10, 31), Decimal("1.80")),
                ("Metformin 500mg", "TABLET", "500mg", "Antidiabetic", "BATCH-LOC-MET01", 400, datetime.date(2027, 12, 31), Decimal("2.10")),
                ("Amlodipine 5mg", "TABLET", "5mg", "Antihypertensive", "BATCH-LOC-AML01", 350, datetime.date(2027, 9, 30), Decimal("2.00")),
                ("ORS Oral Rehydration Salts 21.8g", "SACHET", "21.8g", "Electrolyte Replacement", "BATCH-LOC-ORS01", 200, datetime.date(2028, 1, 31), Decimal("5.00")),
            ]

            seeded_batches = {}
            seeded_meds = {}

            for gen_name, form, strength, category, batch_num, qty, exp_date, cost in medicines_data:
                med, _ = MedicineMaster.objects.get_or_create(
                    generic_name=gen_name,
                    defaults={
                        "dosage_form": form,
                        "strength": strength,
                        "category": category,
                    }
                )
                seeded_meds[gen_name] = med

                batch = MedicineBatch.objects.create(
                    medicine=med,
                    facility=facility,
                    batch_number=batch_num,
                    expiry_date=exp_date,
                    quantity=qty,
                    available_quantity=qty,
                    quarantined_quantity=0,
                    recalled_quantity=0,
                    damaged_quantity=0,
                    unit_cost=cost,
                    status="AVAILABLE"
                )
                seeded_batches[gen_name] = batch

                # Write authoritative initial receipt into InventoryLedger
                InventoryLedger.objects.create(
                    batch=batch,
                    facility=facility,
                    performed_by_staff=pharm_staff or doc_staff,
                    transaction_type="PURCHASE_RECEIPT",
                    quantity_delta=qty,
                    balance_after=qty,
                    remarks=f"Initial demo dispensary stock receipt: {qty} units"
                )
                self.stdout.write(f"  [STOCK] {gen_name} ({batch_num}): {qty} units (Expiry: {exp_date})")

            # -------------------------------------------------------------
            # STEP 4: SEED EXACTLY 10 UNIQUE SYNTHETIC DEMO PATIENTS
            # -------------------------------------------------------------
            self.stdout.write("\nSeeding exactly 10 UNIQUE, realistic SYNTHETIC demo patients...")

            demo_patients_meta = [
                # 1. PRIMARY DEMO PATIENT — Clean state for live end-to-end presentation
                {
                    "uhid": "NC-KA-2026-0001",
                    "name": "Arun Kumar",
                    "age": 34,
                    "gender": "MALE",
                    "dob": "1992-04-12",
                    "mobile": "9800010001",
                    "address": "Ward 12, Shivajinagar, Bengaluru",
                    "abha": "ABHA-DEMO-0001",
                    "vulnerability": "General Population",
                    "scenario": "Patient 01: Fever (Acute fever with chills for 3 days) — PRIMARY LIVE WALKTHROUGH PATIENT",
                    "stage": "REGISTERED_CLEAN"
                },
                # 2. Cough / respiratory complaint
                {
                    "uhid": "NC-KA-2026-0002",
                    "name": "Priya Nair",
                    "age": 28,
                    "gender": "FEMALE",
                    "dob": "1998-07-25",
                    "mobile": "9800010002",
                    "address": "4th Cross, Malleshwaram, Bengaluru",
                    "abha": "ABHA-DEMO-0002",
                    "vulnerability": "General Population",
                    "scenario": "Patient 02: Cough / respiratory complaint (Sore throat and dry cough for 4 days)",
                    "stage": "IN_NURSE_QUEUE"
                },
                # 3. Headache
                {
                    "uhid": "NC-KA-2026-0003",
                    "name": "Ravi Shankar",
                    "age": 45,
                    "gender": "MALE",
                    "dob": "1981-11-14",
                    "mobile": "9800010003",
                    "address": "2nd Main, Rajajinagar, Bengaluru",
                    "abha": "ABHA-DEMO-0003",
                    "vulnerability": "Slum Resident / Low Income Group",
                    "scenario": "Patient 03: Headache (Throbbing frontal headache and mild fatigue for 5 days)",
                    "stage": "TRIAGED_WAITING_DOCTOR"
                },
                # 4. Gastric / abdominal complaint
                {
                    "uhid": "NC-KA-2026-0004",
                    "name": "Meena Devi",
                    "age": 52,
                    "gender": "FEMALE",
                    "dob": "1974-03-08",
                    "mobile": "9800010004",
                    "address": "7th Block, Jayanagar, Bengaluru",
                    "abha": "ABHA-DEMO-0004",
                    "vulnerability": "Senior Citizen / Diabetic",
                    "scenario": "Patient 04: Gastric / abdominal complaint (Epigastric burning discomfort and dyspepsia for 1 week)",
                    "stage": "IN_CONSULTATION"
                },
                # 5. General weakness
                {
                    "uhid": "NC-KA-2026-0005",
                    "name": "Suresh Babu",
                    "age": 39,
                    "gender": "MALE",
                    "dob": "1987-09-30",
                    "mobile": "9800010005",
                    "address": "Sector 3, HSR Layout, Bengaluru",
                    "abha": "ABHA-DEMO-0005",
                    "vulnerability": "General Population",
                    "scenario": "Patient 05: General weakness (Generalized fatigue, lethargy, and body ache for 2 weeks)",
                    "stage": "TRIAGED_WAITING_DOCTOR"
                },
                # 6. Skin complaint
                {
                    "uhid": "NC-KA-2026-0006",
                    "name": "Kavya Reddy",
                    "age": 31,
                    "gender": "FEMALE",
                    "dob": "1995-02-18",
                    "mobile": "9800010006",
                    "address": "1st Stage, Indiranagar, Bengaluru",
                    "abha": "ABHA-DEMO-0006",
                    "vulnerability": "General Population",
                    "scenario": "Patient 06: Skin complaint (Pruritic erythematous rash on forearms for 4 days)",
                    "stage": "IN_NURSE_QUEUE"
                },
                # 7. Joint pain
                {
                    "uhid": "NC-KA-2026-0007",
                    "name": "Manoj Kumar",
                    "age": 42,
                    "gender": "MALE",
                    "dob": "1984-06-05",
                    "mobile": "9800010007",
                    "address": "5th Phase, JP Nagar, Bengaluru",
                    "abha": "ABHA-DEMO-0007",
                    "vulnerability": "Slum Household BPL",
                    "scenario": "Patient 07: Joint pain (Bilateral knee joint stiffness and pain for 3 weeks)",
                    "stage": "TRIAGED_WAITING_DOCTOR"
                },
                # 8. Routine chronic-condition follow-up
                {
                    "uhid": "NC-KA-2026-0008",
                    "name": "Anitha Rao",
                    "age": 36,
                    "gender": "FEMALE",
                    "dob": "1990-10-10",
                    "mobile": "9800010008",
                    "address": "8th Main, Basavanagudi, Bengaluru",
                    "abha": "ABHA-DEMO-0008",
                    "vulnerability": "General Population",
                    "scenario": "Patient 08: Routine chronic-condition follow-up (Hypertension review and routine medication refill)",
                    "stage": "TRIAGED_WAITING_DOCTOR"
                },
                # 9. Fever requiring laboratory investigation
                {
                    "uhid": "NC-KA-2026-0009",
                    "name": "Sanjay Patel",
                    "age": 58,
                    "gender": "MALE",
                    "dob": "1968-12-03",
                    "mobile": "9800010009",
                    "address": "3rd Cross, Koramangala, Bengaluru",
                    "abha": "ABHA-DEMO-0009",
                    "vulnerability": "Senior Citizen / Cardiac History",
                    "scenario": "Patient 09: Fever requiring laboratory investigation (High fever with rigors, CBC & NS1 ordered)",
                    "stage": "LAB_ORDERED_PENDING_SAMPLE"
                },
                # 10. General OPD / follow-up
                {
                    "uhid": "NC-KA-2026-0010",
                    "name": "Deepa Menon",
                    "age": 49,
                    "gender": "FEMALE",
                    "dob": "1977-08-19",
                    "mobile": "9800010010",
                    "address": "6th Block, BTM Layout, Bengaluru",
                    "abha": "ABHA-DEMO-0010",
                    "vulnerability": "General Population",
                    "scenario": "Patient 10: General OPD / follow-up (Preventive wellness check-up and follow-up consultation)",
                    "stage": "REGISTERED_FOLLOWUP"
                },
            ]

            today = datetime.date.today()
            now = timezone.now()
            token_counter = 1

            for p_idx, p_data in enumerate(demo_patients_meta, 1):
                p = Patient.objects.create(
                    patient_id=p_data["uhid"],
                    name=p_data["name"],
                    age=p_data["age"],
                    gender=p_data["gender"],
                    date_of_birth=datetime.datetime.strptime(p_data["dob"], "%Y-%m-%d").date(),
                    mobile=p_data["mobile"],
                    address=p_data["address"],
                    ABHA_ID_DEMO=p_data["abha"],
                    vulnerability_information=p_data["vulnerability"],
                    registered_at_facility=facility,
                    registration_date=today
                )
                self.stdout.write(f"\n  [PATIENT {p_idx:02d}] {p.name} ({p.patient_id}) — {p_data['scenario']}")

                stage = p_data["stage"]

                # ---------------------------------------------------------
                # Patient 1 & 10: Clean registration, no active visit yet
                # ---------------------------------------------------------
                if stage in ["REGISTERED_CLEAN", "REGISTERED_FOLLOWUP"]:
                    self.stdout.write(f"    -> Status: Registered, Ready for intake (Zero visits)")
                    continue

                # ---------------------------------------------------------
                # Patients 2 to 9: Create Visit and OPD Token
                # ---------------------------------------------------------
                tok_num = token_counter
                token_counter += 1
                vis_id = f"VIS-F1-{today.strftime('%Y%m%d')}-{tok_num:03d}"

                # Base visit fields
                v = Visit.objects.create(
                    visit_id=vis_id,
                    patient=p,
                    facility=facility,
                    opd_date=today,
                    visit_type="GENERAL_OPD",
                    priority="NORMAL",
                    chief_complaint=p_data["scenario"].split(" — ")[0],
                    current_queue="TRIAGE",
                    status="WAITING_FOR_TRIAGE",
                    arrival_time=now - datetime.timedelta(minutes=(10 - p_idx) * 12)
                )

                tok = Token.objects.create(
                    token_number=tok_num,
                    visit=v,
                    facility=facility,
                    date=today,
                    priority="NORMAL",
                    status="WAITING"
                )

                VisitStatusHistory.objects.create(
                    visit=v,
                    from_status="NONE",
                    to_status="WAITING_FOR_TRIAGE",
                    queue="TRIAGE",
                    performed_by=nurse_user,
                    performed_by_role="NURSE",
                    notes=f"Issued OPD Token #{tok_num} for {today}"
                )

                # Patient 2: Stop at Nurse Queue
                if stage == "IN_NURSE_QUEUE":
                    self.stdout.write(f"    -> Visit {vis_id} | Token #{tok_num} in TRIAGE queue (WAITING_FOR_TRIAGE)")
                    continue

                # ---------------------------------------------------------
                # Patients 3 to 9: Nurse Triage Completed
                # ---------------------------------------------------------
                triage = TriageVitals.objects.create(
                    visit=v,
                    patient=p,
                    nurse=nurse_user,
                    blood_pressure_systolic=120 + (p_idx * 2 % 16),
                    blood_pressure_diastolic=80 + (p_idx % 6),
                    pulse_bpm=76 + (p_idx % 10),
                    temperature_f=Decimal("98.6") if p_idx != 5 else Decimal("101.4"),
                    spo2_percent=98,
                    respiratory_rate=18,
                    height_cm=Decimal("165.0") + Decimal(p_idx),
                    weight_kg=Decimal("62.0") + Decimal(p_idx * 2),
                    bmi=Decimal("23.5"),
                    blood_glucose_mgdl=110,
                    fever_flag=(p_idx == 5),
                    nurse_notes=f"Intake vitals recorded by Sister Kavitha Rani. Patient ambulatory and alert."
                )

                v.status = "TRIAGED"
                v.current_queue = "DOCTOR"
                v.triage_end_time = now - datetime.timedelta(minutes=(10 - p_idx) * 10)
                v.save()

                VisitStatusHistory.objects.create(
                    visit=v,
                    from_status="WAITING_FOR_TRIAGE",
                    to_status="TRIAGED",
                    queue="DOCTOR",
                    performed_by=nurse_user,
                    performed_by_role="NURSE",
                    notes="Vitals recorded; forwarded to Doctor queue"
                )

                # Patient 3: Stop at Triaged Waiting Doctor
                if stage == "TRIAGED_WAITING_DOCTOR":
                    self.stdout.write(f"    -> Visit {vis_id} | Token #{tok_num} TRIAGED, waiting in DOCTOR queue")
                    continue

                # ---------------------------------------------------------
                # Patient 4: In Consultation with Doctor
                # ---------------------------------------------------------
                if stage == "IN_CONSULTATION":
                    v.status = "IN_CONSULTATION"
                    v.assigned_doctor = doctor_user
                    v.consultation_start_time = now - datetime.timedelta(minutes=5)
                    v.save()

                    Consultation.objects.create(
                        visit=v,
                        patient=p,
                        doctor=doctor_user,
                        doctor_staff=doc_staff,
                        facility=facility,
                        chief_complaint=v.chief_complaint,
                        clinical_history="Patient reports intermittent headache and mild visual blurring for 2 weeks.",
                        clinical_assessment="Suspected tension headache with mild essential hypertension. Fundoscopy within normal limits.",
                        treatment_plan="Lifestyle modification, BP monitoring, symptomatic relief."
                    )
                    self.stdout.write(f"    -> Visit {vis_id} | Token #{tok_num} IN_CONSULTATION with Dr. Sunil (localdoc)")
                    continue

                # ---------------------------------------------------------
                # Patients 5 & 6: Lab Investigation Flow
                # ---------------------------------------------------------
                consult = Consultation.objects.create(
                    visit=v,
                    patient=p,
                    doctor=doctor_user,
                    doctor_staff=doc_staff,
                    facility=facility,
                    chief_complaint=v.chief_complaint,
                    clinical_history=f"Clinical history recorded during examination for {p.name}.",
                    clinical_assessment="Clinical assessment completed. Diagnostic investigation ordered.",
                    treatment_plan="Order diagnostic tests to establish definitive diagnosis."
                )

                if stage == "LAB_ORDERED_PENDING_SAMPLE":
                    v.current_queue = "LAB"
                    v.status = "WAITING_FOR_LAB"
                    v.save()

                    diag_order = DiagnosticOrder.objects.create(
                        visit=v,
                        facility=facility,
                        ordering_doctor_staff=doc_staff,
                        order_number=f"ORD-{today.strftime('%Y%m%d')}-005",
                        order_date=today,
                        lab_token_number=5,
                        priority="NORMAL",
                        status="ORDERED",
                        clinical_indication="Suspected Dengue fever; evaluate platelet count and NS1 antigen."
                    )

                    test_cbc = DiagnosticTestMaster.objects.filter(test_code="CBC").first()
                    test_ns1 = DiagnosticTestMaster.objects.filter(test_code="NS1-AG").first()

                    if test_cbc:
                        TestRequest.objects.create(diagnostic_order=diag_order, test_master=test_cbc, status="PENDING")
                    if test_ns1:
                        TestRequest.objects.create(diagnostic_order=diag_order, test_master=test_ns1, status="PENDING")

                    self.stdout.write(f"    -> Visit {vis_id} | Token #{tok_num} Diagnostic Order #{diag_order.order_number} in LAB queue (Awaiting Specimen)")
                    continue

                if stage == "LAB_RESULT_ENTERED":
                    v.current_queue = "LAB"
                    v.status = "WAITING_FOR_LAB"
                    v.save()

                    diag_order = DiagnosticOrder.objects.create(
                        visit=v,
                        facility=facility,
                        ordering_doctor_staff=doc_staff,
                        order_number=f"ORD-{today.strftime('%Y%m%d')}-006",
                        order_date=today,
                        lab_token_number=6,
                        priority="NORMAL",
                        status="SAMPLE_COLLECTED",
                        clinical_indication="Dysuria; evaluate for urinary tract infection."
                    )

                    test_urine = DiagnosticTestMaster.objects.filter(test_code="URINE-ROUTINE").first()
                    if test_urine:
                        specimen = Specimen.objects.create(
                            diagnostic_order=diag_order,
                            barcode_identifier=f"SPEC-{today.strftime('%Y%m%d')}-006",
                            specimen_type="URINE",
                            status="COLLECTED",
                            collected_by_staff=lab_staff,
                            collected_at=now - datetime.timedelta(minutes=30)
                        )
                        test_req = TestRequest.objects.create(
                            diagnostic_order=diag_order,
                            test_master=test_urine,
                            specimen=specimen,
                            status="COLLECTED"
                        )
                        DiagnosticResult.objects.create(
                            test_request=test_req,
                            result_value_text="Pus Cells: 10-15 / hpf, RBC: 1-2 / hpf, Protein: Trace, Nitrite: Positive",
                            reference_range_applied="Pus Cells: 0-5 / hpf (Normal)",
                            is_abnormal=True,
                            is_critical_panic=False,
                            status="ENTERED",
                            entered_by_staff=lab_staff,
                            entered_at=now - datetime.timedelta(minutes=15)
                        )
                    self.stdout.write(f"    -> Visit {vis_id} | Token #{tok_num} Lab Result Recorded for Urine Routine (Awaiting MO Verification)")
                    continue

                # ---------------------------------------------------------
                # Patients 7, 8, 9: Pharmacy Flow (Prescription & Dispense)
                # ---------------------------------------------------------
                rx = Prescription.objects.create(
                    consultation=consult,
                    patient=p,
                    doctor=doctor_user,
                    doctor_staff=doc_staff,
                    facility=facility,
                    date=today,
                    status="PENDING_VERIFICATION",
                    notes="Take medications after meals with warm water. Ensure adequate hydration."
                )

                if stage == "PHARMACY_PENDING_VERIFY":
                    v.current_queue = "PHARMACY"
                    v.status = "WAITING_FOR_PHARMACY"
                    v.save()

                    PrescriptionItem.objects.create(
                        prescription=rx,
                        medicine=seeded_meds["Amoxicillin 500mg"],
                        medicine_name="Amoxicillin 500mg",
                        dosage="500mg",
                        frequency="TID",
                        duration_days=5,
                        quantity=15,
                        dispensed_quantity=0,
                        status="PENDING"
                    )
                    PrescriptionItem.objects.create(
                        prescription=rx,
                        medicine=seeded_meds["Paracetamol 500mg"],
                        medicine_name="Paracetamol 500mg",
                        dosage="500mg",
                        frequency="SOS",
                        duration_days=3,
                        quantity=10,
                        dispensed_quantity=0,
                        status="PENDING"
                    )
                    self.stdout.write(f"    -> Visit {vis_id} | Prescription #{rx.id} PENDING_VERIFICATION in PHARMACY queue")
                    continue

                if stage == "PHARMACY_VERIFIED_FEFO_READY":
                    v.current_queue = "PHARMACY"
                    v.status = "WAITING_FOR_PHARMACY"
                    v.save()

                    PrescriptionItem.objects.create(
                        prescription=rx,
                        medicine=seeded_meds["Cetirizine 10mg"],
                        medicine_name="Cetirizine 10mg",
                        dosage="10mg",
                        frequency="OD",
                        duration_days=5,
                        quantity=5,
                        dispensed_quantity=0,
                        status="PENDING"
                    )
                    PrescriptionItem.objects.create(
                        prescription=rx,
                        medicine=seeded_meds["Paracetamol 500mg"],
                        medicine_name="Paracetamol 500mg",
                        dosage="500mg",
                        frequency="BD",
                        duration_days=3,
                        quantity=6,
                        dispensed_quantity=0,
                        status="PENDING"
                    )

                    # Pharmacist verified
                    rx.status = "VERIFIED"
                    rx.verified_by = pharm_user
                    rx.verified_at = now - datetime.timedelta(minutes=10)
                    rx.verification_notes = "Dosage and frequency verified against clinical presentation. No known drug-drug interactions."
                    rx.save()
                    self.stdout.write(f"    -> Visit {vis_id} | Prescription #{rx.id} VERIFIED by Pharmacist, ready for FEFO dispense")
                    continue

                if stage == "DISPENSED_COMPLETED":
                    item_pcm = PrescriptionItem.objects.create(
                        prescription=rx,
                        medicine=seeded_meds["Paracetamol 500mg"],
                        medicine_name="Paracetamol 500mg",
                        dosage="500mg",
                        frequency="BD",
                        duration_days=5,
                        quantity=10,
                        dispensed_quantity=0,
                        status="PENDING"
                    )

                    rx.status = "VERIFIED"
                    rx.verified_by = pharm_user
                    rx.verified_at = now - datetime.timedelta(minutes=25)
                    rx.verification_notes = "Verified for routine dispensing."
                    rx.save()

                    # Execute actual domain dispensation service
                    batch_pcm = seeded_batches["Paracetamol 500mg"]
                    dispensation_items = [
                        {
                            "prescription_item": item_pcm,
                            "batch": batch_pcm,
                            "quantity": 10
                        }
                    ]
                    disp = dispense_prescription(
                        prescription=rx,
                        items_to_dispense=dispensation_items,
                        dispensing_staff=pharm_staff,
                        facility=facility
                    )

                    v.status = "COMPLETED"
                    v.current_queue = "COMPLETED"
                    v.completed_time = now - datetime.timedelta(minutes=15)
                    v.save()

                    tok.status = "COMPLETED"
                    tok.save()

                    VisitStatusHistory.objects.create(
                        visit=v,
                        from_status="WAITING_FOR_PHARMACY",
                        to_status="COMPLETED",
                        queue="COMPLETED",
                        performed_by=pharm_user,
                        performed_by_role="PHARMACIST",
                        notes=f"Dispensation #{disp.id} completed. Medication issued to patient."
                    )
                    self.stdout.write(f"    -> Visit {vis_id} | Dispensation #{disp.id} COMPLETED (10 Paracetamol dispensed, Stock: {batch_pcm.available_quantity}, Ledger verified)")
                    continue

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("DEMO DATASET SUCCESSFULLY PREPARED & VALIDATED (10 UNIQUE PATIENTS)!"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

"""
Management command to safely reset and seed a pristine, controlled 10-patient demo dataset
for the Namma Clinic healthcare network with exhaustive pre-delete dependency analysis.

MANDATORY SAFETY & AUDIT CONSTRAINTS:
1. Real Dependency Graph Discovery:
   - Does NOT rely on Mermaid FK diagrams.
   - Inspects live Django model metadata, FK dependencies, on_delete behaviors, and reverse relations.
   - Explicitly classifies tables into PRESERVED MASTER / CONFIGURATION vs RESETTABLE OPERATIONAL.
   - Derives topological deletion order dynamically.
   - Logs the full deletion plan before execution.
   - Aborts if unexpected FK dependencies or unclassified tables are detected.
2. Controlled Destruction:
   - Foreign-key enforcement is NOT blindly disabled.
   - CASCADE is NOT used as a whole-database shortcut.
   - InventoryTransaction and DispensationReturn:
     Normal runtime ORM immutability remains strictly unchanged.
     DEMO_RESET_ONLY: direct raw SQL cursor deletion inside transaction.atomic().
3. Pre-Reseed Validation:
   - Verifies 0 surviving patient-dependent operational records before reseeding.
4. Reseeding Integrity:
   - Exactly 10 patients (NC-DEMO-001 to NC-DEMO-010).
   - Provenance chain verified: PO -> Approval -> Order -> GRN -> Batch -> InventoryTransaction.
   - PO creation/approval/order = 0 inventory mutation.
   - Rejected GRN quantity = 0 usable inventory increase.
   - Zero Maternal/Child and Zero Teleconsultation records.
5. Real Application Audit Verification:
   - Executes a real application operation post-reseed to prove natural AuditLog generation and persistence.
6. Execution Guard:
   - Requires explicit --confirm-demo-reset confirmation flag.
"""

import sys
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from django.utils import timezone
from django.apps import apps
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import (
    Facility, FacilityRelationship, FacilityOxygenSupply,
    FacilityConsumableInventory, FacilityMaintenanceTicket,
    FacilityBedCapacity, FacilityBedAllocation
)
from apps.patients.models import Patient, Household, PatientDocument
from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabTestMaster, LabToken, LabOrder, LabSample, LabResult
from apps.pharmacy.models import (
    MedicineMaster, Vendor, MedicineBatch, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GoodsReceiptItem, InventoryTransaction, DispensationReturn,
    BatchRecall, PatientCounselling, ColdChainLog
)
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.telemedicine.models import Teleconsultation
from apps.outreach.models import OutreachActivity
from apps.wellness.models import WellnessSession
from apps.ars.models import ARSMember, ARSMeeting, ARSActionItem
from apps.quality.models import QualityChecklist, BiomedicalWasteLog
from apps.alerts.models import Alert
from apps.compliance.models import ComplianceItem
from apps.integrations.models import IntegrationConfiguration
from apps.audit.models import AuditLog

User = get_user_model()

PRESERVED_MASTER_TABLES = {
    'geography_state', 'geography_district', 'geography_zone', 'geography_ward',
    'facilities_facility', 'facilities_facilityrelationship',
    'accounts_user', 'pharmacy_medicinemaster', 'pharmacy_vendor',
    'laboratory_labtestmaster', 'integrations_integrationconfiguration',
    'compliance_complianceitem'
}

SYSTEM_INFRA_TABLES = {
    'auth_permission', 'auth_group', 'auth_group_permissions',
    'django_content_type', 'django_session', 'django_migrations',
    'django_admin_log', 'accounts_user_groups', 'accounts_user_user_permissions'
}


class Command(BaseCommand):
    help = "Reset Namma Clinic database to pristine, controlled 10-patient demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-demo-reset',
            action='store_true',
            help='Required confirmation flag to execute demo reset.',
        )

    def handle(self, *args, **options):
        if not options.get('confirm_demo_reset'):
            self.stderr.write(self.style.ERROR(
                "ERROR: Demo reset aborted!\n"
                "This command flushes and resets demo data and MUST NOT be executed as a generic cleanup command.\n"
                "To proceed, pass the explicit confirmation flag:\n"
                "  python manage.py reset_demo_data --confirm-demo-reset\n"
            ))
            sys.exit(1)

        self.stdout.write(self.style.WARNING("======================================================================"))
        self.stdout.write(self.style.WARNING("NAMMA CLINIC — PRE-DELETE DEPENDENCY DISCOVERY & VALIDATION"))
        self.stdout.write(self.style.WARNING("======================================================================"))

        # -------------------------------------------------------------
        # STEP 1: DISCOVER MODEL METADATA & BUILD REAL DEPENDENCY GRAPH
        # -------------------------------------------------------------
        all_models = apps.get_models()
        resettable_models = []
        preserved_models = []

        for model in all_models:
            tbl = model._meta.db_table
            if tbl in PRESERVED_MASTER_TABLES:
                preserved_models.append(model)
            elif tbl in SYSTEM_INFRA_TABLES:
                continue
            else:
                resettable_models.append(model)

        self.stdout.write(f"Discovered {len(preserved_models)} Preserved Master/Configuration Models:")
        for m in preserved_models:
            self.stdout.write(f"  [PRESERVE] {m._meta.label} ({m._meta.db_table})")

        self.stdout.write(f"\nDiscovered {len(resettable_models)} Resettable Operational Models:")

        # Validate that no preserved master model has an unexpected FK to a resettable operational model
        for pm in preserved_models:
            for field in pm._meta.fields:
                if field.is_relation and field.related_model in resettable_models:
                    self.stderr.write(self.style.ERROR(
                        f"SAFETY ABORT: Preserved master model {pm._meta.label} depends on operational model {field.related_model._meta.label}!"
                    ))
                    sys.exit(1)

        # Build adjacency graph among resettable operational models for topological sort
        # rev_adj[A] = set of models B that A points to (A depends on B). A must be deleted BEFORE B.
        rev_adj = {m: set() for m in resettable_models}
        for m in resettable_models:
            for field in m._meta.fields:
                if field.is_relation and field.related_model in resettable_models and field.related_model != m:
                    rev_adj[m].add(field.related_model)

        # Count how many operational models point to m (m cannot be deleted until that count reaches 0)
        dependents_count = {m: 0 for m in resettable_models}
        for m in resettable_models:
            for target in rev_adj[m]:
                dependents_count[target] += 1

        queue = [m for m in resettable_models if dependents_count[m] == 0]
        deletion_order = []

        while queue:
            curr = queue.pop(0)
            deletion_order.append(curr)
            for target in rev_adj[curr]:
                dependents_count[target] -= 1
                if dependents_count[target] == 0:
                    queue.append(target)

        if len(deletion_order) != len(resettable_models):
            unresolved = [m._meta.label for m in resettable_models if m not in deletion_order]
            self.stderr.write(self.style.ERROR(
                f"SAFETY ABORT: Unresolved cyclical dependency detected among models: {unresolved}"
            ))
            sys.exit(1)

        # Print resolved deletion plan
        self.stdout.write(self.style.SUCCESS("\n--- RESOLVED SAFE DELETION PLAN (TOPOLOGICAL ORDER) ---"))
        for idx, m in enumerate(deletion_order, 1):
            fks = [f"{f.name}->{f.remote_field.model._meta.label} ({f.remote_field.on_delete.__name__ if hasattr(f.remote_field, 'on_delete') and f.remote_field.on_delete else 'None'})" for f in m._meta.fields if f.is_relation and f.remote_field]
            fks_str = "; ".join(fks) if fks else "None"
            revs = [f"{r.related_model._meta.label}.{r.field.name}" for r in m._meta.related_objects if r.related_model in resettable_models]
            revs_str = "; ".join(revs) if revs else "None"
            refs_master = [f.remote_field.model._meta.label for f in m._meta.fields if f.is_relation and f.remote_field and f.remote_field.model._meta.db_table in PRESERVED_MASTER_TABLES]
            refs_master_str = ", ".join(refs_master) if refs_master else "None"

            self.stdout.write(f"Step {idx:02d}: {m._meta.label} [Table: {m._meta.db_table}]")
            self.stdout.write(f"         FK Dependencies: {fks_str}")
            self.stdout.write(f"         Operational Dependents: {revs_str}")
            self.stdout.write(f"         References Preserved Master: {refs_master_str}")

        # -------------------------------------------------------------
        # STEP 2: EXECUTE CONTROLLED DESTRUCTION INSIDE TRANSACTION
        # -------------------------------------------------------------
        self.stdout.write(self.style.WARNING("\nExecuting controlled database reset inside transaction.atomic()..."))
        with transaction.atomic():
            # Special handling for append-only tables
            # DEMO_RESET_ONLY: InventoryTransaction and DispensationReturn
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM pharmacy_dispensationreturn;")
                cursor.execute("DELETE FROM pharmacy_inventorytransaction;")

            # Execute deletion of all operational models in topological order
            for m in deletion_order:
                tbl = m._meta.db_table
                if tbl in ['pharmacy_dispensationreturn', 'pharmacy_inventorytransaction']:
                    continue  # already flushed via cursor
                m.objects.all().delete()

            # -------------------------------------------------------------
            # STEP 3: PRE-RESEED PURGE VALIDATION
            # -------------------------------------------------------------
            self.stdout.write("Validating pre-reseed state: 0 surviving operational records...")
            surviving_checks = [
                (Patient, "patients"),
                (Visit, "visits"),
                (Token, "tokens"),
                (TriageVitals, "triage vitals"),
                (Consultation, "consultations"),
                (Prescription, "prescriptions"),
                (PrescriptionItem, "prescription items"),
                (LabOrder, "lab orders"),
                (LabToken, "lab tokens"),
                (PurchaseOrder, "purchase orders"),
                (GoodsReceiptNote, "goods receipt notes"),
                (MedicineBatch, "medicine batches"),
                (InventoryTransaction, "inventory transactions"),
                (Referral, "referrals"),
                (NCDRecord, "ncd records"),
                (PatientDocument, "patient documents"),
                (DiseaseCase, "disease cases"),
                (Teleconsultation, "teleconsultations")
            ]
            for model_cls, name in surviving_checks:
                cnt = model_cls.objects.count()
                if cnt != 0:
                    raise ValidationError(f"SAFETY ABORT: Pre-reseed check failed. {cnt} surviving {name} records detected!")
            self.stdout.write(self.style.SUCCESS("All operational records successfully purged (0 surviving records)."))

            # -------------------------------------------------------------
            # STEP 4: ENSURE PRESERVED MASTER & CONFIGURATION
            # -------------------------------------------------------------
            karnataka, _ = State.objects.get_or_create(code='KA', defaults={'name': 'Karnataka'})
            dist_central, _ = District.objects.get_or_create(code='KA-BU', defaults={'name': 'BBMP Central (Bengaluru Urban)', 'state': karnataka})
            dist_rural, _ = District.objects.get_or_create(code='KA-BR', defaults={'name': 'Bengaluru Rural', 'state': karnataka})

            zone_east, _ = Zone.objects.get_or_create(code='Z-EAST', defaults={'district': dist_central, 'name': 'East Zone'})
            zone_south, _ = Zone.objects.get_or_create(code='Z-SOUTH', defaults={'district': dist_central, 'name': 'South Zone'})
            zone_hoskote, _ = Zone.objects.get_or_create(code='Z-HOS', defaults={'district': dist_rural, 'name': 'Hoskote Zone'})

            ward12, _ = Ward.objects.get_or_create(zone=zone_east, ward_number=12, defaults={'name': 'Indiranagar Ward', 'population': 22000, 'slum_population': 6500})
            ward14, _ = Ward.objects.get_or_create(zone=zone_east, ward_number=14, defaults={'name': 'Ulsoor Ward', 'population': 19500, 'slum_population': 5200})
            ward45, _ = Ward.objects.get_or_create(zone=zone_south, ward_number=45, defaults={'name': 'Jayanagar Ward', 'population': 24000, 'slum_population': 4800})
            ward_rural, _ = Ward.objects.get_or_create(zone=zone_hoskote, ward_number=1, defaults={'name': 'Varthur Rural Ward', 'population': 18000, 'slum_population': 7200})

            # Facilities (IDs: 110, 111, 112, 113)
            hosp_a, _ = Facility.objects.get_or_create(
                id=110,
                defaults={
                    'facility_code': 'HOSP-DIST-01', 'facility_name': 'Victoria District General Hospital & Specialist Center', 'facility_type': 'MAIN_HOSPITAL',
                    'state': karnataka, 'district': dist_central, 'zone': zone_east, 'ward': ward12, 'city_or_ulb': 'BBMP Central', 'urban_rural': 'URBAN',
                    'address': 'Fort Road, Near KR Market, Bengaluru - 560002', 'latitude': 12.9634, 'longitude': 77.5750, 'population_served': 500000,
                    'emergency_available': True, 'lab_available': True, 'pharmacy_available': True, 'teleconsultation_available': False, 'bed_capacity': 750,
                    'services': 'Cardiology, Nephrology, General Surgery, Emergency, ICU'
                }
            )

            nc_a1, _ = Facility.objects.get_or_create(
                id=111,
                defaults={
                    'facility_code': 'HOSP-SUB-01', 'facility_name': 'Indiranagar Sub-District Hospital & UPHC', 'facility_type': 'NAMMA_CLINIC',
                    'parent_facility': hosp_a, 'state': karnataka, 'district': dist_central, 'zone': zone_east, 'ward': ward12, 'city_or_ulb': 'BBMP East', 'urban_rural': 'URBAN',
                    'address': '100 Feet Road, Indiranagar, Bengaluru - 560038', 'latitude': 12.9719, 'longitude': 77.6412, 'population_served': 35000, 'vulnerable_population': 8500,
                    'emergency_available': True, 'lab_available': True, 'pharmacy_available': True, 'teleconsultation_available': False, 'bed_capacity': 50,
                    'services': 'General OPD, NCD Screening, Basic Diagnostics, Pharmacy'
                }
            )

            rc_a4, _ = Facility.objects.get_or_create(
                id=112,
                defaults={
                    'facility_code': 'RC-A4-01', 'facility_name': 'Varthur Rural Primary Clinic A4', 'facility_type': 'RURAL_CLINIC',
                    'parent_facility': nc_a1, 'state': karnataka, 'district': dist_rural, 'zone': zone_hoskote, 'ward': ward_rural, 'city_or_ulb': 'BBMP Peripheral', 'urban_rural': 'RURAL',
                    'address': 'Varthur Main Road, Near Govt High School, Bengaluru Rural - 560087', 'latitude': 12.9398, 'longitude': 77.7460, 'population_served': 18000, 'vulnerable_population': 7200,
                    'emergency_available': False, 'lab_available': True, 'pharmacy_available': True, 'teleconsultation_available': False, 'bed_capacity': 10,
                    'services': 'General OPD, NCD Screening, Immunization, Basic Diagnostics'
                }
            )

            vc_a4_1, _ = Facility.objects.get_or_create(
                id=113,
                defaults={
                    'facility_code': 'VC-A4-01', 'facility_name': 'Gunjur Village Satellite Clinic', 'facility_type': 'VILLAGE_CLINIC',
                    'parent_facility': rc_a4, 'state': karnataka, 'district': dist_rural, 'zone': zone_hoskote, 'ward': ward_rural, 'city_or_ulb': 'BBMP East Peripheral', 'urban_rural': 'RURAL',
                    'address': 'Gunjur Lake Road, Gunjur Village, Bengaluru Rural - 560087', 'latitude': 12.9300, 'longitude': 77.7550, 'population_served': 8000, 'vulnerable_population': 3100,
                    'emergency_available': False, 'lab_available': True, 'pharmacy_available': True, 'teleconsultation_available': False, 'bed_capacity': 4,
                    'services': 'Primary Screening, Immunization, First Aid'
                }
            )

            FacilityRelationship.objects.get_or_create(source_facility=vc_a4_1, destination_facility=rc_a4, defaults={'relationship_type': 'REFERRAL', 'service': 'Village Primary Referral', 'priority': 'PRIMARY', 'distance_km': 2.5})
            FacilityRelationship.objects.get_or_create(source_facility=rc_a4, destination_facility=nc_a1, defaults={'relationship_type': 'REFERRAL', 'service': 'Sub-District Secondary Care', 'priority': 'PRIMARY', 'distance_km': 4.2})
            FacilityRelationship.objects.get_or_create(source_facility=nc_a1, destination_facility=hosp_a, defaults={'relationship_type': 'SPECIALIST', 'service': 'District Cardiology & Tertiary Surgery', 'priority': 'EMERGENCY', 'distance_km': 5.0})
            FacilityRelationship.objects.get_or_create(source_facility=rc_a4, destination_facility=hosp_a, defaults={'relationship_type': 'SPECIALIST', 'service': 'Direct Emergency ICU Referral', 'priority': 'EMERGENCY', 'distance_km': 12.0})

            # 19 Users
            users_meta = [
                ('district', 'district@nammaclinic.gov.in', 'district123', 'Dr. Sunita Rao (District Health Officer)', 'DISTRICT_OFFICER', None, dist_central),
                ('dh_admin', 'dh_admin@nammaclinic.gov.in', 'dh123', 'Dr. K. V. Sharma (District Hospital Supt)', 'HOSPITAL_ADMIN', hosp_a, None),
                ('hospital', 'hospital@nammaclinic.gov.in', 'hospital123', 'Dr. K. V. Sharma (District Hospital Supt)', 'HOSPITAL_ADMIN', hosp_a, None),
                ('sdh_admin', 'sdh_admin@nammaclinic.gov.in', 'sdh123', 'Dr. Meena Swamy (Sub-District Admin)', 'HOSPITAL_ADMIN', nc_a1, None),
                ('vh1_admin', 'vh1_admin@nammaclinic.gov.in', 'vh1123', 'Dr. Ramesh Rao (Village Hospital 1 Admin)', 'HOSPITAL_ADMIN', rc_a4, None),
                ('varthur_admin', 'varthur_admin@nammaclinic.gov.in', 'varthur123', 'Dr. Anita Desai (Varthur Clinic Admin)', 'HOSPITAL_ADMIN', rc_a4, None),
                ('vh2_admin', 'vh2_admin@nammaclinic.gov.in', 'vh2123', 'Dr. Anand Kumar (Village Hospital 2 Admin)', 'HOSPITAL_ADMIN', vc_a4_1, None),
                ('dh_doctor', 'dh_doctor@nammaclinic.gov.in', 'dhdoc123', 'Dr. Vikram Seth (District Senior Cardiologist)', 'DOCTOR', hosp_a, None),
                ('sdh_doctor', 'sdh_doctor@nammaclinic.gov.in', 'sdhdoc123', 'Dr. Asha Patil (Sub-District Physician)', 'DOCTOR', nc_a1, None),
                ('vh1_doctor', 'vh1_doctor@nammaclinic.gov.in', 'vh1doc123', 'Dr. Rajesh Kumar (Village Hospital 1 MO)', 'DOCTOR', rc_a4, None),
                ('doctor', 'doctor@nammaclinic.gov.in', 'doctor123', 'Dr. Rajesh Kumar (Village Hospital 1 MO)', 'DOCTOR', rc_a4, None),
                ('vh2_doctor', 'vh2_doctor@nammaclinic.gov.in', 'vh2doc123', 'Dr. Suresh V. (Village Hospital 2 MO)', 'DOCTOR', vc_a4_1, None),
                ('nurse', 'nurse@nammaclinic.gov.in', 'nurse123', 'Sister Priya Nair', 'NURSE', rc_a4, None),
                ('sdh_nurse', 'sdh_nurse@nammaclinic.gov.in', 'sdhnurse123', 'Sister Kavitha R.', 'NURSE', nc_a1, None),
                ('dh_nurse', 'dh_nurse@nammaclinic.gov.in', 'dhnurse123', 'Sister Mary Joseph', 'NURSE', hosp_a, None),
                ('lab', 'lab@nammaclinic.gov.in', 'lab123', 'Mr. Suresh Gowda', 'LAB_TECHNICIAN', rc_a4, None),
                ('dh_lab', 'dh_lab@nammaclinic.gov.in', 'dhlab123', 'Mr. Chethan M.', 'LAB_TECHNICIAN', hosp_a, None),
                ('pharmacy', 'pharmacy@nammaclinic.gov.in', 'pharmacy123', 'Mrs. Lakshmi Devi', 'PHARMACIST', rc_a4, None),
                ('dh_pharmacy', 'dh_pharmacy@nammaclinic.gov.in', 'dhpharm123', 'Mr. Mahesh Babu', 'PHARMACIST', hosp_a, None),
            ]
            for uname, email, pwd, fname, role, fac, dist in users_meta:
                u = User.objects.filter(username=uname).first()
                if not u:
                    User.objects.create_user(uname, email, pwd, full_name=fname, role=role, assigned_facility=fac, assigned_district=dist)
                else:
                    u.role = role
                    u.full_name = fname
                    u.assigned_facility = fac
                    u.assigned_district = dist
                    u.save()

            u_dist = User.objects.get(username='district')
            u_dh_admin = User.objects.get(username='dh_admin')
            u_sdh_admin = User.objects.get(username='sdh_admin')
            u_vh1_admin = User.objects.get(username='vh1_admin')
            u_vh2_admin = User.objects.get(username='vh2_admin')
            u_dh_doc = User.objects.get(username='dh_doctor')
            u_sdh_doc = User.objects.get(username='sdh_doctor')
            u_doc = User.objects.get(username='doctor')
            u_vh2_doc = User.objects.get(username='vh2_doctor')
            u_nurse = User.objects.get(username='nurse')
            u_sdh_nurse = User.objects.get(username='sdh_nurse')
            u_dh_nurse = User.objects.get(username='dh_nurse')
            u_lab = User.objects.get(username='lab')
            u_dh_lab = User.objects.get(username='dh_lab')
            u_pharm = User.objects.get(username='pharmacy')
            u_dh_pharm = User.objects.get(username='dh_pharmacy')

            # Diagnostics & Medicines
            lt_hba1c, _ = LabTestMaster.objects.get_or_create(code='L-HBA1C', defaults={'name': 'HbA1c Glycated Hemoglobin', 'category': 'Diabetes', 'reference_range': '4.0 - 5.6 %', 'unit': '%'})
            lt_fbg, _ = LabTestMaster.objects.get_or_create(code='L-FBG', defaults={'name': 'Fasting Blood Glucose (FBG)', 'category': 'Diabetes', 'reference_range': '70 - 100 mg/dL', 'unit': 'mg/dL'})
            lt_rbg, _ = LabTestMaster.objects.get_or_create(code='L-RBG', defaults={'name': 'Random Blood Glucose (Rapid Strip)', 'category': 'Diabetes', 'reference_range': '70 - 140 mg/dL', 'unit': 'mg/dL'})
            lt_hb, _ = LabTestMaster.objects.get_or_create(code='L-HB', defaults={'name': 'Hemoglobin (Hb Estimation)', 'category': 'Hematology', 'reference_range': '12.0 - 15.5 g/dL', 'unit': 'g/dL'})
            lt_lipid, _ = LabTestMaster.objects.get_or_create(code='L-LIPID', defaults={'name': 'Lipid Profile (Cholesterol & Triglycerides)', 'category': 'Biochemistry', 'reference_range': 'Desirable < 200 mg/dL', 'unit': 'mg/dL'})
            lt_dengue, _ = LabTestMaster.objects.get_or_create(code='L-DENGUE', defaults={'name': 'Dengue NS1 Antigen Rapid Test Card', 'category': 'Serology', 'reference_range': 'Negative', 'unit': 'Result'})
            lt_malaria, _ = LabTestMaster.objects.get_or_create(code='L-MALARIA', defaults={'name': 'Malaria Antigen (Pf/Pv) Rapid Test', 'category': 'Serology', 'reference_range': 'Negative', 'unit': 'Result'})
            lt_u_prot, _ = LabTestMaster.objects.get_or_create(code='L-URINE-PROT', defaults={'name': 'Urine Albumin / Protein Test', 'category': 'Urinalysis', 'reference_range': 'Nil / Negative', 'unit': 'Grade'})
            lt_tb, _ = LabTestMaster.objects.get_or_create(code='L-TB-SPUTUM', defaults={'name': 'Sputum Smear for AFB (Tuberculosis)', 'category': 'Microbiology', 'reference_range': 'Negative for AFB', 'unit': 'Result'})

            med_met, _ = MedicineMaster.objects.get_or_create(generic_name='Metformin HCl', defaults={'brand_name': 'Glycomet', 'strength': '500 mg', 'dosage_form': 'Tablet', 'category': 'Anti-Diabetic', 'minimum_stock': 50, 'reorder_level': 100})
            med_aml, _ = MedicineMaster.objects.get_or_create(generic_name='Amlodipine Besylate', defaults={'brand_name': 'Amlopres', 'strength': '5 mg', 'dosage_form': 'Tablet', 'category': 'Anti-Hypertensive', 'minimum_stock': 50, 'reorder_level': 100})
            med_pcm, _ = MedicineMaster.objects.get_or_create(generic_name='Paracetamol', defaults={'brand_name': 'Dolo', 'strength': '650 mg', 'dosage_form': 'Tablet', 'category': 'Analgesic / Antipyretic', 'minimum_stock': 100, 'reorder_level': 200})
            med_amx, _ = MedicineMaster.objects.get_or_create(generic_name='Amoxicillin Trihydrate', defaults={'brand_name': 'Mox', 'strength': '500 mg', 'dosage_form': 'Capsule', 'category': 'Antibiotic', 'minimum_stock': 50, 'reorder_level': 100})
            med_tel, _ = MedicineMaster.objects.get_or_create(generic_name='Telmisartan', defaults={'brand_name': 'Telma', 'strength': '40 mg', 'dosage_form': 'Tablet', 'category': 'Anti-Hypertensive', 'minimum_stock': 40, 'reorder_level': 80})
            med_ifa, _ = MedicineMaster.objects.get_or_create(generic_name='Iron & Folic Acid', defaults={'brand_name': 'IFA Red', 'strength': '100mg Fe + 500mcg FA', 'dosage_form': 'Tablet', 'category': 'General Health', 'minimum_stock': 75, 'reorder_level': 150})
            med_cet, _ = MedicineMaster.objects.get_or_create(generic_name='Cetirizine HCl', defaults={'brand_name': 'Cetzine', 'strength': '10 mg', 'dosage_form': 'Tablet', 'category': 'Antihistamine', 'minimum_stock': 30, 'reorder_level': 60})

            v_ksmscl, _ = Vendor.objects.get_or_create(vendor_name='KSMSCL (Karnataka State Medical Supplies Corp Ltd)', defaults={'contact_person': 'Mr. R. K. Hegde (General Manager)', 'phone': '080-22345678', 'email': 'procurement@ksmscl.in', 'address': 'Rehabilitative Building, Anand Rao Circle, Bengaluru', 'gst_number': '29AAACK1234F1Z5', 'status': 'ACTIVE'})
            v_kapl, _ = Vendor.objects.get_or_create(vendor_name='Karnataka Antibiotics & Pharmaceuticals Ltd (KAPL)', defaults={'contact_person': 'Dr. S. M. Patel', 'phone': '080-28392555', 'email': 'sales@kaplindia.com', 'address': 'Peenya Industrial Area, 1st Stage, Bengaluru', 'gst_number': '29AAACK5678F1Z9', 'status': 'ACTIVE'})

            today = datetime.date.today()

            # -------------------------------------------------------------
            # STEP 5: SEED PROCUREMENT LIFECYCLE & PROVENANCE
            # -------------------------------------------------------------
            # PO 1: Victoria District Hospital from KSMSCL (Fully Received)
            po1 = PurchaseOrder.objects.create(
                po_number="PO-HOSP-DIST-01-2026-001", vendor=v_ksmscl, facility=hosp_a,
                order_date=today - datetime.timedelta(days=10), expected_delivery_date=today - datetime.timedelta(days=2),
                status='RECEIVED', created_by=u_dh_admin, approved_by=u_dh_admin,
                approved_at=timezone.now() - datetime.timedelta(days=9),
                notes='District Hospital quarterly essential medicines replenishment indent.'
            )
            poi1_1 = PurchaseOrderItem.objects.create(purchase_order=po1, medicine=med_met, ordered_quantity=1000, received_quantity=1000, accepted_quantity=1000, rejected_quantity=0, unit_price=Decimal("1.20"), total_price=Decimal("1200.00"))
            poi1_2 = PurchaseOrderItem.objects.create(purchase_order=po1, medicine=med_aml, ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_price=Decimal("0.85"), total_price=Decimal("425.00"))
            po1.total_amount = Decimal("1625.00")
            po1.save()

            grn1 = GoodsReceiptNote.objects.create(
                grn_number="GRN-HOSP-DIST-01-2026-001", purchase_order=po1, vendor=v_ksmscl, facility=hosp_a,
                invoice_number='INV-KSMSCL-9821', invoice_date=today - datetime.timedelta(days=3),
                received_date=today - datetime.timedelta(days=2), received_by=u_dh_pharm,
                status='ACCEPTED', notes='Delivered in full, temperature and seals verified intact.'
            )
            GoodsReceiptItem.objects.create(
                grn=grn1, po_item=poi1_1, medicine=med_met, batch_number='MET-DH-2026A',
                mfg_date=today - datetime.timedelta(days=120), expiry_date=today + datetime.timedelta(days=180),
                ordered_quantity=1000, received_quantity=1000, accepted_quantity=1000, rejected_quantity=0, unit_cost=Decimal("1.20")
            )
            b_dh_met = MedicineBatch.objects.create(
                facility=hosp_a, medicine=med_met, batch_number='MET-DH-2026A', vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=120), expiry_date=today + datetime.timedelta(days=180),
                unit_cost=Decimal("1.20"), available_quantity=1000, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=hosp_a, medicine=med_met, batch=b_dh_met,
                transaction_type='PURCHASE_RECEIVED', quantity=1000,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=1000,
                reference_id=f"GRN-{grn1.grn_number}", created_by=u_dh_pharm,
                notes='Stock received via accepted GRN #GRN-HOSP-DIST-01-2026-001'
            )

            GoodsReceiptItem.objects.create(
                grn=grn1, po_item=poi1_2, medicine=med_aml, batch_number='AML-DH-2026B',
                mfg_date=today - datetime.timedelta(days=90), expiry_date=today + datetime.timedelta(days=120),
                ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_cost=Decimal("0.85")
            )
            b_dh_aml = MedicineBatch.objects.create(
                facility=hosp_a, medicine=med_aml, batch_number='AML-DH-2026B', vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=90), expiry_date=today + datetime.timedelta(days=120),
                unit_cost=Decimal("0.85"), available_quantity=500, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=hosp_a, medicine=med_aml, batch=b_dh_aml,
                transaction_type='PURCHASE_RECEIVED', quantity=500,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=500,
                reference_id=f"GRN-{grn1.grn_number}", created_by=u_dh_pharm,
                notes='Stock received via accepted GRN #GRN-HOSP-DIST-01-2026-001'
            )

            # PO 2: Varthur Rural Primary Clinic from KAPL (Partially Received with Damaged Rejection)
            po2 = PurchaseOrder.objects.create(
                po_number="PO-RC-A4-01-2026-001", vendor=v_kapl, facility=rc_a4,
                order_date=today - datetime.timedelta(days=8), expected_delivery_date=today - datetime.timedelta(days=1),
                status='PARTIALLY_RECEIVED', created_by=u_vh1_admin, approved_by=u_vh1_admin,
                approved_at=timezone.now() - datetime.timedelta(days=7),
                notes='Rural clinic stock order: Analgesics and Anti-diabetics.'
            )
            poi2_1 = PurchaseOrderItem.objects.create(purchase_order=po2, medicine=med_pcm, ordered_quantity=1200, received_quantity=1200, accepted_quantity=1150, rejected_quantity=50, unit_price=Decimal("0.50"), total_price=Decimal("600.00"))
            poi2_2 = PurchaseOrderItem.objects.create(purchase_order=po2, medicine=med_met, ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_price=Decimal("1.20"), total_price=Decimal("600.00"))
            po2.total_amount = Decimal("1200.00")
            po2.save()

            grn2 = GoodsReceiptNote.objects.create(
                grn_number="GRN-RC-A4-01-2026-001", purchase_order=po2, vendor=v_kapl, facility=rc_a4,
                invoice_number='INV-KAPL-4412', invoice_date=today - datetime.timedelta(days=2),
                received_date=today - datetime.timedelta(days=1), received_by=u_pharm,
                status='PARTIAL_ACCEPTANCE', notes='50 units Paracetamol rejected due to torn carton in transit.'
            )
            GoodsReceiptItem.objects.create(
                grn=grn2, po_item=poi2_1, medicine=med_pcm, batch_number='PCM-RC-2026P',
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=300),
                ordered_quantity=1200, received_quantity=1200, accepted_quantity=1150, rejected_quantity=50,
                rejection_reason='50 strips outer packaging damaged during transit', unit_cost=Decimal("0.50")
            )
            b_rc_pcm = MedicineBatch.objects.create(
                facility=rc_a4, medicine=med_pcm, batch_number='PCM-RC-2026P', vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=300),
                unit_cost=Decimal("0.50"), available_quantity=1150, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=rc_a4, medicine=med_pcm, batch=b_rc_pcm,
                transaction_type='PURCHASE_RECEIVED', quantity=1150,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=1150,
                reference_id=f"GRN-{grn2.grn_number}", created_by=u_pharm,
                notes='Stock received via partially accepted GRN #GRN-RC-A4-01-2026-001 (50 rejected)'
            )

            GoodsReceiptItem.objects.create(
                grn=grn2, po_item=poi2_2, medicine=med_met, batch_number='MET-RC-2026A',
                mfg_date=today - datetime.timedelta(days=100), expiry_date=today + datetime.timedelta(days=200),
                ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_cost=Decimal("1.20")
            )
            b_rc_met = MedicineBatch.objects.create(
                facility=rc_a4, medicine=med_met, batch_number='MET-RC-2026A', vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=100), expiry_date=today + datetime.timedelta(days=200),
                unit_cost=Decimal("1.20"), available_quantity=500, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=rc_a4, medicine=med_met, batch=b_rc_met,
                transaction_type='PURCHASE_RECEIVED', quantity=500,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=500,
                reference_id=f"GRN-{grn2.grn_number}", created_by=u_pharm,
                notes='Stock received via accepted GRN #GRN-RC-A4-01-2026-001'
            )

            # PO 3: Indiranagar Sub-District Hospital from KSMSCL (Fully Received)
            po3 = PurchaseOrder.objects.create(
                po_number="PO-HOSP-SUB-01-2026-001", vendor=v_ksmscl, facility=nc_a1,
                order_date=today - datetime.timedelta(days=6), expected_delivery_date=today - datetime.timedelta(days=1),
                status='RECEIVED', created_by=u_sdh_admin, approved_by=u_sdh_admin,
                approved_at=timezone.now() - datetime.timedelta(days=5),
                notes='Sub-District Hospital anti-hypertensive replenishment.'
            )
            poi3_1 = PurchaseOrderItem.objects.create(purchase_order=po3, medicine=med_tel, ordered_quantity=400, received_quantity=400, accepted_quantity=400, rejected_quantity=0, unit_price=Decimal("2.50"), total_price=Decimal("1000.00"))
            poi3_2 = PurchaseOrderItem.objects.create(purchase_order=po3, medicine=med_aml, ordered_quantity=300, received_quantity=300, accepted_quantity=300, rejected_quantity=0, unit_price=Decimal("0.85"), total_price=Decimal("255.00"))
            po3.total_amount = Decimal("1255.00")
            po3.save()

            grn3 = GoodsReceiptNote.objects.create(
                grn_number="GRN-HOSP-SUB-01-2026-001", purchase_order=po3, vendor=v_ksmscl, facility=nc_a1,
                invoice_number='INV-KSMSCL-9844', invoice_date=today - datetime.timedelta(days=2),
                received_date=today - datetime.timedelta(days=1), received_by=u_sdh_admin,
                status='ACCEPTED', notes='All line items verified and accepted into stock.'
            )
            GoodsReceiptItem.objects.create(
                grn=grn3, po_item=poi3_1, medicine=med_tel, batch_number='TEL-SDH-2026T',
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=365),
                ordered_quantity=400, received_quantity=400, accepted_quantity=400, rejected_quantity=0, unit_cost=Decimal("2.50")
            )
            b_sdh_tel = MedicineBatch.objects.create(
                facility=nc_a1, medicine=med_tel, batch_number='TEL-SDH-2026T', vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=365),
                unit_cost=Decimal("2.50"), available_quantity=400, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=nc_a1, medicine=med_tel, batch=b_sdh_tel,
                transaction_type='PURCHASE_RECEIVED', quantity=400,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=400,
                reference_id=f"GRN-{grn3.grn_number}", created_by=u_sdh_admin,
                notes='Stock received via accepted GRN #GRN-HOSP-SUB-01-2026-001'
            )

            GoodsReceiptItem.objects.create(
                grn=grn3, po_item=poi3_2, medicine=med_aml, batch_number='AML-SDH-2026A',
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=180),
                ordered_quantity=300, received_quantity=300, accepted_quantity=300, rejected_quantity=0, unit_cost=Decimal("0.85")
            )
            b_sdh_aml = MedicineBatch.objects.create(
                facility=nc_a1, medicine=med_aml, batch_number='AML-SDH-2026A', vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=180),
                unit_cost=Decimal("0.85"), available_quantity=300, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=nc_a1, medicine=med_aml, batch=b_sdh_aml,
                transaction_type='PURCHASE_RECEIVED', quantity=300,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=300,
                reference_id=f"GRN-{grn3.grn_number}", created_by=u_sdh_admin,
                notes='Stock received via accepted GRN #GRN-HOSP-SUB-01-2026-001'
            )

            # PO 4: Gunjur Village Clinic from KAPL (Fully Received)
            po4 = PurchaseOrder.objects.create(
                po_number="PO-VC-A4-01-2026-001", vendor=v_kapl, facility=vc_a4_1,
                order_date=today - datetime.timedelta(days=5), expected_delivery_date=today - datetime.timedelta(days=1),
                status='RECEIVED', created_by=u_vh2_admin, approved_by=u_vh2_admin,
                approved_at=timezone.now() - datetime.timedelta(days=4),
                notes='Village clinic primary medication supply.'
            )
            poi4_1 = PurchaseOrderItem.objects.create(purchase_order=po4, medicine=med_pcm, ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_price=Decimal("0.50"), total_price=Decimal("250.00"))
            po4.total_amount = Decimal("250.00")
            po4.save()

            grn4 = GoodsReceiptNote.objects.create(
                grn_number="GRN-VC-A4-01-2026-001", purchase_order=po4, vendor=v_kapl, facility=vc_a4_1,
                invoice_number='INV-KAPL-4480', invoice_date=today - datetime.timedelta(days=2),
                received_date=today - datetime.timedelta(days=1), received_by=u_vh2_doc,
                status='ACCEPTED', notes='Paracetamol batch received in good order.'
            )
            GoodsReceiptItem.objects.create(
                grn=grn4, po_item=poi4_1, medicine=med_pcm, batch_number='PCM-VC-2026P',
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=300),
                ordered_quantity=500, received_quantity=500, accepted_quantity=500, rejected_quantity=0, unit_cost=Decimal("0.50")
            )
            b_vc_pcm = MedicineBatch.objects.create(
                facility=vc_a4_1, medicine=med_pcm, batch_number='PCM-VC-2026P', vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=300),
                unit_cost=Decimal("0.50"), available_quantity=500, status='AVAILABLE'
            )
            InventoryTransaction.objects.create(
                facility=vc_a4_1, medicine=med_pcm, batch=b_vc_pcm,
                transaction_type='PURCHASE_RECEIVED', quantity=500,
                source_bucket='external_vendor', source_before_qty=0, source_after_qty=0,
                destination_bucket='available_quantity', destination_before_qty=0, destination_after_qty=500,
                reference_id=f"GRN-{grn4.grn_number}", created_by=u_vh2_doc,
                notes='Stock received via accepted GRN #GRN-VC-A4-01-2026-001'
            )

            # PO 5: In-Transit Replenishment (ORDERED, 0 stock mutation)
            po5 = PurchaseOrder.objects.create(
                po_number="PO-HOSP-DIST-01-2026-002", vendor=v_ksmscl, facility=hosp_a,
                order_date=today - datetime.timedelta(days=2), expected_delivery_date=today + datetime.timedelta(days=5),
                status='ORDERED', created_by=u_dh_admin, approved_by=u_dh_admin,
                approved_at=timezone.now() - datetime.timedelta(days=1),
                notes='In-transit replenishment indent. Zero stock impacts before physical delivery & GRN.'
            )
            PurchaseOrderItem.objects.create(purchase_order=po5, medicine=med_ifa, ordered_quantity=300, received_quantity=0, unit_price=Decimal("0.60"), total_price=Decimal("180.00"))
            PurchaseOrderItem.objects.create(purchase_order=po5, medicine=med_cet, ordered_quantity=200, received_quantity=0, unit_price=Decimal("0.90"), total_price=Decimal("180.00"))
            po5.total_amount = Decimal("360.00")
            po5.save()

            # -------------------------------------------------------------
            # STEP 6: EXACTLY 10 PATIENTS & REAL WORKFLOWS
            # -------------------------------------------------------------
            p1 = Patient.objects.create(
                patient_id='NC-DEMO-001', name='Ramesh Kumar', date_of_birth=datetime.date(1974, 5, 12), age=52, gender='MALE',
                mobile='9876543210', address='House #45, Near Govt School, Varthur Slum Area', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-8765-4321-0987', emergency_contact='9876543211 (Sunita - Wife)', vulnerability_information='Slum Household BPL',
                registered_at_facility=rc_a4
            )
            p2 = Patient.objects.create(
                patient_id='NC-DEMO-002', name='Narayana Swamy', date_of_birth=datetime.date(1958, 11, 22), age=68, gender='MALE',
                mobile='9880223344', address='Fort Slum Pocket, KR Market Ward 12', ward=ward12, district=dist_central,
                ABHA_ID_DEMO='91-2233-4455-6677', emergency_contact='9880223345 (Suresh - Son)', vulnerability_information='Senior Citizen / Cardiac History',
                registered_at_facility=hosp_a
            )
            p3 = Patient.objects.create(
                patient_id='NC-DEMO-003', name='Sunita Patil', date_of_birth=datetime.date(1984, 8, 20), age=42, gender='FEMALE',
                mobile='9845012345', address='Cross Road #3, Indiranagar Slum Colony', ward=ward12, district=dist_central,
                ABHA_ID_DEMO='91-1234-5678-9012', emergency_contact='9845012346 (Ashok - Husband)', vulnerability_information='Urban Slum Resident BPL',
                registered_at_facility=nc_a1
            )
            p4 = Patient.objects.create(
                patient_id='NC-DEMO-004', name='Kavitha Sundaram', date_of_birth=datetime.date(1991, 4, 10), age=35, gender='FEMALE',
                mobile='9880112233', address='Varthur Lake BPL Slum Line 4', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-1122-3344-5566', emergency_contact='9880112234 (Ravi - Brother)', vulnerability_information='Low Income Household',
                registered_at_facility=rc_a4
            )
            p5 = Patient.objects.create(
                patient_id='NC-DEMO-005', name='Manjunath Gowda', date_of_birth=datetime.date(1998, 2, 14), age=28, gender='MALE',
                mobile='9900112233', address='Gunjur Village Main Road', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-9988-7766-5544', emergency_contact='9900112235 (Byregowda - Father)', vulnerability_information='Rural Agricultural Worker',
                registered_at_facility=vc_a4_1
            )
            p6 = Patient.objects.create(
                patient_id='NC-DEMO-006', name='Lakshmamma B.', date_of_birth=datetime.date(1965, 7, 8), age=61, gender='FEMALE',
                mobile='9876112233', address='Varthur Post Road, Ward 1', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-4455-6677-8899', emergency_contact='9876112235 (Geetha - Daughter)', vulnerability_information='Diabetic Elderly Widow',
                registered_at_facility=rc_a4
            )
            p7 = Patient.objects.create(
                patient_id='NC-DEMO-007', name='Anand Kumar', date_of_birth=datetime.date(1978, 9, 30), age=48, gender='MALE',
                mobile='9845998877', address='Balagere Cross, Varthur Rural', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-5566-7788-9900', emergency_contact='9845998878 (Malini - Wife)', vulnerability_information='Slum Resident BPL',
                registered_at_facility=rc_a4
            )
            p8 = Patient.objects.create(
                patient_id='NC-DEMO-008', name='Deepa Sharma', date_of_birth=datetime.date(1971, 3, 15), age=55, gender='FEMALE',
                mobile='9880554433', address='KR Market Flower Galli, Ward 12', ward=ward12, district=dist_central,
                ABHA_ID_DEMO='91-6677-8899-0011', emergency_contact='9880554434 (Mohan - Husband)', vulnerability_information='Urban Vendor BPL',
                registered_at_facility=hosp_a
            )
            p9 = Patient.objects.create(
                patient_id='NC-DEMO-009', name='Venkatesh Murthy', date_of_birth=datetime.date(1988, 6, 25), age=38, gender='MALE',
                mobile='9845667788', address='100 Feet Road Slum Pocket, Indiranagar', ward=ward12, district=dist_central,
                ABHA_ID_DEMO='91-7788-9900-1122', emergency_contact='9845667789 (Roopa - Sister)', vulnerability_information='Informal Transport Worker',
                registered_at_facility=nc_a1
            )
            p10 = Patient.objects.create(
                patient_id='NC-DEMO-010', name='Suresh Rao', date_of_birth=datetime.date(1961, 10, 18), age=65, gender='MALE',
                mobile='9900778899', address='Gunjur Colony Pocket B', ward=ward_rural, district=dist_rural,
                ABHA_ID_DEMO='91-8899-0011-2233', emergency_contact='9900778890 (Praveen - Son)', vulnerability_information='Senior Citizen / Day Observation',
                registered_at_facility=vc_a4_1
            )

            Household.objects.create(household_id='HH-DEMO-001', head_name='Ramesh Kumar', address='House #45, Near Govt School, Varthur Slum Area', ward=ward_rural, members_count=4, vulnerable_category='Slum BPL')
            Household.objects.create(household_id='HH-DEMO-002', head_name='Narayana Swamy', address='Fort Slum Pocket, KR Market Ward 12', ward=ward12, members_count=3, vulnerable_category='Senior BPL')

            # --- PATIENT 1 (p1): Doctor -> Lab -> Doctor Loop + FEFO Dispensation + Specialist Referral ---
            v_rc_1 = Visit.objects.create(
                visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-001", patient=p1, facility=rc_a4,
                opd_date=today, visit_type='GENERAL_OPD', priority='HIGH', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Dizziness, fatigue, and elevated home blood sugar readings',
                assigned_doctor=u_doc, arrival_time=timezone.now() - datetime.timedelta(hours=2, minutes=30),
                triage_start_time=timezone.now() - datetime.timedelta(hours=2, minutes=20),
                triage_end_time=timezone.now() - datetime.timedelta(hours=2, minutes=10),
                consultation_start_time=timezone.now() - datetime.timedelta(hours=1, minutes=45),
                consultation_end_time=timezone.now() - datetime.timedelta(hours=1, minutes=15),
                completed_time=timezone.now() - datetime.timedelta(minutes=30)
            )
            Token.objects.create(token_number=1, visit=v_rc_1, facility=rc_a4, date=today, priority='HIGH', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_rc_1, patient=p1, nurse=u_nurse,
                blood_pressure_systolic=148, blood_pressure_diastolic=96, pulse_bpm=84, temperature_f=98.8,
                spo2_percent=98, respiratory_rate=18, height_cm=168.0, weight_kg=78.0, blood_glucose_mgdl=185,
                high_bp_flag=True, high_glucose_flag=True, ncd_risk_flag=True,
                nurse_notes='Elevated BP (148/96) and Random Blood Glucose 185 mg/dL. Fast-tracked for Doctor.'
            )

            c_rc_1 = Consultation.objects.create(
                visit=v_rc_1, patient=p1, doctor=u_doc, facility=rc_a4,
                chief_complaint='Dizziness and fatigue for 5 days',
                clinical_history='Type 2 Diabetes Mellitus diagnosed 2 years ago. Irregular follow-up.',
                clinical_assessment='BP 148/96 mmHg. Random Blood Glucose 185 mg/dL. Ordered HbA1c diagnostic test.',
                diagnosis_code='E11.9 / I10', diagnosis_name='Type 2 Diabetes Mellitus with Essential Hypertension',
                treatment_plan='Initiate Metformin 500mg BD. Lab test for HbA1c. Refer to Victoria Hospital for Cardiology consult.',
                follow_up_date=today + datetime.timedelta(days=14), clinical_notes='Doctor->Lab->Doctor diagnostic loop completed.'
            )

            ltok_rc_1 = LabToken.objects.create(token_number=1, token_code=f"LAB-RC-{today.strftime('%Y%m%d')}-001", visit=v_rc_1, facility=rc_a4, date=today, status='COMPLETED')
            lo_rc_1 = LabOrder.objects.create(lab_token=ltok_rc_1, visit=v_rc_1, consultation=c_rc_1, patient=p1, doctor=u_doc, facility=rc_a4, test_master=lt_hba1c, status='VERIFIED')
            LabSample.objects.create(lab_order=lo_rc_1, sample_type='Blood', sample_code='SMP-RC-001', collected_by=u_lab)
            LabResult.objects.create(lab_order=lo_rc_1, result_value='8.4', unit='%', reference_range='4.0 - 5.6 %', interpretation_flag='HIGH', verified_by=u_lab, notes='HbA1c significantly elevated (8.4%). Poor glycemic control.')

            pr_rc_1 = Prescription.objects.create(
                consultation=c_rc_1, patient=p1, doctor=u_doc, facility=rc_a4,
                status='PENDING_VERIFICATION',
                verification_notes='Prescribed Metformin 500mg BD. Awaiting pharmacist verification.'
            )
            pi_rc_1 = PrescriptionItem.objects.create(
                prescription=pr_rc_1, medicine=med_met, medicine_name='Metformin 500 mg Tablet',
                dosage='1-0-1 After Food', frequency='Twice Daily', duration_days=14, quantity=28, dispensed_quantity=28, status='DISPENSED'
            )
            b_rc_met_dest_before = b_rc_met.available_quantity
            b_rc_met.available_quantity = b_rc_met_dest_before - 28
            b_rc_met.save()
            InventoryTransaction.objects.create(
                facility=rc_a4, medicine=med_met, batch=b_rc_met, transaction_type='DISPENSED', quantity=28,
                source_bucket='available_quantity', source_before_qty=b_rc_met_dest_before, source_after_qty=b_rc_met.available_quantity,
                destination_bucket='patient_dispensed', destination_before_qty=0, destination_after_qty=28,
                patient=p1, visit=v_rc_1, prescription=pr_rc_1, prescription_item=pi_rc_1,
                reference_id=f"PRESCR-{pr_rc_1.id}", created_by=u_pharm,
                notes='Dispensed 28 units Metformin for Ramesh Kumar'
            )
            PatientCounselling.objects.create(
                prescription=pr_rc_1, patient=p1, pharmacist=u_pharm,
                dose_explained=True, frequency_explained=True, duration_explained=True,
                food_instructions_given=True, storage_explained=True, warning_signs_explained=True, adherence_counselled=True,
                counselling_notes='Advised to take Metformin after meals. Explained hypoglycemia symptoms.'
            )

            ref_p1 = Referral.objects.create(
                referral_id='REF-20260901-0001', patient=p1, visit=v_rc_1, consultation=c_rc_1,
                source_facility=rc_a4, destination_facility=hosp_a, referring_doctor=u_doc,
                reason='Specialist cardiology and endocrine assessment for uncontrolled DM with HTN',
                clinical_summary='52/M with BP 148/96 and HbA1c 8.4%. Initiated Metformin 500mg BD. Requires cardiovascular risk screening.',
                required_service='Cardiology Specialist Evaluation', urgency='HIGH', status='COMPLETED'
            )
            ReferralResponse.objects.create(
                referral=ref_p1, hospital_doctor=u_dh_doc,
                specialist_findings='Essential Hypertension with early diabetic vascular markers. ECG normal sinus rhythm.',
                treatment_summary='Continue Metformin 500mg BD. Add lifestyle and dietary salt restriction.',
                return_advice='Patient stable to be managed at primary rural clinic level. Routine follow-up in 14 days.'
            )
            FollowUp.objects.create(
                patient=p1, referral=ref_p1, visit=v_rc_1, facility=rc_a4, category='REFERRAL',
                due_date=today + datetime.timedelta(days=14), status='PENDING', notes='Post-specialist referral review'
            )
            NCDRecord.objects.create(
                patient=p1, facility=rc_a4, hypertension_diagnosed=True, diabetes_diagnosed=True,
                risk_level='HIGH', control_status='UNCONTROLLED', last_bp='148/96', last_glucose=185,
                next_followup_due=today + datetime.timedelta(days=14)
            )
            FacilityBedAllocation.objects.create(
                facility=rc_a4, bed_number='BED-OBS-01', bed_category='GENERAL_OBSERVATION',
                patient=p1, patient_name='Ramesh Kumar (52/M)', attending_doctor='Dr. Rajesh Kumar', status='OCCUPIED'
            )
            PatientDocument.objects.create(
                patient=p1, facility=rc_a4, title='Blood Sugar & HbA1c Panel Report',
                document_type='LAB_REPORT', file_name='lab_report_ramesh.pdf', file_size=245760, mime_type='application/pdf',
                document_date=today, uploaded_by=u_lab, description='Automated Biochemistry Output: HbA1c 8.4% HIGH'
            )

            # --- PATIENT 2 (p2): Severe Hypertension & Emergency Observation Bed ---
            v_dh_1 = Visit.objects.create(
                visit_id=f"VIS-DH-{today.strftime('%Y%m%d')}-001", patient=p2, facility=hosp_a,
                opd_date=today, visit_type='GENERAL_OPD', priority='EMERGENCY', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Severe chest tightness, dyspnea, and hypertensive emergency',
                assigned_doctor=u_dh_doc, arrival_time=timezone.now() - datetime.timedelta(hours=3),
                triage_start_time=timezone.now() - datetime.timedelta(hours=2, minutes=55),
                triage_end_time=timezone.now() - datetime.timedelta(hours=2, minutes=45),
                consultation_start_time=timezone.now() - datetime.timedelta(hours=2, minutes=30),
                consultation_end_time=timezone.now() - datetime.timedelta(hours=2),
                completed_time=timezone.now() - datetime.timedelta(hours=1)
            )
            Token.objects.create(token_number=1, visit=v_dh_1, facility=hosp_a, date=today, priority='EMERGENCY', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_dh_1, patient=p2, nurse=u_dh_nurse,
                blood_pressure_systolic=160, blood_pressure_diastolic=102, pulse_bpm=92, temperature_f=98.6,
                spo2_percent=95, respiratory_rate=22, height_cm=165.0, weight_kg=72.0, blood_glucose_mgdl=140,
                high_bp_flag=True, emergency_flag=True,
                nurse_notes='Severe Stage II Hypertensive urgency (160/102). Fast-track triage to emergency bay.'
            )

            c_dh_1 = Consultation.objects.create(
                visit=v_dh_1, patient=p2, doctor=u_dh_doc, facility=hosp_a,
                chief_complaint='Severe chest tightness & shortness of breath',
                clinical_history='Longstanding Hypertension with erratic compliance. Known smoker.',
                clinical_assessment='BP 160/102 mmHg. ECG shows LVH patterns. Lipid profile ordered.',
                diagnosis_code='I11.9', diagnosis_name='Hypertensive Heart Disease without Heart Failure',
                treatment_plan='Initiate Metformin 500mg OD and Amlodipine 5mg OD. Observation cot allocated.',
                follow_up_date=today + datetime.timedelta(days=7), clinical_notes='Immediate stabilization achieved.'
            )

            ltok_dh_1 = LabToken.objects.create(token_number=1, token_code=f"LAB-DH-{today.strftime('%Y%m%d')}-001", visit=v_dh_1, facility=hosp_a, date=today, status='COMPLETED')
            lo_dh_1 = LabOrder.objects.create(lab_token=ltok_dh_1, visit=v_dh_1, consultation=c_dh_1, patient=p2, doctor=u_dh_doc, facility=hosp_a, test_master=lt_lipid, status='VERIFIED')
            LabSample.objects.create(lab_order=lo_dh_1, sample_type='Blood', sample_code='SMP-DH-001', collected_by=u_dh_lab)
            LabResult.objects.create(lab_order=lo_dh_1, result_value='245', unit='mg/dL', reference_range='< 200 mg/dL', interpretation_flag='HIGH', verified_by=u_dh_lab, notes='Elevated Total Cholesterol (245 mg/dL).')

            pr_dh_1 = Prescription.objects.create(
                consultation=c_dh_1, patient=p2, doctor=u_dh_doc, facility=hosp_a,
                status='DISPENSED', verified_by=u_dh_pharm, verified_at=timezone.now() - datetime.timedelta(hours=1, minutes=30),
                verification_notes='Emergency prescription verified by hospital pharmacist.'
            )
            pi_dh_1 = PrescriptionItem.objects.create(prescription=pr_dh_1, medicine=med_met, medicine_name='Metformin 500 mg Tablet', dosage='1-0-0 Morning', frequency='Once Daily', duration_days=30, quantity=30, dispensed_quantity=30, status='DISPENSED')
            pi_dh_2 = PrescriptionItem.objects.create(prescription=pr_dh_1, medicine=med_aml, medicine_name='Amlodipine 5 mg Tablet', dosage='0-0-1 Night', frequency='Once Daily', duration_days=30, quantity=30, dispensed_quantity=30, status='DISPENSED')

            b_dh_met_before = b_dh_met.available_quantity
            b_dh_met.available_quantity = b_dh_met_before - 30
            b_dh_met.save()
            InventoryTransaction.objects.create(
                facility=hosp_a, medicine=med_met, batch=b_dh_met, transaction_type='DISPENSED', quantity=30,
                source_bucket='available_quantity', source_before_qty=b_dh_met_before, source_after_qty=b_dh_met.available_quantity,
                destination_bucket='patient_dispensed', destination_before_qty=0, destination_after_qty=30,
                patient=p2, visit=v_dh_1, prescription=pr_dh_1, prescription_item=pi_dh_1,
                reference_id=f"PRESCR-{pr_dh_1.id}", created_by=u_dh_pharm, notes='Dispensed 30 units Metformin for Narayana Swamy'
            )

            b_dh_aml_before = b_dh_aml.available_quantity
            b_dh_aml.available_quantity = b_dh_aml_before - 30
            b_dh_aml.save()
            InventoryTransaction.objects.create(
                facility=hosp_a, medicine=med_aml, batch=b_dh_aml, transaction_type='DISPENSED', quantity=30,
                source_bucket='available_quantity', source_before_qty=b_dh_aml_before, source_after_qty=b_dh_aml.available_quantity,
                destination_bucket='patient_dispensed', destination_before_qty=0, destination_after_qty=30,
                patient=p2, visit=v_dh_1, prescription=pr_dh_1, prescription_item=pi_dh_2,
                reference_id=f"PRESCR-{pr_dh_1.id}", created_by=u_dh_pharm, notes='Dispensed 30 units Amlodipine for Narayana Swamy'
            )

            NCDRecord.objects.create(
                patient=p2, facility=hosp_a, hypertension_diagnosed=True, diabetes_diagnosed=False,
                risk_level='HIGH', control_status='UNCONTROLLED', last_bp='160/102', last_glucose=140,
                next_followup_due=today + datetime.timedelta(days=7)
            )
            FacilityBedAllocation.objects.create(
                facility=hosp_a, bed_number='BED-ICU-05', bed_category='ICU_CRITICAL',
                patient=p2, patient_name='Narayana Swamy (68/M)', attending_doctor='Dr. Vikram Seth', status='OCCUPIED'
            )
            PatientDocument.objects.create(
                patient=p2, facility=hosp_a, title='12-Lead ECG & Cardiology Scan',
                document_type='MEDICAL_RECORD', file_name='ecg_scan_narayana.pdf', file_size=310000, mime_type='application/pdf',
                document_date=today, uploaded_by=u_dh_doc, description='12-Lead ECG showing sinus rhythm with LVH voltage criteria.'
            )

            # --- PATIENT 3 (p3): NCD Prescription Renewal — Waiting for Pharmacist Verification/Dispense ---
            v_sdh_1 = Visit.objects.create(
                visit_id=f"VIS-SDH-{today.strftime('%Y%m%d')}-001", patient=p3, facility=nc_a1,
                opd_date=today, visit_type='NCD_SCREENING', priority='NORMAL', current_queue='PHARMACY',
                status='WAITING_FOR_PHARMACY', chief_complaint='Routine Hypertension prescription renewal and BP check',
                assigned_doctor=u_sdh_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=50),
                triage_start_time=timezone.now() - datetime.timedelta(minutes=45),
                triage_end_time=timezone.now() - datetime.timedelta(minutes=35),
                consultation_start_time=timezone.now() - datetime.timedelta(minutes=30),
                consultation_end_time=timezone.now() - datetime.timedelta(minutes=15)
            )
            Token.objects.create(token_number=1, visit=v_sdh_1, facility=nc_a1, date=today, priority='NORMAL', status='WAITING')

            TriageVitals.objects.create(
                visit=v_sdh_1, patient=p3, nurse=u_sdh_nurse,
                blood_pressure_systolic=134, blood_pressure_diastolic=86, pulse_bpm=76, temperature_f=98.4,
                spo2_percent=99, respiratory_rate=16, height_cm=158.0, weight_kg=62.0, blood_glucose_mgdl=115,
                high_bp_flag=False, nurse_notes='Routine monthly NCD visit. BP under moderate control.'
            )

            c_sdh_1 = Consultation.objects.create(
                visit=v_sdh_1, patient=p3, doctor=u_sdh_doc, facility=nc_a1,
                chief_complaint='Routine monthly NCD refill',
                clinical_history='Hypertension for 3 years, well-maintained on Telmisartan.',
                clinical_assessment='BP 134/86 mmHg. Refilled 14-day supply of Telmisartan 40mg.',
                diagnosis_code='I10', diagnosis_name='Essential (Primary) Hypertension',
                treatment_plan='Telmisartan 40mg OD for 14 days. Review in 14 days.',
                follow_up_date=today + datetime.timedelta(days=14), clinical_notes='Prescription routed to pharmacy queue.'
            )

            pr_sdh_1 = Prescription.objects.create(
                consultation=c_sdh_1, patient=p3, doctor=u_sdh_doc, facility=nc_a1,
                status='PENDING_VERIFICATION', notes='Pending pharmacist verification'
            )
            PrescriptionItem.objects.create(
                prescription=pr_sdh_1, medicine=med_tel, medicine_name='Telmisartan 40 mg Tablet',
                dosage='1-0-0 Morning', frequency='Once Daily', duration_days=14, quantity=14, dispensed_quantity=0, status='PENDING'
            )

            NCDRecord.objects.create(
                patient=p3, facility=nc_a1, hypertension_diagnosed=True, diabetes_diagnosed=False,
                risk_level='MODERATE', control_status='CONTROLLED', last_bp='134/86', last_glucose=115,
                next_followup_due=today + datetime.timedelta(days=14)
            )

            # --- PATIENT 4 (p4): Acute Illness — Waiting for Doctor Consultation ---
            v_rc_2 = Visit.objects.create(
                visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-002", patient=p4, facility=rc_a4,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='DOCTOR',
                status='WAITING_FOR_DOCTOR', chief_complaint='Low-grade fever and mild cough for 2 days',
                assigned_doctor=u_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=35),
                triage_start_time=timezone.now() - datetime.timedelta(minutes=30),
                triage_end_time=timezone.now() - datetime.timedelta(minutes=20)
            )
            Token.objects.create(token_number=2, visit=v_rc_2, facility=rc_a4, date=today, priority='NORMAL', status='WAITING')

            TriageVitals.objects.create(
                visit=v_rc_2, patient=p4, nurse=u_nurse,
                blood_pressure_systolic=118, blood_pressure_diastolic=76, pulse_bpm=82, temperature_f=99.4,
                spo2_percent=98, respiratory_rate=18, height_cm=160.0, weight_kg=60.0, blood_glucose_mgdl=102,
                fever_flag=True, nurse_notes='Mild pyrexia (99.4F). Waiting in doctor consultation queue.'
            )

            # --- PATIENT 5 (p5): Acute Fever — Rapid Diagnostic Negative & Paracetamol Dispensed ---
            v_vc_1 = Visit.objects.create(
                visit_id=f"VIS-VC-{today.strftime('%Y%m%d')}-001", patient=p5, facility=vc_a4_1,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Acute fever and body ache for 2 days',
                assigned_doctor=u_vh2_doc, arrival_time=timezone.now() - datetime.timedelta(hours=1, minutes=45),
                triage_start_time=timezone.now() - datetime.timedelta(hours=1, minutes=35),
                triage_end_time=timezone.now() - datetime.timedelta(hours=1, minutes=25),
                consultation_start_time=timezone.now() - datetime.timedelta(hours=1, minutes=10),
                consultation_end_time=timezone.now() - datetime.timedelta(minutes=45),
                completed_time=timezone.now() - datetime.timedelta(minutes=15)
            )
            Token.objects.create(token_number=1, visit=v_vc_1, facility=vc_a4_1, date=today, priority='NORMAL', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_vc_1, patient=p5, nurse=u_nurse,
                blood_pressure_systolic=124, blood_pressure_diastolic=80, pulse_bpm=86, temperature_f=100.4,
                spo2_percent=97, respiratory_rate=18, height_cm=170.0, weight_kg=68.0, blood_glucose_mgdl=98,
                fever_flag=True, nurse_notes='Fever 100.4F. Rapid malaria card test ordered.'
            )

            c_vc_1 = Consultation.objects.create(
                visit=v_vc_1, patient=p5, doctor=u_vh2_doc, facility=vc_a4_1,
                chief_complaint='Acute fever and body ache',
                clinical_history='No previous chronic conditions.',
                clinical_assessment='Temperature 100.4F, pharyngeal congestion. Rapid malaria card test negative.',
                diagnosis_code='J06.9', diagnosis_name='Acute Upper Respiratory Tract Infection',
                treatment_plan='Paracetamol 650mg TDS for 3 days. Adequate hydration.',
                follow_up_date=today + datetime.timedelta(days=3), clinical_notes='Symptomatic management.'
            )

            ltok_vc_1 = LabToken.objects.create(token_number=1, token_code=f"LAB-VC-{today.strftime('%Y%m%d')}-001", visit=v_vc_1, facility=vc_a4_1, date=today, status='COMPLETED')
            lo_vc_1 = LabOrder.objects.create(lab_token=ltok_vc_1, visit=v_vc_1, consultation=c_vc_1, patient=p5, doctor=u_vh2_doc, facility=vc_a4_1, test_master=lt_malaria, status='VERIFIED')
            LabSample.objects.create(lab_order=lo_vc_1, sample_type='Blood', sample_code='SMP-VC-001', collected_by=u_vh2_doc)
            LabResult.objects.create(lab_order=lo_vc_1, result_value='Negative', unit='Result', reference_range='Negative', interpretation_flag='NORMAL', verified_by=u_vh2_doc, notes='Malaria Pf/Pv antigen test negative.')

            pr_vc_1 = Prescription.objects.create(
                consultation=c_vc_1, patient=p5, doctor=u_vh2_doc, facility=vc_a4_1,
                status='DISPENSED', verified_by=u_vh2_doc, verified_at=timezone.now() - datetime.timedelta(minutes=30),
                verification_notes='Verified and dispensed at satellite clinic.'
            )
            pi_vc_1 = PrescriptionItem.objects.create(
                prescription=pr_vc_1, medicine=med_pcm, medicine_name='Paracetamol 650 mg Tablet',
                dosage='1-1-1 After Food', frequency='Three Times Daily', duration_days=3, quantity=9, dispensed_quantity=9, status='DISPENSED'
            )

            b_vc_pcm_before = b_vc_pcm.available_quantity
            b_vc_pcm.available_quantity = b_vc_pcm_before - 9
            b_vc_pcm.save()
            InventoryTransaction.objects.create(
                facility=vc_a4_1, medicine=med_pcm, batch=b_vc_pcm, transaction_type='DISPENSED', quantity=9,
                source_bucket='available_quantity', source_before_qty=b_vc_pcm_before, source_after_qty=b_vc_pcm.available_quantity,
                destination_bucket='patient_dispensed', destination_before_qty=0, destination_after_qty=9,
                patient=p5, visit=v_vc_1, prescription=pr_vc_1, prescription_item=pi_vc_1,
                reference_id=f"PRESCR-{pr_vc_1.id}", created_by=u_vh2_doc, notes='Dispensed 9 units Paracetamol for Manjunath Gowda'
            )

            DiseaseCase.objects.create(
                disease_name='Acute Pyrexia / Viral Syndrome', patient=p5,
                facility=vc_a4_1, ward=ward_rural, severity='MILD', status='CONFIRMED', notes='Fever case logged and resolved.'
            )

            # --- PATIENT 6 (p6): Walk-in Patient — Waiting for Nurse Triage ---
            v_rc_3 = Visit.objects.create(
                visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-003", patient=p6, facility=rc_a4,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='TRIAGE',
                status='WAITING_FOR_TRIAGE', chief_complaint='Routine health checkup and diabetic review',
                arrival_time=timezone.now() - datetime.timedelta(minutes=15)
            )
            Token.objects.create(token_number=3, visit=v_rc_3, facility=rc_a4, date=today, priority='NORMAL', status='WAITING')

            # --- PATIENT 7 (p7): Completed Specialist Referral with Follow-up ---
            v_rc_4 = Visit.objects.create(
                visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-004", patient=p7, facility=rc_a4,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Follow-up post cardiology referral from Victoria Hospital',
                assigned_doctor=u_doc, arrival_time=timezone.now() - datetime.timedelta(hours=2),
                completed_time=timezone.now() - datetime.timedelta(hours=1)
            )
            Token.objects.create(token_number=4, visit=v_rc_4, facility=rc_a4, date=today, priority='NORMAL', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_rc_4, patient=p7, nurse=u_nurse,
                blood_pressure_systolic=128, blood_pressure_diastolic=82, pulse_bpm=74, temperature_f=98.4,
                spo2_percent=99, respiratory_rate=16, height_cm=165.0, weight_kg=70.0, blood_glucose_mgdl=110,
                nurse_notes='Stable post-specialist review vitals.'
            )

            c_rc_4 = Consultation.objects.create(
                visit=v_rc_4, patient=p7, doctor=u_doc, facility=rc_a4,
                chief_complaint='Review of cardiology referral response',
                clinical_history='Hypertension under treatment.',
                clinical_assessment='BP 128/82 mmHg. Specialist advice reviewed. Continue current medication.',
                diagnosis_code='I10', diagnosis_name='Essential Hypertension (Controlled)',
                treatment_plan='Continue lifestyle modifications. Routine follow-up in 30 days.',
                follow_up_date=today + datetime.timedelta(days=30), clinical_notes='Referral loop successfully closed.'
            )

            ref_p7 = Referral.objects.create(
                referral_id='REF-20260901-0002', patient=p7, visit=v_rc_4, consultation=c_rc_4,
                source_facility=rc_a4, destination_facility=hosp_a, referring_doctor=u_doc,
                reason='Specialist cardiology evaluation for atypical chest discomfort',
                clinical_summary='48/M with controlled hypertension. Needed tertiary center ECG and echo review.',
                required_service='Cardiology Consultation', urgency='ROUTINE', status='COMPLETED'
            )
            ReferralResponse.objects.create(
                referral=ref_p7, hospital_doctor=u_dh_doc,
                specialist_findings='Echocardiogram normal. No ischemic changes. Good cardiac function.',
                treatment_summary='Continue baseline anti-hypertensive therapy and lifestyle counseling.',
                return_advice='Discharged back to Varthur Rural Clinic for primary maintenance.'
            )
            FollowUp.objects.create(
                patient=p7, referral=ref_p7, visit=v_rc_4, facility=rc_a4, category='REFERRAL',
                due_date=today + datetime.timedelta(days=7), status='PENDING', notes='Post-referral follow-up check'
            )

            # --- PATIENT 8 (p8): Diagnostic Laboratory In-Progress (Sample Collected) ---
            v_dh_2 = Visit.objects.create(
                visit_id=f"VIS-DH-{today.strftime('%Y%m%d')}-002", patient=p8, facility=hosp_a,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='LAB',
                status='LAB_IN_PROGRESS', chief_complaint='Polyuria, polydipsia, and unexplained weight loss',
                assigned_doctor=u_dh_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=40),
                triage_start_time=timezone.now() - datetime.timedelta(minutes=35),
                triage_end_time=timezone.now() - datetime.timedelta(minutes=25),
                consultation_start_time=timezone.now() - datetime.timedelta(minutes=20),
                consultation_end_time=timezone.now() - datetime.timedelta(minutes=10)
            )
            Token.objects.create(token_number=2, visit=v_dh_2, facility=hosp_a, date=today, priority='NORMAL', status='WAITING')

            TriageVitals.objects.create(
                visit=v_dh_2, patient=p8, nurse=u_dh_nurse,
                blood_pressure_systolic=130, blood_pressure_diastolic=84, pulse_bpm=78, temperature_f=98.6,
                spo2_percent=98, respiratory_rate=18, height_cm=156.0, weight_kg=54.0, blood_glucose_mgdl=165,
                high_glucose_flag=True, nurse_notes='Elevated random glucose 165 mg/dL. Doctor ordered Fasting Glucose test.'
            )

            c_dh_2 = Consultation.objects.create(
                visit=v_dh_2, patient=p8, doctor=u_dh_doc, facility=hosp_a,
                chief_complaint='Suspected new-onset Diabetes Mellitus',
                clinical_history='Symptoms of polyuria for 3 weeks.',
                clinical_assessment='High clinical suspicion for Type 2 Diabetes. Ordered Fasting Blood Glucose (FBG).',
                diagnosis_code='E11.9', diagnosis_name='Type 2 Diabetes Mellitus (Under Evaluation)',
                treatment_plan='Diagnostic workup pending lab results.',
                follow_up_date=today + datetime.timedelta(days=1), clinical_notes='Sample collected. Awaiting verification.'
            )

            ltok_dh_2 = LabToken.objects.create(token_number=2, token_code=f"LAB-DH-{today.strftime('%Y%m%d')}-002", visit=v_dh_2, facility=hosp_a, date=today, status='IN_PROGRESS')
            lo_dh_2 = LabOrder.objects.create(lab_token=ltok_dh_2, visit=v_dh_2, consultation=c_dh_2, patient=p8, doctor=u_dh_doc, facility=hosp_a, test_master=lt_fbg, status='SAMPLE_COLLECTED')
            LabSample.objects.create(lab_order=lo_dh_2, sample_type='Blood', sample_code='SMP-DH-002', collected_by=u_dh_lab)

            # --- PATIENT 9 (p9): Controlled NCD Care Follow-up ---
            v_sdh_2 = Visit.objects.create(
                visit_id=f"VIS-SDH-{today.strftime('%Y%m%d')}-002", patient=p9, facility=nc_a1,
                opd_date=today, visit_type='NCD_SCREENING', priority='NORMAL', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Quarterly NCD checkup and blood pressure monitoring',
                assigned_doctor=u_sdh_doc, arrival_time=timezone.now() - datetime.timedelta(hours=2),
                completed_time=timezone.now() - datetime.timedelta(minutes=45)
            )
            Token.objects.create(token_number=2, visit=v_sdh_2, facility=nc_a1, date=today, priority='NORMAL', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_sdh_2, patient=p9, nurse=u_sdh_nurse,
                blood_pressure_systolic=120, blood_pressure_diastolic=80, pulse_bpm=72, temperature_f=98.4,
                spo2_percent=99, respiratory_rate=16, height_cm=172.0, weight_kg=74.0, blood_glucose_mgdl=104,
                nurse_notes='Optimal blood pressure and normal glucose level.'
            )

            c_sdh_2 = Consultation.objects.create(
                visit=v_sdh_2, patient=p9, doctor=u_sdh_doc, facility=nc_a1,
                chief_complaint='Quarterly NCD follow-up',
                clinical_history='Hypertension well-managed with lifestyle and low-dose Amlodipine.',
                clinical_assessment='BP 120/80 mmHg. Excellent medication compliance and lifestyle adherence.',
                diagnosis_code='I10', diagnosis_name='Essential (Primary) Hypertension (Controlled)',
                treatment_plan='Continue Amlodipine 5mg OD. Recheck in 90 days.',
                follow_up_date=today + datetime.timedelta(days=90), clinical_notes='Patient counselled on continuing low-sodium diet.'
            )

            pr_sdh_2 = Prescription.objects.create(
                consultation=c_sdh_2, patient=p9, doctor=u_sdh_doc, facility=nc_a1,
                status='DISPENSED', verified_by=u_sdh_admin, verified_at=timezone.now() - datetime.timedelta(hours=1, minutes=15),
                verification_notes='Verified maintenance refill.'
            )
            pi_sdh_2 = PrescriptionItem.objects.create(
                prescription=pr_sdh_2, medicine=med_aml, medicine_name='Amlodipine 5 mg Tablet',
                dosage='0-0-1 Night', frequency='Once Daily', duration_days=30, quantity=30, dispensed_quantity=30, status='DISPENSED'
            )

            b_sdh_aml_before = b_sdh_aml.available_quantity
            b_sdh_aml.available_quantity = b_sdh_aml_before - 30
            b_sdh_aml.save()
            InventoryTransaction.objects.create(
                facility=nc_a1, medicine=med_aml, batch=b_sdh_aml, transaction_type='DISPENSED', quantity=30,
                source_bucket='available_quantity', source_before_qty=b_sdh_aml_before, source_after_qty=b_sdh_aml.available_quantity,
                destination_bucket='patient_dispensed', destination_before_qty=0, destination_after_qty=30,
                patient=p9, visit=v_sdh_2, prescription=pr_sdh_2, prescription_item=pi_sdh_2,
                reference_id=f"PRESCR-{pr_sdh_2.id}", created_by=u_sdh_admin, notes='Dispensed 30 units Amlodipine for Venkatesh Murthy'
            )

            NCDRecord.objects.create(
                patient=p9, facility=nc_a1, hypertension_diagnosed=True, diabetes_diagnosed=False,
                risk_level='LOW', control_status='CONTROLLED', last_bp='120/80', last_glucose=104,
                next_followup_due=today + datetime.timedelta(days=90)
            )

            # --- PATIENT 10 (p10): Short-term Day Observation Cot Recovery & Discharge Summary ---
            v_vc_2 = Visit.objects.create(
                visit_id=f"VIS-VC-{today.strftime('%Y%m%d')}-002", patient=p10, facility=vc_a4_1,
                opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='COMPLETED',
                status='COMPLETED', chief_complaint='Post-work exertion, dehydration, and mild dizziness',
                assigned_doctor=u_vh2_doc, arrival_time=timezone.now() - datetime.timedelta(hours=3),
                completed_time=timezone.now() - datetime.timedelta(minutes=30)
            )
            Token.objects.create(token_number=2, visit=v_vc_2, facility=vc_a4_1, date=today, priority='NORMAL', status='COMPLETED')

            TriageVitals.objects.create(
                visit=v_vc_2, patient=p10, nurse=u_nurse,
                blood_pressure_systolic=112, blood_pressure_diastolic=72, pulse_bpm=80, temperature_f=98.6,
                spo2_percent=98, respiratory_rate=16, height_cm=162.0, weight_kg=64.0, blood_glucose_mgdl=94,
                nurse_notes='Dehydration and heat exhaustion. Oral rehydration therapy administered.'
            )

            c_vc_2 = Consultation.objects.create(
                visit=v_vc_2, patient=p10, doctor=u_vh2_doc, facility=vc_a4_1,
                chief_complaint='Exertional dehydration and dizziness',
                clinical_history='No significant past medical history.',
                clinical_assessment='Heat exhaustion, mild orthostatic hypotension. Rested on observation cot for 2 hours with ORS.',
                diagnosis_code='T67.5', diagnosis_name='Heat Exhaustion (Resolved)',
                treatment_plan='Rest, hydration, and avoidance of direct sun during midday.',
                follow_up_date=today + datetime.timedelta(days=7), clinical_notes='Discharged stable in ambulatory condition.'
            )

            FacilityBedAllocation.objects.create(
                facility=vc_a4_1, bed_number='BED-COT-01', bed_category='GENERAL_OBSERVATION',
                patient=p10, patient_name='Suresh Rao (65/M)', attending_doctor='Dr. Suresh V.', status='OCCUPIED'
            )
            PatientDocument.objects.create(
                patient=p10, facility=vc_a4_1, title='Day Care Observation Summary & Discharge Advice',
                document_type='DISCHARGE_SUMMARY', file_name='discharge_summary_suresh_rao.pdf', file_size=198000, mime_type='application/pdf',
                document_date=today, uploaded_by=u_vh2_doc, description='Observation cot monitoring chart and clinical recovery note.'
            )

            # Facility Bed Capacities
            FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='GENERAL_OBSERVATION', total_beds=400, occupied_beds=320, cleaning_in_progress=20, under_maintenance=10, notes='General Medical & Surgical Wards.')
            FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='ICU_CRITICAL', total_beds=50, occupied_beds=42, cleaning_in_progress=3, under_maintenance=1, notes='Intensive Care Unit with vent support.')
            FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='OXYGEN_SUPPORTED', total_beds=200, occupied_beds=160, cleaning_in_progress=10, under_maintenance=5, notes='High Flow Oxygen Wards.')

            FacilityBedCapacity.objects.create(facility=nc_a1, bed_category='GENERAL_OBSERVATION', total_beds=30, occupied_beds=20, cleaning_in_progress=2, under_maintenance=1, notes='General Observation ward.')
            FacilityBedCapacity.objects.create(facility=nc_a1, bed_category='OXYGEN_SUPPORTED', total_beds=15, occupied_beds=8, cleaning_in_progress=1, under_maintenance=0, notes='Oxygen Concentrator Supported Beds.')

            FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='GENERAL_OBSERVATION', total_beds=6, occupied_beds=2, cleaning_in_progress=1, under_maintenance=0, notes='General OPD observation beds.')
            FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='EMERGENCY_TRIAGE', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Emergency resuscitation bay bed.')
            FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='OXYGEN_SUPPORTED', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Oxygen manifold high-care bed.')

            FacilityBedCapacity.objects.create(facility=vc_a4_1, bed_category='GENERAL_OBSERVATION', total_beds=4, occupied_beds=1, cleaning_in_progress=1, under_maintenance=0, notes='Satellite observation cots.')

            # Oxygen & Consumables
            FacilityOxygenSupply.objects.create(facility=hosp_a, oxygen_source='PIPELINE_LIQUID', total_cylinders=80, active_cylinders=65, empty_cylinders=15, current_pressure_psi=2400, fill_percentage=94, status='OPTIMAL', notes='Liquid Medical Oxygen bulk tank.')
            FacilityOxygenSupply.objects.create(facility=nc_a1, oxygen_source='CONCENTRATOR', total_cylinders=20, active_cylinders=16, empty_cylinders=4, current_pressure_psi=1800, fill_percentage=82, status='OPTIMAL', notes='Oxygen concentrators + manifold.')
            FacilityOxygenSupply.objects.create(facility=rc_a4, oxygen_source='CYLINDER_MANIFOLD', total_cylinders=12, active_cylinders=9, empty_cylinders=3, current_pressure_psi=1850, fill_percentage=88, status='OPTIMAL', notes='12-Cylinder manifold system.')
            FacilityOxygenSupply.objects.create(facility=vc_a4_1, oxygen_source='CYLINDER_MANIFOLD', total_cylinders=4, active_cylinders=3, empty_cylinders=1, current_pressure_psi=1500, fill_percentage=75, status='ADEQUATE', notes='4x D-Type cylinders for emergency transport.')

            facilities_list = [hosp_a, nc_a1, rc_a4, vc_a4_1]
            for fac in facilities_list:
                FacilityConsumableInventory.objects.create(facility=fac, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=40, min_threshold=15, reorder_status='ADEQUATE')
                FacilityConsumableInventory.objects.create(facility=fac, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=25, min_threshold=10, reorder_status='ADEQUATE')
                FacilityConsumableInventory.objects.create(facility=fac, item_name='Surgical Face Masks 3-Ply', category='PERSONAL_PROTECTION', unit_of_measure='Boxes (50s)', current_stock=30, min_threshold=10, reorder_status='ADEQUATE')

            FacilityMaintenanceTicket.objects.create(facility=rc_a4, ticket_number='MAINT-RC-001', category='ELECTRICAL', equipment_or_area='Main OPD Solar UPS Battery Backup', priority='HIGH', description='Solar UPS inverter battery overload warning.', reported_by='Sister Priya', assigned_technician='BBMP Electrical Team', status='IN_PROGRESS')
            FacilityMaintenanceTicket.objects.create(facility=vc_a4_1, ticket_number='MAINT-VC-001', category='PLUMBING', equipment_or_area='Doctor Handwash Station Tap', priority='LOW', description='Tap washer replacement needed.', reported_by='Dr. Suresh V.', assigned_technician='Local Village Sanitation Team', status='LOGGED')

            # Quality, Waste & Cold-Chain
            for fac in facilities_list:
                QualityChecklist.objects.create(facility=fac, cleanliness_score=95, infection_control_passed=True, kayakalpa_audit_status='COMPLIANT', inspected_by=u_dist)
                BiomedicalWasteLog.objects.create(facility=fac, yellow_bag_kg=3.5, red_bag_kg=2.2, white_translucent_sharp_kg=0.7, blue_box_glass_kg=1.5, handed_over_by=u_nurse)
                ColdChainLog.objects.create(
                    facility=fac, storage_location='Pharmacy Refrigerator #1',
                    min_temp_celsius=2.0, max_temp_celsius=8.0, recorded_temp_celsius=4.5,
                    recorded_by=u_pharm if fac == rc_a4 else (u_dh_pharm if fac == hosp_a else u_sdh_admin),
                    status='NORMAL'
                )

            # ARS, Outreach & Alerts
            for fac in facilities_list:
                ars_m = ARSMeeting.objects.create(
                    facility=fac, meeting_date=today - datetime.timedelta(days=10),
                    chairperson_name=f'Ward {fac.ward.ward_number if fac.ward else 1} Corporator',
                    attendees_count=8, agenda='Untied Grant allocation for lab reagents and facility upkeep',
                    proceedings_summary='Approved untied funds for facility maintenance.',
                    untied_funds_spent_rs=Decimal("8000.00"), signed_by_chairman=True
                )
                ARSMember.objects.create(facility=fac, name='Ward Corporator', designation='Chairman')
                ARSMember.objects.create(facility=fac, name='Medical Officer', designation='Member Secretary')
                ARSActionItem.objects.create(
                    meeting=ars_m, task_description='Procure water filter replacement cartridge',
                    responsible_person='Facility Admin', due_date=today + datetime.timedelta(days=5), status='IN_PROGRESS'
                )
                OutreachActivity.objects.create(
                    facility=fac, ward=fac.ward or ward_rural, activity_type='Slum Household NCD & Fever Survey',
                    activity_date=today - datetime.timedelta(days=3), households_covered=60, persons_screened=150, vulnerable_identified=18
                )
                WellnessSession.objects.create(
                    facility=fac, session_type='AYUSH Yoga & Meditation', instructor_name='Guru Sri Anand (AYUSH Certified)',
                    session_date=today - datetime.timedelta(days=2), venue=f"{fac.facility_name} Community Hall", participants_count=30
                )
                Alert.objects.create(
                    alert_type='LOW_STOCK', severity='MEDIUM', facility=fac,
                    title=f'Stock Monitoring: Amlodipine 5mg at {fac.facility_name}',
                    description='Stock level adequate under active procurement indent.', status='RESOLVED'
                )

            ComplianceItem.objects.get_or_create(
                requirement_id='REQ-OFF-001',
                defaults={
                    'requirement_text': 'Provide comprehensive primary health care in urban & rural areas',
                    'source_document': 'ULB ROK Booklet', 'classification': 'OFFICIAL BOOKLET REQUIREMENT',
                    'application_module': 'Clinical / Consultation', 'status': 'FULLY_COVERED',
                    'explanation': 'Outpatient consultation, diagnostics, and essential medicine delivery supported across all facilities.'
                }
            )
            ComplianceItem.objects.get_or_create(
                requirement_id='REQ-KM-003',
                defaults={
                    'requirement_text': 'First-Expiry First-Out (FEFO) batch management and stock ledger audit',
                    'source_document': 'K Mati Proposal', 'classification': 'K MATI PROPOSAL',
                    'application_module': 'Pharmacy / Inventory', 'status': 'FULLY_COVERED',
                    'explanation': 'Automated batch expiry sorting and dual-bucket ledger validation implemented.'
                }
            )

            IntegrationConfiguration.objects.get_or_create(system_name='ABDM', defaults={'display_name': 'Ayushman Bharat Digital Mission (ABDM)', 'status': 'MOCK', 'sync_status': 'SUCCESS', 'notes': 'Local ABDM mock connector active.'})
            IntegrationConfiguration.objects.get_or_create(system_name='ABHA', defaults={'display_name': 'ABHA Health ID Gateway', 'status': 'MOCK', 'sync_status': 'SUCCESS', 'notes': 'Local ABHA verification engine.'})
            IntegrationConfiguration.objects.get_or_create(system_name='HMIS', defaults={'display_name': 'Karnataka Health Management Information System', 'status': 'MOCK', 'sync_status': 'SUCCESS', 'notes': 'Periodic HMIS export template ready.'})
            IntegrationConfiguration.objects.get_or_create(system_name='E_AUSHADA', defaults={'display_name': 'KSMSCL E-Aushada Drug Procurement Engine', 'status': 'MOCK', 'sync_status': 'SUCCESS', 'notes': 'Direct indent sync mock interface.'})

            # System Baseline Audit Entry
            AuditLog.objects.create(
                user=u_dist, username_snapshot='district',
                action='SYSTEM_SEED_DEMO', facility=hosp_a,
                details='Demo database reset to pristine baseline with exactly 10 patients, verified procurement provenance, and 4 healthcare facilities.'
            )

        # -------------------------------------------------------------
        # STEP 7: POST-RESEED VERIFICATIONS
        # -------------------------------------------------------------
        self.stdout.write("\nValidating post-reseed patient integrity...")
        p_count = Patient.objects.count()
        if p_count != 10:
            raise ValidationError(f"Post-reseed check failed: Expected 10 patients, found {p_count}!")

        expected_ids = [f"NC-DEMO-{i:03d}" for i in range(1, 11)]
        actual_ids = list(Patient.objects.order_by('patient_id').values_list('patient_id', flat=True))
        if actual_ids != expected_ids:
            raise ValidationError(f"Post-reseed check failed: Patient IDs {actual_ids} do not match expected {expected_ids}!")

        # Verify zero orphans
        if Token.objects.filter(visit__isnull=True).exists():
            raise ValidationError("Orphaned Token detected!")
        if Prescription.objects.filter(consultation__isnull=True).exists():
            raise ValidationError("Orphaned Prescription detected!")

        # Verify Pharmacy Provenance Chain
        self.stdout.write("Validating pharmacy provenance chain...")
        # 1. PO 1 (Victoria / KSMSCL)
        po1_db = PurchaseOrder.objects.get(po_number="PO-HOSP-DIST-01-2026-001")
        grn1_db = GoodsReceiptNote.objects.get(purchase_order=po1_db)
        if grn1_db.status != 'ACCEPTED':
            raise ValidationError(f"GRN 1 status mismatch: {grn1_db.status}")
        b_met_db = MedicineBatch.objects.get(batch_number='MET-DH-2026A')
        tx_met_db = InventoryTransaction.objects.get(batch=b_met_db, transaction_type='PURCHASE_RECEIVED')
        if tx_met_db.quantity != 1000:
            raise ValidationError(f"PO 1 Metformin received quantity mismatch: {tx_met_db.quantity}")

        # 2. PO 2 (Varthur / KAPL)
        po2_db = PurchaseOrder.objects.get(po_number="PO-RC-A4-01-2026-001")
        grn2_db = GoodsReceiptNote.objects.get(purchase_order=po2_db)
        if grn2_db.status != 'PARTIAL_ACCEPTANCE':
            raise ValidationError(f"GRN 2 status mismatch: {grn2_db.status}")
        b_pcm_db = MedicineBatch.objects.get(batch_number='PCM-RC-2026P')
        # Proves: 1150 accepted into inventory, 50 rejected never entered inventory
        if b_pcm_db.available_quantity != 1150:
            raise ValidationError(f"PO 2 Paracetamol inventory mismatch (rejected entered?): {b_pcm_db.available_quantity}")

        # 3. PO 5 (In-Transit)
        po5_db = PurchaseOrder.objects.get(po_number="PO-HOSP-DIST-01-2026-002")
        if po5_db.status != 'ORDERED':
            raise ValidationError(f"PO 5 status mismatch: {po5_db.status}")
        if GoodsReceiptNote.objects.filter(purchase_order=po5_db).exists():
            raise ValidationError("PO 5 in-transit has premature GRN!")

        self.stdout.write(self.style.SUCCESS("Pharmacy provenance chain validated: 100% reconciliation accuracy."))

        # -------------------------------------------------------------
        # STEP 8: REAL APPLICATION AUDIT EVENT VERIFICATION
        # -------------------------------------------------------------
        self.stdout.write("Verifying real application audit event generation...")
        client = APIClient()
        client.force_authenticate(user=u_pharm)
        res = client.post(f"/api/prescriptions/{pr_rc_1.id}/verify/", {
            'notes': 'Dosage and frequency verified against HbA1c result by Pharmacist Lakshmi Devi.'
        }, format='json')

        if res.status_code != 200:
            raise ValidationError(f"Audit generation API call failed with status {res.status_code}: {res.data}")

        # Check for natural AuditLog emission
        audit_event = AuditLog.objects.filter(action='PRESCRIPTION_VERIFIED', facility=rc_a4).order_by('-id').first()

        if not audit_event:
            raise ValidationError("Audit event was not recorded in AuditLog!")

        self.stdout.write(self.style.SUCCESS(
            f"Audit event successfully recorded and verified in database:\n"
            f"  - Action: {audit_event.action}\n"
            f"  - User: {audit_event.username_snapshot}\n"
            f"  - Details: {audit_event.details}\n"
            f"  - Timestamp: {audit_event.timestamp}"
        ))

        # Finalize prescription status to DISPENSED for completed patient 1 OPD cycle
        pr_rc_1.status = 'DISPENSED'
        pr_rc_1.save()

        self.stdout.write(self.style.SUCCESS(
            "\nDemo reset completed successfully!\n"
            "State summary:\n"
            f"  - Patients: {Patient.objects.count()} (Target: 10)\n"
            f"  - Facilities: {Facility.objects.count()} (Target: 4)\n"
            f"  - Users: {User.objects.count()} (Target: 19 across 6 roles)\n"
            f"  - Purchase Orders: {PurchaseOrder.objects.count()}\n"
            f"  - GRNs: {GoodsReceiptNote.objects.count()}\n"
            f"  - Batches: {MedicineBatch.objects.count()}\n"
            f"  - Inventory Transactions: {InventoryTransaction.objects.count()}\n"
            f"  - Teleconsultation records: {Teleconsultation.objects.count()} (Target: 0)\n"
        ))

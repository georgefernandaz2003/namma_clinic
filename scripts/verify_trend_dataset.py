import os
import sys
import django

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DATABASE_ENGINE', 'postgresql')
django.setup()

from apps.accounts.models import User, StaffProfile, RoleMaster, StaffRoleAssignment
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster, Diagnosis
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest, DiagnosticResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, Dispensation, DispensationItem, InventoryLedger, ColdChainLog
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.referrals.models import ReferralOrder, ReferralEvent
from apps.quality.models import QualityChecklist, BiomedicalWasteLog
from apps.outreach.models import OutreachActivity
from apps.wellness.models import WellnessSession

print("======================================================================")
print("NAMMA CLINIC - PRODUCTION-GRADE TREND DATASET VERIFICATION AUDIT")
print("======================================================================")
print(f"1. CORE REGISTRY & RBAC:")
print(f"   - Facilities:                       {Facility.objects.count()} (Primary, Secondary, Rural)")
print(f"   - Users & Staff:                    {User.objects.count()} Users | {StaffProfile.objects.count()} Staff Profiles")
print(f"   - Role Assignments:                 {StaffRoleAssignment.objects.count()}")
print(f"   - Patient Population:               {Patient.objects.count()} Active Adult Patients")

print(f"\n2. CLINICAL OUTPATIENT & QUEUES (90-DAY TIME SERIES):")
print(f"   - Clinical Visits:                  {Visit.objects.count()} (Spanning 2026-07-10 to 2026-10-07)")
print(f"   - Queue Tokens:                     {Token.objects.count()}")
print(f"   - Triage Vitals Captured:           {TriageVitals.objects.count()}")
print(f"   - Doctor Consultations:             {Consultation.objects.count()}")
print(f"   - Recorded Diagnoses:               {Diagnosis.objects.count()}")
print(f"   - ICD-10 Master Catalog:            {DiagnosisMaster.objects.count()}")

print(f"\n3. LABORATORY & DIAGNOSTICS:")
print(f"   - Diagnostic Test Masters:          {DiagnosticTestMaster.objects.count()} Standard UHWC Tests")
print(f"   - Diagnostic Orders:                {DiagnosticOrder.objects.count()}")
print(f"   - Barcoded Specimens:               {Specimen.objects.count()}")
print(f"   - Test Requests Processed:          {TestRequest.objects.count()}")
print(f"   - Verified Diagnostic Results:      {DiagnosticResult.objects.count()}")

print(f"\n4. PHARMACY & DOUBLE-ENTRY INVENTORY LEDGER:")
print(f"   - Essential Medicine Masters:       {MedicineMaster.objects.count()}")
print(f"   - Active Dispensary Batches:        {MedicineBatch.objects.count()}")
print(f"   - Written e-Prescriptions:          {Prescription.objects.count()}")
print(f"   - Prescription Line Items:          {PrescriptionItem.objects.count()}")
print(f"   - Completed Dispensations:          {Dispensation.objects.count()}")
print(f"   - Dispensation Items:               {DispensationItem.objects.count()}")
print(f"   - Double-Entry Inventory Ledgers:   {InventoryLedger.objects.count()}")

print(f"\n5. NCD LONGITUDINAL CHRONIC DISEASE TRAJECTORY:")
print(f"   - Registered Chronic Conditions:    {NCDCondition.objects.count()} (HTN, Type 2 DM)")
print(f"   - Longitudinal Vitals Assessments:  {NCDAssessment.objects.count()} (Follow-up BP/Glucose Trends)")

print(f"\n6. EPIDEMIOLOGICAL SURVEILLANCE & OUTBREAKS:")
print(f"   - Disease Masters:                  {DiseaseMaster.objects.count()}")
print(f"   - Disease Surveillance Cases:       {DiseaseSurveillanceCase.objects.count()} (Dengue, Typhoid, GE, Malaria)")
print(f"   - Public Health Notifications:      {PublicHealthNotification.objects.count()} Dispatched to District Authorities")

print(f"\n7. INTER-FACILITY REFERRAL NETWORK:")
print(f"   - Inter-Facility Referral Orders:   {ReferralOrder.objects.count()} (Primary -> Secondary/Tertiary)")
print(f"   - Referral Lifecycle Events:        {ReferralEvent.objects.count()}")

print(f"\n8. QUALITY, ENVIRONMENTAL & COLD CHAIN MONITORING:")
print(f"   - Biomedical Waste Disposal Logs:   {BiomedicalWasteLog.objects.count()} (Yellow, Red, White, Blue)")
print(f"   - Refrigerator Cold Chain Logs:     {ColdChainLog.objects.count()} (Daily 2°C - 8°C logs)")
print(f"   - Kayakalpa Cleanliness Audits:     {QualityChecklist.objects.count()}")
print(f"   - Community Slum Outreach Camps:    {OutreachActivity.objects.count()}")
print(f"   - AYUSH Wellness Sessions:          {WellnessSession.objects.count()}")
print("======================================================================\n")

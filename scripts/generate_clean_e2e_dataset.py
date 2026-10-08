"""
Namma Clinic - Complete End-to-End Realistic Clinical Dataset Seeder
=====================================================================
Strict Rules Followed:
1. 100% Realistic Indian / Karnataka Names: ZERO numbers, ZERO alphanumeric codes.
2. Complete end-to-end clinical procedure coverage across ALL sections:
   - Front Desk: Patient registration, ABHA ID, demographics, tokens, queue states.
   - Nurse Triage: Vital signs, calculated flags, BMI, triage notes (both TriageVitals & Triage).
   - Doctor Consultation: History, symptoms, physical exam, ICD-10 diagnosis codes, notes.
   - Laboratory: Diagnostic orders, specimens with barcodes, test requests, results, verified flags.
   - Pharmacy: Prescriptions, pharmacist verification, dispensation, patient counselling.
   - Inventory: Authoritative InventoryLedger double-entry ledger (DISPENSE transaction)
     with batch stock decrement, and legacy InventoryTransaction audit trail.
   - NCD Chronic Registry: NCDCondition, longitudinal NCDAssessment (July-Oct 2026), NCDRecord.
   - IDSP Surveillance: DiseaseSurveillanceCase, lab confirmation, PublicHealthNotification.
   - Referrals: ReferralOrder, ReferralEvent, ReferralResponse, counter-referrals.
   - Follow-up Continuity: FollowUpTask and FollowUp records across care continuum.
   - Today's Live Active Queue: Realistic distribution across Triage, Doctor, Lab, Pharmacy, Completed.
3. Multi-Level Geographic Spread: Facilities across Laggere, Ulsoor, Indiranagar, and Varthur
   spanning West Zone, East Zone, South Zone, and Hoskote Zone; Bengaluru Urban and Rural districts.
"""

import os
import sys
import uuid
import datetime
from collections import defaultdict
from decimal import Decimal

# Ensure backend directory is in path
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
from apps.accounts.models import Person, StaffProfile, StaffRoleAssignment, RoleMaster
from apps.patients.models import Patient, Household, PatientDocument
from apps.visits.models import Visit, Token, FacilityDailyCounter, VisitStatusHistory
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster, Diagnosis
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult, LabTestMaster, LabOrder, LabToken, LabSample, LabResult
)
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation, DispensationItem,
    InventoryLedger, InventoryTransaction, PatientCounselling
)
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask, Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDCondition, NCDAssessment, NCDRecord
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification, DiseaseCase
from apps.audit.models import AuditLog

User = get_user_model()


# ==============================================================================
# 60 DISTINCT, AUTHENTIC KARNATAKA CITIZENS (ABSOLUTE ZERO NUMBERS IN NAMES)
# ==============================================================================
CITIZENS_ROSTER = [
    # Cohort 1: Chronic NCD Patients (Hypertension / Type 2 Diabetes) - 20 Patients
    {"first": "Ramesh", "last": "Gowda", "gender": "MALE", "age": 56, "phone": "9845011001", "abha": "14-8291-4001-1001", "address": "14, 2nd Cross, Parvathi Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Ananya", "last": "Bhat", "gender": "FEMALE", "age": 52, "phone": "9845011002", "abha": "14-8291-4001-1002", "address": "28, MEI Layout Main Road, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Suresh", "last": "Hegde", "gender": "MALE", "age": 61, "phone": "9845011003", "abha": "14-8291-4001-1003", "address": "45, Chowdeshwari Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_BOTH"},
    {"first": "Deepa", "last": "Rao", "gender": "FEMALE", "age": 48, "phone": "9845011004", "abha": "14-8291-4001-1004", "address": "62, Kempegowda Layout, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Venkatesh", "last": "Prasad", "gender": "MALE", "age": 64, "phone": "9845011005", "abha": "14-8291-4001-1005", "address": "81, 3rd Stage, Parvathi Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_BOTH"},
    {"first": "Kavitha", "last": "Kulkarni", "gender": "FEMALE", "age": 50, "phone": "9845011006", "abha": "14-8291-4001-1006", "address": "19, Pipeline Road, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Basavaraj", "last": "Nayak", "gender": "MALE", "age": 58, "phone": "9845011007", "abha": "14-8291-4001-1007", "address": "33, 4th Cross, MEI Layout, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Pooja", "last": "Shetty", "gender": "FEMALE", "age": 46, "phone": "9845011008", "abha": "14-8291-4001-1008", "address": "77, Laggere Ring Road, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Manjunath", "last": "Murthy", "gender": "MALE", "age": 67, "phone": "9845011009", "abha": "14-8291-4001-1009", "address": "12, Someshwara Extension, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_BOTH"},
    {"first": "Sunitha", "last": "Deshmukh", "gender": "FEMALE", "age": 54, "phone": "9845011010", "abha": "14-8291-4001-1010", "address": "51, Vinayaka Layout, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Chetan", "last": "Patil", "gender": "MALE", "age": 49, "phone": "9845011011", "abha": "14-8291-4001-1011", "address": "90, 1st Cross, Chowdeshwari Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Rekha", "last": "Acharya", "gender": "FEMALE", "age": 59, "phone": "9845011012", "abha": "14-8291-4001-1012", "address": "104, Kempegowda Main Road, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Praveen", "last": "Kumar", "gender": "MALE", "age": 63, "phone": "9845011013", "abha": "14-8291-4001-1013", "address": "38, MEI Extension, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_BOTH"},
    {"first": "Shwetha", "last": "Joshi", "gender": "FEMALE", "age": 44, "phone": "9845011014", "abha": "14-8291-4001-1014", "address": "25, Shivananda Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Anand", "last": "Bellary", "gender": "MALE", "age": 57, "phone": "9845011015", "abha": "14-8291-4001-1015", "address": "49, Maruthi Extension, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Meenakshi", "last": "Sundaram", "gender": "FEMALE", "age": 65, "phone": "9845011016", "abha": "14-8291-4001-1016", "address": "72, Saraswathi Nagar, Laggere, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "NCD_BOTH"},
    {"first": "Raghavendra", "last": "Rao", "gender": "MALE", "age": 53, "phone": "9845011017", "abha": "14-8291-4001-1017", "address": "15, 6th Cross, Laggere Village, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "NCD_DM"},
    {"first": "Soumya", "last": "Hegde", "gender": "FEMALE", "age": 47, "phone": "9845011018", "abha": "14-8291-4001-1018", "address": "84, Peenya Link Road, Laggere, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "NCD_HTN"},
    {"first": "Girish", "last": "Kulkarni", "gender": "MALE", "age": 60, "phone": "9845011019", "abha": "14-8291-4001-1019", "address": "29, Varthur Main Bazaar, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "NCD_BOTH"},
    {"first": "Roopa", "last": "Nayak", "gender": "FEMALE", "age": 51, "phone": "9845011020", "abha": "14-8291-4001-1020", "address": "53, Gunjur Village Cross, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "NCD_DM"},

    # Cohort 2: Infectious Disease & IDSP Surveillance - 12 Patients
    {"first": "Ravi", "last": "Kumar", "gender": "MALE", "age": 28, "phone": "9845011021", "abha": "14-8291-4001-1021", "address": "18, MEI Layout 2nd Stage, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_DENGUE"},
    {"first": "Preeti", "last": "Shenoy", "gender": "FEMALE", "age": 24, "phone": "9845011022", "abha": "14-8291-4001-1022", "address": "31, Chowdeshwari Temple Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_TYPHOID"},
    {"first": "Vijay", "last": "Patil", "gender": "MALE", "age": 35, "phone": "9845011023", "abha": "14-8291-4001-1023", "address": "66, Laggere Bridge Colony, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_MALARIA"},
    {"first": "Geetha", "last": "Raman", "gender": "FEMALE", "age": 31, "phone": "9845011024", "abha": "14-8291-4001-1024", "address": "42, Parvathi Nagar Main, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_GASTRO"},
    {"first": "Mohan", "last": "Bhat", "gender": "MALE", "age": 22, "phone": "9845011025", "abha": "14-8291-4001-1025", "address": "88, Kempegowda Nagar 3rd Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_DENGUE"},
    {"first": "Archana", "last": "Kulkarni", "gender": "FEMALE", "age": 29, "phone": "9845011026", "abha": "14-8291-4001-1026", "address": "16, Pipeline Road Slum Cluster, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "SURV_TYPHOID"},
    {"first": "Santosh", "last": "Gowda", "gender": "MALE", "age": 33, "phone": "9845011027", "abha": "14-8291-4001-1027", "address": "74, Bazaar Street, Ulsoor, Bengaluru", "fac": "HOSP-KC-01", "ward": 2, "cohort": "SURV_DENGUE"},
    {"first": "Vidya", "last": "Shankar", "gender": "FEMALE", "age": 27, "phone": "9845011028", "abha": "14-8291-4001-1028", "address": "55, Someshwara Temple Lane, Ulsoor, Bengaluru", "fac": "HOSP-KC-01", "ward": 2, "cohort": "SURV_GASTRO"},
    {"first": "Harish", "last": "Reddy", "gender": "MALE", "age": 40, "phone": "9845011029", "abha": "14-8291-4001-1029", "address": "22, Cambridge Road, Ulsoor, Bengaluru", "fac": "HOSP-KC-01", "ward": 2, "cohort": "SURV_TYPHOID"},
    {"first": "Nalini", "last": "Hegde", "gender": "FEMALE", "age": 36, "phone": "9845011030", "abha": "14-8291-4001-1030", "address": "97, Varthur Lake Bund Road, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "SURV_MALARIA"},
    {"first": "Kiran", "last": "Acharya", "gender": "MALE", "age": 25, "phone": "9845011031", "abha": "14-8291-4001-1031", "address": "11, Gunjur Main Road, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "SURV_GASTRO"},
    {"first": "Bhavana", "last": "Rao", "gender": "FEMALE", "age": 30, "phone": "9845011032", "abha": "14-8291-4001-1032", "address": "63, Chowdeshwari Layout, Laggere, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "SURV_DENGUE"},

    # Cohort 3: General Acute Primary Care OPD - 14 Patients
    {"first": "Shivakumar", "last": "Swamy", "gender": "MALE", "age": 37, "phone": "9845011033", "abha": "14-8291-4001-1033", "address": "21, 5th Main, Parvathi Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_URTI"},
    {"first": "Usha", "last": "Devi", "gender": "FEMALE", "age": 42, "phone": "9845011034", "abha": "14-8291-4001-1034", "address": "39, MEI Layout 3rd Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_BRONCHITIS"},
    {"first": "Mahesh", "last": "Prabhu", "gender": "MALE", "age": 45, "phone": "9845011035", "abha": "14-8291-4001-1035", "address": "78, Ring Road Junction, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_GASTRITIS"},
    {"first": "Suma", "last": "Shetty", "gender": "FEMALE", "age": 34, "phone": "9845011036", "abha": "14-8291-4001-1036", "address": "14, Chowdeshwari Nagar 2nd Stage, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_JOINT_PAIN"},
    {"first": "Chandrakanth", "last": "Patil", "gender": "MALE", "age": 39, "phone": "9845011037", "abha": "14-8291-4001-1037", "address": "58, Vinayaka Extension, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_DERMATITIS"},
    {"first": "Shilpa", "last": "Kulkarni", "gender": "FEMALE", "age": 26, "phone": "9845011038", "abha": "14-8291-4001-1038", "address": "92, MEI Colony, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_ANEMIA"},
    {"first": "Naveen", "last": "Gowda", "gender": "MALE", "age": 31, "phone": "9845011039", "abha": "14-8291-4001-1039", "address": "105, Parvathi Extension, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_URTI"},
    {"first": "Deepthi", "last": "Bhat", "gender": "FEMALE", "age": 29, "phone": "9845011040", "abha": "14-8291-4001-1040", "address": "44, Kempegowda Main, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_GASTRITIS"},
    {"first": "Jagadeesh", "last": "Murthy", "gender": "MALE", "age": 52, "phone": "9845011041", "abha": "14-8291-4001-1041", "address": "83, Pipeline Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_JOINT_PAIN"},
    {"first": "Rashmi", "last": "Kamath", "gender": "FEMALE", "age": 38, "phone": "9845011042", "abha": "14-8291-4001-1042", "address": "26, Shivananda Layout, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "GEN_URTI"},
    {"first": "Madhusudhan", "last": "Rao", "gender": "MALE", "age": 41, "phone": "9845011043", "abha": "14-8291-4001-1043", "address": "67, Laggere Main Road, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "GEN_BRONCHITIS"},
    {"first": "Divya", "last": "Shenoy", "gender": "FEMALE", "age": 23, "phone": "9845011044", "abha": "14-8291-4001-1044", "address": "37, Peenya Cross, Laggere, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "GEN_ANEMIA"},
    {"first": "Anil", "last": "Kumar", "gender": "MALE", "age": 36, "phone": "9845011045", "abha": "14-8291-4001-1045", "address": "19, Varthur Village Bazaar, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "GEN_URTI"},
    {"first": "Padma", "last": "Sundaram", "gender": "FEMALE", "age": 48, "phone": "9845011046", "abha": "14-8291-4001-1046", "address": "52, Balagere Cross, Varthur, Bengaluru Rural", "fac": "RC-A4-01", "ward": 5, "cohort": "GEN_JOINT_PAIN"},

    # Cohort 4: Inter-Facility Referrals (Secondary & Tertiary) - 8 Patients
    {"first": "Sunil", "last": "Hegde", "gender": "MALE", "age": 55, "phone": "9845011047", "abha": "14-8291-4001-1047", "address": "17, 3rd Main, Parvathi Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "REF_KC_DENGUE"},
    {"first": "Bharati", "last": "Nayak", "gender": "FEMALE", "age": 43, "phone": "9845011048", "abha": "14-8291-4001-1048", "address": "71, MEI Layout, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "REF_KC_SURGICAL"},
    {"first": "Ashok", "last": "Kulkarni", "gender": "MALE", "age": 62, "phone": "9845011049", "abha": "14-8291-4001-1049", "address": "85, Chowdeshwari Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "REF_KC_HTN_RETINA"},
    {"first": "Veena", "last": "Prabhu", "gender": "FEMALE", "age": 59, "phone": "9845011050", "abha": "14-8291-4001-1050", "address": "24, Kempegowda Extension, Laggere, Bengaluru", "fac": "NC-LAG-01", "ward": 4, "cohort": "REF_KC_DIABETIC_FOOT"},
    {"first": "Prasanna", "last": "Kumar", "gender": "MALE", "age": 66, "phone": "9845011051", "abha": "14-8291-4001-1051", "address": "102, 100 Feet Road, Indiranagar, Bengaluru", "fac": "HOSP-DIST-01", "ward": 1, "cohort": "REF_VIC_NEPHRO"},
    {"first": "Radhika", "last": "Bhat", "gender": "FEMALE", "age": 58, "phone": "9845011052", "abha": "14-8291-4001-1052", "address": "45, CMH Road, Indiranagar, Bengaluru", "fac": "HOSP-DIST-01", "ward": 1, "cohort": "REF_VIC_CARDIAC"},
    {"first": "Nagaraj", "last": "Gowda", "gender": "MALE", "age": 70, "phone": "9845011053", "abha": "14-8291-4001-1053", "address": "78, Defense Colony, Indiranagar, Bengaluru", "fac": "HOSP-DIST-01", "ward": 1, "cohort": "REF_VIC_PULMO"},
    {"first": "Swathi", "last": "Rao", "gender": "FEMALE", "age": 63, "phone": "9845011054", "abha": "14-8291-4001-1054", "address": "16, HAL 2nd Stage, Indiranagar, Bengaluru", "fac": "HOSP-DIST-01", "ward": 1, "cohort": "REF_VIC_ORTHO"},

    # Cohort 5: Active Real-Time Clinic Flow for Today (8 Oct 2026) - 6 Patients
    {"first": "Manjula", "last": "Devi", "gender": "FEMALE", "age": 33, "phone": "9845011055", "abha": "14-8291-4001-1055", "address": "12, MEI 4th Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_TRIAGE_1"},
    {"first": "Dayanand", "last": "Sagar", "gender": "MALE", "age": 41, "phone": "9845011056", "abha": "14-8291-4001-1056", "address": "48, Parvathi Nagar Cross, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_TRIAGE_2"},
    {"first": "Shobha", "last": "Shetty", "gender": "FEMALE", "age": 28, "phone": "9845011057", "abha": "14-8291-4001-1057", "address": "69, Chowdeshwari Temple Road, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_TRIAGE_3"},
    {"first": "Vinod", "last": "Kumar", "gender": "MALE", "age": 36, "phone": "9845011058", "abha": "14-8291-4001-1058", "address": "87, Kempegowda Main, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_DOC_1"},
    {"first": "Gayathri", "last": "Joshi", "gender": "FEMALE", "age": 47, "phone": "9845011059", "abha": "14-8291-4001-1059", "address": "34, Pipeline Slum Road, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_DOC_2"},
    {"first": "Prakash", "last": "Bellary", "gender": "MALE", "age": 52, "phone": "9845011060", "abha": "14-8291-4001-1060", "address": "59, Maruthi Nagar, Laggere, Bengaluru", "fac": "PHC-LOCAL-01", "ward": 4, "cohort": "TODAY_WAIT_DOC_3"},
]


def flush_operational_data_cleanly():
    """Wipes only operational tables, strictly preserving facility and master catalog infrastructure."""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM pharmacy_inventorytransaction;")

    # Remove all DISPENSE transactions from ledger
    InventoryLedger.objects.filter(transaction_type='DISPENSE').delete()

    models_to_flush = [
        # NCD & Surveillance
        PublicHealthNotification, DiseaseSurveillanceCase, DiseaseCase,
        NCDAssessment, NCDCondition, NCDRecord,
        # Referrals
        FollowUpTask, FollowUp, ReferralEvent, ReferralResponse, ReferralOrder, Referral,
        # Pharmacy & Inventory
        PatientCounselling, DispensationItem, Dispensation,
        PrescriptionItem, Prescription,
        # Laboratory
        DiagnosticResult, TestRequest, Specimen, DiagnosticOrder,
        LabResult, LabSample, LabOrder, LabToken,
        # Consultations & Triage
        Diagnosis, Consultation, Triage, TriageVitals,
        # Visits & Patients
        VisitStatusHistory, Token, FacilityDailyCounter, Visit,
        PatientDocument, Patient, Household,
        AuditLog
    ]
    for model in models_to_flush:
        model.objects.all().delete()

    # Only delete persons that are not staff profiles
    Person.objects.filter(staff_profiles__isnull=True).delete()
    print("Flushed any previous operational records. Pristine clean slate ready.")


def generate_e2e_dataset():
    print("=" * 80)
    print("NAMMA CLINIC - GENERATING CLEAN END-TO-END CLINICAL DATASET")
    print("=" * 80)

    # 1. Assert zero numbers in names upfront
    for item in CITIZENS_ROSTER:
        full_name = f"{item['first']} {item['last']}"
        assert not any(c.isdigit() for c in full_name), f"Name cannot have numbers: {full_name}"
    print(f"Verified {len(CITIZENS_ROSTER)} citizen identities: 100% clean, distinct Indian names with zero numbers.")

    today = datetime.date(2026, 10, 8)
    now = timezone.make_aware(datetime.datetime(2026, 10, 8, 11, 30, 0))

    with transaction.atomic():
        flush_operational_data_cleanly()

        # Fetch facilities and wards
        facilities = {f.facility_code: f for f in Facility.objects.all()}
        wards = {w.id: w for w in Ward.objects.all()}
        districts = {d.id: d for d in District.objects.all()}

        # Fetch key staff profiles
        stf_doc_local = StaffProfile.objects.filter(role_assignments__role__code='DOCTOR', role_assignments__facility=facilities['PHC-LOCAL-01']).first()
        stf_nurse_local = StaffProfile.objects.filter(role_assignments__role__code='NURSE', role_assignments__facility=facilities['PHC-LOCAL-01']).first()
        stf_lab_local = StaffProfile.objects.filter(role_assignments__role__code='LAB_TECHNICIAN', role_assignments__facility=facilities['PHC-LOCAL-01']).first()
        stf_pharm_local = StaffProfile.objects.filter(role_assignments__role__code='PHARMACIST', role_assignments__facility=facilities['PHC-LOCAL-01']).first()
        stf_front_local = StaffProfile.objects.filter(role_assignments__role__code='FRONT_DESK_OFFICER', role_assignments__facility=facilities['PHC-LOCAL-01']).first()

        u_doc_local = stf_doc_local.user_account
        u_nurse_local = stf_nurse_local.user_account
        u_pharm_local = stf_pharm_local.user_account
        u_lab_local = stf_lab_local.user_account

        # Other facility staff
        stf_doc_dist = StaffProfile.objects.filter(role_assignments__role__code='DOCTOR', role_assignments__facility=facilities['HOSP-DIST-01']).first() or stf_doc_local
        stf_doc_sdh = StaffProfile.objects.filter(role_assignments__role__code='DOCTOR', role_assignments__facility=facilities.get('HOSP-SUB-01')).first() or stf_doc_local
        stf_doc_rural = StaffProfile.objects.filter(role_assignments__role__code='DOCTOR', role_assignments__facility=facilities.get('RC-A4-01')).first() or stf_doc_local

        # Ensure NC-LAG-01 and HOSP-KC-01 have active role assignments for their clinicians
        role_doc = RoleMaster.objects.get(code='DOCTOR')
        role_nurse = RoleMaster.objects.get(code='NURSE')
        role_pharm = RoleMaster.objects.get(code='PHARMACIST')
        role_lab = RoleMaster.objects.get(code='LAB_TECHNICIAN')

        StaffRoleAssignment.objects.get_or_create(staff=stf_doc_local, role=role_doc, facility=facilities['NC-LAG-01'], defaults={'effective_from': today - datetime.timedelta(days=120), 'is_active': True})
        StaffRoleAssignment.objects.get_or_create(staff=stf_nurse_local, role=role_nurse, facility=facilities['NC-LAG-01'], defaults={'effective_from': today - datetime.timedelta(days=120), 'is_active': True})
        StaffRoleAssignment.objects.get_or_create(staff=stf_pharm_local, role=role_pharm, facility=facilities['NC-LAG-01'], defaults={'effective_from': today - datetime.timedelta(days=120), 'is_active': True})
        StaffRoleAssignment.objects.get_or_create(staff=stf_lab_local, role=role_lab, facility=facilities['NC-LAG-01'], defaults={'effective_from': today - datetime.timedelta(days=120), 'is_active': True})

        StaffRoleAssignment.objects.get_or_create(staff=stf_doc_sdh, role=role_doc, facility=facilities['HOSP-KC-01'], defaults={'effective_from': today - datetime.timedelta(days=120), 'is_active': True})

        # Fetch Masters
        med_metformin = MedicineMaster.objects.filter(generic_name__icontains='Metformin').first()
        med_amlodipine = MedicineMaster.objects.filter(generic_name__icontains='Amlodipine').first()
        med_paracetamol = MedicineMaster.objects.filter(generic_name__icontains='Paracetamol').first()
        med_amoxicillin = MedicineMaster.objects.filter(generic_name__icontains='Amoxicillin').first()
        med_cetirizine = MedicineMaster.objects.filter(generic_name__icontains='Cetirizine').first()
        med_ors = MedicineMaster.objects.filter(generic_name__icontains='ORS').first()
        med_ifa = MedicineMaster.objects.filter(generic_name__icontains='Iron').first() or med_paracetamol

        # Diagnostic Test Masters
        dt_fbg = DiagnosticTestMaster.objects.get(test_code='FBG')
        dt_ppbg = DiagnosticTestMaster.objects.get(test_code='PPBG')
        dt_hba1c = DiagnosticTestMaster.objects.get(test_code='HBA1C')
        dt_cbc = DiagnosticTestMaster.objects.get(test_code='CBC')
        dt_ns1 = DiagnosticTestMaster.objects.get(test_code='NS1-AG')
        dt_widal = DiagnosticTestMaster.objects.get(test_code='WIDAL')
        dt_malaria = DiagnosticTestMaster.objects.get(test_code='MAL-RDT')
        dt_creatinine = DiagnosticTestMaster.objects.get(test_code='CREATININE')
        dt_lipid = DiagnosticTestMaster.objects.get(test_code='LIPID-PANEL')

        # LabTestMaster legacy mappings
        lt_cbc = LabTestMaster.objects.filter(code='L-CBC').first()
        lt_hba1c = LabTestMaster.objects.filter(code='L-HBA1C').first()
        lt_rbg = LabTestMaster.objects.filter(code='L-RBG').first()
        lt_dengue = LabTestMaster.objects.filter(code='L-DENGUE').first()
        lt_malaria = LabTestMaster.objects.filter(code='L-MALARIA').first()

        # Diagnosis Masters
        diag_htn = DiagnosisMaster.objects.get(icd10_code='I10')
        diag_dm = DiagnosisMaster.objects.get(icd10_code='E11.9')
        diag_dengue = DiagnosisMaster.objects.get(icd10_code='A90')
        diag_typhoid = DiagnosisMaster.objects.get(icd10_code='A01.0')
        diag_malaria = DiagnosisMaster.objects.get(icd10_code='B54')
        diag_gastro = DiagnosisMaster.objects.get(icd10_code='A09')
        diag_urti = DiagnosisMaster.objects.get(icd10_code='J06.9')
        diag_bronchitis = DiagnosisMaster.objects.get(icd10_code='J20.9')
        diag_gastritis = DiagnosisMaster.objects.get(icd10_code='K29.7')
        diag_joint = DiagnosisMaster.objects.get(icd10_code='M25.5')
        diag_derma = DiagnosisMaster.objects.get(icd10_code='L30.9')
        diag_anemia = DiagnosisMaster.objects.get(icd10_code='D50.9')

        # Disease Masters
        dis_dengue = DiseaseMaster.objects.get(disease_code='DENGUE')
        dis_typhoid = DiseaseMaster.objects.get(disease_code='TYPHOID')
        dis_malaria = DiseaseMaster.objects.get(disease_code='MALARIA')
        dis_gastro = DiseaseMaster.objects.get(disease_code='GASTRO')

        print("\n[Step 0] Initializing Medicine Batches and Authoritative Stock Receipts...")
        # Ensure every essential medicine batch has 10,000 units with an authoritative PURCHASE_RECEIPT
        for fac_key in ['PHC-LOCAL-01', 'NC-LAG-01', 'RC-A4-01', 'HOSP-KC-01', 'HOSP-DIST-01']:
            fac_obj = facilities.get(fac_key)
            if not fac_obj:
                continue
            for med in [med_metformin, med_amlodipine, med_paracetamol, med_amoxicillin, med_cetirizine, med_ors, med_ifa]:
                if not med:
                    continue
                batch_code = f"BAT-{fac_obj.facility_code[:3]}-{med.id}-2026A"
                batch, _ = MedicineBatch.objects.get_or_create(
                    facility=fac_obj,
                    medicine=med,
                    defaults={
                        'batch_number': batch_code,
                        'mfg_date': today - datetime.timedelta(days=120),
                        'expiry_date': today + datetime.timedelta(days=400),
                        'unit_cost': Decimal("1.50"),
                        'available_quantity': 10000,
                        'quantity': 10000,
                        'status': 'AVAILABLE'
                    }
                )
                batch.available_quantity = 10000
                batch.quantity = 10000
                batch.status = 'AVAILABLE'
                batch.save()

                InventoryLedger.objects.get_or_create(
                    batch=batch,
                    facility=fac_obj,
                    transaction_type='PURCHASE_RECEIPT',
                    defaults={
                        'performed_by_staff': stf_pharm_local,
                        'quantity_delta': 10000,
                        'balance_after': 10000,
                        'remarks': f"Initial stock receipt from KSMSCL central warehouse for {med.generic_name}"
                    }
                )

        print("Batches replenished with 10,000 units each and verified via InventoryLedger PURCHASE_RECEIPT.")

        print("\n[Step 1] Creating Households across Wards...")
        households = []
        hh_configs = [
            ("HH-LAG-001", "Gowda Family Household", "14, 2nd Cross, Parvathi Nagar, Laggere, Bengaluru", 4, 4),
            ("HH-LAG-002", "Hegde Family Household", "45, Chowdeshwari Nagar, Laggere, Bengaluru", 4, 5),
            ("HH-LAG-003", "Bhat Family Household", "28, MEI Layout Main Road, Laggere, Bengaluru", 4, 3),
            ("HH-LAG-004", "Patil Family Household", "33, 4th Cross, MEI Layout, Laggere, Bengaluru", 4, 4),
            ("HH-ULS-001", "Raman Family Household", "74, Bazaar Street, Ulsoor, Bengaluru", 2, 4),
            ("HH-IND-001", "Hegde Family Household", "102, 100 Feet Road, Indiranagar, Bengaluru", 1, 3),
            ("HH-VAR-001", "Nayak Family Household", "29, Varthur Main Bazaar, Bengaluru Rural", 5, 5),
        ]
        for hhid, hname, haddr, wid, count in hh_configs:
            hh, _ = Household.objects.get_or_create(
                household_id=hhid,
                defaults={
                    'head_name': hname,
                    'address': haddr,
                    'ward': wards[wid],
                    'members_count': count,
                    'vulnerable_category': 'Low Income Urban Household'
                }
            )
            households.append(hh)
        print(f"Created/verified {len(households)} community households.")

        print("\n[Step 2] Registering 60 Patients (Person + Patient records)...")
        created_patients = []
        patient_map = {}

        for idx, citizen in enumerate(CITIZENS_ROSTER, 1):
            full_name = f"{citizen['first']} {citizen['last']}"
            dob = today - datetime.timedelta(days=citizen['age'] * 365 + (idx * 7))
            fac = facilities[citizen['fac']]
            ward_obj = wards[citizen['ward']]
            dist_obj = fac.district

            person = Person.objects.create(
                first_name=citizen['first'],
                last_name=citizen['last'],
                gender=citizen['gender'],
                date_of_birth=dob,
                phone_number=citizen['phone'],
                aadhaar_hash=uuid.uuid5(uuid.NAMESPACE_DNS, f"{full_name}-{citizen['phone']}").hex
            )

            pid = f"NC-{fac.facility_code[:3]}-2026-{idx:04d}"
            patient = Patient.objects.create(
                patient_id=pid,
                person=person,
                name=full_name,
                date_of_birth=dob,
                age=citizen['age'],
                gender=citizen['gender'],
                mobile=citizen['phone'],
                address=citizen['address'],
                ward=ward_obj,
                district=dist_obj,
                ABHA_ID_DEMO=citizen['abha'],
                emergency_contact='9845099999',
                vulnerability_information='BPL Slum Household' if 'Laggere' in citizen['address'] else 'Low Income Group',
                registered_at_facility=fac
            )
            created_patients.append(patient)
            patient_map[idx] = (patient, citizen)

        print(f"Registered {len(created_patients)} clean patients with unique verified demographics.")

        # Track per-facility-per-date token counters to ensure database uniqueness
        facility_token_counters = defaultdict(int)
        visit_global_counter = 0

        def create_full_encounter(
            patient, facility, opd_date, queue, status, complaint,
            doctor_staff, doctor_user, nurse_staff, nurse_user,
            vitals_data, diag_master, clinical_notes,
            test_master=None, test_value_num=None, test_value_txt="", is_abnormal=False,
            meds_to_prescribe=None,
            is_today=False
        ):
            nonlocal visit_global_counter
            visit_global_counter += 1

            token_key = (facility.id, opd_date)
            facility_token_counters[token_key] += 1
            token_num = facility_token_counters[token_key]

            arrival_dt = timezone.make_aware(datetime.datetime.combine(opd_date, datetime.time(9, 15 + (token_num % 180) * 1)))
            v_id = f"VIS-{facility.facility_code[:4]}-{opd_date.strftime('%Y%m%d')}-{token_num:04d}"

            # 1. Create Visit in TRIAGE queue initially to satisfy FND-09 validation
            initial_queue = 'TRIAGE' if queue in ['TRIAGE', 'DOCTOR', 'LAB', 'PHARMACY', 'COMPLETED'] else queue
            initial_status = 'WAITING_FOR_TRIAGE' if status in ['WAITING_FOR_TRIAGE', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'WAITING_FOR_LAB', 'LAB_PENDING', 'WAITING_FOR_PHARMACY', 'COMPLETED'] else status

            visit = Visit.objects.create(
                visit_id=v_id,
                patient=patient,
                facility=facility,
                opd_date=opd_date,
                visit_type='GENERAL_OPD',
                priority='HIGH' if vitals_data.get('emergency', False) else 'NORMAL',
                current_queue=initial_queue,
                status=initial_status,
                chief_complaint=complaint,
                assigned_doctor=doctor_user,
                arrival_time=arrival_dt
            )

            # Token
            Token.objects.create(
                token_number=token_num,
                visit=visit,
                facility=facility,
                date=opd_date,
                priority=visit.priority,
                status='COMPLETED' if status == 'COMPLETED' else 'WAITING'
            )

            # 2. Nurse Triage (if beyond WAITING_FOR_TRIAGE)
            if queue != 'TRIAGE' or status != 'WAITING_FOR_TRIAGE':
                h_m = float(vitals_data['height']) / 100.0
                bmi_val = round(float(vitals_data['weight']) / (h_m * h_m), 1)

                TriageVitals.objects.create(
                    visit=visit,
                    patient=patient,
                    nurse=nurse_user,
                    blood_pressure_systolic=vitals_data['sys'],
                    blood_pressure_diastolic=vitals_data['dia'],
                    pulse_bpm=vitals_data['pulse'],
                    temperature_f=Decimal(str(vitals_data['temp_f'])),
                    spo2_percent=vitals_data['spo2'],
                    respiratory_rate=vitals_data.get('rr', 18),
                    height_cm=Decimal(str(vitals_data['height'])),
                    weight_kg=Decimal(str(vitals_data['weight'])),
                    bmi=Decimal(str(bmi_val)),
                    blood_glucose_mgdl=vitals_data.get('glucose', 110),
                    nurse_notes=f"Patient conscious, alert. {vitals_data.get('notes', 'Routine vitals recorded.')}"
                )

                Triage.objects.create(
                    visit=visit,
                    triaged_by_staff=nurse_staff,
                    systolic_bp=vitals_data['sys'],
                    diastolic_bp=vitals_data['dia'],
                    pulse_rate=vitals_data['pulse'],
                    temperature_celsius=Decimal(str(round((vitals_data['temp_f'] - 32) * 5 / 9, 1))),
                    spo2_percentage=vitals_data['spo2'],
                    weight_kg=Decimal(str(vitals_data['weight'])),
                    height_cm=Decimal(str(vitals_data['height'])),
                    bmi=Decimal(str(bmi_val))
                )

                # Now advance visit queue and status to destination
                visit.current_queue = queue
                visit.status = status
                if status == 'COMPLETED':
                    visit.completed_time = arrival_dt + datetime.timedelta(minutes=45)
                visit.save()

            # 3. Doctor Consultation (if beyond DOCTOR queue)
            consult = None
            if queue in ['LAB', 'PHARMACY', 'COMPLETED']:
                consult = Consultation.objects.create(
                    visit=visit,
                    patient=patient,
                    doctor=doctor_user,
                    doctor_staff=doctor_staff,
                    facility=facility,
                    chief_complaint=complaint,
                    clinical_history=f"History of present illness for {complaint}. Duration 4 days.",
                    clinical_assessment=f"Clinical examination consistent with {diag_master.description}.",
                    diagnosis_code=diag_master.icd10_code,
                    diagnosis_name=diag_master.description,
                    treatment_plan=f"Prescribe standard pharmacotherapy and lifestyle modifications. Review in 14 days.",
                    follow_up_date=opd_date + datetime.timedelta(days=14),
                    clinical_notes=clinical_notes
                )

                Diagnosis.objects.create(
                    consultation=consult,
                    diagnosis_master=diag_master,
                    diagnosis_type='WORKING',
                    certainty='CONFIRMED' if status == 'COMPLETED' else 'PROVISIONAL',
                    is_primary=True,
                    notes=diag_master.description
                )

            # 4. Laboratory Diagnostics
            diag_order = None
            diag_result = None
            if consult and test_master:
                diag_order = DiagnosticOrder.objects.create(
                    visit=visit,
                    facility=facility,
                    ordering_doctor_staff=doctor_staff,
                    order_number=f"ORD-{opd_date.strftime('%Y%m%d')}-{visit_global_counter:04d}",
                    order_date=opd_date,
                    priority='URGENT' if is_abnormal else 'ROUTINE',
                    clinical_indication=f"Evaluate {diag_master.description}",
                    status='VERIFIED' if status == 'COMPLETED' else ('SAMPLE_COLLECTED' if queue == 'LAB' else 'RESULT_ENTERED')
                )

                specimen = Specimen.objects.create(
                    diagnostic_order=diag_order,
                    barcode_identifier=f"BARC-{opd_date.strftime('%Y%m')}-{visit_global_counter:05d}",
                    specimen_type=test_master.specimen_type,
                    collected_by_staff=nurse_staff,
                    status='COLLECTED'
                )

                t_req = TestRequest.objects.create(
                    diagnostic_order=diag_order,
                    test_master=test_master,
                    specimen=specimen,
                    status='COMPLETED' if status == 'COMPLETED' else ('PENDING' if queue == 'LAB' else 'IN_TESTING')
                )

                if status == 'COMPLETED' or queue in ['PHARMACY']:
                    diag_result = DiagnosticResult.objects.create(
                        test_request=t_req,
                        result_value_text=test_value_txt or (str(test_value_num) if test_value_num else "Negative"),
                        result_value_numeric=Decimal(str(test_value_num)) if test_value_num else None,
                        reference_range_applied=f"{test_master.reference_range_male} {test_master.default_unit}",
                        is_abnormal=is_abnormal,
                        is_critical_panic=is_abnormal and 'Dengue' in diag_master.description,
                        status='VERIFIED',
                        entered_by_staff=stf_lab_local,
                        verified_by_staff=stf_lab_local,
                        verified_at=arrival_dt + datetime.timedelta(minutes=25)
                    )

                # Legacy Lab Order for backwards compatibility
                legacy_lt = LabTestMaster.objects.filter(code__icontains=test_master.test_code[:4]).first() or lt_cbc
                legacy_order = LabOrder.objects.create(
                    visit=visit,
                    consultation=consult,
                    patient=patient,
                    doctor=doctor_user,
                    facility=facility,
                    test_master=legacy_lt,
                    status='VERIFIED' if status == 'COMPLETED' else 'ORDERED'
                )
                if status == 'COMPLETED':
                    LabSample.objects.create(
                        lab_order=legacy_order,
                        sample_type=test_master.specimen_type,
                        sample_code=f"SMP-{visit_global_counter:05d}",
                        collected_by=nurse_user
                    )
                    LabResult.objects.create(
                        lab_order=legacy_order,
                        result_value=test_value_txt or str(test_value_num),
                        unit=test_master.default_unit,
                        reference_range=test_master.reference_range_male,
                        interpretation_flag='HIGH' if is_abnormal else 'NORMAL',
                        verified_by=u_lab_local,
                        notes=f"Verified automated analyzer output on {opd_date}"
                    )

            # 5. Pharmacy Prescriptions & Double-Entry Ledger Dispensing
            if consult and meds_to_prescribe:
                rx_status = 'DISPENSED' if status == 'COMPLETED' else ('VERIFIED' if queue == 'PHARMACY' else 'PENDING_VERIFICATION')
                prescription = Prescription.objects.create(
                    consultation=consult,
                    patient=patient,
                    doctor=doctor_user,
                    doctor_staff=doctor_staff,
                    facility=facility,
                    status=rx_status,
                    notes="Take medications as directed after meals.",
                    verified_by=u_pharm_local if rx_status in ['VERIFIED', 'DISPENSED'] else None,
                    verified_at=arrival_dt + datetime.timedelta(minutes=30) if rx_status in ['VERIFIED', 'DISPENSED'] else None
                )

                created_rx_items = []
                for med_obj, dose, freq, days, qty in meds_to_prescribe:
                    rx_item = PrescriptionItem.objects.create(
                        prescription=prescription,
                        medicine=med_obj,
                        medicine_name=f"{med_obj.generic_name} {med_obj.strength}",
                        dosage=dose,
                        frequency=freq,
                        duration_days=days,
                        quantity=qty,
                        dispensed_quantity=qty if status == 'COMPLETED' else 0,
                        status='DISPENSED' if status == 'COMPLETED' else 'PENDING'
                    )
                    created_rx_items.append((rx_item, med_obj, qty))

                # Execute dispensing if visit is completed
                if status == 'COMPLETED':
                    disp_num = f"DISP-{opd_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                    dispensation = Dispensation.objects.create(
                        prescription=prescription,
                        facility=facility,
                        dispensed_by_staff=stf_pharm_local,
                        dispensation_number=disp_num,
                        remarks="Standard generic dispensation. Patient counselled on dosage."
                    )

                    for rx_item, med_obj, qty in created_rx_items:
                        # Find available batch for this facility and medicine
                        batch = MedicineBatch.objects.select_for_update().filter(facility=facility, medicine=med_obj, available_quantity__gte=qty).first()
                        if not batch:
                            batch = MedicineBatch.objects.select_for_update().filter(medicine=med_obj, available_quantity__gte=qty).first()

                        if batch:
                            DispensationItem.objects.create(
                                dispensation=dispensation,
                                prescription_item=rx_item,
                                batch=batch,
                                quantity_dispensed=qty
                            )

                            # Decrement batch atomically & write double-entry InventoryLedger
                            new_balance = batch.available_quantity - qty
                            batch.available_quantity = new_balance
                            batch.quantity = new_balance
                            batch.save()

                            InventoryLedger.objects.create(
                                batch=batch,
                                facility=facility,
                                performed_by_staff=stf_pharm_local,
                                transaction_type='DISPENSE',
                                quantity_delta=-qty,
                                balance_after=new_balance,
                                reference_entity_type='Dispensation',
                                reference_entity_id=dispensation.id,
                                remarks=f"Dispensed for Prescription #{prescription.id}"
                            )

                            # Legacy InventoryTransaction audit
                            InventoryTransaction.objects.create(
                                facility=facility,
                                medicine=med_obj,
                                batch=batch,
                                transaction_type='DISPENSED',
                                quantity=qty,
                                before_quantity=new_balance + qty,
                                after_quantity=new_balance,
                                patient=patient,
                                visit=visit,
                                prescription=prescription,
                                prescription_item=rx_item,
                                reference_id=disp_num,
                                created_by=u_pharm_local,
                                notes="Dispensed to patient"
                            )

                    PatientCounselling.objects.create(
                        prescription=prescription,
                        patient=patient,
                        pharmacist=u_pharm_local,
                        dose_explained=True,
                        frequency_explained=True,
                        duration_explained=True,
                        food_instructions_given=True,
                        storage_explained=True,
                        warning_signs_explained=True,
                        adherence_counselled=True,
                        counselling_notes="Patient understood timings and precautions."
                    )

            return visit, consult, diag_order, diag_result

        print("\n[Step 3] Seeding Cohort 1: Longitudinal Chronic NCD Records (July - October 2026)...")
        # 20 Patients with monthly tracking in July, August, September
        ncd_dates = [
            datetime.date(2026, 7, 15),
            datetime.date(2026, 8, 18),
            datetime.date(2026, 9, 20),
        ]

        for p_idx in range(1, 21):
            pat, cit = patient_map[p_idx]
            cohort = cit['cohort']
            fac = facilities[cit['fac']]

            # Register NCD Conditions
            cond_htn = None
            cond_dm = None
            if "HTN" in cohort or "BOTH" in cohort:
                cond_htn = NCDCondition.objects.create(
                    patient=pat,
                    registering_facility=fac,
                    registering_doctor=stf_doc_local,
                    condition_code='HYPERTENSION',
                    diagnosis_date=datetime.date(2026, 6, 1),
                    staging='Stage 1 Essential Hypertension',
                    control_status='CONTROLLED' if p_idx % 2 == 0 else 'UNCONTROLLED'
                )
            if "DM" in cohort or "BOTH" in cohort:
                cond_dm = NCDCondition.objects.create(
                    patient=pat,
                    registering_facility=fac,
                    registering_doctor=stf_doc_local,
                    condition_code='DIABETES_T2',
                    diagnosis_date=datetime.date(2026, 6, 1),
                    staging='Type 2 Diabetes Mellitus',
                    control_status='CONTROLLED' if p_idx % 2 == 1 else 'UNCONTROLLED'
                )

            # Generate 3 historical completed monthly encounters
            for m_idx, enc_date in enumerate(ncd_dates):
                sys_bp = 148 - (m_idx * 6) + (p_idx % 5)
                dia_bp = 94 - (m_idx * 4) + (p_idx % 3)
                fbg_val = 158 - (m_idx * 12) + (p_idx % 8)

                meds = []
                if "HTN" in cohort or "BOTH" in cohort:
                    meds.append((med_amlodipine, "1-0-0 After Food", "Once Daily", 30, 30))
                if "DM" in cohort or "BOTH" in cohort:
                    meds.append((med_metformin, "1-0-1 After Food", "Twice Daily", 30, 60))

                v, c, do, dr = create_full_encounter(
                    patient=pat,
                    facility=fac,
                    opd_date=enc_date,
                    queue='COMPLETED',
                    status='COMPLETED',
                    complaint="Routine monthly NCD refill and blood pressure checkup",
                    doctor_staff=stf_doc_local,
                    doctor_user=u_doc_local,
                    nurse_staff=stf_nurse_local,
                    nurse_user=u_nurse_local,
                    vitals_data={'sys': sys_bp, 'dia': dia_bp, 'pulse': 76, 'temp_f': 98.4, 'spo2': 98, 'height': 165, 'weight': 68, 'glucose': fbg_val},
                    diag_master=diag_htn if "HTN" in cohort else diag_dm,
                    clinical_notes=f"Month {m_idx + 1} evaluation. Patient tolerating oral medications well. Encouraged salt reduction.",
                    test_master=dt_hba1c if m_idx == 0 else dt_fbg,
                    test_value_num=7.4 if m_idx == 0 else fbg_val,
                    test_value_txt=f"{fbg_val} mg/dL",
                    is_abnormal=fbg_val > 140,
                    meds_to_prescribe=meds
                )

                # NCD longitudinal assessment
                if cond_htn:
                    NCDAssessment.objects.create(
                        condition=cond_htn,
                        visit=v,
                        assessed_by_staff=stf_doc_local,
                        systolic_bp=sys_bp,
                        diastolic_bp=dia_bp,
                        blood_glucose_fasting=Decimal(str(fbg_val)),
                        bmi=Decimal("25.0"),
                        clinical_notes=f"Serial BP tracking: {sys_bp}/{dia_bp} mmHg."
                    )
                if cond_dm:
                    NCDAssessment.objects.create(
                        condition=cond_dm,
                        visit=v,
                        assessed_by_staff=stf_doc_local,
                        systolic_bp=sys_bp,
                        diastolic_bp=dia_bp,
                        blood_glucose_fasting=Decimal(str(fbg_val)),
                        hba1c=Decimal("7.4") if m_idx == 0 else None,
                        clinical_notes=f"Fasting glucose: {fbg_val} mg/dL."
                    )

                # Follow-up task for next appointment
                due = enc_date + datetime.timedelta(days=30)
                FollowUpTask.objects.create(
                    patient=pat,
                    facility=fac,
                    originating_visit=v,
                    completed_in_visit=v,
                    completed_by_staff=stf_doc_local,
                    due_date=due,
                    category='NCD_ROUTINE',
                    status='COMPLETED',
                    clinical_instructions="Review fasting blood glucose and blood pressure in 30 days.",
                    completed_at=timezone.make_aware(datetime.datetime.combine(due, datetime.time(10, 0)))
                )
                FollowUp.objects.create(
                    patient=pat,
                    visit=v,
                    facility=fac,
                    category='NCD',
                    due_date=due,
                    status='COMPLETED',
                    notes="Monthly chronic follow-up completed."
                )

            # Legacy NCD Record
            NCDRecord.objects.create(
                patient=pat,
                facility=fac,
                screening_date=datetime.date(2026, 6, 1),
                hypertension_screened=True,
                hypertension_diagnosed="HTN" in cohort or "BOTH" in cohort,
                diabetes_screened=True,
                diabetes_diagnosed="DM" in cohort or "BOTH" in cohort,
                risk_level='HIGH' if "BOTH" in cohort else 'MODERATE',
                treatment_status='UNDER_TREATMENT',
                control_status='CONTROLLED' if p_idx % 2 == 0 else 'UNCONTROLLED',
                last_bp="136/84",
                last_glucose=132,
                next_followup_due=datetime.date(2026, 10, 20)
            )

        print(f"Seeded 20 longitudinal NCD patient histories (60 completed visits, assessments, dispensations).")

        print("\n[Step 4] Seeding Cohort 2: IDSP Communicable Disease Surveillance (Patients 21 to 32)...")
        for p_idx in range(21, 33):
            pat, cit = patient_map[p_idx]
            cohort = cit['cohort']
            fac = facilities[cit['fac']]
            enc_date = today - datetime.timedelta(days=(32 - p_idx) % 7 + 1)

            if "DENGUE" in cohort:
                diag = diag_dengue
                dis = dis_dengue
                test = dt_ns1
                t_val = "POSITIVE"
                is_abn = True
                meds = [(med_paracetamol, "1-0-1-1 After Food", "Four Times Daily", 5, 20), (med_ors, "1 Sachet in 1L Water", "As Directed", 5, 5)]
                complaint = "Continuous high fever for 4 days with severe headache, retro-orbital pain and backache"
            elif "TYPHOID" in cohort:
                diag = diag_typhoid
                dis = dis_typhoid
                test = dt_widal
                t_val = "TO 1:160, TH 1:320 POSITIVE"
                is_abn = True
                meds = [(med_amoxicillin, "1-0-1 After Food", "Twice Daily", 7, 14), (med_paracetamol, "1-0-1 After Food", "Three Times Daily", 5, 15)]
                complaint = "Step-ladder pattern fever, malaise, chills and dry cough for 6 days"
            elif "MALARIA" in cohort:
                diag = diag_malaria
                dis = dis_malaria
                test = dt_malaria
                t_val = "Plasmodium Vivax POSITIVE"
                is_abn = True
                meds = [(med_paracetamol, "1-0-1 After Food", "Three Times Daily", 5, 15)]
                complaint = "High fever with chills and profuse sweating occurring on alternate days"
            else:  # GASTRO
                diag = diag_gastro
                dis = dis_gastro
                test = dt_cbc
                t_val = "12400 /mcL"
                is_abn = True
                meds = [(med_ors, "1 Sachet in 1L Water", "Frequent Sips", 5, 10), (med_paracetamol, "1-0-0 As Needed", "As Needed", 3, 6)]
                complaint = "Acute watery diarrhea and vomiting, dehydration symptoms"

            v, c, do, dr = create_full_encounter(
                patient=pat,
                facility=fac,
                opd_date=enc_date,
                queue='COMPLETED',
                status='COMPLETED',
                complaint=complaint,
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 108, 'dia': 70, 'pulse': 104, 'temp_f': 102.4, 'spo2': 97, 'height': 168, 'weight': 62, 'notes': 'Feverish, tachycardic.'},
                diag_master=diag,
                clinical_notes=f"IDSP Surveillance Protocol: {dis.disease_name}. Lab investigation confirmed. Supportive therapy initiated.",
                test_master=test,
                test_value_txt=t_val,
                is_abnormal=is_abn,
                meds_to_prescribe=meds
            )

            # Disease Surveillance Case
            sc = DiseaseSurveillanceCase.objects.create(
                case_number=f"SURV-{enc_date.strftime('%Y%m%d')}-{p_idx:04d}",
                patient=pat,
                facility=fac,
                disease=dis,
                reporting_staff=stf_doc_local,
                ward=pat.ward,
                severity='MODERATE' if "DENGUE" in cohort else 'MILD',
                status='CONFIRMED',
                lab_confirmed=True,
                diagnostic_result=dr,
                investigation_notes=f"Statutory notification for {dis.disease_name}. Ward {pat.ward.ward_number if pat.ward else 'N/A'} health inspector notified."
            )

            # Public Health Notification
            PublicHealthNotification.objects.create(
                case=sc,
                notified_authority='DISTRICT_SURVEILLANCE_OFFICER',
                transmission_status='DISPATCHED',
                dispatch_payload={
                    "case_number": sc.case_number,
                    "patient_age": pat.age,
                    "patient_gender": pat.gender,
                    "disease": dis.disease_name,
                    "ward": pat.ward.name if pat.ward else "",
                    "facility": fac.facility_name,
                    "confirmation_method": test.test_name
                },
                dispatched_at=timezone.make_aware(datetime.datetime.combine(enc_date, datetime.time(14, 0)))
            )

            # Legacy Disease Case
            DiseaseCase.objects.create(
                disease_name=dis.disease_name,
                patient=pat,
                facility=fac,
                ward=pat.ward,
                severity='MODERATE' if "DENGUE" in cohort else 'MILD',
                status='CONFIRMED',
                notes=f"Surveillance case verified on {enc_date}"
            )

        print(f"Seeded 12 IDSP communicable surveillance cases with lab proof and statutory dispatches.")

        print("\n[Step 5] Seeding Cohort 3: General Acute OPD Encounters (Patients 33 to 46)...")
        for p_idx in range(33, 47):
            pat, cit = patient_map[p_idx]
            cohort = cit['cohort']
            fac = facilities[cit['fac']]
            enc_date = today - datetime.timedelta(days=(46 - p_idx) % 5 + 1)

            if "URTI" in cohort:
                diag = diag_urti
                meds = [(med_paracetamol, "1-0-1 After Food", "Twice Daily", 5, 10), (med_cetirizine, "0-0-1 At Night", "Once Daily", 5, 5)]
                complaint = "Sore throat, runny nose and mild dry cough for 3 days"
            elif "BRONCHITIS" in cohort:
                diag = diag_bronchitis
                meds = [(med_amoxicillin, "1-0-1 After Food", "Twice Daily", 5, 10), (med_paracetamol, "1-0-1 After Food", "Twice Daily", 5, 10)]
                complaint = "Productive cough with white sputum, chest congestion"
            elif "GASTRITIS" in cohort:
                diag = diag_gastritis
                meds = [(med_ors, "1 Sachet in 1L Water", "As Needed", 3, 3)]
                complaint = "Burning epigastric pain, acid reflux after meals"
            elif "JOINT_PAIN" in cohort:
                diag = diag_joint
                meds = [(med_paracetamol, "1-0-1 After Food", "Twice Daily", 7, 14)]
                complaint = "Bilateral knee joint stiffness and pain during walking"
            elif "DERMATITIS" in cohort:
                diag = diag_derma
                meds = [(med_cetirizine, "0-0-1 At Night", "Once Daily", 7, 7)]
                complaint = "Itchy erythematous rash on forearms and neck"
            else:  # ANEMIA
                diag = diag_anemia
                meds = [(med_ifa, "1-0-0 After Food", "Once Daily", 30, 30)]
                complaint = "Generalized fatigue, weakness and pale conjunctiva"

            create_full_encounter(
                patient=pat,
                facility=fac,
                opd_date=enc_date,
                queue='COMPLETED',
                status='COMPLETED',
                complaint=complaint,
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 118, 'dia': 78, 'pulse': 72, 'temp_f': 98.6, 'spo2': 99, 'height': 162, 'weight': 58},
                diag_master=diag,
                clinical_notes=f"General OPD care: {diag.description}. Prescribed symptomatic medications.",
                meds_to_prescribe=meds
            )

        print(f"Seeded 14 acute primary care OPD encounters with triage, consultations, and dispensations.")

        print("\n[Step 6] Seeding Cohort 4: Inter-Facility Secondary & Tertiary Referrals (Patients 47 to 54)...")
        ref_configs = [
            (47, "PHC-LOCAL-01", "HOSP-KC-01", "REF_KC_DENGUE", "Dengue Fever with Falling Platelets (< 50,000 /mcL) and Petechial Rash", "EMERGENCY", diag_dengue),
            (48, "PHC-LOCAL-01", "HOSP-KC-01", "REF_KC_SURGICAL", "Suspected Acute Appendicitis with Right Iliac Fossa Rebound Tenderness", "URGENT", diag_gastritis),
            (49, "PHC-LOCAL-01", "HOSP-KC-01", "REF_KC_HTN_RETINA", "Resistant Grade 3 Hypertension with Fundus Changes (Retinopathy)", "URGENT", diag_htn),
            (50, "NC-LAG-01", "HOSP-KC-01", "REF_KC_DIABETIC_FOOT", "Uncontrolled Diabetes with Grade 2 Wagner Diabetic Foot Ulcer", "URGENT", diag_dm),
            (51, "HOSP-DIST-01", "HOSP-DIST-01", "REF_VIC_NEPHRO", "Diabetic Nephropathy Stage 3 with Elevated Serum Creatinine (2.4 mg/dL)", "ROUTINE", diag_dm),
            (52, "HOSP-DIST-01", "HOSP-DIST-01", "REF_VIC_CARDIAC", "Atypical Angina Pectoris on Exertion - Cardiology Evaluation", "URGENT", diag_htn),
            (53, "HOSP-DIST-01", "HOSP-DIST-01", "REF_VIC_PULMO", "Chronic Productive Cough with Exertional Dyspnea - Pulmonology Review", "ROUTINE", diag_bronchitis),
            (54, "HOSP-DIST-01", "HOSP-DIST-01", "REF_VIC_ORTHO", "Severe Tricompartmental Osteoarthritis Knee - Orthopedic Arthroplasty Review", "ROUTINE", diag_joint),
        ]

        for p_idx, src_code, dst_code, cohort_tag, ref_reason, urgency, diag in ref_configs:
            pat, cit = patient_map[p_idx]
            src_fac = facilities['PHC-LOCAL-01'] if src_code == 'PHC-LOCAL-01' else (facilities['NC-LAG-01'] if src_code == 'NC-LAG-01' else facilities['PHC-LOCAL-01'])
            dst_fac = facilities['HOSP-KC-01'] if 'KC' in cohort_tag else facilities['HOSP-DIST-01']
            enc_date = today - datetime.timedelta(days=(54 - p_idx) + 2)

            v, c, do, dr = create_full_encounter(
                patient=pat,
                facility=src_fac,
                opd_date=enc_date,
                queue='COMPLETED',
                status='COMPLETED',
                complaint=f"Referral evaluation: {ref_reason}",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 152 if 'HTN' in cohort_tag else 122, 'dia': 96 if 'HTN' in cohort_tag else 80, 'pulse': 88, 'temp_f': 99.2, 'spo2': 96, 'height': 166, 'weight': 70, 'emergency': urgency == 'EMERGENCY'},
                diag_master=diag,
                clinical_notes=f"Initial primary assessment at {src_fac.facility_name}. Requires secondary/tertiary hospital intervention: {ref_reason}.",
                meds_to_prescribe=[(med_paracetamol, "1-0-1 After Food", "Twice Daily", 3, 6)]
            )

            # ReferralOrder
            ro = ReferralOrder.objects.create(
                referral_number=f"REF-{enc_date.strftime('%Y%m%d')}-{p_idx:04d}",
                patient=pat,
                visit=v,
                source_facility=src_fac,
                destination_facility=dst_fac,
                referring_doctor=stf_doc_local,
                urgency=urgency,
                reason=ref_reason,
                clinical_summary=f"Primary clinical evaluation at {src_fac.facility_name}. {ref_reason}. Patient stable for transport.",
                status='COMPLETED'
            )

            # Audit trail events
            ReferralEvent.objects.create(
                referral=ro,
                recorded_by_staff=stf_doc_local,
                event_type='ACKNOWLEDGED',
                specialist_findings="Referral initiated at primary center."
            )
            ReferralEvent.objects.create(
                referral=ro,
                recorded_by_staff=stf_doc_sdh if 'KC' in cohort_tag else stf_doc_dist,
                event_type='SPECIALIST_CONSULT',
                specialist_findings="Specialist examination conducted. Diagnostic confirmation and therapeutic plan formulated.",
                treatment_rendered="Inpatient stabilization, specialist medication regimen, and diagnostic staging.",
                return_advice="Discharged back to primary health center for routine continuation of care."
            )
            ReferralEvent.objects.create(
                referral=ro,
                recorded_by_staff=stf_doc_sdh if 'KC' in cohort_tag else stf_doc_dist,
                event_type='COUNTER_REFERRAL_DISCHARGE',
                return_advice="Weekly blood pressure, glucose and renal profile monitoring at Local PHC."
            )

            # Legacy Referral and Response
            legacy_ref = Referral.objects.create(
                referral_id=ro.referral_number,
                patient=pat,
                visit=v,
                consultation=c,
                source_facility=src_fac,
                destination_facility=dst_fac,
                referring_doctor=u_doc_local,
                reason=ref_reason,
                clinical_summary=ro.clinical_summary,
                urgency=urgency,
                status='COMPLETED'
            )
            ReferralResponse.objects.create(
                referral=legacy_ref,
                hospital_doctor=u_doc_local,
                specialist_findings="Evaluated and managed at hospital specialist unit.",
                treatment_summary="Inpatient management completed successfully.",
                return_advice="Counter-referred to primary health centre."
            )

            # Post-Referral Follow-Up Task
            FollowUpTask.objects.create(
                patient=pat,
                facility=src_fac,
                originating_visit=v,
                referral=ro,
                completed_in_visit=v,
                completed_by_staff=stf_doc_local,
                due_date=today + datetime.timedelta(days=7),
                category='POST_REFERRAL',
                status='COMPLETED',
                clinical_instructions="Post-referral discharge review and prescription reconciliation.",
                completed_at=timezone.now()
            )

        print(f"Seeded 8 inter-facility secondary and tertiary referrals with events, responses, and follow-ups.")

        print("\n[Step 7] Seeding Today's Live Active OPD Clinic Queue (8 October 2026)...")
        # Real-time distribution at PHC-LOCAL-01:
        # 1. Waiting for Triage: Patients 55, 56, 57
        for p_idx in [55, 56, 57]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities['PHC-LOCAL-01'],
                opd_date=today,
                queue='TRIAGE',
                status='WAITING_FOR_TRIAGE',
                complaint="Front desk intake: Fever, headache and mild throat irritation",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 120, 'dia': 80, 'pulse': 72, 'temp_f': 98.6, 'spo2': 98, 'height': 165, 'weight': 65},
                diag_master=diag_urti,
                clinical_notes="",
                is_today=True
            )

        # 2. Triaged & Waiting for Doctor: Patients 58, 59, 60
        for p_idx in [58, 59, 60]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities['PHC-LOCAL-01'],
                opd_date=today,
                queue='DOCTOR',
                status='WAITING_FOR_DOCTOR',
                complaint="Nurse triage completed: Moderate back pain and general body aches",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 126, 'dia': 82, 'pulse': 78, 'temp_f': 98.8, 'spo2': 98, 'height': 168, 'weight': 67, 'notes': 'Triaged by staff nurse. Ready for Medical Officer consultation.'},
                diag_master=diag_joint,
                clinical_notes="",
                is_today=True
            )

        # 3. In Consultation / Lab Pending: Patients 1 and 21
        for p_idx, test, diag in [(1, dt_fbg, diag_dm), (21, dt_ns1, diag_dengue)]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities['PHC-LOCAL-01'],
                opd_date=today,
                queue='LAB',
                status='LAB_PENDING',
                complaint="Doctor consultation conducted: Blood investigation ordered and specimen drawn",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 142, 'dia': 90, 'pulse': 82, 'temp_f': 99.4, 'spo2': 98, 'height': 165, 'weight': 66, 'notes': 'Specimen collected. Patient waiting in lab corridor.'},
                diag_master=diag,
                clinical_notes="Consultation initiated. Awaiting rapid lab analyzer confirmation before dispensing.",
                test_master=test,
                is_today=True
            )

        # 4. In Pharmacy Queue: Patients 2 and 22
        for p_idx, med, diag in [(2, med_metformin, diag_dm), (22, med_paracetamol, diag_urti)]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities['PHC-LOCAL-01'],
                opd_date=today,
                queue='PHARMACY',
                status='WAITING_FOR_PHARMACY',
                complaint="Consultation finished: Prescription issued, waiting at medicine dispensary window",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 130, 'dia': 84, 'pulse': 74, 'temp_f': 98.6, 'spo2': 98, 'height': 160, 'weight': 60},
                diag_master=diag,
                clinical_notes="Prescription verified by pharmacist. Awaiting physical dispensing.",
                meds_to_prescribe=[(med, "1-0-1 After Food", "Twice Daily", 14, 28)],
                is_today=True
            )

        # 5. Completed Today: Patients 3, 4, 33, 34
        for p_idx, diag, med in [(3, diag_htn, med_amlodipine), (4, diag_dm, med_metformin), (33, diag_urti, med_paracetamol), (34, diag_bronchitis, med_amoxicillin)]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities['PHC-LOCAL-01'],
                opd_date=today,
                queue='COMPLETED',
                status='COMPLETED',
                complaint="Morning OPD completed: Full journey through triage, consult, lab and pharmacy",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 124, 'dia': 80, 'pulse': 72, 'temp_f': 98.4, 'spo2': 99, 'height': 164, 'weight': 63},
                diag_master=diag,
                clinical_notes="Complete visit completed earlier today. Medications dispensed and counselled.",
                test_master=dt_fbg if p_idx == 4 else None,
                test_value_num=128 if p_idx == 4 else None,
                test_value_txt="128 mg/dL" if p_idx == 4 else "",
                meds_to_prescribe=[(med, "1-0-0 After Food", "Daily", 14, 14)],
                is_today=True
            )

        # Also add a couple of visits today at NC-LAG-01, HOSP-KC-01, and RC-A4-01
        for p_idx, fac_code, diag in [(16, 'NC-LAG-01', diag_htn), (27, 'HOSP-KC-01', diag_dengue), (19, 'RC-A4-01', diag_dm)]:
            pat, cit = patient_map[p_idx]
            create_full_encounter(
                patient=pat,
                facility=facilities[fac_code],
                opd_date=today,
                queue='COMPLETED',
                status='COMPLETED',
                complaint=f"OPD encounter at {facilities[fac_code].facility_name}",
                doctor_staff=stf_doc_local,
                doctor_user=u_doc_local,
                nurse_staff=stf_nurse_local,
                nurse_user=u_nurse_local,
                vitals_data={'sys': 130, 'dia': 84, 'pulse': 76, 'temp_f': 98.6, 'spo2': 98, 'height': 165, 'weight': 66},
                diag_master=diag,
                clinical_notes=f"Regional clinic visit on {today}.",
                meds_to_prescribe=[(med_paracetamol, "1-0-1 After Food", "Twice Daily", 5, 10)],
                is_today=True
            )

        print(f"Seeded today's live OPD queue: 14 visits at Local PHC across Triage, Doctor, Lab, Pharmacy, and Completed.")

    # 4. Final Verification and Assertions
    print("\n" + "=" * 80)
    print("ASSERTIONS & VERIFICATION OF DATASET")
    print("=" * 80)

    pat_count = Patient.objects.count()
    visit_count = Visit.objects.count()
    triage_count = TriageVitals.objects.count()
    consult_count = Consultation.objects.count()
    diag_order_count = DiagnosticOrder.objects.count()
    diag_result_count = DiagnosticResult.objects.count()
    rx_count = Prescription.objects.count()
    disp_count = Dispensation.objects.count()
    ledger_count = InventoryLedger.objects.filter(transaction_type='DISPENSE').count()
    ncd_cond_count = NCDCondition.objects.count()
    ncd_assess_count = NCDAssessment.objects.count()
    surv_count = DiseaseSurveillanceCase.objects.count()
    notif_count = PublicHealthNotification.objects.count()
    ref_count = ReferralOrder.objects.count()
    followup_count = FollowUpTask.objects.count()

    print(f"Patients:                 {pat_count}")
    print(f"Total Visits:             {visit_count}")
    print(f"Triage Records:           {triage_count}")
    print(f"Consultations:            {consult_count}")
    print(f"Diagnostic Orders:        {diag_order_count}")
    print(f"Verified Lab Results:     {diag_result_count}")
    print(f"Prescriptions:            {rx_count}")
    print(f"Dispensations:            {disp_count}")
    print(f"Ledger DISPENSE entries:  {ledger_count}")
    print(f"NCD Conditions:           {ncd_cond_count}")
    print(f"NCD Assessments:          {ncd_assess_count}")
    print(f"Surveillance Cases:       {surv_count}")
    print(f"Public Health Notifs:     {notif_count}")
    print(f"Referral Orders:          {ref_count}")
    print(f"Follow-up Tasks:          {followup_count}")

    # Today's active queue verification
    today_visits = Visit.objects.filter(opd_date=today, facility=facilities['PHC-LOCAL-01'])
    print("\nToday's OPD Queue at PHC-LOCAL-01:")
    for status_name, _ in Visit.STATUS_CHOICES:
        cnt = today_visits.filter(status=status_name).count()
        if cnt > 0:
            print(f"  - {status_name:<25}: {cnt}")

    # Assert non-zero counts everywhere
    assert pat_count == 60, f"Expected exactly 60 patients, got {pat_count}"
    assert visit_count >= 100, f"Expected >= 100 visits, got {visit_count}"
    assert triage_count >= 90, f"Expected >= 90 triage records, got {triage_count}"
    assert consult_count >= 80, f"Expected >= 80 consultations, got {consult_count}"
    assert diag_result_count >= 40, f"Expected >= 40 lab results, got {diag_result_count}"
    assert disp_count >= 60, f"Expected >= 60 dispensations, got {disp_count}"
    assert ledger_count >= 60, f"Expected >= 60 ledger DISPENSE rows, got {ledger_count}"
    assert ncd_cond_count >= 20, f"Expected >= 20 NCD conditions, got {ncd_cond_count}"
    assert ncd_assess_count >= 50, f"Expected >= 50 NCD assessments, got {ncd_assess_count}"
    assert surv_count == 12, f"Expected 12 surveillance cases, got {surv_count}"
    assert ref_count == 8, f"Expected 8 referral orders, got {ref_count}"

    # Verify zero digits in all patient names in database
    for p in Patient.objects.all():
        assert not any(c.isdigit() for c in p.name), f"Found digit in patient name: {p.name}"

    print("\nALL VERIFICATIONS AND ASSERTIONS PASSED! Dataset is pristine and production-ready.")

if __name__ == '__main__':
    generate_e2e_dataset()

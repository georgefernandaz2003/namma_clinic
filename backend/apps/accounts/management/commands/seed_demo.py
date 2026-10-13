from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
import datetime
import random

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
from apps.laboratory.models import LabTestMaster, LabOrder, LabSample, LabResult
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem
)
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.maternal.models import MaternalRecord
from apps.child.models import ChildRecord
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
    help = "Seed database with a high-volume, realistic Namma Clinic digital healthcare network demo dataset for client demonstrations."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Resetting and generating comprehensive Namma Clinic demo dataset across all facilities..."))

        rng = random.Random(42)
        today = timezone.now().date()
        now = timezone.now()

        # =====================================================================
        # 0. SAFE CLEANUP (Reverse Dependency Order)
        # =====================================================================
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
        ChildRecord.objects.all().delete()
        MaternalRecord.objects.all().delete()
        NCDRecord.objects.all().delete()
        FollowUp.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()
        PurchaseOrderItem.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        InventoryTransaction.objects.all().delete()
        MedicineBatch.objects.all().delete()
        Vendor.objects.all().delete()
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
        VisitStatusHistory.objects.all().delete()
        Visit.objects.all().delete()
        PatientDocument.objects.all().delete()
        Patient.objects.all().delete()
        Household.objects.all().delete()
        FacilityBedAllocation.objects.all().delete()
        FacilityBedCapacity.objects.all().delete()
        FacilityMaintenanceTicket.objects.all().delete()
        FacilityConsumableInventory.objects.all().delete()
        FacilityOxygenSupply.objects.all().delete()
        FacilityRelationship.objects.all().delete()
        User.objects.all().delete()
        Facility.objects.all().delete()
        Ward.objects.all().delete()
        Zone.objects.all().delete()
        District.objects.all().delete()
        State.objects.all().delete()

        # =====================================================================
        # 1. GEOGRAPHY
        # =====================================================================
        karnataka = State.objects.create(name='Karnataka', code='KA')
        dist_central = District.objects.create(state=karnataka, name='BBMP Central (Bengaluru Urban)', code='KA-BU')
        dist_rural = District.objects.create(state=karnataka, name='Bengaluru Rural', code='KA-BR')

        zone_east = Zone.objects.create(district=dist_central, name='East Zone', code='Z-EAST')
        zone_south = Zone.objects.create(district=dist_central, name='South Zone', code='Z-SOUTH')
        zone_hoskote = Zone.objects.create(district=dist_rural, name='Hoskote Zone', code='Z-HOS')

        ward12 = Ward.objects.create(zone=zone_east, ward_number=12, name='Indiranagar Ward', population=22000, slum_population=6500)
        ward14 = Ward.objects.create(zone=zone_east, ward_number=14, name='Ulsoor Ward', population=19500, slum_population=5200)
        ward45 = Ward.objects.create(zone=zone_south, ward_number=45, name='Jayanagar Ward', population=24000, slum_population=4800)
        ward_rural = Ward.objects.create(zone=zone_hoskote, ward_number=1, name='Varthur Rural Ward', population=18000, slum_population=7200)
        all_wards = [ward12, ward14, ward45, ward_rural]

        # =====================================================================
        # 2. FACILITIES (4 Tiers)
        # =====================================================================
        hosp_a = Facility.objects.create(
            facility_code='HOSP-DIST-01', facility_name='Victoria District General Hospital & Specialist Center',
            facility_type='MAIN_HOSPITAL', state=karnataka, district=dist_central, zone=zone_east, ward=ward12,
            city_or_ulb='BBMP Central', urban_rural='URBAN', address='Fort Road, Near KR Market, Bengaluru - 560002',
            latitude=12.9634, longitude=77.5750, population_served=500000, emergency_available=True,
            lab_available=True, pharmacy_available=True, teleconsultation_available=True, bed_capacity=750,
            services='Cardiology, Nephrology, General Surgery, Emergency, ICU, Teleconsultation Hub'
        )

        nc_a1 = Facility.objects.create(
            facility_code='HOSP-SUB-01', facility_name='Indiranagar Sub-District Hospital & UPHC',
            facility_type='NAMMA_CLINIC', parent_facility=hosp_a, state=karnataka, district=dist_central,
            zone=zone_east, ward=ward12, city_or_ulb='BBMP East', urban_rural='URBAN',
            address='100 Feet Road, Indiranagar, Bengaluru - 560038', latitude=12.9719, longitude=77.6412,
            population_served=35000, vulnerable_population=8500, emergency_available=True, lab_available=True,
            pharmacy_available=True, teleconsultation_available=True, bed_capacity=60,
            services='Maternal ANC, Child Care, General OPD, Basic Surgery, NCD Screening'
        )

        rc_a4 = Facility.objects.create(
            facility_code='RC-A4-04', facility_name='Varthur Rural Primary Clinic A4',
            facility_type='RURAL_CLINIC', parent_facility=nc_a1, state=karnataka, district=dist_central,
            zone=zone_east, ward=ward_rural, city_or_ulb='BBMP East Peripheral', urban_rural='RURAL',
            address='Main Bus Stand Road, Varthur Village, Bengaluru Rural - 560087', latitude=12.9406,
            longitude=77.7470, population_served=19000, vulnerable_population=7200, emergency_available=False,
            lab_available=True, pharmacy_available=True, teleconsultation_available=True, bed_capacity=10,
            services='General OPD, NCD Screening, Immunization, Basic Diagnostics'
        )

        vc_a4_1 = Facility.objects.create(
            facility_code='VC-A4-01', facility_name='Gunjur Village Satellite Clinic',
            facility_type='VILLAGE_CLINIC', parent_facility=rc_a4, state=karnataka, district=dist_central,
            zone=zone_east, ward=ward_rural, city_or_ulb='BBMP East Peripheral', urban_rural='RURAL',
            address='Gunjur Lake Road, Gunjur Village, Bengaluru Rural - 560087', latitude=12.9300,
            longitude=77.7550, population_served=8000, vulnerable_population=3100, emergency_available=False,
            lab_available=True, pharmacy_available=True, teleconsultation_available=False, bed_capacity=4,
            services='Primary Screening, Immunization, First Aid, Tele-referral'
        )

        facilities_list = [hosp_a, nc_a1, rc_a4, vc_a4_1]

        # Facility Relationships
        FacilityRelationship.objects.create(source_facility=vc_a4_1, destination_facility=rc_a4, relationship_type='REFERRAL', service='Village Primary Referral', priority='PRIMARY', distance_km=2.5)
        FacilityRelationship.objects.create(source_facility=rc_a4, destination_facility=nc_a1, relationship_type='REFERRAL', service='Sub-District Secondary Care', priority='PRIMARY', distance_km=4.2)
        FacilityRelationship.objects.create(source_facility=nc_a1, destination_facility=hosp_a, relationship_type='SPECIALIST', service='District Cardiology & Tertiary Surgery', priority='EMERGENCY', distance_km=5.0)
        FacilityRelationship.objects.create(source_facility=rc_a4, destination_facility=hosp_a, relationship_type='SPECIALIST', service='Direct Emergency ICU Referral', priority='EMERGENCY', distance_km=12.0)

        # =====================================================================
        # 3. USERS & ROLES
        # =====================================================================
        u_dist = User.objects.create_user('district', 'district@nammaclinic.gov.in', 'district123', full_name='Dr. Sunita Rao (District Health Officer)', role='DISTRICT_OFFICER', assigned_district=dist_central)

        u_dh_admin = User.objects.create_user('dh_admin', 'dh_admin@nammaclinic.gov.in', 'dh123', full_name='Dr. K. V. Sharma (District Hospital Supt)', role='HOSPITAL_ADMIN', assigned_facility=hosp_a)
        u_hosp = User.objects.create_user('hospital', 'hospital@nammaclinic.gov.in', 'hospital123', full_name='Dr. K. V. Sharma (District Hospital Supt)', role='HOSPITAL_ADMIN', assigned_facility=hosp_a)
        u_sdh_admin = User.objects.create_user('sdh_admin', 'sdh_admin@nammaclinic.gov.in', 'sdh123', full_name='Dr. Meena Swamy (Sub-District Admin)', role='HOSPITAL_ADMIN', assigned_facility=nc_a1)
        u_vh1_admin = User.objects.create_user('vh1_admin', 'vh1_admin@nammaclinic.gov.in', 'vh1admin123', full_name='Dr. Ramesh Rao (Village Hospital 1 Admin)', role='HOSPITAL_ADMIN', assigned_facility=rc_a4)
        u_vh2_admin = User.objects.create_user('vh2_admin', 'vh2_admin@nammaclinic.gov.in', 'vh2123', full_name='Dr. Anand Kumar (Village Hospital 2 Admin)', role='HOSPITAL_ADMIN', assigned_facility=vc_a4_1)

        u_dh_doc = User.objects.create_user('dh_doctor', 'dh_doctor@nammaclinic.gov.in', 'dhdoc123', full_name='Dr. Vikram Seth (District Senior Cardiologist)', role='DOCTOR', assigned_facility=hosp_a)
        u_sdh_doc = User.objects.create_user('sdh_doctor', 'sdh_doctor@nammaclinic.gov.in', 'sdhdoc123', full_name='Dr. Asha Patil (Sub-District Gynecologist)', role='DOCTOR', assigned_facility=nc_a1)
        u_vh1_doc = User.objects.create_user('vh1_doctor', 'vh1_doctor@nammaclinic.gov.in', 'vh1doc123', full_name='Dr. Rajesh Kumar (Village Hospital 1 MO)', role='DOCTOR', assigned_facility=rc_a4)
        u_vh1_doc2 = User.objects.create_user('vh1_doctor2', 'vh1_doctor2@nammaclinic.gov.in', 'vh1doc123', full_name='Dr. Ananya Sharma (VH1 Duty Doctor)', role='DOCTOR', assigned_facility=rc_a4)
        u_doc = User.objects.create_user('doctor', 'doctor@nammaclinic.gov.in', 'doctor123', full_name='Dr. Rajesh Kumar (Village Hospital 1 MO)', role='DOCTOR', assigned_facility=rc_a4)
        u_vh2_doc = User.objects.create_user('vh2_doctor', 'vh2_doctor@nammaclinic.gov.in', 'vh2doc123', full_name='Dr. Suresh V. (Village Hospital 2 MO)', role='DOCTOR', assigned_facility=vc_a4_1)

        u_dh_nurse = User.objects.create_user('dh_nurse', 'dh_nurse@nammaclinic.gov.in', 'dhnurse123', full_name='Sister Mary Joseph', role='NURSE', assigned_facility=hosp_a)
        u_sdh_nurse = User.objects.create_user('sdh_nurse', 'sdh_nurse@nammaclinic.gov.in', 'sdhnurse123', full_name='Sister Kavitha R.', role='NURSE', assigned_facility=nc_a1)
        u_vh1_nurse = User.objects.create_user('vh1_nurse', 'vh1_nurse@nammaclinic.gov.in', 'vh1nurse123', full_name='Sister Priya Nair (VH1 Staff Nurse)', role='NURSE', assigned_facility=rc_a4)
        u_nurse = User.objects.create_user('nurse', 'nurse@nammaclinic.gov.in', 'nurse123', full_name='Sister Priya Nair', role='NURSE', assigned_facility=rc_a4)

        u_dh_lab = User.objects.create_user('dh_lab', 'dh_lab@nammaclinic.gov.in', 'dhlab123', full_name='Mr. Chethan M.', role='LAB_TECHNICIAN', assigned_facility=hosp_a)
        u_vh1_lab = User.objects.create_user('vh1_lab', 'vh1_lab@nammaclinic.gov.in', 'vh1lab123', full_name='Mr. Suresh Gowda (VH1 Lab Technician)', role='LAB_TECHNICIAN', assigned_facility=rc_a4)
        u_lab = User.objects.create_user('lab', 'lab@nammaclinic.gov.in', 'lab123', full_name='Mr. Suresh Gowda', role='LAB_TECHNICIAN', assigned_facility=rc_a4)

        u_dh_pharm = User.objects.create_user('dh_pharmacy', 'dh_pharmacy@nammaclinic.gov.in', 'dhpharm123', full_name='Mr. Mahesh Babu', role='PHARMACIST', assigned_facility=hosp_a)
        u_vh1_pharm = User.objects.create_user('vh1_pharmacy', 'vh1_pharmacy@nammaclinic.gov.in', 'vh1pharm123', full_name='Mrs. Lakshmi Devi (VH1 Pharmacist)', role='PHARMACIST', assigned_facility=rc_a4)
        u_pharm = User.objects.create_user('pharmacy', 'pharmacy@nammaclinic.gov.in', 'pharmacy123', full_name='Mrs. Lakshmi Devi', role='PHARMACIST', assigned_facility=rc_a4)

        doc_by_fac = {
            hosp_a.id: u_dh_doc,
            nc_a1.id: u_sdh_doc,
            rc_a4.id: u_vh1_doc,
            vc_a4_1.id: u_vh2_doc,
        }
        nurse_by_fac = {
            hosp_a.id: u_dh_nurse,
            nc_a1.id: u_sdh_nurse,
            rc_a4.id: u_vh1_nurse,
            vc_a4_1.id: u_nurse,
        }
        pharm_by_fac = {
            hosp_a.id: u_dh_pharm,
            nc_a1.id: u_dh_pharm,
            rc_a4.id: u_vh1_pharm,
            vc_a4_1.id: u_pharm,
        }
        lab_by_fac = {
            hosp_a.id: u_dh_lab,
            nc_a1.id: u_dh_lab,
            rc_a4.id: u_vh1_lab,
            vc_a4_1.id: u_lab,
        }

        # =====================================================================
        # 4. DIAGNOSTIC TEST MASTERS (14 Tests)
        # =====================================================================
        lab_test_defs = [
            ('L-HBA1C', 'HbA1c Glycated Hemoglobin', 'Diabetes', '4.0 - 5.6 %', '%'),
            ('L-FBG', 'Fasting Blood Glucose (FBG)', 'Diabetes', '70 - 100 mg/dL', 'mg/dL'),
            ('L-RBG', 'Random Blood Glucose (Rapid Strip)', 'Diabetes', '70 - 140 mg/dL', 'mg/dL'),
            ('L-HB', 'Hemoglobin (Hb Estimation)', 'Hematology', '12.0 - 15.5 g/dL', 'g/dL'),
            ('L-LIPID', 'Lipid Profile (Cholesterol & Triglycerides)', 'Biochemistry', 'Desirable < 200 mg/dL', 'mg/dL'),
            ('L-DENGUE', 'Dengue NS1 Antigen Rapid Test Card', 'Serology', 'Negative', 'Result'),
            ('L-MALARIA', 'Malaria Antigen (Pf/Pv) Rapid Test', 'Serology', 'Negative', 'Result'),
            ('L-URINE-PROT', 'Urine Albumin / Protein Test', 'Urinalysis', 'Nil / Negative', 'Grade'),
            ('L-URINE-SUGAR', 'Urine Sugar Test (Benedict / Strip)', 'Urinalysis', 'Nil / Negative', 'Grade'),
            ('L-TB-SPUTUM', 'Sputum Smear for AFB (Tuberculosis)', 'Microbiology', 'Negative for AFB', 'Result'),
            ('L-HIV', 'HIV 1 & 2 Rapid Screening Card', 'Serology', 'Non-Reactive / Negative', 'Result'),
            ('L-HBSAG', 'Hepatitis B Surface Antigen (HBsAg Rapid)', 'Serology', 'Non-Reactive / Negative', 'Result'),
            ('L-PREG-RAPID', 'Urine Pregnancy Test (UPT Card)', 'Maternal RCH', 'Negative', 'Result'),
            ('L-LFT', 'Liver Function Test (Bilirubin & LFT)', 'Biochemistry', 'Bilirubin < 1.2 mg/dL, SGPT < 40 U/L', 'mg/dL, U/L'),
        ]
        lab_tests = [
            LabTestMaster.objects.create(code=code, name=name, category=cat, reference_range=rr, unit=unit)
            for code, name, cat, rr, unit in lab_test_defs
        ]

        # =====================================================================
        # 5. MEDICINE MASTERS & VENDORS (28 Essential Medicines)
        # =====================================================================
        med_defs = [
            ('Metformin HCl', 'Glycomet', '500 mg', 'Tablet', 'Tablets', 'Anti-Diabetic', 60, 120),
            ('Glimepiride', 'Amaryl', '2 mg', 'Tablet', 'Tablets', 'Anti-Diabetic', 40, 80),
            ('Amlodipine Besylate', 'Amlopres', '5 mg', 'Tablet', 'Tablets', 'Anti-Hypertensive', 60, 120),
            ('Telmisartan', 'Telma', '40 mg', 'Tablet', 'Tablets', 'Anti-Hypertensive', 50, 100),
            ('Atenolol', 'Betacard', '50 mg', 'Tablet', 'Tablets', 'Anti-Hypertensive', 40, 80),
            ('Enalapril Maleate', 'Envas', '5 mg', 'Tablet', 'Tablets', 'Anti-Hypertensive', 30, 60),
            ('Paracetamol', 'Dolo', '650 mg', 'Tablet', 'Tablets', 'Analgesic / Antipyretic', 120, 250),
            ('Paracetamol Syrup', 'Calpol Syrup', '250mg/5ml', 'Syrup', 'Bottles', 'Analgesic / Antipyretic', 30, 60),
            ('Ibuprofen', 'Brufen', '400 mg', 'Tablet', 'Tablets', 'NSAID / Analgesic', 50, 100),
            ('Diclofenac Sodium Gel', 'Voveran Gel', '30 g', 'Ointment', 'Tubes', 'Topical Analgesic', 25, 50),
            ('Amoxicillin Trihydrate', 'Mox', '500 mg', 'Capsule', 'Capsules', 'Antibiotic', 60, 120),
            ('Azithromycin', 'Azee', '500 mg', 'Tablet', 'Tablets', 'Antibiotic', 40, 80),
            ('Ciprofloxacin', 'Cifran', '500 mg', 'Tablet', 'Tablets', 'Antibiotic', 40, 80),
            ('Cefixime', 'Taxim-O', '200 mg', 'Tablet', 'Tablets', 'Antibiotic', 30, 60),
            ('Cetirizine HCl', 'Cetzine', '10 mg', 'Tablet', 'Tablets', 'Antihistamine', 50, 100),
            ('Pantoprazole', 'Pan 40', '40 mg', 'Tablet', 'Tablets', 'Antacid / PPI', 60, 120),
            ('Omeprazole', 'Omez', '20 mg', 'Capsule', 'Capsules', 'Antacid / PPI', 50, 100),
            ('Oral Rehydration Salts', 'Electral ORS', '21.8 g', 'Powder', 'Sachets', 'Gastrointestinal', 100, 200),
            ('Iron & Folic Acid', 'IFA Red', '100mg Fe + 500mcg FA', 'Tablet', 'Tablets', 'Maternal Health', 80, 160),
            ('Calcium with Vitamin D3', 'Shelcal 500', '500 mg', 'Tablet', 'Tablets', 'Maternal & Geriatric', 70, 140),
            ('Albendazole', 'Zentel', '400 mg', 'Tablet', 'Tablets', 'Anthelmintic', 40, 80),
            ('Salbutamol Inhaler', 'Asthalin Inhaler', '100 mcg', 'Inhaler', 'Canisters', 'Respiratory', 20, 40),
            ('Cough Syrup (Dextromethorphan)', 'Benadryl DR', '100 ml', 'Syrup', 'Bottles', 'Respiratory', 30, 60),
            ('Atorvastatin', 'Atorva', '10 mg', 'Tablet', 'Tablets', 'Cardiovascular', 40, 80),
            ('Povidone Iodine 5%', 'Betadine', '20 g', 'Ointment', 'Tubes', 'Antiseptic', 30, 60),
            ('Metronidazole', 'Flagyl', '400 mg', 'Tablet', 'Tablets', 'Antiprotozoal', 40, 80),
            ('B-Complex with Zinc', 'Becozinc', 'Standard', 'Capsule', 'Capsules', 'Nutritional Supplement', 60, 120),
            ('Hydrochlorothiazide', 'Aquazide', '12.5 mg', 'Tablet', 'Tablets', 'Diuretic', 30, 60),
        ]
        medicines = [
            MedicineMaster.objects.create(
                generic_name=g, brand_name=b, strength=s, dosage_form=df,
                unit=u, category=cat, minimum_stock=min_s, reorder_level=re_s
            )
            for g, b, s, df, u, cat, min_s, re_s in med_defs
        ]

        vendors_data = [
            ('KSMSCL (Karnataka State Medical Supplies Corp Ltd)', 'Mr. R. K. Hegde (General Manager)', '080-22345678', 'procurement@ksmscl.in', 'Rehabilitative Building, Anand Rao Circle, Bengaluru', '29AAACK1234F1Z5'),
            ('Karnataka Antibiotics & Pharmaceuticals Ltd (KAPL)', 'Dr. S. M. Patel', '080-28392555', 'sales@kaplindia.com', 'Peenya Industrial Area, 1st Stage, Bengaluru', '29AAACK5678F1Z9'),
            ('Micro Labs Ltd (Public Health Division)', 'Mr. Ramesh Babu', '080-26781234', 'institutional@microlabs.in', 'Kudlu Gate, Hosur Road, Bengaluru', '29AAACM1122G1Z1'),
            ('Cipla Healthcare Logistics', 'Mrs. Vani Murthy', '080-25559876', 'blr_depot@cipla.com', 'Bannerghatta Road, Bengaluru', '29AAACC9988H1Z4'),
            ('MedPlus Institutional Distribution', 'Mr. Naveen Gowda', '080-41234567', 'supply@medplus.co.in', 'BTM Layout 2nd Stage, Bengaluru', '29AAACM3344J1Z8'),
        ]
        vendors = [
            Vendor.objects.create(
                vendor_name=vname, contact_person=cp, phone=ph, email=em,
                address=addr, gst_number=gst, status='ACTIVE'
            )
            for vname, cp, ph, em, addr, gst in vendors_data
        ]

        # =====================================================================
        # 6. MEDICINE BATCHES & PURCHASE ORDERS (100+ Batches, 60+ POs)
        # =====================================================================
        batches = []
        batch_seq = 1
        for fac in facilities_list:
            for idx, med in enumerate(medicines):
                v_choice = vendors[idx % len(vendors)]
                # Low stock & out-of-stock variations for pharmacy dashboard realism
                if idx in [4, 11]:  # Atenolol, Azithromycin
                    act_qty = rng.randint(8, med.minimum_stock - 5)
                elif idx == 21:     # Salbutamol Inhaler (out of stock at peripheral clinics)
                    act_qty = 0 if fac in [rc_a4, vc_a4_1] else rng.randint(5, 12)
                else:
                    act_qty = rng.randint(150, 800)

                batches.append(MedicineBatch(
                    facility=fac, medicine=med, batch_number=f"B-{fac.facility_code}-{med.id:02d}-A{batch_seq}",
                    vendor=v_choice, supplier=v_choice.vendor_name,
                    mfg_date=today - datetime.timedelta(days=rng.randint(60, 180)),
                    expiry_date=today + datetime.timedelta(days=rng.randint(90, 365)),
                    quantity=act_qty, unit_cost=round(rng.uniform(0.40, 4.50), 2),
                    status='ACTIVE' if act_qty > 0 else 'EXHAUSTED'
                ))
                batch_seq += 1

                # Expiring-soon batch for some medicines
                # Expiring-soon batch for selected medicines (12 total across facilities)
                if idx % 10 == 0:
                    batches.append(MedicineBatch(
                        facility=fac, medicine=med, batch_number=f"B-{fac.facility_code}-{med.id:02d}-EXP{batch_seq}",
                        vendor=v_choice, supplier=v_choice.vendor_name,
                        mfg_date=today - datetime.timedelta(days=rng.randint(180, 300)),
                        expiry_date=today + datetime.timedelta(days=rng.randint(10, 45)),
                        quantity=rng.randint(15, 60), unit_cost=round(rng.uniform(0.40, 4.50), 2),
                        status='EXPIRING_SOON'
                    ))
                    batch_seq += 1

                # Expired batch for selected medicines (8 total across facilities)
                if idx % 14 == 1:
                    batches.append(MedicineBatch(
                        facility=fac, medicine=med, batch_number=f"B-{fac.facility_code}-{med.id:02d}-OLD{batch_seq}",
                        vendor=v_choice, supplier=v_choice.vendor_name,
                        mfg_date=today - datetime.timedelta(days=rng.randint(380, 500)),
                        expiry_date=today - datetime.timedelta(days=rng.randint(5, 40)),
                        quantity=rng.randint(5, 30), unit_cost=round(rng.uniform(0.40, 4.50), 2),
                        status='EXPIRED'
                    ))
                    batch_seq += 1

                # Exhausted batch for selected medicines (8 total across facilities)
                if idx % 14 == 3:
                    batches.append(MedicineBatch(
                        facility=fac, medicine=med, batch_number=f"B-{fac.facility_code}-{med.id:02d}-EXH{batch_seq}",
                        vendor=v_choice, supplier=v_choice.vendor_name,
                        mfg_date=today - datetime.timedelta(days=220),
                        expiry_date=today + datetime.timedelta(days=120),
                        quantity=0, unit_cost=round(rng.uniform(0.40, 4.50), 2),
                        status='EXHAUSTED'
                    ))
                    batch_seq += 1

        created_batches = MedicineBatch.objects.bulk_create(batches)

        # Purchase Orders across past 90 days (60+ POs)
        po_statuses = ['DRAFT', 'PENDING_APPROVAL', 'ORDERED', 'RECEIVED', 'PARTIALLY_RECEIVED']
        pos_to_create = []
        po_num_counter = 1
        for fac in facilities_list:
            for day_offset in range(2, 90, 5):
                po_date = today - datetime.timedelta(days=day_offset)
                v_choice = vendors[po_num_counter % len(vendors)]
                st = po_statuses[po_num_counter % len(po_statuses)]
                pos_to_create.append(PurchaseOrder(
                    po_number=f"PO-{fac.facility_code[:3]}-{po_date.strftime('%Y%m')}-{po_num_counter:03d}",
                    vendor=v_choice, facility=fac, order_date=po_date,
                    expected_delivery_date=po_date + datetime.timedelta(days=7),
                    status=st, created_by=pharm_by_fac[fac.id],
                    approved_by=u_dist if st in ['ORDERED', 'RECEIVED', 'PARTIALLY_RECEIVED'] else None,
                    approved_at=now - datetime.timedelta(days=day_offset - 1) if st in ['ORDERED', 'RECEIVED', 'PARTIALLY_RECEIVED'] else None,
                    notes=f"Periodic pharmaceutical replenishment for {fac.facility_name}."
                ))
                po_num_counter += 1

        created_pos = PurchaseOrder.objects.bulk_create(pos_to_create)

        po_items_to_create = []
        for po in created_pos:
            med_sample = rng.sample(medicines, k=rng.randint(2, 4))
            tot = 0.0
            for med in med_sample:
                qty = rng.randint(100, 500)
                price = round(rng.uniform(0.45, 3.20), 2)
                tot += qty * price
                rec_qty = qty if po.status == 'RECEIVED' else (qty // 2 if po.status == 'PARTIALLY_RECEIVED' else 0)
                po_items_to_create.append(PurchaseOrderItem(
                    purchase_order=po, medicine=med, ordered_quantity=qty,
                    received_quantity=rec_qty, unit_price=price, total_price=round(qty * price, 2)
                ))
            po.total_amount = round(tot, 2)
            po.save(update_fields=['total_amount'])

        PurchaseOrderItem.objects.bulk_create(po_items_to_create)

        # =====================================================================
        # 7. PATIENTS (720 Patients across 4 Facilities)
        # =====================================================================
        first_names_male = [
            'Ramesh', 'Suresh', 'Rajesh', 'Narayana', 'Manjunath', 'Venkatesh', 'Anand', 'Chethan',
            'Vijay', 'Prakash', 'Raghavendra', 'Basavaraj', 'Shankar', 'Sunil', 'Vinod', 'Harish',
            'Praveen', 'Kiran', 'Mahesh', 'Sandeep', 'Ganesh', 'Satish', 'Ravi', 'Santosh',
            'Deepak', 'Ajay', 'Karthik', 'Arun', 'Naveen', 'Bharath', 'Manoj', 'Pradeep',
            'Mohan', 'Girish', 'Lokesh', 'Shiva', 'Jagadeesh', 'Somasekhar', 'Mallikarjun', 'Chandra'
        ]
        first_names_female = [
            'Kavitha', 'Anita', 'Lakshmi', 'Gowramma', 'Sunita', 'Priya', 'Asha', 'Ananya',
            'Meena', 'Radha', 'Shilpa', 'Poornima', 'Meenakshi', 'Deepa', 'Shweta', 'Rekha',
            'Manjula', 'Geetha', 'Roopa', 'Savitha', 'Saraswathi', 'Parvathi', 'Vani', 'Shanti',
            'Bhavani', 'Sushma', 'Vidya', 'Usha', 'Kamala', 'Renuka', 'Divya', 'Archana',
            'Padmavathi', 'Shobha', 'Sowmya', 'Tejaswini', 'Pushpa', 'Nalini', 'Bhagya', 'Yashoda'
        ]
        first_names_other = ['Kiran', 'Bobby', 'Sneha', 'Jyothi', 'Pinky', 'Chandni', 'Preeti', 'Shashi']
        last_names = [
            'Kumar', 'Swamy', 'Patil', 'Rao', 'Gowda', 'Devi', 'Sharma', 'Nair', 'Joseph',
            'Reddy', 'Shetty', 'Bhat', 'Hegde', 'Joshi', 'Kulkarni', 'Murthy', 'Prasad',
            'Acharya', 'Nayak', 'Babu', 'Iyengar', 'Naidu', 'Menon', 'Pillai', 'Deshmukh'
        ]
        localities = [
            'Indiranagar Slum Pocket 1', 'Indiranagar 100ft Road Catchment', 'Ulsoor Lake Colony BPL',
            'Ulsoor Bazar Settlement', 'Jayanagar 4th Block Catchment', 'Jayanagar Slum Line 2',
            'Varthur Lake BPL Slum Line 4', 'Varthur Village Main Settlement', 'Gunjur Village Colony B',
            'Gunjur Peripheral Rural Pocket', 'HAL 2nd Stage Settlement', 'Domlur Village BPL Colony'
        ]

        patients_to_create = []
        patient_count = 720
        # Age breakdown: infants (0-1: 50), children (2-14: 100), adolescents (15-24: 100), adults (25-59: 320), elderly (60+: 150)
        age_cohorts = (
            [(0, 1)] * 50 +
            [(2, 14)] * 100 +
            [(15, 24)] * 100 +
            [(25, 59)] * 320 +
            [(60, 85)] * 150
        )
        rng.shuffle(age_cohorts)

        for p_idx in range(patient_count):
            fac = facilities_list[p_idx % 4]
            ward = all_wards[p_idx % len(all_wards)]
            min_a, max_a = age_cohorts[p_idx]
            target_age = rng.randint(min_a, max_a)

            # Determine gender
            if p_idx % 35 == 0:
                g = 'OTHER'
                fname = rng.choice(first_names_other)
            elif p_idx % 2 == 0:
                g = 'MALE'
                fname = rng.choice(first_names_male)
            else:
                g = 'FEMALE'
                fname = rng.choice(first_names_female)

            lname = rng.choice(last_names)
            p_name = f"{fname} {lname}"

            # Calculate DOB strictly consistent with completed age as of today
            dob_year = today.year - target_age
            dob_month = rng.randint(1, 12)
            dob_day = rng.randint(1, 28)
            cand_dob = datetime.date(dob_year, dob_month, dob_day)
            if cand_dob > today:
                cand_dob = datetime.date(dob_year - 1, dob_month, dob_day)

            # Exact calendar age calculation
            exact_age = today.year - cand_dob.year - ((today.month, today.day) < (cand_dob.month, cand_dob.day))

            # Realistic vulnerability tags matching public health intelligence services
            if g == 'FEMALE' and 18 <= exact_age <= 42 and p_idx % 4 == 0:
                v_info = 'High Risk Pregnancy ANC' if p_idx % 8 == 0 else 'PREGNANT'
            elif exact_age >= 60:
                v_info = 'Senior Citizen / Geriatric Care' if p_idx % 3 == 0 else 'ELDERLY'
            elif p_idx % 15 == 0:
                v_info = 'Person with Disability (PwD)'
            elif p_idx % 7 == 0:
                v_info = 'Hypertension / Diabetic comorbidity'
            elif p_idx % 3 == 0:
                v_info = 'Slum Resident / Low Income Group'
            elif p_idx % 25 == 0:
                v_info = 'UNKNOWN'
            else:
                v_info = 'General / Non-Vulnerable'

            mobile_num = f"98{rng.randint(10000000, 99999999)}"
            abha_num = f"91-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"
            loc = localities[p_idx % len(localities)]

            patients_to_create.append(Patient(
                patient_id=f"NC-{cand_dob.strftime('%Y%m')}-{p_idx+1:04d}",
                name=p_name,
                date_of_birth=cand_dob,
                age=exact_age,
                gender=g,
                mobile=mobile_num,
                address=f"Door #{rng.randint(1, 350)}, {loc}, Ward {ward.ward_number}",
                ward=ward,
                district=dist_central,
                ABHA_ID_DEMO=abha_num,
                emergency_contact=f"98{rng.randint(10000000, 99999999)} (Family)",
                vulnerability_information=v_info,
                registered_at_facility=fac
            ))

        created_patients = Patient.objects.bulk_create(patients_to_create)

        # =====================================================================
        # 8. VISITS & QUEUES (1400 Visits: ~135 Today, ~1265 Historical)
        # =====================================================================
        complaints_pool = [
            ('Acute high fever with chills, body ache and severe headache', 'FEVER', 'EMERGENCY'),
            ('Chronic joint pain, knee swelling and bilateral hypertension review', 'CHRONIC', 'NORMAL'),
            ('Dizziness, severe fatigue, blurred vision for 5 days', 'DIABETES', 'HIGH'),
            ('Persistent dry cough, sore throat and mild chest discomfort for 4 days', 'RESPIRATORY', 'NORMAL'),
            ('Acute watery diarrhea, mild dehydration and abdominal cramps', 'GI', 'HIGH'),
            ('Routine 2nd Trimester ANC Checkup, fetal heart check and BP monitoring', 'ANC', 'NORMAL'),
            ('Follow-up blood pressure check and anti-hypertensive medication renewal', 'NCD', 'NORMAL'),
            ('Generalized itchy skin rash, erythema and contact dermatitis lesions', 'DERMATOLOGY', 'NORMAL'),
            ('Acute lower back ache after heavy lifting with muscular spasm', 'ORTHO', 'NORMAL'),
            ('Loss of appetite, fatigue and pallor evaluation for anemia', 'GENERAL', 'NORMAL'),
            ('Severe sudden onset shortness of breath and chest tightness', 'EMERGENCY_CHEST', 'EMERGENCY'),
            ('Pediatric fever, poor feeding and nasal congestion for 2 days', 'PEDIATRIC', 'HIGH'),
        ]

        visits_to_create = []
        tokens_to_create = []

        # Today's visits: ~135 across 4 facilities
        # Target queue distribution:
        # WAITING_FOR_TRIAGE (15), IN_TRIAGE (10), TRIAGED (10), WAITING_FOR_DOCTOR (20),
        # IN_CONSULTATION (15), LAB_PENDING (12), LAB_IN_PROGRESS (10), LAB_COMPLETED (8),
        # WAITING_FOR_PHARMACY (15), IN_PHARMACY (10), COMPLETED (10)
        today_queue_plan = [
            ('TRIAGE', 'WAITING_FOR_TRIAGE', 15),
            ('TRIAGE', 'IN_TRIAGE', 10),
            ('DOCTOR', 'TRIAGED', 10),
            ('DOCTOR', 'WAITING_FOR_DOCTOR', 20),
            ('DOCTOR', 'IN_CONSULTATION', 15),
            ('LAB', 'LAB_PENDING', 12),
            ('LAB', 'LAB_IN_PROGRESS', 10),
            ('DOCTOR', 'LAB_COMPLETED', 8),
            ('PHARMACY', 'WAITING_FOR_PHARMACY', 15),
            ('PHARMACY', 'IN_PHARMACY', 10),
            ('COMPLETED', 'COMPLETED', 10),
        ]

        today_visit_records = []
        today_pt_idx = 0
        facility_today_token_counters = {fac.id: 1 for fac in facilities_list}

        for q_name, s_name, count in today_queue_plan:
            for _ in range(count):
                fac = facilities_list[today_pt_idx % 4]
                pt = created_patients[today_pt_idx % len(created_patients)]
                today_pt_idx += 1

                t_num = facility_today_token_counters[fac.id]
                facility_today_token_counters[fac.id] += 1

                cc_text, cc_cat, def_prio = complaints_pool[today_pt_idx % len(complaints_pool)]
                # Controlled priority distribution: small realistic number of EMERGENCY and HIGH
                if (cc_cat == 'EMERGENCY_CHEST' and t_num <= 2) or (t_num == 1 and fac == hosp_a):
                    prio = 'EMERGENCY'
                elif (cc_cat in ['ANC', 'FEVER'] and t_num % 5 == 0) or t_num in [4, 9]:
                    prio = 'HIGH'
                else:
                    prio = 'NORMAL'

                arr_minutes_ago = rng.randint(20, 240)
                arr_time = now - datetime.timedelta(minutes=arr_minutes_ago)

                # Set workflow timestamps according to progression
                t_start = arr_time + datetime.timedelta(minutes=5) if s_name != 'WAITING_FOR_TRIAGE' else None
                t_end = t_start + datetime.timedelta(minutes=8) if t_start and s_name not in ['IN_TRIAGE'] else None
                c_start = t_end + datetime.timedelta(minutes=10) if t_end and s_name not in ['TRIAGED', 'WAITING_FOR_DOCTOR'] else None
                c_end = c_start + datetime.timedelta(minutes=15) if c_start and s_name not in ['IN_CONSULTATION'] else None
                comp_time = c_end + datetime.timedelta(minutes=20) if c_end and s_name == 'COMPLETED' else None

                v_type = 'MATERNAL_ANC' if 'ANC' in cc_cat else ('NCD_SCREENING' if cc_cat in ['CHRONIC', 'DIABETES'] else 'GENERAL_OPD')

                v = Visit(
                    visit_id=f"VIS-{fac.facility_code}-{today.strftime('%Y%m%d')}-{t_num:04d}",
                    patient=pt, facility=fac, opd_date=today, visit_date=arr_time,
                    visit_type=v_type, priority=prio, current_queue=q_name, status=s_name,
                    chief_complaint=cc_text, assigned_doctor=doc_by_fac[fac.id],
                    arrival_time=arr_time, triage_start_time=t_start, triage_end_time=t_end,
                    consultation_start_time=c_start, consultation_end_time=c_end,
                    completed_time=comp_time
                )
                today_visit_records.append(v)

                # Matching Token
                tokens_to_create.append(Token(
                    token_number=t_num, visit=v, facility=fac, date=today,
                    priority=prio, status='COMPLETED' if s_name == 'COMPLETED' else 'WAITING'
                ))

        visits_to_create.extend(today_visit_records)

        # Historical Visits: past 1 to 90 days (~1265 visits)
        hist_days = list(range(1, 91))
        hist_visit_records = []
        h_pt_cursor = today_pt_idx

        for d_offset in hist_days:
            past_date = today - datetime.timedelta(days=d_offset)
            # More visits on weekdays, fewer on weekends
            is_weekend = past_date.weekday() in [5, 6]
            day_visits_count = rng.randint(6, 12) if is_weekend else rng.randint(12, 18)

            fac_token_map = {fac.id: 1 for fac in facilities_list}
            for _ in range(day_visits_count):
                fac = facilities_list[h_pt_cursor % 4]
                pt = created_patients[h_pt_cursor % len(created_patients)]
                h_pt_cursor += 1

                t_num = fac_token_map[fac.id]
                fac_token_map[fac.id] += 1

                cc_text, cc_cat, def_prio = complaints_pool[h_pt_cursor % len(complaints_pool)]
                prio = 'EMERGENCY' if cc_cat == 'EMERGENCY_CHEST' or t_num == 1 else (
                    'HIGH' if cc_cat in ['ANC', 'FEVER'] or t_num % 7 == 0 else 'NORMAL'
                )

                arr_h = rng.randint(8, 15)
                arr_m = rng.randint(0, 59)
                arr_time = timezone.make_aware(datetime.datetime.combine(past_date, datetime.time(arr_h, arr_m)))
                t_start = arr_time + datetime.timedelta(minutes=5)
                t_end = t_start + datetime.timedelta(minutes=7)
                c_start = t_end + datetime.timedelta(minutes=10)
                c_end = c_start + datetime.timedelta(minutes=14)
                comp_time = c_end + datetime.timedelta(minutes=15)

                # Realistic status distribution for historical visits
                roll = rng.random()
                if roll < 0.94:
                    s_name = 'COMPLETED'
                    q_name = 'COMPLETED'
                elif roll < 0.97:
                    s_name = 'CANCELLED'
                    q_name = 'COMPLETED'
                    comp_time = None
                else:
                    s_name = 'NO_SHOW'
                    q_name = 'COMPLETED'
                    comp_time = None

                v_type = 'MATERNAL_ANC' if 'ANC' in cc_cat else ('NCD_SCREENING' if cc_cat in ['CHRONIC', 'DIABETES'] else 'GENERAL_OPD')

                v = Visit(
                    visit_id=f"VIS-{fac.facility_code}-{past_date.strftime('%Y%m%d')}-{t_num:04d}",
                    patient=pt, facility=fac, opd_date=past_date, visit_date=arr_time,
                    visit_type=v_type, priority=prio, current_queue=q_name, status=s_name,
                    chief_complaint=cc_text, assigned_doctor=doc_by_fac[fac.id],
                    arrival_time=arr_time, triage_start_time=t_start, triage_end_time=t_end,
                    consultation_start_time=c_start, consultation_end_time=c_end,
                    completed_time=comp_time
                )
                hist_visit_records.append(v)

                tokens_to_create.append(Token(
                    token_number=t_num, visit=v, facility=fac, date=past_date,
                    priority=prio, status='COMPLETED' if s_name == 'COMPLETED' else 'CANCELLED'
                ))

        visits_to_create.extend(hist_visit_records)
        created_visits = Visit.objects.bulk_create(visits_to_create)

        # Connect tokens to the created visits
        for idx, v in enumerate(created_visits):
            tokens_to_create[idx].visit = v
            tokens_to_create[idx].visit_id = v.id

        Token.objects.bulk_create(tokens_to_create)

        # =====================================================================
        # 9. TRIAGE VITALS (1000+ Records)
        # =====================================================================
        # Only create triage records for visits that reached triage stage or beyond
        eligible_triage_statuses = [
            'IN_TRIAGE', 'TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION',
            'LAB_PENDING', 'LAB_IN_PROGRESS', 'LAB_COMPLETED',
            'WAITING_FOR_PHARMACY', 'IN_PHARMACY', 'COMPLETED'
        ]
        triage_visits = [v for v in created_visits if v.status in eligible_triage_statuses]

        triages_to_create = []
        for v in triage_visits:
            pt = v.patient
            age = pt.age

            # Pediatric vs Adult vitals
            if age <= 5:
                bp_sys = rng.randint(85, 105)
                bp_dia = rng.randint(55, 70)
                pulse = rng.randint(95, 130)
                resp = rng.randint(22, 32)
                h_cm = round(rng.uniform(60.0, 105.0), 1)
                w_kg = round(rng.uniform(5.0, 18.0), 1)
                sugar = rng.randint(75, 120)
            elif age <= 14:
                bp_sys = rng.randint(95, 115)
                bp_dia = rng.randint(60, 75)
                pulse = rng.randint(75, 105)
                resp = rng.randint(18, 24)
                h_cm = round(rng.uniform(110.0, 150.0), 1)
                w_kg = round(rng.uniform(20.0, 45.0), 1)
                sugar = rng.randint(80, 130)
            else:
                # Adults: introduce realistic abnormal clinical values (hypertension, hyperglycemia, fever, hypoxia)
                has_high_bp = rng.random() < 0.28 or age >= 55
                has_diabetes = rng.random() < 0.22 or age >= 50
                bp_sys = rng.randint(142, 178) if has_high_bp else rng.randint(110, 130)
                bp_dia = rng.randint(92, 108) if has_high_bp else rng.randint(70, 84)
                pulse = rng.randint(64, 98)
                resp = rng.randint(15, 22)
                h_cm = round(rng.uniform(150.0, 178.0), 1)
                w_kg = round(rng.uniform(50.0, 88.0), 1)
                sugar = rng.randint(165, 275) if has_diabetes else rng.randint(85, 135)

            # Temperature and fever flag
            has_fever = 'fever' in v.chief_complaint.lower() or rng.random() < 0.15
            temp_f = round(rng.uniform(100.5, 103.2), 1) if has_fever else round(rng.uniform(97.8, 99.1), 1)

            # SpO2
            has_hypoxia = v.priority == 'EMERGENCY' or rng.random() < 0.05
            spo2 = rng.randint(89, 94) if has_hypoxia else rng.randint(96, 99)

            h_m = float(h_cm) / 100.0
            calc_bmi = round(float(w_kg) / (h_m * h_m), 1)

            hb_flag = bp_sys >= 140 or bp_dia >= 90
            hg_flag = sugar >= 160
            fev_flag = temp_f >= 100.4
            hyp_flag = spo2 < 95
            preg_risk = pt.gender == 'FEMALE' and ('PREGNANT' in pt.vulnerability_information.upper() or 'ANC' in pt.vulnerability_information.upper()) and (hb_flag or hg_flag)
            emg_flag = v.priority == 'EMERGENCY' or (hb_flag and bp_sys >= 170) or hyp_flag
            ncd_flag = hb_flag or hg_flag or age >= 50

            nurse_usr = nurse_by_fac[v.facility_id]

            triages_to_create.append(TriageVitals(
                visit=v, patient=pt, nurse=nurse_usr,
                blood_pressure_systolic=bp_sys, blood_pressure_diastolic=bp_dia,
                pulse_bpm=pulse, temperature_f=temp_f, spo2_percent=spo2,
                respiratory_rate=resp, height_cm=h_cm, weight_kg=w_kg, bmi=calc_bmi,
                blood_glucose_mgdl=sugar,
                high_bp_flag=hb_flag, high_glucose_flag=hg_flag, fever_flag=fev_flag,
                low_spo2_flag=hyp_flag, pregnancy_high_risk_flag=preg_risk,
                emergency_flag=emg_flag, ncd_risk_flag=ncd_flag,
                nurse_notes=f"Vitals logged by {nurse_usr.full_name}. Priority {v.priority}."
            ))

        TriageVitals.objects.bulk_create(triages_to_create)

        # =====================================================================
        # 10. CONSULTATIONS & DIAGNOSES (850+ Records)
        # =====================================================================
        doc_consult_statuses = [
            'IN_CONSULTATION', 'LAB_PENDING', 'LAB_IN_PROGRESS', 'LAB_COMPLETED',
            'WAITING_FOR_PHARMACY', 'IN_PHARMACY', 'COMPLETED'
        ]
        consult_visits = [v for v in created_visits if v.status in doc_consult_statuses]

        clinical_catalog = [
            ('J06.9', 'Acute Upper Respiratory Tract Infection', 'Pharyngeal congestion, clear rhinorrhea, mild tonsillar hypertrophy.', 'Paracetamol 650mg TDS x 3d, Cetirizine 10mg OD x 5d, steam inhalation, warm saline gargle.'),
            ('I10', 'Essential (Primary) Hypertension Stage II', 'Elevated arterial pressure >140/90 mmHg, no target organ damage detected.', 'Telmisartan 40mg OD morning, lifestyle salt restriction, review in 14 days.'),
            ('E11.9', 'Type 2 Diabetes Mellitus without Complications', 'Elevated random blood glucose, classic osmotic symptoms (polyuria/polydipsia).', 'Metformin 500mg BD after food, diabetic dietary counseling, HbA1c test ordered.'),
            ('A90', 'Dengue Fever (Classic Dengue)', 'High fever with severe retro-orbital headache, arthralgia and facial flushing.', 'Stat Dengue NS1 card test, oral hydration with ORS, Paracetamol SOS, review CBC platelet counts daily.'),
            ('A09', 'Infectious Gastroenteritis and Colitis', 'Dehydration signs, mild diffuse abdominal tenderness, loose watery stools.', 'Oral Rehydration Solution (ORS) 1 sachet in 1L water, Zinc supplement, hydration monitoring.'),
            ('D50.9', 'Iron Deficiency Anemia, Unspecified', 'Conjunctival pallor, koilonychia signs, severe fatigue.', 'Iron & Folic Acid tablets 1 OD x 30 days, dietary iron counseling, repeat Hb in 4 weeks.'),
            ('K29.7', 'Gastritis and Acid Peptic Disease', 'Epigastric burning sensation, postprandial fullness, acid regurgitation.', 'Pantoprazole 40mg OD before breakfast x 14 days, dietary avoidance of spicy/fried foods.'),
            ('L23.9', 'Allergic Contact Dermatitis / Eczema', 'Erythematous pruritic maculopapular rash, localized excoriations.', 'Cetirizine 10mg OD x 7 days, topical soothing calamine lotion, identify and eliminate contact allergens.'),
            ('R50.9', 'Acute Febrile Illness (Viral Pyrexia)', 'Febrile episode without localized signs, mild malaise.', 'Paracetamol 650mg SOS, adequate fluid intake, danger signs explained.'),
            ('T14.9', 'Minor Blunt Trauma / Soft Tissue Contusion', 'Localized ecchymosis and soft tissue swelling, no bony crepitus or deformity.', 'Diclofenac gel topical application TDS, cold compress, rest affected limb.'),
            ('O99.0', 'Anemia Complicating Pregnancy (Mild)', 'Gestational mild pallor, 2nd trimester routine review.', 'Continue prophylactic Iron & Folic Acid + Calcium Vit D3 tablets, schedule anomaly scan.'),
            ('J45.9', 'Bronchial Asthma, Unspecified', 'Expiratory wheezing on chest auscultation, prolonged expiration.', 'Salbutamol MDI inhaler 2 puffs SOS, avoid dust/cold exposure, review in 7 days.'),
            ('A01.0', 'Typhoid Fever (Enteric Fever)', 'Step-ladder fever pattern, coated tongue, mild hepatomegaly.', 'Amoxicillin 500mg TDS x 7 days, maintain clean drinking water hygiene, review in 3 days.'),
            ('B54', 'Unspecified Malaria (Suspected/Screening)', 'Chills, intermittent pyrexia, profuse sweating.', 'Rapid Malaria antigen strip test ordered, Paracetamol 650mg, monitor temperature.'),
            ('M54.5', 'Mechanical Low Back Pain / Lumbar Strain', 'Paravertebral muscular tenderness, straight leg raise negative bilaterally.', 'Paracetamol + Ibuprofen BD x 5 days, posture correction, lumbar core exercises.'),
        ]

        consultations_to_create = []
        for idx, v in enumerate(consult_visits):
            pt = v.patient
            # Pick diagnostic profile matching chief complaint or demographics
            if 'ANC' in v.chief_complaint or pt.gender == 'FEMALE' and 'PREGNANT' in pt.vulnerability_information.upper():
                d_code, d_name, d_assess, d_plan = clinical_catalog[10] # Anemia complicating pregnancy
            elif 'Dengue' in v.chief_complaint:
                d_code, d_name, d_assess, d_plan = clinical_catalog[3] # Dengue
            elif 'FEVER' in v.chief_complaint.upper():
                d_code, d_name, d_assess, d_plan = clinical_catalog[8] # Viral Pyrexia
            elif 'DIABETES' in v.chief_complaint.upper() or 'fatigue' in v.chief_complaint.lower():
                d_code, d_name, d_assess, d_plan = clinical_catalog[2] # Diabetes
            elif 'CHRONIC' in v.chief_complaint.upper() or 'hypertension' in v.chief_complaint.lower():
                d_code, d_name, d_assess, d_plan = clinical_catalog[1] # Hypertension
            else:
                d_code, d_name, d_assess, d_plan = clinical_catalog[idx % len(clinical_catalog)]

            doc_usr = doc_by_fac[v.facility_id]
            fu_days = rng.choice([3, 7, 14, 28])
            fu_date = v.opd_date + datetime.timedelta(days=fu_days)

            consultations_to_create.append(Consultation(
                visit=v, patient=pt, doctor=doc_usr, facility=v.facility,
                chief_complaint=v.chief_complaint,
                clinical_history=f"Citizen {pt.name} ({pt.age}/{pt.gender}) registered at {v.facility.facility_name}. Prior vulnerability: {pt.vulnerability_information}.",
                clinical_assessment=d_assess,
                diagnosis_code=d_code, diagnosis_name=d_name,
                treatment_plan=d_plan,
                follow_up_date=fu_date,
                clinical_notes=f"Consultation completed by {doc_usr.full_name}. Patient counselled regarding medication adherence and lifestyle modification."
            ))

        created_consultations = Consultation.objects.bulk_create(consultations_to_create)

        # =====================================================================
        # 11. PRESCRIPTIONS & PRESCRIPTION ITEMS (750+ Prescriptions, 1800+ Items)
        # =====================================================================
        # =====================================================================
        # 11. PRESCRIPTIONS & PRESCRIPTION ITEMS (500–1200 Prescriptions, 1500–3000 Items)
        # =====================================================================
        prescriptions_to_create = []
        # Target: 500-1200 prescriptions. Select ~70% of consultations (~850 prescriptions)
        consultations_with_rx = [
            c for c in created_consultations
            if c.visit.status in ['WAITING_FOR_PHARMACY', 'IN_PHARMACY'] or rng.random() < 0.68
        ]
        for c in consultations_with_rx:
            v = c.visit
            st = 'DISPENSED' if v.status == 'COMPLETED' else (
                'ACTIVE' if v.status in ['WAITING_FOR_PHARMACY', 'IN_PHARMACY'] else 'ACTIVE'
            )
            prescriptions_to_create.append(Prescription(
                consultation=c, patient=c.patient, doctor=c.doctor, facility=c.facility,
                status=st, notes=f"Prescription issued for {c.diagnosis_name}."
            ))

        created_prescriptions = Prescription.objects.bulk_create(prescriptions_to_create)

        prescription_items_to_create = []
        for pr in created_prescriptions:
            v_status = pr.consultation.visit.status
            diag = pr.consultation.diagnosis_code

            # Select 1 to 4 relevant medicines
            items_meds = []
            if diag == 'E11.9': # Diabetes
                items_meds = [medicines[0], medicines[1]] # Metformin, Glimepiride
            elif diag == 'I10': # Hypertension
                items_meds = [medicines[2], medicines[3]] # Amlodipine, Telmisartan
            elif diag in ['J06.9', 'R50.9', 'A90']: # Fever / Respiratory
                items_meds = [medicines[6], medicines[14]] # Paracetamol, Cetirizine
                if rng.random() < 0.4:
                    items_meds.append(medicines[10]) # Amoxicillin
            elif diag == 'O99.0': # Maternal Anemia
                items_meds = [medicines[18], medicines[19]] # IFA, Calcium
            elif diag == 'A09': # Gastroenteritis
                items_meds = [medicines[17], medicines[25]] # ORS, Metronidazole
            elif diag == 'K29.7': # Gastritis
                items_meds = [medicines[15]] # Pantoprazole
            else:
                items_meds = rng.sample(medicines, k=rng.randint(1, 3))

            for m in items_meds:
                dur = rng.choice([3, 5, 7, 14, 30])
                qty = dur * rng.choice([1, 2, 3])
                is_dispensed = v_status == 'COMPLETED' or (v_status == 'IN_PHARMACY' and rng.random() < 0.6)
                disp_qty = qty if is_dispensed else 0
                item_st = 'DISPENSED' if is_dispensed else 'PENDING'

                prescription_items_to_create.append(PrescriptionItem(
                    prescription=pr, medicine=m, medicine_name=f"{m.generic_name} ({m.strength})",
                    dosage='1-0-1 After Food' if 'Tablet' in m.dosage_form else '1 TDS SOS',
                    frequency='Twice Daily' if 'Tablet' in m.dosage_form else 'As Directed',
                    duration_days=dur, quantity=qty, dispensed_quantity=disp_qty,
                    status=item_st
                ))

        PrescriptionItem.objects.bulk_create(prescription_items_to_create)

        # =====================================================================
        # 12. LAB WORKFLOW: ORDERS, SAMPLES & RESULTS (500–1000 Orders, 300–800 Samples, 300–800 Results)
        # =====================================================================
        lab_orders_to_create = []
        consultations_with_labs = [
            c for c in created_consultations
            if 'LAB' in c.visit.status or ('Dengue' in c.diagnosis_name and rng.random() < 0.5) or ('Diabetes' in c.diagnosis_name and rng.random() < 0.4) or rng.random() < 0.28
        ]

        for c in consultations_with_labs:
            diag = c.diagnosis_code
            if 'A90' in diag:
                tests = [lab_tests[5], lab_tests[3]] # Dengue NS1, Hemoglobin
            elif 'E11' in diag:
                tests = [lab_tests[0], lab_tests[1]] # HbA1c, FBG
            elif 'I10' in diag:
                tests = [lab_tests[4], lab_tests[7]] # Lipid, Urine Protein
            elif 'O99' in diag:
                tests = [lab_tests[3], lab_tests[12]] # Hb, UPT
            elif 'A09' in diag:
                tests = [lab_tests[8], lab_tests[2]] # Urine Sugar, RBG
            else:
                tests = [rng.choice(lab_tests)]

            v_st = c.visit.status
            if v_st == 'LAB_PENDING':
                order_status = 'ORDERED'
            elif v_st == 'LAB_IN_PROGRESS':
                order_status = 'SAMPLE_COLLECTED'
            elif v_st in ['LAB_COMPLETED', 'WAITING_FOR_PHARMACY', 'IN_PHARMACY', 'COMPLETED']:
                order_status = 'VERIFIED'
            else:
                order_status = rng.choice(['ORDERED', 'SAMPLE_COLLECTED', 'VERIFIED'])

            for t_item in tests:
                lab_orders_to_create.append(LabOrder(
                    visit=c.visit, consultation=c, patient=c.patient,
                    doctor=c.doctor, facility=c.facility, test_master=t_item,
                    status=order_status
                ))

        created_lab_orders = LabOrder.objects.bulk_create(lab_orders_to_create)

        lab_samples_to_create = []
        lab_results_to_create = []
        s_code_seq = 1

        for lo in created_lab_orders:
            # Target: 300-800 LabSamples
            if lo.status in ['SAMPLE_COLLECTED', 'RESULT_ENTRY', 'VERIFIED']:
                if lo.status != 'VERIFIED' or rng.random() < 0.82:
                    stype = 'Urine' if 'URINE' in lo.test_master.code or 'PREG' in lo.test_master.code else (
                        'Sputum' if 'TB' in lo.test_master.code else 'Blood'
                    )
                    lab_samples_to_create.append(LabSample(
                        lab_order=lo, sample_type=stype,
                        sample_code=f"SMP-{lo.facility.facility_code}-{s_code_seq:05d}",
                        collected_by=lab_by_fac[lo.facility_id]
                    ))
                    s_code_seq += 1

            # Target: 300-800 LabResults
            if lo.status == 'VERIFIED' and rng.random() < 0.78:
                # Populate realistic result value, interpretation flag
                tcode = lo.test_master.code
                if tcode == 'L-HBA1C':
                    val = round(rng.uniform(5.2, 9.8), 1)
                    res_val = f"{val} %"
                    flag = 'NORMAL' if val < 5.7 else ('HIGH' if val < 8.0 else 'CRITICAL')
                elif tcode == 'L-FBG':
                    val = rng.randint(75, 210)
                    res_val = f"{val} mg/dL"
                    flag = 'NORMAL' if val <= 100 else ('HIGH' if val <= 160 else 'CRITICAL')
                elif tcode == 'L-RBG':
                    val = rng.randint(80, 260)
                    res_val = f"{val} mg/dL"
                    flag = 'NORMAL' if val <= 140 else ('HIGH' if val <= 200 else 'CRITICAL')
                elif tcode == 'L-HB':
                    val = round(rng.uniform(7.8, 14.8), 1)
                    res_val = f"{val} g/dL"
                    flag = 'NORMAL' if val >= 12.0 else ('LOW' if val >= 9.0 else 'CRITICAL')
                elif tcode == 'L-LIPID':
                    val = rng.randint(140, 270)
                    res_val = f"Total Chol: {val} mg/dL"
                    flag = 'NORMAL' if val < 200 else 'HIGH'
                elif tcode == 'L-DENGUE':
                    is_pos = rng.random() < 0.35
                    res_val = 'Reactive / POSITIVE' if is_pos else 'Non-Reactive / NEGATIVE'
                    flag = 'CRITICAL' if is_pos else 'NORMAL'
                elif tcode == 'L-MALARIA':
                    is_pos = rng.random() < 0.10
                    res_val = 'Pf Positive' if is_pos else 'Negative'
                    flag = 'HIGH' if is_pos else 'NORMAL'
                elif tcode == 'L-URINE-PROT':
                    is_pos = rng.random() < 0.25
                    res_val = 'Trace / 1+' if is_pos else 'Nil / Negative'
                    flag = 'HIGH' if is_pos else 'NORMAL'
                elif tcode == 'L-PREG-RAPID':
                    is_pos = rng.random() < 0.40
                    res_val = 'Positive (Two Bands)' if is_pos else 'Negative (One Band)'
                    flag = 'NORMAL'
                else:
                    res_val = 'Within Normal Limits'
                    flag = 'NORMAL'

                lab_results_to_create.append(LabResult(
                    lab_order=lo, result_value=res_val, unit=lo.test_master.unit,
                    reference_range=lo.test_master.reference_range,
                    interpretation_flag=flag,
                    verified_by=lab_by_fac[lo.facility_id],
                    notes=f"Test executed and released by {lab_by_fac[lo.facility_id].full_name}."
                ))

        LabSample.objects.bulk_create(lab_samples_to_create)
        LabResult.objects.bulk_create(lab_results_to_create)

        # =====================================================================
        # 13. INVENTORY TRANSACTIONS (750+ Records)
        # =====================================================================
        inv_txns = []
        txn_types = ['PURCHASE_RECEIVED', 'DISPENSED', 'ADJUSTMENT', 'EXPIRED', 'RETURNED', 'ISSUED']
        for t_idx in range(750):
            fac = facilities_list[t_idx % 4]
            med = medicines[t_idx % len(medicines)]
            fac_batches = [b for b in created_batches if b.facility_id == fac.id and b.medicine_id == med.id]
            batch_choice = fac_batches[0] if fac_batches else created_batches[0]
            ttype = txn_types[t_idx % len(txn_types)]
            qty = rng.randint(10, 150)
            u_choice = pharm_by_fac[fac.id]

            inv_txns.append(InventoryTransaction(
                facility=fac, medicine=med, batch=batch_choice,
                transaction_type=ttype, quantity=qty,
                reference_id=f"TXN-{fac.facility_code[:3]}-{t_idx+1:04d}",
                created_by=u_choice,
                notes=f"Stock movement logged by {u_choice.full_name} under {ttype}."
            ))

        InventoryTransaction.objects.bulk_create(inv_txns)

        # =====================================================================
        # 14. REFERRALS, RESPONSES & FOLLOW-UPS (160 Referrals, 100 Responses, 180 Follow-ups)
        # =====================================================================
        referrals_to_create = []
        referral_plans = [
            (vc_a4_1, rc_a4, 'Specialist review for uncontrolled fever and rapid diagnostic evaluation', 'Primary care triage at village satellite; referral to Rural Primary Clinic A4.'),
            (rc_a4, nc_a1, 'Secondary care evaluation for high risk pregnancy and gestational hypertension', 'ANC mother 28 weeks with BP 148/96; referral to Sub-District Hospital.'),
            (nc_a1, hosp_a, 'Tertiary Cardiology consultation and 2D-Echocardiogram', 'Hypertensive Heart Disease with ischemic ECG changes; specialist review at District Hospital.'),
            (rc_a4, hosp_a, 'Emergency ICU Referral for hypertensive crisis / chest pain', 'Direct emergency specialist referral with ambulance transfer.')
        ]

        ref_statuses = ['CREATED', 'ACCEPTED', 'IN_TRANSIT', 'REACHED', 'UNDER_TREATMENT', 'FOLLOW_UP_PENDING', 'COMPLETED', 'CLOSED']
        urgencies = ['ROUTINE', 'URGENT', 'EMERGENCY']

        for r_idx in range(160):
            src_fac, dst_fac, reason_txt, summ_txt = referral_plans[r_idx % len(referral_plans)]
            pt = created_patients[r_idx * 3 % len(created_patients)]
            st = ref_statuses[r_idx % len(ref_statuses)]
            urg = urgencies[r_idx % len(urgencies)]

            referrals_to_create.append(Referral(
                referral_id=f"REF-{today.strftime('%Y%m')}-{r_idx+1:04d}",
                patient=pt, source_facility=src_fac, destination_facility=dst_fac,
                referring_doctor=doc_by_fac[src_fac.id],
                reason=reason_txt, clinical_summary=summ_txt,
                required_service='Specialist Evaluation & Investigation',
                urgency=urg, status=st
            ))

        created_referrals = Referral.objects.bulk_create(referrals_to_create)

        referral_responses_to_create = []
        for r in created_referrals:
            if r.status in ['UNDER_TREATMENT', 'FOLLOW_UP_PENDING', 'COMPLETED', 'CLOSED']:
                referral_responses_to_create.append(ReferralResponse(
                    referral=r, hospital_doctor=doc_by_fac[r.destination_facility_id],
                    specialist_findings='Specialist examination conducted. Diagnostic parameters stabilized.',
                    treatment_summary='Adjusted medication regimen. Supervised observation conducted.',
                    return_advice=f'Patient stable for step-down care. Return to {r.source_facility.facility_name} for primary follow-up in 14 days.'
                ))

        ReferralResponse.objects.bulk_create(referral_responses_to_create)

        # FollowUps (180 records)
        followups_to_create = []
        fu_statuses = ['PENDING', 'DUE_TODAY', 'OVERDUE', 'COMPLETED']
        for f_idx in range(180):
            pt = created_patients[f_idx * 2 % len(created_patients)]
            fac = pt.registered_at_facility or hosp_a
            st = fu_statuses[f_idx % len(fu_statuses)]
            if st == 'COMPLETED':
                due_d = today - datetime.timedelta(days=rng.randint(3, 30))
            elif st == 'OVERDUE':
                due_d = today - datetime.timedelta(days=rng.randint(1, 14))
            elif st == 'DUE_TODAY':
                due_d = today
            else: # PENDING
                due_d = today + datetime.timedelta(days=rng.randint(2, 28))

            cat = rng.choice(['NCD', 'MATERNAL_ANC', 'REFERRAL', 'GENERAL'])
            ref_link = created_referrals[f_idx % len(created_referrals)] if cat == 'REFERRAL' else None

            followups_to_create.append(FollowUp(
                patient=pt, referral=ref_link, facility=fac, category=cat,
                due_date=due_d, status=st,
                notes=f"Scheduled {cat} clinical follow-up for {pt.name} at {fac.facility_name}."
            ))

        FollowUp.objects.bulk_create(followups_to_create)

        # =====================================================================
        # 15. NCD RECORDS (200 Records)
        # =====================================================================
        ncd_to_create = []
        adult_patients = [p for p in created_patients if p.age >= 35]
        for idx in range(200):
            pt = adult_patients[idx % len(adult_patients)]
            fac = pt.registered_at_facility or rc_a4
            has_htn = idx % 2 == 0 or idx % 3 == 0
            has_dm = idx % 2 != 0 or idx % 5 == 0
            risk = 'HIGH' if has_htn and has_dm else ('MODERATE' if has_htn else 'LOW')
            control = 'CONTROLLED' if idx % 3 != 0 else 'UNCONTROLLED'
            bp_val = f"{rng.randint(142, 168)}/{rng.randint(92, 104)}" if control == 'UNCONTROLLED' else f"{rng.randint(118, 134)}/{rng.randint(76, 86)}"
            glu_val = rng.randint(165, 260) if control == 'UNCONTROLLED' else rng.randint(95, 135)

            ncd_to_create.append(NCDRecord(
                patient=pt, facility=fac,
                hypertension_screened=True, hypertension_diagnosed=has_htn,
                diabetes_screened=True, diabetes_diagnosed=has_dm,
                risk_level=risk, treatment_status='UNDER_TREATMENT', control_status=control,
                last_bp=bp_val, last_glucose=glu_val,
                next_followup_due=today + datetime.timedelta(days=rng.randint(7, 45))
            ))

        NCDRecord.objects.bulk_create(ncd_to_create)

        # =====================================================================
        # 16. MATERNAL & CHILD HEALTH (65 Maternal, 130 Child Records)
        # =====================================================================
        eligible_maternal = [p for p in created_patients if p.gender == 'FEMALE' and 18 <= p.age <= 40]
        maternal_to_create = []
        for idx in range(65):
            pt = eligible_maternal[idx % len(eligible_maternal)]
            lmp_days_ago = rng.randint(45, 240)
            lmp = today - datetime.timedelta(days=lmp_days_ago)
            edd = lmp + datetime.timedelta(days=280)
            is_high_risk = idx % 4 == 0

            maternal_to_create.append(MaternalRecord(
                patient=pt, anc_number=f"ANC-{today.strftime('%Y')}-{idx+1:03d}",
                lmp_date=lmp, edd_date=edd, high_risk_flag=is_high_risk,
                high_risk_reason='Gestational Anemia & High BP' if is_high_risk else '',
                anc_checkups_count=min(4, max(1, lmp_days_ago // 60)),
                tt_vaccine_given=True, ifa_tablets_issued=True, status='ACTIVE'
            ))

        created_maternal = MaternalRecord.objects.bulk_create(maternal_to_create)

        eligible_children = [p for p in created_patients if p.age <= 5]
        child_to_create = []
        growth_statuses = ['GREEN_ZONE', 'YELLOW_ZONE', 'RED_ZONE']
        sam_statuses = ['NORMAL', 'MAM', 'SAM']

        for idx in range(130):
            pt = eligible_children[idx % len(eligible_children)]
            m_link = created_maternal[idx % len(created_maternal)]
            g_st = growth_statuses[idx % len(growth_statuses)]
            s_st = 'SAM' if g_st == 'RED_ZONE' else ('MAM' if g_st == 'YELLOW_ZONE' else 'NORMAL')

            child_to_create.append(ChildRecord(
                patient=pt, maternal_record=m_link,
                birth_weight_kg=round(rng.uniform(2.10, 3.60), 2),
                immunization_status='UP_TO_DATE' if idx % 5 != 0 else 'PARTIAL',
                sam_mam_status=s_st, growth_chart_status=g_st
            ))

        ChildRecord.objects.bulk_create(child_to_create)

        # =====================================================================
        # 17. PUBLIC HEALTH DISEASE SURVEILLANCE (900 Cases, 90 Days)
        # =====================================================================
        # Strategic epidemiological distribution to satisfy Public Health Intelligence:
        # - Acute Respiratory Infection: surge wave over the past 3 weeks (rising trend, high forecast risk)
        # - Dengue Fever: seasonal curve peaking 3-6 weeks ago, receding recently
        # - Acute Gastroenteritis: localized outbreak in Varthur Rural Ward and Indiranagar Ward
        # - Acute Pyrexia / Viral Fever: steady widespread baseline
        # - Typhoid Fever: steady moderate cases
        # - Malaria: sporadic low cases
        # Also, re-using patients across multiple cases ensures both NEW (~70%) and FOLLOW_UP (~30%) patient types!

        cases_to_create = []
        severities = ['MILD', 'MODERATE', 'SEVERE']

        # Epidemiological schedule over 90 days:
        # Day 0 is today, Day 89 is 89 days ago
        for days_ago in range(90):
            c_date = today - datetime.timedelta(days=days_ago)

            # 1. Acute Respiratory Infection (surge in recent 21 days: day 0 to 21)
            if days_ago <= 14:
                ari_count = rng.randint(4, 7) # Peak surge
            elif days_ago <= 28:
                ari_count = rng.randint(2, 5) # Rising wave
            else:
                ari_count = rng.randint(0, 2) # Low baseline

            for _ in range(ari_count):
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                fac = pt.registered_at_facility or hosp_a
                ward = pt.ward or ward12
                sev = rng.choices(severities, weights=[0.60, 0.30, 0.10])[0]
                cases_to_create.append(DiseaseCase(
                    disease_name='Acute Respiratory Infection', patient=pt, facility=fac,
                    ward=ward, report_date=c_date, severity=sev, status='CONFIRMED',
                    notes=f"ARI case reported on {c_date} at {fac.facility_name}."
                ))

            # 2. Dengue Fever (seasonal wave peaking 21 to 50 days ago)
            if 21 <= days_ago <= 50:
                dengue_count = rng.randint(3, 6) # Seasonal peak
            elif days_ago < 21:
                dengue_count = rng.randint(1, 3) # Post-peak decline
            else:
                dengue_count = rng.randint(0, 1) # Pre-season baseline

            for _ in range(dengue_count):
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                fac = pt.registered_at_facility or nc_a1
                ward = pt.ward or ward14
                sev = rng.choices(severities, weights=[0.55, 0.35, 0.10])[0]
                cases_to_create.append(DiseaseCase(
                    disease_name='Dengue Fever', patient=pt, facility=fac,
                    ward=ward, report_date=c_date, severity=sev, status='CONFIRMED',
                    notes=f"Dengue case logged at {fac.facility_name} for Ward {ward.ward_number}."
                ))

            # 3. Acute Gastroenteritis (clustered in Varthur Rural Ward and Indiranagar Ward)
            ge_count = rng.randint(1, 3)
            for _ in range(ge_count):
                # Cluster specifically in rural ward or ward12
                target_ward = ward_rural if rng.random() < 0.65 else ward12
                target_fac = rc_a4 if target_ward == ward_rural else nc_a1
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                sev = rng.choices(severities, weights=[0.65, 0.28, 0.07])[0]
                cases_to_create.append(DiseaseCase(
                    disease_name='Acute Gastroenteritis', patient=pt, facility=target_fac,
                    ward=target_ward, report_date=c_date, severity=sev, status='CONFIRMED',
                    notes=f"Gastroenteritis water-borne case logged at {target_fac.facility_name}."
                ))

            # 4. Acute Pyrexia / Suspected Viral Fever (steady baseline across all facilities)
            fever_count = rng.randint(1, 3)
            for _ in range(fever_count):
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                fac = facilities_list[rng.randint(0, 3)]
                ward = all_wards[rng.randint(0, len(all_wards) - 1)]
                sev = rng.choices(severities, weights=[0.70, 0.25, 0.05])[0]
                cases_to_create.append(DiseaseCase(
                    disease_name='Acute Pyrexia / Suspected Viral Fever', patient=pt, facility=fac,
                    ward=ward, report_date=c_date, severity=sev, status='CONFIRMED',
                    notes=f"Undifferentiated febrile case recorded at {fac.facility_name}."
                ))

            # 5. Typhoid Fever (steady, moderate)
            if days_ago % 2 == 0:
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                fac = facilities_list[rng.randint(0, 3)]
                ward = all_wards[rng.randint(0, len(all_wards) - 1)]
                cases_to_create.append(DiseaseCase(
                    disease_name='Typhoid Fever', patient=pt, facility=fac,
                    ward=ward, report_date=c_date, severity='MODERATE', status='CONFIRMED',
                    notes=f"Enteric fever surveillance alert at {fac.facility_name}."
                ))

            # 6. Malaria (sporadic low numbers)
            if days_ago % 6 == 0:
                pt = created_patients[rng.randint(0, len(created_patients) - 1)]
                cases_to_create.append(DiseaseCase(
                    disease_name='Malaria', patient=pt, facility=rc_a4,
                    ward=ward_rural, report_date=c_date, severity='MILD', status='CONFIRMED',
                    notes=f"Malaria surveillance screen at Varthur Rural Clinic."
                ))

        # Re-use ~200 patients across multiple dates so that FOLLOW_UP patient type is populated naturally
        repeat_patients = created_patients[:60]
        for rp in repeat_patients:
            for rep_offset in [10, 25, 45]:
                r_date = today - datetime.timedelta(days=rep_offset)
                cases_to_create.append(DiseaseCase(
                    disease_name='Acute Respiratory Infection', patient=rp,
                    facility=rp.registered_at_facility or hosp_a, ward=rp.ward or ward12,
                    report_date=r_date, severity='MILD', status='CONFIRMED',
                    notes=f"Follow-up surveillance case logged for citizen {rp.name} on {r_date}."
                ))

        DiseaseCase.objects.bulk_create(cases_to_create)

        # =====================================================================
        # 18. TELEMEDICINE (80 Teleconsultations)
        # =====================================================================
        teleconsults_to_create = []
        tc_statuses = ['REQUESTED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        for tc_idx in range(80):
            pt = created_patients[tc_idx * 4 % len(created_patients)]
            clinic_fac = [rc_a4, nc_a1, vc_a4_1][tc_idx % 3]
            st = tc_statuses[tc_idx % len(tc_statuses)]
            sched_time = now - datetime.timedelta(days=rng.randint(1, 60), hours=rng.randint(1, 6)) if st == 'COMPLETED' else now + datetime.timedelta(days=rng.randint(1, 14), hours=rng.randint(1, 4))

            teleconsults_to_create.append(Teleconsultation(
                teleconsult_id=f"TELE-{clinic_fac.facility_code[:3]}-{tc_idx+1:03d}",
                patient=pt, clinic_facility=clinic_fac, hub_facility=hosp_a,
                requesting_doctor=doc_by_fac[clinic_fac.id], specialist_doctor=u_dh_doc,
                specialty_required='General Medicine / Cardiology Specialist Hub',
                scheduled_time=sched_time, status=st,
                clinical_notes='Teleconsultation request for secondary opinion on cardiac ECG & chronic medication.',
                specialist_advice='Specialist review conducted. Adjust antihypertensive dosing and maintain local clinic follow-up.'
            ))

        Teleconsultation.objects.bulk_create(teleconsults_to_create)

        # =====================================================================
        # 19. OUTREACH & WELLNESS (60 Outreach, 60 Wellness)
        # =====================================================================
        outreach_to_create = []
        wellness_to_create = []
        for o_idx in range(60):
            fac = facilities_list[o_idx % 4]
            w = fac.ward or ward_rural
            act_date = today - datetime.timedelta(days=o_idx + 1)
            outreach_to_create.append(OutreachActivity(
                facility=fac, ward=w,
                activity_type='Slum Household NCD, ANC & Febrile Surveillance Survey',
                activity_date=act_date, households_covered=rng.randint(40, 85),
                persons_screened=rng.randint(100, 220), vulnerable_identified=rng.randint(12, 35),
                conducted_by='ASHA Workers & Staff Nurse Field Team',
                summary_notes=f"Community outreach camp executed at {w.name}."
            ))

            wellness_to_create.append(WellnessSession(
                facility=fac, session_type='AYUSH Yoga, Pranayama & Lifestyle Counseling',
                instructor_name='Sri Gururaj (Certified AYUSH Yoga Practitioner)',
                session_date=act_date, session_time='07:00 AM - 08:30 AM',
                venue=f"{fac.facility_name} Community Hall / Open Courtyard",
                participants_count=rng.randint(18, 45), incentive_amount_rs=350.00,
                notes=f"Community wellness session conducted for citizens of {fac.facility_name}."
            ))

        OutreachActivity.objects.bulk_create(outreach_to_create)
        WellnessSession.objects.bulk_create(wellness_to_create)

        # =====================================================================
        # 20. ARS MEETINGS, QUALITY & BIOMEDICAL WASTE
        # =====================================================================
        ars_meetings_to_create = []
        ars_actions_to_create = []
        for m_idx in range(24):
            fac = facilities_list[m_idx % 4]
            m_date = today - datetime.timedelta(days=m_idx * 3 + 2)
            m = ARSMeeting.objects.create(
                facility=fac, meeting_date=m_date,
                chairperson_name=f"Ward {fac.ward.ward_number if fac.ward else 12} Corporator / Public Health Rep",
                attendees_count=rng.randint(6, 12),
                agenda='Untied grant allocation for diagnostic reagents, clinic drinking water purifier & patient waiting area benches',
                proceedings_summary='Committee unanimously approved untied maintenance expenditure and verified clinic stock levels.',
                untied_funds_spent_rs=round(rng.uniform(4500.00, 12500.00), 2), signed_by_chairman=True
            )
            ars_meetings_to_create.append(m)

            for act_i in range(4):
                ARSActionItem.objects.create(
                    meeting=m, task_description=f"Procure consumable pack and test reagents for {fac.facility_name}",
                    responsible_person='Facility Admin / Medical Officer',
                    due_date=m_date + datetime.timedelta(days=10),
                    status=rng.choice(['COMPLETED', 'IN_PROGRESS', 'PENDING'])
                )

        for fac in facilities_list:
            ARSMember.objects.create(facility=fac, name='Sri Ward Corporator', designation='Chairman (Ward Committee)')
            ARSMember.objects.create(facility=fac, name='Medical Officer in Charge', designation='Member Secretary')
            ARSMember.objects.create(facility=fac, name='Senior Staff Nurse', designation='Clinical Member')
            ARSMember.objects.create(facility=fac, name='Lead ASHA Facilitator', designation='Community Health Representative')

        # Quality Checklists (60) & Biomedical Waste Logs (120)
        quality_to_create = []
        for q_idx in range(60):
            fac = facilities_list[q_idx % 4]
            quality_to_create.append(QualityChecklist(
                facility=fac, cleanliness_score=rng.randint(88, 99),
                infection_control_passed=True, kayakalpa_audit_status='COMPLIANT',
                corrective_actions='Routine disinfection cycles verified and bio-waste bins color segregation audited.',
                inspected_by=u_dist
            ))
        QualityChecklist.objects.bulk_create(quality_to_create)

        waste_logs_to_create = []
        for w_idx in range(120):
            fac = facilities_list[w_idx % 4]
            waste_logs_to_create.append(BiomedicalWasteLog(
                facility=fac, yellow_bag_kg=round(rng.uniform(2.10, 5.80), 2),
                red_bag_kg=round(rng.uniform(1.40, 3.90), 2),
                white_translucent_sharp_kg=round(rng.uniform(0.30, 1.20), 2),
                blue_box_glass_kg=round(rng.uniform(0.80, 2.40), 2),
                disposal_agency='Authorized Karnataka State CBWTF Operator',
                handed_over_by=nurse_by_fac[fac.id]
            ))
        BiomedicalWasteLog.objects.bulk_create(waste_logs_to_create)

        # =====================================================================
        # 21. INFRASTRUCTURE & MAINTENANCE
        # =====================================================================
        # Maintenance tickets (50 tickets)
        ticket_cats = ['ELECTRICAL', 'PLUMBING', 'OXYGEN_SYSTEM', 'SOLAR_UPS', 'MEDICAL_EQUIPMENT', 'SANITY_CLEANING']
        ticket_statuses = ['LOGGED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']
        maint_tickets = []
        for t_idx in range(50):
            fac = facilities_list[t_idx % 4]
            maint_tickets.append(FacilityMaintenanceTicket(
                facility=fac, ticket_number=f"MAINT-{fac.facility_code[:3]}-{t_idx+1:03d}",
                category=ticket_cats[t_idx % len(ticket_cats)],
                equipment_or_area=f"Facility Wing {t_idx % 3 + 1} Equipment / Fixture",
                priority=rng.choice(['LOW', 'MEDIUM', 'HIGH']),
                description=f"Periodic preventive maintenance and inspection check at {fac.facility_name}.",
                reported_by=nurse_by_fac[fac.id].full_name,
                assigned_technician='BBMP Engineering & Medical Maintenance Cell',
                status=ticket_statuses[t_idx % len(ticket_statuses)]
            ))
        FacilityMaintenanceTicket.objects.bulk_create(maint_tickets)

        # Consumable Inventory & Oxygen & Beds for all 4 facilities
        consumable_items = [
            ('Floor Cleaning Solution (Lysol / Phenyl)', 'CLEANING_SANITATION', 'Litres', 150, 40),
            ('Hand Sanitizer (Alcohol Rub 70%)', 'INFECTION_CONTROL', 'Bottles (500ml)', 120, 30),
            ('Sodium Hypochlorite 5% (Disinfectant)', 'CLEANING_SANITATION', 'Litres', 60, 20),
            ('Biohazard Waste Bags (Yellow 50L)', 'INFECTION_CONTROL', 'Packs (100s)', 25, 10),
            ('Disposable Nitrile Gloves (M)', 'PERSONAL_PROTECTION', 'Boxes (100s)', 45, 15),
            ('Surgical Face Masks 3-Ply', 'PERSONAL_PROTECTION', 'Boxes (50s)', 60, 20),
        ]
        consumables_to_create = []
        for fac in facilities_list:
            for item, cat, uom, stock, thresh in consumable_items:
                consumables_to_create.append(FacilityConsumableInventory(
                    facility=fac, item_name=item, category=cat, unit_of_measure=uom,
                    current_stock=stock, min_threshold=thresh, reorder_status='ADEQUATE'
                ))
        FacilityConsumableInventory.objects.bulk_create(consumables_to_create)

        for f_idx, fac in enumerate(facilities_list):
            FacilityOxygenSupply.objects.create(
                facility=fac, oxygen_source='PIPELINE_LIQUID' if fac == hosp_a else ('CONCENTRATOR' if fac == nc_a1 else 'CYLINDER_MANIFOLD'),
                total_cylinders=80 if fac == hosp_a else (20 if fac == nc_a1 else 10),
                active_cylinders=65 if fac == hosp_a else (16 if fac == nc_a1 else 8),
                empty_cylinders=15 if fac == hosp_a else (4 if fac == nc_a1 else 2),
                current_pressure_psi=2200 if fac == hosp_a else 1850,
                fill_percentage=88, status='OPTIMAL', notes='Central oxygen manifold operational and tested.'
            )

            # Bed capacities
            FacilityBedCapacity.objects.create(facility=fac, bed_category='GENERAL_OBSERVATION', total_beds=100 if fac == hosp_a else 20, occupied_beds=65 if fac == hosp_a else 12, cleaning_in_progress=5, under_maintenance=2)
            FacilityBedCapacity.objects.create(facility=fac, bed_category='EMERGENCY_TRIAGE', total_beds=20 if fac == hosp_a else 5, occupied_beds=14 if fac == hosp_a else 3, cleaning_in_progress=2, under_maintenance=0)
            FacilityBedCapacity.objects.create(facility=fac, bed_category='OXYGEN_SUPPORTED', total_beds=50 if fac == hosp_a else 10, occupied_beds=32 if fac == hosp_a else 6, cleaning_in_progress=3, under_maintenance=1)

            # Bed allocation demo
            pt_bed = created_patients[f_idx * 10]
            FacilityBedAllocation.objects.create(
                facility=fac, bed_number=f"BED-{fac.facility_code[:3]}-01",
                bed_category='GENERAL_OBSERVATION', patient=pt_bed, patient_name=pt_bed.name,
                attending_doctor=doc_by_fac[fac.id].full_name, status='OCCUPIED'
            )

        # =====================================================================
        # 22. ALERTS (150 Alerts across Facilities)
        # =====================================================================
        alert_types = [
            ('LOW_STOCK', 'Low Medicine Stock Alert', 'Current stock is below reorder threshold.', 'MEDIUM'),
            ('NEAR_EXPIRY', 'Near Expiry Medicine Batch Alert', 'Batch expiry approaching within 45 days.', 'WARNING'),
            ('EXPIRED', 'Expired Stock Segregation Alert', 'Expired batch removed from dispensing inventory.', 'HIGH'),
            ('REFERRAL_OVERDUE', 'Referral Patient Overdue Follow-up', 'Referred specialist patient review pending.', 'MEDIUM'),
            ('FOLLOWUP_OVERDUE', 'High Risk NCD Follow-up Overdue', 'Hypertension/Diabetic routine visit overdue.', 'HIGH'),
            ('LAB_PENDING', 'Lab Result Verification Pending', 'Diagnostic sample collected awaiting doctor sign-off.', 'LOW'),
            ('DISEASE_THRESHOLD', 'Public Health Disease Anomaly Threshold', 'Elevated weekly incidence in local catchment ward.', 'CRITICAL'),
            ('INTELLIGENCE_TREND', 'Disease Trend Increase Signal', 'Statistically elevated case acceleration observed.', 'HIGH'),
            ('INTELLIGENCE_LOCALITY', 'High Locality Concentration Signal', 'High spatial density detected in slum catchment.', 'WARNING'),
            ('INTELLIGENCE_FORECAST', 'Surveillance Forecast Risk Signal', 'Holt-Winters projected case count exceeds baseline threshold.', 'CRITICAL'),
        ]
        alert_statuses = ['NEW', 'ACKNOWLEDGED', 'RESOLVED']

        alerts_to_create = []
        for a_idx in range(150):
            fac = facilities_list[a_idx % 4]
            atype, atitle, adesc, asev = alert_types[a_idx % len(alert_types)]
            astatus = alert_statuses[a_idx % len(alert_statuses)]
            pt_alert = created_patients[a_idx % len(created_patients)] if a_idx % 3 == 0 else None

            alerts_to_create.append(Alert(
                alert_type=atype, severity=asev, facility=fac, district=dist_central,
                patient=pt_alert, title=f"{atitle} at {fac.facility_name}",
                description=adesc, status=astatus,
                fingerprint=f"alert-fp-{fac.id}-{atype}-{a_idx}",
                metadata={'source': 'seed_demo', 'generated_index': a_idx}
            ))

        Alert.objects.bulk_create(alerts_to_create)

        # =====================================================================
        # 23. COMPLIANCE & INTEGRATIONS
        # =====================================================================
        ComplianceItem.objects.create(
            requirement_id='REQ-OFF-001', requirement_text='Provide comprehensive primary health care in urban & rural areas',
            source_document='ULB ROK Booklet', classification='OFFICIAL BOOKLET REQUIREMENT',
            application_module='Clinical / Consultation', status='FULLY_COVERED', explanation='Complete 12 service package delivery supported across all 4 facilities.'
        )
        ComplianceItem.objects.create(
            requirement_id='REQ-KM-003', requirement_text='First-Expiry First-Out (FEFO) batch management and stock alerts',
            source_document='K Mati Proposal', classification='K MATI PROPOSAL',
            application_module='Pharmacy / Inventory', status='FULLY_COVERED', explanation='Automated batch expiry sorting and low stock alerts implemented.'
        )
        IntegrationConfiguration.objects.create(system_name='ABDM', display_name='Ayushman Bharat Digital Mission (ABDM)', status='MOCK', sync_status='SUCCESS', notes='Local ABDM mock connector active.')
        IntegrationConfiguration.objects.create(system_name='ABHA', display_name='ABHA Health ID Gateway', status='MOCK', sync_status='SUCCESS', notes='Local ABHA verification engine.')
        IntegrationConfiguration.objects.create(system_name='HMIS', display_name='Karnataka Health Management Information System', status='MOCK', sync_status='SUCCESS', notes='Periodic HMIS export template ready.')
        IntegrationConfiguration.objects.create(system_name='E_AUSHADA', display_name='KSMSCL E-Aushada Drug Procurement Engine', status='MOCK', sync_status='SUCCESS', notes='Direct indent sync mock interface.')

        # =====================================================================
        # 24. AUDIT LOGS (350 Audit Records)
        # =====================================================================
        audit_actions = ['LOGIN', 'PATIENT_CREATE', 'CONSULTATION_SAVE', 'DISPENSE_MEDICINE', 'LAB_RESULT_VERIFY', 'REFERRAL_RAISED', 'STOCK_RECEIVE', 'SYSTEM_SEED_DEMO']
        all_staff = [u_dist, u_dh_doc, u_sdh_doc, u_vh1_doc, u_vh2_doc, u_dh_nurse, u_sdh_nurse, u_vh1_nurse, u_dh_pharm, u_vh1_pharm, u_dh_lab, u_vh1_lab]

        audit_logs_to_create = []
        for au_idx in range(350):
            u_acting = all_staff[au_idx % len(all_staff)]
            fac = getattr(u_acting, 'assigned_facility', None) or hosp_a
            act = audit_actions[au_idx % len(audit_actions)]
            audit_logs_to_create.append(AuditLog(
                user=u_acting, username_snapshot=u_acting.username,
                action=act, facility=fac,
                details=f"Demo audit record: {act} performed at {fac.facility_name}.",
                ip_address=f"192.168.1.{rng.randint(10, 199)}"
            ))

        AuditLog.objects.bulk_create(audit_logs_to_create)

        # =====================================================================
        # 25. COMPREHENSIVE SUMMARY OUTPUT
        # =====================================================================
        # Count actual generated records from database
        total_facilities = Facility.objects.count()
        total_users = User.objects.count()
        total_patients = Patient.objects.count()
        total_visits = Visit.objects.count()
        total_triage = TriageVitals.objects.count()
        total_consultations = Consultation.objects.count()
        total_prescriptions = Prescription.objects.count()
        total_prescription_items = PrescriptionItem.objects.count()
        total_lab_orders = LabOrder.objects.count()
        total_lab_samples = LabSample.objects.count()
        total_lab_results = LabResult.objects.count()
        total_medicines = MedicineMaster.objects.count()
        total_medicine_batches = MedicineBatch.objects.count()
        total_inv_txns = InventoryTransaction.objects.count()
        total_purchase_orders = PurchaseOrder.objects.count()
        total_referrals = Referral.objects.count()
        total_follow_ups = FollowUp.objects.count()
        total_ncd = NCDRecord.objects.count()
        total_maternal = MaternalRecord.objects.count()
        total_child = ChildRecord.objects.count()
        total_disease_cases = DiseaseCase.objects.count()
        total_teleconsults = Teleconsultation.objects.count()
        total_outreach = OutreachActivity.objects.count()
        total_wellness = WellnessSession.objects.count()
        total_ars_meetings = ARSMeeting.objects.count()
        total_quality_records = QualityChecklist.objects.count()
        total_bmw_logs = BiomedicalWasteLog.objects.count()
        total_alerts = Alert.objects.count()
        total_audit_logs = AuditLog.objects.count()

        # Today's activity breakdown
        today_visits_qs = Visit.objects.filter(opd_date=today)
        t_visits_count = today_visits_qs.count()
        t_waiting_triage = today_visits_qs.filter(status='WAITING_FOR_TRIAGE').count()
        t_waiting_doc = today_visits_qs.filter(status__in=['WAITING_FOR_DOCTOR', 'TRIAGED']).count()
        t_in_consult = today_visits_qs.filter(status='IN_CONSULTATION').count()
        t_lab_pending = today_visits_qs.filter(status='LAB_PENDING').count()
        t_lab_in_progress = today_visits_qs.filter(status='LAB_IN_PROGRESS').count()
        t_waiting_pharm = today_visits_qs.filter(status='WAITING_FOR_PHARMACY').count()
        t_completed = today_visits_qs.filter(status='COMPLETED').count()
        t_emergency_high = today_visits_qs.filter(priority__in=['EMERGENCY', 'HIGH']).count()

        self.stdout.write(self.style.SUCCESS("\nDEMO DATA SEED COMPLETED\n"))
        self.stdout.write(f"Facilities: {total_facilities}")
        self.stdout.write(f"Users: {total_users}")
        self.stdout.write(f"Patients: {total_patients}")
        self.stdout.write(f"Visits: {total_visits}")
        self.stdout.write(f"Triage: {total_triage}")
        self.stdout.write(f"Consultations: {total_consultations}")
        self.stdout.write(f"Prescriptions: {total_prescriptions}")
        self.stdout.write(f"Prescription Items: {total_prescription_items}")
        self.stdout.write(f"Lab Orders: {total_lab_orders}")
        self.stdout.write(f"Lab Samples: {total_lab_samples}")
        self.stdout.write(f"Lab Results: {total_lab_results}")
        self.stdout.write(f"Medicines: {total_medicines}")
        self.stdout.write(f"Medicine Batches: {total_medicine_batches}")
        self.stdout.write(f"Inventory Transactions: {total_inv_txns}")
        self.stdout.write(f"Purchase Orders: {total_purchase_orders}")
        self.stdout.write(f"Referrals: {total_referrals}")
        self.stdout.write(f"Follow Ups: {total_follow_ups}")
        self.stdout.write(f"NCD Records: {total_ncd}")
        self.stdout.write(f"Maternal Records: {total_maternal}")
        self.stdout.write(f"Child Records: {total_child}")
        self.stdout.write(f"Disease Cases: {total_disease_cases}")
        self.stdout.write(f"Teleconsultations: {total_teleconsults}")
        self.stdout.write(f"Outreach: {total_outreach}")
        self.stdout.write(f"Wellness: {total_wellness}")
        self.stdout.write(f"ARS Meetings: {total_ars_meetings}")
        self.stdout.write(f"Quality Records: {total_quality_records}")
        self.stdout.write(f"Biomedical Waste Logs: {total_bmw_logs}")
        self.stdout.write(f"Alerts: {total_alerts}")
        self.stdout.write(f"Audit Logs: {total_audit_logs}")

        self.stdout.write(self.style.SUCCESS("\nToday's Activity Summary:"))
        self.stdout.write(f"Today's Visits: {t_visits_count}")
        self.stdout.write(f"Waiting for Triage: {t_waiting_triage}")
        self.stdout.write(f"Waiting for Doctor: {t_waiting_doc}")
        self.stdout.write(f"In Consultation: {t_in_consult}")
        self.stdout.write(f"Lab Pending: {t_lab_pending}")
        self.stdout.write(f"Lab In Progress: {t_lab_in_progress}")
        self.stdout.write(f"Waiting for Pharmacy: {t_waiting_pharm}")
        self.stdout.write(f"Completed: {t_completed}")
        self.stdout.write(f"Emergency/High Priority: {t_emergency_high}\n")

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
from apps.patients.models import Patient, Household, PatientDocument
from apps.visits.models import Visit, Token
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabTestMaster, LabOrder, LabSample, LabResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction, Vendor, PurchaseOrder, PurchaseOrderItem
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
    help = "Seed local SQLite database with realistic Namma Clinic digital healthcare network demo dataset for ALL 4 facilities."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Flushing and re-seeding Namma Clinic demo dataset for ALL 4 healthcare facilities..."))

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
        ward_rural = Ward.objects.create(zone=zone_hoskote, ward_number=1, name='Varthur Rural Ward', population=18000, slum_population=7200)

        # 2. Facilities (Strictly 4 Facilities)
        # Facility 1: Main District Hospital
        hosp_a = Facility.objects.create(
            facility_code='HOSP-DIST-01', facility_name='Victoria District General Hospital & Specialist Center', facility_type='MAIN_HOSPITAL',
            state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP Central', urban_rural='URBAN',
            address='Fort Road, Near KR Market, Bengaluru - 560002', latitude=12.9634, longitude=77.5750, population_served=500000,
            emergency_available=True, lab_available=True, pharmacy_available=True, teleconsultation_available=True, bed_capacity=750,
            services='Cardiology, Nephrology, General Surgery, Emergency, ICU, Teleconsultation Hub'
        )

        # Facility 2: Sub-District Hospital
        nc_a1 = Facility.objects.create(
            facility_code='HOSP-SUB-01', facility_name='Indiranagar Sub-District Hospital & UPHC', facility_type='NAMMA_CLINIC',
            parent_facility=hosp_a, state=karnataka, district=dist_central, zone=zone_east, ward=ward12, city_or_ulb='BBMP East', urban_rural='URBAN',
            address='100 Feet Road, Indiranagar, Bengaluru - 560038', latitude=12.9719, longitude=77.6412, population_served=35000, vulnerable_population=8500,
            emergency_available=True, lab_available=True, pharmacy_available=True, teleconsultation_available=True, bed_capacity=60,
            services='Maternal ANC, Child Care, General OPD, Basic Surgery, NCD Screening'
        )

        # Facility 3: Village Hospital 1 (Rural Primary Clinic)
        rc_a4 = Facility.objects.create(
            facility_code='RC-A4-04', facility_name='Varthur Rural Primary Clinic A4', facility_type='RURAL_CLINIC',
            parent_facility=nc_a1, state=karnataka, district=dist_central, zone=zone_east, ward=ward_rural, city_or_ulb='BBMP East Peripheral', urban_rural='RURAL',
            address='Main Bus Stand Road, Varthur Village, Bengaluru Rural - 560087', latitude=12.9406, longitude=77.7470, population_served=19000, vulnerable_population=7200,
            emergency_available=False, lab_available=True, pharmacy_available=True, teleconsultation_available=True, bed_capacity=10,
            services='General OPD, NCD Screening, Immunization, Basic Diagnostics'
        )

        # Facility 4: Village Hospital 2 (Village Satellite Clinic)
        vc_a4_1 = Facility.objects.create(
            facility_code='VC-A4-01', facility_name='Gunjur Village Satellite Clinic', facility_type='VILLAGE_CLINIC',
            parent_facility=rc_a4, state=karnataka, district=dist_central, zone=zone_east, ward=ward_rural, city_or_ulb='BBMP East Peripheral', urban_rural='RURAL',
            address='Gunjur Lake Road, Gunjur Village, Bengaluru Rural - 560087', latitude=12.9300, longitude=77.7550, population_served=8000, vulnerable_population=3100,
            emergency_available=False, lab_available=True, pharmacy_available=True, teleconsultation_available=False, bed_capacity=4,
            services='Primary Screening, Immunization, First Aid, Tele-referral'
        )

        # 3. Facility Relationships (4-Tier Healthcare Referral Graph)
        FacilityRelationship.objects.create(
            source_facility=vc_a4_1, destination_facility=rc_a4, relationship_type='REFERRAL', service='Village Primary Referral', priority='PRIMARY', distance_km=2.5
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=nc_a1, relationship_type='REFERRAL', service='Sub-District Secondary Care', priority='PRIMARY', distance_km=4.2
        )
        FacilityRelationship.objects.create(
            source_facility=nc_a1, destination_facility=hosp_a, relationship_type='SPECIALIST', service='District Cardiology & Tertiary Surgery', priority='EMERGENCY', distance_km=5.0
        )
        FacilityRelationship.objects.create(
            source_facility=rc_a4, destination_facility=hosp_a, relationship_type='SPECIALIST', service='Direct Emergency ICU Referral', priority='EMERGENCY', distance_km=12.0
        )

        # 4. Users & Staff Accounts Across ALL 4 Facilities
        u_dist = User.objects.create_user('district', 'district@nammaclinic.gov.in', 'district123', full_name='Dr. Sunita Rao (District Health Officer)', role='DISTRICT_OFFICER', assigned_district=dist_central)

        # Facility Admins
        u_dh_admin = User.objects.create_user('dh_admin', 'dh_admin@nammaclinic.gov.in', 'dh123', full_name='Dr. K. V. Sharma (District Hospital Supt)', role='HOSPITAL_ADMIN', assigned_facility=hosp_a)
        u_hosp = User.objects.create_user('hospital', 'hospital@nammaclinic.gov.in', 'hospital123', full_name='Dr. K. V. Sharma (District Hospital Supt)', role='HOSPITAL_ADMIN', assigned_facility=hosp_a)
        u_sdh_admin = User.objects.create_user('sdh_admin', 'sdh_admin@nammaclinic.gov.in', 'sdh123', full_name='Dr. Meena Swamy (Sub-District Admin)', role='HOSPITAL_ADMIN', assigned_facility=nc_a1)
        u_vh1_admin = User.objects.create_user('vh1_admin', 'vh1_admin@nammaclinic.gov.in', 'vh1123', full_name='Dr. Ramesh Rao (Village Hospital 1 Admin)', role='HOSPITAL_ADMIN', assigned_facility=rc_a4)
        u_vh2_admin = User.objects.create_user('vh2_admin', 'vh2_admin@nammaclinic.gov.in', 'vh2123', full_name='Dr. Anand Kumar (Village Hospital 2 Admin)', role='HOSPITAL_ADMIN', assigned_facility=vc_a4_1)

        # Doctors for ALL 4 Facilities
        u_dh_doc = User.objects.create_user('dh_doctor', 'dh_doctor@nammaclinic.gov.in', 'dhdoc123', full_name='Dr. Vikram Seth (District Senior Cardiologist)', role='DOCTOR', assigned_facility=hosp_a)
        u_sdh_doc = User.objects.create_user('sdh_doctor', 'sdh_doctor@nammaclinic.gov.in', 'sdhdoc123', full_name='Dr. Asha Patil (Sub-District Gynecologist)', role='DOCTOR', assigned_facility=nc_a1)
        u_vh1_doc = User.objects.create_user('vh1_doctor', 'vh1_doctor@nammaclinic.gov.in', 'vh1doc123', full_name='Dr. Rajesh Kumar (Village Hospital 1 MO)', role='DOCTOR', assigned_facility=rc_a4)
        u_doc = User.objects.create_user('doctor', 'doctor@nammaclinic.gov.in', 'doctor123', full_name='Dr. Rajesh Kumar (Village Hospital 1 MO)', role='DOCTOR', assigned_facility=rc_a4)
        u_vh2_doc = User.objects.create_user('vh2_doctor', 'vh2_doctor@nammaclinic.gov.in', 'vh2doc123', full_name='Dr. Suresh V. (Village Hospital 2 MO)', role='DOCTOR', assigned_facility=vc_a4_1)

        # Clinical Staff for ALL 4 Facilities
        u_nurse = User.objects.create_user('nurse', 'nurse@nammaclinic.gov.in', 'nurse123', full_name='Sister Priya Nair', role='NURSE', assigned_facility=rc_a4)
        u_sdh_nurse = User.objects.create_user('sdh_nurse', 'sdh_nurse@nammaclinic.gov.in', 'sdhnurse123', full_name='Sister Kavitha R.', role='NURSE', assigned_facility=nc_a1)
        u_dh_nurse = User.objects.create_user('dh_nurse', 'dh_nurse@nammaclinic.gov.in', 'dhnurse123', full_name='Sister Mary Joseph', role='NURSE', assigned_facility=hosp_a)

        u_lab = User.objects.create_user('lab', 'lab@nammaclinic.gov.in', 'lab123', full_name='Mr. Suresh Gowda', role='LAB_TECHNICIAN', assigned_facility=rc_a4)
        u_dh_lab = User.objects.create_user('dh_lab', 'dh_lab@nammaclinic.gov.in', 'dhlab123', full_name='Mr. Chethan M.', role='LAB_TECHNICIAN', assigned_facility=hosp_a)

        u_pharm = User.objects.create_user('pharmacy', 'pharmacy@nammaclinic.gov.in', 'pharmacy123', full_name='Mrs. Lakshmi Devi', role='PHARMACIST', assigned_facility=rc_a4)
        u_dh_pharm = User.objects.create_user('dh_pharmacy', 'dh_pharmacy@nammaclinic.gov.in', 'dhpharm123', full_name='Mr. Mahesh Babu', role='PHARMACIST', assigned_facility=hosp_a)

        # 5. Diagnostic Test Masters & Essential Medicines
        lt_hba1c = LabTestMaster.objects.create(code='L-HBA1C', name='HbA1c Glycated Hemoglobin', category='Diabetes', reference_range='4.0 - 5.6 %', unit='%')
        lt_fbg = LabTestMaster.objects.create(code='L-FBG', name='Fasting Blood Glucose (FBG)', category='Diabetes', reference_range='70 - 100 mg/dL', unit='mg/dL')
        lt_rbg = LabTestMaster.objects.create(code='L-RBG', name='Random Blood Glucose (Rapid Strip)', category='Diabetes', reference_range='70 - 140 mg/dL', unit='mg/dL')
        lt_hb = LabTestMaster.objects.create(code='L-HB', name='Hemoglobin (Hb Estimation)', category='Hematology', reference_range='12.0 - 15.5 g/dL', unit='g/dL')
        lt_lipid = LabTestMaster.objects.create(code='L-LIPID', name='Lipid Profile (Cholesterol & Triglycerides)', category='Biochemistry', reference_range='Desirable < 200 mg/dL', unit='mg/dL')
        lt_dengue = LabTestMaster.objects.create(code='L-DENGUE', name='Dengue NS1 Antigen Rapid Test Card', category='Serology', reference_range='Negative', unit='Result')
        lt_malaria = LabTestMaster.objects.create(code='L-MALARIA', name='Malaria Antigen (Pf/Pv) Rapid Test', category='Serology', reference_range='Negative', unit='Result')
        lt_u_prot = LabTestMaster.objects.create(code='L-URINE-PROT', name='Urine Albumin / Protein Test', category='Urinalysis', reference_range='Nil / Negative', unit='Grade')
        lt_tb = LabTestMaster.objects.create(code='L-TB-SPUTUM', name='Sputum Smear for AFB (Tuberculosis)', category='Microbiology', reference_range='Negative for AFB', unit='Result')
        lt_upt = LabTestMaster.objects.create(code='L-PREG-RAPID', name='Urine Pregnancy Test (UPT Card)', category='Maternal RCH', reference_range='Negative', unit='Result')

        med_met = MedicineMaster.objects.create(generic_name='Metformin HCl', brand_name='Glycomet', strength='500 mg', dosage_form='Tablet', category='Anti-Diabetic', minimum_stock=50, reorder_level=100)
        med_aml = MedicineMaster.objects.create(generic_name='Amlodipine Besylate', brand_name='Amlopres', strength='5 mg', dosage_form='Tablet', category='Anti-Hypertensive', minimum_stock=50, reorder_level=100)
        med_pcm = MedicineMaster.objects.create(generic_name='Paracetamol', brand_name='Dolo', strength='650 mg', dosage_form='Tablet', category='Analgesic / Antipyretic', minimum_stock=100, reorder_level=200)
        med_amx = MedicineMaster.objects.create(generic_name='Amoxicillin Trihydrate', brand_name='Mox', strength='500 mg', dosage_form='Capsule', category='Antibiotic', minimum_stock=50, reorder_level=100)
        med_tel = MedicineMaster.objects.create(generic_name='Telmisartan', brand_name='Telma', strength='40 mg', dosage_form='Tablet', category='Anti-Hypertensive', minimum_stock=40, reorder_level=80)
        med_ifa = MedicineMaster.objects.create(generic_name='Iron & Folic Acid', brand_name='IFA Red', strength='100mg Fe + 500mcg FA', dosage_form='Tablet', category='Maternal Health', minimum_stock=75, reorder_level=150)
        med_cet = MedicineMaster.objects.create(generic_name='Cetirizine HCl', brand_name='Cetzine', strength='10 mg', dosage_form='Tablet', category='Antihistamine', minimum_stock=30, reorder_level=60)

        # Vendors
        v_ksmscl, _ = Vendor.objects.get_or_create(
            vendor_name='KSMSCL (Karnataka State Medical Supplies Corp Ltd)',
            defaults={
                'contact_person': 'Mr. R. K. Hegde (General Manager)',
                'phone': '080-22345678',
                'email': 'procurement@ksmscl.in',
                'address': 'Rehabilitative Building, Anand Rao Circle, Bengaluru',
                'gst_number': '29AAACK1234F1Z5',
                'status': 'ACTIVE'
            }
        )
        v_kapl, _ = Vendor.objects.get_or_create(
            vendor_name='Karnataka Antibiotics & Pharmaceuticals Ltd (KAPL)',
            defaults={
                'contact_person': 'Dr. S. M. Patel',
                'phone': '080-28392555',
                'email': 'sales@kaplindia.com',
                'address': 'Peenya Industrial Area, 1st Stage, Bengaluru',
                'gst_number': '29AAACK5678F1Z9',
                'status': 'ACTIVE'
            }
        )

        today = datetime.date.today()
        yest = today - datetime.timedelta(days=1)
        prev = today - datetime.timedelta(days=2)

        # 6. FEFO Medicine Inventory Batches for ALL 4 Facilities
        facilities_list = [hosp_a, nc_a1, rc_a4, vc_a4_1]
        for fac in facilities_list:
            b1 = MedicineBatch.objects.create(
                facility=fac, medicine=med_met, batch_number=f"MET-{fac.facility_code}-2026A", vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=120), expiry_date=today + datetime.timedelta(days=180), quantity=500, unit_cost=1.20, status='ACTIVE'
            )
            b2 = MedicineBatch.objects.create(
                facility=fac, medicine=med_aml, batch_number=f"AML-{fac.facility_code}-2026B", vendor=v_ksmscl, supplier=v_ksmscl.vendor_name,
                mfg_date=today - datetime.timedelta(days=90), expiry_date=today + datetime.timedelta(days=40), quantity=45, unit_cost=0.85, status='LOW_STOCK'
            )
            b3 = MedicineBatch.objects.create(
                facility=fac, medicine=med_pcm, batch_number=f"PCM-{fac.facility_code}-2026P", vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=60), expiry_date=today + datetime.timedelta(days=300), quantity=1200, unit_cost=0.50, status='ACTIVE'
            )
            b4 = MedicineBatch.objects.create(
                facility=fac, medicine=med_ifa, batch_number=f"IFA-{fac.facility_code}-2026M", vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=150), expiry_date=today + datetime.timedelta(days=240), quantity=800, unit_cost=0.60, status='ACTIVE'
            )
            b5 = MedicineBatch.objects.create(
                facility=fac, medicine=med_amx, batch_number=f"AMX-{fac.facility_code}-OLD", vendor=v_kapl, supplier=v_kapl.vendor_name,
                mfg_date=today - datetime.timedelta(days=375), expiry_date=today - datetime.timedelta(days=10), quantity=30, unit_cost=2.10, status='EXPIRED'
            )

            # Purchase Orders per Facility
            po = PurchaseOrder.objects.create(
                po_number=f"PO-{fac.facility_code}-2026-001", vendor=v_ksmscl, facility=fac, order_date=today - datetime.timedelta(days=5),
                expected_delivery_date=today + datetime.timedelta(days=3), status='ORDERED', created_by=u_dist,
                notes='Emergency replenishment of Essential Anti-Hypertensives & Analgesics.'
            )
            PurchaseOrderItem.objects.create(purchase_order=po, medicine=med_aml, ordered_quantity=200, received_quantity=0, unit_price=0.85, total_price=170.00)
            PurchaseOrderItem.objects.create(purchase_order=po, medicine=med_amx, ordered_quantity=150, received_quantity=0, unit_price=2.10, total_price=315.00)
            po.total_amount = 485.00
            po.save()
            MedicineBatch.objects.create(
                facility=fac, medicine=med_ifa, batch_number=f"IFA-{fac.facility_code}-2026M", supplier='KSMSCL E-Aushada',
                expiry_date=today + datetime.timedelta(days=240), quantity=800, status='ACTIVE'
            )
            MedicineBatch.objects.create(
                facility=fac, medicine=med_amx, batch_number=f"AMX-{fac.facility_code}-OLD", supplier='KSMSCL E-Aushada',
                expiry_date=today - datetime.timedelta(days=10), quantity=30, status='EXPIRED'
            )

        # 7. Patient Registrations Properly Mapped to Each Facility
        # Facility 1: Victoria District Hospital Patients
        p_dh_1 = Patient.objects.create(
            patient_id='NC-20260901-101', name='Kavitha Sundaram', date_of_birth=datetime.date(1980, 4, 10), age=46, gender='FEMALE',
            mobile='9880112233', address='Subbaraya Chetty Road, KR Market, Bengaluru', ward=ward12, district=dist_central,
            ABHA_ID_DEMO='91-1122-3344-5566', vulnerability_information='Urban Slum Resident BPL', registered_at_facility=hosp_a
        )
        p_dh_2 = Patient.objects.create(
            patient_id='NC-20260901-102', name='Narayana Swamy', date_of_birth=datetime.date(1958, 11, 22), age=68, gender='MALE',
            mobile='9880223344', address='Fort Slum Pocket, KR Market Ward 12', ward=ward12, district=dist_central,
            ABHA_ID_DEMO='91-2233-4455-6677', vulnerability_information='Senior Citizen / Cardiac History', registered_at_facility=hosp_a
        )

        # Facility 2: Indiranagar Sub-District Hospital Patients
        p_anita = Patient.objects.create(
            patient_id='NC-20260901-002', name='Anita Devi', date_of_birth=datetime.date(1996, 8, 20), age=30, gender='FEMALE',
            mobile='9845012345', address='Cross Road #3, Indiranagar Slum Colony', ward=ward12, district=dist_central,
            ABHA_ID_DEMO='91-1234-5678-9012', vulnerability_information='High Risk Pregnancy ANC', registered_at_facility=nc_a1
        )
        p_sdh_2 = Patient.objects.create(
            patient_id='NC-20260901-202', name='Manjunath G.', date_of_birth=datetime.date(1985, 2, 14), age=41, gender='MALE',
            mobile='9845998877', address='HAL 2nd Stage, Indiranagar', ward=ward12, district=dist_central,
            ABHA_ID_DEMO='91-5566-7788-9900', vulnerability_information='Hypertension / General BPL', registered_at_facility=nc_a1
        )

        # Facility 3: Varthur Rural Primary Clinic A4 Patients
        p_ramesh = Patient.objects.create(
            patient_id='NC-20260901-001', name='Ramesh Kumar', date_of_birth=datetime.date(1974, 5, 12), age=52, gender='MALE',
            mobile='9876543210', address='House #45, Near Govt School, Varthur Slum Area', ward=ward_rural, district=dist_central,
            ABHA_ID_DEMO='91-8765-4321-0987', emergency_contact='9876543211 (Wife - Sunita)', vulnerability_information='Slum Household BPL',
            registered_at_facility=rc_a4
        )
        p_vh1_2 = Patient.objects.create(
            patient_id='NC-20260901-302', name='Lakshmamma B.', date_of_birth=datetime.date(1965, 7, 8), age=61, gender='FEMALE',
            mobile='9876112233', address='Varthur Lake BPL Slum Line 4', ward=ward_rural, district=dist_central,
            ABHA_ID_DEMO='91-4455-6677-8899', vulnerability_information='Diabetic Elderly', registered_at_facility=rc_a4
        )

        # Facility 4: Gunjur Village Satellite Clinic Patients
        p_suresh = Patient.objects.create(
            patient_id='NC-20260901-003', name='Suresh Patil', date_of_birth=datetime.date(1961, 3, 15), age=65, gender='MALE',
            mobile='9900112233', address='Gunjur Village Main Road', ward=ward_rural, district=dist_central,
            ABHA_ID_DEMO='91-9988-7766-5544', vulnerability_information='Senior Citizen / Diabetic', registered_at_facility=vc_a4_1
        )
        p_vh2_2 = Patient.objects.create(
            patient_id='NC-20260901-402', name='Gowramma M.', date_of_birth=datetime.date(1992, 9, 30), age=34, gender='FEMALE',
            mobile='9900445566', address='Gunjur Colony Pocket B', ward=ward_rural, district=dist_central,
            ABHA_ID_DEMO='91-3344-5566-7788', vulnerability_information='Maternal ANC / Rural BPL', registered_at_facility=vc_a4_1
        )

        # 30 additional Citizens mapped evenly across the 4 facilities
        for i in range(10, 40):
            target_fac = facilities_list[i % 4]
            g = 'MALE' if i % 2 == 0 else 'FEMALE'
            Patient.objects.create(
                patient_id=f"NC-20260901-{i:03d}", name=f"Demo Citizen {i}", age=20 + (i * 3) % 45, gender=g,
                mobile=f"980000{i:04d}", address=f"{target_fac.facility_name} Catchment Slum {i % 4 + 1}", ward=ward_rural, district=dist_central,
                registered_at_facility=target_fac
            )

        # 8. OPD VISITS & DATE-BASED QUEUES FOR ALL 4 HOSPITALS
        # Token numbers restart from #1 for EACH facility per day!

        # --- FACILITY 1: Victoria District Hospital ---
        # Today Visit 1 (Token #1) - Completed
        v_dh_1 = Visit.objects.create(
            visit_id=f"VIS-DH-{today.strftime('%Y%m%d')}-001", patient=p_dh_2, facility=hosp_a,
            opd_date=today, visit_type='GENERAL_OPD', priority='HIGH', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Severe chest tightness & shortness of breath',
            assigned_doctor=u_dh_doc, arrival_time=timezone.now() - datetime.timedelta(hours=3),
            completed_time=timezone.now() - datetime.timedelta(hours=1)
        )
        t_dh_1 = Token.objects.create(token_number=1, visit=v_dh_1, facility=hosp_a, date=today, priority='HIGH', status='COMPLETED')

        # Today Visit 2 (Token #2) - Waiting for Doctor
        v_dh_2 = Visit.objects.create(
            visit_id=f"VIS-DH-{today.strftime('%Y%m%d')}-002", patient=p_dh_1, facility=hosp_a,
            opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='DOCTOR',
            status='WAITING_FOR_DOCTOR', chief_complaint='Chronic joint pain and hypertension evaluation',
            assigned_doctor=u_dh_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=45)
        )
        t_dh_2 = Token.objects.create(token_number=2, visit=v_dh_2, facility=hosp_a, date=today, priority='NORMAL', status='WAITING')

        # --- FACILITY 2: Indiranagar Sub-District Hospital ---
        # Today Visit 1 (Token #1) - Completed ANC
        v_sdh_1 = Visit.objects.create(
            visit_id=f"VIS-SDH-{today.strftime('%Y%m%d')}-001", patient=p_anita, facility=nc_a1,
            opd_date=today, visit_type='MATERNAL_ANC', priority='HIGH', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Routine 2nd Trimester ANC Checkup & BP Check',
            assigned_doctor=u_sdh_doc, arrival_time=timezone.now() - datetime.timedelta(hours=2),
            completed_time=timezone.now() - datetime.timedelta(minutes=40)
        )
        t_sdh_1 = Token.objects.create(token_number=1, visit=v_sdh_1, facility=nc_a1, date=today, priority='HIGH', status='COMPLETED')

        # Today Visit 2 (Token #2) - Waiting for Pharmacy
        v_sdh_2 = Visit.objects.create(
            visit_id=f"VIS-SDH-{today.strftime('%Y%m%d')}-002", patient=p_sdh_2, facility=nc_a1,
            opd_date=today, visit_type='NCD_SCREENING', priority='NORMAL', current_queue='PHARMACY',
            status='WAITING_FOR_PHARMACY', chief_complaint='Routine Hypertension prescription renewal',
            assigned_doctor=u_sdh_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=50)
        )
        t_sdh_2 = Token.objects.create(token_number=2, visit=v_sdh_2, facility=nc_a1, date=today, priority='NORMAL', status='WAITING')

        # --- FACILITY 3: Varthur Rural Primary Clinic A4 ---
        # Today Visit 1 (Token #1) - Waiting for Pharmacy Dispense
        v_rc_1 = Visit.objects.create(
            visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-001", patient=p_ramesh, facility=rc_a4,
            opd_date=today, visit_type='GENERAL_OPD', priority='HIGH', current_queue='PHARMACY',
            status='WAITING_FOR_PHARMACY', chief_complaint='Dizziness, severe fatigue, and blurred vision for 5 days',
            assigned_doctor=u_doc, arrival_time=timezone.now() - datetime.timedelta(hours=1, minutes=30)
        )
        t_rc_1 = Token.objects.create(token_number=1, visit=v_rc_1, facility=rc_a4, date=today, priority='HIGH', status='WAITING')

        # Today Visit 2 (Token #2) - Waiting for Triage
        v_rc_2 = Visit.objects.create(
            visit_id=f"VIS-RC-{today.strftime('%Y%m%d')}-002", patient=p_vh1_2, facility=rc_a4,
            opd_date=today, visit_type='NCD_SCREENING', priority='NORMAL', current_queue='TRIAGE',
            status='WAITING_FOR_TRIAGE', chief_complaint='Blood pressure monitoring & blood sugar check',
            arrival_time=timezone.now() - datetime.timedelta(minutes=25)
        )
        t_rc_2 = Token.objects.create(token_number=2, visit=v_rc_2, facility=rc_a4, date=today, priority='NORMAL', status='WAITING')

        # --- FACILITY 4: Gunjur Village Satellite Clinic ---
        # Today Visit 1 (Token #1) - Completed
        v_vc_1 = Visit.objects.create(
            visit_id=f"VIS-VC-{today.strftime('%Y%m%d')}-001", patient=p_suresh, facility=vc_a4_1,
            opd_date=today, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Fever & body ache for 2 days',
            assigned_doctor=u_vh2_doc, arrival_time=timezone.now() - datetime.timedelta(hours=1, minutes=45),
            completed_time=timezone.now() - datetime.timedelta(minutes=15)
        )
        t_vc_1 = Token.objects.create(token_number=1, visit=v_vc_1, facility=vc_a4_1, date=today, priority='NORMAL', status='COMPLETED')

        # Today Visit 2 (Token #2) - Waiting for Doctor
        v_vc_2 = Visit.objects.create(
            visit_id=f"VIS-VC-{today.strftime('%Y%m%d')}-002", patient=p_vh2_2, facility=vc_a4_1,
            opd_date=today, visit_type='MATERNAL_ANC', priority='HIGH', current_queue='DOCTOR',
            status='WAITING_FOR_DOCTOR', chief_complaint='1st Trimester ANC registration & checkup',
            assigned_doctor=u_vh2_doc, arrival_time=timezone.now() - datetime.timedelta(minutes=15)
        )
        t_vc_2 = Token.objects.create(token_number=2, visit=v_vc_2, facility=vc_a4_1, date=today, priority='HIGH', status='WAITING')

        # Historical Visits for Date-Based Queue Testing (Yesterday)
        # Facility 1 Yesterday Visit
        v_dh_yest = Visit.objects.create(
            visit_id=f"VIS-DH-{yest.strftime('%Y%m%d')}-001", patient=p_dh_2, facility=hosp_a,
            opd_date=yest, visit_type='GENERAL_OPD', priority='EMERGENCY', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='Hypertensive Emergency & Giddiness', assigned_doctor=u_dh_doc,
            arrival_time=timezone.make_aware(datetime.datetime.combine(yest, datetime.time(10, 0)))
        )
        Token.objects.create(token_number=1, visit=v_dh_yest, facility=hosp_a, date=yest, priority='EMERGENCY', status='COMPLETED')

        # Facility 3 Yesterday Visit
        v_rc_yest = Visit.objects.create(
            visit_id=f"VIS-RC-{yest.strftime('%Y%m%d')}-001", patient=p_ramesh, facility=rc_a4,
            opd_date=yest, visit_type='GENERAL_OPD', priority='NORMAL', current_queue='COMPLETED',
            status='COMPLETED', chief_complaint='High BP check', assigned_doctor=u_doc,
            arrival_time=timezone.make_aware(datetime.datetime.combine(yest, datetime.time(11, 30)))
        )
        Token.objects.create(token_number=1, visit=v_rc_yest, facility=rc_a4, date=yest, priority='NORMAL', status='COMPLETED')

        # 9. TRIAGE VITALS FOR ALL FACILITIES
        TriageVitals.objects.create(
            visit=v_dh_1, patient=p_dh_2, nurse=u_dh_nurse,
            blood_pressure_systolic=160, blood_pressure_diastolic=102, pulse_bpm=92, temperature_f=98.6,
            spo2_percent=95, respiratory_rate=22, height_cm=165.0, weight_kg=72.0, blood_glucose_mgdl=190,
            high_bp_flag=True, high_glucose_flag=True, emergency_flag=True, nurse_notes='Patient presents with severe hypertension and shortness of breath. Triage fast-tracked.'
        )

        TriageVitals.objects.create(
            visit=v_sdh_1, patient=p_anita, nurse=u_sdh_nurse,
            blood_pressure_systolic=118, blood_pressure_diastolic=78, pulse_bpm=76, temperature_f=98.4,
            spo2_percent=99, respiratory_rate=16, height_cm=158.0, weight_kg=62.0, blood_glucose_mgdl=95,
            pregnancy_high_risk_flag=True, nurse_notes='2nd Trimester ANC. Fetal heart sound normal (142 bpm).'
        )

        TriageVitals.objects.create(
            visit=v_rc_1, patient=p_ramesh, nurse=u_nurse,
            blood_pressure_systolic=148, blood_pressure_diastolic=96, pulse_bpm=84, temperature_f=99.1,
            spo2_percent=98, respiratory_rate=18, height_cm=168.0, weight_kg=78.0, blood_glucose_mgdl=185,
            high_bp_flag=True, high_glucose_flag=True, ncd_risk_flag=True, nurse_notes='Elevated BP and blood sugar. Fast-tracked for doctor.'
        )

        TriageVitals.objects.create(
            visit=v_vc_1, patient=p_suresh, nurse=u_nurse,
            blood_pressure_systolic=132, blood_pressure_diastolic=84, pulse_bpm=78, temperature_f=100.2,
            spo2_percent=97, respiratory_rate=18, height_cm=162.0, weight_kg=68.0, blood_glucose_mgdl=130,
            fever_flag=True, nurse_notes='Fever 100.2F. Rapid malaria & dengue strip ordered.'
        )

        TriageVitals.objects.create(
            visit=v_dh_2, patient=p_dh_1, nurse=u_dh_nurse,
            blood_pressure_systolic=138, blood_pressure_diastolic=88, pulse_bpm=76, temperature_f=98.6,
            spo2_percent=98, respiratory_rate=18, height_cm=160.0, weight_kg=64.0, blood_glucose_mgdl=115,
            nurse_notes='Hypertension follow-up. Waiting for doctor.'
        )

        TriageVitals.objects.create(
            visit=v_vc_2, patient=p_vh2_2, nurse=u_nurse,
            blood_pressure_systolic=116, blood_pressure_diastolic=74, pulse_bpm=80, temperature_f=98.4,
            spo2_percent=99, respiratory_rate=16, height_cm=155.0, weight_kg=56.0, blood_glucose_mgdl=90,
            pregnancy_high_risk_flag=False, nurse_notes='1st Trimester ANC routine triage.'
        )

        # 10. DOCTOR CONSULTATIONS & EMR DIAGNOSES
        c_dh_1 = Consultation.objects.create(
            visit=v_dh_1, patient=p_dh_2, doctor=u_dh_doc, facility=hosp_a,
            chief_complaint='Severe chest tightness & dyspnea',
            clinical_history='Longstanding Stage II Hypertension, non-compliant with medication.',
            clinical_assessment='BP 160/102 mmHg. ECG shows LVH patterns. Suspected Hypertensive Heart Disease.',
            diagnosis_code='I11.9', diagnosis_name='Hypertensive Heart Disease without Heart Failure',
            treatment_plan='Initiate Telmisartan 40mg + Amlodipine 5mg. Perform Echocardiogram & Lipid profile.',
            follow_up_date=today + datetime.timedelta(days=7), clinical_notes='Admitted to observation ward for 4 hours.'
        )

        c_sdh_1 = Consultation.objects.create(
            visit=v_sdh_1, patient=p_anita, doctor=u_sdh_doc, facility=nc_a1,
            chief_complaint='Routine 2nd Trimester ANC Checkup',
            clinical_history='G2P1A0 at 24 weeks gestation. Previous mild anemia.',
            clinical_assessment='BP normal 118/78. Uterine height corresponds to dates. Hb 10.2 g/dL mild anemia.',
            diagnosis_code='O99.0', diagnosis_name='Anemia Complicating Pregnancy',
            treatment_plan='Continue Iron & Folic Acid tablets 1 OD. Advised rich iron diet. Schedule Obstetric Ultrasound.',
            follow_up_date=today + datetime.timedelta(days=28), clinical_notes='Maternal health card updated.'
        )

        c_rc_1 = Consultation.objects.create(
            visit=v_rc_1, patient=p_ramesh, doctor=u_doc, facility=rc_a4,
            chief_complaint='Dizziness and fatigue for 5 days',
            clinical_history='Hypertension for 2 years. Poor medication adherence.',
            clinical_assessment='Elevated BP 148/96 and Glucose 185 mg/dL. Suspected uncontrolled Type 2 Diabetes.',
            diagnosis_code='E11.9 / I10', diagnosis_name='Type 2 Diabetes Mellitus with Essential Hypertension',
            treatment_plan='Initiate Metformin 500mg BD, Amlodipine 5mg OD. Refer to Victoria Hospital for Cardiology consult.',
            follow_up_date=today + datetime.timedelta(days=14), clinical_notes='Dietary counseling provided.'
        )

        c_vc_1 = Consultation.objects.create(
            visit=v_vc_1, patient=p_suresh, doctor=u_vh2_doc, facility=vc_a4_1,
            chief_complaint='Acute fever and body ache',
            clinical_history='No past chronic illnesses reported.',
            clinical_assessment='Temperature 100.2F, pharyngeal congestion. Dengue & Malaria rapid cards negative.',
            diagnosis_code='J06.9', diagnosis_name='Acute Upper Respiratory Tract Infection',
            treatment_plan='Paracetamol 650mg TDS for 3 days, hydration advice.',
            follow_up_date=today + datetime.timedelta(days=3), clinical_notes='Symptomatic treatment initiated.'
        )

        # 11. PRESCRIPTIONS & DISPENSATIONS
        # Facility 1 Prescription
        pr_dh = Prescription.objects.create(consultation=c_dh_1, patient=p_dh_2, doctor=u_dh_doc, facility=hosp_a, status='DISPENSED')
        pi_dh_1 = PrescriptionItem.objects.create(prescription=pr_dh, medicine=med_tel, medicine_name='Telmisartan 40 mg Tablet', dosage='1-0-0 Morning', frequency='Once Daily', duration_days=30, quantity=30, status='DISPENSED')
        pi_dh_2 = PrescriptionItem.objects.create(prescription=pr_dh, medicine=med_aml, medicine_name='Amlodipine 5 mg Tablet', dosage='0-0-1 Night', frequency='Once Daily', duration_days=30, quantity=30, status='DISPENSED')
        b_dh_aml = MedicineBatch.objects.filter(facility=hosp_a, medicine=med_aml).first()
        if b_dh_aml:
            b_dh_aml.quantity = max(0, b_dh_aml.quantity - 30)
            b_dh_aml.save()
            InventoryTransaction.objects.create(facility=hosp_a, medicine=med_aml, batch=b_dh_aml, transaction_type='DISPENSED', quantity=30, reference_id=f"PRESCR-{pr_dh.id}", created_by=u_dist, notes='Dispensed 30 units Amlodipine for Narayana Swamy')

        # Facility 2 Prescription
        pr_sdh = Prescription.objects.create(consultation=c_sdh_1, patient=p_anita, doctor=u_sdh_doc, facility=nc_a1, status='DISPENSED')
        pi_sdh = PrescriptionItem.objects.create(prescription=pr_sdh, medicine=med_ifa, medicine_name='Iron & Folic Acid Tablet', dosage='1-0-0 After Food', frequency='Once Daily', duration_days=30, quantity=30, status='DISPENSED')
        b_sdh_ifa = MedicineBatch.objects.filter(facility=nc_a1, medicine=med_ifa).first()
        if b_sdh_ifa:
            b_sdh_ifa.quantity = max(0, b_sdh_ifa.quantity - 30)
            b_sdh_ifa.save()
            InventoryTransaction.objects.create(facility=nc_a1, medicine=med_ifa, batch=b_sdh_ifa, transaction_type='DISPENSED', quantity=30, reference_id=f"PRESCR-{pr_sdh.id}", created_by=u_dist, notes='Dispensed 30 units IFA for Anita Devi')

        # Facility 3 Prescription (Pending Dispensation)
        pr_rc = Prescription.objects.create(consultation=c_rc_1, patient=p_ramesh, doctor=u_doc, facility=rc_a4, status='PENDING')
        PrescriptionItem.objects.create(prescription=pr_rc, medicine=med_met, medicine_name='Metformin 500 mg Tablet', dosage='1-0-1 After Food', frequency='Twice Daily', duration_days=14, quantity=28, status='PENDING')
        PrescriptionItem.objects.create(prescription=pr_rc, medicine=med_aml, medicine_name='Amlodipine 5 mg Tablet', dosage='1-0-0 Morning', frequency='Once Daily', duration_days=14, quantity=14, status='PENDING')

        # Facility 4 Prescription
        pr_vc = Prescription.objects.create(consultation=c_vc_1, patient=p_suresh, doctor=u_vh2_doc, facility=vc_a4_1, status='DISPENSED')
        pi_vc = PrescriptionItem.objects.create(prescription=pr_vc, medicine=med_pcm, medicine_name='Paracetamol 650 mg Tablet', dosage='1-1-1 After Food', frequency='Three Times Daily', duration_days=3, quantity=9, status='DISPENSED')
        b_vc_pcm = MedicineBatch.objects.filter(facility=vc_a4_1, medicine=med_pcm).first()
        if b_vc_pcm:
            b_vc_pcm.quantity = max(0, b_vc_pcm.quantity - 9)
            b_vc_pcm.save()
            InventoryTransaction.objects.create(facility=vc_a4_1, medicine=med_pcm, batch=b_vc_pcm, transaction_type='DISPENSED', quantity=9, reference_id=f"PRESCR-{pr_vc.id}", created_by=u_dist, notes='Dispensed 9 units Paracetamol for Suresh Patil')

        # 12. LAB ORDERS & RESULTS ACROSS ALL FACILITIES
        # Facility 1 Lab Order
        lo_dh = LabOrder.objects.create(consultation=c_dh_1, patient=p_dh_2, doctor=u_dh_doc, facility=hosp_a, test_master=lt_lipid, status='VERIFIED')
        LabSample.objects.create(lab_order=lo_dh, sample_type='Blood', sample_code='SMP-DH-001', collected_by=u_dh_lab)
        LabResult.objects.create(lab_order=lo_dh, result_value='245', unit='mg/dL', reference_range='< 200 mg/dL', interpretation_flag='HIGH', verified_by=u_dh_lab, notes='Elevated Total Cholesterol & LDL')

        # Facility 2 Lab Order
        lo_sdh = LabOrder.objects.create(consultation=c_sdh_1, patient=p_anita, doctor=u_sdh_doc, facility=nc_a1, test_master=lt_hb, status='VERIFIED')
        LabSample.objects.create(lab_order=lo_sdh, sample_type='Blood', sample_code='SMP-SDH-001', collected_by=u_sdh_nurse)
        LabResult.objects.create(lab_order=lo_sdh, result_value='10.2', unit='g/dL', reference_range='12.0 - 15.5 g/dL', interpretation_flag='LOW', verified_by=u_sdh_doc, notes='Mild Anemia')

        # Facility 3 Lab Order
        lo_rc = LabOrder.objects.create(consultation=c_rc_1, patient=p_ramesh, doctor=u_doc, facility=rc_a4, test_master=lt_hba1c, status='VERIFIED')
        LabSample.objects.create(lab_order=lo_rc, sample_type='Blood', sample_code='SMP-RC-001', collected_by=u_lab)
        LabResult.objects.create(lab_order=lo_rc, result_value='8.4', unit='%', reference_range='4.0 - 5.6 %', interpretation_flag='HIGH', verified_by=u_lab, notes='Uncontrolled HbA1c')

        # Facility 4 Lab Order
        lo_vc = LabOrder.objects.create(consultation=c_vc_1, patient=p_suresh, doctor=u_vh2_doc, facility=vc_a4_1, test_master=lt_malaria, status='VERIFIED')
        LabSample.objects.create(lab_order=lo_vc, sample_type='Blood', sample_code='SMP-VC-001', collected_by=u_vh2_doc)
        LabResult.objects.create(lab_order=lo_vc, result_value='Negative', unit='Result', reference_range='Negative', interpretation_flag='NORMAL', verified_by=u_vh2_doc, notes='Malaria Pf/Pv antigen negative')

        # 13. SAMPLE MEDICAL DOCUMENTS FOR ALL FACILITIES
        PatientDocument.objects.create(
            patient=p_dh_2, facility=hosp_a, title='12-Lead ECG & Cardiology Scan',
            document_type='MEDICAL_RECORD', file_name='ecg_report_narayana.pdf',
            file_size=310000, mime_type='application/pdf', document_date=today,
            uploaded_by=u_dh_doc, description='12-Lead ECG showing sinus rhythm with LVH voltage criteria.'
        )
        PatientDocument.objects.create(
            patient=p_anita, facility=nc_a1, title='ANC Ultrasonography Report',
            document_type='MEDICAL_RECORD', file_name='anc_ultrasound_anita.pdf',
            file_size=512000, mime_type='application/pdf', document_date=today - datetime.timedelta(days=10),
            uploaded_by=u_sdh_doc, description='Single live intrauterine fetus at 24 weeks gestation.'
        )
        PatientDocument.objects.create(
            patient=p_ramesh, facility=rc_a4, title='Blood Sugar & Lipid Panel Lab Report',
            document_type='LAB_REPORT', file_name='blood_sugar_lipid_panel_ramesh.pdf',
            file_size=245760, mime_type='application/pdf', document_date=today - datetime.timedelta(days=2),
            uploaded_by=u_lab, description='Automated Biochemistry Output: Fasting Glucose 210 mg/dL, HbA1c 8.4% HIGH.'
        )
        PatientDocument.objects.create(
            patient=p_ramesh, facility=rc_a4, title='EHR Doctor Prescription Scan',
            document_type='PRESCRIPTION', file_name='prescription_ramesh_kumar.pdf',
            file_size=184320, mime_type='application/pdf', document_date=today,
            uploaded_by=u_doc, description='Prescribed Metformin 500mg BID and Amlodipine 5mg QD.'
        )
        PatientDocument.objects.create(
            patient=p_suresh, facility=vc_a4_1, title='Primary Clinic Visit Summary',
            document_type='MEDICAL_RECORD', file_name='visit_summary_suresh.pdf',
            file_size=128000, mime_type='application/pdf', document_date=today,
            uploaded_by=u_vh2_doc, description='Rapid malaria & dengue strip test report and paracetamol advice.'
        )

        # 14. CROSS-FACILITY REFERRALS & RESPONSES
        ref_ramesh = Referral.objects.create(
            referral_id='REF-20260903-0001', patient=p_ramesh, visit=v_rc_1, consultation=c_rc_1,
            source_facility=rc_a4, destination_facility=hosp_a, referring_doctor=u_doc,
            reason='Specialist evaluation for uncontrolled hypertension & diabetic review',
            clinical_summary='52/M with BP 148/96, HbA1c 8.4%. Referred for secondary hospital cardiology consult.',
            required_service='Cardiology & Endocrine Review', urgency='HIGH', status='COMPLETED'
        )

        ReferralResponse.objects.create(
            referral=ref_ramesh, hospital_doctor=u_dh_doc,
            specialist_findings='Essential Hypertension with mild ECG changes. Diabetes mellitus uncontrolled.',
            treatment_summary='Continue Metformin 500mg BD. Upgrade Amlodipine to 10mg OD. Added Telmisartan 40mg.',
            return_advice='Patient stable. Return to Rural Clinic A4 for routine follow-up in 14 days.'
        )

        ref_anita = Referral.objects.create(
            referral_id='REF-20260903-0002', patient=p_anita, visit=v_sdh_1, consultation=c_sdh_1,
            source_facility=nc_a1, destination_facility=hosp_a, referring_doctor=u_sdh_doc,
            reason='Obstetric Ultrasound & High Risk ANC Specialist Assessment',
            clinical_summary='30/F, 24 weeks pregnant with mild anemia. Needs detailed anomaly scan.',
            required_service='Obstetric Ultrasonography Hub', urgency='ROUTINE', status='ACCEPTED'
        )

        FollowUp.objects.create(
            patient=p_ramesh, referral=ref_ramesh, visit=ref_ramesh.visit, facility=rc_a4, category='REFERRAL',
            due_date=today + datetime.timedelta(days=14), status='PENDING', notes='Review post-specialist referral response'
        )
        FollowUp.objects.create(
            patient=p_anita, referral=ref_anita, visit=v_sdh_1, facility=nc_a1, category='MATERNAL_ANC',
            due_date=today + datetime.timedelta(days=28), status='PENDING', notes='Next ANC routine checkup'
        )

        # 15. NCD RECORDS FOR ALL FACILITIES
        NCDRecord.objects.create(patient=p_dh_2, facility=hosp_a, hypertension_diagnosed=True, diabetes_diagnosed=False, risk_level='HIGH', control_status='UNCONTROLLED', last_bp='160/102', last_glucose=140, next_followup_due=today + datetime.timedelta(days=7))
        NCDRecord.objects.create(patient=p_sdh_2, facility=nc_a1, hypertension_diagnosed=True, diabetes_diagnosed=False, risk_level='MODERATE', control_status='CONTROLLED', last_bp='134/86', last_glucose=115, next_followup_due=today + datetime.timedelta(days=30))
        NCDRecord.objects.create(patient=p_ramesh, facility=rc_a4, hypertension_diagnosed=True, diabetes_diagnosed=True, risk_level='HIGH', control_status='UNCONTROLLED', last_bp='148/96', last_glucose=185, next_followup_due=today + datetime.timedelta(days=14))
        NCDRecord.objects.create(patient=p_suresh, facility=vc_a4_1, hypertension_diagnosed=True, diabetes_diagnosed=True, risk_level='MODERATE', control_status='CONTROLLED', last_bp='130/84', last_glucose=125, next_followup_due=today + datetime.timedelta(days=30))

        # 16. PUBLIC HEALTH SURVEILLANCE DISEASE CASES
        for fac in facilities_list:
            DiseaseCase.objects.create(
                disease_name='Acute Pyrexia / Suspected Viral Fever', patient=p_ramesh,
                facility=fac, ward=ward_rural, severity='MODERATE', status='CONFIRMED', notes=f'Fever case logged at {fac.facility_name}'
            )

        # 17. OUTREACH & WELLNESS FOR ALL FACILITIES
        for fac in facilities_list:
            OutreachActivity.objects.create(
                facility=fac, ward=fac.ward or ward_rural, activity_type='Slum Household NCD & Fever Survey',
                activity_date=today - datetime.timedelta(days=3), households_covered=50 + fac.id * 10, persons_screened=120 + fac.id * 20, vulnerable_identified=15 + fac.id * 3
            )
            WellnessSession.objects.create(
                facility=fac, session_type='AYUSH Yoga & Meditation', instructor_name='Guru Sri Anand (AYUSH Certified)',
                session_date=today - datetime.timedelta(days=2), venue=f"{fac.facility_name} Courtyard", participants_count=25 + fac.id * 5
            )

        # 18. ARS COMMITTEES & MEETINGS FOR ALL FACILITIES
        for fac in facilities_list:
            ars_m = ARSMeeting.objects.create(
                facility=fac, meeting_date=today - datetime.timedelta(days=10), chairperson_name=f'Ward {fac.ward.ward_number if fac.ward else 12} Corporator',
                attendees_count=8, agenda='Untied Grant allocation for lab reagents & drinking water purifier',
                proceedings_summary='Approved untied funds for essential facility maintenance.', untied_funds_spent_rs=7500.00 + fac.id * 1000, signed_by_chairman=True
            )
            ARSMember.objects.create(facility=fac, name='Sri Ward Representative', designation='Chairman')
            ARSMember.objects.create(facility=fac, name='Medical Officer', designation='Member Secretary')
            ARSActionItem.objects.create(
                meeting=ars_m, task_description='Procure water purifier cartridge & rapid test kits',
                responsible_person='Pharmacist / Facility Admin', due_date=today + datetime.timedelta(days=5), status='IN_PROGRESS'
            )

        # 19. QUALITY CHECKLISTS & BIOMEDICAL WASTE LOGS
        for fac in facilities_list:
            QualityChecklist.objects.create(facility=fac, cleanliness_score=94 + (fac.id % 5), infection_control_passed=True, kayakalpa_audit_status='COMPLIANT', inspected_by=u_dist)
            BiomedicalWasteLog.objects.create(facility=fac, yellow_bag_kg=4.10, red_bag_kg=2.80, white_translucent_sharp_kg=0.80, blue_box_glass_kg=1.90, handed_over_by=u_nurse)

        # 20. INFRASTRUCTURE & BEDS FOR ALL 4 HOSPITALS

        # --- Facility 1: Victoria District Hospital Infrastructure ---
        FacilityOxygenSupply.objects.create(
            facility=hosp_a, oxygen_source='PIPELINE_LIQUID', total_cylinders=80, active_cylinders=65, empty_cylinders=15,
            current_pressure_psi=2400, fill_percentage=94, status='OPTIMAL', notes='Central Liquid Medical Oxygen (LMO) tank & 80-Cylinder manifold backup.'
        )
        FacilityConsumableInventory.objects.create(facility=hosp_a, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=250, min_threshold=50, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=hosp_a, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=180, min_threshold=30, reorder_status='ADEQUATE')
        FacilityMaintenanceTicket.objects.create(
            facility=hosp_a, ticket_number='MAINT-DH-001', category='EQUIPMENT', equipment_or_area='ICU Ventilator #4 Oxygen Sensor',
            priority='HIGH', description='Oxygen sensor calibration warning on ICU Ventilator #4.', reported_by='Dr. Vikram Seth',
            assigned_technician='Biomedical Engineering Division', status='IN_PROGRESS'
        )
        FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='GENERAL_OBSERVATION', total_beds=400, occupied_beds=320, cleaning_in_progress=20, under_maintenance=10, notes='General Medical & Surgical Wards.')
        FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='ICU_CRITICAL', total_beds=50, occupied_beds=42, cleaning_in_progress=3, under_maintenance=1, notes='Intensive Care Unit with vent support.')
        FacilityBedCapacity.objects.create(facility=hosp_a, bed_category='OXYGEN_SUPPORTED', total_beds=200, occupied_beds=160, cleaning_in_progress=10, under_maintenance=5, notes='High Flow Oxygen Wards.')
        FacilityBedAllocation.objects.create(facility=hosp_a, bed_number='BED-ICU-05', bed_category='ICU_CRITICAL', patient=p_dh_2, patient_name='Narayana Swamy (68/M)', attending_doctor='Dr. Vikram Seth', status='OCCUPIED')

        # --- Facility 2: Indiranagar Sub-District Hospital Infrastructure ---
        FacilityOxygenSupply.objects.create(
            facility=nc_a1, oxygen_source='CONCENTRATOR', total_cylinders=20, active_cylinders=16, empty_cylinders=4,
            current_pressure_psi=1800, fill_percentage=82, status='OPTIMAL', notes='4x 10LPM Oxygen Concentrators + 20 Cylinder manifold.'
        )
        FacilityConsumableInventory.objects.create(facility=nc_a1, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=90, min_threshold=20, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=nc_a1, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=45, min_threshold=15, reorder_status='ADEQUATE')
        FacilityMaintenanceTicket.objects.create(
            facility=nc_a1, ticket_number='MAINT-SDH-001', category='ELECTRICAL', equipment_or_area='Maternal Ward Solar Water Heater Inverter',
            priority='MEDIUM', description='Water heater solar panel sensor service required.', reported_by='Sister Kavitha',
            assigned_technician='BBMP Electrical Works', status='LOGGED'
        )
        FacilityBedCapacity.objects.create(facility=nc_a1, bed_category='GENERAL_OBSERVATION', total_beds=30, occupied_beds=20, cleaning_in_progress=2, under_maintenance=1, notes='General Observation & Post-natal ward.')
        FacilityBedCapacity.objects.create(facility=nc_a1, bed_category='MATERNITY_DELIVERY', total_beds=15, occupied_beds=10, cleaning_in_progress=1, under_maintenance=0, notes='Labor Room & ANC High Risk Beds.')
        FacilityBedCapacity.objects.create(facility=nc_a1, bed_category='OXYGEN_SUPPORTED', total_beds=15, occupied_beds=8, cleaning_in_progress=1, under_maintenance=0, notes='Oxygen Concentrator Supported Beds.')
        FacilityBedAllocation.objects.create(facility=nc_a1, bed_number='BED-MAT-02', bed_category='MATERNITY_DELIVERY', patient=p_anita, patient_name='Anita Devi (30/F)', attending_doctor='Dr. Asha Patil', status='OCCUPIED')

        # --- Facility 3: Varthur Rural Primary Clinic A4 Infrastructure ---
        FacilityOxygenSupply.objects.create(
            facility=rc_a4, oxygen_source='CYLINDER_MANIFOLD', total_cylinders=12, active_cylinders=9, empty_cylinders=3,
            current_pressure_psi=1850, fill_percentage=88, status='OPTIMAL', notes='12-Cylinder B-Type Manifold system.'
        )
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=45, min_threshold=15, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Sodium Hypochlorite 5% (Disinfectant)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=20, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=12, min_threshold=15, reorder_status='LOW_STOCK')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Biohazard Waste Bags (Yellow 50L)', category='INFECTION_CONTROL', unit_of_measure='Packs (100s)', current_stock=8, min_threshold=5, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Disposable Nitrile Gloves (M)', category='PERSONAL_PROTECTION', unit_of_measure='Boxes (100s)', current_stock=25, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=rc_a4, item_name='Surgical Face Masks 3-Ply', category='PERSONAL_PROTECTION', unit_of_measure='Boxes (50s)', current_stock=30, min_threshold=10, reorder_status='ADEQUATE')
        FacilityMaintenanceTicket.objects.create(
            facility=rc_a4, ticket_number='MAINT-RC-001', category='ELECTRICAL', equipment_or_area='Main OPD Solar UPS Battery Backup',
            priority='HIGH', description='Solar UPS inverter battery overload warning.', reported_by='Sister Priya',
            assigned_technician='BBMP Electrical Team', status='IN_PROGRESS'
        )
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='GENERAL_OBSERVATION', total_beds=6, occupied_beds=2, cleaning_in_progress=1, under_maintenance=0, notes='General OPD observation beds.')
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='EMERGENCY_TRIAGE', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Emergency resuscitation bay bed.')
        FacilityBedCapacity.objects.create(facility=rc_a4, bed_category='OXYGEN_SUPPORTED', total_beds=2, occupied_beds=1, cleaning_in_progress=0, under_maintenance=0, notes='Oxygen manifold high-care bed.')
        FacilityBedAllocation.objects.create(facility=rc_a4, bed_number='BED-OBS-01', bed_category='GENERAL_OBSERVATION', patient=p_ramesh, patient_name='Ramesh Kumar (52/M)', attending_doctor='Dr. Rajesh Kumar', status='OCCUPIED')

        # --- Facility 4: Gunjur Village Satellite Clinic Infrastructure ---
        FacilityOxygenSupply.objects.create(
            facility=vc_a4_1, oxygen_source='CYLINDER_MANIFOLD', total_cylinders=4, active_cylinders=3, empty_cylinders=1,
            current_pressure_psi=1500, fill_percentage=75, status='ADEQUATE', notes='4x D-Type Oxygen Cylinders for emergency transport.'
        )
        FacilityConsumableInventory.objects.create(facility=vc_a4_1, item_name='Floor Cleaning Solution (Lysol / Phenyl)', category='CLEANING_SANITATION', unit_of_measure='Litres', current_stock=25, min_threshold=10, reorder_status='ADEQUATE')
        FacilityConsumableInventory.objects.create(facility=vc_a4_1, item_name='Hand Sanitizer (Alcohol Rub 70%)', category='INFECTION_CONTROL', unit_of_measure='Bottles (500ml)', current_stock=10, min_threshold=8, reorder_status='ADEQUATE')
        FacilityMaintenanceTicket.objects.create(
            facility=vc_a4_1, ticket_number='MAINT-VC-001', category='PLUMBING', equipment_or_area='Doctor Handwash Station Tap',
            priority='LOW', description='Tap washer replacement needed.', reported_by='Dr. Suresh V.',
            assigned_technician='Local Village Sanitation Team', status='LOGGED'
        )
        FacilityBedCapacity.objects.create(facility=vc_a4_1, bed_category='GENERAL_OBSERVATION', total_beds=4, occupied_beds=1, cleaning_in_progress=1, under_maintenance=0, notes='Satellite observation cots.')
        FacilityBedAllocation.objects.create(facility=vc_a4_1, bed_number='BED-COT-01', bed_category='GENERAL_OBSERVATION', patient=p_suresh, patient_name='Suresh Patil (65/M)', attending_doctor='Dr. Suresh V.', status='OCCUPIED')

        # 21. DEMO ALERTS FOR ALL FACILITIES
        for fac in facilities_list:
            Alert.objects.create(
                alert_type='LOW_STOCK', severity='MEDIUM', facility=fac,
                title=f'Low Stock: Amlodipine 5mg at {fac.facility_name}',
                description='Current batch quantity is 45 units (below reorder threshold of 100 units).', status='NEW'
            )
            Alert.objects.create(
                alert_type='EXPIRED', severity='HIGH', facility=fac,
                title=f'Expired Stock: Amoxicillin 500mg at {fac.facility_name}',
                description='Batch AMX-OLD expired 10 days ago (30 units remaining).', status='NEW'
            )

        # 22. COMPLIANCE MATRIX & INTEGRATIONS
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

        # Audit Entry
        AuditLog.objects.create(user=u_dist, username_snapshot='district', action='SYSTEM_SEED_DEMO', facility=hosp_a, details='Demo database seeded successfully with realistic EMR data, date-based queues, inventory, beds, and documents for ALL 4 healthcare facilities.')

        self.stdout.write(self.style.SUCCESS("Demo dataset successfully seeded for ALL 4 healthcare facilities! All hospitals now have proper mapping, patients, visits, inventory, beds, and documents."))

"""
Namma Clinic - Complete Demo & Master Data Seeder
Populates:
1. Geography (State, Districts, Zones, Wards)
2. Facilities, Departments, Bed Capacities, Oxygen, Consumables
3. Role & Permission Catalogue (Roles, Permissions, RolePermissions)
4. Staff & Users:
   - All Operational Roles from Login.tsx:
     e2e_compounder_user, e2e_nurse_user, e2e_doctor_user, e2e_lab_user,
     e2e_pharmacist_user, e2e_inventory_user, e2e_dual_user, e2e_admin_user, e2e_dho_user
   - Legacy Dev Accounts:
     localdoc, localnurse, localpharm, locallab, localadmin, localdistrict, testadmin
   - README & DEMO_RUNBOOK Accounts:
     admin, district, hospital, varthur_admin, doctor, nurse, lab, pharmacy,
     dh_admin, sdh_admin, vh1_admin, vh2_admin, dh_doctor, sdh_doctor, vh1_doctor, vh2_doctor,
     sdh_nurse, dh_nurse, dh_lab, dh_pharmacy, frontdesk, compounder, inventory
   - Dual-Role properly configured with 2 StaffRoleAssignments on 1 StaffProfile
5. Essential Medicines, Batches, Inventory Ledgers & Transactions
6. Diagnostic Tests & Catalogues
7. Patients (NC-DEMO-001 to NC-DEMO-010, plus Lakshmi Devi NC-2026-00892)
8. Clinical Encounters: Visits, Tokens, Triage Vitals, Consultations, Diagnoses, Prescriptions, Lab Orders, Lab Results
"""
import os
import sys
import datetime
from decimal import Decimal

# Ensure backend path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DATABASE_ENGINE', 'sqlite')

import django
django.setup()

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import (
    Facility, FacilityRelationship, Department, FacilityOxygenSupply,
    FacilityConsumableInventory, FacilityMaintenanceTicket,
    FacilityBedCapacity, FacilityBedAllocation
)
from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment, StaffStatusChoices
)
from apps.accounts.services import seed_roles_and_permissions
from apps.patients.models import Patient, Household, PatientDocument
from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, DiagnosisMaster
from apps.laboratory.models import LabTestMaster, LabToken, LabOrder, LabSample, LabResult
from apps.pharmacy.models import (
    MedicineMaster, Vendor, MedicineBatch, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GoodsReceiptItem, InventoryTransaction, Dispensation,
    DispensationItem, InventoryLedger, PatientCounselling
)
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.telemedicine.models import Teleconsultation
from apps.alerts.models import Alert
from apps.compliance.models import ComplianceItem
from apps.integrations.models import IntegrationConfiguration
from apps.audit.models import AuditLog

User = get_user_model()

def seed_all():
    print("=" * 70)
    print("NAMMA CLINIC - SEEDING COMPLETE DEMO DATASET")
    print("=" * 70)

    # 1. Seed Roles & Permissions Catalogue
    print("\n[1/7] Seeding Role & Permission catalogue...")
    res = seed_roles_and_permissions()
    print(f"  -> {res['summary']}")

    today = datetime.date.today()
    now = timezone.now()

    with transaction.atomic():
        # 2. Geography
        print("\n[2/7] Seeding Geography...")
        karnataka, _ = State.objects.get_or_create(code='KA', defaults={'name': 'Karnataka'})
        dist_central, _ = District.objects.get_or_create(code='KA-BU', defaults={'name': 'BBMP Central (Bengaluru Urban)', 'state': karnataka})
        dist_rural, _ = District.objects.get_or_create(code='KA-BR', defaults={'name': 'Bengaluru Rural', 'state': karnataka})

        zone_east, _ = Zone.objects.get_or_create(code='Z-EAST', defaults={'district': dist_central, 'name': 'East Zone'})
        zone_south, _ = Zone.objects.get_or_create(code='Z-SOUTH', defaults={'district': dist_central, 'name': 'South Zone'})
        zone_west, _ = Zone.objects.get_or_create(code='Z-WEST', defaults={'district': dist_central, 'name': 'West Zone'})
        zone_hoskote, _ = Zone.objects.get_or_create(code='Z-HOS', defaults={'district': dist_rural, 'name': 'Hoskote Zone'})

        ward12, _ = Ward.objects.get_or_create(zone=zone_east, ward_number=12, defaults={'name': 'Indiranagar Ward', 'population': 22000, 'slum_population': 6500})
        ward14, _ = Ward.objects.get_or_create(zone=zone_east, ward_number=14, defaults={'name': 'Ulsoor Ward', 'population': 19500, 'slum_population': 5200})
        ward45, _ = Ward.objects.get_or_create(zone=zone_south, ward_number=45, defaults={'name': 'Jayanagar Ward', 'population': 24000, 'slum_population': 4800})
        ward68, _ = Ward.objects.get_or_create(zone=zone_west, ward_number=68, defaults={'name': 'Laggere Ward', 'population': 35000, 'slum_population': 16000})
        ward_rural, _ = Ward.objects.get_or_create(zone=zone_hoskote, ward_number=1, defaults={'name': 'Varthur Rural Ward', 'population': 18000, 'slum_population': 7200})

        # 3. Facilities
        print("\n[3/7] Seeding Facilities & Departments...")
        fac_hosp, _ = Facility.objects.get_or_create(
            id=110,
            defaults={
                'facility_code': 'HOSP-DIST-01',
                'facility_name': 'Victoria District General Hospital & Specialist Center',
                'facility_type': 'MAIN_HOSPITAL',
                'state': karnataka,
                'district': dist_central,
                'zone': zone_east,
                'ward': ward12,
                'address': 'Fort Road, Near City Market, Bengaluru',
                'phone': '080-26701150',
                'latitude': Decimal('12.9629'),
                'longitude': Decimal('77.5753'),
                'bed_capacity': 250,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )

        fac_sdh, _ = Facility.objects.get_or_create(
            id=111,
            defaults={
                'facility_code': 'HOSP-SUB-01',
                'facility_name': 'CV Raman General Sub-District Hospital',
                'facility_type': 'SECONDARY_HOSPITAL',
                'state': karnataka,
                'district': dist_central,
                'zone': zone_east,
                'ward': ward14,
                'address': '80 Feet Road, Indiranagar, Bengaluru',
                'phone': '080-25281245',
                'latitude': Decimal('12.9784'),
                'longitude': Decimal('77.6408'),
                'bed_capacity': 100,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )

        fac_rc, _ = Facility.objects.get_or_create(
            id=112,
            defaults={
                'facility_code': 'RC-A4-01',
                'facility_name': 'Varthur Rural Primary Clinic A4',
                'facility_type': 'RURAL_CLINIC',
                'state': karnataka,
                'district': dist_rural,
                'zone': zone_hoskote,
                'ward': ward_rural,
                'address': 'Main Road, Varthur Village, Bengaluru',
                'phone': '080-28538200',
                'latitude': Decimal('12.9406'),
                'longitude': Decimal('77.7466'),
                'bed_capacity': 12,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )

        fac_vc, _ = Facility.objects.get_or_create(
            id=113,
            defaults={
                'facility_code': 'VC-A4-01',
                'facility_name': 'Gunjur Village Satellite Clinic',
                'facility_type': 'VILLAGE_CLINIC',
                'state': karnataka,
                'district': dist_rural,
                'zone': zone_hoskote,
                'ward': ward_rural,
                'address': 'Gunjur Palya, Near Lake, Bengaluru',
                'phone': '080-28538299',
                'latitude': Decimal('12.9250'),
                'longitude': Decimal('77.7420'),
                'bed_capacity': 4,
                'emergency_available': False,
                'lab_available': False,
                'pharmacy_available': True
            }
        )

        fac_local, _ = Facility.objects.get_or_create(
            id=1,
            defaults={
                'facility_code': 'PHC-LOCAL-01',
                'facility_name': 'Namma Clinic Local PHC',
                'facility_type': 'NAMMA_CLINIC',
                'state': karnataka,
                'district': dist_central,
                'zone': zone_west,
                'ward': ward68,
                'address': 'Laggere Slum Cluster, Ward 68, Bengaluru',
                'phone': '080-28390001',
                'latitude': Decimal('13.0112'),
                'longitude': Decimal('77.5240'),
                'bed_capacity': 10,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )

        # Legacy convenience IDs
        Facility.objects.get_or_create(
            id=66,
            defaults={
                'facility_code': 'HOSP-KC-01',
                'facility_name': 'KC General Secondary Hospital',
                'facility_type': 'SECONDARY_HOSPITAL',
                'state': karnataka,
                'district': dist_central,
                'zone': zone_east,
                'ward': ward14,
                'bed_capacity': 120,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )
        Facility.objects.get_or_create(
            id=68,
            defaults={
                'facility_code': 'NC-LAG-01',
                'facility_name': 'Namma Clinic Laggere Urban Health Centre',
                'facility_type': 'NAMMA_CLINIC',
                'state': karnataka,
                'district': dist_central,
                'zone': zone_west,
                'ward': ward68,
                'bed_capacity': 10,
                'emergency_available': True,
                'lab_available': True,
                'pharmacy_available': True
            }
        )

        # Facility Relationships
        FacilityRelationship.objects.get_or_create(source_facility=fac_vc, destination_facility=fac_rc, defaults={'relationship_type': 'REFERRAL', 'service': 'Village Primary Referral', 'priority': 'PRIMARY', 'distance_km': 2.5})
        FacilityRelationship.objects.get_or_create(source_facility=fac_rc, destination_facility=fac_sdh, defaults={'relationship_type': 'REFERRAL', 'service': 'Sub-District Secondary Care', 'priority': 'PRIMARY', 'distance_km': 4.2})
        FacilityRelationship.objects.get_or_create(source_facility=fac_sdh, destination_facility=fac_hosp, defaults={'relationship_type': 'SPECIALIST', 'service': 'District Cardiology & Tertiary Surgery', 'priority': 'EMERGENCY', 'distance_km': 5.0})
        FacilityRelationship.objects.get_or_create(source_facility=fac_local, destination_facility=fac_hosp, defaults={'relationship_type': 'SPECIALIST', 'service': 'Tertiary Specialty Referral', 'priority': 'EMERGENCY', 'distance_km': 6.0})

        # Departments
        for fac in [fac_hosp, fac_sdh, fac_rc, fac_vc, fac_local]:
            Department.objects.get_or_create(facility=fac, code='OPD', defaults={'name': 'General Outpatient Department', 'is_active': True})
            Department.objects.get_or_create(facility=fac, code='PHARM', defaults={'name': 'Dispensary & Pharmacy', 'is_active': True})
            Department.objects.get_or_create(facility=fac, code='LAB', defaults={'name': 'Clinical Diagnostics & Lab', 'is_active': True})

        # 4. Create Users & Staff Profiles
        print("\n[4/7] Seeding Users, StaffProfiles, and StaffRoleAssignments...")

        roles_dict = {r.code: r for r in RoleMaster.objects.all()}

        users_config = [
            # Super Admin
            ('admin', 'admin123', 'System Administrator', 'admin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_hosp, True, False),
            
            # Login.tsx Core Operational Roles
            ('e2e_compounder_user', 'Password123!', 'Anand Murthy (Front Desk)', 'frontdesk@nammaclinic.gov.in', 'FRONT_DESK_OFFICER', fac_local, False, False),
            ('e2e_nurse_user', 'Password123!', 'Sister Kavitha Rani (Nurse)', 'nurse.kavitha@nammaclinic.gov.in', 'NURSE', fac_local, False, False),
            ('e2e_doctor_user', 'Password123!', 'Dr. Sunil Kumar (MO)', 'doc.sunil@nammaclinic.gov.in', 'DOCTOR', fac_local, False, False),
            ('e2e_lab_user', 'Password123!', 'Chethan M (Lab Tech)', 'lab.chethan@nammaclinic.gov.in', 'LAB_TECHNICIAN', fac_local, False, False),
            ('e2e_pharmacist_user', 'Password123!', 'Manjunath G (Pharmacist)', 'pharm.manju@nammaclinic.gov.in', 'PHARMACIST', fac_local, False, False),
            ('e2e_inventory_user', 'Password123!', 'Ravi Shankar (Inventory Manager)', 'inv.ravi@nammaclinic.gov.in', 'INVENTORY', fac_local, False, False),
            ('e2e_dual_user', 'Password123!', 'Pooja Hegde (Dual Inv+Pharm)', 'dual.pooja@nammaclinic.gov.in', 'INVENTORY', fac_local, False, True),
            ('e2e_admin_user', 'Password123!', 'Dr. K. V. Sharma (Hospital Admin)', 'admin.sharma@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_local, False, False),
            ('e2e_dho_user', 'Password123!', 'Dr. Sunita Rao (District Health Officer)', 'dho.sunita@nammaclinic.gov.in', 'DISTRICT_OFFICER', None, False, False),

            # Standard Operational Accounts from DEMO_RUNBOOK & README
            ('doctor', 'doctor123', 'Dr. Rajesh Kumar (Medical Officer)', 'doctor@nammaclinic.gov.in', 'DOCTOR', fac_rc, False, False),
            ('nurse', 'nurse123', 'Sister Priya Nair (Staff Nurse)', 'nurse@nammaclinic.gov.in', 'NURSE', fac_rc, False, False),
            ('pharmacy', 'pharmacy123', 'Mrs. Lakshmi Devi (Pharmacist)', 'pharmacy@nammaclinic.gov.in', 'PHARMACIST', fac_rc, False, False),
            ('lab', 'lab123', 'Mr. Suresh Gowda (Lab Tech)', 'lab@nammaclinic.gov.in', 'LAB_TECHNICIAN', fac_rc, False, False),
            ('district', 'district123', 'Dr. Sunita Rao (District Health Officer)', 'district@nammaclinic.gov.in', 'DISTRICT_OFFICER', None, False, False),
            ('hospital', 'hospital123', 'Dr. K. V. Sharma (Hospital Admin)', 'hospital@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_hosp, False, False),
            ('varthur_admin', 'varthur123', 'Dr. Anita Desai (Varthur Clinic Admin)', 'varthur@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_rc, False, False),
            ('frontdesk', 'frontdesk123', 'Front Desk Officer Laggere', 'frontdesk.lag@nammaclinic.gov.in', 'FRONT_DESK_OFFICER', fac_local, False, False),
            ('compounder', 'compounder123', 'Front Desk Officer Varthur', 'compounder@nammaclinic.gov.in', 'FRONT_DESK_OFFICER', fac_rc, False, False),
            ('inventory', 'inventory123', 'Central Inventory Officer', 'inventory@nammaclinic.gov.in', 'INVENTORY', fac_hosp, False, False),

            # Multi-facility staff
            ('dh_admin', 'dh123', 'Dr. K. V. Sharma (DH Supt)', 'dh_admin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_hosp, False, False),
            ('sdh_admin', 'sdh123', 'Dr. Meena Swamy (SDH Admin)', 'sdh_admin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_sdh, False, False),
            ('vh1_admin', 'vh1123', 'Dr. Ramesh Rao (VH1 Admin)', 'vh1_admin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_rc, False, False),
            ('vh2_admin', 'vh2123', 'Dr. Anand Kumar (VH2 Admin)', 'vh2_admin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_vc, False, False),
            ('dh_doctor', 'dhdoc123', 'Dr. Vikram Seth (Cardiologist)', 'dh_doctor@nammaclinic.gov.in', 'DOCTOR', fac_hosp, False, False),
            ('sdh_doctor', 'sdhdoc123', 'Dr. Asha Patil (SDH Physician)', 'sdh_doctor@nammaclinic.gov.in', 'DOCTOR', fac_sdh, False, False),
            ('vh1_doctor', 'vh1doc123', 'Dr. Rajesh Kumar (VH1 MO)', 'vh1_doctor@nammaclinic.gov.in', 'DOCTOR', fac_rc, False, False),
            ('vh2_doctor', 'vh2doc123', 'Dr. Suresh V (VH2 MO)', 'vh2_doctor@nammaclinic.gov.in', 'DOCTOR', fac_vc, False, False),
            ('sdh_nurse', 'sdhnurse123', 'Sister Kavitha R', 'sdh_nurse@nammaclinic.gov.in', 'NURSE', fac_sdh, False, False),
            ('dh_nurse', 'dhnurse123', 'Sister Mary Joseph', 'dh_nurse@nammaclinic.gov.in', 'NURSE', fac_hosp, False, False),
            ('dh_lab', 'dhlab123', 'Mr. Chethan M', 'dh_lab@nammaclinic.gov.in', 'LAB_TECHNICIAN', fac_hosp, False, False),
            ('dh_pharmacy', 'dhpharm123', 'Mr. Mahesh Babu', 'dh_pharmacy@nammaclinic.gov.in', 'PHARMACIST', fac_hosp, False, False),

            # Legacy Dev Accounts
            ('localdoc', 'DoctorPassword123!', 'Dr. Sunil Kumar', 'localdoc@nammaclinic.gov.in', 'DOCTOR', fac_local, False, False),
            ('localnurse', 'NursePassword123!', 'Sister Kavitha Rani', 'localnurse@nammaclinic.gov.in', 'NURSE', fac_local, False, False),
            ('localpharm', 'PharmPassword123!', 'Mr. Manjunath G', 'localpharm@nammaclinic.gov.in', 'PHARMACIST', fac_local, False, False),
            ('locallab', 'LabPassword123!', 'Mr. Chethan M', 'locallab@nammaclinic.gov.in', 'LAB_TECHNICIAN', fac_local, False, False),
            ('localadmin', 'AdminPassword123!', 'Admin Official', 'localadmin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_local, False, False),
            ('localdistrict', 'DistrictPassword123!', 'Dr. District Health Officer', 'localdistrict@nammaclinic.gov.in', 'DISTRICT_OFFICER', None, False, False),
            ('testadmin', 'AdminPassword123!', 'Hospital Administrator', 'testadmin@nammaclinic.gov.in', 'HOSPITAL_ADMIN', fac_local, False, False),
        ]

        seeded_users = {}
        for uname, pwd, fname, email, rcode, fac, is_su, is_dual in users_config:
            rm = roles_dict.get(rcode)
            if not rm:
                continue

            name_parts = fname.split()
            first_name = name_parts[0] if name_parts else uname
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            p, _ = Person.objects.get_or_create(
                aadhaar_hash=f"AADHAAR-HASH-{uname.upper()}",
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'gender': 'MALE' if 'Sister' not in fname and 'Mrs' not in fname and 'Pooja' not in fname else 'FEMALE',
                    'date_of_birth': datetime.date(1985, 5, 15),
                    'phone_number': '9845012345'
                }
            )

            dept = Department.objects.filter(facility=fac, code='OPD').first() if fac else None
            staff, _ = StaffProfile.objects.get_or_create(
                employee_id=f"EMP-{uname.upper()[:15]}",
                defaults={
                    'person': p,
                    'designation': rm.name,
                    'status': StaffStatusChoices.ACTIVE,
                    'department': dept
                }
            )

            u = User.objects.filter(username=uname).first()
            if not u:
                u = User.objects.create_user(
                    username=uname,
                    email=email,
                    password=pwd,
                    full_name=fname,
                    role=rcode,
                    assigned_facility=fac,
                    assigned_district=dist_central if rcode == 'DISTRICT_OFFICER' else (fac.district if fac else dist_central),
                    staff_profile=staff
                )
            else:
                u.set_password(pwd)
                u.full_name = fname
                u.email = email
                u.role = rcode
                u.assigned_facility = fac
                u.assigned_district = dist_central if rcode == 'DISTRICT_OFFICER' else (fac.district if fac else dist_central)
                u.staff_profile = staff
                u.is_active = True
                u.save()

            if is_su:
                u.is_staff = True
                u.is_superuser = True
                u.save()

            StaffRoleAssignment.objects.filter(staff=staff).update(is_active=False)
            StaffRoleAssignment.objects.create(
                staff=staff,
                role=rm,
                facility=fac,
                effective_from=today - datetime.timedelta(days=30),
                is_active=True
            )

            if is_dual:
                rm_pharm = roles_dict.get('PHARMACIST')
                if rm_pharm:
                    StaffRoleAssignment.objects.create(
                        staff=staff,
                        role=rm_pharm,
                        facility=fac,
                        effective_from=today - datetime.timedelta(days=30),
                        is_active=True
                    )

            seeded_users[uname] = u
            print(f"  [USER] {uname:<20} | Role: {rcode:<22} | Facility: {fac.facility_code if fac else 'ALL DISTRICT'}")

        # 5. Medicines, Batches, Inventory Ledgers
        print("\n[5/7] Seeding Medicines, Batches, and Inventory Ledgers...")
        v_ksmscl, _ = Vendor.objects.get_or_create(vendor_name='KSMSCL (Karnataka State Medical Supplies Corp Ltd)', defaults={'contact_person': 'Mr. R. K. Hegde', 'phone': '080-22345678', 'email': 'procurement@ksmscl.in', 'address': 'Anand Rao Circle, Bengaluru', 'gst_number': '29AAACK1234F1Z5', 'status': 'ACTIVE'})
        v_kapl, _ = Vendor.objects.get_or_create(vendor_name='Karnataka Antibiotics & Pharmaceuticals Ltd (KAPL)', defaults={'contact_person': 'Dr. S. M. Patel', 'phone': '080-28392555', 'email': 'sales@kaplindia.com', 'address': 'Peenya Industrial Area, Bengaluru', 'gst_number': '29AAACK5678F1Z9', 'status': 'ACTIVE'})

        med_list = [
            ("Metformin HCl", "Glycomet", "500 mg", "Tablet", "Anti-Diabetic", 50, 100),
            ("Amlodipine Besylate", "Amlopres", "5 mg", "Tablet", "Anti-Hypertensive", 50, 100),
            ("Paracetamol", "Dolo", "650 mg", "Tablet", "Analgesic / Antipyretic", 100, 200),
            ("Amoxicillin Trihydrate", "Mox", "500 mg", "Capsule", "Antibiotic", 50, 100),
            ("Telmisartan", "Telma", "40 mg", "Tablet", "Anti-Hypertensive", 40, 80),
            ("Cetirizine HCl", "Cetzine", "10 mg", "Tablet", "Antihistamine", 30, 60),
            ("ORS Sachet", "Electral", "21.8 g", "Sachet", "Electrolytes", 40, 80),
            ("Iron & Folic Acid", "IFA Red", "100mg Fe + 500mcg FA", "Tablet", "General Health", 75, 150)
        ]

        seeded_meds = {}
        for gname, bname, strength, form, cat, min_s, reorder in med_list:
            m, _ = MedicineMaster.objects.get_or_create(
                generic_name=gname,
                defaults={'brand_name': bname, 'strength': strength, 'dosage_form': form, 'category': cat, 'minimum_stock': min_s, 'reorder_level': reorder}
            )
            seeded_meds[gname] = m

        u_pharm = seeded_users.get('pharmacy') or seeded_users.get('e2e_pharmacist_user')
        stf_pharm = u_pharm.staff_profile if u_pharm else None

        seeded_batches = {}
        for fac in [fac_local, fac_rc, fac_hosp, fac_sdh]:
            for gname, med_obj in seeded_meds.items():
                batch_code = f"BAT-{fac.facility_code[:4]}-{med_obj.id}-2026A"
                exp = today + datetime.timedelta(days=365)
                mfg = today - datetime.timedelta(days=60)
                qty = 500

                batch, _ = MedicineBatch.objects.get_or_create(
                    facility=fac,
                    batch_number=batch_code,
                    defaults={
                        'medicine': med_obj,
                        'vendor': v_ksmscl,
                        'supplier': v_ksmscl.vendor_name,
                        'mfg_date': mfg,
                        'expiry_date': exp,
                        'unit_cost': Decimal("1.25"),
                        'available_quantity': qty,
                        'quantity': qty,
                        'status': 'AVAILABLE'
                    }
                )
                seeded_batches[(fac.id, med_obj.id)] = batch

                if not InventoryLedger.objects.filter(batch=batch, transaction_type='PURCHASE_RECEIPT').exists():
                    InventoryLedger.objects.create(
                        batch=batch,
                        facility=fac,
                        performed_by_staff=stf_pharm or seeded_users['doctor'].staff_profile,
                        transaction_type='PURCHASE_RECEIPT',
                        quantity_delta=qty,
                        balance_after=qty,
                        remarks=f"Initial stock replenishment for {med_obj.generic_name} at {fac.facility_name}"
                    )

        # 6. Lab Test Masters
        print("\n[6/7] Seeding Lab Diagnostics Masters...")
        lt_cbc, _ = LabTestMaster.objects.get_or_create(code='L-CBC', defaults={'name': 'Complete Blood Count (CBC)', 'category': 'Hematology', 'reference_range': 'WBC 4000-11000 /uL', 'unit': '/uL'})
        lt_hba1c, _ = LabTestMaster.objects.get_or_create(code='L-HBA1C', defaults={'name': 'HbA1c Glycated Hemoglobin', 'category': 'Diabetes', 'reference_range': '4.0 - 5.6 %', 'unit': '%'})
        lt_rbg, _ = LabTestMaster.objects.get_or_create(code='L-RBG', defaults={'name': 'Random Blood Glucose (RBG)', 'category': 'Diabetes', 'reference_range': '70 - 140 mg/dL', 'unit': 'mg/dL'})
        lt_dengue, _ = LabTestMaster.objects.get_or_create(code='L-DENGUE', defaults={'name': 'Dengue NS1 Antigen Rapid Card', 'category': 'Serology', 'reference_range': 'Negative', 'unit': 'Result'})
        lt_malaria, _ = LabTestMaster.objects.get_or_create(code='L-MALARIA', defaults={'name': 'Malaria Antigen (Pf/Pv) Strip', 'category': 'Serology', 'reference_range': 'Negative', 'unit': 'Result'})
        lt_lipid, _ = LabTestMaster.objects.get_or_create(code='L-LIPID', defaults={'name': 'Lipid Profile', 'category': 'Biochemistry', 'reference_range': '< 200 mg/dL', 'unit': 'mg/dL'})

        # 7. Patients & Clinical Journeys
        print("\n[7/7] Seeding Demo Patients & Operational Clinical Journeys...")

        # Purge existing operational tables safely
        for m in [DispensationItem, Dispensation, PatientCounselling, PrescriptionItem, Prescription,
                  LabResult, LabSample, LabOrder, LabToken, Consultation, TriageVitals, Triage,
                  Token, VisitStatusHistory, Visit, PatientDocument, Patient]:
            m.objects.all().delete()

        patients_data = [
            ("NC-DEMO-001", "Arun Kumar", 34, "MALE", "9800010001", "91-4829-1029-0001", "Slum Resident BPL", "Acute Febrile Illness", fac_local, ward68, dist_central),
            ("NC-DEMO-002", "Priya Nair", 28, "FEMALE", "9800010002", "91-4829-1029-0002", "General", "Cough & Upper Respiratory Infection", fac_local, ward68, dist_central),
            ("NC-DEMO-003", "Ravi Shankar", 45, "MALE", "9800010003", "91-4829-1029-0003", "Low Income", "Essential Hypertension & Headache", fac_local, ward68, dist_central),
            ("NC-DEMO-004", "Meena Devi", 52, "FEMALE", "9800010004", "91-4829-1029-0004", "Senior Citizen", "Type 2 Diabetes & Dyspepsia", fac_local, ward68, dist_central),
            ("NC-DEMO-005", "Suresh Babu", 39, "MALE", "9800010005", "91-4829-1029-0005", "General", "Generalized Weakness & Anemia", fac_local, ward68, dist_central),
            ("NC-DEMO-006", "Kavya Reddy", 31, "FEMALE", "9800010006", "91-4829-1029-0006", "General", "Allergic Dermatitis & Skin Rash", fac_rc, ward_rural, dist_rural),
            ("NC-DEMO-007", "Manoj Kumar", 42, "MALE", "9800010007", "91-4829-1029-0007", "Slum Resident", "Bilateral Knee Osteoarthritis", fac_rc, ward_rural, dist_rural),
            ("NC-DEMO-008", "Anitha Rao", 36, "FEMALE", "9800010008", "91-4829-1029-0008", "General", "Hypertension Routine Refill", fac_rc, ward_rural, dist_rural),
            ("NC-DEMO-009", "Sanjay Patel", 58, "MALE", "9800010009", "91-4829-1029-0009", "High Risk", "Suspected Dengue Fever with Thrombocytopenia", fac_hosp, ward12, dist_central),
            ("NC-DEMO-010", "Deepa Menon", 49, "FEMALE", "9800010010", "91-4829-1029-0010", "General", "Annual Preventive Health Screening", fac_sdh, ward14, dist_central),
            # Demo Runbook Star Patient
            ("NC-2026-00892", "Lakshmi Devi", 38, "FEMALE", "9845012399", "91-4829-1029-4819", "Laggere Slum Cluster", "Hypertension & Acute Bronchitis", fac_local, ward68, dist_central),
        ]

        u_doctor = seeded_users['doctor']
        u_nurse = seeded_users['nurse']
        u_pharm = seeded_users['pharmacy']
        u_lab = seeded_users['lab']

        for idx, (pid, name, age, gender, phone, abha, slum_cat, complaint, fac, ward_obj, dist_obj) in enumerate(patients_data, 1):
            dob = today - datetime.timedelta(days=age * 365)

            p = Patient.objects.create(
                patient_id=pid,
                name=name,
                date_of_birth=dob,
                age=age,
                gender=gender,
                mobile=phone,
                address=f"{slum_cat}, Ward {ward_obj.ward_number}, Bengaluru",
                ward=ward_obj,
                district=dist_obj,
                ABHA_ID_DEMO=abha,
                emergency_contact='9800000000',
                vulnerability_information=slum_cat,
                registered_at_facility=fac
            )

            # Visit
            v_status = 'COMPLETED' if idx <= 6 else ('IN_CONSULTATION' if idx <= 8 else 'WAITING_FOR_TRIAGE')
            v_queue = 'COMPLETED' if idx <= 6 else ('DOCTOR' if idx <= 8 else 'TRIAGE')

            v = Visit.objects.create(
                visit_id=f"VIS-{fac.facility_code[:4]}-{today.strftime('%Y%m%d')}-{idx:03d}",
                patient=p,
                facility=fac,
                opd_date=today,
                visit_type='GENERAL_OPD',
                priority='HIGH' if 'High' in slum_cat or idx in [1, 9] else 'NORMAL',
                current_queue=v_queue,
                status=v_status,
                chief_complaint=complaint,
                assigned_doctor=u_doctor,
                arrival_time=now - datetime.timedelta(hours=4 - (idx % 3))
            )

            # Token
            Token.objects.create(
                token_number=idx,
                visit=v,
                facility=fac,
                date=today,
                priority=v.priority,
                status='COMPLETED' if v.status == 'COMPLETED' else 'WAITING'
            )

            # Triage vitals (only if triaged or completed)
            if idx <= 8:
                TriageVitals.objects.create(
                    visit=v,
                    patient=p,
                    nurse=u_nurse,
                    blood_pressure_systolic=120 + (idx * 3) % 40,
                    blood_pressure_diastolic=80 + (idx * 2) % 20,
                    pulse_bpm=76 + (idx * 2) % 20,
                    temperature_f=Decimal("98.6") if idx % 2 == 0 else Decimal("100.8"),
                    spo2_percent=98,
                    respiratory_rate=18,
                    blood_glucose_mgdl=110 + (idx * 7) % 60,
                    height_cm=Decimal("165.0"),
                    weight_kg=Decimal("62.5"),
                    nurse_notes=f"Intake vitals recorded for {name}. Oriented to time and place."
                )

                # Consultation
                c = Consultation.objects.create(
                    visit=v,
                    patient=p,
                    doctor=u_doctor,
                    doctor_staff=u_doctor.staff_profile,
                    facility=fac,
                    chief_complaint=complaint,
                    clinical_history=f"Onset of symptoms {idx + 1} days ago. No known drug allergies.",
                    clinical_assessment=f"Clinical presentation consistent with {complaint}.",
                    diagnosis_code="R50.9" if "Fever" in complaint else ("I10" if "Hypertension" in complaint else "J06.9"),
                    diagnosis_name=complaint,
                    treatment_plan="Symptomatic therapy, rest, adequate hydration, medication dispensed.",
                    follow_up_date=today + datetime.timedelta(days=7),
                    clinical_notes="Consultation concluded. Prescriptions dispatched."
                )

                # Prescription & Dispensing
                med_pcm = seeded_meds["Paracetamol"]
                med_aml = seeded_meds["Amlodipine Besylate"]
                med_choice = med_pcm if idx % 2 != 0 else med_aml

                presc = Prescription.objects.create(
                    consultation=c,
                    patient=p,
                    doctor=u_doctor,
                    doctor_staff=u_doctor.staff_profile,
                    facility=fac,
                    status='DISPENSED' if idx <= 6 else 'VERIFIED',
                    verification_notes='Verified by Pharmacist against clinical notes.'
                )

                pi = PrescriptionItem.objects.create(
                    prescription=presc,
                    medicine=med_choice,
                    medicine_name=med_choice.generic_name,
                    dosage='1 tablet TDS' if med_choice == med_pcm else '1 tablet OD',
                    frequency='Three Times Daily' if med_choice == med_pcm else 'Once Daily',
                    duration_days=5,
                    quantity=15 if med_choice == med_pcm else 30,
                    dispensed_quantity=15 if idx <= 6 else 0,
                    status='DISPENSED' if idx <= 6 else 'PENDING'
                )

                if idx <= 6:
                    batch = seeded_batches.get((fac.id, med_choice.id))
                    if batch:
                        InventoryTransaction.objects.create(
                            facility=fac,
                            medicine=med_choice,
                            batch=batch,
                            transaction_type='DISPENSED',
                            quantity=pi.quantity,
                            source_bucket='available_quantity',
                            source_before_qty=batch.available_quantity,
                            source_after_qty=max(0, batch.available_quantity - pi.quantity),
                            destination_bucket='patient_dispensed',
                            destination_before_qty=0,
                            destination_after_qty=pi.quantity,
                            patient=p,
                            visit=v,
                            prescription=presc,
                            prescription_item=pi,
                            created_by=u_pharm,
                            notes=f"Dispensed to {name}"
                        )
                        InventoryLedger.objects.create(
                            batch=batch,
                            facility=fac,
                            performed_by_staff=u_pharm.staff_profile,
                            transaction_type='DISPENSE',
                            quantity_delta=-pi.quantity,
                            balance_after=max(0, batch.available_quantity - pi.quantity),
                            remarks=f"Dispensed for prescription #{presc.id}"
                        )

                # Lab Order for patient 1 & 9
                if idx in [1, 9]:
                    ltok, _ = LabToken.objects.get_or_create(
                        facility=fac,
                        date=today,
                        token_number=idx,
                        defaults={
                            'token_code': f"LAB-{fac.facility_code[:4]}-{idx:03d}",
                            'visit': v,
                            'status': 'COMPLETED'
                        }
                    )
                    lo = LabOrder.objects.create(
                        lab_token=ltok,
                        visit=v,
                        consultation=c,
                        patient=p,
                        doctor=u_doctor,
                        facility=fac,
                        test_master=lt_cbc if idx == 1 else lt_dengue,
                        status='VERIFIED'
                    )
                    LabSample.objects.create(
                        lab_order=lo,
                        sample_type='Venous Blood',
                        sample_code=f"SMP-{idx:04d}",
                        collected_by=u_lab
                    )
                    LabResult.objects.create(
                        lab_order=lo,
                        result_value='8,200' if idx == 1 else 'POSITIVE',
                        unit='/uL' if idx == 1 else 'Card Test',
                        reference_range='4000 - 11000' if idx == 1 else 'NEGATIVE',
                        interpretation_flag='NORMAL' if idx == 1 else 'HIGH',
                        verified_by=u_lab,
                        notes='Report reviewed and signed off.'
                    )

        # Baseline audit event
        AuditLog.objects.create(
            user=seeded_users['district'],
            username_snapshot='district',
            action='SYSTEM_SEED_DEMO',
            facility=fac_hosp,
            details=f"Demo database seeded successfully with {User.objects.count()} users, {Patient.objects.count()} patients, and complete clinical pipelines."
        )

    print("\n" + "=" * 70)
    print("DEMO DATA SEEDING COMPLETE!")
    print("=" * 70)
    print(f"Users in Database      : {User.objects.count()} (Every operational & demo role active)")
    print(f"Facilities in Database : {Facility.objects.count()}")
    print(f"Patients in Database   : {Patient.objects.count()}")
    print(f"Visits in Database     : {Visit.objects.count()}")
    print(f"Prescriptions Dispensed: {Prescription.objects.filter(status='DISPENSED').count()}")
    print(f"Lab Orders Verified    : {LabOrder.objects.filter(status='VERIFIED').count()}")
    print("=" * 70)

if __name__ == '__main__':
    seed_all()

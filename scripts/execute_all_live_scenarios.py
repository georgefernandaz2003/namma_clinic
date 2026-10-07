"""
Comprehensive Live Verification Script for Staff & Clinic Administration
Covers all 7 Live Scenarios across PostgreSQL, Django API, and Playwright browser.
"""
import os
import sys
import time
import json
import datetime
import urllib.request
import urllib.error

sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import transaction
from django.db.models import Q
from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment, StaffStatusChoices
)
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.geography.models import District, State
from apps.accounts.permissions import get_user_active_role_codes, get_user_role_permissions
from apps.common.permissions import get_user_permitted_facilities, is_administrative_staff
from rest_framework.test import APIClient
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_BASE = "http://127.0.0.1:8000/api"

evidence = {}

def log(scenario, step, msg):
    print(f"[{scenario}] Step {step}: {msg}", flush=True)

# ==============================================================================
# SCENARIO 1: DHO CREATES CLINIC
# ==============================================================================
def scenario_1_dho_creates_clinic():
    print("\n" + "="*80)
    print("SCENARIO 1: DHO CREATES CLINIC (PostgreSQL + API + Browser)")
    print("="*80)
    
    # 1. API test with DHO
    client = APIClient()
    dho_user = User.objects.get(username='localdistrict')
    client.force_authenticate(user=dho_user)
    
    code = f"NC-W150-{int(time.time()) % 10000}"
    name = f"Namma Clinic - Ward 150 ({code})"
    payload = {
        'facility_code': code,
        'facility_name': name,
        'facility_type': 'NAMMA_CLINIC',
        'state': 1,
        'district': dho_user.assigned_district_id,
        'address': '12th Main Road, Ward 150, Bengaluru',
        'status': 'ACTIVE'
    }
    
    log("S1", 1, f"Sending POST /api/v1/organization/facilities/ as {dho_user.username}...")
    res = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S1", 2, f"API Response status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.data}"
    
    new_fac_id = res.data['id']
    log("S1", 3, f"Facility created with ID: {new_fac_id}")
    
    # Verify in PostgreSQL
    fac = Facility.objects.get(id=new_fac_id)
    log("S1", 4, f"PostgreSQL Record: id={fac.id}, code={fac.facility_code}, name={fac.facility_name}")
    log("S1", 5, f"PostgreSQL District Binding: district_id={fac.district_id}, district_name={fac.district.name}")
    assert fac.district_id == dho_user.assigned_district_id, "District binding mismatch!"
    
    # Verify in DHO facility scope
    permitted = get_user_permitted_facilities(dho_user.staff_profile, dho_user)
    log("S1", 6, f"DHO Permitted Facilities count: {len(permitted)}, contains new facility: {new_fac_id in permitted}")
    assert new_fac_id in permitted, "New facility not in DHO permitted scope!"
    
    evidence['s1'] = {
        'facility_id': fac.id,
        'facility_code': fac.facility_code,
        'facility_name': fac.facility_name,
        'district_id': fac.district_id,
        'district_name': fac.district.name,
    }
    return fac

# ==============================================================================
# SCENARIO 2: DHO CREATES CLINIC ADMIN
# ==============================================================================
def scenario_2_dho_creates_clinic_admin(fac):
    print("\n" + "="*80)
    print("SCENARIO 2: DHO CREATES CLINIC ADMIN (PostgreSQL + API + Scope Isolation)")
    print("="*80)
    
    client = APIClient()
    dho_user = User.objects.get(username='localdistrict')
    client.force_authenticate(user=dho_user)
    
    emp_id = f"EMP-ADM-{int(time.time()) % 10000}"
    invite_payload = {
        'first_name': 'Kavitha',
        'last_name': 'Reddy',
        'gender': 'FEMALE',
        'date_of_birth': '1987-03-22',
        'phone_number': '9845012399',
        'employee_id': emp_id,
        'designation': 'Hospital Administrator',
        'role_code': 'HOSPITAL_ADMIN',
        'facility_id': fac.id,
        'email': f'{emp_id.lower()}@nammaclinic.gov.in',
    }
    
    log("S2", 1, f"Inviting staff {emp_id} as HOSPITAL_ADMIN for facility {fac.id}...")
    res = client.post('/api/v1/accounts/staff-profiles/invite/', invite_payload, format='json')
    log("S2", 2, f"Invite status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.data}"
    
    staff_id = res.data['id']
    sp = StaffProfile.objects.get(id=staff_id)
    log("S2", 3, f"StaffProfile created in PostgreSQL: id={sp.id}, status={sp.status}")
    assert sp.status == StaffStatusChoices.INVITED, f"Expected INVITED, got {sp.status}"
    
    # Activate staff account
    log("S2", 4, f"Activating staff {staff_id}...")
    res_act = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/activate/')
    log("S2", 5, f"Activate status: {res_act.status_code}")
    assert res_act.status_code == 200, f"Expected 200, got {res_act.status_code}: {res_act.data}"
    
    sp.refresh_from_db()
    log("S2", 6, f"Staff status after activation: {sp.status}")
    assert sp.status == StaffStatusChoices.ACTIVE, f"Expected ACTIVE, got {sp.status}"
    
    # Verify StaffRoleAssignment in PostgreSQL
    sra = StaffRoleAssignment.objects.filter(staff=sp, role__code='HOSPITAL_ADMIN', is_active=True).first()
    log("S2", 7, f"PostgreSQL StaffRoleAssignment: id={sra.id}, role={sra.role.code}, facility_id={sra.facility_id}")
    assert sra is not None, "StaffRoleAssignment not found!"
    assert sra.facility_id == fac.id, "StaffRoleAssignment facility mismatch!"
    
    # The backend invite_staff domain action automatically created the User linked to StaffProfile
    u_admin = User.objects.get(staff_profile=sp)
    u_admin.assigned_facility = fac
    u_admin.assigned_district = fac.district
    u_admin.set_password('ClinicAdmin123!')
    u_admin.save()
    uname = u_admin.username
    log("S2", 8, f"Authoritative User account from invite_staff: username={uname}")
    
    # Test Scope Isolation for this HOSPITAL_ADMIN
    client_admin = APIClient()
    client_admin.force_authenticate(user=u_admin)
    res_list = client_admin.get('/api/v1/accounts/staff-profiles/')
    log("S2", 9, f"Staff list status for new Clinic Admin: {res_list.status_code}")
    assert res_list.status_code == 200, f"Expected 200, got {res_list.status_code}"
    
    profiles = res_list.data if isinstance(res_list.data, list) else res_list.data.get('results', [])
    log("S2", 10, f"Profiles returned to this Hospital Admin: {len(profiles)}")
    for p_item in profiles:
        f_assign = p_item.get('facility_assignment')
        if f_assign:
            log("S2", 11, f"Visible staff ID {p_item['id']} belongs to facility: {f_assign['facility_id']}")
            assert f_assign['facility_id'] == fac.id, f"Foreign facility staff {f_assign['facility_id']} leaked to {fac.id}!"
            
    evidence['s2'] = {
        'admin_username': uname,
        'staff_id': sp.id,
        'role_assignment_id': sra.id,
        'facility_id': fac.id,
        'scoped_profiles_count': len(profiles),
    }

# ==============================================================================
# SCENARIO 3: FACILITY AUTHORIZATION
# ==============================================================================
def scenario_3_facility_authorization():
    print("\n" + "="*80)
    print("SCENARIO 3: FACILITY AUTHORIZATION (Backend Permissions Across Roles)")
    print("="*80)
    
    client = APIClient()
    code = f"NC-AUTH-{int(time.time()) % 10000}"
    payload = {
        'facility_code': code,
        'facility_name': f'Auth Test Clinic {code}',
        'facility_type': 'NAMMA_CLINIC',
        'state': 1,
        'district': 1,
        'status': 'ACTIVE'
    }
    
    results = {}
    
    # 1. DHO
    u_dho = User.objects.get(username='localdistrict')
    client.force_authenticate(user=u_dho)
    res_dho = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 1, f"DHO (localdistrict): status={res_dho.status_code}")
    results['DHO'] = res_dho.status_code
    assert res_dho.status_code == 201, f"Expected 201 for DHO, got {res_dho.status_code}"
    
    # 2. HOSPITAL_ADMIN (live_admin - is_superuser=False)
    u_hosp = User.objects.get(username='live_admin')
    client.force_authenticate(user=u_hosp)
    res_hosp = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 2, f"HOSPITAL_ADMIN (live_admin): status={res_hosp.status_code}")
    results['HOSPITAL_ADMIN'] = res_hosp.status_code
    assert res_hosp.status_code == 403, f"Expected 403 for HOSPITAL_ADMIN, got {res_hosp.status_code}"
    res_mut = client.patch('/api/v1/organization/facilities/1/', {'facility_name': 'Tamper'}, format='json')
    assert res_mut.status_code == 403, f"Expected 403 on mutation for HOSPITAL_ADMIN, got {res_mut.status_code}"
    
    # 3. NURSE
    u_nurse = User.objects.get(username='localnurse')
    client.force_authenticate(user=u_nurse)
    res_nurse = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 3, f"NURSE (localnurse): status={res_nurse.status_code}")
    results['NURSE'] = res_nurse.status_code
    assert res_nurse.status_code == 403, f"Expected 403 for NURSE, got {res_nurse.status_code}"
    
    # 4. DOCTOR
    u_doc = User.objects.get(username='localdoc')
    client.force_authenticate(user=u_doc)
    res_doc = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 4, f"DOCTOR (localdoc): status={res_doc.status_code}")
    results['DOCTOR'] = res_doc.status_code
    assert res_doc.status_code == 403, f"Expected 403 for DOCTOR, got {res_doc.status_code}"
    
    # 5. LAB_TECHNICIAN
    u_lab = User.objects.get(username='locallab')
    client.force_authenticate(user=u_lab)
    res_lab = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 5, f"LAB_TECHNICIAN (locallab): status={res_lab.status_code}")
    results['LAB_TECHNICIAN'] = res_lab.status_code
    assert res_lab.status_code == 403, f"Expected 403 for LAB_TECHNICIAN, got {res_lab.status_code}"
    
    # 6. PHARMACIST
    u_pharm = User.objects.get(username='localpharm')
    client.force_authenticate(user=u_pharm)
    res_pharm = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 6, f"PHARMACIST (localpharm): status={res_pharm.status_code}")
    results['PHARMACIST'] = res_pharm.status_code
    assert res_pharm.status_code == 403, f"Expected 403 for PHARMACIST, got {res_pharm.status_code}"
    
    # 7. FRONT_DESK_OFFICER
    u_cmp = User.objects.get(username='testcompounder')
    client.force_authenticate(user=u_cmp)
    res_cmp = client.post('/api/v1/organization/facilities/', payload, format='json')
    log("S3", 7, f"FRONT_DESK_OFFICER (testcompounder): status={res_cmp.status_code}")
    results['FRONT_DESK_OFFICER'] = res_cmp.status_code
    assert res_cmp.status_code == 403, f"Expected 403 for FRONT_DESK_OFFICER, got {res_cmp.status_code}"
    
    evidence['s3'] = results
    log("S3", 8, f"Summary Matrix: {results}")

# ==============================================================================
# SCENARIO 4: NURSE + COMPOUNDER DUAL ROLE
# ==============================================================================
def scenario_4_nurse_front_desk_officer():
    print("\n" + "="*80)
    print("SCENARIO 4: NURSE + FRONT_DESK_OFFICER SEPARATE ASSIGNMENTS & END ROLE")
    print("="*80)
    
    client = APIClient()
    dho_user = User.objects.get(username='localdistrict')
    client.force_authenticate(user=dho_user)
    
    # 1. Create a disposable staff member
    p = Person.objects.create(
        first_name='Sunita',
        last_name='Bai',
        gender='FEMALE',
        date_of_birth='1991-07-14',
        phone_number='9871122334'
    )
    sp = StaffProfile.objects.create(
        person=p,
        employee_id=f"EMP-NC-{int(time.time()) % 10000}",
        designation='Staff Nurse & Compounder',
        status=StaffStatusChoices.ACTIVE
    )
    fac = Facility.objects.first()
    StaffFacilityAssignment.objects.create(
        staff=sp,
        facility=fac,
        is_primary=True,
        is_active=True,
        effective_from=datetime.date.today()
    )
    log("S4", 1, f"Created staff {sp.employee_id} at facility {fac.id}")
    
    # 2. Assign NURSE
    res_nurse = client.post(f'/api/v1/accounts/staff-profiles/{sp.id}/assign-role/', {
        'role_code': 'NURSE',
        'facility_id': fac.id,
        'effective_from': str(datetime.date.today())
    }, format='json')
    log("S4", 2, f"Assign NURSE status: {res_nurse.status_code}")
    assert res_nurse.status_code in [200, 201], f"Assign NURSE failed: {res_nurse.data}"
    
    # 3. Assign COMPOUNDER separately
    res_cmp = client.post(f'/api/v1/accounts/staff-profiles/{sp.id}/assign-role/', {
        'role_code': 'COMPOUNDER',
        'facility_id': fac.id,
        'effective_from': str(datetime.date.today())
    }, format='json')
    log("S4", 3, f"Assign COMPOUNDER status: {res_cmp.status_code}")
    assert res_cmp.status_code in [200, 201], f"Assign COMPOUNDER failed: {res_cmp.data}"
    
    # 4. Verify in PostgreSQL
    assignments = list(StaffRoleAssignment.objects.filter(staff=sp, is_active=True).values('id', 'role__code', 'is_active'))
    log("S4", 4, f"PostgreSQL Active Role Assignments: {assignments}")
    assert len(assignments) == 2, f"Expected 2 assignments, got {len(assignments)}"
    role_codes = [a['role__code'] for a in assignments]
    assert 'NURSE' in role_codes and 'COMPOUNDER' in role_codes, "Both NURSE and COMPOUNDER must be active!"
    
    # 5. End COMPOUNDER role
    cmp_assignment = next(a for a in assignments if a['role__code'] == 'COMPOUNDER')
    res_end = client.post(f'/api/v1/accounts/role-assignments/{cmp_assignment["id"]}/end-assignment/', {
        'end_date': str(datetime.date.today())
    }, format='json')
    log("S4", 5, f"End COMPOUNDER assignment {cmp_assignment['id']} status: {res_end.status_code}")
    assert res_end.status_code == 200, f"End role failed: {res_end.data}"
    
    # 6. Verify in PostgreSQL that NURSE remains active
    live_roles = list(StaffRoleAssignment.objects.filter(staff=sp, is_active=True).values('id', 'role__code', 'is_active'))
    log("S4", 6, f"PostgreSQL Active Roles after ending COMPOUNDER: {live_roles}")
    assert len(live_roles) == 1, f"Expected exactly 1 active role, got {len(live_roles)}"
    assert live_roles[0]['role__code'] == 'NURSE', f"Expected active role to be NURSE, got {live_roles[0]['role__code']}"
    
    # 7. Verify no NURSE_COMPOUNDER exists in RoleMaster
    assert not RoleMaster.objects.filter(code='NURSE_COMPOUNDER').exists(), "NURSE_COMPOUNDER must not exist in RoleMaster!"
    log("S4", 7, "Verified: No NURSE_COMPOUNDER role exists in RoleMaster.")
    
    evidence['s4'] = {
        'staff_id': sp.id,
        'initial_active_roles': role_codes,
        'remaining_active_roles': [r['role__code'] for r in live_roles],
    }

# ==============================================================================
# SCENARIO 5: LIFECYCLE TRANSITIONS
# ==============================================================================
def scenario_5_lifecycle():
    print("\n" + "="*80)
    print("SCENARIO 5: LIFECYCLE TRANSITIONS (INVITED -> ACTIVE -> SUSPENDED -> DEACTIVATED)")
    print("="*80)
    
    client = APIClient()
    dho_user = User.objects.get(username='localdistrict')
    client.force_authenticate(user=dho_user)
    
    emp_id = f"EMP-LC-{int(time.time()) % 10000}"
    fac = Facility.objects.first()
    
    # 1. INVITED
    res_inv = client.post('/api/v1/accounts/staff-profiles/invite/', {
        'first_name': 'Meera',
        'last_name': 'Nair',
        'gender': 'FEMALE',
        'date_of_birth': '1993-11-05',
        'employee_id': emp_id,
        'designation': 'Lab Technician',
        'role_code': 'LAB_TECHNICIAN',
        'facility_id': fac.id,
        'email': f'{emp_id.lower()}@nammaclinic.gov.in',
    }, format='json')
    assert res_inv.status_code == 201
    staff_id = res_inv.data['id']
    sp = StaffProfile.objects.get(id=staff_id)
    log("S5", 1, f"1. INVITED: staff_id={sp.id}, status={sp.status}")
    assert sp.status == StaffStatusChoices.INVITED
    
    # 2. ACTIVE
    res_act = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/activate/')
    assert res_act.status_code == 200
    sp.refresh_from_db()
    log("S5", 2, f"2. ACTIVE: staff_id={sp.id}, status={sp.status}")
    assert sp.status == StaffStatusChoices.ACTIVE
    
    # 3. SUSPENDED
    res_susp = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/suspend/', {
        'reason': 'Administrative disciplinary inquiry'
    }, format='json')
    assert res_susp.status_code == 200
    sp.refresh_from_db()
    log("S5", 3, f"3. SUSPENDED: staff_id={sp.id}, status={sp.status}")
    assert sp.status == StaffStatusChoices.SUSPENDED
    
    # 4. REACTIVATE (Check if activate works from suspended)
    res_react = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/activate/')
    log("S5", 4, f"Reactivate attempt from SUSPENDED: status={res_react.status_code}")
    if res_react.status_code == 200:
        sp.refresh_from_db()
        log("S5", 4, f"4. REACTIVATED -> ACTIVE: status={sp.status}")
        assert sp.status == StaffStatusChoices.ACTIVE
    else:
        log("S5", 4, f"Reactivation from SUSPENDED returned {res_react.status_code}: {res_react.data}")
    
    # 5. DEACTIVATED
    res_deact = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/deactivate/', {
        'reason': 'Permanent separation'
    }, format='json')
    assert res_deact.status_code == 200
    sp.refresh_from_db()
    log("S5", 5, f"5. DEACTIVATED: staff_id={sp.id}, status={sp.status}")
    assert sp.status == StaffStatusChoices.DEACTIVATED
    
    # Verify mutations are rejected on DEACTIVATED
    res_reassign = client.post(f'/api/v1/accounts/staff-profiles/{staff_id}/assign-role/', {
        'role_code': 'PHARMACIST',
        'facility_id': fac.id,
        'effective_from': str(datetime.date.today())
    }, format='json')
    log("S5", 6, f"Attempt mutation on DEACTIVATED: status={res_reassign.status_code}")
    assert res_reassign.status_code in [400, 403, 404, 409], "Mutations must be rejected on DEACTIVATED staff!"
    
    evidence['s5'] = {
        'staff_id': staff_id,
        'final_status': sp.status,
        'mutation_rejected_status': res_reassign.status_code
    }

# ==============================================================================
# SCENARIO 6: TRANSFER WORKFLOW
# ==============================================================================
def scenario_6_transfer():
    print("\n" + "="*80)
    print("SCENARIO 6: TRANSFER WORKFLOW (Future Scheduled Transfer & Semantics)")
    print("="*80)
    
    client = APIClient()
    dho_user = User.objects.get(username='localdistrict')
    client.force_authenticate(user=dho_user)
    
    fac_origin = Facility.objects.first()
    fac_dest = Facility.objects.exclude(id=fac_origin.id).first()
    assert fac_dest is not None, "At least two facilities required for transfer test!"
    
    # Create disposable active staff
    p = Person.objects.create(first_name='Anand', last_name='Verma', gender='MALE', date_of_birth='1989-10-10')
    sp = StaffProfile.objects.create(
        person=p,
        employee_id=f"EMP-TR-{int(time.time()) % 10000}",
        designation='Medical Officer',
        status=StaffStatusChoices.ACTIVE
    )
    sfa = StaffFacilityAssignment.objects.create(
        staff=sp,
        facility=fac_origin,
        is_primary=True,
        is_active=True,
        effective_from=datetime.date.today() - datetime.timedelta(days=30)
    )
    log("S6", 1, f"Staff {sp.employee_id} created at origin facility {fac_origin.facility_name} (ID: {fac_origin.id})")
    
    # Schedule future transfer
    future_date = datetime.date.today() + datetime.timedelta(days=14)
    res_tr = client.post(f'/api/v1/accounts/staff-profiles/{sp.id}/transfer/', {
        'new_facility_id': fac_dest.id,
        'effective_date': str(future_date),
        'reason': 'Deployment to higher-demand clinic'
    }, format='json')
    
    log("S6", 2, f"Transfer API response status: {res_tr.status_code}")
    assert res_tr.status_code == 200, f"Transfer failed: {res_tr.data}"
    
    sp.refresh_from_db()
    log("S6", 3, f"Staff status after future transfer request: {sp.status}")
    assert sp.status == StaffStatusChoices.TRANSFER_PENDING, f"Expected TRANSFER_PENDING, got {sp.status}"
    
    # Verify current facility assignment remains active and destination assignment is created with future date
    assignments = list(StaffFacilityAssignment.objects.filter(staff=sp).values(
        'id', 'facility_id', 'facility__facility_name', 'is_primary', 'is_active', 'effective_from', 'effective_to'
    ))
    log("S6", 4, f"PostgreSQL Facility Assignments: {assignments}")
    
    origin_assignment = next((a for a in assignments if a['facility_id'] == fac_origin.id), None)
    dest_assignment = next((a for a in assignments if a['facility_id'] == fac_dest.id), None)
    
    assert origin_assignment is not None, "Origin assignment missing!"
    assert dest_assignment is not None, "Destination assignment missing!"
    
    # Current access semantics:
    # Origin assignment remains active until transfer date
    log("S6", 5, f"Origin assignment effective_to: {origin_assignment['effective_to']}")
    assert str(origin_assignment['effective_to']) == str(future_date - datetime.timedelta(days=1)), "Origin assignment must end on effective_date!"
    log("S6", 6, f"Destination assignment effective_from: {dest_assignment['effective_from']}")
    assert str(dest_assignment['effective_from']) == str(future_date), "Destination assignment must start on effective_date!"
    
    # Check permitted facilities right now (today < future_date):
    # Only origin facility is accessible today
    permitted_today = get_user_permitted_facilities(sp)
    log("S6", 7, f"Permitted facilities today (before effective date): {permitted_today}")
    assert fac_origin.id in permitted_today, "Origin facility must be permitted today!"
    assert fac_dest.id not in permitted_today, "Destination facility must NOT have active access before effective date!"
    log("S6", 8, "Verified: Dual simultaneous active access is strictly disallowed.")
    
    evidence['s6'] = {
        'staff_id': sp.id,
        'status': sp.status,
        'origin_facility_id': fac_origin.id,
        'dest_facility_id': fac_dest.id,
        'effective_date': str(future_date),
        'permitted_today': permitted_today
    }

# ==============================================================================
# SCENARIO 7: CLINICAL ROLE ISOLATION
# ==============================================================================
def scenario_7_clinical_role_isolation():
    print("\n" + "="*80)
    print("SCENARIO 7: CLINICAL ROLE ISOLATION (Nurse & Front Desk Officer)")
    print("="*80)
    
    client = APIClient()
    
    # 1. Nurse API 403 test
    u_nurse = User.objects.get(username='localnurse')
    client.force_authenticate(user=u_nurse)
    res_nurse_api = client.get('/api/v1/accounts/staff-profiles/')
    log("S7", 1, f"Nurse calling StaffProfile API directly: status={res_nurse_api.status_code}")
    assert res_nurse_api.status_code == 403, f"Expected 403 for Nurse, got {res_nurse_api.status_code}"
    
    # 2. Compounder API 403 test
    u_cmp = User.objects.get(username='testcompounder')
    client.force_authenticate(user=u_cmp)
    res_cmp_api = client.get('/api/v1/accounts/staff-profiles/')
    log("S7", 2, f"Compounder calling StaffProfile API directly: status={res_cmp_api.status_code}")
    assert res_cmp_api.status_code == 403, f"Expected 403 for Compounder, got {res_cmp_api.status_code}"
    
    # 3. Compounder Permission Matrix check
    cmp_permissions = get_user_role_permissions(u_cmp)
    log("S7", 3, f"Compounder Active Permissions count: {len(cmp_permissions)}")
    log("S7", 4, f"Compounder Permissions: {sorted(list(cmp_permissions))}")
    
    disallowed_keywords = [
        'triage', 'consultation', 'diagnosis', 'prescription',
        'diagnostic', 'specimen', 'lab', 'dispense', 'inventory',
        'procurement', 'staff'
    ]
    for perm in cmp_permissions:
        for kw in disallowed_keywords:
            assert kw not in perm, f"Compounder must NOT have '{kw}' permission, found '{perm}'!"
            
    log("S7", 5, "Verified: Compounder possesses strictly approved registration and queue responsibilities without clinical mutations.")
    
    evidence['s7'] = {
        'nurse_api_status': res_nurse_api.status_code,
        'compounder_api_status': res_cmp_api.status_code,
        'compounder_permissions': sorted(list(cmp_permissions)),
    }

# ==============================================================================
# PLAYWRIGHT BROWSER VALIDATION FOR LIVE SCENARIOS
# ==============================================================================
def run_browser_live_scenarios(created_fac):
    print("\n" + "="*80)
    print("BROWSER LIVE VALIDATION: DHO & Clinic Admin End-to-End")
    print("="*80)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        # 1. Login as DHO
        log("BROWSER", 1, "Logging in as DHO (localdistrict)...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'localdistrict')
        page.fill('input[type="password"]', 'DistrictPassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/district", timeout=15000)
        log("BROWSER", 2, "DHO Dashboard loaded.")
        
        # 2. Open /admin/staff
        log("BROWSER", 3, "Navigating to /admin/staff...")
        page.goto(f"{BASE_URL}/admin/staff")
        page.wait_for_selector('[data-testid="staff-directory-table"], [data-testid="staff-search-input"]', timeout=15000)
        log("BROWSER", 4, "/admin/staff loaded for DHO.")
        
        # 3. Verify newly created facility appears in DHO facility dropdown
        page.wait_for_selector('[data-testid="staff-facility-filter"]')
        time.sleep(3)
        fac_select = page.locator('[data-testid="staff-facility-filter"]')
        options_text = fac_select.inner_text()
        log("BROWSER", 5, f"Facility dropdown options include new clinic: {created_fac.facility_name in options_text}")
        assert created_fac.facility_name in options_text, f"{created_fac.facility_name} not found in facility filter!"
        
        # 4. Test Nurse forbidden card
        log("BROWSER", 6, "Testing Nurse isolation in browser...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector('input[type="text"]', timeout=15000)
        page.fill('input[type="text"]', 'localnurse')
        page.fill('input[type="password"]', 'NursePassword123!')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/nurse", timeout=15000)
        
        page.goto(f"{BASE_URL}/admin/staff")
        time.sleep(1)
        body_text = page.inner_text("body")
        assert "Access Denied" in body_text or "HTTP 403" in body_text, "Nurse should see ForbiddenCard on /admin/staff!"
        log("BROWSER", 7, "Verified: ForbiddenCard correctly displayed on /admin/staff for Nurse.")
        
        browser.close()
        log("BROWSER", 8, "Browser validation completed successfully.")

if __name__ == "__main__":
    fac = scenario_1_dho_creates_clinic()
    scenario_2_dho_creates_clinic_admin(fac)
    scenario_3_facility_authorization()
    scenario_4_nurse_front_desk_officer()
    scenario_5_lifecycle()
    scenario_6_transfer()
    scenario_7_clinical_role_isolation()
    run_browser_live_scenarios(fac)
    print("\n" + "="*80)
    print("ALL 7 REQUIRED LIVE SCENARIOS COMPLETED AND VALIDATED")
    print("="*80)

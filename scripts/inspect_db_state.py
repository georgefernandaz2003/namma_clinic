import os
import sys
import django

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, StaffProfile, StaffRoleAssignment
from apps.pharmacy.models import MedicineMaster, MedicineBatch
from apps.laboratory.models import DiagnosticTestMaster
from apps.consultations.models import DiagnosisMaster
from apps.surveillance.models import DiseaseMaster
from apps.facilities.models import Facility

print("=== USERS & ROLES ===")
for u in User.objects.all():
    sp = u.staff_profile
    fac = u.assigned_facility.facility_code if u.assigned_facility else 'None'
    roles = []
    if sp:
        roles = list(StaffRoleAssignment.objects.filter(staff=sp, is_active=True).values_list('role__code', flat=True))
    sp_id = sp.id if sp else None
    print(f"{u.username:16} | fac: {fac:14} | sp_id: {str(sp_id):5} | roles: {roles}")

print("\n=== MEDICINE MASTERS ===")
for m in MedicineMaster.objects.all():
    print(f"ID:{m.id:2} | Generic: {m.generic_name:25} | Brand: {m.brand_name:20} | Strength: {m.strength}")

print("\n=== BATCHES ===")
for b in MedicineBatch.objects.select_related('medicine', 'facility').all():
    print(f"Batch: {b.batch_number:12} | Med: {b.medicine.generic_name:22} | Fac: {b.facility.facility_code:12} | Avail: {b.available_quantity}")

print("\n=== TEST MASTERS ===")
for t in DiagnosticTestMaster.objects.all():
    print(f"ID:{t.id:2} | Code: {t.code:12} | Name: {t.test_name:30} | Range: {t.normal_range_min}-{t.normal_range_max} {t.unit}")

print("\n=== DIAGNOSES ===")
for d in DiagnosisMaster.objects.all():
    print(f"ID:{d.id:2} | Code: {d.icd10_code:10} | Name: {d.standard_term}")

print("\n=== DISEASES ===")
for dis in DiseaseMaster.objects.all():
    print(f"ID:{dis.id:2} | Code: {dis.disease_code:10} | Name: {dis.disease_name}")

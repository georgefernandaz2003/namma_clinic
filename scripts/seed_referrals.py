import os
import sys
import datetime
import django

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DATABASE_ENGINE', 'postgresql')
django.setup()

from apps.referrals.models import ReferralOrder, ReferralEvent
from apps.visits.models import Visit
from apps.facilities.models import Facility
from apps.accounts.models import StaffProfile

fac_local = Facility.objects.filter(facility_code='PHC-LOCAL-01').first() or Facility.objects.get(id=1)
fac_rc = Facility.objects.filter(facility_code='RC-A4-01').first() or fac_local
fac_sub = Facility.objects.filter(facility_code='HOSP-SUB-01').first() or fac_local
fac_dist = Facility.objects.filter(facility_code='HOSP-DIST-01').first() or fac_local
staff_doc = StaffProfile.objects.filter(user_account__username__in=['doctor', 'e2e_doctor_user', 'localdoc']).first()

visits_for_ref = list(Visit.objects.filter(triage__blood_pressure_systolic__gte=150)[:15]) + list(Visit.objects.filter(consultations__diagnosis_code__in=['A90', 'A01.0'])[:10])

created_refs = 0
for v in visits_for_ref:
    is_htn = (v.consultation.diagnosis_code == 'I10') if hasattr(v, 'consultation') else False
    dest = fac_dist if (v.priority == 'HIGH' or v.id % 2 == 0) else fac_sub
    urgency = 'EMERGENCY' if (v.priority == 'HIGH') else 'URGENT'
    reason = 'Specialist Cardiology Evaluation for Refractory Hypertension' if is_htn else 'Tertiary Inpatient Care for Complicated Febrile Illness with Severe Thrombocytopenia'
    
    ref_num = f'REF-F{v.facility_id}-{v.opd_date.strftime("%Y%m%d")}-{v.id:04d}'
    ro, created = ReferralOrder.objects.get_or_create(
        referral_number=ref_num,
        defaults={
            'visit': v,
            'patient': v.patient,
            'source_facility': v.facility,
            'destination_facility': dest,
            'referring_doctor': staff_doc,
            'urgency': urgency,
            'reason': reason,
            'clinical_summary': f'{reason}. Referred from {v.facility.facility_name}.',
            'status': 'COMPLETED' if v.opd_date < datetime.date(2026, 10, 4) else 'INITIATED',
            'referral_date': v.opd_date
        }
    )
    if created:
        created_refs += 1
        ReferralEvent.objects.create(
            referral=ro,
            recorded_by_staff=staff_doc,
            event_type='INITIATION',
            specialist_findings='Specialist evaluation performed at referral facility.',
            treatment_rendered='Patient stabilized and medication titrated.',
            return_advice='Advised monthly primary clinic follow-up.',
            event_timestamp=v.visit_date + datetime.timedelta(hours=2)
        )

print(f'Referral Orders Seeded: {created_refs} (Total in DB: {ReferralOrder.objects.count()})')

"""
Facility domain service layer.
Authoritative business logic for healthcare facilities.
"""
from apps.facilities.models import Department, ServiceMaster, FacilityService

STANDARD_FACILITY_DEPARTMENTS = [
    ('OPD', 'General OPD'),
    ('PHARM', 'Pharmacy'),
    ('LAB', 'Laboratory'),
    ('TRIAGE', 'Triage'),
]

STANDARD_CANONICAL_SERVICES = [
    {
        'code': 'SRV_GENERAL_OPD',
        'name': 'General OPD Consultation',
        'category': 'CLINICAL',
    },
    {
        'code': 'SRV_NCD_SCREENING',
        'name': 'NCD Screening & Management',
        'category': 'CLINICAL',
    },
    {
        'code': 'SRV_DIAGNOSTICS',
        'name': 'Diagnostic Laboratory Services',
        'category': 'DIAGNOSTIC',
    },
    {
        'code': 'SRV_PHARMACY',
        'name': 'Pharmacy & Dispensing Services',
        'category': 'PHARMACY',
    },
    {
        'code': 'SRV_TRIAGE',
        'name': 'Triage & Vital Signs Assessment',
        'category': 'CLINICAL',
    },
]

def provision_standard_departments(facility):
    """
    Provisions approved standard departments for a facility if not already present.
    Standard departments: General OPD, Pharmacy, Laboratory, Triage.
    Idempotent: uses get_or_create to avoid duplicate key conflicts.
    """
    provisioned = []
    for code, name in STANDARD_FACILITY_DEPARTMENTS:
        dept, _ = Department.objects.get_or_create(
            facility=facility,
            code=code,
            defaults={'name': name, 'is_active': True}
        )
        provisioned.append(dept)
    return provisioned

def ensure_canonical_service_masters():
    """
    Ensures that all approved canonical ServiceMaster records exist in the database.
    Does not seed MCH or teleconsultation.
    """
    masters = []
    for s_data in STANDARD_CANONICAL_SERVICES:
        master, _ = ServiceMaster.objects.get_or_create(
            code=s_data['code'],
            defaults={
                'name': s_data['name'],
                'category': s_data['category'],
                'is_active': True
            }
        )
        masters.append(master)
    return masters

def provision_standard_facility_services(facility):
    """
    Provisions approved canonical services for a given facility with is_available=True.
    Idempotent: uses get_or_create to avoid duplicate mapping conflicts.
    """
    masters = ensure_canonical_service_masters()
    provisioned = []
    for master in masters:
        fac_svc, _ = FacilityService.objects.get_or_create(
            facility=facility,
            service=master,
            defaults={'is_available': True}
        )
        provisioned.append(fac_svc)
    return provisioned

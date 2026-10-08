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

SERVICE_TO_DEPARTMENT_MAP = {
    'SRV_GENERAL_OPD': 'OPD',
    'SRV_NCD_SCREENING': 'OPD',
    'SRV_DIAGNOSTICS': 'LAB',
    'SRV_PHARMACY': 'PHARM',
    'SRV_TRIAGE': 'TRIAGE',
}

DEPARTMENT_TO_SERVICES_MAP = {
    'OPD': ['SRV_GENERAL_OPD', 'SRV_NCD_SCREENING'],
    'LAB': ['SRV_DIAGNOSTICS'],
    'PHARM': ['SRV_PHARMACY'],
    'TRIAGE': ['SRV_TRIAGE'],
}

STANDARD_DEPARTMENT_CODES = {'OPD', 'PHARM', 'LAB', 'TRIAGE'}

def validate_service_enablement(facility, service_code):
    """
    Validates that a canonical service cannot be enabled if its supporting
    physical department is missing or inactive.
    Raises rest_framework.exceptions.ValidationError.
    """
    from rest_framework.exceptions import ValidationError
    dept_code = SERVICE_TO_DEPARTMENT_MAP.get(service_code)
    if not dept_code:
        return
    dept = Department.objects.filter(facility=facility, code=dept_code).first()
    if not dept or not dept.is_active:
        dept_name = dept.name if dept else dept_code
        raise ValidationError(
            f"Cannot enable service '{service_code}' because its supporting department '{dept_name}' ({dept_code}) is inactive or not provisioned at this facility."
        )

def validate_department_deactivation(facility, dept_code):
    """
    Validates that a department cannot be deactivated or deleted while any of its
    dependent facility services remain operational (is_available=True).
    Raises rest_framework.exceptions.ValidationError.
    """
    from rest_framework.exceptions import ValidationError
    dep_service_codes = DEPARTMENT_TO_SERVICES_MAP.get(dept_code, [])
    if not dep_service_codes:
        return
    active_services = list(
        FacilityService.objects.filter(
            facility=facility,
            service__code__in=dep_service_codes,
            is_available=True
        ).values_list('service__name', flat=True)
    )
    if active_services:
        services_str = ", ".join(active_services)
        raise ValidationError(
            f"Cannot deactivate department '{dept_code}' while dependent service(s) ({services_str}) remain active. Please disable the service(s) first."
        )

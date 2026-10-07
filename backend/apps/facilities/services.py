"""
Facility domain service layer.
Authoritative business logic for healthcare facilities.
"""
from apps.facilities.models import Department

STANDARD_FACILITY_DEPARTMENTS = [
    ('OPD', 'General OPD'),
    ('PHARM', 'Pharmacy'),
    ('LAB', 'Laboratory'),
    ('TRIAGE', 'Triage'),
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

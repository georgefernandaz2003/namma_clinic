# Generated for Phase 37 ? Staff-Department Integrity Hardening

from django.db import migrations

def reconcile_staff_department_assignments_forward(apps, schema_editor):
    StaffProfile = apps.get_model('accounts', 'StaffProfile')
    StaffRoleAssignment = apps.get_model('accounts', 'StaffRoleAssignment')
    StaffFacilityAssignment = apps.get_model('accounts', 'StaffFacilityAssignment')
    Facility = apps.get_model('facilities', 'Facility')
    Department = apps.get_model('facilities', 'Department')

    # Standard department codes
    STANDARD_DEPARTMENTS = [
        ('OPD', 'General OPD'),
        ('PHARM', 'Pharmacy'),
        ('LAB', 'Laboratory'),
        ('TRIAGE', 'Triage'),
    ]

    def ensure_depts(facility):
        for code, name in STANDARD_DEPARTMENTS:
            dept = Department.objects.filter(facility=facility, code=code).first()
            if not dept:
                Department.objects.create(
                    facility=facility,
                    code=code,
                    name=name,
                    is_active=True
                )

    for sp in StaffProfile.objects.all():
        roles = list(StaffRoleAssignment.objects.filter(staff=sp, is_active=True).values_list('role__code', flat=True))
        pfa = StaffFacilityAssignment.objects.filter(staff=sp, is_primary=True, is_active=True).first()
        fac = pfa.facility if pfa else None
        if not fac and sp.department:
            fac = sp.department.facility

        if not fac:
            continue

        ensure_depts(fac)
        dept_pharm = Department.objects.filter(facility=fac, code='PHARM').first()
        dept_lab = Department.objects.filter(facility=fac, code='LAB').first()
        dept_opd = Department.objects.filter(facility=fac, code='OPD').first()
        dept_triage = Department.objects.filter(facility=fac, code='TRIAGE').first()

        target_dept = None
        desig_lower = sp.designation.lower()

        if 'PHARMACIST' in roles or 'pharmacist' in desig_lower:
            target_dept = dept_pharm
        elif 'LAB_TECHNICIAN' in roles or 'lab' in desig_lower:
            target_dept = dept_lab
        elif 'DOCTOR' in roles or 'doctor' in desig_lower or 'medical officer' in desig_lower:
            target_dept = dept_opd
        elif 'FRONT_DESK_OFFICER' in roles or 'front desk' in desig_lower or 'compounder' in desig_lower:
            target_dept = dept_opd
        elif 'NURSE' in roles or 'nurse' in desig_lower:
            target_dept = dept_triage or dept_opd

        if target_dept:
            sp.department = target_dept
            sp.save(update_fields=['department'])
            if pfa:
                pfa.department = target_dept
                pfa.save(update_fields=['department'])


def reconcile_staff_department_assignments_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_rename_compounder_to_front_desk_officer'),
        ('facilities', '0004_seed_canonical_services'),
    ]

    operations = [
        migrations.RunPython(
            reconcile_staff_department_assignments_forward,
            reverse_code=reconcile_staff_department_assignments_reverse
        ),
    ]

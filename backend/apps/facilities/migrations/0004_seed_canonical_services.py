from django.db import migrations

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

def seed_canonical_services(apps, schema_editor):
    ServiceMaster = apps.get_model('facilities', 'ServiceMaster')
    Facility = apps.get_model('facilities', 'Facility')
    FacilityService = apps.get_model('facilities', 'FacilityService')

    masters = []
    for s in STANDARD_CANONICAL_SERVICES:
        master, _ = ServiceMaster.objects.get_or_create(
            code=s['code'],
            defaults={
                'name': s['name'],
                'category': s['category'],
                'is_active': True
            }
        )
        masters.append(master)

    # Provision default active services for all existing facilities
    for fac in Facility.objects.all():
        for master in masters:
            FacilityService.objects.get_or_create(
                facility=fac,
                service=master,
                defaults={'is_available': True}
            )

def rollback_canonical_services(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0003_servicemaster_facilityservice_department'),
    ]

    operations = [
        migrations.RunPython(seed_canonical_services, rollback_canonical_services),
    ]

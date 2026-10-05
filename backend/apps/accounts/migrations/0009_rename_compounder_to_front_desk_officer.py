# Generated manually for Phase 28B-0 Rename Compounder to Front Desk Officer

from django.db import migrations, models


def rename_compounder_forward(apps, schema_editor):
    RoleMaster = apps.get_model('accounts', 'RoleMaster')
    User = apps.get_model('accounts', 'User')
    StaffProfile = apps.get_model('accounts', 'StaffProfile')

    # 1. Update existing RoleMaster row in place (preserving PK and all FK assignments/permissions)
    RoleMaster.objects.filter(code='COMPOUNDER').update(
        code='FRONT_DESK_OFFICER',
        name='Front Desk Officer',
        description='Front Desk Officer responsible for patient registration, token issuing, and queue management',
    )

    # 2. Update legacy role column on User
    User.objects.filter(role='COMPOUNDER').update(role='FRONT_DESK_OFFICER')

    # 3. Update StaffProfile designation if it was 'Compounder'
    StaffProfile.objects.filter(designation='Compounder').update(designation='Front Desk Officer')

    # 4. Synchronize permissions using the service
    from apps.accounts.services import seed_roles_and_permissions
    seed_roles_and_permissions()


def rename_compounder_reverse(apps, schema_editor):
    RoleMaster = apps.get_model('accounts', 'RoleMaster')
    User = apps.get_model('accounts', 'User')
    StaffProfile = apps.get_model('accounts', 'StaffProfile')

    RoleMaster.objects.filter(code='FRONT_DESK_OFFICER').update(
        code='COMPOUNDER',
        name='Compounder',
        description='Compounder role for patient registration and queue management',
    )
    User.objects.filter(role='FRONT_DESK_OFFICER').update(role='COMPOUNDER')
    StaffProfile.objects.filter(designation='Front Desk Officer').update(designation='Compounder')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_seed_inventory_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('DISTRICT_OFFICER', 'District Officer'),
                    ('HOSPITAL_ADMIN', 'Hospital Administrator'),
                    ('DOCTOR', 'Doctor'),
                    ('NURSE', 'Nurse'),
                    ('FRONT_DESK_OFFICER', 'Front Desk Officer'),
                    ('LAB_TECHNICIAN', 'Lab Technician'),
                    ('PHARMACIST', 'Pharmacist'),
                    ('INVENTORY', 'Inventory Manager'),
                ],
                default='DOCTOR',
                max_length=30,
            ),
        ),
        migrations.RunPython(rename_compounder_forward, reverse_code=rename_compounder_reverse),
    ]

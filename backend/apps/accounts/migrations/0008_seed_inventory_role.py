# Generated manually for Phase 27.1 Inventory Role Foundation

from django.db import migrations


def seed_inventory_role_forward(apps, schema_editor):
    from apps.accounts.services import seed_roles_and_permissions
    seed_roles_and_permissions()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(seed_inventory_role_forward, reverse_code=migrations.RunPython.noop),
    ]

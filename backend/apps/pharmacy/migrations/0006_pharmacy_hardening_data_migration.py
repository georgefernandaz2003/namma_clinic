from django.db import migrations, models


def migrate_pharmacy_data_forward(apps, schema_editor):
    MedicineBatch = apps.get_model('pharmacy', 'MedicineBatch')
    PrescriptionItem = apps.get_model('consultations', 'PrescriptionItem')

    # Non-destructive bulk QuerySet.update() on MedicineBatch
    # CRITICAL: We use .update(available_quantity=models.F('quantity'))
    # This executes at database level without triggering MedicineBatch.save(),
    # preserving existing quantity and initializing available_quantity directly from legacy quantity.
    # Batches with expiry_date <= today also retain their physical stock count in available_quantity = quantity,
    # without silent zeroing. Runtime predicates (expiry_date > today, expiry_bucket) enforce non-dispensability.
    MedicineBatch.objects.all().update(
        available_quantity=models.F('quantity'),
        quarantined_quantity=0,
        recalled_quantity=0,
        damaged_quantity=0,
        disposed_quantity=0
    )

    # PrescriptionItem dispensed_quantity migration
    # Historical DISPENSED items: dispensed_quantity = quantity
    PrescriptionItem.objects.filter(status='DISPENSED').update(
        dispensed_quantity=models.F('quantity')
    )
    # Historical PENDING items: dispensed_quantity = 0
    PrescriptionItem.objects.filter(status='PENDING').update(
        dispensed_quantity=0
    )


def migrate_pharmacy_data_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0005_inventorytransaction_after_quantity_and_more'),
        ('consultations', '0004_prescription_rejection_reason_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_pharmacy_data_forward, migrate_pharmacy_data_backward),
    ]

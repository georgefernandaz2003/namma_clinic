from django.db import migrations

def populate_prescription_item_medicine(apps, schema_editor):
    PrescriptionItem = apps.get_model('consultations', 'PrescriptionItem')
    MedicineMaster = apps.get_model('pharmacy', 'MedicineMaster')

    # Build lookup table of lower generic and brand names
    meds = list(MedicineMaster.objects.all())
    
    for item in PrescriptionItem.objects.all():
        if item.medicine_id:
            continue
        name_clean = (item.medicine_name or '').strip().lower()
        matched = None

        # 1. Exact match on generic or brand
        for m in meds:
            if m.generic_name.strip().lower() == name_clean or (m.brand_name and m.brand_name.strip().lower() == name_clean):
                matched = m
                break

        # 2. Match if medicine generic name is a substring of item name or vice versa
        if not matched:
            for m in meds:
                gen = m.generic_name.strip().lower()
                # e.g., 'Metformin 500 mg Tablet' contains 'metformin'
                first_word = gen.split()[0]
                if first_word in name_clean:
                    matched = m
                    break

        if matched:
            item.medicine_id = matched.id
            item.save(update_fields=['medicine_id'])
            print(f"[DATA MIGRATION] Linked PrescriptionItem #{item.id} ('{item.medicine_name}') -> MedicineMaster #{matched.id} ('{matched.generic_name}')")
        else:
            print(f"[DATA MIGRATION WARNING] Could not map PrescriptionItem #{item.id} ('{item.medicine_name}') to MedicineMaster. Field left as NULL safely.")

def reverse_populate(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('consultations', '0002_prescriptionitem_medicine'),
        ('pharmacy', '0004_purchaseorder_approved_at_purchaseorder_approved_by_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_prescription_item_medicine, reverse_populate),
    ]

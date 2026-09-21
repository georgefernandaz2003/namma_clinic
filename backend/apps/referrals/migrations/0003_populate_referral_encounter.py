from django.db import migrations

def populate_referral_encounter(apps, schema_editor):
    Referral = apps.get_model('referrals', 'Referral')
    Consultation = apps.get_model('consultations', 'Consultation')
    Visit = apps.get_model('visits', 'Visit')

    for ref in Referral.objects.all():
        updated = False
        # If visit or consultation missing, find matching consultation/visit by patient and facility
        if not ref.consultation_id or not ref.visit_id:
            # Look for consultation with same patient and facility
            consult = Consultation.objects.filter(
                patient_id=ref.patient_id,
                facility_id=ref.source_facility_id
            ).order_by('-created_at').first()

            if consult:
                ref.consultation_id = consult.id
                ref.visit_id = consult.visit_id
                updated = True
                print(f"[DATA MIGRATION] Linked Referral #{ref.id} ('{ref.referral_id}') -> Visit #{consult.visit_id}, Consultation #{consult.id}")
            else:
                # If no consultation, check for visit directly
                v = Visit.objects.filter(
                    patient_id=ref.patient_id,
                    facility_id=ref.source_facility_id
                ).order_by('-opd_date').first()
                if v:
                    ref.visit_id = v.id
                    updated = True
                    print(f"[DATA MIGRATION] Linked Referral #{ref.id} ('{ref.referral_id}') -> Visit #{v.id} (no consultation found)")

        if updated:
            ref.save(update_fields=['visit_id', 'consultation_id'])

def reverse_populate(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('referrals', '0002_referral_consultation_referral_visit'),
        ('consultations', '0001_initial'),
        ('visits', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_referral_encounter, reverse_populate),
    ]

# Generated manually for Phase 27B OPD Token Cutover Safety

from django.db import migrations, models


def sync_daily_counters(apps, schema_editor):
    Token = apps.get_model('visits', 'Token')
    FacilityDailyCounter = apps.get_model('visits', 'FacilityDailyCounter')

    token_groups = Token.objects.values('facility_id', 'date').annotate(max_tok=models.Max('token_number'))
    for tg in token_groups:
        fac_id = tg['facility_id']
        dt = tg['date']
        max_tok = tg['max_tok'] or 0
        counter, created = FacilityDailyCounter.objects.get_or_create(
            facility_id=fac_id,
            counter_date=dt,
            counter_type='OPD',
            defaults={'last_token_number': max_tok}
        )
        if not created and counter.last_token_number < max_tok:
            counter.last_token_number = max_tok
            counter.save(update_fields=['last_token_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0004_facilitydailycounter'),
    ]

    operations = [
        migrations.RunPython(sync_daily_counters, migrations.RunPython.noop),
    ]

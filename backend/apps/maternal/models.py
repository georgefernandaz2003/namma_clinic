from django.db import models

class MaternalRecord(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='maternal_records')
    anc_number = models.CharField(max_length=50, unique=True)
    lmp_date = models.DateField()
    edd_date = models.DateField()
    high_risk_flag = models.BooleanField(default=False)
    high_risk_reason = models.CharField(max_length=200, blank=True)
    anc_checkups_count = models.IntegerField(default=1)
    tt_vaccine_given = models.BooleanField(default=True)
    ifa_tablets_issued = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='ACTIVE')

    def __str__(self):
        return f"Maternal ANC #{self.anc_number} - {self.patient.name}"

from django.db import models

class NCDRecord(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='ncd_records')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    screening_date = models.DateField(auto_now_add=True)
    
    hypertension_screened = models.BooleanField(default=True)
    hypertension_diagnosed = models.BooleanField(default=False)
    diabetes_screened = models.BooleanField(default=True)
    diabetes_diagnosed = models.BooleanField(default=False)
    
    risk_level = models.CharField(max_length=20, default='LOW') # LOW, MODERATE, HIGH
    treatment_status = models.CharField(max_length=30, default='UNDER_TREATMENT')
    control_status = models.CharField(max_length=30, default='CONTROLLED') # CONTROLLED or UNCONTROLLED
    last_bp = models.CharField(max_length=20, default='120/80')
    last_glucose = models.IntegerField(default=110)
    next_followup_due = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"NCD Record - {self.patient.name} [{self.risk_level} Risk]"

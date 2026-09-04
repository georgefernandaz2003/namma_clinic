from django.db import models

class ChildRecord(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='child_records')
    maternal_record = models.ForeignKey('maternal.MaternalRecord', on_delete=models.SET_NULL, null=True, blank=True)
    birth_weight_kg = models.DecimalField(max_digits=4, decimal_places=2, default=3.10)
    immunization_status = models.CharField(max_length=50, default='UP_TO_DATE')
    sam_mam_status = models.CharField(max_length=30, default='NORMAL') # NORMAL, MAM, SAM
    growth_chart_status = models.CharField(max_length=30, default='GREEN_ZONE')

    def __str__(self):
        return f"Child Record - {self.patient.name} ({self.growth_chart_status})"

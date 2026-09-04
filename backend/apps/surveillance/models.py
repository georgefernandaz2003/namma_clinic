from django.db import models

class DiseaseCase(models.Model):
    disease_name = models.CharField(max_length=100) # Fever, Dengue, Gastroenteritis, Acute Respiratory Illness, Malaria
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    ward = models.ForeignKey('geography.Ward', on_delete=models.SET_NULL, null=True, blank=True)
    report_date = models.DateField(auto_now_add=True)
    severity = models.CharField(max_length=20, default='MILD') # MILD, MODERATE, SEVERE
    status = models.CharField(max_length=20, default='CONFIRMED')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.disease_name} - {self.patient.name} ({self.ward.name if self.ward else 'N/A'})"

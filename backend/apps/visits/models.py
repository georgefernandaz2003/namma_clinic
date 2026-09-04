from django.db import models

class Visit(models.Model):
    visit_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='visits')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateTimeField(auto_now_add=True)
    visit_type = models.CharField(max_length=40, default='GENERAL_OPD')
    status = models.CharField(max_length=30, choices=[
        ('WAITING', 'Waiting for Triage'),
        ('TRIAGED', 'Ready for Doctor'),
        ('IN_CONSULTATION', 'In Consultation'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ], default='WAITING')
    chief_complaint = models.TextField(blank=True)
    assigned_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_visits')

    def __str__(self):
        return f"Visit {self.visit_id} - {self.patient.name}"

class Token(models.Model):
    token_number = models.IntegerField()
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='token')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    priority = models.CharField(max_length=20, choices=[
        ('NORMAL', 'Normal Queue'),
        ('EMERGENCY', 'Emergency Priority'),
        ('MATERNAL', 'Maternal / High-Risk'),
        ('SENIOR_CITIZEN', 'Senior Citizen')
    ], default='NORMAL')
    status = models.CharField(max_length=20, default='WAITING')

    def __str__(self):
        return f"Token #{self.token_number} [{self.priority}] - {self.facility.facility_name}"

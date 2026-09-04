from django.db import models

class Teleconsultation(models.Model):
    teleconsult_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    clinic_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='teleconsult_requests')
    hub_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='teleconsult_hubs')
    requesting_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='teleconsult_requests')
    specialist_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='teleconsult_responses')
    
    specialty_required = models.CharField(max_length=100, default='General Medicine / Cardiology')
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('REQUESTED', 'Requested'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ], default='REQUESTED')
    
    clinical_notes = models.TextField(blank=True)
    specialist_advice = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Teleconsult {self.teleconsult_id} - {self.patient.name}"

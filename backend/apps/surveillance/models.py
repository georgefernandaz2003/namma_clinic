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

import datetime

class DiseaseMaster(models.Model):
    disease_code = models.CharField(max_length=50, unique=True)
    disease_name = models.CharField(max_length=150)
    transmission_type = models.CharField(max_length=50) # 'VECTOR_BORNE', 'WATER_BORNE', 'AIR_BORNE'
    is_notifiable_state = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'disease_masters'

    def __str__(self):
        return f"{self.disease_name} [{self.disease_code}]"

class DiseaseSurveillanceCase(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.RESTRICT, related_name='surveillance_cases')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='surveillance_cases')
    disease = models.ForeignKey(DiseaseMaster, on_delete=models.RESTRICT, related_name='cases')
    reporting_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='reported_surveillance_cases')
    ward = models.ForeignKey('geography.Ward', on_delete=models.RESTRICT, null=True, blank=True, related_name='surveillance_cases')
    case_number = models.CharField(max_length=50, unique=True)
    diagnosis_date = models.DateField(default=datetime.date.today)
    severity = models.CharField(max_length=20, default='MILD', choices=[
        ('MILD', 'Mild'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe'),
        ('CRITICAL', 'Critical')
    ])
    status = models.CharField(max_length=20, default='SUSPECTED', choices=[
        ('SUSPECTED', 'Suspected'),
        ('PROBABLE', 'Probable'),
        ('CONFIRMED', 'Confirmed'),
        ('RECOVERED', 'Recovered'),
        ('DECEASED', 'Deceased')
    ])
    lab_confirmed = models.BooleanField(default=False)
    diagnostic_result = models.ForeignKey('laboratory.DiagnosticResult', on_delete=models.RESTRICT, null=True, blank=True, related_name='surveillance_cases')
    investigation_notes = models.TextField(blank=True, default='')
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'disease_surveillance_cases'

    def __str__(self):
        return f"Case {self.case_number}: {self.disease.disease_name} [{self.status}]"

class PublicHealthNotification(models.Model):
    case = models.ForeignKey(DiseaseSurveillanceCase, on_delete=models.CASCADE, related_name='notifications')
    notified_authority = models.CharField(max_length=100) # 'DISTRICT_SURVEILLANCE_OFFICER', 'STATE_IDSP'
    transmission_status = models.CharField(max_length=20, default='QUEUED', choices=[
        ('QUEUED', 'Queued'),
        ('DISPATCHED', 'Dispatched'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('FAILED', 'Failed')
    ])
    dispatch_payload = models.JSONField()
    dispatched_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'public_health_notifications'

    def __str__(self):
        return f"Notification for Case #{self.case_id} -> {self.notified_authority} [{self.transmission_status}]"

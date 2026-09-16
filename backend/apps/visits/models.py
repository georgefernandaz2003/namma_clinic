from django.db import models
from django.utils import timezone
import datetime

class Visit(models.Model):
    STATUS_CHOICES = [
        ('WAITING_FOR_TRIAGE', 'Waiting for Triage'),
        ('IN_TRIAGE', 'In Triage'),
        ('TRIAGED', 'Triaged / Ready for Doctor'),
        ('WAITING_FOR_DOCTOR', 'Waiting for Doctor'),
        ('IN_CONSULTATION', 'In Consultation'),
        ('LAB_PENDING', 'Lab Pending'),
        ('LAB_IN_PROGRESS', 'Lab Test In Progress'),
        ('LAB_COMPLETED', 'Lab Test Completed'),
        ('WAITING_FOR_PHARMACY', 'Waiting for Pharmacy'),
        ('IN_PHARMACY', 'In Pharmacy Dispensing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show')
    ]

    QUEUE_CHOICES = [
        ('TRIAGE', 'Nurse Triage Queue'),
        ('DOCTOR', 'Doctor Consultation Queue'),
        ('LAB', 'Laboratory Queue'),
        ('PHARMACY', 'Pharmacy Dispensing Queue'),
        ('COMPLETED', 'Completed Visit')
    ]

    PRIORITY_CHOICES = [
        ('EMERGENCY', 'Emergency Priority 🚨'),
        ('HIGH', 'High Priority'),
        ('NORMAL', 'Normal Queue')
    ]

    visit_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='visits')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateTimeField(default=timezone.now)
    opd_date = models.DateField(default=datetime.date.today, db_index=True)
    visit_type = models.CharField(max_length=40, default='GENERAL_OPD')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    current_queue = models.CharField(max_length=30, choices=QUEUE_CHOICES, default='TRIAGE')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='WAITING_FOR_TRIAGE')
    chief_complaint = models.TextField(blank=True)
    assigned_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_visits')

    # Timestamps for dynamic waiting time & audit duration calculations
    arrival_time = models.DateTimeField(default=timezone.now)
    triage_start_time = models.DateTimeField(null=True, blank=True)
    triage_end_time = models.DateTimeField(null=True, blank=True)
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    completed_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opd_date', 'arrival_time']

    def __str__(self):
        return f"Visit {self.visit_id} ({self.opd_date}) - {self.patient.name}"


class Token(models.Model):
    token_number = models.IntegerField()
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='token')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='tokens')
    date = models.DateField(default=datetime.date.today, db_index=True)
    priority = models.CharField(max_length=20, choices=Visit.PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=30, default='WAITING')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['facility', 'date', 'token_number'], name='unique_facility_opd_date_token')
        ]
        ordering = ['date', 'token_number']

    def __str__(self):
        return f"Token #{self.token_number} ({self.date}) - {self.facility.facility_name}"


class VisitStatusHistory(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    queue = models.CharField(max_length=30)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    performed_by_role = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.visit.visit_id}: {self.from_status} -> {self.to_status} at {self.timestamp}"

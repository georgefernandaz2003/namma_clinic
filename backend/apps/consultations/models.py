from django.db import models
from django.core.exceptions import ValidationError

class Consultation(models.Model):
    visit = models.OneToOneField('visits.Visit', on_delete=models.CASCADE, related_name='consultation')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    
    chief_complaint = models.TextField()
    clinical_history = models.TextField(blank=True)
    clinical_assessment = models.TextField(blank=True)
    
    diagnosis_code = models.CharField(max_length=50, default='E11')
    diagnosis_name = models.CharField(max_length=200, default='Type 2 Diabetes Mellitus / Essential Hypertension')
    
    treatment_plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    clinical_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation - {self.patient.name} - {self.diagnosis_name}"

class Prescription(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='prescription')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDING_VERIFICATION', 'Pending Pharmacist Verification'),
        ('VERIFIED', 'Verified by Pharmacist'),
        ('ON_HOLD', 'Clinical Hold (Query Pending)'),
        ('REJECTED', 'Rejected by Pharmacist'),
        ('PARTIALLY_DISPENSED', 'Partially Dispensed'),
        ('DISPENSED', 'Fully Dispensed'),
        ('CANCELLED', 'Cancelled by Prescriber / Admin'),
        ('EXPIRED', 'Prescription Validity Expired'),
        ('ACTIVE', 'Active (Legacy Dispensable Status)'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_VERIFICATION')
    notes = models.TextField(blank=True)
    
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_prescriptions')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.status == 'DISPENSED' and self.pk:
            if self.items.filter(status__in=['PENDING', 'PARTIALLY_DISPENSED']).exists():
                raise ValidationError({
                    'status': 'Prescription status cannot be set to DISPENSED while one or more items remain PENDING or PARTIALLY_DISPENSED.'
                })

    def save(self, *args, **kwargs):
        if self.status == 'DISPENSED' and self.pk:
            if self.items.filter(status__in=['PENDING', 'PARTIALLY_DISPENSED']).exists():
                raise ValidationError({
                    'status': 'Prescription status cannot be set to DISPENSED while one or more items remain PENDING or PARTIALLY_DISPENSED.'
                })
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prescription #{self.id} for {self.patient.name} ({self.status})"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('pharmacy.MedicineMaster', on_delete=models.SET_NULL, null=True, blank=True, related_name='prescription_items')
    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=50, default='1-0-1 After Food')
    frequency = models.CharField(max_length=50, default='Twice Daily')
    duration_days = models.IntegerField(default=7)
    quantity = models.IntegerField(default=14)
    dispensed_quantity = models.IntegerField(default=0)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Dispensation'),
        ('PARTIALLY_DISPENSED', 'Partially Dispensed'),
        ('DISPENSED', 'Fully Dispensed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    @property
    def remaining_quantity(self):
        return max(0, self.quantity - self.dispensed_quantity)

    def __str__(self):
        return f"{self.medicine_name} ({self.dispensed_quantity}/{self.quantity} dispensed) - {self.status}"

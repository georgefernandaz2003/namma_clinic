from django.db import models

class Patient(models.Model):
    patient_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(default=30)
    gender = models.CharField(max_length=10, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    mobile = models.CharField(max_length=20)
    address = models.TextField()
    ward = models.ForeignKey('geography.Ward', on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    district = models.ForeignKey('geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    ABHA_ID_DEMO = models.CharField(max_length=50, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    vulnerability_information = models.CharField(max_length=100, default='Slum Resident / Low Income Group')
    registration_date = models.DateField(auto_now_add=True)
    registered_at_facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='registered_patients')

    def __str__(self):
        return f"{self.name} [{self.patient_id}] - {self.mobile}"

class Household(models.Model):
    household_id = models.CharField(max_length=50, unique=True)
    head_name = models.CharField(max_length=150)
    address = models.TextField()
    ward = models.ForeignKey('geography.Ward', on_delete=models.SET_NULL, null=True, blank=True)
    members_count = models.IntegerField(default=4)
    vulnerable_category = models.CharField(max_length=100, default='Slum Household')
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Household {self.household_id} - {self.head_name}"

import datetime

def patient_document_upload_path(instance, filename):
    patient_slug = instance.patient.patient_id.replace('/', '_') if instance and instance.patient else 'general'
    return f'patient_records/{patient_slug}/{filename}'

DOCUMENT_TYPE_CHOICES = [
    ('MEDICAL_RECORD', 'Medical Record'),
    ('LAB_REPORT', 'Lab Report'),
    ('PRESCRIPTION', 'Prescription'),
    ('DISCHARGE_SUMMARY', 'Discharge Summary'),
    ('REFERRAL_DOCUMENT', 'Referral Document'),
    ('OTHER', 'Other Medical Document'),
]

class PatientDocument(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='documents')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, default='OTHER')
    file = models.FileField(upload_to=patient_document_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    document_date = models.DateField(default=datetime.date.today)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_patient_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='ACTIVE', choices=[('ACTIVE', 'Active'), ('ARCHIVED', 'Archived')])

    class Meta:
        ordering = ['-document_date', '-uploaded_at']

    def __str__(self):
        return f"{self.title} [{self.document_type}] - Patient {self.patient.patient_id}"

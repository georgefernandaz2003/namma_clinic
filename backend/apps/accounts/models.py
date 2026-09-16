from django.db import models
from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices):
    DISTRICT_OFFICER = 'DISTRICT_OFFICER', 'District Officer'
    HOSPITAL_ADMIN = 'HOSPITAL_ADMIN', 'Hospital Administrator'
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse'
    LAB_TECHNICIAN = 'LAB_TECHNICIAN', 'Lab Technician'
    PHARMACIST = 'PHARMACIST', 'Pharmacist'

class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=30, choices=RoleChoices.choices, default=RoleChoices.DOCTOR)
    assigned_facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    assigned_district = models.ForeignKey('geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

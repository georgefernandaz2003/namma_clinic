from django.db import models
from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    DISTRICT_ADMIN = 'DISTRICT_ADMIN', 'District Officer'
    ULB_ADMIN = 'ULB_ADMIN', 'ULB Health Officer'
    HOSPITAL_ADMIN = 'HOSPITAL_ADMIN', 'Hospital Administrator'
    MEDICAL_OFFICER = 'MEDICAL_OFFICER', 'Medical Officer / Doctor'
    STAFF_NURSE = 'STAFF_NURSE', 'Staff Nurse'
    LAB_TECHNICIAN = 'LAB_TECHNICIAN', 'Lab Technician'
    PHARMACIST = 'PHARMACIST', 'Pharmacist'
    LDC = 'LDC', 'Lower Division Clerk (LDC)'
    PUBLIC_HEALTH_OFFICER = 'PUBLIC_HEALTH_OFFICER', 'Public Health Officer'

class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=30, choices=RoleChoices.choices, default=RoleChoices.MEDICAL_OFFICER)
    assigned_facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    assigned_district = models.ForeignKey('geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

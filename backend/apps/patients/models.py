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

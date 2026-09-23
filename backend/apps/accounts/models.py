import uuid
import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices):
    DISTRICT_OFFICER = 'DISTRICT_OFFICER', 'District Officer'
    HOSPITAL_ADMIN = 'HOSPITAL_ADMIN', 'Hospital Administrator'
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse'
    LAB_TECHNICIAN = 'LAB_TECHNICIAN', 'Lab Technician'
    PHARMACIST = 'PHARMACIST', 'Pharmacist'

class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    gender = models.CharField(max_length=20, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    aadhaar_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'persons'

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class StaffProfile(models.Model):
    person = models.ForeignKey(Person, on_delete=models.RESTRICT, related_name='staff_profiles')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100)
    medical_council_reg_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    status = models.CharField(max_length=20, default='ACTIVE', choices=[
        ('PROBATION', 'Probation'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('RETIRED', 'Retired'),
        ('RESIGNED', 'Resigned')
    ])
    department = models.ForeignKey('facilities.Department', on_delete=models.RESTRICT, null=True, blank=True, related_name='staff_members')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_profiles'

    def __str__(self):
        return f"{self.employee_id} - {self.designation} ({self.person.first_name})"

class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=30, choices=RoleChoices.choices, default=RoleChoices.DOCTOR)
    assigned_facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    assigned_district = models.ForeignKey('geography.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    phone = models.CharField(max_length=20, blank=True)
    staff_profile = models.OneToOneField(StaffProfile, on_delete=models.RESTRICT, null=True, blank=True, related_name='user_account')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class RoleMaster(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role_masters'

    def __str__(self):
        return f"{self.name} [{self.code}]"

class StaffRoleAssignment(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.RESTRICT, related_name='role_assignments')
    role = models.ForeignKey(RoleMaster, on_delete=models.RESTRICT, related_name='staff_assignments')
    effective_from = models.DateField(default=datetime.date.today)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'staff_role_assignments'
        constraints = [
            models.CheckConstraint(
                check=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F('effective_from')),
                name='chk_staff_role_dates'
            )
        ]

    def __str__(self):
        return f"{self.staff.employee_id} -> {self.role.code} (from {self.effective_from})"

class StaffFacilityAssignment(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.RESTRICT, related_name='facility_assignments')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='staff_facility_assignments')
    department = models.ForeignKey('facilities.Department', on_delete=models.RESTRICT, null=True, blank=True, related_name='staff_facility_assignments')
    is_primary = models.BooleanField(default=False)
    effective_from = models.DateField(default=datetime.date.today)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'staff_facility_assignments'
        constraints = [
            models.CheckConstraint(
                check=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F('effective_from')),
                name='chk_staff_facility_dates'
            )
        ]

    def __str__(self):
        return f"{self.staff.employee_id} -> Facility #{self.facility_id} ({'Primary' if self.is_primary else 'Visiting'})"

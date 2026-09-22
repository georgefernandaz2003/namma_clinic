from django.db import models

class LabTestMaster(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='General Biochemistry')
    reference_range = models.CharField(max_length=100, default='70 - 110 mg/dL')
    unit = models.CharField(max_length=20, default='mg/dL')

    def __str__(self):
        return f"{self.name} ({self.code})"

import datetime

class LabToken(models.Model):
    token_number = models.IntegerField()
    token_code = models.CharField(max_length=50)
    visit = models.ForeignKey('visits.Visit', on_delete=models.CASCADE, related_name='lab_tokens')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='lab_tokens')
    date = models.DateField(default=datetime.date.today, db_index=True)
    status = models.CharField(max_length=30, choices=[
        ('ORDERED', 'Ordered'),
        ('IN_PROGRESS', 'Sample Collected / In Progress'),
        ('COMPLETED', 'Completed & Verified')
    ], default='ORDERED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'token_number']
        constraints = [
            models.UniqueConstraint(fields=['facility', 'date', 'token_number'], name='unique_facility_lab_date_token')
        ]

    def __str__(self):
        return f"{self.token_code} ({self.date}) - {self.facility.facility_name}"


class LabOrder(models.Model):
    lab_token = models.ForeignKey(LabToken, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_orders')
    consultation = models.ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_orders')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    test_master = models.ForeignKey(LabTestMaster, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('ORDERED', 'Ordered'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('RESULT_ENTRY', 'Result Entered'),
        ('VERIFIED', 'Verified & Released')
    ], default='ORDERED')

    def __str__(self):
        return f"Lab Order #{self.id} - {self.test_master.name} for {self.patient.name}"

class LabSample(models.Model):
    lab_order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='sample')
    sample_type = models.CharField(max_length=50, default='Blood')
    sample_code = models.CharField(max_length=50, unique=True)
    collected_at = models.DateTimeField(auto_now_add=True)
    collected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Sample {self.sample_code} ({self.sample_type})"

class LabResult(models.Model):
    lab_order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='result')
    result_value = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    interpretation_flag = models.CharField(max_length=20, choices=[
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('LOW', 'Low'),
        ('CRITICAL', 'Critical')
    ], default='NORMAL')
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Result for {self.lab_order.test_master.name}: {self.result_value} [{self.interpretation_flag}]"

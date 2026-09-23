from django.db import models

class NCDRecord(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='ncd_records')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    screening_date = models.DateField(auto_now_add=True)
    
    hypertension_screened = models.BooleanField(default=True)
    hypertension_diagnosed = models.BooleanField(default=False)
    diabetes_screened = models.BooleanField(default=True)
    diabetes_diagnosed = models.BooleanField(default=False)
    
    risk_level = models.CharField(max_length=20, default='LOW') # LOW, MODERATE, HIGH
    treatment_status = models.CharField(max_length=30, default='UNDER_TREATMENT')
    control_status = models.CharField(max_length=30, default='CONTROLLED') # CONTROLLED or UNCONTROLLED
    last_bp = models.CharField(max_length=20, default='120/80')
    last_glucose = models.IntegerField(default=110)
    next_followup_due = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"NCD Record - {self.patient.name} [{self.risk_level} Risk]"

import datetime

class NCDCondition(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.RESTRICT, related_name='ncd_conditions')
    registering_facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='registered_ncd_conditions')
    registering_doctor = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='registered_ncd_conditions')
    condition_code = models.CharField(max_length=50) # 'HYPERTENSION', 'DIABETES_T2', 'COPD', 'CVD'
    diagnosis_date = models.DateField(default=datetime.date.today)
    staging = models.CharField(max_length=50, blank=True, default='')
    control_status = models.CharField(max_length=30, default='SCREENED', choices=[
        ('SCREENED', 'Screened'),
        ('CONFIRMED', 'Confirmed'),
        ('CONTROLLED', 'Controlled'),
        ('UNCONTROLLED', 'Uncontrolled'),
        ('REMISSION', 'Remission')
    ])
    is_active = models.BooleanField(default=True)
    treatment_plan = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ncd_conditions'
        unique_together = [('patient', 'condition_code')]

    def __str__(self):
        return f"NCDCondition {self.condition_code} for Patient #{self.patient_id}"

class NCDAssessment(models.Model):
    condition = models.ForeignKey(NCDCondition, on_delete=models.RESTRICT, related_name='assessments')
    visit = models.ForeignKey('visits.Visit', on_delete=models.RESTRICT, related_name='ncd_assessments')
    assessed_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='performed_ncd_assessments')
    assessment_date = models.DateTimeField(auto_now_add=True)
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    blood_glucose_fasting = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    blood_glucose_postprandial = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    clinical_notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ncd_assessments'

    def __str__(self):
        return f"NCDAssessment for Condition #{self.condition_id} on {self.assessment_date}"

from django.db import models

class TriageVitals(models.Model):
    visit = models.OneToOneField('visits.Visit', on_delete=models.CASCADE, related_name='triage')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    nurse = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    blood_pressure_systolic = models.IntegerField(default=120)
    blood_pressure_diastolic = models.IntegerField(default=80)
    pulse_bpm = models.IntegerField(default=72)
    temperature_f = models.DecimalField(max_digits=4, decimal_places=1, default=98.6)
    spo2_percent = models.IntegerField(default=98)
    respiratory_rate = models.IntegerField(default=18)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, default=165.0)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, default=65.0)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, default=23.8)
    blood_glucose_mgdl = models.IntegerField(default=110)
    
    # Workflow warning flags (not autonomous diagnosis)
    high_bp_flag = models.BooleanField(default=False)
    high_glucose_flag = models.BooleanField(default=False)
    fever_flag = models.BooleanField(default=False)
    low_spo2_flag = models.BooleanField(default=False)
    pregnancy_high_risk_flag = models.BooleanField(default=False)
    emergency_flag = models.BooleanField(default=False)
    ncd_risk_flag = models.BooleanField(default=False)
    
    nurse_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-compute flags for triage workflow assistance
        self.high_bp_flag = self.blood_pressure_systolic >= 140 or self.blood_pressure_diastolic >= 90
        self.high_glucose_flag = self.blood_glucose_mgdl >= 160
        self.fever_flag = self.temperature_f >= 100.4
        self.low_spo2_flag = self.spo2_percent < 95
        if self.height_cm > 0:
            h_m = float(self.height_cm) / 100.0
            self.bmi = round(float(self.weight_kg) / (h_m * h_m), 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Triage Vitals - {self.patient.name} ({self.blood_pressure_systolic}/{self.blood_pressure_diastolic} BP)"

class Triage(models.Model):
    visit = models.OneToOneField('visits.Visit', on_delete=models.CASCADE, related_name='triage_observation')
    triaged_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='triages')
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    pulse_rate = models.IntegerField(null=True, blank=True)
    temperature_celsius = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    spo2_percentage = models.IntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'triages'
        constraints = [
            models.CheckConstraint(check=models.Q(systolic_bp__isnull=True) | models.Q(systolic_bp__range=(40, 300)), name='chk_triages_bp_sys'),
            models.CheckConstraint(check=models.Q(diastolic_bp__isnull=True) | models.Q(diastolic_bp__range=(30, 200)), name='chk_triages_bp_dia'),
            models.CheckConstraint(check=models.Q(spo2_percentage__isnull=True) | models.Q(spo2_percentage__range=(50, 100)), name='chk_triages_spo2'),
            models.CheckConstraint(check=models.Q(pulse_rate__isnull=True) | models.Q(pulse_rate__range=(30, 250)), name='chk_triages_pulse'),
        ]

    def __str__(self):
        return f"Triage for Visit #{self.visit_id} by Staff #{self.triaged_by_staff_id}"

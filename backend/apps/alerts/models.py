from django.db import models

class Alert(models.Model):
    alert_type = models.CharField(max_length=40, choices=[
        ('LOW_STOCK', 'Low Medicine Stock'),
        ('NEAR_EXPIRY', 'Near Expiry Medicine Batch'),
        ('EXPIRED', 'Expired Stock Alert'),
        ('REFERRAL_OVERDUE', 'Referral Overdue'),
        ('FOLLOWUP_OVERDUE', 'Follow-up Overdue'),
        ('LAB_PENDING', 'Lab Result Pending Verification'),
        ('DISEASE_THRESHOLD', 'Public Health Disease Anomaly Threshold Exceeded'),
        ('HIGH_RISK_FOLLOWUP', 'High-Risk Patient Follow-up Due'),
        ('MISSING_REPORT', 'Clinic Reporting Delayed')
    ])
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low Severity'),
        ('MEDIUM', 'Medium Severity'),
        ('HIGH', 'High Severity'),
        ('CRITICAL', 'Critical Alert')
    ], default='MEDIUM')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('NEW', 'New Alert'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved')
    ], default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"[{self.severity}] {self.title} @ {self.facility.facility_name}"

class OperationalAlert(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='operational_alerts')
    acknowledged_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, null=True, blank=True, related_name='acknowledged_alerts')
    alert_category = models.CharField(max_length=50) # 'PANIC_LAB', 'DRUG_EXPIRY', 'EPIDEMIC_SURGE'
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, default='INFO', choices=[
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical')
    ])
    is_active = models.BooleanField(default=True)
    source_entity_type = models.CharField(max_length=50, blank=True, null=True)
    source_entity_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'operational_alerts'

    def __str__(self):
        return f"[{self.severity}] {self.title} @ Facility #{self.facility_id}"

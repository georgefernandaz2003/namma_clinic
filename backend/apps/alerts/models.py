from django.db import models

class Alert(models.Model):
    alert_type = models.CharField(max_length=50, choices=[
        ('LOW_STOCK', 'Low Medicine Stock'),
        ('NEAR_EXPIRY', 'Near Expiry Medicine Batch'),
        ('EXPIRED', 'Expired Stock Alert'),
        ('REFERRAL_OVERDUE', 'Referral Overdue'),
        ('FOLLOWUP_OVERDUE', 'Follow-up Overdue'),
        ('LAB_PENDING', 'Lab Result Pending Verification'),
        ('DISEASE_THRESHOLD', 'Public Health Disease Anomaly Threshold Exceeded'),
        ('HIGH_RISK_FOLLOWUP', 'High-Risk Patient Follow-up Due'),
        ('MISSING_REPORT', 'Clinic Reporting Delayed'),
        # Step 4: Public Health Intelligence Signals
        ('INTELLIGENCE_TREND', 'Disease Trend Increase Signal'),
        ('INTELLIGENCE_LOCALITY', 'High Locality Concentration Signal'),
        ('INTELLIGENCE_FORECAST', 'Forecast Surveillance Signal'),
        ('INTELLIGENCE_SEASONALITY', 'Seasonal Surveillance Signal'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('INFO', 'Informational Signal'),
        ('LOW', 'Low Severity'),
        ('MEDIUM', 'Medium Severity'),
        ('WARNING', 'Warning Signal'),
        ('HIGH', 'High Severity'),
        ('CRITICAL', 'Critical Alert'),
    ], default='MEDIUM')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    district = models.ForeignKey('geography.District', on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('NEW', 'New Alert'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    ], default='NEW')
    fingerprint = models.CharField(max_length=255, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        'accounts.User',
        related_name='acknowledged_alerts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'accounts.User',
        related_name='resolved_alerts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    resolution_notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"[{self.severity}] {self.title} @ {self.facility.facility_name}"

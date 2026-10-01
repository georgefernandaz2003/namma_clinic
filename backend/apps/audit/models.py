from django.db import models

class AuditLog(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    username_snapshot = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=100) # LOGIN, PATIENT_CREATE, CONSULTATION_SAVE, DISPENSE_MEDICINE, REFERRAL_RAISED, etc.
    facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.username_snapshot} - {self.action}"

class AuditLogEntry(models.Model):
    event_timestamp = models.DateTimeField(auto_now_add=True)
    actor_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, null=True, blank=True, related_name='audit_entries')
    actor_user_id = models.BigIntegerField(null=True, blank=True)
    actor_role_snapshot = models.CharField(max_length=50)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, null=True, blank=True, related_name='audit_entries')
    action_type = models.CharField(max_length=20, choices=[
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW_CONFIDENTIAL', 'View Confidential')
    ])
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    payload_before = models.JSONField(null=True, blank=True)
    payload_after = models.JSONField(null=True, blank=True)
    correlation_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'audit_log_entries'

    def __str__(self):
        return f"[{self.event_timestamp}] {self.action_type} on {self.table_name}:{self.record_id} by Staff #{self.actor_staff_id}"

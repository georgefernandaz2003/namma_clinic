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

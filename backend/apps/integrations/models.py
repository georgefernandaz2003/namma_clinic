from django.db import models

class IntegrationConfiguration(models.Model):
    system_name = models.CharField(max_length=50, unique=True) # ABDM, ABHA, HMIS, RCH, E_AUSHADA, TELEMEDICINE
    display_name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, default='MOCK') # NOT_CONFIGURED, MOCK, READY, CONNECTED
    last_sync_time = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=30, default='SUCCESS')
    notes = models.TextField(default='Demo mock integration - local simulation mode. No external APIs connected.')

    def __str__(self):
        return f"Integration: {self.display_name} [{self.status}]"

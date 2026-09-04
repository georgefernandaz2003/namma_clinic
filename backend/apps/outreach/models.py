from django.db import models

class OutreachActivity(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    ward = models.ForeignKey('geography.Ward', on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=100, default='Household Survey / Slum Health Camp')
    activity_date = models.DateField()
    households_covered = models.IntegerField(default=50)
    persons_screened = models.IntegerField(default=120)
    vulnerable_identified = models.IntegerField(default=15)
    conducted_by = models.CharField(max_length=150, default='ASHA & Staff Nurse Team')
    summary_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Outreach - {self.activity_type} on {self.activity_date}"

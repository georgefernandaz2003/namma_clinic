# Reports app models (aggregation logic in views)
from django.db import models

class ReportExportLog(models.Model):
    report_type = models.CharField(max_length=50)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    records_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Report {self.report_type} on {self.generated_at}"

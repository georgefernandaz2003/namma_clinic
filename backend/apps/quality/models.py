from django.db import models

class QualityChecklist(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    inspection_date = models.DateField(auto_now_add=True)
    cleanliness_score = models.IntegerField(default=95) # Percentage
    infection_control_passed = models.BooleanField(default=True)
    kayakalpa_audit_status = models.CharField(max_length=50, default='COMPLIANT')
    corrective_actions = models.TextField(blank=True)
    inspected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Quality Audit {self.facility.facility_name} - {self.inspection_date}"

class BiomedicalWasteLog(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    yellow_bag_kg = models.DecimalField(max_digits=5, decimal_places=2, default=2.50) # Anatomical & Soiled
    red_bag_kg = models.DecimalField(max_digits=5, decimal_places=2, default=1.80)    # Contaminated Recyclable
    white_translucent_sharp_kg = models.DecimalField(max_digits=5, decimal_places=2, default=0.50) # Sharps
    blue_box_glass_kg = models.DecimalField(max_digits=5, decimal_places=2, default=1.20)         # Glassware
    disposal_agency = models.CharField(max_length=150, default='Authorized CBWTF Vendor')
    handed_over_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Bio-Medical Waste Log {self.facility.facility_name} on {self.date}"

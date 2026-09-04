from django.db import models

class ARSMember(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='ars_members')
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100) # Chairman (Ward Member/Corporator), Member Secretary (Medical Officer), ASHA rep, Community rep
    mobile = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name} ({self.designation})"

class ARSMeeting(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    meeting_date = models.DateField()
    chairperson_name = models.CharField(max_length=150)
    attendees_count = models.IntegerField(default=7)
    agenda = models.TextField()
    proceedings_summary = models.TextField()
    untied_funds_spent_rs = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    signed_by_chairman = models.BooleanField(default=True)

    def __str__(self):
        return f"ARS Meeting on {self.meeting_date} - {self.facility.facility_name}"

class ARSActionItem(models.Model):
    meeting = models.ForeignKey(ARSMeeting, on_delete=models.CASCADE, related_name='action_items')
    task_description = models.TextField()
    responsible_person = models.CharField(max_length=150)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='PENDING') # PENDING, IN_PROGRESS, COMPLETED

    def __str__(self):
        return f"Action Item: {self.task_description[:30]} [{self.status}]"

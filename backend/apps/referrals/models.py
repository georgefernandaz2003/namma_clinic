from django.db import models

class Referral(models.Model):
    referral_id = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='referrals')
    visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    consultation = models.ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    source_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='outgoing_referrals')
    destination_facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='incoming_referrals')
    referring_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    reason = models.TextField()
    clinical_summary = models.TextField()
    required_service = models.CharField(max_length=100, default='Specialist Evaluation')
    urgency = models.CharField(max_length=20, choices=[
        ('ROUTINE', 'Routine Referral'),
        ('URGENT', 'Urgent Evaluation'),
        ('EMERGENCY', 'Emergency Referral')
    ], default='ROUTINE')
    
    referral_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('CREATED', 'Created'),
        ('ACCEPTED', 'Accepted by Hospital'),
        ('IN_TRANSIT', 'Patient in Transit'),
        ('REACHED', 'Reached Facility'),
        ('UNDER_TREATMENT', 'Under Treatment'),
        ('FOLLOW_UP_PENDING', 'Follow-up Pending'),
        ('COMPLETED', 'Completed'),
        ('CLOSED', 'Closed')
    ], default='CREATED')

    def __str__(self):
        return f"Referral {self.referral_id}: {self.source_facility.facility_name} -> {self.destination_facility.facility_name}"

class ReferralResponse(models.Model):
    referral = models.OneToOneField(Referral, on_delete=models.CASCADE, related_name='response')
    hospital_doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    specialist_findings = models.TextField()
    treatment_summary = models.TextField()
    return_advice = models.TextField()
    responded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response for Referral {self.referral.referral_id}"

class FollowUp(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='followups')
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL, null=True, blank=True)
    visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    category = models.CharField(max_length=30, default='NCD')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('DUE_TODAY', 'Due Today'),
        ('OVERDUE', 'Overdue'),
        ('COMPLETED', 'Completed')
    ], default='PENDING')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"FollowUp for {self.patient.name} [{self.category}] due {self.due_date}"

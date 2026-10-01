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
    URGENCY_CHOICES = [
        ('ROUTINE', 'Routine Referral'),
        ('URGENT', 'Urgent Evaluation'),
        ('EMERGENCY', 'Emergency Referral')
    ]

    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='ROUTINE')
    
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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.referral:
            if self.patient_id and self.referral.patient_id and self.patient_id != self.referral.patient_id:
                raise ValidationError("FollowUp patient must match Referral patient.")
            if self.visit_id and self.referral.visit_id and self.visit_id != self.referral.visit_id:
                raise ValidationError(f"FollowUp visit #{self.visit_id} must match Referral encounter visit #{self.referral.visit_id}.")

    def save(self, *args, **kwargs):
        if self.referral:
            if not self.visit_id and self.referral.visit_id:
                self.visit = self.referral.visit
            if not self.patient_id and self.referral.patient_id:
                self.patient = self.referral.patient
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"FollowUp for {self.patient.name} [{self.category}] due {self.due_date}"

import datetime

class ReferralOrder(models.Model):
    visit = models.ForeignKey('visits.Visit', on_delete=models.RESTRICT, related_name='referral_orders')
    patient = models.ForeignKey('patients.Patient', on_delete=models.RESTRICT, related_name='referral_orders')
    source_facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='outgoing_referral_orders')
    destination_facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='incoming_referral_orders')
    referring_doctor = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='authored_referral_orders')
    referral_number = models.CharField(max_length=50, unique=True)
    urgency = models.CharField(max_length=20, default='ROUTINE', choices=[
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency')
    ])
    reason = models.TextField()
    clinical_summary = models.TextField(blank=True, default='')
    status = models.CharField(max_length=30, default='INITIATED', choices=[
        ('INITIATED', 'Initiated'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('IN_TRANSIT', 'In Transit'),
        ('ARRIVED', 'Arrived'),
        ('UNDER_SPECIALIST_CARE', 'Under Specialist Care'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ])
    referral_date = models.DateField(default=datetime.date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'referral_orders'

    def __str__(self):
        return f"ReferralOrder {self.referral_number}: {self.source_facility_id} -> {self.destination_facility_id}"

class ReferralEvent(models.Model):
    referral = models.ForeignKey(ReferralOrder, on_delete=models.CASCADE, related_name='events')
    recorded_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='recorded_referral_events')
    event_type = models.CharField(max_length=30, choices=[
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('TRIAGED', 'Triaged'),
        ('SPECIALIST_CONSULT', 'Specialist Consult'),
        ('ADMITTED', 'Admitted'),
        ('COUNTER_REFERRAL_DISCHARGE', 'Counter Referral Discharge'),
        ('CANCELLED', 'Cancelled')
    ])
    specialist_findings = models.TextField(blank=True, default='')
    treatment_rendered = models.TextField(blank=True, default='')
    return_advice = models.TextField(blank=True, default='')
    event_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'referral_events'

    def __str__(self):
        return f"ReferralEvent [{self.event_type}] for Order #{self.referral_id}"

class FollowUpTask(models.Model):
    """Follow-up recall task. Database-level constraints enforce non-null completion linkage (completed_in_visit, completed_by_staff, completed_at) upon COMPLETED status. Cross-table patient and facility alignment is validated at the service layer."""
    patient = models.ForeignKey('patients.Patient', on_delete=models.RESTRICT, related_name='follow_up_tasks')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='follow_up_tasks')
    originating_visit = models.ForeignKey('visits.Visit', on_delete=models.RESTRICT, null=True, blank=True, related_name='originating_follow_ups')
    referral = models.ForeignKey(ReferralOrder, on_delete=models.RESTRICT, null=True, blank=True, related_name='follow_up_tasks')
    completed_in_visit = models.ForeignKey('visits.Visit', on_delete=models.RESTRICT, null=True, blank=True, related_name='completed_follow_ups')
    completed_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, null=True, blank=True, related_name='completed_follow_ups')
    due_date = models.DateField()
    category = models.CharField(max_length=30, default='GENERAL', choices=[
        ('NCD_ROUTINE', 'NCD Routine'),
        ('POST_REFERRAL', 'Post Referral'),
        ('LAB_REVIEW', 'Lab Review'),
        ('GENERAL', 'General')
    ])
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('CANCELLED', 'Cancelled')
    ])
    clinical_instructions = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_up_tasks'
        constraints = [
            models.CheckConstraint(
                check=(models.Q(status='COMPLETED', completed_in_visit__isnull=False, completed_by_staff__isnull=False, completed_at__isnull=False) | ~models.Q(status='COMPLETED')),
                name='chk_followup_completion_integrity'
            )
        ]

    def __str__(self):
        return f"FollowUpTask #{self.id} for {self.patient_id} [{self.status}]"

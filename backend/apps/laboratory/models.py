from django.db import models

class LabTestMaster(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='General Biochemistry')
    reference_range = models.CharField(max_length=100, default='70 - 110 mg/dL')
    unit = models.CharField(max_length=20, default='mg/dL')

    def __str__(self):
        return f"{self.name} ({self.code})"

import datetime

class LabToken(models.Model):
    token_number = models.IntegerField()
    token_code = models.CharField(max_length=50)
    visit = models.ForeignKey('visits.Visit', on_delete=models.CASCADE, related_name='lab_tokens')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='lab_tokens')
    date = models.DateField(default=datetime.date.today, db_index=True)
    status = models.CharField(max_length=30, choices=[
        ('ORDERED', 'Ordered'),
        ('IN_PROGRESS', 'Sample Collected / In Progress'),
        ('COMPLETED', 'Completed & Verified')
    ], default='ORDERED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'token_number']
        constraints = [
            models.UniqueConstraint(fields=['facility', 'date', 'token_number'], name='unique_facility_lab_date_token')
        ]

    def __str__(self):
        return f"{self.token_code} ({self.date}) - {self.facility.facility_name}"


class LabOrder(models.Model):
    lab_token = models.ForeignKey(LabToken, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_orders')
    consultation = models.ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_orders')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    test_master = models.ForeignKey(LabTestMaster, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('ORDERED', 'Ordered'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('RESULT_ENTRY', 'Result Entered'),
        ('VERIFIED', 'Verified & Released')
    ], default='ORDERED')

    def __str__(self):
        return f"Lab Order #{self.id} - {self.test_master.name} for {self.patient.name}"

class LabSample(models.Model):
    lab_order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='sample')
    sample_type = models.CharField(max_length=50, default='Blood')
    sample_code = models.CharField(max_length=50, unique=True)
    collected_at = models.DateTimeField(auto_now_add=True)
    collected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Sample {self.sample_code} ({self.sample_type})"

class LabResult(models.Model):
    lab_order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='result')
    result_value = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    interpretation_flag = models.CharField(max_length=20, choices=[
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('LOW', 'Low'),
        ('CRITICAL', 'Critical')
    ], default='NORMAL')
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Result for {self.lab_order.test_master.name}: {self.result_value} [{self.interpretation_flag}]"

class DiagnosticTestMaster(models.Model):
    test_code = models.CharField(max_length=50, unique=True)
    test_name = models.CharField(max_length=150)
    category = models.CharField(max_length=50)
    specimen_type = models.CharField(max_length=50)
    default_unit = models.CharField(max_length=30, blank=True, default='')
    reference_range_male = models.CharField(max_length=100, blank=True, default='')
    reference_range_female = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnostic_test_masters'

    def __str__(self):
        return f"{self.test_name} [{self.test_code}]"

class DiagnosticOrder(models.Model):
    visit = models.ForeignKey('visits.Visit', on_delete=models.RESTRICT, related_name='diagnostic_orders')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.RESTRICT, related_name='diagnostic_orders')
    ordering_doctor_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='ordered_diagnostics')
    order_number = models.CharField(max_length=50, unique=True)
    order_date = models.DateField(default=datetime.date.today)
    lab_token_number = models.IntegerField(null=True, blank=True)
    priority = models.CharField(max_length=20, default='ROUTINE', choices=[
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('STAT', 'Stat')
    ])
    status = models.CharField(max_length=30, default='ORDERED', choices=[
        ('ORDERED', 'Ordered'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('RECEIVED_IN_LAB', 'Received In Lab'),
        ('IN_TESTING', 'In Testing'),
        ('RESULT_ENTERED', 'Result Entered'),
        ('VERIFIED', 'Verified'),
        ('AMENDED', 'Amended'),
        ('CANCELLED', 'Cancelled')
    ])
    clinical_indication = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diagnostic_orders'
        constraints = [
            models.UniqueConstraint(
                fields=['facility', 'order_date', 'lab_token_number'],
                condition=models.Q(lab_token_number__isnull=False),
                name='unique_facility_lab_order_token'
            )
        ]
        indexes = [
            models.Index(fields=['facility', 'order_date', 'lab_token_number'], name='idx_diag_order_token')
        ]

    def __str__(self):
        return f"DiagnosticOrder {self.order_number} ({self.status})"

class Specimen(models.Model):
    diagnostic_order = models.ForeignKey(DiagnosticOrder, on_delete=models.RESTRICT, related_name='specimens')
    barcode_identifier = models.CharField(max_length=50, unique=True)
    specimen_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='COLLECTED', choices=[
        ('PENDING', 'Pending'),
        ('COLLECTED', 'Collected'),
        ('RECEIVED', 'Received'),
        ('REJECTED', 'Rejected')
    ])
    collected_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='collected_specimens')
    collected_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'specimens'

    def __str__(self):
        return f"Specimen {self.barcode_identifier} ({self.specimen_type})"

class TestRequest(models.Model):
    diagnostic_order = models.ForeignKey(DiagnosticOrder, on_delete=models.CASCADE, related_name='test_requests')
    test_master = models.ForeignKey(DiagnosticTestMaster, on_delete=models.RESTRICT, related_name='test_requests')
    specimen = models.ForeignKey(Specimen, on_delete=models.RESTRICT, null=True, blank=True, related_name='test_requests')
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('IN_TESTING', 'In Testing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_requests'
        unique_together = [('diagnostic_order', 'test_master')]

    def __str__(self):
        return f"TestRequest: {self.test_master.test_name} for Order #{self.diagnostic_order_id}"

class DiagnosticResult(models.Model):
    test_request = models.OneToOneField(TestRequest, on_delete=models.RESTRICT, related_name='diagnostic_result')
    result_value_text = models.CharField(max_length=255, blank=True, default='')
    result_value_numeric = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    reference_range_applied = models.CharField(max_length=100)
    is_abnormal = models.BooleanField(default=False)
    is_critical_panic = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='ENTERED', choices=[
        ('ENTERED', 'Entered'),
        ('VERIFIED', 'Verified'),
        ('AMENDED', 'Amended')
    ])
    entered_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='entered_diagnostic_results')
    entered_at = models.DateTimeField(auto_now_add=True)
    verified_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, null=True, blank=True, related_name='verified_diagnostic_results')
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'diagnostic_results'
        constraints = [
            models.CheckConstraint(
                check=(models.Q(status='VERIFIED', verified_by_staff__isnull=False, verified_at__isnull=False) | ~models.Q(status='VERIFIED')),
                name='chk_results_verification'
            )
        ]

    def __str__(self):
        return f"Result for TestRequest #{self.test_request_id}: {self.result_value_text or self.result_value_numeric} [{self.status}]"

class DiagnosticResultAmendment(models.Model):
    diagnostic_result = models.ForeignKey(DiagnosticResult, on_delete=models.RESTRICT, related_name='amendments')
    previous_value_text = models.CharField(max_length=255, blank=True, default='')
    previous_value_numeric = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    amended_value_text = models.CharField(max_length=255, blank=True, default='')
    amended_value_numeric = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    amendment_reason = models.TextField()
    amended_by_staff = models.ForeignKey('accounts.StaffProfile', on_delete=models.RESTRICT, related_name='amended_diagnostic_results')
    amended_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnostic_result_amendments'

    def __str__(self):
        return f"Amendment for Result #{self.diagnostic_result_id} at {self.amended_at}"

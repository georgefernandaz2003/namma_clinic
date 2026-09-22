import datetime
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class MedicineMaster(models.Model):
    generic_name = models.CharField(max_length=150)
    brand_name = models.CharField(max_length=150, blank=True)
    strength = models.CharField(max_length=50, default='500 mg')
    dosage_form = models.CharField(max_length=50, default='Tablet')
    unit = models.CharField(max_length=20, default='Tablets')
    category = models.CharField(max_length=50, default='Essential Medicines')
    minimum_stock = models.IntegerField(default=25)
    reorder_level = models.IntegerField(default=50)
    description = models.TextField(blank=True)

    # Regulatory & Schedule Metadata (Nullable / Unknown-safe)
    # Field classification: USER-ENTERED / CONFIGURABLE
    REGULATORY_SCHEDULE_CHOICES = [
        ('SCHEDULE_H', 'Schedule H'),
        ('SCHEDULE_H1', 'Schedule H1'),
        ('SCHEDULE_X', 'Schedule X'),
        ('SCHEDULE_G', 'Schedule G'),
        ('OTC', 'Over the Counter (OTC)'),
        ('GENERAL', 'General Sales'),
        ('UNKNOWN', 'Unclassified / Verification Required'),
    ]
    regulatory_schedule = models.CharField(
        max_length=30, choices=REGULATORY_SCHEDULE_CHOICES, default='UNKNOWN', blank=True
    )
    prescription_required = models.BooleanField(null=True, blank=True, default=None)
    essential_medicine = models.BooleanField(null=True, blank=True, default=None)
    nlem_reference = models.CharField(max_length=100, null=True, blank=True, default=None)

    # Clinical Safety & Handling
    high_alert = models.BooleanField(null=True, blank=True, default=None)
    cold_chain_required = models.BooleanField(default=False)
    route = models.CharField(max_length=50, null=True, blank=True, default=None)

    # Antimicrobial Stewardship Metadata
    AWARE_CHOICES = [
        ('ACCESS', 'Access'),
        ('WATCH', 'Watch'),
        ('RESERVE', 'Reserve'),
        ('NONE', 'Not an Antibiotic'),
        ('UNKNOWN', 'Unclassified'),
    ]
    antibiotic = models.BooleanField(null=True, blank=True, default=None)
    aware_category = models.CharField(max_length=20, choices=AWARE_CHOICES, default='UNKNOWN', blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.generic_name} ({self.strength} {self.dosage_form})"


class Vendor(models.Model):
    vendor_name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], default='ACTIVE')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, null=True, blank=True, related_name='vendors')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_vendors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor_name} ({self.contact_person})"


class MedicineBatch(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='medicine_batches')
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_batches')
    supplier = models.CharField(max_length=100, null=True, blank=True, default=None)
    received_date = models.DateField(auto_now_add=True)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=1.50)

    # -------------------------------------------------------------
    # Quantity Bucket Architecture (Option A)
    # -------------------------------------------------------------
    available_quantity = models.IntegerField(default=0)
    quarantined_quantity = models.IntegerField(default=0)
    recalled_quantity = models.IntegerField(default=0)
    damaged_quantity = models.IntegerField(default=0)
    disposed_quantity = models.IntegerField(default=0)  # Cumulative stock destroyed

    # Legacy field preserved for backwards-compatibility:
    # DEFINITION: Current remaining physical stock on premises = A + Q + R + D
    quantity = models.IntegerField(default=0)

    # Pure Operational Status Choices
    OPERATIONAL_STATUS_CHOICES = [
        ('AVAILABLE', 'Available (Operational)'),
        ('QUARANTINED', 'Quarantined (Quality / Investigation Hold)'),
        ('RECALLED', 'Recalled (Regulatory Recall Hold)'),
        ('DAMAGED', 'Damaged (Condemned / Spoilage)'),
        ('DISPOSED', 'Disposed (Formally Destroyed / Incinerated)'),
        ('EXHAUSTED', 'Stock Exhausted (Zero Physical Quantity)'),
        # Legacy Aliases (Read/Normalized Compatibility Only — Never Newly Emitted)
        ('ACTIVE', 'Active (Legacy Alias for Available)'),
        ('LOW_STOCK', 'Low Stock (Legacy Alias for Available)'),
        ('EXPIRING_SOON', 'Expiring Soon (Legacy Alias for Available)'),
        ('EXPIRED', 'Expired (Legacy Alias)'),
    ]
    status = models.CharField(max_length=20, choices=OPERATIONAL_STATUS_CHOICES, default='AVAILABLE')

    class Meta:
        ordering = ['expiry_date']  # Authoritative FEFO default

    def clean(self):
        super().clean()
        if self.available_quantity < 0:
            raise ValidationError({'available_quantity': 'Available quantity cannot be negative.'})
        if self.quarantined_quantity < 0:
            raise ValidationError({'quarantined_quantity': 'Quarantined quantity cannot be negative.'})
        if self.recalled_quantity < 0:
            raise ValidationError({'recalled_quantity': 'Recalled quantity cannot be negative.'})
        if self.damaged_quantity < 0:
            raise ValidationError({'damaged_quantity': 'Damaged quantity cannot be negative.'})
        if self.disposed_quantity < 0:
            raise ValidationError({'disposed_quantity': 'Disposed quantity cannot be negative.'})

    def derive_operational_status(self):
        """
        Deterministic operational status derivation based on explicit bucket precedence:
        1. If available_quantity > 0: status is ALWAYS 'AVAILABLE'.
        2. If available_quantity == 0 and physical stock remains:
           Precedence: RECALLED > QUARANTINED > DAMAGED.
        3. If total_physical_stock == 0:
           If explicitly marked DISPOSED, status remains 'DISPOSED'; otherwise 'EXHAUSTED'.
        """
        if self.available_quantity > 0:
            return 'AVAILABLE'

        # available_quantity is 0: Evaluate remaining physical stock by precedence
        if self.recalled_quantity > 0:
            return 'RECALLED'
        if self.quarantined_quantity > 0:
            return 'QUARANTINED'
        if self.damaged_quantity > 0:
            return 'DAMAGED'

        # Physical stock on site is 0
        if self.status == 'DISPOSED':
            return 'DISPOSED'
        return 'EXHAUSTED'

    def save(self, *args, **kwargs):
        # Update legacy quantity to reflect current remaining physical stock on site
        self.quantity = (
            self.available_quantity +
            self.quarantined_quantity +
            self.recalled_quantity +
            self.damaged_quantity
        )
        self.status = self.derive_operational_status()
        super().save(*args, **kwargs)

    @property
    def total_physical_stock(self):
        """Current physical stock on site: A + Q + R + D."""
        return (
            self.available_quantity +
            self.quarantined_quantity +
            self.recalled_quantity +
            self.damaged_quantity
        )

    @property
    def expiry_bucket(self):
        """Derived expiry state calculation — Purely dynamic."""
        today = datetime.date.today()
        if self.expiry_date <= today:
            return 'EXPIRED'
        delta = (self.expiry_date - today).days
        if delta <= 30:
            return '0_30_DAYS'
        elif delta <= 60:
            return '31_60_DAYS'
        elif delta <= 90:
            return '61_90_DAYS'
        return 'NOT_EXPIRING'

    @property
    def is_dispensable(self):
        """Authoritative unified dispensing predicate."""
        if self.expiry_date <= datetime.date.today():
            return False
        if self.status in ['QUARANTINED', 'RECALLED', 'DAMAGED', 'DISPOSED', 'EXHAUSTED']:
            return False
        return self.available_quantity > 0

    def __str__(self):
        return f"Batch {self.batch_number} - {self.medicine.generic_name} (Exp: {self.expiry_date}, Avail: {self.available_quantity}, Total Phys: {self.quantity})"


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=[
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Ordered'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Fully Received'),
        ('CANCELLED', 'Cancelled')
    ], default='DRAFT')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_purchase_orders')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_purchase_orders')
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']

    def __str__(self):
        return f"PO #{self.po_number} - {self.vendor.vendor_name} ({self.status})"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE)
    ordered_quantity = models.IntegerField(default=100)
    received_quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_price = self.ordered_quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medicine.generic_name}: {self.ordered_quantity} ordered"


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('PURCHASE_RECEIVED', 'Stock Received via Accepted GRN (+)'),
        ('DISPENSED', 'Medication Dispensed to Patient (-)'),
        ('RETURN_APPROVED', 'Customer Return Approved & Restored to Usable Stock (+)'),
        ('RETURN_QUARANTINED', 'Customer Return Routed to Quarantine (Bucket Transfer)'),
        ('RETURN_DISPOSED', 'Customer Return Routed to Condemnation (-)'),
        ('ADJUSTMENT_INCREASE', 'Stock Count Audit Positive Adjustment (+)'),
        ('ADJUSTMENT_DECREASE', 'Stock Count Audit Negative Adjustment (-)'),
        ('QUARANTINE_HOLD', 'Stock Moved from Available to Quarantine (Bucket Transfer)'),
        ('QUARANTINE_RELEASE', 'Stock Released from Quarantine to Available (Bucket Transfer)'),
        ('RECALL_HOLD', 'Stock Moved from Available to Recalled Bucket (Bucket Transfer)'),
        ('RECALL_RELEASE', 'Recalled Stock Cleared by Regulatory Authority (Bucket Transfer)'),
        ('DISPOSAL_DESTROYED', 'Condemned Stock Destroyed / Incinerated (-)'),
        ('DAMAGE_RECORDED', 'Damaged Stock Moved from Available Bucket (Bucket Transfer)'),
        ('TRANSFERRED_IN', 'Inter-Facility Stock Inflow (+)'),
        ('TRANSFERRED_OUT', 'Inter-Facility Stock Outflow (-)'),
        # Legacy transaction types for backward compatibility
        ('RETURNED', 'Returned Stock (Legacy)'),
        ('ADJUSTMENT', 'Stock Audit Adjustment (Legacy)'),
        ('DAMAGED', 'Damaged / Wastage (Legacy)'),
        ('EXPIRED', 'Expired Stock (Legacy)'),
        ('ISSUED', 'Issued to Sub-Store (Legacy)'),
        ('TRANSFERRED', 'Transferred to Facility (Legacy)'),
    ]
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE)
    batch = models.ForeignKey(MedicineBatch, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()

    # Dual-Bucket Balance Proofs:
    # Every intra-batch bucket transfer explicitly records both sides of the movement
    source_bucket = models.CharField(max_length=30, blank=True, default='')
    source_before_qty = models.IntegerField(default=0)
    source_after_qty = models.IntegerField(default=0)

    destination_bucket = models.CharField(max_length=30, blank=True, default='')
    destination_before_qty = models.IntegerField(default=0)
    destination_after_qty = models.IntegerField(default=0)

    # Legacy backward-compatible fields
    before_quantity = models.IntegerField(default=0)
    after_quantity = models.IntegerField(default=0)

    # Clinical & Operational Audit Context
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True)
    prescription = models.ForeignKey('consultations.Prescription', on_delete=models.SET_NULL, null=True, blank=True)
    prescription_item = models.ForeignKey('consultations.PrescriptionItem', on_delete=models.SET_NULL, null=True, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def clean(self):
        super().clean()
        is_intra_transfer = (
            self.source_bucket and self.destination_bucket and
            self.source_bucket not in ['external_vendor', 'patient_return'] and
            self.destination_bucket not in ['patient_dispensed', 'disposed_quantity']
        )
        if is_intra_transfer:
            decrement = self.source_before_qty - self.source_after_qty
            increment = self.destination_after_qty - self.destination_before_qty
            if decrement != self.quantity:
                raise ValidationError("Source bucket decrement must equal transaction quantity.")
            if increment != self.quantity:
                raise ValidationError("Destination bucket increment must equal transaction quantity.")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Inventory transactions are immutable and cannot be updated.")
        # Reconcile legacy single-bucket fields for backwards compatibility
        if not self.before_quantity and self.source_before_qty:
            self.before_quantity = self.source_before_qty
        if not self.after_quantity and self.source_after_qty:
            self.after_quantity = self.source_after_qty
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Inventory transactions are immutable and cannot be deleted.")

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} x {self.medicine.generic_name} ({self.source_bucket} -> {self.destination_bucket})"


class GoodsReceiptNote(models.Model):
    """Goods Receipt Note (GRN) for physical stock receiving against Purchase Orders."""
    GRN_STATUS_CHOICES = [
        ('DRAFT', 'Draft Inspection'),
        ('ACCEPTED', 'Fully Accepted & Taken into Stock'),
        ('PARTIAL_ACCEPTANCE', 'Partially Accepted with Rejections'),
        ('REJECTED', 'Entire Shipment Rejected'),
    ]
    grn_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='goods_receipts')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='goods_receipts')
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_grns')
    status = models.CharField(max_length=30, choices=GRN_STATUS_CHOICES, default='ACCEPTED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"GRN #{self.grn_number} - PO #{self.purchase_order.po_number} ({self.status})"


class GoodsReceiptItem(models.Model):
    """Line item within a Goods Receipt Note."""
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='grn_items')
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    ordered_quantity = models.IntegerField()
    received_quantity = models.IntegerField()
    rejected_quantity = models.IntegerField(default=0)
    rejection_reason = models.TextField(blank=True)
    accepted_quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.medicine.generic_name} (Batch {self.batch_number}): {self.accepted_quantity} accepted"


class DispensationReturn(models.Model):
    """Two-phase patient dispensation return with clinical assessment and cumulative cap."""
    ASSESSMENT_STATUS_CHOICES = [
        ('PENDING_ASSESSMENT', 'Pending Pharmacist Assessment'),
        ('ASSESSED', 'Assessment Completed'),
    ]
    DISPOSITION_CHOICES = [
        ('PENDING', 'Pending Disposition'),
        ('APPROVED_FOR_STOCK', 'Approved for Stock Restoration (+)'),
        ('QUARANTINE', 'Quarantined for Investigation (Bucket Transfer)'),
        ('DISPOSAL', 'Condemned for Disposal (-)'),
    ]
    return_number = models.CharField(max_length=50, unique=True)
    prescription = models.ForeignKey('consultations.Prescription', on_delete=models.CASCADE, related_name='returns')
    prescription_item = models.ForeignKey('consultations.PrescriptionItem', on_delete=models.CASCADE, related_name='returns')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE, related_name='returns')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='dispensation_returns')
    returned_quantity = models.IntegerField()
    return_reason = models.TextField()
    returned_at = models.DateTimeField(auto_now_add=True)
    returned_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_returns')

    # Phase 2 — Pharmacist Clinical Assessment
    assessment_status = models.CharField(max_length=30, choices=ASSESSMENT_STATUS_CHOICES, default='PENDING_ASSESSMENT')
    condition_intact = models.BooleanField(null=True, default=None)
    packaging_sealed = models.BooleanField(null=True, default=None)
    storage_valid = models.BooleanField(null=True, default=None)
    assessed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessed_returns')
    assessed_at = models.DateTimeField(null=True, blank=True)
    disposition = models.CharField(max_length=30, choices=DISPOSITION_CHOICES, default='PENDING')
    assessment_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-returned_at']

    def __str__(self):
        return f"Return #{self.return_number} - {self.returned_quantity} x {self.batch.medicine.generic_name} ({self.assessment_status})"


class BatchRecall(models.Model):
    """Quantity-scoped regulatory batch recall governance."""
    RECALL_STATUS_CHOICES = [
        ('INITIATED', 'Recall Initiated / Active Hold'),
        ('HELD_IN_QUARANTINE', 'Stock Held in Quarantine'),
        ('RELEASED', 'Recall Cleared / Released by Authority'),
        ('DISPOSED', 'Recalled Stock Condemned & Destroyed'),
    ]
    recall_number = models.CharField(max_length=50, unique=True)
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE, related_name='recalls')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='batch_recalls')
    recall_reference = models.CharField(max_length=100)
    reason = models.TextField()
    recalled_quantity = models.IntegerField(default=0)  # Quantity-scoped recall amount
    initiated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_recalls')
    status = models.CharField(max_length=30, choices=RECALL_STATUS_CHOICES, default='INITIATED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Recall #{self.recall_number} - Batch {self.batch.batch_number} ({self.recalled_quantity} units)"


class PatientCounselling(models.Model):
    """Explicit non-inferential patient counselling documentation."""
    prescription = models.OneToOneField('consultations.Prescription', on_delete=models.CASCADE, related_name='counselling_record')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='counselling_records')
    pharmacist = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_counselling')
    counselled_at = models.DateTimeField(auto_now_add=True)

    # Explicit Checklist (Default None/NULL = Not Documented)
    dose_explained = models.BooleanField(null=True, blank=True, default=None)
    frequency_explained = models.BooleanField(null=True, blank=True, default=None)
    duration_explained = models.BooleanField(null=True, blank=True, default=None)
    food_instructions_given = models.BooleanField(null=True, blank=True, default=None)
    storage_explained = models.BooleanField(null=True, blank=True, default=None)
    warning_signs_explained = models.BooleanField(null=True, blank=True, default=None)
    adherence_counselled = models.BooleanField(null=True, blank=True, default=None)
    counselling_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-counselled_at']

    def __str__(self):
        return f"Counselling for Prescription #{self.prescription_id} ({self.patient.name})"


class ColdChainLog(models.Model):
    """Manual storage temperature log for cold-chain medicines."""
    STATUS_CHOICES = [
        ('NORMAL', 'Normal Storage Temperature'),
        ('EXCURSION', 'Temperature Excursion Alert'),
        ('UNCONFIGURED_RANGE', 'Temperature Logged — Storage Range Not Configured'),
    ]
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='cold_chain_logs')
    storage_location = models.CharField(max_length=100, default='Pharmacy Refrigerator')
    min_temp_celsius = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, default=None)
    max_temp_celsius = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, default=None)
    recorded_temp_celsius = models.DecimalField(max_digits=4, decimal_places=1)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cold_chain_entries')
    recorded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='UNCONFIGURED_RANGE')
    corrective_action = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']

    def save(self, *args, **kwargs):
        if self.min_temp_celsius is not None and self.max_temp_celsius is not None:
            if self.recorded_temp_celsius < self.min_temp_celsius or self.recorded_temp_celsius > self.max_temp_celsius:
                self.status = 'EXCURSION'
            else:
                self.status = 'NORMAL'
        else:
            self.status = 'UNCONFIGURED_RANGE'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ColdChainLog {self.recorded_temp_celsius}°C at {self.storage_location} ({self.status})"

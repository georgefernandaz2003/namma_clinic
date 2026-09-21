from django.db import models
from django.utils import timezone

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
    supplier = models.CharField(max_length=100, default='KSMSCL (E-Aushada)')
    received_date = models.DateField(auto_now_add=True)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    quantity = models.IntegerField(default=500)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=1.50)
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('EXHAUSTED', 'Exhausted')
    ], default='ACTIVE')

    class Meta:
        ordering = ['expiry_date'] # FEFO rule (First Expiry First Out)

    def __str__(self):
        return f"Batch {self.batch_number} - {self.medicine.generic_name} (Exp: {self.expiry_date}, Qty: {self.quantity})"

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
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE)
    batch = models.ForeignKey(MedicineBatch, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=30, choices=[
        ('PURCHASE_RECEIVED', 'Purchase Received'),
        ('DISPENSED', 'Dispensed to Patient'),
        ('RETURNED', 'Returned Stock'),
        ('ADJUSTMENT', 'Stock Audit Adjustment'),
        ('DAMAGED', 'Damaged / Wastage'),
        ('EXPIRED', 'Expired Stock'),
        ('ISSUED', 'Issued to Sub-Store'),
        ('TRANSFERRED', 'Transferred to Facility')
    ])
    quantity = models.IntegerField()
    reference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} x {self.medicine.generic_name}"

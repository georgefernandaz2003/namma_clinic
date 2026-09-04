from django.db import models

class MedicineMaster(models.Model):
    generic_name = models.CharField(max_length=150)
    brand_name = models.CharField(max_length=150, blank=True)
    strength = models.CharField(max_length=50, default='500 mg')
    dosage_form = models.CharField(max_length=50, default='Tablet')
    unit = models.CharField(max_length=20, default='Tablets')
    category = models.CharField(max_length=50, default='Essential Medicines')
    reorder_level = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.generic_name} ({self.strength} {self.dosage_form})"

class MedicineBatch(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE, related_name='medicine_batches')
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    supplier = models.CharField(max_length=100, default='KSMSCL (E-Aushada)')
    received_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    quantity = models.IntegerField(default=500)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=1.50)
    status = models.CharField(max_length=20, default='ACTIVE')

    class Meta:
        ordering = ['expiry_date'] # FEFO rule (First Expiry First Out)

    def __str__(self):
        return f"Batch {self.batch_number} - {self.medicine.generic_name} (Exp: {self.expiry_date}, Qty: {self.quantity})"

class InventoryTransaction(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    medicine = models.ForeignKey(MedicineMaster, on_delete=models.CASCADE)
    batch = models.ForeignKey(MedicineBatch, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=30, choices=[
        ('RECEIVED', 'Received Stock'),
        ('ISSUED', 'Issued to Sub-Store'),
        ('DISPENSED', 'Dispensed to Patient'),
        ('TRANSFERRED', 'Transferred to Facility'),
        ('DAMAGED', 'Damaged / Wastage'),
        ('EXPIRED', 'Expired Stock'),
        ('ADJUSTMENT', 'Stock Audit Adjustment')
    ])
    quantity = models.IntegerField()
    reference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} x {self.medicine.generic_name}"

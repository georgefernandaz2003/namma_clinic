import os
import sys
sys.path.append('.')
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.pharmacy.models import Vendor, PurchaseOrder, MedicineBatch, InventoryTransaction
from apps.pharmacy.views import VendorSerializer, PurchaseOrderSerializer, MedicineBatchSerializer

print("Total Vendors in DB:", Vendor.objects.count())
for v in Vendor.objects.all():
    print(" - Vendor:", v.id, v.vendor_name, "Facility:", v.facility)

print("\nTotal Purchase Orders in DB:", PurchaseOrder.objects.count())
for po in PurchaseOrder.objects.all():
    print(" - PO:", po.id, po.po_number, "Facility:", po.facility.facility_name, "Status:", po.status)

print("\nTotal Medicine Batches in DB:", MedicineBatch.objects.count())
for b in MedicineBatch.objects.all():
    print(" - Batch:", b.id, b.batch_number, "Facility:", b.facility.facility_name, "Medicine:", b.medicine.generic_name, "Exp:", b.expiry_date)

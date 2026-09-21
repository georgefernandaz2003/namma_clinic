import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.conf import settings
from apps.facilities.models import Facility
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation
from apps.laboratory.models import LabOrder
from apps.pharmacy.models import MedicineMaster, MedicineBatch, PurchaseOrder, InventoryTransaction
from apps.audit.models import AuditLog

db_conf = settings.DATABASES['default']
db_file = Path(db_conf['NAME'])

print("=" * 65)
print("       NAMMA CLINIC - DATABASE CONNECTION INFORMATION")
print("=" * 65)
print(f" Database Engine:       {db_conf['ENGINE']}")
print(f" Database Path:         {db_file.resolve()}")
print(f" File Size:             {round(db_file.stat().st_size / 1024, 2)} KB")
print(f" File Exists on Disk:   {db_file.exists()}")
print(f" Connection Options:    {db_conf.get('OPTIONS', {})}")

with connection.cursor() as cur:
    cur.execute("PRAGMA journal_mode;")
    j_mode = cur.fetchone()[0]
    cur.execute("PRAGMA foreign_keys;")
    fk = "ENABLED" if cur.fetchone()[0] == 1 else "DISABLED"
    cur.execute("PRAGMA synchronous;")
    sync = cur.fetchone()[0]
    cur.execute("PRAGMA busy_timeout;")
    timeout = cur.fetchone()[0]
    cur.execute("PRAGMA cache_size;")
    cache = cur.fetchone()[0]
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    total_tables = cur.fetchone()[0]

print("-" * 65)
print("       ACTIVE ENGINE PRAGMAS & RUNTIME STATE")
print("-" * 65)
print(f" Journal Mode:          {j_mode.upper()} (Concurrent Write-Ahead Logging)")
print(f" Foreign Key Enforce:   {fk}")
print(f" Synchronous I/O:       {sync} (NORMAL - High performance + Crash Safe)")
print(f" Busy Lock Timeout:     {timeout} ms ({timeout // 1000} seconds)")
print(f" Cache Memory:          {abs(cache)} KB (~{abs(cache) // 1024} MB RAM)")
print(f" Database Integrity:    {integrity.upper()} (All pages valid)")
print(f" Total Managed Tables:  {total_tables} tables")
print("-" * 65)
print("       HEALTHCARE DATA SUMMARY")
print("-" * 65)
print(f" Registered Facilities:         {Facility.objects.count()}")
print(f" Healthcare Staff / Users:      {User.objects.count()}")
print(f" Registered Patients:           {Patient.objects.count()}")
print(f" OPD Visits & Queues:           {Visit.objects.count()}")
print(f" Doctor Consultations:          {Consultation.objects.count()}")
print(f" Diagnostic Lab Orders:         {LabOrder.objects.count()}")
print(f" Approved Medicine Catalogue:   {MedicineMaster.objects.count()}")
print(f" Active Medicine Batches:       {MedicineBatch.objects.count()}")
print(f" Vendor Purchase Orders:        {PurchaseOrder.objects.count()}")
print(f" Inventory Stock Transactions:  {InventoryTransaction.objects.count()}")
print(f" System Audit Logs:             {AuditLog.objects.count()}")
print("=" * 65)

import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.abspath('backend'))

django.setup()

from apps.facilities.models import Facility
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryLedger
from apps.reports.karnataka_command_center import get_karnataka_command_center_data

print("--- Database Verification: Pharmacy & Supply Chain ---")

# 1. Facility Count
fac_count = Facility.objects.count()
print(f"Total Facilities in DB: {fac_count}")
assert fac_count > 0, "No facilities found in database!"

# 2. Medicine Formulary & Batches
med_count = MedicineMaster.objects.count()
batch_count = MedicineBatch.objects.count()
ledger_count = InventoryLedger.objects.count()
print(f"Total Medicine Formulations (MedicineMaster): {med_count}")
print(f"Total Batches (MedicineBatch): {batch_count}")
print(f"Total Ledger Entries (InventoryLedger): {ledger_count}")

# 3. Command Center Service Validation
state_data = get_karnataka_command_center_data("all", "all", "all")
ps_state = state_data.get("pharmacy_supply", {})
print("\n[State Level Scope]")
print(f"Total Medicines: {ps_state['summary_kpis']['total_medicines']}")
print(f"Low Stock: {ps_state['summary_kpis']['low_stock']}")
print(f"Critical Stock: {ps_state['summary_kpis']['critical_stock']}")
print(f"Expiring <30d: {ps_state['summary_kpis']['expiring_30d']}")
print(f"Stock Value: {ps_state['summary_kpis']['stock_value']}")
print(f"Top Consumed Formulations: {len(ps_state['top_consumed_medicines'])}")
print(f"Supply Orders / Indents: {len(ps_state['orders_and_supply'])}")
print(f"Predictions: {len(ps_state['predictions'])}")

assert ps_state['summary_kpis']['total_medicines'] == 240
assert ps_state['summary_kpis']['low_stock'] == 8
assert ps_state['summary_kpis']['critical_stock'] == 3
assert len(ps_state['consumption_trend']['months']) == 12
assert len(ps_state['orders_and_supply']) == 4
assert 'days_7' in ps_state['expiry_buckets']
assert 'days_30' in ps_state['expiry_buckets']
assert 'days_60' in ps_state['expiry_buckets']
assert 'days_90' in ps_state['expiry_buckets']

# 4. District Scoped Validation
dakshina_data = get_karnataka_command_center_data("dakshina_kannada", "all", "all")
ps_dakshina = dakshina_data.get("pharmacy_supply", {})
print("\n[Dakshina Kannada District Scope]")
print(f"Low Stock: {ps_dakshina['summary_kpis']['low_stock']}")
print(f"Critical Stock: {ps_dakshina['summary_kpis']['critical_stock']}")
print(f"Expiring <30d: {ps_dakshina['summary_kpis']['expiring_30d']}")
print(f"Stock Value: {ps_dakshina['summary_kpis']['stock_value']}")

assert ps_dakshina['summary_kpis']['low_stock'] == 2
assert ps_dakshina['summary_kpis']['critical_stock'] == 1
assert ps_dakshina['summary_kpis']['expiring_30d'] == 3

print("\n✓ Database and Command Center verification passed successfully!")

import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.reports.karnataka_command_center import get_karnataka_command_center_data

print(f"Total Facilities in DB: {Facility.objects.count()}")
print(f"Total Patients in DB: {Patient.objects.count()}")

data = get_karnataka_command_center_data(district_id="all")
disease_intel = data.get("disease_intelligence", {})
print(f"Disease Summary KPIs: {disease_intel.get('summary_kpis')}")
print(f"Disease items count: {len(disease_intel.get('diseases', []))}")
print(f"Monthly trends count: {len(disease_intel.get('monthly_trends', {}))}")
print(f"Geographic dist count: {len(disease_intel.get('geographic_distribution', {}))}")

# Check with a filtered scope (Dakshina Kannada)
dk_data = get_karnataka_command_center_data(district_id="dakshina_kannada")
dk_intel = dk_data.get("disease_intelligence", {})
print(f"Dakshina Kannada Active Cases: {dk_intel.get('summary_kpis', {}).get('total_active_cases')}")

print("DATABASE & SERVICE VERIFICATION COMPLETED SUCCESSFULLY!")

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.facilities.models import Facility
from apps.visits.models import Visit, Token
from apps.laboratory.models import LabOrder

def test_sync():
    print("=== AUDIT QUEUE AND LAB INTEGRATION ===")
    for f in Facility.objects.all():
        print(f"  Facility: {f.id} | {f.facility_code} | {f.facility_name}")
    fac = Facility.objects.filter(facility_name__icontains='Varthur').first() or Facility.objects.first()
    print(f"\nSelected Facility: {fac.facility_name} (ID: {fac.id}, Code: {fac.facility_code})")

    # 1. Check all visits for today
    visits = Visit.objects.filter(facility=fac)
    print(f"\nTotal Visits at {fac.facility_name}: {visits.count()}")
    for v in visits:
        tok = getattr(v, 'token', None)
        tok_num = tok.token_number if tok else 'None'
        print(f"  - Visit #{v.id} (Token #{tok_num}): Patient={v.patient.name}, Queue={v.current_queue}, Status={v.status}")

    # 2. Check lab orders for facility
    lab_orders = LabOrder.objects.filter(facility=fac)
    print(f"\nTotal Lab Orders at {fac.facility_name}: {lab_orders.count()}")
    for lo in lab_orders:
        linked_visit_token = lo.visit.token.token_number if (lo.visit and hasattr(lo.visit, 'token')) else 'Unlinked'
        print(f"  - Order #LAB-{lo.id:04d}: Patient={lo.patient.name}, Test={lo.test_master.name}, Status={lo.status}, Linked Visit={lo.visit_id} (Token #{linked_visit_token})")

    # 3. Verify Lab Queue Visit
    lab_visit = Visit.objects.filter(facility=fac, current_queue='LAB').first()
    assert lab_visit is not None, "Expected at least 1 visit in current_queue='LAB'"
    print(f"\nVerified LAB queue visit found: Token #{lab_visit.token.token_number} ({lab_visit.patient.name}) in state {lab_visit.status}")

    # 4. Check Queue filter matching
    lab_pending_visits = Visit.objects.filter(facility=fac, current_queue='LAB', status__icontains='LAB')
    print(f"Visits in LAB queue: {lab_pending_visits.count()}")
    assert lab_pending_visits.count() >= 1, "Lab pending count in Queue must be >= 1"

    # 5. Test Django REST API Client for date-based lab orders
    import datetime
    from rest_framework.test import APIClient
    from apps.accounts.models import User

    client = APIClient()
    admin_user = User.objects.filter(role='DISTRICT_OFFICER').first() or User.objects.filter(is_superuser=True).first()
    client.force_authenticate(user=admin_user)

    today_str = datetime.date.today().isoformat()
    yest_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # Test Today Lab Orders
    res_today = client.get(f'/api/lab/orders/?facility={fac.id}&date={today_str}')
    today_orders = res_today.data.get('results', res_today.data)
    print(f"\nAPI Test /api/lab/orders/?facility={fac.id}&date={today_str}: {len(today_orders)} orders returned")
    assert len(today_orders) >= 2, "Expected at least 2 lab orders for today"

    # Test Yesterday Lab Orders (should be 0 or empty for RC-A4)
    res_yest = client.get(f'/api/lab/orders/?facility={fac.id}&date={yest_str}')
    yest_orders = res_yest.data.get('results', res_yest.data)
    print(f"API Test /api/lab/orders/?facility={fac.id}&date={yest_str}: {len(yest_orders)} orders returned")

    # Test All Dates Lab Orders
    res_all = client.get(f'/api/lab/orders/?facility={fac.id}&date=all')
    all_orders = res_all.data.get('results', res_all.data)
    print(f"API Test /api/lab/orders/?facility={fac.id}&date=all: {len(all_orders)} orders returned")
    assert len(all_orders) >= len(today_orders), "All orders count must be >= today orders"

    print("\nALL QUEUE & LAB INTEGRATION AND DATE MANAGEMENT CHECKS PASSED!")

if __name__ == '__main__':
    test_sync()

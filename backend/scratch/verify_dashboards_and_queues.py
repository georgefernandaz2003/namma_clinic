import os
import sys
import django

# Setup django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.facilities.models import Facility
import datetime

def test_all_dashboards_and_queues():
    print("=" * 70)
    print("      NAMMA CLINIC - AUDIT OF ALL DASHBOARDS & QUEUES")
    print("=" * 70)

    # 1. Retrieve key facilities
    dh = Facility.objects.get(facility_code='HOSP-DIST-01')
    rc_a4 = Facility.objects.get(facility_code='RC-A4-04')
    vc = Facility.objects.get(facility_code='VC-A4-01')
    
    # 2. Retrieve role users
    u_district = User.objects.get(username='district')
    u_dh_admin = User.objects.get(username='dh_admin')
    u_doctor = User.objects.get(username='vh1_doctor')
    u_nurse = User.objects.get(username='nurse')
    u_lab = User.objects.get(username='lab')
    u_pharmacy = User.objects.get(username='pharmacy')
    
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    client = APIClient()

    # -------------------------------------------------------------
    # SECTION 1: ROLE-SPECIFIC DASHBOARD APIS (/api/dashboard/summary/)
    # -------------------------------------------------------------
    print("\n--- SECTION 1: ROLE-SPECIFIC DASHBOARDS (/api/dashboard/summary/) ---")
    
    # 1.1 District Officer Dashboard
    client.force_authenticate(user=u_district)
    res = client.get('/api/dashboard/summary/')
    assert res.status_code == 200, f"District Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] District Officer Dashboard:")
    print(f"     - Active Scope: {data['active_facility']} ({data['active_facility_type']})")
    print(f"     - Total Monitored Facilities: {data['total_facilities']}")
    print(f"     - Total Registered District Patients: {data['total_patients']}")
    print(f"     - District-wide Today OPD: {data['todays_opd']}")
    print(f"     - Cross-Facility Referrals Pending: {data['referrals_summary']['pending']}")
    print(f"     - Low Stock Medicines Across District: {data['inventory_summary']['low_stock']}")
    print(f"     - Facility Breakdown Count: {len(data['facility_overview'])} facilities")
    assert len(data['facility_overview']) >= 4, "Should list all 4 facilities in district overview"

    # 1.2 Hospital Admin Dashboard
    client.force_authenticate(user=u_dh_admin)
    res = client.get(f'/api/dashboard/summary/?facility={dh.id}')
    assert res.status_code == 200, f"Hospital Admin Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] Hospital Admin Dashboard (Victoria District Hospital):")
    print(f"     - Facility: {data['active_facility']}")
    print(f"     - Facility Today OPD: {data['todays_opd']}")
    print(f"     - Waiting Doctor: {data['kpis']['doctor_waiting']}, Waiting Pharmacy: {data['kpis']['pharmacy_waiting']}")
    print(f"     - Staff Active: Doctors: {data['staff_status']['doctors']['active']}, Nurses: {data['staff_status']['nurses']['active']}")

    # 1.3 Doctor Clinical Dashboard
    client.force_authenticate(user=u_doctor)
    res = client.get(f'/api/dashboard/summary/?facility={rc_a4.id}&date={today_str}')
    assert res.status_code == 200, f"Doctor Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] Doctor Clinical Dashboard (Dr. Rajesh Kumar):")
    print(f"     - Patients Waiting for Doctor: {data['kpis']['doctor_waiting']}")
    print(f"     - Patients in Consultation: {data['kpis']['in_consultation']}")
    print(f"     - Lab Tests Awaiting Results: {data['kpis']['lab_pending']}")
    print(f"     - Completed Consultations Today: {data['kpis']['completed']}")
    print(f"     - Doctor Actions Required: {[a['title'] for a in data['action_required']]}")

    # 1.4 Nurse Triage Dashboard
    client.force_authenticate(user=u_nurse)
    res = client.get(f'/api/dashboard/summary/?facility={rc_a4.id}&date={today_str}')
    assert res.status_code == 200, f"Nurse Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] Nurse Triage Dashboard (Nurse Deepa Nayak):")
    print(f"     - Patients Waiting for Triage Vitals: {data['kpis']['triage_waiting']}")
    print(f"     - Nurse Actions Required: {[a['title'] for a in data['action_required']]}")

    # 1.5 Lab Technician Dashboard
    client.force_authenticate(user=u_lab)
    res = client.get(f'/api/dashboard/summary/?facility={rc_a4.id}&date={today_str}')
    assert res.status_code == 200, f"Lab Technician Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] Lab Technician Dashboard (Lab Tech Shweta Rao):")
    print(f"     - Lab Diagnostic Orders Pending: {data['kpis']['lab_pending']}")
    print(f"     - Lab Actions Required: {[a['title'] for a in data['action_required']]}")

    # 1.6 Pharmacist Dashboard
    client.force_authenticate(user=u_pharmacy)
    res = client.get(f'/api/dashboard/summary/?facility={rc_a4.id}&date={today_str}')
    assert res.status_code == 200, f"Pharmacist Dashboard failed: {res.status_code}"
    data = res.data
    print(f" [OK] Pharmacist Dashboard (Pharmacist Anand Murthy):")
    print(f"     - Prescriptions Waiting Dispensation: {data['kpis']['pharmacy_waiting']}")
    print(f"     - Low Stock Items: {data['inventory_summary']['low_stock']}")
    print(f"     - Pharmacist Actions Required: {[a['title'] for a in data['action_required']]}")

    # -------------------------------------------------------------
    # SECTION 2: PHARMACY INTERNAL DASHBOARD (/api/pharmacy/dashboard/)
    # -------------------------------------------------------------
    print("\n--- SECTION 2: PHARMACY INTERNAL DASHBOARD & PROCUREMENT KPIS ---")
    res = client.get(f'/api/pharmacy/dashboard/?facility={rc_a4.id}')
    assert res.status_code == 200, f"Pharmacy Dashboard failed: {res.status_code}"
    p_dash = res.data
    print(f" [OK] Pharmacy Internal KPIs for Varthur Rural Clinic A4:")
    print(f"     - Total EDL Medicines: {p_dash.get('total_medicines', 0)}")
    print(f"     - Total Available Physical Stock: {p_dash.get('total_available_stock', 0)} units")
    print(f"     - Low Stock Medicines: {p_dash.get('low_stock_count', 0)}")
    print(f"     - Out of Stock Medicines: {p_dash.get('out_of_stock_count', 0)}")
    print(f"     - Expiring Soon Batches: {p_dash.get('expiring_soon_count', 0)}")
    print(f"     - Expired Quarantined Batches: {p_dash.get('expired_count', 0)}")
    print(f"     - Pending Prescriptions: {p_dash.get('pending_prescriptions_count', 0)}")
    print(f"     - Pending Purchase Orders: {p_dash.get('pending_purchase_orders_count', 0)}")
    print(f"     - Active Registered Vendors: {p_dash.get('total_vendors_count', 0)}")

    res_proc = client.get(f'/api/pharmacy/purchase-orders/procurement_summary/?facility={rc_a4.id}')
    assert res_proc.status_code == 200, f"Procurement summary failed: {res_proc.status_code}"
    proc = res_proc.data
    print(f" [OK] Procurement & Vendor KPIs:")
    print(f"     - Total Purchase Orders: {proc.get('total_orders', 0)}")
    print(f"     - Draft POs: {proc.get('draft', 0)}")
    print(f"     - Pending Approval POs: {proc.get('pending_approval', 0)}")
    print(f"     - Ordered POs: {proc.get('ordered', 0)}")
    print(f"     - Received POs: {proc.get('received', 0)}")
    print(f"     - Total Procurement Spend: Rs {proc.get('total_spend', 0):,.2f}")

    # -------------------------------------------------------------
    # SECTION 3: OPD QUEUES BY SUB-QUEUE TAB (/api/visits/?queue=...)
    # -------------------------------------------------------------
    print("\n--- SECTION 3: OPD QUEUES BY SUB-QUEUE TAB (/api/visits/?queue=...) ---")
    client.force_authenticate(user=u_doctor)
    
    queue_tabs = ['ALL', 'TRIAGE', 'DOCTOR', 'LAB', 'PHARMACY', 'COMPLETED']
    for q_tab in queue_tabs:
        param = f"&queue={q_tab}" if q_tab != 'ALL' else ""
        res = client.get(f'/api/visits/?facility={rc_a4.id}&date={today_str}{param}')
        assert res.status_code == 200, f"OPD Queue tab {q_tab} failed: {res.status_code}"
        records = res.data.get('results', res.data)
        print(f" [OK] Queue Tab [{q_tab}]: {len(records)} visits found")
        for v in records:
            tok = v.get('token_number') or (v.get('token_details') or {}).get('token_number') or 'N/A'
            p_name = v.get('patient_name') or (v.get('patient_details') or {}).get('name') or 'Unknown'
            print(f"      - Token #{tok} | {p_name} | Status: {v['status']} | Queue: {v['current_queue']}")

    # 3.2 OPD History Summary Endpoint
    res = client.get(f'/api/visits/history-summary/?facility={rc_a4.id}')
    assert res.status_code == 200, f"OPD History summary failed: {res.status_code}"
    history_days = res.data
    print(f" [OK] OPD History Summary Log: {len(history_days)} historical dates tracked.")

    # -------------------------------------------------------------
    # SECTION 4: LABORATORY SPECIMEN QUEUES (/api/lab/orders/)
    # -------------------------------------------------------------
    print("\n--- SECTION 4: LABORATORY SPECIMEN QUEUES (/api/lab/orders/) ---")
    client.force_authenticate(user=u_lab)
    
    # 4.1 All Orders
    res = client.get('/api/lab/orders/')
    assert res.status_code == 200
    all_lab = res.data.get('results', res.data)
    print(f" [OK] Laboratory Total Orders in Facility: {len(all_lab)}")
    
    # Check breakdown across pipeline stages
    ordered_q = [o for o in all_lab if o['status'] == 'ORDERED']
    sample_col_q = [o for o in all_lab if o['status'] == 'SAMPLE_COLLECTED']
    verified_q = [o for o in all_lab if o['status'] == 'VERIFIED']
    
    print(f"     - Stage 1: Sample Collection Queue (ORDERED): {len(ordered_q)} orders")
    for o in ordered_q:
        print(f"        * Order #{o['id']} | Test: {o.get('test_name', 'N/A')} | Patient: {o.get('patient_name', 'N/A')}")
        
    print(f"     - Stage 2: Result Entry & Verification Queue (SAMPLE_COLLECTED): {len(sample_col_q)} orders")
    for o in sample_col_q:
        sample_code = (o.get('sample') or {}).get('sample_code') or 'Pending'
        print(f"        * Order #{o['id']} | Test: {o.get('test_name', 'N/A')} | Barcode: {sample_code} | Patient: {o.get('patient_name', 'N/A')}")

    print(f"     - Stage 3: Completed Reports (VERIFIED): {len(verified_q)} orders")
    for o in verified_q:
        res_val = (o.get('result') or {}).get('result_value') or 'N/A'
        res_unit = (o.get('result') or {}).get('unit') or ''
        res_flag = (o.get('result') or {}).get('interpretation_flag') or ''
        print(f"        * Order #{o['id']} | Test: {o.get('test_name', 'N/A')} | Result: {res_val} {res_unit} ({res_flag})")

    # -------------------------------------------------------------
    # SECTION 5: PHARMACY PRESCRIPTIONS QUEUE (/api/pharmacy/prescriptions/)
    # -------------------------------------------------------------
    print("\n--- SECTION 5: PHARMACY PRESCRIPTIONS QUEUE ---")
    client.force_authenticate(user=u_pharmacy)
    res = client.get(f'/api/pharmacy/prescriptions/?facility={rc_a4.id}')
    assert res.status_code == 200
    rx_list = res.data.get('results', res.data)
    print(f" [OK] Pharmacy Total Prescriptions: {len(rx_list)}")
    
    pending_rx = [rx for rx in rx_list if rx['status'] == 'PENDING']
    dispensed_rx = [rx for rx in rx_list if rx['status'] == 'DISPENSED']
    print(f"     - Prescriptions Pending Dispensation: {len(pending_rx)}")
    for rx in pending_rx:
        print(f"        * Rx #{rx['id']} | Patient: {rx.get('patient_name', 'N/A')} | Doctor: {rx.get('doctor_name', 'N/A')} | Status: {rx['status']}")
    print(f"     - Prescriptions Dispensed: {len(dispensed_rx)}")
    for rx in dispensed_rx:
        print(f"        * Rx #{rx['id']} | Patient: {rx.get('patient_name', 'N/A')} | Status: {rx['status']}")

    # -------------------------------------------------------------
    # SECTION 6: REFERRALS QUEUES (/api/referrals/)
    # -------------------------------------------------------------
    print("\n--- SECTION 6: REFERRALS QUEUES (/api/referrals/) ---")
    client.force_authenticate(user=u_doctor)
    res = client.get('/api/referrals/')
    assert res.status_code == 200
    ref_list = res.data.get('results', res.data)
    print(f" [OK] Total Accessible Referrals: {len(ref_list)}")
    for r in ref_list:
        print(f"      - Ref #{r.get('referral_number', r['id'])} | Patient: {r.get('patient_name', 'N/A')} | {r.get('source_facility_name', 'Source')} -> {r.get('destination_facility_name', 'Dest')} | Status: {r.get('status')}")

    print("\n" + "=" * 70)
    print("   ALL DASHBOARDS AND QUEUES ARE CONFIRMED 100% OPERATIONAL & REFLECTING!")
    print("=" * 70)

if __name__ == '__main__':
    test_all_dashboards_and_queues()

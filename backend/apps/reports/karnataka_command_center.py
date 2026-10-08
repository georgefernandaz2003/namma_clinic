"""
Karnataka Public Health Command Center & Predictive Analytics Data Engine.
Provides authoritative state-wide healthcare intelligence, cascading hierarchy
(State -> District -> Zone -> Hospital), multi-month historical trends, and predictive forecasts.
"""
from typing import Dict, List, Any
import datetime

# ---------------------------------------------------------------------------
# 1. KARNATAKA HEALTHCARE ECOSYSTEM HIERARCHY (NO WARD LEVEL)
# Hierarchy: State -> District -> Zone -> Hospital / Facility
# ---------------------------------------------------------------------------

KARNATAKA_DISTRICTS = [
    {
        "id": "dakshina_kannada",
        "name": "Dakshina Kannada",
        "region": "Coastal Karnataka",
        "headquarters": "Mangaluru",
        "population": 2089649,
        "zones": [
            {
                "id": "mangalore_zone",
                "name": "Mangalore Zone",
                "hospitals": [
                    {"id": "wenlock_dh", "name": "District Hospital Mangalore (Wenlock)", "type": "District Hospital", "beds": 750, "icu": 60, "base_opd": 850, "base_ipd": 95, "base_emer": 45, "staff_doc": 62, "staff_nurse": 180},
                    {"id": "lady_goschen_gh", "name": "Lady Goschen General Hospital", "type": "General Hospital", "beds": 260, "icu": 20, "base_opd": 380, "base_ipd": 40, "base_emer": 18, "staff_doc": 28, "staff_nurse": 85},
                    {"id": "surathkal_chc", "name": "Surathkal Community Health Centre", "type": "CHC", "beds": 30, "icu": 4, "base_opd": 160, "base_ipd": 8, "base_emer": 8, "staff_doc": 8, "staff_nurse": 22},
                    {"id": "bejai_uphc", "name": "Mangalore Urban PHC (Bejai)", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 95, "base_ipd": 2, "base_emer": 4, "staff_doc": 3, "staff_nurse": 8}
                ]
            },
            {
                "id": "bantwal_zone",
                "name": "Bantwal Zone",
                "hospitals": [
                    {"id": "bantwal_th", "name": "Bantwal Taluk Hospital", "type": "Taluk Hospital", "beds": 100, "icu": 8, "base_opd": 220, "base_ipd": 16, "base_emer": 12, "staff_doc": 14, "staff_nurse": 38},
                    {"id": "bc_road_chc", "name": "BC Road Community Health Centre", "type": "CHC", "beds": 30, "icu": 2, "base_opd": 140, "base_ipd": 6, "base_emer": 6, "staff_doc": 6, "staff_nurse": 18}
                ]
            },
            {
                "id": "puttur_zone",
                "name": "Puttur Zone",
                "hospitals": [
                    {"id": "puttur_th", "name": "Puttur Taluk Hospital", "type": "Taluk Hospital", "beds": 100, "icu": 10, "base_opd": 240, "base_ipd": 18, "base_emer": 14, "staff_doc": 16, "staff_nurse": 42}
                ]
            }
        ]
    },
    {
        "id": "mysuru",
        "name": "Mysuru",
        "region": "Southern Karnataka",
        "headquarters": "Mysuru",
        "population": 3001127,
        "zones": [
            {
                "id": "mysuru_city_zone",
                "name": "Mysuru City Zone",
                "hospitals": [
                    {"id": "kr_hospital_mysuru", "name": "KR Teaching District Hospital (MMCRI)", "type": "Medical College Hospital", "beds": 1050, "icu": 90, "base_opd": 1200, "base_ipd": 140, "base_emer": 65, "staff_doc": 95, "staff_nurse": 280},
                    {"id": "cheluvamba_gh", "name": "Cheluvamba General Hospital", "type": "General Hospital", "beds": 400, "icu": 30, "base_opd": 450, "base_ipd": 45, "base_emer": 22, "staff_doc": 38, "staff_nurse": 110},
                    {"id": "chamundipuram_uphc", "name": "Chamundipuram Urban PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 110, "base_ipd": 2, "base_emer": 5, "staff_doc": 4, "staff_nurse": 9}
                ]
            },
            {
                "id": "nanjangud_zone",
                "name": "Nanjangud Zone",
                "hospitals": [
                    {"id": "nanjangud_th", "name": "Nanjangud Taluk Hospital", "type": "Taluk Hospital", "beds": 120, "icu": 10, "base_opd": 260, "base_ipd": 20, "base_emer": 14, "staff_doc": 16, "staff_nurse": 44}
                ]
            },
            {
                "id": "hunsur_zone",
                "name": "Hunsur Zone",
                "hospitals": [
                    {"id": "hunsur_gh", "name": "Hunsur General Hospital", "type": "General Hospital", "beds": 80, "icu": 6, "base_opd": 190, "base_ipd": 14, "base_emer": 10, "staff_doc": 12, "staff_nurse": 32}
                ]
            }
        ]
    },
    {
        "id": "belagavi",
        "name": "Belagavi",
        "region": "Northern Karnataka",
        "headquarters": "Belagavi",
        "population": 4779661,
        "zones": [
            {
                "id": "belagavi_city_zone",
                "name": "Belagavi City Zone",
                "hospitals": [
                    {"id": "bims_belagavi", "name": "Belagavi Institute of Medical Sciences (BIMS)", "type": "Medical College Hospital", "beds": 850, "icu": 75, "base_opd": 980, "base_ipd": 110, "base_emer": 55, "staff_doc": 82, "staff_nurse": 240},
                    {"id": "civil_hospital_belagavi", "name": "Civil District Hospital Belagavi", "type": "District Hospital", "beds": 500, "icu": 40, "base_opd": 620, "base_ipd": 65, "base_emer": 32, "staff_doc": 48, "staff_nurse": 140},
                    {"id": "vadgaon_uphc", "name": "Vadgaon Urban PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 105, "base_ipd": 2, "base_emer": 4, "staff_doc": 3, "staff_nurse": 8}
                ]
            },
            {
                "id": "chikkodi_zone",
                "name": "Chikkodi Zone",
                "hospitals": [
                    {"id": "chikkodi_th", "name": "Chikkodi Taluk Hospital", "type": "Taluk Hospital", "beds": 100, "icu": 8, "base_opd": 230, "base_ipd": 18, "base_emer": 12, "staff_doc": 15, "staff_nurse": 38}
                ]
            },
            {
                "id": "gokak_zone",
                "name": "Gokak Zone",
                "hospitals": [
                    {"id": "gokak_gh", "name": "Gokak General Hospital", "type": "General Hospital", "beds": 90, "icu": 6, "base_opd": 210, "base_ipd": 15, "base_emer": 11, "staff_doc": 13, "staff_nurse": 35}
                ]
            }
        ]
    },
    {
        "id": "kalaburagi",
        "name": "Kalaburagi",
        "region": "Kalyana Karnataka",
        "headquarters": "Kalaburagi",
        "population": 2566326,
        "zones": [
            {
                "id": "kalaburagi_central_zone",
                "name": "Kalaburagi Central Zone",
                "hospitals": [
                    {"id": "gims_kalaburagi", "name": "Gulbarga Institute of Medical Sciences (GIMS)", "type": "Medical College Hospital", "beds": 750, "icu": 65, "base_opd": 880, "base_ipd": 95, "base_emer": 48, "staff_doc": 70, "staff_nurse": 210},
                    {"id": "sedam_rd_uphc", "name": "Sedam Road Urban PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 90, "base_ipd": 2, "base_emer": 4, "staff_doc": 3, "staff_nurse": 7}
                ]
            },
            {
                "id": "aland_zone",
                "name": "Aland Zone",
                "hospitals": [
                    {"id": "aland_th", "name": "Aland Taluk Hospital", "type": "Taluk Hospital", "beds": 100, "icu": 8, "base_opd": 210, "base_ipd": 16, "base_emer": 10, "staff_doc": 14, "staff_nurse": 36}
                ]
            },
            {
                "id": "sedam_zone",
                "name": "Sedam Zone",
                "hospitals": [
                    {"id": "sedam_chc", "name": "Sedam Community Health Centre", "type": "CHC", "beds": 30, "icu": 4, "base_opd": 135, "base_ipd": 6, "base_emer": 6, "staff_doc": 6, "staff_nurse": 16}
                ]
            }
        ]
    },
    {
        "id": "bengaluru_urban",
        "name": "Bengaluru Urban",
        "region": "Metropolitan Region",
        "headquarters": "Bengaluru",
        "population": 9621551,
        "zones": [
            {
                "id": "central_zone",
                "name": "Central Zone",
                "hospitals": [
                    {"id": "victoria_hospital", "name": "Victoria Hospital & Bowring Complex", "type": "Medical College Hospital", "beds": 1200, "icu": 110, "base_opd": 1450, "base_ipd": 160, "base_emer": 80, "staff_doc": 115, "staff_nurse": 340},
                    {"id": "kc_general_hospital", "name": "KC General Secondary Hospital", "type": "Secondary Hospital", "beds": 300, "icu": 25, "base_opd": 420, "base_ipd": 42, "base_emer": 20, "staff_doc": 32, "staff_nurse": 95},
                    {"id": "malleshwaram_uphc", "name": "Malleshwaram Namma Clinic PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 125, "base_ipd": 3, "base_emer": 5, "staff_doc": 4, "staff_nurse": 10}
                ]
            },
            {
                "id": "east_zone",
                "name": "East Zone",
                "hospitals": [
                    {"id": "cv_raman_gh", "name": "CV Raman General Hospital", "type": "General Hospital", "beds": 150, "icu": 12, "base_opd": 280, "base_ipd": 24, "base_emer": 15, "staff_doc": 20, "staff_nurse": 55}
                ]
            },
            {
                "id": "south_zone",
                "name": "South Zone",
                "hospitals": [
                    {"id": "jayanagar_gh", "name": "Jayanagar General Hospital", "type": "General Hospital", "beds": 200, "icu": 18, "base_opd": 340, "base_ipd": 30, "base_emer": 18, "staff_doc": 24, "staff_nurse": 68}
                ]
            }
        ]
    },
    {
        "id": "shivamogga",
        "name": "Shivamogga",
        "region": "Malnad Region",
        "headquarters": "Shivamogga",
        "population": 1752759,
        "zones": [
            {
                "id": "shivamogga_city_zone",
                "name": "Shivamogga City Zone",
                "hospitals": [
                    {"id": "mcgann_hospital", "name": "McGann Teaching District Hospital", "type": "Medical College Hospital", "beds": 650, "icu": 50, "base_opd": 720, "base_ipd": 75, "base_emer": 36, "staff_doc": 56, "staff_nurse": 170},
                    {"id": "shivamogga_kote_uphc", "name": "Shivamogga Urban PHC (Kote)", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 85, "base_ipd": 2, "base_emer": 3, "staff_doc": 3, "staff_nurse": 7}
                ]
            },
            {
                "id": "bhadravati_zone",
                "name": "Bhadravati Zone",
                "hospitals": [
                    {"id": "bhadravati_gh", "name": "Bhadravati General Hospital", "type": "General Hospital", "beds": 120, "icu": 12, "base_opd": 250, "base_ipd": 20, "base_emer": 14, "staff_doc": 18, "staff_nurse": 45}
                ]
            }
        ]
    },
    {
        "id": "ballari",
        "name": "Ballari",
        "region": "Central Mining Belt",
        "headquarters": "Ballari",
        "population": 2452595,
        "zones": [
            {
                "id": "ballari_city_zone",
                "name": "Ballari City Zone",
                "hospitals": [
                    {"id": "vims_ballari", "name": "Vijayanagar Institute of Medical Sciences (VIMS)", "type": "Medical College Hospital", "beds": 800, "icu": 70, "base_opd": 920, "base_ipd": 100, "base_emer": 50, "staff_doc": 76, "staff_nurse": 225},
                    {"id": "ballari_civil_gh", "name": "Ballari Civil Hospital", "type": "District Hospital", "beds": 350, "icu": 25, "base_opd": 410, "base_ipd": 45, "base_emer": 22, "staff_doc": 34, "staff_nurse": 98}
                ]
            },
            {
                "id": "sandur_zone",
                "name": "Sandur Zone",
                "hospitals": [
                    {"id": "sandur_th", "name": "Sandur Taluk Hospital", "type": "Taluk Hospital", "beds": 80, "icu": 6, "base_opd": 180, "base_ipd": 14, "base_emer": 10, "staff_doc": 12, "staff_nurse": 30}
                ]
            }
        ]
    },
    {
        "id": "tumakuru",
        "name": "Tumakuru",
        "region": "Southern Plains",
        "headquarters": "Tumakuru",
        "population": 2678980,
        "zones": [
            {
                "id": "tumakuru_urban_zone",
                "name": "Tumakuru Urban Zone",
                "hospitals": [
                    {"id": "tumakuru_dh", "name": "Tumakuru District Hospital", "type": "District Hospital", "beds": 450, "icu": 35, "base_opd": 560, "base_ipd": 58, "base_emer": 28, "staff_doc": 42, "staff_nurse": 125},
                    {"id": "mandipet_uphc", "name": "Mandipet Urban PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 95, "base_ipd": 2, "base_emer": 4, "staff_doc": 3, "staff_nurse": 8}
                ]
            },
            {
                "id": "kunigal_zone",
                "name": "Kunigal Zone",
                "hospitals": [
                    {"id": "kunigal_th", "name": "Kunigal Taluk Hospital", "type": "Taluk Hospital", "beds": 90, "icu": 6, "base_opd": 195, "base_ipd": 15, "base_emer": 11, "staff_doc": 13, "staff_nurse": 34}
                ]
            }
        ]
    },
    {
        "id": "udupi",
        "name": "Udupi",
        "region": "Coastal Karnataka",
        "headquarters": "Udupi",
        "population": 1177361,
        "zones": [
            {
                "id": "udupi_city_zone",
                "name": "Udupi City Zone",
                "hospitals": [
                    {"id": "udupi_dh", "name": "Udupi District Hospital", "type": "District Hospital", "beds": 250, "icu": 20, "base_opd": 360, "base_ipd": 35, "base_emer": 18, "staff_doc": 26, "staff_nurse": 75},
                    {"id": "ajjarkad_uphc", "name": "Ajjarkad Urban PHC", "type": "Urban PHC", "beds": 10, "icu": 0, "base_opd": 90, "base_ipd": 2, "base_emer": 4, "staff_doc": 3, "staff_nurse": 7}
                ]
            },
            {
                "id": "kundapura_zone",
                "name": "Kundapura Zone",
                "hospitals": [
                    {"id": "kundapura_th", "name": "Kundapura Taluk Hospital", "type": "Taluk Hospital", "beds": 100, "icu": 8, "base_opd": 210, "base_ipd": 16, "base_emer": 11, "staff_doc": 14, "staff_nurse": 36}
                ]
            }
        ]
    }
]

# ---------------------------------------------------------------------------
# 2. TIME PERIOD MULTIPLIERS & LABELS
# ---------------------------------------------------------------------------
TIME_PERIODS = {
    "today": {"label": "Today", "multiplier": 0.033, "days": 1},
    "yesterday": {"label": "Yesterday", "multiplier": 0.032, "days": 1},
    "last_7_days": {"label": "Last 7 Days", "multiplier": 0.23, "days": 7},
    "last_30_days": {"label": "Last 30 Days", "multiplier": 1.0, "days": 30},
    "last_3_months": {"label": "Last 3 Months", "multiplier": 3.0, "days": 90},
    "last_6_months": {"label": "Last 6 Months", "multiplier": 6.0, "days": 180},
    "last_1_year": {"label": "Last 1 Year", "multiplier": 12.0, "days": 365},
    "custom": {"label": "Custom Range", "multiplier": 1.0, "days": 30}
}

# ---------------------------------------------------------------------------
# 3. CORE COMMAND CENTER DATA GENERATION ENGINE
# ---------------------------------------------------------------------------

def get_karnataka_command_center_data(district_id: str = "all", zone_id: str = "all", hospital_id: str = "all", time_period: str = "last_30_days", role: str = "HOSPITAL_ADMIN") -> Dict[str, Any]:
    """
    Computes aggregated public health intelligence, trends, predictions, and alerts
    for any node in the hierarchy (State -> District -> Zone -> Hospital).
    """
    time_info = TIME_PERIODS.get(time_period, TIME_PERIODS["last_30_days"])
    t_mult = time_info["multiplier"]

    # 1. Resolve Filter Scope & Breadcrumbs
    selected_district = None
    selected_zone = None
    selected_hospital = None

    if district_id and district_id != "all":
        selected_district = next((d for d in KARNATAKA_DISTRICTS if d["id"] == district_id), None)
    
    if selected_district and zone_id and zone_id != "all":
        selected_zone = next((z for z in selected_district["zones"] if z["id"] == zone_id), None)

    if selected_zone and hospital_id and hospital_id != "all":
        selected_hospital = next((h for h in selected_zone["hospitals"] if h["id"] == hospital_id), None)

    # Build Cascading Select Options
    available_districts = [{"id": "all", "name": "All Karnataka Districts"}] + [
        {"id": d["id"], "name": f"{d['name']} ({d['region']})"} for d in KARNATAKA_DISTRICTS
    ]

    available_zones = [{"id": "all", "name": "All Zones in District"}]
    if selected_district:
        available_zones += [{"id": z["id"], "name": z["name"]} for z in selected_district["zones"]]

    available_hospitals = [{"id": "all", "name": "All Hospitals in Zone"}]
    if selected_zone:
        available_hospitals += [{"id": h["id"], "name": f"{h['name']} [{h['type']}]"} for h in selected_zone["hospitals"]]
    elif selected_district:
        # If district selected but zone is 'all', allow selecting any hospital in that district
        all_dist_hospitals = []
        for z in selected_district["zones"]:
            for h in z["hospitals"]:
                all_dist_hospitals.append({"id": h["id"], "name": f"{h['name']} ({z['name']})"})
        available_hospitals += all_dist_hospitals

    # Breadcrumbs
    breadcrumbs = ["Central Command", "Karnataka State"]
    if selected_district:
        breadcrumbs.append(selected_district["name"])
    if selected_zone:
        breadcrumbs.append(selected_zone["name"])
    if selected_hospital:
        breadcrumbs.append(selected_hospital["name"])

    # Determine scope level name
    if selected_hospital:
        scope_level = "HOSPITAL"
        scope_name = selected_hospital["name"]
        scope_type = f"{selected_hospital['type']} Level"
    elif selected_zone:
        scope_level = "ZONE"
        scope_name = f"{selected_zone['name']} ({selected_district['name']})"
        scope_type = "Zone Healthcare Cluster"
    elif selected_district:
        scope_level = "DISTRICT"
        scope_name = f"{selected_district['name']} District"
        scope_type = f"District Administration ({selected_district['region']})"
    else:
        scope_level = "STATE"
        scope_name = "Karnataka State Apex Command"
        scope_type = "State-Wide Healthcare Ecosystem (31 Districts)"

    # 2. Filter Active Hospitals
    active_hospitals = []
    if selected_hospital:
        active_hospitals = [selected_hospital]
    elif selected_zone:
        active_hospitals = selected_zone["hospitals"]
    elif selected_district:
        for z in selected_district["zones"]:
            active_hospitals.extend(z["hospitals"])
    else:
        for d in KARNATAKA_DISTRICTS:
            for z in d["zones"]:
                active_hospitals.extend(z["hospitals"])

    # 3. Aggregate Baseline Capacity & Workload
    total_facilities = len(active_hospitals)
    total_beds = sum(h["beds"] for h in active_hospitals)
    total_icu = sum(h["icu"] for h in active_hospitals)
    
    # Scale base metrics by time multiplier
    daily_opd = sum(h["base_opd"] for h in active_hospitals)
    daily_ipd = sum(h["base_ipd"] for h in active_hospitals)
    daily_emer = sum(h["base_emer"] for h in active_hospitals)
    
    tot_opd = int(daily_opd * 30 * t_mult)
    tot_ipd = int(daily_ipd * 30 * t_mult)
    tot_emer = int(daily_emer * 30 * t_mult)
    tot_patients = int((tot_opd * 0.72) + tot_ipd)

    total_doctors = sum(h["staff_doc"] for h in active_hospitals)
    total_nurses = sum(h["staff_nurse"] for h in active_hospitals)
    total_lab_techs = max(int(total_doctors * 0.42), 2)
    total_pharmacists = max(int(total_doctors * 0.35), 2)
    total_inventory = max(int(total_facilities * 1.2), 1)

    # Bed Occupancy calculations (varies naturally between 76% and 91%)
    bed_occ_rate = round(min(89.4, max(72.0, (daily_ipd * 6.5 / max(total_beds, 1)) * 100)), 1)
    if scope_level == "STATE":
        bed_occ_rate = 84.6
    occupied_beds = int(total_beds * (bed_occ_rate / 100))

    icu_occ_rate = round(min(96.5, bed_occ_rate + 7.2), 1)
    occupied_icu = int(total_icu * (icu_occ_rate / 100))

    # Disease and Stock Alert counts (scaled by scope)
    disease_alert_count = max(1, int(len(active_hospitals) * 0.22))
    stock_alert_count = max(1, int(len(active_hospitals) * 0.14))

    # 4. Top 8 Command Center KPIs
    kpis = [
        {"id": "facilities", "label": "Healthcare Facilities", "value": f"{total_facilities:,}", "change": f"{scope_type}", "unit": "Active Centers", "status": "normal"},
        {"id": "patients", "label": "Active Patients", "value": f"{tot_patients:,}", "change": "+8.4% MoM", "unit": "Citizens Tracked", "status": "normal"},
        {"id": "opd", "label": "OPD Visits", "value": f"{tot_opd:,}", "change": "+12.1% Surge", "unit": f"{time_info['label']}", "status": "normal"},
        {"id": "ipd", "label": "IPD Admissions", "value": f"{tot_ipd:,}", "change": "+4.2% Inflow", "unit": f"{time_info['label']}", "status": "normal"},
        {"id": "emergency", "label": "Emergency Cases", "value": f"{tot_emer:,}", "change": "+18.6% Acute", "unit": "Trauma & Acute", "status": "warning" if tot_emer > 500 else "normal"},
        {"id": "bed_occupancy", "label": "Bed Occupancy Rate", "value": f"{bed_occ_rate}%", "change": f"{occupied_beds:,}/{total_beds:,} Beds", "unit": "Ward Load", "status": "warning" if bed_occ_rate > 85 else "normal"},
        {"id": "disease_alerts", "label": "Disease Alerts", "value": str(disease_alert_count), "change": "Dengue & Enteric", "unit": "Outbreak Signals", "status": "critical" if disease_alert_count >= 4 else "warning"},
        {"id": "stock_alerts", "label": "Medicine Stock Alerts", "value": str(stock_alert_count), "change": "Stockout <7 Days", "unit": "Critical Generics", "status": "critical" if stock_alert_count >= 3 else "warning"}
    ]

    # 5. Multi-Month Trend Data (Jan -> Oct Historical, Nov -> Dec Forecast)
    # Scaled gracefully by the volume of the selected scope
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov (F)", "Dec (F)"]
    growth_curve = [0.82, 0.85, 0.88, 0.90, 0.94, 0.98, 1.02, 1.09, 1.15, 1.21, 1.28, 1.34]
    
    opd_monthly = [int(tot_opd * g / (1.21 if time_period == "last_30_days" else 1.0)) for g in growth_curve]
    ipd_monthly = [int(tot_ipd * g / (1.21 if time_period == "last_30_days" else 1.0)) for g in growth_curve]
    emer_monthly = [int(tot_emer * g / (1.21 if time_period == "last_30_days" else 1.0)) for g in growth_curve]
    bed_occ_monthly = [round(min(97.0, 74.0 + (i * 2.2)), 1) for i in range(12)]
    dengue_curve = [int(tot_opd * 0.008 * factor) for factor in [0.4, 0.3, 0.5, 0.6, 0.9, 1.4, 2.1, 2.6, 2.8, 2.2, 1.5, 0.9]]
    medicine_burn_monthly = [int(tot_opd * 2.8 * g / 1.21) for g in growth_curve]

    trend_series = {
        "months": months,
        "split_index": 10,  # 0-9 are Historical (Jan-Oct), 10-11 are Forecast (Nov-Dec)
        "opd": opd_monthly,
        "ipd": ipd_monthly,
        "emergency": emer_monthly,
        "bed_occupancy": bed_occ_monthly,
        "disease_cases": dengue_curve,
        "medicine_consumption": medicine_burn_monthly,
        "hospital_crowd_index": [int(v / max(len(active_hospitals), 1)) for v in opd_monthly]
    }

    # 6. Comparison Chart (District or Zone comparison depending on scope)
    comparison_chart = {}
    if scope_level == "STATE":
        comparison_chart = {
            "title": "District Healthcare Workload & Bed Utilization across Karnataka",
            "categories": [d["name"] for d in KARNATAKA_DISTRICTS],
            "series": [
                {"name": "OPD Visits (Thousands)", "values": [round(sum(h["base_opd"] for z in d["zones"] for h in z["hospitals"]) * 30 * t_mult / 1000, 1) for d in KARNATAKA_DISTRICTS], "color": "#3B82F6"},
                {"name": "Total Beds", "values": [sum(h["beds"] for z in d["zones"] for h in z["hospitals"]) for d in KARNATAKA_DISTRICTS], "color": "#10B981"},
                {"name": "Active Emergency Cases", "values": [round(sum(h["base_emer"] for z in d["zones"] for h in z["hospitals"]) * 30 * t_mult / 100, 1) for d in KARNATAKA_DISTRICTS], "color": "#F59E0B"}
            ]
        }
    elif scope_level == "DISTRICT":
        comparison_chart = {
            "title": f"Zone Healthcare Workload in {selected_district['name']}",
            "categories": [z["name"] for z in selected_district["zones"]],
            "series": [
                {"name": "OPD Visits (Thousands)", "values": [round(sum(h["base_opd"] for h in z["hospitals"]) * 30 * t_mult / 1000, 1) for z in selected_district["zones"]], "color": "#3B82F6"},
                {"name": "Total Beds", "values": [sum(h["beds"] for h in z["hospitals"]) for z in selected_district["zones"]], "color": "#10B981"},
                {"name": "ICU Beds", "values": [sum(h["icu"] for h in z["hospitals"]) for z in selected_district["zones"]], "color": "#EF4444"}
            ]
        }
    else:
        # Zone or Hospital comparison
        comparison_chart = {
            "title": f"Hospital Capacity & Intake Comparison in {scope_name}",
            "categories": [h["name"][:20] for h in active_hospitals],
            "series": [
                {"name": "Daily OPD Capacity", "values": [h["base_opd"] for h in active_hospitals], "color": "#3B82F6"},
                {"name": "Inpatient Beds", "values": [h["beds"] for h in active_hospitals], "color": "#10B981"},
                {"name": "ICU Beds", "values": [h["icu"] for h in active_hospitals], "color": "#8B5CF6"}
            ]
        }

    # 7. Disease Intelligence
    disease_list = [
        {
            "id": "dengue",
            "name": "Dengue Fever",
            "category": "Vector-Borne (Aedes)",
            "current_cases": int(tot_patients * 0.038),
            "new_cases": int(tot_patients * 0.007),
            "active_cases": int(tot_patients * 0.015),
            "recovered": int(tot_patients * 0.022),
            "mortality": max(1, int(tot_patients * 0.00015)),
            "trend": "Increasing",
            "forecast_7d": "+18%",
            "forecast_14d": "+24%",
            "forecast_30d": "-12% (Post-fogging)",
            "risk": "HIGH",
            "affected_area": "Dakshina Kannada & Coastal Belt",
            "recommended_action": "Deploy ASHA fever-screening squad; conduct intensive anti-larval chemical fogging."
        },
        {
            "id": "malaria",
            "name": "Malaria (P. vivax & falciparum)",
            "category": "Vector-Borne (Anopheles)",
            "current_cases": int(tot_patients * 0.012),
            "new_cases": int(tot_patients * 0.002),
            "active_cases": int(tot_patients * 0.004),
            "recovered": int(tot_patients * 0.008),
            "mortality": 0,
            "trend": "Stable",
            "forecast_7d": "+2%",
            "forecast_14d": "+3%",
            "forecast_30d": "-4%",
            "risk": "MODERATE",
            "affected_area": "Mangalore Port & Construction Corridors",
            "recommended_action": "Routine surveillance; stock Artemisinin combination therapy and rapid diagnostic kits."
        },
        {
            "id": "tuberculosis",
            "name": "Tuberculosis (NTEP)",
            "category": "Airborne Chronic",
            "current_cases": int(tot_patients * 0.025),
            "new_cases": int(tot_patients * 0.003),
            "active_cases": int(tot_patients * 0.019),
            "recovered": int(tot_patients * 0.006),
            "mortality": max(1, int(tot_patients * 0.0002)),
            "trend": "Stable",
            "forecast_7d": "+0.5%",
            "forecast_14d": "+1.1%",
            "forecast_30d": "+2.0%",
            "risk": "MODERATE",
            "affected_area": "Kalaburagi & Belagavi Industrial Clusters",
            "recommended_action": "Directly Observed Therapy (DOTS) compliance tracking; ensure 6-month fixed-dose refill continuity."
        },
        {
            "id": "respiratory_infections",
            "name": "Acute Respiratory Infections (ARI/ILI)",
            "category": "Airborne Droplet",
            "current_cases": int(tot_patients * 0.082),
            "new_cases": int(tot_patients * 0.018),
            "active_cases": int(tot_patients * 0.035),
            "recovered": int(tot_patients * 0.046),
            "mortality": max(1, int(tot_patients * 0.0001)),
            "trend": "Increasing",
            "forecast_7d": "+15%",
            "forecast_14d": "+22%",
            "forecast_30d": "+10%",
            "risk": "HIGH",
            "affected_area": "Bengaluru Urban, Mysuru & Tumakuru",
            "recommended_action": "Increase nebulizer stations at OPD triage; buffer Azithromycin and Amoxicillin stocks."
        },
        {
            "id": "hypertension",
            "name": "Essential Hypertension (NCD)",
            "category": "Non-Communicable Chronic",
            "current_cases": int(tot_patients * 0.145),
            "new_cases": int(tot_patients * 0.012),
            "active_cases": int(tot_patients * 0.138),
            "recovered": int(tot_patients * 0.007),
            "mortality": 0,
            "trend": "Stable / Controlled",
            "forecast_7d": "+1%",
            "forecast_14d": "+2%",
            "forecast_30d": "+4%",
            "risk": "LOW (91.5% Controlled)",
            "affected_area": "Karnataka-wide Cohort",
            "recommended_action": "Automate 30-day generic Amlodipine refills; monitor mean cohort BP in primary care."
        },
        {
            "id": "diabetes",
            "name": "Type-2 Diabetes Mellitus (NCD)",
            "category": "Non-Communicable Chronic",
            "current_cases": int(tot_patients * 0.128),
            "new_cases": int(tot_patients * 0.011),
            "active_cases": int(tot_patients * 0.121),
            "recovered": int(tot_patients * 0.007),
            "mortality": 0,
            "trend": "Stable / Controlled",
            "forecast_7d": "+1.2%",
            "forecast_14d": "+2.5%",
            "forecast_30d": "+5%",
            "risk": "LOW (89.2% Controlled)",
            "affected_area": "Karnataka-wide Cohort",
            "recommended_action": "Ensure Metformin buffer stock; quarterly HbA1c screening campaigns."
        },
        {
            "id": "cardiovascular",
            "name": "Cardiovascular Disease (CVD/IHD)",
            "category": "Non-Communicable Chronic",
            "current_cases": int(tot_patients * 0.034),
            "new_cases": int(tot_patients * 0.004),
            "active_cases": int(tot_patients * 0.031),
            "recovered": int(tot_patients * 0.003),
            "mortality": max(1, int(tot_patients * 0.0004)),
            "trend": "Stable",
            "forecast_7d": "+0.8%",
            "forecast_14d": "+1.4%",
            "forecast_30d": "+3.0%",
            "risk": "MODERATE",
            "affected_area": "Mysuru, Belagavi & Ballari Centers",
            "recommended_action": "Tertiary cardiologist tele-consultation linkage and emergency Sorbitrate supply."
        },
        {
            "id": "chronic_kidney",
            "name": "Chronic Kidney Disease (CKD)",
            "category": "Non-Communicable Chronic",
            "current_cases": int(tot_patients * 0.015),
            "new_cases": int(tot_patients * 0.001),
            "active_cases": int(tot_patients * 0.014),
            "recovered": 0,
            "mortality": max(1, int(tot_patients * 0.0003)),
            "trend": "Stable",
            "forecast_7d": "+0.4%",
            "forecast_14d": "+0.9%",
            "forecast_30d": "+1.8%",
            "risk": "MODERATE",
            "affected_area": "Udupi, Dakshina Kannada & Shivamogga",
            "recommended_action": "District hospital hemodialysis slot optimization and creatinine laboratory monitoring."
        }
    ]

    # 8. Healthcare Operations Metrics
    healthcare_ops = {
        "opd_visits": tot_opd,
        "ipd_admissions": tot_ipd,
        "emergency_cases": tot_emer,
        "bed_capacity": total_beds,
        "occupied_beds": occupied_beds,
        "bed_occupancy_pct": bed_occ_rate,
        "icu_capacity": total_icu,
        "occupied_icu": occupied_icu,
        "icu_occupancy_pct": icu_occ_rate,
        "avg_waiting_time_mins": 34 if scope_level != "HOSPITAL" else 28,
        "avg_length_of_stay_days": 4.5,
        "referrals_in": int(tot_ipd * 0.14),
        "referrals_out": int(tot_emer * 0.22),
        "discharges": int(tot_ipd * 0.88),
        "readmissions_30d": int(tot_ipd * 0.038),
        "facility_workload_status": "High Operational Velocity" if bed_occ_rate > 80 else "Normal Operational Velocity"
    }

    # 9. Pharmacy & Supply Chain + Medicine Predictions
    # Scaled by facility count and volume
    medicines = [
        {
            "name": "Paracetamol 500mg Tab",
            "generic": "Antipyretic / Analgesic",
            "current_stock": int(tot_opd * 0.65),
            "daily_consumption": int(tot_opd * 0.65 / 15),
            "predicted_consumption": int(tot_opd * 0.65 / 15 * 1.25),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=12)).strftime("%d %b %Y"),
            "days_runway": 12.0,
            "risk": "CRITICAL" if 12.0 < 15 else "HIGH",
            "recommended_reorder": int(tot_opd * 0.65 * 1.8),
            "po_status": "KSMSCL Indent PO-2026-KA-49 Active",
            "monthly_inflow": int(tot_opd * 0.5),
            "monthly_outflow": int(tot_opd * 0.65)
        },
        {
            "name": "Metformin 500mg Tab",
            "generic": "Oral Hypoglycemic (Type-2 DM)",
            "current_stock": int(tot_opd * 0.45),
            "daily_consumption": int(tot_opd * 0.45 / 22),
            "predicted_consumption": int(tot_opd * 0.45 / 22 * 1.05),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=21)).strftime("%d %b %Y"),
            "days_runway": 21.0,
            "risk": "MODERATE",
            "recommended_reorder": int(tot_opd * 0.45 * 1.2),
            "po_status": "Routine Quarterly Indent",
            "monthly_inflow": int(tot_opd * 0.4),
            "monthly_outflow": int(tot_opd * 0.42)
        },
        {
            "name": "Amlodipine 5mg Tab",
            "generic": "Antihypertensive (Calcium Channel Blocker)",
            "current_stock": int(tot_opd * 0.52),
            "daily_consumption": int(tot_opd * 0.52 / 24),
            "predicted_consumption": int(tot_opd * 0.52 / 24 * 1.04),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=23)).strftime("%d %b %Y"),
            "days_runway": 23.0,
            "risk": "MODERATE",
            "recommended_reorder": int(tot_opd * 0.52 * 1.1),
            "po_status": "Healthy Buffer Refill",
            "monthly_inflow": int(tot_opd * 0.5),
            "monthly_outflow": int(tot_opd * 0.48)
        },
        {
            "name": "ORS Sachet 21.8g",
            "generic": "Oral Rehydration Salts (WHO formula)",
            "current_stock": int(tot_opd * 0.15),
            "daily_consumption": int(tot_opd * 0.15 / 8),
            "predicted_consumption": int(tot_opd * 0.15 / 8 * 1.4),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=6)).strftime("%d %b %Y"),
            "days_runway": 5.7,
            "risk": "CRITICAL",
            "recommended_reorder": int(tot_opd * 0.15 * 3.0),
            "po_status": "Emergency Expedited PO-2026-KA-82",
            "monthly_inflow": int(tot_opd * 0.12),
            "monthly_outflow": int(tot_opd * 0.22)
        },
        {
            "name": "Amoxicillin 500mg Cap",
            "generic": "Broad-Spectrum Antibiotic",
            "current_stock": int(tot_opd * 0.35),
            "daily_consumption": int(tot_opd * 0.35 / 28),
            "predicted_consumption": int(tot_opd * 0.35 / 28 * 1.15),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=24)).strftime("%d %b %Y"),
            "days_runway": 24.3,
            "risk": "NORMAL",
            "recommended_reorder": int(tot_opd * 0.35 * 1.0),
            "po_status": "Scheduled Replenishment",
            "monthly_inflow": int(tot_opd * 0.35),
            "monthly_outflow": int(tot_opd * 0.31)
        },
        {
            "name": "Cetirizine 10mg Tab",
            "generic": "Antihistaminic / Anti-Allergic",
            "current_stock": int(tot_opd * 0.38),
            "daily_consumption": int(tot_opd * 0.38 / 31),
            "predicted_consumption": int(tot_opd * 0.38 / 31 * 1.08),
            "predicted_stockout_date": (datetime.date.today() + datetime.timedelta(days=29)).strftime("%d %b %Y"),
            "days_runway": 28.7,
            "risk": "NORMAL",
            "recommended_reorder": int(tot_opd * 0.38 * 0.9),
            "po_status": "Stock Buffered",
            "monthly_inflow": int(tot_opd * 0.38),
            "monthly_outflow": int(tot_opd * 0.33)
        }
    ]

    pharmacy_summary = {
        "total_skus": 240,
        "total_inventory_valuation_inr": f"₹{(tot_opd * 18.5):,.0f}",
        "daily_consumption_units": int(sum(m["daily_consumption"] for m in medicines)),
        "monthly_consumption_units": int(sum(m["daily_consumption"] * 30 for m in medicines)),
        "low_stock_medicines_count": 8 if scope_level == "STATE" else 2,
        "critical_stock_medicines_count": 3 if scope_level == "STATE" else 1,
        "near_expiry_count": 5 if scope_level == "STATE" else 1,
        "expired_count": 0,
        "fefo_compliance_pct": 100.0
    }

    # 10. Workforce Intelligence
    workforce = {
        "doctors": {
            "total": total_doctors,
            "on_duty": int(total_doctors * 0.88),
            "on_leave": total_doctors - int(total_doctors * 0.88),
            "patients_per_doctor": round(tot_opd / max(int(total_doctors * 0.88 * 30 * t_mult), 1), 1),
            "workload_status": "High Clinical Intake" if tot_opd / max(total_doctors, 1) > 150 else "Optimal"
        },
        "nurses": {
            "total": total_nurses,
            "on_duty": int(total_nurses * 0.87),
            "on_leave": total_nurses - int(total_nurses * 0.87),
            "patient_to_nurse_ratio": f"1:{max(4, int(occupied_beds / max(int(total_nurses * 0.87 * 0.5), 1)))}",
            "workload_status": "Elevated Shift Strain" if bed_occ_rate > 85 else "Balanced"
        },
        "lab_technicians": {
            "total": total_lab_techs,
            "on_duty": int(total_lab_techs * 0.92),
            "tests_processed": int(tot_opd * 0.42),
            "pending_tests": int(tot_opd * 0.05),
            "avg_turnaround_hrs": 2.2,
            "workload_status": "Approaching Analyzer Ceiling" if tot_opd * 0.05 > 400 else "Stable"
        },
        "pharmacists": {
            "total": total_pharmacists,
            "on_duty": int(total_pharmacists * 0.90),
            "prescriptions_processed": int(tot_opd * 0.88),
            "dispensing_volume_daily": int(tot_opd * 0.88 / 30 / t_mult),
            "workload_status": "High Dispensation Pace"
        },
        "inventory_officers": {
            "total": total_inventory,
            "on_duty": total_inventory,
            "low_stock_alerts_handled": stock_alert_count,
            "critical_pos_raised": 4 if scope_level == "STATE" else 1,
            "reorder_requirements": "Active KSMSCL Indent Follow-up"
        }
    }

    # 11. Predictive Intelligence Suite (Current, Trend, Prediction, Risk, Recommended Action)
    predictions = [
        {
            "id": "pred_disease",
            "category": "Disease Outbreak Prediction",
            "title": "Vector-Borne Dengue Clustering Forecast",
            "current": f"{int(tot_patients * 0.038):,} Active Clinical Presentations",
            "trend": "Increasing (+18% MoM across coastal & peri-urban taluks)",
            "prediction": "+24% case surge projected over next 14 days due to late monsoon drainage stagnation",
            "risk": "HIGH",
            "recommended_action": "Increase ASHA active fever surveillance squads; dispatch municipal ULV larvicide fogging teams."
        },
        {
            "id": "pred_crowd",
            "category": "Hospital Crowd & Waiting Hall Prediction",
            "title": f"OPD Intake Rush & Token Queue Surge in {scope_name}",
            "current": f"{int(daily_opd * 0.95):,} Daily Consultations",
            "trend": "Surging (+14% over baseline intake)",
            "prediction": f"Tomorrow peak rush forecasted at {int(daily_opd * 1.15):,} patients between 09:30 AM – 11:30 AM",
            "risk": "HIGH",
            "recommended_action": "Open 2 supplemental token registration counters and assign senior triage nurses to pre-screen vital signs."
        },
        {
            "id": "pred_beds",
            "category": "Bed Demand & Ward Capacity Prediction",
            "title": "ICU & High-Dependency Unit Bed Ceiling",
            "current": f"{icu_occ_rate}% ICU Occupancy ({occupied_icu}/{total_icu} Beds)",
            "trend": "Approaching Critical Saturation (+6.1% this week)",
            "prediction": "ICU bed demand projected to exceed 96% within 72 hours across referral hospitals",
            "risk": "CRITICAL" if icu_occ_rate > 90 else "HIGH",
            "recommended_action": "Authorize immediate step-down transfer of stable post-op cases to general HDU; alert district referral coordinator."
        },
        {
            "id": "pred_stock",
            "category": "Medicine Stock-out & Procurement Prediction",
            "title": "Oral Rehydration Salt (ORS) & Paracetamol Buffer Runout",
            "current": "ORS: 5.7 days runway • Paracetamol: 12.0 days runway",
            "trend": "Daily burn rate accelerating by +28% due to seasonal acute gastroenteritis and viral fevers",
            "prediction": "ORS sachets predicted to stock out in 6 days; Paracetamol in 12 days without depot delivery",
            "risk": "CRITICAL",
            "recommended_action": "Auto-indent KSMSCL PO-2026-KA-49 for 30,000 units with expedited warehouse dispatch."
        },
        {
            "id": "pred_lab",
            "category": "Laboratory Workload & Turnaround Prediction",
            "title": "Platelet Count & Dengue NS1 Diagnostic Order Surge",
            "current": f"{int(tot_opd * 0.42):,} Lab Tests Conducted ({int(tot_opd * 0.05):,} Pending)",
            "trend": "+22% week-on-week increase in complete blood count (CBC) requests",
            "prediction": "Laboratory diagnostic workload expected to exceed current automated analyzer capacity by 15% next week",
            "risk": "HIGH",
            "recommended_action": "Activate backup cell counter analyzer; schedule overtime laboratory technician shift."
        },
        {
            "id": "pred_staff",
            "category": "Workforce & Nursing Capacity Prediction",
            "title": "Emergency & Inpatient Nursing Ratio Deficit",
            "current": f"{total_nurses} Total Nurses • Shift Ratio {workforce['nurses']['patient_to_nurse_ratio']}",
            "trend": "+18% rise in acute bed occupancy over the last 14 days",
            "prediction": f"Projected shortage of {max(2, int(total_facilities * 1.5))} staff nurses during evening triage and emergency shifts",
            "risk": "HIGH",
            "recommended_action": "Deploy reserve rotational nurses from community outreach rosters to acute clinical inpatient wards."
        }
    ]

    # 12. Alerts & Actions
    alerts = [
        {
            "id": "alt_1",
            "severity": "CRITICAL",
            "problem": "ICU Capacity Ceiling Approached (96.2% Saturation)",
            "location": f"{scope_name} → High Dependency Care Unit",
            "impact": "Only 3 ventilator-equipped emergency beds remaining in critical triage",
            "recommended_action": "Authorize immediate transfer of stabilized convalescent patients to step-down secondary care wards."
        },
        {
            "id": "alt_2",
            "severity": "CRITICAL",
            "problem": "ORS Sachet Stockout Imminent (<6 Days Runway)",
            "location": f"{scope_name} → Central Pharmacy Store",
            "impact": "Severe dehydration treatment risk during acute gastroenteritis presentations",
            "recommended_action": "Expedite KSMSCL regional depot delivery requisition #PO-2026-KA-82 under emergency procurement protocol."
        },
        {
            "id": "alt_3",
            "severity": "HIGH",
            "problem": "Vector-Borne Dengue Infection Spike (+32 Cases in 48h)",
            "location": f"{scope_name} → Infectious Surveillance Catchment",
            "impact": "Intense acute fever admissions straining outpatient clinic consultation slots",
            "recommended_action": "Deploy rapid ASHA fever-detection teams; initiate chemical larvicide thermal fogging in affected clusters."
        },
        {
            "id": "alt_4",
            "severity": "HIGH",
            "problem": "Laboratory Analyzer Diagnostic Queue Backlog",
            "location": f"{scope_name} → Central Diagnostic Unit",
            "impact": "Diagnostic report turnaround time prolonged to 3.8 hours for CBC and platelet profiles",
            "recommended_action": "Activate secondary cell-counter backup; reassign senior technician to evening verification shifts."
        },
        {
            "id": "alt_5",
            "severity": "WARNING",
            "problem": "OPD Morning Registration Hall Queue Delay (>40 min Wait)",
            "location": f"{scope_name} → Outpatient Triage & Token Desks",
            "impact": "Patient waiting hall congestion during morning 09:30 AM rush window",
            "recommended_action": "Open 2 auxiliary digital token counters and assign nursing students for vital sign pre-screening."
        },
        {
            "id": "alt_6",
            "severity": "NORMAL",
            "problem": "Non-Communicable Chronic Disease Control Rate Stabilized (91.5%)",
            "location": f"{scope_name} → NCD Hypertension & Diabetes Clinic",
            "impact": "High generic therapy compliance averted an estimated 14 secondary cardiovascular hospitalizations",
            "recommended_action": "Maintain 30-day automated repeat dispensing and monthly digital tele-monitoring recalls."
        }
    ]

    # 13. Role-Based Tailored Highlights
    role_lens = {
        "active_role": role,
        "role_title": role.replace("_", " ").title(),
        "priority_focus": {
            "HOSPITAL_ADMIN": "Focus on Bed Occupancy (84.6%), Staffing Roster Deficit, and Emergency Inflow Capacity.",
            "DOCTOR": "Focus on Disease Outbreak Clusters (Dengue +18%), Clinical Waiting Hall Load, and Referral Pathways.",
            "NURSE": "Focus on Ward Patient-to-Nurse Ratio (1:5.5), High-Dependency Bed Transfers, and Morning Triage Vitals.",
            "LAB_TECHNICIAN": "Focus on 410 Pending Diagnostic Orders, Platelet Analyzer Workload, and Turnaround Time Target (2.0 hrs).",
            "PHARMACIST": "Focus on Paracetamol & ORS Stockout Forecast (<12 days), FEFO Batch Audit, and Generic Dispensation Velocity.",
            "INVENTORY_OFFICER": "Focus on KSMSCL Reorder Indents #PO-2026-KA-49, Depot Transit Latencies, and Buffer Safety Stock.",
            "DISTRICT_OFFICER": "Focus on Inter-Zone Healthcare Disparities, Tertiary Referral Load, and State Resource Reallocation."
        }.get(role, "State-wide Command Center Governance & Public Health Intelligence.")
    }

    # 14. Return Master Payload
    return {
        "metadata": {
            "title": "KARNATAKA PUBLIC HEALTH COMMAND CENTER",
            "subtitle": "State-wide healthcare intelligence & predictive governance",
            "classification": "DEMO / SYNTHETIC DATA",
            "disclaimer": "This system operates on simulated Karnataka healthcare data covering 9 representative districts, 21 zones, and 33 hospitals for public health demonstration and decision-support training.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "authoritative_state": "Karnataka (KA)"
        },
        "filters": {
            "selected_state": "Karnataka",
            "selected_district": district_id,
            "selected_zone": zone_id,
            "selected_hospital": hospital_id,
            "selected_time_period": time_period,
            "available_districts": available_districts,
            "available_zones": available_zones,
            "available_hospitals": available_hospitals,
            "available_time_periods": [
                {"id": k, "label": v["label"]} for k, v in TIME_PERIODS.items()
            ],
            "breadcrumbs": breadcrumbs,
            "active_scope": {
                "level": scope_level,
                "name": scope_name,
                "type": scope_type,
                "facility_count": total_facilities,
                "total_beds": total_beds
            }
        },
        "command_center": {
            "kpis": kpis,
            "comparison_chart": comparison_chart,
            "top_predictions": predictions[:3],
            "critical_alerts": [a for a in alerts if a["severity"] in ["CRITICAL", "HIGH"]][:4]
        },
        "trend_analysis": {
            "months": trend_series["months"],
            "split_index": trend_series["split_index"],
            "series": trend_series
        },
        "disease_intelligence": {
            "diseases": disease_list,
            "top_vector_threat": disease_list[0],
            "top_airborne_threat": disease_list[3],
            "chronic_stabilization": disease_list[4]
        },
        "healthcare_operations": healthcare_ops,
        "pharmacy_supply": {
            "summary": pharmacy_summary,
            "medicines": medicines
        },
        "workforce_intelligence": workforce,
        "predictive_intelligence": {
            "predictions": predictions,
            "stockout_risk_medicines": [m for m in medicines if m["risk"] in ["CRITICAL", "HIGH"]]
        },
        "alerts_actions": alerts,
        "role_lens": role_lens
    }

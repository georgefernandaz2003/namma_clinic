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
    breadcrumbs = ["Karnataka"]
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
        scope_type = f"District Healthcare Network ({selected_district['region']})"
    else:
        scope_level = "STATE"
        scope_name = "Karnataka State Overview"
        scope_type = "State-Wide Healthcare Overview (31 Districts)"

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
        {"id": "bed_occupancy", "label": "Bed Occupancy", "value": f"{bed_occ_rate}%", "change": f"{occupied_beds:,}/{total_beds:,} Beds", "unit": "Ward Load", "status": "warning" if bed_occ_rate > 85 else "normal"},
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
            "title": "District Healthcare Overview",
            "categories": [d["name"] for d in KARNATAKA_DISTRICTS],
            "series": [
                {"name": "OPD Visits (Thousands)", "values": [round(sum(h["base_opd"] for z in d["zones"] for h in z["hospitals"]) * 30 * t_mult / 1000, 1) for d in KARNATAKA_DISTRICTS], "color": "#3B82F6"},
                {"name": "Total Beds", "values": [sum(h["beds"] for z in d["zones"] for h in z["hospitals"]) for d in KARNATAKA_DISTRICTS], "color": "#10B981"},
                {"name": "Active Emergency Cases", "values": [round(sum(h["base_emer"] for z in d["zones"] for h in z["hospitals"]) * 30 * t_mult / 100, 1) for d in KARNATAKA_DISTRICTS], "color": "#F59E0B"}
            ]
        }
    elif scope_level == "DISTRICT":
        comparison_chart = {
            "title": f"Zone Healthcare Overview — {selected_district['name']}",
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
            "title": f"Facility Healthcare Overview — {scope_name}",
            "categories": [h["name"][:20] for h in active_hospitals],
            "series": [
                {"name": "Daily OPD Capacity", "values": [h["base_opd"] for h in active_hospitals], "color": "#3B82F6"},
                {"name": "Inpatient Beds", "values": [h["beds"] for h in active_hospitals], "color": "#10B981"},
                {"name": "ICU Beds", "values": [h["icu"] for h in active_hospitals], "color": "#8B5CF6"}
            ]
        }

    # 7. Disease Intelligence (Analytical Dashboard Data Model)
    scope_ratio = tot_patients / 353352.0 if tot_patients else 1.0
    if scope_level == "STATE":
        scope_ratio = 1.0

    disease_list = [
        {
            "id": "dengue",
            "name": "Dengue Fever",
            "short_name": "Dengue",
            "category": "Vector-Borne",
            "current_cases": int(13427 * scope_ratio),
            "active_cases": int(5300 * scope_ratio),
            "recovered": int(7773 * scope_ratio),
            "new_cases": int(1240 * scope_ratio),
            "mortality": max(1, int(18 * scope_ratio)),
            "trend": "Increasing",
            "forecast_7d": "+18%",
            "forecast_14d": "+24%",
            "forecast_30d": "-12%",
            "risk": "HIGH",
            "affected_areas": ["Dakshina Kannada", "Udupi", "Mysuru"],
            "recommended_action": "Increase surveillance and vector-control activities."
        },
        {
            "id": "malaria",
            "name": "Malaria",
            "short_name": "Malaria",
            "category": "Vector-Borne",
            "current_cases": int(4240 * scope_ratio),
            "active_cases": int(1413 * scope_ratio),
            "recovered": int(2826 * scope_ratio),
            "new_cases": int(180 * scope_ratio),
            "mortality": 0,
            "trend": "Increasing",
            "forecast_7d": "+2%",
            "forecast_14d": "+3%",
            "forecast_30d": "-4%",
            "risk": "MODERATE",
            "affected_areas": ["Mangalore Port", "Dakshina Kannada", "Udupi"],
            "recommended_action": "Routine surveillance; stock Artemisinin combination therapy and rapid diagnostic kits."
        },
        {
            "id": "tuberculosis",
            "name": "Tuberculosis (TB)",
            "short_name": "Tuberculosis",
            "category": "Airborne",
            "current_cases": int(8833 * scope_ratio),
            "active_cases": int(6713 * scope_ratio),
            "recovered": int(2120 * scope_ratio),
            "new_cases": int(480 * scope_ratio),
            "mortality": max(1, int(42 * scope_ratio)),
            "trend": "Increasing",
            "forecast_7d": "+0.5%",
            "forecast_14d": "+1.1%",
            "forecast_30d": "+2.0%",
            "risk": "HIGH",
            "affected_areas": ["Kalaburagi", "Belagavi", "Bengaluru Urban"],
            "recommended_action": "Directly Observed Therapy (DOTS) compliance tracking; ensure 6-month fixed-dose refill continuity."
        },
        {
            "id": "respiratory_infections",
            "name": "Respiratory Infection",
            "short_name": "Respiratory Infection",
            "category": "Airborne",
            "current_cases": int(28974 * scope_ratio),
            "active_cases": int(12367 * scope_ratio),
            "recovered": int(16254 * scope_ratio),
            "new_cases": int(1420 * scope_ratio),
            "mortality": max(1, int(24 * scope_ratio)),
            "trend": "Increasing",
            "forecast_7d": "+15%",
            "forecast_14d": "+22%",
            "forecast_30d": "+10%",
            "risk": "HIGH",
            "affected_areas": ["Bengaluru Urban", "Mysuru", "Tumakuru"],
            "recommended_action": "Increase nebulizer stations at OPD triage; buffer Azithromycin and Amoxicillin stocks."
        },
        {
            "id": "hypertension",
            "name": "Hypertension",
            "short_name": "Hypertension",
            "category": "Non-Communicable",
            "current_cases": int(51240 * scope_ratio),
            "active_cases": int(21450 * scope_ratio),
            "recovered": int(29790 * scope_ratio),
            "new_cases": int(420 * scope_ratio),
            "mortality": 0,
            "trend": "Increasing",
            "forecast_7d": "+1%",
            "forecast_14d": "+2%",
            "forecast_30d": "+4%",
            "risk": "LOW",
            "affected_areas": ["Bengaluru Urban", "Mysuru", "Belagavi"],
            "recommended_action": "Automate 30-day generic Amlodipine refills; monitor mean cohort BP in primary care."
        },
        {
            "id": "diabetes",
            "name": "Diabetes",
            "short_name": "Diabetes",
            "category": "Non-Communicable",
            "current_cases": int(45230 * scope_ratio),
            "active_cases": int(18210 * scope_ratio),
            "recovered": int(27020 * scope_ratio),
            "new_cases": int(310 * scope_ratio),
            "mortality": 0,
            "trend": "Increasing",
            "forecast_7d": "+1.2%",
            "forecast_14d": "+2.5%",
            "forecast_30d": "+5%",
            "risk": "LOW",
            "affected_areas": ["Belagavi", "Tumakuru", "Kalaburagi"],
            "recommended_action": "Ensure Metformin buffer stock; quarterly HbA1c screening campaigns."
        },
        {
            "id": "cardiovascular",
            "name": "Cardiovascular Disease",
            "short_name": "Cardiovascular",
            "category": "Non-Communicable",
            "current_cases": int(12040 * scope_ratio),
            "active_cases": int(4200 * scope_ratio),
            "recovered": int(7840 * scope_ratio),
            "new_cases": int(150 * scope_ratio),
            "mortality": max(1, int(35 * scope_ratio)),
            "trend": "Stable",
            "forecast_7d": "+0.8%",
            "forecast_14d": "+1.4%",
            "forecast_30d": "+3.0%",
            "risk": "MODERATE",
            "affected_areas": ["Mysuru", "Belagavi", "Ballari"],
            "recommended_action": "Tertiary cardiologist tele-consultation linkage and emergency Sorbitrate supply."
        },
        {
            "id": "chronic_kidney",
            "name": "Chronic Kidney Disease (CKD)",
            "short_name": "CKD",
            "category": "Non-Communicable",
            "current_cases": int(5310 * scope_ratio),
            "active_cases": int(2797 * scope_ratio),
            "recovered": int(2513 * scope_ratio),
            "new_cases": int(80 * scope_ratio),
            "mortality": max(1, int(15 * scope_ratio)),
            "trend": "Stable",
            "forecast_7d": "+0.4%",
            "forecast_14d": "+0.9%",
            "forecast_30d": "+1.8%",
            "risk": "MODERATE",
            "affected_areas": ["Udupi", "Dakshina Kannada", "Shivamogga"],
            "recommended_action": "District hospital hemodialysis slot optimization and creatinine laboratory monitoring."
        }
    ]

    # Calculate Top KPIs (Section 3: Exactly 4 compact KPIs)
    total_active_cases = sum(d["active_cases"] for d in disease_list)
    total_new_cases = sum(d["new_cases"] for d in disease_list)
    high_risk_diseases_count = len([d for d in disease_list if d["risk"] == "HIGH"])
    increasing_diseases_count = len([d for d in disease_list if d["trend"] == "Increasing"])

    # Monthly Trends (Jan - Dec: Historical Jan-Oct, Forecast Nov-Dec)
    disease_monthly_trends = {
        "dengue": [int(v * scope_ratio) for v in [3800, 3200, 4100, 4800, 6200, 8900, 11400, 12800, 13100, 13427, 15840, 14200]],
        "malaria": [int(v * scope_ratio) for v in [4100, 3900, 4050, 4120, 4200, 4350, 4400, 4300, 4280, 4240, 4325, 4150]],
        "tuberculosis": [int(v * scope_ratio) for v in [8600, 8550, 8620, 8680, 8710, 8740, 8760, 8790, 8810, 8833, 8877, 8920]],
        "respiratory_infections": [int(v * scope_ratio) for v in [24000, 23500, 22800, 21900, 22400, 23800, 25200, 26900, 27800, 28974, 33320, 36500]],
        "hypertension": [int(v * scope_ratio) for v in [49800, 50000, 50200, 50400, 50600, 50800, 50950, 51050, 51150, 51240, 51750, 52200]],
        "diabetes": [int(v * scope_ratio) for v in [43800, 44000, 44200, 44400, 44600, 44800, 44900, 45050, 45150, 45230, 45770, 46200]],
        "cardiovascular": [int(v * scope_ratio) for v in [11600, 11680, 11740, 11800, 11860, 11920, 11960, 11990, 12010, 12040, 12130, 12250]],
        "chronic_kidney": [int(v * scope_ratio) for v in [5150, 5180, 5200, 5220, 5240, 5260, 5280, 5295, 5300, 5310, 5330, 5360]]
    }

    # Geographic Distribution per disease
    disease_geo_distribution = {}
    if scope_level == "STATE":
        geo_regions = [d["name"] for d in KARNATAKA_DISTRICTS]
        weights = {
            "dengue": [0.255, 0.182, 0.162, 0.145, 0.034, 0.021, 0.012, 0.101, 0.088],
            "malaria": [0.280, 0.120, 0.110, 0.150, 0.040, 0.030, 0.020, 0.100, 0.150],
            "tuberculosis": [0.080, 0.150, 0.190, 0.220, 0.180, 0.050, 0.060, 0.040, 0.030],
            "respiratory_infections": [0.090, 0.180, 0.140, 0.280, 0.080, 0.060, 0.050, 0.080, 0.040],
            "hypertension": [0.080, 0.160, 0.150, 0.270, 0.110, 0.070, 0.060, 0.060, 0.040],
            "diabetes": [0.070, 0.150, 0.160, 0.260, 0.120, 0.080, 0.060, 0.060, 0.040],
            "cardiovascular": [0.060, 0.210, 0.180, 0.240, 0.090, 0.060, 0.080, 0.050, 0.030],
            "chronic_kidney": [0.190, 0.120, 0.110, 0.180, 0.060, 0.140, 0.040, 0.040, 0.120]
        }
        for d in disease_list:
            w_list = weights.get(d["id"], [1.0 / len(geo_regions)] * len(geo_regions))
            disease_geo_distribution[d["id"]] = [
                {"name": geo_regions[i], "cases": max(1, int(d["current_cases"] * w_list[i]))}
                for i in range(len(geo_regions))
            ]
    elif scope_level == "DISTRICT":
        geo_regions = [z["name"] for z in selected_district["zones"]]
        for d in disease_list:
            disease_geo_distribution[d["id"]] = [
                {"name": z_name, "cases": max(1, int(d["current_cases"] / len(geo_regions)))}
                for z_name in geo_regions
            ]
    else:
        geo_regions = [h["name"][:20] for h in active_hospitals]
        for d in disease_list:
            disease_geo_distribution[d["id"]] = [
                {"name": h_name, "cases": max(1, int(d["current_cases"] / max(len(geo_regions), 1)))}
                for h_name in geo_regions
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

    # 11. Predictions & Trends (Clean, compact format: Title, Current, Forecast, Risk, Recommendation)
    compact_predictions = [
        {
            "id": "pred_dengue",
            "title": "Dengue Cases",
            "current": "13,427" if scope_level == "STATE" else f"{int(tot_patients * 0.038):,}",
            "forecast": "+24%",
            "risk": "HIGH",
            "recommendation": "Increase surveillance."
        },
        {
            "id": "pred_hospital_demand",
            "title": "Hospital Demand",
            "current": "13,722 / day" if scope_level == "STATE" else f"{int(daily_opd * 0.95):,} / day",
            "forecast": "+21%",
            "risk": "HIGH",
            "recommendation": "Prepare additional capacity."
        },
        {
            "id": "pred_icu",
            "title": "ICU Occupancy",
            "current": "91.8%" if scope_level == "STATE" else f"{icu_occ_rate}%",
            "forecast": "96%",
            "risk": "CRITICAL",
            "recommendation": "Review bed capacity."
        },
        {
            "id": "pred_medicine",
            "title": "Medicine Stock",
            "current": f"{medicines[3]['current_stock']:,} units",
            "forecast": "Run out in 6 days",
            "risk": "HIGH",
            "recommendation": "Initiate replenishment."
        }
    ]

    # 12. Alerts & Recommendations (Clean, compact format: Alert, Status, Short explanation, Recommendation)
    compact_alerts = [
        {
            "id": "alt_1",
            "title": "ICU Occupancy",
            "severity": "CRITICAL",
            "status": "96.2% occupied" if scope_level == "STATE" else f"{icu_occ_rate}% occupied",
            "explanation": "Expected to exceed capacity.",
            "recommendation": "Review available ICU capacity."
        },
        {
            "id": "alt_2",
            "title": "Medicine Stock",
            "severity": "HIGH",
            "status": "ORS stock projected to run out within 6 days.",
            "explanation": "Accelerated consumption due to seasonal fevers.",
            "recommendation": "Initiate replenishment."
        },
        {
            "id": "alt_3",
            "title": "Dengue Cases",
            "severity": "HIGH",
            "status": "Cases increased by 32 in the last 48 hours.",
            "explanation": "Clusters detected in peri-urban catchments.",
            "recommendation": "Increase surveillance."
        },
        {
            "id": "alt_4",
            "title": "Outpatient Waiting Time",
            "severity": "WARNING",
            "status": "Average waiting time reached 34 minutes.",
            "explanation": "Morning registration queue congestion.",
            "recommendation": "Open auxiliary registration counters."
        }
    ]

    # Health Overview (4 short insights)
    health_overview = {
        "whats_changing": "Outpatient visits increased 12%.",
        "where": f"Highest demand: {selected_district['name'] if selected_district else 'Mysuru'} district.",
        "forecast": "Dengue cases expected to increase 24%.",
        "action": "Increase surveillance in affected zones."
    }

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
        }.get(role, "State-wide Healthcare Telemetry & Predictive Analytics.")
    }

    # 14. Return Master Payload
    return {
        "metadata": {
            "title": "Healthcare Dashboard",
            "subtitle": "Karnataka • State-wide Health Overview",
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
            "health_overview": health_overview,
            "kpis": kpis,
            "comparison_chart": comparison_chart,
            "top_predictions": compact_predictions,
            "critical_alerts": compact_alerts
        },
        "trend_analysis": {
            "months": trend_series["months"],
            "split_index": trend_series["split_index"],
            "series": trend_series
        },
        "disease_intelligence": {
            "summary_kpis": {
                "total_active_cases": total_active_cases,
                "new_cases": total_new_cases,
                "high_risk_diseases": high_risk_diseases_count,
                "diseases_increasing": increasing_diseases_count,
            },
            "diseases": disease_list,
            "monthly_trends": disease_monthly_trends,
            "geographic_distribution": disease_geo_distribution,
            "geo_scope_type": "District" if scope_level == "STATE" else ("Zone" if scope_level == "DISTRICT" else "Hospital"),
            "months": months,
            "split_index": 10,
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
            "predictions": compact_predictions,
            "stockout_risk_medicines": [m for m in medicines if m["risk"] in ["CRITICAL", "HIGH"]]
        },
        "alerts_actions": compact_alerts,
        "role_lens": role_lens
    }

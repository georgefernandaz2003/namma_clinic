"""
Public Health Intelligence Forecasting & Seasonal Analysis - STEP 2 Module
Authoritative, database-driven epidemiological forecasting and seasonal analysis service.

Derives strictly from real database records across:
- apps.surveillance.models.DiseaseCase
- apps.facilities.models.Facility
- apps.geography.models.District, Ward

Statistical Method:
- Weighted Moving Average (WMA) with Autoregressive Extension
- Window: Configurable (default 6 weeks)
- Weights: Linearly increasing recency weights w = [1, 2, ..., K]
- Non-negativity: Lower bounds, upper bounds, and predictions are strictly >= 0.0
- Explainability: Clear bounds, variance-derived confidence intervals, no black-box ML
- Safe Terminology: Describes projections as surveillance signals, never "confirmed outbreaks"
"""

import datetime
import math
from django.db.models import Count, Q
from django.utils import timezone

from apps.surveillance.models import DiseaseCase
from apps.facilities.models import Facility
from apps.geography.models import District, Ward
from apps.surveillance.demographic_services import (
    filter_cases_by_demographics,
    normalize_severity,
    normalize_gender,
    resolve_patient_demographics,
    AGE_GROUPS,
    SEVERITY_MILD,
    SEVERITY_MODERATE,
    SEVERITY_SEVERE,
    SEVERITY_UNKNOWN,
)
from apps.surveillance.vulnerable_population_services import (
    filter_cases_by_vulnerable_group,
    normalize_vulnerable_group,
    VULNERABLE_GROUPS,
    VULNERABLE_GROUP_UNKNOWN,
)
from apps.surveillance.patient_type_services import (
    filter_cases_by_patient_type,
    annotate_case_patient_type,
    get_case_patient_type,
    PATIENT_TYPE_NEW,
    PATIENT_TYPE_FOLLOW_UP,
    PATIENT_TYPE_UNKNOWN,
)
from apps.surveillance.intelligence_services import (
    resolve_date,
    compute_trend_status,
    resolve_facility_scope,
    ScopeResult
)
from apps.surveillance.intelligence_forecast_risk_services import calculate_forecast_risk

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


# ---------------------------------------------------------------------------
# 1. Weekly Time Series Generation
# ---------------------------------------------------------------------------

def build_disease_time_series(facility_ids=None, district_id=None, disease_name=None,
                              as_of_date=None, weeks_count=52, age_group=None, gender=None,
                              severity=None, vulnerable_group=None, patient_type=None):
    """
    Builds a continuous weekly disease time series ending at as_of_date.
    
    Guarantees:
    - Every week is exactly 7 consecutive days
    - Strict continuity: week[k].end + 1 day == week[k+1].start
    - Preserves zero-case weeks without omitting any intervals
    - Uses real database DiseaseCase counts exclusively
    - Fully deterministic based on as_of_date
    - Supports optional demographic, severity, vulnerable group, and patient-type filtering
    """
    as_of = resolve_date(as_of_date)
    weeks_count = max(1, int(weeks_count or 52))

    # Calculate earliest start date for the series
    total_days = weeks_count * 7
    series_start = as_of - datetime.timedelta(days=total_days - 1)

    # Base QuerySet
    qs = DiseaseCase.objects.all()
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name and disease_name.strip():
        qs = qs.filter(disease_name__iexact=disease_name.strip())
        active_disease = disease_name.strip()
    else:
        top_d = qs.values('disease_name').annotate(cnt=Count('id')).order_by('-cnt').first()
        active_disease = top_d['disease_name'] if (top_d and top_d['disease_name']) else 'All Monitored Conditions'
        if top_d and top_d['disease_name']:
            qs = qs.filter(disease_name=top_d['disease_name'])

    # Single aggregation query across the entire date range, respecting all filter layers in order
    scoped_cases = qs.filter(report_date__range=[series_start, as_of])

    # Single efficient query with select_related('patient') and annotated patient type
    cases_qs = annotate_case_patient_type(scoped_cases).select_related('patient')
    cases_list = list(cases_qs)

    has_filters = bool(age_group or gender or severity or vulnerable_group or patient_type)
    if has_filters:
        matching_cases = []
        for c in cases_list:
            # 1. Age group & Gender
            demo = resolve_patient_demographics(
                getattr(c, 'patient', None),
                reference_date=c.report_date,
                allow_stored_age_fallback=False
            )
            if age_group:
                if demo['age_group'] != age_group:
                    continue

            if gender:
                if demo['gender'] != normalize_gender(gender):
                    continue

            # 2. Severity
            if severity:
                sev = normalize_severity(getattr(c, 'severity', None))
                sev_target = normalize_severity(severity)
                if sev != sev_target:
                    continue

            # 3. Vulnerable Group
            if vulnerable_group:
                p = getattr(c, 'patient', None)
                v_info = getattr(p, 'vulnerability_information', None) if p else None
                vg = normalize_vulnerable_group(v_info)
                vg_target = normalize_vulnerable_group(vulnerable_group)
                if vg != vg_target:
                    continue

            # 4. Patient Type
            if patient_type:
                pt = get_case_patient_type(c)
                pt_target = str(patient_type).strip().upper()
                if pt_target == 'FOLLOWUP':
                    pt_target = PATIENT_TYPE_FOLLOW_UP
                if pt != pt_target:
                    continue

            matching_cases.append(c)
    else:
        matching_cases = cases_list

    cases_by_date = {}
    for c in matching_cases:
        r_date = c.report_date
        cases_by_date[r_date] = cases_by_date.get(r_date, 0) + 1

    series = []
    for i in range(weeks_count):
        # Index 0 is oldest week, weeks_count - 1 is most recent week ending at as_of
        offset_from_end = (weeks_count - 1 - i) * 7
        w_end = as_of - datetime.timedelta(days=offset_from_end)
        w_start = w_end - datetime.timedelta(days=6)

        # Count cases within this 7-day interval
        w_cases = 0
        curr_day = w_start
        while curr_day <= w_end:
            w_cases += cases_by_date.get(curr_day, 0)
            curr_day += datetime.timedelta(days=1)

        series.append({
            'week_number': i + 1,
            'week_start': str(w_start),
            'week_end': str(w_end),
            'cases': w_cases
        })

    return {
        'disease': active_disease,
        'as_of_date': str(as_of),
        'weeks_count': len(series),
        'total_cases_in_series': sum(w['cases'] for w in series),
        'series': series
    }


# ---------------------------------------------------------------------------
# 2. Disease Forecasting (WMA Method)
# ---------------------------------------------------------------------------

def generate_disease_forecast(time_series, horizon_weeks=4, has_demographic_filter=False):
    """
    Generates explainable, statistical weekly disease forecasts using a
    Weighted Moving Average (WMA) method.

    Calculation Method:
    - Baseline: Moving average of the most recent observations weighted by recency
      Weights: w = [1, 2, ..., K] normalized over window K (default K=min(6, len(series)))
    - Autoregressive projection: Roll forward projected values for multi-step horizon
    - Bounds: Standard deviation sigma computed over historical window.
      lower_bound = max(0.0, round(predicted - 1.645 * sigma * sqrt(1 + 0.1 * (h - 1)), 1))
      upper_bound = max(lower_bound, round(predicted + 1.645 * sigma * sqrt(1 + 0.1 * (h - 1)), 1))
    
    Safety & Non-negativity:
    - predicted_cases >= 0.0
    - lower_bound >= 0.0
    - upper_bound >= predicted_cases >= lower_bound
    - If total historical cases < 3 or series has fewer than 2 data points:
      returns status = "INSUFFICIENT_DATA" without forcing a forecast
    """
    horizon_weeks = max(1, min(12, int(horizon_weeks or 4)))

    raw_points = time_series.get('series', time_series) if isinstance(time_series, dict) else time_series
    if not raw_points or len(raw_points) < 2:
        return {
            'status': 'INSUFFICIENT_DATA',
            'horizon_weeks': horizon_weeks,
            'method': 'WEIGHTED_MOVING_AVERAGE',
            'points': [],
            'explanation': 'Insufficient historical surveillance records (less than 2 observation weeks) to generate a forecast.'
        }

    case_history = [p['cases'] for p in raw_points]
    total_cases = sum(case_history)

    # Require minimum data baseline to prevent fabricated or spurious predictions
    if total_cases < 3:
        if has_demographic_filter:
            explanation = (
                f"Insufficient historical surveillance cases for the selected demographic criteria "
                f"(total {total_cases} cases recorded). Minimum baseline of 3 cases required to generate a reliable forecast."
            )
        else:
            explanation = (
                f"Insufficient historical surveillance cases (total {total_cases} cases recorded). "
                f"Minimum baseline of 3 cases required."
            )
        return {
            'status': 'INSUFFICIENT_DATA',
            'horizon_weeks': horizon_weeks,
            'method': 'WEIGHTED_MOVING_AVERAGE',
            'points': [],
            'explanation': explanation
        }

    # Window size: up to 6 most recent weeks (or available)
    window_k = min(6, len(case_history))
    recent_history = list(case_history[-window_k:])

    # Calculate baseline variance / standard deviation
    mean_recent = sum(recent_history) / len(recent_history)
    variance = sum((x - mean_recent) ** 2 for x in recent_history) / (len(recent_history) - 1 if len(recent_history) > 1 else 1)
    std_dev = math.sqrt(variance)
    # Ensure baseline dispersion floor of 0.8
    sigma = max(0.8, std_dev)

    # Weights favor recency
    weights = list(range(1, window_k + 1))
    sum_weights = sum(weights)

    # Find the end date of the last historical week
    last_week_end_str = raw_points[-1]['week_end']
    try:
        current_cursor_end = datetime.datetime.strptime(last_week_end_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        current_cursor_end = datetime.date.today()

    forecast_points = []
    rolling_cases = list(case_history)

    for h in range(1, horizon_weeks + 1):
        # Calculate WMA over the most recent window_k points
        sub_window = rolling_cases[-window_k:]
        wma_numerator = sum(w * val for w, val in zip(weights, sub_window))
        predicted_val = wma_numerator / sum_weights

        # Non-negative predicted cases
        predicted_rounded = round(max(0.0, predicted_val), 1)

        # Uncertainty widening factor for multi-step horizon
        expansion = math.sqrt(1.0 + 0.15 * (h - 1))
        margin = 1.645 * sigma * expansion

        lower_bound = round(max(0.0, predicted_val - margin), 1)
        upper_bound = round(max(predicted_rounded, predicted_val + margin), 1)

        f_start = current_cursor_end + datetime.timedelta(days=1)
        f_end = f_start + datetime.timedelta(days=6)
        current_cursor_end = f_end

        forecast_points.append({
            'forecast_week_start': str(f_start),
            'forecast_week_end': str(f_end),
            'predicted_cases': predicted_rounded,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        })

        # Autoregressive step: append prediction to rolling history
        rolling_cases.append(predicted_rounded)

    # Explainable projection summary
    trend_description = (
        "projected to increase" if forecast_points[-1]['predicted_cases'] > forecast_points[0]['predicted_cases']
        else "projected to remain stable or decrease"
    )

    return {
        'status': 'AVAILABLE',
        'horizon_weeks': horizon_weeks,
        'method': 'WEIGHTED_MOVING_AVERAGE',
        'historical_window_weeks': window_k,
        'points': forecast_points,
        'explanation': (
            f"Forecast indicates cases are {trend_description} over the next {horizon_weeks} weeks "
            f"based on a {window_k}-week weighted moving average. Provides a baseline surveillance signal for planning."
        )
    }


# ---------------------------------------------------------------------------
# 3. Seasonal Pattern Analysis
# ---------------------------------------------------------------------------

def build_subgroup_monthly_patterns(month_counts, month_occurrences, represented_months):
    """
    Constructs standardized monthly pattern dictionaries for a specific demographic subgroup.
    """
    patterns = []
    for m in represented_months:
        cnt = month_counts.get(m, 0)
        occ = month_occurrences[m]
        avg = round(cnt / occ, 2)
        patterns.append({
            'month_number': m,
            'month_name': MONTH_NAMES[m - 1],
            'total_cases': cnt,
            'occurrences': occ,
            'average_cases': avg
        })
    return patterns


def compute_subgroup_metrics(patterns, total_cases, months_count):
    """
    Calculates peak_month, seasonal_strength, and seasonal_status for a demographic subgroup.
    """
    if not patterns or total_cases == 0:
        return None, 0.0, 'NOT_ENOUGH_DATA'

    sorted_m = sorted(patterns, key=lambda x: x['average_cases'], reverse=True)
    peak = sorted_m[0] if sorted_m and sorted_m[0]['total_cases'] > 0 else None

    month_averages = [m['average_cases'] for m in patterns]
    num_rep = len(patterns)
    if num_rep > 0:
        mean_monthly = sum(month_averages) / float(num_rep)
        if mean_monthly > 0:
            variance_m = sum((x - mean_monthly) ** 2 for x in month_averages) / float(num_rep)
            cv = math.sqrt(variance_m) / mean_monthly
            seasonal_strength = round(min(1.0, cv), 2)
        else:
            seasonal_strength = 0.0
    else:
        seasonal_strength = 0.0

    if total_cases < 10 or months_count < 6:
        status = 'NOT_ENOUGH_DATA'
    elif seasonal_strength >= 0.45 and peak and peak['total_cases'] >= 3:
        status = 'DETECTED'
    else:
        status = 'WEAK'

    return peak, seasonal_strength, status


def calculate_seasonal_pattern(facility_ids=None, district_id=None, disease_name=None,
                               as_of_date=None, months_count=12, age_group=None, gender=None,
                               severity=None, vulnerable_group=None, patient_type=None):
    """
    Analyzes historical surveillance records across calendar months to identify
    potential seasonal clustering without inferring causality.
    Enhanced for Prompt 7: Supports multi-dimensional demographic seasonality analysis across:
    1. Disease
    2. Age group (seasonal_age_groups)
    3. Gender (seasonal_gender)
    4. Severity (seasonal_severity)
    5. Vulnerable population (seasonal_vulnerable_groups)
    6. Patient type (seasonal_patient_types)
    7. Age + Gender (seasonal_age_gender)
    8. Age + Gender + Severity (seasonal_age_gender_severity)
    9. Age + Gender + Vulnerable Population (seasonal_age_gender_vulnerability)
    10. Age + Gender + Patient Type (seasonal_age_gender_patient_type)

    Guarantees:
    - Point-in-time correct age calculation using DiseaseCase.report_date.
    - Authoritative patient type using point-in-time prior history.
    - Single-pass in-memory cross-tabulation avoiding N+1 queries.
    - Preserves all existing top-level fields for backward compatibility.
    """
    as_of = resolve_date(as_of_date)
    months_count = max(1, min(60, int(months_count or 12)))

    # Compute start date for the seasonal window
    start_year = as_of.year
    start_month = as_of.month - months_count + 1
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    seasonal_start = datetime.date(start_year, start_month, 1)

    qs = DiseaseCase.objects.all()
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name and disease_name.strip():
        qs = qs.filter(disease_name__iexact=disease_name.strip())
        active_disease = disease_name.strip()
    else:
        top_d = qs.values('disease_name').annotate(cnt=Count('id')).order_by('-cnt').first()
        active_disease = top_d['disease_name'] if (top_d and top_d['disease_name']) else 'All Monitored Conditions'
        if top_d and top_d['disease_name']:
            qs = qs.filter(disease_name=top_d['disease_name'])

    scoped_cases = qs.filter(report_date__range=[seasonal_start, as_of])
    if age_group or gender:
        scoped_cases = filter_cases_by_demographics(scoped_cases, age_groups=age_group, genders=gender)
    if severity:
        sev_norm = normalize_severity(severity)
        if sev_norm != SEVERITY_UNKNOWN:
            scoped_cases = scoped_cases.filter(severity=sev_norm)
        else:
            scoped_cases = scoped_cases.filter(severity=severity)
    if vulnerable_group:
        scoped_cases = filter_cases_by_vulnerable_group(scoped_cases, vulnerable_group=vulnerable_group)
    if patient_type:
        scoped_cases = filter_cases_by_patient_type(scoped_cases, patient_type=patient_type)

    # Determine exact occurrences of each calendar month inside [seasonal_start, as_of]
    month_occurrences = {}
    curr_y = start_year
    curr_m = start_month
    for _ in range(months_count):
        month_occurrences[curr_m] = month_occurrences.get(curr_m, 0) + 1
        curr_m += 1
        if curr_m > 12:
            curr_m = 1
            curr_y += 1
    represented_months = sorted(month_occurrences.keys())

    # Single efficient query with select_related('patient') and annotated patient type
    cases_qs = annotate_case_patient_type(scoped_cases).select_related('patient')
    cases_list = list(cases_qs)
    total_seasonal_cases = len(cases_list)

    # Categorize all records
    base_ags = list(AGE_GROUPS)
    base_genders = ['MALE', 'FEMALE', 'OTHER']
    base_severities = [SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE]
    base_vgs = list(VULNERABLE_GROUPS)
    base_pts = [PATIENT_TYPE_NEW, PATIENT_TYPE_FOLLOW_UP]

    has_unk_ag = False
    has_unk_g = False
    has_unk_sev = False
    has_unk_vg = False
    has_unk_pt = False

    classified_records = []
    month_counts_dict = {m: 0 for m in represented_months}

    for c in cases_list:
        m = c.report_date.month if c.report_date else None
        if m in month_counts_dict:
            month_counts_dict[m] += 1

        demo = resolve_patient_demographics(
            getattr(c, 'patient', None),
            reference_date=c.report_date,
            allow_stored_age_fallback=False
        )
        ag = demo['age_group']
        g = demo['gender']
        sev = normalize_severity(getattr(c, 'severity', None))
        patient = getattr(c, 'patient', None)
        v_info = getattr(patient, 'vulnerability_information', None) if patient else None
        vg = normalize_vulnerable_group(v_info)
        pt = get_case_patient_type(c)

        if ag == 'UNKNOWN':
            has_unk_ag = True
        if g == 'UNKNOWN':
            has_unk_g = True
        if sev == SEVERITY_UNKNOWN:
            has_unk_sev = True
        if vg == VULNERABLE_GROUP_UNKNOWN:
            has_unk_vg = True
        if pt == PATIENT_TYPE_UNKNOWN:
            has_unk_pt = True

        classified_records.append((m, ag, g, sev, vg, pt))

    active_ags = list(base_ags) + (['UNKNOWN'] if has_unk_ag else [])
    active_genders = list(base_genders) + (['UNKNOWN'] if has_unk_g else [])
    active_severities = list(base_severities) + ([SEVERITY_UNKNOWN] if has_unk_sev else [])
    active_vgs = list(base_vgs) + ([VULNERABLE_GROUP_UNKNOWN] if has_unk_vg else [])
    active_pts = list(base_pts) + ([PATIENT_TYPE_UNKNOWN] if has_unk_pt else [])

    # Initialize monthly breakdown counters
    ag_month_counts = {ag: {m: 0 for m in represented_months} for ag in active_ags}
    g_month_counts = {g: {m: 0 for m in represented_months} for g in active_genders}
    sev_month_counts = {s: {m: 0 for m in represented_months} for s in active_severities}
    vg_month_counts = {v: {m: 0 for m in represented_months} for v in active_vgs}
    pt_month_counts = {p: {m: 0 for m in represented_months} for p in active_pts}

    age_gender_counts = {ag: {g: {m: 0 for m in represented_months} for g in active_genders} for ag in active_ags}
    ag_g_sev_counts = {ag: {g: {s: {m: 0 for m in represented_months} for s in active_severities} for g in active_genders} for ag in active_ags}
    ag_g_vg_counts = {ag: {g: {v: {m: 0 for m in represented_months} for v in active_vgs} for g in active_genders} for ag in active_ags}
    ag_g_pt_counts = {ag: {g: {p: {m: 0 for m in represented_months} for p in active_pts} for g in active_genders} for ag in active_ags}

    for (m, ag, g, sev, vg, pt) in classified_records:
        if m not in month_counts_dict:
            continue
        if ag in ag_month_counts and m in ag_month_counts[ag]:
            ag_month_counts[ag][m] += 1
        if g in g_month_counts and m in g_month_counts[g]:
            g_month_counts[g][m] += 1
        if sev in sev_month_counts and m in sev_month_counts[sev]:
            sev_month_counts[sev][m] += 1
        if vg in vg_month_counts and m in vg_month_counts[vg]:
            vg_month_counts[vg][m] += 1
        if pt in pt_month_counts and m in pt_month_counts[pt]:
            pt_month_counts[pt][m] += 1

        if ag in age_gender_counts and g in age_gender_counts[ag] and m in age_gender_counts[ag][g]:
            age_gender_counts[ag][g][m] += 1
        if (ag in ag_g_sev_counts and g in ag_g_sev_counts[ag] and sev in ag_g_sev_counts[ag][g] and m in ag_g_sev_counts[ag][g][sev]):
            ag_g_sev_counts[ag][g][sev][m] += 1
        if (ag in ag_g_vg_counts and g in ag_g_vg_counts[ag] and vg in ag_g_vg_counts[ag][g] and m in ag_g_vg_counts[ag][g][vg]):
            ag_g_vg_counts[ag][g][vg][m] += 1
        if (ag in ag_g_pt_counts and g in ag_g_pt_counts[ag] and pt in ag_g_pt_counts[ag][g] and m in ag_g_pt_counts[ag][g][pt]):
            ag_g_pt_counts[ag][g][pt][m] += 1

    # 1D Demographic Breakdowns
    seasonal_age_groups = []
    for ag in active_ags:
        patterns = build_subgroup_monthly_patterns(ag_month_counts[ag], month_occurrences, represented_months)
        total_ag_cases = sum(ag_month_counts[ag].values())
        peak, strength, status_val = compute_subgroup_metrics(patterns, total_ag_cases, months_count)
        seasonal_age_groups.append({
            'age_group': ag,
            'monthly_patterns': patterns,
            'total_cases': total_ag_cases,
            'peak_month': peak,
            'seasonal_strength': strength,
            'seasonal_status': status_val
        })

    seasonal_gender = []
    for g in active_genders:
        patterns = build_subgroup_monthly_patterns(g_month_counts[g], month_occurrences, represented_months)
        total_g_cases = sum(g_month_counts[g].values())
        peak, strength, status_val = compute_subgroup_metrics(patterns, total_g_cases, months_count)
        seasonal_gender.append({
            'gender': g,
            'monthly_patterns': patterns,
            'total_cases': total_g_cases,
            'peak_month': peak,
            'seasonal_strength': strength,
            'seasonal_status': status_val
        })

    seasonal_severity = []
    for s in active_severities:
        patterns = build_subgroup_monthly_patterns(sev_month_counts[s], month_occurrences, represented_months)
        total_s_cases = sum(sev_month_counts[s].values())
        peak, strength, status_val = compute_subgroup_metrics(patterns, total_s_cases, months_count)
        seasonal_severity.append({
            'severity': s,
            'monthly_patterns': patterns,
            'total_cases': total_s_cases,
            'peak_month': peak,
            'seasonal_strength': strength,
            'seasonal_status': status_val
        })

    seasonal_vulnerable_groups = []
    for vg in active_vgs:
        patterns = build_subgroup_monthly_patterns(vg_month_counts[vg], month_occurrences, represented_months)
        total_vg_cases = sum(vg_month_counts[vg].values())
        peak, strength, status_val = compute_subgroup_metrics(patterns, total_vg_cases, months_count)
        seasonal_vulnerable_groups.append({
            'vulnerable_group': vg,
            'monthly_patterns': patterns,
            'total_cases': total_vg_cases,
            'peak_month': peak,
            'seasonal_strength': strength,
            'seasonal_status': status_val
        })

    seasonal_patient_types = []
    for pt in active_pts:
        patterns = build_subgroup_monthly_patterns(pt_month_counts[pt], month_occurrences, represented_months)
        total_pt_cases = sum(pt_month_counts[pt].values())
        peak, strength, status_val = compute_subgroup_metrics(patterns, total_pt_cases, months_count)
        seasonal_patient_types.append({
            'patient_type': pt,
            'monthly_patterns': patterns,
            'total_cases': total_pt_cases,
            'peak_month': peak,
            'seasonal_strength': strength,
            'seasonal_status': status_val
        })

    # Multi-dimensional Cross-tabulation Matrices
    seasonal_age_gender = {}
    for ag in active_ags:
        seasonal_age_gender[ag] = {}
        for g in active_genders:
            patterns = build_subgroup_monthly_patterns(age_gender_counts[ag][g], month_occurrences, represented_months)
            tot = sum(age_gender_counts[ag][g].values())
            seasonal_age_gender[ag][g] = {
                'monthly_patterns': patterns,
                'total_cases': tot
            }

    seasonal_age_gender_severity = {}
    for ag in active_ags:
        seasonal_age_gender_severity[ag] = {}
        for g in active_genders:
            seasonal_age_gender_severity[ag][g] = {}
            for s in active_severities:
                patterns = build_subgroup_monthly_patterns(ag_g_sev_counts[ag][g][s], month_occurrences, represented_months)
                tot = sum(ag_g_sev_counts[ag][g][s].values())
                seasonal_age_gender_severity[ag][g][s] = {
                    'monthly_patterns': patterns,
                    'total_cases': tot
                }

    seasonal_age_gender_vulnerability = {}
    for ag in active_ags:
        seasonal_age_gender_vulnerability[ag] = {}
        for g in active_genders:
            seasonal_age_gender_vulnerability[ag][g] = {}
            for vg in active_vgs:
                patterns = build_subgroup_monthly_patterns(ag_g_vg_counts[ag][g][vg], month_occurrences, represented_months)
                tot = sum(ag_g_vg_counts[ag][g][vg].values())
                seasonal_age_gender_vulnerability[ag][g][vg] = {
                    'monthly_patterns': patterns,
                    'total_cases': tot
                }

    seasonal_age_gender_patient_type = {}
    for ag in active_ags:
        seasonal_age_gender_patient_type[ag] = {}
        for g in active_genders:
            seasonal_age_gender_patient_type[ag][g] = {}
            for pt in active_pts:
                patterns = build_subgroup_monthly_patterns(ag_g_pt_counts[ag][g][pt], month_occurrences, represented_months)
                tot = sum(ag_g_pt_counts[ag][g][pt].values())
                seasonal_age_gender_patient_type[ag][g][pt] = {
                    'monthly_patterns': patterns,
                    'total_cases': tot
                }

    # Rule: Minimum volume required to detect seasonal variation at top level
    if total_seasonal_cases < 10 or months_count < 6:
        return {
            'disease': active_disease,
            'seasonal_status': 'NOT_ENOUGH_DATA',
            'seasonal_strength': 0.0,
            'total_cases_analyzed': total_seasonal_cases,
            'months_analyzed': months_count,
            'highest_case_month': None,
            'lowest_case_month': None,
            'strongest_historical_periods': [],
            'monthly_patterns': [],
            'explanation': (
                f"Insufficient historical surveillance data ({total_seasonal_cases} cases observed across {months_count} months). "
                "A minimum of 10 cases over at least 6 months is required to assess seasonal patterns."
            ),
            'seasonal_age_groups': seasonal_age_groups,
            'seasonal_gender': seasonal_gender,
            'seasonal_severity': seasonal_severity,
            'seasonal_vulnerable_groups': seasonal_vulnerable_groups,
            'seasonal_patient_types': seasonal_patient_types,
            'seasonal_age_gender': seasonal_age_gender,
            'seasonal_age_gender_severity': seasonal_age_gender_severity,
            'seasonal_age_gender_vulnerability': seasonal_age_gender_vulnerability,
            'seasonal_age_gender_patient_type': seasonal_age_gender_patient_type,
        }

    # Represent ONLY calendar months that actually occur in the requested observation window
    monthly_patterns = []
    month_averages = []

    for m in represented_months:
        cnt = month_counts_dict.get(m, 0)
        occurrences = month_occurrences[m]
        avg_cnt = round(cnt / occurrences, 2)
        month_averages.append(avg_cnt)
        monthly_patterns.append({
            'month_number': m,
            'month_name': MONTH_NAMES[m - 1],
            'total_cases': cnt,
            'occurrences': occurrences,
            'average_cases': avg_cnt
        })

    # Find highest and lowest case months strictly from represented months
    sorted_months = sorted(monthly_patterns, key=lambda x: x['average_cases'], reverse=True)
    highest_month = sorted_months[0] if sorted_months and sorted_months[0]['total_cases'] > 0 else None
    lowest_month = sorted_months[-1] if sorted_months else None

    # Calculate seasonal strength metric via coefficient of variation across represented months
    num_represented = len(monthly_patterns)
    if num_represented > 0:
        mean_monthly = sum(month_averages) / float(num_represented)
        if mean_monthly > 0:
            variance_m = sum((x - mean_monthly) ** 2 for x in month_averages) / float(num_represented)
            cv = math.sqrt(variance_m) / mean_monthly
            seasonal_strength = round(min(1.0, cv), 2)
        else:
            seasonal_strength = 0.0
    else:
        seasonal_strength = 0.0

    # Strongest historical periods (top 3 represented months with > 0 cases)
    strongest_periods = [
        {
            'period': f"{m['month_name']} (Calendar Month {m['month_number']})",
            'average_cases': m['average_cases'],
            'total_cases': m['total_cases']
        }
        for m in sorted_months[:3] if m['total_cases'] > 0
    ]

    # Determine status
    if seasonal_strength >= 0.45 and highest_month and highest_month['total_cases'] >= 3:
        status = 'DETECTED'
        explanation = (
            f"Historical surveillance indicates recurrent elevated case clustering in {highest_month['month_name']} "
            f"(averaging {highest_month['average_cases']} cases). Seasonal strength index: {seasonal_strength}."
        )
    else:
        status = 'WEAK'
        explanation = (
            f"Case distribution across calendar months shows low variance (seasonal strength index: {seasonal_strength}). "
            "No dominant seasonal clustering detected in historical records."
        )

    return {
        'disease': active_disease,
        'seasonal_status': status,
        'seasonal_strength': seasonal_strength,
        'total_cases_analyzed': total_seasonal_cases,
        'months_analyzed': months_count,
        'highest_case_month': highest_month,
        'lowest_case_month': lowest_month,
        'strongest_historical_periods': strongest_periods,
        'monthly_patterns': monthly_patterns,
        'explanation': explanation,
        'seasonal_age_groups': seasonal_age_groups,
        'seasonal_gender': seasonal_gender,
        'seasonal_severity': seasonal_severity,
        'seasonal_vulnerable_groups': seasonal_vulnerable_groups,
        'seasonal_patient_types': seasonal_patient_types,
        'seasonal_age_gender': seasonal_age_gender,
        'seasonal_age_gender_severity': seasonal_age_gender_severity,
        'seasonal_age_gender_vulnerability': seasonal_age_gender_vulnerability,
        'seasonal_age_gender_patient_type': seasonal_age_gender_patient_type,
    }


# ---------------------------------------------------------------------------
# 4. Master Unified Forecast Summary
# ---------------------------------------------------------------------------

def generate_forecast_summary(facility_id=None, district_id=None, disease_name=None,
                              as_of_date=None, historical_weeks=52, horizon_weeks=4,
                              months_count=None, user=None, age_group=None, gender=None,
                              severity=None, vulnerable_group=None, patient_type=None):
    """
    Unified public health intelligence forecasting & seasonal pattern entry point.
    Combines:
    - Scope authorization (reusing resolve_facility_scope)
    - Continuous weekly time series
    - Step 1 trend direction & percentage change
    - Explainable WMA forecast
    - Seasonal pattern analysis
    - Optional demographic, severity, vulnerable group, and patient-type filtering
    """
    scope = resolve_facility_scope(
        user=user,
        requested_facility_id=facility_id,
        requested_district_id=district_id
    )
    if not scope.is_authorized:
        return {
            'is_authorized': False,
            'error': scope.error
        }

    # 1. Weekly time series
    ts_data = build_disease_time_series(
        facility_ids=scope.facility_ids,
        district_id=scope.district_id,
        disease_name=disease_name,
        as_of_date=as_of_date,
        weeks_count=historical_weeks,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    series = ts_data['series']
    active_disease = ts_data['disease']

    # 2. Step 1 Trend Integration
    curr_cases = series[-1]['cases'] if series else 0
    prev_cases = series[-2]['cases'] if len(series) > 1 else 0
    trend_dir, pct_change, trend_expl = compute_trend_status(curr_cases, prev_cases)

    # 3. Forecast calculation
    has_demo_filter = bool(age_group or gender or severity or vulnerable_group or patient_type)
    forecast_data = generate_disease_forecast(
        time_series=series,
        horizon_weeks=horizon_weeks,
        has_demographic_filter=has_demo_filter
    )

    # 4. Forecast Risk calculation (derived from the exact same historical series & forecast points)
    forecast_risk_data = calculate_forecast_risk(
        historical_series=series,
        forecast_points=forecast_data.get('points', []),
        forecast_status=forecast_data.get('status')
    )

    # 5. Seasonal pattern analysis (respecting months_count if provided)
    seasonal_months = months_count if months_count else max(6, min(12, int(historical_weeks / 4.33)))
    seasonal_data = calculate_seasonal_pattern(
        facility_ids=scope.facility_ids,
        district_id=scope.district_id,
        disease_name=active_disease,
        as_of_date=as_of_date,
        months_count=seasonal_months,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    # Master explanation synthesizing trend, forecast, and seasonality
    summary_explanation = (
        f"Public health intelligence for {active_disease}: "
        f"Recent 7-day trend signal is {trend_dir} ({curr_cases} cases vs {prev_cases} prior). "
        f"Forecast status: {forecast_data['status']}. "
        f"Seasonal pattern: {seasonal_data['seasonal_status']}."
    )

    filters_dict = {}
    if active_disease:
        filters_dict['disease'] = active_disease
    if age_group:
        filters_dict['age_group'] = age_group
    if gender:
        filters_dict['gender'] = gender
    if severity:
        filters_dict['severity'] = severity
    if vulnerable_group:
        filters_dict['vulnerable_group'] = vulnerable_group
    if patient_type:
        filters_dict['patient_type'] = patient_type

    return {
        'is_authorized': True,
        'disease': active_disease,
        'filters': filters_dict,
        'scope': {
            'facility_ids': scope.facility_ids,
            'district_id': scope.district_id
        },
        'observation_period': {
            'start_date': series[0]['week_start'] if series else None,
            'end_date': series[-1]['week_end'] if series else None,
            'weeks_count': len(series),
            'total_cases': ts_data['total_cases_in_series']
        },
        'historical_series': series,
        'trend': {
            'direction': trend_dir,
            'percentage_change': pct_change,
            'current_week_cases': curr_cases,
            'previous_week_cases': prev_cases,
            'explanation': trend_expl
        },
        'forecast': forecast_data,
        'forecast_risk': forecast_risk_data,
        'seasonality': seasonal_data,
        'explanation': summary_explanation
    }

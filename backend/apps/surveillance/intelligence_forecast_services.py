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
from apps.surveillance.demographic_services import filter_cases_by_demographics
from apps.surveillance.intelligence_services import (
    resolve_date,
    compute_trend_status,
    resolve_facility_scope,
    ScopeResult
)

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


# ---------------------------------------------------------------------------
# 1. Weekly Time Series Generation
# ---------------------------------------------------------------------------

def build_disease_time_series(facility_ids=None, district_id=None, disease_name=None,
                              as_of_date=None, weeks_count=52, age_group=None, gender=None):
    """
    Builds a continuous weekly disease time series ending at as_of_date.
    
    Guarantees:
    - Every week is exactly 7 consecutive days
    - Strict continuity: week[k].end + 1 day == week[k+1].start
    - Preserves zero-case weeks without omitting any intervals
    - Uses real database DiseaseCase counts exclusively
    - Fully deterministic based on as_of_date
    - Supports optional demographic filtering (age_group, gender)
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

    # Single aggregation query across the entire date range, respecting demographic filters
    scoped_cases = qs.filter(report_date__range=[series_start, as_of])
    if age_group or gender:
        scoped_cases = filter_cases_by_demographics(scoped_cases, age_groups=age_group, genders=gender)

    cases_by_date = dict(
        scoped_cases
        .values('report_date')
        .annotate(cnt=Count('id'))
        .values_list('report_date', 'cnt')
    )

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

def generate_disease_forecast(time_series, horizon_weeks=4):
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
        return {
            'status': 'INSUFFICIENT_DATA',
            'horizon_weeks': horizon_weeks,
            'method': 'WEIGHTED_MOVING_AVERAGE',
            'points': [],
            'explanation': f'Insufficient historical surveillance cases (total {total_cases} cases recorded). Minimum baseline of 3 cases required.'
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

def calculate_seasonal_pattern(facility_ids=None, district_id=None, disease_name=None,
                               as_of_date=None, months_count=12, age_group=None, gender=None):
    """
    Analyzes historical surveillance records across calendar months to identify
    potential seasonal clustering without inferring causality.

    Returns:
    - average cases by calendar month (1 to 12)
    - highest-case month
    - lowest-case month
    - strongest historical periods
    - seasonal_strength: normalized index [0.0 - 1.0]
    - seasonal_status: 'DETECTED', 'WEAK', or 'NOT_ENOUGH_DATA'
    - supports optional demographic filtering (age_group, gender)
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
    total_seasonal_cases = scoped_cases.count()

    # Rule: Minimum volume required to detect seasonal variation
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
            )
        }

    # Group actual cases by calendar month inside [seasonal_start, as_of]
    monthly_data = (
        scoped_cases.values('report_date__month')
        .annotate(total_cases=Count('id'))
        .order_by('report_date__month')
    )
    month_counts_dict = {row['report_date__month']: row['total_cases'] for row in monthly_data}

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

    # Represent ONLY calendar months that actually occur in the requested observation window
    monthly_patterns = []
    month_averages = []

    for m in sorted(month_occurrences.keys()):
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
    highest_month = sorted_months[0] if sorted_months else None
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
        'explanation': explanation
    }


# ---------------------------------------------------------------------------
# 4. Master Unified Forecast Summary
# ---------------------------------------------------------------------------

def generate_forecast_summary(facility_id=None, district_id=None, disease_name=None,
                              as_of_date=None, historical_weeks=52, horizon_weeks=4,
                              months_count=None, user=None, age_group=None, gender=None):
    """
    Unified public health intelligence forecasting & seasonal pattern entry point.
    Combines:
    - Scope authorization (reusing resolve_facility_scope)
    - Continuous weekly time series
    - Step 1 trend direction & percentage change
    - Explainable WMA forecast
    - Seasonal pattern analysis
    - Optional demographic filtering (age_group, gender)
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
        gender=gender
    )

    series = ts_data['series']
    active_disease = ts_data['disease']

    # 2. Step 1 Trend Integration
    curr_cases = series[-1]['cases'] if series else 0
    prev_cases = series[-2]['cases'] if len(series) > 1 else 0
    trend_dir, pct_change, trend_expl = compute_trend_status(curr_cases, prev_cases)

    # 3. Forecast calculation
    forecast_data = generate_disease_forecast(
        time_series=series,
        horizon_weeks=horizon_weeks
    )

    # 4. Seasonal pattern analysis (respecting months_count if provided)
    seasonal_months = months_count if months_count else max(6, min(12, int(historical_weeks / 4.33)))
    seasonal_data = calculate_seasonal_pattern(
        facility_ids=scope.facility_ids,
        district_id=scope.district_id,
        disease_name=active_disease,
        as_of_date=as_of_date,
        months_count=seasonal_months,
        age_group=age_group,
        gender=gender
    )

    # Master explanation synthesizing trend, forecast, and seasonality
    summary_explanation = (
        f"Public health intelligence for {active_disease}: "
        f"Recent 7-day trend signal is {trend_dir} ({curr_cases} cases vs {prev_cases} prior). "
        f"Forecast status: {forecast_data['status']}. "
        f"Seasonal pattern: {seasonal_data['seasonal_status']}."
    )

    return {
        'is_authorized': True,
        'disease': active_disease,
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
        'seasonality': seasonal_data,
        'explanation': summary_explanation
    }

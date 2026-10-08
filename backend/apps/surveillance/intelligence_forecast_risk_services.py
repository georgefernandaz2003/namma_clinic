"""
Public Health Intelligence - Forecast Risk and Threshold Services
===================================================================
Provides a deterministic, explainable surveillance risk classification layer
built on top of historical surveillance time series and WMA forecast projections.

Risk Classifications:
- NORMAL: Projected cases are below the elevation threshold (ratio < 1.15).
- ELEVATED: Projected cases are at or above elevation threshold but below high risk (1.15 <= ratio < 1.50).
- HIGH_RISK: Projected cases are at or above high risk threshold (ratio >= 1.50).
- INSUFFICIENT_DATA: Historical surveillance observations are insufficient (< 3 cases)
  to establish a credible baseline.

This service produces an early surveillance/planning signal, not a clinical
or epidemiological confirmation of an outbreak.
"""

import math
from typing import Any, Dict, List, Optional, Union

FORECAST_RISK_ELEVATION_RATIO = 1.15
FORECAST_RISK_HIGH_RATIO = 1.50
FORECAST_RISK_MIN_CASES = 3

RISK_LEVEL_NORMAL = 'NORMAL'
RISK_LEVEL_ELEVATED = 'ELEVATED'
RISK_LEVEL_HIGH = 'HIGH_RISK'
RISK_LEVEL_INSUFFICIENT = 'INSUFFICIENT_DATA'

RISK_STATUS_AVAILABLE = 'AVAILABLE'
RISK_STATUS_INSUFFICIENT = 'INSUFFICIENT_DATA'


def calculate_forecast_risk(
    historical_series: Union[Dict[str, Any], List[Any]],
    forecast_points: Union[Dict[str, Any], List[Any]],
    minimum_cases: int = FORECAST_RISK_MIN_CASES,
    elevation_ratio: float = FORECAST_RISK_ELEVATION_RATIO,
    high_risk_ratio: float = FORECAST_RISK_HIGH_RATIO,
    forecast_status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates deterministic forecast risk levels by comparing forecast projections
    against the historical baseline derived strictly from the same filtered historical series.

    Deterministic Rules:
    - Baseline: Average cases per historical week across the filtered series.
    - Ratio: predicted_cases / historical_baseline.
    - Normal: ratio < elevation_ratio (1.15).
    - Elevated: elevation_ratio <= ratio < high_risk_ratio (1.15 <= ratio < 1.50).
    - High Risk: ratio >= high_risk_ratio (ratio >= 1.50).
    - Insufficient Data: Total historical cases < minimum_cases (3) or forecast status is INSUFFICIENT_DATA.
    - Zero Baseline Handling:
      * predicted_cases == 0 -> NORMAL (ratio_to_baseline = None, no increase).
      * predicted_cases > 0 -> HIGH_RISK (ratio_to_baseline = None, projection emerges above 0 baseline).
    - Precedence for highest_risk_level: HIGH_RISK > ELEVATED > NORMAL > INSUFFICIENT_DATA.
    """
    # 1. Extract historical series points
    if isinstance(historical_series, dict):
        raw_series = historical_series.get('series', [])
    elif isinstance(historical_series, (list, tuple)):
        raw_series = list(historical_series)
    else:
        raw_series = []

    # 2. Extract forecast points and status
    if isinstance(forecast_points, dict):
        if forecast_status is None:
            forecast_status = forecast_points.get('status')
        raw_points = forecast_points.get('points', [])
    elif isinstance(forecast_points, (list, tuple)):
        raw_points = list(forecast_points)
    else:
        raw_points = []

    total_cases = 0
    for item in raw_series:
        if isinstance(item, dict):
            total_cases += item.get('cases', item.get('case_count', 0))
        elif isinstance(item, (int, float)):
            total_cases += item

    weeks_count = len(raw_series)

    # 3. Handle Insufficient Data
    is_insufficient = (
        forecast_status == RISK_STATUS_INSUFFICIENT or
        total_cases < minimum_cases or
        weeks_count == 0 or
        len(raw_points) == 0
    )

    if is_insufficient:
        return {
            'status': RISK_STATUS_INSUFFICIENT,
            'historical_baseline': None,
            'elevation_ratio_threshold': elevation_ratio,
            'high_risk_ratio_threshold': high_risk_ratio,
            'risk_points': [],
            'highest_risk_level': RISK_LEVEL_INSUFFICIENT,
            'risk_points_count': 0,
            'high_risk_points_count': 0,
            'elevated_points_count': 0,
            'normal_points_count': 0,
            'explanation': 'Insufficient historical surveillance cases for reliable forecast risk classification.'
        }

    # 4. Calculate Historical Baseline
    historical_baseline = round(total_cases / weeks_count, 2)

    risk_points = []
    for p in raw_points:
        if not isinstance(p, dict):
            continue

        predicted = round(float(p.get('predicted_cases', 0.0)), 2)
        w_start = p.get('forecast_week_start')
        w_end = p.get('forecast_week_end')
        w_num = p.get('forecast_week')

        # Handle zero baseline safely
        if historical_baseline == 0.0:
            if predicted == 0.0:
                risk_level = RISK_LEVEL_NORMAL
                ratio_val = None
                ratio_to_baseline = None
                explanation = "Projected cases are 0 against a zero historical baseline and remain below the elevation threshold."
            else:
                risk_level = RISK_LEVEL_HIGH
                ratio_val = None
                ratio_to_baseline = None
                explanation = f"Projected cases ({predicted}) emerge above a zero historical baseline."
        else:
            ratio_exact = predicted / historical_baseline
            ratio_val = round(ratio_exact, 4)
            ratio_to_baseline = round(ratio_exact, 2)

            if ratio_val >= high_risk_ratio:
                risk_level = RISK_LEVEL_HIGH
                pct = int(round((ratio_val - 1.0) * 100))
                explanation = f"Projected cases are {pct}% above the historical baseline."
            elif ratio_val >= elevation_ratio:
                risk_level = RISK_LEVEL_ELEVATED
                pct = int(round((ratio_val - 1.0) * 100))
                explanation = f"Projected cases are {pct}% above the historical baseline."
            else:
                risk_level = RISK_LEVEL_NORMAL
                if ratio_val >= 1.0:
                    pct = int(round((ratio_val - 1.0) * 100))
                    explanation = f"Projected cases are {pct}% above the historical baseline and remain below the elevation threshold."
                else:
                    pct = int(round((1.0 - ratio_val) * 100))
                    if pct == 0:
                        explanation = "Projected cases match the historical baseline and remain below the elevation threshold."
                    else:
                        explanation = f"Projected cases are {pct}% below the historical baseline and remain below the elevation threshold."

        point_entry = {
            'forecast_week_start': w_start,
            'forecast_week_end': w_end,
            'predicted_cases': predicted,
            'historical_baseline': historical_baseline,
            'ratio_to_baseline': ratio_to_baseline,
            'risk_level': risk_level,
            'explanation': explanation
        }
        if w_num is not None:
            point_entry['forecast_week'] = w_num

        risk_points.append(point_entry)

    # 5. Determine Highest Risk Level Precedence
    has_high = any(pt['risk_level'] == RISK_LEVEL_HIGH for pt in risk_points)
    has_elevated = any(pt['risk_level'] == RISK_LEVEL_ELEVATED for pt in risk_points)
    has_normal = any(pt['risk_level'] == RISK_LEVEL_NORMAL for pt in risk_points)

    if has_high:
        highest_risk = RISK_LEVEL_HIGH
        summary_expl = "The selected surveillance population has a high-risk projected week."
    elif has_elevated:
        highest_risk = RISK_LEVEL_ELEVATED
        summary_expl = "The selected surveillance population has an elevated-risk projected week."
    elif has_normal:
        highest_risk = RISK_LEVEL_NORMAL
        summary_expl = "The selected surveillance population remains at normal projected risk."
    else:
        highest_risk = RISK_LEVEL_INSUFFICIENT
        summary_expl = "Insufficient historical surveillance cases for reliable forecast risk classification."

    # 6. Reconcile Counts
    high_count = sum(1 for pt in risk_points if pt['risk_level'] == RISK_LEVEL_HIGH)
    elevated_count = sum(1 for pt in risk_points if pt['risk_level'] == RISK_LEVEL_ELEVATED)
    normal_count = sum(1 for pt in risk_points if pt['risk_level'] == RISK_LEVEL_NORMAL)

    return {
        'status': RISK_STATUS_AVAILABLE,
        'historical_baseline': historical_baseline,
        'elevation_ratio_threshold': elevation_ratio,
        'high_risk_ratio_threshold': high_risk_ratio,
        'risk_points': risk_points,
        'highest_risk_level': highest_risk,
        'risk_points_count': len(risk_points),
        'high_risk_points_count': high_count,
        'elevated_points_count': elevated_count,
        'normal_points_count': normal_count,
        'explanation': summary_expl
    }

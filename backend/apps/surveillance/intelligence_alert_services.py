"""
Public Health Intelligence Alert Services - STEP 4
Evaluates authoritative Step 1 and Step 2 surveillance outputs to produce
actionable, human-reviewable surveillance alerts.

Strict constraints:
- Deterministic deduplication via fingerprinting.
- Traceable to real database surveillance data.
- Never declare confirmed outbreaks or automated diagnoses.
- Safe severity levels: INFO, WARNING, CRITICAL.
- Audit logging for all creation and lifecycle actions.
"""

import hashlib
import datetime
from django.utils import timezone
from django.db.models import Count, Q

from apps.alerts.models import Alert
from apps.audit.models import AuditLog
from apps.facilities.models import Facility
from apps.geography.models import District, Ward
from apps.surveillance.models import DiseaseCase
from apps.surveillance.intelligence_services import (
    resolve_date,
    get_period_dates,
    calculate_disease_trends,
    aggregate_disease_by_locality,
    resolve_facility_scope,
    ScopeResult
)
from apps.surveillance.intelligence_forecast_services import (
    build_disease_time_series,
    generate_disease_forecast,
    calculate_seasonal_pattern
)

# ---------------------------------------------------------------------------
# Centralized Configurable Thresholds
# ---------------------------------------------------------------------------
INTELLIGENCE_LOCALITY_SHARE_THRESHOLD = 25.0
INTELLIGENCE_MIN_LOCALITY_CASES = 3
INTELLIGENCE_FORECAST_ELEVATION_RATIO = 1.15
INTELLIGENCE_MIN_FORECAST_CASES = 3.0


# ---------------------------------------------------------------------------
# Fingerprint Helper for Deduplication
# ---------------------------------------------------------------------------
def generate_alert_fingerprint(alert_type, disease, facility_id=None, district_id=None,
                               locality_id=None, observation_date=None, signal_period=None):
    """
    Produces a deterministic SHA-256 fingerprint for deduplication across
    repeated dashboard refreshes or background evaluations.
    """
    scope_token = f"FAC_{facility_id}" if facility_id else f"DIST_{district_id}"
    d_clean = str(disease or '').strip().upper()
    loc_token = str(locality_id or '')
    date_token = str(observation_date or '')
    period_token = str(signal_period or '')

    raw = f"{alert_type}|{d_clean}|{scope_token}|{loc_token}|{date_token}|{period_token}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


# ---------------------------------------------------------------------------
# Alert Evaluation Service
# ---------------------------------------------------------------------------
def evaluate_facility_intelligence_signals(facility, as_of_date=None, actor_user=None):
    """
    Evaluates all 4 surveillance signals for a single facility against real surveillance data:
    1. Disease Trend Increase (INCREASING or POSSIBLE_INCREASE)
    2. High Locality Concentration (locality_share >= 25.0%)
    3. Forecast Surveillance Signal (predicted increase vs historical baseline)
    4. Seasonal Surveillance Signal (seasonality DETECTED and peak overlap)
    """
    as_of = resolve_date(as_of_date)
    observation_date_str = str(as_of)
    evaluated_alerts = []
    created_count = 0
    updated_count = 0

    fac_id = facility.id
    district = facility.district

    # -----------------------------------------------------------------------
    # Signal A: Disease Trend Increase
    # -----------------------------------------------------------------------
    trend_result = calculate_disease_trends(
        facility_ids=[fac_id],
        as_of_date=as_of,
        window_days=7
    )
    for trend in trend_result.get('disease_trends', []):
        status_dir = trend.get('trend_direction')
        disease_name = trend.get('disease')
        current_cases = trend.get('current_cases', 0)
        previous_cases = trend.get('previous_period_cases', 0)
        pct_change = trend.get('percentage_change', 0.0)

        if status_dir in ['INCREASING', 'POSSIBLE_INCREASE'] and current_cases > 0:
            fp = generate_alert_fingerprint(
                alert_type='INTELLIGENCE_TREND',
                disease=disease_name,
                facility_id=fac_id,
                observation_date=observation_date_str,
                signal_period=trend.get('observation_period', {}).get('start_date')
            )

            pct_display = f" ({pct_change:+.1f}%)" if pct_change is not None else " (new emergence)"
            title = f"Disease Trend Signal: {disease_name}"
            description = (
                f"Surveillance trend indicates {status_dir.replace('_', ' ').lower()} for {disease_name}. "
                f"Current: {current_cases}, Previous: {previous_cases}{pct_display}."
            )
            metadata = {
                'signal_type': 'DISEASE_TREND',
                'disease': disease_name,
                'facility_id': fac_id,
                'facility_name': facility.facility_name,
                'district_id': district.id if district else None,
                'district_name': district.name if district else None,
                'observation_date': observation_date_str,
                'current_cases': current_cases,
                'previous_cases': previous_cases,
                'percentage_change': pct_change,
                'trend_direction': status_dir,
                'explanation': trend.get('explanation', description)
            }

            alert, created = _get_or_create_dedup_alert(
                alert_type='INTELLIGENCE_TREND',
                severity='WARNING',
                facility=facility,
                district=district,
                title=title,
                description=description,
                fingerprint=fp,
                metadata=metadata,
                actor_user=actor_user
            )
            evaluated_alerts.append(alert)
            if created:
                created_count += 1
            else:
                updated_count += 1

    # -----------------------------------------------------------------------
    # Signal B: High Locality Concentration
    # -----------------------------------------------------------------------
    locality_result = aggregate_disease_by_locality(
        facility_ids=[fac_id],
        as_of_date=as_of,
        window_days=7
    )
    for loc in locality_result.get('locality_aggregations', []):
        locality_share = loc.get('locality_share_pct', 0.0)
        current_cases = loc.get('current_cases', 0)
        loc_info = loc.get('locality', {})
        locality_name = loc_info.get('name') if isinstance(loc_info, dict) else 'Unknown Locality'
        loc_id = loc_info.get('ward_id') if isinstance(loc_info, dict) else None
        disease_name = loc.get('disease') or 'All Monitored Conditions'

        if locality_share >= INTELLIGENCE_LOCALITY_SHARE_THRESHOLD and current_cases >= INTELLIGENCE_MIN_LOCALITY_CASES:
            fp = generate_alert_fingerprint(
                alert_type='INTELLIGENCE_LOCALITY',
                disease=disease_name,
                facility_id=fac_id,
                locality_id=loc_id,
                observation_date=observation_date_str,
                signal_period=loc.get('observation_period', {}).get('start_date')
            )

            title = f"Locality Concentration Signal: {disease_name} in {locality_name}"
            description = (
                f"{locality_name} accounts for {locality_share:.1f}% of observed {disease_name} cases "
                f"({current_cases} cases) at {facility.facility_name}."
            )
            metadata = {
                'signal_type': 'HIGH_LOCALITY_CONCENTRATION',
                'disease': disease_name,
                'facility_id': fac_id,
                'facility_name': facility.facility_name,
                'district_id': district.id if district else None,
                'district_name': district.name if district else None,
                'locality': locality_name,
                'locality_id': loc_id,
                'current_cases': current_cases,
                'locality_share': locality_share,
                'reporting_hospitals': loc.get('reporting_hospitals', [facility.facility_name]),
                'observation_period': loc.get('observation_period', {}),
                'threshold_used': INTELLIGENCE_LOCALITY_SHARE_THRESHOLD,
                'explanation': description
            }

            alert, created = _get_or_create_dedup_alert(
                alert_type='INTELLIGENCE_LOCALITY',
                severity='WARNING',
                facility=facility,
                district=district,
                title=title,
                description=description,
                fingerprint=fp,
                metadata=metadata,
                actor_user=actor_user
            )
            evaluated_alerts.append(alert)
            if created:
                created_count += 1
            else:
                updated_count += 1

    # -----------------------------------------------------------------------
    # Signal C & D: Forecast & Seasonal Signals per Monitored Disease
    # -----------------------------------------------------------------------
    # Identify distinct monitored diseases at this facility with surveillance activity
    distinct_diseases = list(
        DiseaseCase.objects.filter(
            facility_id=fac_id,
            report_date__lte=as_of
        ).values_list('disease_name', flat=True).distinct()
    )

    for disease_name in distinct_diseases:
        if not disease_name:
            continue

        # Signal C: Forecast Surveillance Signal
        ts = build_disease_time_series(
            facility_ids=[fac_id],
            disease_name=disease_name,
            as_of_date=as_of,
            weeks_count=6
        )
        forecast = generate_disease_forecast(
            time_series=ts,
            horizon_weeks=2
        )
        if forecast.get('status') == 'AVAILABLE':
            points = forecast.get('points', [])
            if points:
                predictions = [p['predicted_cases'] for p in points]
                avg_pred = sum(predictions) / len(predictions)

                series = ts.get('series', [])
                case_values = [w['cases'] for w in series]
                if len(case_values) >= 4:
                    baseline = sum(case_values[: len(case_values) // 2]) / float(len(case_values) // 2)
                else:
                    baseline = sum(case_values) / float(len(case_values)) if case_values else 0.0

                is_elevated = (
                    avg_pred >= INTELLIGENCE_MIN_FORECAST_CASES and (
                        (baseline > 0 and avg_pred >= baseline * INTELLIGENCE_FORECAST_ELEVATION_RATIO)
                        or (baseline == 0 and avg_pred >= INTELLIGENCE_MIN_FORECAST_CASES)
                    )
                )

                if is_elevated:
                    fp = generate_alert_fingerprint(
                        alert_type='INTELLIGENCE_FORECAST',
                        disease=disease_name,
                        facility_id=fac_id,
                        observation_date=observation_date_str,
                        signal_period=f"{forecast.get('horizon_weeks', 2)}w"
                    )

                    title = f"Forecast Surveillance Signal: {disease_name}"
                    description = "Forecast indicates elevated future case volume."
                    metadata = {
                        'signal_type': 'FORECAST_SURVEILLANCE_SIGNAL',
                        'disease': disease_name,
                        'facility_id': fac_id,
                        'facility_name': facility.facility_name,
                        'district_id': district.id if district else None,
                        'district_name': district.name if district else None,
                        'observation_date': observation_date_str,
                        'forecast_horizon': f"{forecast.get('horizon_weeks', 2)} weeks",
                        'predicted_cases': round(avg_pred, 1),
                        'lower_bound': points[0].get('lower_bound', 0.0),
                        'upper_bound': points[-1].get('upper_bound', 0.0),
                        'historical_baseline': round(baseline, 1),
                        'forecast_method': forecast.get('method', 'WEIGHTED_MOVING_AVERAGE'),
                        'explanation': description
                    }

                    alert, created = _get_or_create_dedup_alert(
                        alert_type='INTELLIGENCE_FORECAST',
                        severity='WARNING',
                        facility=facility,
                        district=district,
                        title=title,
                        description=description,
                        fingerprint=fp,
                        metadata=metadata,
                        actor_user=actor_user
                    )
                    evaluated_alerts.append(alert)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

        # Signal D: Seasonal Surveillance Signal
        seasonality = calculate_seasonal_pattern(
            facility_ids=[fac_id],
            disease_name=disease_name,
            as_of_date=as_of,
            months_count=12
        )
        if seasonality.get('seasonal_status') == 'DETECTED':
            highest_month = seasonality.get('highest_case_month')
            strongest_periods = seasonality.get('strongest_historical_periods', [])
            current_month_num = as_of.month

            is_seasonal_peak = (
                (highest_month and highest_month.get('month_number') == current_month_num)
                or any(p.get('month_number') == current_month_num for p in strongest_periods)
            )

            if is_seasonal_peak:
                fp = generate_alert_fingerprint(
                    alert_type='INTELLIGENCE_SEASONALITY',
                    disease=disease_name,
                    facility_id=fac_id,
                    observation_date=observation_date_str,
                    signal_period=f"M_{current_month_num}"
                )

                month_name = highest_month.get('month_name', 'current season') if highest_month else 'current season'
                title = f"Seasonal Surveillance Signal: {disease_name}"
                description = (
                    f"Surveillance history shows higher seasonal incidence for {disease_name} "
                    f"around this period (peak historically observed in {month_name})."
                )
                metadata = {
                    'signal_type': 'SEASONAL_SURVEILLANCE_SIGNAL',
                    'disease': disease_name,
                    'facility_id': fac_id,
                    'facility_name': facility.facility_name,
                    'district_id': district.id if district else None,
                    'district_name': district.name if district else None,
                    'observation_date': observation_date_str,
                    'current_month': current_month_num,
                    'highest_case_month': month_name,
                    'seasonal_strength': seasonality.get('seasonal_strength', 0.0),
                    'seasonal_status': 'DETECTED',
                    'explanation': description
                }

                alert, created = _get_or_create_dedup_alert(
                    alert_type='INTELLIGENCE_SEASONALITY',
                    severity='INFO',
                    facility=facility,
                    district=district,
                    title=title,
                    description=description,
                    fingerprint=fp,
                    metadata=metadata,
                    actor_user=actor_user
                )
                evaluated_alerts.append(alert)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

    return {
        'facility_id': fac_id,
        'facility_name': facility.facility_name,
        'alerts': evaluated_alerts,
        'created_count': created_count,
        'updated_count': updated_count
    }


def evaluate_intelligence_alerts(facility_ids=None, district_id=None, as_of_date=None, actor_user=None):
    """
    Evaluates surveillance intelligence signals across specified facility/district scopes.
    Deduplicates active alerts and logs an audit trail.
    """
    as_of = resolve_date(as_of_date)
    fac_qs = Facility.objects.all()

    if facility_ids is not None:
        fac_qs = fac_qs.filter(id__in=facility_ids)
    elif district_id is not None:
        fac_qs = fac_qs.filter(district_id=district_id)

    facilities = list(fac_qs.select_related('district'))
    if not facilities:
        return {
            'as_of_date': str(as_of),
            'facilities_evaluated': 0,
            'total_alerts': 0,
            'created_count': 0,
            'updated_count': 0,
            'alerts': []
        }

    all_alerts = []
    total_created = 0
    total_updated = 0

    for fac in facilities:
        res = evaluate_facility_intelligence_signals(fac, as_of_date=as_of, actor_user=actor_user)
        all_alerts.extend(res['alerts'])
        total_created += res['created_count']
        total_updated += res['updated_count']

    # Record audit log for surveillance evaluation
    if actor_user and actor_user.is_authenticated:
        AuditLog.objects.create(
            user=actor_user,
            username_snapshot=actor_user.username,
            action='INTELLIGENCE_SIGNALS_EVALUATED',
            facility=facilities[0] if facilities else None,
            details=(
                f"Evaluated surveillance signals for {len(facilities)} facility/facilities as of {as_of}. "
                f"Created: {total_created}, Updated/Deduplicated: {total_updated}."
            ),
            timestamp=timezone.now()
        )

    return {
        'as_of_date': str(as_of),
        'facilities_evaluated': len(facilities),
        'total_alerts': len(all_alerts),
        'created_count': total_created,
        'updated_count': total_updated,
        'alerts': all_alerts
    }


def _get_or_create_dedup_alert(alert_type, severity, facility, district, title,
                               description, fingerprint, metadata, actor_user=None):
    """
    Mandatory Deduplication:
    If an unresolved (NEW or ACKNOWLEDGED) alert with the same fingerprint exists,
    updates its metadata and explanation without creating a duplicate record.
    Otherwise creates a new Alert and logs an audit record.
    """
    existing = Alert.objects.filter(
        fingerprint=fingerprint,
        status__in=['NEW', 'ACKNOWLEDGED']
    ).first()

    if existing:
        existing.metadata = metadata
        existing.description = description
        existing.severity = severity
        existing.save(update_fields=['metadata', 'description', 'severity'])
        return existing, False

    new_alert = Alert.objects.create(
        alert_type=alert_type,
        severity=severity,
        facility=facility,
        district=district,
        title=title,
        description=description,
        status='NEW',
        fingerprint=fingerprint,
        metadata=metadata
    )

    AuditLog.objects.create(
        user=actor_user if (actor_user and actor_user.is_authenticated) else None,
        username_snapshot=actor_user.username if (actor_user and actor_user.is_authenticated) else 'SYSTEM',
        action='ALERT_CREATED',
        facility=facility,
        details=f"Created surveillance alert {alert_type} for {facility.facility_name}: {title}",
        timestamp=timezone.now()
    )

    return new_alert, True


# ---------------------------------------------------------------------------
# Lifecycle State Transition Helpers
# ---------------------------------------------------------------------------
def acknowledge_alert(alert_instance, actor_user):
    """
    Transitions alert from NEW -> ACKNOWLEDGED.
    Disallows acknowledging an already RESOLVED alert.
    Audits the acknowledgement.
    """
    if alert_instance.status == 'RESOLVED':
        raise ValueError("Cannot acknowledge an alert that has already been resolved.")

    alert_instance.status = 'ACKNOWLEDGED'
    alert_instance.acknowledged_at = timezone.now()
    if actor_user and actor_user.is_authenticated:
        alert_instance.acknowledged_by = actor_user
    alert_instance.save(update_fields=['status', 'acknowledged_at', 'acknowledged_by'])

    AuditLog.objects.create(
        user=actor_user if (actor_user and actor_user.is_authenticated) else None,
        username_snapshot=actor_user.username if (actor_user and actor_user.is_authenticated) else 'SYSTEM',
        action='ALERT_ACKNOWLEDGED',
        facility=alert_instance.facility,
        details=f"Alert #{alert_instance.id} ({alert_instance.title}) acknowledged.",
        timestamp=timezone.now()
    )
    return alert_instance


def resolve_alert(alert_instance, actor_user, resolution_notes=''):
    """
    Transitions alert to RESOLVED with notes and timestamp.
    Audits the resolution.
    """
    alert_instance.status = 'RESOLVED'
    alert_instance.resolved_at = timezone.now()
    alert_instance.resolution_notes = resolution_notes or ''
    if actor_user and actor_user.is_authenticated:
        alert_instance.resolved_by = actor_user
    alert_instance.save(update_fields=['status', 'resolved_at', 'resolved_by', 'resolution_notes'])

    AuditLog.objects.create(
        user=actor_user if (actor_user and actor_user.is_authenticated) else None,
        username_snapshot=actor_user.username if (actor_user and actor_user.is_authenticated) else 'SYSTEM',
        action='ALERT_RESOLVED',
        facility=alert_instance.facility,
        details=f"Alert #{alert_instance.id} ({alert_instance.title}) resolved. Notes: {resolution_notes}",
        timestamp=timezone.now()
    )
    return alert_instance

"""
Public Health Intelligence Backend Module - STEP 1 Foundation
Authoritative, reusable epidemiological service implementing database-driven
disease trend analysis, locality aggregation, historical aggregation,
hospital-level aggregation, and district-level aggregation.

All calculations derive strictly from real database records across:
- apps.surveillance.models.DiseaseCase
- apps.consultations.models.Consultation
- apps.facilities.models.Facility
- apps.geography.models.Ward, District

Terminology Standards:
- NORMAL
- INCREASING
- DECREASING
- POSSIBLE_INCREASE
- INSUFFICIENT_DATA

Guarantees:
- Zero division safety on zero baseline
- Missing locality handled gracefully ("Unknown Locality")
- Missing diagnosis handled gracefully ("Unspecified Diagnosis")
- Strict hospital isolation for Hospital Admins
- Strict district scoping for District Officers
- Cross-district isolation enforced
- No false outbreak claims asserted
"""

import datetime
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.surveillance.models import DiseaseCase
from apps.consultations.models import Consultation
from apps.facilities.models import Facility
from apps.geography.models import Ward, District
from apps.surveillance.demographic_services import (
    AGE_GROUPS,
    AGE_GROUP_0_5,
    AGE_GROUP_6_14,
    AGE_GROUP_15_24,
    AGE_GROUP_25_44,
    AGE_GROUP_45_59,
    AGE_GROUP_60_PLUS,
    AGE_GROUP_UNKNOWN,
    GENDER_CHOICES,
    GENDER_MALE,
    GENDER_FEMALE,
    GENDER_OTHER,
    GENDER_UNKNOWN,
    calculate_age,
    get_age_group,
    normalize_gender,
    resolve_patient_demographics,
    aggregate_demographics,
    get_demographic_intelligence,
    filter_cases_by_demographics,
    validate_demographic_params,
    SEVERITY_CHOICES,
    SEVERITY_MILD,
    SEVERITY_MODERATE,
    SEVERITY_SEVERE,
    SEVERITY_UNKNOWN,
    normalize_severity,
    validate_severity_param,
    build_severity_demographic_matrices,
)
from apps.surveillance.vulnerable_population_services import (
    VULNERABLE_GROUPS,
    VULNERABLE_GROUP_UNKNOWN,
    ALL_VULNERABLE_GROUPS,
    normalize_vulnerable_group,
    filter_cases_by_vulnerable_group,
    build_vulnerable_population_matrices,
)
from apps.surveillance.patient_type_services import (
    PATIENT_TYPE_NEW,
    PATIENT_TYPE_FOLLOW_UP,
    PATIENT_TYPE_UNKNOWN,
    VALID_PATIENT_TYPES,
    ALL_PATIENT_TYPES,
    normalize_patient_type,
    validate_patient_type_param,
    annotate_case_patient_type,
    get_case_patient_type,
    filter_cases_by_patient_type,
    build_patient_type_matrices,
)


# ---------------------------------------------------------------------------
# Helper: Date Range & Target Resolution
# ---------------------------------------------------------------------------

def resolve_date(target_date=None):
    """Parses date string or date object, defaulting to today."""
    if target_date is None:
        return datetime.date.today()
    if isinstance(target_date, str):
        try:
            return datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return datetime.date.today()
    if isinstance(target_date, datetime.datetime):
        return target_date.date()
    return target_date


def get_period_dates(start_date=None, end_date=None, as_of_date=None, window_days=7):
    """
    Computes current and preceding comparison periods.
    If start_date and end_date are given, uses that window.
    Otherwise uses window_days ending on as_of_date.
    """
    as_of = resolve_date(as_of_date)
    if start_date and end_date:
        c_start = resolve_date(start_date)
        c_end = resolve_date(end_date)
        duration = (c_end - c_start).days + 1
        p_end = c_start - datetime.timedelta(days=1)
        p_start = p_end - datetime.timedelta(days=duration - 1)
    else:
        c_end = as_of
        c_start = c_end - datetime.timedelta(days=window_days - 1)
        duration = window_days
        p_end = c_start - datetime.timedelta(days=1)
        p_start = p_end - datetime.timedelta(days=window_days - 1)

    return {
        'current_start': c_start,
        'current_end': c_end,
        'previous_start': p_start,
        'previous_end': p_end,
        'duration_days': duration
    }


def compute_trend_status(current_count, previous_count):
    """
    Authoritative status determination complying with Step 1 rules:
    - NORMAL
    - INCREASING
    - DECREASING
    - POSSIBLE_INCREASE
    - INSUFFICIENT_DATA
    """
    c = int(current_count or 0)
    p = int(previous_count or 0)

    # 1. Zero data across both periods
    if c == 0 and p == 0:
        return 'INSUFFICIENT_DATA', None, "No cases reported in either observation period."

    # 2. Zero baseline with new cases
    if p == 0 and c > 0:
        if c >= 3:
            return 'INCREASING', None, f"Zero cases in previous period; {c} cases recorded in current period."
        return 'POSSIBLE_INCREASE', None, f"Early signal: {c} cases observed compared to zero previous cases."

    # 3. Standard percentage change when previous > 0
    pct_change = round(((c - p) / p) * 100.0, 2)

    if pct_change >= 15.0:
        if (c - p) >= 2 or pct_change >= 25.0:
            status = 'INCREASING'
        else:
            status = 'POSSIBLE_INCREASE'
        explanation = f"Current cases ({c}) increased by {pct_change:+.1f}% over previous period ({p})."
    elif pct_change > 0.0:
        status = 'POSSIBLE_INCREASE'
        explanation = f"Current cases ({c}) showed slight upward momentum (+{pct_change:.1f}%) over previous period ({p})."
    elif pct_change <= -15.0:
        status = 'DECREASING'
        explanation = f"Current cases ({c}) decreased by {abs(pct_change):.1f}% compared to previous period ({p})."
    else:
        status = 'NORMAL'
        explanation = f"Case count ({c}) is within normal variation relative to previous period ({p}, {pct_change:+.1f}%)."

    return status, pct_change, explanation


# ---------------------------------------------------------------------------
# Scope Resolution Helper
# ---------------------------------------------------------------------------

class ScopeResult:
    """
    Structured outcome of facility and district scope resolution.
    Encapsulates explicit authorization status, resolved facility IDs,
    resolved district ID, and permission denial explanation.
    """
    def __init__(self, is_authorized, facility_ids=None, district_id=None, error=None):
        self.is_authorized = bool(is_authorized)
        self.facility_ids = list(facility_ids) if facility_ids else []
        self.district_id = district_id
        self.error = error

    def __bool__(self):
        return self.is_authorized

    def __iter__(self):
        # Enables tuple unpacking: fac_ids, scoped_dist_id = resolve_facility_scope(...)
        return iter((self.facility_ids, self.district_id))

    def __repr__(self):
        return f"<ScopeResult authorized={self.is_authorized} fac_ids={self.facility_ids} dist_id={self.district_id} error={self.error}>"


def resolve_facility_scope(user=None, requested_facility_id=None, requested_district_id=None):
    """
    Authoritative facility and district scope resolution with explicit authorization:

    1. DISTRICT_OFFICER + requested facility inside assigned district:
       -> return only that requested facility.
    2. DISTRICT_OFFICER + requested facility outside assigned district:
       -> explicitly reject the request (is_authorized=False).
    3. DISTRICT_OFFICER + requested district equal to assigned district:
       -> return all facilities in that district.
    4. DISTRICT_OFFICER + requested district different from assigned district:
       -> explicitly reject the request (is_authorized=False).
    5. HOSPITAL_ADMIN + requested facility equal to assigned facility:
       -> allow.
    6. HOSPITAL_ADMIN + requested facility different from assigned facility:
       -> explicitly reject the request (is_authorized=False).
    7. HOSPITAL_ADMIN requesting another district:
       -> explicitly reject the request (is_authorized=False).
    """
    req_fac_id = None
    if requested_facility_id is not None and str(requested_facility_id).strip() != '':
        if hasattr(requested_facility_id, 'id'):
            req_fac_id = requested_facility_id.id
        else:
            try:
                req_fac_id = int(requested_facility_id)
            except (ValueError, TypeError):
                return ScopeResult(False, [], None, "Invalid facility identifier.")

    req_dist_id = None
    if requested_district_id is not None and str(requested_district_id).strip() != '':
        if hasattr(requested_district_id, 'id'):
            req_dist_id = requested_district_id.id
        else:
            try:
                req_dist_id = int(requested_district_id)
            except (ValueError, TypeError):
                return ScopeResult(False, [], None, "Invalid district identifier.")

    # Standalone or unauthenticated function invocation (e.g. internal service/test helper with user=None)
    if not user or not user.is_authenticated:
        if req_fac_id:
            fac = Facility.objects.filter(id=req_fac_id).first()
            if not fac:
                return ScopeResult(False, [], None, "Facility not found.")
            return ScopeResult(True, [fac.id], fac.district_id, None)
        if req_dist_id:
            dist = District.objects.filter(id=req_dist_id).first()
            if not dist:
                return ScopeResult(False, [], None, "District not found.")
            fac_ids = list(Facility.objects.filter(district=dist).values_list('id', flat=True))
            return ScopeResult(True, fac_ids, dist.id, None)
        all_fac_ids = list(Facility.objects.values_list('id', flat=True))
        return ScopeResult(True, all_fac_ids, None, None)

    # Superuser has unrestricted access across facilities and districts
    if getattr(user, 'is_superuser', False):
        if req_fac_id:
            fac = Facility.objects.filter(id=req_fac_id).first()
            if not fac:
                return ScopeResult(False, [], None, "Facility not found.")
            return ScopeResult(True, [fac.id], fac.district_id, None)
        if req_dist_id:
            dist = District.objects.filter(id=req_dist_id).first()
            if not dist:
                return ScopeResult(False, [], None, "District not found.")
            fac_ids = list(Facility.objects.filter(district=dist).values_list('id', flat=True))
            return ScopeResult(True, fac_ids, dist.id, None)
        all_fac_ids = list(Facility.objects.values_list('id', flat=True))
        return ScopeResult(True, all_fac_ids, None, None)

    role = getattr(user, 'role', '')

    # District Officer Scoping Rules
    if role == 'DISTRICT_OFFICER':
        user_dist = getattr(user, 'assigned_district', None)
        user_dist_id = getattr(user, 'assigned_district_id', None)
        if not user_dist_id and user_dist:
            user_dist_id = user_dist.id
        if not user_dist_id:
            return ScopeResult(False, [], None, "Permission denied: District Officer has no assigned district.")

        district_fac_qs = Facility.objects.filter(district_id=user_dist_id)
        district_fac_ids = list(district_fac_qs.values_list('id', flat=True))

        # Check requested district
        if req_dist_id is not None and req_dist_id != user_dist_id:
            return ScopeResult(False, [], user_dist_id, "Permission denied: Requested district is outside assigned district jurisdiction.")

        # Check requested facility
        if req_fac_id is not None:
            if not district_fac_qs.filter(id=req_fac_id).exists():
                return ScopeResult(False, [], user_dist_id, "Permission denied: Requested facility is outside assigned district.")
            return ScopeResult(True, [req_fac_id], user_dist_id, None)

        # Default to all facilities in assigned district
        return ScopeResult(True, district_fac_ids, user_dist_id, None)

    # Operational Roles: HOSPITAL_ADMIN, DOCTOR, NURSE
    if role in ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE']:
        assigned_fac = getattr(user, 'assigned_facility', None)
        assigned_fac_id = getattr(user, 'assigned_facility_id', None)
        if assigned_fac:
            assigned_fac_id = assigned_fac.id
            fac_dist_id = assigned_fac.district_id
        elif assigned_fac_id:
            fac = Facility.objects.filter(id=assigned_fac_id).first()
            fac_dist_id = fac.district_id if fac else None
        else:
            return ScopeResult(False, [], None, "Permission denied: User has no assigned hospital facility.")

        # Check requested facility
        if req_fac_id is not None and req_fac_id != assigned_fac_id:
            return ScopeResult(False, [], None, "Permission denied: Cannot access facility outside assigned hospital.")

        # Check requested district
        if req_dist_id is not None and req_dist_id != fac_dist_id:
            return ScopeResult(False, [], None, "Permission denied: Hospital Admin cannot query outside assigned hospital district.")

        # Strictly locked to assigned facility
        return ScopeResult(True, [assigned_fac_id], fac_dist_id, None)

    return ScopeResult(False, [], None, "Permission denied: User role is not authorized for health intelligence.")


# ---------------------------------------------------------------------------
# 1. Disease Trend Analysis
# ---------------------------------------------------------------------------

def calculate_disease_trends(facility_ids=None, district_id=None, disease_name=None,
                             start_date=None, end_date=None, as_of_date=None, window_days=7,
                             age_group=None, gender=None, severity=None, vulnerable_group=None,
                             patient_type=None):
    """
    Computes disease metrics:
    - current cases (within observation window)
    - previous-period cases (equal preceding window)
    - 7-day cases
    - 30-day cases
    - 90-day cases
    - historical monthly counts (past 6 months)
    - percentage change
    - trend direction (NORMAL, INCREASING, DECREASING, POSSIBLE_INCREASE, INSUFFICIENT_DATA)
    - demographic breakdowns
    - optional severity filtering
    - optional vulnerable_group filtering
    - optional patient_type filtering
    """
    periods = get_period_dates(start_date=start_date, end_date=end_date, as_of_date=as_of_date, window_days=window_days)
    c_start = periods['current_start']
    c_end = periods['current_end']
    p_start = periods['previous_start']
    p_end = periods['previous_end']
    as_of = periods['current_end']

    qs = DiseaseCase.objects.all()
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name:
        qs = qs.filter(disease_name__iexact=disease_name)

    if severity:
        qs = qs.filter(severity__iexact=severity)

    if age_group or gender:
        qs = filter_cases_by_demographics(qs, age_groups=age_group, genders=gender)

    if vulnerable_group:
        qs = filter_cases_by_vulnerable_group(qs, vulnerable_group=vulnerable_group)

    if patient_type:
        qs = filter_cases_by_patient_type(qs, patient_type=patient_type)

    # Fixed time intervals relative to as_of date
    d7_start = as_of - datetime.timedelta(days=6)
    d30_start = as_of - datetime.timedelta(days=29)
    d90_start = as_of - datetime.timedelta(days=89)

    # Group by unique disease name (handling missing/blank as 'Unspecified Diagnosis')
    distinct_diseases = list(qs.values_list('disease_name', flat=True).distinct())
    if not distinct_diseases and disease_name:
        distinct_diseases = [disease_name]

    results = []
    total_curr = 0
    total_prev = 0

    for d in distinct_diseases:
        raw_name = d or ''
        clean_name = raw_name.strip() if raw_name.strip() else 'Unspecified Diagnosis'

        d_qs = qs.filter(disease_name=raw_name) if raw_name else qs.filter(Q(disease_name__isnull=True) | Q(disease_name=''))

        curr_cnt = d_qs.filter(report_date__range=[c_start, c_end]).count()
        prev_cnt = d_qs.filter(report_date__range=[p_start, p_end]).count()
        cnt_7d = d_qs.filter(report_date__range=[d7_start, as_of]).count()
        cnt_30d = d_qs.filter(report_date__range=[d30_start, as_of]).count()
        cnt_90d = d_qs.filter(report_date__range=[d90_start, as_of]).count()

        # Monthly historical aggregation (past 6 calendar months)
        monthly_series = []
        for m_offset in range(5, -1, -1):
            # Calculate month year
            y = as_of.year
            m = as_of.month - m_offset
            while m <= 0:
                m += 12
                y -= 1
            month_count = d_qs.filter(report_date__year=y, report_date__month=m).count()
            monthly_series.append({
                'month': f"{y}-{m:02d}",
                'year': y,
                'month_number': m,
                'cases': month_count
            })

        status_str, pct_change, explanation = compute_trend_status(curr_cnt, prev_cnt)

        total_curr += curr_cnt
        total_prev += prev_cnt

        curr_window_cases = d_qs.filter(report_date__range=[c_start, c_end])
        d_demographics = aggregate_demographics(curr_window_cases, reference_date=as_of)

        results.append({
            'disease': clean_name,
            'current_cases': curr_cnt,
            'previous_period_cases': prev_cnt,
            'cases_7d': cnt_7d,
            'cases_30d': cnt_30d,
            'cases_90d': cnt_90d,
            'historical_monthly_counts': monthly_series,
            'percentage_change': pct_change,
            'trend_direction': status_str,
            'explanation': explanation,
            'demographics': d_demographics,
            'observation_period': {
                'start_date': str(c_start),
                'end_date': str(c_end),
                'duration_days': periods['duration_days'],
                'previous_start': str(p_start),
                'previous_end': str(p_end)
            }
        })

    # Sort diseases by current cases descending
    results.sort(key=lambda x: x['current_cases'], reverse=True)
    overall_status, overall_pct, overall_expl = compute_trend_status(total_curr, total_prev)

    overall_demographics = aggregate_demographics(qs.filter(report_date__range=[c_start, c_end]), reference_date=as_of)

    return {
        'summary': {
            'total_current_cases': total_curr,
            'total_previous_cases': total_prev,
            'overall_percentage_change': overall_pct,
            'overall_trend_direction': overall_status,
            'diseases_monitored_count': len(results),
            'demographics': overall_demographics,
            'observation_period': {
                'start_date': str(c_start),
                'end_date': str(c_end),
                'duration_days': periods['duration_days']
            }
        },
        'disease_trends': results
    }


# ---------------------------------------------------------------------------
# 2. Disease-by-Locality Aggregation
# ---------------------------------------------------------------------------

def aggregate_disease_by_locality(facility_ids=None, district_id=None, disease_name=None,
                                  start_date=None, end_date=None, as_of_date=None, window_days=14,
                                  age_group=None, gender=None, severity=None, vulnerable_group=None,
                                  patient_type=None):
    """
    Computes disease distribution by locality/ward:
    - disease cases by locality/ward
    - hospitals reporting the disease
    - locality share of disease cases
    - current vs previous period
    - trend direction
    Handles missing locality cleanly as 'Unknown Locality'.
    Handles multiple hospitals reporting in the same ward.
    Supports optional severity, vulnerable_group, and patient_type filtering.
    """
    periods = get_period_dates(start_date=start_date, end_date=end_date, as_of_date=as_of_date, window_days=window_days)
    c_start = periods['current_start']
    c_end = periods['current_end']
    p_start = periods['previous_start']
    p_end = periods['previous_end']

    qs = DiseaseCase.objects.all()
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name:
        qs = qs.filter(disease_name__iexact=disease_name)

    if severity:
        qs = qs.filter(severity__iexact=severity)

    if age_group or gender:
        qs = filter_cases_by_demographics(qs, age_groups=age_group, genders=gender)

    if vulnerable_group:
        qs = filter_cases_by_vulnerable_group(qs, vulnerable_group=vulnerable_group)

    if patient_type:
        qs = filter_cases_by_patient_type(qs, patient_type=patient_type)

    total_cases_in_scope = qs.filter(report_date__range=[c_start, c_end]).count()

    # Identify all wards represented in data plus wards in district
    ward_ids = list(qs.values_list('ward_id', flat=True).distinct())

    # Build locality buckets
    localities = []

    # 1. Process known wards
    known_ward_ids = [w_id for w_id in ward_ids if w_id is not None]
    wards_map = {w.id: w for w in Ward.objects.filter(id__in=known_ward_ids).select_related('zone__district')}

    for w_id in known_ward_ids:
        ward_obj = wards_map.get(w_id)
        if not ward_obj:
            continue

        w_qs = qs.filter(ward_id=w_id)
        curr_cnt = w_qs.filter(report_date__range=[c_start, c_end]).count()
        prev_cnt = w_qs.filter(report_date__range=[p_start, p_end]).count()

        # Reporting hospitals for this ward
        rep_facs = list(
            w_qs.filter(report_date__range=[c_start, c_end])
            .values('facility__id', 'facility__facility_name', 'facility__facility_code')
            .annotate(case_count=Count('id'))
        )
        reporting_hospitals = [
            {
                'hospital_id': f['facility__id'],
                'hospital_name': f['facility__facility_name'],
                'hospital_code': f['facility__facility_code'],
                'cases_reported': f['case_count']
            }
            for f in rep_facs
        ]

        # Locality share of total cases in scope
        share_pct = round((curr_cnt / total_cases_in_scope) * 100.0, 2) if total_cases_in_scope > 0 else 0.0

        status_str, pct_change, explanation = compute_trend_status(curr_cnt, prev_cnt)

        localities.append({
            'locality': {
                'ward_id': ward_obj.id,
                'ward_number': ward_obj.ward_number,
                'name': ward_obj.name,
                'zone': ward_obj.zone.name if ward_obj.zone else None,
                'population': ward_obj.population,
                'slum_population': ward_obj.slum_population
            },
            'disease': disease_name or "All Monitored Conditions",
            'current_cases': curr_cnt,
            'previous_period_cases': prev_cnt,
            'percentage_change': pct_change,
            'locality_share_pct': share_pct,
            'trend_direction': status_str,
            'reporting_hospitals_count': len(reporting_hospitals),
            'reporting_hospitals': reporting_hospitals,
            'explanation': explanation,
            'observation_period': {
                'start_date': str(c_start),
                'end_date': str(c_end),
                'duration_days': periods['duration_days']
            }
        })

    # 2. Process records with missing locality (ward is None)
    unknown_qs = qs.filter(ward__isnull=True)
    unk_curr = unknown_qs.filter(report_date__range=[c_start, c_end]).count()
    unk_prev = unknown_qs.filter(report_date__range=[p_start, p_end]).count()

    if unk_curr > 0 or unk_prev > 0 or None in ward_ids:
        unk_rep_facs = list(
            unknown_qs.filter(report_date__range=[c_start, c_end])
            .values('facility__id', 'facility__facility_name', 'facility__facility_code')
            .annotate(case_count=Count('id'))
        )
        unk_reporting_hospitals = [
            {
                'hospital_id': f['facility__id'],
                'hospital_name': f['facility__facility_name'],
                'hospital_code': f['facility__facility_code'],
                'cases_reported': f['case_count']
            }
            for f in unk_rep_facs
        ]
        unk_share = round((unk_curr / total_cases_in_scope) * 100.0, 2) if total_cases_in_scope > 0 else 0.0
        unk_status, unk_pct, unk_expl = compute_trend_status(unk_curr, unk_prev)

        localities.append({
            'locality': {
                'ward_id': None,
                'ward_number': None,
                'name': "Unknown Locality",
                'zone': None,
                'population': None,
                'slum_population': None
            },
            'disease': disease_name or "All Monitored Conditions",
            'current_cases': unk_curr,
            'previous_period_cases': unk_prev,
            'percentage_change': unk_pct,
            'locality_share_pct': unk_share,
            'trend_direction': unk_status,
            'reporting_hospitals_count': len(unk_reporting_hospitals),
            'reporting_hospitals': unk_reporting_hospitals,
            'explanation': unk_expl,
            'observation_period': {
                'start_date': str(c_start),
                'end_date': str(c_end),
                'duration_days': periods['duration_days']
            }
        })

    # Sort localities by current cases descending
    localities.sort(key=lambda x: x['current_cases'], reverse=True)

    return {
        'total_cases_in_period': total_cases_in_scope,
        'localities_count': len(localities),
        'locality_aggregations': localities
    }


# ---------------------------------------------------------------------------
# 3. Historical Disease Aggregation
# ---------------------------------------------------------------------------

def aggregate_historical_disease(facility_ids=None, district_id=None, disease_name=None,
                                 months=6, as_of_date=None, age_group=None, gender=None,
                                 severity=None, vulnerable_group=None, patient_type=None):
    """
    Computes multi-month historical disease aggregation series:
    - monthly counts
    - breakdown by severity (MILD, MODERATE, SEVERE, UNKNOWN)
    - trend direction across sequential periods
    - historical age-group distribution (all supported age groups represented)
    - historical gender distribution (all supported genders represented)
    - historical severity distribution (all supported severities represented)
    - monthly severity trends
    - 2D age + gender cross-tabulation matrix
    - monthly demographic trends across each historical month
    - cross-analyses: severity_age_groups, severity_gender, severity_age_gender
    - historical vulnerable-population distribution (all supported groups represented)
    - monthly vulnerable-population trends
    - cross-analyses: vulnerable_age_groups, vulnerable_gender, vulnerable_age_gender,
      vulnerable_severity, vulnerable_age_gender_severity
    - historical patient-type distribution (NEW, FOLLOW_UP, UNKNOWN)
    - monthly patient-type trends
    - cross-analyses: patient_type_age_groups, patient_type_gender, patient_type_age_gender,
      patient_type_severity, patient_type_vulnerable_groups, patient_type_age_gender_vulnerability
    - optional vulnerable_group filtering
    - optional patient_type filtering
    """
    from apps.surveillance.demographic_services import (
        AGE_GROUPS,
        AGE_GROUP_0_5,
        AGE_GROUP_6_14,
        AGE_GROUP_15_24,
        AGE_GROUP_25_44,
        AGE_GROUP_45_59,
        AGE_GROUP_60_PLUS,
        AGE_GROUP_UNKNOWN,
        GENDER_CHOICES,
        GENDER_MALE,
        GENDER_FEMALE,
        GENDER_OTHER,
        GENDER_UNKNOWN,
        SEVERITY_CHOICES,
        SEVERITY_MILD,
        SEVERITY_MODERATE,
        SEVERITY_SEVERE,
        SEVERITY_UNKNOWN,
        normalize_severity,
        resolve_patient_demographics,
        build_age_gender_matrix,
        build_severity_demographic_matrices,
        filter_cases_by_demographics,
    )
    from apps.surveillance.vulnerable_population_services import (
        VULNERABLE_GROUPS,
        VULNERABLE_GROUP_UNKNOWN,
        ALL_VULNERABLE_GROUPS,
        normalize_vulnerable_group,
        filter_cases_by_vulnerable_group,
        build_vulnerable_population_matrices,
    )
    from apps.surveillance.patient_type_services import (
        PATIENT_TYPE_NEW,
        PATIENT_TYPE_FOLLOW_UP,
        PATIENT_TYPE_UNKNOWN,
        VALID_PATIENT_TYPES,
        ALL_PATIENT_TYPES,
        normalize_patient_type,
        filter_cases_by_patient_type,
        get_case_patient_type,
        annotate_case_patient_type,
        build_patient_type_matrices,
    )

    as_of = resolve_date(as_of_date)

    qs = DiseaseCase.objects.all()
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name:
        qs = qs.filter(disease_name__iexact=disease_name)
        active_disease = disease_name
    else:
        top_d = qs.values('disease_name').annotate(cnt=Count('id')).order_by('-cnt').first()
        active_disease = top_d['disease_name'] if top_d and top_d['disease_name'] else 'All Monitored Diseases'
        if top_d and top_d['disease_name']:
            qs = qs.filter(disease_name=active_disease)

    if severity:
        qs = qs.filter(severity__iexact=severity)

    if age_group or gender:
        qs = filter_cases_by_demographics(qs, age_groups=age_group, genders=gender)

    if vulnerable_group:
        qs = filter_cases_by_vulnerable_group(qs, vulnerable_group=vulnerable_group)

    if patient_type:
        qs = filter_cases_by_patient_type(qs, patient_type=patient_type)

    # Generate chronological sequence of months from oldest to newest
    months_list = []
    for m_offset in range(months - 1, -1, -1):
        y = as_of.year
        m = as_of.month - m_offset
        while m <= 0:
            m += 12
            y -= 1
        period_label = f"{y}-{m:02d}"
        months_list.append((y, m, period_label))

    oldest_y, oldest_m, _ = months_list[0]
    newest_y, newest_m, _ = months_list[-1]
    start_date = datetime.date(oldest_y, oldest_m, 1)

    # Determine end date of the historical period
    if newest_m == 12:
        end_date = datetime.date(newest_y + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(newest_y, newest_m + 1, 1) - datetime.timedelta(days=1)

    # Single efficient query with select_related('patient') and annotated patient_type
    historical_cases_qs = annotate_case_patient_type(qs.filter(
        report_date__gte=start_date,
        report_date__lte=end_date
    )).select_related('patient')

    historical_cases = list(historical_cases_qs)

    # Initialize data structures for each month
    all_severities = SEVERITY_CHOICES + [SEVERITY_UNKNOWN]
    month_data = {}
    for (y, m, pl) in months_list:
        month_data[(y, m)] = {
            'period_label': pl,
            'year': y,
            'month': m,
            'total_cases': 0,
            'severity': {s: 0 for s in all_severities},
            'age_groups': {ag: 0 for ag in AGE_GROUPS},
            'gender': {g: 0 for g in GENDER_CHOICES},
            'vulnerable_groups': {vg: 0 for vg in ALL_VULNERABLE_GROUPS},
            'patient_type': {pt: 0 for pt in ALL_PATIENT_TYPES},
            'unknown_age': 0,
            'unknown_gender': 0,
        }

    # Tracking across entire historical window
    total_severity_counts = {s: 0 for s in all_severities}
    total_age_group_counts = {ag: 0 for ag in AGE_GROUPS}
    total_unknown_age_count = 0
    total_gender_counts = {g: 0 for g in GENDER_CHOICES}
    total_unknown_gender_count = 0
    total_vulnerable_counts = {vg: 0 for vg in ALL_VULNERABLE_GROUPS}
    total_patient_type_counts = {pt: 0 for pt in ALL_PATIENT_TYPES}

    # Process all cases in a single in-memory pass
    for case in historical_cases:
        r_date = case.report_date
        y = r_date.year
        m = r_date.month
        key = (y, m)
        if key not in month_data:
            continue

        # Safe severity normalization without silently converting missing into MILD
        sev = normalize_severity(case.severity)
        month_data[key]['severity'][sev] += 1
        total_severity_counts[sev] += 1
        month_data[key]['total_cases'] += 1

        # Authoritative demographics calculated using DiseaseCase.report_date
        demo = resolve_patient_demographics(
            case.patient,
            reference_date=r_date,
            allow_stored_age_fallback=False
        )
        case_ag = demo['age_group']
        case_g = demo['gender']

        # Age group tracking
        if case_ag in total_age_group_counts:
            total_age_group_counts[case_ag] += 1
            month_data[key]['age_groups'][case_ag] += 1
        else:
            total_unknown_age_count += 1
            month_data[key]['unknown_age'] += 1

        # Gender tracking
        if case_g in total_gender_counts:
            total_gender_counts[case_g] += 1
            month_data[key]['gender'][case_g] += 1
        else:
            total_unknown_gender_count += 1
            month_data[key]['unknown_gender'] += 1

        # Vulnerable group tracking
        patient = getattr(case, 'patient', None)
        v_info = getattr(patient, 'vulnerability_information', None) if patient else None
        case_vg = normalize_vulnerable_group(v_info)
        month_data[key]['vulnerable_groups'][case_vg] += 1
        total_vulnerable_counts[case_vg] += 1

        # Patient type tracking (point-in-time relative to case report_date)
        case_pt = get_case_patient_type(case)
        month_data[key]['patient_type'][case_pt] += 1
        total_patient_type_counts[case_pt] += 1

    # Build historical_series (preserves existing format and backward compatibility)
    historical_series = []
    case_counts = []
    monthly_demographic_trends = []
    monthly_severity_trends = []
    monthly_vulnerable_population_trends = []
    monthly_patient_type_trends = []

    has_unknown_vg = total_vulnerable_counts[VULNERABLE_GROUP_UNKNOWN] > 0
    active_trend_vgs = list(VULNERABLE_GROUPS)
    if has_unknown_vg:
        active_trend_vgs.append(VULNERABLE_GROUP_UNKNOWN)

    has_unknown_pt = total_patient_type_counts[PATIENT_TYPE_UNKNOWN] > 0
    active_trend_pts = list(VALID_PATIENT_TYPES)
    if has_unknown_pt:
        active_trend_pts.append(PATIENT_TYPE_UNKNOWN)

    for (y, m, pl) in months_list:
        md = month_data[(y, m)]
        tot = md['total_cases']
        case_counts.append(tot)

        historical_series.append({
            'period_label': pl,
            'year': y,
            'month': m,
            'total_cases': tot,
            'severity_breakdown': {
                'MILD': md['severity'].get('MILD', 0),
                'MODERATE': md['severity'].get('MODERATE', 0),
                'SEVERE': md['severity'].get('SEVERE', 0),
                'UNKNOWN': md['severity'].get('UNKNOWN', 0),
            }
        })

        # Monthly demographic trend object
        ag_dict = dict(md['age_groups'])
        if total_unknown_age_count > 0:
            ag_dict[AGE_GROUP_UNKNOWN] = md['unknown_age']

        g_dict = dict(md['gender'])
        if total_unknown_gender_count > 0:
            g_dict[GENDER_UNKNOWN] = md['unknown_gender']

        monthly_demographic_trends.append({
            'month': pl,
            'total_cases': tot,
            'age_groups': ag_dict,
            'gender': g_dict
        })

        # Monthly severity trend object (sum of severities equals total_cases)
        monthly_severity_trends.append({
            'month': pl,
            'total_cases': tot,
            'severity': {
                'MILD': md['severity'].get('MILD', 0),
                'MODERATE': md['severity'].get('MODERATE', 0),
                'SEVERE': md['severity'].get('SEVERE', 0),
                'UNKNOWN': md['severity'].get('UNKNOWN', 0),
            }
        })

        # Monthly vulnerable-population trend object (sum of groups equals total_cases)
        monthly_vulnerable_population_trends.append({
            'month': pl,
            'total_cases': tot,
            'vulnerable_groups': {
                vg: md['vulnerable_groups'].get(vg, 0)
                for vg in active_trend_vgs
            }
        })

        # Monthly patient-type trend object (sum of patient types strictly equals total_cases)
        pt_trend_entry = {
            'month': pl,
            'total_cases': tot,
            'NEW': md['patient_type'].get('NEW', 0),
            'FOLLOW_UP': md['patient_type'].get('FOLLOW_UP', 0),
            'patient_type': {
                pt: md['patient_type'].get(pt, 0)
                for pt in active_trend_pts
            }
        }
        if has_unknown_pt:
            pt_trend_entry['UNKNOWN'] = md['patient_type'].get('UNKNOWN', 0)
        monthly_patient_type_trends.append(pt_trend_entry)

    # Build historical_age_groups (all supported age groups represented, plus UNKNOWN if present)
    historical_age_groups = []
    for ag in AGE_GROUPS:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['age_groups'].get(ag, 0), 'cases': month_data[(y, m)]['age_groups'].get(ag, 0)}
            for (y, m, pl) in months_list
        ]
        historical_age_groups.append({
            'age_group': ag,
            'total_cases': total_age_group_counts[ag],
            'monthly_counts': m_counts
        })

    if total_unknown_age_count > 0:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['unknown_age'], 'cases': month_data[(y, m)]['unknown_age']}
            for (y, m, pl) in months_list
        ]
        historical_age_groups.append({
            'age_group': AGE_GROUP_UNKNOWN,
            'total_cases': total_unknown_age_count,
            'monthly_counts': m_counts
        })

    # Build historical_gender (all supported genders represented, plus UNKNOWN if present)
    historical_gender = []
    for g in GENDER_CHOICES:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['gender'].get(g, 0), 'cases': month_data[(y, m)]['gender'].get(g, 0)}
            for (y, m, pl) in months_list
        ]
        historical_gender.append({
            'gender': g,
            'total_cases': total_gender_counts[g],
            'monthly_counts': m_counts
        })

    if total_unknown_gender_count > 0:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['unknown_gender'], 'cases': month_data[(y, m)]['unknown_gender']}
            for (y, m, pl) in months_list
        ]
        historical_gender.append({
            'gender': GENDER_UNKNOWN,
            'total_cases': total_unknown_gender_count,
            'monthly_counts': m_counts
        })

    # Build historical_severity (all supported severities represented, plus UNKNOWN if present)
    historical_severity = []
    for s in SEVERITY_CHOICES:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['severity'].get(s, 0), 'cases': month_data[(y, m)]['severity'].get(s, 0)}
            for (y, m, pl) in months_list
        ]
        historical_severity.append({
            'severity': s,
            'total_cases': total_severity_counts[s],
            'monthly_counts': m_counts
        })

    if total_severity_counts[SEVERITY_UNKNOWN] > 0:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['severity'].get(SEVERITY_UNKNOWN, 0), 'cases': month_data[(y, m)]['severity'].get(SEVERITY_UNKNOWN, 0)}
            for (y, m, pl) in months_list
        ]
        historical_severity.append({
            'severity': SEVERITY_UNKNOWN,
            'total_cases': total_severity_counts[SEVERITY_UNKNOWN],
            'monthly_counts': m_counts
        })

    # Build historical_vulnerable_groups (all supported groups represented, plus UNKNOWN if present)
    historical_vulnerable_groups = []
    for vg in VULNERABLE_GROUPS:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['vulnerable_groups'].get(vg, 0), 'cases': month_data[(y, m)]['vulnerable_groups'].get(vg, 0)}
            for (y, m, pl) in months_list
        ]
        historical_vulnerable_groups.append({
            'vulnerable_group': vg,
            'total_cases': total_vulnerable_counts[vg],
            'monthly_counts': m_counts
        })

    if total_vulnerable_counts[VULNERABLE_GROUP_UNKNOWN] > 0:
        m_counts = [
            {'month': pl, 'count': month_data[(y, m)]['vulnerable_groups'].get(VULNERABLE_GROUP_UNKNOWN, 0), 'cases': month_data[(y, m)]['vulnerable_groups'].get(VULNERABLE_GROUP_UNKNOWN, 0)}
            for (y, m, pl) in months_list
        ]
        historical_vulnerable_groups.append({
            'vulnerable_group': VULNERABLE_GROUP_UNKNOWN,
            'total_cases': total_vulnerable_counts[VULNERABLE_GROUP_UNKNOWN],
            'monthly_counts': m_counts
        })

    # Build historical_patient_type (authoritative dict, only include UNKNOWN if present)
    historical_patient_type = {
        PATIENT_TYPE_NEW: total_patient_type_counts[PATIENT_TYPE_NEW],
        PATIENT_TYPE_FOLLOW_UP: total_patient_type_counts[PATIENT_TYPE_FOLLOW_UP],
    }
    if total_patient_type_counts[PATIENT_TYPE_UNKNOWN] > 0:
        historical_patient_type[PATIENT_TYPE_UNKNOWN] = total_patient_type_counts[PATIENT_TYPE_UNKNOWN]

    # Build age_gender_matrix using existing utility
    age_gender_matrix = build_age_gender_matrix(
        historical_cases,
        reference_date=as_of,
        allow_stored_age_fallback=False
    )

    # Build cross-severity matrices
    severity_age_groups, severity_gender, severity_age_gender = build_severity_demographic_matrices(
        historical_cases,
        reference_date=as_of,
        allow_stored_age_fallback=False
    )

    # Build cross-vulnerable population matrices
    (
        vulnerable_age_groups,
        vulnerable_gender,
        vulnerable_age_gender,
        vulnerable_severity,
        vulnerable_age_gender_severity,
    ) = build_vulnerable_population_matrices(
        historical_cases,
        reference_date=as_of,
        allow_stored_age_fallback=False
    )

    # Build cross-patient type matrices
    (
        patient_type_age_groups,
        patient_type_gender,
        patient_type_age_gender,
        patient_type_severity,
        patient_type_vulnerable_groups,
        patient_type_age_gender_vulnerability,
    ) = build_patient_type_matrices(
        historical_cases,
        reference_date=as_of,
        allow_stored_age_fallback=False
    )

    current_val = case_counts[-1] if case_counts else 0
    previous_val = case_counts[-2] if len(case_counts) > 1 else 0
    status_str, pct_change, explanation = compute_trend_status(current_val, previous_val)
    mean_cases = round(sum(case_counts) / len(case_counts), 2) if case_counts else 0.0

    return {
        'disease': active_disease,
        'months_analyzed': months,
        'total_cases_in_history': sum(case_counts),
        'monthly_average': mean_cases,
        'mean_monthly_cases': mean_cases,
        'current_month_cases': current_val,
        'previous_month_cases': previous_val,
        'percentage_change': pct_change,
        'trend_direction': status_str,
        'explanation': explanation,
        'historical_series': historical_series,
        'monthly_series': historical_series,
        'severity_breakdown': {
            'MILD': total_severity_counts['MILD'],
            'MODERATE': total_severity_counts['MODERATE'],
            'SEVERE': total_severity_counts['SEVERE'],
            'UNKNOWN': total_severity_counts['UNKNOWN']
        },
        'patient_type_breakdown': {
            'NEW': total_patient_type_counts['NEW'],
            'FOLLOW_UP': total_patient_type_counts['FOLLOW_UP'],
            'UNKNOWN': total_patient_type_counts['UNKNOWN']
        },
        'observation_period': {
            'start_date': str(start_date),
            'end_date': str(as_of),
            'months_count': months
        },
        'historical_age_groups': historical_age_groups,
        'historical_gender': historical_gender,
        'age_gender_matrix': age_gender_matrix,
        'monthly_demographic_trends': monthly_demographic_trends,
        'historical_severity': historical_severity,
        'monthly_severity_trends': monthly_severity_trends,
        'severity_age_groups': severity_age_groups,
        'severity_gender': severity_gender,
        'severity_age_gender': severity_age_gender,
        'historical_vulnerable_groups': historical_vulnerable_groups,
        'monthly_vulnerable_population_trends': monthly_vulnerable_population_trends,
        'vulnerable_age_groups': vulnerable_age_groups,
        'vulnerable_gender': vulnerable_gender,
        'vulnerable_age_gender': vulnerable_age_gender,
        'vulnerable_severity': vulnerable_severity,
        'vulnerable_age_gender_severity': vulnerable_age_gender_severity,
        'historical_patient_type': historical_patient_type,
        'monthly_patient_type_trends': monthly_patient_type_trends,
        'patient_type_age_groups': patient_type_age_groups,
        'patient_type_gender': patient_type_gender,
        'patient_type_age_gender': patient_type_age_gender,
        'patient_type_severity': patient_type_severity,
        'patient_type_vulnerable_groups': patient_type_vulnerable_groups,
        'patient_type_age_gender_vulnerability': patient_type_age_gender_vulnerability,
    }



# ---------------------------------------------------------------------------
# 4. Hospital-Level Aggregation
# ---------------------------------------------------------------------------

def aggregate_hospital_level(facility_id, user=None, start_date=None, end_date=None, as_of_date=None,
                             age_group=None, gender=None, severity=None, vulnerable_group=None,
                             patient_type=None):
    """
    Hospital Admin scope:
    - Only their assigned hospital
    - Only clinical/surveillance data recorded at that hospital
    Returns:
    - hospital information
    - total disease cases
    - disease breakdown
    - locality distribution served by this hospital
    - 7d, 30d, 90d metrics
    - trend direction
    """
    # Verify authorization
    scope = resolve_facility_scope(user=user, requested_facility_id=facility_id)
    if not scope.is_authorized or facility_id not in scope.facility_ids:
        # Cross-hospital unauthorized access prevented
        return {
            'error': scope.error or 'Permission denied: Cannot access clinical data outside assigned hospital.',
            'facility_id': facility_id
        }

    fac = Facility.objects.filter(id=facility_id).first()
    if not fac:
        return {'error': 'Facility not found', 'facility_id': facility_id}

    trends = calculate_disease_trends(
        facility_ids=[fac.id],
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    localities = aggregate_disease_by_locality(
        facility_ids=[fac.id],
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    as_of = resolve_date(as_of_date)
    hosp_cases = DiseaseCase.objects.filter(facility=fac)
    if severity:
        hosp_cases = hosp_cases.filter(severity__iexact=severity)
    if age_group or gender:
        hosp_cases = filter_cases_by_demographics(hosp_cases, age_groups=age_group, genders=gender)
    if vulnerable_group:
        hosp_cases = filter_cases_by_vulnerable_group(hosp_cases, vulnerable_group=vulnerable_group)
    if patient_type:
        hosp_cases = filter_cases_by_patient_type(hosp_cases, patient_type=patient_type)

    d7_cases = hosp_cases.filter(report_date__range=[as_of - datetime.timedelta(days=6), as_of]).count()
    d30_cases = hosp_cases.filter(report_date__range=[as_of - datetime.timedelta(days=29), as_of]).count()
    d90_cases = hosp_cases.filter(report_date__range=[as_of - datetime.timedelta(days=89), as_of]).count()

    return {
        'hospital': {
            'id': fac.id,
            'name': fac.facility_name,
            'code': fac.facility_code,
            'type': fac.get_facility_type_display(),
            'bed_capacity': fac.bed_capacity,
            'ward': fac.ward.name if fac.ward else None,
            'district': fac.district.name if fac.district else None
        },
        'summary': trends['summary'],
        'cases_7d': d7_cases,
        'cases_30d': d30_cases,
        'cases_90d': d90_cases,
        'diseases': trends['disease_trends'],
        'localities_served': localities['locality_aggregations']
    }


# ---------------------------------------------------------------------------
# 5. District-Level Aggregation
# ---------------------------------------------------------------------------

def aggregate_district_level(district_id, user=None, start_date=None, end_date=None, as_of_date=None,
                             age_group=None, gender=None, severity=None, vulnerable_group=None,
                             patient_type=None):
    """
    District Officer scope:
    - All hospitals/facilities inside assigned district
    - Strict cross-district isolation
    Returns:
    - district summary
    - total hospitals reporting
    - district-wide disease breakdown
    - locality breakdown
    - hospital comparison across the district
    """
    # Authorize user
    scope = resolve_facility_scope(user=user, requested_district_id=district_id)
    if not scope.is_authorized:
        return {
            'error': scope.error or 'Permission denied: Cross-district access is prohibited.',
            'district_id': district_id
        }
    if user and user.is_authenticated and user.role != 'DISTRICT_OFFICER' and not getattr(user, 'is_superuser', False):
        return {
            'error': 'Permission denied: District-level aggregation is restricted to District Officers.',
            'district_id': district_id
        }

    dist = District.objects.filter(id=district_id).first()
    if not dist:
        return {'error': 'District not found', 'district_id': district_id}

    # Strict isolation: only facilities in this district
    district_facs = Facility.objects.filter(district=dist)
    district_fac_ids = list(district_facs.values_list('id', flat=True))

    trends = calculate_disease_trends(
        facility_ids=district_fac_ids,
        district_id=dist.id,
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    localities = aggregate_disease_by_locality(
        facility_ids=district_fac_ids,
        district_id=dist.id,
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    # Hospital comparison within the district
    periods = get_period_dates(start_date=start_date, end_date=end_date, as_of_date=as_of_date)
    c_start = periods['current_start']
    c_end = periods['current_end']

    dist_cases = DiseaseCase.objects.filter(facility__in=district_facs, report_date__range=[c_start, c_end])
    if severity:
        dist_cases = dist_cases.filter(severity__iexact=severity)
    if age_group or gender:
        dist_cases = filter_cases_by_demographics(dist_cases, age_groups=age_group, genders=gender)
    if vulnerable_group:
        dist_cases = filter_cases_by_vulnerable_group(dist_cases, vulnerable_group=vulnerable_group)
    if patient_type:
        dist_cases = filter_cases_by_patient_type(dist_cases, patient_type=patient_type)

    hospital_comparison = []
    for f in district_facs:
        f_cases = dist_cases.filter(facility=f).count()
        hospital_comparison.append({
            'hospital_id': f.id,
            'hospital_name': f.facility_name,
            'hospital_code': f.facility_code,
            'facility_type': f.get_facility_type_display(),
            'cases_reported': f_cases
        })

    hospital_comparison.sort(key=lambda x: x['cases_reported'], reverse=True)

    return {
        'district': {
            'id': dist.id,
            'name': dist.name,
            'code': dist.code,
            'state': dist.state.name if dist.state else None,
            'total_facilities': district_facs.count()
        },
        'summary': trends['summary'],
        'diseases': trends['disease_trends'],
        'localities': localities['locality_aggregations'],
        'hospital_comparison': hospital_comparison
    }


# ---------------------------------------------------------------------------
# Master Step 1 Summary
# ---------------------------------------------------------------------------

def get_public_health_intelligence_summary(facility_id=None, district_id=None, user=None,
                                            start_date=None, end_date=None, as_of_date=None,
                                            age_group=None, gender=None, severity=None,
                                            vulnerable_group=None, patient_type=None):
    """
    Unified entry point for Step 1 Public Health Intelligence.
    Resolves scope automatically from user role or passed identifiers.
    """
    scope = resolve_facility_scope(
        user=user,
        requested_facility_id=facility_id,
        requested_district_id=district_id
    )
    if not scope.is_authorized:
        return {'error': scope.error}

    fac_ids = scope.facility_ids
    scoped_dist_id = scope.district_id

    # If single hospital scope
    if fac_ids and len(fac_ids) == 1 and (facility_id or (user and user.role in ['HOSPITAL_ADMIN', 'DOCTOR'])):
        return aggregate_hospital_level(
            facility_id=fac_ids[0],
            user=user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=age_group,
            gender=gender,
            severity=severity,
            vulnerable_group=vulnerable_group,
            patient_type=patient_type
        )

    # District scope
    effective_dist_id = scoped_dist_id or district_id
    if effective_dist_id:
        return aggregate_district_level(
            district_id=effective_dist_id,
            user=user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=age_group,
            gender=gender,
            severity=severity,
            vulnerable_group=vulnerable_group,
            patient_type=patient_type
        )

    # District-wide fallback across all accessible facilities
    trends = calculate_disease_trends(
        facility_ids=fac_ids,
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )
    localities = aggregate_disease_by_locality(
        facility_ids=fac_ids,
        start_date=start_date,
        end_date=end_date,
        as_of_date=as_of_date,
        age_group=age_group,
        gender=gender,
        severity=severity,
        vulnerable_group=vulnerable_group,
        patient_type=patient_type
    )

    return {
        'module_title': 'Public Health Intelligence & Forecasting - Foundation',
        'summary': trends['summary'],
        'diseases': trends['disease_trends'],
        'localities': localities['locality_aggregations']
    }


"""
Authoritative Patient Type Intelligence Services for Public Health Surveillance.
Derives, validates, filters, and matrices patient-type classifications:
- NEW: First recorded clinical case in the available system history for this patient.
- FOLLOW_UP: Patient has a previous recorded clinical case before the current case's report_date.
- UNKNOWN: Insufficient historical or demographic tracking information to classify safely.

Temporal Point-in-Time Guarantees:
- Relative to each case's own report_date.
- Strictly non-circular (current case does not count as its own previous visit).
- Future cases do not alter the classification of earlier historical records.
- Operates deterministically on real database records without fabricating data.
- Avoids N+1 query loops via Subquery Exists annotations and select_related('patient').
"""

import datetime
from django.db.models import Exists, OuterRef, Q

from apps.surveillance.models import DiseaseCase
from apps.surveillance.demographic_services import (
    AGE_GROUPS,
    resolve_patient_demographics,
    normalize_severity,
    SEVERITY_MILD,
    SEVERITY_MODERATE,
    SEVERITY_SEVERE,
    SEVERITY_UNKNOWN,
)
from apps.surveillance.vulnerable_population_services import (
    VULNERABLE_GROUPS,
    normalize_vulnerable_group,
    VULNERABLE_GROUP_UNKNOWN,
)

PATIENT_TYPE_NEW = 'NEW'
PATIENT_TYPE_FOLLOW_UP = 'FOLLOW_UP'
PATIENT_TYPE_UNKNOWN = 'UNKNOWN'

VALID_PATIENT_TYPES = [PATIENT_TYPE_NEW, PATIENT_TYPE_FOLLOW_UP]
ALL_PATIENT_TYPES = [PATIENT_TYPE_NEW, PATIENT_TYPE_FOLLOW_UP, PATIENT_TYPE_UNKNOWN]


def normalize_patient_type(val):
    """
    Normalizes arbitrary patient type strings to canonical codes:
    'NEW', 'FOLLOW_UP', or 'UNKNOWN'.
    """
    if val is None:
        return PATIENT_TYPE_UNKNOWN

    clean = str(val).strip().upper()
    if not clean:
        return PATIENT_TYPE_UNKNOWN

    if clean in ('NEW', 'FIRST_TIME', 'FIRST_VISIT'):
        return PATIENT_TYPE_NEW
    if clean in ('FOLLOW_UP', 'FOLLOWUP', 'REPEAT', 'REVISIT', 'SUBSEQUENT'):
        return PATIENT_TYPE_FOLLOW_UP

    return PATIENT_TYPE_UNKNOWN


def validate_patient_type_param(val=None, patient_type=None):
    """
    Validates patient_type query parameter for API endpoints.
    Returns (clean_value, error_message).
    - If val is None or empty: returns (None, None).
    - 'NEW' or 'FOLLOW_UP': returns (clean_value, None).
    - 'UNKNOWN': rejected with HTTP 400 (internal output category only).
    - Invalid values: rejected with HTTP 400.
    """
    if val is None and patient_type is not None:
        val = patient_type

    if val is None:
        return None, None

    clean = str(val).strip().upper()
    if not clean:
        return None, None

    if clean == PATIENT_TYPE_UNKNOWN:
        return None, "Patient type filter does not accept UNKNOWN."

    if clean in (PATIENT_TYPE_NEW,):
        return PATIENT_TYPE_NEW, None

    if clean in (PATIENT_TYPE_FOLLOW_UP, 'FOLLOWUP'):
        return PATIENT_TYPE_FOLLOW_UP, None

    return None, f"Invalid patient_type parameter '{clean}'. Must be one of: {', '.join(VALID_PATIENT_TYPES)}."


def annotate_case_patient_type(qs):
    """
    Annotates a DiseaseCase queryset with `has_prior_case` in a single SQL query
    using an Exists subquery evaluated relative to each case's report_date and id.
    Strictly avoids circular counting and avoids N+1 queries.
    """
    earlier_subquery = DiseaseCase.objects.filter(
        patient_id=OuterRef('patient_id')
    ).filter(
        Q(report_date__lt=OuterRef('report_date')) |
        Q(report_date=OuterRef('report_date'), id__lt=OuterRef('id'))
    )
    return qs.annotate(has_prior_case=Exists(earlier_subquery))


def get_case_patient_type(case):
    """
    Determines the patient-type classification for a single DiseaseCase:
    - NEW: patient's first recorded clinical case up to this report_date.
    - FOLLOW_UP: patient had an earlier clinical case prior to this report_date.
    - UNKNOWN: missing patient reference or report_date.
    Uses pre-annotated `has_prior_case` if available, otherwise queries safely.
    """
    if case is None:
        return PATIENT_TYPE_UNKNOWN

    patient_id = getattr(case, 'patient_id', None)
    report_date = getattr(case, 'report_date', None)

    if not patient_id or not report_date:
        return PATIENT_TYPE_UNKNOWN

    if hasattr(case, 'has_prior_case'):
        return PATIENT_TYPE_FOLLOW_UP if case.has_prior_case else PATIENT_TYPE_NEW

    # Fallback for unannotated individual instances
    earlier_exists = DiseaseCase.objects.filter(
        patient_id=patient_id
    ).filter(
        Q(report_date__lt=report_date) |
        Q(report_date=report_date, id__lt=getattr(case, 'id', 0) or 0)
    ).exists()

    return PATIENT_TYPE_FOLLOW_UP if earlier_exists else PATIENT_TYPE_NEW


def filter_cases_by_patient_type(qs, patient_type=None):
    """
    Filters DiseaseCase queryset by patient type (NEW or FOLLOW_UP).
    Uses single-query Exists subquery annotation.
    Preserves all existing filters and avoids N+1 database queries.
    """
    if not patient_type:
        return qs

    clean_pt = str(patient_type).strip().upper()
    if clean_pt == 'FOLLOWUP':
        clean_pt = PATIENT_TYPE_FOLLOW_UP

    if clean_pt not in VALID_PATIENT_TYPES:
        if clean_pt == PATIENT_TYPE_UNKNOWN:
            return qs.filter(Q(patient__isnull=True) | Q(report_date__isnull=True))
        return qs.none()

    annotated = annotate_case_patient_type(qs)
    if clean_pt == PATIENT_TYPE_NEW:
        return annotated.filter(
            patient__isnull=False,
            report_date__isnull=False,
            has_prior_case=False
        )
    elif clean_pt == PATIENT_TYPE_FOLLOW_UP:
        return annotated.filter(
            patient__isnull=False,
            report_date__isnull=False,
            has_prior_case=True
        )

    return qs


def build_patient_type_matrices(cases, reference_date=None, allow_stored_age_fallback=False):
    """
    Computes cross-tabulation matrices for patient type with:
    1. patient_type_age_groups: {pt: {ag: count}}
    2. patient_type_gender: {pt: {gender: count}}
    3. patient_type_age_gender: {pt: {ag: {gender: count}}}
    4. patient_type_severity: {pt: {severity: count}}
    5. patient_type_vulnerable_groups: {pt: {vg: count}}
    6. patient_type_age_gender_vulnerability: {pt: {ag: {gender: {vg: count}}}}

    Age is strictly computed relative to each case's own report_date.
    Includes UNKNOWN categories dynamically only when unknown data actually exists.
    """
    base_pts = [PATIENT_TYPE_NEW, PATIENT_TYPE_FOLLOW_UP]
    base_ags = list(AGE_GROUPS)
    base_genders = ['MALE', 'FEMALE', 'OTHER']
    base_severities = [SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE]
    base_vgs = list(VULNERABLE_GROUPS)

    has_unk_pt = False
    has_unk_ag = False
    has_unk_g = False
    has_unk_sev = False
    has_unk_vg = False

    classified_cases = []
    for c in cases:
        pt = get_case_patient_type(c)
        ref_d = c.report_date if c.report_date else reference_date
        demo = resolve_patient_demographics(
            getattr(c, 'patient', None),
            reference_date=ref_d,
            allow_stored_age_fallback=allow_stored_age_fallback
        )
        ag = demo['age_group']
        g = demo['gender']
        sev = normalize_severity(getattr(c, 'severity', None))
        vg = normalize_vulnerable_group(getattr(getattr(c, 'patient', None), 'vulnerability_information', None))

        if pt == PATIENT_TYPE_UNKNOWN:
            has_unk_pt = True
        if ag == 'UNKNOWN':
            has_unk_ag = True
        if g == 'UNKNOWN':
            has_unk_g = True
        if sev == SEVERITY_UNKNOWN:
            has_unk_sev = True
        if vg == VULNERABLE_GROUP_UNKNOWN:
            has_unk_vg = True

        classified_cases.append((pt, ag, g, sev, vg))

    active_pts = list(base_pts) + ([PATIENT_TYPE_UNKNOWN] if has_unk_pt else [])
    active_ags = list(base_ags) + (['UNKNOWN'] if has_unk_ag else [])
    active_genders = list(base_genders) + (['UNKNOWN'] if has_unk_g else [])
    active_severities = list(base_severities) + ([SEVERITY_UNKNOWN] if has_unk_sev else [])
    active_vgs = list(base_vgs) + ([VULNERABLE_GROUP_UNKNOWN] if has_unk_vg else [])

    # Initialize matrices
    pt_age_groups = {pt: {ag: 0 for ag in active_ags} for pt in active_pts}
    pt_gender = {pt: {g: 0 for g in active_genders} for pt in active_pts}
    pt_age_gender = {pt: {ag: {g: 0 for g in active_genders} for ag in active_ags} for pt in active_pts}
    pt_severity = {pt: {s: 0 for s in active_severities} for pt in active_pts}
    pt_vulnerable_groups = {pt: {vg: 0 for vg in active_vgs} for pt in active_pts}
    pt_age_gender_vulnerability = {
        pt: {
            ag: {
                g: {vg: 0 for vg in active_vgs}
                for g in active_genders
            }
            for ag in active_ags
        }
        for pt in active_pts
    }

    # Aggregate counts
    for (pt, ag, g, sev, vg) in classified_cases:
        if pt in pt_age_groups and ag in pt_age_groups[pt]:
            pt_age_groups[pt][ag] += 1
        if pt in pt_gender and g in pt_gender[pt]:
            pt_gender[pt][g] += 1
        if pt in pt_age_gender and ag in pt_age_gender[pt] and g in pt_age_gender[pt][ag]:
            pt_age_gender[pt][ag][g] += 1
        if pt in pt_severity and sev in pt_severity[pt]:
            pt_severity[pt][sev] += 1
        if pt in pt_vulnerable_groups and vg in pt_vulnerable_groups[pt]:
            pt_vulnerable_groups[pt][vg] += 1
        if (pt in pt_age_gender_vulnerability and
            ag in pt_age_gender_vulnerability[pt] and
            g in pt_age_gender_vulnerability[pt][ag] and
            vg in pt_age_gender_vulnerability[pt][ag][g]):
            pt_age_gender_vulnerability[pt][ag][g][vg] += 1

    return (
        pt_age_groups,
        pt_gender,
        pt_age_gender,
        pt_severity,
        pt_vulnerable_groups,
        pt_age_gender_vulnerability,
    )

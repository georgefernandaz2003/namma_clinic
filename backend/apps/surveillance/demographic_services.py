"""
Public Health Intelligence Demographic Service
Authoritative Demographic Source Inspection & Determination:

1. Patient Date of Birth & Age:
   - apps.patients.models.Patient.date_of_birth (models.DateField, null=True, blank=True)
     The primary authoritative source for patient age. Age is calculated dynamically
     relative to the reference date (e.g. disease report date, as-of date, or today)
     as completed calendar years without storing duplicated calculated age fields.
   - apps.patients.models.Patient.age (models.IntegerField, default=30)
     The authoritative fallback source when date_of_birth is missing (null/blank)
     or invalid (e.g. future date or unparseable).

2. Patient Gender:
   - apps.patients.models.Patient.gender (models.CharField, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
     The authoritative source for patient gender, utilizing existing model enum choices.
     Missing or unrecognized gender entries are safely classified as 'UNKNOWN'.

3. Surveillance Integration:
   - apps.surveillance.models.DiseaseCase.patient
     Foreign key linking each surveillance disease case to its authoritative Patient record.
"""

import datetime
from django.db.models import Q


# ---------------------------------------------------------------------------
# Authoritative Age Group Constants
# ---------------------------------------------------------------------------
# Standard epidemiological age group brackets required across public health reporting:
# 0-5, 6-14, 15-24, 25-44, 45-59, 60+
AGE_GROUP_0_5 = '0-5'
AGE_GROUP_6_14 = '6-14'
AGE_GROUP_15_24 = '15-24'
AGE_GROUP_25_44 = '25-44'
AGE_GROUP_45_59 = '45-59'
AGE_GROUP_60_PLUS = '60+'
AGE_GROUP_UNKNOWN = 'UNKNOWN'

AGE_GROUPS = [
    AGE_GROUP_0_5,
    AGE_GROUP_6_14,
    AGE_GROUP_15_24,
    AGE_GROUP_25_44,
    AGE_GROUP_45_59,
    AGE_GROUP_60_PLUS,
]

# Existing Application Gender Values
GENDER_MALE = 'MALE'
GENDER_FEMALE = 'FEMALE'
GENDER_OTHER = 'OTHER'
GENDER_UNKNOWN = 'UNKNOWN'

GENDER_CHOICES = [GENDER_MALE, GENDER_FEMALE, GENDER_OTHER]

# ---------------------------------------------------------------------------
# Authoritative Severity Constants
# ---------------------------------------------------------------------------
SEVERITY_MILD = 'MILD'
SEVERITY_MODERATE = 'MODERATE'
SEVERITY_SEVERE = 'SEVERE'
SEVERITY_UNKNOWN = 'UNKNOWN'

SEVERITY_CHOICES = [SEVERITY_MILD, SEVERITY_MODERATE, SEVERITY_SEVERE]


# ---------------------------------------------------------------------------
# Core Demographic Utilities
# ---------------------------------------------------------------------------

def calculate_age(date_of_birth=None, reference_date=None, allow_stored_age_fallback=False, fallback_age=None):
    """
    Authoritative Age Calculation:
    Calculates patient age strictly in completed calendar years from date_of_birth
    relative to reference_date (such as DiseaseCase.report_date).

    Rules:
    1. Primary source is date_of_birth. Stored Patient.age is NOT used as primary source
       when date_of_birth is available because stored registration age can quickly become stale over time.
    2. Missing DOB (None, blank):
       Does NOT fabricate an age. Returns None (and age_group 'UNKNOWN').
       Fallback behavior: Stored Patient.age is only used if allow_stored_age_fallback=True
       is explicitly passed and fallback_age is a valid non-negative integer.
    3. Future DOB (date_of_birth > reference_date):
       Safely rejected as invalid. Returns None (and age_group 'UNKNOWN').
    4. Reference Date:
       Calculated strictly relative to reference_date (defaults to today if None).
    """
    ref_date = reference_date
    if ref_date is None:
        ref_date = datetime.date.today()
    elif isinstance(ref_date, datetime.datetime):
        ref_date = ref_date.date()
    elif isinstance(ref_date, str):
        try:
            ref_date = datetime.datetime.strptime(ref_date, '%Y-%m-%d').date()
        except ValueError:
            ref_date = datetime.date.today()

    parsed_dob = None
    if date_of_birth:
        if isinstance(date_of_birth, datetime.datetime):
            parsed_dob = date_of_birth.date()
        elif isinstance(date_of_birth, datetime.date):
            parsed_dob = date_of_birth
        elif isinstance(date_of_birth, str):
            try:
                parsed_dob = datetime.datetime.strptime(date_of_birth.strip(), '%Y-%m-%d').date()
            except ValueError:
                parsed_dob = None

    # Calculate exact age from DOB if valid
    if parsed_dob is not None:
        if parsed_dob <= ref_date:
            age = (
                ref_date.year
                - parsed_dob.year
                - ((ref_date.month, ref_date.day) < (parsed_dob.month, parsed_dob.day))
            )
            if age >= 0:
                return age
        # If parsed_dob > ref_date: Future DOB, reject safely
        return None

    # Missing or invalid DOB
    if not allow_stored_age_fallback:
        # Do not fabricate an age; return explicit None
        return None

    # Explicit fallback to stored age only if allowed
    if fallback_age is not None:
        try:
            val = int(fallback_age)
            if val >= 0:
                return val
        except (ValueError, TypeError):
            pass

    return None


def get_case_patient_age(disease_case, allow_stored_age_fallback=False):
    """
    Calculates age strictly from disease_case.patient.date_of_birth
    using disease_case.report_date as the reference date.
    Does NOT use stored Patient.age as primary source.
    """
    if not disease_case or not getattr(disease_case, 'patient', None):
        return None
    patient = disease_case.patient
    return calculate_age(
        date_of_birth=getattr(patient, 'date_of_birth', None),
        reference_date=getattr(disease_case, 'report_date', None),
        allow_stored_age_fallback=allow_stored_age_fallback,
        fallback_age=getattr(patient, 'age', None)
    )


def get_case_demographics(disease_case, allow_stored_age_fallback=False):
    """
    Extracts authoritative demographics for a DiseaseCase:
    - Calculates age strictly from patient.date_of_birth using disease_case.report_date
    - Assigns age_group into 0-5, 6-14, 15-24, 25-44, 45-59, 60+ (or UNKNOWN)
    - Uses existing Patient.gender choices (MALE, FEMALE, OTHER, or UNKNOWN)
    """
    if not disease_case or not getattr(disease_case, 'patient', None):
        return {
            'age': None,
            'age_group': AGE_GROUP_UNKNOWN,
            'gender': GENDER_UNKNOWN,
            'date_of_birth': None,
            'report_date': None
        }
    patient = disease_case.patient
    report_date = getattr(disease_case, 'report_date', None) or datetime.date.today()
    demo = resolve_patient_demographics(
        patient,
        reference_date=report_date,
        allow_stored_age_fallback=allow_stored_age_fallback
    )
    demo['report_date'] = report_date.strftime('%Y-%m-%d') if hasattr(report_date, 'strftime') else str(report_date)
    return demo


def get_age_group(age):
    """
    Classifies integer age into standardized epidemiological age group brackets:
    - 0-5: 0 <= age <= 5
    - 6-14: 6 <= age <= 14
    - 15-24: 15 <= age <= 24
    - 25-44: 25 <= age <= 44
    - 45-59: 45 <= age <= 59
    - 60+: age >= 60

    Returns 'UNKNOWN' for None, negative, or invalid age inputs.
    """
    if age is None:
        return AGE_GROUP_UNKNOWN

    try:
        val = int(age)
    except (ValueError, TypeError):
        return AGE_GROUP_UNKNOWN

    if val < 0:
        return AGE_GROUP_UNKNOWN
    elif 0 <= val <= 5:
        return AGE_GROUP_0_5
    elif 6 <= val <= 14:
        return AGE_GROUP_6_14
    elif 15 <= val <= 24:
        return AGE_GROUP_15_24
    elif 25 <= val <= 44:
        return AGE_GROUP_25_44
    elif 45 <= val <= 59:
        return AGE_GROUP_45_59
    else: # val >= 60
        return AGE_GROUP_60_PLUS


def normalize_gender(gender):
    """
    Normalizes gender string against the application's existing choices:
    ('MALE', 'FEMALE', 'OTHER').
    Returns 'UNKNOWN' for missing, blank, or incompatible values.
    """
    if not gender:
        return GENDER_UNKNOWN

    cleaned = str(gender).strip().upper()
    if cleaned in GENDER_CHOICES:
        return cleaned

    return GENDER_UNKNOWN


def resolve_patient_demographics(patient, reference_date=None, allow_stored_age_fallback=False):
    """
    Extracts authoritative demographics from a Patient model instance or dictionary.
    Returns:
    {
        'age': int or None,
        'age_group': str ('0-5', '6-14', ..., 'UNKNOWN'),
        'gender': str ('MALE', 'FEMALE', 'OTHER', 'UNKNOWN'),
        'date_of_birth': str (YYYY-MM-DD) or None
    }
    """
    if not patient:
        return {
            'age': None,
            'age_group': AGE_GROUP_UNKNOWN,
            'gender': GENDER_UNKNOWN,
            'date_of_birth': None
        }

    dob = getattr(patient, 'date_of_birth', None)
    fallback_age = getattr(patient, 'age', None)
    raw_gender = getattr(patient, 'gender', None)

    # In case patient is a dict
    if isinstance(patient, dict):
        dob = patient.get('date_of_birth')
        fallback_age = patient.get('age')
        raw_gender = patient.get('gender')

    age = calculate_age(
        date_of_birth=dob,
        reference_date=reference_date,
        allow_stored_age_fallback=allow_stored_age_fallback,
        fallback_age=fallback_age
    )
    age_group = get_age_group(age)
    gender = normalize_gender(raw_gender)

    dob_str = None
    if dob:
        if hasattr(dob, 'strftime'):
            dob_str = dob.strftime('%Y-%m-%d')
        else:
            dob_str = str(dob)

    return {
        'age': age,
        'age_group': age_group,
        'gender': gender,
        'date_of_birth': dob_str
    }


# ---------------------------------------------------------------------------
# Demographic Aggregation for Surveillance Datasets
# ---------------------------------------------------------------------------

def aggregate_demographics(disease_cases_qs, reference_date=None, allow_stored_age_fallback=False):
    """
    Computes demographic distribution across a queryset or list of DiseaseCase instances.
    Safely handles missing DOB, missing gender, and invalid data.

    Returns:
    {
        'total_cases': int,
        'age_groups': {
            '0-5': int,
            '6-14': int,
            '15-24': int,
            '25-44': int,
            '45-59': int,
            '60+': int,
            'UNKNOWN': int
        },
        'gender': {
            'MALE': int,
            'FEMALE': int,
            'OTHER': int,
            'UNKNOWN': int
        },
        'average_age': float or None,
        'min_age': int or None,
        'max_age': int or None
    }
    """
    age_group_counts = {
        AGE_GROUP_0_5: 0,
        AGE_GROUP_6_14: 0,
        AGE_GROUP_15_24: 0,
        AGE_GROUP_25_44: 0,
        AGE_GROUP_45_59: 0,
        AGE_GROUP_60_PLUS: 0,
        AGE_GROUP_UNKNOWN: 0
    }

    gender_counts = {
        GENDER_MALE: 0,
        GENDER_FEMALE: 0,
        GENDER_OTHER: 0,
        GENDER_UNKNOWN: 0
    }

    total_cases = 0
    valid_ages = []

    # Iterate over cases with patient joined
    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = cases.select_related('patient')

    for case in cases:
        total_cases += 1
        patient = getattr(case, 'patient', None)
        case_ref_date = getattr(case, 'report_date', reference_date) or reference_date
        demo = resolve_patient_demographics(
            patient,
            reference_date=case_ref_date,
            allow_stored_age_fallback=allow_stored_age_fallback
        )

        ag = demo['age_group']
        age_group_counts[ag] = age_group_counts.get(ag, 0) + 1

        g = demo['gender']
        gender_counts[g] = gender_counts.get(g, 0) + 1

        if demo['age'] is not None:
            valid_ages.append(demo['age'])

    avg_age = round(sum(valid_ages) / len(valid_ages), 1) if valid_ages else None
    min_age = min(valid_ages) if valid_ages else None
    max_age = max(valid_ages) if valid_ages else None

    return {
        'total_cases': total_cases,
        'age_groups': age_group_counts,
        'gender': gender_counts,
        'average_age': avg_age,
        'min_age': min_age,
        'max_age': max_age
    }


def validate_demographic_params(age_group=None, gender=None):
    """
    Validates optional demographic query parameters for Public Health Intelligence.

    Supported age_group values:
    '0-5', '6-14', '15-24', '25-44', '45-59', '60+'

    Supported gender values:
    'MALE', 'FEMALE', 'OTHER'

    Validation:
    - invalid age_group -> error message (HTTP 400)
    - invalid gender -> error message (HTTP 400)
    - empty/None demographic filters -> returns None without error
    """
    cleaned_ag = None
    if age_group is not None and str(age_group).strip() != '':
        ag_str = str(age_group).strip()
        if ag_str not in AGE_GROUPS:
            return None, None, f"Invalid age_group '{age_group}'. Supported values are: {', '.join(AGE_GROUPS)}."
        cleaned_ag = ag_str

    cleaned_g = None
    if gender is not None and str(gender).strip() != '':
        g_str = str(gender).strip().upper()
        if g_str not in GENDER_CHOICES:
            return None, None, f"Invalid gender '{gender}'. Supported values are: {', '.join(GENDER_CHOICES)}."
        cleaned_g = g_str

    return cleaned_ag, cleaned_g, None


def normalize_severity(severity):
    """
    Normalizes severity string against the application's supported choices:
    ('MILD', 'MODERATE', 'SEVERE').
    Returns 'UNKNOWN' for missing, blank, or incompatible values.
    Does NOT convert missing or invalid severity into MILD.
    """
    if not severity:
        return SEVERITY_UNKNOWN

    cleaned = str(severity).strip().upper()
    if cleaned in SEVERITY_CHOICES:
        return cleaned

    return SEVERITY_UNKNOWN


def validate_severity_param(severity=None):
    """
    Validates optional severity query parameter for Public Health Intelligence.
    Supported values: 'MILD', 'MODERATE', 'SEVERE'.
    UNKNOWN is NOT a selectable public filter.
    Returns: (cleaned_severity, error_message)
    - If valid or None/empty: (cleaned_val or None, None)
    - If invalid or UNKNOWN: (None, error_message)
    """
    if severity is None or str(severity).strip() == '':
        return None, None

    cleaned = str(severity).strip().upper()
    if cleaned not in SEVERITY_CHOICES:
        return None, f"Invalid severity '{severity}'. Supported values are: {', '.join(SEVERITY_CHOICES)}."

    return cleaned, None


def get_demographic_intelligence(facility_ids=None, district_id=None, disease_name=None,
                                 start_date=None, end_date=None, as_of_date=None,
                                 age_group=None, gender=None, severity=None,
                                 vulnerable_group=None, patient_type=None):
    """
    Public Health Intelligence Demographic Analysis Service.
    Derives strictly from real database records across DiseaseCase and Patient.
    Supports filtering by facility_ids, district_id, disease_name, date window,
    optional demographic criteria (age_group, gender), severity, vulnerable_group,
    and patient_type.
    """
    from apps.surveillance.models import DiseaseCase
    from apps.surveillance.intelligence_services import get_period_dates

    periods = get_period_dates(start_date=start_date, end_date=end_date, as_of_date=as_of_date)
    c_start = periods['current_start']
    c_end = periods['current_end']
    as_of = periods['current_end']

    qs = DiseaseCase.objects.filter(report_date__range=[c_start, c_end])
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)
    elif district_id is not None:
        qs = qs.filter(facility__district_id=district_id)

    if disease_name and disease_name != 'All Monitored Conditions':
        qs = qs.filter(disease_name__iexact=disease_name)

    if severity:
        qs = qs.filter(severity__iexact=severity)

    if age_group or gender:
        qs = filter_cases_by_demographics(qs, age_groups=age_group, genders=gender)

    if vulnerable_group:
        from apps.surveillance.vulnerable_population_services import filter_cases_by_vulnerable_group
        qs = filter_cases_by_vulnerable_group(qs, vulnerable_group=vulnerable_group)

    if patient_type:
        from apps.surveillance.patient_type_services import filter_cases_by_patient_type
        qs = filter_cases_by_patient_type(qs, patient_type=patient_type)

    # Overall demographic summary
    overall_demographics = aggregate_demographics(qs, reference_date=as_of)

    # Per-disease demographic breakdown
    distinct_diseases = list(qs.values_list('disease_name', flat=True).distinct())
    disease_demographics = []

    for d in distinct_diseases:
        clean_name = (d or '').strip() or 'Unspecified Diagnosis'
        d_qs = qs.filter(disease_name=d) if d else qs.filter(Q(disease_name__isnull=True) | Q(disease_name=''))
        d_demo = aggregate_demographics(d_qs, reference_date=as_of)
        disease_demographics.append({
            'disease': clean_name,
            'total_cases': d_demo['total_cases'],
            'age_groups': d_demo['age_groups'],
            'gender': d_demo['gender'],
            'average_age': d_demo['average_age'],
            'min_age': d_demo['min_age'],
            'max_age': d_demo['max_age']
        })

    disease_demographics.sort(key=lambda x: x['total_cases'], reverse=True)

    return {
        'observation_period': {
            'start_date': str(c_start),
            'end_date': str(c_end),
            'duration_days': periods['duration_days']
        },
        'summary': overall_demographics,
        'disease_demographics': disease_demographics
    }


# ---------------------------------------------------------------------------
# Reusable Utilities for Demographic Filtering & Combinations
# ---------------------------------------------------------------------------

def matches_demographic_criteria(patient, age_groups=None, genders=None, reference_date=None, allow_stored_age_fallback=False):
    """
    Evaluates whether a patient record matches requested demographic criteria:
    - age_groups: list, set, or single age group string, e.g. ['0-5', '6-14']
    - genders: list, set, or single gender string, e.g. ['MALE', 'FEMALE']
    - reference_date: reference date for age calculation (e.g. disease report_date)
    """
    demo = resolve_patient_demographics(
        patient,
        reference_date=reference_date,
        allow_stored_age_fallback=allow_stored_age_fallback
    )

    if age_groups:
        if isinstance(age_groups, str):
            age_groups = [age_groups]
        clean_ag = {str(ag).strip() for ag in age_groups if ag}
        if clean_ag and demo['age_group'] not in clean_ag:
            return False

    if genders:
        if isinstance(genders, str):
            genders = [genders]
        clean_g = {normalize_gender(g) for g in genders if g}
        if clean_g and demo['gender'] not in clean_g:
            return False

    return True


def filter_cases_by_demographics(disease_cases_qs, age_groups=None, genders=None, reference_date=None, allow_stored_age_fallback=False):
    """
    Filters DiseaseCase instances matching age groups and/or gender criteria.
    Determines age relative to each case's report_date (or provided reference_date)
    without redundant database persistence.
    """
    if not age_groups and not genders:
        return disease_cases_qs

    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = cases.select_related('patient')

    matching_ids = []
    for case in cases:
        case_ref = getattr(case, 'report_date', reference_date) or reference_date
        if matches_demographic_criteria(
            patient=getattr(case, 'patient', None),
            age_groups=age_groups,
            genders=genders,
            reference_date=case_ref,
            allow_stored_age_fallback=allow_stored_age_fallback
        ):
            matching_ids.append(case.id)

    if hasattr(disease_cases_qs, 'filter'):
        return disease_cases_qs.filter(id__in=matching_ids)
    return [c for c in cases if c.id in matching_ids]


def build_age_gender_matrix(disease_cases_qs, reference_date=None, allow_stored_age_fallback=False):
    """
    Builds a 2D cross-tabulation matrix of case counts combining age groups and genders:
    Rows: AGE_GROUPS (0-5, 6-14, 15-24, 25-44, 45-59, 60+, UNKNOWN)
    Columns: GENDERS (MALE, FEMALE, OTHER, UNKNOWN)
    """
    all_age_groups = AGE_GROUPS + [AGE_GROUP_UNKNOWN]
    all_genders = GENDER_CHOICES + [GENDER_UNKNOWN]

    # Initialize empty grid
    matrix = {
        ag: {g: 0 for g in all_genders}
        for ag in all_age_groups
    }

    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = cases.select_related('patient')

    for case in cases:
        case_ref = getattr(case, 'report_date', reference_date) or reference_date
        demo = resolve_patient_demographics(
            getattr(case, 'patient', None),
            reference_date=case_ref,
            allow_stored_age_fallback=allow_stored_age_fallback
        )
        ag = demo['age_group']
        g = demo['gender']

        if ag not in matrix:
            ag = AGE_GROUP_UNKNOWN
        if g not in matrix[ag]:
            g = GENDER_UNKNOWN

        matrix[ag][g] += 1

    return matrix


def build_severity_demographic_matrices(disease_cases_qs, reference_date=None, allow_stored_age_fallback=False):
    """
    Builds multidimensional cross-tabulations combining severity and demographics:
    1. severity_age_groups: severity -> age_group -> count
    2. severity_gender: severity -> gender -> count
    3. severity_age_gender: severity -> age_group -> gender -> count

    Uses individual case report_date for age calculation without duplicate logic.
    Retains UNKNOWN where actual demographic/severity data is missing or invalid.
    """
    all_age_groups = AGE_GROUPS + [AGE_GROUP_UNKNOWN]
    all_genders = GENDER_CHOICES + [GENDER_UNKNOWN]

    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = list(cases.select_related('patient'))
    elif not isinstance(cases, list):
        cases = list(cases)

    has_unknown_sev = any(normalize_severity(getattr(c, 'severity', None)) == SEVERITY_UNKNOWN for c in cases)

    severities = list(SEVERITY_CHOICES)
    if has_unknown_sev:
        severities.append(SEVERITY_UNKNOWN)

    severity_age_groups = {
        s: {ag: 0 for ag in all_age_groups}
        for s in severities
    }

    severity_gender = {
        s: {g: 0 for g in all_genders}
        for s in severities
    }

    severity_age_gender = {
        s: {ag: {g: 0 for g in all_genders} for ag in all_age_groups}
        for s in severities
    }

    for case in cases:
        case_ref = getattr(case, 'report_date', reference_date) or reference_date
        demo = resolve_patient_demographics(
            getattr(case, 'patient', None),
            reference_date=case_ref,
            allow_stored_age_fallback=allow_stored_age_fallback
        )
        ag = demo['age_group']
        g = demo['gender']
        sev = normalize_severity(getattr(case, 'severity', None))

        if sev in severity_age_groups:
            severity_age_groups[sev][ag] = severity_age_groups[sev].get(ag, 0) + 1
            severity_gender[sev][g] = severity_gender[sev].get(g, 0) + 1
            severity_age_gender[sev][ag][g] = severity_age_gender[sev][ag].get(g, 0) + 1

    return severity_age_groups, severity_gender, severity_age_gender


# Re-export patient type intelligence functions for direct access from demographic_services
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


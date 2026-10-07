"""
Public Health Intelligence - Vulnerable Population Services (Prompt 5 Foundation)
Authoritative vulnerability normalization, validation, filtering, and cross-tabulation utilities.

Source of Truth:
- apps.patients.models.Patient.vulnerability_information (models.CharField, default='Slum Resident / Low Income Group')
  Authoritative patient-level vulnerability tag populated during citizen registration and outreach.
- apps.surveillance.models.DiseaseCase.patient
  Foreign key linking each surveillance case to its authoritative Patient record.

Supported Public Health Vulnerability Groups:
- PREGNANT: High-risk pregnant women, ANC mothers.
- ELDERLY: Senior citizens, geriatric patients, elderly with comorbidities.
- DISABILITY: Persons with disabilities (PwD).
- CHRONIC_CONDITION: Non-communicable diseases (hypertension, diabetes, cardiac, etc.).
- LOW_INCOME_SLUM: Slum residents, BPL card holders, daily wage/migrant workers.
- GENERAL: General / non-vulnerable citizens.
- UNKNOWN: Missing, blank, or unrecognized vulnerability entries (not a selectable filter).
"""

from apps.surveillance.demographic_services import (
    AGE_GROUPS,
    AGE_GROUP_UNKNOWN,
    GENDER_CHOICES,
    GENDER_UNKNOWN,
    SEVERITY_CHOICES,
    SEVERITY_UNKNOWN,
    normalize_gender,
    normalize_severity,
    resolve_patient_demographics,
)

# ---------------------------------------------------------------------------
# Authoritative Vulnerable Group Constants
# ---------------------------------------------------------------------------
VULNERABLE_GROUP_PREGNANT = 'PREGNANT'
VULNERABLE_GROUP_ELDERLY = 'ELDERLY'
VULNERABLE_GROUP_DISABILITY = 'DISABILITY'
VULNERABLE_GROUP_CHRONIC = 'CHRONIC_CONDITION'
VULNERABLE_GROUP_LOW_INCOME = 'LOW_INCOME_SLUM'
VULNERABLE_GROUP_GENERAL = 'GENERAL'
VULNERABLE_GROUP_UNKNOWN = 'UNKNOWN'

VULNERABLE_GROUPS = [
    VULNERABLE_GROUP_PREGNANT,
    VULNERABLE_GROUP_ELDERLY,
    VULNERABLE_GROUP_DISABILITY,
    VULNERABLE_GROUP_CHRONIC,
    VULNERABLE_GROUP_LOW_INCOME,
    VULNERABLE_GROUP_GENERAL,
]

ALL_VULNERABLE_GROUPS = VULNERABLE_GROUPS + [VULNERABLE_GROUP_UNKNOWN]


def normalize_vulnerable_group(val):
    """
    Authoritative vulnerability group normalization mapping real database entries
    and canonical filter inputs into standardized public health vulnerability categories.

    Does not fabricate vulnerability. Returns UNKNOWN for missing, empty, or unsupported values.
    """
    if val is None:
        return VULNERABLE_GROUP_UNKNOWN

    raw = str(val).strip()
    if not raw:
        return VULNERABLE_GROUP_UNKNOWN

    u = raw.upper()

    # Exact canonical matches
    if u in ['PREGNANT', 'PREGNANCY', 'MATERNAL', 'ANC', 'HIGH_RISK_PREGNANCY']:
        return VULNERABLE_GROUP_PREGNANT
    if u in ['ELDERLY', 'SENIOR_CITIZEN', 'SENIOR', 'GERIATRIC']:
        return VULNERABLE_GROUP_ELDERLY
    if u in ['DISABILITY', 'PWD', 'PERSON_WITH_DISABILITY']:
        return VULNERABLE_GROUP_DISABILITY
    if u in ['CHRONIC_CONDITION', 'CHRONIC', 'COMORBIDITY']:
        return VULNERABLE_GROUP_CHRONIC
    if u in ['LOW_INCOME_SLUM', 'LOW_INCOME', 'SLUM', 'BPL', 'SOCIOECONOMIC', 'SLUM_BPL']:
        return VULNERABLE_GROUP_LOW_INCOME
    if u in ['GENERAL', 'NON_VULNERABLE', 'GENERAL / NON-VULNERABLE']:
        return VULNERABLE_GROUP_GENERAL
    if u == 'UNKNOWN':
        return VULNERABLE_GROUP_UNKNOWN

    # Authoritative application choices from Patients master
    # 1. Pregnancy / Maternal
    if any(k in u for k in ['PREGNAN', 'MATERNAL', ' ANC']):
        return VULNERABLE_GROUP_PREGNANT

    # 2. Senior / Elderly
    if any(k in u for k in ['ELDERLY', 'SENIOR CITIZEN']):
        return VULNERABLE_GROUP_ELDERLY

    # 3. Disability
    if any(k in u for k in ['DISABILITY', 'PWD']):
        return VULNERABLE_GROUP_DISABILITY

    # 4. Chronic condition
    if any(k in u for k in ['HYPERTENSION', 'CARDIAC', 'DIABETIC', 'FEBRILE']):
        return VULNERABLE_GROUP_CHRONIC

    # 5. Low Income / Slum / BPL / Migrant
    if any(k in u for k in ['SLUM', 'LOW INCOME', 'BPL', 'MIGRANT', 'DAILY WAGE']):
        return VULNERABLE_GROUP_LOW_INCOME

    # 6. General
    if 'GENERAL' in u:
        return VULNERABLE_GROUP_GENERAL

    return VULNERABLE_GROUP_UNKNOWN


def validate_vulnerable_group_param(vulnerable_group=None):
    """
    Validates optional vulnerable_group query parameter for Public Health Intelligence.
    Supported public values include canonical groups and application-standard choices.
    UNKNOWN is NOT a selectable public filter.

    Returns:
    - (cleaned_group, None) if valid
    - (None, None) if None or empty
    - (None, error_message) if invalid or UNKNOWN
    """
    if vulnerable_group is None or str(vulnerable_group).strip() == '':
        return None, None

    cleaned_str = str(vulnerable_group).strip()
    norm = normalize_vulnerable_group(cleaned_str)

    if norm == VULNERABLE_GROUP_UNKNOWN:
        supported_str = ', '.join(VULNERABLE_GROUPS)
        return None, f"Invalid vulnerable_group '{vulnerable_group}'. Supported groups are: {supported_str}."

    return norm, None


def filter_cases_by_vulnerable_group(disease_cases_qs, vulnerable_group=None):
    """
    Filters DiseaseCase instances matching a requested vulnerable group.
    Loads patient data via select_related('patient') to avoid N+1 queries.
    """
    if not vulnerable_group:
        return disease_cases_qs

    norm_filter = normalize_vulnerable_group(vulnerable_group)
    if norm_filter == VULNERABLE_GROUP_UNKNOWN:
        if hasattr(disease_cases_qs, 'none'):
            return disease_cases_qs.none()
        return []

    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = cases.select_related('patient')

    matching_ids = []
    for case in cases:
        p = getattr(case, 'patient', None)
        v_info = getattr(p, 'vulnerability_information', None) if p else None
        if normalize_vulnerable_group(v_info) == norm_filter:
            matching_ids.append(case.id)

    if hasattr(disease_cases_qs, 'filter'):
        return disease_cases_qs.filter(id__in=matching_ids)
    return [c for c in cases if c.id in matching_ids]


def build_vulnerable_population_matrices(disease_cases_qs, reference_date=None, allow_stored_age_fallback=False):
    """
    Builds multidimensional cross-tabulations combining vulnerable groups with demographics & severity:
    1. vulnerable_age_groups: vulnerable_group -> age_group -> count
    2. vulnerable_gender: vulnerable_group -> gender -> count
    3. vulnerable_age_gender: vulnerable_group -> age_group -> gender -> count
    4. vulnerable_severity: vulnerable_group -> severity -> count
    5. vulnerable_age_gender_severity: vulnerable_group -> age_group -> gender -> severity -> count

    Uses individual case report_date for age calculation without duplicate logic.
    Retains UNKNOWN where actual demographic, severity, or vulnerability data is missing or invalid.
    """
    all_age_groups = AGE_GROUPS + [AGE_GROUP_UNKNOWN]
    all_genders = GENDER_CHOICES + [GENDER_UNKNOWN]
    all_severities = SEVERITY_CHOICES + [SEVERITY_UNKNOWN]

    cases = disease_cases_qs
    if hasattr(cases, 'select_related'):
        cases = list(cases.select_related('patient'))
    elif not isinstance(cases, list):
        cases = list(cases)

    # Determine if UNKNOWN vulnerable group is represented
    has_unknown_vg = any(
        normalize_vulnerable_group(getattr(getattr(c, 'patient', None), 'vulnerability_information', None)) == VULNERABLE_GROUP_UNKNOWN
        for c in cases
    )

    active_vulnerable_groups = list(VULNERABLE_GROUPS)
    if has_unknown_vg:
        active_vulnerable_groups.append(VULNERABLE_GROUP_UNKNOWN)

    # 1. vulnerable_age_groups
    vulnerable_age_groups = {
        vg: {ag: 0 for ag in all_age_groups}
        for vg in active_vulnerable_groups
    }

    # 2. vulnerable_gender
    vulnerable_gender = {
        vg: {g: 0 for g in all_genders}
        for vg in active_vulnerable_groups
    }

    # 3. vulnerable_age_gender
    vulnerable_age_gender = {
        vg: {ag: {g: 0 for g in all_genders} for ag in all_age_groups}
        for vg in active_vulnerable_groups
    }

    # 4. vulnerable_severity
    vulnerable_severity = {
        vg: {s: 0 for s in all_severities}
        for vg in active_vulnerable_groups
    }

    # 5. vulnerable_age_gender_severity
    vulnerable_age_gender_severity = {
        vg: {
            ag: {
                g: {s: 0 for s in all_severities}
                for g in all_genders
            }
            for ag in all_age_groups
        }
        for vg in active_vulnerable_groups
    }

    for case in cases:
        case_ref = getattr(case, 'report_date', reference_date) or reference_date
        patient = getattr(case, 'patient', None)
        demo = resolve_patient_demographics(
            patient,
            reference_date=case_ref,
            allow_stored_age_fallback=allow_stored_age_fallback
        )
        ag = demo['age_group']
        g = demo['gender']
        sev = normalize_severity(getattr(case, 'severity', None))
        vg = normalize_vulnerable_group(getattr(patient, 'vulnerability_information', None) if patient else None)

        if vg in vulnerable_age_groups:
            vulnerable_age_groups[vg][ag] = vulnerable_age_groups[vg].get(ag, 0) + 1
            vulnerable_gender[vg][g] = vulnerable_gender[vg].get(g, 0) + 1
            vulnerable_age_gender[vg][ag][g] = vulnerable_age_gender[vg][ag].get(g, 0) + 1
            vulnerable_severity[vg][sev] = vulnerable_severity[vg].get(sev, 0) + 1
            vulnerable_age_gender_severity[vg][ag][g][sev] = vulnerable_age_gender_severity[vg][ag][g].get(sev, 0) + 1

    return (
        vulnerable_age_groups,
        vulnerable_gender,
        vulnerable_age_gender,
        vulnerable_severity,
        vulnerable_age_gender_severity,
    )

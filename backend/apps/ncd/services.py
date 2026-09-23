"""
NCD Domain Services: Longitudinal Chronic Care and Disease Registration.
"""
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.common.exceptions import DomainValidationError


def register_ncd_condition(
    patient,
    facility,
    registering_doctor,
    condition_code,
    staging="",
    control_status="SCREENED"
):
    """
    Registers a patient in the long-term chronic NCD registry.
    """
    if NCDCondition.objects.filter(patient=patient, condition_code=condition_code).exists():
        raise DomainValidationError(
            f"Patient #{patient.id} is already registered for condition '{condition_code}'."
        )

    return NCDCondition.objects.create(
        patient=patient,
        registering_facility=facility,
        registering_doctor=registering_doctor,
        condition_code=condition_code,
        staging=staging,
        control_status=control_status
    )


def record_ncd_assessment(
    condition,
    visit,
    assessed_by_staff,
    systolic_bp=None,
    diastolic_bp=None,
    blood_glucose_fasting=None,
    clinical_notes=""
):
    """
    Records a periodic clinical assessment for an active NCD condition.
    """
    return NCDAssessment.objects.create(
        condition=condition,
        visit=visit,
        assessed_by_staff=assessed_by_staff,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        blood_glucose_fasting=blood_glucose_fasting,
        clinical_notes=clinical_notes
    )

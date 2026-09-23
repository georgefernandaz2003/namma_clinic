"""
Public Health Surveillance Services.
Decouples statutory epidemiological notifications from ordinary clinical consultations.
"""
import uuid
import datetime
from django.db import transaction
from django.utils import timezone
from apps.surveillance.models import DiseaseMaster, DiseaseSurveillanceCase, PublicHealthNotification
from apps.common.exceptions import DomainValidationError


def report_surveillance_case(
    patient,
    facility,
    disease,
    reporting_staff,
    case_number=None,
    severity="MILD",
    status="SUSPECTED",
    ward=None,
    investigation_notes=""
):
    """
    Reports a suspected or confirmed communicable disease case to statutory public health surveillance.
    """
    num = case_number or f"SURV-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    return DiseaseSurveillanceCase.objects.create(
        case_number=num,
        patient=patient,
        facility=facility,
        disease=disease,
        reporting_staff=reporting_staff,
        ward=ward,
        severity=severity,
        status=status,
        investigation_notes=investigation_notes
    )


def dispatch_public_health_notification(
    case,
    notified_authority,
    dispatch_payload
):
    """
    Dispatches a statutory epidemiological notification to district/state surveillance authorities (e.g. IDSP).
    """
    return PublicHealthNotification.objects.create(
        case=case,
        notified_authority=notified_authority,
        transmission_status="DISPATCHED",
        dispatch_payload=dispatch_payload,
        dispatched_at=timezone.now()
    )

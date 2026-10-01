"""
Referral & Follow-Up Domain Services.
Enforces aggregate state machine validation, append-only event trail, and cross-encounter follow-up completion.
"""
import uuid
import datetime
from django.db import transaction
from django.utils import timezone
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.common.exceptions import (
    UnauthorizedDomainAction,
    DomainValidationError,
    InvalidStateTransition,
    InvalidFollowUpCompletionError
)
from apps.audit.services import record_audit_event


def create_referral_order(
    patient,
    visit,
    source_facility,
    destination_facility,
    referring_doctor_staff,
    reason,
    urgency="ROUTINE",
    clinical_summary="",
    referral_number=None
):
    """
    Creates a new ReferralOrder and appends the initial CREATED event.
    """
    if source_facility == destination_facility:
        raise DomainValidationError("Destination facility cannot be identical to source facility.")

    ref_num = referral_number or f"REF-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    with transaction.atomic():
        order = ReferralOrder.objects.create(
            referral_number=ref_num,
            patient=patient,
            visit=visit,
            source_facility=source_facility,
            destination_facility=destination_facility,
            referring_doctor=referring_doctor_staff,
            urgency=urgency,
            reason=reason,
            clinical_summary=clinical_summary,
            status="INITIATED"
        )

        ReferralEvent.objects.create(
            referral=order,
            recorded_by_staff=referring_doctor_staff,
            event_type="ACKNOWLEDGED",
            specialist_findings=f"Referral initiated: {reason}"
        )

        return order


def transition_referral_state(referral_order, new_status, actor_staff, notes="", transport_details=None):
    """
    Validates and executes a state transition on a ReferralOrder, appending an immutable ReferralEvent.
    """
    valid_transitions = {
        "INITIATED": ["ACKNOWLEDGED", "CANCELLED"],
        "ACKNOWLEDGED": ["IN_TRANSIT", "ARRIVED", "CANCELLED"],
        "IN_TRANSIT": ["ARRIVED", "CANCELLED"],
        "ARRIVED": ["UNDER_SPECIALIST_CARE", "COMPLETED", "CANCELLED"],
        "UNDER_SPECIALIST_CARE": ["COMPLETED", "CANCELLED"],
        "COMPLETED": [],
        "CANCELLED": []
    }

    current = referral_order.status
    allowed = valid_transitions.get(current, [])
    if new_status not in allowed:
        raise InvalidStateTransition("ReferralOrder", current, new_status)

    with transaction.atomic():
        referral_order.status = new_status
        referral_order.save(update_fields=["status", "updated_at"])

        event = ReferralEvent.objects.create(
            referral=referral_order,
            recorded_by_staff=actor_staff,
            event_type="SPECIALIST_CONSULT" if new_status == "UNDER_SPECIALIST_CARE" else "ACKNOWLEDGED",
            specialist_findings=notes
        )

        return referral_order, event


def create_followup_task(
    patient,
    facility,
    due_date,
    category="GENERAL",
    originating_visit=None,
    referral=None,
    clinical_instructions=""
):
    """
    Creates a pending patient follow-up / recall task.
    """
    return FollowUpTask.objects.create(
        patient=patient,
        facility=facility,
        due_date=due_date,
        category=category,
        originating_visit=originating_visit,
        referral=referral,
        clinical_instructions=clinical_instructions,
        status="PENDING"
    )


def complete_followup(followup_task, completed_in_visit, completing_staff):
    """
    Formally completes a FollowUpTask.
    Enforces cross-encounter integrity:
    1. Task must be in PENDING status.
    2. completed_in_visit must be COMPLETED.
    3. completed_in_visit.patient == followup_task.patient.
    4. completed_in_visit.facility == followup_task.facility.
    5. completing_staff must be an active staff profile.
    6. Sets completed_in_visit, completed_by_staff, completed_at atomically.
    """
    if followup_task.status != "PENDING":
        raise InvalidFollowUpCompletionError(
            followup_task.id,
            f"FollowUpTask is in '{followup_task.status}' status. Only PENDING tasks can be completed."
        )

    if not completing_staff or completing_staff.status != "ACTIVE":
        raise UnauthorizedDomainAction("Only active clinical staff may complete follow-up tasks.")

    if completed_in_visit.status != "COMPLETED":
        raise InvalidFollowUpCompletionError(
            followup_task.id,
            f"Visit #{completed_in_visit.id} is in status '{completed_in_visit.status}'. FollowUp completion requires a COMPLETED visit."
        )

    if completed_in_visit.patient_id != followup_task.patient_id:
        raise InvalidFollowUpCompletionError(
            followup_task.id,
            f"Patient mismatch: FollowUp is for Patient #{followup_task.patient_id}, but Visit is for Patient #{completed_in_visit.patient_id}."
        )

    if completed_in_visit.facility_id != followup_task.facility_id:
        raise InvalidFollowUpCompletionError(
            followup_task.id,
            f"Facility mismatch: FollowUp is at Facility #{followup_task.facility_id}, but Visit is at Facility #{completed_in_visit.facility_id}."
        )

    with transaction.atomic():
        locked_task = FollowUpTask.objects.select_for_update().get(pk=followup_task.pk)
        locked_task.status = "COMPLETED"
        locked_task.completed_in_visit = completed_in_visit
        locked_task.completed_by_staff = completing_staff
        locked_task.completed_at = timezone.now()
        locked_task.save(update_fields=["status", "completed_in_visit", "completed_by_staff", "completed_at"])

        record_audit_event(
            actor_staff=completing_staff,
            actor_role_snapshot=completing_staff.designation,
            facility=completed_in_visit.facility,
            action_type="UPDATE",
            table_name="follow_up_tasks",
            record_id=locked_task.id,
            payload_after={"status": "COMPLETED", "completed_in_visit_id": completed_in_visit.id}
        )
        return locked_task

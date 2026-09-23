"""
Diagnostic Domain Services.
Enforces 1:N:1 order/request/specimen cardinality, 1:1 result lock, and immutable amendment history.
"""
import uuid
import datetime
from django.db import transaction, IntegrityError
from django.utils import timezone
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult, DiagnosticResultAmendment
)
from apps.common.exceptions import (
    DomainValidationError,
    DiagnosticResultAlreadyExistsError,
    VerifiedResultImmutableError
)
from apps.audit.services import record_audit_event


def create_diagnostic_order(
    visit,
    facility,
    ordering_doctor_staff,
    priority="ROUTINE",
    clinical_indication="",
    order_date=None,
    order_number=None
):
    """
    Creates an encounter-linked DiagnosticOrder.
    """
    today = order_date or datetime.date.today()
    ord_num = order_number or f"ORD-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    with transaction.atomic():
        order = DiagnosticOrder.objects.create(
            visit=visit,
            facility=facility,
            ordering_doctor_staff=ordering_doctor_staff,
            order_number=ord_num,
            order_date=today,
            priority=priority,
            clinical_indication=clinical_indication,
            status="ORDERED"
        )
        return order


def create_test_request(diagnostic_order, test_master, specimen=None):
    """
    Adds a test investigation requisition to a DiagnosticOrder.
    Requisitions can optionally link to an existing biological specimen.
    """
    if TestRequest.objects.filter(diagnostic_order=diagnostic_order, test_master=test_master).exists():
        raise DomainValidationError(
            f"Test '{test_master.test_name}' has already been requested under Order #{diagnostic_order.order_number}."
        )

    with transaction.atomic():
        request = TestRequest.objects.create(
            diagnostic_order=diagnostic_order,
            test_master=test_master,
            specimen=specimen,
            status="PENDING"
        )
        return request


def collect_specimen(
    diagnostic_order,
    barcode_identifier,
    specimen_type,
    collected_by_staff,
    test_requests=None
):
    """
    Registers collection of a biological Specimen and links it to one or more TestRequests.
    """
    if Specimen.objects.filter(barcode_identifier=barcode_identifier).exists():
        raise DomainValidationError(f"Specimen barcode '{barcode_identifier}' already exists.")

    with transaction.atomic():
        specimen = Specimen.objects.create(
            diagnostic_order=diagnostic_order,
            barcode_identifier=barcode_identifier,
            specimen_type=specimen_type,
            collected_by_staff=collected_by_staff,
            status="COLLECTED"
        )
        if test_requests:
            for tr in test_requests:
                tr.specimen = specimen
                tr.save(update_fields=["specimen"])

        return specimen


def record_diagnostic_result(
    test_request,
    entered_by_staff,
    result_value_text="",
    result_value_numeric=None,
    reference_range_applied="",
    is_abnormal=False,
    is_critical_panic=False
):
    """
    Records laboratory analysis result for a TestRequest.
    Enforces strictly at most one DiagnosticResult per TestRequest.
    """
    if hasattr(test_request, "diagnostic_result") or DiagnosticResult.objects.filter(test_request=test_request).exists():
        raise DiagnosticResultAlreadyExistsError(test_request.id)

    with transaction.atomic():
        try:
            result = DiagnosticResult.objects.create(
                test_request=test_request,
                result_value_text=result_value_text,
                result_value_numeric=result_value_numeric,
                reference_range_applied=reference_range_applied,
                is_abnormal=is_abnormal,
                is_critical_panic=is_critical_panic,
                status="ENTERED",
                entered_by_staff=entered_by_staff
            )
            test_request.status = "COMPLETED"
            test_request.save(update_fields=["status"])
            return result
        except IntegrityError as exc:
            raise DiagnosticResultAlreadyExistsError(test_request.id) from exc


def verify_diagnostic_result(diagnostic_result, verified_by_staff):
    """
    Locks and formally verifies a diagnostic result.
    Once verified, values cannot be silently updated (must use amendment).
    """
    with transaction.atomic():
        locked_result = DiagnosticResult.objects.select_for_update().get(pk=diagnostic_result.pk)
        if locked_result.status == "VERIFIED":
            raise VerifiedResultImmutableError(locked_result.id)

        locked_result.status = "VERIFIED"
        locked_result.verified_by_staff = verified_by_staff
        locked_result.verified_at = timezone.now()
        locked_result.save(update_fields=["status", "verified_by_staff", "verified_at"])

        record_audit_event(
            actor_staff=verified_by_staff,
            actor_role_snapshot=verified_by_staff.designation,
            facility=locked_result.test_request.diagnostic_order.facility,
            action_type="UPDATE",
            table_name="diagnostic_results",
            record_id=locked_result.id,
            payload_after={"status": "VERIFIED", "verified_at": str(locked_result.verified_at)}
        )
        return locked_result


def amend_diagnostic_result(
    diagnostic_result,
    amended_by_staff,
    amendment_reason,
    amended_value_text="",
    amended_value_numeric=None
):
    """
    Amends a previously verified diagnostic result, preserving complete immutable history.
    """
    if not amendment_reason:
        raise DomainValidationError("amendment_reason is mandatory when amending a verified result.")

    with transaction.atomic():
        locked_result = DiagnosticResult.objects.select_for_update().get(pk=diagnostic_result.pk)
        if locked_result.status not in ["VERIFIED", "AMENDED"]:
            raise DomainValidationError(
                f"Result #{locked_result.id} is in status '{locked_result.status}'. Only VERIFIED results can be amended."
            )

        # Create immutable amendment audit record
        amendment = DiagnosticResultAmendment.objects.create(
            diagnostic_result=locked_result,
            previous_value_text=locked_result.result_value_text,
            previous_value_numeric=locked_result.result_value_numeric,
            amended_value_text=amended_value_text,
            amended_value_numeric=amended_value_numeric,
            amendment_reason=amendment_reason,
            amended_by_staff=amended_by_staff
        )

        locked_result.result_value_text = amended_value_text
        locked_result.result_value_numeric = amended_value_numeric
        locked_result.status = "AMENDED"
        locked_result.save(update_fields=["result_value_text", "result_value_numeric", "status"])

        return locked_result, amendment

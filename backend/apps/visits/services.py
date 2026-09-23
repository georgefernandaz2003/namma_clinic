"""
Token Allocation and Encounter Services.
Implements concurrency-safe sequence allocation across independent OPD and LAB namespaces.
"""
import datetime
from django.db import transaction, IntegrityError
from apps.visits.models import Visit, Token, FacilityDailyCounter
from apps.common.exceptions import (
    DomainValidationError,
    DuplicateTokenError
)
from apps.audit.services import record_audit_event


def allocate_token(facility, counter_type, counter_date=None):
    """
    Atomically increments and returns the next daily token number for a facility and queue type.
    Uses SELECT FOR UPDATE on FacilityDailyCounter row.
    """
    today = counter_date or datetime.date.today()
    if counter_type not in ["OPD", "LAB"]:
        raise DomainValidationError(f"Invalid counter_type '{counter_type}'. Must be 'OPD' or 'LAB'.")

    with transaction.atomic():
        counter, created = FacilityDailyCounter.objects.select_for_update().get_or_create(
            facility=facility,
            counter_date=today,
            counter_type=counter_type,
            defaults={"last_token_number": 0}
        )
        counter.last_token_number += 1
        counter.save(update_fields=["last_token_number", "updated_at"])
        return counter.last_token_number


def issue_opd_token(visit, facility=None, token_date=None, priority="NORMAL"):
    """
    Issues a unique OPD token for a Visit within the facility's daily OPD namespace.
    """
    fac = facility or visit.facility
    today = token_date or visit.opd_date or datetime.date.today()

    if hasattr(visit, "token") and visit.token is not None:
        return visit.token

    with transaction.atomic():
        token_num = allocate_token(facility=fac, counter_type="OPD", counter_date=today)
        try:
            token = Token.objects.create(
                visit=visit,
                facility=fac,
                date=today,
                token_number=token_num,
                priority=priority,
                status="WAITING"
            )
        except IntegrityError as exc:
            raise DuplicateTokenError(fac.id, "OPD", token_num, today) from exc

        return token


def issue_lab_token(diagnostic_order, facility=None, order_date=None):
    """
    Issues a unique Laboratory token for a DiagnosticOrder within the facility's daily LAB namespace.
    """
    fac = facility or diagnostic_order.facility
    today = order_date or diagnostic_order.order_date or datetime.date.today()

    if diagnostic_order.lab_token_number is not None:
        return diagnostic_order.lab_token_number

    with transaction.atomic():
        token_num = allocate_token(facility=fac, counter_type="LAB", counter_date=today)
        diagnostic_order.lab_token_number = token_num
        try:
            diagnostic_order.save(update_fields=["lab_token_number", "updated_at"])
        except IntegrityError as exc:
            raise DuplicateTokenError(fac.id, "LAB", token_num, today) from exc

        return token_num

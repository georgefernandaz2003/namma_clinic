import datetime
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError

from apps.visits.models import Visit, Token, FacilityDailyCounter, VisitStatusHistory
from apps.laboratory.models import DiagnosticOrder


class DomainServiceError(Exception):
    """Base exception for domain service layer operations."""
    pass


class TokenExhaustedError(DomainServiceError):
    pass


class CounterConflictError(DomainServiceError):
    pass


class UnauthorizedDomainAction(PermissionDenied):
    pass


class DomainValidationError(ValidationError):
    pass


def allocate_token(facility, counter_type, counter_date=None):
    """
    Allocates the next sequential token number for the given facility, counter type, and date.
    Maintains monotonicity and gapless issuance per facility/day using row-level locking.
    """
    if counter_date is None:
        counter_date = datetime.date.today()

    with transaction.atomic():
        counter, created = FacilityDailyCounter.objects.select_for_update().get_or_create(
            facility=facility,
            counter_type=counter_type,
            counter_date=counter_date,
            defaults={'last_token_number': 0}
        )

        # Invariant: counter must never be behind maximum existing tokens for this facility/day
        if counter_type == 'OPD':
            max_existing = Token.objects.filter(
                facility=facility,
                date=counter_date
            ).aggregate(max_val=models.Max('token_number'))['max_val'] or 0
            if counter.last_token_number < max_existing:
                counter.last_token_number = max_existing

        counter.last_token_number += 1
        counter.save(update_fields=['last_token_number', 'updated_at'])
        return counter.last_token_number


def issue_opd_token(visit, facility=None, token_date=None, priority=None):
    """
    Issues an authoritative OPD Token for a visit using FacilityDailyCounter.
    Strictly prohibits MAX(token_number) calculation.
    """
    if facility is None:
        facility = visit.facility
    if token_date is None:
        token_date = visit.opd_date or datetime.date.today()

    with transaction.atomic():
        # Check if visit already has a token
        existing_token = Token.objects.filter(visit=visit).first()
        if existing_token:
            return existing_token

        token_num = allocate_token(facility=facility, counter_type='OPD', counter_date=token_date)

        token = Token.objects.create(
            token_number=token_num,
            visit=visit,
            facility=facility,
            date=token_date,
            priority=priority or visit.priority or 'NORMAL',
            status='WAITING'
        )
        return token


def issue_lab_token(diagnostic_order, facility=None, order_date=None):
    """
    Issues a sequential LAB token using FacilityDailyCounter (LAB namespace).
    Idempotent: returns existing lab_token_number if already allocated.
    """
    if diagnostic_order.lab_token_number:
        return diagnostic_order.lab_token_number

    if facility is None:
        facility = diagnostic_order.facility
    if order_date is None:
        order_date = diagnostic_order.order_date or datetime.date.today()

    with transaction.atomic():
        token_num = allocate_token(facility=facility, counter_type='LAB', counter_date=order_date)
        diagnostic_order.lab_token_number = token_num
        diagnostic_order.save(update_fields=['lab_token_number'])
        return token_num


def call_next_queue_item(facility, requesting_user=None, target_queue="TRIAGE", staff=None, queue_name=None):
    """
    Atomically selects and claims the highest priority waiting patient for the user's role & facility today.
    Uses SELECT FOR UPDATE SKIP LOCKED to prevent concurrent double-claiming.
    """
    today = datetime.date.today()
    if queue_name is not None:
        target_queue = queue_name
    if requesting_user is None and staff is not None:
        requesting_user = getattr(staff, "user_account", getattr(staff, "user", None))
        if requesting_user is None and hasattr(staff, "person"):
            from apps.accounts.models import User
            requesting_user = User.objects.filter(staff_profile=staff).first()

    from apps.accounts.permissions import has_role_permission, can_access_facility, get_user_active_role_codes

    if not requesting_user or not requesting_user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if not has_role_permission(requesting_user, 'queue.call_next'):
        raise PermissionDenied("User does not have authorization to call next patient (queue.call_next required).")

    fac_id = getattr(facility, 'id', facility)
    if not can_access_facility(requesting_user, fac_id):
        raise PermissionDenied(f"User is not authorized for facility ID {fac_id}.")

    user_roles = get_user_active_role_codes(requesting_user)

    # Disallow Front Desk Officer from calling patients
    if "FRONT_DESK_OFFICER" in user_roles and "NURSE" not in user_roles and "DOCTOR" not in user_roles and not requesting_user.is_superuser:
        raise PermissionDenied("Front Desk Officer role is strictly prohibited from calling patients.")

    target_queue_upper = (target_queue or "TRIAGE").upper()
    if "NURSE" in user_roles and target_queue_upper != "TRIAGE" and not requesting_user.is_superuser:
        raise ValidationError("Nurses are only authorized to call patients from the TRIAGE queue.")
    elif "DOCTOR" in user_roles and target_queue_upper != "DOCTOR" and not requesting_user.is_superuser:
        raise ValidationError("Doctors are only authorized to call patients from the DOCTOR consultation queue.")

    with transaction.atomic():
        waiting_status_map = {
            'TRIAGE': ['WAITING_FOR_TRIAGE', 'WAITING'],
            'DOCTOR': ['WAITING_FOR_DOCTOR', 'WAITING', 'TRIAGED', 'DOCTOR_REVIEW', 'LAB_COMPLETED'],
        }
        active_status_map = {
            'TRIAGE': ('IN_TRIAGE', 'TRIAGE'),
            'DOCTOR': ('IN_CONSULTATION', 'DOCTOR'),
        }

        eligible_statuses = waiting_status_map.get(target_queue_upper, ['WAITING_FOR_TRIAGE'])
        next_status, queue_code = active_status_map.get(target_queue_upper, ('IN_TRIAGE', 'TRIAGE'))

        priority_case = models.Case(
            models.When(priority='EMERGENCY', then=models.Value(1)),
            models.When(priority='HIGH', then=models.Value(2)),
            models.When(priority='NORMAL', then=models.Value(3)),
            default=models.Value(4),
            output_field=models.IntegerField()
        )

        # Select and lock next waiting patient, skipping any row currently locked by another worker
        next_visit = Visit.objects.select_for_update(skip_locked=True).filter(
            facility_id=fac_id,
            opd_date=today,
            current_queue=target_queue_upper,
            status__in=eligible_statuses
        ).annotate(priority_weight=priority_case).order_by('priority_weight', 'arrival_time').first()

        if not next_visit:
            raise ValueError(f"No waiting patients in {target_queue_upper} queue for today.")

        from_stat = next_visit.status
        next_visit.status = next_status
        now = timezone.now()
        if target_queue_upper == 'DOCTOR':
            next_visit.consultation_start_time = now
            next_visit.assigned_doctor = requesting_user
        elif target_queue_upper == 'TRIAGE':
            next_visit.triage_start_time = now

        next_visit.save()

        # Update associated Token status to IN_PROGRESS
        if hasattr(next_visit, 'token') and next_visit.token:
            next_visit.token.status = 'IN_PROGRESS'
            next_visit.token.save(update_fields=['status'])

        # Audit History
        VisitStatusHistory.objects.create(
            visit=next_visit,
            from_status=from_stat,
            to_status=next_status,
            queue=queue_code,
            performed_by=requesting_user,
            performed_by_role=",".join(sorted(user_roles)),
            notes=f"Patient called by {requesting_user.get_full_name() or requesting_user.username} for {target_queue_upper}"
        )

        return next_visit


def transition_visit_status(visit, to_status, requesting_user=None, target_queue=None, notes="", staff=None):
    """
    Transitions visit workflow status with validation, triage invariant enforcement, and audit history.
    """
    today = datetime.date.today()
    if requesting_user is None and staff is not None:
        requesting_user = getattr(staff, "user_account", getattr(staff, "user", None))
        if requesting_user is None and hasattr(staff, "person"):
            from apps.accounts.models import User
            requesting_user = User.objects.filter(staff_profile=staff).first()

    from apps.accounts.permissions import has_role_permission, can_access_facility, get_user_active_role_codes

    if not requesting_user or not requesting_user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if not has_role_permission(requesting_user, 'queue.transition'):
        raise PermissionDenied("User does not have authorization for queue transitions (queue.transition required).")

    if not can_access_facility(requesting_user, visit.facility_id):
        raise PermissionDenied(f"User is not authorized for facility ID {visit.facility_id}.")

    user_roles = get_user_active_role_codes(requesting_user)

    # Disallow Front Desk Officer from advancing patient through clinical stages
    if "FRONT_DESK_OFFICER" in user_roles and "NURSE" not in user_roles and "DOCTOR" not in user_roles and not requesting_user.is_superuser:
        if to_status in ['IN_TRIAGE', 'TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'WAITING_FOR_PHARMACY', 'IN_PHARMACY']:
            raise PermissionDenied("Front Desk Officer role is strictly prohibited from transitioning clinical workflow states.")

    # Guard historical date modification
    if visit.opd_date != today and not requesting_user.is_superuser:
        raise ValidationError("Historical visit queue records cannot be transitioned.")

    # Validate allowed transitions
    allowed_transitions = {
        'WAITING_FOR_TRIAGE': ['IN_TRIAGE', 'WAITING_FOR_DOCTOR', 'CANCELLED', 'NO_SHOW'],
        'IN_TRIAGE': ['TRIAGED', 'WAITING_FOR_DOCTOR', 'CANCELLED'],
        'TRIAGED': ['WAITING_FOR_DOCTOR', 'IN_CONSULTATION'],
        'WAITING_FOR_DOCTOR': ['IN_CONSULTATION', 'CANCELLED'],
        'IN_CONSULTATION': ['DOCTOR_REVIEW', 'WAITING_FOR_LAB', 'IN_LAB', 'LAB_COMPLETED', 'WAITING_FOR_PHARMACY', 'COMPLETED'],
        'DOCTOR_REVIEW': ['IN_CONSULTATION', 'WAITING_FOR_PHARMACY', 'COMPLETED'],
        'WAITING_FOR_LAB': ['IN_LAB', 'LAB_COMPLETED'],
        'IN_LAB': ['LAB_COMPLETED'],
        'LAB_COMPLETED': ['DOCTOR_REVIEW', 'IN_CONSULTATION'],
        'WAITING_FOR_PHARMACY': ['IN_PHARMACY', 'COMPLETED'],
        'IN_PHARMACY': ['COMPLETED'],
        'COMPLETED': [],
        'CANCELLED': [],
        'NO_SHOW': [],
    }

    current_stat = visit.status
    allowed = allowed_transitions.get(current_stat, [])
    if to_status not in allowed and not requesting_user.is_superuser:
        raise ValidationError(f"Invalid transition from {current_stat} to {to_status}.")

    # Invariant: Advancing to WAITING_FOR_DOCTOR or IN_CONSULTATION requires triage vitals
    # (unless SRV_TRIAGE is disabled at the facility)
    if to_status in ['WAITING_FOR_DOCTOR', 'IN_CONSULTATION']:
        from apps.facilities.models import FacilityService
        triage_active = FacilityService.objects.filter(
            facility_id=visit.facility_id,
            service__code='SRV_TRIAGE',
            is_available=True
        ).exists()
        if triage_active:
            from apps.triage.models import TriageVitals
            has_vitals = TriageVitals.objects.filter(visit=visit).exists() or hasattr(visit, 'triage')
            if not has_vitals:
                raise ValidationError("Cannot advance visit to DOCTOR queue without recorded triage vitals.")

    from_status = visit.status
    now = timezone.now()

    with transaction.atomic():
        visit.status = to_status
        target_q = (target_queue or visit.current_queue).upper()

        if to_status == 'IN_TRIAGE':
            visit.triage_start_time = now
            visit.current_queue = 'TRIAGE'
        elif to_status in ['TRIAGED', 'WAITING_FOR_DOCTOR']:
            visit.triage_end_time = now
            visit.current_queue = 'DOCTOR'
            visit.status = 'WAITING_FOR_DOCTOR'
        elif to_status == 'DOCTOR_REVIEW':
            visit.current_queue = 'DOCTOR'
            visit.status = 'DOCTOR_REVIEW'
        elif to_status == 'COMPLETED' or target_q == 'COMPLETED':
            visit.completed_time = now
            visit.current_queue = 'COMPLETED'
            visit.status = 'COMPLETED'
        elif to_status == 'WAITING_FOR_PHARMACY':
            visit.consultation_end_time = now
            visit.current_queue = 'PHARMACY'

        visit.save()

        VisitStatusHistory.objects.create(
            visit=visit,
            from_status=from_status,
            to_status=visit.status,
            queue=visit.current_queue,
            performed_by=requesting_user,
            performed_by_role=",".join(sorted(user_roles)),
            notes=notes or f"Transitioned from {from_status} to {visit.status}"
        )

        return visit


def void_opd_token(visit, requesting_user=None, reason="Duplicate token voided", staff=None, facility=None):
    """
    Voids an eligible untriaged duplicate token within 30 minutes of arrival.
    Non-destructive: updates status to CANCELLED and preserves audit trail.
    """
    if requesting_user is None and staff is not None:
        requesting_user = getattr(staff, "user_account", getattr(staff, "user", None))
        if requesting_user is None and hasattr(staff, "person"):
            from apps.accounts.models import User
            requesting_user = User.objects.filter(staff_profile=staff).first()

    if facility is not None:
        target_fac_id = getattr(facility, "id", facility)
        if visit.facility_id != target_fac_id:
            raise PermissionDenied("Visit does not belong to the specified facility.")

    from apps.accounts.permissions import has_role_permission, can_access_facility, get_user_active_role_codes

    if not requesting_user or not requesting_user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if not has_role_permission(requesting_user, 'queue.void'):
        raise PermissionDenied("User does not have authorization to void queue tokens (queue.void required).")

    if not can_access_facility(requesting_user, visit.facility_id):
        raise PermissionDenied(f"User is not authorized for facility ID {visit.facility_id}.")

    user_roles = get_user_active_role_codes(requesting_user)

    if visit.status == 'CANCELLED':
        raise ValidationError("Visit token is already voided.")

    # Rule 1: Must be untriaged and in TRIAGE queue
    if visit.status not in ['WAITING_FOR_TRIAGE', 'WAITING'] or visit.current_queue != 'TRIAGE':
        raise ValidationError("Cannot void a visit: only eligible untriaged visits may be voided.")

    # Rule 2: 30-minute duplicate-void window
    if visit.arrival_time:
        elapsed_seconds = (timezone.now() - visit.arrival_time).total_seconds()
        if elapsed_seconds > 30 * 60:
            raise ValidationError("Token void window has expired (must be within 30-minute window of arrival).")

    from_stat = visit.status
    with transaction.atomic():
        visit.status = 'CANCELLED'
        # Do not set current_queue to COMPLETED because models.py requires status=COMPLETED for current_queue=COMPLETED
        visit.completed_time = timezone.now()
        visit.save()

        if hasattr(visit, 'token') and visit.token:
            visit.token.status = 'CANCELLED'
            visit.token.save(update_fields=['status'])

        VisitStatusHistory.objects.create(
            visit=visit,
            from_status=from_stat,
            to_status='CANCELLED',
            queue=visit.current_queue,
            performed_by=requesting_user,
            performed_by_role=",".join(sorted(user_roles)),
            notes=reason or "Duplicate token voided by front desk."
        )

        return visit


def get_queue_history_summary(facility=None, target_date=None, facility_id=None, accessible_facility_ids=None):
    """
    Returns date-wise OPD summary table derived directly from PostgreSQL.
    If target_date is given, returns a single summary dict for that date.
    Otherwise returns list of daily summaries (last 30 days).
    """
    fac = facility or facility_id
    fac_id = getattr(fac, 'id', fac) if fac is not None else None

    # Handle case where date was passed as second positional argument
    if target_date is None and isinstance(accessible_facility_ids, datetime.date):
        target_date = accessible_facility_ids
        accessible_facility_ids = None
    elif isinstance(target_date, (list, set, tuple)):
        # In case accessible_facility_ids was passed second
        accessible_facility_ids = target_date
        target_date = None

    queryset = Visit.objects.all()
    if fac_id:
        queryset = queryset.filter(facility_id=fac_id)
    if accessible_facility_ids is not None:
        queryset = queryset.filter(facility_id__in=accessible_facility_ids)

    if target_date:
        queryset = queryset.filter(opd_date=target_date)
        aggr = queryset.aggregate(
            total_patients=models.Count('id'),
            waiting_triage=models.Count('id', filter=models.Q(status__in=['WAITING_FOR_TRIAGE', 'WAITING'])),
            in_triage=models.Count('id', filter=models.Q(status='IN_TRIAGE')),
            waiting_doctor=models.Count('id', filter=models.Q(status__in=['WAITING_FOR_DOCTOR', 'TRIAGED', 'DOCTOR_REVIEW'])),
            in_consultation=models.Count('id', filter=models.Q(status='IN_CONSULTATION')),
            completed_patients=models.Count('id', filter=models.Q(status='COMPLETED')),
            cancelled_patients=models.Count('id', filter=models.Q(status='CANCELLED'))
        )
        return {
            'opd_date': str(target_date),
            'total_patients': aggr['total_patients'],
            'waiting_triage': aggr['waiting_triage'],
            'waiting_doctor': aggr['waiting_doctor'],
            'completed_patients': aggr['completed_patients'],
            'cancelled_patients': aggr['cancelled_patients']
        }

    cutoff_date = datetime.date.today() - datetime.timedelta(days=30)
    queryset = queryset.filter(opd_date__gte=cutoff_date)

    return list(queryset.values('opd_date').annotate(
        total_patients=models.Count('id'),
        waiting_triage=models.Count('id', filter=models.Q(status__in=['WAITING_FOR_TRIAGE', 'WAITING'])),
        in_triage=models.Count('id', filter=models.Q(status='IN_TRIAGE')),
        waiting_doctor=models.Count('id', filter=models.Q(status__in=['WAITING_FOR_DOCTOR', 'TRIAGED', 'DOCTOR_REVIEW'])),
        in_consultation=models.Count('id', filter=models.Q(status='IN_CONSULTATION')),
        completed_patients=models.Count('id', filter=models.Q(status='COMPLETED')),
        cancelled_patients=models.Count('id', filter=models.Q(status='CANCELLED'))
    ).order_by('-opd_date'))

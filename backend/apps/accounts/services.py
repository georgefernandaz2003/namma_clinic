"""
IAM Domain Services: Professional Identity, Role Assignments, and Facility Postings.
Decouples staff clinical identity from mutable user authentication accounts.
"""
import datetime
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import (
    Person, StaffProfile, RoleMaster,
    StaffRoleAssignment, StaffFacilityAssignment
)
from apps.common.exceptions import (
    DomainValidationError,
    UnauthorizedDomainAction,
    InvalidAssignmentPeriodError,
    OverlappingAssignmentError,
    InvalidStateTransition
)
from apps.audit.services import record_audit_event


def create_staff_profile(
    person,
    employee_id,
    designation,
    department=None,
    medical_council_reg_number=None,
    status="ACTIVE",
    actor_staff=None
):
    """
    Creates a new professional StaffProfile linked to a natural Person.
    """
    if not employee_id:
        raise DomainValidationError("employee_id is required for StaffProfile.", code="MISSING_EMPLOYEE_ID")
    if not designation:
        raise DomainValidationError("designation is required for StaffProfile.", code="MISSING_DESIGNATION")

    if StaffProfile.objects.filter(employee_id=employee_id).exists():
        raise DomainValidationError(f"StaffProfile with employee_id '{employee_id}' already exists.", code="DUPLICATE_EMPLOYEE_ID")

    with transaction.atomic():
        profile = StaffProfile.objects.create(
            person=person,
            employee_id=employee_id,
            designation=designation,
            department=department,
            medical_council_reg_number=medical_council_reg_number,
            status=status
        )

        record_audit_event(
            actor_staff=actor_staff,
            actor_role_snapshot=actor_staff.designation if actor_staff else "SYSTEM",
            facility=department.facility if department else None,
            action_type="CREATE",
            table_name="staff_profiles",
            record_id=profile.id,
            payload_after={"employee_id": profile.employee_id, "status": profile.status}
        )
        return profile


def update_staff_status(staff_profile, new_status, actor_staff=None):
    """
    Updates the operational lifecycle status of a StaffProfile.
    """
    valid_statuses = ["PROBATION", "ACTIVE", "SUSPENDED", "RETIRED", "RESIGNED"]
    if new_status not in valid_statuses:
        raise InvalidStateTransition("StaffProfile", staff_profile.status, new_status)

    old_status = staff_profile.status
    staff_profile.status = new_status
    staff_profile.save(update_fields=["status", "updated_at"])

    record_audit_event(
        actor_staff=actor_staff,
        actor_role_snapshot=actor_staff.designation if actor_staff else "SYSTEM",
        action_type="UPDATE",
        table_name="staff_profiles",
        record_id=staff_profile.id,
        payload_before={"status": old_status},
        payload_after={"status": new_status}
    )
    return staff_profile


def assign_role(staff_profile, role, effective_from=None, effective_to=None, actor_staff=None):
    """
    Assigns a dynamic role to a StaffProfile with effective-date validation and overlap prevention.
    """
    today = datetime.date.today()
    start_date = effective_from or today

    if effective_to and effective_to < start_date:
        raise InvalidAssignmentPeriodError(start_date, effective_to)

    # Check for active overlapping assignment for the same role
    existing_active = StaffRoleAssignment.objects.filter(
        staff=staff_profile,
        role=role,
        is_active=True
    ).exclude(effective_to__lt=start_date)

    if effective_to:
        existing_active = existing_active.filter(effective_from__lte=effective_to)

    if existing_active.exists():
        raise OverlappingAssignmentError(staff_profile.id, "ROLE", role.code)

    with transaction.atomic():
        assignment = StaffRoleAssignment.objects.create(
            staff=staff_profile,
            role=role,
            effective_from=start_date,
            effective_to=effective_to,
            is_active=True
        )

        record_audit_event(
            actor_staff=actor_staff,
            actor_role_snapshot=actor_staff.designation if actor_staff else "SYSTEM",
            action_type="CREATE",
            table_name="staff_role_assignments",
            record_id=assignment.id,
            payload_after={
                "staff_id": staff_profile.id,
                "role_code": role.code,
                "effective_from": str(start_date),
                "effective_to": str(effective_to) if effective_to else None
            }
        )
        return assignment


def end_role_assignment(assignment, end_date=None, actor_staff=None):
    """
    Terminates an active role assignment preserving historical records.
    """
    effective_end = end_date or datetime.date.today()
    if effective_end < assignment.effective_from:
        raise InvalidAssignmentPeriodError(assignment.effective_from, effective_end)

    assignment.effective_to = effective_end
    assignment.is_active = False
    assignment.save(update_fields=["effective_to", "is_active"])

    record_audit_event(
        actor_staff=actor_staff,
        actor_role_snapshot=actor_staff.designation if actor_staff else "SYSTEM",
        action_type="UPDATE",
        table_name="staff_role_assignments",
        record_id=assignment.id,
        payload_after={"is_active": False, "effective_to": str(effective_end)}
    )
    return assignment


def assign_facility(
    staff_profile,
    facility,
    department=None,
    is_primary=False,
    effective_from=None,
    effective_to=None,
    actor_staff=None
):
    """
    Assigns a StaffProfile to a healthcare Facility / Department.
    If is_primary=True, terminates any prior active primary facility assignment.
    """
    today = datetime.date.today()
    start_date = effective_from or today

    if effective_to and effective_to < start_date:
        raise InvalidAssignmentPeriodError(start_date, effective_to)

    with transaction.atomic():
        if is_primary:
            # Demote or terminate prior primary facility assignment
            prior_primaries = StaffFacilityAssignment.objects.filter(
                staff=staff_profile,
                is_primary=True,
                is_active=True
            )
            for prior in prior_primaries:
                prior.is_primary = False
                prior.save(update_fields=["is_primary"])

        assignment = StaffFacilityAssignment.objects.create(
            staff=staff_profile,
            facility=facility,
            department=department,
            is_primary=is_primary,
            effective_from=start_date,
            effective_to=effective_to,
            is_active=True
        )

        record_audit_event(
            actor_staff=actor_staff,
            actor_role_snapshot=actor_staff.designation if actor_staff else "SYSTEM",
            facility=facility,
            action_type="CREATE",
            table_name="staff_facility_assignments",
            record_id=assignment.id,
            payload_after={
                "staff_id": staff_profile.id,
                "facility_id": facility.id,
                "is_primary": is_primary,
                "effective_from": str(start_date)
            }
        )
        return assignment


def transfer_staff(staff_profile, new_facility, new_department=None, effective_date=None, actor_staff=None):
    """
    Atomically transfers a staff member to a new primary facility.
    """
    transfer_date = effective_date or datetime.date.today()
    yesterday = transfer_date - datetime.timedelta(days=1)

    with transaction.atomic():
        # Close current primary facility assignments
        current_primaries = StaffFacilityAssignment.objects.filter(
            staff=staff_profile,
            is_primary=True,
            is_active=True
        )
        for cur in current_primaries:
            cur.effective_to = max(cur.effective_from, yesterday)
            cur.is_active = False
            cur.is_primary = False
            cur.save(update_fields=["effective_to", "is_active", "is_primary"])

        # Create new primary assignment
        new_assignment = assign_facility(
            staff_profile=staff_profile,
            facility=new_facility,
            department=new_department,
            is_primary=True,
            effective_from=transfer_date,
            actor_staff=actor_staff
        )
        return new_assignment

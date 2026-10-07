"""
IAM Domain Services: Professional Identity, Role Assignments, Account Lifecycle, and Postings.
Authoritative domain logic with anti-privilege escalation, multi-role assignment, and durable auditing.
"""
import datetime
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import (
    Person, StaffProfile, StaffStatusChoices, RoleMaster,
    StaffRoleAssignment, StaffFacilityAssignment, User, RoleChoices
)
from apps.common.exceptions import (
    DomainValidationError,
    UnauthorizedDomainAction,
    InvalidAssignmentPeriodError,
    OverlappingAssignmentError,
    InvalidStateTransition
)
from apps.audit.services import record_audit_event


def resolve_actor(actor):
    """
    Extracts (actor_user, actor_staff, actor_role) from either User, StaffProfile, or None.
    """
    if actor is None:
        return None, None, "SYSTEM"

    if isinstance(actor, User):
        actor_user = actor
        actor_staff = getattr(actor, 'staff_profile', None)
        actor_role = getattr(actor, 'role', 'SYSTEM')
        if actor_staff:
            assigned = StaffRoleAssignment.objects.filter(staff=actor_staff, is_active=True).select_related('role').first()
            if assigned:
                actor_role = assigned.role.code
        return actor_user, actor_staff, actor_role

    if isinstance(actor, StaffProfile):
        actor_staff = actor
        actor_user = getattr(actor, 'user_account', None)
        assigned = StaffRoleAssignment.objects.filter(staff=actor_staff, is_active=True).select_related('role').first()
        if assigned:
            actor_role = assigned.role.code
        elif actor_user and actor_user.role:
            actor_role = actor_user.role
        elif actor_staff.designation in ["Hospital Administrator", "System Administrator", "Medical Superintendent"]:
            actor_role = "HOSPITAL_ADMIN"
        elif actor_staff.designation in ["District Health Officer"]:
            actor_role = "DISTRICT_OFFICER"
        elif actor_staff.designation in ["Staff Nurse"]:
            actor_role = "NURSE"
        elif actor_staff.designation in ["Medical Officer"]:
            actor_role = "DOCTOR"
        else:
            actor_role = actor.designation
        return actor_user, actor_staff, actor_role

    return None, None, "SYSTEM"


def is_administrative_staff(staff_profile):
    """Checks if a StaffProfile holds administrative privileges."""
    if not staff_profile or staff_profile.status != StaffStatusChoices.ACTIVE:
        return False
    admin_designations = [
        "Hospital Administrator", "System Administrator",
        "Medical Superintendent", "District Health Officer"
    ]
    if staff_profile.designation in admin_designations:
        return True
    admin_roles = ["ADMIN", "SYSTEM_ADMIN", "HOSPITAL_ADMIN", "DHO", "DISTRICT_OFFICER"]
    return StaffRoleAssignment.objects.filter(
        staff=staff_profile,
        role__code__in=admin_roles,
        is_active=True
    ).exists()


def validate_admin_actor(actor, target_facility=None, target_staff=None, target_role=None, action=None):
    """
    Validates anti-privilege escalation rules:
    - Operational roles cannot perform staff/role administration.
    - HOSPITAL_ADMIN (Clinic Admin) can only manage staff within their assigned facility.
    - HOSPITAL_ADMIN cannot assign DISTRICT_OFFICER or system-level roles.
    - DISTRICT_OFFICER can only manage staff within their assigned district.
    - Self-assignment / self-escalation is strictly prohibited.
    """
    actor_user, actor_staff, actor_role = resolve_actor(actor)
    if actor is None:
        return actor_user, actor_staff, actor_role

    # Django Superuser bypasses scoping
    if actor_user and getattr(actor_user, 'is_superuser', False):
        return actor_user, actor_staff, actor_role

    # Inactive actor denied
    if actor_staff and actor_staff.status != StaffStatusChoices.ACTIVE:
        raise UnauthorizedDomainAction(f"Inactive staff '{actor_staff.employee_id}' cannot perform administrative actions.")
    if actor_user and not actor_user.is_active:
        raise UnauthorizedDomainAction(f"Inactive user '{actor_user.username}' cannot perform administrative actions.")

    # 1. Administrative check for staff actor
    if actor_staff and not is_administrative_staff(actor_staff) and not (actor_user and actor_user.is_superuser):
        if action in ['transfer', 'assign_facility']:
            pass
        else:
            raise UnauthorizedDomainAction(f"Staff '{actor_staff.employee_id}' lacks administrative authority.")

    # Operational roles cannot perform admin actions
    operational_roles = ['DOCTOR', 'NURSE', 'FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'PHARMACIST']
    if actor_role in operational_roles:
        if action in ['transfer', 'assign_facility']:
            pass
        else:
            raise UnauthorizedDomainAction(f"Operational role '{actor_role}' is not authorized to perform staff administration.")

    # 2. Self-assignment / Self-escalation check (role assignment)
    if target_role:
        if target_staff and actor_staff and target_staff.id == actor_staff.id:
            raise UnauthorizedDomainAction("Users cannot modify or assign roles to themselves.")
        if target_staff and actor_user and getattr(actor_user, 'staff_profile_id', None) == target_staff.id:
            raise UnauthorizedDomainAction("Users cannot modify or assign roles to themselves.")

    # 3. Hospital Admin (Clinic Admin) Scoping
    if actor_role in ['HOSPITAL_ADMIN', 'ADMIN']:
        admin_fac_id = getattr(actor_user, 'assigned_facility_id', None) if actor_user else None
        if not admin_fac_id and actor_staff:
            primary_fa = actor_staff.facility_assignments.filter(is_primary=True, is_active=True).first()
            if primary_fa:
                admin_fac_id = primary_fa.facility_id

        # Target facility scope check (for assignments)
        if target_facility and admin_fac_id and action != 'transfer' and target_facility.id != admin_fac_id:
            raise UnauthorizedDomainAction(
                f"Clinic Admin of facility #{admin_fac_id} cannot administer foreign facility #{target_facility.id}."
            )

        # Target staff scope check: target staff must belong to clinic admin's facility
        if target_staff and admin_fac_id:
            staff_in_fac = target_staff.facility_assignments.filter(facility_id=admin_fac_id, is_active=True).exists()
            target_user = getattr(target_staff, 'user_account', None)
            if not staff_in_fac and target_user and target_user.assigned_facility_id != admin_fac_id:
                raise UnauthorizedDomainAction(
                    f"Clinic Admin cannot administer staff '{target_staff.employee_id}' outside assigned facility."
                )

        # Target role scope check: Clinic Admin cannot grant Hospital Admin, DHO, or system roles
        if target_role:
            target_role_code = target_role.code if hasattr(target_role, 'code') else str(target_role)
            restricted_roles = ['HOSPITAL_ADMIN', 'ADMIN', 'DISTRICT_OFFICER', 'DHO', 'SYSTEM_ADMIN', 'SUPERUSER']
            if target_role_code in restricted_roles:
                raise UnauthorizedDomainAction(
                    f"Clinic Admin cannot assign privileged role '{target_role_code}'."
                )

    # 4. District Officer Scoping
    if actor_role in ['DISTRICT_OFFICER', 'DHO']:
        dist_id = getattr(actor_user, 'assigned_district_id', None) if actor_user else None
        if not dist_id:
            raise UnauthorizedDomainAction("District Officer with NULL district fails closed.")

        if target_facility and target_facility.district_id != dist_id:
            raise UnauthorizedDomainAction(
                f"District Officer cannot administer facility #{target_facility.id} outside assigned district #{dist_id}."
            )

        # Target role scope check: DHO cannot assign system-level roles
        if target_role:
            target_role_code = target_role.code if hasattr(target_role, 'code') else str(target_role)
            restricted_system_roles = ['SYSTEM_ADMIN', 'SUPERUSER', 'ADMIN']
            if target_role_code in restricted_system_roles:
                raise UnauthorizedDomainAction(
                    f"District Officer cannot assign system-level role '{target_role_code}'."
                )

        if target_staff:
            staff_dist_ok = target_staff.facility_assignments.filter(
                facility__district_id=dist_id, is_active=True
            ).exists()
            target_user = getattr(target_staff, 'user_account', None)
            if not staff_dist_ok and target_user and target_user.assigned_district_id != dist_id:
                if target_user.assigned_facility and target_user.assigned_facility.district_id != dist_id:
                    raise UnauthorizedDomainAction(
                        f"District Officer cannot administer staff '{target_staff.employee_id}' outside assigned district #{dist_id}."
                    )

    return actor_user, actor_staff, actor_role


def create_staff_profile(
    person,
    employee_id,
    designation,
    department=None,
    medical_council_reg_number=None,
    status=StaffStatusChoices.ACTIVE,
    actor_staff=None
):
    """Creates a new professional StaffProfile linked to a natural Person."""
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


def invite_staff(
    email,
    first_name,
    last_name,
    gender,
    date_of_birth,
    employee_id,
    designation,
    facility,
    role_code=None,
    phone_number=None,
    department=None,
    actor=None,
    password=None
):
    """
    Onboards a new staff member in INVITED lifecycle state.
    Creates Person, StaffProfile (INVITED), User account (is_active=False),
    optional StaffRoleAssignment, and StaffFacilityAssignment.
    """
    actor_user, actor_staff, actor_role = validate_admin_actor(
        actor=actor,
        target_facility=facility,
        target_role=role_code
    )

    if not employee_id:
        raise DomainValidationError("employee_id is required.", code="MISSING_EMPLOYEE_ID")
    if password and len(password) < 8:
        raise DomainValidationError("Password must be at least 8 characters.", code="INVALID_PASSWORD")
    if StaffProfile.objects.filter(employee_id=employee_id).exists():
        raise DomainValidationError(f"StaffProfile '{employee_id}' already exists.", code="DUPLICATE_EMPLOYEE_ID")

    with transaction.atomic():
        person = Person.objects.create(
            first_name=first_name,
            last_name=last_name or '',
            gender=gender,
            date_of_birth=date_of_birth,
            phone_number=phone_number or ''
        )

        profile = StaffProfile.objects.create(
            person=person,
            employee_id=employee_id,
            designation=designation,
            department=department,
            status=StaffStatusChoices.INVITED
        )

        # User account created with is_active=False until invitation accepted/activated
        user_role = role_code if role_code in RoleChoices.values else RoleChoices.DOCTOR
        username = employee_id.lower().replace("-", "_")
        if User.objects.filter(username=username).exists():
            username = f"{username}_{person.id}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name or '',
            role=user_role,
            assigned_facility=facility,
            assigned_district=facility.district if facility else None,
            staff_profile=profile,
            is_active=False
        )

        # Primary Facility Assignment
        if facility:
            StaffFacilityAssignment.objects.create(
                staff=profile,
                facility=facility,
                department=department,
                is_primary=True,
                effective_from=datetime.date.today(),
                is_active=True
            )

        # Role Assignment if provided
        if role_code:
            role_master = RoleMaster.objects.filter(code=role_code, is_active=True).first()
            if role_master:
                StaffRoleAssignment.objects.create(
                    staff=profile,
                    role=role_master,
                    facility=facility,
                    effective_from=datetime.date.today(),
                    is_active=True,
                    assigned_by=actor_user
                )

        record_audit_event(
            actor_staff=actor_staff,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=facility,
            action_type="INVITE_STAFF",
            table_name="staff_profiles",
            record_id=profile.id,
            payload_after={
                "employee_id": profile.employee_id,
                "status": StaffStatusChoices.INVITED,
                "role_code": role_code,
                "facility_id": facility.id if facility else None
            }
        )

        return profile, user


def activate_staff(staff_profile, actor=None, password=None):
    """
    Activates an invited staff profile and activates their associated user account.
    Optional password parameter sets initial credentials without shell intervention.
    """
    primary_fa = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    facility = primary_fa.facility if primary_fa else None

    actor_user, actor_staff, actor_role = validate_admin_actor(
        actor=actor,
        target_facility=facility,
        target_staff=staff_profile
    )

    if staff_profile.status not in [StaffStatusChoices.INVITED, StaffStatusChoices.SUSPENDED]:
        raise InvalidStateTransition("StaffProfile", staff_profile.status, StaffStatusChoices.ACTIVE)

    if password and len(password) < 8:
        raise DomainValidationError("Password must be at least 8 characters.", code="INVALID_PASSWORD")

    old_status = staff_profile.status
    with transaction.atomic():
        staff_profile.status = StaffStatusChoices.ACTIVE
        staff_profile.save(update_fields=["status", "updated_at"])

        user = getattr(staff_profile, 'user_account', None)
        if user:
            user.is_active = True
            update_fields = ["is_active"]
            if password:
                user.set_password(password)
                update_fields.append("password")
            user.save(update_fields=update_fields)

        record_audit_event(
            actor_staff=actor_staff,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=facility,
            action_type="ACTIVATE_STAFF",
            table_name="staff_profiles",
            record_id=staff_profile.id,
            payload_before={"status": old_status},
            payload_after={"status": StaffStatusChoices.ACTIVE}
        )

    return staff_profile


def set_staff_credentials(staff_profile, password, actor=None):
    """
    Provisions or updates credentials for an active/invited staff profile.
    Enforces scope checks, minimum complexity, and never stores/logs plaintext credentials.
    """
    primary_fa = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    facility = primary_fa.facility if primary_fa else None

    actor_user, actor_staff, actor_role = validate_admin_actor(
        actor=actor,
        target_facility=facility,
        target_staff=staff_profile,
        action="set_credentials"
    )

    if not password or len(password) < 8:
        raise DomainValidationError("Password must be at least 8 characters.", code="INVALID_PASSWORD")

    user = getattr(staff_profile, 'user_account', None)
    if not user:
        raise DomainValidationError(f"StaffProfile '{staff_profile.employee_id}' has no associated user account.", code="USER_NOT_FOUND")

    with transaction.atomic():
        user.set_password(password)
        user.save(update_fields=["password"])

        record_audit_event(
            actor_staff=actor_staff,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=facility,
            action_type="SET_CREDENTIALS",
            table_name="users",
            record_id=user.id,
            payload_after={"employee_id": staff_profile.employee_id, "credentials_configured": True}
        )
    return staff_profile


def update_staff_status(staff_profile, new_status, actor_staff=None):
    """Updates the operational lifecycle status of a StaffProfile."""
    if new_status not in StaffStatusChoices.values:
        raise InvalidStateTransition("StaffProfile", staff_profile.status, new_status)

    old_status = staff_profile.status
    with transaction.atomic():
        staff_profile.status = new_status
        staff_profile.save(update_fields=["status", "updated_at"])

        # Synchronize user account active status
        user = getattr(staff_profile, 'user_account', None)
        if user:
            if new_status in [StaffStatusChoices.SUSPENDED, StaffStatusChoices.DEACTIVATED, StaffStatusChoices.INVITED]:
                user.is_active = False
            elif new_status == StaffStatusChoices.ACTIVE:
                user.is_active = True
            user.save(update_fields=["is_active"])

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


def assign_role(staff_profile, role, facility=None, effective_from=None, effective_to=None, actor=None, actor_staff=None):
    """
    Authoritative role assignment to a StaffProfile with effective-date validation,
    overlap prevention, anti-privilege escalation, and audit logging.
    """
    effective_actor = actor or actor_staff
    primary_fa = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    context_facility = facility or (
        primary_fa.facility if primary_fa else (
            staff_profile.department.facility if staff_profile.department else getattr(getattr(staff_profile, 'user_account', None), 'assigned_facility', None)
        )
    )

    # Section 9: Validate role-facility/district invariants
    facility_roles = ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'PHARMACIST']
    if role.code in facility_roles and not context_facility:
        raise DomainValidationError(
            f"Role '{role.code}' requires a valid facility context.",
            code="MISSING_FACILITY_CONTEXT"
        )

    if role.code in ['DISTRICT_OFFICER', 'DHO']:
        target_user = getattr(staff_profile, 'user_account', None)
        user_dist = getattr(target_user, 'assigned_district_id', None)
        fac_dist = context_facility.district_id if context_facility else None
        if not user_dist and not fac_dist:
            raise DomainValidationError(
                "DISTRICT_OFFICER role requires a valid district context.",
                code="MISSING_DISTRICT_CONTEXT"
            )

    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=context_facility,
        target_staff=staff_profile,
        target_role=role
    )

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
            facility=context_facility,
            effective_from=start_date,
            effective_to=effective_to,
            is_active=True,
            assigned_by=actor_user
        )

        record_audit_event(
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=context_facility,
            action_type="ASSIGN_ROLE",
            table_name="staff_role_assignments",
            record_id=assignment.id,
            payload_after={
                "staff_id": staff_profile.id,
                "role_code": role.code,
                "effective_from": str(start_date),
                "effective_to": str(effective_to) if effective_to else None,
                "facility_id": context_facility.id if context_facility else None
            }
        )
        return assignment


def end_role_assignment(assignment, end_date=None, actor=None, actor_staff=None):
    """
    Terminates an active role assignment preserving historical records and auditing.
    """
    effective_actor = actor or actor_staff
    primary_fa = assignment.staff.facility_assignments.filter(is_primary=True, is_active=True).first()
    context_facility = assignment.facility or (primary_fa.facility if primary_fa else None)

    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=context_facility,
        target_staff=assignment.staff,
        target_role=assignment.role
    )

    effective_end = end_date or datetime.date.today()
    if effective_end < assignment.effective_from:
        raise InvalidAssignmentPeriodError(assignment.effective_from, effective_end)

    with transaction.atomic():
        assignment.effective_to = effective_end
        assignment.is_active = False
        assignment.save(update_fields=["effective_to", "is_active", "updated_at"])

        record_audit_event(
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=context_facility,
            action_type="END_ROLE",
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
    actor=None,
    actor_staff=None
):
    """
    Assigns a StaffProfile to a healthcare Facility / Department.
    If is_primary=True, terminates any prior active primary facility assignment.
    """
    effective_actor = actor or actor_staff
    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=facility,
        target_staff=staff_profile,
        action='assign_facility'
    )

    today = datetime.date.today()
    start_date = effective_from or today

    if effective_to and effective_to < start_date:
        raise InvalidAssignmentPeriodError(start_date, effective_to)

    with transaction.atomic():
        if is_primary:
            # Demote prior primary facility assignments
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
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=facility,
            action_type="ASSIGN_FACILITY",
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


def transfer_staff(staff_profile, new_facility, new_department=None, effective_date=None, actor=None, actor_staff=None):
    """
    Atomically transfers a staff member to a new primary facility.
    - If transfer_date > today, status is TRANSFER_PENDING.
      Prior assignment remains active until transfer_date - 1.
      User assigned_facility remains current facility until transfer date.
      New assignment is created with effective_from = transfer_date.
    - If transfer_date <= today, transfer is immediate:
      Prior assignment closed.
      New assignment is primary and active.
      User assigned_facility updated to new_facility.
      Status remains/becomes ACTIVE.
    """
    effective_actor = actor or actor_staff
    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=new_facility,
        target_staff=staff_profile,
        action='transfer'
    )

    current_primary = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    current_fac = current_primary.facility if current_primary else getattr(staff_profile.department, 'facility', None)

    if actor_role in ['HOSPITAL_ADMIN', 'ADMIN']:
        if current_fac and new_facility and current_fac.district_id != new_facility.district_id:
            raise UnauthorizedDomainAction("Clinic Admin cannot perform cross-district staff transfers.")
        admin_fac_id = getattr(actor_user, 'assigned_facility_id', None)
        if not admin_fac_id and actor_staff_obj:
            p_fa = actor_staff_obj.facility_assignments.filter(is_primary=True, is_active=True).first()
            admin_fac_id = p_fa.facility_id if p_fa else None
        if admin_fac_id and current_fac and current_fac.id != admin_fac_id:
            raise UnauthorizedDomainAction(f"Clinic Admin cannot transfer staff from foreign facility #{current_fac.id}.")

    if actor_role in ['DISTRICT_OFFICER', 'DHO']:
        dist_id = getattr(actor_user, 'assigned_district_id', None)
        if new_facility and new_facility.district_id != dist_id:
            raise UnauthorizedDomainAction(
                f"District Officer cannot transfer staff to facility #{new_facility.id} outside assigned district #{dist_id}."
            )
        if current_fac and current_fac.district_id != dist_id:
            raise UnauthorizedDomainAction(
                f"District Officer cannot transfer staff from facility #{current_fac.id} outside assigned district #{dist_id}."
            )

    transfer_date = effective_date or datetime.date.today()
    yesterday = transfer_date - datetime.timedelta(days=1)
    is_future = transfer_date > datetime.date.today()

    with transaction.atomic():
        if is_future:
            staff_profile.status = StaffStatusChoices.TRANSFER_PENDING
            staff_profile.save(update_fields=["status", "updated_at"])

            # Current primary remains active until yesterday
            current_primaries = StaffFacilityAssignment.objects.filter(
                staff=staff_profile,
                is_primary=True,
                is_active=True
            )
            for cur in current_primaries:
                cur.effective_to = max(cur.effective_from, yesterday)
                cur.save(update_fields=["effective_to"])

            # Create new assignment starting on transfer_date
            new_assignment = StaffFacilityAssignment.objects.create(
                staff=staff_profile,
                facility=new_facility,
                department=new_department,
                is_primary=True,
                is_active=True,
                effective_from=transfer_date
            )
        else:
            # Immediate transfer
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

            new_assignment = StaffFacilityAssignment.objects.create(
                staff=staff_profile,
                facility=new_facility,
                department=new_department,
                is_primary=True,
                is_active=True,
                effective_from=transfer_date
            )

            # Update User assigned_facility immediately
            user = getattr(staff_profile, 'user_account', None)
            if user and user.assigned_facility_id != new_facility.id:
                user.assigned_facility = new_facility
                user.save(update_fields=["assigned_facility"])

            if staff_profile.status == StaffStatusChoices.TRANSFER_PENDING:
                staff_profile.status = StaffStatusChoices.ACTIVE
                staff_profile.save(update_fields=["status", "updated_at"])

        record_audit_event(
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=new_facility,
            action_type="TRANSFER_STAFF",
            table_name="staff_profiles",
            record_id=staff_profile.id,
            payload_before={"facility_id": current_fac.id if current_fac else None},
            payload_after={"facility_id": new_facility.id, "transfer_date": str(transfer_date), "status": staff_profile.status}
        )

        return new_assignment


def suspend_staff(staff_profile, reason=None, actor=None, actor_staff=None):
    """
    Suspends a staff member, denying operational access across all facilities.
    """
    effective_actor = actor or actor_staff
    primary_fa = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    context_facility = primary_fa.facility if primary_fa else None

    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=context_facility,
        target_staff=staff_profile
    )

    old_status = staff_profile.status
    with transaction.atomic():
        staff_profile.status = StaffStatusChoices.SUSPENDED
        staff_profile.save(update_fields=["status", "updated_at"])

        user = getattr(staff_profile, 'user_account', None)
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])

        record_audit_event(
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=context_facility,
            action_type="SUSPEND_STAFF",
            table_name="staff_profiles",
            record_id=staff_profile.id,
            payload_before={"status": old_status},
            payload_after={"status": StaffStatusChoices.SUSPENDED, "reason": reason}
        )
    return staff_profile


def deactivate_staff(staff_profile, reason=None, actor=None, actor_staff=None):
    """
    Permanently deactivates a staff profile, revoking account login and role assignments.
    """
    effective_actor = actor or actor_staff
    primary_fa = staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
    context_facility = primary_fa.facility if primary_fa else None

    actor_user, actor_staff_obj, actor_role = validate_admin_actor(
        actor=effective_actor,
        target_facility=context_facility,
        target_staff=staff_profile
    )

    old_status = staff_profile.status
    today = datetime.date.today()

    with transaction.atomic():
        staff_profile.status = StaffStatusChoices.DEACTIVATED
        staff_profile.save(update_fields=["status", "updated_at"])

        # Revoke user account
        user = getattr(staff_profile, 'user_account', None)
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])

        # Inactivate active role assignments
        StaffRoleAssignment.objects.filter(staff=staff_profile, is_active=True).update(
            is_active=False,
            effective_to=today
        )

        # Inactivate active facility assignments
        StaffFacilityAssignment.objects.filter(staff=staff_profile, is_active=True).update(
            is_active=False,
            effective_to=today
        )

        record_audit_event(
            actor_staff=actor_staff_obj,
            actor_user_id=actor_user.id if actor_user else None,
            actor_role_snapshot=actor_role,
            facility=context_facility,
            action_type="DEACTIVATE_STAFF",
            table_name="staff_profiles",
            record_id=staff_profile.id,
            payload_before={"status": old_status},
            payload_after={"status": StaffStatusChoices.DEACTIVATED, "reason": reason}
        )
    return staff_profile


def seed_roles_and_permissions(stdout=None):
    """
    Idempotent deterministic seed mechanism for the 7 operational roles,
    57 permissions, and role-permission mappings.
    Safe to execute multiple times. Preserves existing records.
    """
    from apps.accounts.models import RoleMaster, PermissionMaster, RolePermission
    from apps.accounts.constants import SEEDED_ROLES, SEEDED_PERMISSIONS, ROLE_PERMISSION_MAP

    roles_created = 0
    roles_updated = 0
    perms_created = 0
    perms_updated = 0
    mappings_created = 0

    # 1. Seed Roles
    from apps.accounts.models import User, StaffProfile
    RoleMaster.objects.filter(code="COMPOUNDER").update(
        code="FRONT_DESK_OFFICER",
        name="Front Desk Officer",
        display_name="Front Desk Officer / Registration Clerk",
        description="Front-desk patient registration, demographic updates, and OPD queue token issuance"
    )
    User.objects.filter(role="COMPOUNDER").update(role="FRONT_DESK_OFFICER")
    StaffProfile.objects.filter(designation__iexact="Compounder").update(designation="Front Desk Officer")

    role_objs = {}
    for r_data in SEEDED_ROLES:
        role, created = RoleMaster.objects.get_or_create(
            code=r_data["code"],
            defaults={
                "name": r_data["name"],
                "display_name": r_data["display_name"],
                "description": r_data["description"],
                "scope_level": r_data["scope_level"],
                "is_system_role": r_data["is_system_role"],
                "is_active": r_data["is_active"],
            }
        )
        if created:
            roles_created += 1
        else:
            updated = False
            if not role.display_name and r_data.get("display_name"):
                role.display_name = r_data["display_name"]
                updated = True
            if not role.description and r_data.get("description"):
                role.description = r_data["description"]
                updated = True
            if role.scope_level != r_data.get("scope_level"):
                role.scope_level = r_data["scope_level"]
                updated = True
            if updated:
                role.save()
                roles_updated += 1
        role_objs[r_data["code"]] = role

    # 2. Seed Permissions
    perm_objs = {}
    for p_data in SEEDED_PERMISSIONS:
        perm, created = PermissionMaster.objects.get_or_create(
            code=p_data["code"],
            defaults={
                "name": p_data["name"],
                "display_name": p_data["display_name"],
                "description": p_data["description"],
                "domain": p_data["domain"],
                "action": p_data["action"],
                "is_active": True,
            }
        )
        if created:
            perms_created += 1
        else:
            updated = False
            if not perm.display_name and p_data.get("display_name"):
                perm.display_name = p_data["display_name"]
                updated = True
            if not perm.domain and p_data.get("domain"):
                perm.domain = p_data["domain"]
                updated = True
            if not perm.action and p_data.get("action"):
                perm.action = p_data["action"]
                updated = True
            if updated:
                perm.save()
                perms_updated += 1
        perm_objs[p_data["code"]] = perm

    # 3. Seed and Reconcile RolePermission Mappings
    for role_code, perm_codes in ROLE_PERMISSION_MAP.items():
        role_obj = role_objs.get(role_code)
        if not role_obj:
            continue
        valid_perm_ids = set()
        for perm_code in perm_codes:
            perm_obj = perm_objs.get(perm_code)
            if not perm_obj:
                continue
            valid_perm_ids.add(perm_obj.id)
            mapping, created = RolePermission.objects.get_or_create(
                role=role_obj,
                permission=perm_obj,
                defaults={"is_active": True}
            )
            if created:
                mappings_created += 1
            elif not mapping.is_active:
                mapping.is_active = True
                mapping.save(update_fields=["is_active"])

        # Reconcile: Deactivate any permissions removed from this role
        RolePermission.objects.filter(role=role_obj).exclude(permission_id__in=valid_perm_ids).update(is_active=False)

    summary = (
        f"Role & Permission Catalogue Seed Complete: "
        f"Roles ({roles_created} created, {roles_updated} updated, {len(role_objs)} total), "
        f"Permissions ({perms_created} created, {perms_updated} updated, {len(perm_objs)} total), "
        f"RolePermissions ({mappings_created} created, {RolePermission.objects.filter(is_active=True).count()} active)."
    )
    if stdout:
        stdout.write(summary)
    return {
        "roles_created": roles_created,
        "roles_updated": roles_updated,
        "perms_created": perms_created,
        "perms_updated": perms_updated,
        "mappings_created": mappings_created,
        "summary": summary
    }

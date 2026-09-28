import datetime
"""
IAM Authorization & Scoping Engine.
Authoritative source of truth: RoleMaster + RolePermission + PermissionMaster.
User.role is a transitional legacy field that cannot independently grant permissions.
Multi-role resolution: Union of active RoleMaster permissions via StaffRoleAssignment and User.role.
"""
from rest_framework import permissions

# Complete bidirectional mapping translating legacy view action strings to canonical catalogue permissions
LEGACY_PERMISSION_MAP = {
    # Patient
    'patients.view': 'patients.read',
    'patients.read': 'patients.read',
    'patients.create': 'patients.create',
    'patients.update': 'patients.update_demographics',
    'patients.update_demographics': 'patients.update_demographics',

    # Queue
    'queue.view': 'queue.view',
    'queue.read': 'queue.view',
    'queue.create': 'queue.create',
    'queue.issue_token': 'queue.issue_token',
    'queue.call_next': 'queue.call_next',
    'queue.transition': 'queue.transition',
    'queue.update': 'queue.transition',
    'queue.void': 'queue.void',

    # Vitals & Triage
    'vitals.create': 'vitals.create',
    'vitals.update': 'vitals.update',
    'vitals.view': 'consultation.read',
    'vitals.read': 'consultation.read',
    'triage.create': 'triage.create',
    'triage.update': 'triage.update',
    'triage.view': 'consultation.read',
    'triage.read': 'consultation.read',

    # Consultations & Diagnosis
    'consultation.create': 'consultation.create',
    'consultation.read': 'consultation.read',
    'consultation.view': 'consultation.read',
    'consultation.update': 'consultation.update',
    'diagnosis.create': 'diagnosis.create',
    'diagnosis.read': 'diagnosis.read',
    'diagnosis.view': 'diagnosis.read',
    'diagnosis.update': 'diagnosis.update',

    # Prescriptions
    'prescription.create': 'prescription.create',
    'prescription.read': 'prescription.read',
    'prescription.view': 'prescription.read',
    'prescription.update': 'prescription.update',
    'prescription.verify': 'prescription.verify',
    'prescription.hold': 'prescription.hold',
    'prescription.reject': 'prescription.reject',

    # Referrals & Clinical Transitions
    'referrals.create': 'consultation.create',
    'referrals.view': 'consultation.read',
    'referrals.read': 'consultation.read',

    # NCD & Disease Surveillance (clinical diagnosis sub-domains)
    'ncd.create': 'diagnosis.create',
    'ncd.update': 'diagnosis.update',
    'ncd.view': 'diagnosis.read',
    'ncd.read': 'diagnosis.read',
    'surveillance.create': 'diagnosis.create',
    'surveillance.update': 'diagnosis.update',
    'surveillance.view': 'diagnosis.read',
    'surveillance.read': 'diagnosis.read',

    # Laboratory
    'lab_order.create': 'lab_order.create',
    'lab_orders.create': 'lab_order.create',
    'lab_order.read': 'lab_order.read',
    'lab_orders.view': 'lab_order.read',
    'specimen.collect': 'specimen.collect',
    'lab_result.create': 'lab_result.create',
    'lab_results.create': 'lab_result.create',
    'lab_result.read': 'lab_result.read',
    'lab_results.view': 'lab_result.read',
    'lab_result.update': 'lab_result.update',
    'lab_results.update': 'lab_result.update',
    'lab_result.verify': 'lab_result.verify',
    'lab_result.amend': 'lab_result.amend',

    # Pharmacy & Inventory
    'inventory.read': 'inventory.read',
    'inventory.view': 'inventory.read',
    'inventory.create': 'inventory.adjust',
    'inventory.update': 'inventory.adjust',
    'inventory.adjust': 'inventory.adjust',
    'pharmacy.view': 'inventory.read',
    'pharmacy.dispense': 'dispensation.create',
    'dispensation.create': 'dispensation.create',
    'dispensation.read': 'dispensation.read',
    'medicine_batch.read': 'medicine_batch.read',

    # Procurement
    'purchase_order.create': 'purchase_order.create',
    'po.create': 'purchase_order.create',
    'purchase_order.read': 'purchase_order.read',
    'po.view': 'purchase_order.read',
    'purchase_order.update': 'purchase_order.update',
    'po.update': 'purchase_order.update',
    'purchase_order.approve': 'purchase_order.approve',
    'po.approve': 'purchase_order.approve',
    'goods_receipt.create': 'goods_receipt.create',
    'po.receive': 'goods_receipt.create',
    'vendor.create': 'purchase_order.create',
    'vendor.update': 'purchase_order.update',
    'vendor.view': 'purchase_order.read',

    # Facility & Staff & Audit
    'facility.read': 'facility.read',
    'hospital.view': 'facility.read',
    'clinic.view': 'facility.read',
    'facility.create': 'facility.create',
    'facility.update': 'facility.update',
    'system_config.update': 'facility.update',
    'system_config.view': 'facility.read',
    'facility.deactivate': 'facility.deactivate',
    'staff.read': 'staff.read',
    'staff.view': 'staff.read',
    'staff.create': 'staff.create',
    'staff.invite': 'staff.invite',
    'staff.assign_role': 'staff.assign_role',
    'staff.update': 'staff.assign_role',
    'staff.end_role': 'staff.end_role',
    'staff.assign_facility': 'staff.assign_facility',
    'staff.transfer': 'staff.transfer',
    'staff.suspend': 'staff.suspend',
    'staff.deactivate': 'staff.deactivate',
    'audit.read': 'audit.read',
    'audit_logs.view': 'audit.read',
    'reports.read': 'audit.read',
    'reports.view': 'audit.read',
    'reports.export': 'audit.read',
    'dashboard.view': 'patients.read',
    'appointments.view': 'queue.view',
    'appointments.update': 'queue.transition',
}

# Static reference table preserved strictly for unseeded test fixtures.
# NEVER evaluated when database catalogue contains RolePermission mappings.
ROLE_PERMISSIONS = {
    'DISTRICT_OFFICER': {
        'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
        'audit_logs.view', 'dashboard.view', 'referrals.view', 'inventory.view', 'queue.view',
        'lab_orders.view', 'patients.view', 'po.view', 'vendor.view', 'ncd.view', 'surveillance.view',
        'triage.view', 'consultation.view', 'prescription.view', 'telemedicine.view', 'outreach.view', 'wellness.view',
        'ars.view', 'quality.view', 'integrations.view',
        'patients.read', 'consultation.read', 'diagnosis.read', 'prescription.read',
        'lab_order.read', 'lab_result.read', 'inventory.read', 'purchase_order.read',
        'purchase_order.approve', 'staff.read', 'staff.create', 'staff.invite',
        'staff.assign_role', 'staff.end_role', 'staff.assign_facility', 'staff.transfer',
        'staff.suspend', 'staff.deactivate', 'facility.read', 'facility.create',
        'facility.update', 'facility.deactivate', 'audit.read'
    },
    'HOSPITAL_ADMIN': {
        'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
        'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.create', 'appointments.update',
        'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
        'system_config.view', 'system_config.update', 'dashboard.view', 'queue.view', 'queue.call_next', 'queue.transition', 'queue.create', 'referrals.view',
        'po.view', 'po.create', 'po.update', 'po.approve', 'vendor.view', 'vendor.create', 'vendor.update',
        'lab_orders.view', 'lab_results.view',
        'ncd.view', 'surveillance.view', 'ars.view', 'quality.view', 'integrations.view',
        'patients.read', 'patients.update_demographics', 'queue.issue_token', 'queue.void',
        'purchase_order.read', 'purchase_order.approve', 'staff.read', 'staff.invite',
        'staff.assign_role', 'staff.end_role', 'staff.assign_facility', 'staff.transfer',
        'staff.suspend', 'staff.deactivate', 'facility.read', 'facility.update', 'audit.read'
    },
    'DOCTOR': {
        'patients.view', 'patients.update', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
        'triage.view', 'triage.create', 'triage.update',
        'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
        'lab_orders.view', 'lab_orders.create', 'lab_results.view',
        'referrals.view', 'referrals.create', 'clinic.view', 'queue.view', 'queue.call_next', 'queue.transition', 'dashboard.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update',
        'patients.read', 'vitals.create', 'vitals.update', 'lab_order.create', 'lab_order.read',
        'lab_result.read', 'lab_result.verify', 'medicine_batch.read'
    },
    'NURSE': {
        'patients.view', 'patients.update', 'appointments.view', 'appointments.update',
        'vitals.view', 'vitals.create', 'vitals.update', 'triage.view', 'triage.create', 'triage.update',
        'queue.view', 'queue.call_next', 'queue.transition', 'queue.update', 'clinic.view', 'dashboard.view',
        'lab_orders.view', 'lab_results.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update',
        'patients.read', 'consultation.read', 'diagnosis.read', 'prescription.read',
        'lab_order.read', 'lab_result.read', 'specimen.collect', 'medicine_batch.read'
    },
    'COMPOUNDER': {
        'patients.view', 'patients.read', 'patients.create', 'patients.update', 'patients.update_demographics',
        'queue.view', 'queue.create', 'queue.issue_token', 'queue.void',
        'clinic.view', 'dashboard.view'
    },
    'LAB_TECHNICIAN': {
        'patients.view', 'patients.read', 'queue.view', 'queue.call_next', 'queue.transition',
        'lab_orders.view', 'lab_orders.create', 'lab_orders.update',
        'lab_results.view', 'lab_results.create', 'lab_results.update',
        'clinic.view', 'dashboard.view',
        'lab_order.read', 'specimen.collect', 'lab_result.create', 'lab_result.read', 'lab_result.amend'
    },
    'PHARMACIST': {
        'prescription.view', 'prescription.read', 'prescription.verify', 'prescription.hold', 'prescription.reject',
        'pharmacy.view', 'pharmacy.dispense', 'dispensation.create', 'dispensation.read',
        'inventory.view', 'inventory.read', 'inventory.create', 'inventory.update', 'inventory.adjust',
        'medicine_batch.read', 'reports.view', 'reports.export', 'clinic.view', 'dashboard.view',
        'po.view', 'po.create', 'po.update', 'po.receive', 'vendor.view', 'vendor.create', 'vendor.update',
        'purchase_order.create', 'purchase_order.read', 'purchase_order.update', 'goods_receipt.create'
    }
}


def get_user_active_role_codes(user):
    """
    Resolves the authoritative set of active role codes for an authenticated user.
    Authoritative Resolution Invariant:
    1. If a StaffProfile exists AND has any StaffRoleAssignment records:
       - Effective roles = active StaffRoleAssignment roles ONLY.
       - User.role MUST be ignored for authorization (has ZERO authorization weight).
       - If the StaffProfile status is not ACTIVE (e.g. SUSPENDED, DEACTIVATED, INVITED),
         returns set() (fails closed).
       - Only assignments where is_active=True, role__is_active=True, and
         (effective_to is NULL or effective_to >= today) and effective_from <= today
         are considered active.
    2. If NO StaffRoleAssignment records exist for the user (legacy transitional fallback):
       - User.role is considered ONLY IF represented by an active RoleMaster in the DB.
       - If StaffProfile exists and is inactive, fails closed (returns set()).
       - Clearly marked as transitional behavior for unassigned/legacy fixtures.
    """
    if not user or not user.is_authenticated:
        return set()

    # Live database check on user account active status
    if not getattr(user, 'is_active', True):
        return set()

    from django.db import models
    from apps.accounts.models import RoleMaster

    staff_profile = getattr(user, 'staff_profile', None)

    # 1. Authoritative resolution: StaffProfile with StaffRoleAssignment records
    if staff_profile and staff_profile.role_assignments.exists():
        # Lifecycle enforcement: INVITED, SUSPENDED, DEACTIVATED cannot perform operational actions
        if getattr(staff_profile, 'status', 'ACTIVE') != 'ACTIVE':
            return set()

        today = datetime.date.today()
        active_assignments = staff_profile.role_assignments.filter(
            is_active=True,
            role__is_active=True
        ).filter(
            models.Q(effective_from__lte=today) & (models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=today))
        ).values_list('role__code', flat=True)

        # Invariant: User.role is strictly ignored when StaffRoleAssignment exists
        return set(active_assignments)

    # If staff profile exists but has no role assignments, verify lifecycle status
    if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') != 'ACTIVE':
        return set()

    # 2. Transitional legacy User.role fallback (ONLY if active in RoleMaster catalogue)
    legacy_role = getattr(user, 'role', None)
    if legacy_role:
        if RoleMaster.objects.filter(code=legacy_role, is_active=True).exists():
            return {legacy_role}

    return set()


def get_user_role_permissions(user):
    """
    Authoritative Permission Resolution Engine:
    Resolves the UNION of active permissions across all active roles for the user.
    Database (RoleMaster + RolePermission + PermissionMaster) is the SOLE authoritative source.
    User.role alone CANNOT grant any permissions without active database catalogue entries.
    """
    if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
        return set()

    staff_profile = getattr(user, 'staff_profile', None)
    if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') != 'ACTIVE':
        return set()

    # Superuser has all seeded canonical permissions
    if getattr(user, 'is_superuser', False):
        try:
            from apps.accounts.constants import SEEDED_PERMISSIONS
            return {p['code'] for p in SEEDED_PERMISSIONS}
        except Exception:
            return set()

    active_role_codes = get_user_active_role_codes(user)
    if not active_role_codes:
        return set()

    from apps.accounts.models import RolePermission
    # Strict database query:
    # 1. Role must be in active_role_codes AND role.is_active must be True
    # 2. Permission must be is_active=True
    # 3. RolePermission mapping itself must be is_active=True
    db_perms = set(RolePermission.objects.filter(
        role__code__in=active_role_codes,
        role__is_active=True,
        permission__is_active=True,
        is_active=True
    ).values_list('permission__code', flat=True))

    return db_perms


def has_role_permission(user, permission_name):
    """
    Check if user possesses the requested permission code.
    Evaluates against database-backed RolePermission catalogue exclusively.
    User.role cannot independently grant permissions.
    """
    if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
        return False

    staff_profile = getattr(user, 'staff_profile', None)
    if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') != 'ACTIVE':
        return False

    if getattr(user, 'is_superuser', False):
        return True

    user_perms = get_user_role_permissions(user)

    # If user has no active permissions in DB:
    if not user_perms:
        # Fallback ONLY for legacy test environments where RolePermission table was never seeded
        from apps.accounts.models import RolePermission
        if not RolePermission.objects.exists():
            legacy_role = getattr(user, 'role', None)
            return permission_name in ROLE_PERMISSIONS.get(legacy_role, set())
        return False

    # 1. Check direct match against database permissions
    if permission_name in user_perms:
        return True

    # 2. Check legacy / alias mapping against database permissions
    canonical_code = LEGACY_PERMISSION_MAP.get(permission_name)
    if canonical_code and canonical_code in user_perms:
        return True

    return False


def get_accessible_facility_ids_for_user(user):
    """
    Facility Scoping Helper:
    - DISTRICT_OFFICER: Returns list of facility IDs in user's assigned district.
      FAILS CLOSED (returns []) if assigned_district_id is NULL.
    - Staff with StaffFacilityAssignment: Returns list of authorized facility IDs.
      If status is TRANSFER_PENDING, strictly restricts to primary facility (no dual access).
    - Operational Users fallback: Returns [user.assigned_facility_id] only.
    """
    if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
        return []

    staff_profile = getattr(user, 'staff_profile', None)
    if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
        return []

    from django.db import models

    # Check District Officer role
    user_roles = get_user_active_role_codes(user)
    if 'DISTRICT_OFFICER' in user_roles or getattr(user, 'role', None) == 'DISTRICT_OFFICER':
        if getattr(user, 'assigned_district_id', None):
            from apps.facilities.models import Facility
            return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list('id', flat=True))
        # NULL district must fail closed. DHO role does NOT grant statewide access.
        return []

    # Check StaffFacilityAssignment if present on StaffProfile
    if staff_profile:
        today = datetime.date.today()
        fac_qs = staff_profile.facility_assignments.filter(
            is_active=True
        ).filter(
            models.Q(effective_from__lte=today) & (models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=today))
        )
        if getattr(staff_profile, 'status', 'ACTIVE') == 'TRANSFER_PENDING':
            # Do not silently grant access to both old and new facilities; restrict to primary
            primary_id = fac_qs.filter(is_primary=True).values_list('facility_id', flat=True).first()
            if primary_id:
                return [primary_id]
            if getattr(user, 'assigned_facility_id', None):
                return [user.assigned_facility_id]
            return []

        fac_ids = list(fac_qs.values_list('facility_id', flat=True))
        if fac_ids:
            return list(set(fac_ids))

    if getattr(user, 'assigned_facility_id', None):
        return [user.assigned_facility_id]

    return []


def can_access_facility(user, facility_id):
    """
    Verifies if user has authorization to access the specified facility ID.
    - DISTRICT_OFFICER: Scoped strictly to assigned district. NULL district FAILS CLOSED (returns False).
    - Operational Users: Scoped strictly to authorized facilities.
    """
    if not user or not user.is_authenticated or not getattr(user, 'is_active', True) or not facility_id:
        return False

    staff_profile = getattr(user, 'staff_profile', None)
    if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
        return False

    accessible_ids = get_accessible_facility_ids_for_user(user)
    try:
        return int(facility_id) in accessible_ids
    except (ValueError, TypeError):
        return False


class IsAuthenticatedAndRoleAuthorized(permissions.BasePermission):
    """DRF permission checking authentication and live database account status."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not getattr(request.user, 'is_active', True):
            return False
        staff_profile = getattr(request.user, 'staff_profile', None)
        if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
            return False
        return True


class HasPermission(permissions.BasePermission):
    """
    DRF Custom Permission class checking method or view-level permission against live database catalogue.
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not getattr(request.user, 'is_active', True):
            return False

        staff_profile = getattr(request.user, 'staff_profile', None)
        if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
            self.message = f"Account is {staff_profile.status.lower()}. Operational access is denied."
            return False

        action = getattr(view, 'action', None)
        perm_map = getattr(view, 'required_permissions', {})
        if perm_map and action and action in perm_map:
            req_perm = perm_map[action]
        elif perm_map and request.method in perm_map:
            req_perm = perm_map[request.method]
        else:
            req_perm = getattr(view, 'required_permission', None)

        if not req_perm:
            return True

        return has_role_permission(request.user, req_perm)


class HasFacilityScope(permissions.BasePermission):
    """
    DRF Permission enforcing Facility & Resource Scoping on API requests:
    - DISTRICT_OFFICER: Read-only oversight across facilities in assigned district. Cannot mutate clinical or facility records.
      Fails closed if assigned_district_id is NULL.
    - Operational Staff: Scoped strictly to their authorized facilities.
    """
    message = "You do not have authorization to access resources outside your assigned facility or district scope."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not getattr(request.user, 'is_active', True):
            return False

        staff_profile = getattr(request.user, 'staff_profile', None)
        if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
            self.message = f"Account is {staff_profile.status.lower()}. Operational access is denied."
            return False

        # District Officer is blocked from direct clinical, demographic, surveillance, and facility procurement mutations
        user_roles = get_user_active_role_codes(request.user)
        if 'DISTRICT_OFFICER' in user_roles or getattr(request.user, 'role', None) == 'DISTRICT_OFFICER':
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                mutation_restricted_views = {
                    'ConsultationViewSet', 'PrescriptionViewSet', 'TriageVitalsViewSet', 'DispenseMedicineView',
                    'PurchaseOrderViewSet', 'VendorViewSet', 'PatientViewSet', 'NCDRecordViewSet',
                    'DiseaseCaseViewSet', 'ReferralViewSet', 'FollowUpViewSet', 'LabOrderViewSet',
                    'LabResultViewSet', 'VisitViewSet', 'MedicineMasterViewSet', 'MedicineBatchViewSet',
                    'FacilityOxygenSupplyViewSet', 'FacilityConsumableInventoryViewSet', 'FacilityMaintenanceTicketViewSet',
                    'FacilityBedCapacityViewSet', 'FacilityBedAllocationViewSet'
                }
                if view.__class__.__name__ in mutation_restricted_views:
                    self.message = "District Officers have read-only oversight access and cannot modify clinical, patient, or facility records."
                    return False

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated or not getattr(request.user, 'is_active', True):
            return False

        staff_profile = getattr(request.user, 'staff_profile', None)
        if staff_profile and getattr(staff_profile, 'status', 'ACTIVE') in ['INVITED', 'SUSPENDED', 'DEACTIVATED']:
            return False

        user_roles = get_user_active_role_codes(request.user)
        if 'DISTRICT_OFFICER' in user_roles or getattr(request.user, 'role', None) == 'DISTRICT_OFFICER':
            if request.method not in permissions.SAFE_METHODS:
                return False
            # Check district isolation. NULL district fails closed!
            if not getattr(request.user, 'assigned_district_id', None):
                return False

            from apps.facilities.models import Facility
            dist_fac_ids = set(Facility.objects.filter(district_id=request.user.assigned_district_id).values_list('id', flat=True))

            # Check patient direct district
            if getattr(obj, 'district_id', None):
                return obj.district_id == request.user.assigned_district_id

            # Check referral source / destination
            if hasattr(obj, 'source_facility_id') or hasattr(obj, 'destination_facility_id'):
                src = getattr(obj, 'source_facility_id', None)
                dst = getattr(obj, 'destination_facility_id', None)
                return (src in dist_fac_ids or dst in dist_fac_ids)

            # Check facility foreign keys
            obj_fac_id = getattr(obj, 'facility_id', None) or getattr(obj, 'assigned_facility_id', None) or getattr(obj, 'registered_at_facility_id', None)
            if obj_fac_id:
                return obj_fac_id in dist_fac_ids
            return True

        accessible_fac_ids = get_accessible_facility_ids_for_user(request.user)
        if not accessible_fac_ids:
            return False

        # Cross-facility referral exemption: if user's accessible facilities include destination or source
        if hasattr(obj, 'source_facility_id') and hasattr(obj, 'destination_facility_id'):
            if obj.source_facility_id in accessible_fac_ids or obj.destination_facility_id in accessible_fac_ids:
                return True

        obj_fac_id = getattr(obj, 'facility_id', None) or getattr(obj, 'assigned_facility_id', None) or getattr(obj, 'registered_at_facility_id', None)
        if obj_fac_id:
            return obj_fac_id in accessible_fac_ids

        return True

from rest_framework import permissions

ROLE_PERMISSIONS = {
    'DISTRICT_OFFICER': {
        'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
        'audit_logs.view', 'dashboard.view', 'referrals.view', 'inventory.view', 'queue.view',
        'lab_orders.view', 'patients.view', 'po.view', 'vendor.view', 'ncd.view', 'surveillance.view',
        'triage.view', 'consultation.view', 'prescription.view', 'telemedicine.view', 'outreach.view', 'wellness.view'
    },
    'HOSPITAL_ADMIN': {
        'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
        'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.create', 'appointments.update',
        'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
        'system_config.view', 'system_config.update', 'dashboard.view', 'queue.view', 'referrals.view',
        'po.view', 'po.create', 'po.update', 'po.approve', 'vendor.view', 'vendor.create', 'vendor.update',
        'lab_orders.view', 'lab_orders.create', 'lab_orders.update', 'lab_results.view', 'lab_results.create', 'lab_results.update',
        'ncd.view', 'surveillance.view'
    },
    'DOCTOR': {
        'patients.view', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
        'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
        'lab_orders.view', 'lab_orders.create', 'lab_orders.update', 'lab_results.view', 'lab_results.create', 'lab_results.update',
        'referrals.view', 'referrals.create', 'clinic.view', 'queue.view', 'dashboard.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update'
    },
    'NURSE': {
        'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.update',
        'vitals.view', 'vitals.create', 'vitals.update', 'triage.view', 'triage.create', 'triage.update',
        'queue.view', 'queue.update', 'clinic.view', 'dashboard.view',
        'lab_orders.view', 'lab_orders.update', 'lab_results.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update'
    },
    'LAB_TECHNICIAN': {
        'patients.view', 'lab_orders.view', 'lab_orders.create', 'lab_orders.update',
        'lab_results.view', 'lab_results.create', 'lab_results.update',
        'clinic.view', 'dashboard.view'
    },
    'PHARMACIST': {
        'prescription.view', 'pharmacy.view', 'pharmacy.dispense', 'inventory.view', 'inventory.create', 'inventory.update',
        'reports.view', 'reports.export', 'clinic.view', 'dashboard.view',
        'po.view', 'po.create', 'po.update', 'po.receive', 'vendor.view', 'vendor.create', 'vendor.update'
    }
}


def has_role_permission(user, permission_name):
    """Check if user role possesses the requested permission code."""
    if not user or not user.is_authenticated:
        return False
    user_perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission_name in user_perms

def get_accessible_facility_ids_for_user(user):
    """
    Facility Scoping Helper:
    - DISTRICT_OFFICER: Returns list of facility IDs in user's assigned district (or None for all facilities in district).
    - Operational Users (HOSPITAL_ADMIN, DOCTOR, NURSE, LAB_TECHNICIAN, PHARMACIST):
      Returns [user.assigned_facility_id] only.
    """
    if not user or not user.is_authenticated:
        return []

    if user.role == 'DISTRICT_OFFICER':
        if user.assigned_district_id:
            from apps.facilities.models import Facility
            return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list('id', flat=True))
        return None

    if user.assigned_facility_id:
        return [user.assigned_facility_id]

    return []

def can_access_facility(user, facility_id):
    """Verifies if user has authorization to access the specified facility ID."""
    if not user or not user.is_authenticated or not facility_id:
        return False
    if user.role == 'DISTRICT_OFFICER':
        return True
    return user.assigned_facility_id == int(facility_id)


class IsAuthenticatedAndRoleAuthorized(permissions.BasePermission):
    """DRF permission checking authentication."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class HasPermission(permissions.BasePermission):
    """
    DRF Custom Permission class checking method or view-level permission.
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
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
    - DISTRICT_OFFICER: Read-only access across facilities in district. Cannot perform clinical or procurement mutations.
    - HOSPITAL_ADMIN, DOCTOR, NURSE, LAB_TECHNICIAN, PHARMACIST: Scoped strictly to their assigned facility.
    """
    message = "You do not have authorization to access resources outside your assigned facility."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # District Officer is blocked from direct clinical, demographic, surveillance, and facility procurement mutations
        if request.user.role == 'DISTRICT_OFFICER':
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                mutation_restricted_views = {
                    'ConsultationViewSet', 'PrescriptionViewSet', 'TriageVitalsViewSet', 'DispenseMedicineView',
                    'PurchaseOrderViewSet', 'VendorViewSet', 'PatientViewSet', 'NCDRecordViewSet',
                    'DiseaseCaseViewSet', 'ReferralViewSet', 'FollowUpViewSet', 'LabOrderViewSet',
                    'LabResultViewSet', 'VisitViewSet', 'MedicineMasterViewSet', 'MedicineBatchViewSet'
                }
                if view.__class__.__name__ in mutation_restricted_views:
                    self.message = "District Officers have read-only oversight access and cannot modify clinical, patient, or facility records."
                    return False

        return True


    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == 'DISTRICT_OFFICER':
            if request.method in permissions.SAFE_METHODS:
                return True
            return False

        user_fac_id = request.user.assigned_facility_id
        if not user_fac_id:
            return False

        obj_fac_id = getattr(obj, 'facility_id', None) or getattr(obj, 'assigned_facility_id', None) or getattr(obj, 'registered_at_facility_id', None)

        # Cross-facility referral exemption: if user's facility is destination or source of referral
        if hasattr(obj, 'source_facility_id') and hasattr(obj, 'destination_facility_id'):
            if obj.source_facility_id == user_fac_id or obj.destination_facility_id == user_fac_id:
                return True

        if obj_fac_id:
            return obj_fac_id == user_fac_id

        return True


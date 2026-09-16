from rest_framework import permissions

ROLE_PERMISSIONS = {
    'DISTRICT_OFFICER': {
        'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
        'audit_logs.view', 'dashboard.view'
    },
    'HOSPITAL_ADMIN': {
        'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
        'patients.view', 'patients.create', 'appointments.view', 'appointments.create', 'appointments.update',
        'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
        'system_config.view', 'system_config.update', 'dashboard.view'
    },
    'DOCTOR': {
        'patients.view', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
        'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
        'lab_orders.view', 'lab_orders.create', 'lab_results.view', 'referrals.view', 'referrals.create',
        'clinic.view', 'queue.view', 'dashboard.view'
    },
    'NURSE': {
        'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.create',
        'vitals.view', 'vitals.create', 'triage.view', 'triage.create', 'queue.view', 'queue.update',
        'clinic.view', 'dashboard.view'
    },
    'LAB_TECHNICIAN': {
        'patients.view', 'lab_orders.view', 'lab_results.view', 'lab_results.create', 'lab_results.update',
        'clinic.view', 'dashboard.view'
    },
    'PHARMACIST': {
        'prescription.view', 'pharmacy.view', 'pharmacy.dispense', 'inventory.view', 'inventory.create', 'inventory.update',
        'clinic.view', 'dashboard.view'
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
    Hierarchical Access Control Scoping Helper:
    - DISTRICT_OFFICER or unassigned district user:
      Returns None (Full district-wide network data access).
    - Hospital Administrator / Main Hospital User:
      Returns [Main Hospital ID + All Child Facility IDs]
    - Clinic User (DOCTOR, NURSE, LAB_TECHNICIAN, PHARMACIST):
      Returns [Assigned Facility ID only]
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.role == 'DISTRICT_OFFICER' or not user.assigned_facility:
        return None
        
    facility = user.assigned_facility
    return facility.get_all_descendant_ids()


class IsAuthenticatedAndRoleAuthorized(permissions.BasePermission):
    """DRF permission checking authentication."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class HasPermission(permissions.BasePermission):
    """
    DRF Custom Permission class that checks view.required_permission against user's role.
    Supports required_permissions dict keyed by HTTP method (GET, POST, PUT, DELETE).
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        perm_map = getattr(view, 'required_permissions', {})
        if perm_map and request.method in perm_map:
            req_perm = perm_map[request.method]
        else:
            req_perm = getattr(view, 'required_permission', None)
            
        if not req_perm:
            return True
            
        return has_role_permission(request.user, req_perm)

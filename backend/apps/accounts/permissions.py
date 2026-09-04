from rest_framework import permissions

def get_accessible_facility_ids_for_user(user):
    """
    Hierarchical Access Control Scoping Helper:
    - SUPER_ADMIN / DISTRICT_ADMIN / PUBLIC_HEALTH_OFFICER or unassigned user:
      Returns None (Full network data access).
    - Parent / Main Hospital User:
      Returns [Main Hospital ID + All Child Facility IDs]
      (Main Hospital Doctor/Admin can see Main Hospital data AND all child clinics' data).
    - Primary / Child Clinic User (Namma Clinic, Rural Clinic, UPHC):
      Returns [Child Facility ID only]
      (Child facility user CANNOT see parent Main Hospital data or sibling clinics).
    """
    if not user or not user.is_authenticated:
        return []
    
    # Super admins, district officers, and public health officers see all network data
    if user.role in ['SUPER_ADMIN', 'DISTRICT_ADMIN', 'PUBLIC_HEALTH_OFFICER'] or not user.assigned_facility:
        return None
        
    facility = user.assigned_facility
    return facility.get_all_descendant_ids()


class IsAuthenticatedAndRoleAuthorized(permissions.BasePermission):
    """DRF permission checking authentication."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

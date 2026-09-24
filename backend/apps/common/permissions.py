"""
Backend Authoritative Permission and Scope Classes for Namma Clinic REST API.
Enforces active StaffProfile resolution, administrative privileges, and facility/district isolation.
"""
from rest_framework.permissions import BasePermission
from apps.common.exceptions import UnauthorizedDomainAction
from apps.accounts.services import is_administrative_staff
from apps.accounts.models import StaffFacilityAssignment

def get_request_staff(request, required=True):
    """
    Resolves the authenticated requesting user's active StaffProfile.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_active:
        if required:
            raise UnauthorizedDomainAction("User is not authenticated or account is inactive.")
        return None

    staff = getattr(user, "staff_profile", None)
    if not staff:
        person = getattr(user, "person", None)
        if person:
            staff = person.staff_profiles.filter(status="ACTIVE").first()

    if required and (not staff or staff.status != "ACTIVE"):
        raise UnauthorizedDomainAction("Requesting user does not possess an active StaffProfile.")
    return staff


def get_user_permitted_facilities(staff_profile, user=None):
    """
    Returns query filter or list of facility IDs the user/staff is authorized to access.
    Returns None if user possesses global/administrative statewide scope.
    """
    if user and user.is_superuser:
        return None
    if staff_profile and is_administrative_staff(staff_profile):
        if staff_profile.designation == "District Health Officer" and user and user.assigned_district_id:
            from apps.facilities.models import Facility
            return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list("id", flat=True))
        if staff_profile.designation in ["System Administrator", "State Health Director"]:
            return None

    facility_ids = set()
    if staff_profile:
        active_assignments = StaffFacilityAssignment.objects.filter(staff=staff_profile, is_active=True).values_list("facility_id", flat=True)
        facility_ids.update(active_assignments)
    if user and user.assigned_facility_id:
        facility_ids.add(user.assigned_facility_id)

    return list(facility_ids)


def check_facility_permission(facility, staff_profile, user):
    """
    Validates that the user/staff is authorized to perform mutations in the given facility.
    Raises UnauthorizedDomainAction if unauthorized.
    """
    if user and user.is_superuser:
        return
    permitted = get_user_permitted_facilities(staff_profile, user)
    if permitted is None:
        return  # Global/statewide administrative authority
    facility_id = getattr(facility, "id", facility)
    if facility_id not in permitted:
        raise UnauthorizedDomainAction(f"User is not authorized for facility ID {facility_id}.")


class IsActiveStaff(BasePermission):
    """
    Requires the requesting user to be authenticated, active, and linked to an active StaffProfile.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        staff = get_request_staff(request, required=False)
        return staff is not None and staff.status == "ACTIVE"


class IsAdministrativeStaff(BasePermission):
    """
    Requires the requesting user to hold administrative authority (Superuser or Admin role/designation).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        staff = get_request_staff(request, required=False)
        return is_administrative_staff(staff)


class FacilityScopedPermission(BasePermission):
    """
    Enforces object-level facility isolation. Ordinary clinical staff can only access records
    belonging to facilities they are actively assigned to.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        staff = get_request_staff(request, required=False)
        permitted_facilities = get_user_permitted_facilities(staff, request.user)
        if permitted_facilities is None:
            return True  # Statewide / Superuser

        target_facility_id = None
        if hasattr(obj, "facility_id"):
            target_facility_id = obj.facility_id
        elif hasattr(obj, "registered_at_facility_id"):
            target_facility_id = obj.registered_at_facility_id
        elif hasattr(obj, "source_facility_id"):
            if obj.source_facility_id in permitted_facilities:
                return True
            if hasattr(obj, "destination_facility_id") and obj.destination_facility_id in permitted_facilities:
                return True
            return False

        if target_facility_id is None:
            return True

        return target_facility_id in permitted_facilities

"""
Organization & Facility REST API (v1).
Manages State, District, Taluk, Zone, Ward, Facility, and Department hierarchies.
"""
from rest_framework import serializers, viewsets, permissions, exceptions
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.common.permissions import IsActiveStaff, IsAdministrativeStaff, get_request_staff, get_user_permitted_facilities
from apps.accounts.permissions import get_user_active_role_codes

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class TalukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluk
        fields = '__all__'

class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class FacilitySerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Facility
        fields = [
            'id', 'facility_code', 'facility_name', 'facility_type',
            'state', 'district', 'zone', 'ward', 'address', 'status', 'departments'
        ]


class IsFacilityAdministrator(permissions.BasePermission):
    """
    Authoritative permission class governing Facility administrative operations (create, update, delete).
    Rules:
    - Superusers have global facility administration authority.
    - DISTRICT_OFFICER (DHO) may create and mutate facilities strictly within their assigned district.
    - HOSPITAL_ADMIN, DOCTOR, NURSE, COMPOUNDER, LAB_TECHNICIAN, PHARMACIST receive HTTP 403 Forbidden.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False

        if user.is_superuser:
            return True

        active_roles = get_user_active_role_codes(user)
        is_dho = ('DISTRICT_OFFICER' in active_roles) or (getattr(user, 'role', None) == 'DISTRICT_OFFICER')
        if not is_dho:
            return False

        staff = get_request_staff(request, required=False)
        if staff and staff.status != 'ACTIVE':
            return False

        dho_dist_id = getattr(user, 'assigned_district_id', None)
        if not dho_dist_id and staff:
            dho_dist_id = getattr(getattr(staff, 'user_account', None), 'assigned_district_id', None)

        if not dho_dist_id:
            return False  # Fails closed on NULL district

        # On create: validate target district if provided
        if view.action == 'create' or request.method == 'POST':
            target_dist = request.data.get('district')
            if target_dist is not None:
                if isinstance(target_dist, dict):
                    target_dist = target_dist.get('id')
                if str(target_dist) != str(dho_dist_id):
                    raise exceptions.PermissionDenied(
                        "District Officer can only create facilities within their assigned district."
                    )

        return True

    def has_object_permission(self, request, view, obj):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False

        if user.is_superuser:
            return True

        active_roles = get_user_active_role_codes(user)
        is_dho = ('DISTRICT_OFFICER' in active_roles) or (getattr(user, 'role', None) == 'DISTRICT_OFFICER')
        if not is_dho:
            return False

        dho_dist_id = getattr(user, 'assigned_district_id', None)
        if not dho_dist_id and hasattr(user, 'staff_profile'):
            dho_dist_id = getattr(user.staff_profile, 'assigned_district_id', None)

        if not dho_dist_id:
            return False

        # Facility must be in DHO's assigned district
        if obj.district_id != dho_dist_id:
            return False

        # If payload mutates district to another district outside DHO's jurisdiction
        if request.method in ['PUT', 'PATCH']:
            target_dist = request.data.get('district')
            if target_dist is not None:
                if isinstance(target_dist, dict):
                    target_dist = target_dist.get('id')
                if str(target_dist) != str(dho_dist_id):
                    raise exceptions.PermissionDenied(
                        "District Officer cannot transfer facility outside assigned district."
                    )

        return True


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsActiveStaff]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all().select_related('state')
    serializer_class = DistrictSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class TalukViewSet(viewsets.ModelViewSet):
    queryset = Taluk.objects.all().select_related('district')
    serializer_class = TalukSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.all().select_related('zone')
    serializer_class = WardSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().select_related('state', 'district', 'zone', 'ward').prefetch_related('departments')
    serializer_class = FacilitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsFacilityAdministrator()]
        return [IsActiveStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(id__in=permitted)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            dho_dist_id = getattr(user, 'assigned_district_id', None)
            if not dho_dist_id and hasattr(user, 'staff_profile'):
                dho_dist_id = getattr(user.staff_profile, 'assigned_district_id', None)
            if dho_dist_id and 'district' not in serializer.validated_data:
                serializer.save(district_id=dho_dist_id)
                return
        serializer.save()

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related('facility')
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

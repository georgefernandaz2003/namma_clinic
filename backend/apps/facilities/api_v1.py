"""
Organization & Facility REST API (v1).
Manages State, District, Taluk, Zone, Ward, Facility, and Department hierarchies.
"""
from rest_framework import serializers, viewsets, permissions, exceptions
from rest_framework.exceptions import PermissionDenied
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
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = Department
        fields = ['id', 'facility', 'facility_name', 'code', 'name', 'is_active', 'created_at']

    def validate_code(self, value):
        return value.strip().upper()

class FacilitySerializer(serializers.ModelSerializer):
    district_name = serializers.ReadOnlyField(source='district.name')
    departments = DepartmentSerializer(many=True, read_only=True)
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), required=False)

    class Meta:
        model = Facility
        fields = [
            'id', 'facility_code', 'facility_name', 'facility_type',
            'state', 'district', 'district_name', 'zone', 'ward', 'address',
            'population_served', 'vulnerable_population', 'phone', 'email',
            'opening_time', 'closing_time', 'services', 'specialists',
            'status', 'departments'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None

        if user and not user.is_superuser and not attrs.get('district') and not self.instance:
            dho_dist_id = getattr(user, 'assigned_district_id', None)
            if not dho_dist_id and hasattr(user, 'staff_profile'):
                dho_dist_id = getattr(user.staff_profile, 'assigned_district_id', None)
            if dho_dist_id:
                attrs['district'] = District.objects.filter(id=dho_dist_id).first()

        district = attrs.get('district')
        if not district and self.instance:
            district = self.instance.district
        if not attrs.get('state') and district:
            attrs['state'] = district.state

        if not self.instance and not attrs.get('district'):
            raise serializers.ValidationError({'district': 'District is required.'})

        status_val = attrs.get('status')
        if status_val and status_val not in ['ACTIVE', 'INACTIVE']:
            raise serializers.ValidationError({'status': "Facility status must be 'ACTIVE' or 'INACTIVE'."})

        return attrs


class IsFacilityAdministrator(permissions.BasePermission):
    """
    Authoritative permission class governing Facility administrative operations (create, update, delete).
    Rules:
    - Superusers have global facility administration authority.
    - DISTRICT_OFFICER (DHO) may create and mutate facilities strictly within their assigned district.
    - HOSPITAL_ADMIN, DOCTOR, NURSE, FRONT_DESK_OFFICER, LAB_TECHNICIAN, PHARMACIST receive HTTP 403 Forbidden.
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
        extra_kwargs = {}
        if not user.is_superuser:
            dho_dist_id = getattr(user, 'assigned_district_id', None)
            if not dho_dist_id and hasattr(user, 'staff_profile'):
                dho_dist_id = getattr(user.staff_profile, 'assigned_district_id', None)
            if dho_dist_id and 'district' not in serializer.validated_data:
                extra_kwargs['district_id'] = dho_dist_id
        facility = serializer.save(**extra_kwargs)
        from apps.facilities.services import provision_standard_departments
        provision_standard_departments(facility)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related('facility')
    serializer_class = DepartmentSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

    def get_queryset(self):
        qs = Department.objects.all().select_related('facility')
        # On single object mutation or retrieval, return all so check_object_permissions can evaluate and return HTTP 403 instead of 404
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return qs

        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)

        facility_param = self.request.query_params.get('facility')
        if facility_param:
            qs = qs.filter(facility_id=facility_param)

        return qs.order_by('id')

    def check_facility_scope(self, facility_id):
        user = self.request.user
        if user.is_superuser:
            return True
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, user)
        if permitted is not None and facility_id not in permitted:
            raise PermissionDenied(
                f"You do not have administrative authority over facility #{facility_id}."
            )
        return True

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        self.check_facility_scope(obj.facility_id)

    def perform_create(self, serializer):
        user = self.request.user
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, user)

        target_facility = serializer.validated_data.get('facility')
        if not target_facility and permitted:
            from apps.facilities.models import Facility
            target_facility = Facility.objects.get(pk=permitted[0])
            serializer.validated_data['facility'] = target_facility

        if target_facility:
            self.check_facility_scope(target_facility.id)

        serializer.save()

    def perform_update(self, serializer):
        target_facility = serializer.validated_data.get('facility')
        if target_facility:
            self.check_facility_scope(target_facility.id)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_facility_scope(instance.facility_id)
        instance.delete()

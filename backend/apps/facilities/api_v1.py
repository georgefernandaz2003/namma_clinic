"""
Organization & Facility REST API (v1).
Manages State, District, Taluk, Zone, Ward, Facility, and Department hierarchies.
"""
from rest_framework import serializers, viewsets, permissions, exceptions, status
from rest_framework.response import Response
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

    def validate(self, attrs):
        is_active = attrs.get('is_active')
        if is_active is False and self.instance and self.instance.is_active:
            from apps.facilities.services import validate_department_deactivation
            validate_department_deactivation(self.instance.facility, self.instance.code)
        return attrs

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
        from apps.facilities.services import provision_standard_departments, provision_standard_facility_services
        provision_standard_departments(facility)
        provision_standard_facility_services(facility)

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_facility_scope(instance.facility_id)

        # Protect standard departments from physical deletion
        from apps.facilities.services import STANDARD_DEPARTMENT_CODES, validate_department_deactivation
        if instance.code in STANDARD_DEPARTMENT_CODES:
            raise exceptions.ValidationError({
                'detail': f"Standard system department '{instance.name}' ({instance.code}) cannot be deleted. Deactivate the department instead."
            })

        # Check dependent active services
        validate_department_deactivation(instance.facility, instance.code)

        from django.db.models.deletion import RestrictedError
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RestrictedError as e:
            return Response(
                {
                    'error': f"Cannot delete department '{instance.name}' because active staff members or records reference it.",
                    'detail': str(e)
                },
                status=status.HTTP_409_CONFLICT
            )


class ServiceMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceMaster
        fields = ['id', 'code', 'name', 'category', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class FacilityServiceSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.facility_name', read_only=True)
    facility_code = serializers.CharField(source='facility.facility_code', read_only=True)
    service_code = serializers.CharField(source='service.code', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_category = serializers.CharField(source='service.category', read_only=True)

    class Meta:
        model = FacilityService
        fields = [
            'id', 'facility', 'facility_name', 'facility_code',
            'service', 'service_code', 'service_name', 'service_category',
            'is_available', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'facility_name', 'facility_code', 'service_code', 'service_name', 'service_category']

    def validate(self, attrs):
        facility = attrs.get('facility') or (self.instance.facility if self.instance else None)
        service = attrs.get('service') or (self.instance.service if self.instance else None)
        if facility and service and not self.instance:
            if FacilityService.objects.filter(facility=facility, service=service).exists():
                raise serializers.ValidationError("This service is already configured for this facility.")

        is_available = attrs.get('is_available')
        if is_available is True:
            srv_code = service.code if service else (self.instance.service.code if self.instance else None)
            fac_obj = facility or (self.instance.facility if self.instance else None)
            if srv_code and fac_obj:
                from apps.facilities.services import validate_service_enablement
                validate_service_enablement(fac_obj, srv_code)

        return attrs


class ServiceMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceMaster.objects.filter(is_active=True).order_by('id')
    serializer_class = ServiceMasterSerializer
    permission_classes = [permissions.IsAuthenticated]


class FacilityServiceViewSet(viewsets.ModelViewSet):
    queryset = FacilityService.objects.all().select_related('facility', 'service')
    serializer_class = FacilityServiceSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        # Clinical staff must NOT administer facility service configuration
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

    def get_queryset(self):
        user = self.request.user
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, user)

        # For detail actions (retrieve, update, destroy), return all so check_object_permissions enforces HTTP 403
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return FacilityService.objects.all().select_related('facility', 'service')

        qs = FacilityService.objects.all().select_related('facility', 'service')
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

        # Check that user has administrative role (HOSPITAL_ADMIN or DISTRICT_OFFICER)
        active_roles = set(get_user_active_role_codes(user))
        if not active_roles.intersection({'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'}):
            raise PermissionDenied("Clinical staff are not authorized to configure facility services.")

        # DHO district check
        if 'DISTRICT_OFFICER' in active_roles:
            assigned_district_id = getattr(user, 'assigned_district_id', None)
            if not assigned_district_id and staff:
                assigned_district_id = getattr(staff, 'assigned_district_id', None)
            if assigned_district_id:
                fac = Facility.objects.filter(pk=facility_id).first()
                if fac and fac.district_id != assigned_district_id:
                    raise PermissionDenied("DHO cannot configure services for facilities outside their assigned district.")

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
            target_facility = Facility.objects.get(pk=permitted[0])
            serializer.validated_data['facility'] = target_facility

        if target_facility:
            self.check_facility_scope(target_facility.id)

        serializer.save()

    def perform_update(self, serializer):
        target_facility = serializer.validated_data.get('facility')
        if target_facility:
            self.check_facility_scope(target_facility.id)
        else:
            self.check_facility_scope(serializer.instance.facility_id)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_facility_scope(instance.facility_id)
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        # Hospital Admin must receive HTTP 403 on DELETE
        active_roles = set(get_user_active_role_codes(request.user))
        if 'HOSPITAL_ADMIN' in active_roles and not request.user.is_superuser:
            raise PermissionDenied(
                "Hospital Administrators are not permitted to delete facility services. Services can only be enabled or disabled."
            )

        instance = self.get_object()
        self.check_facility_scope(instance.facility_id)

        # Canonical services cannot be permanently removed
        from apps.facilities.services import STANDARD_CANONICAL_SERVICES
        canonical_codes = {s['code'] for s in STANDARD_CANONICAL_SERVICES}
        if instance.service.code in canonical_codes:
            raise exceptions.ValidationError({
                'detail': f"Canonical facility service '{instance.service.name}' ({instance.service.code}) cannot be permanently deleted. Toggle its operational availability instead."
            })

        return super().destroy(request, *args, **kwargs)


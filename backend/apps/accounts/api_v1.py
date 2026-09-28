"""
IAM REST API (v1).
Delegates all identity, role, and facility mutations to domain services.
Direct PUT/PATCH/DELETE mutations are disabled to enforce service workflows and audit trails.
Role and Permission catalogue definitions are system-level assets restricted to system superusers.
"""
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment
)
from apps.accounts.serializers import (
    RoleMasterSerializer, PermissionMasterSerializer, RolePermissionSerializer
)
from apps.accounts.services import (
    create_staff_profile, update_staff_status, assign_role,
    end_role_assignment, assign_facility, transfer_staff
)
from apps.common.permissions import IsActiveStaff, IsAdministrativeStaff, get_request_staff

class IsSystemAdminForCatalogue(permissions.BasePermission):
    """
    Catalogue definitions (Roles, Permissions, RolePermission mappings) are system-level assets.
    Operational roles (DISTRICT_OFFICER, HOSPITAL_ADMIN, DOCTOR, NURSE, COMPOUNDER, LAB_TECHNICIAN, PHARMACIST)
    are strictly denied mutation access.
    Only trusted Django system superusers may create, modify, or delete definitions.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_superuser)

class RoleMasterViewSet(viewsets.ModelViewSet):
    """
    System-level Role Catalogue ViewSet.
    Read-only for operational staff; mutations restricted to Django system superusers.
    """
    queryset = RoleMaster.objects.all().prefetch_related('role_permissions__permission')
    serializer_class = RoleMasterSerializer
    permission_classes = [IsSystemAdminForCatalogue]

class PermissionMasterViewSet(viewsets.ModelViewSet):
    """
    System-level Permission Catalogue ViewSet.
    Read-only for operational staff; mutations restricted to Django system superusers.
    """
    queryset = PermissionMaster.objects.all()
    serializer_class = PermissionMasterSerializer
    permission_classes = [IsSystemAdminForCatalogue]

class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    Role-Permission mapping ViewSet.
    Read-only for operational staff; mutations restricted to Django system superusers.
    """
    queryset = RolePermission.objects.all().select_related('role', 'permission')
    serializer_class = RolePermissionSerializer
    permission_classes = [IsSystemAdminForCatalogue]

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'gender', 'date_of_birth', 'phone_number']

class StaffProfileSerializer(serializers.ModelSerializer):
    person_details = PersonSerializer(source='person', read_only=True)
    person = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all(), write_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'person', 'person_details', 'employee_id',
            'designation', 'department', 'status', 'medical_council_reg_number'
        ]

class StaffStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["PROBATION", "ACTIVE", "SUSPENDED", "RETIRED", "RESIGNED"])

class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffRoleAssignment
        fields = ['id', 'staff', 'role', 'effective_from', 'effective_to', 'is_active']
        read_only_fields = ['is_active']

class EndRoleAssignmentSerializer(serializers.Serializer):
    end_date = serializers.DateField(required=False)

class FacilityAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffFacilityAssignment
        fields = ['id', 'staff', 'facility', 'department', 'is_primary', 'effective_from', 'effective_to', 'is_active']
        read_only_fields = ['is_active']

class TransferStaffSerializer(serializers.Serializer):
    staff_profile_id = serializers.IntegerField()
    new_facility_id = serializers.IntegerField()
    new_department_id = serializers.IntegerField(required=False, allow_null=True)
    effective_date = serializers.DateField(required=False)

class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.all().select_related('person', 'department')
    serializer_class = StaffProfileSerializer
    permission_classes = [IsActiveStaff]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        profile = create_staff_profile(
            person=serializer.validated_data['person'],
            employee_id=serializer.validated_data['employee_id'],
            designation=serializer.validated_data['designation'],
            department=serializer.validated_data.get('department'),
            medical_council_reg_number=serializer.validated_data.get('medical_council_reg_number'),
            actor_staff=actor
        )
        return Response(self.get_serializer(profile).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='update-status', permission_classes=[IsAdministrativeStaff])
    def update_status(self, request, pk=None):
        profile = self.get_object()
        serializer = StaffStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        updated = update_staff_status(profile, serializer.validated_data['status'], actor_staff=actor)
        return Response(self.get_serializer(updated).data)

class RoleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StaffRoleAssignment.objects.all().select_related('staff', 'role')
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsAdministrativeStaff]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        assignment = assign_role(
            staff_profile=serializer.validated_data['staff'],
            role=serializer.validated_data['role'],
            effective_from=serializer.validated_data.get('effective_from'),
            effective_to=serializer.validated_data.get('effective_to'),
            actor_staff=actor
        )
        return Response(self.get_serializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='end-assignment')
    def end_assignment(self, request, pk=None):
        assignment = self.get_object()
        serializer = EndRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        ended = end_role_assignment(assignment, end_date=serializer.validated_data.get('end_date'), actor_staff=actor)
        return Response(self.get_serializer(ended).data)

class FacilityAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StaffFacilityAssignment.objects.all().select_related('staff', 'facility')
    serializer_class = FacilityAssignmentSerializer
    permission_classes = [IsAdministrativeStaff]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        assignment = assign_facility(
            staff_profile=serializer.validated_data['staff'],
            facility=serializer.validated_data['facility'],
            department=serializer.validated_data.get('department'),
            is_primary=serializer.validated_data.get('is_primary', False),
            effective_from=serializer.validated_data.get('effective_from'),
            effective_to=serializer.validated_data.get('effective_to'),
            actor_staff=actor
        )
        return Response(self.get_serializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='transfer')
    def transfer(self, request):
        serializer = TransferStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request)

        from apps.facilities.models import Facility, Department
        staff_prof = StaffProfile.objects.get(pk=serializer.validated_data['staff_profile_id'])
        new_fac = Facility.objects.get(pk=serializer.validated_data['new_facility_id'])
        new_dept = Department.objects.filter(pk=serializer.validated_data.get('new_department_id')).first()

        new_assignment = transfer_staff(
            staff_profile=staff_prof,
            new_facility=new_fac,
            new_department=new_dept,
            effective_date=serializer.validated_data.get('effective_date'),
            actor_staff=actor
        )
        return Response(FacilityAssignmentSerializer(new_assignment).data, status=status.HTTP_200_OK)

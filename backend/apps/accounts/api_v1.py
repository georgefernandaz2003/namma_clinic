"""
IAM REST API (v1).
Delegates all identity, role, and facility mutations to domain services.
Direct PUT/PATCH/DELETE mutations are disabled to enforce service workflows and audit trails.
Role and Permission catalogue definitions are system-level assets restricted to system superusers.
Staff administration and directory listing is restricted to authorized administrators (Superuser, DHO, Clinic Admin).
Operational clinical roles (DOCTOR, NURSE, COMPOUNDER, LAB_TECHNICIAN, PHARMACIST) are denied staff administration.
"""
import datetime
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import (
    Person, StaffProfile, RoleMaster, PermissionMaster, RolePermission,
    StaffRoleAssignment, StaffFacilityAssignment, StaffStatusChoices
)
from apps.accounts.serializers import (
    RoleMasterSerializer, PermissionMasterSerializer, RolePermissionSerializer,
    StaffRoleAssignmentSerializer
)
from apps.accounts.services import (
    create_staff_profile, update_staff_status, assign_role,
    end_role_assignment, assign_facility, transfer_staff,
    invite_staff, activate_staff, suspend_staff, deactivate_staff,
    is_administrative_staff
)
from apps.accounts.permissions import get_user_active_role_codes
from apps.common.permissions import get_request_staff
from apps.facilities.models import Facility, Department


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


class IsStaffAdministrator(permissions.BasePermission):
    """
    Restricts staff management and read-only directory listing to administrators:
    - Django System Superusers (Global scope)
    - DISTRICT_OFFICER / DHO (District scope)
    - HOSPITAL_ADMIN / Clinic Admin (Facility scope)
    Operational clinical roles (DOCTOR, NURSE, COMPOUNDER, LAB_TECHNICIAN, PHARMACIST)
    are strictly denied staff administration (HTTP 403 Forbidden).
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False
        if user.is_superuser:
            return True

        # Check live database role assignments
        active_roles = get_user_active_role_codes(user)
        admin_roles = {'DISTRICT_OFFICER', 'DHO', 'HOSPITAL_ADMIN', 'ADMIN'}
        if any(r in admin_roles for r in active_roles):
            return True

        # Staff profile status and administrative designation check
        staff = getattr(user, 'staff_profile', None)
        if staff and staff.status == StaffStatusChoices.ACTIVE:
            if is_administrative_staff(staff):
                return True

        return False


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
    """
    Read-only and mutation serializer for StaffProfile.
    Includes staff identity, account status, assigned roles with effective dates,
    primary facility assignment, and district context. Excludes passwords, hashes, JWTs.
    """
    person_details = PersonSerializer(source='person', read_only=True)
    person = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all(), write_only=True, required=False)
    roles = serializers.SerializerMethodField()
    facility_assignment = serializers.SerializerMethodField()
    district_context = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'person', 'person_details', 'employee_id',
            'designation', 'department', 'status', 'medical_council_reg_number',
            'roles', 'facility_assignment', 'district_context'
        ]
        read_only_fields = ['status']

    def get_roles(self, obj):
        today = datetime.date.today()
        assignments = obj.role_assignments.filter(is_active=True).select_related('role')
        return [
            {
                'id': a.id,
                'role_id': a.role.id,
                'role_code': a.role.code,
                'role_name': a.role.name,
                'effective_from': str(a.effective_from),
                'effective_to': str(a.effective_to) if a.effective_to else None,
                'is_active': a.is_active
            }
            for a in assignments
        ]

    def get_facility_assignment(self, obj):
        primary_fa = obj.facility_assignments.filter(is_primary=True, is_active=True).select_related('facility', 'department').first()
        if not primary_fa:
            # Fallback to any active facility assignment
            primary_fa = obj.facility_assignments.filter(is_active=True).select_related('facility', 'department').first()
        if primary_fa and primary_fa.facility:
            return {
                'facility_id': primary_fa.facility.id,
                'facility_name': primary_fa.facility.facility_name,
                'facility_code': primary_fa.facility.facility_code,
                'department_id': primary_fa.department_id,
                'department_name': primary_fa.department.name if primary_fa.department else None,
                'is_primary': primary_fa.is_primary,
                'effective_from': str(primary_fa.effective_from)
            }
        return None

    def get_district_context(self, obj):
        primary_fa = obj.facility_assignments.filter(is_primary=True, is_active=True).select_related('facility__district').first()
        if primary_fa and primary_fa.facility and primary_fa.facility.district:
            return {
                'district_id': primary_fa.facility.district.id,
                'district_name': primary_fa.facility.district.name,
                'district_code': getattr(primary_fa.facility.district, 'code', '')
            }
        user = getattr(obj, 'user_account', None)
        if user and user.assigned_district:
            return {
                'district_id': user.assigned_district.id,
                'district_name': user.assigned_district.name,
                'district_code': getattr(user.assigned_district, 'code', '')
            }
        return None


class InviteStaffSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    gender = serializers.CharField(max_length=10)
    date_of_birth = serializers.DateField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    employee_id = serializers.CharField(max_length=50)
    designation = serializers.CharField(max_length=100)
    role_id = serializers.IntegerField(required=False)
    role_code = serializers.CharField(max_length=50, required=False)
    facility_id = serializers.IntegerField()
    department_id = serializers.IntegerField(required=False, allow_null=True)
    medical_council_reg_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False)


class StaffStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StaffStatusChoices.values)


class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffRoleAssignment
        fields = ['id', 'staff', 'role', 'facility', 'effective_from', 'effective_to', 'is_active']
        read_only_fields = ['is_active']


class AssignRoleActionSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=False)
    role_code = serializers.CharField(max_length=50, required=False)
    facility_id = serializers.IntegerField(required=False, allow_null=True)
    effective_from = serializers.DateField(required=False)
    effective_to = serializers.DateField(required=False, allow_null=True)


class EndRoleAssignmentSerializer(serializers.Serializer):
    end_date = serializers.DateField(required=False)


class FacilityAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffFacilityAssignment
        fields = ['id', 'staff', 'facility', 'department', 'is_primary', 'effective_from', 'effective_to', 'is_active']
        read_only_fields = ['is_active']


class AssignFacilityActionSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    department_id = serializers.IntegerField(required=False, allow_null=True)
    is_primary = serializers.BooleanField(required=False, default=False)
    effective_from = serializers.DateField(required=False)
    effective_to = serializers.DateField(required=False, allow_null=True)


class TransferStaffSerializer(serializers.Serializer):
    new_facility_id = serializers.IntegerField()
    new_department_id = serializers.IntegerField(required=False, allow_null=True)
    effective_date = serializers.DateField(required=False)


class ReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class StaffProfileViewSet(viewsets.ModelViewSet):
    """
    Staff Administration ViewSet:
    - Lists and details staff profiles scoped to administrator's jurisdiction.
    - Actions: invite, activate, suspend, deactivate, assign-role, assign-facility, transfer.
    - Operational clinical users (DOCTOR, NURSE, etc.) receive HTTP 403 Forbidden.
    """
    serializer_class = StaffProfileSerializer
    permission_classes = [IsStaffAdministrator]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return StaffProfile.objects.none()

        # Django Superuser: Global scope
        if user.is_superuser:
            return StaffProfile.objects.all().select_related(
                'person', 'department'
            ).prefetch_related(
                'role_assignments__role', 'facility_assignments__facility'
            )

        active_roles = get_user_active_role_codes(user)

        # DISTRICT_OFFICER (DHO): Scoped strictly to assigned district
        if 'DISTRICT_OFFICER' in active_roles or getattr(user, 'role', None) == 'DISTRICT_OFFICER':
            dist_id = getattr(user, 'assigned_district_id', None)
            if not dist_id:
                return StaffProfile.objects.none()  # Fails closed on NULL district
            return StaffProfile.objects.filter(
                Q(facility_assignments__facility__district_id=dist_id, facility_assignments__is_active=True) |
                Q(department__facility__district_id=dist_id)
            ).distinct().select_related(
                'person', 'department'
            ).prefetch_related(
                'role_assignments__role', 'facility_assignments__facility'
            )

        # HOSPITAL_ADMIN (Clinic Admin): Scoped strictly to own facility
        if 'HOSPITAL_ADMIN' in active_roles or getattr(user, 'role', None) == 'HOSPITAL_ADMIN':
            fac_id = getattr(user, 'assigned_facility_id', None)
            if not fac_id and getattr(user, 'staff_profile', None):
                p_fa = user.staff_profile.facility_assignments.filter(is_primary=True, is_active=True).first()
                fac_id = p_fa.facility_id if p_fa else None
            if not fac_id:
                return StaffProfile.objects.none()
            return StaffProfile.objects.filter(
                Q(facility_assignments__facility_id=fac_id, facility_assignments__is_active=True) |
                Q(department__facility_id=fac_id)
            ).distinct().select_related(
                'person', 'department'
            ).prefetch_related(
                'role_assignments__role', 'facility_assignments__facility'
            )

        return StaffProfile.objects.none()

    def create(self, request, *args, **kwargs):
        """Legacy create action delegating to create_staff_profile."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = get_request_staff(request, required=False)

        profile = create_staff_profile(
            person=serializer.validated_data['person'],
            employee_id=serializer.validated_data['employee_id'],
            designation=serializer.validated_data['designation'],
            department=serializer.validated_data.get('department'),
            medical_council_reg_number=serializer.validated_data.get('medical_council_reg_number'),
            actor_staff=actor
        )
        return Response(self.get_serializer(profile).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='invite')
    def invite(self, request):
        """Authoritative domain action to invite a new staff member."""
        serializer = InviteStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        role_code = d.get('role_code')
        if not role_code and d.get('role_id'):
            r = RoleMaster.objects.filter(pk=d['role_id']).first()
            if r:
                role_code = r.code

        email = d.get('email') or f"{d['employee_id'].lower()}@nammaclinic.org"
        facility = Facility.objects.get(pk=d['facility_id'])
        department = Department.objects.filter(pk=d.get('department_id')).first() if d.get('department_id') else None

        staff_profile, _ = invite_staff(
            email=email,
            first_name=d['first_name'],
            last_name=d['last_name'],
            gender=d['gender'],
            date_of_birth=d['date_of_birth'],
            employee_id=d['employee_id'],
            designation=d['designation'],
            facility=facility,
            role_code=role_code,
            department=department,
            phone_number=d.get('phone_number'),
            actor=request.user
        )
        return Response(self.get_serializer(staff_profile).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Authoritative domain action to activate staff and enable operational authorization."""
        profile = self.get_object()
        activated = activate_staff(profile, actor=request.user)
        return Response(self.get_serializer(activated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """Authoritative domain action to suspend staff and revoke operational access."""
        profile = self.get_object()
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suspended = suspend_staff(profile, reason=serializer.validated_data.get('reason'), actor=request.user)
        return Response(self.get_serializer(suspended).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Authoritative domain action to permanently deactivate staff and end postings."""
        profile = self.get_object()
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deactivated = deactivate_staff(profile, reason=serializer.validated_data.get('reason'), actor=request.user)
        return Response(self.get_serializer(deactivated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-role')
    def assign_role_action(self, request, pk=None):
        """Authoritative domain action to assign an operational role to staff."""
        profile = self.get_object()
        serializer = AssignRoleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        role = None
        if d.get('role_id'):
            role = RoleMaster.objects.get(pk=d['role_id'])
        elif d.get('role_code'):
            role = RoleMaster.objects.get(code=d['role_code'])

        facility = Facility.objects.filter(pk=d.get('facility_id')).first() if d.get('facility_id') else None

        assignment = assign_role(
            staff_profile=profile,
            role=role,
            facility=facility,
            effective_from=d.get('effective_from'),
            effective_to=d.get('effective_to'),
            actor=request.user
        )
        return Response(RoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='assign-facility')
    def assign_facility_action(self, request, pk=None):
        """Authoritative domain action to assign staff to a facility."""
        profile = self.get_object()
        serializer = AssignFacilityActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        facility = Facility.objects.get(pk=d['facility_id'])
        department = Department.objects.filter(pk=d.get('department_id')).first() if d.get('department_id') else None

        assignment = assign_facility(
            staff_profile=profile,
            facility=facility,
            department=department,
            is_primary=d.get('is_primary', False),
            effective_from=d.get('effective_from'),
            effective_to=d.get('effective_to'),
            actor=request.user
        )
        return Response(FacilityAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer_action(self, request, pk=None):
        """Authoritative domain action to atomically transfer staff to a new facility."""
        profile = self.get_object()
        serializer = TransferStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        new_fac = Facility.objects.get(pk=d['new_facility_id'])
        new_dept = Department.objects.filter(pk=d.get('new_department_id')).first() if d.get('new_department_id') else None

        new_assignment = transfer_staff(
            staff_profile=profile,
            new_facility=new_fac,
            new_department=new_dept,
            effective_date=d.get('effective_date'),
            actor=request.user
        )
        return Response(FacilityAssignmentSerializer(new_assignment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Legacy status update action mapping to authoritative domain services."""
        profile = self.get_object()
        serializer = StaffStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_status = serializer.validated_data['status']

        if target_status == StaffStatusChoices.SUSPENDED:
            updated = suspend_staff(profile, actor=request.user)
        elif target_status == StaffStatusChoices.DEACTIVATED:
            updated = deactivate_staff(profile, actor=request.user)
        elif target_status == StaffStatusChoices.ACTIVE:
            updated = activate_staff(profile, actor=request.user)
        else:
            actor = get_request_staff(request, required=False)
            updated = update_staff_status(profile, target_status, actor_staff=actor)

        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    """
    Role Assignment ViewSet:
    Creates and ends dynamic role assignments for staff.
    """
    queryset = StaffRoleAssignment.objects.all().select_related('staff', 'role', 'facility')
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsStaffAdministrator]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = assign_role(
            staff_profile=serializer.validated_data['staff'],
            role=serializer.validated_data['role'],
            facility=serializer.validated_data.get('facility'),
            effective_from=serializer.validated_data.get('effective_from'),
            effective_to=serializer.validated_data.get('effective_to'),
            actor=request.user
        )
        return Response(self.get_serializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='end-assignment')
    def end_assignment(self, request, pk=None):
        assignment = self.get_object()
        serializer = EndRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ended = end_role_assignment(
            assignment,
            end_date=serializer.validated_data.get('end_date'),
            actor=request.user
        )
        return Response(self.get_serializer(ended).data, status=status.HTTP_200_OK)


class FacilityAssignmentViewSet(viewsets.ModelViewSet):
    """
    Facility Assignment ViewSet:
    Creates postings and executes atomic staff transfers.
    """
    queryset = StaffFacilityAssignment.objects.all().select_related('staff', 'facility', 'department')
    serializer_class = FacilityAssignmentSerializer
    permission_classes = [IsStaffAdministrator]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = assign_facility(
            staff_profile=serializer.validated_data['staff'],
            facility=serializer.validated_data['facility'],
            department=serializer.validated_data.get('department'),
            is_primary=serializer.validated_data.get('is_primary', False),
            effective_from=serializer.validated_data.get('effective_from'),
            effective_to=serializer.validated_data.get('effective_to'),
            actor=request.user
        )
        return Response(self.get_serializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='transfer')
    def transfer(self, request):
        staff_id = request.data.get('staff_profile_id')
        new_fac_id = request.data.get('new_facility_id')
        new_dept_id = request.data.get('new_department_id')
        eff_date = request.data.get('effective_date')

        if not staff_id or not new_fac_id:
            return Response(
                {"error": "staff_profile_id and new_facility_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        staff_prof = StaffProfile.objects.get(pk=staff_id)
        new_fac = Facility.objects.get(pk=new_fac_id)
        new_dept = Department.objects.filter(pk=new_dept_id).first() if new_dept_id else None

        new_assignment = transfer_staff(
            staff_profile=staff_prof,
            new_facility=new_fac,
            new_department=new_dept,
            effective_date=eff_date,
            actor=request.user
        )
        return Response(FacilityAssignmentSerializer(new_assignment).data, status=status.HTTP_200_OK)

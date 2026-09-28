from rest_framework import serializers
from apps.accounts.models import User, RoleMaster, PermissionMaster, RolePermission, StaffRoleAssignment, StaffProfile
from apps.accounts.permissions import get_user_role_permissions

class UserSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='assigned_facility.facility_name')
    facility_type = serializers.ReadOnlyField(source='assigned_facility.facility_type')
    district_name = serializers.ReadOnlyField(source='assigned_district.name')
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role',
            'role_display', 'assigned_facility', 'facility_name',
            'facility_type', 'assigned_district', 'district_name'
        ]

class UserProfileSerializer(serializers.ModelSerializer):
    facility_details = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    scope_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role',
            'role_display', 'roles', 'assigned_facility', 'assigned_district',
            'facility_details', 'permissions', 'scope_type'
        ]

    def get_roles(self, obj):
        from apps.accounts.permissions import get_user_active_role_codes
        return sorted(list(get_user_active_role_codes(obj)))

    def get_facility_details(self, obj):
        if obj.assigned_facility:
            return {
                'id': obj.assigned_facility.id,
                'facility_code': obj.assigned_facility.facility_code,
                'facility_name': obj.assigned_facility.facility_name,
                'facility_type': obj.assigned_facility.facility_type,
                'district_name': obj.assigned_facility.district.name if obj.assigned_facility.district else ''
            }
        return None

    def get_permissions(self, obj):
        return sorted(list(get_user_role_permissions(obj)))

    def get_scope_type(self, obj):
        if obj.role == 'DISTRICT_OFFICER':
            return 'DISTRICT'
        return 'FACILITY'

class PermissionMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionMaster
        fields = [
            'id', 'code', 'name', 'display_name', 'description',
            'domain', 'action', 'is_active', 'created_at', 'updated_at'
        ]

class RolePermissionSerializer(serializers.ModelSerializer):
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'role_code', 'permission', 'permission_code',
            'permission_name', 'is_active', 'created_at', 'updated_at'
        ]

class RoleMasterSerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()
    permission_codes = serializers.SerializerMethodField()

    class Meta:
        model = RoleMaster
        fields = [
            'id', 'code', 'name', 'display_name', 'description',
            'scope_level', 'is_system_role', 'is_active',
            'permissions_count', 'permission_codes',
            'created_at', 'updated_at'
        ]

    def get_permissions_count(self, obj):
        return obj.role_permissions.filter(is_active=True).count()

    def get_permission_codes(self, obj):
        return list(obj.role_permissions.filter(is_active=True).values_list('permission__code', flat=True))


class StaffRoleAssignmentSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source='role.code', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    employee_id = serializers.CharField(source='staff.employee_id', read_only=True)
    facility_name = serializers.CharField(source='facility.facility_name', read_only=True)

    class Meta:
        model = StaffRoleAssignment
        fields = [
            'id', 'staff', 'employee_id', 'role', 'role_code', 'role_name',
            'facility', 'facility_name', 'effective_from', 'effective_to',
            'is_active', 'created_at', 'updated_at'
        ]

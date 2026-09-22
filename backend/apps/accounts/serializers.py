from rest_framework import serializers
from apps.accounts.models import User, RoleChoices

class UserSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='assigned_facility.facility_name')
    facility_type = serializers.ReadOnlyField(source='assigned_facility.facility_type')
    district_name = serializers.ReadOnlyField(source='assigned_district.name')
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'full_name', 'email', 'phone', 'role',
            'role_display', 'assigned_facility', 'facility_name',
            'facility_type', 'assigned_district', 'district_name'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return attrs

        user = request.user
        role = attrs.get('role', self.instance.role if self.instance else None)
        assigned_facility = attrs.get('assigned_facility', self.instance.assigned_facility if self.instance else None)
        assigned_district = attrs.get('assigned_district', self.instance.assigned_district if self.instance else None)

        # 1. Non-admin clinical users must not modify/create users
        if user.role in [RoleChoices.DOCTOR, RoleChoices.NURSE, RoleChoices.LAB_TECHNICIAN, RoleChoices.PHARMACIST]:
            raise serializers.ValidationError("Clinical staff do not have permission to manage user accounts.")

        # 2. District Officer must not mutate users
        if user.role == RoleChoices.DISTRICT_OFFICER:
            raise serializers.ValidationError("District Officers have read-only access and cannot modify user accounts.")

        # 3. Hospital Admin business rules & privilege escalation prevention
        if user.role == RoleChoices.HOSPITAL_ADMIN:
            # Cannot create or escalate user to DISTRICT_OFFICER
            if role == RoleChoices.DISTRICT_OFFICER:
                raise serializers.ValidationError({
                    'role': 'Hospital administrators cannot create or assign District Officer accounts.'
                })

            # Cannot assign district-level accounts
            if assigned_district:
                raise serializers.ValidationError({
                    'assigned_district': 'Hospital administrators cannot assign district-level accounts.'
                })

            # Must belong to user's assigned facility
            user_fac = user.assigned_facility
            if not user_fac:
                raise serializers.ValidationError({
                    'assigned_facility': 'You must be assigned to a facility to manage staff.'
                })

            if assigned_facility and assigned_facility != user_fac:
                raise serializers.ValidationError({
                    'assigned_facility': 'You cannot assign users to another facility.'
                })

            # Auto-assign Hospital Admin's facility on creation if not explicitly passed
            if not self.instance and not assigned_facility:
                attrs['assigned_facility'] = user_fac

        # 4. Prevent users from modifying their own role, facility, or district through arbitrary PATCH
        if self.instance and self.instance.id == user.id:
            if 'role' in attrs and attrs['role'] != self.instance.role:
                raise serializers.ValidationError({
                    'role': 'You cannot modify your own role.'
                })
            if 'assigned_facility' in attrs and attrs['assigned_facility'] != self.instance.assigned_facility:
                raise serializers.ValidationError({
                    'assigned_facility': 'You cannot modify your own assigned facility.'
                })
            if 'assigned_district' in attrs and attrs['assigned_district'] != self.instance.assigned_district:
                raise serializers.ValidationError({
                    'assigned_district': 'You cannot modify your own assigned district.'
                })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    facility_details = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    permissions = serializers.SerializerMethodField()
    scope_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role',
            'role_display', 'assigned_facility', 'assigned_district',
            'facility_details', 'permissions', 'scope_type'
        ]

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
        from apps.accounts.permissions import ROLE_PERMISSIONS
        return list(ROLE_PERMISSIONS.get(obj.role, set()))

    def get_scope_type(self, obj):
        if obj.role == 'DISTRICT_OFFICER':
            return 'DISTRICT'
        return 'FACILITY'


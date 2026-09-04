from rest_framework import serializers
from apps.accounts.models import User

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

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role',
            'role_display', 'assigned_facility', 'assigned_district', 'facility_details'
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

from rest_framework import serializers
from apps.geography.models import State, District
from apps.facilities.models import (
    Facility, FacilityRelationship, FacilityOxygenSupply,
    FacilityConsumableInventory, FacilityMaintenanceTicket,
    FacilityBedCapacity, FacilityBedAllocation
)

class FacilityRelationshipSerializer(serializers.ModelSerializer):
    source_name = serializers.ReadOnlyField(source='source_facility.facility_name')
    source_type = serializers.ReadOnlyField(source='source_facility.facility_type')
    destination_name = serializers.ReadOnlyField(source='destination_facility.facility_name')
    destination_type = serializers.ReadOnlyField(source='destination_facility.facility_type')

    class Meta:
        model = FacilityRelationship
        fields = '__all__'

class FacilitySerializer(serializers.ModelSerializer):
    district_name = serializers.ReadOnlyField(source='district.name')
    zone_name = serializers.ReadOnlyField(source='zone.name')
    ward_name = serializers.ReadOnlyField(source='ward.name')
    parent_name = serializers.ReadOnlyField(source='parent_facility.facility_name')
    outgoing_relationships = FacilityRelationshipSerializer(many=True, read_only=True)
    incoming_relationships = FacilityRelationshipSerializer(many=True, read_only=True)
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), required=False)

    class Meta:
        model = Facility
        fields = '__all__'

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


class FacilityOxygenSupplySerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = FacilityOxygenSupply
        fields = '__all__'


class FacilityConsumableInventorySerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = FacilityConsumableInventory
        fields = '__all__'


class FacilityMaintenanceTicketSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = FacilityMaintenanceTicket
        fields = '__all__'


class FacilityBedCapacitySerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    available_beds = serializers.ReadOnlyField()

    class Meta:
        model = FacilityBedCapacity
        fields = '__all__'


class FacilityBedAllocationSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = FacilityBedAllocation
        fields = '__all__'


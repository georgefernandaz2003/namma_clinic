from rest_framework import serializers
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

    class Meta:
        model = Facility
        fields = '__all__'


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


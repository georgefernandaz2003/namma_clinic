from rest_framework import serializers
from apps.patients.models import Patient, Household

class PatientSerializer(serializers.ModelSerializer):
    ward_name = serializers.ReadOnlyField(source='ward.name')
    district_name = serializers.ReadOnlyField(source='district.name')
    facility_name = serializers.ReadOnlyField(source='registered_at_facility.facility_name')

    class Meta:
        model = Patient
        fields = '__all__'

class HouseholdSerializer(serializers.ModelSerializer):
    ward_name = serializers.ReadOnlyField(source='ward.name')

    class Meta:
        model = Household
        fields = '__all__'

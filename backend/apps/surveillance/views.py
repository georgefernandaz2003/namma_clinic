from rest_framework import serializers, viewsets, permissions
from apps.surveillance.models import DiseaseCase
from apps.surveillance.demographic_services import (
    calculate_age,
    get_case_patient_age,
    get_age_group,
    normalize_gender
)

class DiseaseCaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    ward_name = serializers.ReadOnlyField(source='ward.name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    patient_age = serializers.SerializerMethodField()
    patient_age_group = serializers.SerializerMethodField()
    patient_gender = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseCase
        fields = '__all__'

    def get_patient_age(self, obj):
        return get_case_patient_age(obj)

    def get_patient_age_group(self, obj):
        age = self.get_patient_age(obj)
        return get_age_group(age)

    def get_patient_gender(self, obj):
        if obj.patient:
            return normalize_gender(obj.patient.gender)
        return 'UNKNOWN'

class DiseaseCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseCase.objects.all().select_related('patient', 'facility', 'ward')
    serializer_class = DiseaseCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'ward', 'disease_name', 'severity']

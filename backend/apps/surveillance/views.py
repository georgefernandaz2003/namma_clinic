from rest_framework import serializers, viewsets, permissions
from apps.surveillance.models import DiseaseCase

class DiseaseCaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    ward_name = serializers.ReadOnlyField(source='ward.name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = DiseaseCase
        fields = '__all__'

class DiseaseCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseCase.objects.all().select_related('patient', 'facility', 'ward')
    serializer_class = DiseaseCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'ward', 'disease_name', 'severity']

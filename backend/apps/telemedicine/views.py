from rest_framework import serializers, viewsets, permissions
from apps.telemedicine.models import Teleconsultation

class TeleconsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    clinic_facility_name = serializers.ReadOnlyField(source='clinic_facility.facility_name')
    hub_facility_name = serializers.ReadOnlyField(source='hub_facility.facility_name')

    class Meta:
        model = Teleconsultation
        fields = '__all__'

class TeleconsultationViewSet(viewsets.ModelViewSet):
    queryset = Teleconsultation.objects.all().select_related('patient', 'clinic_facility', 'hub_facility')
    serializer_class = TeleconsultationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['clinic_facility', 'hub_facility', 'status']

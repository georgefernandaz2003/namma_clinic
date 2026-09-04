from rest_framework import serializers, viewsets, permissions
from apps.ncd.models import NCDRecord

class NCDRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = NCDRecord
        fields = '__all__'

class NCDRecordViewSet(viewsets.ModelViewSet):
    queryset = NCDRecord.objects.all().select_related('patient', 'facility')
    serializer_class = NCDRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'risk_level', 'control_status']

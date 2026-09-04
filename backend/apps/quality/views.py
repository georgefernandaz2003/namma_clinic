from rest_framework import serializers, viewsets, permissions
from apps.quality.models import QualityChecklist, BiomedicalWasteLog

class QualityChecklistSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = QualityChecklist
        fields = '__all__'

class BiomedicalWasteLogSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = BiomedicalWasteLog
        fields = '__all__'

class QualityChecklistViewSet(viewsets.ModelViewSet):
    queryset = QualityChecklist.objects.all().select_related('facility')
    serializer_class = QualityChecklistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility']

class BiomedicalWasteLogViewSet(viewsets.ModelViewSet):
    queryset = BiomedicalWasteLog.objects.all().select_related('facility')
    serializer_class = BiomedicalWasteLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility']

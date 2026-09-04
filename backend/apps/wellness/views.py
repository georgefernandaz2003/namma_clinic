from rest_framework import serializers, viewsets, permissions
from apps.wellness.models import WellnessSession

class WellnessSessionSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = WellnessSession
        fields = '__all__'

class WellnessSessionViewSet(viewsets.ModelViewSet):
    queryset = WellnessSession.objects.all().select_related('facility')
    serializer_class = WellnessSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility']

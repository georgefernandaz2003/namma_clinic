from rest_framework import serializers, viewsets, permissions
from apps.alerts.models import Alert

class AlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = Alert
        fields = '__all__'

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().select_related('facility', 'patient', 'assigned_user')
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'status', 'severity', 'alert_type']

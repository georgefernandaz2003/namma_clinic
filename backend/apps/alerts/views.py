from rest_framework import serializers, viewsets, permissions
from apps.alerts.models import Alert
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class AlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = Alert
        fields = '__all__'

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'dashboard.view'
    filterset_fields = ['facility', 'status', 'severity', 'alert_type']

    def get_queryset(self):
        queryset = Alert.objects.all().select_related('facility', 'patient', 'assigned_user').order_by('-created_at', '-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

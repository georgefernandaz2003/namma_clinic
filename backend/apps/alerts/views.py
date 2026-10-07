from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.alerts.models import Alert
from apps.accounts.permissions import (
    get_accessible_facility_ids_for_user,
    can_access_facility,
    HasPermission,
    HasFacilityScope
)
from apps.surveillance.intelligence_alert_services import acknowledge_alert, resolve_alert


class AlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    district_name = serializers.ReadOnlyField(source='district.name')
    acknowledged_by_username = serializers.ReadOnlyField(source='acknowledged_by.username')
    resolved_by_username = serializers.ReadOnlyField(source='resolved_by.username')

    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = [
            'id',
            'alert_type',
            'facility',
            'district',
            'patient',
            'title',
            'description',
            'status',
            'severity',
            'fingerprint',
            'metadata',
            'created_at',
            'assigned_user',
            'acknowledged_at',
            'acknowledged_by',
            'resolved_at',
            'resolved_by',
            'resolution_notes',
        ]


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'dashboard.view'
    filterset_fields = ['facility', 'status', 'severity', 'alert_type']

    def get_queryset(self):
        queryset = Alert.objects.all().select_related(
            'facility', 'district', 'patient', 'assigned_user', 'acknowledged_by', 'resolved_by'
        ).order_by('-created_at', '-id')
        user = self.request.user
        accessible_ids = get_accessible_facility_ids_for_user(user)

        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)

        facility_param = self.request.query_params.get('facility')
        if facility_param:
            if not getattr(user, 'is_superuser', False) and not can_access_facility(user, facility_param):
                raise PermissionDenied("You do not have authorization to access resources outside your assigned facility.")
            queryset = queryset.filter(facility_id=facility_param)

        return queryset

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        if new_status == 'ACKNOWLEDGED':
            try:
                acknowledge_alert(instance, request.user)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        elif new_status == 'RESOLVED':
            notes = request.data.get('resolution_notes', '')
            resolve_alert(instance, request.user, resolution_notes=notes)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        elif new_status:
            return Response(
                {'error': f"Invalid status '{new_status}'. Use ACKNOWLEDGED or RESOLVED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'patch'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        instance = self.get_object()
        try:
            acknowledge_alert(instance, request.user)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post', 'patch'], url_path='resolve')
    def resolve(self, request, pk=None):
        instance = self.get_object()
        notes = request.data.get('resolution_notes', '')
        resolve_alert(instance, request.user, resolution_notes=notes)
        return Response(self.get_serializer(instance).data)

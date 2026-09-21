from rest_framework import serializers, viewsets, permissions
from apps.ncd.models import NCDRecord
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class NCDRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = NCDRecord
        fields = '__all__'

class NCDRecordViewSet(viewsets.ModelViewSet):
    serializer_class = NCDRecordSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'ncd.view',
        'POST': 'ncd.create',
        'PUT': 'ncd.update',
        'PATCH': 'ncd.update',
        'DELETE': 'ncd.update'
    }
    filterset_fields = ['facility', 'risk_level', 'control_status']

    def get_queryset(self):
        queryset = NCDRecord.objects.all().select_related('patient', 'facility').order_by('-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)

        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

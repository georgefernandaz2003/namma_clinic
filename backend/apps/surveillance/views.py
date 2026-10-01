from rest_framework import serializers, viewsets, permissions
from apps.surveillance.models import DiseaseCase
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class DiseaseCaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    ward_name = serializers.ReadOnlyField(source='ward.name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = DiseaseCase
        fields = '__all__'

class DiseaseCaseViewSet(viewsets.ModelViewSet):
    serializer_class = DiseaseCaseSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'surveillance.view',
        'POST': 'surveillance.create',
        'PUT': 'surveillance.update',
        'PATCH': 'surveillance.update',
        'DELETE': 'surveillance.update'
    }
    filterset_fields = ['facility', 'ward', 'disease_name', 'severity']

    def get_queryset(self):
        queryset = DiseaseCase.objects.all().select_related('patient', 'facility', 'ward').order_by('-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)

        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

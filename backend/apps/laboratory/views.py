from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.laboratory.models import LabTestMaster, LabOrder, LabSample, LabResult

class LabTestMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestMaster
        fields = '__all__'

class LabSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabSample
        fields = '__all__'

class LabResultSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.ReadOnlyField(source='verified_by.full_name')

    class Meta:
        model = LabResult
        fields = '__all__'

class LabOrderSerializer(serializers.ModelSerializer):
    test_name = serializers.ReadOnlyField(source='test_master.name')
    test_code = serializers.ReadOnlyField(source='test_master.code')
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    sample = LabSampleSerializer(read_only=True)
    result = LabResultSerializer(read_only=True)

    class Meta:
        model = LabOrder
        fields = '__all__'

class LabTestMasterViewSet(viewsets.ModelViewSet):
    queryset = LabTestMaster.objects.all()
    serializer_class = LabTestMasterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

from apps.accounts.permissions import get_accessible_facility_ids_for_user

class LabOrderViewSet(viewsets.ModelViewSet):
    serializer_class = LabOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'status', 'patient']

    def get_queryset(self):
        queryset = LabOrder.objects.all().select_related('test_master', 'patient', 'facility', 'doctor')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

    @action(detail=True, methods=['post'], url_path='collect-sample')
    def collect_sample(self, request, pk=None):
        order = self.get_object()
        sample_code = request.data.get('sample_code') or f"SMP-{order.id:04d}"
        sample_type = request.data.get('sample_type', 'Blood / Serum')
        sample, _ = LabSample.objects.get_or_create(
            lab_order=order,
            defaults={'sample_type': sample_type, 'sample_code': sample_code, 'collected_by': request.user}
        )
        order.status = 'SAMPLE_COLLECTED'
        order.save()
        return Response({'status': 'Sample collected', 'sample': LabSampleSerializer(sample).data})

    @action(detail=True, methods=['post'], url_path='save-result')
    def save_result(self, request, pk=None):
        order = self.get_object()
        res_val = request.data.get('result_value', 'Normal')
        flag = request.data.get('interpretation_flag', 'NORMAL')
        notes = request.data.get('notes', '')

        result, _ = LabResult.objects.get_or_create(
            lab_order=order,
            defaults={
                'result_value': res_val,
                'unit': request.data.get('unit') or order.test_master.unit,
                'reference_range': request.data.get('reference_range') or order.test_master.reference_range,
                'interpretation_flag': flag,
                'verified_by': request.user,
                'notes': notes
            }
        )
        order.status = 'VERIFIED'
        order.save()
        return Response({'status': 'Result verified & released', 'result': LabResultSerializer(result).data})

    @action(detail=True, methods=['post'], url_path='enter_result')
    def enter_result(self, request, pk=None):
        return self.save_result(request, pk=pk)

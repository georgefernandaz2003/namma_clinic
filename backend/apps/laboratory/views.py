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
    token_number = serializers.ReadOnlyField(source='visit.token.token_number')
    visit_code = serializers.ReadOnlyField(source='visit.visit_id')
    sample = LabSampleSerializer(read_only=True)
    sample_details = LabSampleSerializer(source='sample', read_only=True)
    result = LabResultSerializer(read_only=True)

    class Meta:
        model = LabOrder
        fields = '__all__'

from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope
from apps.audit.models import AuditLog
import datetime

class LabTestMasterViewSet(viewsets.ModelViewSet):
    queryset = LabTestMaster.objects.all().order_by('id')
    serializer_class = LabTestMasterSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        HasPermission
    ]
    required_permissions = {
        'GET': 'lab_test_master.view',
        'POST': 'lab_test_master.create',
        'PUT': 'lab_test_master.update',
        'PATCH': 'lab_test_master.update',
        'DELETE': 'lab_test_master.delete',
        'list': 'lab_test_master.view',
        'retrieve': 'lab_test_master.view',
        'create': 'lab_test_master.create',
        'update': 'lab_test_master.update',
        'partial_update': 'lab_test_master.update',
        'destroy': 'lab_test_master.delete',
    }

class LabOrderViewSet(viewsets.ModelViewSet):
    serializer_class = LabOrderSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'lab_orders.view',
        'POST': 'lab_orders.create',
        'collect_sample': 'lab_orders.update',
        'save_result': 'lab_results.create',
        'enter_result': 'lab_results.create',
        'PUT': 'lab_orders.update',
        'PATCH': 'lab_orders.update',
        'DELETE': 'lab_orders.update'
    }
    filterset_fields = ['facility', 'status', 'patient', 'visit']


    def get_queryset(self):
        queryset = LabOrder.objects.all().select_related('test_master', 'patient', 'facility', 'doctor', 'visit', 'visit__token').order_by('-order_date', '-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)

        # Date filtering (supports YYYY-MM-DD or 'all')
        req_date = self.request.query_params.get('date', None)
        if req_date and req_date != 'all':
            try:
                target_date = datetime.datetime.strptime(req_date, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__date=target_date)
            except ValueError:
                pass

        return queryset

    def create(self, request, *args, **kwargs):
        visit_id = request.data.get('visit')
        test_master_id = request.data.get('test_master')
        if visit_id and test_master_id:
            existing = LabOrder.objects.filter(visit_id=visit_id, test_master_id=test_master_id).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        doctor = serializer.validated_data.get('doctor') or self.request.user
        order = serializer.save(doctor=doctor)

        # Connect with active OPD Visit and synchronize queue status
        from apps.visits.models import Visit
        target_visit = order.visit
        if not target_visit and order.patient and order.facility:
            target_visit = Visit.objects.filter(
                patient=order.patient,
                facility=order.facility,
                opd_date=order.order_date.date() if order.order_date else datetime.date.today()
            ).exclude(status='COMPLETED').first()
            if target_visit:
                order.visit = target_visit
                order.save(update_fields=['visit'])

        if target_visit and target_visit.status != 'COMPLETED':
            target_visit.current_queue = 'LAB'
            target_visit.status = 'LAB_PENDING'
            target_visit.save(update_fields=['current_queue', 'status'])

    @action(detail=True, methods=['post'], url_path='collect-sample')
    def collect_sample(self, request, pk=None):
        order = self.get_object()
        sample_code = request.data.get('sample_code') or f"SMP-{order.id:04d}"
        sample_type = request.data.get('sample_type', 'Blood / Serum')

        # Check for sample_code uniqueness collision with another order
        import uuid
        existing_sample = LabSample.objects.filter(sample_code=sample_code).exclude(lab_order=order).first()
        if existing_sample:
            sample_code = f"SMP-{order.id:04d}-{uuid.uuid4().hex[:4].upper()}"

        sample, created = LabSample.objects.get_or_create(
            lab_order=order,
            defaults={'sample_type': sample_type, 'sample_code': sample_code, 'collected_by': request.user}
        )
        if not created:
            sample.sample_type = sample_type
            if not sample.collected_by:
                sample.collected_by = request.user
            sample.save()

        order.status = 'SAMPLE_COLLECTED'
        order.save(update_fields=['status'])

        # Update visit queue status to in-progress
        if order.visit and order.visit.status != 'COMPLETED':
            order.visit.current_queue = 'LAB'
            order.visit.status = 'LAB_IN_PROGRESS'
            order.visit.save(update_fields=['current_queue', 'status'])

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='LAB_SAMPLE_COLLECTED',
            facility=order.facility,
            details=f"Specimen collected for Lab Order #{order.id} ({order.test_master.name}). Barcode: {sample.sample_code}"
        )

        return Response({'status': 'Sample collected', 'sample': LabSampleSerializer(sample).data})

    @action(detail=True, methods=['post'], url_path='save-result')
    def save_result(self, request, pk=None):
        order = self.get_object()
        res_val = request.data.get('result_value', 'Normal')
        flag = request.data.get('interpretation_flag', 'NORMAL')
        notes = request.data.get('notes', '')

        result, created = LabResult.objects.get_or_create(
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
        if not created:
            result.result_value = res_val
            result.unit = request.data.get('unit') or result.unit or order.test_master.unit
            result.reference_range = request.data.get('reference_range') or result.reference_range or order.test_master.reference_range
            result.interpretation_flag = flag
            result.verified_by = request.user
            result.notes = notes
            result.save()

        order.status = 'VERIFIED'
        order.save(update_fields=['status'])

        # Check if all lab orders for this patient/visit are verified
        if order.visit and order.visit.status != 'COMPLETED':
            pending_orders = LabOrder.objects.filter(visit=order.visit).exclude(status__in=['VERIFIED', 'CANCELLED']).count()
            if pending_orders == 0:
                order.visit.current_queue = 'DOCTOR'
                order.visit.status = 'LAB_COMPLETED'
                order.visit.save(update_fields=['current_queue', 'status'])

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='LAB_RESULT_VERIFIED',
            facility=order.facility,
            details=f"Result verified for Lab Order #{order.id} ({order.test_master.name}): {result.result_value} [{result.interpretation_flag}]"
        )

        return Response({'status': 'Result verified & released', 'result': LabResultSerializer(result).data})

    @action(detail=True, methods=['post'], url_path='enter_result')
    def enter_result(self, request, pk=None):
        return self.save_result(request, pk=pk)

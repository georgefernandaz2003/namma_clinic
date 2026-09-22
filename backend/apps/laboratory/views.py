from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models
import datetime
from apps.laboratory.models import LabTestMaster, LabToken, LabOrder, LabSample, LabResult
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope
from apps.audit.models import AuditLog

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

class LabTokenSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    visit_id_str = serializers.ReadOnlyField(source='visit.visit_id')
    opd_token_number = serializers.ReadOnlyField(source='visit.token.token_number')
    patient_name = serializers.ReadOnlyField(source='visit.patient.name')

    class Meta:
        model = LabToken
        fields = '__all__'

class LabOrderSerializer(serializers.ModelSerializer):
    test_name = serializers.ReadOnlyField(source='test_master.name')
    test_code = serializers.ReadOnlyField(source='test_master.code')
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    lab_token_code = serializers.ReadOnlyField(source='lab_token.token_code')
    lab_token_number = serializers.ReadOnlyField(source='lab_token.token_number')
    lab_token_status = serializers.ReadOnlyField(source='lab_token.status')
    opd_token_number = serializers.ReadOnlyField(source='visit.token.token_number')
    sample = LabSampleSerializer(read_only=True)
    sample_details = LabSampleSerializer(source='sample', read_only=True)
    result = LabResultSerializer(read_only=True)

    class Meta:
        model = LabOrder
        fields = '__all__'

class LabTestMasterViewSet(viewsets.ModelViewSet):
    queryset = LabTestMaster.objects.all()
    serializer_class = LabTestMasterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LabTokenViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabTokenSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'list': 'lab_orders.view',
        'retrieve': 'lab_orders.view',
        'GET': 'lab_orders.view'
    }
    filterset_fields = ['facility', 'status', 'visit', 'date']

    def get_queryset(self):
        queryset = LabToken.objects.all().select_related('facility', 'visit', 'visit__patient').order_by('-date', '-token_number')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        visit_param = self.request.query_params.get('visit')
        if visit_param:
            queryset = queryset.filter(visit_id=visit_param)
        return queryset


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
    filterset_fields = ['facility', 'status', 'patient', 'visit', 'consultation', 'lab_token']

    def get_queryset(self):
        queryset = LabOrder.objects.all().select_related(
            'test_master', 'patient', 'facility', 'doctor', 'lab_token', 'visit'
        ).order_by('-order_date', '-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        visit_param = self.request.query_params.get('visit')
        if visit_param:
            queryset = queryset.filter(visit_id=visit_param)
        consultation_param = self.request.query_params.get('consultation')
        if consultation_param:
            queryset = queryset.filter(consultation_id=consultation_param)
        lab_token_param = self.request.query_params.get('lab_token')
        if lab_token_param:
            queryset = queryset.filter(lab_token_id=lab_token_param)
        patient_param = self.request.query_params.get('patient')
        if patient_param:
            queryset = queryset.filter(patient_id=patient_param)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        from apps.visits.models import Visit, VisitStatusHistory
        from apps.consultations.models import Consultation

        data = request.data
        patient_id = data.get('patient')
        facility_id = data.get('facility')
        consultation_id = data.get('consultation')
        visit_id = data.get('visit')
        test_master_id = data.get('test_master')
        test_ids = data.get('test_ids') or []
        if hasattr(request.data, 'getlist'):
            raw_list = request.data.getlist('test_ids')
            if raw_list and len(raw_list) > len(test_ids):
                test_ids = raw_list

        if test_master_id:
            try:
                tm_int = int(test_master_id)
                if tm_int not in test_ids:
                    test_ids = [tm_int] + [int(x) for x in test_ids if int(x) != tm_int]
            except (ValueError, TypeError):
                if test_master_id not in test_ids:
                    test_ids = [test_master_id] + list(test_ids)

        if not test_ids:
            return Response({'error': 'At least one lab test must be specified.'}, status=status.HTTP_400_BAD_REQUEST)
        if not patient_id:
            return Response({'error': 'Patient is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not facility_id:
            return Response({'error': 'Facility is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient_id = int(patient_id)
            facility_id = int(facility_id)
            if consultation_id:
                consultation_id = int(consultation_id)
            if visit_id:
                visit_id = int(visit_id)
        except (ValueError, TypeError):
            pass

        consultation = None
        if consultation_id:
            consultation = Consultation.objects.filter(id=consultation_id).first()
            if not consultation:
                return Response({'error': f'Consultation #{consultation_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)
            if consultation.patient_id != patient_id:
                return Response({'error': 'Consultation does not belong to specified patient.'}, status=status.HTTP_400_BAD_REQUEST)
            if consultation.facility_id != facility_id:
                return Response({'error': 'Consultation does not belong to specified facility.'}, status=status.HTTP_400_BAD_REQUEST)
            if visit_id and consultation.visit_id != visit_id:
                return Response({'error': 'Consultation does not belong to specified visit.'}, status=status.HTTP_400_BAD_REQUEST)
            if not visit_id:
                visit_id = consultation.visit_id

        visit = None
        if visit_id:
            visit = Visit.objects.filter(id=visit_id).first()
            if not visit:
                return Response({'error': f'Visit #{visit_id} not found.'}, status=status.HTTP_400_BAD_REQUEST)

        today = datetime.date.today()

        with transaction.atomic():
            # Generate or reuse ONE Lab Token for this encounter session
            lab_token = None
            if visit:
                # Find active non-completed LabToken for this visit today
                lab_token = LabToken.objects.filter(visit=visit, date=today).exclude(status='COMPLETED').first()

                if not lab_token:
                    max_token = LabToken.objects.select_for_update().filter(
                        facility_id=facility_id, date=today
                    ).aggregate(models.Max('token_number'))['token_number__max'] or 0
                    token_number = max_token + 1
                    token_code = f"LAB-{token_number:03d}"
                    lab_token = LabToken.objects.create(
                        token_number=token_number,
                        token_code=token_code,
                        visit=visit,
                        facility_id=facility_id,
                        date=today,
                        status='ORDERED'
                    )

            created_orders = []
            for tid in test_ids:
                test_master = LabTestMaster.objects.filter(id=tid).first()
                if not test_master:
                    continue
                order = LabOrder.objects.create(
                    lab_token=lab_token,
                    visit=visit,
                    consultation=consultation,
                    patient_id=patient_id,
                    doctor=request.user,
                    facility_id=facility_id,
                    test_master=test_master,
                    status='ORDERED'
                )
                created_orders.append(order)

            # Transition Visit to WAITING_FOR_LAB
            if visit:
                from_stat = visit.status
                visit.current_queue = 'LAB'
                visit.status = 'WAITING_FOR_LAB'
                visit.save()

                if hasattr(visit, 'token'):
                    visit.token.status = 'IN_PROGRESS'
                    visit.token.save()

                VisitStatusHistory.objects.create(
                    visit=visit,
                    from_status=from_stat,
                    to_status='WAITING_FOR_LAB',
                    queue='LAB',
                    performed_by=request.user,
                    performed_by_role=getattr(request.user, 'role', ''),
                    notes=f"Doctor ordered {len(created_orders)} lab test(s). Lab Token: {lab_token.token_code if lab_token else 'N/A'}"
                )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='LAB_ORDERS_CREATED',
                facility_id=facility_id,
                details=f"Doctor {request.user.username} created {len(created_orders)} lab test(s) under Lab Token {lab_token.token_code if lab_token else 'N/A'} for Visit {visit.visit_id if visit else 'N/A'}"
            )

        if len(created_orders) == 1 and not data.get('test_ids'):
            return Response(LabOrderSerializer(created_orders[0]).data, status=status.HTTP_201_CREATED)
        return Response(LabOrderSerializer(created_orders, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='collect-sample')
    def collect_sample(self, request, pk=None):
        from apps.visits.models import VisitStatusHistory
        order = self.get_object()
        sample_code = request.data.get('sample_code') or f"SMP-{order.id:04d}"
        sample_type = request.data.get('sample_type', 'Blood / Serum')

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
        order.save()

        # Update lab token status to IN_PROGRESS if still ORDERED
        if order.lab_token and order.lab_token.status == 'ORDERED':
            order.lab_token.status = 'IN_PROGRESS'
            order.lab_token.save()

        # Update visit status to LAB_IN_PROGRESS if WAITING_FOR_LAB
        visit = order.visit or (order.consultation.visit if order.consultation else None)
        if visit and visit.status in ['WAITING_FOR_LAB', 'LAB_PENDING']:
            from_st = visit.status
            visit.status = 'LAB_IN_PROGRESS'
            visit.save()
            VisitStatusHistory.objects.create(
                visit=visit,
                from_status=from_st,
                to_status='LAB_IN_PROGRESS',
                queue='LAB',
                performed_by=request.user,
                performed_by_role=getattr(request.user, 'role', ''),
                notes=f"Sample collected for {order.test_master.name} (Barcode: {sample.sample_code})"
            )

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
        from apps.visits.models import VisitStatusHistory
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
        order.save()

        # Check if all orders for this Lab Token (or Visit) are now VERIFIED
        lab_token = order.lab_token
        visit = order.visit or (order.consultation.visit if order.consultation else None)

        if lab_token:
            all_orders = LabOrder.objects.filter(lab_token=lab_token)
            unverified_exists = all_orders.exclude(status='VERIFIED').exists()
            if not unverified_exists:
                lab_token.status = 'COMPLETED'
                lab_token.save()

                if visit and visit.status != 'COMPLETED':
                    from_stat = visit.status
                    visit.current_queue = 'DOCTOR'
                    visit.status = 'DOCTOR_REVIEW'
                    visit.save()

                    VisitStatusHistory.objects.create(
                        visit=visit,
                        from_status=from_stat,
                        to_status='DOCTOR_REVIEW',
                        queue='DOCTOR',
                        performed_by=request.user,
                        performed_by_role=getattr(request.user, 'role', ''),
                        notes=f"All lab tests verified for {lab_token.token_code}. Patient returned to Doctor Queue for review."
                    )
        elif visit:
            all_orders = LabOrder.objects.filter(visit=visit)
            unverified_exists = all_orders.exclude(status='VERIFIED').exists()
            if not unverified_exists and visit.status in ['WAITING_FOR_LAB', 'LAB_PENDING', 'LAB_IN_PROGRESS']:
                from_stat = visit.status
                visit.current_queue = 'DOCTOR'
                visit.status = 'DOCTOR_REVIEW'
                visit.save()

                VisitStatusHistory.objects.create(
                    visit=visit,
                    from_status=from_stat,
                    to_status='DOCTOR_REVIEW',
                    queue='DOCTOR',
                    performed_by=request.user,
                    performed_by_role=getattr(request.user, 'role', ''),
                    notes="All lab tests verified. Patient returned to Doctor Queue for review."
                )

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

from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models
from django.utils import timezone
import datetime

from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.patients.serializers import PatientSerializer
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'

class VisitStatusHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.ReadOnlyField(source='performed_by.full_name')

    class Meta:
        model = VisitStatusHistory
        fields = '__all__'

class VisitSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    token_details = TokenSerializer(source='token', read_only=True)
    token_number = serializers.ReadOnlyField(source='token.token_number')
    assigned_doctor_name = serializers.ReadOnlyField(source='assigned_doctor.full_name')
    waiting_time_minutes = serializers.SerializerMethodField()
    status_history_list = VisitStatusHistorySerializer(source='status_history', many=True, read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'

    def get_waiting_time_minutes(self, obj):
        if not obj.arrival_time:
            return 0
        end_ref = obj.completed_time or timezone.now()
        delta = end_ref - obj.arrival_time
        return max(0, int(delta.total_seconds() // 60))


class VisitViewSet(viewsets.ModelViewSet):
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permissions = {
        'GET': 'queue.view',
        'POST': 'queue.update',
        'PUT': 'queue.update',
        'PATCH': 'queue.update',
        'DELETE': 'queue.update'
    }

    def get_queryset(self):
        queryset = Visit.objects.all().select_related('patient', 'facility', 'assigned_doctor', 'token')
        
        # Scoping filter
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)

        req_fac = self.request.query_params.get('facility', None)
        if req_fac:
            queryset = queryset.filter(facility_id=req_fac)

        # Date filtering (default to today YYYY-MM-DD if not explicitly set to 'all')
        req_date = self.request.query_params.get('date', None)
        if req_date and req_date != 'all':
            try:
                target_date = datetime.datetime.strptime(req_date, '%Y-%m-%d').date()
                queryset = queryset.filter(opd_date=target_date)
            except ValueError:
                queryset = queryset.filter(opd_date=datetime.date.today())
        elif not req_date:
            queryset = queryset.filter(opd_date=datetime.date.today())

        # Queue filter (triage, doctor, lab, pharmacy, completed)
        req_queue = self.request.query_params.get('queue', None)
        req_status = self.request.query_params.get('status', None)

        if req_queue and req_queue != 'ALL':
            req_queue_upper = req_queue.upper()
            queryset = queryset.filter(current_queue=req_queue_upper)
            if req_queue_upper != 'COMPLETED' and not req_status:
                queryset = queryset.exclude(status='COMPLETED')

        # Status filter
        if req_status:
            req_status_upper = req_status.upper()
            if req_status_upper == 'WAITING':
                queryset = queryset.filter(status__in=['WAITING', 'WAITING_FOR_TRIAGE', 'IN_TRIAGE'])
            elif req_status_upper == 'TRIAGED':
                queryset = queryset.filter(status__in=['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION'])
            else:
                queryset = queryset.filter(status=req_status_upper)


        # Priority ordering: EMERGENCY (1) > HIGH (2) > NORMAL (3), then arrival_time ascending
        priority_case = models.Case(
            models.When(priority='EMERGENCY', then=models.Value(1)),
            models.When(priority='HIGH', then=models.Value(2)),
            models.When(priority='NORMAL', then=models.Value(3)),
            default=models.Value(4),
            output_field=models.IntegerField()
        )
        return queryset.annotate(priority_weight=priority_case).order_by('priority_weight', 'arrival_time')

    def create(self, request, *args, **kwargs):
        patient_id = request.data.get('patient')
        facility_id = request.data.get('facility')
        visit_type = request.data.get('visit_type', 'GENERAL_OPD')
        priority = request.data.get('priority', 'NORMAL')
        chief_complaint = request.data.get('chief_complaint', '')

        if not patient_id:
            return Response({'error': 'Please select a valid registered patient.'}, status=status.HTTP_400_BAD_REQUEST)
        if not facility_id:
            return Response({'error': 'No active facility selected.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient_id = int(patient_id)
            facility_id = int(facility_id)
        except (ValueError, TypeError):
            pass

        # Operational OPD Date is strictly today
        today = datetime.date.today()

        with transaction.atomic():
            # Server-side sequential token generation per facility and date
            max_token = Token.objects.select_for_update().filter(
                facility_id=facility_id, date=today
            ).aggregate(models.Max('token_number'))['token_number__max'] or 0
            
            token_number = max_token + 1
            base_id = f"VIS-F{facility_id}-{today.strftime('%Y%m%d')}-{token_number:03d}"
            visit_id = base_id
            seq = 1
            while Visit.objects.filter(visit_id=visit_id).exists():
                visit_id = f"{base_id}-{seq}"
                seq += 1

            visit = Visit.objects.create(
                visit_id=visit_id,
                patient_id=patient_id,
                facility_id=facility_id,
                opd_date=today,
                visit_type=visit_type,
                priority=priority,
                chief_complaint=chief_complaint,
                current_queue='TRIAGE',
                status='WAITING_FOR_TRIAGE',
                arrival_time=timezone.now()
            )

            token = Token.objects.create(
                token_number=token_number,
                visit=visit,
                facility_id=facility_id,
                date=today,
                priority=priority,
                status='WAITING'
            )

            VisitStatusHistory.objects.create(
                visit=visit,
                from_status='NONE',
                to_status='WAITING_FOR_TRIAGE',
                queue='TRIAGE',
                performed_by=request.user,
                performed_by_role=getattr(request.user, 'role', ''),
                notes=f"Issued OPD Token #{token_number} for {today}"
            )

        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='call-next')
    def call_next_patient(self, request):
        """
        Atomically selects and calls the highest priority waiting patient for the user's role & facility today.
        """
        facility_id = request.data.get('facility') or getattr(request.user.assigned_facility, 'id', None)
        target_queue = request.data.get('queue', 'DOCTOR')
        today = datetime.date.today()

        if not facility_id:
            return Response({'error': 'Facility context required to call next patient.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            waiting_status_map = {
                'TRIAGE': 'WAITING_FOR_TRIAGE',
                'DOCTOR': 'WAITING_FOR_DOCTOR',
                'LAB': 'LAB_PENDING',
                'PHARMACY': 'WAITING_FOR_PHARMACY'
            }
            active_status_map = {
                'TRIAGE': ('IN_TRIAGE', 'TRIAGE'),
                'DOCTOR': ('IN_CONSULTATION', 'DOCTOR'),
                'LAB': ('LAB_IN_PROGRESS', 'LAB'),
                'PHARMACY': ('IN_PHARMACY', 'PHARMACY')
            }

            req_status = waiting_status_map.get(target_queue, 'WAITING_FOR_DOCTOR')
            next_status, queue_code = active_status_map.get(target_queue, ('IN_CONSULTATION', 'DOCTOR'))

            priority_case = models.Case(
                models.When(priority='EMERGENCY', then=models.Value(1)),
                models.When(status='LAB_COMPLETED', then=models.Value(2)),
                models.When(priority='HIGH', then=models.Value(3)),
                models.When(priority='NORMAL', then=models.Value(4)),
                default=models.Value(5),
                output_field=models.IntegerField()
            )

            # Lock eligible waiting patient
            next_visit = Visit.objects.select_for_update().filter(
                facility_id=facility_id,
                opd_date=today,
                current_queue=target_queue,
                status__in=[req_status, 'WAITING', 'TRIAGED', 'LAB_COMPLETED']
            ).annotate(priority_weight=priority_case).order_by('priority_weight', 'arrival_time').first()

            if not next_visit:
                return Response({'message': f'No waiting patients in {target_queue} queue for today.'}, status=status.HTTP_200_OK)

            from_stat = next_visit.status
            next_visit.status = next_status
            if target_queue == 'DOCTOR':
                next_visit.assigned_doctor = request.user
                next_visit.consultation_start_time = timezone.now()
            elif target_queue == 'TRIAGE':
                next_visit.triage_start_time = timezone.now()

            next_visit.save()

            VisitStatusHistory.objects.create(
                visit=next_visit,
                from_status=from_stat,
                to_status=next_status,
                queue=queue_code,
                performed_by=request.user,
                performed_by_role=getattr(request.user, 'role', ''),
                notes=f"Called next patient by {request.user.full_name or request.user.username}"
            )

        return Response(VisitSerializer(next_visit).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='transition-status')
    def transition_status(self, request, pk=None):
        """
        Transition workflow status with history audit logging. Blocked for past dates.
        """
        visit = self.get_object()
        today = datetime.date.today()

        if visit.opd_date < today:
            return Response({'error': 'Historical OPD queues are read-only. Status modifications on past dates are blocked.'}, status=status.HTTP_400_BAD_REQUEST)

        to_status = request.data.get('to_status')
        target_queue = request.data.get('queue', visit.current_queue)
        notes = request.data.get('notes', '')

        if not to_status:
            return Response({'error': 'Parameter to_status is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from_status = visit.status
        visit.status = to_status
        visit.current_queue = target_queue

        now = timezone.now()
        if to_status == 'TRIAGED':
            visit.triage_end_time = now
            visit.current_queue = 'DOCTOR'
            visit.status = 'WAITING_FOR_DOCTOR'
        elif to_status == 'COMPLETED':
            visit.completed_time = now
            visit.current_queue = 'COMPLETED'
        elif to_status == 'WAITING_FOR_PHARMACY':
            visit.consultation_end_time = now
            visit.current_queue = 'PHARMACY'

        visit.save()

        VisitStatusHistory.objects.create(
            visit=visit,
            from_status=from_status,
            to_status=visit.status,
            queue=visit.current_queue,
            performed_by=request.user,
            performed_by_role=getattr(request.user, 'role', ''),
            notes=notes
        )

        return Response(VisitSerializer(visit).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='history-summary')
    def history_summary(self, request):
        """
        Returns date-wise OPD summary table for facility isolation and reporting.
        """
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        queryset = Visit.objects.all()
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)

        facility_id = request.query_params.get('facility')
        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)

        summary_data = queryset.values('opd_date').annotate(
            total_patients=models.Count('id'),
            completed_patients=models.Count('id', filter=models.Q(status='COMPLETED')),
            cancelled_patients=models.Count('id', filter=models.Q(status='CANCELLED'))
        ).order_by('-opd_date')[:30]

        return Response(list(summary_data), status=status.HTTP_200_OK)

"""
Visits & Token Allocation REST API (v1).
Consolidated authoritative OPD queue and token handling backed by domain services.
"""
import uuid
import datetime
from django.utils import timezone
from rest_framework import serializers, viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.visits.services import (
    issue_opd_token, issue_lab_token,
    call_next_queue_item, transition_visit_status,
    void_opd_token, get_queue_history_summary
)
from apps.patients.serializers import PatientSerializer
from apps.laboratory.models import DiagnosticOrder
from apps.accounts.permissions import has_role_permission
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'


class VisitSerializer(serializers.ModelSerializer):
    patient_details = serializers.SerializerMethodField()
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    token_details = serializers.SerializerMethodField()
    token_number = serializers.CharField(source='token.token_number', read_only=True)
    assigned_doctor_name = serializers.ReadOnlyField(source='assigned_doctor.full_name')
    waiting_time_minutes = serializers.SerializerMethodField()
    status_history_list = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = [
            'id', 'visit_id', 'patient', 'patient_details', 'facility', 'facility_name',
            'visit_type', 'opd_date', 'current_queue', 'status', 'priority',
            'chief_complaint', 'assigned_doctor', 'assigned_doctor_name',
            'token_number', 'token_details', 'arrival_time', 'triage_start_time',
            'triage_end_time', 'consultation_start_time', 'consultation_end_time',
            'completed_time', 'waiting_time_minutes', 'status_history_list'
        ]
        read_only_fields = ['visit_id', 'arrival_time']

    def get_patient_details(self, obj):
        p = obj.patient
        if not p:
            return None
        return {
            'id': p.id,
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender,
            'mobile': p.mobile,
        }

    def get_token_details(self, obj):
        try:
            tok = obj.token
            return {
                'id': tok.id,
                'token_number': tok.token_number,
                'priority': tok.priority,
                'status': tok.status
            }
        except Exception:
            return None

    def get_waiting_time_minutes(self, obj):
        if obj.status in ['COMPLETED', 'CANCELLED', 'NO_SHOW']:
            return 0
        now = timezone.now()
        start = obj.arrival_time or obj.visit_date or now
        return max(0, int((now - start).total_seconds() // 60))

    def get_status_history_list(self, obj):
        # Do not query history on high-volume list endpoints to maintain strict query bounds
        view = self.context.get('view')
        request = self.context.get('request')
        is_list = getattr(view, 'action', None) == 'list'
        include_history = request and request.query_params.get('include_history') == 'true'
        if is_list and not include_history:
            return []
        return [
            {
                'id': h.id,
                'from_status': h.from_status,
                'to_status': h.to_status,
                'queue': h.queue,
                'performed_by_name': h.performed_by.full_name if h.performed_by else 'System',
                'performed_by_role': h.performed_by_role,
                'notes': h.notes,
                'timestamp': h.timestamp.isoformat() if h.timestamp else None
            }
            for h in obj.status_history.all()
        ]


class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all().select_related('patient', 'facility', 'assigned_doctor', 'token')
    serializer_class = VisitSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            queryset = queryset.filter(facility_id__in=permitted)

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

        from django.db import models
        priority_case = models.Case(
            models.When(priority='EMERGENCY', then=models.Value(1)),
            models.When(priority='HIGH', then=models.Value(2)),
            models.When(priority='NORMAL', then=models.Value(3)),
            default=models.Value(4),
            output_field=models.IntegerField()
        )
        return queryset.annotate(priority_weight=priority_case).order_by('priority_weight', 'arrival_time')

    def create(self, request, *args, **kwargs):
        # Authoritative permission check
        if not request.user.is_superuser and not has_role_permission(request.user, 'queue.create'):
            raise exceptions.PermissionDenied("You do not have permission to register visits or issue OPD tokens.")

        patient_id = request.data.get('patient')
        facility_id = request.data.get('facility')
        visit_type = request.data.get('visit_type', 'GENERAL_OPD')
        priority = request.data.get('priority', 'NORMAL')
        chief_complaint = request.data.get('chief_complaint', '')

        if not patient_id:
            raise exceptions.ValidationError({'patient': 'Please select a valid registered patient.'})

        staff = get_request_staff(request, required=False)
        # Authoritative facility derivation from staff context if client did not supply or to ensure consistency
        if not facility_id:
            if staff and staff.facility_id:
                facility_id = staff.facility_id
            elif getattr(request.user, 'assigned_facility_id', None):
                facility_id = request.user.assigned_facility_id

        if not facility_id:
            raise exceptions.ValidationError({'facility': 'Facility context is required.'})

        from apps.facilities.models import Facility
        try:
            fac = Facility.objects.get(pk=facility_id)
        except Facility.DoesNotExist:
            raise exceptions.ValidationError({'facility': 'Invalid facility ID.'})

        check_facility_permission(fac, staff, request.user)

        from apps.patients.models import Patient
        try:
            pat = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            raise exceptions.ValidationError({'patient': 'Patient not found.'})

        # Ensure patient registered facility matches visit facility unless cross-facility authorized
        if pat.registered_at_facility_id and pat.registered_at_facility_id != fac.id:
            if not request.user.is_superuser and getattr(request.user, 'role', '') not in ['DISTRICT_OFFICER']:
                raise exceptions.PermissionDenied("Patient is registered at a different facility.")

        today = datetime.date.today()
        vis_id = f"VIS-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        from django.db import transaction
        with transaction.atomic():
            visit = Visit.objects.create(
                visit_id=vis_id,
                patient=pat,
                facility=fac,
                opd_date=today,
                visit_type=visit_type,
                priority=priority,
                chief_complaint=chief_complaint,
                current_queue='TRIAGE',
                status='WAITING_FOR_TRIAGE',
                arrival_time=timezone.now()
            )
            # Authoritative token issuance backed by FacilityDailyCounter
            token = issue_opd_token(visit=visit, facility=fac, priority=priority)

            VisitStatusHistory.objects.create(
                visit=visit,
                from_status='NONE',
                to_status='WAITING_FOR_TRIAGE',
                queue='TRIAGE',
                performed_by=request.user,
                performed_by_role=getattr(request.user, 'role', ''),
                notes=f"Issued OPD Token #{token.token_number} for {today}"
            )

        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='call-next')
    def call_next(self, request):
        """
        Atomically claims and calls the next waiting patient for the authorized clinician.
        Enforces queue.call_next and facility scope.
        """
        facility_id = request.data.get('facility')
        if not facility_id and request.user.assigned_facility_id:
            facility_id = request.user.assigned_facility_id

        if not facility_id:
            raise exceptions.ValidationError({'facility': 'Facility context required to call next patient.'})

        from apps.facilities.models import Facility
        try:
            fac = Facility.objects.get(pk=facility_id)
        except Facility.DoesNotExist:
            raise exceptions.ValidationError({'facility': 'Invalid facility ID.'})

        staff = get_request_staff(request, required=False)
        check_facility_permission(fac, staff, request.user)

        target_queue = request.data.get('queue', 'TRIAGE')
        try:
            claimed_visit = call_next_queue_item(
                facility=fac,
                requesting_user=request.user,
                target_queue=target_queue
            )
            return Response(VisitSerializer(claimed_visit).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'message': str(e), 'claimed': None}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='transition-status')
    def transition_status(self, request, pk=None):
        """
        Transitions queue/visit status with validation and audit logging.
        """
        visit = self.get_object()
        to_status = request.data.get('to_status')
        target_queue = request.data.get('queue', None)
        notes = request.data.get('notes', '')

        updated_visit = transition_visit_status(
            visit=visit,
            to_status=to_status,
            requesting_user=request.user,
            target_queue=target_queue,
            notes=notes
        )
        return Response(VisitSerializer(updated_visit).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='history-summary')
    def history_summary(self, request):
        """
        Returns date-wise OPD summary counts for the requested facility scope.
        """
        staff = get_request_staff(request, required=False)
        permitted = get_user_permitted_facilities(staff, request.user)
        facility_id = request.query_params.get('facility', None)

        summary = get_queue_history_summary(
            facility_id=facility_id,
            accessible_facility_ids=permitted
        )
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='void-token')
    def void_token_collection(self, request):
        """
        Collection endpoint: POST /api/v1/visits/void-token/ with {"visit_id": 123, "reason": "..."}
        """
        visit_id = request.data.get('visit_id')
        if not visit_id:
            return Response({'error': 'visit_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            visit = Visit.objects.get(pk=visit_id)
        except Visit.DoesNotExist:
            return Response({'error': 'Visit not found.'}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', 'Duplicate token voided by front desk.')
        voided_visit = void_opd_token(
            visit=visit,
            requesting_user=request.user,
            reason=reason
        )
        tok_num = voided_visit.token.token_number if hasattr(voided_visit, 'token') else None
        return Response({
            'message': 'Token voided successfully.',
            'token_number': tok_num,
            'status': 'CANCELLED'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='void-token')
    def void_token(self, request, pk=None):
        """
        Detail endpoint: POST /api/v1/visits/<id>/void-token/
        """
        visit = self.get_object()
        reason = request.data.get('reason', 'Duplicate token voided by front desk.')

        voided_visit = void_opd_token(
            visit=visit,
            requesting_user=request.user,
            reason=reason
        )
        tok_num = voided_visit.token.token_number if hasattr(voided_visit, 'token') else None
        return Response({
            'message': 'Token voided successfully.',
            'token_number': tok_num,
            'status': 'CANCELLED'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='issue-opd-token')
    def issue_opd(self, request, pk=None):
        visit = self.get_object()
        token = issue_opd_token(visit=visit, facility=visit.facility)
        return Response({"token_number": token.token_number, "status": "ISSUED"})

    @action(detail=True, methods=['post'], url_path='issue-lab-token')
    def issue_lab(self, request, pk=None):
        visit = self.get_object()
        diag_order_id = request.data.get("diagnostic_order_id")
        diag_order = DiagnosticOrder.objects.filter(pk=diag_order_id, visit=visit).first()
        if not diag_order:
            return Response({"error": "Valid DiagnosticOrder linked to this Visit is required."}, status=status.HTTP_400_BAD_REQUEST)

        lab_token_no = issue_lab_token(diagnostic_order=diag_order, facility=visit.facility)
        return Response({"lab_token_number": lab_token_no, "status": "ISSUED"})

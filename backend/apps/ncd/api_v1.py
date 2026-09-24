"""
NCD, Disease Surveillance, Operational Alerts & Audit REST API (v1).
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.ncd.models import NCDCondition, NCDAssessment
from apps.ncd.services import register_ncd_condition, record_ncd_assessment
from apps.surveillance.models import DiseaseSurveillanceCase, PublicHealthNotification
from apps.surveillance.services import report_surveillance_case, dispatch_public_health_notification
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry
from apps.common.permissions import IsActiveStaff, IsAdministrativeStaff, FacilityScopedPermission, get_request_staff, get_user_permitted_facilities

# --- NCD ---
class NCDConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCDCondition
        fields = '__all__'

class NCDAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCDAssessment
        fields = '__all__'
        read_only_fields = ['assessor_staff', 'created_at']

class NCDConditionViewSet(viewsets.ModelViewSet):
    queryset = NCDCondition.objects.all().select_related('patient', 'facility')
    serializer_class = NCDConditionSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        condition = register_ncd_condition(
            patient=serializer.validated_data['patient'],
            facility=serializer.validated_data['facility'],
            condition_name=serializer.validated_data['condition_name'],
            icd10_code=serializer.validated_data.get('icd10_code', ''),
            diagnosed_date=serializer.validated_data.get('diagnosed_date'),
            severity_stage=serializer.validated_data.get('severity_stage', 'STAGE_1')
        )
        return Response(self.get_serializer(condition).data, status=status.HTTP_201_CREATED)

class NCDAssessmentViewSet(viewsets.ModelViewSet):
    queryset = NCDAssessment.objects.all().select_related('ncd_condition', 'assessor_staff')
    serializer_class = NCDAssessmentSerializer
    permission_classes = [IsActiveStaff]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        assessment = record_ncd_assessment(
            ncd_condition=serializer.validated_data['ncd_condition'],
            assessor_staff=staff,
            assessment_date=serializer.validated_data.get('assessment_date'),
            systolic_bp=serializer.validated_data.get('systolic_bp'),
            diastolic_bp=serializer.validated_data.get('diastolic_bp'),
            fasting_blood_sugar=serializer.validated_data.get('fasting_blood_sugar'),
            hba1c=serializer.validated_data.get('hba1c'),
            complications_noted=serializer.validated_data.get('complications_noted', '')
        )
        return Response(self.get_serializer(assessment).data, status=status.HTTP_201_CREATED)


# --- Surveillance ---
class DiseaseSurveillanceCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseSurveillanceCase
        fields = '__all__'
        read_only_fields = ['case_identifier', 'reporting_staff', 'created_at']

class PublicHealthNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHealthNotification
        fields = '__all__'
        read_only_fields = ['dispatched_at']

class DiseaseSurveillanceCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseSurveillanceCase.objects.all().select_related('patient', 'facility', 'reporting_staff')
    serializer_class = DiseaseSurveillanceCaseSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        case = report_surveillance_case(
            disease_name=serializer.validated_data['disease_name'],
            suspected_or_confirmed=serializer.validated_data['suspected_or_confirmed'],
            patient=serializer.validated_data['patient'],
            facility=serializer.validated_data['facility'],
            reporting_staff=staff,
            onset_date=serializer.validated_data.get('onset_date'),
            symptoms_description=serializer.validated_data.get('symptoms_description', ''),
            epidemiological_notes=serializer.validated_data.get('epidemiological_notes', '')
        )
        return Response(self.get_serializer(case).data, status=status.HTTP_201_CREATED)

class PublicHealthNotificationViewSet(viewsets.ModelViewSet):
    queryset = PublicHealthNotification.objects.all().select_related('surveillance_case')
    serializer_class = PublicHealthNotificationSerializer
    permission_classes = [IsActiveStaff]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notif = dispatch_public_health_notification(
            surveillance_case=serializer.validated_data['surveillance_case'],
            recipient_agency=serializer.validated_data['recipient_agency'],
            notification_channel=serializer.validated_data.get('notification_channel', 'SYSTEM_DISPATCH'),
            message_payload=serializer.validated_data.get('message_payload', {})
        )
        return Response(self.get_serializer(notif).data, status=status.HTTP_201_CREATED)


# --- Alerts ---
class OperationalAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationalAlert
        fields = '__all__'
        read_only_fields = ['created_at', 'acknowledged_at', 'acknowledged_by_staff']

class OperationalAlertViewSet(viewsets.ModelViewSet):
    queryset = OperationalAlert.objects.all().select_related('facility', 'acknowledged_by_staff')
    serializer_class = OperationalAlertSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        from django.utils import timezone
        alert = self.get_object()
        staff = get_request_staff(request)
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by_staff = staff
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])
        return Response(self.get_serializer(alert).data)


# --- Audit (Read-only, Admin restricted) ---
class AuditLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = '__all__'
        read_only_fields = fields

class AuditLogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit records are write-only to domain services and read-only to authorized administrators.
    Arbitrary creation/update/deletion via REST API is strictly forbidden.
    """
    queryset = AuditLogEntry.objects.all().select_related('actor_staff', 'facility').order_by('-event_timestamp')
    serializer_class = AuditLogEntrySerializer
    permission_classes = [IsAdministrativeStaff]

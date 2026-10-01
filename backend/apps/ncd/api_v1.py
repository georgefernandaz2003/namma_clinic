"""
NCD, Disease Surveillance, Operational Alerts & Audit REST API (v1).
Enforces facility scoping, correct OperationalAlert acknowledge lifecycle, and admin-only audit.
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
from apps.common.permissions import (
    IsActiveStaff, IsAdministrativeStaff, FacilityScopedPermission,
    get_request_staff, get_user_permitted_facilities, check_facility_permission
)

# --- NCD ---
class NCDConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCDCondition
        fields = '__all__'
        read_only_fields = ['registering_doctor', 'created_at', 'updated_at']

class NCDAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCDAssessment
        fields = '__all__'
        read_only_fields = ['assessed_by_staff']

class NCDConditionViewSet(viewsets.ModelViewSet):
    queryset = NCDCondition.objects.all().select_related('patient', 'registering_facility')
    serializer_class = NCDConditionSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(registering_facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        fac = serializer.validated_data.get('registering_facility')
        check_facility_permission(fac, staff, request.user)

        condition = register_ncd_condition(
            patient=serializer.validated_data['patient'],
            facility=fac,
            registering_doctor=staff,
            condition_code=serializer.validated_data.get('condition_code', 'HTN'),
            staging=serializer.validated_data.get('staging', ''),
            control_status=serializer.validated_data.get('control_status', 'SCREENED')
        )
        return Response(self.get_serializer(condition).data, status=status.HTTP_201_CREATED)

class NCDAssessmentViewSet(viewsets.ModelViewSet):
    queryset = NCDAssessment.objects.all().select_related('condition', 'assessed_by_staff')
    serializer_class = NCDAssessmentSerializer
    permission_classes = [IsActiveStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(condition__registering_facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        cond = serializer.validated_data['condition']
        check_facility_permission(cond.registering_facility, staff, request.user)

        assessment = record_ncd_assessment(
            condition=cond,
            visit=serializer.validated_data.get('visit'),
            assessed_by_staff=staff,
            systolic_bp=serializer.validated_data.get('systolic_bp'),
            diastolic_bp=serializer.validated_data.get('diastolic_bp'),
            blood_glucose_fasting=serializer.validated_data.get('blood_glucose_fasting'),
            clinical_notes=serializer.validated_data.get('clinical_notes', '')
        )
        return Response(self.get_serializer(assessment).data, status=status.HTTP_201_CREATED)


# --- Surveillance ---
class DiseaseSurveillanceCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseSurveillanceCase
        fields = '__all__'
        read_only_fields = ['case_number', 'reporting_staff', 'reported_at', 'updated_at']

class PublicHealthNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHealthNotification
        fields = '__all__'
        read_only_fields = ['dispatched_at']

class DiseaseSurveillanceCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseSurveillanceCase.objects.all().select_related('patient', 'facility', 'reporting_staff')
    serializer_class = DiseaseSurveillanceCaseSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, request.user)

        case = report_surveillance_case(
            patient=serializer.validated_data['patient'],
            facility=fac,
            disease=serializer.validated_data['disease'],
            reporting_staff=staff,
            case_number=serializer.validated_data.get('case_number'),
            severity=serializer.validated_data.get('severity', 'MODERATE'),
            status=serializer.validated_data.get('status', 'CONFIRMED'),
            ward=serializer.validated_data.get('ward'),
            investigation_notes=serializer.validated_data.get('investigation_notes', '')
        )
        return Response(self.get_serializer(case).data, status=status.HTTP_201_CREATED)

class PublicHealthNotificationViewSet(viewsets.ModelViewSet):
    queryset = PublicHealthNotification.objects.all().select_related('case')
    serializer_class = PublicHealthNotificationSerializer
    permission_classes = [IsActiveStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(case__facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        case = serializer.validated_data['case']
        check_facility_permission(case.facility, staff, request.user)

        notif = dispatch_public_health_notification(
            case=case,
            notified_authority=serializer.validated_data['notified_authority'],
            dispatch_payload=serializer.validated_data.get('dispatch_payload', {})
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
        alert.is_active = False
        alert.acknowledged_by_staff = staff
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=['is_active', 'acknowledged_by_staff', 'acknowledged_at'])
        return Response(self.get_serializer(alert).data)


# --- Audit (Read-only, Admin restricted) ---
class AuditLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = '__all__'

class AuditLogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit records are write-only to domain services and read-only to authorized administrators.
    Arbitrary creation/update/deletion via REST API is strictly forbidden.
    """
    queryset = AuditLogEntry.objects.all().select_related('actor_staff', 'facility').order_by('-event_timestamp')
    serializer_class = AuditLogEntrySerializer
    permission_classes = [IsAdministrativeStaff]

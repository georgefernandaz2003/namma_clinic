"""
Public Health Intelligence Alert Views - STEP 4
Dedicated endpoints for public health surveillance alerts and human-reviewed actions.

Supported endpoints:
- GET /api/surveillance/intelligence/alerts/
- POST /api/surveillance/intelligence/alerts/evaluate/
- GET /api/surveillance/intelligence/alerts/<id>/
- PATCH /api/surveillance/intelligence/alerts/<id>/
- POST /api/surveillance/intelligence/alerts/<id>/acknowledge/
- POST /api/surveillance/intelligence/alerts/<id>/resolve/

Strict constraints:
- RBAC and facility/district isolation enforced (HTTP 403 on violations).
- Controlled manual evaluation action.
- Deduplication and audit logging integrated.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.alerts.models import Alert
from apps.alerts.views import AlertSerializer
from apps.accounts.permissions import (
    HasPermission,
    can_access_facility,
    get_accessible_facility_ids_for_user
)
from apps.surveillance.intelligence_services import resolve_facility_scope
from apps.surveillance.intelligence_alert_services import (
    evaluate_intelligence_alerts,
    acknowledge_alert,
    resolve_alert
)


class BaseIntelligenceAlertView(APIView):
    """Base API view verifying authentication and dashboard access permission."""
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'dashboard.view'


class PublicHealthIntelligenceAlertsView(BaseIntelligenceAlertView):
    """
    GET /api/surveillance/intelligence/alerts/
    Lists active and past public health intelligence signals scoped to the requester.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        status_param = request.query_params.get('status')
        severity_param = request.query_params.get('severity')
        alert_type_param = request.query_params.get('alert_type')
        disease_param = request.query_params.get('disease')

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error or 'Unauthorized scope access.'}, status=status.HTTP_403_FORBIDDEN)

        qs = Alert.objects.filter(
            alert_type__startswith='INTELLIGENCE_',
            facility_id__in=scope.facility_ids
        ).select_related('facility', 'district', 'acknowledged_by', 'resolved_by').order_by('-created_at', '-id')

        if status_param:
            norm_status = 'NEW' if status_param.upper() == 'OPEN' else status_param.upper()
            qs = qs.filter(status=norm_status)

        if severity_param:
            qs = qs.filter(severity=severity_param.upper())

        if alert_type_param:
            qs = qs.filter(alert_type=alert_type_param.upper())

        if disease_param:
            qs = qs.filter(metadata__disease__iexact=disease_param.strip())

        serializer = AlertSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'facility_ids': scope.facility_ids,
            'district_id': scope.district_id,
            'results': serializer.data
        })


class PublicHealthIntelligenceEvaluateView(BaseIntelligenceAlertView):
    """
    POST /api/surveillance/intelligence/alerts/evaluate/
    Manually triggers evaluation of surveillance intelligence signals.
    Only authorized operational and admin roles may invoke this action.
    """
    def post(self, request):
        # Operational authorization check: District Officers, Hospital Admins, Doctors, Admins
        user = request.user
        allowed_roles = {'DISTRICT_OFFICER', 'HOSPITAL_ADMIN', 'DOCTOR'}
        if not getattr(user, 'is_superuser', False) and user.role not in allowed_roles:
            return Response(
                {'error': 'Your role is not authorized to trigger surveillance signal evaluation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        fac_id = request.data.get('facility') or request.query_params.get('facility')
        dist_id = request.data.get('district') or request.query_params.get('district')
        as_of_date = request.data.get('date') or request.query_params.get('date')

        scope = resolve_facility_scope(
            user=user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error or 'Unauthorized scope access.'}, status=status.HTTP_403_FORBIDDEN)

        eval_result = evaluate_intelligence_alerts(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            as_of_date=as_of_date,
            actor_user=user
        )

        serialized_alerts = AlertSerializer(eval_result['alerts'], many=True).data
        return Response({
            'status': 'success',
            'as_of_date': eval_result['as_of_date'],
            'facilities_evaluated': eval_result['facilities_evaluated'],
            'total_alerts': eval_result['total_alerts'],
            'created_count': eval_result['created_count'],
            'updated_count': eval_result['updated_count'],
            'alerts': serialized_alerts
        }, status=status.HTTP_200_OK)


def get_intelligence_alert_or_404(pk, user):
    """
    Retrieves an alert by pk strictly requiring alert_type__startswith='INTELLIGENCE_'.
    Returns 404 if the alert does not exist or is not an intelligence alert (preventing
    information leakage about non-intelligence alerts).
    Enforces cross-facility/district access control, returning 403 Forbidden on violation.
    """
    alert = get_object_or_404(
        Alert.objects.select_related('facility', 'district', 'acknowledged_by', 'resolved_by').filter(
            alert_type__startswith='INTELLIGENCE_'
        ),
        pk=pk
    )
    if not getattr(user, 'is_superuser', False) and not can_access_facility(user, alert.facility_id):
        raise PermissionDenied("You do not have authorization to access this facility alert.")
    return alert


class PublicHealthIntelligenceAlertDetailView(BaseIntelligenceAlertView):
    """
    GET, PATCH /api/surveillance/intelligence/alerts/<id>/
    Retrieves or updates an individual surveillance alert's status.
    """
    def get(self, request, pk):
        alert = get_intelligence_alert_or_404(pk, request.user)
        return Response(AlertSerializer(alert).data)

    def patch(self, request, pk):
        alert = get_intelligence_alert_or_404(pk, request.user)
        new_status = request.data.get('status')
        notes = request.data.get('resolution_notes', '')

        if not new_status:
            return Response({'error': 'Status field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        norm_status = 'NEW' if new_status.upper() == 'OPEN' else new_status.upper()

        if norm_status == 'ACKNOWLEDGED':
            try:
                acknowledge_alert(alert, request.user)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif norm_status == 'RESOLVED':
            resolve_alert(alert, request.user, resolution_notes=notes)
        else:
            return Response(
                {'error': f"Invalid status '{new_status}'. Supported: ACKNOWLEDGED, RESOLVED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(AlertSerializer(alert).data)


class PublicHealthIntelligenceAlertAcknowledgeView(BaseIntelligenceAlertView):
    """
    POST /api/surveillance/intelligence/alerts/<id>/acknowledge/
    """
    def post(self, request, pk):
        alert = get_intelligence_alert_or_404(pk, request.user)
        try:
            acknowledge_alert(alert, request.user)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AlertSerializer(alert).data)


class PublicHealthIntelligenceAlertResolveView(BaseIntelligenceAlertView):
    """
    POST /api/surveillance/intelligence/alerts/<id>/resolve/
    """
    def post(self, request, pk):
        alert = get_intelligence_alert_or_404(pk, request.user)
        notes = request.data.get('resolution_notes', '')
        resolve_alert(alert, request.user, resolution_notes=notes)
        return Response(AlertSerializer(alert).data)

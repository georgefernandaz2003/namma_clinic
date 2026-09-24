"""
Visits & Token Allocation REST API (v1).
Integrates encounter creation with monotonic OPD/LAB token services.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.visits.models import Visit
from apps.visits.services import issue_opd_token, issue_lab_token
from apps.laboratory.models import DiagnosticOrder
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)

class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = [
            'id', 'visit_id', 'patient', 'facility', 'visit_type',
            'opd_date', 'current_queue', 'status', 'token_number', 'created_at'
        ]
        read_only_fields = ['visit_id', 'token_number', 'created_at']

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all().select_related('patient', 'facility')
    serializer_class = VisitSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        import uuid, datetime
        staff = get_request_staff(self.request)
        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, self.request.user)

        vis_id = f"VIS-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        visit = serializer.save(visit_id=vis_id)
        # Issue OPD token automatically on visit encounter creation
        issue_opd_token(visit=visit, facility=visit.facility)

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

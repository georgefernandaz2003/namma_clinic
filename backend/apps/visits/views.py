from rest_framework import serializers, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.visits.models import Visit, Token
from apps.patients.serializers import PatientSerializer
import datetime

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'

class VisitSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    token_details = TokenSerializer(source='token', read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'

from apps.accounts.permissions import get_accessible_facility_ids_for_user

class VisitViewSet(viewsets.ModelViewSet):
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'status', 'visit_type']

    def get_queryset(self):
        queryset = Visit.objects.all().select_related('patient', 'facility', 'assigned_doctor')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

    def create(self, request, *args, **kwargs):
        # Auto-generate visit_id and daily token
        patient_id = request.data.get('patient')
        facility_id = request.data.get('facility')
        visit_type = request.data.get('visit_type', 'GENERAL_OPD')
        priority = request.data.get('priority', 'NORMAL')
        chief_complaint = request.data.get('chief_complaint', '')

        count = Visit.objects.filter(facility_id=facility_id, visit_date__date=datetime.date.today()).count() + 1
        visit_id = f"VIS-{datetime.date.today().strftime('%Y%m%d')}-{count:03d}"

        visit = Visit.objects.create(
            visit_id=visit_id,
            patient_id=patient_id,
            facility_id=facility_id,
            visit_type=visit_type,
            chief_complaint=chief_complaint,
            status='WAITING'
        )

        token = Token.objects.create(
            token_number=count,
            visit=visit,
            facility_id=facility_id,
            priority=priority,
            status='WAITING'
        )

        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)

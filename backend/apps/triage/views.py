from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from apps.triage.models import TriageVitals
from apps.visits.models import Visit
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope


class TriageVitalsSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')

    class Meta:
        model = TriageVitals
        fields = '__all__'

class TriageVitalsViewSet(viewsets.ModelViewSet):
    queryset = TriageVitals.objects.all().select_related('visit', 'patient', 'nurse')
    serializer_class = TriageVitalsSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'triage.view',
        'POST': 'triage.create',
        'PUT': 'triage.update',
        'PATCH': 'triage.update',
        'DELETE': 'triage.update'
    }

    def get_queryset(self):
        queryset = TriageVitals.objects.all().select_related('visit', 'patient', 'nurse')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(visit__facility_id__in=accessible_ids)
        visit_param = self.request.query_params.get('visit')
        if visit_param:
            queryset = queryset.filter(visit_id=visit_param)
        return queryset

    def create(self, request, *args, **kwargs):
        visit_id = request.data.get('visit')
        if not visit_id:
            return Response({'error': 'Visit is required.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_triage = TriageVitals.objects.filter(visit_id=visit_id).first()
        if existing_triage:
            serializer = self.get_serializer(existing_triage, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            triage = serializer.save(nurse=self.request.user)
            self._update_visit_queue(triage, is_update=True)
            return Response(self.get_serializer(triage).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        triage = serializer.save(nurse=self.request.user)
        self._update_visit_queue(triage, is_update=False)
        return Response(self.get_serializer(triage).data, status=status.HTTP_201_CREATED)

    def _update_visit_queue(self, triage, is_update=False):
        visit = triage.visit
        from_stat = visit.status
        visit.status = 'WAITING_FOR_DOCTOR'
        visit.current_queue = 'DOCTOR'
        visit.triage_end_time = timezone.now()
        visit.save()

        if hasattr(visit, 'token'):
            visit.token.status = 'TRIAGED'
            visit.token.save()

        from apps.visits.models import VisitStatusHistory
        action_note = "Nurse triage updated" if is_update else "Nurse triage logged"
        VisitStatusHistory.objects.create(
            visit=visit,
            from_status=from_stat,
            to_status='WAITING_FOR_DOCTOR',
            queue='DOCTOR',
            performed_by=self.request.user,
            performed_by_role=getattr(self.request.user, 'role', ''),
            notes=f"{action_note} by {self.request.user.full_name or self.request.user.username}"
        )


from rest_framework import serializers, viewsets, permissions
from django.utils import timezone
from apps.triage.models import TriageVitals
from apps.visits.models import Visit


class TriageVitalsSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')

    class Meta:
        model = TriageVitals
        fields = '__all__'

class TriageVitalsViewSet(viewsets.ModelViewSet):
    queryset = TriageVitals.objects.all().select_related('visit', 'patient', 'nurse')
    serializer_class = TriageVitalsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        triage = serializer.save(nurse=self.request.user)
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
        VisitStatusHistory.objects.create(
            visit=visit,
            from_status=from_stat,
            to_status='WAITING_FOR_DOCTOR',
            queue='DOCTOR',
            performed_by=self.request.user,
            performed_by_role=getattr(self.request.user, 'role', ''),
            notes=f"Nurse triage logged by {self.request.user.full_name or self.request.user.username}"
        )


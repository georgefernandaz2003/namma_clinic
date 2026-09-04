from rest_framework import serializers, viewsets, permissions
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
        # Update visit status to TRIAGED
        visit = triage.visit
        visit.status = 'TRIAGED'
        visit.save()
        if hasattr(visit, 'token'):
            visit.token.status = 'TRIAGED'
            visit.token.save()

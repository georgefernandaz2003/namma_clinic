"""
Clinical Consultations & Triage REST API (v1).
Captures clinical encounters and vitals linked to durable StaffProfile authorship.
"""
from rest_framework import serializers, viewsets
from apps.consultations.models import Consultation
from apps.triage.models import TriageVitals
from apps.common.permissions import IsActiveStaff, FacilityScopedPermission, get_request_staff

class TriageVitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageVitals
        fields = '__all__'
        read_only_fields = ['recorded_by']

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = [
            'id', 'visit', 'patient', 'facility', 'doctor_staff',
            'chief_complaint', 'clinical_findings', 'diagnosis_text',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['doctor_staff', 'created_at', 'updated_at']

class TriageVitalsViewSet(viewsets.ModelViewSet):
    queryset = TriageVitals.objects.all().select_related('visit', 'patient')
    serializer_class = TriageVitalsSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all().select_related('visit', 'patient', 'facility', 'doctor_staff')
    serializer_class = ConsultationSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def perform_create(self, serializer):
        staff = get_request_staff(self.request)
        serializer.save(doctor_staff=staff)

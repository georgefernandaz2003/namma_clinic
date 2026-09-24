"""
Clinical Consultations & Triage REST API (v1).
Captures clinical encounters and vitals linked to durable StaffProfile authorship.
Enforces facility scoping on querysets and mutation payloads.
"""
from rest_framework import serializers, viewsets
from apps.consultations.models import Consultation
from apps.triage.models import TriageVitals
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)

class TriageVitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageVitals
        fields = '__all__'
        read_only_fields = ['nurse']

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = [
            'id', 'visit', 'patient', 'facility', 'doctor_staff',
            'consultation_sequence', 'chief_complaint', 'clinical_history',
            'clinical_assessment', 'diagnosis_code', 'diagnosis_name',
            'treatment_plan', 'follow_up_date', 'clinical_notes', 'created_at'
        ]
        read_only_fields = ['doctor_staff', 'created_at']

class TriageVitalsViewSet(viewsets.ModelViewSet):
    queryset = TriageVitals.objects.all().select_related('visit', 'patient')
    serializer_class = TriageVitalsSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(visit__facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        staff = get_request_staff(self.request)
        visit = serializer.validated_data['visit']
        check_facility_permission(visit.facility, staff, self.request.user)
        serializer.save(nurse=self.request.user)

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all().select_related('visit', 'patient', 'facility', 'doctor_staff')
    serializer_class = ConsultationSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        staff = get_request_staff(self.request)
        is_doc = (
            self.request.user.is_superuser or
            getattr(self.request.user, "role", "") == "DOCTOR" or
            staff.designation in ["Medical Officer", "Doctor", "Chief Medical Officer"] or
            staff.role_assignments.filter(role__code="DOCTOR", is_active=True).exists()
        )
        if not is_doc:
            from apps.common.exceptions import UnauthorizedDomainAction
            raise UnauthorizedDomainAction("Only medical officers may conduct and record clinical consultations.")

        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, self.request.user)
        serializer.save(doctor_staff=staff)

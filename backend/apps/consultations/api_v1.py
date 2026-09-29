"""
Clinical Consultations and Triage REST API (v1).
Captures clinical encounters and vitals linked to durable StaffProfile authorship.
Enforces facility scoping on querysets and mutation payloads.
Enforces role-based clinical privacy boundaries:
- Triage: NURSE, DOCTOR, SUPERUSER only (denies Compounder, Lab Tech, Pharmacist, Admin, DHO)
- Consultation: DOCTOR, SUPERUSER only (denies Compounder, Lab Tech, Pharmacist, Nurse, Admin, DHO)
"""
from rest_framework import serializers, viewsets, permissions
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from apps.consultations.models import Consultation
from apps.triage.models import TriageVitals
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)
from apps.accounts.permissions import get_user_active_role_codes


class ClinicalTriagePermission(BasePermission):
    """
    Access to clinical triage records is restricted to clinical nursing and medical staff.
    Denies Compounder, Lab Tech, Pharmacist, Hospital Admin, District Officer.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False
        if user.is_superuser:
            return True

        role = getattr(user, 'role', '')
        if role in ['COMPOUNDER', 'LAB_TECHNICIAN', 'PHARMACIST', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER']:
            return False

        if request.method not in permissions.SAFE_METHODS:
            active_roles = get_user_active_role_codes(user)
            if active_roles:
                return bool({'NURSE', 'DOCTOR'}.intersection(active_roles))
            return role in ['NURSE', 'DOCTOR']

        return role in ['NURSE', 'DOCTOR']


class PhysicianConsultationPermission(BasePermission):
    """
    Access to physician consultation records is restricted to medical officers.
    Denies Compounder, Lab Tech, Pharmacist, Nurse, Hospital Admin, District Officer.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False
        if user.is_superuser:
            return True

        role = getattr(user, 'role', '')
        if role in ['COMPOUNDER', 'LAB_TECHNICIAN', 'PHARMACIST', 'NURSE', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER']:
            return False

        if request.method not in permissions.SAFE_METHODS:
            active_roles = get_user_active_role_codes(user)
            if active_roles:
                return 'DOCTOR' in active_roles
            return role == 'DOCTOR'

        return role == 'DOCTOR'


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
    permission_classes = [IsActiveStaff, ClinicalTriagePermission, FacilityScopedPermission]

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
    permission_classes = [IsActiveStaff, PhysicianConsultationPermission, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        staff = get_request_staff(self.request)
        active_roles = get_user_active_role_codes(self.request.user)
        if active_roles:
            is_doc = self.request.user.is_superuser or 'DOCTOR' in active_roles
        else:
            is_doc = self.request.user.is_superuser or getattr(self.request.user, 'role', '') == 'DOCTOR'
        if not is_doc:
            raise PermissionDenied("Only medical officers may conduct and record clinical consultations.")

        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, self.request.user)
        serializer.save(doctor_staff=staff)

"""
Patients REST API (v1).
Registration, retrieval, and facility-scoped demographic management.
"""
from rest_framework import serializers, viewsets, filters
from apps.patients.models import Patient
from apps.accounts.models import Person
from apps.common.permissions import IsActiveStaff, FacilityScopedPermission, get_request_staff, get_user_permitted_facilities

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'person', 'name', 'age', 'gender',
            'mobile', 'address', 'registered_at_facility', 'registration_date'
        ]
        read_only_fields = ['patient_id', 'registration_date']

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().select_related('person', 'registered_at_facility')
    serializer_class = PatientSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'mobile', 'patient_id']

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(registered_at_facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        import uuid, datetime
        staff = get_request_staff(self.request)
        fac = serializer.validated_data.get('registered_at_facility')
        if not fac and staff.facility_assignments.filter(is_active=True).exists():
            fac = staff.facility_assignments.filter(is_active=True).first().facility

        pat_id = f"PAT-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        serializer.save(patient_id=pat_id, registered_at_facility=fac)

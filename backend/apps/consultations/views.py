from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from apps.consultations.models import Consultation, Prescription, PrescriptionItem

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    doctor_name = serializers.ReadOnlyField(source='doctor.full_name')
    patient_name = serializers.ReadOnlyField(source='patient.name')

    class Meta:
        model = Prescription
        fields = '__all__'

class ConsultationSerializer(serializers.ModelSerializer):
    prescription = PrescriptionSerializer(read_only=True)
    patient_name = serializers.ReadOnlyField(source='patient.name')
    doctor_name = serializers.ReadOnlyField(source='doctor.full_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = Consultation
        fields = '__all__'

from apps.accounts.permissions import get_accessible_facility_ids_for_user

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Consultation.objects.all().select_related('visit', 'patient', 'doctor', 'facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        visit_id = data.get('visit')
        patient_id = data.get('patient')
        facility_id = data.get('facility')
        
        consultation = Consultation.objects.create(
            visit_id=visit_id,
            patient_id=patient_id,
            facility_id=facility_id,
            doctor=request.user,
            chief_complaint=data.get('chief_complaint', ''),
            clinical_history=data.get('clinical_history', ''),
            clinical_assessment=data.get('clinical_assessment', ''),
            diagnosis_code=data.get('diagnosis_code', 'E11'),
            diagnosis_name=data.get('diagnosis_name', 'Type 2 Diabetes Mellitus'),
            treatment_plan=data.get('treatment_plan', ''),
            follow_up_date=data.get('follow_up_date') or None,
            clinical_notes=data.get('clinical_notes', '')
        )

        # Update visit status
        visit = consultation.visit
        visit.status = 'COMPLETED'
        visit.save()
        if hasattr(visit, 'token'):
            visit.token.status = 'COMPLETED'
            visit.token.save()

        # Handle Prescriptions if provided
        prescription_items = data.get('prescription_items', [])
        if prescription_items:
            prescription = Prescription.objects.create(
                consultation=consultation,
                patient_id=patient_id,
                doctor=request.user,
                facility_id=facility_id,
                status='ACTIVE'
            )
            for item in prescription_items:
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine_name=item.get('medicine_name'),
                    dosage=item.get('dosage', '1-0-1 After Food'),
                    frequency=item.get('frequency', 'Twice Daily'),
                    duration_days=item.get('duration_days', 7),
                    quantity=item.get('quantity', 14),
                    status='PENDING'
                )

        return Response(ConsultationSerializer(consultation).data, status=status.HTTP_201_CREATED)

class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility', 'status', 'patient']

    def get_queryset(self):
        queryset = Prescription.objects.all().select_related('consultation', 'patient', 'doctor', 'facility').prefetch_related('items')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

from django.utils import timezone
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from apps.consultations.models import Consultation, Prescription, PrescriptionItem

import datetime

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    doctor_name = serializers.ReadOnlyField(source='doctor.full_name')
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_age = serializers.ReadOnlyField(source='patient.age')
    patient_gender = serializers.ReadOnlyField(source='patient.gender')
    token_number = serializers.SerializerMethodField()
    visit_id = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = '__all__'

    def get_token_number(self, obj):
        if hasattr(obj, 'consultation') and obj.consultation and hasattr(obj.consultation, 'visit') and obj.consultation.visit:
            if hasattr(obj.consultation.visit, 'token') and obj.consultation.visit.token:
                return obj.consultation.visit.token.token_number
            return obj.consultation.visit.id
        return None

    def get_visit_id(self, obj):
        if hasattr(obj, 'consultation') and obj.consultation and obj.consultation.visit:
            return obj.consultation.visit.id
        return None

class ConsultationSerializer(serializers.ModelSerializer):
    prescription = PrescriptionSerializer(read_only=True)
    patient_name = serializers.ReadOnlyField(source='patient.name')
    doctor_name = serializers.ReadOnlyField(source='doctor.full_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = Consultation
        fields = '__all__'

from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]

    required_permissions = {
        'GET': 'consultation.view',
        'POST': 'consultation.create',
        'PUT': 'consultation.update',
        'PATCH': 'consultation.update',
        'DELETE': 'consultation.update'
    }

    def get_queryset(self):
        queryset = Consultation.objects.all().select_related('visit', 'patient', 'doctor', 'facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        visit_id = data.get('visit')
        patient_id = data.get('patient')
        facility_id = data.get('facility')
        
        consultation = Consultation.objects.filter(visit_id=visit_id).first()
        if consultation:
            consultation.chief_complaint = data.get('chief_complaint', consultation.chief_complaint)
            consultation.clinical_history = data.get('clinical_history', consultation.clinical_history)
            consultation.clinical_assessment = data.get('clinical_assessment', consultation.clinical_assessment)
            consultation.diagnosis_code = data.get('diagnosis_code', consultation.diagnosis_code)
            consultation.diagnosis_name = data.get('diagnosis_name', consultation.diagnosis_name)
            consultation.clinical_notes = data.get('clinical_notes', consultation.clinical_notes)
            consultation.save()
        else:
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

        # Handle Prescriptions if provided
        prescription_items = data.get('prescription_items', [])
        if prescription_items:
            prescription = getattr(consultation, 'prescription', None) or Prescription.objects.filter(consultation=consultation).first()
            if not prescription:
                prescription = Prescription.objects.create(
                    consultation=consultation,
                    patient_id=patient_id,
                    doctor=request.user,
                    facility_id=facility_id,
                    status='PENDING'
                )
            else:
                prescription.status = 'PENDING'
                prescription.save(update_fields=['status'])
                prescription.items.all().delete()

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

        # Handle Lab Diagnostic Orders if provided directly
        lab_test_ids = data.get('lab_test_ids') or data.get('tests') or []
        if lab_test_ids:
            from apps.laboratory.models import LabOrder, LabTestMaster
            for tid in lab_test_ids:
                try:
                    test_obj = LabTestMaster.objects.filter(pk=tid).first()
                    if test_obj:
                        LabOrder.objects.get_or_create(
                            visit_id=visit_id,
                            test_master=test_obj,
                            defaults={
                                'patient_id': patient_id,
                                'facility_id': facility_id,
                                'doctor': request.user,
                                'status': 'ORDERED',
                                'consultation': consultation
                            }
                        )
                except Exception:
                    pass

        # Update visit status & queue
        visit = consultation.visit
        if visit:
            from apps.laboratory.models import LabOrder
            from django.db.models import Q
            has_pending_lab = LabOrder.objects.filter(
                Q(consultation=consultation) | Q(visit=visit) | Q(patient=consultation.patient, facility=consultation.facility),
                status__in=['ORDERED', 'SAMPLE_COLLECTED']
            ).exists()

            if has_pending_lab:
                visit.current_queue = 'LAB'
                visit.status = 'LAB_PENDING'
            elif prescription_items:
                visit.current_queue = 'PHARMACY'
                visit.status = 'WAITING_FOR_PHARMACY'
            else:
                visit.current_queue = 'COMPLETED'
                visit.status = 'COMPLETED'
                visit.completed_time = timezone.now()
            visit.save()
            if hasattr(visit, 'token'):
                visit.token.status = 'COMPLETED' if visit.status == 'COMPLETED' else 'IN_PROGRESS'
                visit.token.save()

        return Response(ConsultationSerializer(consultation).data, status=status.HTTP_201_CREATED)

class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'prescription.view',
        'POST': 'prescription.create',
        'PUT': 'prescription.update',
        'PATCH': 'prescription.update',
        'DELETE': 'prescription.update'
    }
    filterset_fields = ['facility', 'status', 'patient']

    def get_queryset(self):
        queryset = Prescription.objects.all().select_related('consultation', 'consultation__visit', 'consultation__visit__token', 'patient', 'doctor', 'facility').prefetch_related('items').order_by('-date', '-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        
        req_date = self.request.query_params.get('date')
        if req_date and req_date != 'all':
            try:
                target_date = datetime.datetime.strptime(req_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date=target_date)
            except ValueError:
                pass

        visit_param = self.request.query_params.get('visit')
        if visit_param:
            queryset = queryset.filter(consultation__visit_id=visit_param)

        return queryset

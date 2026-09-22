from django.utils import timezone
from django.db import models
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.visits.models import Visit

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_generic_name = serializers.ReadOnlyField(source='medicine.generic_name')
    medicine_brand_name = serializers.ReadOnlyField(source='medicine.brand_name')

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

    def validate(self, attrs):
        status_val = attrs.get('status')
        if status_val == 'DISPENSED' and self.instance:
            if self.instance.items.filter(status='PENDING').exists():
                raise serializers.ValidationError({
                    'status': 'Cannot set prescription header to DISPENSED while items remain PENDING.'
                })
        return attrs

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
        visit_param = self.request.query_params.get('visit')
        if visit_param:
            queryset = queryset.filter(visit_id=visit_param)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        visit_id = data.get('visit')
        patient_id = data.get('patient')
        facility_id = data.get('facility')

        if not visit_id:
            return Response({'error': 'Visit is required for consultation.'}, status=status.HTTP_400_BAD_REQUEST)

        # FND-09: Ensure visit is not untriaged in triage queue
        visit_obj = Visit.objects.filter(id=visit_id).first()
        if visit_obj and (visit_obj.current_queue == 'TRIAGE' or visit_obj.status in ['WAITING_FOR_TRIAGE', 'IN_TRIAGE']):
            from apps.triage.models import TriageVitals
            if not TriageVitals.objects.filter(visit_id=visit_id).exists():
                return Response({'error': 'Cannot record consultation: Patient is still in TRIAGE queue without recorded vitals.'}, status=status.HTTP_400_BAD_REQUEST)
        
        consultation = Consultation.objects.filter(visit_id=visit_id).first()
        is_update = consultation is not None

        if is_update:
            consultation.chief_complaint = data.get('chief_complaint', consultation.chief_complaint)
            consultation.clinical_history = data.get('clinical_history', consultation.clinical_history)
            consultation.clinical_assessment = data.get('clinical_assessment', consultation.clinical_assessment)
            consultation.diagnosis_code = data.get('diagnosis_code', consultation.diagnosis_code)
            consultation.diagnosis_name = data.get('diagnosis_name', consultation.diagnosis_name)
            consultation.clinical_notes = data.get('clinical_notes', consultation.clinical_notes)
            consultation.treatment_plan = data.get('treatment_plan', consultation.treatment_plan)
            if data.get('follow_up_date'):
                consultation.follow_up_date = data.get('follow_up_date')
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
                    patient_id=patient_id or consultation.patient_id,
                    doctor=request.user,
                    facility_id=facility_id or consultation.facility_id,
                    status='ACTIVE'
                )
            else:
                prescription.items.all().delete()

            from apps.pharmacy.models import MedicineMaster
            for item in prescription_items:
                medicine_id = item.get('medicine_id') or item.get('medicine')
                medicine_obj = None
                if medicine_id:
                    medicine_obj = MedicineMaster.objects.filter(id=medicine_id).first()
                elif item.get('medicine_name'):
                    clean_name = item.get('medicine_name').strip()
                    medicine_obj = MedicineMaster.objects.filter(
                        generic_name__iexact=clean_name
                    ).first()
                    if not medicine_obj:
                        first_word = clean_name.split()[0]
                        medicine_obj = MedicineMaster.objects.filter(generic_name__icontains=first_word).first()

                med_name = item.get('medicine_name') or (medicine_obj.generic_name if medicine_obj else 'Prescribed Medicine')

                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine=medicine_obj,
                    medicine_name=med_name,
                    dosage=item.get('dosage', '1-0-1 After Food'),
                    frequency=item.get('frequency', 'Twice Daily'),
                    duration_days=item.get('duration_days', 7),
                    quantity=item.get('quantity', 14),
                    status='PENDING'
                )

        # Handle Lab Test Orders if provided directly
        lab_test_ids = data.get('lab_test_ids', [])
        has_lab_orders = bool(lab_test_ids) or data.get('has_lab_orders')

        # Update visit status & queue
        visit = consultation.visit
        if visit:
            if lab_test_ids:
                import datetime
                from apps.laboratory.models import LabTestMaster, LabToken, LabOrder
                today = datetime.date.today()
                lab_token = LabToken.objects.filter(visit=visit, date=today).exclude(status='COMPLETED').first()
                if not lab_token:
                    max_tok = LabToken.objects.filter(facility_id=facility_id or consultation.facility_id, date=today).aggregate(models.Max('token_number'))['token_number__max'] or 0
                    tok_num = max_tok + 1
                    lab_token = LabToken.objects.create(
                        token_number=tok_num,
                        token_code=f"LAB-{tok_num:03d}",
                        visit=visit,
                        facility_id=facility_id or consultation.facility_id,
                        date=today,
                        status='ORDERED'
                    )
                for tid in lab_test_ids:
                    tm = LabTestMaster.objects.filter(id=tid).first()
                    if tm and not LabOrder.objects.filter(visit=visit, consultation=consultation, test_master=tm).exists():
                        LabOrder.objects.create(
                            lab_token=lab_token,
                            visit=visit,
                            consultation=consultation,
                            patient_id=patient_id or consultation.patient_id,
                            doctor=request.user,
                            facility_id=facility_id or consultation.facility_id,
                            test_master=tm,
                            status='ORDERED'
                        )

            from apps.visits.models import VisitStatusHistory
            from_stat = visit.status

            # Check if visit currently has pending lab orders
            if not has_lab_orders and hasattr(visit, 'lab_orders'):
                has_lab_orders = visit.lab_orders.exclude(status='VERIFIED').exists()

            if has_lab_orders and visit.status != 'DOCTOR_REVIEW':
                # Move encounter to WAITING_FOR_LAB; do NOT mark COMPLETED; do NOT move directly to PHARMACY
                visit.current_queue = 'LAB'
                visit.status = 'WAITING_FOR_LAB'
                visit.save()
                if hasattr(visit, 'token'):
                    visit.token.status = 'IN_PROGRESS'
                    visit.token.save()
                VisitStatusHistory.objects.create(
                    visit=visit,
                    from_status=from_stat,
                    to_status='WAITING_FOR_LAB',
                    queue='LAB',
                    performed_by=request.user,
                    performed_by_role=getattr(request.user, 'role', ''),
                    notes="Consultation saved. Waiting for laboratory investigations."
                )
            else:
                # No pending lab tests (or finalizing encounter after DOCTOR_REVIEW)
                if prescription_items:
                    visit.current_queue = 'PHARMACY'
                    visit.status = 'WAITING_FOR_PHARMACY'
                    visit.save()
                    if hasattr(visit, 'token'):
                        visit.token.status = 'IN_PROGRESS'
                        visit.token.save()
                    VisitStatusHistory.objects.create(
                        visit=visit,
                        from_status=from_stat,
                        to_status='WAITING_FOR_PHARMACY',
                        queue='PHARMACY',
                        performed_by=request.user,
                        performed_by_role=getattr(request.user, 'role', ''),
                        notes="Consultation finalized with prescription. Sent to Pharmacy."
                    )
                else:
                    visit.current_queue = 'COMPLETED'
                    visit.status = 'COMPLETED'
                    visit.completed_time = timezone.now()
                    visit.save()
                    if hasattr(visit, 'token'):
                        visit.token.status = 'COMPLETED'
                        visit.token.save()
                    VisitStatusHistory.objects.create(
                        visit=visit,
                        from_status=from_stat,
                        to_status='COMPLETED',
                        queue='COMPLETED',
                        performed_by=request.user,
                        performed_by_role=getattr(request.user, 'role', ''),
                        notes="Consultation completed & finalized."
                    )

        res_status = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED
        return Response(ConsultationSerializer(consultation).data, status=res_status)

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
        queryset = Prescription.objects.all().select_related('consultation', 'patient', 'doctor', 'facility').prefetch_related('items')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.referrals.models import Referral, ReferralResponse, FollowUp
import datetime

class ReferralResponseSerializer(serializers.ModelSerializer):
    doctor_name = serializers.ReadOnlyField(source='hospital_doctor.full_name')

    class Meta:
        model = ReferralResponse
        fields = '__all__'

class ReferralSerializer(serializers.ModelSerializer):
    source_facility_name = serializers.ReadOnlyField(source='source_facility.facility_name')
    destination_facility_name = serializers.ReadOnlyField(source='destination_facility.facility_name')
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mobile = serializers.ReadOnlyField(source='patient.mobile')
    referring_doctor_name = serializers.ReadOnlyField(source='referring_doctor.full_name')
    response = ReferralResponseSerializer(read_only=True)

    class Meta:
        model = Referral
        fields = '__all__'

class FollowUpSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = FollowUp
        fields = '__all__'

from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class ReferralViewSet(viewsets.ModelViewSet):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'referrals.view',
        'POST': 'referrals.create',
        'PUT': 'referrals.create',
        'PATCH': 'referrals.create',
        'DELETE': 'referrals.create'
    }
    filterset_fields = ['source_facility', 'destination_facility', 'status', 'urgency']


    def get_queryset(self):
        queryset = Referral.objects.all().select_related('patient', 'source_facility', 'destination_facility', 'referring_doctor')
        from django.db.models import Q
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(
                Q(source_facility_id__in=accessible_ids) | Q(destination_facility_id__in=accessible_ids)
            ).distinct()
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            if accessible_ids is not None and int(facility_param) not in accessible_ids:
                return queryset.none()
            queryset = queryset.filter(
                Q(source_facility_id=facility_param) | Q(destination_facility_id=facility_param)
            ).distinct()
        return queryset.order_by('-id')

    def create(self, request, *args, **kwargs):
        count = Referral.objects.count() + 1
        ref_id = f"REF-{datetime.date.today().strftime('%Y%m%d')}-{count:04d}"
        
        referral = Referral.objects.create(
            referral_id=ref_id,
            patient_id=request.data.get('patient'),
            visit_id=request.data.get('visit'),
            consultation_id=request.data.get('consultation'),
            source_facility_id=request.data.get('source_facility'),
            destination_facility_id=request.data.get('destination_facility'),
            referring_doctor=request.user,
            reason=request.data.get('reason', 'Specialist Consultation'),
            clinical_summary=request.data.get('clinical_summary', ''),
            required_service=request.data.get('required_service', 'Specialist Evaluation'),
            urgency=request.data.get('urgency', 'ROUTINE'),
            status='CREATED'
        )

        return Response(ReferralSerializer(referral).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        referral = self.get_object()
        findings = request.data.get('specialist_findings', 'Specialist examination completed.')
        treatment = request.data.get('treatment_summary', 'Medication adjusted.')
        advice = request.data.get('return_advice', 'Return to primary clinic for follow-up.')

        response, _ = ReferralResponse.objects.get_or_create(
            referral=referral,
            defaults={
                'hospital_doctor': request.user,
                'specialist_findings': findings,
                'treatment_summary': treatment,
                'return_advice': advice
            }
        )

        referral.status = 'COMPLETED'
        referral.save()

        # Create return follow-up for clinic
        FollowUp.objects.create(
            patient=referral.patient,
            referral=referral,
            facility=referral.source_facility,
            category='REFERRAL',
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            status='PENDING',
            notes=f"Return referral follow-up after hospital consultation: {advice}"
        )

        return Response({
            'status': 'Referral completed and response logged!',
            'referral': ReferralSerializer(referral).data,
            'response': ReferralResponseSerializer(response).data
        })

class FollowUpViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'patients.view',
        'POST': 'patients.update',
        'PUT': 'patients.update',
        'PATCH': 'patients.update',
        'DELETE': 'patients.update'
    }
    filterset_fields = ['facility', 'status', 'category']

    def get_queryset(self):
        queryset = FollowUp.objects.all().select_related('patient', 'facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset


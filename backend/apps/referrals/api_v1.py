"""
Referrals & Follow-Up REST API (v1).
State machine transitions and cross-encounter completion via domain services.
Enforces facility scoping on querysets and mutation payloads.
"""
from django.db import models
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.referrals.services import (
    create_referral_order, transition_referral_state, create_followup_task, complete_followup
)
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)

class ReferralEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralEvent
        fields = '__all__'
        read_only_fields = ['recorded_at']

class ReferralOrderSerializer(serializers.ModelSerializer):
    events = ReferralEventSerializer(many=True, read_only=True)

    class Meta:
        model = ReferralOrder
        fields = '__all__'
        read_only_fields = ['referral_number', 'status', 'referring_doctor', 'created_at', 'updated_at']

class TransitionReferralSerializer(serializers.Serializer):
    new_status = serializers.CharField(max_length=64)
    notes = serializers.CharField(required=False, default="")

class FollowUpTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpTask
        fields = '__all__'
        read_only_fields = ['status', 'completed_in_visit', 'completed_by_staff', 'completed_at', 'created_at']

class CompleteFollowUpSerializer(serializers.Serializer):
    completed_in_visit_id = serializers.IntegerField()


class ReferralOrderViewSet(viewsets.ModelViewSet):
    queryset = ReferralOrder.objects.all().select_related('patient', 'source_facility', 'destination_facility', 'referring_doctor').prefetch_related('events')
    serializer_class = ReferralOrderSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(models.Q(source_facility_id__in=permitted) | models.Q(destination_facility_id__in=permitted))
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        src_fac = serializer.validated_data['source_facility']
        check_facility_permission(src_fac, staff, request.user)

        order = create_referral_order(
            patient=serializer.validated_data['patient'],
            visit=serializer.validated_data['visit'],
            source_facility=src_fac,
            destination_facility=serializer.validated_data['destination_facility'],
            referring_doctor_staff=staff,
            reason=serializer.validated_data['reason'],
            urgency=serializer.validated_data.get('urgency', 'ROUTINE'),
            clinical_summary=serializer.validated_data.get('clinical_summary', '')
        )
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='transition')
    def transition_state(self, request, pk=None):
        order = self.get_object()
        serializer = TransitionReferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        updated_order, event = transition_referral_state(
            referral_order=order,
            new_status=serializer.validated_data['new_status'],
            actor_staff=staff,
            notes=serializer.validated_data.get('notes', '')
        )
        return Response(self.get_serializer(updated_order).data)

class FollowUpTaskViewSet(viewsets.ModelViewSet):
    queryset = FollowUpTask.objects.all().select_related('patient', 'facility', 'completed_in_visit', 'completed_by_staff')
    serializer_class = FollowUpTaskSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, request.user)

        task = create_followup_task(
            patient=serializer.validated_data['patient'],
            facility=fac,
            due_date=serializer.validated_data['due_date'],
            category=serializer.validated_data.get('category', 'GENERAL'),
            originating_visit=serializer.validated_data.get('originating_visit'),
            referral=serializer.validated_data.get('referral'),
            clinical_instructions=serializer.validated_data.get('clinical_instructions', '')
        )
        return Response(self.get_serializer(task).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        task = self.get_object()
        serializer = CompleteFollowUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        from apps.visits.models import Visit
        visit = Visit.objects.get(pk=serializer.validated_data['completed_in_visit_id'])

        completed_task = complete_followup(
            followup_task=task,
            completed_in_visit=visit,
            completing_staff=staff
        )
        return Response(self.get_serializer(completed_task).data)

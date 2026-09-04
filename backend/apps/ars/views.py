from rest_framework import serializers, viewsets, permissions
from apps.ars.models import ARSMember, ARSMeeting, ARSActionItem

class ARSActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARSActionItem
        fields = '__all__'

class ARSMeetingSerializer(serializers.ModelSerializer):
    action_items = ARSActionItemSerializer(many=True, read_only=True)
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = ARSMeeting
        fields = '__all__'

class ARSMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARSMember
        fields = '__all__'

class ARSMeetingViewSet(viewsets.ModelViewSet):
    queryset = ARSMeeting.objects.all().select_related('facility').prefetch_related('action_items')
    serializer_class = ARSMeetingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility']

class ARSMemberViewSet(viewsets.ModelViewSet):
    queryset = ARSMember.objects.all()
    serializer_class = ARSMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

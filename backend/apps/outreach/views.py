from rest_framework import serializers, viewsets, permissions
from apps.outreach.models import OutreachActivity

class OutreachActivitySerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = OutreachActivity
        fields = '__all__'

class OutreachActivityViewSet(viewsets.ModelViewSet):
    queryset = OutreachActivity.objects.all().select_related('facility', 'ward')
    serializer_class = OutreachActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['facility']

from rest_framework import serializers, viewsets, permissions
from apps.audit.models import AuditLog
from apps.common.permissions import (
    IsAdministrativeStaff, get_request_staff, get_user_permitted_facilities
)

class AuditLogSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = AuditLog
        fields = '__all__'

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdministrativeStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

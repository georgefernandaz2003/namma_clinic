from rest_framework import viewsets, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from django.db.models import Q

from apps.accounts.models import User, RoleChoices
from apps.accounts.serializers import UserSerializer, UserProfileSerializer
from apps.accounts.permissions import (
    HasPermission,
    HasFacilityScope,
    get_accessible_facility_ids_for_user
)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'staff.view',
        'POST': 'staff.create',
        'PUT': 'staff.update',
        'PATCH': 'staff.update',
        'DELETE': 'staff.delete',
        'list': 'staff.view',
        'retrieve': 'staff.view',
        'create': 'staff.create',
        'update': 'staff.update',
        'partial_update': 'staff.update',
        'destroy': 'staff.delete',
    }
    filterset_fields = ['role', 'assigned_facility', 'assigned_district']
    search_fields = ['username', 'full_name', 'email']
    ordering = ['id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return User.objects.none()

        queryset = User.objects.all().select_related('assigned_facility', 'assigned_district').order_by('id')

        # 1. District Officer: Scoped to facilities in their assigned district and users in the district
        if user.role == RoleChoices.DISTRICT_OFFICER:
            if user.assigned_district_id:
                accessible_fac_ids = get_accessible_facility_ids_for_user(user)
                queryset = queryset.filter(
                    Q(assigned_district_id=user.assigned_district_id) |
                    Q(assigned_facility_id__in=accessible_fac_ids or [])
                )
            else:
                queryset = queryset.none()

            facility_param = self.request.query_params.get('facility')
            if facility_param:
                queryset = queryset.filter(assigned_facility_id=facility_param)

            return queryset

        # 2. Hospital Admin & operational staff: Scoped strictly to user's assigned facility
        accessible_fac_ids = get_accessible_facility_ids_for_user(user)
        if not accessible_fac_ids:
            return User.objects.none()

        queryset = queryset.filter(assigned_facility_id__in=accessible_fac_ids)

        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(assigned_facility_id=facility_param)

        return queryset

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = User.objects.filter(**filter_kwargs).select_related('assigned_facility', 'assigned_district').first()
        if not obj:
            raise Http404("No User matches the given query.")

        # Check object permissions against user facility/district scope
        self.check_object_permissions(self.request, obj)

        # Ensure object is part of the scoped queryset
        if not self.filter_queryset(self.get_queryset()).filter(pk=obj.pk).exists():
            self.permission_denied(
                self.request,
                message="You do not have authorization to access resources outside your assigned facility."
            )

        return obj

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == RoleChoices.HOSPITAL_ADMIN:
            serializer.save(assigned_facility=user.assigned_facility)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise serializers.ValidationError("You cannot delete your own account.")
        if self.request.user.role == RoleChoices.HOSPITAL_ADMIN:
            if instance.assigned_facility_id != self.request.user.assigned_facility_id:
                raise permissions.exceptions.PermissionDenied("You cannot delete staff belonging to another facility.")
        super().perform_destroy(instance)


class CurrentUserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


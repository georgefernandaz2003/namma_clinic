"""
Organization & Facility REST API (v1).
Manages State, District, Taluk, Zone, Ward, Facility, and Department hierarchies.
"""
from rest_framework import serializers, viewsets
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.common.permissions import IsActiveStaff, IsAdministrativeStaff, get_request_staff, get_user_permitted_facilities

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class TalukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluk
        fields = '__all__'

class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class FacilitySerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Facility
        fields = [
            'id', 'facility_code', 'facility_name', 'facility_type',
            'state', 'district', 'zone', 'ward', 'address', 'status', 'departments'
        ]


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsActiveStaff]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all().select_related('state')
    serializer_class = DistrictSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class TalukViewSet(viewsets.ModelViewSet):
    queryset = Taluk.objects.all().select_related('district')
    serializer_class = TalukSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.all().select_related('zone')
    serializer_class = WardSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().select_related('state', 'district', 'zone', 'ward').prefetch_related('departments')
    serializer_class = FacilitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(id__in=permitted)
        return qs

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related('facility')
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrativeStaff()]
        return [IsActiveStaff()]

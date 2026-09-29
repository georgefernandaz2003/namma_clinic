"""
Diagnostics REST API (v1).
Delegates requisition, specimen collection, result entry, verification, and amendment to domain services.
Enforces facility isolation and verification immutability.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen,
    TestRequest, DiagnosticResult, DiagnosticResultAmendment
)
from apps.laboratory.services import (
    create_diagnostic_order, create_test_request, collect_specimen,
    record_diagnostic_result, verify_diagnostic_result, amend_diagnostic_result
)
from apps.common.permissions import (
    IsMedicalOfficer,
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)

class DiagnosticTestMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTestMaster
        fields = '__all__'

class DiagnosticOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticOrder
        fields = '__all__'
        read_only_fields = ['order_number', 'ordering_doctor_staff', 'lab_token_number', 'status', 'created_at']

class TestRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestRequest
        fields = '__all__'
        read_only_fields = ['status', 'created_at']

class SpecimenSerializer(serializers.ModelSerializer):
    test_request_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = Specimen
        fields = ['id', 'diagnostic_order', 'barcode_identifier', 'specimen_type', 'collected_by_staff', 'collected_at', 'status', 'test_request_ids']
        read_only_fields = ['collected_by_staff', 'collected_at', 'status']

class DiagnosticResultSerializer(serializers.ModelSerializer):
    reference_range_applied = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = DiagnosticResult
        fields = '__all__'
        read_only_fields = ['status', 'entered_by_staff', 'entered_at', 'verified_by_staff', 'verified_at']

class AmendResultSerializer(serializers.Serializer):
    amendment_reason = serializers.CharField(max_length=255)
    amended_value_text = serializers.CharField(required=False, default="")
    amended_value_numeric = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, allow_null=True)



from rest_framework.permissions import BasePermission

class DiagnosticAccessPermission(BasePermission):
    """
    Denies diagnostic laboratory records to Compounder and Pharmacist.
    Allows Lab Technician, Doctor, Nurse, Hospital Admin, District Officer, Superuser.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        if role in ['COMPOUNDER', 'PHARMACIST']:
            return False
        return True

class DiagnosticTestMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiagnosticTestMaster.objects.filter(is_active=True)
    serializer_class = DiagnosticTestMasterSerializer
    permission_classes = [IsActiveStaff]

class DiagnosticOrderViewSet(viewsets.ModelViewSet):
    queryset = DiagnosticOrder.objects.all().select_related('visit', 'facility', 'ordering_doctor_staff')
    serializer_class = DiagnosticOrderSerializer
    permission_classes = [IsActiveStaff, DiagnosticAccessPermission, FacilityScopedPermission]

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

        order = create_diagnostic_order(
            visit=serializer.validated_data['visit'],
            facility=fac,
            ordering_doctor_staff=staff,
            priority=serializer.validated_data.get('priority', 'ROUTINE'),
            clinical_indication=serializer.validated_data.get('clinical_indication', ''),
            order_date=serializer.validated_data.get('order_date')
        )
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

class TestRequestViewSet(viewsets.ModelViewSet):
    queryset = TestRequest.objects.all().select_related('diagnostic_order', 'test_master', 'specimen')
    serializer_class = TestRequestSerializer
    permission_classes = [IsActiveStaff, DiagnosticAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(diagnostic_order__facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        diag_order = serializer.validated_data['diagnostic_order']
        check_facility_permission(diag_order.facility, staff, request.user)

        req = create_test_request(
            diagnostic_order=diag_order,
            test_master=serializer.validated_data['test_master'],
            specimen=serializer.validated_data.get('specimen')
        )
        return Response(self.get_serializer(req).data, status=status.HTTP_201_CREATED)

class SpecimenViewSet(viewsets.ModelViewSet):
    queryset = Specimen.objects.all().select_related('diagnostic_order', 'collected_by_staff')
    serializer_class = SpecimenSerializer
    permission_classes = [IsActiveStaff, DiagnosticAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(diagnostic_order__facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        diag_order = serializer.validated_data['diagnostic_order']
        check_facility_permission(diag_order.facility, staff, request.user)

        tr_ids = serializer.validated_data.get('test_request_ids', [])
        test_reqs = TestRequest.objects.filter(id__in=tr_ids) if tr_ids else None

        specimen = collect_specimen(
            diagnostic_order=diag_order,
            barcode_identifier=serializer.validated_data['barcode_identifier'],
            specimen_type=serializer.validated_data['specimen_type'],
            collected_by_staff=staff,
            test_requests=test_reqs
        )
        return Response(self.get_serializer(specimen).data, status=status.HTTP_201_CREATED)

class DiagnosticResultViewSet(viewsets.ModelViewSet):
    """
    Diagnostic results endpoint.
    Direct PUT/PATCH/DELETE is disabled to guarantee verification immutability.
    Draft creation: POST /
    Verification: POST /{id}/verify/
    Amendment: POST /{id}/amend/
    """
    queryset = DiagnosticResult.objects.all().select_related('test_request', 'entered_by_staff', 'verified_by_staff')
    serializer_class = DiagnosticResultSerializer
    permission_classes = [IsActiveStaff, DiagnosticAccessPermission]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(test_request__diagnostic_order__facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        tr = serializer.validated_data['test_request']
        check_facility_permission(tr.diagnostic_order.facility, staff, request.user)

        result = record_diagnostic_result(
            test_request=tr,
            entered_by_staff=staff,
            result_value_text=serializer.validated_data.get('result_value_text', ''),
            result_value_numeric=serializer.validated_data.get('result_value_numeric'),
            reference_range_applied=serializer.validated_data.get('reference_range_applied', ''),
            is_abnormal=serializer.validated_data.get('is_abnormal', False),
            is_critical_panic=serializer.validated_data.get('is_critical_panic', False)
        )
        return Response(self.get_serializer(result).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='verify', permission_classes=[IsMedicalOfficer])
    def verify(self, request, pk=None):
        diag_res = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(diag_res.test_request.diagnostic_order.facility, staff, request.user)
        verified = verify_diagnostic_result(diag_res, verified_by_staff=staff)
        return Response(self.get_serializer(verified).data)

    @action(detail=True, methods=['post'], url_path='amend')
    def amend(self, request, pk=None):
        diag_res = self.get_object()
        serializer = AmendResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)
        check_facility_permission(diag_res.test_request.diagnostic_order.facility, staff, request.user)

        amended_res, amendment = amend_diagnostic_result(
            diagnostic_result=diag_res,
            amended_by_staff=staff,
            amendment_reason=serializer.validated_data['amendment_reason'],
            amended_value_text=serializer.validated_data.get('amended_value_text', ''),
            amended_value_numeric=serializer.validated_data.get('amended_value_numeric')
        )
        return Response(self.get_serializer(amended_res).data)

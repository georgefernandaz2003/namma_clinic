"""
Patients REST API (v1).
Registration, retrieval, and facility-scoped demographic management.
Authoritative RBAC:
- POST: Strictly restricted to roles possessing 'patients.create' (Compounder, Hospital Admin).
- PATCH / PUT: Strictly restricted to roles possessing 'patients.update_demographics' and whitelisted fields.
- Duplicate detection: Concurrency-safe check on (facility + normalized mobile + normalized name).
"""
import uuid
import datetime
import hashlib
from django.db import transaction, connection, IntegrityError
from rest_framework import serializers, viewsets, filters, permissions, exceptions, status
from rest_framework.response import Response
from apps.patients.models import Patient, normalize_patient_name, normalize_patient_mobile
from apps.accounts.models import Person
from apps.accounts.permissions import has_role_permission
from apps.common.permissions import (
    IsActiveStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)


class DuplicatePatientError(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A patient with matching demographic records (name and mobile) already exists at this facility."
    default_code = "duplicate_patient"


class IsPatientRegistrationStaff(permissions.BasePermission):
    """
    Authoritative permission class governing Patient creation and demographic updates.
    Rules:
    - Superusers have global authority.
    - POST (create): Requires 'patients.create'.
    - PATCH / PUT (update): Requires 'patients.update_demographics'.
    - Safe methods (GET, HEAD, OPTIONS): Requires IsActiveStaff.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False

        if user.is_superuser:
            return True

        staff = get_request_staff(request, required=False)
        if not staff or staff.status != 'ACTIVE':
            return False

        if view.action == 'create' or request.method == 'POST':
            return has_role_permission(user, 'patients.create')

        if view.action in ['update', 'partial_update'] or request.method in ['PUT', 'PATCH']:
            return has_role_permission(user, 'patients.update_demographics')

        return True

    def has_object_permission(self, request, view, obj):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'is_active', True):
            return False

        if user.is_superuser:
            return True

        if request.method in ['PUT', 'PATCH']:
            return has_role_permission(user, 'patients.update_demographics')

        return True


class PatientSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='registered_at_facility.facility_name')
    ward_name = serializers.ReadOnlyField(source='ward.name')
    district_name = serializers.ReadOnlyField(source='district.name')

    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'person', 'name', 'date_of_birth', 'age', 'gender',
            'mobile', 'address', 'ward', 'ward_name', 'district', 'district_name',
            'ABHA_ID_DEMO', 'emergency_contact', 'vulnerability_information',
            'registered_at_facility', 'facility_name', 'registration_date'
        ]
        read_only_fields = ['patient_id', 'registration_date']


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().select_related('person', 'registered_at_facility', 'ward', 'district')
    serializer_class = PatientSerializer
    permission_classes = [IsActiveStaff, IsPatientRegistrationStaff, FacilityScopedPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'mobile', 'patient_id']

    DEMOGRAPHIC_WHITELIST = {'address', 'mobile', 'emergency_contact', 'ward'}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ['update', 'partial_update', 'destroy']:
            return qs

        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            # Continuity-of-care policy: explicit demographic search allows statewide lookup
            return qs

        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(registered_at_facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        # 1. Authoritative permission check
        if not request.user.is_superuser and not has_role_permission(request.user, 'patients.create'):
            raise exceptions.PermissionDenied("You do not have permission to register new patients.")

        # 2. Extract and resolve target facility
        staff = get_request_staff(request, required=False)
        fac_id = request.data.get('registered_at_facility')
        fac = None
        if fac_id:
            from apps.facilities.models import Facility
            try:
                fac = Facility.objects.get(pk=fac_id)
            except Facility.DoesNotExist:
                raise exceptions.ValidationError({'registered_at_facility': 'Invalid facility ID.'})
        elif staff and staff.facility_assignments.filter(is_active=True).exists():
            fac = staff.facility_assignments.filter(is_active=True).first().facility
        elif request.user.assigned_facility:
            fac = request.user.assigned_facility

        if fac:
            check_facility_permission(fac, staff, request.user)

        # 3. Duplicate Patient Detection: same facility + normalized mobile + normalized name
        raw_name = request.data.get('name', '')
        raw_mobile = request.data.get('mobile', '')
        normalized_name = normalize_patient_name(raw_name)
        normalized_mobile = normalize_patient_mobile(raw_mobile)

        if normalized_name and normalized_mobile and fac:
            # Deterministic 60-bit signed key for PostgreSQL advisory xact lock
            lock_key = int(hashlib.sha256(f"{fac.id}:{normalized_name}:{normalized_mobile}".encode('utf-8')).hexdigest()[:15], 16)
            try:
                with transaction.atomic():
                    if connection.vendor == 'postgresql':
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT pg_advisory_xact_lock(%s);", [lock_key])

                    existing = Patient.objects.filter(
                        registered_at_facility=fac,
                        normalized_name=normalized_name,
                        normalized_mobile=normalized_mobile
                    ).first()
                    if existing:
                        raise DuplicatePatientError(
                            f"A patient with matching demographic records (name and mobile) is already registered at this facility with ID: {existing.patient_id}."
                        )

                    return super().create(request, *args, **kwargs)
            except IntegrityError as exc:
                err_msg = str(exc).lower()
                if 'unique_patient_facility_normalized_identity' in err_msg or 'duplicate key' in err_msg:
                    existing = Patient.objects.filter(
                        registered_at_facility=fac,
                        normalized_name=normalized_name,
                        normalized_mobile=normalized_mobile
                    ).first()
                    pat_id_str = f" with ID: {existing.patient_id}" if existing else ""
                    raise DuplicatePatientError(
                        f"A patient with matching demographic records (name and mobile) is already registered at this facility{pat_id_str}."
                    )
                raise
        else:
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        staff = get_request_staff(self.request, required=False)
        fac = serializer.validated_data.get('registered_at_facility')
        if not fac and staff and staff.facility_assignments.filter(is_active=True).exists():
            fac = staff.facility_assignments.filter(is_active=True).first().facility
        elif not fac and self.request.user.assigned_facility:
            fac = self.request.user.assigned_facility

        if fac:
            check_facility_permission(fac, staff, self.request.user)

        pat_id = f"PAT-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Clean/sanitize ABHA: store blank/empty string if not provided
        raw_abha = serializer.validated_data.get('ABHA_ID_DEMO', '')
        cleaned_abha = raw_abha.strip() if isinstance(raw_abha, str) else ''

        serializer.save(
            patient_id=pat_id,
            registered_at_facility=fac,
            ABHA_ID_DEMO=cleaned_abha
        )

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self._handle_demographic_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self._handle_demographic_update(request, *args, **kwargs)

    def _handle_demographic_update(self, request, *args, **kwargs):
        # 1. Authoritative permission check
        if not request.user.is_superuser and not has_role_permission(request.user, 'patients.update_demographics'):
            raise exceptions.PermissionDenied("You do not have permission to update patient demographics.")

        instance = self.get_object()
        staff = get_request_staff(request, required=False)

        # 2. Facility scope check
        if instance.registered_at_facility:
            check_facility_permission(instance.registered_at_facility, staff, request.user)

        # 3. Whitelist enforcement: prohibit non-demographic modifications
        disallowed_fields = set(request.data.keys()) - self.DEMOGRAPHIC_WHITELIST
        if disallowed_fields:
            raise exceptions.ValidationError({
                "error": f"Modification of protected fields is prohibited. Allowed demographic fields: {', '.join(sorted(self.DEMOGRAPHIC_WHITELIST))}. Disallowed fields attempted: {', '.join(sorted(disallowed_fields))}."
            })

        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied("Patient records cannot be deleted.")
        return super().destroy(request, *args, **kwargs)
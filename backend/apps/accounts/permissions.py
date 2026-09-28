from rest_framework import permissions

PERMISSION_ALIASES = {
    'patients.view': 'patients.read',
    'patients.read': 'patients.view',
    'patients.update': 'patients.update_demographics',
    'patients.update_demographics': 'patients.update',
    'queue.view': 'queue.read',
    'queue.read': 'queue.view',
    'appointments.view': 'appointments.read',
    'appointments.read': 'appointments.view',
    'vitals.view': 'vitals.read',
    'vitals.read': 'vitals.view',
    'triage.view': 'triage.read',
    'triage.read': 'triage.view',
    'consultation.view': 'consultation.read',
    'consultation.read': 'consultation.view',
    'diagnosis.view': 'diagnosis.read',
    'diagnosis.read': 'diagnosis.view',
    'prescription.view': 'prescription.read',
    'prescription.read': 'prescription.view',
    'lab_orders.view': 'lab_order.read',
    'lab_order.read': 'lab_orders.view',
    'lab_orders.create': 'lab_order.create',
    'lab_order.create': 'lab_orders.create',
    'lab_results.view': 'lab_result.read',
    'lab_result.read': 'lab_results.view',
    'lab_results.create': 'lab_result.create',
    'lab_result.create': 'lab_results.create',
    'lab_results.update': 'lab_result.update',
    'lab_result.update': 'lab_results.update',
    'pharmacy.view': 'inventory.read',
    'pharmacy.dispense': 'dispensation.create',
    'dispensation.create': 'pharmacy.dispense',
    'inventory.view': 'inventory.read',
    'inventory.read': 'inventory.view',
    'po.view': 'purchase_order.read',
    'purchase_order.read': 'po.view',
    'po.create': 'purchase_order.create',
    'purchase_order.create': 'po.create',
    'po.update': 'purchase_order.update',
    'purchase_order.update': 'po.update',
    'po.approve': 'purchase_order.approve',
    'purchase_order.approve': 'po.approve',
    'po.receive': 'goods_receipt.create',
    'goods_receipt.create': 'po.receive',
    'hospital.view': 'facility.read',
    'clinic.view': 'facility.read',
    'facility.read': 'clinic.view',
    'staff.view': 'staff.read',
    'staff.read': 'staff.view',
    'staff.update': 'staff.assign_role',
    'audit_logs.view': 'audit.read',
    'audit.read': 'audit_logs.view',
    'reports.view': 'reports.read',
    'reports.read': 'reports.view',
}

ROLE_PERMISSIONS = {
    'DISTRICT_OFFICER': {
        'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
        'audit_logs.view', 'dashboard.view', 'referrals.view', 'inventory.view', 'queue.view',
        'lab_orders.view', 'patients.view', 'po.view', 'vendor.view', 'ncd.view', 'surveillance.view',
        'triage.view', 'consultation.view', 'prescription.view', 'telemedicine.view', 'outreach.view', 'wellness.view',
        'ars.view', 'quality.view', 'integrations.view',
        'patients.read', 'consultation.read', 'diagnosis.read', 'prescription.read',
        'lab_order.read', 'lab_result.read', 'inventory.read', 'purchase_order.read',
        'purchase_order.approve', 'staff.read', 'staff.create', 'staff.invite',
        'staff.assign_role', 'staff.end_role', 'staff.assign_facility', 'staff.transfer',
        'staff.suspend', 'staff.deactivate', 'facility.read', 'facility.create',
        'facility.update', 'facility.deactivate', 'audit.read'
    },
    'HOSPITAL_ADMIN': {
        'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
        'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.create', 'appointments.update',
        'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
        'system_config.view', 'system_config.update', 'dashboard.view', 'queue.view', 'queue.call_next', 'queue.transition', 'queue.create', 'referrals.view',
        'po.view', 'po.create', 'po.update', 'po.approve', 'vendor.view', 'vendor.create', 'vendor.update',
        'lab_orders.view', 'lab_results.view',
        'ncd.view', 'surveillance.view', 'ars.view', 'quality.view', 'integrations.view',
        'patients.read', 'patients.update_demographics', 'queue.issue_token', 'queue.void',
        'purchase_order.read', 'purchase_order.approve', 'staff.read', 'staff.invite',
        'staff.assign_role', 'staff.end_role', 'staff.assign_facility', 'staff.transfer',
        'staff.suspend', 'staff.deactivate', 'facility.read', 'facility.update', 'audit.read'
    },
    'DOCTOR': {
        'patients.view', 'patients.update', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
        'triage.view', 'triage.create', 'triage.update',
        'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
        'lab_orders.view', 'lab_orders.create', 'lab_results.view',
        'referrals.view', 'referrals.create', 'clinic.view', 'queue.view', 'queue.call_next', 'queue.transition', 'dashboard.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update',
        'patients.read', 'vitals.create', 'vitals.update', 'lab_order.create', 'lab_order.read',
        'lab_result.read', 'lab_result.verify', 'medicine_batch.read'
    },
    'NURSE': {
        'patients.view', 'patients.update', 'appointments.view', 'appointments.update',
        'vitals.view', 'vitals.create', 'vitals.update', 'triage.view', 'triage.create', 'triage.update',
        'queue.view', 'queue.call_next', 'queue.transition', 'queue.update', 'clinic.view', 'dashboard.view',
        'lab_orders.view', 'lab_results.view',
        'ncd.view', 'ncd.create', 'ncd.update', 'surveillance.view', 'surveillance.create', 'surveillance.update',
        'patients.read', 'consultation.read', 'diagnosis.read', 'prescription.read',
        'lab_order.read', 'lab_result.read', 'specimen.collect', 'medicine_batch.read'
    },
    'COMPOUNDER': {
        'patients.view', 'patients.read', 'patients.create', 'patients.update', 'patients.update_demographics',
        'queue.view', 'queue.create', 'queue.issue_token', 'queue.void',
        'clinic.view', 'dashboard.view'
    },
    'LAB_TECHNICIAN': {
        'patients.view', 'patients.read', 'queue.view', 'queue.call_next', 'queue.transition',
        'lab_orders.view', 'lab_orders.create', 'lab_orders.update',
        'lab_results.view', 'lab_results.create', 'lab_results.update',
        'clinic.view', 'dashboard.view',
        'lab_order.read', 'specimen.collect', 'lab_result.create', 'lab_result.read', 'lab_result.amend'
    },
    'PHARMACIST': {
        'prescription.view', 'prescription.read', 'prescription.verify', 'prescription.hold', 'prescription.reject',
        'pharmacy.view', 'pharmacy.dispense', 'dispensation.create', 'dispensation.read',
        'inventory.view', 'inventory.read', 'inventory.create', 'inventory.update', 'inventory.adjust',
        'medicine_batch.read', 'reports.view', 'reports.export', 'clinic.view', 'dashboard.view',
        'po.view', 'po.create', 'po.update', 'po.receive', 'vendor.view', 'vendor.create', 'vendor.update',
        'purchase_order.create', 'purchase_order.read', 'purchase_order.update', 'goods_receipt.create'
    }
}

def get_user_role_permissions(user):
    if not user or not user.is_authenticated:
        return set()
    role_code = getattr(user, 'role', None)
    if not role_code:
        return set()
    if getattr(user, 'is_superuser', False):
        try:
            from apps.accounts.constants import SEEDED_PERMISSIONS
            return {p['code'] for p in SEEDED_PERMISSIONS}
        except Exception:
            pass
    try:
        from apps.accounts.models import RolePermission
        db_perms = set(RolePermission.objects.filter(
            role__code=role_code,
            is_active=True,
            permission__is_active=True
        ).values_list('permission__code', flat=True))
        if db_perms:
            return db_perms
    except Exception:
        pass
    return ROLE_PERMISSIONS.get(role_code, set())

def has_role_permission(user, permission_name):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    user_perms = get_user_role_permissions(user)
    if permission_name in user_perms:
        return True
    alias = PERMISSION_ALIASES.get(permission_name)
    if alias and alias in user_perms:
        return True
    return False

def get_accessible_facility_ids_for_user(user):
    if not user or not user.is_authenticated:
        return []
    if user.role == 'DISTRICT_OFFICER':
        if user.assigned_district_id:
            from apps.facilities.models import Facility
            return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list('id', flat=True))
        return []
    if user.assigned_facility_id:
        return [user.assigned_facility_id]
    return []

def can_access_facility(user, facility_id):
    if not user or not user.is_authenticated or not facility_id:
        return False
    if user.role == 'DISTRICT_OFFICER':
        if user.assigned_district_id:
            from apps.facilities.models import Facility
            return Facility.objects.filter(id=facility_id, district_id=user.assigned_district_id).exists()
        return False
    return user.assigned_facility_id == int(facility_id)

class IsAuthenticatedAndRoleAuthorized(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class HasPermission(permissions.BasePermission):
    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        action = getattr(view, 'action', None)
        perm_map = getattr(view, 'required_permissions', {})
        if perm_map and action and action in perm_map:
            req_perm = perm_map[action]
        elif perm_map and request.method in perm_map:
            req_perm = perm_map[request.method]
        else:
            req_perm = getattr(view, 'required_permission', None)
        if not req_perm:
            return True
        return has_role_permission(request.user, req_perm)

class HasFacilityScope(permissions.BasePermission):
    message = 'You do not have authorization to access resources outside your assigned facility or district scope.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'DISTRICT_OFFICER':
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                mutation_restricted_views = {
                    'ConsultationViewSet', 'PrescriptionViewSet', 'TriageVitalsViewSet', 'DispenseMedicineView',
                    'PurchaseOrderViewSet', 'VendorViewSet', 'PatientViewSet', 'NCDRecordViewSet',
                    'DiseaseCaseViewSet', 'ReferralViewSet', 'FollowUpViewSet', 'LabOrderViewSet',
                    'LabResultViewSet', 'VisitViewSet', 'MedicineMasterViewSet', 'MedicineBatchViewSet',
                    'FacilityOxygenSupplyViewSet', 'FacilityConsumableInventoryViewSet', 'FacilityMaintenanceTicketViewSet',
                    'FacilityBedCapacityViewSet', 'FacilityBedAllocationViewSet'
                }
                if view.__class__.__name__ in mutation_restricted_views:
                    self.message = 'District Officers have read-only oversight access and cannot modify clinical, patient, or facility records.'
                    return False
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'DISTRICT_OFFICER':
            if request.method not in permissions.SAFE_METHODS:
                return False
            if not request.user.assigned_district_id:
                return False
            from apps.facilities.models import Facility
            dist_fac_ids = set(Facility.objects.filter(district_id=request.user.assigned_district_id).values_list('id', flat=True))
            if getattr(obj, 'district_id', None):
                return obj.district_id == request.user.assigned_district_id
            if hasattr(obj, 'source_facility_id') or hasattr(obj, 'destination_facility_id'):
                src = getattr(obj, 'source_facility_id', None)
                dst = getattr(obj, 'destination_facility_id', None)
                return (src in dist_fac_ids or dst in dist_fac_ids)
            obj_fac_id = getattr(obj, 'facility_id', None) or getattr(obj, 'assigned_facility_id', None) or getattr(obj, 'registered_at_facility_id', None)
            if obj_fac_id:
                return obj_fac_id in dist_fac_ids
            return True
        user_fac_id = request.user.assigned_facility_id
        if not user_fac_id:
            return False
        obj_fac_id = getattr(obj, 'facility_id', None) or getattr(obj, 'assigned_facility_id', None) or getattr(obj, 'registered_at_facility_id', None)
        if hasattr(obj, 'source_facility_id') and hasattr(obj, 'destination_facility_id'):
            if obj.source_facility_id == user_fac_id or obj.destination_facility_id == user_fac_id:
                return True
        if obj_fac_id:
            return obj_fac_id == user_fac_id
        return True

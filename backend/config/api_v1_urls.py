"""
API Version 1 Routing Configuration.
Authoritative REST API foundation backed exclusively by domain service layer.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts.api_v1 import (
    StaffProfileViewSet, RoleAssignmentViewSet, FacilityAssignmentViewSet
)
from apps.facilities.api_v1 import (
    StateViewSet, DistrictViewSet, TalukViewSet, WardViewSet,
    FacilityViewSet, DepartmentViewSet
)
from apps.patients.api_v1 import PatientViewSet
from apps.visits.api_v1 import VisitViewSet
from apps.consultations.api_v1 import ConsultationViewSet, TriageVitalsViewSet
from apps.laboratory.api_v1 import (
    DiagnosticTestMasterViewSet, DiagnosticOrderViewSet,
    TestRequestViewSet, SpecimenViewSet, DiagnosticResultViewSet
)
from apps.pharmacy.api_v1 import (
    MedicineMasterViewSet, MedicineBatchViewSet, PrescriptionViewSet,
    DispensationViewSet, InventoryLedgerViewSet,
    VendorViewSet, PurchaseOrderViewSet, GoodsReceiptNoteViewSet
)
from apps.referrals.api_v1 import ReferralOrderViewSet, FollowUpTaskViewSet
from apps.ncd.api_v1 import (
    NCDConditionViewSet, NCDAssessmentViewSet,
    DiseaseSurveillanceCaseViewSet, PublicHealthNotificationViewSet,
    OperationalAlertViewSet, AuditLogEntryViewSet
)

router_v1 = DefaultRouter()

# IAM
router_v1.register(r'accounts/staff-profiles', StaffProfileViewSet, basename='v1-staffprofile')
router_v1.register(r'accounts/role-assignments', RoleAssignmentViewSet, basename='v1-roleassignment')
router_v1.register(r'accounts/facility-assignments', FacilityAssignmentViewSet, basename='v1-facilityassignment')

# Organization
router_v1.register(r'organization/states', StateViewSet, basename='v1-state')
router_v1.register(r'organization/districts', DistrictViewSet, basename='v1-district')
router_v1.register(r'organization/taluks', TalukViewSet, basename='v1-taluk')
router_v1.register(r'organization/wards', WardViewSet, basename='v1-ward')
router_v1.register(r'organization/facilities', FacilityViewSet, basename='v1-facility')
router_v1.register(r'organization/departments', DepartmentViewSet, basename='v1-department')

# Patients & Encounters
router_v1.register(r'patients', PatientViewSet, basename='v1-patient')
router_v1.register(r'visits', VisitViewSet, basename='v1-visit')
router_v1.register(r'clinical/consultations', ConsultationViewSet, basename='v1-consultation')
router_v1.register(r'clinical/triage', TriageVitalsViewSet, basename='v1-triage')

# Diagnostics
router_v1.register(r'diagnostics/tests', DiagnosticTestMasterViewSet, basename='v1-diagtest')
router_v1.register(r'diagnostics/orders', DiagnosticOrderViewSet, basename='v1-diagorder')
router_v1.register(r'diagnostics/requests', TestRequestViewSet, basename='v1-diagrequest')
router_v1.register(r'diagnostics/specimens', SpecimenViewSet, basename='v1-diagspecimen')
router_v1.register(r'diagnostics/results', DiagnosticResultViewSet, basename='v1-diagresult')

# Pharmacy & Inventory
router_v1.register(r'pharmacy/medicines', MedicineMasterViewSet, basename='v1-medicine')
router_v1.register(r'pharmacy/batches', MedicineBatchViewSet, basename='v1-medicinebatch')
router_v1.register(r'pharmacy/prescriptions', PrescriptionViewSet, basename='v1-prescription')
router_v1.register(r'pharmacy/dispensations', DispensationViewSet, basename='v1-dispensation')
router_v1.register(r'pharmacy/ledger', InventoryLedgerViewSet, basename='v1-inventoryledger')

# Procurement
router_v1.register(r'procurement/vendors', VendorViewSet, basename='v1-vendor')
router_v1.register(r'procurement/purchase-orders', PurchaseOrderViewSet, basename='v1-purchaseorder')
router_v1.register(r'procurement/grn', GoodsReceiptNoteViewSet, basename='v1-grn')

# Referrals & Follow-Up
router_v1.register(r'referrals/orders', ReferralOrderViewSet, basename='v1-referralorder')
router_v1.register(r'referrals/followups', FollowUpTaskViewSet, basename='v1-followuptask')

# NCD & Surveillance
router_v1.register(r'ncd/conditions', NCDConditionViewSet, basename='v1-ncdcondition')
router_v1.register(r'ncd/assessments', NCDAssessmentViewSet, basename='v1-ncdassessment')
router_v1.register(r'surveillance/cases', DiseaseSurveillanceCaseViewSet, basename='v1-surveillancecase')
router_v1.register(r'surveillance/notifications', PublicHealthNotificationViewSet, basename='v1-surveillancenotif')

# Alerts & Audit
router_v1.register(r'alerts', OperationalAlertViewSet, basename='v1-alert')
router_v1.register(r'audit', AuditLogEntryViewSet, basename='v1-audit')

urlpatterns = [
    path('', include(router_v1.urls)),
]

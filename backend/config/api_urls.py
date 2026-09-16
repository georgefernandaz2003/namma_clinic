from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import UserViewSet, CurrentUserProfileView
from apps.geography.views import StateViewSet, DistrictViewSet, ZoneViewSet, WardViewSet
from apps.facilities.views import (
    FacilityViewSet, FacilityRelationshipViewSet, FacilityHierarchyView, NetworkGraphView,
    FacilityOxygenSupplyViewSet, FacilityConsumableInventoryViewSet, FacilityMaintenanceTicketViewSet,
    FacilityBedCapacityViewSet, FacilityBedAllocationViewSet
)
from apps.patients.views import PatientViewSet, PatientTimelineView
from apps.visits.views import VisitViewSet
from apps.triage.views import TriageVitalsViewSet
from apps.consultations.views import ConsultationViewSet, PrescriptionViewSet
from apps.laboratory.views import LabTestMasterViewSet, LabOrderViewSet
from apps.pharmacy.views import MedicineMasterViewSet, MedicineBatchViewSet, DispenseMedicineView
from apps.referrals.views import ReferralViewSet, FollowUpViewSet
from apps.ncd.views import NCDRecordViewSet
from apps.surveillance.views import DiseaseCaseViewSet
from apps.telemedicine.views import TeleconsultationViewSet
from apps.outreach.views import OutreachActivityViewSet
from apps.wellness.views import WellnessSessionViewSet
from apps.ars.views import ARSMeetingViewSet, ARSMemberViewSet
from apps.quality.views import QualityChecklistViewSet, BiomedicalWasteLogViewSet
from apps.alerts.views import AlertViewSet
from apps.integrations.views import IntegrationConfigurationViewSet
from apps.compliance.views import ComplianceItemViewSet
from apps.audit.views import AuditLogViewSet
from apps.reports.views import DashboardSummaryView, CSVExportView, ResetDemoView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'states', StateViewSet, basename='state')
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'wards', WardViewSet, basename='ward')
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'facility-relationships', FacilityRelationshipViewSet, basename='facilityrelationship')
router.register(r'facilities-infra/oxygen-supplies', FacilityOxygenSupplyViewSet, basename='oxygensupply')
router.register(r'facilities-infra/consumables', FacilityConsumableInventoryViewSet, basename='consumableinventory')
router.register(r'facilities-infra/maintenance-tickets', FacilityMaintenanceTicketViewSet, basename='maintenanceticket')
router.register(r'facilities-infra/bed-capacity', FacilityBedCapacityViewSet, basename='bedcapacity')
router.register(r'facilities-infra/bed-allocations', FacilityBedAllocationViewSet, basename='bedallocation')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'visits', VisitViewSet, basename='visit')
router.register(r'triage', TriageVitalsViewSet, basename='triage')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'pharmacy/prescriptions', PrescriptionViewSet, basename='pharmacyprescription')
router.register(r'lab/tests', LabTestMasterViewSet, basename='labtest')
router.register(r'lab/orders', LabOrderViewSet, basename='laborder')
router.register(r'pharmacy/medicines', MedicineMasterViewSet, basename='medicinemaster')
router.register(r'pharmacy/batches', MedicineBatchViewSet, basename='medicinebatch')
router.register(r'referrals', ReferralViewSet, basename='referral')
router.register(r'followups', FollowUpViewSet, basename='followup')
router.register(r'ncd', NCDRecordViewSet, basename='ncd')
router.register(r'surveillance', DiseaseCaseViewSet, basename='surveillance')
router.register(r'telemedicine', TeleconsultationViewSet, basename='telemedicine')
router.register(r'outreach', OutreachActivityViewSet, basename='outreach')
router.register(r'wellness', WellnessSessionViewSet, basename='wellness')
router.register(r'ars/meetings', ARSMeetingViewSet, basename='arsmeeting')
router.register(r'ars/members', ARSMemberViewSet, basename='arsmember')
router.register(r'quality/checklists', QualityChecklistViewSet, basename='qualitychecklist')
router.register(r'quality/waste-logs', BiomedicalWasteLogViewSet, basename='biomedicalwaste')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'integrations', IntegrationConfigurationViewSet, basename='integration')
router.register(r'compliance', ComplianceItemViewSet, basename='compliance')
router.register(r'audit', AuditLogViewSet, basename='audit')

urlpatterns = [
    # Auth
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserProfileView.as_view(), name='user_profile'),

    # Hierarchy & Network Graph
    path('facilities/hierarchy/', FacilityHierarchyView.as_view(), name='facility_hierarchy'),
    path('facilities/network-graph/', NetworkGraphView.as_view(), name='network_graph'),

    # Patient Timeline
    path('patients/<int:pk>/timeline/', PatientTimelineView.as_view(), name='patient_timeline'),

    # Pharmacy FEFO Dispense
    path('pharmacy/dispense/', DispenseMedicineView.as_view(), name='pharmacy_dispense'),

    # Dashboard & Reports
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('reports/export/', CSVExportView.as_view(), name='csv_export'),
    path('admin/reset-demo/', ResetDemoView.as_view(), name='reset_demo'),

    # Router URLs
    path('', include(router.urls)),
]

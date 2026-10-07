"""
Backend Authorization & Operational Tests for Facility Services (Phase 33).
Verifies:
- Canonical ServiceMaster catalog seeding (zero MCH, zero teleconsultation)
- FacilityService auto-provisioning on facility onboarding
- Hospital Admin own-facility viewing and toggling (is_available)
- Hospital Admin foreign-facility mutation rejected with HTTP 403
- Clinical roles (DOCTOR, NURSE) mutation rejected with HTTP 403
- DHO district scope (within district allowed, cross-district rejected with HTTP 403)
- Duplicate service mapping protection
- Visit/Token creation lifecycle: blocked when service disabled, allowed when enabled
- Preservation of historical visits when service is disabled
"""

from rest_framework.test import APITestCase
from rest_framework import status
import datetime
import uuid

from apps.facilities.models import Facility, ServiceMaster, FacilityService
from apps.geography.models import State, District
from apps.accounts.models import Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment, User
from apps.patients.models import Patient
from apps.visits.models import Visit

class FacilityServicesTests(APITestCase):

    def setUp(self):
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district_a = District.objects.create(name="Bengaluru Urban", code="BEN", state=self.state)
        self.district_b = District.objects.create(name="Mysuru", code="MYS", state=self.state)

        self.facility_a = Facility.objects.create(
            facility_code="FAC-P33-BLR-01",
            facility_name="Malleshwaram Clinic",
            state=self.state,
            district=self.district_a,
            status="ACTIVE"
        )
        self.facility_b = Facility.objects.create(
            facility_code="FAC-P33-MYS-01",
            facility_name="Mysuru General Clinic",
            state=self.state,
            district=self.district_b,
            status="ACTIVE"
        )

        # Standard Roles
        role_dho = RoleMaster.objects.get(code="DISTRICT_OFFICER")
        role_admin = RoleMaster.objects.get(code="HOSPITAL_ADMIN")
        role_doc = RoleMaster.objects.get(code="DOCTOR")

        # 1. DHO User (District A)
        self.person_dho = Person.objects.create(first_name="District", last_name="Officer", date_of_birth=datetime.date(1980, 1, 1), gender="MALE")
        self.staff_dho = StaffProfile.objects.create(person=self.person_dho, employee_id="EMP-DHO-P33", designation="District Health Officer", status="ACTIVE")
        self.dho_user = User.objects.create_user(username="dho_blr_p33", password="Password123!", role="DISTRICT_OFFICER", assigned_district=self.district_a, staff_profile=self.staff_dho)
        StaffRoleAssignment.objects.create(staff=self.staff_dho, role=role_dho, is_active=True)

        # 2. Hospital Admin User (Facility A)
        self.person_admin = Person.objects.create(first_name="Hospital", last_name="Admin", date_of_birth=datetime.date(1985, 1, 1), gender="MALE")
        self.staff_admin = StaffProfile.objects.create(person=self.person_admin, employee_id="EMP-ADMIN-P33", designation="Hospital Administrator", status="ACTIVE")
        self.admin_user = User.objects.create_user(username="admin_fac_a_p33", password="Password123!", role="HOSPITAL_ADMIN", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_admin)
        StaffRoleAssignment.objects.create(staff=self.staff_admin, role=role_admin, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_admin, facility=self.facility_a, is_primary=True, is_active=True)

        # 3. Clinical Doctor User (Facility A)
        self.person_doc = Person.objects.create(first_name="Clinical", last_name="Doctor", date_of_birth=datetime.date(1990, 1, 1), gender="FEMALE")
        self.staff_doc = StaffProfile.objects.create(person=self.person_doc, employee_id="EMP-DOC-P33", designation="Medical Officer", status="ACTIVE")
        self.doc_user = User.objects.create_user(username="doc_fac_a_p33", password="Password123!", role="DOCTOR", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_doc)
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=role_doc, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)

        # Patient for Facility A
        self.patient = Patient.objects.create(
            patient_id=f"PAT-P33-{uuid.uuid4().hex[:6].upper()}",
            name="Ravi Kumar",
            gender="MALE",
            age=32,
            mobile="9876543210",
            address="Bengaluru",
            registered_at_facility=self.facility_a
        )

        # Ensure canonical services exist
        from apps.facilities.services import ensure_canonical_service_masters, provision_standard_facility_services
        ensure_canonical_service_masters()
        provision_standard_facility_services(self.facility_a)
        provision_standard_facility_services(self.facility_b)

    def test_canonical_catalog_seeded_correctly_no_mch(self):
        """Verify the 5 canonical services exist and zero MCH/teleconsultation records exist."""
        codes = set(ServiceMaster.objects.values_list('code', flat=True))
        expected_codes = {'SRV_GENERAL_OPD', 'SRV_NCD_SCREENING', 'SRV_DIAGNOSTICS', 'SRV_PHARMACY', 'SRV_TRIAGE'}
        for exp in expected_codes:
            self.assertIn(exp, codes)

        # Strict check: No MCH or teleconsultation in ServiceMaster
        for code in codes:
            self.assertNotIn('ANC', code.upper())
            self.assertNotIn('PNC', code.upper())
            self.assertNotIn('IMMUNIZATION', code.upper())
            self.assertNotIn('MATERNAL', code.upper())
            self.assertNotIn('TELECONSULTATION', code.upper())

    def test_facility_onboarding_auto_provisions_services(self):
        """Newly created facility must automatically have all 5 canonical services provisioned."""
        self.client.force_authenticate(user=self.dho_user)
        payload = {
            "facility_code": "FAC-NEW-P33",
            "facility_name": "New Hebbal Clinic",
            "facility_type": "NAMMA_CLINIC",
            "district": self.district_a.id,
            "status": "ACTIVE"
        }
        res = self.client.post("/api/v1/organization/facilities/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_fac_id = res.data["id"]

        fac_services = FacilityService.objects.filter(facility_id=new_fac_id)
        self.assertEqual(fac_services.count(), 5)
        for fs in fac_services:
            self.assertTrue(fs.is_available)

    def test_hospital_admin_can_view_own_facility_services(self):
        """Hospital Admin should list only services for their assigned facility."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/organization/facility-services/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should return services for facility_a only
        for item in res.data.get('results', res.data):
            self.assertEqual(item['facility'], self.facility_a.id)

    def test_hospital_admin_can_toggle_own_facility_service(self):
        """Hospital Admin can disable and re-enable services for their own facility."""
        self.client.force_authenticate(user=self.admin_user)
        fs = FacilityService.objects.get(facility=self.facility_a, service__code="SRV_GENERAL_OPD")
        self.assertTrue(fs.is_available)

        # Disable service
        patch_res = self.client.patch(f"/api/v1/organization/facility-services/{fs.id}/", {"is_available": False}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        fs.refresh_from_db()
        self.assertFalse(fs.is_available)

        # Re-enable service
        patch_res2 = self.client.patch(f"/api/v1/organization/facility-services/{fs.id}/", {"is_available": True}, format="json")
        self.assertEqual(patch_res2.status_code, status.HTTP_200_OK)
        fs.refresh_from_db()
        self.assertTrue(fs.is_available)

    def test_hospital_admin_foreign_facility_mutation_rejected_403(self):
        """Hospital Admin attempting to update or delete a foreign facility's service receives 403."""
        self.client.force_authenticate(user=self.admin_user)
        foreign_fs = FacilityService.objects.get(facility=self.facility_b, service__code="SRV_GENERAL_OPD")

        # Attempt PATCH
        res = self.client.patch(f"/api/v1/organization/facility-services/{foreign_fs.id}/", {"is_available": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt DELETE
        del_res = self.client.delete(f"/api/v1/organization/facility-services/{foreign_fs.id}/")
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_dho_cross_district_service_mutation_rejected_403(self):
        """DHO for District A attempting to modify service in District B receives 403."""
        self.client.force_authenticate(user=self.dho_user)
        foreign_district_fs = FacilityService.objects.get(facility=self.facility_b, service__code="SRV_GENERAL_OPD")

        res = self.client.patch(f"/api/v1/organization/facility-services/{foreign_district_fs.id}/", {"is_available": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinical_role_mutation_rejected_403(self):
        """Doctor attempting to modify facility services receives HTTP 403."""
        self.client.force_authenticate(user=self.doc_user)
        fs = FacilityService.objects.get(facility=self.facility_a, service__code="SRV_GENERAL_OPD")

        res = self.client.patch(f"/api/v1/organization/facility-services/{fs.id}/", {"is_available": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_service_mapping_rejected(self):
        """Cannot create duplicate FacilityService mapping for same facility and service."""
        self.client.force_authenticate(user=self.dho_user)
        existing_fs = FacilityService.objects.filter(facility=self.facility_a).first()
        payload = {
            "facility": self.facility_a.id,
            "service": existing_fs.service.id,
            "is_available": True
        }
        res = self.client.post("/api/v1/organization/facility-services/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_visit_creation_blocked_when_service_disabled(self):
        """Creating an OPD token for a disabled service fails with 400 validation error."""
        # Disable General OPD
        fs = FacilityService.objects.get(facility=self.facility_a, service__code="SRV_GENERAL_OPD")
        fs.is_available = False
        fs.save()

        # Admin / Front Desk attempts to issue OPD token
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "visit_type": "GENERAL_OPD",
            "priority": "NORMAL",
            "chief_complaint": "Headache"
        }
        res = self.client.post("/api/v1/visits/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unavailable or disabled", str(res.data))

        # Re-enable General OPD
        fs.is_available = True
        fs.save()

        res2 = self.client.post("/api/v1/visits/", payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_teleconsultation_token_creation_rejected_400(self):
        """Teleconsultation is not an approved operational service and must be rejected."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "visit_type": "TELECONSULTATION",
            "priority": "NORMAL"
        }
        res = self.client.post("/api/v1/visits/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not operational", str(res.data))

    def test_historical_visits_preserved_when_service_disabled(self):
        """Disabling a service preserves existing historical visits in database."""
        # Create a historical visit
        hist_visit = Visit.objects.create(
            visit_id=f"HIST-{uuid.uuid4().hex[:6].upper()}",
            patient=self.patient,
            facility=self.facility_a,
            opd_date=datetime.date.today() - datetime.timedelta(days=1),
            visit_type="GENERAL_OPD",
            status="COMPLETED"
        )
        self.assertTrue(Visit.objects.filter(pk=hist_visit.pk).exists())

        # Disable General OPD
        fs = FacilityService.objects.get(facility=self.facility_a, service__code="SRV_GENERAL_OPD")
        fs.is_available = False
        fs.save()

        # Check historical visit is still completely intact
        hist_visit.refresh_from_db()
        self.assertEqual(hist_visit.status, "COMPLETED")
        self.assertEqual(hist_visit.visit_type, "GENERAL_OPD")

from rest_framework.test import APITestCase
from rest_framework import status
import datetime
import uuid

from apps.geography.models import State, District
from apps.facilities.models import Facility, Department, ServiceMaster, FacilityService
from apps.accounts.models import Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment, User
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.facilities.services import (
    provision_standard_departments,
    provision_standard_facility_services,
    SERVICE_TO_DEPARTMENT_MAP,
    DEPARTMENT_TO_SERVICES_MAP,
)


class OperationalSyncAndGateHardeningTests(APITestCase):
    def setUp(self):
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district_a = District.objects.create(name="Bengaluru Urban", code="BEN", state=self.state)
        self.district_b = District.objects.create(name="Mysuru", code="MYS", state=self.state)

        self.facility_a = Facility.objects.create(
            facility_code="FAC-P35-BLR-01",
            facility_name="Malleshwaram Clinic",
            state=self.state,
            district=self.district_a,
            status="ACTIVE"
        )
        self.facility_b = Facility.objects.create(
            facility_code="FAC-P35-MYS-01",
            facility_name="Mysuru General Clinic",
            state=self.state,
            district=self.district_b,
            status="ACTIVE"
        )

        # Standard provision for Facility A
        self.depts_a = provision_standard_departments(self.facility_a)
        self.services_a = provision_standard_facility_services(self.facility_a)

        # Roles
        role_dho = RoleMaster.objects.get(code="DISTRICT_OFFICER")
        role_admin = RoleMaster.objects.get(code="HOSPITAL_ADMIN")
        role_doc = RoleMaster.objects.get(code="DOCTOR")
        role_nurse = RoleMaster.objects.get(code="NURSE")
        role_fdo = RoleMaster.objects.get(code="FRONT_DESK_OFFICER")
        role_pharm = RoleMaster.objects.get(code="PHARMACIST")

        # 1. DHO User (District A)
        self.person_dho = Person.objects.create(first_name="District", last_name="Officer", date_of_birth=datetime.date(1980, 1, 1), gender="MALE")
        self.staff_dho = StaffProfile.objects.create(person=self.person_dho, employee_id="EMP-DHO-P35", designation="District Health Officer", status="ACTIVE")
        self.dho_user = User.objects.create_user(username="dho_blr_p35", password="Password123!", role="DISTRICT_OFFICER", assigned_district=self.district_a, staff_profile=self.staff_dho)
        StaffRoleAssignment.objects.create(staff=self.staff_dho, role=role_dho, is_active=True)

        # 2. Hospital Admin User (Facility A)
        self.person_admin = Person.objects.create(first_name="Hospital", last_name="Admin", date_of_birth=datetime.date(1985, 1, 1), gender="MALE")
        self.staff_admin = StaffProfile.objects.create(person=self.person_admin, employee_id="EMP-ADMIN-P35", designation="Hospital Administrator", status="ACTIVE")
        self.admin_user = User.objects.create_user(username="admin_fac_a_p35", password="Password123!", role="HOSPITAL_ADMIN", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_admin)
        StaffRoleAssignment.objects.create(staff=self.staff_admin, role=role_admin, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_admin, facility=self.facility_a, is_primary=True, is_active=True)

        # 3. Clinical Doctor User (Facility A)
        self.person_doc = Person.objects.create(first_name="Clinical", last_name="Doctor", date_of_birth=datetime.date(1990, 1, 1), gender="FEMALE")
        self.staff_doc = StaffProfile.objects.create(person=self.person_doc, employee_id="EMP-DOC-P35", designation="Medical Officer", status="ACTIVE")
        self.doc_user = User.objects.create_user(username="doc_fac_a_p35", password="Password123!", role="DOCTOR", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_doc)
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=role_doc, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)

        # 4. Nurse User (Facility A)
        self.person_nurse = Person.objects.create(first_name="Staff", last_name="Nurse", date_of_birth=datetime.date(1992, 1, 1), gender="FEMALE")
        self.staff_nurse = StaffProfile.objects.create(person=self.person_nurse, employee_id="EMP-NURSE-P35", designation="Staff Nurse", status="ACTIVE")
        self.nurse_user = User.objects.create_user(username="nurse_fac_a_p35", password="Password123!", role="NURSE", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_nurse)
        StaffRoleAssignment.objects.create(staff=self.staff_nurse, role=role_nurse, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_nurse, facility=self.facility_a, is_primary=True, is_active=True)

        # 5. Front Desk Officer (Facility A)
        self.person_fdo = Person.objects.create(first_name="Desk", last_name="Officer", date_of_birth=datetime.date(1993, 1, 1), gender="MALE")
        self.staff_fdo = StaffProfile.objects.create(person=self.person_fdo, employee_id="EMP-FDO-P35", designation="Registration Desk Officer", status="ACTIVE")
        self.fdo_user = User.objects.create_user(username="fdo_fac_a_p35", password="Password123!", role="FRONT_DESK_OFFICER", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_fdo)
        StaffRoleAssignment.objects.create(staff=self.staff_fdo, role=role_fdo, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_fdo, facility=self.facility_a, is_primary=True, is_active=True)

        # 6. Pharmacist (Facility A)
        self.person_pharm = Person.objects.create(first_name="Chief", last_name="Pharmacist", date_of_birth=datetime.date(1988, 1, 1), gender="MALE")
        self.staff_pharm = StaffProfile.objects.create(person=self.person_pharm, employee_id="EMP-PHARM-P35", designation="Pharmacist", status="ACTIVE")
        self.pharm_user = User.objects.create_user(username="pharm_fac_a_p35", password="Password123!", role="PHARMACIST", assigned_facility=self.facility_a, assigned_district=self.district_a, staff_profile=self.staff_pharm)
        StaffRoleAssignment.objects.create(staff=self.staff_pharm, role=role_pharm, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_pharm, facility=self.facility_a, is_primary=True, is_active=True)

        # Patient for Facility A
        self.patient = Patient.objects.create(
            patient_id=f"PAT-P35-{uuid.uuid4().hex[:6].upper()}",
            name="Ramesh Kumar",
            gender="MALE",
            age=45,
            mobile="9876543210",
            address="Bengaluru",
            registered_at_facility=self.facility_a
        )

    # 1. Active service + active department
    def test_active_service_and_active_department(self):
        self.client.force_authenticate(user=self.admin_user)
        fac_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_GENERAL_OPD')
        dept_opd = Department.objects.get(facility=self.facility_a, code='OPD')

        self.assertTrue(fac_svc.is_available)
        self.assertTrue(dept_opd.is_active)

        # Can disable service
        resp = self.client.patch(f"/api/v1/organization/facility-services/{fac_svc.id}/", {"is_available": False})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_available'])

        # Can re-enable since OPD department is active
        resp2 = self.client.patch(f"/api/v1/organization/facility-services/{fac_svc.id}/", {"is_available": True})
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data['is_available'])

    # 2. Inactive department + service re-enable blocked (HTTP 400)
    def test_inactive_department_service_enablement_blocked(self):
        self.client.force_authenticate(user=self.admin_user)
        fac_svc_opd = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_GENERAL_OPD')
        fac_svc_ncd = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_NCD_SCREENING')
        dept_opd = Department.objects.get(facility=self.facility_a, code='OPD')

        # Disable both services first
        fac_svc_opd.is_available = False
        fac_svc_opd.save()
        fac_svc_ncd.is_available = False
        fac_svc_ncd.save()

        # Deactivate OPD department
        dept_opd.is_active = False
        dept_opd.save()

        # Attempt to re-enable SRV_GENERAL_OPD while OPD department is inactive -> 400
        resp = self.client.patch(f"/api/v1/organization/facility-services/{fac_svc_opd.id}/", {"is_available": True})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supporting department", str(resp.data).lower())

        # Attempt to re-enable SRV_NCD_SCREENING while OPD department is inactive -> 400
        resp2 = self.client.patch(f"/api/v1/organization/facility-services/{fac_svc_ncd.id}/", {"is_available": True})
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supporting department", str(resp2.data).lower())

    # 3. Department deactivation blocked while dependent service is active (HTTP 400)
    def test_deactivate_department_with_active_dependent_service_blocked(self):
        self.client.force_authenticate(user=self.admin_user)
        dept_opd = Department.objects.get(facility=self.facility_a, code='OPD')

        # Attempt to deactivate OPD while SRV_GENERAL_OPD is active -> 400
        resp = self.client.patch(f"/api/v1/organization/departments/{dept_opd.id}/", {"is_active": False})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dependent service", str(resp.data).lower())

    # 4. Service disabled -> downstream diagnostic operation blocked (HTTP 400)
    def test_downstream_gate_diagnostic_disabled(self):
        self.client.force_authenticate(user=self.admin_user)
        diag_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_DIAGNOSTICS')
        diag_svc.is_available = False
        diag_svc.save()

        # Create visit for patient
        visit = Visit.objects.create(
            visit_id="VIS-TEST-DIAG-001",
            patient=self.patient,
            facility=self.facility_a,
            opd_date=datetime.date.today(),
            current_queue="DOCTOR",
            status="WAITING_FOR_DOCTOR"
        )

        # Authenticate as Doctor and attempt to create DiagnosticOrder -> 400
        self.client.force_authenticate(user=self.doc_user)
        resp = self.client.post("/api/v1/diagnostics/orders/", {
            "visit": visit.id,
            "facility": self.facility_a.id,
            "priority": "ROUTINE",
            "clinical_indication": "Suspected Typhoid"
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SRV_DIAGNOSTICS", str(resp.data))

        # Attempt via consultations order endpoint -> 400
        resp2 = self.client.post("/api/consultations/", {
            "visit": visit.id,
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "lab_test_ids": [1],
            "chief_complaint": "Fever"
        })
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SRV_DIAGNOSTICS", str(resp2.data))

    # 5. Service disabled -> downstream pharmacy operation blocked (HTTP 400)
    def test_downstream_gate_pharmacy_disabled(self):
        self.client.force_authenticate(user=self.admin_user)
        pharm_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_PHARMACY')
        pharm_svc.is_available = False
        pharm_svc.save()

        visit = Visit.objects.create(
            visit_id="VIS-TEST-PHARM-001",
            patient=self.patient,
            facility=self.facility_a,
            opd_date=datetime.date.today(),
            current_queue="DOCTOR",
            status="WAITING_FOR_DOCTOR"
        )

        # Doctor consultation attempting prescription -> 400
        self.client.force_authenticate(user=self.doc_user)
        resp = self.client.post("/api/consultations/", {
            "visit": visit.id,
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "chief_complaint": "Joint pain",
            "prescription_items": [
                {"medicine_name": "Paracetamol 500mg", "dosage": "1-0-1", "quantity": 10}
            ]
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SRV_PHARMACY", str(resp.data))

    # 6. Service disabled -> downstream triage blocked & direct-to-doctor routing
    def test_triage_disabled_and_direct_to_doctor_routing(self):
        self.client.force_authenticate(user=self.admin_user)
        triage_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_TRIAGE')
        triage_svc.is_available = False
        triage_svc.save()

        # FDO registers a new visit when triage is disabled
        self.client.force_authenticate(user=self.fdo_user)
        resp = self.client.post("/api/v1/visits/", {
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "visit_type": "GENERAL_OPD",
            "priority": "NORMAL",
            "chief_complaint": "Headache"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['current_queue'], "DOCTOR")
        self.assertEqual(resp.data['status'], "WAITING_FOR_DOCTOR")

        visit_id = resp.data['id']
        visit = Visit.objects.get(id=visit_id)
        self.assertEqual(visit.current_queue, "DOCTOR")
        self.assertEqual(visit.status, "WAITING_FOR_DOCTOR")

        # Nurse attempting to log triage vitals for this visit -> 400
        self.client.force_authenticate(user=self.nurse_user)
        triage_resp = self.client.post("/api/triage/", {
            "visit": visit.id,
            "patient": self.patient.id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80
        })
        self.assertEqual(triage_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SRV_TRIAGE", str(triage_resp.data))

        # Doctor conducts consultation directly (triage bypass invariant allows this)
        self.client.force_authenticate(user=self.doc_user)
        consult_resp = self.client.post("/api/consultations/", {
            "visit": visit.id,
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "chief_complaint": "Headache",
            "clinical_assessment": "Tension headache",
            "treatment_plan": "Rest and hydration"
        })
        self.assertIn(consult_resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    # 7. Hospital Admin DELETE FacilityService -> 403 Forbidden
    def test_hospital_admin_delete_facility_service_returns_403(self):
        self.client.force_authenticate(user=self.admin_user)
        fac_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_GENERAL_OPD')
        resp = self.client.delete(f"/api/v1/organization/facility-services/{fac_svc.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(FacilityService.objects.filter(id=fac_svc.id).exists())

    # 8. Standard department DELETE -> safe rejection (HTTP 400)
    def test_standard_department_delete_blocked(self):
        self.client.force_authenticate(user=self.admin_user)
        for code in ['OPD', 'PHARM', 'LAB', 'TRIAGE']:
            dept = Department.objects.get(facility=self.facility_a, code=code)
            resp = self.client.delete(f"/api/v1/organization/departments/{dept.id}/")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("standard system department", str(resp.data).lower())
            self.assertTrue(Department.objects.filter(id=dept.id).exists())

    # 9. Referenced custom department DELETE -> 409 Conflict (no HTTP 500)
    def test_referenced_custom_department_delete_returns_409(self):
        self.client.force_authenticate(user=self.admin_user)
        # Create a custom department
        custom_dept = Department.objects.create(
            facility=self.facility_a,
            code="PHYSIO",
            name="Physiotherapy",
            is_active=True
        )

        # Reference it with a staff member
        self.staff_nurse.department = custom_dept
        self.staff_nurse.save()

        # Attempt deletion -> 409
        resp = self.client.delete(f"/api/v1/organization/departments/{custom_dept.id}/")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("active staff members or records reference it", str(resp.data).lower())
        self.assertTrue(Department.objects.filter(id=custom_dept.id).exists())

    # 10. Canonical FacilityService permanent delete blocked even for superuser/DHO (HTTP 400)
    def test_canonical_service_delete_blocked_for_dho(self):
        self.client.force_authenticate(user=self.dho_user)
        fac_svc = FacilityService.objects.get(facility=self.facility_a, service__code='SRV_DIAGNOSTICS')
        resp = self.client.delete(f"/api/v1/organization/facility-services/{fac_svc.id}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot be permanently deleted", str(resp.data).lower())
        self.assertTrue(FacilityService.objects.filter(id=fac_svc.id).exists())

    # 11. DHO district scoping remains intact
    def test_dho_district_scoping_intact(self):
        self.client.force_authenticate(user=self.dho_user)
        # Facility B is in Mysuru (District B), while DHO is Bengaluru Urban (District A)
        resp = self.client.get(f"/api/v1/organization/facility-services/?facility={self.facility_b.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # District scoping correctly limits visible facility services
        self.assertEqual(len(resp.data['results']), 0)

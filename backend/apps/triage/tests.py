"""
Phase 27B Triage Tests:
Atomicity of Nurse triage creation, queue state advancement to DOCTOR queue,
atomic rollback verification, and RBAC boundary enforcement (Compounder denied).
"""
import datetime
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.accounts.services import seed_roles_and_permissions
from apps.geography.models import State, District
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.visits.services import issue_opd_token
from apps.triage.models import TriageVitals


class TriageHandoffAndAtomicityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)

        self.facility_1 = Facility.objects.create(
            facility_name="Namma Clinic PHC #1",
            facility_code="PHC-TRIAGE-01",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            status="ACTIVE"
        )
        self.facility_2 = Facility.objects.create(
            facility_name="Namma Clinic PHC #2",
            facility_code="PHC-TRIAGE-02",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state,
            status="ACTIVE"
        )

        role_nurse = RoleMaster.objects.get(code="NURSE")
        role_compounder = RoleMaster.objects.get(code="FRONT_DESK_OFFICER")

        # Nurse User at Facility 1
        p_nurse = Person.objects.create(first_name="Radha", last_name="Nurse", gender="FEMALE", date_of_birth="1992-03-03")
        staff_nurse = StaffProfile.objects.create(
            person=p_nurse, employee_id="EMP-NURSE-01", designation="Staff Nurse", status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=staff_nurse, role=role_nurse, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=staff_nurse, facility=self.facility_1, is_primary=True, is_active=True)
        self.user_nurse = User.objects.create_user(
            username="test_triage_nurse", password="password123",
            role="NURSE", assigned_facility=self.facility_1, staff_profile=staff_nurse
        )

        # Compounder User at Facility 1
        p_cmp = Person.objects.create(first_name="Kumar", last_name="FrontDesk", gender="MALE", date_of_birth="1990-01-01")
        staff_cmp = StaffProfile.objects.create(
            person=p_cmp, employee_id="EMP-CMP-01", designation="Front Desk Officer", status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=staff_cmp, role=role_compounder, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=staff_cmp, facility=self.facility_1, is_primary=True, is_active=True)
        self.user_compounder = User.objects.create_user(
            username="test_triage_cmp", password="password123",
            role="FRONT_DESK_OFFICER", assigned_facility=self.facility_1, staff_profile=staff_cmp
        )

        # Patient at Facility 1
        self.patient = Patient.objects.create(
            patient_id="PAT-TR-001",
            name="Test Patient Radha",
            age=32,
            gender="FEMALE",
            mobile="9800055003",
            address="12 Main Road",
            registered_at_facility=self.facility_1
        )

        # Visit for Patient at Facility 1
        today = datetime.date.today()
        self.visit = Visit.objects.create(
            visit_id=f"VIS-TR-{today.strftime('%Y%m%d')}-001",
            patient=self.patient,
            facility=self.facility_1,
            opd_date=today,
            visit_type="GENERAL_OPD",
            priority="NORMAL",
            chief_complaint="Fever and chills",
            current_queue="TRIAGE",
            status="WAITING_FOR_TRIAGE",
            arrival_time=timezone.now()
        )
        self.token = issue_opd_token(visit=self.visit, facility=self.facility_1)

    def test_01_nurse_triage_creation_advances_queue_and_sets_history(self):
        """Nurse triage creation atomically saves vitals, advances visit to WAITING_FOR_DOCTOR, and updates queue."""
        self.client.force_authenticate(user=self.user_nurse)
        payload = {
            "visit": self.visit.id,
            "patient": self.patient.id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "pulse_bpm": 74,
            "temperature_f": "98.6",
            "spo2_percent": 99,
            "blood_glucose_mgdl": 95,
            "nurse_notes": "Patient alert, stable vitals"
        }
        res = self.client.post('/api/v1/clinical/triage/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify TriageVitals record exists
        triage = TriageVitals.objects.filter(visit=self.visit).first()
        self.assertIsNotNone(triage)
        self.assertEqual(triage.blood_pressure_systolic, 120)
        self.assertEqual(triage.nurse, self.user_nurse)

        # Verify Visit state transitioned to WAITING_FOR_DOCTOR and queue to DOCTOR
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, 'WAITING_FOR_DOCTOR')
        self.assertEqual(self.visit.current_queue, 'DOCTOR')
        self.assertIsNotNone(self.visit.triage_end_time)

        # Verify Token status transitioned to TRIAGED
        self.token.refresh_from_db()
        self.assertEqual(self.token.status, 'TRIAGED')

        # Verify VisitStatusHistory logged
        history = VisitStatusHistory.objects.filter(visit=self.visit, to_status='WAITING_FOR_DOCTOR').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.performed_by, self.user_nurse)
        self.assertEqual(history.queue, 'DOCTOR')

    def test_02_triage_atomicity_and_rollback(self):
        """If visit queue advancement fails, TriageVitals must roll back; no partial triage state allowed."""
        self.client.force_authenticate(user=self.user_nurse)
        payload = {
            "visit": self.visit.id,
            "patient": self.patient.id,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "pulse_bpm": 80,
            "temperature_f": "100.2",
            "spo2_percent": 97
        }

        # Simulate a database failure during queue advancement inside the atomic transaction
        with patch.object(Visit, 'save', side_effect=RuntimeError("Simulated database failure during visit queue update")):
            with self.assertRaises(RuntimeError):
                self.client.post('/api/v1/clinical/triage/', payload, format='json')

        # Verify complete rollback: TriageVitals must NOT be created
        triage_count = TriageVitals.objects.filter(visit=self.visit).count()
        self.assertEqual(triage_count, 0, "TriageVitals must roll back if queue transition fails")

        # Verify Visit remains unchanged in WAITING_FOR_TRIAGE / TRIAGE queue
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, 'WAITING_FOR_TRIAGE')
        self.assertEqual(self.visit.current_queue, 'TRIAGE')

    def test_03_compounder_cannot_create_triage(self):
        """Compounder role must receive HTTP 403 Forbidden when attempting to log triage vitals."""
        self.client.force_authenticate(user=self.user_compounder)
        payload = {
            "visit": self.visit.id,
            "patient": self.patient.id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80
        }
        res = self.client.post('/api/v1/clinical/triage/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Confirm no triage was created
        self.assertEqual(TriageVitals.objects.filter(visit=self.visit).count(), 0)

    def test_04_cross_facility_triage_is_rejected(self):
        """Nurse at Facility 1 cannot submit triage for a visit registered at Facility 2."""
        visit_fac2 = Visit.objects.create(
            visit_id="VIS-FAC2-001",
            patient=self.patient,
            facility=self.facility_2,
            opd_date=datetime.date.today(),
            visit_type="GENERAL_OPD",
            priority="NORMAL",
            current_queue="TRIAGE",
            status="WAITING_FOR_TRIAGE",
            arrival_time=timezone.now()
        )

        self.client.force_authenticate(user=self.user_nurse)
        payload = {
            "visit": visit_fac2.id,
            "patient": self.patient.id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80
        }
        res = self.client.post('/api/v1/clinical/triage/', payload, format='json')
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

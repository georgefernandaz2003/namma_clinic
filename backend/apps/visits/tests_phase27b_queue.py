"""
Phase 27B: OPD Queue & Token State Machine Consolidation Tests.
Includes multi-threaded PostgreSQL concurrency tests for token allocation and call-next,
along with queue state machine transitions, role authorization, and duplicate voiding.
"""
import datetime
import threading
import uuid
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment
)
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter, VisitStatusHistory
from apps.triage.models import TriageVitals
from apps.visits.services import (
    issue_opd_token,
    call_next_queue_item,
    transition_visit_status,
    void_opd_token,
    get_queue_history_summary
)


class Phase27BBaseHelper:
    """Helper methods to set up test infrastructure."""
    @classmethod
    def setup_base_entities(cls):
        state, _ = State.objects.get_or_create(name="Karnataka", code="KA")
        dist, _ = District.objects.get_or_create(name="Bengaluru Urban", code="KA-BLR", state=state)
        taluk, _ = Taluk.objects.get_or_create(name="Bengaluru East", code="TAL-BLR-E", district=dist)
        zone, _ = Zone.objects.get_or_create(name="Mahadevapura Zone", district=dist)
        ward, _ = Ward.objects.get_or_create(name="Varthur", ward_number=149, zone=zone)

        facility_a, _ = Facility.objects.get_or_create(
            facility_code="PHC-VARTHUR-27B",
            defaults=dict(
                facility_name="Varthur Clinic 27B",
                facility_type="PRIMARY_HEALTH_CENTRE",
                district=dist, state=state, zone=zone, ward=ward
            )
        )
        facility_b, _ = Facility.objects.get_or_create(
            facility_code="PHC-WHITEFIELD-27B",
            defaults=dict(
                facility_name="Whitefield Clinic 27B",
                facility_type="PRIMARY_HEALTH_CENTRE",
                district=dist, state=state, zone=zone, ward=ward
            )
        )

        dept_a, _ = Department.objects.get_or_create(facility=facility_a, code="OPD", defaults=dict(name="Outpatient"))
        dept_b, _ = Department.objects.get_or_create(facility=facility_b, code="OPD", defaults=dict(name="Outpatient"))

        role_compounder, _ = RoleMaster.objects.get_or_create(code="FRONT_DESK_OFFICER", defaults=dict(name="Front Desk Officer"))
        role_nurse, _ = RoleMaster.objects.get_or_create(code="NURSE", defaults=dict(name="Staff Nurse"))
        role_admin, _ = RoleMaster.objects.get_or_create(code="HOSPITAL_ADMIN", defaults=dict(name="Hospital Admin"))

        return {
            "facility_a": facility_a,
            "facility_b": facility_b,
            "role_compounder": role_compounder,
            "role_nurse": role_nurse,
            "role_admin": role_admin,
            "dept_a": dept_a,
        }

    @classmethod
    def create_staff_user(cls, username, role_code, facility, dept):
        person, _ = Person.objects.get_or_create(
            phone_number=f"99{abs(hash(username)) % 100000000:08d}",
            defaults=dict(
                first_name=username.capitalize(),
                last_name="Staff",
                gender="MALE",
                date_of_birth=datetime.date(1990, 1, 1)
            )
        )
        staff, _ = StaffProfile.objects.get_or_create(
            employee_id=f"EMP-{username.upper()}",
            defaults=dict(
                person=person,
                designation=role_code,
                department=dept,
                status="ACTIVE"
            )
        )
        user, _ = User.objects.get_or_create(
            username=username,
            defaults=dict(
                email=f"{username}@example.com",
                role=role_code,
                is_active=True,
                staff_profile=staff,
                assigned_facility=facility
            )
        )
        if user.staff_profile != staff or user.assigned_facility != facility:
            user.staff_profile = staff
            user.assigned_facility = facility
            user.save()

        role_obj = RoleMaster.objects.get(code=role_code)
        StaffRoleAssignment.objects.get_or_create(
            staff=staff, role=role_obj, facility=facility,
            defaults=dict(effective_from=datetime.date.today(), is_active=True)
        )
        return user, staff

    @classmethod
    def create_patient(cls, identifier, facility):
        p, _ = Patient.objects.get_or_create(
            patient_id=f"PID-27B-{identifier}",
            defaults=dict(
                name=f"Patient {identifier}",
                mobile=f"98765{identifier:05d}",
                age=30,
                gender="MALE",
                registered_at_facility=facility
            )
        )
        return p

    @classmethod
    def create_visit(cls, patient, facility, **kwargs):
        defaults = dict(
            visit_id=f"VIS-{facility.id}-{uuid.uuid4().hex[:8].upper()}",
            patient=patient,
            facility=facility,
            visit_type="GENERAL_OPD",
            priority="NORMAL",
            status="WAITING_FOR_TRIAGE",
            current_queue="TRIAGE",
            arrival_time=timezone.now()
        )
        defaults.update(kwargs)
        return Visit.objects.create(**defaults)


class OPDTokenConcurrencyTests(TransactionTestCase):
    """
    Validates PostgreSQL multi-threaded token generation concurrency.
    Ensures that concurrent issuance requests yield strictly sequential,
    non-colliding token numbers and FacilityDailyCounter stays consistent.
    """
    def setUp(self):
        self.base = Phase27BBaseHelper.setup_base_entities()
        self.facility_a = self.base["facility_a"]
        self.facility_b = self.base["facility_b"]
        self.dept_a = self.base["dept_a"]

    def test_concurrent_opd_token_issuance_same_facility(self):
        """10 threads concurrently issue tokens for the same facility and date."""
        today = datetime.date.today()
        num_threads = 10
        patients = [Phase27BBaseHelper.create_patient(i, self.facility_a) for i in range(1, num_threads + 1)]
        visits = [
            Phase27BBaseHelper.create_visit(patient=p, facility=self.facility_a, visit_type="GENERAL_OPD", priority="NORMAL")
            for p in patients
        ]

        token_numbers = []
        errors = []
        lock = threading.Lock()

        def worker(idx):
            try:
                tok = issue_opd_token(visit=visits[idx], facility=self.facility_a, token_date=today)
                with lock:
                    token_numbers.append(tok.token_number)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors occurred during concurrent issuance: {errors}")
        self.assertEqual(len(token_numbers), num_threads)
        self.assertEqual(len(set(token_numbers)), num_threads, "Duplicate token numbers detected!")
        self.assertEqual(sorted(token_numbers), list(range(1, num_threads + 1)))

        counter = FacilityDailyCounter.objects.get(facility=self.facility_a, counter_type="OPD", counter_date=today)
        self.assertEqual(counter.last_token_number, num_threads)

    def test_token_namespaces_isolated_across_facilities(self):
        """Tokens issued at Facility A and Facility B on the same day start independently from 1."""
        today = datetime.date.today()
        p1 = Phase27BBaseHelper.create_patient(101, self.facility_a)
        p2 = Phase27BBaseHelper.create_patient(102, self.facility_b)

        v1 = Phase27BBaseHelper.create_visit(patient=p1, facility=self.facility_a)
        v2 = Phase27BBaseHelper.create_visit(patient=p2, facility=self.facility_b)

        tok1 = issue_opd_token(visit=v1, facility=self.facility_a, token_date=today)
        tok2 = issue_opd_token(visit=v2, facility=self.facility_b, token_date=today)

        self.assertEqual(tok1.token_number, 1)
        self.assertEqual(tok2.token_number, 1)

        counter_a = FacilityDailyCounter.objects.get(facility=self.facility_a, counter_type="OPD", counter_date=today)
        counter_b = FacilityDailyCounter.objects.get(facility=self.facility_b, counter_type="OPD", counter_date=today)
        self.assertEqual(counter_a.last_token_number, 1)
        self.assertEqual(counter_b.last_token_number, 1)


class CallNextConcurrencyTests(TransactionTestCase):
    """
    Validates PostgreSQL row locking (SELECT FOR UPDATE SKIP LOCKED) on call-next.
    When multiple nurses simultaneously call next, each waiting patient must be claimed
    by exactly one nurse with no duplicate claims or deadlocks.
    """
    def setUp(self):
        self.base = Phase27BBaseHelper.setup_base_entities()
        self.facility_a = self.base["facility_a"]
        self.dept_a = self.base["dept_a"]

    def test_concurrent_call_next_no_double_claim(self):
        """5 nurses call-next against 3 waiting visits. Exactly 3 claimed, 2 get empty queue."""
        num_patients = 3
        num_nurses = 5

        patients = [Phase27BBaseHelper.create_patient(200 + i, self.facility_a) for i in range(num_patients)]
        visits = []
        for i, p in enumerate(patients):
            v = Phase27BBaseHelper.create_visit(
                patient=p, facility=self.facility_a, status="WAITING_FOR_TRIAGE", current_queue="TRIAGE"
            )
            issue_opd_token(visit=v, facility=self.facility_a)
            visits.append(v)

        nurses = [
            Phase27BBaseHelper.create_staff_user(f"nurse_{i}", "NURSE", self.facility_a, self.dept_a)[1]
            for i in range(num_nurses)
        ]

        claimed_visit_ids = []
        empty_queue_count = 0
        errors = []
        lock = threading.Lock()

        def worker(nurse_idx):
            nonlocal empty_queue_count
            try:
                claimed = call_next_queue_item(
                    facility=self.facility_a,
                    queue_name="TRIAGE",
                    staff=nurses[nurse_idx]
                )
                with lock:
                    if claimed:
                        claimed_visit_ids.append(claimed.id)
            except ValueError as ve:
                if "No waiting patients" in str(ve):
                    with lock:
                        empty_queue_count += 1
                else:
                    with lock:
                        errors.append(ve)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_nurses)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Unexpected errors in call-next: {errors}")
        self.assertEqual(len(claimed_visit_ids), num_patients)
        self.assertEqual(len(set(claimed_visit_ids)), num_patients, "Double claim detected!")
        self.assertEqual(empty_queue_count, num_nurses - num_patients)


class QueueStateMachineTests(TestCase):
    """
    Validates queue state machine transitions, role enforcement, and token voiding rules.
    """
    def setUp(self):
        self.base = Phase27BBaseHelper.setup_base_entities()
        self.facility_a = self.base["facility_a"]
        self.facility_b = self.base["facility_b"]
        self.dept_a = self.base["dept_a"]

        self.user_compounder, self.staff_compounder = Phase27BBaseHelper.create_staff_user(
            "compounder_user", "FRONT_DESK_OFFICER", self.facility_a, self.dept_a
        )
        self.user_nurse, self.staff_nurse = Phase27BBaseHelper.create_staff_user(
            "nurse_user", "NURSE", self.facility_a, self.dept_a
        )
        self.user_admin, self.staff_admin = Phase27BBaseHelper.create_staff_user(
            "admin_user", "HOSPITAL_ADMIN", self.facility_a, self.dept_a
        )

        self.patient = Phase27BBaseHelper.create_patient(301, self.facility_a)
        self.visit = Phase27BBaseHelper.create_visit(
            patient=self.patient,
            facility=self.facility_a,
            status="WAITING_FOR_TRIAGE",
            current_queue="TRIAGE",
            arrival_time=timezone.now()
        )
        self.token = issue_opd_token(visit=self.visit, facility=self.facility_a)

    def test_compounder_cannot_call_next(self):
        """Compounder must NOT have queue.call_next authority."""
        with self.assertRaises(PermissionDenied):
            call_next_queue_item(
                facility=self.facility_a,
                queue_name="TRIAGE",
                staff=self.staff_compounder
            )

    def test_compounder_cannot_transition_into_clinical_stages(self):
        """Compounder must NOT be able to advance a visit into clinical stages."""
        with self.assertRaises(PermissionDenied):
            transition_visit_status(
                visit=self.visit,
                to_status="IN_TRIAGE",
                staff=self.staff_compounder
            )

    def test_nurse_transition_requires_vitals_before_doctor_queue(self):
        """Transitioning to WAITING_FOR_DOCTOR requires vitals to be recorded."""
        self.visit.status = "IN_TRIAGE"
        self.visit.save()

        # Without vitals, transition must fail
        with self.assertRaises(ValidationError) as cm:
            transition_visit_status(
                visit=self.visit,
                to_status="WAITING_FOR_DOCTOR",
                staff=self.staff_nurse
            )
        self.assertIn("vitals", str(cm.exception).lower())

        # Record vitals
        TriageVitals.objects.create(
            visit=self.visit,
            patient=self.visit.patient,
            nurse=self.user_nurse,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            pulse_bpm=72,
            temperature_f=98.6
        )

        # Now transition must succeed
        updated = transition_visit_status(
            visit=self.visit,
            to_status="WAITING_FOR_DOCTOR",
            staff=self.staff_nurse
        )
        self.assertEqual(updated.status, "WAITING_FOR_DOCTOR")
        self.assertEqual(updated.current_queue, "DOCTOR")

    def test_void_opd_token_valid(self):
        """Compounder can void an untriaged token within 30 minutes."""
        voided = void_opd_token(
            visit=self.visit,
            staff=self.staff_compounder,
            facility=self.facility_a,
            reason="Accidental duplicate entry"
        )
        self.assertEqual(voided.status, "CANCELLED")
        # Visit record is preserved, not physically deleted
        self.assertTrue(Visit.objects.filter(id=self.visit.id).exists())
        # Audit history logged
        history = VisitStatusHistory.objects.filter(visit=self.visit, to_status="CANCELLED")
        self.assertTrue(history.exists())

    def test_void_opd_token_expired_window(self):
        """Voiding fails if visit arrived more than 30 minutes ago."""
        self.visit.arrival_time = timezone.now() - datetime.timedelta(minutes=35)
        self.visit.save()

        with self.assertRaises(ValidationError) as cm:
            void_opd_token(
                visit=self.visit,
                staff=self.staff_compounder,
                facility=self.facility_a,
                reason="Expired void test"
            )
        self.assertIn("30-minute", str(cm.exception))

    def test_void_opd_token_already_progressed(self):
        """Voiding fails if visit has already entered triage or doctor queue."""
        self.visit.status = "IN_TRIAGE"
        self.visit.save()

        with self.assertRaises(ValidationError) as cm:
            void_opd_token(
                visit=self.visit,
                staff=self.staff_compounder,
                facility=self.facility_a,
                reason="Progressed void test"
            )
        self.assertIn("untriaged", str(cm.exception).lower())

    def test_void_opd_token_wrong_facility(self):
        """Staff from another facility cannot void a visit."""
        with self.assertRaises(PermissionDenied):
            void_opd_token(
                visit=self.visit,
                staff=self.staff_compounder,
                facility=self.facility_b,
                reason="Wrong facility void"
            )

    def test_void_opd_token_unauthorized_role(self):
        """Nurse (who does not have queue.void) cannot void a token."""
        with self.assertRaises(PermissionDenied):
            void_opd_token(
                visit=self.visit,
                staff=self.staff_nurse,
                facility=self.facility_a,
                reason="Unauthorized void"
            )

    def test_void_opd_token_repeated_void(self):
        """Cannot void an already cancelled visit."""
        void_opd_token(
            visit=self.visit,
            staff=self.staff_compounder,
            facility=self.facility_a,
            reason="First void"
        )
        with self.assertRaises(ValidationError) as cm:
            void_opd_token(
                visit=self.visit,
                staff=self.staff_compounder,
                facility=self.facility_a,
                reason="Second void"
            )
        self.assertIn("already", str(cm.exception).lower())

    def test_queue_history_summary_counts(self):
        """Summary derives authoritative PostgreSQL counts for facility and date."""
        today = datetime.date.today()
        summary = get_queue_history_summary(self.facility_a, today)
        self.assertEqual(summary["total_patients"], 1)
        self.assertEqual(summary["waiting_triage"], 1)
        self.assertEqual(summary["completed_patients"], 0)
        self.assertEqual(summary["cancelled_patients"], 0)

        # Void the visit and re-check
        void_opd_token(
            visit=self.visit,
            staff=self.staff_compounder,
            facility=self.facility_a,
            reason="Summary count void"
        )
        summary2 = get_queue_history_summary(self.facility_a, today)
        self.assertEqual(summary2["cancelled_patients"], 1)
        self.assertEqual(summary2["waiting_triage"], 0)


class QueueAPIv1EndpointTests(TestCase):
    """
    Tests REST API interactions on /api/v1/visits/ endpoints.
    """
    def setUp(self):
        self.base = Phase27BBaseHelper.setup_base_entities()
        self.facility_a = self.base["facility_a"]
        self.facility_b = self.base["facility_b"]
        self.dept_a = self.base["dept_a"]

        self.user_compounder, self.staff_compounder = Phase27BBaseHelper.create_staff_user(
            "api_compounder", "FRONT_DESK_OFFICER", self.facility_a, self.dept_a
        )
        self.user_nurse, self.staff_nurse = Phase27BBaseHelper.create_staff_user(
            "api_nurse", "NURSE", self.facility_a, self.dept_a
        )
        self.user_admin, self.staff_admin = Phase27BBaseHelper.create_staff_user(
            "api_admin", "HOSPITAL_ADMIN", self.facility_a, self.dept_a
        )

        self.patient = Phase27BBaseHelper.create_patient(401, self.facility_a)
        self.client = APIClient()

    def test_v1_issue_token_compounder_allowed(self):
        """Compounder can issue token via POST /api/v1/visits/."""
        self.client.force_authenticate(user=self.user_compounder)
        res = self.client.post("/api/v1/visits/", {
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "visit_type": "GENERAL_OPD",
            "priority": "NORMAL"
        }, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertIn("token_details", res.data)
        self.assertEqual(res.data["token_details"]["token_number"], 1)

    def test_v1_call_next_compounder_forbidden_nurse_allowed(self):
        """Compounder is rejected with 403 on call-next; Nurse succeeds."""
        v = Phase27BBaseHelper.create_visit(
            patient=self.patient, facility=self.facility_a, status="WAITING_FOR_TRIAGE", current_queue="TRIAGE"
        )
        issue_opd_token(visit=v, facility=self.facility_a)

        # Compounder tries call-next
        self.client.force_authenticate(user=self.user_compounder)
        res_comp = self.client.post("/api/v1/visits/call-next/", {
            "facility": self.facility_a.id,
            "queue": "TRIAGE"
        }, format="json")
        self.assertEqual(res_comp.status_code, 403)

        # Nurse calls next
        self.client.force_authenticate(user=self.user_nurse)
        res_nurse = self.client.post("/api/v1/visits/call-next/", {
            "facility": self.facility_a.id,
            "queue": "TRIAGE"
        }, format="json")
        self.assertEqual(res_nurse.status_code, 200)
        self.assertEqual(res_nurse.data["id"], v.id)

    def test_v1_void_token_endpoint(self):
        """Compounder voids duplicate token via POST /api/v1/visits/void-token/."""
        v = Phase27BBaseHelper.create_visit(
            patient=self.patient, facility=self.facility_a, status="WAITING_FOR_TRIAGE", current_queue="TRIAGE"
        )
        issue_opd_token(visit=v, facility=self.facility_a)

        self.client.force_authenticate(user=self.user_compounder)
        res = self.client.post("/api/v1/visits/void-token/", {
            "visit_id": v.id,
            "reason": "Accidental double registration"
        }, format="json")
        self.assertEqual(res.status_code, 200)
        v.refresh_from_db()
        self.assertEqual(v.status, "CANCELLED")

    def test_v1_history_summary_endpoint(self):
        """GET /api/v1/visits/history-summary/ returns array of day summaries."""
        self.client.force_authenticate(user=self.user_compounder)
        res = self.client.get(f"/api/v1/visits/history-summary/?facility={self.facility_a.id}")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

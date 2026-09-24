"""
Referrals & Follow-Up Domain Service Tests (apps/referrals/tests_services.py).
Tests referral orders, state transitions, append-only event trail, follow-up completion,
and unauthorized completion failure.
"""
import datetime
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.visits.models import Visit
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.referrals.services import (
    create_referral_order, transition_referral_state, create_followup_task, complete_followup
)
from apps.common.exceptions import (
    UnauthorizedDomainAction, InvalidFollowUpCompletionError, InvalidStateTransition
)

class ReferralDomainServiceTests(DomainServiceBaseTestCase):
    def test_referral_state_transitions_and_append_event(self):
        order = create_referral_order(
            patient=self.patient, visit=self.completed_visit, source_facility=self.clinic_a,
            destination_facility=self.clinic_b, referring_doctor_staff=self.doc_staff, reason="Cardiology evaluation"
        )
        self.assertEqual(order.status, "INITIATED")
        self.assertEqual(order.events.count(), 1)

        transition_referral_state(order, "ACKNOWLEDGED", actor_staff=self.doc_staff, notes="Acknowledged by hospital desk")
        order.refresh_from_db()
        self.assertEqual(order.status, "ACKNOWLEDGED")
        self.assertEqual(order.events.count(), 2)

        with self.assertRaises(InvalidStateTransition):
            transition_referral_state(order, "COMPLETED", actor_staff=self.doc_staff)

    def test_followup_valid_completion(self):
        task = create_followup_task(patient=self.patient, facility=self.clinic_a, due_date=datetime.date.today())
        completed_task = complete_followup(task, completed_in_visit=self.completed_visit, completing_staff=self.doc_staff)
        self.assertEqual(completed_task.status, "COMPLETED")
        self.assertEqual(completed_task.completed_in_visit, self.completed_visit)

    def test_unauthorized_followup_completion_inactive_staff(self):
        """Failure 4: Inactive staff cannot complete follow-up tasks."""
        task = create_followup_task(patient=self.patient, facility=self.clinic_a, due_date=datetime.date.today())
        with self.assertRaises(UnauthorizedDomainAction):
            complete_followup(task, completed_in_visit=self.completed_visit, completing_staff=self.suspended_staff)

    def test_followup_completion_non_completed_visit_rejected(self):
        """Failure: FollowUp completion requires a COMPLETED visit."""
        task = create_followup_task(patient=self.patient, facility=self.clinic_a, due_date=datetime.date.today())
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(task, completed_in_visit=self.visit, completing_staff=self.doc_staff)

    def test_followup_completion_patient_and_facility_mismatch_rejected(self):
        """Failure: Patient or facility mismatch between follow-up and visit is rejected."""
        task = create_followup_task(patient=self.patient, facility=self.clinic_a, due_date=datetime.date.today())
        other_patient_visit = Visit.objects.create(
            visit_id="VIS-OTH-P", patient=self.patient2, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED"
        )
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(task, completed_in_visit=other_patient_visit, completing_staff=self.doc_staff)

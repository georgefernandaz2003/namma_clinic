"""
Audit Domain Service Tests (apps/audit/tests_services.py).
Tests audit event recording, actor preservation, and before/after payloads.
"""
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.audit.models import AuditLogEntry
from apps.audit.services import record_audit_event

class AuditDomainServiceTests(DomainServiceBaseTestCase):
    def test_audit_event_recording_and_actor_preservation(self):
        """Failure 10: Actor preservation and state capture."""
        entry = record_audit_event(
            actor_staff=self.admin_staff,
            actor_role_snapshot="Hospital Administrator",
            facility=self.clinic_a,
            action_type="UPDATE",
            table_name="staff_profiles",
            record_id=self.admin_staff.id,
            payload_before={"status": "PROBATION"},
            payload_after={"status": "ACTIVE"}
        )
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.actor_staff, self.admin_staff)
        self.assertEqual(entry.action_type, "UPDATE")
        self.assertEqual(entry.table_name, "staff_profiles")
        self.assertEqual(entry.payload_before, {"status": "PROBATION"})
        self.assertEqual(entry.payload_after, {"status": "ACTIVE"})

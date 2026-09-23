"""
Domain audit service for durable, immutable event recording.
"""
from apps.audit.models import AuditLogEntry


def record_audit_event(
    action_type,
    table_name,
    record_id,
    actor_staff=None,
    actor_user_id=None,
    actor_role_snapshot="SYSTEM",
    facility=None,
    payload_before=None,
    payload_after=None,
    correlation_id=None,
    ip_address=None,
    user_agent=""
):
    """
    Creates an immutable AuditLogEntry preserving durable actor identity,
    before/after JSON payload snapshots, and facility context.
    """
    return AuditLogEntry.objects.create(
        actor_staff=actor_staff,
        actor_user_id=actor_user_id,
        actor_role_snapshot=actor_role_snapshot,
        facility=facility,
        action_type=action_type,
        table_name=table_name,
        record_id=str(record_id),
        payload_before=payload_before,
        payload_after=payload_after,
        correlation_id=correlation_id,
        ip_address=ip_address,
        user_agent=user_agent
    )

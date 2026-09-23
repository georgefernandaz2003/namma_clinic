"""
Core domain exception hierarchy for Namma Clinic domain service layer.
Decouples domain business rules from HTTP/REST framework and raw database drivers.
"""

class DomainError(Exception):
    """Base exception for all domain and business rule violations."""
    def __init__(self, message=None, code=None, details=None):
        super().__init__(message or "A domain rule violation occurred.")
        self.message = message or "A domain rule violation occurred."
        self.code = code or "DOMAIN_ERROR"
        self.details = details or {}

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class DomainValidationError(DomainError):
    """Input or entity state failed domain validation."""
    def __init__(self, message, code="VALIDATION_ERROR", details=None):
        super().__init__(message, code=code, details=details)


class UnauthorizedDomainAction(DomainError):
    """Actor lacks necessary professional credentials, role, or facility scope."""
    def __init__(self, message="Actor is not authorized to perform this domain action.", details=None):
        super().__init__(message, code="UNAUTHORIZED_DOMAIN_ACTION", details=details)


class InvalidStateTransition(DomainError):
    """An entity attempted an illegal transition in its lifecycle state machine."""
    def __init__(self, entity_name, current_state, target_state, message=None):
        msg = message or f"Cannot transition {entity_name} from '{current_state}' to '{target_state}'."
        super().__init__(msg, code="INVALID_STATE_TRANSITION", details={
            "entity": entity_name,
            "current_state": current_state,
            "target_state": target_state
        })


class DuplicateTokenError(DomainError):
    """Attempted to allocate a duplicate token within a facility daily namespace."""
    def __init__(self, facility_id, namespace, token_number, date):
        msg = f"Token #{token_number} already issued for facility #{facility_id} in {namespace} namespace on {date}."
        super().__init__(msg, code="DUPLICATE_TOKEN", details={
            "facility_id": facility_id,
            "namespace": namespace,
            "token_number": token_number,
            "date": str(date)
        })


class InvalidAssignmentPeriodError(DomainError):
    """Effective dates are malformed (e.g. effective_to < effective_from)."""
    def __init__(self, effective_from, effective_to, message=None):
        msg = message or f"Effective end date ({effective_to}) cannot precede start date ({effective_from})."
        super().__init__(msg, code="INVALID_ASSIGNMENT_PERIOD", details={
            "effective_from": str(effective_from),
            "effective_to": str(effective_to) if effective_to else None
        })


class OverlappingAssignmentError(DomainError):
    """Staff member has a conflicting active assignment for the same role/facility."""
    def __init__(self, staff_id, assignment_type, target_id, message=None):
        msg = message or f"Staff #{staff_id} already has an active overlapping {assignment_type} assignment for {target_id}."
        super().__init__(msg, code="OVERLAPPING_ASSIGNMENT", details={
            "staff_id": staff_id,
            "assignment_type": assignment_type,
            "target_id": target_id
        })


class DiagnosticResultAlreadyExistsError(DomainError):
    """TestRequest already has a current DiagnosticResult."""
    def __init__(self, test_request_id):
        msg = f"A diagnostic result has already been recorded for TestRequest #{test_request_id}."
        super().__init__(msg, code="DIAGNOSTIC_RESULT_ALREADY_EXISTS", details={"test_request_id": test_request_id})


class VerifiedResultImmutableError(DomainError):
    """Attempted to modify or re-verify an already verified diagnostic result."""
    def __init__(self, diagnostic_result_id, message=None):
        msg = message or f"DiagnosticResult #{diagnostic_result_id} is VERIFIED and immutable. Use amendment service."
        super().__init__(msg, code="VERIFIED_RESULT_IMMUTABLE", details={"diagnostic_result_id": diagnostic_result_id})


class InvalidFollowUpCompletionError(DomainError):
    """Follow-up task completion failed cross-encounter validation."""
    def __init__(self, followup_id, reason, details=None):
        msg = f"Cannot complete FollowUpTask #{followup_id}: {reason}."
        super().__init__(msg, code="INVALID_FOLLOWUP_COMPLETION", details=details or {"followup_id": followup_id, "reason": reason})


class InsufficientStockError(DomainError):
    """Requested stock deduction exceeds available physical or ledger balance."""
    def __init__(self, batch_id, requested_qty, available_qty):
        msg = f"Insufficient stock for batch #{batch_id}. Requested: {requested_qty}, Available: {available_qty}."
        super().__init__(msg, code="INSUFFICIENT_STOCK", details={
            "batch_id": batch_id,
            "requested_qty": requested_qty,
            "available_qty": available_qty
        })


class InvalidBatchOperationError(DomainError):
    """Operation on medicine batch violates operational status or bucket state."""
    def __init__(self, batch_id, operation, reason):
        msg = f"Cannot perform {operation} on batch #{batch_id}: {reason}."
        super().__init__(msg, code="INVALID_BATCH_OPERATION", details={
            "batch_id": batch_id,
            "operation": operation,
            "reason": reason
        })


class InvalidProcurementStateError(DomainError):
    """Purchase order or goods receipt note state transition violation."""
    def __init__(self, po_id, reason):
        msg = f"Procurement violation for PO #{po_id}: {reason}."
        super().__init__(msg, code="INVALID_PROCUREMENT_STATE", details={"po_id": po_id, "reason": reason})

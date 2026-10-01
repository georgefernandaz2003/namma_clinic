"""
API Exception Handler for Namma Clinic Domain Service Layer.
Maps domain business rule violations and security constraints to consistent HTTP status codes.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from apps.common.exceptions import (
    DomainError,
    DomainValidationError,
    UnauthorizedDomainAction,
    InvalidStateTransition,
    DuplicateTokenError,
    InvalidAssignmentPeriodError,
    OverlappingAssignmentError,
    DiagnosticResultAlreadyExistsError,
    VerifiedResultImmutableError,
    InvalidFollowUpCompletionError,
    InsufficientStockError,
    InvalidBatchOperationError,
    InvalidProcurementStateError,
)

def domain_exception_handler(exc, context):
    """
    Translates explicit domain exceptions into standard JSON error envelopes.
    """
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, UnauthorizedDomainAction):
        return Response({
            "error": exc.message,
            "code": getattr(exc, "code", "UNAUTHORIZED_DOMAIN_ACTION"),
            "details": getattr(exc, "details", {})
        }, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (DomainValidationError, InvalidAssignmentPeriodError)):
        return Response({
            "error": exc.message,
            "code": getattr(exc, "code", "VALIDATION_ERROR"),
            "details": getattr(exc, "details", {})
        }, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (
        InvalidStateTransition,
        DuplicateTokenError,
        DiagnosticResultAlreadyExistsError,
        VerifiedResultImmutableError,
        OverlappingAssignmentError,
        InsufficientStockError,
        InvalidBatchOperationError,
        InvalidProcurementStateError,
        InvalidFollowUpCompletionError
    )):
        return Response({
            "error": exc.message,
            "code": getattr(exc, "code", "CONFLICT"),
            "details": getattr(exc, "details", {})
        }, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, DomainError):
        return Response({
            "error": exc.message,
            "code": getattr(exc, "code", "DOMAIN_ERROR"),
            "details": getattr(exc, "details", {})
        }, status=status.HTTP_400_BAD_REQUEST)

    return None

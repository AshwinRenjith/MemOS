"""
MemoryOS Domain — Exceptions

All application exceptions inherit from MemoryOSError.
No bare exceptions — docs/CODING_STANDARDS.md §2.3.
"""

from __future__ import annotations


class MemoryOSError(Exception):
    """Base exception for all MemoryOS domain errors."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


# ============================================================
# State Machine Errors
# ============================================================
class InvalidStateTransitionError(MemoryOSError):
    """Raised when a state machine transition is invalid.

    Pattern: (current_state, event) → error.
    See docs/CODING_STANDARDS.md §3.3.
    """

    def __init__(
        self,
        entity_type: str,
        current_state: str,
        attempted_event: str,
    ) -> None:
        super().__init__(
            f"Invalid {entity_type} transition: "
            f"state={current_state}, event={attempted_event}",
            code="INVALID_STATE_TRANSITION",
        )
        self.entity_type = entity_type
        self.current_state = current_state
        self.attempted_event = attempted_event


# ============================================================
# Data Integrity Errors
# ============================================================
class InvariantViolationError(MemoryOSError):
    """Raised when a system invariant is violated (INV-01..INV-10).

    This is a CRITICAL error. Log at CRITICAL level and alert immediately.
    """

    def __init__(self, invariant_id: str, detail: str) -> None:
        super().__init__(
            f"Invariant violation [{invariant_id}]: {detail}",
            code=f"INVARIANT_VIOLATION_{invariant_id}",
        )
        self.invariant_id = invariant_id


class CommitHashMismatchError(MemoryOSError):
    """Raised when recomputed commit hash doesn't match stored hash (INV-03)."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            f"Commit hash mismatch: expected={expected}, actual={actual}",
            code="COMMIT_HASH_MISMATCH",
        )
        self.expected = expected
        self.actual = actual


class SignatureVerificationError(MemoryOSError):
    """Raised when commit signature verification fails (INV-02)."""

    def __init__(self, commit_hash: str) -> None:
        super().__init__(
            f"Signature verification failed for commit: {commit_hash}",
            code="SIGNATURE_VERIFICATION_FAILED",
        )
        self.commit_hash = commit_hash


# ============================================================
# Concurrency Errors
# ============================================================
class OptimisticConcurrencyError(MemoryOSError):
    """Raised when ETag / If-Match check fails (INV-09).

    HTTP: 409 Conflict with current ETag in response.
    """

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"Concurrent modification detected for {entity_type}: {entity_id}",
            code="CONCURRENT_MODIFICATION",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


# ============================================================
# Authorization & Tenant Errors
# ============================================================
class TenantIsolationError(MemoryOSError):
    """Raised on suspected tenant isolation breach (INV-04).

    This is a CRITICAL security event. Triggers TENANT_ISOLATION_BREACH_SUSPECTED alert.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Tenant isolation breach suspected: {detail}",
            code="TENANT_ISOLATION_BREACH",
        )


class AuthorizationError(MemoryOSError):
    """Raised when user lacks required RBAC permission."""

    def __init__(self, role: str, operation: str) -> None:
        super().__init__(
            f"Role {role} is not authorized for operation: {operation}",
            code="AUTHORIZATION_DENIED",
        )
        self.role = role
        self.operation = operation


# ============================================================
# Legal Hold Errors (INV-05)
# ============================================================
class LegalHoldError(MemoryOSError):
    """Raised when an operation is attempted on a legally held entity."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"Operation blocked: {entity_type} {entity_id} is under legal hold (INV-05)",
            code="LEGAL_HOLD_ACTIVE",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


# ============================================================
# Privacy & Classification Errors
# ============================================================
class DataClassificationError(MemoryOSError):
    """Raised when content violates data classification rules."""

    def __init__(self, data_class: str, reason: str) -> None:
        super().__init__(
            f"Content blocked by classification {data_class}: {reason}",
            code="DATA_CLASSIFICATION_BLOCKED",
        )
        self.data_class = data_class


class ConsentRequiredError(MemoryOSError):
    """Raised when PII_ADJACENT data requires explicit consent."""

    def __init__(self, org_id: str) -> None:
        super().__init__(
            f"Explicit consent required for PII_ADJACENT data in org: {org_id}",
            code="CONSENT_REQUIRED",
        )
        self.org_id = org_id


# ============================================================
# Resource Errors
# ============================================================
class EntityNotFoundError(MemoryOSError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} not found: {entity_id}",
            code="NOT_FOUND",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(MemoryOSError):
    """Raised on idempotency key collision or unique constraint violation."""

    def __init__(self, entity_type: str, key: str) -> None:
        super().__init__(
            f"Duplicate {entity_type}: {key}",
            code="DUPLICATE",
        )
        self.entity_type = entity_type
        self.key = key

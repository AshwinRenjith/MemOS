"""
MemoryOS Unit Tests — Domain Exceptions

Validates exception hierarchy and error codes.
"""

from memoryos.domain.exceptions import (
    AuthorizationError,
    CommitHashMismatchError,
    ConsentRequiredError,
    DataClassificationError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvariantViolationError,
    InvalidStateTransitionError,
    LegalHoldError,
    MemoryOSError,
    OptimisticConcurrencyError,
    SignatureVerificationError,
    TenantIsolationError,
)


class TestExceptionHierarchy:
    """All domain exceptions must inherit from MemoryOSError."""

    def test_all_inherit_from_base(self) -> None:
        exceptions = [
            InvalidStateTransitionError("Branch", "ACTIVE", "merge"),
            InvariantViolationError("INV-01", "orphan node"),
            CommitHashMismatchError("expected", "actual"),
            SignatureVerificationError("a" * 64),
            OptimisticConcurrencyError("Branch", "branch-id"),
            TenantIsolationError("cross-org access"),
            AuthorizationError("VIEWER", "delete_repo"),
            LegalHoldError("Branch", "branch-id"),
            DataClassificationError("SENSITIVE", "blocked"),
            ConsentRequiredError("org-id"),
            EntityNotFoundError("Repository", "repo-id"),
            DuplicateEntityError("Commit", "hash"),
        ]
        for exc in exceptions:
            assert isinstance(exc, MemoryOSError)
            assert isinstance(exc, Exception)


class TestErrorCodes:
    def test_invariant_violation_code(self) -> None:
        exc = InvariantViolationError("INV-04", "cross-tenant access")
        assert exc.code == "INVARIANT_VIOLATION_INV-04"
        assert exc.invariant_id == "INV-04"

    def test_state_transition_code(self) -> None:
        exc = InvalidStateTransitionError("Branch", "MERGED", "delete")
        assert exc.code == "INVALID_STATE_TRANSITION"
        assert "MERGED" in str(exc)
        assert "delete" in str(exc)

    def test_tenant_isolation_code(self) -> None:
        exc = TenantIsolationError("org_a tried to access org_b data")
        assert exc.code == "TENANT_ISOLATION_BREACH"

    def test_authorization_code(self) -> None:
        exc = AuthorizationError("VIEWER", "rollback")
        assert exc.code == "AUTHORIZATION_DENIED"
        assert exc.role == "VIEWER"
        assert exc.operation == "rollback"

    def test_legal_hold_code(self) -> None:
        exc = LegalHoldError("Branch", "abc-123")
        assert exc.code == "LEGAL_HOLD_ACTIVE"
        assert "INV-05" in str(exc)

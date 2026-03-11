"""
MemoryOS Domain — Protocols

Dependency inversion interfaces (Python Protocol types).
Infrastructure adapters implement these protocols.
Domain and engine layers depend only on these abstractions — never on concrete infra.

See: docs/CODING_STANDARDS.md §3.2
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


# ============================================================
# Clock Protocol (CODING_STANDARDS §2.1)
# ============================================================
@runtime_checkable
class Clock(Protocol):
    """Injectable clock for deterministic time control in tests.

    Business logic MUST use this instead of time.time() or datetime.now().
    """

    def now_ms(self) -> int:
        """Return current time as Unix epoch milliseconds (BIGINT)."""
        ...


# ============================================================
# ID Generator Protocol (CODING_STANDARDS §2.1)
# ============================================================
@runtime_checkable
class IDGenerator(Protocol):
    """Injectable ID generator for deterministic testing.

    Business logic MUST use this instead of uuid.uuid4() directly.
    """

    def generate(self) -> UUID:
        """Return a new unique identifier."""
        ...


# ============================================================
# Key Provider Protocol (ADR-0002)
# ============================================================
@runtime_checkable
class KeyProvider(Protocol):
    """Abstract key custody interface.

    Implementations:
        - LocalKeyProvider    (Phase A — PyNaCl Ed25519)
        - HostedKMSProvider   (Phase B — AWS KMS)
        - CustomerKMSProvider (Phase D — Vault/HSM)
    """

    async def sign(self, data: bytes) -> bytes:
        """Sign data and return the signature bytes."""
        ...

    async def verify(
        self, data: bytes, signature: bytes, public_key: bytes
    ) -> bool:
        """Verify a signature against data and public key."""
        ...

    async def get_public_key(self, agent_id: UUID) -> bytes:
        """Retrieve the current active public key for an agent."""
        ...


# ============================================================
# Secret Provider Protocol (ADR-0004)
# ============================================================
@runtime_checkable
class SecretProvider(Protocol):
    """Abstract secret retrieval and encryption key management.

    Implementations:
        - EnvSecretProvider    (Development, CI)
        - AWSSecretProvider    (Cloud profile)
        - VaultSecretProvider  (Sovereign profile)
    """

    async def get_secret(self, name: str) -> str:
        """Retrieve a secret by name."""
        ...

    async def get_encryption_key(self, org_id: UUID, data_class: str) -> bytes:
        """Retrieve the AES-256-GCM key for a given org and data class."""
        ...

    async def rotate_encryption_key(self, org_id: UUID, data_class: str) -> None:
        """Trigger key rotation for a specific org and data class."""
        ...


# ============================================================
# Commit Repository Protocol
# ============================================================
@runtime_checkable
class CommitRepository(Protocol):
    """Persistence port for commit operations."""

    async def append(self, commit: object) -> None:
        """Append a commit to the immutable log. Must be atomic with outbox write."""
        ...

    async def get_by_hash(self, commit_hash: str) -> object | None:
        """Retrieve a commit by its SHA-256 hash."""
        ...

    async def list_by_branch(
        self,
        repo_id: UUID,
        branch_name: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[object], str | None]:
        """List commits on a branch with cursor pagination."""
        ...


# ============================================================
# Memory Node Repository Protocol
# ============================================================
@runtime_checkable
class MemoryNodeRepository(Protocol):
    """Persistence port for memory node operations."""

    async def create(self, node: object) -> None:
        """Create a new memory node."""
        ...

    async def deprecate(self, node_id: UUID, reason: str, timestamp: int) -> None:
        """Mark a memory node as deprecated."""
        ...

    async def get_by_id(self, node_id: UUID) -> object | None:
        """Retrieve a memory node by ID."""
        ...


# ============================================================
# Vector Store Protocol
# ============================================================
@runtime_checkable
class VectorStore(Protocol):
    """Abstraction over the vector database (Qdrant).

    Org-scoped: implementations receive an org-scoped client
    from OrgScopedConnectionFactory (ADR-0003).
    """

    async def upsert(
        self,
        node_id: UUID,
        embedding: list[float],
        payload: dict[str, object],
    ) -> None:
        """Upsert a vector with payload into the org-scoped collection."""
        ...

    async def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 20,
        min_score: float = 0.3,
        filters: dict[str, object] | None = None,
    ) -> list[tuple[UUID, float, dict[str, object]]]:
        """Search for similar vectors. Returns (node_id, score, payload) tuples."""
        ...

    async def delete(self, node_id: UUID) -> None:
        """Delete a vector from the collection."""
        ...


# ============================================================
# Event Publisher Protocol
# ============================================================
@runtime_checkable
class EventPublisher(Protocol):
    """Abstraction over event publishing (Kafka via outbox relay).

    Events are published via the transactional outbox pattern:
    1. Write to outbox table in same PG transaction as commit.
    2. Relay/CDC picks up and publishes to Kafka.
    """

    async def publish(self, event: object) -> None:
        """Publish an event. In practice, writes to outbox table."""
        ...

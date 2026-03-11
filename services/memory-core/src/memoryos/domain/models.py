"""
MemoryOS Domain — Models (Value Objects & Entities)

Pydantic models for all domain boundaries. No dict crossing API or module boundaries.
These models are immutable data contracts — no business logic here.

See: PRD §2.1, §5.1, docs/CODING_STANDARDS.md §2.2
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from memoryos.domain.enums import (
    AgentStatus,
    AuthorType,
    BranchStatus,
    CommitType,
    ConflictStatus,
    ContradictionType,
    DataClass,
    KeyCustodyMode,
    KeyStatus,
    MemoryAction,
    MemoryTier,
    PlanTier,
    PRStatus,
    ResolutionStrategy,
    ReviewType,
    SourceType,
    UserRole,
    WritePriority,
)


# ============================================================
# Organization
# ============================================================
class Organization(BaseModel):
    """Top-level tenant unit. All data is scoped to an org. PRD §2.1."""

    org_id: UUID
    name: str = Field(min_length=1, max_length=256)
    plan_tier: PlanTier
    created_at: int
    deleted_at: int | None = None
    settings: dict[str, object] = Field(default_factory=dict)

    model_config = {"frozen": True}


# ============================================================
# User & Agent Identity
# ============================================================
class User(BaseModel):
    """Human actor within an organization. PRD §2.1."""

    user_id: UUID
    org_id: UUID
    role: UserRole
    created_at: int
    deleted_at: int | None = None

    model_config = {"frozen": True}


class Agent(BaseModel):
    """Automated actor within an organization. PRD §2.1."""

    agent_id: UUID
    org_id: UUID
    name: str = Field(min_length=1, max_length=256)
    trust_level: int = Field(ge=0, le=4, default=2)
    key_custody_mode: KeyCustodyMode = KeyCustodyMode.LOCAL_KEY
    reputation_score: float = Field(ge=0.0, le=1.0, default=0.5)
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: int
    suspended_at: int | None = None
    revoked_at: int | None = None

    model_config = {"frozen": True}


class KeyRecord(BaseModel):
    """Public key registration record. PRD §7.3."""

    key_id: UUID
    agent_id: UUID
    org_id: UUID
    public_key: bytes
    custody_mode: KeyCustodyMode
    status: KeyStatus = KeyStatus.ACTIVE
    created_at: int
    rotated_at: int | None = None
    revoked_at: int | None = None

    model_config = {"frozen": True}


# ============================================================
# Repository & Branch
# ============================================================
class Repository(BaseModel):
    """Memory container for an agent project. PRD §2.1."""

    repo_id: UUID
    org_id: UUID
    name: str = Field(min_length=1, max_length=256)
    head_commit_hash: str | None = None
    forked_from: UUID | None = None
    onboarding_mode: bool = False
    memignore_config: list[str] = Field(default_factory=list)
    created_at: int
    deleted_at: int | None = None

    model_config = {"frozen": True}


class Branch(BaseModel):
    """Named pointer to a commit hash within a repo. PRD §2.2."""

    branch_id: UUID
    repo_id: UUID
    name: str = Field(min_length=1, max_length=128)
    head_commit_hash: str | None = None
    purpose: str | None = None
    status: BranchStatus = BranchStatus.ACTIVE
    created_by: UUID
    created_at: int
    merged_at: int | None = None
    soft_deleted_at: int | None = None
    legal_hold_until: int | None = None
    retention_days: int = Field(ge=30, default=90)
    etag: str

    model_config = {"frozen": True}


# ============================================================
# Commit (Immutable)
# ============================================================
class Commit(BaseModel):
    """Immutable memory state change record. PRD §2.1, INV-06.

    Once created, a commit is NEVER modified or deleted.
    """

    commit_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    repo_id: UUID
    branch_id: UUID
    branch_name: str
    parent_hash: str | None = None
    author_id: UUID
    author_type: AuthorType
    signature: bytes
    timestamp: int
    commit_type: CommitType
    importance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    novelty_score: float = Field(ge=0.0, le=1.0, default=0.0)
    diff_object: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = {"frozen": True}


# ============================================================
# Memory Node
# ============================================================
class MemoryNode(BaseModel):
    """Individual knowledge atom. Every node maps to exactly one commit (INV-01)."""

    node_id: UUID
    repo_id: UUID
    commit_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    tier: MemoryTier
    content: str | None = None
    content_encrypted: bytes | None = None
    data_class: DataClass
    source_type: SourceType
    confidence: float = Field(ge=0.0, le=1.0)
    importance_score: float = Field(ge=0.0, le=1.0)
    access_count: int = Field(ge=0, default=0)
    last_accessed: int | None = None
    provenance: dict[str, object] = Field(default_factory=dict)
    deprecated_at: int | None = None
    created_at: int

    model_config = {"frozen": True}

    @property
    def is_active(self) -> bool:
        """A node is active when it has not been deprecated."""
        return self.deprecated_at is None


# ============================================================
# Conflict Record
# ============================================================
class ConflictRecord(BaseModel):
    """Persistent contradiction lifecycle record. PRD §2.4."""

    conflict_id: UUID
    repo_id: UUID
    node_a_id: UUID
    node_b_id: UUID
    contradiction_type: ContradictionType
    resolution_strategy: ResolutionStrategy
    status: ConflictStatus = ConflictStatus.OPEN
    resolver_id: UUID | None = None
    rationale: str | None = None
    deferred_until: int | None = None
    created_at: int
    resolved_at: int | None = None

    model_config = {"frozen": True}


# ============================================================
# Pull Request
# ============================================================
class PullRequest(BaseModel):
    """Knowledge merge proposal. PRD §2.3."""

    pr_id: UUID
    org_id: UUID
    source_branch_id: UUID
    target_repo_id: UUID
    proposer_id: UUID
    review_type: ReviewType
    status: PRStatus = PRStatus.DRAFT
    semantic_diff: dict[str, object] | None = None
    etag: str
    created_at: int
    merged_at: int | None = None

    model_config = {"frozen": True}


# ============================================================
# API Request / Response Value Objects
# ============================================================
class WriteMemoryInput(BaseModel):
    """Input for a memory write operation. PRD §4.3."""

    content: str = Field(min_length=1, max_length=8000)
    source_type: SourceType
    priority: WritePriority = WritePriority.NORMAL
    branch: str = "main"
    data_class: DataClass = DataClass.GENERAL
    entity_context: list[str] = Field(default_factory=list)
    evidence: list[dict[str, object]] = Field(default_factory=list)


class WriteMemoryOutput(BaseModel):
    """Output from a memory write operation."""

    commit_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    action: MemoryAction
    importance_score: float = Field(ge=0.0, le=1.0)
    job_id: UUID | None = None
    idempotency_key: UUID
    warnings: list[str] = Field(default_factory=list)


class RetrieveMemoryInput(BaseModel):
    """Input for a memory retrieval operation. PRD §4.4."""

    query: str = Field(min_length=1)
    token_budget: int = Field(ge=500, le=8000, default=2000)
    include_tiers: list[MemoryTier] = Field(
        default_factory=lambda: list(MemoryTier)
    )
    include_relational: bool = True
    branch: str = "main"
    as_of_commit: str | None = None
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.3)
    min_importance: float = Field(ge=0.0, le=1.0, default=0.0)


class MemoryScore(BaseModel):
    """Retrieval ranking scores."""

    relevance: float = Field(ge=0.0, le=1.0)
    recency: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    final: float = Field(ge=0.0, le=1.0)

    model_config = {"frozen": True}

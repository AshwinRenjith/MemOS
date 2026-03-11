"""
MemoryOS Domain — Enumerations

Canonical enum definitions derived from PRD §2.1 identity model and §5.1 schema.
These enums are the single source of truth for valid values across the codebase.
"""

from enum import StrEnum, unique


# ============================================================
# Organization & Plan
# ============================================================
@unique
class PlanTier(StrEnum):
    """Organization subscription tier. See PRD §11.3 for spending caps."""
    FREE = "FREE"
    DEVELOPER = "DEVELOPER"
    TEAM = "TEAM"
    ENTERPRISE = "ENTERPRISE"


# ============================================================
# User Roles (PRD §7.2)
# ============================================================
@unique
class UserRole(StrEnum):
    """User RBAC role. See PRD §7.2 permission matrix."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"
    REVIEWER = "REVIEWER"


# ============================================================
# Agent Identity (PRD §2.1)
# ============================================================
@unique
class AgentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


@unique
class KeyCustodyMode(StrEnum):
    """Key custody tier. See PRD §7.1, ADR-0002."""
    HOSTED_KMS = "HOSTED_KMS"
    CUSTOMER_KMS = "CUSTOMER_KMS"
    LOCAL_KEY = "LOCAL_KEY"


@unique
class KeyStatus(StrEnum):
    """Key lifecycle status. See PRD §7.3."""
    ACTIVE = "ACTIVE"
    ROTATED_OUT = "ROTATED_OUT"
    REVOKED = "REVOKED"


# ============================================================
# Repository (PRD §2.1)
# ============================================================
@unique
class RepoVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    ORG_PRIVATE = "ORG_PRIVATE"
    PRIVATE = "PRIVATE"


# ============================================================
# Branch Lifecycle (PRD §2.2)
# ============================================================
@unique
class BranchStatus(StrEnum):
    """Branch lifecycle state. See PRD §2.2 state machine."""
    ACTIVE = "ACTIVE"
    MERGED = "MERGED"
    SOFT_DELETED = "SOFT_DELETED"
    LEGAL_HOLD = "LEGAL_HOLD"
    HARD_DELETED = "HARD_DELETED"


# ============================================================
# Version Control (PRD §2.1, §5.1)
# ============================================================
@unique
class AuthorType(StrEnum):
    AGENT = "AGENT"
    USER = "USER"
    SYSTEM = "SYSTEM"


@unique
class CommitType(StrEnum):
    """Commit type discriminator. See PRD §5.1."""
    OBSERVE = "OBSERVE"
    LEARN = "LEARN"
    FORGET = "FORGET"
    CORRECT = "CORRECT"
    MERGE = "MERGE"
    ROLLBACK = "ROLLBACK"
    INIT = "INIT"
    CONSOLIDATE = "CONSOLIDATE"


# ============================================================
# Memory (PRD §2.1, §5.1)
# ============================================================
@unique
class MemoryTier(StrEnum):
    """Memory tier. See PRD §2.1."""
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    RELATIONAL = "RELATIONAL"


@unique
class DataClass(StrEnum):
    """Data classification. See PRD §8.1, data_classification_playbook.md."""
    GENERAL = "GENERAL"
    BEHAVIORAL = "BEHAVIORAL"
    PII_ADJACENT = "PII_ADJACENT"
    SENSITIVE = "SENSITIVE"


@unique
class SourceType(StrEnum):
    """Memory source type. See PRD §4.3."""
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    USER_STATED = "USER_STATED"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    CONSOLIDATED = "CONSOLIDATED"


@unique
class MemoryAction(StrEnum):
    """Action taken on a memory write. See PRD §4.3."""
    WRITTEN = "WRITTEN"
    DEDUPLICATED = "DEDUPLICATED"
    QUEUED = "QUEUED"
    SANDBOXED = "SANDBOXED"
    BLOCKED = "BLOCKED"


@unique
class DeprecationReason(StrEnum):
    DECAYED = "DECAYED"
    SUPERSEDED = "SUPERSEDED"
    ROLLBACK = "ROLLBACK"


# ============================================================
# Semantic Diff (PRD §6.1, §6.3)
# ============================================================
@unique
class DiffAction(StrEnum):
    """Semantic diff classification action. See PRD §6.1."""
    NOVEL = "NOVEL"
    RELATED = "RELATED"
    WEAKLY_RELATED = "WEAKLY_RELATED"
    REFINEMENT = "REFINEMENT"
    REINFORCEMENT = "REINFORCEMENT"
    CONTRADICTION = "CONTRADICTION"
    DUPLICATE = "DUPLICATE"


@unique
class EdgeType(StrEnum):
    RELATED = "RELATED"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


# ============================================================
# Conflict Lifecycle (PRD §2.4)
# ============================================================
@unique
class ContradictionType(StrEnum):
    DIRECT = "DIRECT"
    PARTIAL = "PARTIAL"
    TEMPORAL = "TEMPORAL"


@unique
class ResolutionStrategy(StrEnum):
    """Conflict resolution strategy. See PRD §2.4."""
    EVIDENCE_WEIGHT = "EVIDENCE_WEIGHT"
    VOTE = "VOTE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    MANAGER_AGENT = "MANAGER_AGENT"
    TIMESTAMP_WIN = "TIMESTAMP_WIN"


@unique
class ConflictStatus(StrEnum):
    """Conflict lifecycle state. See PRD §2.4 state machine."""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"


# ============================================================
# Pull Request Lifecycle (PRD §2.3)
# ============================================================
@unique
class ReviewType(StrEnum):
    AUTO = "AUTO"
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    CONSENSUS = "CONSENSUS"


@unique
class PRStatus(StrEnum):
    """Pull request lifecycle state. See PRD §2.3 state machine."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MERGED = "MERGED"
    CLOSED = "CLOSED"


# ============================================================
# Write Priority (PRD §4.3)
# ============================================================
@unique
class WritePriority(StrEnum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# Events (PRD §3.1)
# ============================================================
@unique
class EventType(StrEnum):
    COMMIT_CREATED = "memory.commit.created"
    COMMIT_ROLLBACK = "memory.commit.rollback"

"""
MemoryOS Unit Tests — Domain Enums

Validates enum completeness and consistency with database schema.
"""

from memoryos.domain.enums import (
    AgentStatus,
    AuthorType,
    BranchStatus,
    CommitType,
    ConflictStatus,
    ContradictionType,
    DataClass,
    DiffAction,
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


class TestEnumCompleteness:
    """Verify enums match PRD §5.1 schema values exactly."""

    def test_plan_tiers(self) -> None:
        expected = {"FREE", "DEVELOPER", "TEAM", "ENTERPRISE"}
        assert {e.value for e in PlanTier} == expected

    def test_user_roles(self) -> None:
        expected = {"OWNER", "ADMIN", "DEVELOPER", "VIEWER", "REVIEWER"}
        assert {e.value for e in UserRole} == expected

    def test_commit_types(self) -> None:
        expected = {
            "OBSERVE", "LEARN", "FORGET", "CORRECT",
            "MERGE", "ROLLBACK", "INIT", "CONSOLIDATE",
        }
        assert {e.value for e in CommitType} == expected

    def test_memory_tiers(self) -> None:
        expected = {"WORKING", "EPISODIC", "SEMANTIC", "RELATIONAL"}
        assert {e.value for e in MemoryTier} == expected

    def test_data_classes(self) -> None:
        expected = {"GENERAL", "BEHAVIORAL", "PII_ADJACENT", "SENSITIVE"}
        assert {e.value for e in DataClass} == expected

    def test_source_types(self) -> None:
        expected = {
            "OBSERVATION", "INFERENCE", "USER_STATED",
            "TOOL_OUTPUT", "HUMAN_APPROVED", "CONSOLIDATED",
        }
        assert {e.value for e in SourceType} == expected

    def test_branch_statuses(self) -> None:
        expected = {"ACTIVE", "MERGED", "SOFT_DELETED", "LEGAL_HOLD", "HARD_DELETED"}
        assert {e.value for e in BranchStatus} == expected

    def test_pr_statuses(self) -> None:
        expected = {
            "DRAFT", "OPEN", "IN_REVIEW", "CHANGES_REQUESTED",
            "APPROVED", "REJECTED", "MERGED", "CLOSED",
        }
        assert {e.value for e in PRStatus} == expected

    def test_conflict_statuses(self) -> None:
        expected = {"OPEN", "IN_REVIEW", "RESOLVED", "DEFERRED"}
        assert {e.value for e in ConflictStatus} == expected

    def test_key_custody_modes(self) -> None:
        expected = {"HOSTED_KMS", "CUSTOMER_KMS", "LOCAL_KEY"}
        assert {e.value for e in KeyCustodyMode} == expected

    def test_author_types(self) -> None:
        expected = {"AGENT", "USER", "SYSTEM"}
        assert {e.value for e in AuthorType} == expected

    def test_memory_actions(self) -> None:
        expected = {"WRITTEN", "DEDUPLICATED", "QUEUED", "SANDBOXED", "BLOCKED"}
        assert {e.value for e in MemoryAction} == expected

    def test_diff_actions(self) -> None:
        expected = {
            "NOVEL", "RELATED", "WEAKLY_RELATED",
            "REFINEMENT", "REINFORCEMENT", "CONTRADICTION", "DUPLICATE",
        }
        assert {e.value for e in DiffAction} == expected

    def test_resolution_strategies(self) -> None:
        expected = {
            "EVIDENCE_WEIGHT", "VOTE", "HUMAN_REVIEW",
            "MANAGER_AGENT", "TIMESTAMP_WIN",
        }
        assert {e.value for e in ResolutionStrategy} == expected


class TestEnumStringValues:
    """Verify StrEnum values can be used directly as string comparisons."""

    def test_strenum_comparison(self) -> None:
        assert CommitType.OBSERVE == "OBSERVE"
        assert DataClass.SENSITIVE == "SENSITIVE"
        assert BranchStatus.ACTIVE == "ACTIVE"

    def test_strenum_in_format(self) -> None:
        assert f"status={BranchStatus.MERGED}" == "status=MERGED"

    def test_priority_lowercase(self) -> None:
        """Write priority uses lowercase per OpenAPI spec."""
        assert WritePriority.NORMAL == "normal"
        assert WritePriority.CRITICAL == "critical"

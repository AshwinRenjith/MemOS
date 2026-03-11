"""
MemoryOS Unit Tests — Domain Models

Validates Pydantic model constraints match PRD §5.1 schema constraints.
"""

import pytest
from pydantic import ValidationError
from uuid import uuid4

from memoryos.domain.enums import (
    AuthorType,
    BranchStatus,
    CommitType,
    DataClass,
    MemoryTier,
    PlanTier,
    SourceType,
)
from memoryos.domain.models import (
    Branch,
    Commit,
    MemoryNode,
    Organization,
    Repository,
    WriteMemoryInput,
)


class TestOrganization:
    def test_valid_organization(self) -> None:
        org = Organization(
            org_id=uuid4(),
            name="Test Org",
            plan_tier=PlanTier.FREE,
            created_at=1710100000000,
        )
        assert org.plan_tier == PlanTier.FREE
        assert org.deleted_at is None

    def test_name_min_length(self) -> None:
        with pytest.raises(ValidationError, match="min_length"):
            Organization(
                org_id=uuid4(),
                name="",
                plan_tier=PlanTier.FREE,
                created_at=1710100000000,
            )

    def test_frozen_immutability(self) -> None:
        org = Organization(
            org_id=uuid4(),
            name="Test",
            plan_tier=PlanTier.FREE,
            created_at=1710100000000,
        )
        with pytest.raises(ValidationError):
            org.name = "Changed"  # type: ignore[misc]


class TestCommit:
    def test_valid_commit(self) -> None:
        commit = Commit(
            commit_hash="a" * 64,
            repo_id=uuid4(),
            branch_id=uuid4(),
            branch_name="main",
            author_id=uuid4(),
            author_type=AuthorType.AGENT,
            signature=b"fake-sig",
            timestamp=1710100000000,
            commit_type=CommitType.OBSERVE,
        )
        assert commit.importance_score == 0.0
        assert commit.parent_hash is None
        assert commit.metadata == {}

    def test_invalid_hash_length(self) -> None:
        with pytest.raises(ValidationError, match="pattern"):
            Commit(
                commit_hash="tooshort",
                repo_id=uuid4(),
                branch_id=uuid4(),
                branch_name="main",
                author_id=uuid4(),
                author_type=AuthorType.AGENT,
                signature=b"sig",
                timestamp=1710100000000,
                commit_type=CommitType.OBSERVE,
            )

    def test_importance_score_bounds(self) -> None:
        with pytest.raises(ValidationError, match="less_than_equal"):
            Commit(
                commit_hash="a" * 64,
                repo_id=uuid4(),
                branch_id=uuid4(),
                branch_name="main",
                author_id=uuid4(),
                author_type=AuthorType.AGENT,
                signature=b"sig",
                timestamp=1710100000000,
                commit_type=CommitType.OBSERVE,
                importance_score=1.5,
            )


class TestMemoryNode:
    def test_active_node(self) -> None:
        node = MemoryNode(
            node_id=uuid4(),
            repo_id=uuid4(),
            commit_hash="b" * 64,
            tier=MemoryTier.EPISODIC,
            content="User prefers Python.",
            data_class=DataClass.GENERAL,
            source_type=SourceType.OBSERVATION,
            confidence=0.95,
            importance_score=0.7,
            provenance={"agent_id": str(uuid4())},
            created_at=1710100000000,
        )
        assert node.is_active is True
        assert node.content_encrypted is None

    def test_deprecated_node(self) -> None:
        node = MemoryNode(
            node_id=uuid4(),
            repo_id=uuid4(),
            commit_hash="b" * 64,
            tier=MemoryTier.SEMANTIC,
            content="Old fact",
            data_class=DataClass.GENERAL,
            source_type=SourceType.INFERENCE,
            confidence=0.5,
            importance_score=0.3,
            provenance={},
            created_at=1710100000000,
            deprecated_at=1710200000000,
        )
        assert node.is_active is False

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            MemoryNode(
                node_id=uuid4(),
                repo_id=uuid4(),
                commit_hash="b" * 64,
                tier=MemoryTier.EPISODIC,
                content="test",
                data_class=DataClass.GENERAL,
                source_type=SourceType.OBSERVATION,
                confidence=-0.1,
                importance_score=0.5,
                provenance={},
                created_at=1710100000000,
            )


class TestBranch:
    def test_valid_branch(self) -> None:
        branch = Branch(
            branch_id=uuid4(),
            repo_id=uuid4(),
            name="feature/experiment",
            head_commit_hash="c" * 64,
            status=BranchStatus.ACTIVE,
            created_by=uuid4(),
            created_at=1710100000000,
            etag=str(uuid4()),
        )
        assert branch.retention_days == 90
        assert branch.legal_hold_until is None

    def test_retention_days_minimum(self) -> None:
        with pytest.raises(ValidationError, match="greater_than_equal"):
            Branch(
                branch_id=uuid4(),
                repo_id=uuid4(),
                name="test",
                status=BranchStatus.ACTIVE,
                created_by=uuid4(),
                created_at=1710100000000,
                retention_days=7,  # below minimum 30
                etag="etag",
            )


class TestWriteMemoryInput:
    def test_valid_write_input(self) -> None:
        inp = WriteMemoryInput(
            content="User prefers concise answers",
            source_type=SourceType.OBSERVATION,
        )
        assert inp.branch == "main"
        assert inp.data_class == DataClass.GENERAL
        assert inp.priority == "normal"

    def test_content_max_length(self) -> None:
        with pytest.raises(ValidationError, match="max_length"):
            WriteMemoryInput(
                content="x" * 8001,
                source_type=SourceType.OBSERVATION,
            )

    def test_content_min_length(self) -> None:
        with pytest.raises(ValidationError, match="min_length"):
            WriteMemoryInput(
                content="",
                source_type=SourceType.OBSERVATION,
            )

-- ============================================================
-- Migration 0005: Conflict Records + Pull Requests
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §5.1 (PostgreSQL Schema), §2.3 (PR Lifecycle), §2.4 (Conflict Lifecycle)
-- Invariants: INV-04 (tenant isolation), INV-10 (merge parent cardinality)
-- Rollback:   DROP TABLE pull_requests; DROP TABLE conflict_records;
-- ============================================================

-- UP

-- Conflict Records (PRD §2.4 — Conflict Lifecycle State Machine)
CREATE TABLE conflict_records (
    conflict_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id               UUID NOT NULL REFERENCES repositories(repo_id),
    node_a_id             UUID NOT NULL REFERENCES memory_nodes(node_id),
    node_b_id             UUID NOT NULL REFERENCES memory_nodes(node_id),
    contradiction_type    TEXT NOT NULL CHECK (contradiction_type IN ('DIRECT', 'PARTIAL', 'TEMPORAL')),
    resolution_strategy   TEXT NOT NULL CHECK (resolution_strategy IN (
                              'EVIDENCE_WEIGHT', 'VOTE', 'HUMAN_REVIEW',
                              'MANAGER_AGENT', 'TIMESTAMP_WIN'
                          )),
    status                TEXT NOT NULL CHECK (status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'DEFERRED'))
                          DEFAULT 'OPEN',
    resolver_id           UUID,
    rationale             TEXT,
    deferred_until        BIGINT,
    created_at            BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    resolved_at           BIGINT,

    -- Every RESOLVED record must have resolver and rationale (PRD §2.4 invariant 2)
    CONSTRAINT chk_resolved_fields CHECK (
        CASE
            WHEN status = 'RESOLVED' THEN resolver_id IS NOT NULL AND rationale IS NOT NULL AND resolved_at IS NOT NULL
            ELSE true
        END
    ),
    -- DEFERRED records must have a deferred_until timestamp
    CONSTRAINT chk_deferred_until CHECK (
        CASE
            WHEN status = 'DEFERRED' THEN deferred_until IS NOT NULL
            ELSE true
        END
    ),
    -- Ensure node_a and node_b are different
    CONSTRAINT chk_different_nodes CHECK (node_a_id != node_b_id)
);

-- ConflictRecords are NEVER deleted (PRD §2.4 invariant 1)
CREATE RULE no_delete_conflict_records AS ON DELETE TO conflict_records DO INSTEAD NOTHING;

-- RLS (INV-04)
ALTER TABLE conflict_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE conflict_records FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON conflict_records
    USING (repo_id IN (
        SELECT repo_id FROM repositories
        WHERE org_id = current_setting('app.org_id', true)::UUID
    ));

GRANT SELECT, INSERT, UPDATE ON conflict_records TO memoryos_app;

CREATE INDEX idx_conflicts_repo_status ON conflict_records (repo_id, status);
CREATE INDEX idx_conflicts_open ON conflict_records (repo_id, created_at DESC)
    WHERE status = 'OPEN';
CREATE INDEX idx_conflicts_nodes ON conflict_records (node_a_id, node_b_id);
CREATE INDEX idx_conflicts_deferred ON conflict_records (deferred_until)
    WHERE status = 'DEFERRED' AND deferred_until IS NOT NULL;

COMMENT ON TABLE conflict_records IS 'Persistent contradiction lifecycle record. NEVER deleted. See PRD §2.4.';
COMMENT ON COLUMN conflict_records.status IS 'Lifecycle: OPEN → IN_REVIEW → RESOLVED | DEFERRED. RESOLVED can reopen on new evidence.';

-- Pull Requests (PRD §2.3 — PR Lifecycle State Machine)
CREATE TABLE pull_requests (
    pr_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                UUID NOT NULL REFERENCES organizations(org_id),
    source_branch_id      UUID NOT NULL REFERENCES branches(branch_id),
    target_repo_id        UUID NOT NULL REFERENCES repositories(repo_id),
    proposer_id           UUID NOT NULL,
    review_type           TEXT NOT NULL CHECK (review_type IN ('AUTO', 'HUMAN', 'AGENT', 'CONSENSUS')),
    status                TEXT NOT NULL CHECK (status IN (
                              'DRAFT', 'OPEN', 'IN_REVIEW', 'CHANGES_REQUESTED',
                              'APPROVED', 'REJECTED', 'MERGED', 'CLOSED'
                          )) DEFAULT 'DRAFT',
    semantic_diff         JSONB,
    etag                  TEXT NOT NULL DEFAULT gen_random_uuid()::TEXT,
    created_at            BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    merged_at             BIGINT,

    -- PR can only be in MERGED status if merged_at is set
    CONSTRAINT chk_merged_timestamp CHECK (
        CASE
            WHEN status = 'MERGED' THEN merged_at IS NOT NULL
            ELSE true
        END
    )
);

-- RLS (INV-04)
ALTER TABLE pull_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE pull_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON pull_requests
    USING (org_id = current_setting('app.org_id', true)::UUID);

GRANT SELECT, INSERT, UPDATE ON pull_requests TO memoryos_app;

CREATE INDEX idx_prs_org_status ON pull_requests (org_id, status);
CREATE INDEX idx_prs_source_branch ON pull_requests (source_branch_id);
CREATE INDEX idx_prs_target_repo ON pull_requests (target_repo_id, status);
CREATE INDEX idx_prs_proposer ON pull_requests (proposer_id, created_at DESC);

COMMENT ON TABLE pull_requests IS 'Knowledge merge proposal. See PRD §2.3 for lifecycle state machine.';
COMMENT ON COLUMN pull_requests.semantic_diff IS 'Computed semantic diff for this PR. See PRD §6.3 DiffObject schema.';
COMMENT ON COLUMN pull_requests.etag IS 'Optimistic concurrency token for status updates.';

-- DOWN
-- DROP TABLE IF EXISTS pull_requests CASCADE;
-- DROP RULE IF EXISTS no_delete_conflict_records ON conflict_records;
-- DROP TABLE IF EXISTS conflict_records CASCADE;

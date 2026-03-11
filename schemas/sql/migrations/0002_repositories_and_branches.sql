-- ============================================================
-- Migration 0002: Repositories and Branches
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §5.1 (PostgreSQL Schema), §2.1 (Identity Model), §2.2 (Branch Lifecycle)
-- Invariants: INV-04 (tenant isolation), INV-05 (legal hold), INV-09 (branch head CAS)
-- Rollback:   DROP TABLE branches; DROP TABLE repositories;
-- ============================================================

-- UP

-- Repositories
CREATE TABLE repositories (
    repo_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id            UUID NOT NULL REFERENCES organizations(org_id),
    name              TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 256),
    visibility        TEXT NOT NULL CHECK (visibility IN ('PUBLIC', 'ORG_PRIVATE', 'PRIVATE')),
    head_commit_hash  CHAR(64),
    forked_from       UUID REFERENCES repositories(repo_id),
    onboarding_mode   BOOLEAN NOT NULL DEFAULT false,
    memignore_config  JSONB NOT NULL DEFAULT '[]',
    created_at        BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    deleted_at        BIGINT
);

-- RLS (INV-04)
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON repositories
    USING (org_id = current_setting('app.org_id', true)::UUID);

GRANT SELECT, INSERT, UPDATE ON repositories TO memoryos_app;

CREATE INDEX idx_repositories_org_id ON repositories (org_id);
CREATE INDEX idx_repositories_name ON repositories (org_id, name);
CREATE INDEX idx_repositories_forked_from ON repositories (forked_from) WHERE forked_from IS NOT NULL;

COMMENT ON TABLE repositories IS 'Memory container for one agent project. See PRD §2.1.';
COMMENT ON COLUMN repositories.memignore_config IS 'Org-customizable .memignore rules (JSON array). Built-in rules are applied separately.';
COMMENT ON COLUMN repositories.onboarding_mode IS 'When true, suppresses deduplication to allow bulk knowledge import.';

-- Branches
CREATE TABLE branches (
    branch_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id           UUID NOT NULL REFERENCES repositories(repo_id),
    name              TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 128),
    head_commit_hash  CHAR(64),
    purpose           TEXT,
    status            TEXT NOT NULL CHECK (status IN ('ACTIVE', 'MERGED', 'SOFT_DELETED', 'LEGAL_HOLD', 'HARD_DELETED'))
                      DEFAULT 'ACTIVE',
    created_by        UUID NOT NULL,
    created_at        BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    merged_at         BIGINT,
    soft_deleted_at   BIGINT,
    legal_hold_until  BIGINT,
    retention_days    INT NOT NULL DEFAULT 90 CHECK (retention_days >= 30),
    -- ETag for optimistic concurrency on branch HEAD updates (INV-09)
    etag              TEXT NOT NULL DEFAULT gen_random_uuid()::TEXT,
    UNIQUE(repo_id, name)
);

-- RLS (INV-04) — branches inherit org scope via repo
ALTER TABLE branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE branches FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON branches
    USING (repo_id IN (
        SELECT repo_id FROM repositories
        WHERE org_id = current_setting('app.org_id', true)::UUID
    ));

GRANT SELECT, INSERT, UPDATE ON branches TO memoryos_app;

CREATE INDEX idx_branches_repo_id ON branches (repo_id);
CREATE INDEX idx_branches_status ON branches (repo_id, status);
CREATE INDEX idx_branches_legal_hold ON branches (status) WHERE status = 'LEGAL_HOLD';

COMMENT ON TABLE branches IS 'Named pointer to a commit hash within a Repo. See PRD §2.1, §2.2 for lifecycle state machine.';
COMMENT ON COLUMN branches.status IS 'Branch lifecycle state: ACTIVE → SOFT_DELETED → HARD_DELETED, or ACTIVE → MERGED, or ACTIVE → LEGAL_HOLD. See PRD §2.2.';
COMMENT ON COLUMN branches.legal_hold_until IS 'If status=LEGAL_HOLD, this timestamp indicates earliest release. INV-05: no mutation while in LEGAL_HOLD.';
COMMENT ON COLUMN branches.etag IS 'Optimistic concurrency token. Updated on every branch HEAD change. INV-09 enforcement.';
COMMENT ON COLUMN branches.retention_days IS 'Days to retain after soft-delete. Min 30. See PRD §2.2 retention policy.';

-- DOWN
-- DROP TABLE IF EXISTS branches CASCADE;
-- DROP TABLE IF EXISTS repositories CASCADE;

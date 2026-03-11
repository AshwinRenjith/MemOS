-- ============================================================
-- Migration 0003: Commits (Append-Only) + Outbox
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §5.1 (PostgreSQL Schema), §3.1 (Event-Sourced Write Path)
-- Invariants: INV-01 (node→commit), INV-06 (commit immutability), INV-10 (merge parent)
-- Rollback:   DROP TABLE outbox; DROP TABLE commits;
-- ============================================================

-- UP

-- Commits table (APPEND-ONLY — INV-06)
CREATE TABLE commits (
    commit_hash       CHAR(64) PRIMARY KEY,
    repo_id           UUID NOT NULL REFERENCES repositories(repo_id),
    branch_id         UUID NOT NULL REFERENCES branches(branch_id),
    parent_hash       CHAR(64),              -- NULL for INIT commits only
    author_id         UUID NOT NULL,
    author_type       TEXT NOT NULL CHECK (author_type IN ('AGENT', 'USER', 'SYSTEM')),
    signature         BYTEA NOT NULL,
    timestamp         BIGINT NOT NULL,
    commit_type       TEXT NOT NULL CHECK (commit_type IN (
                          'OBSERVE', 'LEARN', 'FORGET', 'CORRECT',
                          'MERGE', 'ROLLBACK', 'INIT', 'CONSOLIDATE'
                      )),
    branch_name       TEXT NOT NULL,
    importance_score  FLOAT NOT NULL DEFAULT 0.0 CHECK (importance_score BETWEEN 0.0 AND 1.0),
    novelty_score     FLOAT NOT NULL DEFAULT 0.0 CHECK (novelty_score BETWEEN 0.0 AND 1.0),
    diff_object       JSONB NOT NULL DEFAULT '{}',
    metadata          JSONB NOT NULL DEFAULT '{}'
);

-- ENFORCE APPEND-ONLY (INV-06): no updates or deletes on commits
-- PostgreSQL rules ensure these operations are silently blocked at the DB level.
CREATE RULE no_update_commits AS ON UPDATE TO commits DO INSTEAD NOTHING;
CREATE RULE no_delete_commits AS ON DELETE TO commits DO INSTEAD NOTHING;

-- RLS (INV-04) — commits inherit org scope via repo
ALTER TABLE commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE commits FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON commits
    USING (repo_id IN (
        SELECT repo_id FROM repositories
        WHERE org_id = current_setting('app.org_id', true)::UUID
    ));

-- Grant INSERT only (no UPDATE/DELETE) for the app role (defense in depth with rules)
GRANT SELECT, INSERT ON commits TO memoryos_app;

-- Indexes for common query patterns
CREATE INDEX idx_commits_repo_branch ON commits (repo_id, branch_name, timestamp DESC);
CREATE INDEX idx_commits_repo_type ON commits (repo_id, commit_type);
CREATE INDEX idx_commits_author ON commits (author_id, timestamp DESC);
CREATE INDEX idx_commits_timestamp ON commits (repo_id, timestamp DESC);
CREATE INDEX idx_commits_parent ON commits (parent_hash) WHERE parent_hash IS NOT NULL;
CREATE INDEX idx_commits_importance ON commits (repo_id, importance_score DESC)
    WHERE importance_score >= 0.7;

COMMENT ON TABLE commits IS 'Immutable memory state change record. APPEND-ONLY: no UPDATE or DELETE. See PRD §2.1, INV-06.';
COMMENT ON COLUMN commits.commit_hash IS 'SHA-256 hash of canonical JSON payload. See ADR-0001.';
COMMENT ON COLUMN commits.signature IS 'Ed25519 signature over commit_hash|timestamp. See ADR-0002.';
COMMENT ON COLUMN commits.diff_object IS 'Versioned DiffObject per PRD §6.3. Records all memory mutations in this commit.';
COMMENT ON COLUMN commits.metadata IS 'Informational metadata. NOT part of commit hash (excluded for INV-03 replay determinism).';

-- Outbox table (for event-sourced write path — §3.1)
-- This table is written in the SAME transaction as the commit insert.
-- A CDC tool (Debezium) or polling relay picks up unpublished events.
CREATE TABLE outbox (
    outbox_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id      CHAR(64) NOT NULL,     -- commit_hash (foreign key to commits)
    event_type        TEXT NOT NULL CHECK (event_type IN (
                          'memory.commit.created',
                          'memory.commit.rollback'
                      )),
    payload           JSONB NOT NULL,
    created_at        BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    published_at      BIGINT                 -- NULL until CDC/relay picks up
);

-- RLS (INV-04) — outbox doesn't have org_id directly, but is only
-- written in the same transaction as a commit, so isolation is inherited.
-- For query safety, we add RLS via aggregate_id → commits → repo → org.
ALTER TABLE outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON outbox
    USING (aggregate_id IN (
        SELECT commit_hash FROM commits
        WHERE repo_id IN (
            SELECT repo_id FROM repositories
            WHERE org_id = current_setting('app.org_id', true)::UUID
        )
    ));

GRANT SELECT, INSERT, UPDATE ON outbox TO memoryos_app;

-- Index for relay/CDC polling: find unpublished events
CREATE INDEX idx_outbox_unpublished ON outbox (created_at ASC)
    WHERE published_at IS NULL;

COMMENT ON TABLE outbox IS 'Transactional outbox for event-sourced write path. See PRD §3.1. Written atomically with commit.';
COMMENT ON COLUMN outbox.aggregate_id IS 'commit_hash — links this event to its commit.';
COMMENT ON COLUMN outbox.published_at IS 'NULL until CDC/relay publishes to Kafka. Set by relay after successful publish.';

-- DOWN
-- DROP TABLE IF EXISTS outbox CASCADE;
-- DROP RULE IF EXISTS no_delete_commits ON commits;
-- DROP RULE IF EXISTS no_update_commits ON commits;
-- DROP TABLE IF EXISTS commits CASCADE;

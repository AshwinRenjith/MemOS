-- ============================================================
-- Migration 0004: Memory Nodes
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §5.1 (PostgreSQL Schema), §2.1 (Memory Node identity)
-- Invariants: INV-01 (node→commit mapping), INV-04 (tenant isolation),
--             INV-08 (PII/SENSITIVE encryption)
-- Rollback:   DROP TABLE memory_nodes;
-- ============================================================

-- UP

CREATE TABLE memory_nodes (
    node_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id             UUID NOT NULL REFERENCES repositories(repo_id),
    commit_hash         CHAR(64) NOT NULL REFERENCES commits(commit_hash),  -- INV-01
    tier                TEXT NOT NULL CHECK (tier IN ('WORKING', 'EPISODIC', 'SEMANTIC', 'RELATIONAL')),
    content             TEXT,                  -- NULL if data_class = SENSITIVE (encrypted blob in content_encrypted)
    content_encrypted   BYTEA,                 -- non-NULL if data_class IN ('PII_ADJACENT', 'SENSITIVE') — INV-08
    data_class          TEXT NOT NULL CHECK (data_class IN ('GENERAL', 'BEHAVIORAL', 'PII_ADJACENT', 'SENSITIVE')),
    source_type         TEXT NOT NULL CHECK (source_type IN (
                            'OBSERVATION', 'INFERENCE', 'USER_STATED',
                            'TOOL_OUTPUT', 'HUMAN_APPROVED', 'CONSOLIDATED'
                        )),
    confidence          FLOAT NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    importance_score    FLOAT NOT NULL CHECK (importance_score BETWEEN 0.0 AND 1.0),
    access_count        INT NOT NULL DEFAULT 0,
    last_accessed       BIGINT,
    provenance          JSONB NOT NULL,
    deprecated_at       BIGINT,                -- non-NULL when node is superseded/decayed/rolled-back
    created_at          BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,

    -- INV-08 enforcement: if data_class requires encryption, content must be NULL
    CONSTRAINT chk_encryption_content CHECK (
        CASE
            WHEN data_class IN ('PII_ADJACENT', 'SENSITIVE') THEN content IS NULL
            ELSE true
        END
    ),
    -- INV-08 enforcement: if data_class requires encryption, encrypted blob must exist
    CONSTRAINT chk_encryption_blob CHECK (
        CASE
            WHEN data_class IN ('PII_ADJACENT', 'SENSITIVE') THEN content_encrypted IS NOT NULL
            ELSE true
        END
    )
);

-- RLS (INV-04)
ALTER TABLE memory_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_nodes FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON memory_nodes
    USING (repo_id IN (
        SELECT repo_id FROM repositories
        WHERE org_id = current_setting('app.org_id', true)::UUID
    ));

GRANT SELECT, INSERT, UPDATE ON memory_nodes TO memoryos_app;

-- Indexes
CREATE INDEX idx_memory_nodes_repo ON memory_nodes (repo_id, tier, created_at DESC);
CREATE INDEX idx_memory_nodes_commit ON memory_nodes (commit_hash);
CREATE INDEX idx_memory_nodes_tier ON memory_nodes (repo_id, tier) WHERE deprecated_at IS NULL;
CREATE INDEX idx_memory_nodes_importance ON memory_nodes (repo_id, importance_score DESC)
    WHERE deprecated_at IS NULL;
CREATE INDEX idx_memory_nodes_data_class ON memory_nodes (repo_id, data_class)
    WHERE data_class IN ('PII_ADJACENT', 'SENSITIVE');
CREATE INDEX idx_memory_nodes_deprecated ON memory_nodes (repo_id, deprecated_at)
    WHERE deprecated_at IS NOT NULL;

COMMENT ON TABLE memory_nodes IS 'Individual knowledge atom. Every node maps to exactly one commit (INV-01). See PRD §2.1.';
COMMENT ON COLUMN memory_nodes.content IS 'Plaintext content. NULL when data_class requires encryption (INV-08).';
COMMENT ON COLUMN memory_nodes.content_encrypted IS 'AES-256-GCM encrypted content. Key per org per data class. See PRD §8.1.';
COMMENT ON COLUMN memory_nodes.provenance IS 'Full provenance chain: source agent, session, evidence refs, timestamps.';
COMMENT ON COLUMN memory_nodes.deprecated_at IS 'Set when node is superseded, decayed, or rolled back. Non-null = inactive.';

-- DOWN
-- DROP TABLE IF EXISTS memory_nodes CASCADE;

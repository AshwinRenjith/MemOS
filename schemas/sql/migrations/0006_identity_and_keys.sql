-- ============================================================
-- Migration 0006: Key Registry + Agents + Users
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §2.1 (Identity Model), §7.1–7.3 (Key Custody & Lifecycle)
-- Invariants: INV-02 (offline signature verification), INV-04 (tenant isolation)
-- Rollback:   DROP TABLE key_registry; DROP TABLE agents; DROP TABLE users;
-- ============================================================

-- UP

-- Users
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id),
    email_encrypted BYTEA NOT NULL,           -- encrypted at rest (never plaintext)
    role            TEXT NOT NULL CHECK (role IN ('OWNER', 'ADMIN', 'DEVELOPER', 'VIEWER', 'REVIEWER')),
    created_at      BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    deleted_at      BIGINT                    -- soft-delete for GDPR
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON users
    USING (org_id = current_setting('app.org_id', true)::UUID);

GRANT SELECT, INSERT, UPDATE ON users TO memoryos_app;

CREATE INDEX idx_users_org ON users (org_id);
CREATE INDEX idx_users_role ON users (org_id, role);

COMMENT ON TABLE users IS 'Human actor within an Org. See PRD §2.1.';
COMMENT ON COLUMN users.email_encrypted IS 'AES-256-GCM encrypted email. Decrypted only when needed. Never stored plaintext.';
COMMENT ON COLUMN users.role IS 'RBAC role. See PRD §7.2 permission matrix.';

-- Agents
CREATE TABLE agents (
    agent_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES organizations(org_id),
    name                TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 256),
    trust_level         INT NOT NULL DEFAULT 2 CHECK (trust_level BETWEEN 0 AND 4),
    key_custody_mode    TEXT NOT NULL CHECK (key_custody_mode IN ('HOSTED_KMS', 'CUSTOMER_KMS', 'LOCAL_KEY'))
                        DEFAULT 'LOCAL_KEY',
    reputation_score    FLOAT NOT NULL DEFAULT 0.5 CHECK (reputation_score BETWEEN 0.0 AND 1.0),
    status              TEXT NOT NULL CHECK (status IN ('ACTIVE', 'SUSPENDED', 'REVOKED'))
                        DEFAULT 'ACTIVE',
    created_at          BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    suspended_at        BIGINT,
    revoked_at          BIGINT
);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON agents
    USING (org_id = current_setting('app.org_id', true)::UUID);

GRANT SELECT, INSERT, UPDATE ON agents TO memoryos_app;

CREATE INDEX idx_agents_org ON agents (org_id);
CREATE INDEX idx_agents_status ON agents (org_id, status);

COMMENT ON TABLE agents IS 'Automated actor within an Org. See PRD §2.1.';
COMMENT ON COLUMN agents.trust_level IS '0-4 trust scale. See PRD §7.1 for custody mode ↔ trust level mapping.';
COMMENT ON COLUMN agents.key_custody_mode IS 'LOCAL_KEY (Phase A), HOSTED_KMS (Phase B), CUSTOMER_KMS (Phase D). See ADR-0002.';

-- Key Registry (supports key lifecycle: provision → rotate → revoke)
CREATE TABLE key_registry (
    key_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id            UUID NOT NULL REFERENCES agents(agent_id),
    org_id              UUID NOT NULL REFERENCES organizations(org_id),
    public_key          BYTEA NOT NULL,        -- Ed25519 public key bytes
    custody_mode        TEXT NOT NULL CHECK (custody_mode IN ('LOCAL_KEY', 'HOSTED_KMS', 'CUSTOMER_KMS')),
    status              TEXT NOT NULL CHECK (status IN ('ACTIVE', 'ROTATED_OUT', 'REVOKED'))
                        DEFAULT 'ACTIVE',
    created_at          BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    rotated_at          BIGINT,
    revoked_at          BIGINT,

    -- Rotated/revoked keys retain timestamps
    CONSTRAINT chk_rotated_timestamp CHECK (
        CASE WHEN status = 'ROTATED_OUT' THEN rotated_at IS NOT NULL ELSE true END
    ),
    CONSTRAINT chk_revoked_timestamp CHECK (
        CASE WHEN status = 'REVOKED' THEN revoked_at IS NOT NULL ELSE true END
    )
);

-- Only one ACTIVE key per agent at a time
CREATE UNIQUE INDEX idx_key_registry_active_agent ON key_registry (agent_id)
    WHERE status = 'ACTIVE';

ALTER TABLE key_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE key_registry FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON key_registry
    USING (org_id = current_setting('app.org_id', true)::UUID);

GRANT SELECT, INSERT, UPDATE ON key_registry TO memoryos_app;

CREATE INDEX idx_key_registry_agent ON key_registry (agent_id, status);

COMMENT ON TABLE key_registry IS 'Public key store for Ed25519 signing keys. Old keys retained for historical verification (INV-02). See PRD §7.3.';
COMMENT ON COLUMN key_registry.public_key IS 'Ed25519 public key bytes. Used for offline commit signature verification.';

-- DOWN
-- DROP TABLE IF EXISTS key_registry CASCADE;
-- DROP TABLE IF EXISTS agents CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

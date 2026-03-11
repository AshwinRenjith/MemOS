-- ============================================================
-- Migration 0001: Bootstrap — Organizations
-- ============================================================
-- Author:     AI Builder (Phase 0)
-- Date:       2026-03-11
-- PRD:        §5.1 (PostgreSQL Schema), §2.1 (Identity Model)
-- Invariants: INV-04 (tenant isolation via RLS)
-- Rollback:   DROP TABLE organizations; DROP ROLE IF EXISTS memoryos_app;
-- ============================================================

-- UP

-- Create the application database role (non-superuser, non-bypassrls)
-- This role is used by the memory-core application. It CANNOT bypass RLS.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'memoryos_app') THEN
        CREATE ROLE memoryos_app WITH LOGIN PASSWORD 'change_me_in_production' NOSUPERUSER NOBYPASSRLS;
    END IF;
END
$$;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4() fallback

-- Organizations table
CREATE TABLE organizations (
    org_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 256),
    plan_tier     TEXT NOT NULL CHECK (plan_tier IN ('FREE', 'DEVELOPER', 'TEAM', 'ENTERPRISE')),
    created_at    BIGINT NOT NULL DEFAULT (extract(epoch FROM now()) * 1000)::BIGINT,
    deleted_at    BIGINT,
    settings      JSONB NOT NULL DEFAULT '{}'
);

-- Row-Level Security (INV-04: tenant isolation by construction)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- RLS policy: application user can only see rows matching session org_id
CREATE POLICY org_isolation ON organizations
    USING (org_id = current_setting('app.org_id', true)::UUID);

-- Force RLS even for table owner (defense in depth)
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

-- Grant application role access
GRANT SELECT, INSERT, UPDATE ON organizations TO memoryos_app;

-- Indexes
CREATE INDEX idx_organizations_plan_tier ON organizations (plan_tier);
CREATE INDEX idx_organizations_created_at ON organizations (created_at);

COMMENT ON TABLE organizations IS 'Top-level tenant unit. All data is scoped to an Org. See PRD §2.1.';
COMMENT ON COLUMN organizations.plan_tier IS 'FREE | DEVELOPER | TEAM | ENTERPRISE — determines rate limits and feature access.';
COMMENT ON COLUMN organizations.settings IS 'Org-level configuration: retention overrides, .memignore customizations, etc.';

-- DOWN
-- DROP TABLE IF EXISTS organizations CASCADE;
-- DROP ROLE IF EXISTS memoryos_app;

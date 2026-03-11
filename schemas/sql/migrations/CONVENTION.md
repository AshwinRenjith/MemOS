# SQL Migration Convention

> Binding convention for all MemoryOS database migrations.
> See also: docs/CODING_STANDARDS.md §4.

---

## Naming

Migrations are numbered sequentially with zero-padded 4-digit prefix:

```
schemas/sql/migrations/
  0001_bootstrap_organizations.sql
  0002_repositories_and_branches.sql
  0003_commits_append_only.sql
  ...
```

## Structure

Each migration file MUST contain:

1. **Header comment** with:
   - Migration number and title
   - Author
   - Date
   - PRD section reference
   - Invariants affected
   - Rollback strategy

2. **Forward migration** (`-- UP`)

3. **Rollback migration** (`-- DOWN`)

## Rules

1. **Every migration must be reversible.** The `-- DOWN` section must
   undo the `-- UP` section cleanly.

2. **No destructive DDL without supervisor approval.** DROP TABLE, DROP
   COLUMN, or data-deleting operations require explicit sign-off and a
   backout plan documented in the PR.

3. **RLS policies are mandatory** on every table containing `org_id`.
   The migration that creates the table MUST include RLS enablement
   and the org isolation policy.

4. **Commit table immutability** is enforced via PostgreSQL rules
   (`CREATE RULE no_update_commits ...`). The migration creating the
   commits table MUST include these rules.

5. **Test before apply.** All migrations must be tested against a
   clean database and against a database with existing data before
   being applied to staging.

## Execution

Migrations are applied using Alembic (Python SQLAlchemy migration tool).
The raw SQL files in this directory are the source of truth. Alembic
migration scripts import and execute these SQL files.

```bash
# Apply next migration
alembic upgrade head

# Rollback one
alembic downgrade -1

# Apply specific migration
alembic upgrade 0003
```

## Rollback Triggers

A migration rollback is triggered if:
- Any invariant test fails after migration
- Any tenant isolation test fails
- Any data integrity check fails
- Supervisor requests rollback

## Evidence

After each migration:
1. Record the migration version and timestamp
2. Run invariant tests
3. Save test results to evidence directory

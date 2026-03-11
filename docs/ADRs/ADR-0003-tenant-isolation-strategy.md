# ADR-0003: Tenant Isolation Strategy

| Field           | Value                                                  |
|-----------------|--------------------------------------------------------|
| **Status**      | ACCEPTED                                               |
| **Date**        | 2026-03-11                                             |
| **Author**      | AI Builder (Phase 0)                                   |
| **Phase**       | Phase 0 (design), Phase A (enforcement), Phase C (pentest) |
| **PRD Section** | §3.4 (Tenant Isolation), §2.5 (INV-04)                |
| **Invariants**  | INV-04                                                 |

---

## Context

MemoryOS is a multi-tenant platform where each Organization is a top-level
isolation boundary. The PRD states (§3.4, INV-04):

> **INV-04**: Cross-tenant retrieval is impossible by construction. An org_id
> filter is applied at the storage driver level before any query execution,
> not at the application layer.

This is the single most critical security invariant. A tenant isolation breach
is classified as `TENANT_ISOLATION_BREACH_SUSPECTED` (§10.4) and triggers
immediate API lockdown, security on-call page, and forensic investigation.

The audit of v1.0 (P0-04) found that tenant isolation was listed as an "open
problem" while the product simultaneously promised enterprise-grade isolation.
This ADR establishes the binding implementation strategy.

---

## Decision

### Principle: Isolation by Construction, Not Policy

Every storage layer enforces isolation at the **driver/connection level**. The
application code never constructs a cross-org query — it is structurally unable
to do so because the connection itself is org-scoped.

### Layer-by-Layer Isolation

#### PostgreSQL — Row-Level Security (RLS)

```sql
-- Every table with org_id has RLS enabled
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;

-- RLS policy: the application DB user can ONLY see rows
-- matching the org_id set in the session variable
CREATE POLICY org_isolation ON repositories
    USING (org_id = current_setting('app.org_id')::UUID);

-- The application database user does NOT have BYPASSRLS privilege.
-- RLS policies are set by the DBA role (migration user).
-- The application user CANNOT alter or bypass RLS.
```

**Connection flow:**
1. API Gateway extracts `org_id` from the authenticated JWT/API key.
2. Before executing ANY query, the database session sets:
   `SET LOCAL app.org_id = '{org_id}';`
3. All subsequent queries in that transaction are automatically filtered by RLS.
4. This is implemented in a SQLAlchemy session factory middleware — no individual
   query ever references `org_id` in a WHERE clause. RLS handles it.

#### Qdrant — Collection-per-Organization

```
Collection naming:  episodes_{org_id}
                    semantic_{org_id}

Connection factory: QdrantConnectionFactory.get_client(org_id) → QdrantClient
    - Client is pre-configured with collection name
    - No method exposes collection listing or cross-collection queries
    - Client wrapper has no "switch collection" API
```

- ONE Qdrant collection per org, per tier.
- The `MemoryEngine` receives only an org-scoped Qdrant client from the connection factory.
- There is no 'all-orgs' collection. The factory does not expose `list_collections()`.

#### Neo4j — Database-per-Organization (Phase C)

```
Connection string: bolt://neo4j-host:7687/org_{org_id}
```

- ONE Neo4j database per org (not namespace — full database).
- Cross-database queries are disabled at the Neo4j config level (`dbms.security.procedures.unrestricted` does NOT include cross-db procedures).

#### Redis — Key Prefix Enforcement

```
Key pattern:  {org_id}:working:{session_id}:{key}

Connection factory: RedisConnectionFactory.get_client(org_id) → OrgScopedRedis
    - All keys auto-prefixed with {org_id}:
    - FLUSHALL, FLUSHDB, DBSIZE, KEYS * are BLOCKED
    - SCAN operations are prefix-scoped via Lua wrapper
```

#### S3 / Object Store — Prefix Isolation

```
Bucket path:  s3://memoryos-commits/{org_id}/

IAM policy: arn:aws:s3:::memoryos-commits/{org_id}/*
    - Read/write only to own prefix
    - Cross-prefix copy/read blocked by IAM deny policy
```

#### Kafka — Topic-per-Organization

```
Topic name:   memory.commits.{org_id}

Consumer group: memoryos-worker-{org_id}
    - Consumer group ACLs restrict to own-org topic
    - No consumer can subscribe to another org's topic
```

### Connection Factory Pattern

All storage layer clients are obtained through org-scoped connection factories:

```python
class OrgScopedConnectionFactory(Protocol):
    """Produces org-isolated storage clients."""

    def postgres_session(self, org_id: UUID) -> AsyncSession:
        """Returns a session with RLS pre-configured for org_id."""
        ...

    def qdrant_client(self, org_id: UUID) -> OrgScopedQdrantClient:
        """Returns a Qdrant client locked to org's collections."""
        ...

    def redis_client(self, org_id: UUID) -> OrgScopedRedisClient:
        """Returns a Redis client with mandatory key prefixing."""
        ...

    def kafka_producer(self, org_id: UUID) -> OrgScopedKafkaProducer:
        """Returns a producer locked to org's topic."""
        ...
```

Application code NEVER directly creates database connections. The factory is
the only entry point. This is enforced by import linting (no direct SQLAlchemy
session creation outside `infra/`).

---

## Alternatives Considered

| Alternative                           | Pros                       | Cons                                             | Why Rejected                                  |
|---------------------------------------|----------------------------|--------------------------------------------------|-----------------------------------------------|
| Shared collections with org_id filter | Simpler ops, fewer resources | Single bug in filter → full breach               | Violates "by construction" requirement        |
| Separate databases per org (full)     | Maximum isolation           | Ops overhead at scale (100+ orgs = 100+ DBs)     | Qdrant/Neo4j use this; PG uses RLS instead    |
| Application-layer WHERE clause        | Easiest to implement        | Forgettable, bypassable, violates INV-04          | Explicitly prohibited by PRD                   |
| Schema-per-org in PostgreSQL          | Good isolation, single DB   | Migration complexity, connection pooling issues   | RLS is simpler and equally secure              |

---

## Consequences

### Positive
- Cross-tenant data access is structurally impossible — not just unlikely.
- No single code bug can expose another org's data (defense in depth).
- Audit-friendly: isolation is verifiable at the infrastructure level.

### Negative / Trade-offs
- Operational complexity: provisioning a new org requires creating Qdrant collections,
  Neo4j databases, Kafka topics, and S3 prefixes. Automated in org provisioning pipeline.
- Resource overhead: many small collections vs. one large one. Acceptable at
  current scale projections (hundreds of orgs, not millions).

### Risks
- RLS misconfiguration: mitigated by automated RLS verification in invariant test suite.
- Qdrant collection naming collision: mitigated by UUID-based org_id (collision probability negligible).

---

## Rollback / Migration

This decision is foundational and difficult to reverse. If RLS proves insufficient:
1. Migrate to schema-per-org (requires data migration).
2. The connection factory pattern remains valid — only the factory internals change.
3. Application code is unaffected.

---

## Validation

### Phase A Exit Criteria (automated — must pass):
- **Isolation test**: Create Org A and Org B. Write memories to both. Attempt to
  retrieve Org A's memories using Org B's credentials. Must return zero results under
  ALL API call patterns (direct, time-travel, list, search).
- **RLS bypass test**: Attempt to query without setting `app.org_id` session variable.
  Must raise an error, not return unfiltered results.
- **Qdrant isolation test**: Attempt to search a collection named for a different org.
  Must fail at the connection factory level.

### Phase C Exit Criteria:
- **External penetration test** by approved security firm focusing specifically on
  tenant isolation (OWASP ASVS Level 3 tenant isolation suite). Zero critical/high findings.

---

## References

- PRD v2.1 §3.4 (Tenant Isolation — Construction-Level Guarantees)
- PRD v2.1 §2.5 (INV-04)
- PRD v2.1 §10.4 (TENANT_ISOLATION_BREACH_SUSPECTED alert)
- PRD v2.1 §13.2 (Security Gate — External Penetration Test)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/16/ddl-rowsecurity.html)

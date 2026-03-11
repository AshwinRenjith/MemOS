# MemoryOS Threat Model v1

> Initial threat model for MemoryOS. Updated per phase.
> See PRD §7 (Security), §8 (Privacy), §10.4 (Alerts).

---

## 1. System Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRUST BOUNDARY                           │
│                                                                 │
│  Agent SDK ──────┐                                              │
│                  ▼                                              │
│  User Dashboard → Memory Gateway (FastAPI) → PostgreSQL         │
│                       │         │            Qdrant             │
│                       │         │            Neo4j (Phase C)     │
│                       │         │            Redis              │
│                       │         └→ Kafka → memory-worker        │
│                       │                                         │
│  External LLM APIs ←──┘  (Cloud profile only)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Threat Categories

### T1 — Memory Poisoning (CRITICAL)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Malicious agent or user injects false, misleading, or manipulative memories to corrupt agent knowledge. |
| **Attack Vector**| Write API with crafted content designed to override system prompts, inject false facts, or manipulate agent behavior. |
| **Impact**      | Agent acts on poisoned knowledge. Cascading trust corruption across multi-agent swarms. Potential liability. |
| **PRD Reference**| §1.2 JTBD-4, §6.1 (Sandbox Branch), §9.1 (Intent Classifier ≥95% block rate) |
| **Mitigations** | 1. Intent Classifier at write path (Phase B) — blocks/sandboxes suspicious content. |
|                 | 2. `.memignore` rules block known attack patterns (§8.2). |
|                 | 3. Sandbox branch for uncertain writes — quarantine before merge. |
|                 | 4. Provenance tracking — every memory traces back to source. |
|                 | 5. LOCAL_KEY agents cannot auto-merge to main (ADR-0002). |
| **Residual Risk**| Novel attack patterns not in training set. Mitigated by active learning (§9.3). |

### T2 — Tenant Isolation Breach (CRITICAL)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Organization A accesses Organization B's memory data.        |
| **Attack Vector**| SQL injection, IDOR, misconfigured RLS, cross-collection Qdrant query, API parameter manipulation. |
| **Impact**      | Complete loss of enterprise trust. Regulatory violation. Potential data breach notification requirements. |
| **PRD Reference**| §3.4, §2.5 (INV-04), §10.4 (TENANT_ISOLATION_BREACH_SUSPECTED) |
| **Mitigations** | 1. RLS on all PostgreSQL tables (ADR-0003). |
|                 | 2. Collection-per-org in Qdrant. |
|                 | 3. Database-per-org in Neo4j. |
|                 | 4. Key-prefix isolation in Redis. |
|                 | 5. Topic-per-org in Kafka. |
|                 | 6. OrgScopedConnectionFactory — no direct DB access. |
|                 | 7. External penetration test (Phase C exit criterion). |
| **Residual Risk**| Bug in connection factory. Mitigated by invariant tests + pentest. |

### T3 — Key Compromise (HIGH)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Agent's private signing key is extracted or stolen.          |
| **Attack Vector**| Memory dump of agent process, disk access to plaintext key, side-channel attack on LOCAL_KEY agents. |
| **Impact**      | Attacker can forge commits impersonating the agent. Historical audit trail integrity questioned. |
| **PRD Reference**| §7.1 (Key Custody), §7.3 (Compromise Response) |
| **Mitigations** | 1. Three-tier custody model — HOSTED_KMS has no key material exposure. |
|                 | 2. LOCAL_KEY restricted (Phase B): no auto-merge, human review required. |
|                 | 3. Key revocation propagates within 30 seconds. |
|                 | 4. Compromised key triggers SECURITY_ALERT, all sessions invalidated. |
|                 | 5. Historical commits flagged, not deleted (INV-06). |
| **Residual Risk**| HOSTED_KMS compromise (cloud provider breach). Mitigated by CUSTOMER_KMS option (Phase D). |

### T4 — Commit Tampering (HIGH)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Attacker modifies historical commit records to alter the memory audit trail. |
| **Attack Vector**| Direct database access (compromised credentials), application bug that bypasses immutability rules. |
| **Impact**      | Loss of audit trail integrity. Regulatory non-compliance. Inability to verify agent decision history. |
| **PRD Reference**| §2.5 (INV-06), §5.1 (append-only rules) |
| **Mitigations** | 1. PostgreSQL rules: `no_update_commits`, `no_delete_commits`. |
|                 | 2. Application role cannot UPDATE or DELETE commits. |
|                 | 3. Every commit cryptographically signed — tamper detectable via signature verification. |
|                 | 4. S3 Object Lock for cold commit storage (Phase C). |
| **Residual Risk**| DBA role compromise. Mitigated by access controls, audit logging, SOC 2 controls. |

### T5 — Privilege Escalation (MEDIUM)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | DEVELOPER or VIEWER role performs OWNER/ADMIN-restricted operations. |
| **Attack Vector**| Missing RBAC check on endpoint, parameter tampering, JWT manipulation. |
| **Impact**      | Unauthorized rollbacks, key management, repository deletion, legal hold manipulation. |
| **PRD Reference**| §7.2 (RBAC Permission Matrix) |
| **Mitigations** | 1. RBAC check at API gateway layer (middleware). |
|                 | 2. Automated RBAC allow/deny tests for every matrix cell (Phase B). |
|                 | 3. JWT claims validated on every request. |
| **Residual Risk**| Missing RBAC test for new endpoint. Mitigated by CI RBAC test suite. |

### T6 — Data Exfiltration via Retrieval (MEDIUM)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Authorized user crafts retrieval queries to systematically extract all stored memories. |
| **Attack Vector**| Broad queries with high token_budget, iterative retrieval to map full knowledge base. |
| **Impact**      | Bulk data export bypassing intended access patterns. IP theft if public marketplace is active. |
| **Mitigations** | 1. Rate limiting per org per endpoint (§4.1). |
|                 | 2. Token budget cap (8000 max). |
|                 | 3. Retrieval audit logging — anomalous patterns trigger alert. |
|                 | 4. Per-org spending caps limit compute abuse. |
| **Residual Risk**| Slow-and-low exfiltration over many days. Mitigated by aggregate usage monitoring. |

### T7 — Denial of Service via Write Amplification (MEDIUM)

| Attribute       | Detail                                                       |
|-----------------|--------------------------------------------------------------|
| **Threat**      | Runaway agent or malicious user floods write API to exhaust resources. |
| **Attack Vector**| Agent in infinite loop creating excessive writes. Bulk write attack. |
| **Impact**      | Kafka lag spike, Qdrant resource exhaustion, elevated costs, degraded service for other tenants. |
| **PRD Reference**| §11.3 (Kill-Switch Policies), §10.4 (KAFKA_LAG_HIGH alert) |
| **Mitigations** | 1. Per-org rate limiting. |
|                 | 2. Per-org spending caps (§11.3). |
|                 | 3. Anomalous agent auto-rate-limit (§11.3). |
|                 | 4. Kill-switch: suspend agent pending investigation. |
| **Residual Risk**| Coordinated multi-agent attack from same org. Mitigated by org-level cap. |

---

## 3. Trust Boundaries

| Boundary                    | Controls                                       |
|-----------------------------|-------------------------------------------------|
| External → Memory Gateway   | TLS 1.3, JWT/API key auth, rate limiting         |
| Gateway → PostgreSQL        | RLS, parameterized queries, app role (no bypass) |
| Gateway → Qdrant            | OrgScopedConnectionFactory, collection isolation |
| Gateway → Redis             | Prefix-scoped client, restricted commands         |
| Gateway → Kafka             | Topic-per-org, ACL-scoped producer                |
| Gateway → External LLM API  | TLS, API key rotation, cost monitoring           |
| Service → Service           | mTLS (Istio), service mesh identity               |

---

## 4. Review Schedule

| Phase    | Threat Model Review Action                              |
|----------|---------------------------------------------------------|
| Phase 0  | Initial threat model (this document)                    |
| Phase A  | Review after tenant isolation implementation            |
| Phase B  | Add intent classifier + RBAC threats. Tabletop exercise.|
| Phase C  | External penetration test. Update based on findings.    |
| Phase D  | Sovereign profile review. Air-gap threat analysis.      |

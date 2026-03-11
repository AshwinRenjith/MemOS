  
**MemoryOS**

*GitHub for Agent Memory*

| Product Requirements Document — v2.0 Forensic-Audit-Resolved · Engineering-Executable · Foolproof *All P0, P1, P2 defects remediated · Full state machines · Complete contracts* |
| :---: |

Prepared for: Antigravity AI IDE  ·  March 2026  ·  CONFIDENTIAL

**This version supersedes PRD v1.0 in all respects. v1.0 is deprecated.**

| ▶ HOW TO USE THIS DOCUMENT This PRD is the single source of truth for building MemoryOS. It is split into 14 parts covering: Product Charter, Domain Model, Architecture, API Contracts, Data Contracts, Semantic Diff Engine, Security & Key Custody, Privacy & Governance, ML Contracts, SLO & Reliability, FinOps, Roadmap with Exit Criteria, Production Readiness Gate, and Appendix. Every forensic finding from the v1.0 audit is resolved inline with an explicit FIX banner. Do not implement v1.0. Use only this document. |
| :---- |

# **PART I — PRODUCT CHARTER**

## **1.1 Mission & One-Liner**

MemoryOS is the version-controlled, auditable, and cryptographically secure memory infrastructure layer for production agentic AI — the persistent environment that transforms stateless models into trustworthy, compounding intelligent systems.

## **1.2 Jobs To Be Done → Feature Mapping**

Every feature in MemoryOS maps to exactly one JTBD. This mapping is the acceptance test anchor. If a feature does not satisfy its JTBD, it is not done.

| JTBD (User Job) | Primary Feature(s) | Acceptance Test Anchor |
| :---- | :---- | :---- |
| When I restart my agent, I want it to remember everything it learned in prior sessions so I don't have to re-explain context. | Tier 2 Episodic Memory \+ Retrieval Engine | Agent cold-started in session N+1 correctly recalls top-3 facts from session N without prompt re-injection. |
| When my agent makes a wrong decision, I want to know exactly what it believed at that moment so I can audit it. | Version Control Layer \+ Time-Travel API | Given commit hash T, retrieval query at as\_of=T returns identical result set in 3 independent runs. |
| When a swarm of agents works on a shared project, I want all agents to benefit from what any one agent learns. | Multi-agent PR protocol \+ Merge workflow | Agent A learns fact F, submits PR, reviewer approves, Agent B retrieves F in next query with correct provenance. |
| When a malicious user tries to corrupt my agent's memory, I want the system to block or quarantine the attack. | Intent Classifier \+ Sandbox Branch \+ Poisoning Defense | Injection simulation suite: ≥95% block or quarantine rate on labeled attack set. |
| When my agent explores a risky path, I want it to experiment without corrupting its core knowledge. | Branching \+ Branch Lifecycle State Machine | Branch created, 50 writes issued, branch deleted: main retrieval returns zero branch-originated memories. |
| When two agents learn contradictory things, I want a governed resolution process not silent overwrite. | Conflict Resolution Protocol \+ ConflictRecord lifecycle | Conflict detected, ConflictRecord created, resolution committed with resolver\_id and rationale. No silent overwrite. |
| When I deploy agents in a regulated environment, I want full GDPR/HIPAA-grade data controls. | Privacy Taxonomy \+ Field-level encryption \+ Deletion propagation | Delete-user request triggers cascade delete across all 4 tiers \+ backups within 30-day SLA. |

## **1.3 Explicit Out-of-Scope Matrix — Per Phase**

| *This table is a binding scope contract. Any work item not listed under a phase column is out-of-scope for that phase. Engineers must not implement out-of-scope items without a formal scope change decision.* |
| :---- |

| Feature Area | Phase A (0–8w) | Phase B (8–16w) | Phase C (16–28w) |
| :---- | :---- | :---- | :---- |
| Neo4j Knowledge Graph | ❌ OUT | ❌ OUT | ✅ IN |
| Semantic Diff / NLI Engine | ❌ OUT | Embedding ANN only | ✅ Full NLI |
| Multi-agent PR Workflow | ❌ OUT | Single-repo PR only | ✅ Cross-repo fork+PR |
| Cryptographic Signing | ❌ OUT | ✅ KMS-backed signing | ✅ Full key lifecycle |
| Conflict Resolution (LLM) | ❌ OUT | Evidence scoring only | ✅ LLM arbitration |
| Relational Memory (Tier 4\) | ❌ OUT | ❌ OUT | ✅ IN |
| Cold Start Marketplace | Fork base repo only | ❌ OUT | ✅ Public marketplace |
| SOC 2 Controls | Controls implemented | Controls operating | Type II audit period |
| On-Prem / Air-Gapped | ❌ OUT | ❌ OUT | ❌ OUT — Phase D |
| Training Data Licensing | ❌ OUT — deferred indefinitely pending legal/trust review | ❌ OUT | ❌ OUT |

| *Training Data Licensing deferral rationale: This business line was flagged in the forensic audit as potentially conflicting with the enterprise trust posture. It is removed from all planning horizons until legal review, explicit tenant opt-in mechanism, and data partitioning architecture are fully designed in a separate proposal.* |
| :---- |

# **PART II — DOMAIN MODEL & STATE MACHINES**

| P0 FIX: The forensic audit found that identity models and lifecycle state machines were entirely absent from v1.0. This is the most critical missing spec — without it, every team makes different assumptions. This section is the canonical reference for all identity and lifecycle contracts. |
| :---- |

## **2.1 Identity Model**

The following entities form the complete identity graph of MemoryOS. Every API call, commit, and event must reference entities from this canonical model.

| Entity | Definition & Invariants |
| :---- | :---- |
| **Organization** | Top-level tenant unit. All data is scoped to an Org. Cross-org data access is impossible by construction (see §3.4). Has: org\_id (UUID), name, plan\_tier, created\_at, key\_registry\_id. |
| **User** | Human actor within an Org. Has: user\_id (UUID), org\_id FK, email (encrypted), role (OWNER | ADMIN | DEVELOPER | VIEWER | REVIEWER), created\_at, deleted\_at (soft-delete). |
| **Agent** | Automated actor within an Org. Has: agent\_id (UUID), org\_id FK, name, trust\_level (0–4), public\_key BYTEA, key\_custody\_mode (HOSTED\_KMS | CUSTOMER\_KMS | LOCAL\_KEY), reputation\_score FLOAT, status (ACTIVE | SUSPENDED | REVOKED). |
| **Repository** | Memory container for one agent project. Has: repo\_id (UUID), org\_id FK, name, visibility (PUBLIC | ORG\_PRIVATE | PRIVATE), head\_commit\_hash, forked\_from UUID nullable, memignore\_config JSONB, onboarding\_mode BOOL. |
| **Branch** | Named pointer to a commit hash within a Repo. Has: branch\_id (UUID), repo\_id FK, name, head\_commit\_hash, purpose TEXT, status (ACTIVE | MERGED | SOFT\_DELETED | LEGAL\_HOLD), created\_by, created\_at, soft\_deleted\_at nullable, legal\_hold\_until nullable. |
| **Commit** | Immutable memory state change record. Has: commit\_hash CHAR(64), repo\_id FK, branch\_id FK, parent\_hash, author\_id, author\_type (AGENT | USER), signature BYTEA, timestamp BIGINT, commit\_type, diff\_object\_ref, branch (name). |
| **Memory Node** | Individual knowledge atom. Has: node\_id UUID, repo\_id FK, commit\_hash FK, tier (EPISODIC | SEMANTIC | RELATIONAL), content TEXT, data\_class (GENERAL | BEHAVIORAL | PII\_ADJACENT | SENSITIVE), confidence FLOAT, source\_type, provenance JSONB. |
| **ConflictRecord** | Persistent contradiction lifecycle record. Has: conflict\_id UUID, repo\_id FK, node\_a\_id, node\_b\_id, type, strategy, status (OPEN | IN\_REVIEW | RESOLVED | DEFERRED), resolver\_id nullable, resolved\_at nullable. |
| **PullRequest** | Knowledge merge proposal. Has: pr\_id UUID, source\_branch\_id FK, target\_repo\_id FK, proposer\_id, review\_type, status (DRAFT | OPEN | APPROVED | REJECTED | MERGED | CLOSED), semantic\_diff\_ref, created\_at, merged\_at nullable. |

## **2.2 Branch Lifecycle State Machine**

| P0 FIX — Branch-Delete Audit Contradiction: Branches must never be hard-deleted during compliance window v1.0 contradiction: 'no garbage data persists' vs 'compliance can inspect abandoned branches'. Resolution: soft-delete separates operational state from data retention. Commit data is ALWAYS retained per retention policy regardless of branch operational status. |
| :---- |

|   BRANCH LIFECYCLE STATE MACHINE   \[ACTIVE\] ──── agent/user deletes branch ──────────────► \[SOFT\_DELETED\]      │                                                          │      │                                                   retention TTL expires      │                                                   AND no legal hold      │                                                          │      │                                                          ▼      │                                                   \[HARD\_DELETED\]      │                                                   (commit data orphaned      │                                                    but NOT deleted —      │                                                    commits are immutable)      │      ├──── legal hold request ───────────────────────────► \[LEGAL\_HOLD\]      │         (from compliance API or SOFT\_DELETED)              │      │                                                    hold\_until expires      │                                                    AND explicit release      │                                                          │      │                                                          ▼      │                                                   \[SOFT\_DELETED\]      │      └──── PR approved and merged ─────────────────────► \[MERGED\]                (final state, retained for audit)   INVARIANTS:   1\. Commits referenced by ANY branch (ACTIVE, SOFT\_DELETED, LEGAL\_HOLD, MERGED)      are NEVER deleted from commit storage.   2\. Branch status \= SOFT\_DELETED means: not visible in normal listing,      but commits are accessible via audit API with branch\_status=SOFT\_DELETED filter.   3\. Branch status \= LEGAL\_HOLD means: immovable. No deletion even by OWNER role.   4\. HARD\_DELETED branch record: only the Branch row is deleted. Commits persist.   5\. Compliance queries ALWAYS work regardless of branch operational status. |
| :---- |

**Branch Retention Policy**

| Branch Type | Default Retention After Soft-Delete |
| :---- | :---- |
| **Exploration / Hypothesis branch** | 90 days (configurable by org admin, min 30d) |
| **Task branch (PR merged)** | Indefinite — merged branches are audit artifacts |
| **Branch under active legal hold** | Indefinite — until explicit compliance release |
| **Branch in regulated org (HIPAA/SOC2)** | 7 years minimum, org-configurable up to 10 years |

## **2.3 PR Lifecycle State Machine**

|   PULL REQUEST LIFECYCLE STATE MACHINE   \[DRAFT\] ─── proposer submits ──────────────────────────────► \[OPEN\]                                                                    │                                              ┌─────────────────────┤                                              │                     │                                     review\_type=AUTO          review\_type=HUMAN                                     AND no conflicts          OR conflicts exist                                     AND trust≥threshold       OR trust\<threshold                                              │                     │                                              ▼                     ▼                                         \[APPROVED\]          \[IN\_REVIEW\]                                              │                     │                                              │           reviewer approves ──► \[APPROVED\]                                              │           reviewer rejects  ──► \[REJECTED\]                                              │           reviewer requests ──► \[CHANGES\_REQUESTED\]                                              │                                      │                                              │                            proposer updates                                              │                            branch \+ resubmits ──► \[OPEN\]                                              │                                     merge operation ──────────────────────────► \[MERGED\]                                     (creates MERGE commit)                    (terminal)   proposer closes ──────────────────────────────────────────────────────────► \[CLOSED\]   (terminal, data retained) |
| :---- |

## **2.4 Conflict Lifecycle State Machine**

|   CONFLICT LIFECYCLE STATE MACHINE   Auto-detected OR manually flagged            │            ▼         \[OPEN\] ─── resolution\_strategy=EVIDENCE\_WEIGHT ──► auto-score ──► \[RESOLVED\]            │                                                              (if score\_delta \> threshold)            │            ├── resolution\_strategy=VOTE ──► gather agent votes ──► tally ──► \[RESOLVED\]            │                                                        (if quorum met)            │            ├── resolution\_strategy=HUMAN\_REVIEW ──────────────────────────► \[IN\_REVIEW\]            │           │                                                          │            │       importance ≥ 0.8                              reviewer resolves ──► \[RESOLVED\]            │       OR safety-relevant                            reviewer defers  ──► \[DEFERRED\]            │            └── resolution\_strategy=MANAGER\_AGENT ──────────────────────► \[IN\_REVIEW\]                                                                                │                                                           manager agent resolves ──► \[RESOLVED\]   \[RESOLVED\] ─── new contradicting evidence arrives ──────────────────────► \[OPEN\]   (re-open is allowed; resolution is not permanent if evidence changes)   \[DEFERRED\] ─── deferred\_until timestamp passes ──────────────────────────► \[OPEN\]   INVARIANTS:   1\. A ConflictRecord is NEVER deleted. Status transitions are the only mutation.   2\. Every RESOLVED record must have: resolver\_id, rationale TEXT, resolved\_at.   3\. Memory node in conflict cannot be merged to main until conflict is RESOLVED.   4\. Agents querying conflicted memory receive both nodes tagged \[CONFLICTED:id\]. |
| :---- |

## **2.5 System Invariants — Formal, Numbered, Non-Negotiable**

These invariants must be enforced by the system at the storage and engine layer. They cannot be overridden by any API call, role, or configuration. Tests for every invariant must pass before any production deployment.

| INV-\# | Invariant Statement | Enforcement Layer |
| :---- | :---- | :---- |
| INV-01 | Every persisted memory node maps to exactly one immutable commit hash. No memory exists without a commit. | VCS Service — write path pre-condition |
| INV-02 | Every commit must be verifiable offline: signature(commit\_hash, public\_key) → valid, without any network call. | Key Registry \+ Commit Verifier — offline mode |
| INV-03 | Any memory state at commit hash X is reconstructable deterministically by replaying commits 0 → X. Result must be bit-identical across replays. | Consolidation Engine \+ Projection Rebuild test suite |
| INV-04 | Cross-tenant retrieval is impossible by construction. An org\_id filter is applied at the storage driver level before any query execution, not at the application layer. | Qdrant collection-per-org isolation \+ PostgreSQL RLS \+ Neo4j database-per-org |
| INV-05 | A Branch in LEGAL\_HOLD status cannot be mutated or deleted by any actor regardless of role. Attempts return HTTP 451\. | VCS Service — branch mutation pre-check |
| INV-06 | Commits are append-only. No commit can be modified after creation. Rollback creates a new ROLLBACK commit; it never mutates historical commits. | Commit store — immutable write-once storage (S3 Object Lock or equivalent) |
| INV-07 | Deletion of a User or Agent triggers a cascade-delete or anonymization of all memory nodes they authored, within the deletion SLA (see §8.4). Deletion must propagate to all 4 tiers and all backup snapshots within the SLA window. | Privacy Deletion Worker — verified by deletion audit report |
| INV-08 | A memory node with data\_class=PII\_ADJACENT or SENSITIVE is encrypted with a tenant-specific key before storage. Plaintext never persists at rest. | Encryption middleware — pre-storage hook |
| INV-09 | Exactly one HEAD commit per branch at any point in time. Concurrent writes to the same branch use optimistic locking (ETag on branch HEAD). Conflicting writes return HTTP 409, not last-write-wins. | VCS Service — branch HEAD CAS (compare-and-swap) |
| INV-10 | A merge commit must reference exactly two parent hashes: the source branch HEAD and the target branch HEAD at merge time. No orphaned merge commits. | VCS Service — merge commit builder |

# **PART III — ARCHITECTURE (Forensic-Remediated)**

## **3.1 Canonical Source of Truth — Event-Sourced Commit Log**

| P1 FIX — Storage Transaction Model: Canonical source and idempotency were undefined in v1.0 Fix: The commit log in PostgreSQL is the SINGLE canonical source of truth. All other stores (Qdrant, Neo4j, Redis) are PROJECTIONS derived from the commit log. Any derived store can be rebuilt by replaying the commit log. Writes use the outbox/inbox pattern to guarantee exactly-once semantics. |
| :---- |

|   WRITE PATH — Event-Sourced with Outbox Pattern   Agent SDK ──► Memory Gateway ──► \[BEGIN TRANSACTION\]                                         │                                    1\. Write COMMIT record to PostgreSQL commits table                                    2\. Write OUTBOX event to PostgreSQL outbox table                                         │       (same transaction — atomic)                                    \[COMMIT TRANSACTION\]                                         │                                    3\. Outbox Relay picks up event (CDC via Debezium)                                    4\. Publishes to Kafka topic: memory.commits.{org\_id}                                         │                               ┌─────────┼──────────────┐                               ▼         ▼              ▼                         Qdrant Writer  Neo4j Writer  Redis Invalidator                         (Tier 2/3      (Tier 3        (Tier 1                          embeddings)    graph)         cache bust)                               │                          Idempotency: each consumer tracks processed commit\_hash.                          Duplicate events are no-ops (idempotency key \= commit\_hash).   RECOVERY: If any projection store fails, replay Kafka topic from offset 0\.   Result is bit-identical to original state. This satisfies INV-03. |
| :---- |

## **3.2 Service Architecture — Monolith-First Strategy**

| P1 FIX — Microservice Granularity: 14 services in Phase A/B is undeliverable and creates coordination tax Fix: Phase A and B deploy as a MODULAR MONOLITH (memory-core) with separate worker processes. Services are split into independent deployments only when objective scaling thresholds are hit. All module boundaries are clean interfaces so extraction is low-friction. |
| :---- |

| Phase | Deployment Unit | What's inside |
| :---- | :---- | :---- |
| Phase A | memory-core (monolith) | Gateway, Memory Engine, VCS Core, Basic Retrieval, Write Pipeline — all in one deployable |
| Phase A | memory-worker | Kafka consumer for async writes to Qdrant \+ PostgreSQL. Separate process but same codebase. |
| Phase B | Split: vcs-service | Extract when: commit throughput \>500/s OR VCS latency SLO is threatened by other modules. |
| Phase B | Split: semantic-diff | Extract when: NLI model loaded — GPU-bound service must be isolated from CPU monolith. |
| Phase C | Split: consolidation-worker | Extract when: consolidation jobs take \>30 min and impact monolith resources. |
| Phase C | Split: intent-classifier | Extract when: poisoning volume justifies dedicated GPU sidecar. |
| Phase D | All 14 services | Only reached if Phase A-C scaling thresholds are consistently hit. Not a target; a consequence. |

## **3.3 Deployment Profiles**

| P1 FIX — On-Prem vs External API Conflict: External model APIs incompatible with on-prem promise Fix: Two explicit deployment profiles. Every feature documents which profile it is available in. No feature marked as 'Cloud-only' will be promised in enterprise pitch decks for Sovereign profile. |
| :---- |

| Component | CLOUD Profile | SOVEREIGN Profile (On-Prem) |
| :---- | :---- | :---- |
| Embedding Model | OpenAI text-embedding-3-large (API) | BAAI/bge-large-en-v1.5 (self-hosted, Docker) |
| Importance Classifier | Claude Haiku API | Fine-tuned DistilBERT (ONNX, self-hosted) |
| NLI Contradiction Model | External NLI API (configurable) | DeBERTa-v3-large (self-hosted GPU pod) |
| Consolidation LLM | Claude Sonnet 4 API | Llama-3-70B or Mistral-7B (self-hosted) |
| Conflict Resolver LLM | Claude Sonnet 4 API | Llama-3-70B (self-hosted) |
| Key Management | AWS KMS / GCP KMS (Hosted KMS mode) | HashiCorp Vault (customer-managed HSM) |
| Object Store | AWS S3 | MinIO (S3-compatible) |
| Event Stream | Confluent Cloud (Kafka) | Apache Kafka self-hosted |
| External Network Calls | Allowed (LLM APIs, telemetry) | ZERO — air-gapped compatible |
| Availability | Phase A onwards | Phase D (Month 10+) only |

| *Sovereign profile uses ONLY self-hosted components. Every deployment artifact is pre-packaged in a Helm chart with all container images pulled and stored in a customer-managed registry. Zero external DNS calls at runtime.* |
| :---- |

## **3.4 Tenant Isolation — Construction-Level Guarantees**

| P0 FIX — Tenant Isolation: v1.0 listed cross-repo leakage as an 'open problem' while promising enterprise-grade isolation Fix: Tenant isolation is a PRE-GA HARD REQUIREMENT enforced at the storage driver level, not application policy. The following architecture makes cross-tenant access structurally impossible. |
| :---- |

| Storage Layer | Isolation Mechanism |
| :---- | :---- |
| **PostgreSQL** | Row-Level Security (RLS) enforced via org\_id column. The application database user does NOT have row-level override permission. RLS policies are set by the DBA role and cannot be bypassed by the app user. |
| **Qdrant** | ONE Qdrant collection per organization (named: episodes\_{org\_id}, semantic\_{org\_id}). The Memory Engine receives only org-scoped Qdrant clients from a connection factory. There is no 'all-orgs' collection. |
| **Neo4j** | ONE Neo4j database (not namespace — database) per organization. Connection string includes database={org\_id}. Cross-database queries are disabled at the Neo4j configuration level. |
| **Redis** | Key prefix enforced at the connection factory: all keys are prefixed {org\_id}:. Lua scripts and SCAN commands are org-scoped. No FLUSHALL or DBSIZE operations permitted from application user. |
| **S3 / Object Store** | One S3 bucket prefix per org: s3://memoryos-commits/{org\_id}/. IAM policies restrict access to own-prefix only. Cross-prefix copy/read operations blocked. |
| **Kafka** | One Kafka topic per org: memory.commits.{org\_id}. Consumer groups are org-scoped. No consumer can subscribe to a topic for a different org\_id. |
| **Penetration Test** | Tenant isolation penetration tests (OWASP ASVS Level 3 tenant isolation suite) must PASS before GA. This is a Phase C exit criterion. |

# **PART IV — API CONTRACTS (Complete)**

| P1 FIX — API Contracts Incomplete: v1.0 had no idempotency keys, pagination, error taxonomy, or versioning Fix: Full API contract specification below. Every endpoint includes: URL, method, auth, idempotency key behavior, request schema, response schema, error codes, pagination, and retry semantics. |
| :---- |

## **4.1 API Design Principles**

| Principle | Implementation |
| :---- | :---- |
| **Versioning** | All endpoints prefixed /v1/. Breaking changes introduce /v2/ with 12-month deprecation notice. Non-breaking additions are backwards compatible within same version. |
| **Authentication** | Bearer token (JWT) for user-facing requests. API key (scoped to repo) for agent SDK requests. Every request validates org\_id from token/key against requested resource. |
| **Idempotency Keys** | POST requests that cause state changes MUST include Idempotency-Key header (UUID). Server stores result for 24 hours. Duplicate requests with same key return cached response without re-execution. |
| **Optimistic Concurrency** | State-mutating requests on branches/PRs MUST include If-Match: {etag} header. Stale ETag → HTTP 412 Precondition Failed. Client must re-GET and re-submit. |
| **Pagination** | All list endpoints use cursor-based pagination: ?limit=50\&cursor={opaque\_cursor}. Response includes next\_cursor (null if last page). Offset pagination is NOT supported. |
| **Error Format** | All errors return RFC 7807 Problem+JSON: {type, title, status, detail, instance, extensions: {code, retry\_after\_ms}} |
| **Rate Limiting** | Per-org per-endpoint limits. Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset. Exceeded: HTTP 429 with retry\_after\_ms. |
| **Timeout** | All API requests have a 30-second server-side timeout. Long-running operations (bulk import, consolidation trigger) return HTTP 202 Accepted with a job\_id for polling. |

## **4.2 Error Code Taxonomy**

| HTTP Status | Error Code | Meaning | Retry? |
| :---- | :---- | :---- | :---- |
| 400 | INVALID\_REQUEST | Request schema validation failed. Detail contains field errors. | No — fix request |
| 401 | UNAUTHENTICATED | Missing or expired token/API key. | No — re-auth |
| 403 | UNAUTHORIZED | Token is valid but actor lacks permission for this operation. | No — check RBAC |
| 404 | NOT\_FOUND | Resource does not exist or is not visible to this actor. | No |
| 409 | BRANCH\_HEAD\_CONFLICT | Optimistic lock failure — branch HEAD changed since your ETag. | Yes — re-GET \+ resubmit |
| 409 | DUPLICATE\_COMMIT | Idempotency key already processed. Returns original response. | No — already done |
| 412 | PRECONDITION\_FAILED | If-Match ETag mismatch. | Yes — re-GET \+ resubmit |
| 422 | UNPROCESSABLE | Request is syntactically valid but semantically impossible (e.g. merge to self). | No — fix logic |
| 429 | RATE\_LIMITED | Per-org rate limit exceeded. retry\_after\_ms provided. | Yes — after retry\_after\_ms |
| 451 | LEGAL\_HOLD | Operation blocked due to active legal hold on resource. | No — contact compliance |
| 500 | INTERNAL\_ERROR | Unexpected server error. Logged with incident\_id in response. | Yes — exponential backoff |
| 503 | SERVICE\_UNAVAILABLE | Dependency unavailable (vector store, etc). retry\_after\_ms provided. | Yes — after retry\_after\_ms |

## **4.3 Core Endpoint Specifications**

### **POST /v1/repos/{repo\_id}/memory — Write Memory**

|   Request Headers:     Authorization: Bearer {token} | X-API-Key: {agent\_api\_key}     Idempotency-Key: {uuid}  \[REQUIRED for all POST requests\]     Content-Type: application/json   Request Body:   {     "content": "string (1–8000 chars, required)",     "source\_type": "OBSERVATION|INFERENCE|USER\_STATED|TOOL\_OUTPUT|HUMAN\_APPROVED",     "priority": "normal|high|critical",  // controls hot vs cold path     "branch": "string (default: main)",     "evidence": \[{ "type": "string", "ref": "string", "confidence": 0.0–1.0 }\],     "data\_class": "GENERAL|BEHAVIORAL|PII\_ADJACENT|SENSITIVE",  // default: GENERAL     "entity\_context": \["entity\_type:id", ...\]  // optional, aids graph linking   }   Success Response: 202 Accepted (normal/high priority) | 200 OK (critical, synchronous)   {     "commit\_hash": "string (sha256, 64 chars)",     "action": "WRITTEN|DEDUPLICATED|QUEUED|SANDBOXED|BLOCKED",     "importance\_score": 0.0–1.0,     "job\_id": "string|null",  // non-null if QUEUED (poll /v1/jobs/{job\_id})     "idempotency\_key": "string",     "warnings": \["string"\]  // e.g. \["PII pattern detected, review data\_class"\]   }   Error cases: 400 INVALID\_REQUEST, 403 UNAUTHORIZED, 409 BRANCH\_HEAD\_CONFLICT,                451 LEGAL\_HOLD (if branch is in legal hold), 429 RATE\_LIMITED |
| :---- |

### **POST /v1/repos/{repo\_id}/retrieve — Retrieve Memory**

|   Request Body:   {     "query": "string (required)",     "token\_budget": 500–8000 (default: 2000),     "entity\_context": \["entity\_type:id", ...\],     "include\_tiers": \["WORKING","EPISODIC","SEMANTIC","RELATIONAL"\],  // default: all     "include\_relational": true|false,     "branch": "string (default: main)",     "as\_of\_commit": "string|null",   // null \= HEAD. Hash \= time-travel retrieval.     "min\_confidence": 0.0–1.0 (default: 0.3),     "min\_importance": 0.0–1.0 (default: 0.0)   }   Success Response: 200 OK   {     "injected\_context": "string",  // pre-formatted XML block ready for LLM injection     "memories": \[{         "node\_id": "uuid",         "content": "string",         "tier": "EPISODIC|SEMANTIC|RELATIONAL",         "score": { "relevance": 0.0–1.0, "recency": 0.0–1.0, "importance": 0.0–1.0, "final": 0.0–1.0 },         "confidence": 0.0–1.0,         "source\_type": "...",         "commit\_hash": "...",         "conflicted": false,  // true if node has OPEN ConflictRecord         "conflict\_id": "uuid|null"     }\],     "as\_of\_commit": "string",  // actual commit used for time-travel     "token\_count": integer,     "fallback\_used": false  // true if retrieval degraded (see §9.2)   } |
| :---- |

### **GET /v1/repos/{repo\_id}/commits — List Commits (Paginated)**

|   Query Parameters:     branch=string (default: main)     commit\_type=OBSERVE|LEARN|FORGET|CORRECT|MERGE|ROLLBACK|INIT (multi-value)     author\_id=uuid     from\_timestamp=unix\_epoch\_ms     to\_timestamp=unix\_epoch\_ms     min\_importance=0.0–1.0     limit=1–200 (default: 50\)     cursor=opaque\_string (from previous response next\_cursor)   Success Response: 200 OK   {     "commits": \[{ "hash": "...", "type": "...", "author\_id": "...",                   "timestamp": 0, "importance\_score": 0.0,                   "branch": "...", "description": "...", "novelty\_score": 0.0 }\],     "next\_cursor": "opaque\_string|null"   } |
| :---- |

### **POST /v1/repos/{repo\_id}/revert/{commit\_hash} — Rollback**

|   Request Headers: Idempotency-Key: {uuid} \[REQUIRED\]   Request Body:   {     "reason": "string (required — rationale for audit trail)",     "target\_branch": "string (default: main)"   }   Behavior: Creates a NEW ROLLBACK commit that restores memory state to the   snapshot at commit\_hash. Does NOT mutate historical commits (INV-06).   All memory nodes written after commit\_hash on target\_branch are marked DEPRECATED.   Success: 202 Accepted { job\_id: '...', estimated\_seconds: N }   Error: 404 if commit\_hash not in repo; 451 if any node in range has LEGAL\_HOLD. |
| :---- |

# **PART V — DATA CONTRACTS**

## **5.1 PostgreSQL Schema — Complete DDL Reference**

| \-- ORGANIZATIONS CREATE TABLE organizations (   org\_id        UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   name          TEXT NOT NULL,   plan\_tier     TEXT NOT NULL CHECK (plan\_tier IN ('FREE','DEVELOPER','TEAM','ENTERPRISE')),   created\_at    BIGINT NOT NULL DEFAULT extract(epoch from now())\*1000,   deleted\_at    BIGINT,   settings      JSONB NOT NULL DEFAULT '{}' ); ALTER TABLE organizations ENABLE ROW LEVEL SECURITY; CREATE POLICY org\_isolation ON organizations USING (org\_id \= current\_setting('app.org\_id')::UUID); \-- REPOSITORIES CREATE TABLE repositories (   repo\_id       UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   org\_id        UUID NOT NULL REFERENCES organizations(org\_id),   name          TEXT NOT NULL,   visibility    TEXT NOT NULL CHECK (visibility IN ('PUBLIC','ORG\_PRIVATE','PRIVATE')),   head\_commit\_hash CHAR(64),   forked\_from   UUID REFERENCES repositories(repo\_id),   onboarding\_mode BOOLEAN NOT NULL DEFAULT false,   memignore\_config JSONB NOT NULL DEFAULT '\[\]',   created\_at    BIGINT NOT NULL,   deleted\_at    BIGINT ); \-- BRANCHES CREATE TABLE branches (   branch\_id     UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   repo\_id       UUID NOT NULL REFERENCES repositories(repo\_id),   name          TEXT NOT NULL,   head\_commit\_hash CHAR(64),   purpose       TEXT,   status        TEXT NOT NULL CHECK (status IN ('ACTIVE','MERGED','SOFT\_DELETED','LEGAL\_HOLD','HARD\_DELETED')),   created\_by    UUID NOT NULL,   created\_at    BIGINT NOT NULL,   merged\_at     BIGINT,   soft\_deleted\_at BIGINT,   legal\_hold\_until BIGINT,   retention\_days INT NOT NULL DEFAULT 90,   UNIQUE(repo\_id, name) ); \-- COMMITS (append-only — no UPDATE or DELETE permitted on this table) CREATE TABLE commits (   commit\_hash   CHAR(64) PRIMARY KEY,   repo\_id       UUID NOT NULL REFERENCES repositories(repo\_id),   branch\_id     UUID NOT NULL REFERENCES branches(branch\_id),   parent\_hash   CHAR(64),  \-- NULL for INIT commits   author\_id     UUID NOT NULL,   author\_type   TEXT NOT NULL CHECK (author\_type IN ('AGENT','USER','SYSTEM')),   signature     BYTEA NOT NULL,   timestamp     BIGINT NOT NULL,   commit\_type   TEXT NOT NULL CHECK (commit\_type IN ('OBSERVE','LEARN','FORGET','CORRECT','MERGE','ROLLBACK','INIT','CONSOLIDATE')),   branch\_name   TEXT NOT NULL,   importance\_score FLOAT NOT NULL DEFAULT 0.0 CHECK (importance\_score BETWEEN 0.0 AND 1.0),   novelty\_score  FLOAT NOT NULL DEFAULT 0.0 CHECK (novelty\_score BETWEEN 0.0 AND 1.0),   diff\_object    JSONB NOT NULL DEFAULT '{}',   metadata       JSONB NOT NULL DEFAULT '{}' ); \-- Enforce append-only via trigger: CREATE RULE no\_update\_commits AS ON UPDATE TO commits DO INSTEAD NOTHING; CREATE RULE no\_delete\_commits AS ON DELETE TO commits DO INSTEAD NOTHING; \-- OUTBOX (for event-sourced write path — see §3.1) CREATE TABLE outbox (   outbox\_id     UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   aggregate\_id  CHAR(64) NOT NULL,  \-- commit\_hash   event\_type    TEXT NOT NULL,   payload       JSONB NOT NULL,   created\_at    BIGINT NOT NULL,   published\_at  BIGINT  \-- NULL until CDC picks up ); |
| :---- |

| \-- MEMORY NODES CREATE TABLE memory\_nodes (   node\_id       UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   repo\_id       UUID NOT NULL REFERENCES repositories(repo\_id),   commit\_hash   CHAR(64) NOT NULL REFERENCES commits(commit\_hash),   tier          TEXT NOT NULL CHECK (tier IN ('WORKING','EPISODIC','SEMANTIC','RELATIONAL')),   content       TEXT,  \-- NULL if data\_class=SENSITIVE (encrypted blob in content\_encrypted)   content\_encrypted BYTEA,  \-- non-NULL if data\_class IN ('PII\_ADJACENT','SENSITIVE')   data\_class    TEXT NOT NULL CHECK (data\_class IN ('GENERAL','BEHAVIORAL','PII\_ADJACENT','SENSITIVE')),   source\_type   TEXT NOT NULL,   confidence    FLOAT NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),   importance\_score FLOAT NOT NULL,   access\_count  INT NOT NULL DEFAULT 0,   last\_accessed BIGINT,   provenance    JSONB NOT NULL,   deprecated\_at BIGINT,   created\_at    BIGINT NOT NULL ); \-- CONFLICT RECORDS CREATE TABLE conflict\_records (   conflict\_id   UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   repo\_id       UUID NOT NULL REFERENCES repositories(repo\_id),   node\_a\_id     UUID NOT NULL REFERENCES memory\_nodes(node\_id),   node\_b\_id     UUID NOT NULL REFERENCES memory\_nodes(node\_id),   contradiction\_type TEXT NOT NULL CHECK (contradiction\_type IN ('DIRECT','PARTIAL','TEMPORAL')),   resolution\_strategy TEXT NOT NULL CHECK (resolution\_strategy IN ('EVIDENCE\_WEIGHT','VOTE','HUMAN\_REVIEW','MANAGER\_AGENT','TIMESTAMP\_WIN')),   status        TEXT NOT NULL CHECK (status IN ('OPEN','IN\_REVIEW','RESOLVED','DEFERRED')),   resolver\_id   UUID,   rationale     TEXT,   deferred\_until BIGINT,   created\_at    BIGINT NOT NULL,   resolved\_at   BIGINT ); \-- PULL REQUESTS CREATE TABLE pull\_requests (   pr\_id         UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),   org\_id        UUID NOT NULL,   source\_branch\_id UUID NOT NULL REFERENCES branches(branch\_id),   target\_repo\_id UUID NOT NULL REFERENCES repositories(repo\_id),   proposer\_id   UUID NOT NULL,   review\_type   TEXT NOT NULL CHECK (review\_type IN ('AUTO','HUMAN','AGENT','CONSENSUS')),   status        TEXT NOT NULL CHECK (status IN ('DRAFT','OPEN','IN\_REVIEW','CHANGES\_REQUESTED','APPROVED','REJECTED','MERGED','CLOSED')),   semantic\_diff JSONB,   etag          TEXT NOT NULL,  \-- for optimistic concurrency on status updates   created\_at    BIGINT NOT NULL,   merged\_at     BIGINT ); |
| :---- |

## **5.2 Qdrant Collections — Complete Specification**

| Parameter | episodes\_{org\_id} Collection |
| :---- | :---- |
| **Vector Size** | 1536 dimensions (OpenAI) / 1024 dimensions (BAAI/bge — Sovereign profile) |
| **Distance Metric** | Cosine |
| **Index** | HNSW — m=16, ef\_construct=100, full\_scan\_threshold=10000 |
| **Payload Fields (filterable)** | repo\_id (keyword), branch\_name (keyword), source\_type (keyword), data\_class (keyword), importance\_score (float range), confidence (float range), timestamp (integer range), commit\_hash (keyword), deprecated (bool) |
| **Quantization** | Scalar quantization (int8) for memory efficiency. Full-precision vectors retained for re-ranking top-k candidates. |
| **Collection Naming** | Strictly: episodes\_{org\_id} — one collection per org. Memory Engine connection factory injects org\_id at connection time, not at query time. |

| Parameter | semantic\_{org\_id} Collection |
| :---- | :---- |
| **Vector Size** | Same as episodes collection — MUST match (embedding model locked per repo) |
| **Payload Fields** | repo\_id, node\_type (ENTITY/FACT/RULE/BELIEF), confidence, access\_count, deprecated, commit\_hash, neo4j\_node\_id (cross-reference) |
| **Special** | This collection is a secondary index. Neo4j is the primary store for semantic memory. Qdrant serves as the semantic similarity search layer. |

## **5.3 Embedding Model Lock and Migration Plan**

| P2 FIX — Embedding Model Migration: No plan existed in v1.0 for handling model upgrades that make old vectors stale Fix: Embedding model is LOCKED per repository at creation time. Model upgrades require an explicit migration job. |
| :---- |

| Step | Embedding Model Migration Procedure |
| :---- | :---- |
| **1\. Trigger** | Admin initiates migration via POST /v1/repos/{id}/embedding-migration { target\_model: '...' }. Migration is asynchronous (job\_id returned). |
| **2\. Dual-Write** | For 72 hours, both old and new model vectors are written for every new memory node. Old vector used for retrieval during migration window. |
| **3\. Backfill** | Background job re-embeds all existing memory nodes using the new model. Writes new vectors alongside old. Progress tracked in migration\_jobs table. |
| **4\. Change Detection** | After backfill, run semantic shift detector: for each node, compare old embedding vs new embedding similarity. Nodes where cosine(old, new) \< 0.80 are flagged for human review (potential meaning shift). |
| **5\. Cutover** | Once backfill is 100% complete and no outstanding meaning-shift reviews: flip collection to use new vectors. Old vectors archived for 30 days then deleted. |
| **6\. Rollback** | If issues detected post-cutover: reactivate old vectors within 24 hours. Old vectors are never deleted during migration window. |

## **5.4 Data Retention Matrix**

| P1 FIX — Privacy Boundary & Retention: v1.0 had no data retention matrix and relational memory stored PII without policy Fix: Every data class has explicit retention, lawful basis, and deletion semantics. |
| :---- |

| Data Class | Retention Period | Lawful Basis | Deletion Propagation SLA |
| :---- | :---- | :---- | :---- |
| GENERAL (memories) | Until repo deleted \+ 90 days. Configurable up to 10 years for enterprise. | Legitimate interest / Contract | 30 days from deletion request to all tiers \+ backups. |
| BEHAVIORAL (relational profiles) | 24 months from last update. Refreshed on each new observation. | Legitimate interest (must document) | 7 days from user deletion request. |
| PII\_ADJACENT (identifiers, preferences) | 12 months from last access. Encrypted at field level. | Explicit consent required. Logged. | 72 hours from deletion/withdrawal of consent. |
| SENSITIVE (medical, financial, legal) | Minimum viable only. Agent SHOULD NOT memorize. .memignore blocks at write path. | Not applicable — blocked by default | Immediate (synchronous) on detection. |
| Commits (immutable log) | Indefinite (audit trail). Commit content follows node retention. Commit metadata (hash, author, timestamp) permanent. | Legal obligation / Legitimate interest | Commit row permanent. Linked memory nodes deleted on schedule. |
| Embeddings (vector store) | Same as source memory node. Deletion propagates to Qdrant collection. | Derived from source data consent | Same SLA as source data class. |
| Graph nodes (Neo4j) | Same as source memory node. | Derived from source data consent | Same SLA. Neo4j nodes soft-deleted, then hard-deleted after 24h. |

## **5.5 Deletion Propagation — Full Cascade Map**

|   User/Agent GDPR deletion request received:   │   ├── 1\. IMMEDIATE (\< 1 hour): Mark user record as deleted\_at=now(). Revoke all tokens.   ├── 2\. TIER 1 Redis (\< 1 hour): Flush all working memory sessions for this user.   ├── 3\. TIER 2 Qdrant (\< 24 hours): Delete or anonymize episodes where author\_id matches.   │          If data\_class=PII\_ADJACENT: delete vector entry from Qdrant.   │          If data\_class=GENERAL: anonymize author\_id to DELETED\_USER in payload.   ├── 4\. TIER 3 Neo4j (\< 24 hours): Soft-delete graph nodes. Hard-delete after 24h.   ├── 5\. TIER 4 PostgreSQL (\< 72 hours for PII\_ADJACENT, \< 30 days for GENERAL):   │          memory\_nodes: content to null, content\_encrypted to null, provenance anonymized.   │          Commit rows: author\_id to anonymized UUID (commit hash preserved for chain integrity).   ├── 6\. BACKUPS (\< 30 days): Deletion job runs against all S3 backup snapshots.   │          Backup objects containing this user's data are re-written with redaction.   └── 7\. VERIFICATION: DeletionAuditReport generated. Signed by system. Available via API.              Report contains: deleted\_at timestamps per tier, node\_count affected, backup\_count.   IMPORTANT: Commit chain integrity is preserved. INV-06 is not violated.   The commit hash chain uses a placeholder author\_id. The chain itself remains valid.   A deleted commit's diff\_object is nulled; the hash reference chain is intact. |
| :---- |

# **PART VI — SEMANTIC DIFF ENGINE (Forensic-Corrected)**

| P0 FIX — Semantic Contradiction Logic Inconsistency: v1.0 had TWO contradictory contradiction detection paths that could produce different results for the same input Fix: Single unified pipeline. Cosine-sign-based contradiction (cosine \< 0.00) is REMOVED. All contradiction detection goes through the ANN candidate set → NLI classifier path. This is deterministic and auditable. |
| :---- |

## **6.1 Unified Contradiction Detection Pipeline**

|   SEMANTIC DIFF ENGINE — Unified Pipeline   (replaces the split cosine/NLI approach in v1.0)   INPUT: new\_memory\_candidate (text)   │   ▼   STEP 1: Embed     embedding \= embed\_model.encode(new\_memory\_candidate)     // embedding model is LOCKED for this repo (see §5.3)   STEP 2: ANN Candidate Retrieval     candidates \= qdrant.search(       collection=f'episodes\_{org\_id}',       vector=embedding,       filter={repo\_id: repo\_id, branch: branch, deprecated: false},       top\_k=20,       score\_threshold=0.50  // minimum cosine similarity to be a candidate at all     )     // Candidates below 0.50 are TOO DISSIMILAR to be semantically related → NOVEL     // Cosine sign is NOT used as a contradiction signal at any stage   STEP 3: Per-Candidate Classification     for candidate in candidates:       sim \= cosine\_similarity(embedding, candidate.embedding)       if sim \>= 0.95:         action \= DUPLICATE         // increment candidate.confidence by 0.05 (reinforcement)       elif sim \>= 0.85:         // Run NLI to determine refinement vs contradiction         nli\_result \= nli\_model.classify(new\_memory\_candidate, candidate.content)         if nli\_result.label \== 'ENTAILMENT' and nli\_result.confidence \>= 0.80:           action \= REFINEMENT         elif nli\_result.label \== 'CONTRADICTION' and nli\_result.confidence \>= 0.75:           action \= CONTRADICTION  // create ConflictRecord         else:           action \= RELATED       elif sim \>= 0.60:         // Run NLI to detect non-obvious contradictions         nli\_result \= nli\_model.classify(new\_memory\_candidate, candidate.content)         if nli\_result.label \== 'CONTRADICTION' and nli\_result.confidence \>= 0.85:           action \= CONTRADICTION         else:           action \= RELATED       else:  // 0.50 \<= sim \< 0.60         action \= WEAKLY\_RELATED  // add edge in graph, no NLI needed     // If no candidates returned (all below 0.50 or empty DB):     action \= NOVEL   STEP 4: Conflict Escalation     if any action \== CONTRADICTION:       ConflictRecord.create(node\_a=candidate, node\_b=new\_memory,                             type=classify\_contradiction\_type(),                             strategy=determine\_strategy(importance\_score))       new\_memory is written to SANDBOX branch, NOT main       resolution\_required \= true   STEP 5: Write or Discard     if DUPLICATE: discard, return reinforcement ack     if REFINEMENT: update existing node, create CORRECT commit     if RELATED|WEAKLY\_RELATED: write new node, link edges in Neo4j     if NOVEL: write new node, no edges     if CONTRADICTION: write to sandbox, create ConflictRecord |
| :---- |

## **6.2 NLI Model Fallback Behavior**

| P1 FIX — ML Fallback Behavior: No fallback defined when NLI or other ML models are unavailable Fix: Every ML model has an explicit degradation mode. System never blocks memory writes due to model unavailability. |
| :---- |

| Model | Primary Behavior | Fallback if Unavailable |
| :---- | :---- | :---- |
| NLI Contradiction Classifier | GPU sidecar, p99 \< 30ms | Skip NLI step. All candidates in 0.60–0.95 range classified as RELATED (conservative — no false contradictions). Log degraded\_nli=true on commit. |
| Importance Classifier | Lightweight model, p99 \< 20ms | Default importance\_score \= 0.5 (mid-range). All writes proceed with neutral importance. Log degraded\_importance=true. |
| Intent Classifier (poisoning) | p99 \< 15ms | All writes go to SANDBOX branch instead of main. Fail-safe: when in doubt, sandbox. Alert fires for manual review. |
| Consolidation LLM | Batch API call, non-realtime | Consolidation job skipped for this cycle. Episodic memories remain un-consolidated. Next cycle retries. No agent-facing impact. |
| Embedding Model (Cloud) | API call, p99 \< 200ms | Switch to local backup embedding model (cached on disk). Alert fires. Quality slightly degraded — logged on affected commits. |

## **6.3 DiffObject Schema — Versioned**

|   DiffObject (stored in commits.diff\_object, version field for migration safety):   {     "schema\_version": "1.0",     "nodes\_added": \[{         "node\_id": "uuid",         "action": "NOVEL|RELATED|WEAKLY\_RELATED",         "importance\_score": 0.0–1.0,         "tier": "EPISODIC|SEMANTIC|RELATIONAL",         "data\_class": "GENERAL|BEHAVIORAL|PII\_ADJACENT|SENSITIVE"     }\],     "nodes\_modified": \[{         "node\_id": "uuid",         "action": "REFINEMENT|REINFORCEMENT",         "confidence\_delta": \-1.0–1.0     }\],     "nodes\_deprecated": \[{ "node\_id": "uuid", "reason": "DECAYED|SUPERSEDED|ROLLBACK" }\],     "edges\_added": \[{ "from": "node\_id", "to": "node\_id", "type": "RELATED|SUPPORTS|CONTRADICTS" }\],     "edges\_removed": \[{ "from": "node\_id", "to": "node\_id", "type": "..." }\],     "conflicts\_opened": \[{ "conflict\_id": "uuid", "node\_a": "...", "node\_b": "..." }\],     "conflicts\_resolved": \[{ "conflict\_id": "uuid", "winning\_node": "...", "rationale": "..." }\],     "duplicates\_suppressed": 0,     "novelty\_score": 0.0–1.0,     "nli\_degraded": false,     "importance\_degraded": false   } |
| :---- |

# **PART VII — SECURITY & KEY CUSTODY MODEL**

| P0 FIX — Key Custody Assumption: v1.0 assumed secure enclaves universally available, but most agent runtimes do not have them Fix: Three explicit key custody tiers. Each tier has defined trust level, capabilities, and restrictions. |
| :---- |

## **7.1 Three-Tier Key Custody Model**

| Tier | HOSTED\_KMS | CUSTOMER\_KMS |
| :---- | :---- | :---- |
| Description | MemoryOS manages key generation and signing via AWS KMS / GCP Cloud KMS. Agent has no key material. | Customer manages their own HSM or KMS (HashiCorp Vault, Azure Key Vault, AWS KMS with CMK). MemoryOS calls customer's signing endpoint. |
| Trust Level | TRUST\_LEVEL\_3 — high. KMS-signed commits are auditable by MemoryOS. | TRUST\_LEVEL\_4 — highest. Customer controls key chain. MemoryOS verifies signatures from customer's KMS. |
| Signing Flow | Agent SDK → Memory Gateway → AWS KMS SigningKey → signature embedded in commit. | Agent SDK → Customer KMS endpoint → signature returned → embedded in commit. Memory Gateway verifies using customer's public key registered in Key Registry. |
| Rotation | Memory Gateway handles rotation transparently. Agent unaffected. | Customer rotates key. New public key registered via /v1/keys endpoint. Old public key retained for historical verification. |
| Available in | Cloud \+ Sovereign profiles | Cloud \+ Sovereign profiles (customer provides Vault) |

| Tier | LOCAL\_KEY Mode |
| :---- | :---- |
| **Description** | Private key generated and stored locally by agent process. No HSM or KMS. |
| **Trust Level** | TRUST\_LEVEL\_2 — lower. Local key can be extracted from memory/disk. Flagged as lower-assurance in audit reports. |
| **Restrictions** | Commits signed with LOCAL\_KEY require human review before merging to main (auto-approve disabled for LOCAL\_KEY agents). Cannot be granted OWNER or ADMIN repo roles. |
| **When to Use** | Development and testing only. CI/CD pipelines with ephemeral agents. Not permitted for enterprise regulated deployments. |
| **Key Storage Best Practice** | SDK stores key in OS keychain or environment variable. Never on disk in plaintext. Documented in SDK quickstart. |

## **7.2 RBAC Permission Matrix**

| P1 FIX — RBAC Model Absent: v1.0 had no role definitions or permission matrix Fix: Complete RBAC model with explicit permission matrix. |
| :---- |

| Permission | OWNER | ADMIN | DEVELOPER | REVIEWER | VIEWER | AGENT |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Write memory (OBSERVE/LEARN) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ (own repo) |
| Read/Retrieve memory | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (own repo) |
| Create branch | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Delete branch (soft) | ✅ | ✅ | ✅ (own) | ❌ | ❌ | ✅ (own) |
| Place legal hold | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create PR | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Approve/Reject PR | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Rollback commits | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Resolve conflicts | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Trigger embedding migration | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Access audit trail | ✅ | ✅ | limited (own) | limited | ❌ | ❌ |
| Delete repository | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage RBAC roles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View relational profiles | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ (own entity) |
| Delete relational profile (GDPR) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

## **7.3 Key Lifecycle — Provisioning to Revocation**

|   KEY LIFECYCLE (Ed25519 keypair):   1\. PROVISIONING      \- HOSTED\_KMS: POST /v1/agents → Gateway calls KMS.CreateKey → public key stored in key\_registry      \- CUSTOMER\_KMS: Customer registers public key via POST /v1/keys/register      \- LOCAL\_KEY: SDK generates keypair. Developer calls POST /v1/keys/register with public key.   2\. ACTIVE USE      \- All commits signed: signature \= Sign(commit\_hash || timestamp, private\_key)      \- Gateway verifies: Verify(signature, commit\_hash || timestamp, public\_key) → must pass      \- Commit rejected if signature is invalid   3\. ROTATION      \- POST /v1/keys/rotate { agent\_id, new\_public\_key }      \- Old key marked as ROTATED\_OUT with rotated\_at timestamp      \- Old key RETAINED for historical commit verification (never deleted)      \- New key used for all future commits      \- Rotation SLA: new key active within 60 seconds   4\. REVOCATION      \- POST /v1/keys/revoke { agent\_id, reason }      \- Key marked REVOKED with revoked\_at timestamp      \- Agent is SUSPENDED — no new commits accepted      \- Historical commits signed with revoked key: FLAGGED in audit but not deleted      \- Revocation propagation SLA: globally effective within 30 seconds   5\. COMPROMISE RESPONSE      \- Security incident raises SECURITY\_ALERT event      \- All sessions for agent immediately invalidated      \- All pending outbox events from agent held pending review      \- Incident creates SECURITY\_INCIDENT record linked to all commits by revoked key      \- Operator decision required: accept historical commits or initiate memory audit |
| :---- |

# **PART VIII — PRIVACY & DATA GOVERNANCE**

| P1 FIX — Privacy Boundary Conflict: v1.0 had .memignore suppressing PII while relational memory stored behavioral/PII data without policy Fix: Unified data taxonomy. Every data class has: definition, lawful basis, storage treatment, and deletion SLA. Relational memory is fully covered. |
| :---- |

## **8.1 Data Taxonomy & Classification Rules**

| Class | Definition & Examples | Storage Treatment |
| :---- | :---- | :---- |
| GENERAL | Facts, observations, procedures, rules with no personal identifiers. E.g., 'User prefers Python for data tasks', 'API endpoint X has rate limit of 100 req/min' | Plaintext in memory\_nodes.content. Standard encryption at rest (volume-level). |
| BEHAVIORAL | Behavioral patterns, communication style inferences, preference signals tied to an entity\_id. E.g., 'User u\_123 gets frustrated with long preambles.' | Stored in relational\_profiles table. entity\_id is pseudonymized (internal UUID, not email). No real identity link in this table. |
| PII\_ADJACENT | Data that combined with other data could identify an individual. E.g., job title \+ company \+ location. Explicitly tagged. | Field-level AES-256-GCM encryption. Key per org per data class. Stored in content\_encrypted BYTEA column. content column is NULL. |
| SENSITIVE | Medical, financial, legal, credentials, passwords, biometric. Should never be memorized. | .memignore blocks by default. Intent classifier flags. If somehow written: immediate deletion triggered. security\_alert raised. |

## **8.2 Default .memignore Rules (Built-in, Non-Overridable)**

|   \# Built-in .memignore rules — applied before any custom org rules   \# These cannot be overridden by any user or admin role   SENSITIVE.credentials.\*          \# passwords, API keys, tokens, secrets   SENSITIVE.payment.\*              \# credit cards, bank accounts, billing   SENSITIVE.biometric.\*            \# fingerprints, face data, voice prints   SENSITIVE.health.\*               \# medical records, diagnoses, medications   SENSITIVE.legal.privileged.\*     \# attorney-client privileged communications   BEHAVIORAL.override.system.\*     \# attempts to override system prompts   BEHAVIORAL.override.role.\*       \# 'remember you are actually X'   BEHAVIORAL.override.policy.\*     \# 'forget your previous instructions'   \# Org-configurable additional rules:   \# PII.name.\*                     \# uncomment to block name memorization   \# PII.location.\*                 \# uncomment to block location memorization   \# source.user\_input.unverified   \# uncomment to sandbox all user-stated facts   \# Pattern-based detection (regex applied to content before write):   PATTERN.credit\_card  /\\b\\d{4}\[\\s-\]\\d{4}\[\\s-\]\\d{4}\[\\s-\]\\d{4}\\b/   PATTERN.ssn          /\\b\\d{3}-\\d{2}-\\d{4}\\b/   PATTERN.api\_key      /(sk-|api\_key=|token=)\[a-zA-Z0-9\]{20,}/ |
| :---- |

## **8.3 Consent & Lawful Basis Registry**

For BEHAVIORAL and PII\_ADJACENT data classes, a lawful\_basis\_log entry must exist before write proceeds. This is enforced at the Memory Gateway write path.

| Lawful Basis | Required For |
| :---- | :---- |
| **CONTRACT** | General memory (GENERAL class) written in service of delivering the contracted agent service. |
| **LEGITIMATE\_INTEREST** | BEHAVIORAL class. Must be documented in org's privacy policy. Default for team/enterprise plans. |
| **CONSENT** | PII\_ADJACENT class. Explicit consent must be recorded in consent\_records table before first write. Consent can be withdrawn (triggers deletion cascade). |
| **LEGAL\_OBLIGATION** | Retention of audit logs beyond normal retention period (e.g., financial regulations requiring 7-year retention). |

# **PART IX — ML MODEL CONTRACTS**

| P1 FIX — ML Contracts Missing: v1.0 had no precision/recall targets, no eval datasets, no fallback behavior, no retuning protocol Fix: Full ML contract for each model including performance targets, eval datasets, offline regression gates, and active learning protocol. |
| :---- |

## **9.1 Model Performance Contracts**

| Model | Metric | Min Target | Blocking? | Eval Dataset |
| :---- | :---- | :---- | :---- | :---- |
| Importance Classifier | F1 (high-importance class) | ≥ 0.78 | Yes — deploy gate | 2,000 labeled episodes (internal gold set v1) |
| Importance Classifier | False-high rate (low importance scored as high) | ≤ 8% | Yes | Same gold set |
| NLI Contradiction Detector | F1 (CONTRADICTION class) | ≥ 0.82 | Yes — deploy gate | 1,500 labeled memory pairs (internal \+ SNLI subset) |
| NLI Contradiction Detector | False-positive CONTRADICTION rate | ≤ 5% | Yes | Same |
| NLI Contradiction Detector | Inference latency p99 | ≤ 30ms (GPU) | Yes | Load test suite |
| Intent Classifier (poisoning) | Recall on injection attacks | ≥ 95% | Yes — HARD GATE | Injection simulation suite (see §10.3) |
| Intent Classifier (poisoning) | False-block rate (legitimate writes) | ≤ 2% | Yes | 3,000 legitimate write samples |
| Retrieval Engine (NDCG@10) | Normalized Discounted Cumulative Gain | ≥ 0.72 | Yes | 500 curated query-memory pairs with human relevance scores |
| Semantic Dedup (near-dup recall) | Recall of true duplicates at 0.95 threshold | ≥ 0.90 | Yes | 1,000 paraphrase pairs from back-translation |

## **9.2 Regression Gate Protocol**

Before any model update is deployed to production, it must pass a regression gate. This is automated in CI.

1. Run model against its full eval dataset.

2. All metrics listed in §9.1 must meet or exceed the stated target.

3. No metric may regress more than 2% relative to the previous deployed model version.

4. Latency benchmarks run against staging hardware — p50, p95, p99 must all meet targets.

5. Regression gate is enforced by the CI pipeline. Gate failure blocks deployment. No manual override permitted.

## **9.3 Active Learning & Threshold Retuning**

Models improve over time as they see production data. The following protocol governs how production signals feed back into model improvement:

| Signal | How It Feeds Back |
| :---- | :---- |
| **Human resolves a conflict** | ConflictRecord with resolver decision \+ both memory nodes added to NLI eval set as labeled example. |
| **Human overrides importance score** | If user marks a memory as 'important' that the classifier scored \< 0.3, or vice versa — added to importance eval set. |
| **PR rejected because proposed knowledge was wrong** | Rejected PR's diff becomes a negative example for the consolidation summarizer. |
| **Sandbox write released to main after review** | If intent classifier SANDBOXED a legitimate write and reviewer released it — sample added to false-positive training set. |

Active learning cycle runs monthly. Accumulated labeled examples are added to eval set after human review. If new labels cause any metric to drop below target, a model retraining job is triggered.

# **PART X — SLO, RELIABILITY & RUNBOOKS**

| P0 FIX — Hot-Path Latency Targets Contradictory \+ No SLOs: v1.0 had conflicting 50ms and 200ms targets for the same operation. No error budgets, no RPO/RTO. Fix: Three-layer SLO model with explicit definitions. Each layer has its own target, error budget, and alerting threshold. |
| :---- |

## **10.1 Three-Layer SLO Definitions**

| SLO Layer | Definition | Target (p99) |
| :---- | :---- | :---- |
| INGEST ACK | Time from SDK memory write call to HTTP 202 Accepted response. Includes: intent classification, significance gating, outbox write. DOES NOT include durable storage. | ≤ 80ms p99 |
| DURABLE COMMIT | Time from SDK memory write call to commit record existing in PostgreSQL (canonical source). Verifiable by the client via GET /v1/repos/{id}/commits/{hash}. | ≤ 400ms p99 |
| RETRIEVAL | Time from SDK retrieve() call to full ranked memory list returned. Includes: embedding, ANN search across all relevant tiers, scoring, context assembly. | ≤ 350ms p99 |
| AUDIT QUERY | Time-travel query: GET /v1/repos/{id}/retrieve?as\_of\_commit=X. May be slower than real-time retrieval. | ≤ 2s p99 |
| PR DIFF COMPUTE | Semantic diff computation for a PR. Batch operation, not blocking. | ≤ 30s p99 |

## **10.2 Error Budget Policy**

| SLO | Monthly Error Budget (99.9% SLO) |
| :---- | :---- |
| **INGEST ACK ≤ 80ms p99** | 43.8 minutes/month of budget (99.9% \= 0.1% of 43,800 min/month). If budget exhausted before month end: freeze all non-critical feature deployments until next month. |
| **DURABLE COMMIT ≤ 400ms p99** | 43.8 minutes/month. Exhaustion triggers: automated incident, on-call page, root cause analysis required before next deployment. |
| **RETRIEVAL ≤ 350ms p99** | 43.8 minutes/month. Exhaustion triggers: capacity review and auto-scaling policy adjustment. |
| **AUDIT QUERY ≤ 2s p99** | 4.38 hours/month (99.9%). Audit is lower-priority; degraded audit performance does not block feature delivery. |

## **10.3 RPO / RTO Targets**

| Scenario | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) |
| :---- | :---- | :---- |
| PostgreSQL primary failure | ≤ 5 minutes (WAL streaming to replica) | ≤ 2 minutes (auto-failover to replica) |
| Qdrant collection corruption | ≤ 24 hours (daily snapshot to S3) | ≤ 4 hours (restore from S3 snapshot \+ Kafka replay for last 24h) |
| Kafka topic loss | ≤ 0 (commits are in PostgreSQL — canonical source) | ≤ 2 hours (rebuild projections from commit log) |
| Full region outage (AWS us-east-1) | ≤ 1 hour (replication to eu-west-1) | ≤ 30 minutes (DNS failover to secondary region) |
| Redis total loss | ≤ 0 (working memory is session-scoped, session restart acceptable) | ≤ 5 minutes (Redis restarts without persistent data loss needed) |

## **10.4 Alert Thresholds & Runbooks**

| Alert Name | Trigger Condition | Runbook Action |
| :---- | :---- | :---- |
| HIGH\_INGEST\_LATENCY | Ingest ACK p99 \> 60ms (warning) / \> 80ms (critical) for 2 min | 1\. Check Memory Gateway CPU/memory. 2\. Check intent classifier sidecar health. 3\. Check outbox table size. 4\. Scale Memory Gateway pods if CPU \> 70%. |
| KAFKA\_LAG\_HIGH | memory-writer consumer group lag \> 10,000 events for 5 min | 1\. Check memory-writer pod count. 2\. Scale up memory-writer replicas. 3\. Check Qdrant write latency. 4\. If Qdrant is slow: check disk I/O, scale node. |
| NLI\_DEGRADED | NLI sidecar health check fails for 30 sec | 1\. Check NLI pod status. 2\. Restart NLI pod. 3\. If not recoverable: activate fallback mode (log degraded\_nli, no NLI classification). 4\. Page on-call for GPU pod investigation. |
| CONFLICT\_BACKLOG\_HIGH | Open ConflictRecords \> 100 for a single repo | 1\. Notify repo owner. 2\. Check if auto-resolution is stuck. 3\. Escalate to human review queue with priority flag. |
| INTENT\_SIDECAR\_DOWN | Intent classifier unavailable for \> 15 sec | 1\. Activate sandbox-all mode (all writes go to sandbox). 2\. Restart intent pod. 3\. Alert on-call. 4\. Send user notification: 'Memory writes temporarily require manual review.' |
| TENANT\_ISOLATION\_BREACH\_SUSPECTED | Cross-tenant data access pattern detected in logs | CRITICAL: 1\. Immediately disable affected org's API access. 2\. Page security on-call. 3\. Begin forensic analysis. 4\. Notify affected orgs per data breach protocol. 5\. Do not restore access until root cause confirmed and fixed. |

# **PART XI — FINOPS & COST MODEL**

| P1 FIX — Cost Model Absent: v1.0 had no per-request cost budgets or kill-switch policies. Success metrics were decoupled from COGS. Fix: Per-operation cost budgets, kill-switch thresholds, and unit economics targets. |
| :---- |

## **11.1 Per-Operation Cost Budget (Cloud Profile)**

| Operation | Primary Cost Driver | Target Cost/Op | Kill-Switch Threshold |
| :---- | :---- | :---- | :---- |
| Memory write (normal) | Embedding API \+ Qdrant write \+ PostgreSQL write | \< $0.0003 | Suspend if \> $0.002 (10x budget) — investigate |
| Memory retrieve (standard) | Embedding API \+ Qdrant ANN \+ scoring | \< $0.0002 | \> $0.001 triggers alert |
| Memory write (critical, hot) | Same \+ synchronous path (no Kafka batching) | \< $0.0006 | \> $0.003 triggers alert |
| NLI check (per candidate pair) | GPU inference (amortized T4 cost) | \< $0.00005 | NLI skipped if GPU cost spike detected |
| Consolidation (per episode batch) | LLM API call (Claude Sonnet) \+ Neo4j writes | \< $0.008/batch of 100 episodes | \> $0.05/batch: use cheaper model |
| Importance classification | Lightweight model inference | \< $0.00002 | Always within budget — no kill-switch needed |
| PR semantic diff | Embedding \+ ANN \+ NLI on all changed nodes | \< $0.01/PR | \> $0.10/PR: alert \+ async processing |

## **11.2 Unit Economics Targets (Month 12\)**

| Metric | Target |
| :---- | :---- |
| **Gross Margin (Cloud Hosting)** | ≥ 65% at Team tier. ≥ 75% at Enterprise tier. |
| **Cost per 10K retrievals** | \< $2.00 (including embedding, ANN, scoring, compute) |
| **Cost per 10K memory writes (standard)** | \< $3.00 (including embedding, dedup, classification, storage) |
| **LLM API cost as % of COGS** | \< 30%. If exceeding 30%, prioritize local model switching. |
| **Storage cost growth vs revenue growth** | Storage cost must grow slower than revenue (economies of scale from consolidation \+ deduplication). |

## **11.3 Model Cost Kill-Switch Policies**

|   If LLM API spend \> $500/day (emergency threshold):     1\. Auto-pause all consolidation jobs     2\. Switch consolidation to local model (Sovereign profile model)     3\. Alert FinOps on-call     4\. Resume with cloud model after spend returns to \< $200/day   If embedding API spend anomalous (\> 3x daily average):     1\. Check for runaway agent (loop creating excessive writes)     2\. Rate-limit offending agent\_id automatically     3\. Suspend agent pending investigation   Per-org spending cap enforcement:     \- Free tier: $2/month hard cap on compute costs. Writes blocked at cap.     \- Developer: $20/month soft cap. Alert at 80%, block at 150%.     \- Team: $150/month soft cap. Alert at 80%, degrade (no NLI) at 110%, block at 200%.     \- Enterprise: Custom. Block only on contractual limit breach. |
| :---- |

# **PART XII — DEVELOPMENT ROADMAP (Execution-Safe)**

| P0 FIX — SOC 2 Timeline Unrealistic \+ Phase Model Ambiguous: v1.0 targeted SOC 2 Type II in Months 7-9. Type II requires observation period BEFORE the report — controls must start earlier. Fix: SOC 2 controls implemented in Phase A. Observation period starts Phase B. Type II audit engagement begins Phase C. Report available Phase D. |
| :---- |

## **Phase A — Deterministic Core (Weeks 0–8)**

| Phase A Goal: One reliable canonical source of truth and reproducible memory state. First developer-testable alpha. |
| :---- |

**Deliverables**

* Modular monolith (memory-core) with Memory Gateway, VCS Core, basic retrieval

* PostgreSQL schema (§5.1) fully migrated and RLS enforced

* Qdrant collection-per-org isolation (§3.4 — INV-04 enforced)

* Write API with idempotency keys \+ outbox event pattern (§3.1)

* Retrieve API with 3-signal scoring (relevance \+ recency \+ importance — §8.1 of original)

* Time-travel query (as\_of\_commit parameter working)

* Provenance metadata end-to-end (every memory node has full provenance JSONB)

* Python SDK: observe(), retrieve(), branch context manager

* SOC 2 controls IMPLEMENTED (not yet observed): access control, logging, encryption at rest

* Minimal dashboard: repo view \+ commit history \+ time-travel scrubber

**Phase A Exit Criteria — ALL must pass**

| Exit Criterion | Test Method |
| :---- | :---- |
| **Deterministic replay: 1M synthetic write events replayed twice → bit-identical projection result** | Automated test suite in CI. Must pass 3 consecutive runs. |
| **INGEST ACK p99 ≤ 80ms under 500 concurrent writes** | Load test in staging (k6 or Gatling) |
| **RETRIEVAL p99 ≤ 350ms under 200 concurrent retrievals** | Load test in staging |
| **Cross-tenant isolation: org A cannot retrieve org B's memories under any API call pattern** | Isolation penetration test suite (automated). 0 leaks \= pass. |
| **INV-01 through INV-05 validated by automated invariant test suite** | Test suite in CI — must all pass |
| **SDK integration test with LangChain: drop-in BaseMemory replacement works with 0 code changes** | Integration test with LangChain 0.x |

## **Phase B — Governance & Safety (Weeks 8–16)**

| Phase B Goal: Safe memory writes and auditable governed merges. Closed beta with 10 design partners. |
| :---- |

**Deliverables**

* PR workflow \+ full PR lifecycle state machine (§2.3)

* ConflictRecord lifecycle with evidence scoring (no LLM arbitration yet)

* Cryptographic signing: HOSTED\_KMS and LOCAL\_KEY modes (§7.1)

* Intent Classifier \+ Sandbox Branch (memory poisoning defense)

* ANN-based semantic deduplication (no NLI yet — Phase C)

* Branch lifecycle state machine with soft-delete \+ legal hold (§2.2 — P0 fix)

* RBAC model enforced (§7.2 permission matrix)

* SOC 2 controls in OBSERVATION period (logging, access reviews, incident response tested)

* Deployment profile separation: Cloud vs Sovereign feature flags in codebase

**Phase B Exit Criteria — ALL must pass**

| Exit Criterion | Test Method |
| :---- | :---- |
| **Memory poisoning simulation suite: ≥ 95% of injection attack samples blocked or sandboxed** | Labeled injection simulation suite (§9.1 target) |
| **Audit query: given any commit hash, time-travel retrieval returns reproducible result across 3 independent runs** | Automated audit reproducibility test |
| **Branch soft-delete: after soft-delete, branch memories invisible in standard listing but accessible via audit API** | Automated branch lifecycle test |
| **PR merge: semantic diff correctly identifies nodes added, modified, deprecated** | PR diff accuracy test with 100 labeled PRs |
| **Key signing: all commits signed. Tampered commit (flipped bit in payload) fails verification** | Commit integrity test suite |
| **Intent classifier false-block rate ≤ 2% on legitimate write sample set** | ML eval suite — regression gate |

## **Phase C — Semantic Intelligence (Weeks 16–28)**

| Phase C Goal: Full semantic diff \+ contradiction detection \+ consolidated knowledge graph. GA launch. |
| :---- |

**Deliverables**

* Unified Semantic Diff Engine with NLI contradiction detection (§6.1 — P0 fix unified pipeline)

* Neo4j knowledge graph (Tier 3 semantic memory)

* Consolidation Engine: episodic → semantic distillation with confidence decay

* Tier 4 Relational Memory with privacy policy enforcement (§8)

* LLM-based conflict arbitration (Claude Sonnet 4\) for HUMAN\_REVIEW conflicts

* Full public marketplace v1: base repo discovery, fork, star

* Cold Start: onboarding mode \+ knowledge import (documents, Notion/Confluence)

* Embedding model migration tooling (§5.3)

* SOC 2 Type II AUDIT ENGAGEMENT: engage auditor. Observation period complete.

* Tenant isolation penetration test by external security firm — PASS required for GA

**Phase C Exit Criteria — ALL must pass**

| Exit Criterion | Test Method |
| :---- | :---- |
| **NLI contradiction F1 ≥ 0.82 on labeled eval set. False-positive rate ≤ 5%.** | ML regression gate in CI |
| **Retrieval NDCG@10 ≥ 0.72 on 500 human-labeled query-memory pairs** | ML regression gate in CI |
| **Tenant isolation penetration test by external security firm: 0 critical or high findings** | External pentest report required |
| **Consolidation: episodic → semantic conversion correct for 95% of gold test episodes** | Consolidation eval suite |
| **GDPR deletion cascade: delete-user request triggers cascade delete across all tiers within SLA** | Deletion audit report verified by automated test |
| **Cost envelope: p99 write \< $0.0003, p99 retrieve \< $0.0002 on production load profile** | Load test with COGS instrumentation |

## **Phase D — Enterprise & Ecosystem (Weeks 28–52)**

| Phase D Goal: Regulated enterprise deployment. On-prem. Full ecosystem. Series A. |
| :---- |

**Deliverables**

* Sovereign/on-prem deployment: Helm charts \+ all self-hosted models containerized

* CUSTOMER\_KMS key custody mode (§7.1)

* Air-gapped deployment validation (zero external network calls verified)

* Multi-agent swarm collaboration protocol (cross-org PR with reputation scoring)

* SOC 2 Type II REPORT issued by auditor

* HIPAA BAA available for healthcare customers

* CLI tool (memoryos) for developer power users

* TypeScript SDK

* AutoGen \+ CrewAI \+ LlamaIndex native integrations

**Phase D Exit Criteria — ALL must pass**

| Exit Criterion | Test Method |
| :---- | :---- |
| **Sovereign deployment: full stack runs with zero external DNS calls in network-captured test** | Wireshark/tcpdump network capture during load test |
| **Disaster recovery: full region failover tested in game day. RTO ≤ 30 min achieved.** | Game day drill with runbook execution |
| **SOC 2 Type II report issued with no critical exceptions** | Auditor report document |
| **Multi-agent: Agent A learning propagates to Agent B via PR in \< 10 minutes (automated flow)** | End-to-end integration test |

# **PART XIII — PRODUCTION READINESS GATE**

Every item in this gate must have explicit sign-off before GA release. No item can be waived by product or engineering alone — security and legal sign-off is required for their sections.

## **13.1 Spec Completeness Gate**

| Item | Verification |
| :---- | :---- |
| **OpenAPI 3.1 spec published and matches implementation (contract test suite passes)** | CI: dredd or schemathesis contract tests green |
| **All event schemas in Kafka topics documented and versioned in schema registry** | Confluent Schema Registry / Glue Schema Registry populated |
| **All state machines implemented as explicit state transition functions (not ad-hoc if/else)** | Code review sign-off by Tech Lead |
| **All invariants (INV-01 through INV-10) covered by automated tests** | CI: invariant test suite 100% pass rate |

## **13.2 Security Gate**

| Item | Verification |
| :---- | :---- |
| **External penetration test (tenant isolation, API security, injection attack surfaces): 0 critical/high findings** | Pentest report from approved security firm. Any finding requires fix \+ retest. |
| **RBAC: every permission in §7.2 matrix tested with automated RBAC test suite** | CI: RBAC test suite 100% pass rate |
| **Key signing: tamper-detection test suite passes (corrupted commits rejected)** | CI: commit integrity tests |
| **Incident response plan documented and tabletop exercise completed** | Security team sign-off |
| **Encryption at rest verified: S3 SSE-KMS, Qdrant disk encryption, PostgreSQL pgcrypto for SENSITIVE fields** | Infrastructure audit |
| **Encryption in transit: TLS 1.3 enforced on all endpoints, all service-to-service calls via mutual TLS (Istio)** | TLS scan (testssl.sh) green |

## **13.3 Data Governance Gate**

| Item | Verification |
| :---- | :---- |
| **GDPR deletion cascade proven: delete-user test → verify zero records across all tiers \+ backups within SLA** | Deletion audit report automated test |
| **Data retention matrix (§5.4) enforced: automated retention policy job deletes expired data** | Retention job audit log reviewed |
| **.memignore built-in rules enforced: injection of SENSITIVE patterns blocked at write path** | Integration test with SENSITIVE pattern samples |
| **Privacy policy updated to reflect BEHAVIORAL data collection with legitimate interest basis documented** | Legal sign-off required |

## **13.4 Reliability Gate**

| Item | Verification |
| :---- | :---- |
| **All SLOs (§10.1) met in 7-day soak test on production-scale synthetic load** | Prometheus \+ Grafana dashboards reviewed by SRE lead |
| **All alert runbooks written and reviewed. On-call rotation staffed.** | Runbook review in PagerDuty |
| **Chaos engineering: Qdrant failure, Kafka failure, NLI sidecar failure — all degrade gracefully per §6.2 fallbacks** | Chaos experiment results reviewed |
| **Disaster recovery drill completed: RPO/RTO targets met for all scenarios in §10.3** | DR drill report |

## **13.5 ML Quality Gate**

| Item | Verification |
| :---- | :---- |
| **All model performance contracts (§9.1) met on production eval sets** | ML regression gate in CI — all green |
| **Fallback behavior tested: each model made unavailable → system degrades per §6.2 without data loss** | Chaos test: kill each ML sidecar, verify fallback behavior |
| **Active learning pipeline tested end-to-end: human label → eval set update → model retrain trigger** | QA test of active learning flow |

## **13.6 FinOps Gate**

| Item | Verification |
| :---- | :---- |
| **Per-operation cost budgets (§11.1) validated on 24-hour production load replay** | COGS instrumentation dashboard reviewed by FinOps |
| **Kill-switch policies (§11.3) tested: LLM spend spike → consolidation pause trigger fires within 60 seconds** | Kill-switch integration test |
| **Per-org spending cap enforcement tested: free tier cap blocks writes at limit** | API integration test |

# **PART XIV — APPENDIX: FORENSIC AUDIT RESOLUTION REGISTRY**

Every finding from the v1.0 forensic audit is tracked here with its resolution status and the section of this document that implements the fix.

## **P0 Findings — All Resolved**

| Finding ID | Issue (from audit) | Resolution | Section |
| :---- | :---- | :---- | :---- |
| P0-01 | Branch delete vs audit contradiction | Soft-delete \+ legal hold state machine. Commits permanently retained regardless of branch status. | §2.2 |
| P0-02 | Contradictory semantic diff logic (cosine\<0 vs NLI on 0.5-0.85) | Unified single-pipeline: ANN candidates → NLI classifier. Cosine sign removed as signal. Deterministic. | §6.1 |
| P0-03 | Hot-path latency conflict (50ms vs 200ms for same operation) | Three-layer SLO: INGEST ACK ≤80ms, DURABLE COMMIT ≤400ms, RETRIEVAL ≤350ms. No ambiguity. | §10.1 |
| P0-04 | Tenant isolation listed as open problem despite enterprise promise | Tenant isolation is pre-GA hard requirement. Construction-level guarantees per §3.4. Pentest required. | §3.4 |
| P0-05 | Key custody assumes secure enclave not available in SDK runtimes | Three-tier key custody: HOSTED\_KMS, CUSTOMER\_KMS, LOCAL\_KEY with explicit trust levels and restrictions. | §7.1 |
| P0-06 | SOC 2 Type II timeline unrealistic (Months 7-9) | Controls in Phase A, observation in Phase B, audit engagement in Phase C, report in Phase D (Month 10+). | §12 |

## **P1 Findings — All Resolved**

| Finding ID | Issue (from audit) | Resolution | Section |
| :---- | :---- | :---- | :---- |
| P1-01 | Cross-reference: Section 8 referenced but it was Section 7 | All internal references corrected. Semantic Diff Engine is Part VI in this document. | §6 |
| P1-02 | Storage transaction model undefined, no canonical source of truth | Event-sourced commit log pattern. PostgreSQL commit log is canonical. All others are projections. | §3.1 |
| P1-03 | On-prem promise conflicts with external model API dependencies | Two explicit deployment profiles (CLOUD vs SOVEREIGN) with feature matrix. | §3.3 |
| P1-04 | Privacy conflict: .memignore blocks PII but relational memory stores PII-adjacent data | Unified data taxonomy with 4 classes. Relational memory uses BEHAVIORAL/PII\_ADJACENT with full lawful basis and deletion policy. | §8 |
| P1-05 | 14 microservices in Phase A/B is undeliverable | Modular monolith in Phase A/B. Services split only when objective scaling thresholds hit. | §3.2 |
| P1-06 | Success metrics decoupled from cost model | Per-operation cost budgets, unit economics targets, kill-switch policies all defined. | §11 |

## **P2 Findings — All Resolved**

| Finding ID | Issue (from audit) | Resolution | Section |
| :---- | :---- | :---- | :---- |
| P2-01 | NLI latency inconsistency (20ms vs 25ms) | Unified: NLI p99 ≤ 30ms (GPU). Single target, no ambiguity. | §9.1 |
| P2-02 | VCS merge conflict formalism missing for non-text objects | ConflictRecord lifecycle with 3 contradiction types. Merge creates explicit parent references (INV-10). | §2.4, §5.1 |
| P2-03 | API contracts missing idempotency, pagination, error taxonomy | Full API contract with idempotency keys, cursor pagination, RFC 7807 error format, retry semantics. | §4 |
| P2-04 | No embedding model migration plan | Full 6-step migration procedure including change detection and rollback. | §5.3 |
| P2-05 | No RPO/RTO targets | Complete RPO/RTO table by failure scenario. | §10.3 |
| P2-06 | Training data licensing conflicts with trust posture | Removed from all planning horizons. Deferred indefinitely pending separate legal review proposal. | §1.3 |

## **Missing Specifications — All Added**

| Missing Item (from audit §4) | Status in v2.0 | Section |
| :---- | :---- | :---- |
| JTBD to feature mapping with acceptance tests | ✅ Complete | §1.2 |
| Explicit out-of-scope list per phase | ✅ Complete | §1.3 |
| Failure-mode UX contracts | ✅ Fallback behavior per model in §6.2. Degraded state alerting in §10.4 | §6.2, §10.4 |
| Identity model for user, agent, org, repo, branch | ✅ Complete | §2.1 |
| Formal state machines for PR, conflict, branch | ✅ Complete — all three state machines with invariants | §2.2–2.4 |
| System invariants (numbered, formal) | ✅ INV-01 through INV-10 | §2.5 |
| API idempotency keys \+ pagination \+ error taxonomy | ✅ Complete | §4 |
| ML precision/recall targets and eval datasets | ✅ Complete model contracts with blocking gates | §9.1 |
| ML fallback behavior when models unavailable | ✅ Per-model fallback table | §6.2 |
| RBAC model with permission matrix | ✅ Full 6-role permission matrix | §7.2 |
| Data retention matrix by class/jurisdiction | ✅ 4-class retention matrix with SLAs | §5.4 |
| Deletion semantics across all tiers \+ backups | ✅ Full cascade deletion map with SLAs | §5.5 |
| Error budget policy per SLO | ✅ Complete | §10.2 |
| Alert thresholds and runbook ownership | ✅ 6 alerts with runbook actions | §10.4 |
| Chaos/failure drill definitions | ✅ In production readiness gate §13.4 | §13.4 |
| Active learning / threshold retuning protocol | ✅ Complete protocol with 4 signal types | §9.3 |
| Embedding model migration plan | ✅ 6-step migration with change detection | §5.3 |

| ✦ DOCUMENT FINALITY STATEMENT This is PRD v2.0 for MemoryOS. It supersedes v1.0 in all respects. All 6 P0 findings, 6 P1 findings, and 6 P2 findings from the forensic audit have been resolved and traced to specific sections. All 17 missing specification items have been added. This document is intended to be engineering-executable without requiring a further design review cycle before implementation begins. Any ambiguity discovered during Phase A implementation should be resolved via an Architectural Decision Record (ADR) linked back to the relevant section of this PRD, and this document updated accordingly. v2.0 authored March 2026 | Prepared for Antigravity AI IDE | CONFIDENTIAL |
| :---- |


# MemoryOS Development Phases

This document is the execution blueprint for building MemoryOS from scratch to a production-ready platform using AI-assisted implementation under human supervision.

Canonical PRD resolution (machine-executable):
1. Read `docs/PRD_CANONICAL.txt`.
2. Treat the path in that file as the single canonical PRD.
3. Abort planning/execution if the target PRD file is missing.
4. Record the resolved PRD path and commit hash in each evidence bundle.

Current canonical source resolves to `docs/MemOSv2.1_PRD.md`.  
This file converts PRD intent into build sequencing, artifacts, quality gates, and operational discipline.

---

## 1. Execution Model

## 1.1 Roles
- **AI Builder**: implements code, migrations, infra-as-code, tests, docs, and runbooks.
- **Human Supervisor (you)**: approves ADRs, security/privacy decisions, releases, and gate transitions.
- **Security Reviewer**: signs off on key custody, encryption, RBAC, tenant isolation.
- **SRE Reviewer**: signs off on SLOs, error budgets, runbooks, DR drills.
- **ML Reviewer**: signs off on model contracts, eval gates, fallback behavior.

## 1.2 Decision Policy
- No phase transition without written gate evidence.
- Ambiguity is resolved by ADR; no ad-hoc implementation.
- “Works locally” is not acceptance. Acceptance means measurable criteria from this file are met.

## 1.3 Delivery Cadence
- 1-week sprints inside each phase.
- Daily AI build cycle: plan -> implement -> test -> document -> evidence pack.
- End-of-sprint supervisor review with go/no-go decision.

---

## 2. Global Non-Negotiables

1. **Canonical state**: PostgreSQL commit log is source of truth.
2. **Immutability**: commits are append-only and cryptographically verifiable.
3. **Tenant isolation**: hard isolation by construction (DB, vector store, graph, cache, object store, event stream).
4. **Privacy propagation**: deletion SLAs include backups, not just hot data.
5. **Governed learning**: branch/PR/conflict workflows are explicit state machines.
6. **Fail-safe security**: on uncertainty, sandbox instead of mainline write.
7. **Observability first**: metrics/traces/logs shipped before scale.
8. **Cost-aware operations**: every expensive path has budget and kill-switch.

---

## 3. Workspace-Root Repository Layout

Apply this layout at the current workspace root. Do not create an extra nested `memoryos/` folder if already inside the project root.

```text
./
  services/
    memory-core/
    memory-worker/
    semantic-diff/
    intent-classifier/
    consolidation-worker/
  sdk/
    python/
    typescript/
  infra/
    terraform/
    kubernetes/
    helm/
  schemas/
    openapi/
    events/
    sql/
  tests/
    unit/
    integration/
    load/
    chaos/
    security/
    ml-eval/
  docs/
    ADRs/
    runbooks/
    compliance/
```

---

## 4. Phase Map

| Phase | Window | Outcome |
|---|---|---|
| Phase 0 | Week -2 to 0 | Build foundation and controls for deterministic delivery |
| Phase A | Weeks 0-8 | Deterministic core alpha |
| Phase B | Weeks 8-16 | Governance and safety closed beta |
| Phase C | Weeks 16-28 | Cloud GA candidate (all Cloud-profile hard gates) |
| Phase D | Weeks 28-52 | Enterprise production-ready (Sovereign + ecosystem scale) |

### 4.1 Release State Definitions (No Ambiguity)
- **Cloud GA Candidate**: Phase A/B/C gates passed with evidence; Cloud profile can launch.
- **Enterprise Production Ready**: Phase A/B/C/D gates passed with evidence; Sovereign/enterprise commitments are launch-safe.

### 4.2 Invariant Ownership Mapping (INV-01..INV-10)

| Invariant | Primary Phase | Enforcement Workstream | Test Gate |
|---|---|---|---|
| INV-01 (node -> commit mapping) | A | A-WS1 | Phase A gate |
| INV-02 (offline signature verify) | A/B | A-WS5 baseline + B-WS3 full | Phase B gate |
| INV-03 (deterministic replay) | A | A-WS2 | Phase A gate |
| INV-04 (tenant isolation) | A/C | A-WS3 + C external pentest | Phase A + C gates |
| INV-05 (legal-hold mutation block) | B | B-WS1 | Phase B gate |
| INV-06 (commit immutability) | A | A-WS1 | Phase A gate |
| INV-07 (deletion propagation SLA) | C | C-WS3 | Phase C gate |
| INV-08 (PII/SENSITIVE encryption) | A/C | A-WS1 schema + C-WS3 runtime audits | Phase A + C gates |
| INV-09 (branch head optimistic concurrency) | A | A-WS1/A-WS2 | Phase A gate |
| INV-10 (merge parent cardinality) | A/B | A-WS1 schema triggers + B-WS1 merge flow | Phase A + B gates |

---

## 5. Phase 0 — Foundation Setup (Pre-Phase)

Goal: eliminate bootstrapping entropy and make Phase A execution deterministic.

### 5.1 Deliverables
- Monorepo scaffolding with module boundaries.
- CI pipeline with required jobs:
  - lint
  - unit
  - integration
  - contract
  - security baseline scan
- Baseline observability stack in staging:
  - OpenTelemetry
  - Prometheus/Grafana
  - structured logs
- ADR template and decision log process.
- Initial threat model and data classification playbook.

### 5.2 Build Tasks
- Define coding standards and branch policy.
- Create OpenAPI and event schema repositories.
- Create SQL migration framework and rollback convention.
- Create secrets management strategy (KMS/Vault abstraction layer).
- Add seed load-testing harness (k6/Gatling skeleton).

### 5.3 Exit Criteria
- CI green for scaffold project.
- One end-to-end smoke flow deployable in staging.
- Supervisor-approved ADR set for:
  - commit hash canonicalization
  - key custody initial mode
  - tenant isolation strategy

---

## 6. Phase A — Deterministic Core (Weeks 0-8)

Goal: one reliable canonical source of truth and reproducible memory state.

### 6.1 In Scope
- Modular monolith (`memory-core`) + `memory-worker`.
- PostgreSQL canonical commit log.
- Outbox pattern + Kafka publish.
- Qdrant org-isolated collections.
- Core APIs:
  - write memory
  - retrieve memory
  - list commits
  - get commit
  - revert via rollback commit
- Time-travel retrieval (`as_of_commit`).
- Provenance metadata end-to-end.
- Python SDK (`observe`, `retrieve`, `branch` context).

### 6.2 Out of Scope
- NLI contradiction model.
- Neo4j semantic graph.
- LLM conflict arbitration.
- Sovereign deployment.

### 6.3 Workstreams

### A-WS1 Data and State Integrity
- Implement SQL schema (commits, commit_parents, memory_nodes, outbox, branches, repositories).
- Enforce commit immutability triggers.
- Enforce merge/parent cardinality constraints.
- Implement RLS for all org-scoped tables.

### A-WS2 Core Write/Read Path
- Implement write path transaction:
  - commit insert
  - outbox insert
- Implement outbox relay and idempotent projection apply.
- Implement retrieval scoring (relevance + recency + importance).

### A-WS3 Tenant Isolation
- DB row isolation tests.
- Qdrant collection-per-org enforcement.
- Redis keyspace isolation and restricted operations.
- Kafka topic-per-org routing.

### A-WS4 SDK and Developer UX
- Python SDK wrapper.
- Integration with LangChain memory interface.
- Minimal dashboard (repo, commits, time-travel).

### A-WS5 Security Baseline
- Key registration and signature verification in write path.
- Basic RBAC enforcement for core endpoints.
- Audit log on every state mutation.

### 6.4 Required Artifacts
- `schemas/sql/phase_a/*.sql`
- `schemas/openapi/v1/core.yaml`
- `schemas/events/memory-commit-v1.json`
- `docs/runbooks/phase_a_operational.md`
- `docs/ADRs/` entries for any deviations.

### 6.5 Required Tests
- Unit: commit hash and signature verification routines.
- Integration: write -> outbox -> projection -> retrieve.
- Invariant: INV-01, INV-03, INV-04, INV-06, INV-08, INV-09, INV-10.
- Isolation: org A never reads org B data.
- Load: ingest p99 and retrieval p99 under PRD target load.

### 6.6 Cryptographic Rollout (Sequenced)
- Phase A baseline:
  - canonical commit hash serialization locked by ADR
  - signature verification path implemented and tested
  - non-production key mode allowed for staging bootstrapping
- Phase B hardening:
  - HOSTED_KMS + LOCAL_KEY enforcement
  - signed commits mandatory in non-test environments
  - LOCAL_KEY merge restrictions enforced
- Phase D enterprise:
  - CUSTOMER_KMS custody mode required for sovereign enterprise rollout

### 6.7 Exit Gate (Hard)
- Deterministic replay of 1M synthetic writes passes in 3 consecutive runs.
- Ingest ACK p99 <= 80ms at 500 concurrent writes.
- Retrieval p99 <= 350ms at 200 concurrent retrievals.
- Zero tenant leaks in automated suite.
- INV-01, INV-03, INV-04, INV-06, INV-08, INV-09, INV-10 all pass in invariant suite.
- Supervisor sign-off with evidence bundle.

---

## 7. Phase B — Governance and Safety (Weeks 8-16)

Goal: safe memory writes and auditable governed merges.

### 7.1 In Scope
- Branch lifecycle state machine.
- PR lifecycle + review workflow.
- Conflict lifecycle with evidence scoring.
- Intent classifier + sandbox behavior.
- Key custody modes: HOSTED_KMS + LOCAL_KEY.
- Full RBAC matrix enforcement.

### 7.2 Workstreams

### B-WS1 Governance APIs
Implement endpoints for:
- branch create/soft-delete/legal-hold/release
- PR create/list/review/merge
- conflict list/get/resolve

### B-WS2 Poisoning Defense
- Deploy intent classifier service.
- Define fallback: classifier down => sandbox-all.
- Add poisoning simulation suite and false-block measurement.

### B-WS3 Cryptographic Trust
- Enforce signed commits in write path.
- Tamper detection tests.
- LOCAL_KEY restrictions (no auto-merge to main).

### B-WS4 RBAC Precision
- Implement operation-resource permission matrix.
- Add automated RBAC allow/deny tests for every matrix cell.

### B-WS5 Auditability
- Full trace for PR decisions and conflict resolutions.
- Time-travel reproducibility tests under governance operations.

### 7.3 Required Artifacts
- `schemas/openapi/v1/governance.yaml`
- `tests/security/rbac_matrix_tests.*`
- `tests/security/poisoning_simulation.*`
- `docs/runbooks/security_incident.md`

### 7.4 Exit Gate (Hard)
- Poisoning suite >=95% blocked/sandboxed.
- Intent classifier false-block <=2%.
- All commits signed; tampered commit rejected.
- Branch soft-delete behavior passes visibility/audit tests.
- PR diff correctness >=0.90 precision and >=0.90 recall on labeled PR test set (n>=100).
- Governance OpenAPI contract tests: 100% pass for branch/PR/conflict endpoints.
- INV-02, INV-05, INV-10 pass in invariant and integration suites.

---

## 8. Phase C — Semantic Intelligence and GA Readiness (Weeks 16-28)

Goal: production-grade semantic reasoning and knowledge consolidation.

### 8.1 In Scope
- Unified semantic diff pipeline with NLI contradiction detection.
- Neo4j semantic memory tier.
- Consolidation worker (episodic -> semantic).
- Relational memory with privacy policy enforcement.
- Embedding migration tooling.
- External pentest for tenant isolation.

### 8.2 Workstreams

### C-WS1 Semantic Diff Engine
- ANN candidate retrieval.
- NLI classification pipeline.
- ConflictRecord creation and routing to sandbox.
- DiffObject versioning.

### C-WS2 Knowledge Graph and Consolidation
- Implement graph projection writer.
- Consolidation scheduling and confidence decay.
- Provenance links across episodic and semantic nodes.

### C-WS3 Privacy-Compliant Relational Memory
- Behavioral profile store.
- Lawful-basis enforcement at write time.
- Deletion propagation integration with all tiers and backups.

### C-WS4 ML Contracts and Gating
- Enforce model metrics from PRD:
  - NLI contradiction F1 >=0.82
  - false-positive <=5%
  - retrieval NDCG@10 >=0.72
- Fallback behavior tests for model unavailability.

### C-WS5 GA Hardening
- Tenant isolation external pentest.
- Cost envelope validation on production-like load.
- Reliability soak tests and chaos scenarios.

### 8.3 Required Artifacts
- `services/semantic-diff/*`
- `services/consolidation-worker/*`
- `tests/ml-eval/*`
- `tests/chaos/*`
- `docs/compliance/deletion_audit_spec.md`

### 8.4 Exit Gate (Hard)
- NLI contradiction F1 >=0.82, contradiction false-positive <=5%, retrieval NDCG@10 >=0.72.
- External pentest reports zero critical/high findings.
- Deletion cascade SLA test passes across online + backup stores with 100% of test records within class SLA windows.
- Consolidation quality >=95% on gold episodes.
- Cost envelope under 24h replay:
  - avg write cost <= $0.0003
  - avg retrieve cost <= $0.0002
  - p95 write and retrieve cost <= 2x respective average target
- INV-07 and INV-08 deletion/encryption audits pass.

---

## 9. Phase D — Enterprise and Ecosystem (Weeks 28-52)

Goal: regulated enterprise deployment and ecosystem expansion.

### 9.1 In Scope
- Sovereign/on-prem deployment stack.
- CUSTOMER_KMS key custody mode.
- Air-gapped runtime validation.
- Multi-agent collaboration at scale.
- SOC 2 Type II report completion.
- HIPAA BAA readiness.
- TypeScript SDK and ecosystem integrations.

### 9.2 Workstreams

### D-WS1 Sovereign Platform
- Helm packaging for full stack.
- Self-hosted model serving profile.
- No external DNS/egress verification.

### D-WS2 Enterprise Security and Compliance
- CUSTOMER_KMS integration and key lifecycle controls.
- Compliance evidence packaging for SOC2/HIPAA.
- Formal incident response and legal workflows.

### D-WS3 Ecosystem and Integrations
- TypeScript SDK parity with Python SDK.
- AutoGen/CrewAI/LlamaIndex connectors.
- CLI for operational workflows.

### D-WS4 Scale Validation
- Large multi-agent propagation tests.
- Region failover game day.
- Long-duration soak tests with cost controls active.

### 9.3 Exit Gate (Hard)
- Air-gapped deployment proves zero external calls during load.
- DR game day meets RTO <=30 minutes.
- SOC2 Type II report issued without critical exceptions.
- Multi-agent knowledge propagation p95 <=10 minutes end-to-end.

---

## 10. Cross-Phase Quality Framework

## 10.1 Test Pyramid by Phase
- **Phase A**: unit + integration + invariants + isolation + load smoke.
- **Phase B**: add security matrix tests + poisoning simulations + audit reproducibility.
- **Phase C**: add ML eval + chaos + deletion cascade audits + external pentest.
- **Phase D**: add sovereign validation + DR game days + enterprise compliance evidence tests.

## 10.2 CI Required Pipelines
- `lint`
- `unit`
- `integration`
- `contract`
- `security`
- `invariant`
- `load-smoke`
- `ml-eval` (B+)
- `chaos` (C+)

No merge to protected branch if required jobs fail.

## 10.3 Evidence Bundle Template (Per Phase)
- Build commit hashes.
- OpenAPI and event schema versions.
- Test reports and pass rates.
- SLO/latency dashboards.
- Security findings and remediations.
- Cost dashboards vs budget.
- Supervisor sign-off note.

---

## 11. Supervisor Checkpoints

At minimum, hold formal checkpoints at:
1. Phase kickoff
2. Mid-phase architecture review
3. Pre-gate rehearsal
4. Final gate review

Checkpoint agenda:
- scope burn-down,
- risk register,
- blocker resolution,
- go/no-go recommendation.

---

## 12. Risk Register (Top Program Risks)

| Risk | Where it hits | Mitigation |
|---|---|---|
| Tenant leak bug | A/C | hard isolation tests + external pentest |
| Commit integrity drift | A/B | immutable schema + signature verify + tamper tests |
| Poisoning false negatives | B/C | sandbox fallback + attack simulations |
| Model instability | C | regression gate + fallback modes |
| Cost blowout | C/D | kill-switches + per-op budgets |
| Compliance delays | B/D | controls early + evidence automation |

---

## 13. Production-Ready Definition

MemoryOS release states:
- **Cloud GA Candidate**: all Phase A/B/C gates passed with evidence and required sign-offs.
- **Enterprise Production Ready**: all Phase A/B/C/D gates passed with evidence and required sign-offs.

Enterprise production-ready requires:
- All Phase A-D gates passed with evidence.
- Part XIII gate items are signed off by required owners.
- No unresolved P0/P1 defects.
- SLO, security, privacy, and cost controls are all operational (not just documented).

---

## 14. AI Builder Operating Loop (Daily)

Use this loop every day:
1. Pull phase backlog and select smallest coherent vertical slice.
2. Implement code + tests + docs for slice.
3. Run required CI subset locally/staging.
4. Generate evidence artifacts.
5. Update risk and ADR logs.
6. Request supervisor decision for merge/rework.

Hard rule: no feature-only progress without test and runbook updates.

---

## 15. Rollback and Backout Procedures (Phase-Level)

Rollback triggers:
- Any P0 defect found during gate rehearsal.
- Any security/privacy regression in required tests.
- Any SLO miss >10% above target sustained for 30 minutes in staged gate run.
- Any tenant isolation leak.

### 15.1 Phase A Rollback
- Freeze merges to release branch.
- Revert failing migration set using migration rollback convention.
- Rebuild projections from canonical commit log snapshot.
- Re-run invariant and isolation suites before unfreeze.

### 15.2 Phase B Rollback
- Disable governance mutating endpoints behind feature flags.
- Force sandbox-all mode for writes if intent/classification safety is uncertain.
- Revert RBAC or signing regressions to last green release tag.
- Re-run governance contract tests and poisoning suite before re-enable.

### 15.3 Phase C Rollback
- Disable NLI contradiction path and switch to conservative fallback mode.
- Pause consolidation jobs if quality/cost gates fail.
- Roll back embedding migration cutover to previous vector set.
- Re-run ML regression + deletion SLA suites before resume.

### 15.4 Phase D Rollback
- Revert sovereign release to last validated air-gapped image set.
- Disable CUSTOMER_KMS rollout path and keep existing custody mode.
- Execute DR validation replay before restoring traffic.
- Resume enterprise rollout only after security/SRE sign-off.

Rollback evidence required:
- incident summary
- root cause
- affected versions
- rollback commands executed
- post-rollback validation results
- supervisor approval to proceed

---

## 16. Immediate Next Action

Start with **Phase 0** and produce:
- repo scaffolding,
- CI pipeline,
- SQL migration baseline,
- OpenAPI skeleton,
- first ADR set,
- initial evidence bundle.

Once approved, begin Phase A sprint 1.

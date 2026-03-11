# MemoryOS Execution Checklist (Command-Level)

Purpose: run MemoryOS delivery from scratch to production using AI implementation + human supervision, with explicit day-by-day commands tied to gates in `docs/phases.md`.

This checklist is machine-oriented: each block is designed to be run as-is or with only the noted variable substitutions.

---

## 0. Run Preconditions

Run from workspace root:

```bash
pwd
```

Expected path: project root that contains `docs/`.

Required baseline tools (verify first):

```bash
command -v bash
command -v rg
command -v jq
command -v curl
command -v python3
command -v git || true
command -v docker || true
command -v k6 || true
command -v npm || true
command -v uv || true
command -v schemathesis || true
```

If a tool is missing, install it before continuing or mark the day blocked.

---

## 1. Canonical PRD Resolution (Run Every Day Before Work)

```bash
set -euo pipefail

PRD_PATH="$(cat docs/PRD_CANONICAL.txt)"
test -f "$PRD_PATH"

echo "Canonical PRD: $PRD_PATH"
```

Record PRD identity for evidence:

```bash
mkdir -p evidence/meta
{
  echo "timestamp_utc=$(date -u +%FT%TZ)"
  echo "canonical_prd=$PRD_PATH"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "git_commit=$(git rev-parse HEAD)"
    echo "git_branch=$(git rev-parse --abbrev-ref HEAD)"
  else
    echo "git_commit=NA"
    echo "git_branch=NA"
  fi
} > evidence/meta/canonical_prd_context.env
cat evidence/meta/canonical_prd_context.env
```

---

## 2. Standard Environment Variables

Set these once per day:

```bash
export PHASE="phase0"      # phase0 | phaseA | phaseB | phaseC | phaseD
export WEEK="w01"          # e.g., w01, w02 ...
export DAY="d01"           # d01..d05
export RUN_DATE="$(date -u +%F)"
export RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
export EVIDENCE_DIR="evidence/$PHASE/$WEEK/$DAY-$RUN_TS"
mkdir -p "$EVIDENCE_DIR"

echo "$EVIDENCE_DIR"
```

---

## 3. Universal Daily Skeleton (Use Every Working Day)

## 3.1 Day Start Snapshot

```bash
{
  echo "phase=$PHASE"
  echo "week=$WEEK"
  echo "day=$DAY"
  echo "run_ts=$RUN_TS"
  echo "prd=$PRD_PATH"
} > "$EVIDENCE_DIR/day_context.env"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short > "$EVIDENCE_DIR/git_status_start.txt"
  git log --oneline -n 20 > "$EVIDENCE_DIR/git_log_start.txt"
fi

rg -n '^## ' docs/phases.md > "$EVIDENCE_DIR/phases_sections.txt"
```

## 3.2 Build + Test Command Pack

Run what exists (safe autodetect):

```bash
# Python format/lint/tests
if [ -f pyproject.toml ]; then
  uv run ruff check . | tee "$EVIDENCE_DIR/ruff_check.log"
  uv run pytest -q | tee "$EVIDENCE_DIR/pytest.log"
fi

# Node lint/test
if [ -f package.json ]; then
  npm run lint --if-present | tee "$EVIDENCE_DIR/npm_lint.log"
  npm test --if-present | tee "$EVIDENCE_DIR/npm_test.log"
fi

# Go tests
if rg --files -g '*.go' >/dev/null 2>&1; then
  go test ./... | tee "$EVIDENCE_DIR/go_test.log"
fi
```

## 3.3 Contract + Schema Checks

```bash
if [ -f schemas/openapi/v1/core.yaml ]; then
  cp schemas/openapi/v1/core.yaml "$EVIDENCE_DIR/openapi_core_snapshot.yaml"
fi
if [ -f schemas/openapi/v1/governance.yaml ]; then
  cp schemas/openapi/v1/governance.yaml "$EVIDENCE_DIR/openapi_governance_snapshot.yaml"
fi

if command -v schemathesis >/dev/null 2>&1 && [ -f schemas/openapi/v1/core.yaml ]; then
  schemathesis run schemas/openapi/v1/core.yaml --checks all \
    | tee "$EVIDENCE_DIR/schemathesis_core.log"
fi
```

## 3.4 Day Close Snapshot

```bash
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short > "$EVIDENCE_DIR/git_status_end.txt"
  git diff --stat > "$EVIDENCE_DIR/git_diff_stat.txt"
fi

ls -la "$EVIDENCE_DIR" > "$EVIDENCE_DIR/evidence_inventory.txt"
```

---

## 4. Phase 0 (Pre-Phase) Day-by-Day (10 Working Days)

Objective: scaffold deterministic delivery system before feature implementation.

## Day 01

```bash
export PHASE=phase0 WEEK=w00 DAY=d01
# Resolve canonical PRD
PRD_PATH="$(cat docs/PRD_CANONICAL.txt)"; test -f "$PRD_PATH"
# Initialize structure
mkdir -p services sdk infra/{terraform,kubernetes,helm} schemas/{sql,openapi/v1,events} tests/{unit,integration,load,chaos,security,ml-eval} docs/{ADRs,runbooks,compliance} evidence
find services sdk infra schemas tests docs -maxdepth 2 -type d | sort
```

## Day 02

```bash
export PHASE=phase0 WEEK=w00 DAY=d02
# Create ADR template
cat > docs/ADRs/ADR_TEMPLATE.md <<'ADR'
# ADR-XXXX: Title
## Context
## Decision
## Alternatives
## Impact
## Rollback/Migration
ADR

# Create canonical coding standards file
cat > docs/CODING_STANDARDS.md <<'STD'
# Coding Standards
- Deterministic behavior preferred.
- Schema migrations must be reversible.
- Every feature ships tests + runbook update.
STD
```

## Day 03

```bash
export PHASE=phase0 WEEK=w00 DAY=d03
# OpenAPI skeletons
cat > schemas/openapi/v1/core.yaml <<'YAML'
openapi: 3.1.0
info: {title: MemoryOS Core API, version: v1}
paths: {}
YAML

cat > schemas/openapi/v1/governance.yaml <<'YAML'
openapi: 3.1.0
info: {title: MemoryOS Governance API, version: v1}
paths: {}
YAML
```

## Day 04

```bash
export PHASE=phase0 WEEK=w00 DAY=d04
# SQL migration scaffold
mkdir -p schemas/sql/migrations
cat > schemas/sql/migrations/0001_bootstrap.sql <<'SQL'
-- bootstrap migration placeholder
SQL
cat > schemas/sql/migrations/ROLLBACK.md <<'MD'
# Rollback Convention
- Every migration must define a rollback strategy in PR notes.
MD
```

## Day 05

```bash
export PHASE=phase0 WEEK=w00 DAY=d05
# CI skeleton
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'YAML'
name: ci
on: [push, pull_request]
jobs:
  placeholder:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "replace with real jobs"
YAML
```

## Day 06

```bash
export PHASE=phase0 WEEK=w00 DAY=d06
# Observability scaffold docs
cat > docs/runbooks/observability_baseline.md <<'MD'
# Observability Baseline
- tracing: OpenTelemetry
- metrics: Prometheus
- dashboards: Grafana
MD
```

## Day 07

```bash
export PHASE=phase0 WEEK=w00 DAY=d07
# Threat model seed
cat > docs/compliance/threat_model_v1.md <<'MD'
# Threat Model v1
- memory poisoning
- tenant isolation breach
- key compromise
MD
```

## Day 08

```bash
export PHASE=phase0 WEEK=w00 DAY=d08
# Data classification playbook
cat > docs/compliance/data_classification_playbook.md <<'MD'
# Data Classification
- GENERAL
- BEHAVIORAL
- PII_ADJACENT
- SENSITIVE
MD
```

## Day 09

```bash
export PHASE=phase0 WEEK=w00 DAY=d09
# Create first ADRs required by phases.md
cat > docs/ADRs/ADR-0001-canonical-commit-hash.md <<'ADR'
# ADR-0001: Canonical Commit Hash Serialization
## Decision
Define deterministic serialization for commit hash inputs.
ADR

cat > docs/ADRs/ADR-0002-key-custody-initial-mode.md <<'ADR'
# ADR-0002: Initial Key Custody Mode
## Decision
Start with hosted/non-production mode in early staging.
ADR

cat > docs/ADRs/ADR-0003-tenant-isolation-strategy.md <<'ADR'
# ADR-0003: Tenant Isolation Strategy
## Decision
Enforce org-scoped isolation in all storage layers.
ADR
```

## Day 10 (Phase 0 Gate)

```bash
export PHASE=phase0 WEEK=w00 DAY=d10
# Gate evidence pack
mkdir -p evidence/phase0/gate
rg -n 'ADR-0001|ADR-0002|ADR-0003' docs/ADRs/* > evidence/phase0/gate/adr_presence.txt
find schemas/openapi schemas/sql .github/workflows -type f | sort > evidence/phase0/gate/scaffold_files.txt

test -f docs/ADRs/ADR-0001-canonical-commit-hash.md
test -f docs/ADRs/ADR-0002-key-custody-initial-mode.md
test -f docs/ADRs/ADR-0003-tenant-isolation-strategy.md

echo "PHASE0_GATE_PASS" > evidence/phase0/gate/result.txt
```

---

## 5. Weekly Day-by-Day Pattern (Used for Phases A-D)

For each week in Phases A-D, run these exact day profiles:

## Day 1 (Plan + Contracts)

```bash
# Pull phase/week objectives and select vertical slices
rg -n "^## ${PHASE}" docs/phases.md || true
# Update backlog notes
mkdir -p planning/$PHASE/$WEEK
```

## Day 2 (Core Implementation)

```bash
# Implement primary workstream code and schema changes
# Run quick unit tests after each slice
if [ -f pyproject.toml ]; then uv run pytest tests/unit -q; fi
if [ -f package.json ]; then npm test -- --runInBand --testPathPattern=unit || true; fi
```

## Day 3 (Integration + Security)

```bash
if [ -f pyproject.toml ]; then uv run pytest tests/integration -q; fi
if [ -d tests/security ]; then
  if [ -f pyproject.toml ]; then uv run pytest tests/security -q; fi
fi
```

## Day 4 (Performance + Resilience)

```bash
mkdir -p artifacts/load artifacts/chaos
# Example k6 runs if scripts exist
if [ -f tests/load/ingest.js ]; then
  k6 run tests/load/ingest.js --summary-export artifacts/load/ingest.json
fi
if [ -f tests/load/retrieve.js ]; then
  k6 run tests/load/retrieve.js --summary-export artifacts/load/retrieve.json
fi
```

## Day 5 (Gate Rehearsal + Evidence)

```bash
mkdir -p evidence/$PHASE/$WEEK/gate_rehearsal
# contract tests
if command -v schemathesis >/dev/null 2>&1 && [ -f schemas/openapi/v1/core.yaml ]; then
  schemathesis run schemas/openapi/v1/core.yaml --checks all > evidence/$PHASE/$WEEK/gate_rehearsal/schemathesis_core.txt
fi
if command -v schemathesis >/dev/null 2>&1 && [ -f schemas/openapi/v1/governance.yaml ]; then
  schemathesis run schemas/openapi/v1/governance.yaml --checks all > evidence/$PHASE/$WEEK/gate_rehearsal/schemathesis_governance.txt
fi
```

---

## 6. Phase A (Weeks 1-8) Detailed Daily Run Instructions

Weekly objective progression:
- **W01** schema + migrations baseline (`commits`, `commit_parents`, `memory_nodes`, `outbox`).
- **W02** commit immutability and parent cardinality triggers.
- **W03** write path transaction + outbox relay.
- **W04** projection consumers + idempotency.
- **W05** retrieval scoring + `as_of_commit` support.
- **W06** tenant isolation implementation across stores.
- **W07** Python SDK + minimal dashboard.
- **W08** load hardening + Phase A gate.

Daily command pack for each week (D1..D5): run Section 5 + commands below.

### Phase A Extra Day Commands

```bash
# Invariant tests (Phase A required set)
if [ -f pyproject.toml ] && [ -d tests/invariants ]; then
  uv run pytest tests/invariants -q -k "INV_01 or INV_03 or INV_04 or INV_06 or INV_08 or INV_09 or INV_10"
fi

# Isolation suite
if [ -f pyproject.toml ] && [ -d tests/security ]; then
  uv run pytest tests/security -q -k "tenant_isolation"
fi
```

### Phase A Gate Command Pack (Week 8 Day 5)

```bash
mkdir -p evidence/phaseA/gate

# Deterministic replay check
if [ -f pyproject.toml ] && [ -d tests/integration ]; then
  uv run pytest tests/integration -q -k "deterministic_replay" | tee evidence/phaseA/gate/deterministic_replay.log
fi

# Load checks (expects k6 summaries)
INGEST_P99=$(jq -r '.metrics.http_req_duration.values["p(99)"] // .metrics.http_req_duration["p(99)"] // 999999' artifacts/load/ingest.json 2>/dev/null || echo 999999)
RETRIEVE_P99=$(jq -r '.metrics.http_req_duration.values["p(99)"] // .metrics.http_req_duration["p(99)"] // 999999' artifacts/load/retrieve.json 2>/dev/null || echo 999999)

echo "ingest_p99_ms=$INGEST_P99" | tee evidence/phaseA/gate/load_metrics.txt
echo "retrieve_p99_ms=$RETRIEVE_P99" | tee -a evidence/phaseA/gate/load_metrics.txt

awk -v v="$INGEST_P99" 'BEGIN{exit (v<=80)?0:1}'
awk -v v="$RETRIEVE_P99" 'BEGIN{exit (v<=350)?0:1}'

echo "PHASEA_GATE_PASS" > evidence/phaseA/gate/result.txt
```

---

## 7. Phase B (Weeks 9-16) Detailed Daily Run Instructions

Weekly objective progression:
- **W09** branch lifecycle endpoints.
- **W10** PR create/list/review/merge APIs.
- **W11** conflict endpoints and resolution flow.
- **W12** intent classifier integration + sandbox fallback.
- **W13** signed commit enforcement + tamper tests.
- **W14** RBAC matrix enforcement.
- **W15** audit traces + reproducibility.
- **W16** Phase B gate.

Daily command pack for each week (D1..D5): run Section 5 + commands below.

### Phase B Extra Day Commands

```bash
# Governance contract coverage
if command -v schemathesis >/dev/null 2>&1 && [ -f schemas/openapi/v1/governance.yaml ]; then
  schemathesis run schemas/openapi/v1/governance.yaml --checks all | tee artifacts/contract/governance_contract.log
fi

# Security + poisoning
if [ -f pyproject.toml ] && [ -d tests/security ]; then
  uv run pytest tests/security -q -k "rbac or poisoning or signature or tamper"
fi
```

### Phase B Gate Command Pack (Week 16 Day 5)

```bash
mkdir -p evidence/phaseB/gate artifacts/security

# Example metric extraction from poisoning report json
# Expected JSON keys:
# {"blocked_or_sandboxed_rate":0.97,"false_block_rate":0.015,"pr_diff_precision":0.93,"pr_diff_recall":0.91}
POISON_JSON="artifacts/security/poisoning_metrics.json"

BLOCK_RATE=$(jq -r '.blocked_or_sandboxed_rate // 0' "$POISON_JSON")
FALSE_BLOCK=$(jq -r '.false_block_rate // 1' "$POISON_JSON")
PR_PREC=$(jq -r '.pr_diff_precision // 0' "$POISON_JSON")
PR_REC=$(jq -r '.pr_diff_recall // 0' "$POISON_JSON")

awk -v v="$BLOCK_RATE" 'BEGIN{exit (v>=0.95)?0:1}'
awk -v v="$FALSE_BLOCK" 'BEGIN{exit (v<=0.02)?0:1}'
awk -v v="$PR_PREC" 'BEGIN{exit (v>=0.90)?0:1}'
awk -v v="$PR_REC" 'BEGIN{exit (v>=0.90)?0:1}'

echo "PHASEB_GATE_PASS" > evidence/phaseB/gate/result.txt
```

---

## 8. Phase C (Weeks 17-28) Detailed Daily Run Instructions

Weekly objective progression:
- **W17-W18** semantic diff service + ANN candidate retrieval.
- **W19-W20** NLI contradiction and conflict routing.
- **W21-W22** graph projection + consolidation worker.
- **W23-W24** relational memory + lawful basis enforcement.
- **W25** deletion propagation + backup SLA verification.
- **W26** embedding migration tooling.
- **W27** external pentest and fixes.
- **W28** GA gate run.

Daily command pack for each week (D1..D5): run Section 5 + commands below.

### Phase C Extra Day Commands

```bash
# ML eval
if [ -f pyproject.toml ] && [ -d tests/ml-eval ]; then
  uv run pytest tests/ml-eval -q | tee artifacts/ml/phase_c_eval.log
fi

# Chaos checks
if [ -f pyproject.toml ] && [ -d tests/chaos ]; then
  uv run pytest tests/chaos -q | tee artifacts/chaos/phase_c_chaos.log
fi
```

### Phase C Gate Command Pack (Week 28 Day 5)

```bash
mkdir -p evidence/phaseC/gate artifacts/ml artifacts/cost

# Expected JSON keys in artifacts/ml/phase_c_metrics.json:
# {"nli_f1":0.84,"nli_false_positive":0.04,"retrieval_ndcg10":0.75,"consolidation_quality":0.96}
ML_JSON="artifacts/ml/phase_c_metrics.json"
COST_JSON="artifacts/cost/phase_c_cost_24h.json"

NLI_F1=$(jq -r '.nli_f1 // 0' "$ML_JSON")
NLI_FP=$(jq -r '.nli_false_positive // 1' "$ML_JSON")
NDCG=$(jq -r '.retrieval_ndcg10 // 0' "$ML_JSON")
CONS_Q=$(jq -r '.consolidation_quality // 0' "$ML_JSON")

AVG_WRITE=$(jq -r '.avg_write_cost // 999' "$COST_JSON")
AVG_RETRIEVE=$(jq -r '.avg_retrieve_cost // 999' "$COST_JSON")
P95_WRITE=$(jq -r '.p95_write_cost // 999' "$COST_JSON")
P95_RETRIEVE=$(jq -r '.p95_retrieve_cost // 999' "$COST_JSON")

awk -v v="$NLI_F1" 'BEGIN{exit (v>=0.82)?0:1}'
awk -v v="$NLI_FP" 'BEGIN{exit (v<=0.05)?0:1}'
awk -v v="$NDCG" 'BEGIN{exit (v>=0.72)?0:1}'
awk -v v="$CONS_Q" 'BEGIN{exit (v>=0.95)?0:1}'
awk -v v="$AVG_WRITE" 'BEGIN{exit (v<=0.0003)?0:1}'
awk -v v="$AVG_RETRIEVE" 'BEGIN{exit (v<=0.0002)?0:1}'
awk -v p95="$P95_WRITE" -v avg="$AVG_WRITE" 'BEGIN{exit (p95<=2*avg)?0:1}'
awk -v p95="$P95_RETRIEVE" -v avg="$AVG_RETRIEVE" 'BEGIN{exit (p95<=2*avg)?0:1}'

echo "PHASEC_GATE_PASS" > evidence/phaseC/gate/result.txt
```

---

## 9. Phase D (Weeks 29-52) Detailed Daily Run Instructions

Weekly objective progression:
- **W29-W34** sovereign packaging + self-hosted model profile.
- **W35-W38** CUSTOMER_KMS enterprise path.
- **W39-W42** air-gapped validation + network capture automation.
- **W43-W46** ecosystem integrations (TS SDK, connectors, CLI).
- **W47-W50** scale + DR drills.
- **W51-W52** enterprise gate and release package.

Daily command pack for each week (D1..D5): run Section 5 + commands below.

### Phase D Extra Day Commands

```bash
# Sovereign packaging
if [ -d infra/helm ]; then
  find infra/helm -type f | sort > artifacts/release/helm_manifest_files.txt
fi

# DR rehearsal artifacts
mkdir -p artifacts/dr
```

### Phase D Gate Command Pack (Week 52 Day 5)

```bash
mkdir -p evidence/phaseD/gate artifacts/network artifacts/dr artifacts/multiagent

# Expected JSON keys in artifacts/multiagent/propagation.json:
# {"p95_propagation_minutes":8.5}
P95_PROP_MIN=$(jq -r '.p95_propagation_minutes // 999' artifacts/multiagent/propagation.json)
awk -v v="$P95_PROP_MIN" 'BEGIN{exit (v<=10)?0:1}'

# Network capture check (should be empty for external DNS)
# Expected file: artifacts/network/external_dns_hits.txt
if [ -f artifacts/network/external_dns_hits.txt ]; then
  test ! -s artifacts/network/external_dns_hits.txt
fi

echo "PHASED_GATE_PASS" > evidence/phaseD/gate/result.txt
```

---

## 10. Gate Review Commands (Every Phase End)

```bash
PHASE_GATE_DIR="evidence/$PHASE/gate"
mkdir -p "$PHASE_GATE_DIR"

# Collect all phase evidence pointers
find "evidence/$PHASE" -type f | sort > "$PHASE_GATE_DIR/evidence_index.txt"

# Record unresolved severity markers if tracked
if [ -f docs/risk_register.csv ]; then
  rg -n 'P0|P1' docs/risk_register.csv > "$PHASE_GATE_DIR/open_sev_findings.txt" || true
fi

# Manual sign-off placeholder
cat > "$PHASE_GATE_DIR/supervisor_signoff.md" <<'MD'
# Supervisor Sign-off
- phase:
- date:
- decision: GO | NO-GO
- blockers:
- required follow-ups:
MD
```

## 10.1 Release-State Gate Checks

Cloud GA candidate check (Phase A/B/C must be green):

```bash
test -f evidence/phaseA/gate/result.txt
test -f evidence/phaseB/gate/result.txt
test -f evidence/phaseC/gate/result.txt
grep -q 'PHASEA_GATE_PASS' evidence/phaseA/gate/result.txt
grep -q 'PHASEB_GATE_PASS' evidence/phaseB/gate/result.txt
grep -q 'PHASEC_GATE_PASS' evidence/phaseC/gate/result.txt
echo "CLOUD_GA_CANDIDATE_PASS"
```

Enterprise production-ready check (Phase A/B/C/D must be green):

```bash
test -f evidence/phaseA/gate/result.txt
test -f evidence/phaseB/gate/result.txt
test -f evidence/phaseC/gate/result.txt
test -f evidence/phaseD/gate/result.txt
grep -q 'PHASEA_GATE_PASS' evidence/phaseA/gate/result.txt
grep -q 'PHASEB_GATE_PASS' evidence/phaseB/gate/result.txt
grep -q 'PHASEC_GATE_PASS' evidence/phaseC/gate/result.txt
grep -q 'PHASED_GATE_PASS' evidence/phaseD/gate/result.txt
echo "ENTERPRISE_PRODUCTION_READY_PASS"
```

---

## 11. Rollback / Backout Command Pack

Use when rollback triggers in `docs/phases.md` are hit.

```bash
set -euo pipefail
ROLLBACK_TS="$(date -u +%Y%m%dT%H%M%SZ)"
RB_DIR="evidence/rollback/$ROLLBACK_TS"
mkdir -p "$RB_DIR"

# Freeze merge signal (project-specific automation should enforce this)
echo "freeze_merges=true" > "$RB_DIR/freeze_flag.txt"

# Record current state
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short > "$RB_DIR/git_status.txt"
  git log --oneline -n 50 > "$RB_DIR/git_log.txt"
fi

# Placeholders for rollback execution commands (fill per incident):
cat > "$RB_DIR/rollback_commands.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
# Example:
# migrate down 1
# restore projection snapshot
# replay canonical commit log
SH
chmod +x "$RB_DIR/rollback_commands.sh"

# Post-rollback validation
cat > "$RB_DIR/post_rollback_validation.md" <<'MD'
- invariant suite rerun: pending
- isolation suite rerun: pending
- contract tests rerun: pending
- load sanity rerun: pending
MD
```

---

## 12. Definition of Done for AI Daily Delivery

A day is complete only if all are true:
- planned slices implemented,
- relevant tests run and captured,
- evidence artifacts written,
- risks/ADRs updated,
- supervisor decision requested.

If any item fails, mark day status as `BLOCKED` and stop scope expansion.

---

## 13. First-Day Quickstart

Run this exact sequence on the first active delivery day:

```bash
set -euo pipefail
PRD_PATH="$(cat docs/PRD_CANONICAL.txt)"; test -f "$PRD_PATH"
export PHASE=phase0 WEEK=w00 DAY=d01 RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
export EVIDENCE_DIR="evidence/$PHASE/$WEEK/$DAY-$RUN_TS"
mkdir -p "$EVIDENCE_DIR"

mkdir -p services sdk infra/{terraform,kubernetes,helm} schemas/{sql,openapi/v1,events} tests/{unit,integration,load,chaos,security,ml-eval} docs/{ADRs,runbooks,compliance} evidence
find services sdk infra schemas tests docs -maxdepth 2 -type d | sort | tee "$EVIDENCE_DIR/tree.txt"

echo "DAY_COMPLETE: phase0 w00 d01" | tee "$EVIDENCE_DIR/day_complete.txt"
```

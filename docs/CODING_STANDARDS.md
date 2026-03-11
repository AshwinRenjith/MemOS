# MemoryOS — Coding Standards

> This document is binding. Deviations require an ADR with supervisor approval.

---

## 1. Language & Runtime

| Stack         | Version     | Usage                                    |
|---------------|-------------|------------------------------------------|
| Python        | ≥ 3.11      | Services, SDK, tests, migrations         |
| TypeScript    | ≥ 5.5       | TypeScript SDK (Phase D)                 |
| SQL           | PostgreSQL 16| Canonical data store, migrations         |
| Protobuf/JSON | —           | Event schemas (Kafka)                    |

---

## 2. Code Quality Rules

### 2.1 Deterministic Behavior

- **No implicit side effects.** Functions must declare their effects in type signatures or docstrings.
- **No global mutable state.** Configuration is injected via `pydantic-settings`, never via module-level singletons.
- **No `time.time()` in business logic.** Use an injectable `Clock` protocol so time can be controlled in tests.
- **No random values in business logic.** Use injectable ID generators for UUIDs.

### 2.2 Type Safety

- **All public functions must have complete type annotations.** No `Any` without a documented justification.
- **Pydantic models for all API boundaries.** No raw `dict` crossing an API or module boundary.
- **mypy strict mode must pass.** No `# type: ignore` without an inline justification comment.

### 2.3 Error Handling

- **Domain exceptions only.** All raised exceptions must inherit from `MemoryOSError`.
- **No bare `except`.** Always catch specific exception types.
- **API errors return RFC 7807 Problem+JSON.** Never expose stack traces in production responses.

### 2.4 Logging

- **Use `structlog` for all logging.** No `print()` statements. No `logging.getLogger()`.
- **Log levels:** `debug` for internals, `info` for operations, `warning` for degraded modes, `error` for failures, `critical` for invariant violations.
- **Every log line must include:** `org_id`, `repo_id` (if applicable), `trace_id`, `operation`.

---

## 3. Architecture Rules

### 3.1 Module Boundaries

```
services/memory-core/
├── src/memoryos/
│   ├── api/          # FastAPI routers — HTTP boundary only
│   ├── domain/       # Domain models, value objects, state machines
│   ├── engine/       # Memory engine, retrieval, scoring
│   ├── vcs/          # Version control: commits, branches, PRs
│   ├── security/     # Auth, RBAC, key custody, signing
│   ├── privacy/      # Data classification, .memignore, deletion
│   ├── infra/        # Database, Qdrant, Redis, Kafka adapters
│   └── observability/# Telemetry, metrics, structured logging
```

- **API layer never contains business logic.** It validates input, calls domain/engine, formats output.
- **Domain layer has ZERO infrastructure imports.** No SQLAlchemy, no Qdrant, no Redis in `domain/`.
- **Infrastructure adapters implement domain protocols.** Dependency inversion enforced via Python `Protocol` types.

### 3.2 Dependency Direction

```
API → Engine/VCS → Domain ← Infrastructure (adapters)
```

Inner layers never import outer layers. Violations are caught by import linting rules.

### 3.3 State Machines

- All state machines (Branch, PR, Conflict) must be implemented as **explicit transition functions**, not ad-hoc `if/elif` chains.
- Pattern: `(current_state, event) → (new_state, side_effects)`.
- Every transition must be unit-tested.
- Invalid transitions must raise `InvalidStateTransitionError`.

---

## 4. Database & Migration Rules

- **Every migration must be reversible.** Each `.sql` migration file must have a corresponding `down` section or rollback strategy documented in the PR.
- **Migrations are sequential.** Named `XXXX_description.sql` with zero-padded 4-digit prefix.
- **No destructive DDL in production migrations** without supervisor approval and a documented backout plan.
- **RLS policies are mandatory** on every table containing `org_id`.
- **Commit table is append-only.** No `UPDATE` or `DELETE` triggers must exist. Verified by invariant tests.

---

## 5. Testing Standards

| Test Type     | Location               | Speed Target   | When to Run          |
|---------------|------------------------|----------------|----------------------|
| Unit          | `tests/unit/`          | < 100ms each   | Every commit         |
| Integration   | `tests/integration/`   | < 5s each      | Every PR             |
| Invariant     | `tests/invariants/`    | < 10s each     | Every PR             |
| Security      | `tests/security/`      | < 10s each     | Every PR             |
| Load          | `tests/load/`          | minutes        | Weekly + gate        |
| Chaos         | `tests/chaos/`         | minutes        | Pre-gate             |
| ML Eval       | `tests/ml-eval/`       | minutes        | Model update + gate  |

- **Every feature ships with tests.** No merge without corresponding tests.
- **Invariant tests (INV-01..INV-10) never regress.** A regression in invariant tests is a P0 blocker.
- **Test isolation:** each test must clean up after itself. No test-order dependencies.

---

## 6. Git & Branch Policy

| Branch         | Purpose                         | Merge Policy               |
|----------------|----------------------------------|-----------------------------|
| `main`         | Production-ready code            | PR required, 1 approval     |
| `develop`      | Integration branch               | PR required                  |
| `feature/*`    | Feature development              | Squash merge to `develop`    |
| `fix/*`        | Bug fixes                        | Squash merge to `develop`    |
| `release/*`    | Release preparation              | Merge to `main` + tag        |
| `hotfix/*`     | Production hotfixes              | Merge to `main` + `develop`  |

- **Commit messages:** Conventional Commits format (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`).
- **No force-push to `main` or `develop`.**
- **Every PR must reference:** the Phase, Workstream, and relevant INV/ADR numbers.

---

## 7. Security Standards

- **No secrets in code.** Secrets injected via environment variables or KMS.
- **No `eval()`, `exec()`, or dynamic SQL construction.** Use parameterized queries only.
- **All HTTP endpoints require authentication.** No unauthenticated endpoints except health checks.
- **TLS 1.3 enforced** on all service-to-service communication.
- **Dependency scanning** via `pip-audit` in CI.

---

## 8. Documentation Standards

- **Every public module** has a module-level docstring explaining purpose and usage.
- **Every public function** has a docstring with: description, args, returns, raises.
- **Every ADR** follows the template in `docs/ADRs/ADR_TEMPLATE.md`.
- **Every runbook** follows the template in `docs/runbooks/RUNBOOK_TEMPLATE.md`.

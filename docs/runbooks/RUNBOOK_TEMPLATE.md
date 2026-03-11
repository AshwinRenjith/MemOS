# Runbook Template

> Use this template for all operational runbooks.
> Every feature must ship with a runbook update (docs/CODING_STANDARDS.md §8).

---

| Field             | Value                                      |
|-------------------|--------------------------------------------|
| **Service**       | (e.g., memory-core, memory-worker)         |
| **Owner**         | (team or individual)                       |
| **Last Updated**  | YYYY-MM-DD                                 |
| **PRD Section**   | §X.X                                       |
| **Alert Name**    | (from PRD §10.4, if applicable)            |

---

## 1. Overview

Brief description of what this runbook covers and when to use it.

---

## 2. Detection

### Automated Alerts
- Alert name and threshold
- Dashboard link
- PagerDuty / on-call escalation path

### Manual Detection
- Symptoms to look for
- Log queries to run
- Metrics to check

---

## 3. Impact Assessment

| Severity | Condition                                          |
|----------|----------------------------------------------------|
| P0       | Data loss, tenant isolation breach, total outage   |
| P1       | SLO breach, degraded service for multiple orgs     |
| P2       | Elevated latency, single org affected              |
| P3       | Non-user-facing, monitoring gap                    |

---

## 4. Response Steps

### Step 1: Verify
```bash
# Commands to verify the issue
```

### Step 2: Mitigate
```bash
# Commands to mitigate immediately
```

### Step 3: Investigate
```bash
# Commands and queries for root cause analysis
```

### Step 4: Resolve
```bash
# Commands to fully resolve
```

### Step 5: Verify Resolution
```bash
# Commands to confirm the issue is resolved
```

---

## 5. Rollback Procedure

If mitigation fails or resolution introduces new issues:

```bash
# Rollback commands
```

---

## 6. Post-Incident

- [ ] Incident summary written
- [ ] Root cause identified
- [ ] Timeline documented
- [ ] Follow-up action items created
- [ ] Runbook updated with learnings
- [ ] Evidence artifacts saved to `evidence/`

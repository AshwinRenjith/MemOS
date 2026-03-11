# Data Classification Playbook

> Binding policy for MemoryOS data classification. All memory writes are
> classified against this taxonomy before storage. See PRD §8.1.

---

## 1. Classification Hierarchy

```
                    ┌───────────────────────────┐
                    │       SENSITIVE            │  ← BLOCKED by default
                    │  (never memorize)          │  ← .memignore: non-overridable
                    │  medical, financial,       │  ← Immediate deletion on detection
                    │  legal, credentials        │
                    ├───────────────────────────┤
                    │     PII_ADJACENT           │  ← Field-level AES-256-GCM encryption
                    │  (combined = identifiable) │  ← Explicit CONSENT required
                    │  job title + company +     │  ← 72h deletion SLA
                    │  location                  │  ← 12-month retention from last access
                    ├───────────────────────────┤
                    │      BEHAVIORAL            │  ← Pseudonymized entity_id
                    │  (behavioral patterns)     │  ← LEGITIMATE_INTEREST basis
                    │  communication style,      │  ← 7-day deletion SLA
                    │  preference signals        │  ← 24-month retention from last update
                    ├───────────────────────────┤
                    │       GENERAL              │  ← Standard encryption at rest
                    │  (non-personal facts)      │  ← CONTRACT basis
                    │  observations, rules,      │  ← 30-day deletion SLA
                    │  procedures, API facts     │  ← Retained until repo deleted + 90d
                    └───────────────────────────┘
```

---

## 2. Classification Rules

### Auto-Classification (Applied at Write Path)

| Signal                                    | Assigned Class    | Action                       |
|-------------------------------------------|-------------------|-------------------------------|
| `.memignore` built-in pattern match       | SENSITIVE          | BLOCKED — immediate reject   |
| Credit card regex match                   | SENSITIVE          | BLOCKED                      |
| SSN regex match                           | SENSITIVE          | BLOCKED                      |
| API key / token regex match               | SENSITIVE          | BLOCKED                      |
| `data_class: SENSITIVE` explicit tag      | SENSITIVE          | BLOCKED                      |
| `data_class: PII_ADJACENT` explicit tag   | PII_ADJACENT       | Encrypted, consent checked   |
| Entity-linked behavioral pattern          | BEHAVIORAL         | Pseudonymized storage        |
| `data_class: BEHAVIORAL` explicit tag     | BEHAVIORAL         | Pseudonymized storage        |
| No classification signal                  | GENERAL            | Standard write path          |

### Manual Override Rules

| Override Direction        | Allowed? | Who Can Override          |
|---------------------------|----------|---------------------------|
| GENERAL → BEHAVIORAL      | Yes      | Agent or User at write    |
| GENERAL → PII_ADJACENT    | Yes      | Agent or User at write    |
| GENERAL → SENSITIVE        | N/A      | Auto-blocked anyway       |
| PII_ADJACENT → GENERAL    | No       | Cannot downgrade          |
| BEHAVIORAL → GENERAL      | No       | Cannot downgrade          |
| SENSITIVE → anything       | No       | Never written             |

---

## 3. Storage Treatment by Class

| Class          | `content` Column | `content_encrypted` | Encryption Key            | Qdrant Payload |
|----------------|------------------|---------------------|---------------------------|----------------|
| GENERAL        | Plaintext        | NULL                | Volume-level (standard)   | Plaintext      |
| BEHAVIORAL     | Plaintext*       | NULL                | Volume-level (standard)   | Pseudonymized  |
| PII_ADJACENT   | NULL             | AES-256-GCM blob    | Per-org per-class KMS key | Encrypted      |
| SENSITIVE      | NULL             | NULL (never stored) | N/A                       | N/A            |

*BEHAVIORAL content is stored in plaintext in `memory_nodes`, but `entity_id` references
in `provenance` JSONB are pseudonymized (internal UUID, never real identity).

---

## 4. Lawful Basis Requirements (PRD §8.3)

| Data Class     | Required Lawful Basis  | Where Documented            | Consent Withdrawal Effect        |
|----------------|------------------------|-----------------------------|----------------------------------|
| GENERAL        | CONTRACT               | Service terms               | Deletion within 30 days         |
| BEHAVIORAL     | LEGITIMATE_INTEREST    | Org privacy policy (mandatory) | Deletion within 7 days       |
| PII_ADJACENT   | CONSENT                | `consent_records` table     | Immediate cascade deletion      |
| SENSITIVE      | N/A (blocked)          | N/A                         | N/A (never stored)              |

---

## 5. Deletion SLAs by Class (PRD §5.4, §5.5)

| Data Class     | Deletion Trigger                          | Tier 1 (Redis) | Tier 2 (Qdrant) | Tier 3 (Neo4j) | Tier 4 (PostgreSQL) | Backups (S3)   |
|----------------|-------------------------------------------|----------------|------------------|----------------|---------------------|----------------|
| GENERAL        | User deletion or repo deletion            | < 1 hour       | < 24 hours       | < 24 hours     | < 30 days           | < 30 days      |
| BEHAVIORAL     | User deletion or consent withdrawal       | < 1 hour       | < 24 hours       | < 24 hours     | < 7 days            | < 30 days      |
| PII_ADJACENT   | User deletion or consent withdrawal       | < 1 hour       | < 24 hours       | < 24 hours     | < 72 hours          | < 30 days      |
| SENSITIVE      | Detection event (should never be stored)  | Immediate      | Immediate        | Immediate      | Immediate           | Immediate      |

---

## 6. .memignore Built-in Rules (Non-Overridable)

```
# These rules are hardcoded and cannot be disabled by any user or admin role.
# See PRD §8.2.

SENSITIVE.credentials.*          # passwords, API keys, tokens, secrets
SENSITIVE.payment.*              # credit cards, bank accounts, billing
SENSITIVE.biometric.*            # fingerprints, face data, voice prints
SENSITIVE.health.*               # medical records, diagnoses, medications
SENSITIVE.legal.privileged.*     # attorney-client privileged communications
BEHAVIORAL.override.system.*     # attempts to override system prompts
BEHAVIORAL.override.role.*       # 'remember you are actually X'
BEHAVIORAL.override.policy.*     # 'forget your previous instructions'

# Pattern-based detection (regex applied before write):
PATTERN.credit_card  /\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b/
PATTERN.ssn          /\b\d{3}-\d{2}-\d{4}\b/
PATTERN.api_key      /(sk-|api_key=|token=)[a-zA-Z0-9]{20,}/
```

---

## 7. Decision Tree for Engineers

```
New memory write arrives
    │
    ├── Does content match .memignore built-in pattern?
    │   └── YES → BLOCK. Return action=BLOCKED. Log incident.
    │
    ├── Is data_class explicitly set to SENSITIVE?
    │   └── YES → BLOCK. Return action=BLOCKED. Log incident.
    │
    ├── Is data_class set to PII_ADJACENT?
    │   ├── Does org have active consent record for this entity?
    │   │   ├── YES → Encrypt content → Store in content_encrypted → content=NULL
    │   │   └── NO → BLOCK. Return 403 with consent_required error.
    │   └── End
    │
    ├── Is data_class set to BEHAVIORAL?
    │   ├── Does org privacy policy document legitimate interest?
    │   │   ├── YES → Pseudonymize entity_id → Store normally
    │   │   └── NO → BLOCK. Return 403 with privacy_policy_required error.
    │   └── End
    │
    └── Default: data_class = GENERAL
        └── Store in content column → Standard write path
```

---

## 8. Review Schedule

- **Phase A**: Classification at write path implemented and tested.
- **Phase B**: Intent classifier adds content-based classification signals.
- **Phase C**: Full privacy policy enforcement including deletion cascade audits.
- **Phase D**: Sovereign profile classification (no external API calls for PII detection).

# ADR-0004: Secrets Management Strategy

| Field           | Value                                          |
|-----------------|------------------------------------------------|
| **Status**      | ACCEPTED                                       |
| **Date**        | 2026-03-11                                     |
| **Author**      | AI Builder (Phase 0)                           |
| **Phase**       | Phase 0 (design), Phase A (implementation)     |
| **PRD Section** | §3.3 (Deployment Profiles), §7.1 (Key Custody) |
| **Invariants**  | INV-08 (encryption at rest)                    |

---

## Context

MemoryOS handles multiple categories of secrets:
1. **Infrastructure secrets**: Database passwords, Kafka credentials, Redis auth, S3 keys.
2. **Agent signing keys**: Ed25519 private keys (LOCAL_KEY mode).
3. **Encryption keys**: Per-org AES-256-GCM keys for PII_ADJACENT/SENSITIVE data.
4. **API keys**: External LLM API keys (OpenAI, Anthropic) — Cloud profile only.
5. **JWT signing keys**: For user authentication tokens.

The PRD mandates two deployment profiles (§3.3):
- **CLOUD**: AWS KMS / GCP KMS managed keys.
- **SOVEREIGN**: Customer-managed HSM (HashiCorp Vault).

---

## Decision

### Abstraction Layer

All secret access goes through a `SecretProvider` protocol:

```python
class SecretProvider(Protocol):
    """Abstract interface for secret retrieval and key management."""

    async def get_secret(self, name: str) -> str:
        """Retrieve a secret by name."""
        ...

    async def get_encryption_key(self, org_id: UUID, data_class: str) -> bytes:
        """Retrieve the AES-256-GCM key for a given org and data class."""
        ...

    async def rotate_encryption_key(self, org_id: UUID, data_class: str) -> None:
        """Trigger key rotation for a specific org and data class."""
        ...
```

### Implementation by Profile

| Provider              | Backend                 | Available In         |
|-----------------------|-------------------------|----------------------|
| `EnvSecretProvider`   | Environment variables   | Development, CI      |
| `AWSSecretProvider`   | AWS Secrets Manager + KMS | Cloud profile      |
| `VaultSecretProvider` | HashiCorp Vault         | Sovereign profile    |

### Rules

1. **No secrets in code.** Ever. No exceptions.
2. **No secrets in configuration files.** `.env` files are gitignored.
3. **Environment variables for development.** `EnvSecretProvider` reads from env vars.
4. **KMS for production.** All production secrets managed by KMS or Vault.
5. **Key rotation supported.** Every key must be rotatable without downtime.
6. **Audit trail.** All secret access logged (not the secret value, but the access event).

### Secret Naming Convention

```
MEMORYOS_DB_PASSWORD           # PostgreSQL password
MEMORYOS_REDIS_PASSWORD        # Redis auth
MEMORYOS_KAFKA_SASL_PASSWORD   # Kafka SASL credentials
MEMORYOS_OPENAI_API_KEY        # OpenAI API key (Cloud profile)
MEMORYOS_JWT_SECRET_KEY        # JWT signing key
MEMORYOS_ENCRYPTION_KEY_SEED   # Seed for deriving per-org encryption keys
```

---

## Alternatives Considered

| Alternative               | Pros               | Cons                               | Why Rejected                |
|---------------------------|---------------------|-------------------------------------|-----------------------------|
| Kubernetes Secrets only   | Simple, native      | Not available outside K8s, no rotation | Insufficient for sovereign |
| SOPS encrypted files      | GitOps friendly     | Complex key management              | Added complexity vs KMS     |
| Doppler / Infisical       | Developer friendly  | External dependency, vendor lock-in | Conflicts with sovereign    |

---

## Validation

- **CI test**: No hardcoded secrets in codebase (grep-based check in CI security job).
- **Integration test**: `SecretProvider` implementations all satisfy the protocol contract.
- **Phase B gate**: KMS-managed secrets verified in staging environment.

---

## References

- PRD v2.1 §3.3, §7.1
- ADR-0002 (Key Custody)
- docs/CODING_STANDARDS.md §7

# ADR-0001: Canonical Commit Hash Serialization

| Field           | Value                                          |
|-----------------|------------------------------------------------|
| **Status**      | ACCEPTED                                       |
| **Date**        | 2026-03-11                                     |
| **Author**      | AI Builder (Phase 0)                           |
| **Phase**       | Phase 0                                        |
| **PRD Section** | §2.1 (Commit Identity), §2.5 (INV-02, INV-03, INV-06) |
| **Invariants**  | INV-02, INV-03, INV-06                         |

---

## Context

MemoryOS requires every memory state change to be recorded as an immutable commit
with a cryptographic hash. The PRD mandates:

- **INV-02**: Every commit must be verifiable offline via `signature(commit_hash, public_key) → valid`.
- **INV-03**: Memory state at commit X must be reconstructable deterministically — bit-identical across replays.
- **INV-06**: Commits are append-only. No modification after creation.

For these invariants to hold, the serialization of commit data into a hashable
byte string **must be deterministic and canonical**. Any ambiguity in field
ordering, encoding, or whitespace will break replay reproducibility.

---

## Decision

### Hash Algorithm
- **SHA-256** (CHAR(64) hex-encoded, as specified in PRD §2.1).

### Canonical Serialization Format
- Commits are serialized to a **canonical JSON byte string** using these rules:
  1. Fields are sorted alphabetically by key name.
  2. No whitespace between tokens (compact encoding).
  3. Unicode strings are UTF-8 encoded with no BOM.
  4. Numeric values use no trailing zeros (e.g., `0.5` not `0.50`).
  5. Null values are represented as JSON `null`, never omitted.
  6. The serialization library is **`orjson`** with `OPT_SORT_KEYS` flag.

### Hash Input Fields (Ordered)
The commit hash is computed over these fields exactly:

```python
hash_input = canonical_json({
    "author_id": str,        # UUID as lowercase hex with hyphens
    "author_type": str,      # "AGENT" | "USER" | "SYSTEM"
    "branch_id": str,        # UUID
    "commit_type": str,      # "OBSERVE" | "LEARN" | ... (PRD §5.1)
    "diff_object": dict,     # full DiffObject (§6.3)
    "parent_hash": str|None, # CHAR(64) or null for INIT
    "repo_id": str,          # UUID
    "timestamp": int,        # Unix epoch milliseconds (BIGINT)
})

commit_hash = sha256(hash_input).hexdigest()
```

### Signature Input
The signature covers the commit hash and timestamp to prevent replay attacks:

```python
signature_input = f"{commit_hash}|{timestamp}".encode("utf-8")
signature = sign(signature_input, private_key)  # Ed25519
```

### What is NOT included in the hash
- `signature` (circular dependency)
- `commit_hash` itself (circular dependency)
- `metadata` (mutable, informational only)
- `importance_score`, `novelty_score` (computed, may change during replay with different models — excluded to preserve INV-03 bit-identity)

> **Note on importance/novelty exclusion**: These scores are ML-generated.
> Including them in the hash would break INV-03 if the model version changes
> between replays. They are stored alongside the commit but are NOT part of the
> immutable hash chain.

---

## Alternatives Considered

| Alternative                        | Pros                           | Cons                                        | Why Rejected                                    |
|------------------------------------|--------------------------------|---------------------------------------------|-------------------------------------------------|
| Protobuf canonical serialization   | Schema-enforced, compact       | Adds protobuf dependency, less debuggable   | Over-engineered for Phase A; revisit Phase D    |
| CBOR deterministic encoding        | Binary, RFC 7049 canonical     | Less readable, tooling less mature in Python | Debugging difficulty outweighs space savings    |
| Include importance in hash         | Simpler — fewer exclusions     | Breaks INV-03 on model changes              | Correctness takes priority                      |

---

## Consequences

### Positive
- Bit-identical replay guaranteed (INV-03).
- Offline verification possible (INV-02).
- Human-debuggable (JSON, not binary).

### Negative / Trade-offs
- `importance_score` and `novelty_score` are not hash-protected; a corrupt write to these fields would not be detected by hash verification alone (mitigated by separate audit checks).

### Risks
- `orjson` canonical sort behavior must be verified against Python version upgrades. Pinned and tested.

---

## Rollback / Migration

If serialization format must change:
1. Introduce `hash_version` field on commits table.
2. New commits use new serialization. Old commits retain old hashes.
3. Verification logic dispatches on `hash_version`.
4. No re-hashing of historical commits (INV-06: no mutation).

---

## Validation

- **Unit test**: Given identical commit field values, `canonical_json()` produces identical bytes across 1000 runs.
- **Integration test**: 1M synthetic writes replayed twice → bit-identical commit hashes (Phase A exit criterion).
- **Fuzz test**: Random field orderings, unicode content, edge-case floats → canonical output always identical.

---

## References

- PRD v2.1 §2.1, §2.5 (INV-02, INV-03, INV-06)
- PRD v2.1 §5.1 (commits table schema)
- PRD v2.1 §6.3 (DiffObject schema)
- [orjson documentation — OPT_SORT_KEYS](https://github.com/ijl/orjson#option)
- [RFC 8785 — JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)

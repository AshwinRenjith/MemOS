"""
MemoryOS — Version-Controlled Memory Infrastructure for AI

This is the root package for the memory-core service, the modular monolith
that implements the core MemoryOS functionality during Phase A and B.

Architecture (docs/CODING_STANDARDS.md §3.1):
    api/          — FastAPI routers (HTTP boundary only)
    domain/       — Domain models, value objects, state machines
    engine/       — Memory engine, retrieval, scoring
    vcs/          — Version control: commits, branches, PRs
    security/     — Auth, RBAC, key custody, signing
    privacy/      — Data classification, .memignore, deletion
    infra/        — Database, Qdrant, Redis, Kafka adapters
    observability/ — Telemetry, metrics, structured logging

Dependency direction:
    API → Engine/VCS → Domain ← Infrastructure (adapters)
    Inner layers never import outer layers.
"""

__version__ = "0.1.0"

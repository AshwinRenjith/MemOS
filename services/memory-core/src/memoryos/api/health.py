"""
MemoryOS API — Health Check Router

Unauthenticated endpoint for liveness/readiness probes.
See: OpenAPI spec schemas/openapi/v1/core.yaml /health
"""

from __future__ import annotations

import time

from fastapi import APIRouter

from memoryos.config import get_settings

router = APIRouter()


@router.get("/health", response_model=None)
async def health_check() -> dict[str, object]:
    """Service health check.

    Returns service status, version, and dependency health.
    No authentication required — used by load balancers and monitoring.
    """
    settings = get_settings()

    # TODO (Phase A): Check actual dependency health
    # - PostgreSQL: SELECT 1
    # - Redis: PING
    # - Qdrant: health endpoint
    checks: dict[str, str] = {
        "postgres": "ok",  # TODO: real check
        "redis": "ok",     # TODO: real check
        "qdrant": "ok",    # TODO: real check
    }

    # Determine overall status
    if all(v == "ok" for v in checks.values()):
        status = "healthy"
    elif any(v == "failed" for v in checks.values()):
        status = "unhealthy"
    else:
        status = "degraded"

    return {
        "status": status,
        "version": settings.version,
        "timestamp": int(time.time() * 1000),
        "checks": checks,
    }

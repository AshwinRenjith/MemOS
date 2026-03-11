"""
MemoryOS — FastAPI Application Factory

Creates and configures the FastAPI application with middleware,
exception handlers, and routers. This is the HTTP entry point.

See: docs/CODING_STANDARDS.md §3.1 (API layer)
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse

from memoryos.api.health import router as health_router
from memoryos.config import Settings, get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager.

    Startup: initialize database pools, vector store connections, telemetry.
    Shutdown: gracefully close connections.
    """
    settings = get_settings()
    logger.info(
        "memoryos_starting",
        version=settings.version,
        environment=settings.environment,
        deployment_profile=settings.deployment_profile,
    )

    # TODO (Phase A): Initialize database connection pool
    # TODO (Phase A): Initialize Qdrant client factory
    # TODO (Phase A): Initialize Redis client factory
    # TODO (Phase A): Initialize telemetry (tracing, metrics)

    yield

    # Shutdown
    logger.info("memoryos_shutting_down")
    # TODO (Phase A): Close connection pools


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Testable — accepts injected settings."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="MemoryOS",
        description="Version-controlled, auditable memory infrastructure for AI",
        version=settings.version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # --- Middleware ---
    @app.middleware("http")
    async def request_timing_middleware(
        request: Request, call_next: object
    ) -> Response:
        """Add timing headers and structured logging to every request."""
        start = time.perf_counter_ns()
        response: Response = await call_next(request)  # type: ignore[arg-type]
        duration_ms = (time.perf_counter_ns() - start) / 1_000_000

        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Service-Version"] = settings.version

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response

    # --- Exception Handlers ---
    # TODO (Phase A): Add RFC 7807 Problem+JSON exception handlers
    # TODO (Phase A): Add MemoryOSError → HTTP status mapping

    # --- Routers ---
    app.include_router(health_router, prefix="/v1", tags=["Health"])
    # TODO (Phase A): Include memory router
    # TODO (Phase A): Include commits router
    # TODO (Phase B): Include branches router
    # TODO (Phase B): Include pulls router
    # TODO (Phase B): Include conflicts router
    # TODO (Phase B): Include keys router

    return app


# Module-level app instance for uvicorn
app = create_app()

"""
MemoryOS — Configuration (pydantic-settings)

All configuration is injected via environment variables. No global mutable state.
See: docs/CODING_STANDARDS.md §2.1
"""

from __future__ import annotations

from enum import StrEnum, unique
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


@unique
class Environment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@unique
class DeploymentProfile(StrEnum):
    """PRD §3.3: Cloud vs Sovereign deployment profiles."""
    CLOUD = "cloud"
    SOVEREIGN = "sovereign"


class Settings(BaseSettings):
    """Application settings. All values from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MEMORYOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    environment: Environment = Environment.DEVELOPMENT
    deployment_profile: DeploymentProfile = DeploymentProfile.CLOUD
    debug: bool = False
    log_level: str = "INFO"
    service_name: str = "memory-core"
    version: str = "0.1.0"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database (PostgreSQL) ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "memoryos"
    db_user: str = "memoryos_app"
    db_password: str = "change_me_in_production"
    db_pool_min: int = 5
    db_pool_max: int = 20
    db_statement_timeout_ms: int = 30000

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # --- Qdrant ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None

    # --- Kafka ---
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_sasl_password: str | None = None

    # --- Observability ---
    otlp_endpoint: str = "http://localhost:4317"
    traces_sample_rate: float = 1.0  # 100% in dev, 10% in production

    # --- External LLM (Cloud profile only) ---
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # --- JWT ---
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # --- Encryption ---
    encryption_key_seed: str = "change_me_in_production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_sovereign(self) -> bool:
        return self.deployment_profile == DeploymentProfile.SOVEREIGN


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton for application settings.

    Use dependency injection in FastAPI instead of importing this directly.
    This exists primarily for bootstrap/startup code.
    """
    return Settings()

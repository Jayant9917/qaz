"""Dependency readiness probes."""

from time import perf_counter
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import text

from novo.core.config import Settings
from novo.infrastructure.cache import get_redis
from novo.infrastructure.database import get_engine


class DependencyState(BaseModel):
    status: Literal["available", "unavailable", "not_required"]
    required: bool
    latency_ms: float | None = None
    error_code: str | None = None


async def _postgres_state() -> DependencyState:
    started = perf_counter()
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return DependencyState(
            status="available",
            required=True,
            latency_ms=round((perf_counter() - started) * 1000, 2),
        )
    except Exception:
        return DependencyState(
            status="unavailable",
            required=True,
            latency_ms=round((perf_counter() - started) * 1000, 2),
            error_code="postgres_unavailable",
        )


async def _redis_state() -> DependencyState:
    started = perf_counter()
    try:
        await get_redis().ping()
        return DependencyState(
            status="available",
            required=True,
            latency_ms=round((perf_counter() - started) * 1000, 2),
        )
    except Exception:
        return DependencyState(
            status="unavailable",
            required=True,
            latency_ms=round((perf_counter() - started) * 1000, 2),
            error_code="redis_unavailable",
        )


async def check_dependencies(settings: Settings) -> dict[str, DependencyState]:
    if not settings.require_infrastructure_for_readiness:
        return {
            "postgres": DependencyState(status="not_required", required=False),
            "redis": DependencyState(status="not_required", required=False),
        }
    return {
        "postgres": await _postgres_state(),
        "redis": await _redis_state(),
    }

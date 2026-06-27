"""Model call accounting services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import Integer, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from novo.core.request_context import get_request_id
from novo.models.calls import ModelCall
from novo.models.registry import ModelCatalog


@dataclass(slots=True)
class ModelUsageRow:
    provider: str | None
    model_name: str | None
    run_count: int
    token_count: int
    average_latency_ms: float | None
    success_count: int
    failure_count: int
    cost_minor: int


@dataclass(slots=True)
class ModelHealthRow:
    model_id: UUID
    provider: str
    model_key: str
    display_name: str
    enabled: bool
    health_status: str
    recent_run_count: int
    recent_success_rate: float | None
    last_run_at: datetime | None


async def get_model_by_key(db: AsyncSession, provider: str, model_key: str) -> ModelCatalog | None:
    return await db.scalar(
        select(ModelCatalog).where(
            ModelCatalog.provider == provider,
            ModelCatalog.model_key == model_key,
        )
    )


def _estimate_cost_minor(model: ModelCatalog, input_tokens: int, output_tokens: int) -> int:
    pricing = model.pricing if isinstance(model.pricing, dict) else {}
    input_rate = pricing.get("input_minor_per_1k", pricing.get("input_minor", 0))
    output_rate = pricing.get("output_minor_per_1k", pricing.get("output_minor", 0))
    estimated_input = (input_tokens / 1000) * float(input_rate)
    estimated_output = (output_tokens / 1000) * float(output_rate)
    estimated_cost = estimated_input + estimated_output
    return round(estimated_cost)


async def create_model_call(
    db: AsyncSession,
    *,
    owner_id: UUID,
    model: ModelCatalog,
    message_id: UUID | None,
    route_reason: str,
    classification_max: str,
    prompt_hash: str,
    input_tokens: int,
) -> ModelCall:
    call = ModelCall(
        owner_id=owner_id,
        message_id=message_id,
        model_id=model.id,
        route_reason=route_reason,
        classification_max=classification_max,
        status="running",
        input_tokens=input_tokens,
        output_tokens=0,
        cached_tokens=0,
        latency_ms=None,
        cost_minor=0,
        currency=str((model.pricing or {}).get("currency", "USD")),
        prompt_hash=prompt_hash,
        trace_id=get_request_id(),
    )
    db.add(call)
    await db.flush()
    return call


async def complete_model_call(
    db: AsyncSession,
    *,
    call: ModelCall,
    response_text: str,
    output_tokens: int,
    latency_ms: int,
) -> ModelCall:
    call.status = "completed"
    call.output_tokens = output_tokens
    call.latency_ms = latency_ms
    call.cost_minor = _estimate_cost_minor(call.model, call.input_tokens, output_tokens)
    call.currency = str((call.model.pricing or {}).get("currency", "USD"))
    call.response_hash = sha256(response_text.encode("utf-8")).hexdigest()
    call.finished_at = datetime.now(UTC)
    call.error_code = None
    call.error_detail_safe = None
    await db.flush()
    return call


async def fail_model_call(
    db: AsyncSession,
    *,
    call: ModelCall,
    error_code: str,
    error_detail_safe: str,
) -> ModelCall:
    call.status = "failed"
    call.error_code = error_code
    call.error_detail_safe = error_detail_safe
    call.finished_at = datetime.now(UTC)
    await db.flush()
    return call


async def list_model_usage(db: AsyncSession) -> list[ModelUsageRow]:
    rows = await db.execute(
        select(
            ModelCatalog.provider,
            ModelCatalog.model_key,
            func.count(ModelCall.id),
            func.sum(ModelCall.output_tokens + ModelCall.input_tokens),
            func.avg(ModelCall.latency_ms),
            func.sum(func.cast(ModelCall.status == "completed", Integer)),
            func.sum(ModelCall.cost_minor),
        )
        .join(ModelCall, ModelCall.model_id == ModelCatalog.id)
        .group_by(ModelCatalog.provider, ModelCatalog.model_key)
        .order_by(ModelCatalog.provider.asc(), ModelCatalog.model_key.asc())
    )
    items: list[ModelUsageRow] = []
    for (
        provider,
        model_name,
        run_count,
        token_sum,
        avg_latency,
        success_sum,
        cost_sum,
    ) in rows.all():
        run_count_int = int(run_count or 0)
        success_int = int(success_sum or 0)
        items.append(
            ModelUsageRow(
                provider=provider,
                model_name=model_name,
                run_count=run_count_int,
                token_count=int(token_sum or 0),
                average_latency_ms=float(avg_latency) if avg_latency is not None else None,
                success_count=success_int,
                failure_count=run_count_int - success_int,
                cost_minor=int(cost_sum or 0),
            )
        )
    return items


async def list_model_health(db: AsyncSession) -> list[ModelHealthRow]:
    recent_runs = await db.execute(
        select(
            ModelCall.model_id,
            func.count(ModelCall.id),
            func.sum(func.cast(ModelCall.status == "completed", Integer)),
            func.max(ModelCall.finished_at),
        )
        .where(ModelCall.started_at >= func.now() - text("INTERVAL '7 days'"))
        .group_by(ModelCall.model_id)
    )
    usage_map: dict[UUID, tuple[int, int, datetime | None]] = {}
    for model_id, run_count, success_count, last_run_at in recent_runs.all():
        usage_map[model_id] = (int(run_count or 0), int(success_count or 0), last_run_at)

    items: list[ModelHealthRow] = []
    models = await db.scalars(
        select(ModelCatalog).order_by(
            ModelCatalog.provider.asc(), ModelCatalog.model_key.asc()
        )
    )
    for model in list(models):
        run_count, success_count, last_run_at = usage_map.get(model.id, (0, 0, None))
        success_rate = (success_count / run_count) if run_count else None
        health_status = "healthy" if model.enabled else "disabled"
        if model.enabled and run_count and success_rate is not None and success_rate < 0.8:
            health_status = "degraded"
        items.append(
            ModelHealthRow(
                model_id=model.id,
                provider=model.provider,
                model_key=model.model_key,
                display_name=model.display_name,
                enabled=model.enabled,
                health_status=health_status,
                recent_run_count=run_count,
                recent_success_rate=success_rate,
                last_run_at=last_run_at,
            )
        )
    return items

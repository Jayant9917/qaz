"""Model registry API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import (
    RequestIdentity,
    require_csrf_protection,
    require_permission,
)
from novo.identity.service import log_event
from novo.infrastructure.database import get_session
from novo.models.accounting import list_model_health, list_model_usage
from novo.models.registry import ModelCatalog, ModelPolicy
from novo.models.service import (
    create_model_policy,
    get_model,
    get_model_policy,
    invalidate_registry_cache,
    list_model_policies,
    list_models,
    resolve_route_selection,
)

router = APIRouter(tags=["models"])


class ModelCatalogResponse(BaseModel):
    id: UUID
    provider: str
    model_key: str
    display_name: str
    capabilities: dict[str, Any]
    context_window: int
    max_output_tokens: int
    privacy_eligibility: str
    pricing: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ModelCatalogUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    capabilities: dict[str, Any] | None = None
    context_window: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    privacy_eligibility: str | None = Field(default=None, min_length=1, max_length=24)
    pricing: dict[str, Any] | None = None
    enabled: bool | None = None


class ModelCatalogListResponse(BaseModel):
    items: list[ModelCatalogResponse]


class ModelPolicyResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    rules: dict[str, Any]
    max_classification: str
    max_cost_minor: int
    currency: str
    latency_target_ms: int
    fallback_allowed: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime
    version: int


class ModelPolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rules: dict[str, Any] = Field(default_factory=dict)
    max_classification: str = Field(default="private", min_length=1, max_length=24)
    max_cost_minor: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=16)
    latency_target_ms: int = Field(default=5000, ge=1)
    fallback_allowed: bool = True
    enabled: bool = True


class ModelPolicyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    rules: dict[str, Any] | None = None
    max_classification: str | None = Field(default=None, min_length=1, max_length=24)
    max_cost_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=16)
    latency_target_ms: int | None = Field(default=None, ge=1)
    fallback_allowed: bool | None = None
    enabled: bool | None = None


class ModelPolicyListResponse(BaseModel):
    items: list[ModelPolicyResponse]


class RouteSimulationRequest(BaseModel):
    purpose: str = Field(default="conversation.reply", min_length=1, max_length=120)
    classification: str = Field(default="private", min_length=1, max_length=24)
    route_mode: str = Field(default="fast", min_length=1, max_length=24)
    model_policy_id: UUID | None = None


class RouteSimulationResponse(BaseModel):
    path: str
    route_reason: str
    prompt_version: str
    model_provider: str
    model_name: str
    model_policy_id: UUID | None
    prompt_binding_id: UUID | None
    prompt_template_id: UUID | None
    prompt_version_id: UUID | None


class ModelUsageItem(BaseModel):
    provider: str | None
    model_name: str | None
    run_count: int
    token_count: int
    average_latency_ms: float | None
    success_count: int
    failure_count: int
    cost_minor: int


class ModelUsageResponse(BaseModel):
    items: list[ModelUsageItem]


class ModelHealthItem(BaseModel):
    model_id: UUID
    provider: str
    model_key: str
    display_name: str
    enabled: bool
    health_status: str
    recent_run_count: int
    recent_success_rate: float | None
    last_run_at: datetime | None


class ModelHealthResponse(BaseModel):
    items: list[ModelHealthItem]


async def _serialize_model(model: ModelCatalog) -> ModelCatalogResponse:
    return ModelCatalogResponse.model_validate(model, from_attributes=True)


async def _serialize_policy(policy: ModelPolicy) -> ModelPolicyResponse:
    return ModelPolicyResponse.model_validate(policy, from_attributes=True)


@router.get("/models", response_model=ModelCatalogListResponse)
async def get_models(
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelCatalogListResponse:
    items = await list_models(db)
    return ModelCatalogListResponse(items=[await _serialize_model(item) for item in items])


@router.get("/models/{model_id}", response_model=ModelCatalogResponse)
async def get_model_detail(
    model_id: UUID,
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelCatalogResponse:
    model = await get_model(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return await _serialize_model(model)


@router.patch("/models/{model_id}", response_model=ModelCatalogResponse)
async def patch_model(
    model_id: UUID,
    payload: ModelCatalogUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelCatalogResponse:
    model = await get_model(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    if payload.display_name is not None:
        model.display_name = payload.display_name
    if payload.capabilities is not None:
        model.capabilities = payload.capabilities
    if payload.context_window is not None:
        model.context_window = payload.context_window
    if payload.max_output_tokens is not None:
        model.max_output_tokens = payload.max_output_tokens
    if payload.privacy_eligibility is not None:
        model.privacy_eligibility = payload.privacy_eligibility
    if payload.pricing is not None:
        model.pricing = payload.pricing
    if payload.enabled is not None:
        model.enabled = payload.enabled
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="model.update",
        resource_type="platform.model_catalog",
        resource_id=str(model.id),
        outcome="success",
        details={"model_key": model.model_key},
    )
    await db.commit()
    await db.refresh(model)
    invalidate_registry_cache()
    return await _serialize_model(model)


@router.get("/model-policies", response_model=ModelPolicyListResponse)
async def get_model_policies(
    identity: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelPolicyListResponse:
    items = await list_model_policies(db, identity.user.id)
    return ModelPolicyListResponse(items=[await _serialize_policy(item) for item in items])


@router.post(
    "/model-policies", response_model=ModelPolicyResponse, status_code=status.HTTP_201_CREATED
)
async def post_model_policy(
    payload: ModelPolicyCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelPolicyResponse:
    policy = await create_model_policy(
        db,
        owner_id=identity.user.id,
        name=payload.name,
        rules=payload.rules,
        max_classification=payload.max_classification,
        max_cost_minor=payload.max_cost_minor,
        currency=payload.currency,
        latency_target_ms=payload.latency_target_ms,
        fallback_allowed=payload.fallback_allowed,
        enabled=payload.enabled,
    )
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="model_policy.create",
        resource_type="platform.model_policies",
        resource_id=str(policy.id),
        outcome="success",
        details={"name": policy.name},
    )
    await db.commit()
    await db.refresh(policy)
    invalidate_registry_cache()
    return await _serialize_policy(policy)


@router.patch("/model-policies/{policy_id}", response_model=ModelPolicyResponse)
async def patch_model_policy(
    policy_id: UUID,
    payload: ModelPolicyUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelPolicyResponse:
    policy = await get_model_policy(db, identity.user.id, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model policy not found")
    if payload.name is not None:
        policy.name = payload.name
    if payload.rules is not None:
        policy.rules = payload.rules
    if payload.max_classification is not None:
        policy.max_classification = payload.max_classification
    if payload.max_cost_minor is not None:
        policy.max_cost_minor = payload.max_cost_minor
    if payload.currency is not None:
        policy.currency = payload.currency
    if payload.latency_target_ms is not None:
        policy.latency_target_ms = payload.latency_target_ms
    if payload.fallback_allowed is not None:
        policy.fallback_allowed = payload.fallback_allowed
    if payload.enabled is not None:
        policy.enabled = payload.enabled
    policy.version += 1
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="model_policy.update",
        resource_type="platform.model_policies",
        resource_id=str(policy.id),
        outcome="success",
        details={"name": policy.name},
    )
    await db.commit()
    await db.refresh(policy)
    invalidate_registry_cache()
    return await _serialize_policy(policy)


@router.post("/models/route-simulation", response_model=RouteSimulationResponse)
async def post_route_simulation(
    payload: RouteSimulationRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RouteSimulationResponse:
    selection = await resolve_route_selection(
        db,
        owner_id=identity.user.id,
        classification=payload.classification,
        purpose=payload.purpose,
        route_mode=payload.route_mode,
        model_policy_id=payload.model_policy_id,
    )
    return RouteSimulationResponse(
        path=selection.path,
        route_reason=selection.route_reason,
        prompt_version=selection.prompt_version,
        model_provider=selection.model_provider,
        model_name=selection.model_name,
        model_policy_id=selection.model_policy_id,
        prompt_binding_id=selection.prompt_binding_id,
        prompt_template_id=selection.prompt_template_id,
        prompt_version_id=selection.prompt_version_id,
    )


@router.get("/model-usage", response_model=ModelUsageResponse)
async def get_model_usage(
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelUsageResponse:
    usage_items = await list_model_usage(db)
    items = [
        ModelUsageItem.model_validate(item, from_attributes=True)
        for item in usage_items
    ]
    return ModelUsageResponse(items=items)


@router.get("/model-health", response_model=ModelHealthResponse)
async def get_model_health(
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ModelHealthResponse:
    health_items = await list_model_health(db)
    items = [
        ModelHealthItem.model_validate(item, from_attributes=True)
        for item in health_items
    ]
    return ModelHealthResponse(items=items)

"""Prompt registry API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, require_csrf_protection, require_permission
from novo.identity.service import log_event
from novo.infrastructure.database import get_session
from novo.models.registry import PromptBinding, PromptTemplate, PromptVersion
from novo.models.service import (
    activate_prompt_version,
    create_prompt_version,
    evaluate_prompt_version,
    get_prompt_binding,
    get_prompt_template,
    get_prompt_version,
    invalidate_registry_cache,
    list_prompt_bindings,
    list_prompt_templates,
    list_prompt_versions,
    retire_prompt_version,
)

router = APIRouter(tags=["prompts"])


class PromptTemplateResponse(BaseModel):
    id: UUID
    prompt_key: str
    purpose: str
    name: str
    description: str
    variable_schema: dict[str, Any]
    security_level: str
    owner_id: UUID | None
    created_at: datetime
    updated_at: datetime


class PromptTemplateListResponse(BaseModel):
    items: list[PromptTemplateResponse]


class PromptTemplateCreateRequest(BaseModel):
    prompt_key: str = Field(min_length=1, max_length=120)
    purpose: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=500)
    variable_schema: dict[str, Any] = Field(default_factory=dict)
    security_level: str = Field(default="private", min_length=1, max_length=24)
    owner_id: UUID | None = None


class PromptVersionResponse(BaseModel):
    id: UUID
    template_id: UUID
    version_no: int
    content: str
    content_hash: str
    status: str
    change_reason: str | None
    created_by: UUID | None
    evaluation_status: str
    created_at: datetime
    activated_at: datetime | None
    retired_at: datetime | None


class PromptVersionListResponse(BaseModel):
    items: list[PromptVersionResponse]


class PromptVersionCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=200_000)
    change_reason: str | None = Field(default=None, max_length=500)


class PromptVersionEvaluationResponse(BaseModel):
    id: UUID
    evaluation_status: str
    content_hash: str


class PromptBindingResponse(BaseModel):
    id: UUID
    owner_id: UUID | None
    purpose: str
    agent_type: str | None
    tool_capability_id: UUID | None
    prompt_version_id: UUID
    priority: int
    valid_from: datetime | None
    valid_until: datetime | None
    created_at: datetime


class PromptBindingListResponse(BaseModel):
    items: list[PromptBindingResponse]


class PromptBindingUpdateRequest(BaseModel):
    prompt_version_id: UUID | None = None
    priority: int | None = Field(default=None, ge=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None


async def _serialize_template(template: PromptTemplate) -> PromptTemplateResponse:
    return PromptTemplateResponse.model_validate(template, from_attributes=True)


async def _serialize_version(version: PromptVersion) -> PromptVersionResponse:
    return PromptVersionResponse.model_validate(version, from_attributes=True)


async def _serialize_binding(binding: PromptBinding) -> PromptBindingResponse:
    return PromptBindingResponse.model_validate(binding, from_attributes=True)


@router.get("/prompt-templates", response_model=PromptTemplateListResponse)
async def get_prompt_templates(
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptTemplateListResponse:
    items = await list_prompt_templates(db)
    return PromptTemplateListResponse(items=[await _serialize_template(item) for item in items])


@router.post(
    "/prompt-templates", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED
)
async def post_prompt_template(
    payload: PromptTemplateCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptTemplateResponse:
    template = PromptTemplate(
        prompt_key=payload.prompt_key,
        purpose=payload.purpose,
        name=payload.name,
        description=payload.description,
        variable_schema=payload.variable_schema,
        security_level=payload.security_level,
        owner_id=payload.owner_id or identity.user.id,
    )
    db.add(template)
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="prompt.template.create",
        resource_type="platform.prompt_templates",
        resource_id=str(template.id),
        outcome="success",
        details={"prompt_key": template.prompt_key},
    )
    await db.commit()
    await db.refresh(template)
    invalidate_registry_cache()
    return await _serialize_template(template)


@router.get("/prompt-templates/{template_id}/versions", response_model=PromptVersionListResponse)
async def get_prompt_template_versions(
    template_id: UUID,
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersionListResponse:
    template = await get_prompt_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found"
        )
    items = await list_prompt_versions(db, template.id)
    return PromptVersionListResponse(items=[await _serialize_version(item) for item in items])


@router.post(
    "/prompt-templates/{template_id}/versions",
    response_model=PromptVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_prompt_template_version(
    template_id: UUID,
    payload: PromptVersionCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersionResponse:
    template = await get_prompt_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found"
        )
    version = await create_prompt_version(
        db,
        template=template,
        content=payload.content,
        change_reason=payload.change_reason,
        created_by=identity.user.id,
    )
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="prompt.version.create",
        resource_type="platform.prompt_versions",
        resource_id=str(version.id),
        outcome="success",
        details={"template_id": str(template.id), "version_no": version.version_no},
    )
    await db.commit()
    await db.refresh(version)
    invalidate_registry_cache()
    return await _serialize_version(version)


@router.post(
    "/prompt-versions/{version_id}/evaluate", response_model=PromptVersionEvaluationResponse
)
async def post_prompt_version_evaluate(
    version_id: UUID,
    _: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersionEvaluationResponse:
    version = await get_prompt_version(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt version not found"
        )
    await evaluate_prompt_version(db, version)
    await db.commit()
    await db.refresh(version)
    invalidate_registry_cache()
    return PromptVersionEvaluationResponse(
        id=version.id,
        evaluation_status=version.evaluation_status,
        content_hash=version.content_hash,
    )


@router.post("/prompt-versions/{version_id}/activate", response_model=PromptVersionResponse)
async def post_prompt_version_activate(
    version_id: UUID,
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersionResponse:
    version = await get_prompt_version(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt version not found"
        )
    await activate_prompt_version(db, version)
    await db.commit()
    await db.refresh(version)
    invalidate_registry_cache()
    return await _serialize_version(version)


@router.post("/prompt-versions/{version_id}/retire", response_model=PromptVersionResponse)
async def post_prompt_version_retire(
    version_id: UUID,
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersionResponse:
    version = await get_prompt_version(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt version not found"
        )
    await retire_prompt_version(db, version)
    await db.commit()
    await db.refresh(version)
    invalidate_registry_cache()
    return await _serialize_version(version)


@router.get("/prompt-bindings", response_model=PromptBindingListResponse)
async def get_prompt_bindings(
    identity: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptBindingListResponse:
    items = await list_prompt_bindings(db, identity.user.id)
    return PromptBindingListResponse(items=[await _serialize_binding(item) for item in items])


@router.put("/prompt-bindings/{binding_id}", response_model=PromptBindingResponse)
async def put_prompt_binding(
    binding_id: UUID,
    payload: PromptBindingUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PromptBindingResponse:
    binding = await get_prompt_binding(db, binding_id)
    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt binding not found"
        )
    if payload.prompt_version_id is not None:
        binding.prompt_version_id = payload.prompt_version_id
    if payload.priority is not None:
        binding.priority = payload.priority
    if payload.valid_from is not None:
        binding.valid_from = payload.valid_from
    if payload.valid_until is not None:
        binding.valid_until = payload.valid_until
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="prompt.binding.update",
        resource_type="platform.prompt_bindings",
        resource_id=str(binding.id),
        outcome="success",
        details={"purpose": binding.purpose},
    )
    await db.commit()
    await db.refresh(binding)
    invalidate_registry_cache()
    return await _serialize_binding(binding)

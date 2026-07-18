"""Memory routes for the first E3 foundation slice."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, get_request_identity, require_csrf_protection
from novo.infrastructure.database import get_session
from novo.memory.candidates import contains_secret, detect_memory_candidate
from novo.memory.models import Memory, MemoryAccessEvent, MemoryRevision
from novo.memory.service import (
    archive_memory,
    create_memory,
    delete_memory,
    get_memory,
    list_memories,
    list_memory_access_events,
    list_memory_revisions,
    record_memory_access_event,
    restore_memory,
    update_memory,
)

router = APIRouter(prefix="/memories", tags=["memory"])


class MemoryBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MemoryResponse(MemoryBaseModel):
    id: UUID
    owner_id: UUID
    kind: str
    title: str
    canonical_content: str
    classification: str
    status: str
    confidence: float
    importance: float
    access_count: int
    last_accessed_at: datetime | None
    valid_from: datetime | None
    valid_until: datetime | None
    retention_until: datetime | None
    review_after: datetime | None
    source_type: str
    source_id: UUID | None
    source_locator: dict[str, Any]
    evidence_excerpt: str | None
    evidence_hash: str
    extraction_method: str
    embedding_status: str
    embedding_version: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    version: int


class MemoryRevisionResponse(MemoryBaseModel):
    id: UUID
    owner_id: UUID
    memory_id: UUID
    version: int
    title: str
    canonical_content: str
    status: str
    source_type: str
    created_at: datetime


class MemoryRevisionListResponse(BaseModel):
    items: list[MemoryRevisionResponse]


class MemoryAccessEventResponse(MemoryBaseModel):
    id: UUID
    owner_id: UUID
    memory_id: UUID
    actor_type: str
    actor_id: UUID | None
    agent_run_id: UUID | None
    purpose: str
    decision: str
    policy_version_id: UUID | None
    relevance_score: float | None
    used_in_prompt: bool
    provider: str | None
    trace_id: str | None
    created_at: datetime


class MemoryListResponse(BaseModel):
    items: list[MemoryResponse]


class MemoryAccessEventListResponse(BaseModel):
    items: list[MemoryAccessEventResponse]


class MemorySuggestRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)
    source_locator: dict[str, Any] = Field(default_factory=dict)


class MemorySuggestionResponse(BaseModel):
    should_suggest: bool
    title: str | None = None
    content: str | None = None
    kind: str | None = None
    classification: str | None = None
    confidence: float | None = None
    importance: float | None = None
    auto_save: bool = False
    reason: str | None = None


class MemoryCreateRequest(BaseModel):
    kind: str = Field(default="long_term", min_length=1, max_length=24)
    title: str = Field(min_length=1, max_length=240)
    canonical_content: str = Field(min_length=1, max_length=50_000)
    classification: str = Field(default="private", min_length=1, max_length=24)
    status: str = Field(default="active", min_length=1, max_length=24)
    confidence: float = Field(default=1.0, ge=0, le=1)
    importance: float = Field(default=0.5, ge=0, le=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    retention_until: datetime | None = None
    review_after: datetime | None = None
    source_type: str = Field(default="explicit_remember", min_length=1, max_length=120)
    source_id: UUID | None = None
    source_locator: dict[str, Any] = Field(default_factory=dict)
    evidence_excerpt: str | None = Field(default=None, max_length=5000)
    extraction_method: str = Field(default="explicit", min_length=1, max_length=120)
    embedding_status: str = Field(default="not_requested", min_length=1, max_length=24)
    embedding_version: str | None = Field(default=None, max_length=120)


class MemoryRememberRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)
    title: str | None = Field(default=None, min_length=1, max_length=240)
    kind: str = Field(default="long_term", min_length=1, max_length=24)
    classification: str = Field(default="private", min_length=1, max_length=24)
    confidence: float = Field(default=1.0, ge=0, le=1)
    importance: float = Field(default=0.5, ge=0, le=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    retention_until: datetime | None = None
    review_after: datetime | None = None
    source_locator: dict[str, Any] = Field(default_factory=dict)
    evidence_excerpt: str | None = Field(default=None, max_length=5000)
    embedding_version: str | None = Field(default=None, max_length=120)


class MemoryUpdateRequest(BaseModel):
    kind: str | None = Field(default=None, min_length=1, max_length=24)
    title: str | None = Field(default=None, min_length=1, max_length=240)
    canonical_content: str | None = Field(default=None, min_length=1, max_length=50_000)
    classification: str | None = Field(default=None, min_length=1, max_length=24)
    status: str | None = Field(default=None, min_length=1, max_length=24)
    confidence: float | None = Field(default=None, ge=0, le=1)
    importance: float | None = Field(default=None, ge=0, le=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    retention_until: datetime | None = None
    review_after: datetime | None = None
    source_type: str | None = Field(default=None, min_length=1, max_length=120)
    source_id: UUID | None = None
    source_locator: dict[str, Any] | None = None
    evidence_excerpt: str | None = Field(default=None, max_length=5000)
    extraction_method: str | None = Field(default=None, min_length=1, max_length=120)
    embedding_status: str | None = Field(default=None, min_length=1, max_length=24)
    embedding_version: str | None = Field(default=None, max_length=120)


class MemoryCorrectRequest(MemoryUpdateRequest):
    canonical_content: str = Field(min_length=1, max_length=50_000)
    source_type: str = Field(default="owner_correction", min_length=1, max_length=120)
    extraction_method: str = Field(default="owner_correction", min_length=1, max_length=120)


def _memory_response(memory: Memory) -> MemoryResponse:
    return MemoryResponse.model_validate(memory, from_attributes=True)


def _revision_response(revision: MemoryRevision) -> MemoryRevisionResponse:
    return MemoryRevisionResponse.model_validate(revision, from_attributes=True)


def _access_event_response(event: MemoryAccessEvent) -> MemoryAccessEventResponse:
    return MemoryAccessEventResponse.model_validate(event, from_attributes=True)


def _derive_memory_title(content: str) -> str:
    compact = " ".join(content.split()).strip()
    if not compact:
        return "Remembered note"
    candidate = compact.split(". ", 1)[0].strip()
    title = candidate[:240].rstrip(".?!,;:")
    if not title:
        title = compact[:240].rstrip(".?!,;:")
    return title or "Remembered note"


@router.post("/suggest", response_model=MemorySuggestionResponse, response_model_exclude_none=True)
async def suggest_memory(
    payload: MemorySuggestRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
) -> MemorySuggestionResponse:
    """Classify chat text without storing it; the owner must approve any save."""

    del identity
    candidate = detect_memory_candidate(payload.content)
    if candidate is None:
        return MemorySuggestionResponse(should_suggest=False)
    return MemorySuggestionResponse(
        should_suggest=True,
        title=candidate.title,
        content=candidate.content,
        kind=candidate.kind,
        classification=candidate.classification,
        confidence=candidate.confidence,
        importance=candidate.importance,
        auto_save=candidate.auto_save,
        reason=candidate.reason,
    )


async def _load_memory_or_404(
    db: AsyncSession, identity: RequestIdentity, memory_id: UUID
) -> Memory:
    memory = await get_memory(db, identity.user.id, memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.get("", response_model=MemoryListResponse)
async def get_memories(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = Query(default=None, alias="status"),
    kind: str | None = Query(default=None),
    classification: str | None = Query(default=None),
) -> MemoryListResponse:
    items = await list_memories(
        db,
        identity.user.id,
        status=status_filter,
        kind=kind,
        classification=classification,
    )
    return MemoryListResponse(items=[_memory_response(item) for item in items])


@router.post("/remember", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def remember_memory(
    payload: MemoryRememberRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    if contains_secret(payload.content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Memory cannot contain passwords, API keys, tokens, or recovery codes.",
        )
    memory = await create_memory(
        db,
        owner_id=identity.user.id,
        kind=payload.kind,
        title=payload.title or _derive_memory_title(payload.content),
        canonical_content=payload.content,
        classification=payload.classification,
        confidence=payload.confidence,
        importance=payload.importance,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        retention_until=payload.retention_until,
        review_after=payload.review_after,
        source_type="explicit_remember",
        source_locator=payload.source_locator,
        evidence_excerpt=payload.evidence_excerpt or payload.content,
        extraction_method="explicit",
        embedding_version=payload.embedding_version,
    )
    return _memory_response(memory)


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def post_memory(
    payload: MemoryCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    if contains_secret(payload.canonical_content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Memory cannot contain passwords, API keys, tokens, or recovery codes.",
        )
    memory = await create_memory(
        db,
        owner_id=identity.user.id,
        kind=payload.kind,
        title=payload.title,
        canonical_content=payload.canonical_content,
        classification=payload.classification,
        status=payload.status,
        confidence=payload.confidence,
        importance=payload.importance,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        retention_until=payload.retention_until,
        review_after=payload.review_after,
        source_type=payload.source_type,
        source_id=payload.source_id,
        source_locator=payload.source_locator,
        evidence_excerpt=payload.evidence_excerpt,
        extraction_method=payload.extraction_method,
        embedding_status=payload.embedding_status,
        embedding_version=payload.embedding_version,
    )
    return _memory_response(memory)


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory_detail(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    memory = await _load_memory_or_404(db, identity, memory_id)
    await record_memory_access_event(
        db,
        memory=memory,
        actor_type="owner",
        actor_id=identity.user.id,
        purpose="memory.read",
        decision="allowed",
    )
    return _memory_response(memory)


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def patch_memory(
    memory_id: UUID,
    payload: MemoryUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    if payload.canonical_content is not None and contains_secret(payload.canonical_content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Memory cannot contain passwords, API keys, tokens, or recovery codes.",
        )
    memory = await _load_memory_or_404(db, identity, memory_id)
    if all(
        value is None
        for value in (
            payload.kind,
            payload.title,
            payload.canonical_content,
            payload.classification,
            payload.status,
            payload.confidence,
            payload.importance,
            payload.valid_from,
            payload.valid_until,
            payload.retention_until,
            payload.review_after,
            payload.source_type,
            payload.source_id,
            payload.source_locator,
            payload.evidence_excerpt,
            payload.extraction_method,
            payload.embedding_status,
            payload.embedding_version,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No memory changes provided",
        )
    updated = await update_memory(
        db,
        memory=memory,
        title=payload.title,
        kind=payload.kind,
        canonical_content=payload.canonical_content,
        classification=payload.classification,
        status=payload.status,
        confidence=payload.confidence,
        importance=payload.importance,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        retention_until=payload.retention_until,
        review_after=payload.review_after,
        source_type=payload.source_type,
        source_id=payload.source_id,
        source_locator=payload.source_locator,
        evidence_excerpt=payload.evidence_excerpt,
        extraction_method=payload.extraction_method,
        embedding_status=payload.embedding_status,
        embedding_version=payload.embedding_version,
    )
    return _memory_response(updated)


@router.post("/{memory_id}/correct", response_model=MemoryResponse)
async def correct_memory(
    memory_id: UUID,
    payload: MemoryCorrectRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    if contains_secret(payload.canonical_content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Memory cannot contain passwords, API keys, tokens, or recovery codes.",
        )
    memory = await _load_memory_or_404(db, identity, memory_id)
    updated = await update_memory(
        db,
        memory=memory,
        title=payload.title,
        kind=payload.kind,
        canonical_content=payload.canonical_content,
        classification=payload.classification,
        status=payload.status,
        confidence=payload.confidence,
        importance=payload.importance,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        retention_until=payload.retention_until,
        review_after=payload.review_after,
        source_type=payload.source_type,
        source_id=payload.source_id,
        source_locator=payload.source_locator,
        evidence_excerpt=payload.evidence_excerpt,
        extraction_method=payload.extraction_method,
        embedding_status=payload.embedding_status,
        embedding_version=payload.embedding_version,
    )
    return _memory_response(updated)


@router.post("/{memory_id}/archive", response_model=MemoryResponse)
async def archive_memory_route(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    memory = await _load_memory_or_404(db, identity, memory_id)
    archived = await archive_memory(db, memory=memory)
    return _memory_response(archived)


@router.post("/{memory_id}/restore", response_model=MemoryResponse)
async def restore_memory_route(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    memory = await _load_memory_or_404(db, identity, memory_id)
    restored = await restore_memory(db, memory=memory)
    return _memory_response(restored)


@router.delete("/{memory_id}", response_model=MemoryResponse)
async def delete_memory_route(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryResponse:
    memory = await _load_memory_or_404(db, identity, memory_id)
    deleted = await delete_memory(db, memory=memory)
    return _memory_response(deleted)


@router.get("/{memory_id}/revisions", response_model=MemoryRevisionListResponse)
async def get_memory_revisions(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryRevisionListResponse:
    await _load_memory_or_404(db, identity, memory_id)
    items = await list_memory_revisions(db, identity.user.id, memory_id)
    return MemoryRevisionListResponse(items=[_revision_response(item) for item in items])


@router.get("/{memory_id}/access-events", response_model=MemoryAccessEventListResponse)
async def get_memory_access_events(
    memory_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryAccessEventListResponse:
    await _load_memory_or_404(db, identity, memory_id)
    items = await list_memory_access_events(db, identity.user.id, memory_id)
    return MemoryAccessEventListResponse(items=[_access_event_response(item) for item in items])

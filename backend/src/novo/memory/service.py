"""Memory service helpers for the first E3 slice."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.infrastructure.rls import apply_owner_context
from novo.memory.models import Memory, MemoryAccessEvent

DEFAULT_KIND = 'long_term'
DEFAULT_CLASSIFICATION = 'private'
DEFAULT_STATUS = 'active'
DEFAULT_CONFIDENCE = Decimal('1.000')
DEFAULT_IMPORTANCE = Decimal('0.500')
DEFAULT_SOURCE_TYPE = 'explicit_remember'
DEFAULT_EXTRACTION_METHOD = 'explicit'
DEFAULT_EMBEDDING_STATUS = 'not_requested'


def _now() -> datetime:
    return datetime.now(UTC)


def _decimal(value: Decimal | float | int | None, default: Decimal) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _hash_text(text: str | None) -> str:
    return sha256((text or '').encode('utf-8')).hexdigest()


def _locator(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


async def list_memories(
    db: AsyncSession,
    owner_id: UUID,
    *,
    status: str | None = None,
    kind: str | None = None,
    classification: str | None = None,
) -> list[Memory]:
    query = select(Memory).where(Memory.owner_id == owner_id, Memory.deleted_at.is_(None))
    if status is not None:
        query = query.where(Memory.status == status)
    if kind is not None:
        query = query.where(Memory.kind == kind)
    if classification is not None:
        query = query.where(Memory.classification == classification)
    query = query.order_by(Memory.updated_at.desc(), Memory.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_memory(db: AsyncSession, owner_id: UUID, memory_id: UUID) -> Memory | None:
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.owner_id == owner_id,
            Memory.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_memory_access_events(
    db: AsyncSession,
    owner_id: UUID,
    memory_id: UUID,
) -> list[MemoryAccessEvent]:
    result = await db.execute(
        select(MemoryAccessEvent)
        .where(MemoryAccessEvent.owner_id == owner_id, MemoryAccessEvent.memory_id == memory_id)
        .order_by(MemoryAccessEvent.created_at.asc())
    )
    return list(result.scalars().all())


async def _next_revision_no(db: AsyncSession, memory_id: UUID) -> int:
    revision_no = await db.scalar(
        select(func.coalesce(func.max(Memory.version), 0)).where(Memory.id == memory_id)
    )
    return int(revision_no or 0) + 1


async def create_memory(
    db: AsyncSession,
    *,
    owner_id: UUID,
    kind: str = DEFAULT_KIND,
    title: str,
    canonical_content: str,
    classification: str = DEFAULT_CLASSIFICATION,
    status: str = DEFAULT_STATUS,
    confidence: Decimal | float | int = DEFAULT_CONFIDENCE,
    importance: Decimal | float | int = DEFAULT_IMPORTANCE,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    retention_until: datetime | None = None,
    review_after: datetime | None = None,
    source_type: str = DEFAULT_SOURCE_TYPE,
    source_id: UUID | None = None,
    source_locator: dict[str, Any] | None = None,
    evidence_excerpt: str | None = None,
    extraction_method: str = DEFAULT_EXTRACTION_METHOD,
    embedding_status: str = DEFAULT_EMBEDDING_STATUS,
    embedding_version: str | None = None,
) -> Memory:
    now = _now()
    memory = Memory(
        owner_id=owner_id,
        kind=kind,
        title=title,
        canonical_content=canonical_content,
        classification=classification,
        status=status,
        confidence=_decimal(confidence, DEFAULT_CONFIDENCE),
        importance=_decimal(importance, DEFAULT_IMPORTANCE),
        access_count=0,
        valid_from=valid_from or now,
        valid_until=valid_until,
        retention_until=retention_until,
        review_after=review_after,
        source_type=source_type,
        source_id=source_id,
        source_locator=_locator(source_locator),
        evidence_excerpt=evidence_excerpt,
        evidence_hash=_hash_text(evidence_excerpt or canonical_content),
        extraction_method=extraction_method,
        embedding_status=embedding_status,
        embedding_version=embedding_version,
        version=1,
    )
    if status == 'deleted':
        memory.deleted_at = now
    db.add(memory)
    await db.commit()
    await apply_owner_context(db, owner_id)
    await db.refresh(memory)
    return memory


async def update_memory(
    db: AsyncSession,
    *,
    memory: Memory,
    title: str | None = None,
    kind: str | None = None,
    canonical_content: str | None = None,
    classification: str | None = None,
    status: str | None = None,
    confidence: Decimal | float | int | None = None,
    importance: Decimal | float | int | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    retention_until: datetime | None = None,
    review_after: datetime | None = None,
    source_type: str | None = None,
    source_id: UUID | None = None,
    source_locator: dict[str, Any] | None = None,
    evidence_excerpt: str | None = None,
    extraction_method: str | None = None,
    embedding_status: str | None = None,
    embedding_version: str | None = None,
) -> Memory:
    now = _now()
    if title is not None:
        memory.title = title
    if kind is not None:
        memory.kind = kind
    if canonical_content is not None:
        memory.canonical_content = canonical_content
        memory.evidence_hash = _hash_text(evidence_excerpt or canonical_content)
    if classification is not None:
        memory.classification = classification
    if status is not None:
        memory.status = status
        memory.deleted_at = now if status == 'deleted' else None
    if confidence is not None:
        memory.confidence = _decimal(confidence, DEFAULT_CONFIDENCE)
    if importance is not None:
        memory.importance = _decimal(importance, DEFAULT_IMPORTANCE)
    if valid_from is not None:
        memory.valid_from = valid_from
    if valid_until is not None:
        memory.valid_until = valid_until
    if retention_until is not None:
        memory.retention_until = retention_until
    if review_after is not None:
        memory.review_after = review_after
    if source_type is not None:
        memory.source_type = source_type
    if source_id is not None:
        memory.source_id = source_id
    if source_locator is not None:
        memory.source_locator = _locator(source_locator)
    if evidence_excerpt is not None:
        memory.evidence_excerpt = evidence_excerpt
    if extraction_method is not None:
        memory.extraction_method = extraction_method
    if embedding_status is not None:
        memory.embedding_status = embedding_status
    if embedding_version is not None:
        memory.embedding_version = embedding_version
    memory.updated_at = now
    memory.version += 1
    await db.commit()
    await apply_owner_context(db, memory.owner_id)
    await db.refresh(memory)
    return memory


async def archive_memory(db: AsyncSession, *, memory: Memory) -> Memory:
    return await update_memory(db, memory=memory, status='archived')


async def restore_memory(db: AsyncSession, *, memory: Memory) -> Memory:
    memory.deleted_at = None
    return await update_memory(db, memory=memory, status='active')


async def delete_memory(db: AsyncSession, *, memory: Memory) -> Memory:
    return await update_memory(db, memory=memory, status='deleted')


async def record_memory_access_event(
    db: AsyncSession,
    *,
    memory: Memory,
    actor_type: str = 'owner',
    actor_id: UUID | None = None,
    agent_run_id: UUID | None = None,
    purpose: str = 'memory.read',
    decision: str = 'allowed',
    policy_version_id: UUID | None = None,
    relevance_score: Decimal | float | int | None = None,
    used_in_prompt: bool = False,
    provider: str | None = None,
    trace_id: str | None = None,
) -> MemoryAccessEvent:
    event = MemoryAccessEvent(
        owner_id=memory.owner_id,
        memory_id=memory.id,
        actor_type=actor_type,
        actor_id=actor_id,
        agent_run_id=agent_run_id,
        purpose=purpose,
        decision=decision,
        policy_version_id=policy_version_id,
        relevance_score=(
            _decimal(relevance_score, DEFAULT_IMPORTANCE) if relevance_score is not None else None
        ),
        used_in_prompt=used_in_prompt,
        provider=provider,
        trace_id=trace_id,
    )
    memory.access_count += 1
    memory.last_accessed_at = _now()
    memory.updated_at = memory.last_accessed_at
    memory.version += 1
    db.add(event)
    await db.commit()
    await apply_owner_context(db, memory.owner_id)
    await db.refresh(event)
    await db.refresh(memory)
    return event



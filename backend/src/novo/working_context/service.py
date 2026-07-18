"""Redis-backed working context helpers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.exceptions import RedisError

from novo.core.config import get_settings
from novo.infrastructure.cache import get_redis
from novo.working_context.models import WorkingContext

logger = logging.getLogger(__name__)

WORKING_CONTEXT_KEY_PREFIX = "novo:v1:{environment}:{owner_id}:session:{session_id}:working-context"
MAX_NOTES = 10
DEFAULT_NOTE_LIMIT = 500
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60


def _now() -> datetime:
    return datetime.now(UTC)


def _ttl_seconds(ttl_seconds: int | None = None) -> int:
    if ttl_seconds is not None:
        return max(ttl_seconds, 60)
    settings = get_settings()
    return max(settings.session_ttl_hours * 60 * 60, 60)


def _redis_key(owner_id: UUID, session_id: UUID) -> str:
    settings = get_settings()
    return WORKING_CONTEXT_KEY_PREFIX.format(
        environment=settings.environment,
        owner_id=owner_id,
        session_id=session_id,
    )


def _decode_context(payload: str) -> WorkingContext:
    return WorkingContext.model_validate(json.loads(payload))


def _encode_context(context: WorkingContext) -> str:
    return context.model_dump_json()


def _trim_notes(notes: list[str]) -> list[str]:
    cleaned = [note.strip() for note in notes if note and note.strip()]
    return cleaned[-MAX_NOTES:]


def _empty_context(owner_id: UUID, session_id: UUID) -> WorkingContext:
    return WorkingContext(owner_id=owner_id, session_id=session_id, notes=[], status="empty")


async def get_working_context(owner_id: UUID, session_id: UUID) -> WorkingContext | None:
    try:
        raw = await get_redis().get(_redis_key(owner_id, session_id))
    except RedisError:
        logger.warning(
            "working_context_unavailable action=get owner_id=%s session_id=%s",
            owner_id,
            session_id,
            exc_info=True,
        )
        return None
    if raw is None:
        return None
    try:
        return _decode_context(raw)
    except Exception:
        logger.warning(
            "working_context_decode_failed owner_id=%s session_id=%s",
            owner_id,
            session_id,
            exc_info=True,
        )
        return None


async def save_working_context(
    context: WorkingContext, *, ttl_seconds: int | None = None
) -> WorkingContext:
    ttl = _ttl_seconds(ttl_seconds)
    context.updated_at = _now()
    if context.expires_at is None:
        context.expires_at = context.updated_at + timedelta(seconds=ttl)
    try:
        await get_redis().set(
            _redis_key(context.owner_id, context.session_id), _encode_context(context), ex=ttl
        )
    except RedisError:
        logger.warning(
            "working_context_unavailable action=save owner_id=%s session_id=%s",
            context.owner_id,
            context.session_id,
            exc_info=True,
        )
    return context


async def upsert_working_context(
    owner_id: UUID,
    session_id: UUID,
    *,
    ttl_seconds: int | None = None,
    conversation_id: UUID | None = None,
    current_response_id: UUID | None = None,
    last_response_id: UUID | None = None,
    last_user_message_id: UUID | None = None,
    last_assistant_message_id: UUID | None = None,
    status: str | None = None,
    summary: str | None = None,
    active_task: str | None = None,
    notes: list[str] | None = None,
    stream_cursor: str | None = None,
    last_event: str | None = None,
    expires_at: datetime | None = None,
) -> WorkingContext:
    context = await get_working_context(owner_id, session_id)
    if context is None:
        context = _empty_context(owner_id, session_id)
    if conversation_id is not None:
        context.conversation_id = conversation_id
    if current_response_id is not None:
        context.current_response_id = current_response_id
    if last_response_id is not None:
        context.last_response_id = last_response_id
    if last_user_message_id is not None:
        context.last_user_message_id = last_user_message_id
    if last_assistant_message_id is not None:
        context.last_assistant_message_id = last_assistant_message_id
    if status is not None:
        context.status = status
    if summary is not None:
        context.summary = summary
    if active_task is not None:
        context.active_task = active_task
    if notes is not None:
        context.notes = _trim_notes(notes)
    if stream_cursor is not None:
        context.stream_cursor = stream_cursor
    if last_event is not None:
        context.last_event = last_event
    if expires_at is not None:
        context.expires_at = expires_at
    elif context.expires_at is None:
        context.expires_at = _now() + timedelta(seconds=_ttl_seconds(ttl_seconds))
    return await save_working_context(context, ttl_seconds=ttl_seconds)


async def append_working_context_note(
    owner_id: UUID,
    session_id: UUID,
    note: str,
    *,
    ttl_seconds: int | None = None,
) -> WorkingContext:
    context = await get_working_context(owner_id, session_id)
    if context is None:
        context = _empty_context(owner_id, session_id)
    context.notes = _trim_notes([*context.notes, note])
    context.status = context.status or "empty"
    return await save_working_context(context, ttl_seconds=ttl_seconds)


async def clear_working_context(owner_id: UUID, session_id: UUID) -> WorkingContext:
    context = _empty_context(owner_id, session_id)
    try:
        await get_redis().delete(_redis_key(owner_id, session_id))
    except RedisError:
        logger.warning(
            "working_context_unavailable action=clear owner_id=%s session_id=%s",
            owner_id,
            session_id,
            exc_info=True,
        )
    return context

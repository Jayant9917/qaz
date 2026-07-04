"""Redis working context routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from novo.api.dependencies import RequestIdentity, get_request_identity, require_csrf_protection
from novo.working_context.models import WorkingContext
from novo.working_context.service import (
    append_working_context_note,
    clear_working_context,
    get_working_context,
    upsert_working_context,
)

router = APIRouter(prefix="/working-context", tags=["working-context"])


class WorkingContextUpdateRequest(BaseModel):
    conversation_id: UUID | None = None
    current_response_id: UUID | None = None
    last_response_id: UUID | None = None
    last_user_message_id: UUID | None = None
    last_assistant_message_id: UUID | None = None
    status: str | None = Field(default=None, max_length=24)
    summary: str | None = Field(default=None, max_length=10_000)
    active_task: str | None = Field(default=None, max_length=240)
    notes: list[str] | None = None
    stream_cursor: str | None = Field(default=None, max_length=120)
    last_event: str | None = Field(default=None, max_length=120)


class WorkingContextNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=500)


class WorkingContextResponse(WorkingContext):
    model_config = ConfigDict(from_attributes=True)


def _empty_context(identity: RequestIdentity) -> WorkingContextResponse:
    return WorkingContextResponse(
        owner_id=identity.user.id,
        session_id=identity.session.id,
        status="empty",
        notes=[],
        updated_at=datetime.now(UTC),
        expires_at=identity.session.expires_at,
    )


async def _load_or_empty(identity: RequestIdentity) -> WorkingContextResponse:
    context = await get_working_context(identity.user.id, identity.session.id)
    if context is None:
        return _empty_context(identity)
    if context.expires_at is None:
        context.expires_at = identity.session.expires_at
    return WorkingContextResponse.model_validate(context, from_attributes=True)


@router.get("", response_model=WorkingContextResponse)
async def get_context(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
) -> WorkingContextResponse:
    return await _load_or_empty(identity)


@router.put("", response_model=WorkingContextResponse)
async def put_context(
    payload: WorkingContextUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
) -> WorkingContextResponse:
    context = await upsert_working_context(
        identity.user.id,
        identity.session.id,
        ttl_seconds=max(int((identity.session.expires_at - datetime.now(UTC)).total_seconds()), 60),
        conversation_id=payload.conversation_id,
        current_response_id=payload.current_response_id,
        last_response_id=payload.last_response_id,
        last_user_message_id=payload.last_user_message_id,
        last_assistant_message_id=payload.last_assistant_message_id,
        status=payload.status,
        summary=payload.summary,
        active_task=payload.active_task,
        notes=payload.notes,
        stream_cursor=payload.stream_cursor,
        last_event=payload.last_event,
        expires_at=identity.session.expires_at,
    )
    return WorkingContextResponse.model_validate(context, from_attributes=True)


@router.post("/notes", response_model=WorkingContextResponse)
async def post_context_note(
    payload: WorkingContextNoteRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
) -> WorkingContextResponse:
    context = await append_working_context_note(
        identity.user.id,
        identity.session.id,
        payload.note,
        ttl_seconds=max(int((identity.session.expires_at - datetime.now(UTC)).total_seconds()), 60),
    )
    return WorkingContextResponse.model_validate(context, from_attributes=True)


@router.delete("", response_model=WorkingContextResponse)
async def delete_context(
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
) -> WorkingContextResponse:
    context = await clear_working_context(identity.user.id, identity.session.id)
    return WorkingContextResponse.model_validate(context, from_attributes=True)

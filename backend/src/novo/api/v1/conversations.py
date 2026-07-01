"""Conversation routes for the E2 fast path foundation."""

from __future__ import annotations

import logging

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from hashlib import sha256
from time import perf_counter
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, get_request_identity, require_csrf_protection
from novo.conversations.guardrails import inspect_text
from novo.conversations.models import Conversation, Message
from novo.conversations.responses import ResponseRun
from novo.conversations.service import (
    archive_conversation,
    complete_response_run,
    create_conversation,
    create_message,
    create_response_run,
    delete_conversation,
    fail_response_run,
    get_conversation,
    get_response_run,
    list_conversations,
    list_messages,
)
from novo.infrastructure.database import get_session
from novo.models.accounting import (
    complete_model_call,
    create_model_call,
    get_model_by_key,
)
from novo.models.gateway import generate_model_reply, stream_model_reply
from novo.models.registry import ModelCatalog
from novo.models.service import resolve_route_selection

router = APIRouter(prefix="/conversations", tags=["conversations"])

logger = logging.getLogger(__name__)


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    classification: str = Field(default="private", min_length=1, max_length=24)


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    classification: str | None = Field(default=None, min_length=1, max_length=24)


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)
    role: str = Field(default="user", min_length=1, max_length=24)
    content_format: str = Field(default="text/plain", min_length=1, max_length=40)
    classification: str = Field(default="private", min_length=1, max_length=24)
    parent_message_id: UUID | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    owner_id: UUID
    parent_message_id: UUID | None
    sequence_no: int
    role: str
    content: str
    content_format: str
    classification: str
    status: str
    token_count: int
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    response_id: UUID | None = None


class ConversationResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    status: str
    classification: str
    summary: str | None
    summary_version: int
    default_model_policy_id: UUID | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None
    version: int


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]


class MessageListResponse(BaseModel):
    items: list[MessageResponse]


class MessageCreateResponse(BaseModel):
    message: MessageResponse
    response_id: UUID


class ResponseEventStarted(BaseModel):
    response_id: UUID
    conversation_id: UUID
    user_message_id: UUID


class ResponseEventRouteSelected(BaseModel):
    response_id: UUID
    path: str
    route_reason: str
    prompt_version: str
    model_provider: str
    model_name: str


class ResponseEventContextReady(BaseModel):
    response_id: UUID
    conversation_id: UUID
    user_message_id: UUID


class ResponseEventWarning(BaseModel):
    response_id: UUID
    warnings: list[str]


class ResponseEventToken(BaseModel):
    response_id: UUID
    index: int
    token: str
    content: str


class ResponseEventCompleted(BaseModel):
    response_id: UUID
    conversation_id: UUID
    assistant_message: MessageResponse


class ResponseEventFailed(BaseModel):
    response_id: UUID
    error_message: str


def _conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse.model_validate(conversation, from_attributes=True)


def _message_response(message: Message, *, response_id: UUID | None = None) -> MessageResponse:
    payload = MessageResponse.model_validate(message, from_attributes=True)
    if response_id is not None:
        return payload.model_copy(update={"response_id": response_id})
    return payload


def _sse_event(event_id: int, event_name: str, payload: BaseModel) -> str:
    return f"id: {event_id}\nevent: {event_name}\ndata: {payload.model_dump_json()}\n\n"


OPENROUTER_RETRY_MODEL_KEYS: tuple[str, ...] = (
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
    "poolside/laguna-m1:free",
)


async def _load_retry_models(
    db: AsyncSession,
    *,
    selected_model_key: str,
) -> list[ModelCatalog]:
    fallback_models: list[ModelCatalog] = []
    for model_key in OPENROUTER_RETRY_MODEL_KEYS:
        if model_key == selected_model_key:
            continue
        model = await get_model_by_key(db, "openrouter", model_key)
        if model is not None:
            fallback_models.append(model)
    return fallback_models

@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationListResponse:
    items = await list_conversations(db, identity.user.id)
    return ConversationListResponse(items=[_conversation_response(item) for item in items])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def post_conversation(
    payload: ConversationCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    try:
        conversation = await create_conversation(
            db,
            owner_id=identity.user.id,
            title=payload.title,
            classification=payload.classification,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conversation title already exists for this owner",
        ) from exc
    return _conversation_response(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_detail(
    conversation_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return _conversation_response(conversation)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def patch_conversation(
    conversation_id: UUID,
    payload: ConversationUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if payload.title is not None:
        conversation.title = payload.title
    if payload.classification is not None:
        conversation.classification = payload.classification
    conversation.version += 1
    await db.commit()
    await db.refresh(conversation)
    return _conversation_response(conversation)


@router.delete("/{conversation_id}", response_model=ConversationResponse)
async def remove_conversation(
    conversation_id: UUID,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    deleted = await delete_conversation(db, conversation=conversation)
    return _conversation_response(deleted)


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MessageListResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    items = await list_messages(db, identity.user.id, conversation_id)
    return MessageListResponse(items=[_message_response(item) for item in items])


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_conversation_message(
    conversation_id: UUID,
    payload: MessageCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MessageCreateResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    message = await create_message(
        db,
        owner_id=identity.user.id,
        conversation=conversation,
        role=payload.role,
        content=payload.content,
        content_format=payload.content_format,
        classification=payload.classification,
        parent_message_id=payload.parent_message_id,
    )
    selection = await resolve_route_selection(
        db,
        owner_id=identity.user.id,
        classification=payload.classification,
        purpose="conversation.reply",
        route_mode="fast",
        model_policy_id=conversation.default_model_policy_id,
    )
    response = await create_response_run(
        db,
        owner_id=identity.user.id,
        conversation_id=conversation.id,
        user_message_id=message.id,
        route=selection.path,
        route_reason=selection.route_reason,
        prompt_version=selection.prompt_version,
        model_provider=selection.model_provider,
        model_name=selection.model_name,
    )
    return MessageCreateResponse(message=_message_response(message), response_id=response.id)


async def _ensure_response_ready(
    db: AsyncSession,
    *,
    response: ResponseRun,
) -> ResponseRun:
    if response.status == "completed" and response.response_text:
        return response

    user_message = response.user_message
    model = await get_model_by_key(db, response.model_provider, response.model_name)
    if model is None:
        await fail_response_run(
            db, response=response, error_message="Selected model is not registered"
        )
        return response

    system_prompt = (
        "You are NOVO, the owner-first AI OS. Respond calmly, directly, and helpfully. "
        "Write in plain text with short paragraphs. If you use headings, put them on "
        "their own line "
        "without markdown symbols like ### or **. Use simple hyphen bullets only when helpful. "
        "Avoid dense markdown formatting unless the user explicitly asks for it."
    )
    fallback_models = await _load_retry_models(
        db,
        selected_model_key=model.model_key,
    )
    reply_result = await generate_model_reply(
        model=model,
        user_message=user_message.content,
        prompt_version=response.prompt_version,
        system_prompt=system_prompt,
        fallback_models=fallback_models,
    )
    if not reply_result.safe_text.strip():
        await fail_response_run(db, response=response, error_message="Empty response text")
        return response

    prompt_source = f"{response.prompt_version}:{user_message.content}"
    prompt_hash = sha256(prompt_source.encode()).hexdigest()
    model_call = await create_model_call(
        db,
        owner_id=response.owner_id,
        model=model,
        message_id=user_message.id,
        route_reason=response.route_reason,
        classification_max=user_message.classification,
        prompt_hash=prompt_hash,
        input_tokens=len(user_message.content.split()),
    )
    assistant_message = await create_message(
        db,
        owner_id=response.owner_id,
        conversation=response.conversation,
        role="assistant",
        content=reply_result.safe_text,
        content_format="text/plain",
        classification=user_message.classification,
        parent_message_id=user_message.id,
    )
    assistant_message.model_call_id = model_call.id
    if reply_result.provider_request_id is not None:
        model_call.provider_request_id = reply_result.provider_request_id
    metadata: dict[str, object] = {}
    if reply_result.findings:
        metadata["guardrail_warnings"] = [finding.code for finding in reply_result.findings]
    if reply_result.used_fallback and reply_result.fallback_reason:
        metadata["fallback_used"] = True
        metadata["fallback_reason"] = reply_result.fallback_reason
        if reply_result.fallback_detail_safe:
            metadata["fallback_detail_safe"] = reply_result.fallback_detail_safe
        metadata["attempts"] = reply_result.attempts
    if metadata:
        assistant_message.metadata_json = metadata
    await complete_model_call(
        db,
        call=model_call,
        response_text=reply_result.safe_text,
        output_tokens=len(reply_result.safe_text.split()),
        latency_ms=25,
        warning_code=reply_result.fallback_reason if reply_result.used_fallback else None,
        warning_detail_safe=(
            reply_result.fallback_detail_safe if reply_result.used_fallback else None
        ),
    )
    await complete_response_run(
        db,
        response=response,
        response_text=reply_result.safe_text,
        assistant_message=assistant_message,
        latency_ms=25,
    )
    return response


@router.get("/responses/{response_id}/events")
async def stream_response_events(
    response_id: UUID,
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> StreamingResponse:
    response = await get_response_run(db, identity.user.id, response_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")

    async def event_generator() -> AsyncIterator[str]:
        event_id = 1
        try:
                yield _sse_event(
                    event_id,
                    "response.started",
                    ResponseEventStarted(
                        response_id=response.id,
                        conversation_id=response.conversation_id,
                        user_message_id=response.user_message_id,
                    ),
                )
                event_id += 1
                yield _sse_event(
                    event_id,
                    "response.route_selected",
                    ResponseEventRouteSelected(
                        response_id=response.id,
                        path=response.route,
                        route_reason=response.route_reason,
                        prompt_version=response.prompt_version,
                        model_provider=response.model_provider,
                        model_name=response.model_name,
                    ),
                )
                event_id += 1

                user_findings = inspect_text(response.user_message.content)
                if user_findings:
                    yield _sse_event(
                        event_id,
                        "response.warning",
                        ResponseEventWarning(
                            response_id=response.id,
                            warnings=[finding.code for finding in user_findings],
                        ),
                    )
                    event_id += 1

                yield _sse_event(
                    event_id,
                    "response.context_ready",
                    ResponseEventContextReady(
                        response_id=response.id,
                        conversation_id=response.conversation_id,
                        user_message_id=response.user_message_id,
                    ),
                )
                event_id += 1

                if response.status == "completed" and response.response_text:
                    assistant_query = await db.execute(
                        select(Message).where(
                            Message.parent_message_id == response.user_message_id,
                            Message.role == "assistant",
                            Message.owner_id == response.owner_id,
                        )
                    )
                    assistant_message_obj = assistant_query.scalar_one_or_none()
                    if assistant_message_obj is None:
                        yield _sse_event(
                            event_id,
                            "response.failed",
                            ResponseEventFailed(
                                response_id=response.id,
                                error_message="Assistant message missing",
                            ),
                        )
                        return
                    running_text = []
                    for index, token in enumerate(response.response_text.split(), start=1):
                        running_text.append(token)
                        yield _sse_event(
                            event_id,
                            "response.token",
                            ResponseEventToken(
                                response_id=response.id,
                                index=index,
                                token=token,
                                content=" ".join(running_text),
                            ),
                        )
                        event_id += 1
                        await asyncio.sleep(0)
                    yield _sse_event(
                        event_id,
                        "response.completed",
                        ResponseEventCompleted(
                            response_id=response.id,
                            conversation_id=response.conversation_id,
                            assistant_message=_message_response(
                                assistant_message_obj,
                                response_id=response.id,
                            ),
                        ),
                    )
                    return

                model = await get_model_by_key(db, response.model_provider, response.model_name)
                if model is None:
                    await fail_response_run(
                        db,
                        response=response,
                        error_message="Selected model is not registered",
                    )
                    yield _sse_event(
                        event_id,
                        "response.failed",
                        ResponseEventFailed(
                            response_id=response.id,
                            error_message="Selected model is not registered",
                        ),
                    )
                    return

                started_at = perf_counter()
                prompt_source = f"{response.prompt_version}:{response.user_message.content}"
                prompt_hash = sha256(prompt_source.encode()).hexdigest()
                model_call = await create_model_call(
                    db,
                    owner_id=response.owner_id,
                    model=model,
                    message_id=response.user_message.id,
                    route_reason=response.route_reason,
                    classification_max=response.user_message.classification,
                    prompt_hash=prompt_hash,
                    input_tokens=len(response.user_message.content.split()),
                )
                system_prompt = (
                    "You are NOVO, the owner-first AI OS. Respond calmly, directly, and helpfully. "
                    "Write in plain text with short paragraphs. If you use headings, put them on "
                    "their own line "
                    "without markdown symbols like ### or **. Use simple hyphen bullets only when helpful. "
                    "Avoid dense markdown formatting unless the user explicitly asks for it."
                )
                running_text_parts: list[str] = []
                token_index = 0
                final_chunk = None

                async for chunk in stream_model_reply(
                    model=model,
                    user_message=response.user_message.content,
                    prompt_version=response.prompt_version,
                    system_prompt=system_prompt,
                ):
                    if chunk.token:
                        token_index += 1
                        running_text_parts.append(chunk.token)
                        yield _sse_event(
                            event_id,
                            "response.token",
                            ResponseEventToken(
                                response_id=response.id,
                                index=token_index,
                                token=chunk.token,
                                content="".join(running_text_parts),
                            ),
                        )
                        event_id += 1
                        await asyncio.sleep(0)
                    if chunk.done:
                        final_chunk = chunk

                if final_chunk is None or not final_chunk.safe_text.strip():
                    await fail_response_run(db, response=response, error_message="Empty response text")
                    yield _sse_event(
                        event_id,
                        "response.failed",
                        ResponseEventFailed(response_id=response.id, error_message="Empty response text"),
                    )
                    return

                if final_chunk.provider_request_id is not None:
                    model_call.provider_request_id = final_chunk.provider_request_id

                assistant_message = await create_message(
                    db,
                    owner_id=response.owner_id,
                    conversation=response.conversation,
                    role="assistant",
                    content=final_chunk.safe_text,
                    content_format="text/plain",
                    classification=response.user_message.classification,
                    parent_message_id=response.user_message.id,
                )
                assistant_message.model_call_id = model_call.id
                metadata: dict[str, object] = {}
                if final_chunk.findings:
                    metadata["guardrail_warnings"] = [finding.code for finding in final_chunk.findings]
                if final_chunk.used_fallback and final_chunk.fallback_reason:
                    metadata["fallback_used"] = True
                    metadata["fallback_reason"] = final_chunk.fallback_reason
                    if final_chunk.fallback_detail_safe:
                        metadata["fallback_detail_safe"] = final_chunk.fallback_detail_safe
                    metadata["attempts"] = final_chunk.attempts
                if metadata:
                    assistant_message.metadata_json = metadata
                latency_ms = int((perf_counter() - started_at) * 1000)
                await complete_model_call(
                    db,
                    call=model_call,
                    response_text=final_chunk.safe_text,
                    output_tokens=len(final_chunk.safe_text.split()),
                    latency_ms=latency_ms,
                    warning_code=(
                        final_chunk.fallback_reason if final_chunk.used_fallback else None
                    ),
                    warning_detail_safe=(
                        final_chunk.fallback_detail_safe if final_chunk.used_fallback else None
                    ),
                )
                await complete_response_run(
                    db,
                    response=response,
                    response_text=final_chunk.safe_text,
                    assistant_message=assistant_message,
                    latency_ms=latency_ms,
                )
                yield _sse_event(
                    event_id,
                    "response.completed",
                    ResponseEventCompleted(
                        response_id=response.id,
                        conversation_id=response.conversation_id,
                        assistant_message=_message_response(assistant_message, response_id=response.id),
                    ),
                )
        except Exception:
            logger.exception(
                "NOVO conversation response streaming failed",
                extra={
                    "response_id": str(response.id),
                    "conversation_id": str(response.conversation_id),
                    "user_message_id": str(response.user_message_id),
                },
            )
            try:
                await db.rollback()
                await fail_response_run(
                    db,
                    response=response,
                    error_message="NOVO backend error while generating the reply",
                )
            except Exception:
                logger.exception(
                    "NOVO failed to persist response failure",
                    extra={
                        "response_id": str(response.id),
                        "conversation_id": str(response.conversation_id),
                    },
                )
            yield _sse_event(
                event_id,
                "response.failed",
                ResponseEventFailed(
                    response_id=response.id,
                    error_message="NOVO hit a backend error while generating the reply. Check the backend terminal for details.",
                ),
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{conversation_id}/archive", response_model=ConversationResponse)
async def archive_conversation_route(
    conversation_id: UUID,
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    conversation = await get_conversation(db, identity.user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    archived = await archive_conversation(db, conversation=conversation)
    return _conversation_response(archived)
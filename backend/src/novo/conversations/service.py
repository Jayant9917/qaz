"""Conversation service helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.conversations.models import Conversation, Message
from novo.conversations.responses import ResponseRun


async def list_conversations(db: AsyncSession, owner_id: UUID) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.owner_id == owner_id,
            Conversation.deleted_at.is_(None),
        )
        .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(
    db: AsyncSession, owner_id: UUID, conversation_id: UUID
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == owner_id,
            Conversation.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_conversation(
    db: AsyncSession,
    *,
    owner_id: UUID,
    title: str,
    classification: str = "private",
) -> Conversation:
    conversation = Conversation(
        owner_id=owner_id,
        title=title,
        classification=classification,
        status="active",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def archive_conversation(
    db: AsyncSession,
    *,
    conversation: Conversation,
) -> Conversation:
    conversation.status = "archived"
    conversation.archived_at = datetime.now(UTC)
    conversation.updated_at = conversation.archived_at
    conversation.version += 1
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(
    db: AsyncSession,
    *,
    conversation: Conversation,
) -> Conversation:
    conversation.status = "deleted"
    conversation.deleted_at = datetime.now(UTC)
    conversation.updated_at = conversation.deleted_at
    conversation.version += 1
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def list_messages(db: AsyncSession, owner_id: UUID, conversation_id: UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(
            Message.owner_id == owner_id,
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None),
        )
        .order_by(Message.sequence_no.asc())
    )
    return list(result.scalars().all())


async def create_message(
    db: AsyncSession,
    *,
    owner_id: UUID,
    conversation: Conversation,
    role: str,
    content: str,
    content_format: str = "text/plain",
    classification: str = "private",
    parent_message_id: UUID | None = None,
) -> Message:
    next_sequence = await db.scalar(
        select(func.coalesce(func.max(Message.sequence_no), 0)).where(
            Message.conversation_id == conversation.id,
        )
    )
    message = Message(
        owner_id=owner_id,
        conversation_id=conversation.id,
        parent_message_id=parent_message_id,
        sequence_no=int(next_sequence or 0) + 1,
        role=role,
        content=content,
        content_format=content_format,
        classification=classification,
        status="created",
    )
    conversation.version += 1
    conversation.updated_at = datetime.now(UTC)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    await db.refresh(conversation)
    return message


async def create_response_run(
    db: AsyncSession,
    *,
    owner_id: UUID,
    conversation_id: UUID,
    user_message_id: UUID,
    route: str = "fast",
    route_reason: str = "fast-path stub",
    prompt_version: str = "e2.stub.v1",
    model_provider: str = "stub",
    model_name: str = "echo",
) -> ResponseRun:
    response = ResponseRun(
        owner_id=owner_id,
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        status="queued",
        route=route,
        route_reason=route_reason,
        prompt_version=prompt_version,
        model_provider=model_provider,
        model_name=model_name,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response


async def get_response_run(
    db: AsyncSession, owner_id: UUID, response_id: UUID
) -> ResponseRun | None:
    result = await db.execute(
        select(ResponseRun).where(
            ResponseRun.id == response_id,
            ResponseRun.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def complete_response_run(
    db: AsyncSession,
    *,
    response: ResponseRun,
    response_text: str,
    assistant_message: Message,
    latency_ms: int,
) -> ResponseRun:
    response.status = "completed"
    response.response_text = response_text
    response.token_count = len(response_text.split())
    response.latency_ms = latency_ms
    response.completed_at = datetime.now(UTC)
    response.error_message = None
    assistant_message.status = "completed"
    assistant_message.token_count = response.token_count
    assistant_message.content = response_text
    assistant_message.edited_at = response.completed_at
    await db.commit()
    await db.refresh(response)
    await db.refresh(assistant_message)
    return response


async def fail_response_run(
    db: AsyncSession,
    *,
    response: ResponseRun,
    error_message: str,
) -> ResponseRun:
    response.status = "failed"
    response.error_message = error_message
    response.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(response)
    return response



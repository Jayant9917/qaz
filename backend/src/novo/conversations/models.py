"""Conversation domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novo.infrastructure.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index("ix_chat_conversations_owner_updated_at", "owner_id", "updated_at"),
        UniqueConstraint("owner_id", "title", name="uq_chat_conversations_owner_title"),
        {"schema": "chat"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    classification: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_model_policy_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    messages: Mapped[list[Any]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Message.sequence_no",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index("ix_chat_messages_conversation_sequence", "conversation_id", "sequence_no"),
        Index("ix_chat_messages_owner_created_at", "owner_id", "created_at"),
        Index("ix_chat_messages_parent_message_id", "parent_message_id"),
        UniqueConstraint("conversation_id", "sequence_no", name="uq_chat_messages_sequence"),
        {"schema": "chat"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_message_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat.messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(24), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(40), nullable=False, default="text/plain")
    classification: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="created")
    model_call_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    tool_action_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages", lazy="joined"
    )

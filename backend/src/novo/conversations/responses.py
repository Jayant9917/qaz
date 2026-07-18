"""Response run models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novo.infrastructure.base import Base


class ResponseRun(Base):
    __tablename__ = "responses"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "chat"}

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
    user_message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat.messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    route: Mapped[str] = mapped_column(String(32), nullable=False, default="fast")
    route_reason: Mapped[str] = mapped_column(String(240), nullable=False, default="fast-path stub")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="e2.stub.v1")
    model_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="stub")
    model_name: Mapped[str] = mapped_column(String(80), nullable=False, default="echo")
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Any] = relationship("Conversation", lazy="joined")
    user_message: Mapped[Any] = relationship("Message", lazy="joined")

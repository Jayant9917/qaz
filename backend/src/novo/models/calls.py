"""Model call accounting records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novo.infrastructure.base import Base


class ModelCall(Base):
    __tablename__ = "model_calls"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index("ix_platform_model_calls_owner_started_at", "owner_id", "started_at"),
        Index("ix_platform_model_calls_model_started_at", "model_id", "started_at"),
        Index("ix_platform_model_calls_message_id", "message_id"),
        Index("ix_platform_model_calls_provider_request_id", "provider_request_id"),
        {"schema": "platform"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    message_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat.messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("platform.model_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    route_reason: Mapped[str] = mapped_column(String(240), nullable=False)
    classification_max: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    provider_request_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="running")
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USD")
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    error_detail_safe: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    model: Mapped[Any] = relationship("ModelCatalog", lazy="joined")

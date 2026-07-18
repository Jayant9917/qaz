"""Explicit memory domain models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novo.infrastructure.base import Base


class Memory(Base):
    __tablename__ = "memories"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="memory_confidence_range"),
        CheckConstraint("importance >= 0 AND importance <= 1", name="memory_importance_range"),
        CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from",
            name="memory_valid_window_order",
        ),
        Index("ix_memory_memories_owner_status_kind", "owner_id", "status", "kind"),
        Index("ix_memory_memories_owner_classification", "owner_id", "classification"),
        Index("ix_memory_memories_review_after", "review_after"),
        Index("ix_memory_memories_retention_until", "retention_until"),
        {"schema": "memory"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    canonical_content: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, default=Decimal("1.000")
    )
    importance: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, default=Decimal("0.500")
    )
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(120), nullable=False, default="explicit_remember"
    )
    source_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    source_locator: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(120), nullable=False, default="explicit")
    embedding_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="not_requested"
    )
    embedding_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    access_events: Mapped[list[Any]] = relationship(
        "MemoryAccessEvent",
        back_populates="memory",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="MemoryAccessEvent.created_at",
    )


class MemoryRevision(Base):
    __tablename__ = "memory_revisions"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index("ix_memory_revisions_owner_memory_created_at", "owner_id", "memory_id", "created_at"),
        {"schema": "memory"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("memory.memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    canonical_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    source_type: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class MemoryAccessEvent(Base):
    __tablename__ = "memory_access_events"
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index("ix_memory_access_events_owner_created_at", "owner_id", "created_at"),
        Index("ix_memory_access_events_memory_created_at", "memory_id", "created_at"),
        {"schema": "memory"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("memory.memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    agent_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    purpose: Mapped[str] = mapped_column(String(120), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    policy_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    used_in_prompt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    memory: Mapped[Memory] = relationship("Memory", back_populates="access_events", lazy="joined")

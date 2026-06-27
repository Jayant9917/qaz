"""Governance and permission models."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novo.infrastructure.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        PGUUID(as_uuid=True),
        ForeignKey("identity.roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        PGUUID(as_uuid=True),
        ForeignKey("governance.permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema="governance",
)


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "governance"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    roles: Mapped[list[object]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin",
    )


class SystemControlState(Base):
    __tablename__ = "system_control_state"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "governance"}

    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automations_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tools_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_models_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    security_mode: Mapped[str] = mapped_column(String(24), nullable=False, default="assistant")
    changed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ControlEvent(Base):
    __tablename__ = "control_events"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "governance"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    previous_value: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

"""Redis working context models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkingContext(BaseModel):
    model_config = ConfigDict(extra="ignore")

    owner_id: UUID
    session_id: UUID
    conversation_id: UUID | None = None
    current_response_id: UUID | None = None
    last_response_id: UUID | None = None
    last_user_message_id: UUID | None = None
    last_assistant_message_id: UUID | None = None
    status: str = "empty"
    summary: str | None = None
    active_task: str | None = None
    notes: list[str] = Field(default_factory=list)
    stream_cursor: str | None = None
    last_event: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None

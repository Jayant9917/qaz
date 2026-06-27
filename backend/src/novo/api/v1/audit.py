"""Audit log routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, require_permission
from novo.identity.service import list_audit_logs
from novo.infrastructure.database import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    session_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    outcome: str
    request_id: str | None
    details: dict[str, object]
    created_at: str


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[RequestIdentity, Depends(require_permission("audit.read"))],
) -> list[AuditLogResponse]:
    logs = await list_audit_logs(db, 100)
    return [
        AuditLogResponse(
            id=log.id,
            actor_user_id=log.actor_user_id,
            session_id=log.session_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            outcome=log.outcome,
            request_id=log.request_id,
            details=log.details,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]

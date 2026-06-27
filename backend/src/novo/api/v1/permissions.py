"""Permission catalog routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, require_permission
from novo.governance.models import Permission
from novo.identity.service import list_permissions, log_event
from novo.infrastructure.database import get_session

router = APIRouter(prefix="/permissions", tags=["permissions"])


class PermissionCreateRequest(BaseModel):
    key: str = Field(min_length=3, max_length=120)
    resource: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=120)
    risk_level: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=500)


class PermissionResponse(BaseModel):
    id: UUID
    key: str
    resource: str
    action: str
    risk_level: str
    description: str


@router.get("", response_model=list[PermissionResponse])
async def get_permissions(
    db: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[RequestIdentity, Depends(require_permission("permissions.read"))],
) -> list[PermissionResponse]:
    permissions = await list_permissions(db)
    return [
        PermissionResponse(
            id=permission.id,
            key=permission.key,
            resource=permission.resource,
            action=permission.action,
            risk_level=permission.risk_level,
            description=permission.description,
        )
        for permission in permissions
    ]


@router.post("", response_model=PermissionResponse)
async def create_permission(
    payload: PermissionCreateRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("permissions.write"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PermissionResponse:
    existing = await db.scalar(select(Permission).where(Permission.key == payload.key))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission already exists",
        )

    permission = Permission(
        key=payload.key,
        resource=payload.resource,
        action=payload.action,
        risk_level=payload.risk_level,
        description=payload.description,
    )
    db.add(permission)
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="permissions.create",
        resource_type="permission",
        resource_id=payload.key,
        outcome="success",
        details={"resource": payload.resource, "action": payload.action},
    )
    await db.commit()
    await db.refresh(permission)
    return PermissionResponse(
        id=permission.id,
        key=permission.key,
        resource=permission.resource,
        action=permission.action,
        risk_level=permission.risk_level,
        description=permission.description,
    )

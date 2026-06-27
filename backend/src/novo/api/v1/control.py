"""System control state routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, require_csrf_protection, require_permission
from novo.core.config import Settings, get_settings
from novo.governance.models import SystemControlState
from novo.governance.service import (
    VALID_SECURITY_MODES,
    activate_kill_switch,
    deactivate_kill_switch,
    get_system_control_state,
    list_control_events,
    set_control_state,
)
from novo.infrastructure.database import get_session
from novo.infrastructure.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/control", tags=["control"])


class ControlStateResponse(BaseModel):
    owner_id: UUID
    kill_switch_active: bool
    automations_enabled: bool
    tools_enabled: bool
    external_models_enabled: bool
    security_mode: str
    changed_by: UUID | None
    change_reason: str | None
    changed_at: datetime
    version: int


class ControlStateUpdateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    kill_switch_active: bool | None = None
    automations_enabled: bool | None = None
    tools_enabled: bool | None = None
    external_models_enabled: bool | None = None
    security_mode: str | None = Field(default=None, max_length=24)


class KillSwitchRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ControlEventResponse(BaseModel):
    id: UUID
    owner_id: UUID
    control_name: str
    previous_value: str | None
    new_value: str | None
    actor_id: UUID | None
    reason: str | None
    created_at: datetime
    trace_id: str | None


def _state_response(state: SystemControlState) -> ControlStateResponse:
    return ControlStateResponse(
        owner_id=state.owner_id,
        kill_switch_active=state.kill_switch_active,
        automations_enabled=state.automations_enabled,
        tools_enabled=state.tools_enabled,
        external_models_enabled=state.external_models_enabled,
        security_mode=state.security_mode,
        changed_by=state.changed_by,
        change_reason=state.change_reason,
        changed_at=state.changed_at,
        version=state.version,
    )


@router.get("/state", response_model=ControlStateResponse)
async def read_control_state(
    identity: Annotated[RequestIdentity, Depends(require_permission("security.control.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ControlStateResponse:
    state = await get_system_control_state(db, identity.user.id)
    await db.commit()
    return _state_response(state)


@router.patch("/state", response_model=ControlStateResponse)
async def update_control_state(
    payload: ControlStateUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("security.control.write"))],
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ControlStateResponse:
    await enforce_rate_limit(
        f"control:state:update:{identity.user.id}",
        limit=settings.mutation_rate_limit,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )
    if (
        payload.security_mode is not None
        and payload.security_mode.strip().casefold() not in VALID_SECURITY_MODES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid security mode"
        )

    state = await set_control_state(
        db,
        owner_id=identity.user.id,
        actor_id=identity.user.id,
        reason=payload.reason,
        kill_switch_active=payload.kill_switch_active,
        automations_enabled=payload.automations_enabled,
        tools_enabled=payload.tools_enabled,
        external_models_enabled=payload.external_models_enabled,
        security_mode=payload.security_mode,
    )
    await db.commit()
    return _state_response(state)


@router.post("/kill-switch/activate", response_model=ControlStateResponse)
async def activate(
    payload: KillSwitchRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("security.kill_switch.write"))],
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ControlStateResponse:
    await enforce_rate_limit(
        f"control:kill-switch:activate:{identity.user.id}",
        limit=settings.mutation_rate_limit,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )
    state = await activate_kill_switch(
        db, owner_id=identity.user.id, actor_id=identity.user.id, reason=payload.reason
    )
    await db.commit()
    return _state_response(state)


@router.post("/kill-switch/deactivate", response_model=ControlStateResponse)
async def deactivate(
    payload: KillSwitchRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("security.kill_switch.write"))],
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ControlStateResponse:
    await enforce_rate_limit(
        f"control:kill-switch:deactivate:{identity.user.id}",
        limit=settings.mutation_rate_limit,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )
    state = await deactivate_kill_switch(
        db, owner_id=identity.user.id, actor_id=identity.user.id, reason=payload.reason
    )
    await db.commit()
    return _state_response(state)


@router.get("/events", response_model=list[ControlEventResponse])
async def read_control_events(
    identity: Annotated[RequestIdentity, Depends(require_permission("security.control.read"))],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ControlEventResponse]:
    events = await list_control_events(db, identity.user.id, 100)
    return [
        ControlEventResponse(
            id=event.id,
            owner_id=event.owner_id,
            control_name=event.control_name,
            previous_value=event.previous_value,
            new_value=event.new_value,
            actor_id=event.actor_id,
            reason=event.reason,
            created_at=event.created_at,
            trace_id=event.trace_id,
        )
        for event in events
    ]

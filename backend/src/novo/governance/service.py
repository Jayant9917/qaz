"""Governance state services."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.core.request_context import get_request_id
from novo.governance.models import ControlEvent, SystemControlState
from novo.infrastructure.cache import get_redis
from novo.infrastructure.rls import apply_owner_context

VALID_SECURITY_MODES = {"observer", "assistant", "operator", "autonomous"}
CONTROL_STATE_CACHE_PREFIX = "novo:control-state:"


class ControlStateError(ValueError):
    pass


async def get_system_control_state(db: AsyncSession, owner_id: UUID) -> SystemControlState:
    await apply_owner_context(db, owner_id)
    state = await db.scalar(
        select(SystemControlState).where(SystemControlState.owner_id == owner_id)
    )
    if state is None:
        state = SystemControlState(owner_id=owner_id)
        db.add(state)
        await db.flush()
    return state


async def list_control_events(
    db: AsyncSession, owner_id: UUID, limit: int = 100
) -> list[ControlEvent]:
    await apply_owner_context(db, owner_id)
    result = await db.scalars(
        select(ControlEvent)
        .where(ControlEvent.owner_id == owner_id)
        .order_by(ControlEvent.created_at.desc())
        .limit(limit)
    )
    return list(result)


async def _store_projection(state: SystemControlState) -> None:
    payload = {
        "owner_id": str(state.owner_id),
        "kill_switch_active": state.kill_switch_active,
        "automations_enabled": state.automations_enabled,
        "tools_enabled": state.tools_enabled,
        "external_models_enabled": state.external_models_enabled,
        "security_mode": state.security_mode,
        "changed_by": str(state.changed_by) if state.changed_by else None,
        "change_reason": state.change_reason,
        "changed_at": state.changed_at.isoformat() if state.changed_at else None,
        "version": state.version,
    }
    try:
        await get_redis().set(
            f"{CONTROL_STATE_CACHE_PREFIX}{state.owner_id}",
            json.dumps(payload, separators=(",", ":")),
            ex=300,
        )
    except Exception:
        return


async def set_control_state(
    db: AsyncSession,
    *,
    owner_id: UUID,
    actor_id: UUID,
    reason: str,
    kill_switch_active: bool | None = None,
    automations_enabled: bool | None = None,
    tools_enabled: bool | None = None,
    external_models_enabled: bool | None = None,
    security_mode: str | None = None,
) -> SystemControlState:
    await apply_owner_context(db, owner_id)
    state = await get_system_control_state(db, owner_id)
    previous = {
        "kill_switch_active": state.kill_switch_active,
        "automations_enabled": state.automations_enabled,
        "tools_enabled": state.tools_enabled,
        "external_models_enabled": state.external_models_enabled,
        "security_mode": state.security_mode,
    }

    if security_mode is not None:
        normalized = security_mode.strip().casefold()
        if normalized not in VALID_SECURITY_MODES:
            raise ControlStateError(f"Invalid security mode: {security_mode}")
        state.security_mode = normalized

    if kill_switch_active is not None:
        state.kill_switch_active = kill_switch_active
    if automations_enabled is not None:
        state.automations_enabled = automations_enabled
    if tools_enabled is not None:
        state.tools_enabled = tools_enabled
    if external_models_enabled is not None:
        state.external_models_enabled = external_models_enabled

    state.changed_by = actor_id
    state.change_reason = reason
    state.changed_at = datetime.now(UTC)
    state.version += 1

    current = {
        "kill_switch_active": state.kill_switch_active,
        "automations_enabled": state.automations_enabled,
        "tools_enabled": state.tools_enabled,
        "external_models_enabled": state.external_models_enabled,
        "security_mode": state.security_mode,
    }

    db.add(
        ControlEvent(
            owner_id=owner_id,
            control_name="system_control_state",
            previous_value=json.dumps(previous, separators=(",", ":")),
            new_value=json.dumps(current, separators=(",", ":")),
            actor_id=actor_id,
            reason=reason,
            trace_id=get_request_id(),
        )
    )
    await db.flush()
    await _store_projection(state)
    return state


async def activate_kill_switch(
    db: AsyncSession, *, owner_id: UUID, actor_id: UUID, reason: str
) -> SystemControlState:
    return await set_control_state(
        db,
        owner_id=owner_id,
        actor_id=actor_id,
        reason=reason,
        kill_switch_active=True,
        automations_enabled=False,
        tools_enabled=False,
        external_models_enabled=False,
    )


async def deactivate_kill_switch(
    db: AsyncSession, *, owner_id: UUID, actor_id: UUID, reason: str
) -> SystemControlState:
    return await set_control_state(
        db,
        owner_id=owner_id,
        actor_id=actor_id,
        reason=reason,
        kill_switch_active=False,
    )

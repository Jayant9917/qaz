"""Reusable API dependencies for identity and authorization."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from novo.governance.service import get_system_control_state
from novo.identity.models import Session, User
from novo.identity.security import hash_csrf_token
from novo.identity.service import load_auth_context
from novo.infrastructure.database import get_session
from novo.infrastructure.rls import apply_owner_context


@dataclass(slots=True)
class RequestIdentity:
    user: User
    session: Session
    roles: list[str]
    permissions: list[str]


async def get_session_token(
    authorization: Annotated[str | None, Header()] = None,
    session_cookie: Annotated[str | None, Cookie(alias="novo_session")] = None,
) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        if token:
            return token

    if session_cookie:
        token = session_cookie.strip()
        if token:
            return token

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session token")


async def get_csrf_token(
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> str:
    if not x_csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    token = x_csrf_token.strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return token


async def get_request_identity(
    db: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str, Depends(get_session_token)],
) -> RequestIdentity:
    context = await load_auth_context(db, token)
    await apply_owner_context(db, context.user.id)
    return RequestIdentity(
        user=context.user,
        session=context.session,
        roles=context.roles,
        permissions=context.permissions,
    )


_KILL_SWITCH_BYPASS_PERMISSIONS = {
    "auth.read",
    "audit.read",
    "permissions.read",
    "security.control.read",
    "security.kill_switch.write",
}


def require_permission(permission_key: str) -> Callable[[RequestIdentity], RequestIdentity]:
    async def dependency(
        identity: Annotated[RequestIdentity, Depends(get_request_identity)],
        db: Annotated[AsyncSession, Depends(get_session)],
    ) -> RequestIdentity:
        state = await get_system_control_state(db, identity.user.id)
        if state.kill_switch_active and permission_key not in _KILL_SWITCH_BYPASS_PERMISSIONS:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Kill switch active")
        if permission_key not in identity.permissions and "*" not in identity.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return identity

    return dependency


async def require_csrf_protection(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    csrf_token: Annotated[str, Depends(get_csrf_token)],
) -> RequestIdentity:
    expected = identity.session.csrf_token_hash
    if not expected or hash_csrf_token(csrf_token) != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return identity

"""Reusable API dependencies for identity and authorization."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from novo.identity.models import Session, User
from novo.identity.service import load_auth_context
from novo.infrastructure.database import get_session


@dataclass(slots=True)
class RequestIdentity:
    user: User
    session: Session
    roles: list[str]
    permissions: list[str]


async def get_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return token


async def get_request_identity(
    db: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str, Depends(get_bearer_token)],
) -> RequestIdentity:
    context = await load_auth_context(db, token)
    return RequestIdentity(
        user=context.user,
        session=context.session,
        roles=context.roles,
        permissions=context.permissions,
    )


def require_permission(permission_key: str) -> Callable[[RequestIdentity], RequestIdentity]:
    async def dependency(
        identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    ) -> RequestIdentity:
        if permission_key not in identity.permissions and "*" not in identity.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return identity

    return dependency

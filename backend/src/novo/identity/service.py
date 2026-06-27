"""Identity and session services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.audit.models import AuditLog
from novo.core.config import Settings
from novo.core.request_context import get_request_id
from novo.governance.models import Permission, role_permissions
from novo.governance.service import get_system_control_state
from novo.identity.models import Role, Session, User, user_roles
from novo.identity.security import (
    generate_csrf_token,
    generate_session_token,
    hash_csrf_token,
    hash_password,
    hash_session_token,
    normalize_email,
    verify_password,
)

OWNER_ROLE_KEY = "owner"
DEFAULT_PERMISSION_SEEDS = [
    ("auth.read", "auth", "read", "low", "Read authentication state"),
    ("auth.write", "auth", "write", "medium", "Manage authentication state"),
    ("audit.read", "audit", "read", "low", "Read audit logs"),
    ("audit.write", "audit", "write", "high", "Write audit logs"),
    ("permissions.read", "permissions", "read", "low", "Read permission catalog"),
    (
        "permissions.write",
        "permissions",
        "write",
        "medium",
        "Manage permission catalog",
    ),
    (
        "security.control.read",
        "security",
        "read",
        "medium",
        "Read system control state",
    ),
    (
        "security.control.write",
        "security",
        "write",
        "critical",
        "Manage system control state",
    ),
    (
        "security.kill_switch.write",
        "security",
        "write",
        "critical",
        "Control emergency kill switch",
    ),
]


@dataclass(slots=True)
class AuthContext:
    user: User
    session: Session
    roles: list[str]
    permissions: list[str]


async def log_event(
    db: AsyncSession,
    *,
    actor_user_id: str | None,
    session_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    outcome: str,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            session_id=session_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            request_id=get_request_id(),
            details=details or {},
        )
    )
    await db.flush()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == normalize_email(email)))


async def list_permissions(db: AsyncSession) -> list[Permission]:
    result = await db.scalars(select(Permission).order_by(Permission.key.asc()))
    return list(result)


async def list_audit_logs(db: AsyncSession, limit: int) -> list[AuditLog]:
    result = await db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return list(result)


async def ensure_security_seed(db: AsyncSession, settings: Settings) -> User:
    owner_role = await db.scalar(select(Role).where(Role.key == OWNER_ROLE_KEY))
    if owner_role is None:
        owner_role = Role(
            key=OWNER_ROLE_KEY,
            name="Owner",
            description="Full-control role for the NOVO owner",
            is_system=True,
        )
        db.add(owner_role)
        await db.flush()

    existing_permission_keys = set(
        await db.scalars(
            select(Permission.key)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == owner_role.id)
        )
    )

    for key, resource, action, risk_level, description in DEFAULT_PERMISSION_SEEDS:
        permission = await db.scalar(select(Permission).where(Permission.key == key))
        if permission is None:
            permission = Permission(
                key=key,
                resource=resource,
                action=action,
                risk_level=risk_level,
                description=description,
            )
            db.add(permission)
            await db.flush()

        if key not in existing_permission_keys:
            await db.execute(
                insert(role_permissions).values(role_id=owner_role.id, permission_id=permission.id)
            )
            existing_permission_keys.add(key)

    owner_email = normalize_email(settings.bootstrap_owner_email)
    owner_user = await db.scalar(select(User).where(User.email == owner_email))
    if owner_user is None:
        owner_user = User(
            email=owner_email,
            display_name=settings.bootstrap_owner_display_name,
            password_hash=hash_password(settings.bootstrap_owner_password),
            is_active=True,
        )
        owner_user.roles.append(owner_role)
        db.add(owner_user)
        await db.flush()

    await get_system_control_state(db, owner_user.id)
    await db.commit()
    return owner_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active or user.deleted_at is not None or user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_session(
    db: AsyncSession,
    *,
    user: User,
    session_ttl_hours: int,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[Session, str, str]:
    raw_token = generate_session_token()
    csrf_token = generate_csrf_token()
    token_hash = hash_session_token(raw_token)
    csrf_token_hash = hash_csrf_token(csrf_token)
    now = datetime.now(UTC)
    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        csrf_token_hash=csrf_token_hash,
        expires_at=now + timedelta(hours=session_ttl_hours),
        last_used_at=now,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()
    return session, raw_token, csrf_token


async def load_auth_context(db: AsyncSession, raw_token: str) -> AuthContext:
    token_hash = hash_session_token(raw_token)
    session = await db.scalar(
        select(Session)
        .where(Session.token_hash == token_hash)
        .where(Session.revoked_at.is_(None))
        .where(Session.expires_at > func.now())
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = await db.scalar(
        select(User).where(User.id == session.user_id).where(User.is_active.is_(True))
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    role_rows = await db.scalars(
        select(Role.key)
        .join(user_roles, user_roles.c.role_id == Role.id)
        .where(user_roles.c.user_id == user.id)
    )
    permission_rows = await db.scalars(
        select(Permission.key)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .join(Role, Role.id == role_permissions.c.role_id)
        .join(user_roles, user_roles.c.role_id == Role.id)
        .where(user_roles.c.user_id == user.id)
    )
    session.last_used_at = datetime.now(UTC)
    await db.flush()
    return AuthContext(
        user=user,
        session=session,
        roles=list(role_rows),
        permissions=list(permission_rows),
    )


async def revoke_session(db: AsyncSession, session: Session, reason: str) -> Session:
    session.revoked_at = datetime.now(UTC)
    session.revoked_reason = reason
    await db.flush()
    return session

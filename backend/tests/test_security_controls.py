"""Security control tests for E1 governance protections."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from novo.api.v1 import auth as auth_routes
from novo.core.config import get_settings
from novo.main import create_app


def bootstrap_owner(client: TestClient, *, email: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {}
    if email is not None:
        payload = {
            "email": email,
            "display_name": email.split("@")[0].title(),
            "password": "novo-owner-1234",
        }
    response = client.post("/api/v1/auth/bootstrap", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "csrf_token" in body
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(cookie.startswith("novo_session=") for cookie in set_cookie_headers)
    assert any(cookie.startswith("novo_csrf_token=") for cookie in set_cookie_headers)
    return body


@pytest.fixture
def strict_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("NOVO_LOGIN_RATE_LIMIT", "1")
    monkeypatch.setenv("NOVO_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_csrf_required_for_user_settings(client: TestClient) -> None:
    tokens = bootstrap_owner(client)

    blocked = client.patch(
        "/api/v1/auth/me/settings",
        json={"display_name": "Nova Owner"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "CSRF validation failed"

    allowed = client.patch(
        "/api/v1/auth/me/settings",
        headers={"X-CSRF-Token": str(tokens["csrf_token"])},
        json={"display_name": "Nova Owner"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["display_name"] == "Nova Owner"


def test_owner_isolation_for_control_state(client: TestClient) -> None:
    owner_one = bootstrap_owner(client)
    owner_two = bootstrap_owner(client, email="second.owner@novo.example")

    owner_one_headers = {
        "Authorization": f"Bearer {owner_one['access_token']}",
        "X-CSRF-Token": str(owner_one["csrf_token"]),
    }
    owner_two_headers = {
        "Authorization": f"Bearer {owner_two['access_token']}",
        "X-CSRF-Token": str(owner_two["csrf_token"]),
    }

    owner_one_state = client.get("/api/v1/control/state", headers=owner_one_headers)
    owner_two_state = client.get("/api/v1/control/state", headers=owner_two_headers)

    assert owner_one_state.status_code == 200
    assert owner_two_state.status_code == 200
    assert owner_one_state.json()["owner_id"] != owner_two_state.json()["owner_id"]

    switched = client.patch(
        "/api/v1/control/state",
        headers=owner_two_headers,
        json={"reason": "owner two update", "tools_enabled": True},
    )
    assert switched.status_code == 200
    assert switched.json()["owner_id"] == owner_two_state.json()["owner_id"]

    owner_one_refresh = client.get("/api/v1/control/state", headers=owner_one_headers)
    assert owner_one_refresh.status_code == 200
    assert owner_one_refresh.json()["owner_id"] == owner_one_state.json()["owner_id"]


def test_session_revocation_blocks_reuse(client: TestClient) -> None:
    owner = bootstrap_owner(client)
    csrf_token = str(owner["csrf_token"])
    headers = {"X-CSRF-Token": csrf_token}

    before = client.get("/api/v1/auth/me")
    assert before.status_code == 200

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.headers.get("set-cookie") is not None
    assert logout.status_code == 200

    after = client.get("/api/v1/auth/me")
    assert after.status_code == 401
    assert after.json()["detail"] in {"Invalid or expired session", "Missing session token"}


def test_audit_failure_blocks_mutation(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = bootstrap_owner(client)
    headers = {
        "Authorization": f"Bearer {owner['access_token']}",
        "X-CSRF-Token": str(owner["csrf_token"]),
    }

    before = client.get(
        "/api/v1/auth/me/settings", headers={"Authorization": f"Bearer {owner['access_token']}"}
    )
    assert before.status_code == 200
    original_name = before.json()["display_name"]

    async def fail_log_event(*args, **kwargs):
        raise RuntimeError("audit insert failed")

    monkeypatch.setattr(auth_routes, "log_event", fail_log_event)

    with pytest.raises(RuntimeError, match="audit insert failed"):
        client.patch(
            "/api/v1/auth/me/settings",
            headers=headers,
            json={"display_name": "Should rollback"},
        )

    after = client.get(
        "/api/v1/auth/me/settings", headers={"Authorization": f"Bearer {owner['access_token']}"}
    )
    assert after.status_code == 200
    assert after.json()["display_name"] == original_name


def test_kill_switch_blocks_mutating_routes(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }

    activated = client.post(
        "/api/v1/control/kill-switch/activate",
        headers=headers,
        json={"reason": "maintenance"},
    )
    assert activated.status_code == 200
    assert activated.json()["kill_switch_active"] is True

    blocked = client.patch(
        "/api/v1/auth/me/settings",
        headers=headers,
        json={"display_name": "Blocked"},
    )
    assert blocked.status_code == 423
    assert blocked.json()["detail"] == "Kill switch active"

    deactivated = client.post(
        "/api/v1/control/kill-switch/deactivate",
        headers=headers,
        json={"reason": "done"},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["kill_switch_active"] is False


def test_login_rate_limit_blocks_repeated_attempts(strict_client: TestClient) -> None:
    payload = {"email": "rate-limit-test@example.com", "password": "novo-owner-1234"}

    first = strict_client.post("/api/v1/auth/login", json=payload)
    assert first.status_code == 401

    second = strict_client.post("/api/v1/auth/login", json=payload)
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded"

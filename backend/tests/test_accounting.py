"""Accounting and guardrail tests for the E2 fast path."""

from __future__ import annotations

from fastapi.testclient import TestClient


def bootstrap_owner(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "owner@novo.example",
            "display_name": "Nova Owner",
            "password": "novo-owner-1234",
        },
    )
    assert response.status_code == 200
    return response.json()


def auth_headers(tokens: dict[str, object]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }


def test_guardrails_emit_warning_and_model_accounting(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    created = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Guardrail chat", "classification": "private"},
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "my api_key is sk-abcdef1234567890", "role": "user"},
    )
    assert message.status_code == 201
    response_id = message.json()["response_id"]

    with client.stream(
        "GET",
        f"/api/v1/conversations/responses/{response_id}/events",
        headers=headers,
    ) as stream:
        body = "".join(stream.iter_text())

    assert "response.warning" in body
    assert "response.completed" in body

    usage = client.get("/api/v1/model-usage", headers=headers)
    assert usage.status_code == 200
    usage_items = usage.json()["items"]
    assert usage_items
    assert any(item["run_count"] >= 1 for item in usage_items)
    assert any(item["token_count"] >= 1 for item in usage_items)
    assert any("cost_minor" in item for item in usage_items)

    health = client.get("/api/v1/model-health", headers=headers)
    assert health.status_code == 200
    health_items = health.json()["items"]
    assert health_items
    assert any(
        item["health_status"] in {"healthy", "disabled", "degraded"} for item in health_items
    )

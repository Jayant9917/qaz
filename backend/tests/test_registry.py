"""Registry API tests for models and prompts."""

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
    body = response.json()
    assert "access_token" in body
    assert "csrf_token" in body
    return body


def auth_headers(tokens: dict[str, object]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }


def test_registry_endpoints_expose_seeded_models_and_prompts(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    models = client.get("/api/v1/models", headers=headers)
    assert models.status_code == 200
    model_items = models.json()["items"]
    assert len(model_items) >= 3
    assert any(item["model_key"] == "openrouter/free/fast" for item in model_items)

    policies = client.get("/api/v1/model-policies", headers=headers)
    assert policies.status_code == 200
    policy_items = policies.json()["items"]
    assert policy_items
    assert policy_items[0]["name"] == "conversation.fast-path.default"

    prompts = client.get("/api/v1/prompt-templates", headers=headers)
    assert prompts.status_code == 200
    prompt_items = prompts.json()["items"]
    assert any(item["prompt_key"] == "conversation.reply" for item in prompt_items)

    prompt_versions = client.get(
        f"/api/v1/prompt-templates/{prompt_items[0]['id']}/versions",
        headers=headers,
    )
    assert prompt_versions.status_code == 200
    assert prompt_versions.json()["items"]

    bindings = client.get("/api/v1/prompt-bindings", headers=headers)
    assert bindings.status_code == 200
    assert any(item["purpose"] == "conversation.reply" for item in bindings.json()["items"])


def test_route_simulation_uses_registry_selection(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    simulation = client.post(
        "/api/v1/models/route-simulation",
        headers=headers,
        json={"purpose": "conversation.reply", "classification": "private", "route_mode": "fast"},
    )
    assert simulation.status_code == 200
    body = simulation.json()
    assert body["path"] == "fast"
    assert body["prompt_version"].startswith("conversation.reply.v")
    assert body["model_provider"] in {"openrouter", "stub"}
    assert body["model_name"]

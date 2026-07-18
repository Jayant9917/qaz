"""Tests for memory safety and immutable revision snapshots."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "revision-owner@novo.example",
            "display_name": "Revision Owner",
            "password": "novo-owner-1234",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }


def test_memory_revisions_and_secret_guardrail(client: TestClient) -> None:
    headers = _headers(client)
    created = client.post(
        "/api/v1/memories/remember",
        headers=headers,
        json={"title": "Preference", "content": "I prefer concise answers."},
    )
    assert created.status_code == 201
    memory = created.json()

    revisions = client.get(f"/api/v1/memories/{memory['id']}/revisions", headers=headers)
    assert revisions.status_code == 200
    assert revisions.json()["items"][0]["canonical_content"] == "I prefer concise answers."

    corrected = client.post(
        f"/api/v1/memories/{memory['id']}/correct",
        headers=headers,
        json={"canonical_content": "I prefer very concise answers."},
    )
    assert corrected.status_code == 200

    revisions = client.get(f"/api/v1/memories/{memory['id']}/revisions", headers=headers)
    assert len(revisions.json()["items"]) == 2
    assert revisions.json()["items"][0]["canonical_content"] == "I prefer concise answers."

    secret = client.post(
        "/api/v1/memories/remember",
        headers=headers,
        json={"content": "My API key is abc123."},
    )
    assert secret.status_code == 422

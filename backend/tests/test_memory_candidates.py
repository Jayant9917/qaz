"""Tests for the approval-first memory suggestion flow."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _auth(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "candidate-owner@novo.example",
            "display_name": "Candidate Owner",
            "password": "novo-owner-1234",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }


def test_memory_suggestion_is_not_saved_and_rejects_secrets(client: TestClient) -> None:
    headers = _auth(client)

    candidate = client.post(
        "/api/v1/memories/suggest",
        headers=headers,
        json={"content": "I prefer concise technical explanations."},
    )
    assert candidate.status_code == 200
    assert candidate.json()["should_suggest"] is True
    assert candidate.json()["content"] == "I prefer concise technical explanations."

    no_candidate = client.post(
        "/api/v1/memories/suggest",
        headers=headers,
        json={"content": "What is the weather today?"},
    )
    assert no_candidate.json() == {"should_suggest": False, "auto_save": False}

    secret = client.post(
        "/api/v1/memories/suggest",
        headers=headers,
        json={"content": "My API key is abc123 and my password is secret."},
    )
    assert secret.json() == {"should_suggest": False, "auto_save": False}

    memories = client.get("/api/v1/memories", headers=headers)
    assert memories.status_code == 200
    assert memories.json()["items"] == []

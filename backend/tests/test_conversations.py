"""Conversation API tests for the E2 fast path foundation."""

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


def conversation_headers(tokens: dict[str, object]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-CSRF-Token": str(tokens["csrf_token"]),
    }


def test_conversation_lifecycle(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = conversation_headers(tokens)

    created = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "First chat", "classification": "private"},
    )
    assert created.status_code == 201
    conversation = created.json()
    assert conversation["title"] == "First chat"
    assert conversation["status"] == "active"

    duplicate = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "First chat", "classification": "private"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Conversation title already exists for this owner"

    listed = client.get("/api/v1/conversations", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == conversation["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Hello NOVO", "role": "user"},
    )
    assert message.status_code == 201
    assert message.json()["message"]["sequence_no"] == 1
    assert message.json()["response_id"]

    response_id = message.json()["response_id"]
    with client.stream(
        "GET",
        f"/api/v1/conversations/responses/{response_id}/events",
        headers=headers,
    ) as stream:
        body = "".join(stream.iter_text())

    assert "response.started" in body
    assert "response.completed" in body

    messages = client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=headers)
    assert messages.status_code == 200
    items = messages.json()["items"]
    contents = [item["content"] for item in items]
    assert "Hello NOVO" in contents
    assistant_messages = [item for item in items if item["role"] == "assistant"]
    assert assistant_messages
    assert assistant_messages[-1]["content"].strip()

    archived = client.post(f"/api/v1/conversations/{conversation['id']}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

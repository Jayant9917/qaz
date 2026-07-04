"""Redis working context API tests."""

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


def test_working_context_round_trip_and_chat_projection(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    initial = client.get("/api/v1/working-context", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["status"] == "empty"

    updated = client.put(
        "/api/v1/working-context",
        headers=headers,
        json={
            "summary": "Keep NOVO focused on the desktop shell.",
            "active_task": "Finish E3",
            "notes": ["Remember to keep this small."],
            "status": "thinking",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["summary"] == "Keep NOVO focused on the desktop shell."
    assert updated.json()["status"] == "thinking"
    assert updated.json()["notes"] == ["Remember to keep this small."]

    noted = client.post(
        "/api/v1/working-context/notes",
        headers=headers,
        json={"note": "Use Redis for temporary state only."},
    )
    assert noted.status_code == 200
    assert noted.json()["notes"][-1] == "Use Redis for temporary state only."

    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Working context chat", "classification": "private"},
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "Hello NOVO", "role": "user"},
    )
    assert message.status_code == 201
    response_id = message.json()["response_id"]
    user_message_id = message.json()["message"]["id"]

    with client.stream(
        "GET",
        f"/api/v1/conversations/responses/{response_id}/events",
        headers=headers,
    ) as stream:
        body = "".join(stream.iter_text())

    assert "response.completed" in body

    projected = client.get("/api/v1/working-context", headers=headers)
    assert projected.status_code == 200
    body = projected.json()
    assert body["conversation_id"] == conversation_id
    assert body["last_user_message_id"] == user_message_id
    assert body["last_response_id"] == response_id
    assert body["status"] == "idle"

    cleared = client.delete("/api/v1/working-context", headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["status"] == "empty"

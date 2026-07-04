"""Memory API tests for the first E3 explicit memory slice."""

from __future__ import annotations

from fastapi.testclient import TestClient


def bootstrap_owner(client: TestClient) -> dict[str, object]:
    response = client.post(
        '/api/v1/auth/bootstrap',
        json={
            'email': 'owner@novo.example',
            'display_name': 'Nova Owner',
            'password': 'novo-owner-1234',
        },
    )
    assert response.status_code == 200
    return response.json()


def auth_headers(tokens: dict[str, object]) -> dict[str, str]:
    return {
        'Authorization': f"Bearer {tokens['access_token']}",
        'X-CSRF-Token': str(tokens['csrf_token']),
    }


def test_memory_lifecycle_and_user_flow(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    created = client.post(
        '/api/v1/memories',
        headers=headers,
        json={
            'kind': 'long_term',
            'title': 'Meeting time',
            'canonical_content': 'My meeting is at 3 PM on Friday.',
            'classification': 'private',
            'confidence': 0.98,
            'importance': 0.8,
            'source_type': 'explicit_remember',
            'source_locator': {'channel': 'desktop'},
            'evidence_excerpt': 'Remember that my meeting is at 3 PM.',
        },
    )
    assert created.status_code == 201
    memory = created.json()
    assert memory['title'] == 'Meeting time'
    assert memory['status'] == 'active'

    listed = client.get('/api/v1/memories', headers=headers)
    assert listed.status_code == 200
    assert listed.json()['items']
    assert listed.json()['items'][0]['id'] == memory['id']

    detail = client.get(f"/api/v1/memories/{memory['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()['access_count'] >= 1

    events = client.get(f"/api/v1/memories/{memory['id']}/access-events", headers=headers)
    assert events.status_code == 200
    assert events.json()['items']
    assert any(item['purpose'] == 'memory.read' for item in events.json()['items'])

    corrected = client.post(
        f"/api/v1/memories/{memory['id']}/correct",
        headers=headers,
        json={
            'canonical_content': 'My meeting is at 4 PM on Friday.',
            'classification': 'private',
            'confidence': 0.99,
            'title': 'Meeting time',
            'source_type': 'owner_correction',
            'source_locator': {'channel': 'desktop', 'note': 'manual correction'},
        },
    )
    assert corrected.status_code == 200
    assert corrected.json()['canonical_content'] == 'My meeting is at 4 PM on Friday.'
    assert corrected.json()['version'] > memory['version']

    patched = client.patch(
        f"/api/v1/memories/{memory['id']}",
        headers=headers,
        json={'title': 'Updated meeting time', 'importance': 0.9},
    )
    assert patched.status_code == 200
    assert patched.json()['title'] == 'Updated meeting time'
    assert patched.json()['importance'] == 0.9

    archived = client.post(f"/api/v1/memories/{memory['id']}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()['status'] == 'archived'

    restored = client.post(f"/api/v1/memories/{memory['id']}/restore", headers=headers)
    assert restored.status_code == 200
    assert restored.json()['status'] == 'active'

    deleted = client.delete(f"/api/v1/memories/{memory['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()['status'] == 'deleted'

    after_delete = client.get(f"/api/v1/memories/{memory['id']}", headers=headers)
    assert after_delete.status_code == 404


def test_memory_list_can_filter_by_kind_and_status(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    client.post(
        '/api/v1/memories',
        headers=headers,
        json={
            'kind': 'long_term',
            'title': 'Preference',
            'canonical_content': 'I prefer concise answers.',
        },
    )
    client.post(
        '/api/v1/memories',
        headers=headers,
        json={
            'kind': 'episodic',
            'title': 'Event',
            'canonical_content': 'We launched NOVO E2.5.',
            'status': 'archived',
        },
    )

    filtered = client.get('/api/v1/memories?kind=episodic&status=archived', headers=headers)
    assert filtered.status_code == 200
    items = filtered.json()['items']
    assert len(items) == 1
    assert items[0]['kind'] == 'episodic'
    assert items[0]['status'] == 'archived'

def test_explicit_remember_command_creates_memory(client: TestClient) -> None:
    tokens = bootstrap_owner(client)
    headers = auth_headers(tokens)

    remembered = client.post(
        '/api/v1/memories/remember',
        headers=headers,
        json={
            'content': 'I prefer concise answers.',
            'source_locator': {'channel': 'desktop', 'command': 'remember'},
            'evidence_excerpt': 'Remember that I prefer concise answers.',
        },
    )
    assert remembered.status_code == 201
    memory = remembered.json()
    assert memory['title'] == 'I prefer concise answers'
    assert memory['canonical_content'] == 'I prefer concise answers.'
    assert memory['source_type'] == 'explicit_remember'
    assert memory['status'] == 'active'

    listed = client.get('/api/v1/memories', headers=headers)
    assert listed.status_code == 200
    assert listed.json()['items'][0]['id'] == memory['id']


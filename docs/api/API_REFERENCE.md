# NOVO API Reference

**Base path:** `/api/v1`

This reference covers the current backend HTTP API exposed by NOVO. It is written for developers who need to integrate with the backend, build the frontend, or understand the system contract before adding new features.

---

## 1. API conventions

### 1.1 Transport

- JSON over HTTP for standard requests and responses.
- Server-sent events (SSE) for live response streams.
- Pydantic models define the request and response contracts.

### 1.2 Authentication model

NOVO currently uses a browser-friendly session model for owner-facing flows:

- login returns an access token and CSRF token
- the backend stores the session in an HttpOnly cookie
- unsafe write actions require CSRF protection
- permission checks are enforced at the route layer

For non-browser clients, the access token is still returned in the auth response.

### 1.3 Common status codes

| Status | Meaning |
|---|---|
| 200 | Request succeeded |
| 201 | Resource created |
| 401 | Not authenticated or session invalid |
| 403 | Authenticated but not allowed |
| 404 | Resource not found |
| 409 | Conflict, usually uniqueness or duplicate state |
| 422 | Validation error |
| 503 | Service not ready |

### 1.4 Validation behavior

NOVO uses FastAPI + Pydantic validation. Invalid request bodies return structured validation errors with field-level details.

---

## 2. Endpoint map

### 2.1 Health

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/health/live` | Basic liveness check | No |
| GET | `/health/ready` | Readiness check for dependent services | No |

### 2.2 Authentication and owner settings

| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/auth/bootstrap` | Create or initialize the owner account and bootstrap the security seed | No |
| POST | `/auth/login` | Authenticate the owner and create a session | No |
| POST | `/auth/logout` | Revoke the current session | Yes |
| GET | `/auth/me` | Return the current authenticated identity | Yes |
| GET | `/auth/me/settings` | Read current owner settings | Yes |
| PATCH | `/auth/me/settings` | Update owner settings | Yes + CSRF |

### 2.3 Permissions

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/permissions` | List permission catalog entries | Yes |
| POST | `/permissions` | Create a permission catalog entry | Yes + CSRF |

### 2.4 Control center

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/control/state` | Read the current system control state | Yes |
| PATCH | `/control/state` | Update control state and security mode | Yes + CSRF |
| POST | `/control/kill-switch/activate` | Activate the kill switch | Yes + CSRF |
| POST | `/control/kill-switch/deactivate` | Deactivate the kill switch | Yes + CSRF |
| GET | `/control/events` | List recent control events | Yes |

### 2.5 Audit

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/audit/logs` | Read recent audit entries | Yes |

### 2.6 Model registry and routing

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/models` | List model catalog entries | Yes |
| GET | `/models/{model_id}` | Read a model catalog entry | Yes |
| PATCH | `/models/{model_id}` | Update a model catalog entry | Yes + CSRF |
| GET | `/model-policies` | List the owner's model policies | Yes |
| POST | `/model-policies` | Create a model policy | Yes + CSRF |
| PATCH | `/model-policies/{policy_id}` | Update a model policy | Yes + CSRF |
| POST | `/models/route-simulation` | Simulate model routing for a purpose/classification | Yes |
| GET | `/model-usage` | Read model usage metrics | Yes |
| GET | `/model-health` | Read model health summary | Yes |

### 2.7 Prompt registry

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/prompt-templates` | List prompt templates | Yes |
| POST | `/prompt-templates` | Create a prompt template | Yes + CSRF |
| GET | `/prompt-templates/{template_id}/versions` | List versions for a prompt template | Yes |
| POST | `/prompt-templates/{template_id}/versions` | Create a new prompt version | Yes + CSRF |
| POST | `/prompt-versions/{version_id}/evaluate` | Evaluate a prompt version | Yes |
| POST | `/prompt-versions/{version_id}/activate` | Activate a prompt version | Yes + CSRF |
| POST | `/prompt-versions/{version_id}/retire` | Retire a prompt version | Yes + CSRF |
| GET | `/prompt-bindings` | List prompt bindings | Yes |
| PUT | `/prompt-bindings/{binding_id}` | Update a prompt binding | Yes + CSRF |

### 2.8 Conversations and response stream

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/conversations` | List conversations for the current owner | Yes |
| POST | `/conversations` | Create a conversation | Yes + CSRF |
| GET | `/conversations/{conversation_id}` | Read one conversation | Yes |
| PATCH | `/conversations/{conversation_id}` | Update a conversation | Yes + CSRF |
| DELETE | `/conversations/{conversation_id}` | Delete a conversation | Yes + CSRF |
| GET | `/conversations/{conversation_id}/messages` | Read messages for a conversation | Yes |
| POST | `/conversations/{conversation_id}/messages` | Create a message and start a response run | Yes + CSRF |
| GET | `/conversations/responses/{response_id}/events` | Stream response events over SSE | Yes |
| POST | `/conversations/{conversation_id}/archive` | Archive a conversation | Yes + CSRF |

---

## 3. Endpoint details

### 3.1 Health

#### GET `/health/live`

Returns a lightweight liveness check.

Response shape:

```json
{
  "status": "alive",
  "service": "novo",
  "version": "0.1.0"
}
```

#### GET `/health/ready`

Checks whether required dependencies are available. Returns `503` when one or more required services are not ready.

Typical response fields:

- `status`: `ready` or `not_ready`
- `dependencies`: a keyed object describing service availability

---

### 3.2 Authentication and owner settings

#### POST `/auth/bootstrap`

Creates or initializes the owner account and ensures the security seed exists.

Request body:

```json
{
  "email": "owner@example.com",
  "display_name": "NOVO Owner",
  "password": "a-strong-password"
}
```

Notes:

- fields are optional because the backend can fall back to configured bootstrap defaults
- rate limiting is enforced
- this endpoint is intended for initial setup and recovery flows

#### POST `/auth/login`

Authenticates the owner and starts a session.

Request body:

```json
{
  "email": "owner@example.com",
  "password": "a-strong-password"
}
```

Response includes:

- access token
- CSRF token
- user profile
- roles
- permissions
- session metadata

#### POST `/auth/logout`

Revokes the current session and clears the auth cookies.

#### GET `/auth/me`

Returns the current authenticated user, session, roles, and permissions.

#### GET `/auth/me/settings`

Returns owner settings such as:

- display name
- timezone
- locale
- security mode
- account status

#### PATCH `/auth/me/settings`

Updates owner-facing settings.

Request body may include:

- `display_name`
- `timezone`
- `locale`
- `security_mode`

---

### 3.3 Permissions

#### GET `/permissions`

Returns the permission catalog for the owner.

#### POST `/permissions`

Creates a permission catalog entry.

Request body fields:

- `key`
- `resource`
- `action`
- `risk_level`
- `description`

This endpoint is used to define the control surface NOVO can reason about.

---

### 3.4 Control center

#### GET `/control/state`

Returns the current control state for the owner.

Includes fields such as:

- kill switch state
- automations enabled
- tools enabled
- external models enabled
- security mode
- version

#### PATCH `/control/state`

Updates the control state.

Request body may include:

- `reason` (required)
- `kill_switch_active`
- `automations_enabled`
- `tools_enabled`
- `external_models_enabled`
- `security_mode`

#### POST `/control/kill-switch/activate`

Activates the kill switch.

#### POST `/control/kill-switch/deactivate`

Deactivates the kill switch.

#### GET `/control/events`

Returns recent control events for auditing and debugging.

---

### 3.5 Audit

#### GET `/audit/logs`

Returns recent audit events.

Audit entries capture actions such as:

- auth events
- permission changes
- model policy changes
- prompt registry changes
- control changes

---

### 3.6 Model registry and routing

#### GET `/models`

Lists the model catalog entries available to NOVO.

#### GET `/models/{model_id}`

Returns one model catalog entry.

#### PATCH `/models/{model_id}`

Updates model metadata such as:

- display name
- capabilities
- context window
- max output tokens
- privacy eligibility
- pricing
- enabled flag

#### GET `/model-policies`

Lists model policies owned by the current user.

#### POST `/model-policies`

Creates a model policy.

Common request fields:

- `name`
- `rules`
- `max_classification`
- `max_cost_minor`
- `currency`
- `latency_target_ms`
- `fallback_allowed`
- `enabled`

#### PATCH `/model-policies/{policy_id}`

Updates an existing model policy.

#### POST `/models/route-simulation`

Simulates how the model router would choose a provider/model for a given purpose.

Useful for:

- debugging model selection
- validating route rules
- checking fallback behavior

#### GET `/model-usage`

Returns aggregated model usage metrics.

#### GET `/model-health`

Returns a health snapshot of models in the catalog.

---

### 3.7 Prompt registry

#### GET `/prompt-templates`

Lists prompt templates.

#### POST `/prompt-templates`

Creates a prompt template.

Request body fields:

- `prompt_key`
- `purpose`
- `name`
- `description`
- `variable_schema`
- `security_level`
- `owner_id` (optional)

#### GET `/prompt-templates/{template_id}/versions`

Lists versions for one prompt template.

#### POST `/prompt-templates/{template_id}/versions`

Creates a new version for a prompt template.

#### POST `/prompt-versions/{version_id}/evaluate`

Runs prompt version evaluation.

#### POST `/prompt-versions/{version_id}/activate`

Marks a prompt version as active.

#### POST `/prompt-versions/{version_id}/retire`

Marks a prompt version as retired.

#### GET `/prompt-bindings`

Lists prompt bindings for the current owner.

#### PUT `/prompt-bindings/{binding_id}`

Updates a prompt binding.

---

### 3.8 Conversations and response streaming

#### GET `/conversations`

Returns the current owner's conversations.

#### POST `/conversations`

Creates a new conversation.

Request body fields:

- `title`
- `classification` (defaults to `private`)

Conflict behavior:

- returns `409 Conflict` if the title already exists for that owner

#### GET `/conversations/{conversation_id}`

Returns one conversation.

#### PATCH `/conversations/{conversation_id}`

Updates conversation metadata.

#### DELETE `/conversations/{conversation_id}`

Deletes a conversation.

#### GET `/conversations/{conversation_id}/messages`

Returns the message history for a conversation.

#### POST `/conversations/{conversation_id}/messages`

Creates a user message and starts a response run.

Request body fields:

- `content`
- `role`
- `content_format`
- `classification`
- `parent_message_id` (optional)

Response includes:

- the stored message
- the response run identifier

#### GET `/conversations/responses/{response_id}/events`

Streams the response lifecycle over Server-Sent Events.

Event types currently include:

- `started`
- `route_selected`
- `context_ready`
- `warning`
- `token`
- `completed`
- `failed`

This endpoint is the live path that powers the chat UI while NOVO generates a reply.

#### POST `/conversations/{conversation_id}/archive`

Archives a conversation.

---

## 4. Integration notes

### 4.1 Browser clients

Browser clients should use the session cookie and CSRF token flow.

### 4.2 Write operations

Write actions are intentionally guarded by:

- authentication
- permission checks
- CSRF protection
- rate limiting on sensitive endpoints
- audit logging

### 4.3 Recommended integration order

1. Health endpoints
2. Authentication
3. Conversations
4. Control state
5. Permissions and audit
6. Model and prompt registry

---

## 5. Practical usage examples

### Create a conversation

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token>" \
  -b "novo_session=<session-cookie>" \
  -d '{"title":"New chat","classification":"private"}'
```

### Send a message

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/conversations/<conversation-id>/messages" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token>" \
  -b "novo_session=<session-cookie>" \
  -d '{"content":"Hello NOVO","role":"user","content_format":"text/plain","classification":"private"}'
```

### Read the response event stream

```bash
curl -N "http://127.0.0.1:8000/api/v1/conversations/responses/<response-id>/events" \
  -b "novo_session=<session-cookie>"
```

---

## 6. Notes for future expansion

This API reference intentionally documents the current contract only.

When NOVO grows, add new folders or sections for:

- memory APIs
- RAG/document APIs
- agent APIs
- tool execution APIs
- desktop assistant APIs

Keep the contract versioned and explicit so the frontend and backend can evolve without ambiguity.

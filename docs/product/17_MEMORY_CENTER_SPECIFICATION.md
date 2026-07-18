# NOVO Memory Center Specification

**Route:** `http://localhost:3000/memory`  
**Frontend implementation:** `frontend/src/app/memory/page.tsx`  
**Backend implementation:** `backend/src/novo/api/v1/memory.py`  
**Domain service:** `backend/src/novo/memory/service.py`  
**Database model:** `backend/src/novo/memory/models.py`  
**Migration:** `backend/migrations/versions/0012_e3_memory_core.py`

## 1. Purpose

The Memory Center is the owner-facing interface for deliberate, durable NOVO memories.

Its purpose is to let the owner decide what NOVO should remember instead of allowing the assistant to silently build an invisible profile. The current page provides the first usable E3 memory slice: an owner can explicitly save a memory, see active memories, archive a memory, and delete a memory.

Memory is not the same as chat history. Chat history stores conversations. A memory is a selected fact, preference, constraint, or piece of durable context that NOVO may use later.

Examples of appropriate memories:

- `I prefer concise technical explanations.`
- `The NOVO backend uses FastAPI.`
- `My main project is NOVO.`

The current page intentionally supports explicit memory only. Automatic extraction from conversations, reflection, consolidation, semantic retrieval, and companion memory are future capabilities.

## 2. Owner value

The Memory Center should answer four owner questions:

1. What does NOVO currently remember?
2. Why was this memory created?
3. Can I stop using it without deleting it?
4. Can I permanently remove it?

The current implementation answers the first, third, and fourth questions in the UI. The backend already stores provenance and access data, but the current UI does not yet expose all of those details.

## 3. Access and authentication

The page is a browser Control Center surface, not a public page.

The owner must:

1. Start the NOVO backend.
2. Start the frontend.
3. Open `/login`.
4. Sign in.
5. Open `/memory`.

If the browser has no valid session, the API returns `401 Unauthorized`. The page displays `Your session ended. Please sign in again.` The user should return to:

```text
http://localhost:3000/login
```

The frontend sends requests with:

- `credentials: "include"` so the HttpOnly session cookie is used.
- The `novo_csrf_token` cookie value as the `X-CSRF-Token` header for protected writes.
- The backend API base from `NEXT_PUBLIC_NOVO_API_URL`, or the current host on port `8000`.

The backend protects memory routes with owner identity and CSRF checks. A memory must belong to the authenticated owner before it can be read or changed.

## 4. Current interface

### 4.1 Page header

The page currently displays:

- A `Back to Control Center` link.
- The label `NOVO Control Center`.
- The page title `Memory Center`.

The current implementation is directly reachable at `/memory`. A visible Memory item has not yet been added to the main Control Center navigation.

### 4.2 Explicit memory form

The left side of the page contains the `Explicit memory` card.

Visible text:

- `Choose what NOVO remembers.`
- `Only save durable facts or preferences you intentionally approve.`

Inputs:

#### Title

- Optional short title.
- Sent as `title` when provided.
- If empty, the backend derives a title from the memory content.

#### Memory

- Required text area.
- The current placeholder is `I prefer concise technical explanations.`
- The frontend rejects an empty or whitespace-only value before making the request.

Button:

#### Remember this

- Sends `POST /api/v1/memories/remember`.
- Shows `Saving...` while the request is in progress.
- Clears the form after a successful save.
- Reloads the active-memory list after saving.
- Displays `Memory saved.` after success.

### 4.3 Active memories section

The right side contains the `Active memories` section.

The page loads only active, non-deleted memories using:

```text
GET /api/v1/memories?status=active
```

The header displays a count such as:

```text
1 active memory
```

or:

```text
3 active memories
```

If there are no active memories, the page displays:

```text
No active memories yet.
```

Each active memory card currently displays:

- Memory kind
- Classification
- Memory title
- Status
- Canonical memory content
- Source type
- Creation date
- Access count

### 4.4 Archive button

The `Archive` button sends:

```text
POST /api/v1/memories/{memory_id}/archive
```

Archiving changes the memory status to `archived`. The memory is no longer returned by the current active-memory query, but it remains stored for future review or restoration.

The current page does not provide an archive view or Restore button yet.

### 4.5 Delete button

The `Delete` button first asks for browser confirmation:

```text
Delete "{memory title}" permanently?
```

If confirmed, it sends:

```text
DELETE /api/v1/memories/{memory_id}
```

The current backend implements this as a soft-delete state transition: the memory status becomes `deleted` and `deleted_at` is set. Normal list and get queries exclude deleted rows.

The UI removes the deleted memory after reloading the active list.

## 5. Current frontend behavior

The page currently has these states:

- Loading memories
- Active memory count
- Empty active-memory list
- Session expired or unauthenticated
- Generic API failure
- Saving a new memory
- Archive/delete request in progress
- Successful save/archive/delete status

When a memory action is busy, the action buttons for that memory are disabled.

The page uses safe user-facing error conversion from `frontend/src/lib/user-facing-errors.ts`. It does not expose raw backend stack traces in the browser.

## 6. Backend API contract

The memory router is mounted at `/api/v1/memories`.

### 6.1 List memories

```text
GET /api/v1/memories
```

Optional query parameters:

- `status`
- `kind`
- `classification`

The current page uses `status=active`.

The service automatically filters by:

- Current owner ID
- `deleted_at IS NULL`

Results are ordered by newest update first, then newest creation time.

### 6.2 Explicit remember

```text
POST /api/v1/memories/remember
```

Request fields:

- `content` — required, 1 to 50,000 characters
- `title` — optional, up to 240 characters
- `kind` — defaults to `long_term`
- `classification` — defaults to `private`
- `confidence` — defaults to `1.0`, range 0 to 1
- `importance` — defaults to `0.5`, range 0 to 1
- `valid_from`
- `valid_until`
- `retention_until`
- `review_after`
- `source_locator`
- `evidence_excerpt`
- `embedding_version`

The route forces the following explicit-memory values:

- `source_type = explicit_remember`
- `extraction_method = explicit`
- `embedding_status = not_requested` unless changed by service behavior

### 6.3 General memory creation

```text
POST /api/v1/memories
```

This lower-level route accepts the full creation contract. It is available for future controlled services and integrations, but the current Memory Center uses the simpler `/remember` route.

### 6.4 Read one memory

```text
GET /api/v1/memories/{memory_id}
```

The route:

1. Confirms owner access.
2. Rejects missing, deleted, or cross-owner memories.
3. Records an allowed memory access event.
4. Increments `access_count`.
5. Updates `last_accessed_at` and `version`.

### 6.5 Update memory

```text
PATCH /api/v1/memories/{memory_id}
```

Supported update fields include:

- `title`
- `kind`
- `canonical_content`
- `classification`
- `status`
- `confidence`
- `importance`
- `valid_from`
- `valid_until`
- `retention_until`
- `review_after`
- `source_type`
- `source_id`
- `source_locator`
- `evidence_excerpt`
- `extraction_method`
- `embedding_status`
- `embedding_version`

At least one change is required.

The current UI does not yet expose this endpoint through an Edit button.

### 6.6 Correct memory

```text
POST /api/v1/memories/{memory_id}/correct
```

This is a correction-specific update contract. It requires new canonical content and defaults its provenance to:

- `source_type = owner_correction`
- `extraction_method = owner_correction`

The current UI does not yet expose a Correct button.

### 6.7 Archive memory

```text
POST /api/v1/memories/{memory_id}/archive
```

Changes the status to `archived` and increments the memory version.

### 6.8 Restore memory

```text
POST /api/v1/memories/{memory_id}/restore
```

Changes the status back to `active` and clears `deleted_at`.

The current UI does not yet expose a Restore button.

### 6.9 Delete memory

```text
DELETE /api/v1/memories/{memory_id}
```

This is currently a soft delete. It changes the status to `deleted`, sets `deleted_at`, increments the version, and excludes the memory from normal reads.

### 6.10 Access events

```text
GET /api/v1/memories/{memory_id}/access-events
```

Returns the append-only access records for one memory.

The current UI does not yet expose an access-history panel.

## 7. Database storage

The first memory migration creates the `memory.memories` and `memory.memory_access_events` tables.

### 7.1 `memory.memories`

| Field | Purpose |
|---|---|
| `id` | Unique memory identifier |
| `owner_id` | Owner who controls the memory |
| `kind` | Memory category, currently defaulting to `long_term` |
| `title` | Short human-readable label |
| `canonical_content` | Authoritative memory text |
| `classification` | Privacy/data classification, currently defaulting to `private` |
| `status` | Lifecycle state such as `active`, `archived`, or `deleted` |
| `confidence` | Confidence score from 0 to 1 |
| `importance` | Importance score from 0 to 1 |
| `access_count` | Number of recorded direct memory reads |
| `last_accessed_at` | Last recorded access time |
| `valid_from` | Beginning of validity window |
| `valid_until` | End of validity window |
| `retention_until` | Planned retention expiry |
| `review_after` | Planned review time |
| `source_type` | Provenance category, currently `explicit_remember` for the UI |
| `source_id` | Optional source record identifier |
| `source_locator` | Structured location information for provenance |
| `evidence_excerpt` | Evidence supporting the memory |
| `evidence_hash` | SHA-256 hash of evidence or canonical content |
| `extraction_method` | How the memory was created, currently `explicit` for the UI |
| `embedding_status` | Future semantic-indexing lifecycle state |
| `embedding_version` | Version of the future embedding model/index |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |
| `deleted_at` | Soft-delete timestamp |
| `version` | Current mutation/access version number |

Database constraints currently enforce:

- Confidence is between 0 and 1.
- Importance is between 0 and 1.
- `valid_until` cannot be before `valid_from`.
- Owner IDs are required.
- Memory titles and content are required.

Indexes support:

- Owner, status, and kind lookup.
- Owner and classification lookup.
- Review scheduling.
- Retention scheduling.

### 7.2 `memory.memory_access_events`

| Field | Purpose |
|---|---|
| `id` | Unique access-event identifier |
| `owner_id` | Owner whose memory was accessed |
| `memory_id` | Accessed memory |
| `actor_type` | Actor category, currently `owner` for direct reads |
| `actor_id` | Optional actor identifier |
| `agent_run_id` | Future agent-run relationship |
| `purpose` | Why the memory was accessed, currently `memory.read` |
| `decision` | Access decision, currently `allowed` for direct reads |
| `policy_version_id` | Policy version used for a future decision |
| `relevance_score` | Future retrieval relevance score |
| `used_in_prompt` | Whether memory entered a model prompt |
| `provider` | Future model/provider context |
| `trace_id` | Request tracing identifier |
| `created_at` | Access timestamp |

## 8. Current lifecycle

The current lifecycle is:

```text
User enters memory
        |
        v
POST /memories/remember
        |
        v
Create owner-scoped active memory
        |
        +--> Listed in Active memories
        |
        +--> Archive -> archived and hidden from active list
        |
        +--> Delete -> deleted + deleted_at and hidden from normal reads
```

Direct memory reads create access events and increment access counters.

The current implementation does not yet create separate immutable revision rows. It increments the memory `version` field in place.

## 9. Security and privacy behavior

Current protections:

- Authentication is required.
- Owner scoping is applied to list, get, update, archive, restore, delete, and access-event operations.
- CSRF protection is required for writes.
- Deleted memories are excluded from normal reads.
- The frontend sends credentials using browser cookies.
- The frontend shows safe error messages instead of backend traces.

Important current limitation:

The first memory slice does not yet implement a dedicated memory guardrail that scans content for passwords, API keys, session tokens, recovery codes, or other secrets before saving. The architecture requires that secrets never become memory, but the complete enforcement layer is still pending.

## 10. What is implemented today

Implemented in code:

- Durable owner-scoped memory table.
- Access-event table.
- Explicit remember endpoint.
- Full memory CRUD backend routes.
- Correction backend route.
- Archive backend route.
- Restore backend route.
- Soft-delete backend route.
- Access-event backend route.
- Active-memory list query.
- Memory Center page at `/memory`.
- Explicit memory form.
- Active-memory cards.
- Archive button.
- Delete button with confirmation.
- Frontend loading, empty, success, busy, and error states.
- Backend memory lifecycle tests.

## 11. What is not implemented in the current interface

The current page does not yet have:

- A visible main-navigation Memory link.
- Login redirect button after a 401 response.
- Edit button.
- Correct button.
- Restore button.
- Archived-memory view.
- Deleted-memory view.
- Memory detail page.
- Access-history panel.
- Provenance detail panel.
- Confidence and importance controls.
- Classification selector.
- Validity and retention date controls.
- Review scheduling controls.
- Memory export.
- Bulk actions.
- Search.
- Filtering by kind or classification in the UI.
- Secret detection feedback.
- Revision history display.
- Source and tag management.

## 12. Planned Memory Center expansion

The next complete Memory Center version should add:

### Owner controls

- Edit memory.
- Correct memory with correction provenance.
- Restore archived memories.
- View archived and deleted records.
- Permanently purge deleted records after policy checks.
- Export memories.
- Filter by status, kind, classification, and source.
- Search memory content.

### Evidence and explainability

- Revision timeline.
- Source list.
- Evidence excerpts.
- Access-event history.
- Explanation of why a memory was used.
- Whether a memory entered a prompt.
- Which model/provider received it.

### Safety

- Secret and credential detection.
- Restricted-content policy.
- Confirmation for classification changes.
- Review dates and retention expiry.
- Deletion reconciliation with future vector and graph projections.

### Memory architecture

- `memory_revisions`.
- `memory_sources`.
- Tags and memory-tag relationships.
- Memory relations.
- Candidate extraction.
- Consolidation and duplicate detection.
- Contradiction handling.
- Reflection proposals.
- Semantic memory embeddings.

## 13. Definition of done for the full section

The Memory Center should be considered complete when the owner can:

1. Create a memory intentionally.
2. See exactly what is stored.
3. See where it came from.
4. Correct it without losing history.
5. Classify it.
6. Archive and restore it.
7. Delete it and verify that it is no longer retrievable.
8. See when and why it was accessed.
9. Confirm that secrets cannot become memory.
10. Export or recover owner-approved memories.
11. Understand whether a memory influenced an answer.
12. Use the same controls from the web Control Center and future desktop assistant flows.

## 14. How to run and test the current section

Start PostgreSQL and Redis:

```powershell
cd D:\NOVO
docker compose -f infra\compose\docker-compose.core.yml up -d
```

Start the backend:

```powershell
cd D:\NOVO\backend
python -m uvicorn novo.main:app --reload --app-dir src
```

Start the frontend:

```powershell
cd D:\NOVO
pnpm --filter @novo/frontend dev
```

Open the login page first:

```text
http://localhost:3000/login
```

Then open Memory Center:

```text
http://localhost:3000/memory
```

Backend memory tests:

```powershell
cd D:\NOVO\backend
python -m pytest tests\test_memory.py
```

Frontend checks:

```powershell
cd D:\NOVO
pnpm --filter @novo/frontend lint
pnpm --filter @novo/frontend typecheck
pnpm --filter @novo/frontend test
```

## 15. Product position

The Memory Center is one of NOVO's main differentiators. It is designed to make AI memory visible, deliberate, reversible, and owner-controlled.

NOVO should not silently create an invisible personal profile. The owner should be able to see what is remembered, understand its provenance, correct it, archive it, and delete it.

The current implementation is the first functional slice of that larger promise. It provides explicit memory creation and basic lifecycle control. The next work is to expose the backend's existing correction, restore, and access-history capabilities through the interface and then add revisioned provenance and memory guardrails.

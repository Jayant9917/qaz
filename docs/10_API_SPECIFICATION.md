# NOVO API Specification

**Status:** Draft for owner review
**Owner:** Jay Rana
**Base path:** /api/v1
**Updated:** 2026-06-24

## 1. Purpose

This document defines NOVO's external HTTP, SSE, and WebSocket contracts. APIs expose application use cases; they do not expose databases, provider SDKs, or internal infrastructure.

## 2. Principles

- Versioned
- Authenticated by default
- Owner-scoped
- Schema validated
- Idempotent where applicable
- Pagination for collections
- Explicit async job resources
- Stable machine error codes
- Privacy-safe responses
- OpenAPI generated and reviewed
- No secret values
- No direct infrastructure access

## 3. Transport

- HTTPS JSON for commands and queries
- SSE for chat tokens, run events, and job progress
- WebSocket for bidirectional voice/computer-control sessions
- Presigned MinIO URLs only for authorized object-specific upload/download

## 4. Authentication

Browser uses Secure, HttpOnly, SameSite session cookie.

State-changing cookie requests require CSRF token.

Service clients use separately scoped service authentication.

Unauthenticated endpoints are limited to bootstrap/login and minimal liveness where configured.

## 5. Common headers

Request:

- X-Request-ID optional client ID
- Idempotency-Key required on retryable commands
- X-CSRF-Token for browser mutations
- If-Match or version field for optimistic updates
- traceparent when trusted service propagation applies

Response:

- X-Request-ID
- ETag/version where supported
- Retry-After
- RateLimit metadata where appropriate

## 6. Resource identifiers and time

- UUID strings
- UTC ISO 8601 timestamps
- IANA timezone in owner settings
- No sequential IDs
- Money uses integer minor units and currency
- Hashes use documented lowercase format

## 7. Response envelope

Single resources normally return:

- data
- meta with request_id and optional version

Collections return:

- data array
- page with next_cursor and has_more
- meta

Streaming endpoints use typed event envelopes rather than the JSON response envelope.

## 8. Error contract

Fields:

- error.code
- error.message
- error.details safe and optional
- error.field_errors optional
- error.request_id
- error.retryable
- error.retry_after_seconds optional

Never expose stack traces, SQL, credentials, raw provider response, or internal policy details.

Common codes:

- authentication_required
- session_expired
- csrf_failed
- forbidden
- policy_denied
- approval_required
- validation_failed
- conflict
- version_conflict
- idempotency_conflict
- rate_limited
- not_found
- resource_deleting
- dependency_unavailable
- guardrail_failed
- budget_exhausted
- request_cancelled
- internal_error

## 9. Pagination and filtering

Cursor pagination is default.

Filters are allowlisted and typed.

Sort fields are allowlisted.

Maximum page sizes prevent export-by-pagination abuse.

Search endpoints use dedicated query contracts rather than arbitrary SQL-like filters.

## 10. Idempotency

Required for:

- Message submission
- Upload confirmation
- Approval-bound actions
- Tool proposals/execution commands
- Automation execution
- Export
- Delete request
- Job retry

Same key and same request returns existing result. Same key and different request returns idempotency_conflict.

## 11. Async job contract

Command returns HTTP 202 with:

- job_id
- status
- status_url
- events_url
- created_at
- cancellable

Job resource includes type, progress, stage, attempt, timestamps, safe error, result reference, and cancellation state.

## 12. Auth endpoints

- POST /auth/bootstrap
- POST /auth/login
- POST /auth/logout
- POST /auth/reauthenticate
- POST /auth/recovery/start
- POST /auth/recovery/complete
- GET /sessions
- DELETE /sessions/{session_id}
- POST /sessions/revoke-all

Critical recovery endpoints have dedicated rate and audit controls.

## 13. Profile and settings

- GET /me
- PATCH /me
- GET /settings
- PATCH /settings
- GET /security-mode
- PUT /security-mode

Security-mode elevation may require reauthentication and approval.

## 14. Conversations

- GET /conversations
- POST /conversations
- GET /conversations/{id}
- PATCH /conversations/{id}
- DELETE /conversations/{id}
- GET /conversations/{id}/messages
- POST /conversations/{id}/messages
- POST /conversations/{id}/archive

Message request includes content, attachment IDs, response preferences, and idempotency key.

## 15. Chat streaming

POST message may return a response/run identifier.

SSE endpoint:

- GET /responses/{response_id}/events

Event types:

- response.started
- response.route_selected
- response.context_ready
- response.token
- response.citation
- response.warning
- response.completed
- response.failed
- approval.required
- job.created

Events have monotonically increasing event ID to support reconnection.

Sensitive internal reasoning is never streamed.

## 16. Orchestrator response metadata

When requested by Control Center or explanation UI:

- path: fast or deep
- route_reason
- retrieval_sources
- model tier/provider/model
- prompt version
- latency summary
- cost summary
- policy decision IDs
- grounding warnings
- run ID when applicable

## 17. Memory endpoints

- GET /memories
- POST /memories
- GET /memories/{id}
- PATCH /memories/{id}
- POST /memories/{id}/correct
- POST /memories/{id}/archive
- POST /memories/{id}/restore
- DELETE /memories/{id}
- GET /memories/{id}/revisions
- GET /memories/{id}/sources
- GET /memories/{id}/access-events
- GET /memory-candidates
- POST /memory-candidates/{id}/resolve
- POST /memory/reflection-runs
- GET /memory/reflection-insights
- POST /memory/reflection-insights/{id}/resolve

Memory output includes class, confidence, provenance, state, retention, projection state, and version.

## 18. Companion endpoints

- GET /companion/profile
- PATCH /companion/profile
- GET /goals
- POST /goals
- PATCH /goals/{id}
- GET /projects
- POST /projects
- PATCH /projects/{id}
- GET /life-events
- POST /life-events
- GET /emotional-observations
- PATCH /emotional-observations/{id}
- DELETE /emotional-observations/{id}
- POST /companion/reset

Companion reset shows exact data affected.

## 19. Document upload

1. POST /documents/upload-requests
2. Client uploads to returned presigned URL.
3. POST /documents/{id}/upload-confirmations
4. API returns ingestion job.

Request includes filename, size, checksum, MIME, classification, and optional tags.

## 20. Document endpoints

- GET /documents
- GET /documents/{id}
- PATCH /documents/{id}
- DELETE /documents/{id}
- GET /documents/{id}/versions
- GET /documents/{id}/ingestion-runs
- POST /documents/{id}/retry
- POST /documents/{id}/reindex
- GET /documents/{id}/download-url
- GET /documents/{id}/chunks for privileged diagnostics only

## 21. RAG search and citations

- POST /rag/retrieve
- POST /rag/answer
- GET /rag/runs/{id}
- GET /citations/{citation_id}

RAG request follows invocation contract: purpose, mode, class ceiling, budgets, source/document scope, and citation strictness.

Response follows selected-evidence/output contract and never returns unauthorized chunks.

## 22. Agent runs

- GET /agent-runs
- POST /agent-runs
- GET /agent-runs/{id}
- POST /agent-runs/{id}/cancel
- POST /agent-runs/{id}/pause
- POST /agent-runs/{id}/resume
- GET /agent-runs/{id}/steps
- GET /agent-runs/{id}/decisions
- GET /agent-runs/{id}/events

Resume requires state/policy compatibility.

## 23. Tools and integrations

- GET /tools
- GET /tools/{tool_key}
- GET /tools/{tool_key}/capabilities
- PATCH /tools/{tool_key}
- GET /integrations
- POST /integrations
- GET /integrations/{id}
- PATCH /integrations/{id}
- DELETE /integrations/{id}
- POST /integrations/{id}/verify
- POST /tool-actions/preview
- POST /tool-actions
- GET /tool-actions/{id}
- POST /tool-actions/{id}/reconcile

Credentials are submitted through a protected setup flow and never returned.

## 24. Permissions and policies

- GET /permissions
- POST /permissions
- PATCH /permissions/{id}
- DELETE /permissions/{id}
- POST /permissions/simulate
- GET /policies
- POST /policies
- GET /policies/{name}/versions
- POST /policies/{name}/versions
- POST /policy-versions/{id}/activate
- POST /policy-versions/{id}/retire
- GET /policy-decisions/{id}

Policy simulation never executes.

## 25. Approvals

- GET /approvals
- GET /approvals/{id}
- POST /approvals/{id}/approve
- POST /approvals/{id}/reject
- POST /approvals/{id}/cancel

Approval response includes expected action hash/version and may require reauthentication token.

API rejects material mismatch, expiry, consumed approval, stale policy, revoked session, or kill switch.

## 26. Models

- GET /models
- GET /models/{id}
- PATCH /models/{id}
- GET /model-policies
- POST /model-policies
- PATCH /model-policies/{id}
- POST /models/route-simulation
- GET /model-usage
- GET /model-health

Route simulation does not call the model unless explicitly requested and permitted.

## 27. Prompt Registry

- GET /prompt-templates
- POST /prompt-templates
- GET /prompt-templates/{id}/versions
- POST /prompt-templates/{id}/versions
- POST /prompt-versions/{id}/evaluate
- POST /prompt-versions/{id}/activate
- POST /prompt-versions/{id}/retire
- GET /prompt-bindings
- PUT /prompt-bindings/{id}

Prompt content access is privileged and audited. Secret literals are rejected.

## 28. Automations

- GET /automations
- POST /automations
- GET /automations/{id}
- PATCH /automations/{id}
- DELETE /automations/{id}
- POST /automations/{id}/enable
- POST /automations/{id}/disable
- POST /automations/{id}/run
- GET /automation-executions
- GET /automation-executions/{id}

Enable validates policy, expiry, trigger, scopes, and budgets.

## 29. Audit and egress

- GET /audit-events
- GET /audit-events/{id}
- POST /audit-exports
- GET /audit-exports/{id}
- GET /data-egress-events
- GET /explanations/{resource_type}/{resource_id}

Audit filtering is bounded. Exports are approval-bound, encrypted, and expiring.

## 30. Kill switch and controls

- GET /system-controls
- POST /system-controls/kill-switch/activate
- POST /system-controls/kill-switch/deactivate
- PATCH /system-controls

Activation may support scoped stop. Deactivation requires reauthentication and integrity checks.

## 31. Jobs

- GET /jobs
- GET /jobs/{id}
- POST /jobs/{id}/cancel
- POST /jobs/{id}/retry
- GET /jobs/{id}/events

Retry is available only when job type and failure classification permit it.

## 32. Health and operations

- GET /health/live
- GET /health/ready
- GET /health/dependencies authenticated
- GET /version
- GET /capabilities

Public health reveals minimal information.

## 33. WebSocket sessions

Voice/computer-control WebSocket handshake returns a short-lived session-scoped token.

Controls:

- Origin and session validation
- Frame size/rate limits
- Heartbeat
- Cancellation
- No credential frames
- Typed event schemas
- Reconnect rules
- Kill-switch termination

## 34. Rate and concurrency limits

Limits apply by user, session, IP indicator, endpoint, capability, provider, and cost.

Sensitive endpoints have stricter limits.

Rate limit errors include safe retry metadata.

## 35. Optimistic concurrency

PATCH/PUT uses version or ETag.

Conflict returns current version and conflict code without overwriting.

Approval consumption and one-time effects use transactional locks.

## 36. Authorization

Every endpoint maps to a named capability and resource scope.

Route visibility in frontend does not grant access.

Collection queries enforce owner RLS and allowlisted filters.

Object download URLs require authorization at issuance.

## 37. Validation and size limits

Define per-endpoint:

- Body size
- String length
- Array count
- Attachment count
- Upload size
- Page size
- Query complexity
- Time range
- Export limit

Unknown action fields are rejected.

## 38. OpenAPI and compatibility

OpenAPI is generated from Pydantic contracts and reviewed in CI.

Breaking changes require a new API version or migration period.

Additive response fields are allowed; clients ignore unknown non-action fields.

Action request schemas remain strict.

## 39. API testing

- Schema/contract tests
- Auth/CSRF/session tests
- RLS/owner isolation
- Permission mapping
- Idempotency
- Pagination
- Version conflict
- SSE reconnection
- WebSocket limits
- Approval races
- Upload confirmation
- Error redaction
- Rate limits
- OpenAPI compatibility
- Kill switch

## 40. Definition of done

- Every UI and client use case maps to a versioned endpoint.
- Every mutation has authorization, idempotency, concurrency, and audit behavior.
- Async work returns jobs and progress.
- Chat/run events reconnect safely.
- No endpoint exposes secrets or infrastructure.
- RAG, memory, agent, tool, approval, model, prompt, automation, audit, and control contracts align with their specifications.

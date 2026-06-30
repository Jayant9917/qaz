# NOVO Tool Framework

**Status:** Draft for owner review
**Owner:** Jay Rana
**Updated:** 2026-06-24

## 1. Purpose

The Tool Framework lets NOVO interact with external systems through narrow, typed, governed capabilities.

A tool is never an unrestricted application connection. It is a registered collection of explicit capabilities with schemas, risk, permissions, credentials, previews, idempotency, and audit behavior.

## 2. Principles

1. Disabled until registered.
2. Deny by default.
3. Capability-level permission.
4. Strict typed input and output.
5. Model output never executes directly.
6. Minimum credential scope.
7. Preview before sensitive effects.
8. Exact approval binding.
9. Idempotency and reconciliation.
10. Complete visibility and revocation.

## 3. Architecture

Flow:

Orchestrator decides capability may be needed.

Agent or Fast Path submits typed proposal.

Tool Gateway resolves registry entry.

Guardrails validate schema, scope, risk, permission, approval, mode, destination, and idempotency.

Secrets Provider supplies scoped credential.

Adapter executes.

Result Validator sanitizes output.

Action and audit records commit.

## 4. Tool registry

governance.tools stores stable tool identity.

Required manifest:

- tool_key
- name and description
- version
- publisher/source
- manifest hash
- adapter type
- supported capabilities
- network requirements
- secret references required
- health check
- installation/update state
- enabled state

Manifest changes are reviewed and audited.

## 5. Capability registry

Each capability defines:

- capability_key
- purpose
- input schema
- output schema
- default risk
- side-effect flag
- approval default
- preview support
- idempotency support
- retry class
- resource types
- data categories
- destination behavior
- timeout
- rate/concurrency limit
- compensation support

Examples:

- email.read
- email.send
- calendar.read
- calendar.create_event
- filesystem.read
- filesystem.write
- filesystem.delete
- browser.read_page
- browser.submit_form
- notes.search
- notes.create
- github.read_repository
- github.create_issue

## 6. Integration accounts

An integration represents an owner-configured external account.

It stores:

- Tool
- Friendly name
- Account identifier
- Granted scopes
- Vault credential reference
- Status
- Verification time
- Provider metadata
- Revocation state

It never stores secret values.

## 7. Input schema

Action schemas:

- Reject unknown fields.
- Use bounded strings/arrays.
- Validate formats and ranges.
- Normalize paths, addresses, domains, times, amounts, and recipients.
- Separate content from destination.
- Mark sensitive fields.
- Define required and optional fields.
- Include schema version.
- Avoid arbitrary provider payload passthrough.

## 8. Output schema

Tool results include:

- status
- provider_request_id
- normalized data
- result summary
- affected resource IDs
- side-effect confirmation
- retry safety
- next page/cursor when relevant
- warnings
- safe error
- reconciliation state

Raw provider output is treated as untrusted and is not passed directly to a model.

## 9. Proposal contract

A proposal contains tool/capability version, integration, arguments, target, expected effect, risk, reason, run/step IDs, deadline, and idempotency key.

The proposal is not permission.

## 10. Validation pipeline

1. Resolve tool/version.
2. Resolve capability/schema.
3. Validate and normalize arguments.
4. Resolve integration and resource.
5. Calculate effective risk.
6. Evaluate security mode.
7. Evaluate permission/policy.
8. Check classification and destination.
9. Check budgets and rate limits.
10. Generate preview and action hash.
11. Resolve approval.
12. Recheck control state and policy.
13. Obtain scoped credential.
14. Execute.
15. Validate result.
16. Persist outcome and audit.

## 11. Effective risk

Risk may be raised by:

- External side effect
- Destructive operation
- Public visibility
- Sensitive data
- New recipient/domain
- Bulk volume
- Financial amount
- Privilege level
- Irreversibility
- Automation
- Computer-control uncertainty

A model cannot lower risk.

## 12. Preview

Sensitive previews show:

- Account
- Recipients/destination
- Exact effect
- Relevant content
- Files/records affected
- Amount/currency
- Visibility
- Reversibility
- Data leaving NOVO
- Deadline

Preview generation is deterministic where possible.

## 13. Approval

Approval binds to action hash, account, capability, arguments, payload hash, target, classification, and expiry.

Material change creates a new proposal and approval.

Consumption is one-time and locked transactionally.

## 14. Idempotency

Every externally repeatable action has a stable key.

Framework records:

- Owner and capability
- Request hash
- Provider request ID
- State
- Response reference
- Expiry
- Reconciliation result

Same key/different request is rejected.

## 15. Retry policy

- Read-only: bounded retry with backoff.
- Idempotent write: stable-key retry.
- Provider idempotency: follow provider contract.
- Non-idempotent: no blind retry.
- Ambiguous outcome: reconcile first.
- Authorization denial: no retry workaround.
- Validation failure: repair proposal or ask owner.
- Rate limit: respect retry-after and deadline.

## 16. Reconciliation

Adapters define how to determine whether an ambiguous effect occurred.

Examples:

- Search sent folder by provider request ID.
- Query event by external ID.
- Compare file checksum/version.
- Check transaction status.
- Query created issue by idempotency marker.

Unresolved ambiguity remains visible and blocks automated repeat.

## 17. Credential handling

- Vault reference only in PostgreSQL.
- Adapter retrieves secret just in time.
- Credential scope matches capability.
- Secret stays out of model, memory, queue, URL, logs, traces, screenshot, and audit.
- Rotation/revocation supported.
- Integration verification does not reveal secret.
- Separate environment credentials.

## 18. Adapter interface

Adapters implement:

- validate_configuration
- health_check
- preview when supported
- execute
- reconcile
- cancel when supported
- normalize_result
- classify_error
- revoke/disconnect

Provider-specific details stay inside adapter.

## 19. Read versus write separation

Prefer separate capabilities and provider scopes for read and mutation.

Read results remain untrusted content and may contain prompt injection.

Write capabilities always receive explicit resource and destination scope.

## 20. Filesystem tool

Controls:

- Allowed roots
- Canonical path resolution
- Symlink/junction policy
- File type and size
- Read/write/delete separation
- No traversal
- No hidden credential paths
- Atomic writes where possible
- Backup/version behavior
- Delete approval
- Change summary

## 21. Browser tool

Separate:

- read_page
- navigate
- fill_form
- submit_form
- download
- upload
- authenticated_session

Reading page content does not grant authority.

Downloads use quarantine. Uploads require egress review. Submission is approval-bound by policy.

## 22. Email and messaging

Separate read, draft, send, reply, forward, attachment, and delete.

Send preview includes account, recipients, subject, body, attachments, classification, and visibility.

Recipient/domain changes invalidate approval.

## 23. Calendar

Separate read, create, update, cancel, invite, and respond.

Preview includes timezone, participants, recurrence, conferencing, and notifications.

## 24. Database and terminal

These are Critical developer capabilities.

Controls:

- Workspace/database allowlist
- Read versus mutation separation
- Command/query schema
- No arbitrary secret interpolation
- Transaction boundaries
- Destructive statement detection
- Result/output limits
- Approval for mutations
- Sandbox and resource limits
- Complete audit

## 25. GitHub and coding tools

Separate repository read, issue, pull request, branch, commit, and push.

Repository/worktree scope is explicit. No force push or destructive reset by default.

## 26. Computer Control Layer

Computer Use Agent proposes; Computer Control Layer executes.

It uses application/domain/path/network restrictions, expected-state validation, step approval, evidence, deadline, download quarantine, and kill switch.

## 27. MCP and plugins

MCP servers and plugins are untrusted integrations.

Before enablement:

- Inspect source/manifest.
- Record version/hash.
- Enumerate capabilities.
- Define schemas.
- Review scopes and network.
- Configure credentials.
- Assign permissions.
- Test disable/revoke.
- Review update behavior.

Plugin update cannot silently add capabilities.

## 28. Tool discovery

Models receive only capabilities eligible for the request, owner, mode, policy, and context.

Do not expose every registered tool to every prompt.

Descriptions are concise and cannot contain untrusted provider instructions.

## 29. Result handling

- Validate schema.
- Enforce size limits.
- Redact secrets.
- Label untrusted text.
- Store minimal durable summary.
- Store large artifacts in MinIO.
- Preserve provider/resource IDs.
- Require RAG/Memory Guardrails before downstream storage.
- Never treat a tool result as policy.

## 30. Sync versus async

Synchronous only for bounded low-latency operations.

Use jobs for long searches, large file work, exports, automation, computer sessions, bulk operations, or provider workflows.

Async actions preserve approval hash and expose progress/cancellation.

## 31. Circuit breakers and health

Track capability/provider:

- Availability
- Error rate
- Latency
- Rate-limit state
- Authentication health
- Last verification
- Circuit state

Unhealthy tools are excluded from Orchestrator selection.

## 32. Events

- tool.registered
- tool.enabled
- tool.disabled
- integration.connected
- integration.revoked
- tool.action_proposed
- tool.approval_requested
- tool.action_started
- tool.action_completed
- tool.action_failed
- tool.action_ambiguous
- tool.action_cancelled

## 33. Audit and explanations

Record why tool was selected, policy decision, approval, action hash, sanitized arguments, destination categories, provider request ID, result, failure, retry, and reconciliation.

Owner sees exact external effects.

## 34. Observability

- Calls by tool/capability
- Success/failure/ambiguity
- Latency
- Retries
- Rate limits
- Approval time
- Denials
- Idempotency hits
- Credential health
- Circuit state
- Cost
- Data egress categories

## 35. Required tests

- Registry/schema version
- Unknown-field rejection
- Permission precedence
- Risk escalation
- Preview/action hash
- Approval mutation invalidation
- Idempotency and races
- Ambiguous outcome
- Retry classification
- Secret leak
- Prompt-injected result
- Kill switch
- Integration revocation
- Plugin capability expansion
- Filesystem traversal
- Browser download/upload
- Computer unexpected state

## 36. Initial implementation order

1. Tool Registry and Gateway
2. Deterministic mock tool
3. Weather/read
4. Notes search/read
5. Calendar/read
6. Document search
7. Notes/create with approval
8. Calendar/create with approval
9. Email draft
10. Email send
11. GitHub read
12. Coding tools
13. Browser/computer control last

## 37. Open decisions

- Initial tools
- Vault provider
- MCP policy
- Plugin signature policy
- Default approval expiry
- Domain/path allowlist syntax
- Reconciliation requirements
- Tool-result retention
- Circuit-breaker thresholds
- Computer sandbox technology

## 38. Definition of done

- Every capability is narrow, typed, risked, permissioned, and auditable.
- No model output executes directly.
- Credentials remain isolated.
- Approval binds exact effects.
- Retry and ambiguity are safe.
- Results remain untrusted until validated.
- Revocation and kill switch work.
- Tests cover provider, policy, race, injection, and failure behavior.

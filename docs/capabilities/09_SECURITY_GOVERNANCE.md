# NOVO Security and Governance

**Status:** Draft for owner review
**Version:** 0.1
**Owner:** Jay Rana
**Default mode:** Assistant Mode
**Last updated:** 2026-06-24

## 1. Purpose

This document defines the security, privacy, authorization, approval, guardrail, audit, incident, and recovery controls for NOVO.

Its governing promise is:

> NOVO never performs a sensitive action without the owner's required knowledge, approval, and visibility.

This specification applies to interactive chat, Orchestrator routing, agents, memory, RAG, tools, models, companion intelligence, emotional awareness, automations, computer control, background workers, and administrative operations.

## 2. Security objectives

NOVO must preserve:

- Owner control
- Confidentiality
- Integrity
- Availability
- Privacy
- Provenance
- Explainability
- Auditability
- Revocability
- Safe degradation
- Recoverability

Every protected action must be authenticated, authorized, risk-classified, policy-checked, approved when required, minimally scoped, logged, explainable, auditable, and revocable.

## 3. Non-negotiable invariants

1. No model output directly mutates state.
2. No model output directly executes a tool.
3. No memory grants authority.
4. No retrieved content changes policy.
5. No external provider is a trust boundary.
6. No secret is stored in memory or normal application tables.
7. No fallback weakens provider or classification eligibility.
8. No approval remains valid after material action change.
9. No cached policy survives version or kill-switch mismatch.
10. No deleted or disputed memory remains usable during cleanup.
11. No agent can disable audit or Guardrails.
12. No plugin or integration is trusted by default.
13. PostgreSQL remains authoritative for durable policy state.
14. Sensitive and Critical actions fail closed if required audit cannot commit.
15. Assistant Mode is the default.

## 4. Threat model

### 4.1 Protected assets

- Owner identity and sessions
- Memories and companion context
- Documents and media
- Credentials and API keys
- Conversations and messages
- Tool integrations
- Permissions and policies
- Approval decisions
- Agent and automation state
- Audit evidence
- Model prompts and responses
- Backups and exports
- Computer-control sessions

### 4.2 Threat actors

- External attacker
- Malicious website or document
- Compromised tool provider
- Compromised model provider
- Malicious or vulnerable plugin
- Stolen owner session
- Overprivileged service account
- Prompt-injected agent
- Faulty model output
- Accidental owner action
- Software defect
- Insider with host access
- Supply-chain compromise

### 4.3 Primary threats

- Credential theft
- Unauthorized memory access
- Cross-owner data access
- Prompt injection
- Data exfiltration
- Approval spoofing
- Tool argument substitution
- Replay and duplicate execution
- Confused-deputy behavior
- Privilege escalation
- Audit tampering
- Destructive automation
- Malicious file parsing
- Dependency compromise
- Model hallucination causing action
- Emotional manipulation
- Hidden autonomous behavior
- Stale-policy execution

## 5. Trust zones

1. Client zone: browser, desktop, mobile, and voice devices.
2. Application zone: API, Orchestrator, agents, Guardrails, and application services.
3. Worker zone: ingestion, embedding, reflection, automation, and jobs.
4. Data zone: PostgreSQL, Redis, Milvus, Neo4j, RabbitMQ, MinIO, and Secrets Provider.
5. Automation sandbox: browser and computer-control execution.
6. External zone: OpenRouter, model providers, websites, email, calendar, and other APIs.
7. Operations zone: deployment, backup, monitoring, and recovery administration.

Crossing a zone requires authenticated identity, explicit protocol, minimum data, and applicable Guardrails.

## 6. Security architecture components

### 6.1 Identity and Session Service

Authenticates owner and service actors, manages sessions, revocation, reauthentication, and device visibility.

### 6.2 Policy Decision Point

Evaluates actor, capability, resource, classification, risk, security mode, destination, time, budget, and current control state.

### 6.3 Policy Enforcement Points

Enforce decisions at API, Orchestrator, retrieval, prompt construction, model gateway, tool gateway, memory service, export, deletion, automation, and computer control.

### 6.4 Guardrails Engine

Applies deterministic and model-assisted validation around input, output, action, memory, and egress. Model-assisted guardrails cannot independently grant permission.

### 6.5 Approval Engine

Creates exact action previews, binds decisions to action hashes, expires approvals, requires reauthentication where needed, and permits one-time consumption.

### 6.6 Privacy Firewall

Minimizes, redacts, blocks, and records external data transmission.

### 6.7 Secrets Provider

Stores and supplies scoped credentials without exposing them to models or agents.

### 6.8 Audit Service

Creates append-only, tamper-evident evidence and owner-readable explanations.

### 6.9 Kill Switch

Stops protected work, disables capabilities, revokes sessions or credentials by scope, and preserves recovery access.

## 7. Identity model

Actors:

- Owner user
- Authenticated human administrator
- API service
- Orchestrator
- Agent worker
- Ingestion worker
- Reflection worker
- Scheduler
- Automation identity
- Tool integration identity
- System recovery identity

Every actor has a stable ID, actor type, authentication method, allowed role, and audit attribution.

Models are not authenticated actors and never receive permissions.

## 8. Owner authentication

Version 1 should support strong local authentication using a password or passkey plus optional TOTP, subject to final owner decision.

Requirements:

- Modern password hashing when passwords are used
- Rate limiting and progressive delay
- Multi-factor or passkey support for production
- Secure recovery procedure
- No security questions
- Session/device visibility
- Recent reauthentication for Critical operations
- Audit of login, failure, recovery, and lockout
- Secure credential change and revocation

## 9. Session security

- Session tokens are random, high entropy, and stored only as hashes server-side.
- Browser session IDs use HttpOnly, Secure, SameSite cookies.
- Browsers keep the session cookie and submit CSRF from a companion non-HttpOnly cookie or equivalent protected source.
- State-changing cookie requests use CSRF protection.
- Sessions have absolute and inactivity expiry.
- Rotation occurs after authentication and privilege change.
- Logout and kill switch revoke immediately.
- Redis may cache revocation, but PostgreSQL is authoritative.
- Sensitive approval requires session freshness.
- IP and device metadata are indicators, not sole authentication.
- Stolen-session response supports device-specific and global revocation.

## 10. Service identity

Each runtime role has separate credentials and minimum privileges.

Required identities:

- novo_api
- novo_agent_worker
- novo_ingestion_worker
- novo_reflection_worker
- novo_scheduler
- novo_auditor
- novo_migrator
- novo_readonly

Service credentials are rotated, stored in the Secrets Provider, scoped to environment, and never shared across roles.

## 11. Authorization model

NOVO uses capability and resource authorization with policy context.

Decision inputs:

- Actor and role
- Owner
- Requested capability
- Integration/account
- Resource type and ID
- Resource pattern
- Data classification
- Risk level
- Security mode
- Destination
- Time and expiry
- Safety budget
- Session freshness
- Approval state
- Kill-switch state
- Policy version

Decision outputs:

- allow
- deny
- ask
- allow with constraints
- allow locally only
- allow with redaction
- allow summary only

Default is deny unless a safe product default explicitly applies.

## 12. Permission model

Permission states:

- Allow
- Deny
- Ask Every Time

Permissions may target:

- Subject
- Tool
- Capability
- Integration
- Account
- Resource
- Path or domain
- Data classification
- Destination
- Time window
- Action count
- Cost or spend

Examples:

- Email/read
- Email/send
- Browser/read_page
- Browser/submit_form
- Filesystem/read
- Filesystem/write
- Filesystem/delete
- Calendar/read
- Calendar/create_event
- Model/send_private_context
- Memory/read_confidential

## 13. Permission precedence

Evaluation order:

1. Global kill-switch or disabled subsystem
2. Explicit resource/capability Deny
3. Security-mode restriction
4. Classification/destination prohibition
5. Required approval
6. More specific permission
7. Higher priority permission
8. Explicit Allow
9. Safe default
10. Default Deny

Deny wins at equal or broader applicable priority. No Allow overrides a nondelegable Critical prohibition.

## 14. Security modes

### Observer

Read-only access to permitted data. No state mutation or external effects.

### Assistant

Suggest, draft, explain, preview, and ask. No external execution. Default mode.

### Operator

Execute permitted actions after policy and required approvals.

### Autonomous

Execute only inside explicit, bounded, expiring, revocable policies and safety budgets.

Raising mode requires explicit owner action and audit. Critical actions retain approval requirements where policy declares them nondelegable.

## 15. Risk classification

### Safe

Read-only, low-sensitivity, reversible, and no meaningful external effect.

Examples: weather, allowed document search, read notes.

### Sensitive

External communication, data change, account-context access, or meaningful privacy effect.

Examples: send message, send email, create event, write file, authenticated browsing.

### Critical

Destructive, financial, security, public, high-volume, irreversible, privileged, or high-impact.

Examples: delete files, database mutation, credential change, financial action, public posting, bulk export, security-mode change.

Risk is assigned by registered capability and may be raised by arguments, destination, volume, classification, or context. A model cannot lower risk.
## 16. Guardrails Enforcement Lifecycle

Every protected request may pass these stages:

1. Pre-retrieval authorization and classification filtering.
2. Pre-model prompt sanitation and provider eligibility.
3. Post-model output and schema validation.
4. Pre-tool permission, approval, idempotency, and mode check.
5. Pre-memory-write provenance, classification, contradiction, and inference checks.
6. Pre-egress Privacy Firewall and destination audit.
7. Final policy/control-state recheck immediately before mutation.
8. Post-effect result validation and audit.

Stages not relevant to a request are skipped explicitly, not forgotten.

## 17. Input Guardrails

Input controls:

- Transport size and content type
- Schema validation
- Secret/token/credential detection
- Prompt-injection detection
- Unsafe instruction isolation
- File and MIME validation
- Owner and resource scope
- Memory classification filtering
- Provider eligibility
- Context minimization
- Rate and concurrency limits

Untrusted content is labeled structurally and cannot become system instruction.

## 18. Output Guardrails

Model output is untrusted.

Controls:

- Strict schema validation
- Reject unknown fields for action proposals
- Type, enum, length, range, and format checks
- Tool capability allowlist
- Resource and destination normalization
- Unsupported-claim review for sensitive actions
- Citation/evidence checks where required
- Content-safety controls
- Bounded repair
- Eligible model fallback
- Refusal or clarification on persistent invalidity

Repair never changes the requested action beyond owner intent.

## 19. Action Guardrails

Before tool execution or state mutation:

1. Resolve registered tool and capability version.
2. Validate exact arguments.
3. Resolve integration/account.
4. Calculate effective risk.
5. Evaluate permission and security mode.
6. Check resource, destination, and classification.
7. Check safety budget.
8. Build deterministic preview.
9. Calculate action hash.
10. Resolve exact approval.
11. Check idempotency.
12. Recheck kill switch and policy version.
13. Retrieve scoped credential.
14. Execute with deadline.
15. Validate result.
16. Record outcome and audit.

An ambiguous provider outcome is reconciled before retry.

## 20. Memory Guardrails

Before candidate acceptance or revision:

- Reject secrets
- Require provenance
- Require atomic claim
- Distinguish statement from inference
- Validate confidence
- Classify sensitivity
- Detect duplicate and contradiction
- Review sensitive inference
- Check retention
- Check external embedding eligibility

Before retrieval:

- Filter owner, purpose, classification, status, validity, and destination
- Reload canonical PostgreSQL records
- Block disputed, deleting, deleted, expired, or unauthorized records
- Record materially used memory

Memory cannot grant permission or approval.

## 21. Egress Guardrails

Every external transmission evaluates:

- Destination and provider
- Purpose
- Owner policy
- Maximum classification
- Data categories
- Minimum necessary payload
- Secret and identifier redaction
- Provider retention/region constraints when known
- Policy decision
- Egress event

Unknown provider eligibility fails closed.

## 22. Fast-path policy enforcement

Security must be efficient enough for ordinary chat without becoming weaker.

Allowed optimizations:

- Compiled policy rules
- Active policy snapshot cache
- Cached model/provider eligibility
- Cached control state
- Compact capability decision tables
- Redis revocation and kill-switch projection

Requirements:

- Cache includes owner, environment, policy version, and control-state version.
- PostgreSQL remains authoritative.
- Policy changes and kill switch invalidate immediately.
- Sensitive/Critical actions perform final authoritative recheck.
- Cache miss reloads or fails closed.
- Stale security data never becomes permissive.
- Evaluation latency is measured.

Fast path skips irrelevant heavy history, not required enforcement.

## 23. Human Approval Engine

Approval is required when policy returns Ask or the capability is nondelegable.

Approval display includes:

- Proposed action
- Tool and capability
- Integration/account
- Recipient, destination, or resource
- Exact relevant arguments
- Data classification and egress categories
- Expected external effect
- Risk level
- Reason
- Reversibility
- Expiry
- Whether reauthentication is required

Responses: approve, reject, edit proposal, or cancel.

Editing creates a new action and invalidates the old approval.

## 24. Approval binding

An action hash covers all material fields:

- Tool and capability version
- Integration/account
- Resource and destination
- Recipients
- Payload or content hash
- File path
- Amount and currency
- Visibility
- Security mode
- Relevant classification
- Execution deadline

Approval is one-time and expiring. Consumption uses a row lock. A hash mismatch, expiry, policy version incompatibility, revoked session, or kill switch invalidates it.

## 25. Reauthentication

Recent strong authentication is required for configured Critical actions such as:

- Global session revocation
- Credential changes
- Security-mode escalation
- Disabling Guardrails
- Bulk export
- Destructive database operation
- Financial action
- Kill-switch deactivation
- Recovery and restore

The approval UI cannot satisfy reauthentication through model conversation alone.

## 26. Privacy classification

### Public

Low sensitivity but still owner-scoped where applicable.

### Private

Default personal information.

### Confidential

High sensitivity requiring explicit access and external-provider eligibility.

### Secret

Not sent externally by default. Narrow local use only.

### Restricted

Highest protection. Excluded from external models, reflection, embeddings, graph projection, automation, and broad retrieval by default.

Classification can be raised automatically but lowered only through authorized owner action or explicit policy.

## 27. Privacy Firewall

Responsibilities:

- Detect secrets and credentials
- Detect prohibited personal fields
- Minimize context
- Replace unnecessary direct identifiers
- Redact or tokenize allowed fields
- Enforce classification/provider policy
- Preserve only short-lived redaction mapping when necessary
- Create data-egress event
- Block unsafe transmission

The Privacy Firewall runs before OpenRouter, embedding providers, external tools, exports, notifications, and telemetry.

## 28. OpenRouter and model-provider security

OpenRouter is the initial gateway for free and low-cost models, not a trust boundary.

Requirements:

- Backend-only gateway access
- Key from Secrets Provider
- TLS and strict endpoint configuration
- Provider/model eligibility from Model Registry
- Classification limit
- Minimum context
- Prompt and response hashes rather than raw sensitive logging
- Deadline and bounded retry
- Egress event
- Output Guardrails
- No weaker fallback

Free-model compensation:

- Strict structured schemas
- Smaller prompts
- Bounded context
- Deterministic preprocessing
- Bounded repair
- Health-aware fallback
- Independent action validation
- Safe degradation

Free model output cannot be trusted more because it is fast or cheap.

## 29. Prompt-injection defense

Potential injection sources:

- Websites
- Email
- Documents
- Tool output
- Memory
- Model output
- Image/OCR text
- Code comments
- Plugin metadata

Defenses:

- Structural separation of policy, owner instruction, context, and untrusted data
- No authority from quoted content
- Tool allowlists
- Least-privilege retrieval
- Secret isolation
- Sanitized prompt templates
- Suspicious instruction detection
- Output/action validation
- Human preview
- Sandboxed parsing and browsing
- Audit and evidence

Instructions to ignore policy, reveal secrets, approve actions, alter memory, or call tools are treated as untrusted content.

## 30. Prompt Registry security

- Immutable prompt versions
- Hash verification
- Typed variable schema
- Purpose-specific bindings
- Draft, evaluated, approved, active, and retired states
- Authorized activation and rollback
- Security evaluation before production
- No runtime agent modification
- No secret literals
- Audit of activation and use
- Prompt version recorded on model calls

External prompt content cannot overwrite protected system prompts.

## 31. Tool security

Every tool exposes narrow capabilities with strict input/output schemas.

Requirements:

- Disabled by default until registered
- Manifest/version hash
- Risk classification
- Minimum OAuth/provider scopes
- Separate read/write where possible
- Integration-specific permissions
- Preview support for side effects
- Idempotency support metadata
- Deadline and cancellation
- Sanitized result
- Provider request ID
- Complete action audit

Tools never receive unrelated memory or credentials.

## 32. Secrets management

Secret values include API keys, passwords, OAuth refresh tokens, cookies, private keys, database credentials, encryption keys, and recovery codes.

Rules:

- Dedicated Secrets Provider
- Application rows store references only
- No prompt, memory, queue, URL, log, trace, audit, screenshot, or exception exposure
- Scoped retrieval by service identity
- Short-lived process memory
- Rotation and revocation
- Access audit without secret value
- Environment separation
- Backup and recovery procedure
- Leak detection and immediate revocation workflow

## 33. Audit architecture

Authoritative evidence uses audit.events.

Required properties:

- Append-only runtime access
- Monotonic sequence
- Actor and session attribution
- Event and resource type
- Action and outcome
- Risk and reason
- Policy and approval links
- Trace and correlation IDs
- Redacted metadata
- Previous hash and event hash
- Retention policy

Operational logs and Langfuse are not substitutes for audit evidence.

## 34. Audit integrity

- Runtime roles cannot update or delete audit rows.
- Hash chaining detects alteration.
- Periodic verification records signed or protected checkpoints.
- Clock drift is monitored.
- Export is approval-bound and encrypted.
- Audit failure alerts immediately.
- Sensitive/Critical effects fail closed if required audit cannot commit.
- Audit records never duplicate deleted secret content.

## 35. Explainability

NOVO must explain:

- Why Fast or Deep Path was selected
- Why a model and provider were selected
- Why context or memory was used
- Why a tool was proposed
- Why policy allowed, denied, constrained, or asked
- What approval authorized
- What effect occurred
- What data left NOVO
- Why fallback or refusal occurred

Explanations expose useful reasons without revealing secrets or exploitable policy internals.

## 36. Kill switch

Scopes:

- All agents
- Automations
- Tools
- External models
- Computer control
- Individual integration
- Individual session
- All sessions
- Credential group

Activation:

1. Strongly authenticate owner.
2. Commit control state and audit.
3. Update immediate Redis projection.
4. Reject new protected work.
5. Signal active workers.
6. Cancel providers where possible.
7. Quarantine or pause queued work.
8. Revoke selected sessions/credentials.

Recovery UI remains locally available. Sensitive work never automatically resumes.

## 37. Kill-switch deactivation

Deactivation requires recent strong authentication, reason, audit, system-integrity checks, and explicit scope selection.

Before restoring execution:

- Verify authoritative policy
- Verify audit availability
- Check pending approvals
- Quarantine stale queued actions
- Validate credentials and integrations
- Review active automations
- Confirm no incident containment remains

Previously approved sensitive actions do not automatically resume.
## 38. Database security

- Private network access only
- TLS connections
- Separate runtime roles
- No runtime table ownership
- Row-level security on owner-scoped tables
- Constraints for critical invariants
- Parameterized SQL
- Migration-only DDL role
- Encrypted storage and backups
- Query timeout and connection limits
- Database activity monitoring
- Tested point-in-time recovery
- No secret values in rows

Cross-owner tests are release blockers.

## 39. Redis security

- Private network and authenticated TLS
- No public endpoint
- Environment and owner namespacing
- TTL for transient data
- Minimal sensitive content
- No durable authority
- Safe serialization
- Memory and command limits
- Kill-switch and revocation versioning
- Full-loss recovery from PostgreSQL
- Avoid dangerous administrative commands in runtime roles

## 40. Milvus and Neo4j security

- Private authenticated connections
- Owner and classification metadata
- Policy prefilter and PostgreSQL post-authorization
- No authority for content or permission
- Versioned projections
- Immediate canonical block on deletion/dispute
- Reconciliation for stale/orphaned records
- Rebuild capability
- Restricted/Secret projection disabled by default
- No direct client or model access

## 41. RabbitMQ security

- TLS and per-service credentials
- Least-privilege vhosts, exchanges, and queues
- No plaintext secrets
- Minimal payload or object reference
- Message size limits
- Schema version validation
- At-least-once idempotent consumers
- Dead-letter handling
- Publisher confirms
- Transactional outbox
- Retry limits and poison-message quarantine
- Control-state check before protected work

## 42. MinIO and file security

- Private buckets
- Opaque object keys
- Server-side encryption
- Versioning where appropriate
- Short-lived method/object-specific presigned URLs
- Quarantine upload
- Size, extension, declared MIME, and detected MIME checks
- Checksum verification
- Malware scanning
- Sandboxed parsing
- Archive and decompression limits
- No macro/script execution
- Metadata authorization in PostgreSQL
- Governed deletion and orphan reconciliation

## 43. RAG security

Document content is untrusted.

Controls:

- Authorized document and chunk selection
- Classification filtering
- Parser isolation
- Injection labeling
- No document instruction authority
- Chunk provenance
- Retrieval reauthorization
- Context minimization
- Citation/evidence validation
- No automatic tool invocation from retrieved content
- Deletion propagation
- Index rebuild and reconciliation

## 44. Agent security

- Orchestrator decides whether an agent is needed.
- Agents use narrow declared capabilities.
- Each step has deadline and budget.
- Model plans are untrusted.
- Tool proposals are typed.
- Guardrails run at every protected boundary.
- Workers heartbeat and support cancellation.
- Loops have step and cost limits.
- Agents cannot change policy, audit, credentials, or mode.
- Agent memory access is purpose-scoped.
- Deep runs persist decisions and outcomes.
- Fast chat avoids unnecessary agent authority.

## 45. Automation security

Every automation has:

- Owner
- Trigger
- Workflow definition
- Allowed capabilities
- Security mode
- Policy version
- Data scope
- Destination scope
- Time window
- Action/count/cost budgets
- Expiry
- Notification policy
- Revocation state

Automations stop on expired policy, changed material arguments, kill switch, budget exhaustion, ambiguous provider outcomes, or required approval.

## 46. Computer-control security

The Computer Control Layer runs in an isolated sandbox.

Requirements:

- Application, account, path, domain, network, clipboard, and time restrictions
- Observation before action
- Expected-state validation
- Step-level policy check
- Exact approval for sensitive effects
- Screenshot or structured evidence under privacy policy
- Download quarantine
- Upload egress review
- Privilege-prompt stop
- Unexpected UI stop
- Session deadline
- Kill-switch termination
- No on-screen instruction authority
- No access to unrelated host secrets

Playwright is preferred for deterministic browser work. Visual reasoning cannot authorize execution.

## 47. Companion and emotional safety

Companion behavior must be transparent, configurable, and resettable.

NOVO must not:

- Claim consciousness or human emotion
- Encourage dependency or isolation
- Use affection or urgency to obtain approval
- Diagnose health
- Pressure, shame, or guilt the owner
- Hide adaptation
- Treat inferred emotion as identity
- Use emotional state to weaken security
- Optimize engagement at the expense of owner wellbeing

Emotional observations are uncertain, sourced, short-lived, editable, and non-authorizing.

## 48. Notification security

- Notifications reveal minimum information.
- Sensitive details require authenticated app view.
- Channels are owner-approved.
- Recipients and destination are validated.
- Approval tokens are never placed in notification URLs.
- Notification links are short-lived and bound to session/action.
- Delivery failure does not imply action failure or success.
- Rate limits prevent spam and coercive repetition.

## 49. Plugin and integration security

Plugins and integrations are untrusted until:

- Manifest and publisher/source are inspected
- Version/hash is recorded
- Capabilities are declared
- Permissions are owner-approved
- Dependencies are scanned
- Network and filesystem scopes are bounded
- Secrets access is declared
- Update behavior is controlled
- Revocation and removal are tested

No plugin receives broad default access. Updates cannot silently expand capabilities.

## 50. Supply-chain security

- Lock dependency versions
- Verify package sources and checksums where supported
- Generate software bill of materials
- Scan dependencies and images
- Sign or verify release artifacts
- Protect CI credentials
- Separate build and production secrets
- Review transitive dependencies
- Patch critical vulnerabilities
- Pin container images by digest in production
- Restrict installation scripts
- Audit prompt, tool manifest, and policy changes as code

## 51. Network security

- Expose only reverse proxy/API
- Private infrastructure networks
- TLS across boundaries
- Strict CORS
- Host validation
- Request limits
- Egress allowlists where practical
- Separate automation network
- No public database/cache/vector/queue/object/vault/admin ports
- Authenticated health detail
- Firewall and service identity
- Rate and connection limits

## 52. Encryption and key management

- Encryption in transit
- Encrypted disks and backups
- Vault-managed credentials and keys
- Key versioning
- Rotation
- Revocation
- Separate environment keys
- Minimal key access
- Documented recovery
- Application envelope encryption for selected high-sensitivity columns after threat review
- No encryption key stored beside ciphertext as ordinary data

Hashes provide integrity, not confidentiality.

## 53. Data retention and deletion

Retention is explicit by data type and classification.

Deletion workflow:

1. Authenticate and authorize.
2. Obtain approval when required.
3. Mark canonical record Deleting.
4. Block access immediately.
5. Invalidate Redis/cache.
6. Remove Milvus/Neo4j projections.
7. Remove MinIO objects.
8. Purge permitted PostgreSQL content.
9. Expire exports and telemetry projections.
10. Record safe completion evidence.
11. Disclose backup expiry separately.

Audit does not preserve deleted content unnecessarily.

## 54. Backup and restore security

- Encrypted backups
- Off-host copy
- Restricted backup identity
- Integrity verification
- Tested restore
- Recovery-point and recovery-time objectives
- Key recovery procedure
- Restore into isolated environment first
- Malware and integrity checks
- Policy/control state restored before agents/tools
- Pending approvals invalidated after uncertain restore boundary
- Outbox replay reviewed for duplicate external effects
- Audit verification before re-enabling execution

## 55. Incident classification

Example incident levels:

- SEV-1: active credential theft, destructive action, major data exposure, audit compromise
- SEV-2: contained unauthorized access, policy bypass, repeated unsafe execution
- SEV-3: failed control, suspicious activity, limited exposure
- SEV-4: low-risk defect or near miss

Severity considers data class, external effect, owner control, reversibility, scope, and ongoing risk.

## 56. Incident response

1. Detect and preserve safe evidence.
2. Activate appropriate kill-switch scope.
3. Revoke sessions and credentials.
4. Stop agents, automation, and computer control.
5. Isolate affected integrations/services.
6. Determine authoritative state.
7. Notify owner clearly.
8. Contain and eradicate.
9. Restore from verified state.
10. Reconcile external effects.
11. Rotate secrets.
12. Review audit and data egress.
13. Document root cause.
14. Add regression tests and policy changes.
15. Obtain explicit approval before broad reactivation.

Models do not lead incident response autonomously.

## 57. Security observability

Metrics and alerts:

- Authentication failures and lockouts
- Session creation and revocation
- Permission denials
- Approval acceptance/rejection/expiry
- Critical actions
- Kill-switch events
- Policy-cache version mismatch
- Privacy Firewall blocks
- Secret detections
- Invalid model output and repairs
- Free-model reliability degradation
- Egress by destination/classification
- Tool ambiguous outcomes
- Audit write/verification failures
- Projection deletion lag
- Plugin/integration changes
- Computer-control unexpected state
- Backup and restore failures

Metrics contain no raw secrets or sensitive prompt text.

## 58. Security testing

Required test classes:

- Unit tests for policy and Guardrails
- Property tests for precedence and action hashing
- Integration tests for approval/tool execution
- RLS and cross-owner tests
- Prompt-injection suites
- Secret-leak tests
- Free-model malformed-output tests
- Replay/idempotency tests
- Concurrency/TOCTOU tests
- File/parser fuzzing
- SSRF and egress tests
- Computer-sandbox escape tests
- Kill-switch propagation tests
- Audit tamper tests
- Backup/restore exercises
- Dependency and container scans
- Threat-model review
- Manual penetration testing before internet exposure

## 59. Mandatory abuse cases

NOVO must safely handle:

- Email asks agent to reveal credentials.
- Website says ignore system policy.
- Document embeds a tool command.
- Model fabricates approval.
- Model changes recipient after approval.
- Same payment/action request is retried.
- User deletes memory while embedding worker runs.
- Stale policy cache says Allow after Deny.
- Free model returns malformed or extra tool fields.
- Plugin update requests new scopes.
- Computer agent sees an unexpected confirmation dialog.
- Reflection infers a sensitive trait.
- Emotional inference tries to affect approval language.
- RabbitMQ redelivers a completed action.
- Restore replays an old outbox event.

## 60. Security release gates

A release cannot enable a protected capability unless:

- Threat model is updated
- Capability and risk are registered
- Permission defaults exist
- Guardrail stages are implemented
- Approval preview is tested
- Audit evidence is defined
- Idempotency/reconciliation exists
- Kill-switch behavior exists
- Deletion/retention behavior exists
- Dashboard visibility exists
- Abuse tests pass
- Recovery is documented

## 61. Rollout phases

### S1: Identity and baseline

Authentication, sessions, RLS, secrets, TLS, audit foundation, Assistant Mode.

### S2: Policy and Guardrails

Permissions, policies, control state, fast policy cache, input/output/memory/egress Guardrails.

### S3: Governed tools

Tool registry, risk, previews, approval binding, idempotency, scoped credentials.

### S4: Models and privacy

OpenRouter gateway, registry eligibility, free-model validation, Privacy Firewall, egress register.

### S5: Memory and RAG security

Classification, provenance, retrieval reauthorization, injection defense, deletion propagation.

### S6: Automation and companion

Bounded policies, safety budgets, emotional safeguards, reflection review.

### S7: Computer control

Sandbox, evidence, step policy, unexpected-state stops, kill-switch tests.

No phase advances without its tests and Control Center visibility.

## 62. Open decisions

1. Authentication method and passkey timeline.
2. MFA requirement for personal production.
3. Secrets Provider selection.
4. Policy language and compilation engine.
5. Policy cache TTL and invalidation.
6. Nondelegable Critical capability list.
7. Reauthentication freshness.
8. Approval expiry by risk.
9. External provider classification matrix.
10. Data residency requirements.
11. Audit checkpoint signing mechanism.
12. Security log and audit retention.
13. Envelope-encrypted columns.
14. Malware scanner and parser sandbox.
15. Incident notification channels.
16. Internet exposure versus private VPN.
17. Plugin signature policy.
18. Maximum autonomous safety budgets.
19. Emotional-observation retention.
20. Computer-control evidence retention.

Conservative defaults apply until decisions are made.

## 63. Definition of done

Security Governance is accepted when:

- Every trust boundary has enforcement.
- Identity and service roles are explicit.
- Permission precedence is deterministic.
- Fast-path policy evaluation is both safe and measurable.
- All Guardrail stages have contracts.
- Model output cannot directly cause effects.
- Approval binds exact action and is one-time.
- OpenRouter/free-model use cannot weaken policy.
- Memory, RAG, tools, automations, companion, and computer control have specific safeguards.
- Secrets remain isolated.
- Audit is append-only and verifiable.
- Kill switch and recovery are tested.
- Deletion blocks immediately across all stores.
- Incident response and restore are executable.
- Abuse cases and release gates are automated where possible.

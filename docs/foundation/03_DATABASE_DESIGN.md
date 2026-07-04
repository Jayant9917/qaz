# NOVO Database Design

**Status:** Draft for owner review
**Version:** 0.1
**Owner:** Jay Rana
**Database:** PostgreSQL
**Last updated:** 2026-06-23

## 1. Purpose

This document defines NOVO's complete durable relational model before application code is written. It translates the Project Vision and System Architecture into tables, relationships, constraints, indexes, lifecycle rules, security boundaries, and migration requirements.

PostgreSQL is NOVO's system of record. Redis contains reconstructable ephemeral state. Milvus contains rebuildable vectors. MinIO stores binary objects. RabbitMQ delivers asynchronous work. The secrets vault stores secret values.

## 2. Non-negotiable data principles

1. Every owner-scoped record contains owner_id.
2. Durable facts have one authoritative PostgreSQL location.
3. Credentials and secret values never enter application tables.
4. Large binaries never enter PostgreSQL.
5. Embedding vectors live in Milvus, not PostgreSQL.
6. Queue delivery state never replaces durable job state.
7. Every memory preserves provenance and revision history.
8. Every protected action preserves policy, approval, execution, and audit relationships.
9. Logical deletion blocks access immediately.
10. Physical deletion is a tracked multi-store workflow.
11. Sensitive history is immutable or revisioned, never silently overwritten.
12. All timestamps are UTC TIMESTAMPTZ.
13. All public identifiers are opaque UUIDs.
14. Cross-system changes use a transactional outbox.
15. Runtime database roles use least privilege and row-level security.

## 3. PostgreSQL schemas

| Schema | Responsibility |
|---|---|
| identity | Owner accounts, authentication, sessions, settings |
| chat | Conversations, messages, attachments |
| memory | Memories, revisions, provenance, tags, access |
| knowledge | Objects, documents, versions, chunks, ingestion |
| agent | Runs, steps, decisions, tool actions |
| governance | Tools, permissions, policies, approvals, kill switch |
| automation | Automations, schedules, executions |
| platform | Models, jobs, outbox, idempotency |
| audit | Append-only security and governance evidence |

## 4. Shared conventions

### 4.1 Standard columns

Mutable owner resources normally include:

| Column | Type | Purpose |
|---|---|---|
| id | UUID | Primary key |
| owner_id | UUID | Ownership and isolation |
| created_at | TIMESTAMPTZ | Creation time |
| updated_at | TIMESTAMPTZ | Last mutation time |
| version | INTEGER | Optimistic concurrency |
| deleted_at | TIMESTAMPTZ | Logical deletion when supported |

### 4.2 Stable state vocabularies

- data_classification: public, private, confidential, secret, restricted
- risk_level: safe, sensitive, critical
- permission_effect: allow, deny, ask
- security_mode: observer, assistant, operator, autonomous
- actor_type: user, agent, automation, service, system
- job_status: pending, queued, running, succeeded, failed, cancelled, dead_lettered
- approval_status: pending, approved, rejected, expired, consumed, cancelled
- record_status: active, archived, deleting, deleted
- message_role: system, user, assistant, tool
- memory_kind: long_term, semantic, episodic
- source_type: explicit_user, conversation, message, document, tool, agent_run, import, system

Use PostgreSQL enums only after a vocabulary is proven stable. During early development, use checked VARCHAR values to make migrations safer.

## 5. Identity domain

### 5.1 identity.users

The owner account and future user boundary.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| email | CITEXT | nullable, unique when present |
| display_name | VARCHAR(120) | not null |
| timezone | VARCHAR(64) | valid IANA timezone |
| locale | VARCHAR(16) | default en |
| status | VARCHAR(24) | active, locked, disabled, deleted |
| security_mode | VARCHAR(24) | default assistant |
| created_at | TIMESTAMPTZ | not null |
| updated_at | TIMESTAMPTZ | not null |
| last_login_at | TIMESTAMPTZ | nullable |
| deleted_at | TIMESTAMPTZ | nullable |
| version | INTEGER | default 1 |

Indexes: unique normalized email; status; active users. Do not enforce one physical row even though Version 1 has one owner.

### 5.2 identity.auth_identities

Maps local, operating-system, OIDC, and passkey identities.

Columns: id PK, user_id FK, provider, provider_subject, credential_reference, display_label, verified_at, last_used_at, created_at, updated_at.

Constraints: unique provider plus provider_subject. credential_reference stores only a vault reference.

### 5.3 identity.sessions

Columns: id PK, user_id FK, token_hash, device_name, user_agent, ip_hash, created_at, last_seen_at, expires_at, revoked_at, revoke_reason.

Constraints: token_hash unique; expires_at greater than created_at. Store no raw session token. Index user_id plus revoked_at plus expires_at.

### 5.4 identity.user_settings

One-to-one settings row.

Columns: user_id PK/FK, preferences JSONB, privacy_defaults JSONB, notification_settings JSONB, accessibility_settings JSONB, ui_settings JSONB, created_at, updated_at, version.

Each JSONB document has an application schema_version and Pydantic validation.

## 6. Conversation domain

### 6.1 chat.conversations

Columns: id PK, owner_id FK, title, status, classification, summary, summary_version, default_model_policy_id nullable FK, created_at, updated_at, archived_at, deleted_at, version.

Indexes: owner_id plus updated_at descending for active conversations; optional full-text title and summary index.

### 6.2 chat.messages

Columns: id PK, owner_id FK, conversation_id FK, parent_message_id nullable self-FK, sequence_no BIGINT, role, content TEXT, content_format, classification, status, model_call_id nullable FK, tool_action_id nullable FK, token_count, metadata JSONB, created_at, edited_at, deleted_at.

Constraints:

- unique conversation_id plus sequence_no
- owner_id must match conversation owner
- token_count cannot be negative
- tool role requires a related tool action or explicit imported status

Indexes: conversation_id plus sequence_no; owner_id plus created_at; parent_message_id.

Message edits must create audit evidence. Material regeneration creates a new message branch instead of destroying the old response.

### 6.3 chat.message_attachments

Columns: id PK, owner_id, message_id FK, object_id FK, purpose, display_order, created_at.

Unique message_id plus object_id plus purpose. Authorization requires both message and object ownership.

## 7. Memory domain

Current implementation note:

- The codebase currently implements memory.memories and memory.memory_access_events.
- The revision, source, tag, relation, candidate, consolidation, reflection, and graph projection tables remain planned for later E3 slices.

### 7.1 memory.memories

Canonical memory identity and policy envelope.

| Column | Type | Purpose |
|---|---|---|
| id | UUID | PK |
| owner_id | UUID | owner FK |
| kind | VARCHAR(24) | long_term, semantic, episodic |
| title | VARCHAR(240) | human-readable label |
| canonical_content | TEXT | current approved content |
| classification | VARCHAR(24) | privacy level |
| status | VARCHAR(24) | proposed, active, disputed, archived, deleting, deleted |
| confidence | NUMERIC(4,3) | 0 through 1 |
| importance | NUMERIC(4,3) | 0 through 1 |
| access_count | BIGINT | default 0 |
| last_accessed_at | TIMESTAMPTZ | nullable |
| valid_from | TIMESTAMPTZ | nullable |
| valid_until | TIMESTAMPTZ | nullable |
| retention_until | TIMESTAMPTZ | nullable |
| review_after | TIMESTAMPTZ | nullable |
| current_revision_id | UUID | current revision FK |
| embedding_status | VARCHAR(24) | not_requested, pending, indexed, failed, stale, deleted |
| embedding_version | VARCHAR(120) | nullable |
| created_at, updated_at | TIMESTAMPTZ | not null |
| deleted_at | TIMESTAMPTZ | nullable |
| version | INTEGER | optimistic lock |

Constraints: confidence and importance from 0 to 1; valid_until after valid_from; Secret and Restricted records cannot be externally embedded unless an explicit future policy permits it.

Indexes: owner/status/kind; owner/classification; review_after; retention_until; active validity range.

### 7.2 memory.memory_revisions

Immutable revision history.

Columns: id PK, memory_id FK, revision_no, content, classification, confidence, change_type, change_reason, changed_by_type, changed_by_id, supersedes_revision_id nullable FK, content_hash, created_at.

Unique memory_id plus revision_no. Runtime roles cannot update or delete revisions.

### 7.3 memory.memory_sources

Provenance for the memory claim.

Columns: id PK, memory_id FK, revision_id FK, source_type, source_id nullable UUID, source_locator JSONB, evidence_excerpt nullable TEXT, evidence_hash, extraction_method, created_at.

Indexes: memory_id; source_type plus source_id. This relationship enables correction and deletion when a source changes.

### 7.4 memory.tags

Columns: id PK, owner_id, name, normalized_name, color, created_at, updated_at.

Unique owner_id plus normalized_name.

### 7.5 memory.memory_tags

Columns: memory_id FK, tag_id FK, created_at. Composite primary key memory_id plus tag_id.

### 7.6 memory.memory_relations

Columns: id PK, owner_id, source_memory_id FK, target_memory_id FK, relation_type, weight NUMERIC(4,3), created_at.

Unique source, target, relation type. Prevent self-reference. Both memories must have the same owner.

### 7.7 memory.memory_access_events

Append-only explanation of memory retrieval and use.

Columns: id PK, owner_id, memory_id, revision_id, actor_type, actor_id, agent_run_id nullable, purpose, decision, policy_version_id, relevance_score, used_in_prompt BOOLEAN, provider nullable, created_at, trace_id.

Never store the prompt itself. Partition later if volume requires it.

## 8. Object and knowledge domain

### 8.1 knowledge.objects

Authoritative metadata for MinIO objects.

Columns: id PK, owner_id, bucket, object_key, version_id, original_filename, declared_mime, detected_mime, size_bytes, sha256, classification, scan_status, encryption_status, status, retention_until, created_at, updated_at, deleted_at.

Constraints: unique bucket plus object_key plus version_id; nonnegative size; object key is opaque and contains no filename or secret.

### 8.2 knowledge.documents

Columns: id PK, owner_id, current_object_id FK, title, author, source_type, source_uri, language, classification, status, current_version_no, created_at, updated_at, deleted_at, version.

Indexes: owner/status/updated_at; source type; title search when enabled.

### 8.3 knowledge.document_versions

Immutable document and processing lineage.

Columns: id PK, document_id FK, version_no, object_id FK, sha256, parser_name, parser_version, chunker_name, chunker_version, embedding_model, embedding_version, status, page_count, character_count, error_code, error_detail_safe, created_at, completed_at.

Unique document_id plus version_no.

### 8.4 knowledge.document_chunks

Columns: id PK, owner_id, document_id FK, document_version_id FK, ordinal, content, content_hash, page_start, page_end, section_path JSONB, token_count, classification, embedding_status, milvus_collection, milvus_entity_id, created_at, updated_at, deleted_at.

Constraints: unique document_version_id plus ordinal; pages and token count nonnegative. Milvus fields are derived locators.

Indexes: document_version_id plus ordinal; owner/document; pending embedding partial index.

### 8.5 knowledge.tags

Columns: id PK, owner_id, name, normalized_name, color, created_at, updated_at.

Unique owner_id plus normalized_name. Knowledge tags remain separate from memory tags until a shared taxonomy is deliberately approved.

### 8.6 knowledge.document_tags

Columns: document_id FK, tag_id FK, created_at. Composite PK document_id plus tag_id. Document and tag must have the same owner.

### 8.7 knowledge.ingestion_runs

Columns: id PK, owner_id, document_id, document_version_id, job_id, stage, status, attempt, started_at, heartbeat_at, finished_at, chunks_created, chunks_embedded, error_code, error_detail_safe, trace_id.

Unique job_id plus attempt plus stage. Supports visible progress and resumable retries.

## 9. Agent domain

### 9.1 agent.runs

Columns: id PK, owner_id, conversation_id nullable, trigger_type, trigger_id nullable, goal, status, security_mode, policy_snapshot_id, started_at, heartbeat_at, finished_at, cancelled_at, stop_reason, result_summary, input_tokens, output_tokens, total_cost_minor, currency, trace_id, created_at, updated_at, version.

Indexes: owner/status/created_at; conversation_id; heartbeat for abandoned-run detection.

### 9.2 agent.run_steps

Columns: id PK, run_id FK, parent_step_id nullable self-FK, sequence_no, step_type, name, status, input_summary, output_summary, started_at, finished_at, error_code, error_detail_safe, retry_count, trace_span_id.

Unique run_id plus sequence_no.

### 9.3 agent.decisions

Explainability record.

Columns: id PK, run_id FK, step_id nullable FK, decision_type, selected_option, alternatives JSONB, reason, constraints JSONB, model_call_id nullable FK, policy_decision_id nullable FK, created_at.

Decision records are append-only.

### 9.4 agent.tool_actions

Columns: id PK, owner_id, run_id FK, step_id nullable FK, tool_capability_id FK, integration_id nullable FK, risk_level, status, arguments_redacted JSONB, action_hash, idempotency_key, approval_id nullable FK, policy_decision_id FK, provider_request_id, result_summary, created_at, approved_at, executed_at, finished_at, error_code, error_detail_safe.

Unique owner_id plus idempotency_key where present. Full sensitive arguments are not retained in general logs.

## 10. Model domain

### 10.1 platform.model_catalog

Columns: id PK, provider, model_key, display_name, capabilities JSONB, context_window, max_output_tokens, privacy_eligibility, pricing JSONB, enabled, created_at, updated_at.

Unique provider plus model_key.

### 10.2 platform.model_policies

Columns: id PK, owner_id, name, rules JSONB, max_classification, max_cost_minor, currency, latency_target_ms, fallback_allowed, enabled, created_at, updated_at, version.

### 10.3 platform.model_calls

Columns: id PK, owner_id, agent_run_id nullable, message_id nullable, model_id FK, route_reason, classification_max, provider_request_id, status, input_tokens, output_tokens, cached_tokens, latency_ms, cost_minor, currency, prompt_hash, response_hash, started_at, finished_at, error_code, error_detail_safe, trace_id.

Raw prompts and responses are excluded by default. Index owner/time, model/time, run, and provider request ID.

## 11. Tool and governance domain

### 11.1 governance.tools

Columns: id PK, tool_key, name, description, version, enabled, manifest_hash, created_at, updated_at.

Unique tool_key.

### 11.2 governance.tool_capabilities

Columns: id PK, tool_id FK, capability_key, description, default_risk_level, input_schema JSONB, output_schema JSONB, has_side_effect, approval_required, supports_preview, supports_idempotency, enabled, created_at, updated_at.

Unique tool_id plus capability_key.

### 11.3 governance.integrations

Configured tool accounts.

Columns: id PK, owner_id, tool_id, name, account_identifier, credential_reference, granted_scopes TEXT array, status, last_verified_at, created_at, updated_at, version.

Only the vault reference is stored. Unique owner/tool/name.

### 11.4 governance.permissions

Columns: id PK, owner_id, subject_type, subject_id nullable, capability_id, integration_id nullable, resource_pattern nullable, effect, constraints JSONB, valid_from, valid_until, priority, created_by, created_at, updated_at, version.

Policy evaluation uses specificity, priority, and deny precedence. Index active permissions by owner, subject, capability, and integration.

### 11.5 governance.policy_versions

Immutable policy documents.

Columns: id PK, owner_id, policy_name, version_no, document JSONB, document_hash, status, created_by, created_at, activated_at, retired_at.

Unique owner/policy/version. Partial unique index allows one active version per named policy.

### 11.6 governance.policy_decisions

Append-only authorization result.

Columns: id PK, owner_id, actor_type, actor_id, capability_id nullable, resource_type, resource_id nullable, risk_level, decision, reason_code, reason_summary, policy_version_id, context_hash, constraints_applied JSONB, created_at, trace_id.

### 11.7 governance.approvals

Columns: id PK, owner_id, action_id FK, action_hash, risk_level, status, requested_at, expires_at, resolved_at, resolved_by, resolution_reason, reauthenticated_at, consumed_at, version.

Rules:

- approval applies to one exact action hash
- approval expires
- approval is consumed once
- changed action invalidates approval
- critical approval may require recent reauthentication

### 11.8 governance.system_control_state

Current strongly consistent control state.

Columns: owner_id PK, kill_switch_active, automations_enabled, tools_enabled, external_models_enabled, changed_by, change_reason, changed_at, version.

Redis holds an immediate projection but PostgreSQL remains authoritative.

### 11.9 governance.control_events

Append-only: id, owner_id, control_name, previous_value, new_value, actor_id, reason, created_at, trace_id.

### 11.10 governance.data_egress_events

Columns: id PK, owner_id, destination_type, destination, purpose, classification_max, data_categories TEXT array, payload_hash, policy_decision_id, model_call_id nullable, tool_action_id nullable, created_at.

No payload content is stored.

## 12. Automation domain

### 12.1 automation.automations

Columns: id PK, owner_id, name, description, trigger_type, trigger_config JSONB, workflow_definition JSONB, policy_version_id, security_mode, status, valid_from, expires_at, last_run_at, next_run_at, safety_budgets JSONB, created_at, updated_at, version.

### 12.2 automation.executions

Columns: id PK, automation_id FK, agent_run_id nullable FK, scheduled_for, status, started_at, finished_at, result_summary, error_code, error_detail_safe, created_at.

Unique automation_id plus scheduled_for prevents duplicate scheduled execution.

## 13. Job and messaging domain

### 13.1 platform.jobs

Columns: id PK, owner_id, job_type, status, priority, payload_reference, progress_current, progress_total, attempt, max_attempts, available_at, locked_by, lease_expires_at, started_at, finished_at, cancel_requested_at, error_code, error_detail_safe, created_at, updated_at.

Indexes: status plus available_at plus priority; lease expiry; owner plus created_at.

### 13.2 platform.outbox_events

Columns: id PK, owner_id nullable, aggregate_type, aggregate_id, event_type, schema_version, payload JSONB, correlation_id, causation_id, created_at, published_at, attempts, last_error_safe.

Partial index on unpublished rows ordered by created_at.

### 13.3 platform.processed_messages

Columns: consumer_name, message_id, processed_at, result_hash. Composite PK consumer_name plus message_id. Retain beyond the maximum redelivery period.

### 13.4 platform.idempotency_keys

Columns: owner_id, scope, idempotency_key, request_hash, status, response_code, response_reference, created_at, expires_at.

Composite PK owner_id plus scope plus idempotency_key. Reusing a key with a different request hash is rejected.

## 14. Audit domain

### 14.1 audit.events

Append-only security evidence.

| Column | Purpose |
|---|---|
| id | UUID event identity |
| sequence_no | monotonic BIGSERIAL |
| occurred_at | event time |
| recorded_at | database receipt time |
| owner_id | affected owner |
| actor_type, actor_id | initiator |
| session_id | user session when applicable |
| event_type | stable event name |
| risk_level | event risk |
| resource_type, resource_id | affected resource |
| action, outcome | attempted behavior and result |
| reason_code, summary | safe explanation |
| metadata_redacted | structured safe details |
| trace_id, correlation_id | cross-system linkage |
| previous_hash, event_hash | tamper-evidence chain |
| retention_until | policy retention |

Partition monthly when volume justifies it. Runtime roles cannot UPDATE or DELETE. Never store secrets or full sensitive payloads.

### 14.2 audit.exports

Columns: id PK, owner_id, requested_by, filters JSONB, status, approval_id, object_id, created_at, expires_at, downloaded_at, error_code, error_detail_safe.

Export objects are encrypted, short-lived, and require governed access.

## 15. Core relationships

- User owns conversations, memories, documents, runs, integrations, permissions, policies, automations, and audit records.
- Conversation contains ordered messages.
- Message may reference a model call, tool action, and object attachments.
- Memory contains immutable revisions, provenance sources, tags, relations, and access events.
- Document references MinIO object metadata and immutable processing versions.
- Document version contains ordered chunks and ingestion runs.
- Agent run contains steps, decisions, model calls, and tool actions.
- Tool action references capability, integration, policy decision, and optional approval.
- Automation execution may create an agent run.
- Jobs and outbox events coordinate asynchronous work.
- Audit events correlate protected behavior without duplicating content.

## 16. Foreign-key deletion policy

Default is RESTRICT.

CASCADE is allowed only for dependent records with no independent legal, audit, or recovery value, such as a temporary join row.

Owner deletion is a governed workflow, not a database cascade:

1. Disable sessions, tools, automations, and model egress.
2. Mark owner resources deleting.
3. Block retrieval immediately.
4. Delete Milvus vectors.
5. Delete or retain MinIO objects according to policy.
6. Expire Redis state.
7. Purge permitted PostgreSQL content.
8. Retain only policy-required safe audit facts.
9. Report backup retention separately.
10. Mark deletion complete.

## 17. Index strategy

Required index families:

- every frequently joined foreign key
- owner plus status plus updated_at for dashboard lists
- conversation plus sequence_no
- active memory by kind, classification, validity, review, and retention
- document plus version and chunk ordinal
- pending embedding and ingestion states
- run plus status plus heartbeat
- pending approval plus expiry
- active permissions by subject/capability
- scheduled automation plus next_run_at
- job status plus available_at
- unpublished outbox partial index
- audit owner/time/type and BRIN time index at scale

Use GIN only for defined JSONB containment or full-text access paths. Validate using EXPLAIN ANALYZE with realistic data.

## 18. Row-level security

Enable RLS on all owner-scoped tables.

The application transaction sets a validated owner context. Policies require row owner_id to match. Cross-owner access fails even if application filtering is defective.

Runtime roles:

| Role | Access |
|---|---|
| novo_migrator | schema migration only |
| novo_api | normal owner-facing use cases |
| novo_agent_worker | runs, steps, decisions, governed actions |
| novo_ingestion_worker | objects, documents, chunks |
| novo_scheduler | automations and job scheduling |
| novo_auditor | append audit and restricted read |
| novo_readonly | operational diagnostics |

Runtime roles never own tables and cannot bypass RLS.

## 19. Concurrency and integrity

- Optimistic version checks for user-editable records.
- Row locks for approval consumption, action execution, budgets, and job leases.
- Unique idempotency keys prevent duplicate effects.
- State transition services reject illegal transitions.
- Immutable revisions, policies, decisions, and audit rows reject runtime mutation.
- Owner IDs on related records are checked in service logic and critical database triggers.
- Transaction isolation defaults to READ COMMITTED; use stricter isolation for budget and one-time execution races.
- Long operations never hold database transactions open.

## 20. Retention and partitioning

Retention is policy-specific:

- sessions expire after inactivity
- idempotency and processed-message rows outlive retry windows
- operational error detail has short retention
- model usage aggregates may retain longer than detailed calls
- memory follows its classification and explicit retention
- deleted content purges after a recovery window
- audit evidence follows security policy
- backups have independent encrypted retention

Start unpartitioned except audit if expected volume requires it. Add monthly partitions for append-only access, model, action, and audit records only after measurement.

## 21. Encryption

- TLS for all database connections.
- Encrypted storage and encrypted backups.
- Vault-managed database credentials.
- Highly sensitive columns may use application-level envelope encryption after threat-model review.
- Searchable hashes must not be confused with encryption.
- Encryption keys are versioned and rotatable.
- No key material is stored in database rows.

## 22. Migration policy

- Alembic is the only production schema-change path.
- Migrations work for fresh install and upgrade.
- Use expand, backfill, switch, contract for breaking changes.
- Large backfills are resumable jobs.
- Destructive changes require backup, verification, and explicit approval.
- Application startup checks schema compatibility but never auto-migrates production.
- Each release tests migration, data constraints, rollback or compensation, backup, and restore.

## 23. Seed data

Seed only non-secret definitions:

- security modes and classifications
- built-in tool manifests and capabilities
- default risk levels
- default deny/ask permission templates
- initial model catalog metadata
- default Assistant Mode policy
- audit event type registry if adopted

Owner accounts and credentials are created through secure setup, never migration files.

## 24. Open decisions

1. UUIDv7 versus UUIDv4.
2. Password/passkey/OIDC authentication design.
3. Audit hash signing and verification process.
4. Exact retention by classification.
5. PostgreSQL full-text conversation search in Version 1.
6. Shared versus domain-specific tags.
7. Policy language: JSON Logic, CEL, or constrained custom format.
8. Threshold for monthly partitions.
9. Which sensitive columns need envelope encryption.
10. Whether quoted provenance evidence is stored for Confidential data.

## 25. Implementation order

1. Schemas, extensions, shared checks, and database roles.
2. Users, identities, sessions, and settings.
3. Conversations and messages.
4. Objects, documents, versions, and chunks.
5. Memories, revisions, sources, and tags.
6. Model catalog, policies, and calls.
7. Tools, capabilities, integrations, and permissions.
8. Agent runs, steps, decisions, and actions.
9. Policies, approvals, controls, and egress.
10. Jobs, outbox, idempotency, and processed messages.
11. Automations.
12. Audit events and exports.
13. RLS, append-only triggers, partitions, and retention jobs.
14. Seed data and end-to-end migration tests.

## 26. Required database tests

- owner isolation and RLS
- unique conversation ordering
- memory score and validity constraints
- immutable revision and policy history
- approval expiry and one-time consumption
- action idempotency
- job lease recovery
- outbox atomicity
- duplicate message consumption
- legal and illegal state transitions
- logical deletion blocking retrieval
- multi-store deletion tracking
- audit append-only enforcement and hash verification
- backup restoration and migration upgrade

## 27. Definition of done

This design is accepted when:

- every Phase 1 through Phase 3 durable fact maps to a named table
- all relationships and ownership boundaries are unambiguous
- secrets, binaries, vectors, and queue state are correctly excluded
- memory provenance and revision history are complete
- permissions, policies, approvals, actions, and audit form one traceable chain
- constraints and indexes support known API access patterns
- deletion and retention span every storage system
- migrations and database tests reproduce the accepted design
- Memory, RAG, Agent, Security, and API specifications use the same names and states

## 28. Version 2 Companion and Platform Extensions

These tables extend the accepted normalized design for companion intelligence, reflection, registries, graph projection, and computer control.

### 28.1 companion.companion_profiles

Columns: id PK, owner_id unique FK, preferred_tone, communication_preferences JSONB, boundaries JSONB, enabled, created_at, updated_at, version. This stores owner configuration, not a hidden psychological profile.

### 28.2 companion.goals

Columns: id PK, owner_id, parent_goal_id nullable self-FK, title, description, category, status, priority, target_date, success_definition, classification, source_memory_id nullable, created_at, updated_at, completed_at, deleted_at, version. Index owner/status/priority/target_date.

### 28.3 companion.goal_progress_events

Append-only columns: id PK, owner_id, goal_id FK, measured_at, value_numeric nullable, value_text nullable, unit nullable, source_type, source_id nullable, note, created_at. Index goal/measured_at.

### 28.4 companion.projects and companion.project_milestones

projects columns: id PK, owner_id, title, description, status, priority, start_date, target_date, classification, created_at, updated_at, archived_at, version.

project_milestones columns: id PK, project_id FK, title, status, target_date, completed_at, source_id nullable, created_at, updated_at. Index project/status/target_date.

### 28.5 companion.interests

Columns: id PK, owner_id, name, normalized_name, confidence, source_type, source_id, status, review_after, created_at, updated_at. Unique owner/normalized_name for active rows.

### 28.6 companion.life_events

Columns: id PK, owner_id, title, description, event_date, classification, confidence, source_type, source_id, status, created_at, updated_at, deleted_at. Life events require explicit provenance and may require owner confirmation.

### 28.7 companion.emotional_observations

Columns: id PK, owner_id, message_id nullable FK, conversation_id nullable FK, label, valence nullable, arousal nullable, confidence, inference_method, model_call_id nullable, evidence_hash, status, observed_at, expires_at, reviewed_at, created_at.

Constraints: confidence from zero to one; status is proposed, accepted, rejected, expired, or deleted. It is never a diagnosis, never an authorization input, and never silently permanent. Index owner/status/observed_at and expiry.

### 28.8 memory.memory_candidates

Columns: id PK, owner_id, conversation_id nullable, message_id nullable, candidate_type, proposed_content, classification, confidence, importance_score, novelty_score, recurrence_score, status, extraction_method, created_at, review_after, decided_at, resulting_memory_id nullable. Index owner/status/importance/created_at.

### 28.9 memory.consolidation_runs and memory.consolidation_decisions

consolidation_runs columns: id PK, owner_id, job_id, status, policy_version_id, candidate_count, accepted_count, rejected_count, started_at, finished_at, trace_id, safe error fields.

consolidation_decisions columns: id PK, run_id, candidate_id, decision, reason, duplicate_memory_id nullable, contradiction_memory_id nullable, requires_review, resulting_revision_id nullable, created_at. Unique run/candidate.

### 28.10 memory.reflection_runs and memory.reflection_insights

reflection_runs columns: id PK, owner_id, schedule_id nullable, scope_start, scope_end, policy_version_id, status, started_at, finished_at, model_call_id nullable, trace_id, safe error fields.

reflection_insights columns: id PK, reflection_run_id, owner_id, insight_type, summary, evidence_references JSONB, confidence, classification, proposed_action, review_status, resulting_candidate_id nullable, created_at, reviewed_at. Index owner/review_status/created_at.

### 28.11 memory.graph_sync_records

Columns: id PK, owner_id, source_type, source_id, source_version, graph_node_id, projection_version, status, last_synced_at, retry_count, safe error fields. Unique source_type/source_id/projection_version. PostgreSQL is authoritative; Neo4j is rebuildable.

### 28.12 platform.prompt_templates

Columns: id PK, prompt_key unique, purpose, name, description, variable_schema JSONB, security_level, owner_id nullable, created_at, updated_at.

### 28.13 platform.prompt_versions

Columns: id PK, template_id FK, version_no, content, content_hash, status, change_reason, created_by, evaluation_status, created_at, activated_at, retired_at. Unique template/version. Immutable after creation.

### 28.14 platform.prompt_bindings

Columns: id PK, owner_id nullable, purpose, agent_type nullable, tool_capability_id nullable, prompt_version_id, priority, valid_from, valid_until, created_at. Partial uniqueness ensures one active binding per resolved scope.

### 28.15 platform.domain_event_types and platform.event_deliveries

domain_event_types columns: event_type and schema_version composite PK, description, payload_schema JSONB, sensitivity, retention_policy, active, created_at.

event_deliveries columns: id PK, outbox_event_id, consumer_name, status, attempt, first_attempt_at, last_attempt_at, acknowledged_at, safe error fields. Unique outbox event/consumer.

### 28.16 agent.computer_sessions

Columns: id PK, owner_id, agent_run_id, sandbox_profile, status, policy_version_id, approval_id nullable, started_at, heartbeat_at, finished_at, termination_reason, trace_id. Index owner/status/time.

### 28.17 agent.computer_actions

Columns: id PK, session_id, sequence_no, action_type, target_redacted, arguments_redacted JSONB, action_hash, risk_level, policy_decision_id, approval_id nullable, status, started_at, finished_at, result_summary, safe error fields. Unique session/sequence and session/action_hash where appropriate.

### 28.18 agent.computer_evidence

Columns: id PK, session_id, action_id nullable, object_id FK, evidence_type, classification, captured_at, retention_until, content_hash. Evidence follows privacy and retention policy.

### 28.19 Normalization and storage rules

All Version 2 authoritative tables remain in Third Normal Form. Companion observations reference source records instead of copying conversations. Prompt versions separate stable template identity from immutable content. Computer evidence references MinIO objects. Neo4j graph IDs are derived locators. Counters and current status fields are controlled denormalization with documented repair paths.

Visual references: diagrams/DATABASE_RELATIONSHIPS.md and diagrams/MEMORY_COMPANION_PIPELINE.md.

## 29. Orchestrator, Guardrails, and Hot-Path Data Support

### 29.1 Orchestrator runtime records

agent.runs, agent.run_steps, agent.decisions, agent.tool_actions, platform.jobs, platform.model_catalog, platform.model_policies, and platform.model_calls collectively support the Orchestrator.

agent.decisions records fast/deep routing, retrieval plan, model tier, async decision, and reason. A fast no-agent response may use a lightweight decision/model-call record rather than creating artificial multi-step runs.

### 29.2 Guardrails and policy records

governance.permissions, governance.policy_versions, governance.policy_decisions, governance.approvals, governance.system_control_state, governance.data_egress_events, and audit.events support Guardrails and Policy Enforcement.

Policy decisions must record enforcement stage: input, retrieval, model_input, model_output, action, memory_write, or egress.

### 29.3 Fast-path hot reads

Fast chat uses compact indexed reads and Redis projections backed by PostgreSQL. Heavy audit history, broad policy history, reflection, graph joins, and analytics stay off the hot path unless required.

Required access paths include active policy version, system control state, recent conversation sequence, current summary, exact active memory lookup, model eligibility, and provider health. Cache keys carry policy/configuration version so stale security state fails closed or reloads.

### 29.4 Free-model routing metadata

platform.model_catalog and platform.model_policies support OpenRouter model key, free/paid tier, context limit, structured-output reliability, tool-output reliability, observed latency, availability, quality score, classification eligibility, fallback priority, health expiry, and last verification.

platform.model_calls records selected tier, fallback chain, validation/repair attempts, registry version, route reason, and safe failure outcome.

These additions remain normalized: observed health may use append-only model-health samples later, while model_catalog stores only the current routing projection.

# NOVO Database Relationships and Normalization

## 1. Domain-level ERD

~~~mermaid
erDiagram
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ CONVERSATIONS : owns
    CONVERSATIONS ||--o{ MESSAGES : contains
    MESSAGES ||--o{ MESSAGE_ATTACHMENTS : has
    USERS ||--o{ MEMORIES : owns
    MEMORIES ||--o{ MEMORY_REVISIONS : versions
    MEMORY_REVISIONS ||--o{ MEMORY_SOURCES : supported_by
    MEMORIES ||--o{ MEMORY_TAGS : classified_by
    TAGS ||--o{ MEMORY_TAGS : applies
    USERS ||--o{ DOCUMENTS : owns
    DOCUMENTS ||--o{ DOCUMENT_VERSIONS : versions
    DOCUMENT_VERSIONS ||--o{ DOCUMENT_CHUNKS : contains
    DOCUMENT_VERSIONS ||--o{ INGESTION_RUNS : processed_by
    USERS ||--o{ AGENT_RUNS : owns
    AGENT_RUNS ||--o{ RUN_STEPS : contains
    AGENT_RUNS ||--o{ DECISIONS : explains
    AGENT_RUNS ||--o{ TOOL_ACTIONS : proposes
    TOOLS ||--o{ TOOL_CAPABILITIES : exposes
    TOOL_CAPABILITIES ||--o{ TOOL_ACTIONS : executes
    TOOL_ACTIONS o|--o| APPROVALS : authorized_by
    POLICY_VERSIONS ||--o{ POLICY_DECISIONS : produces
    POLICY_DECISIONS ||--o{ TOOL_ACTIONS : governs
    USERS ||--o{ AUDIT_EVENTS : scoped_to
~~~

## 2. Companion and memory Version 2 ERD

~~~mermaid
erDiagram
    USERS ||--o{ COMPANION_PROFILES : configures
    USERS ||--o{ GOALS : owns
    USERS ||--o{ PROJECTS : owns
    USERS ||--o{ INTERESTS : owns
    USERS ||--o{ LIFE_EVENTS : owns
    USERS ||--o{ EMOTIONAL_OBSERVATIONS : owns
    CONVERSATIONS ||--o{ MEMORY_CANDIDATES : produces
    MESSAGES ||--o{ MEMORY_CANDIDATES : supports
    MEMORY_CANDIDATES ||--o{ CONSOLIDATION_DECISIONS : evaluated_by
    CONSOLIDATION_RUNS ||--o{ CONSOLIDATION_DECISIONS : contains
    REFLECTION_RUNS ||--o{ REFLECTION_INSIGHTS : produces
    REFLECTION_INSIGHTS o|--o| MEMORY_CANDIDATES : proposes
    MEMORY_CANDIDATES o|--o| MEMORIES : becomes
    GOALS ||--o{ GOAL_PROGRESS_EVENTS : measures
    PROJECTS ||--o{ PROJECT_MILESTONES : contains
    EMOTIONAL_OBSERVATIONS }o--o| MESSAGES : inferred_from
    MEMORIES ||--o{ GRAPH_SYNC_RECORDS : projected_by
~~~

## 3. Registry and computer-control ERD

~~~mermaid
erDiagram
    MODEL_CATALOG ||--o{ MODEL_CALLS : selected_for
    MODEL_POLICIES ||--o{ MODEL_CALLS : constrains
    PROMPT_TEMPLATES ||--o{ PROMPT_VERSIONS : versions
    PROMPT_VERSIONS ||--o{ PROMPT_BINDINGS : bound_by
    MODEL_CALLS }o--o| PROMPT_VERSIONS : renders
    AGENT_RUNS ||--o{ COMPUTER_SESSIONS : starts
    COMPUTER_SESSIONS ||--o{ COMPUTER_ACTIONS : contains
    COMPUTER_ACTIONS ||--o{ COMPUTER_EVIDENCE : records
    COMPUTER_ACTIONS o|--o| APPROVALS : authorized_by
    OUTBOX_EVENTS ||--o{ EVENT_DELIVERIES : delivered_as
~~~

## 4. Normalization assessment

NOVO's relational model targets Third Normal Form for authoritative business data.

| Normal form | How NOVO satisfies it |
|---|---|
| First Normal Form | Scalar columns and join tables replace repeating groups |
| Second Normal Form | Join-table attributes depend on the complete composite key |
| Third Normal Form | Provider, tool, tag, policy, and model facts live in their own tables |
| Controlled denormalization | Summaries, counters, current revision IDs, and status projections improve reads |
| Derived stores | Milvus and Neo4j are indexes, not competing truth |

Intentional denormalization must document:

- authoritative source
- refresh mechanism
- acceptable staleness
- repair/rebuild process
- authorization recheck
- deletion propagation

## 5. Index coverage map

| Access path | Required index |
|---|---|
| Active owner conversations | conversations(owner_id, status, updated_at DESC) |
| Ordered messages | messages(conversation_id, sequence_no) UNIQUE |
| Active memories | memories(owner_id, status, kind, updated_at DESC) |
| Memory review/expiry | memories(owner_id, review_after), memories(owner_id, retention_until) |
| Provenance lookup | memory_sources(source_type, source_id) |
| Document versions | document_versions(document_id, version_no) UNIQUE |
| Ordered chunks | document_chunks(document_version_id, ordinal) UNIQUE |
| Pending embeddings | partial document_chunks where embedding_status = pending |
| Active runs | agent_runs(owner_id, status, created_at DESC) |
| Pending approvals | approvals(owner_id, status, expires_at) |
| Capability permissions | permissions(owner_id, subject_type, capability_id, integration_id) |
| Due automations | automations(status, next_run_at) |
| Runnable jobs | jobs(status, available_at, priority) |
| Unpublished events | partial outbox_events(created_at) where published_at is null |
| Audit timeline | audit_events(owner_id, occurred_at DESC) |
| Audit scale | BRIN audit_events(occurred_at) |
| Candidate consolidation | memory_candidates(owner_id, status, importance_score, created_at) |
| Reflection review | reflection_insights(owner_id, review_status, created_at) |
| Goal dashboard | goals(owner_id, status, priority, target_date) |
| Computer session replay | computer_actions(session_id, sequence_no) UNIQUE |

## 6. Index verification policy

An index is not considered implemented merely because it appears in this document.

Each migration must be verified with:

1. PostgreSQL catalog inspection.
2. EXPLAIN ANALYZE with realistic row counts.
3. Foreign-key index audit.
4. Duplicate and partial-index constraint tests.
5. Write-amplification review.
6. Production slow-query telemetry.

The Control Center may later expose database health, missing-index warnings, unused indexes, table growth, and vacuum health.

## 7. Storage ownership

~~~mermaid
flowchart LR
    PG["PostgreSQL<br/>authoritative rows"] --> Milvus["Milvus<br/>derived vectors"]
    PG --> Neo4j["Neo4j<br/>derived relationships"]
    PG --> Redis["Redis<br/>ephemeral projections"]
    PG --> MQ["RabbitMQ<br/>delivery references"]
    PG --> MinIO["MinIO<br/>object metadata links"]
    Milvus --> Rebuild["Rebuild from PostgreSQL"]
    Neo4j --> Rebuild
~~~

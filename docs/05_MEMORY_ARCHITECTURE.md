# NOVO Memory Architecture

**Status:** Draft for owner review
**Version:** 0.1
**Owner:** Jay Rana
**Default mode:** Assistant Mode
**Last updated:** 2026-06-24

## 1. Purpose

Memory is NOVO's continuity layer. It retains useful context, owner-approved preferences, goals, projects, and past experiences without creating an invisible or uncontrollable profile.

This specification defines short-term, long-term, semantic, episodic, companion, emotional, and graph memory; creation, consolidation, reflection, retrieval, correction, deletion, privacy, audit, reliability, and testing.

Visual reference: diagrams/MEMORY_COMPANION_PIPELINE.md.

## 2. Owner memory promise

The owner must always be able to determine:

1. What NOVO remembers.
2. Why it remembers it.
3. Where it came from.
4. Whether it is fact, statement, observation, or inference.
5. How confident NOVO is.
6. When it was created, used, revised, or scheduled for review.
7. Which responses or actions used it.
8. How to correct, restrict, archive, export, or delete it.
9. Whether it was sent to an external model.

Memory improves continuity without silently converting conversation into permanent identity.

## 3. Non-negotiable principles

### 3.1 PostgreSQL is authoritative

Canonical content, revisions, provenance, classification, status, permissions, retention, and deletion state live in PostgreSQL. Redis, Milvus, and Neo4j are projections.

### 3.2 Explicit truth outranks inference

An explicit owner correction outranks model inference, repetition, emotional detection, tool inference, summaries, and graph relationships. Disputed or corrected records stop influencing responses immediately.

### 3.3 Provenance is mandatory

Every durable memory requires a source or explicit system reason. A memory without provenance cannot become Active.

### 3.4 Inference is labeled

Inferred content retains method, confidence, evidence, and review policy. It is never represented as a direct owner statement.

### 3.5 Secrets are excluded

Credentials, keys, passwords, tokens, cookies, and recovery codes are rejected and handled only by the Secrets Provider.

### 3.6 Retrieval requires authorization

A vector or graph result is not authorization. Every candidate is reloaded and reauthorized from PostgreSQL.

### 3.7 Memory is reversible

Creation, consolidation, merging, reflection, and relationship projection are correctable and deletable.

### 3.8 Companion memory is not surveillance

NOVO stores only information needed for owner-approved purposes. It does not silently capture every activity, emotion, relationship, or interaction.

## 4. Memory taxonomy

### 4.1 Short-term working memory

Purpose: current conversation continuity, active task variables, recent tool observations, pending clarification, and approval context.

Primary store: Redis. It is temporary, reconstructable, and normally lives minutes to hours. It never becomes durable without the candidate pipeline.

### 4.2 Long-term declarative memory

Owner-approved facts, preferences, goals, constraints, profile information, and durable project context.

Authority: memory.memories and memory.memory_revisions in PostgreSQL.

### 4.3 Semantic memory

Meaning-based retrieval over authorized durable content.

Authority: PostgreSQL. Derived index: Milvus. Semantic memory is a retrieval method, not separate truth.

### 4.4 Episodic memory

Past conversations, agent runs, tasks, tool actions, events, outcomes, and lessons.

Authority: PostgreSQL. Episodic summaries link to underlying evidence and temporal boundaries rather than duplicating entire conversations.

### 4.5 Companion context

Goals, projects, milestones, interests, life events, communication preferences, personal development progress, and owner-approved continuity.

Authority: companion schema tables plus linked memories.

### 4.6 Emotional observations

Uncertain contextual signals, not facts or diagnoses.

Rules:

- Distinguish explicit statements from inference.
- Require confidence and source.
- Record inference method and model version.
- Default to short retention.
- Allow rejection, editing, disabling, and deletion.
- Never authorize actions or alter security mode.
- Never optimize engagement or dependency.
- Never present as medical or psychological diagnosis.

### 4.7 Knowledge-graph projection

Neo4j represents authorized relationships among entities, memories, goals, projects, documents, tools, and concepts. PostgreSQL remains authoritative.

## 5. Storage responsibility

| Data | Authority | Derived or temporary |
|---|---|---|
| Conversation context | PostgreSQL messages | Redis working set |
| Durable memory | PostgreSQL | Milvus vector |
| Revisions and sources | PostgreSQL | None |
| Episodic summaries | PostgreSQL | Milvus |
| Goals and projects | PostgreSQL companion schema | Milvus or Neo4j |
| Emotional observations | PostgreSQL companion schema | Redis recent context |
| Relationships | PostgreSQL records | Neo4j |
| Document knowledge | PostgreSQL and MinIO | Milvus and Neo4j |
| Access explanation | PostgreSQL | Analytics |
| Secrets | Secrets vault | Short-lived process memory |

## 6. Canonical tables

The Memory Service uses:

- memory.memories
- memory.memory_revisions
- memory.memory_sources
- memory.tags
- memory.memory_tags
- memory.memory_relations
- memory.memory_access_events
- memory.memory_candidates
- memory.consolidation_runs
- memory.consolidation_decisions
- memory.reflection_runs
- memory.reflection_insights
- memory.graph_sync_records
- companion.companion_profiles
- companion.goals
- companion.goal_progress_events
- companion.projects
- companion.project_milestones
- companion.interests
- companion.life_events
- companion.emotional_observations

Database Design owns columns. This document owns lifecycle behavior.

## 7. State machines

### 7.1 Candidate states

- extracted
- classified
- scored
- awaiting_review
- accepted
- rejected
- temporary
- superseded
- expired
- failed

### 7.2 Durable memory states

- proposed: unavailable for normal retrieval
- active: eligible under policy
- disputed: correctness challenged and blocked
- archived: preserved but normally excluded
- deleting: inaccessible during cleanup
- deleted: removed from active stores

Only Active memory enters normal response context.

### 7.3 Embedding states

not_requested, pending, indexed, stale, failed, deleting, deleted.

Embedding failure never destroys canonical memory.

## 8. Creation sources

Candidates may originate from:

- Explicit remember command
- Owner profile or setting
- Conversation message
- Tool or agent result
- Document or import
- Goal or milestone
- Repeated pattern
- Reflection insight
- System migration

Each source has separate defaults. Explicit requests still pass secret detection, classification, and validation.

## 9. Candidate extraction

1. Receive eligible source event.
2. Load owner memory policy.
3. Detect secrets and prohibited data.
4. Separate owner statements from quoted untrusted content.
5. Extract atomic claims.
6. Assign candidate type and provenance.
7. Classify sensitivity.
8. Estimate confidence.
9. Score importance, novelty, recurrence, and utility.
10. Detect duplicates and contradictions.
11. Assign retention and review defaults.
12. Route to reject, temporary, consolidate, or review.
13. Record decision explanation.
14. Publish downstream events after commit.

A conversation may produce zero candidates.

## 10. Atomic candidate rules

Good candidates express one independently reviewable claim.

Examples:

- The owner prefers concise technical explanations.
- NOVO uses FastAPI.
- The owner is working toward a named goal.

Rejected shapes:

- Full transcripts
- Multiple unrelated claims
- Copied pages
- Credentials
- Unsupported personality judgments
- Diagnoses
- Model assumptions presented as fact

## 11. Scoring

All scores range from zero to one.

### Confidence

Evidence quality based on explicitness, source reliability, independent support, extraction certainty, contradiction strength, recency, and confirmation.

### Importance

Long-term value based on explicit remember request, goal relevance, future utility, safety significance, stability, cost of forgetting, and milestone significance.

### Novelty

Difference from active canonical memory.

### Recurrence

Repeated evidence across meaningfully independent episodes.

### Utility

Expected assistance value weighed against privacy cost.

A configurable starting decision formula is 30 percent importance, 25 percent confidence, 20 percent utility, 15 percent recurrence, and 10 percent novelty.

Classification, prohibited content, contradiction, and review rules override scores.

## 12. Default decisions

| Condition | Outcome |
|---|---|
| Secret detected | Reject and offer vault guidance |
| Restricted without explicit permission | Reject |
| Explicit valid remember request | Accept or review by classification |
| Low-confidence inference | Temporary or reject |
| Emotional inference | Short retention and review-sensitive |
| Exact duplicate | Add valuable provenance only |
| Compatible update | Create revision |
| Material contradiction | Dispute and review |
| Stable useful preference | Accept under policy |
| Transient task detail | Short-term only |
| Untrusted document instruction | Reject as behavioral memory |
| Reflection insight | Proposed and policy-reviewed |

## 13. Consolidation Service

Responsibilities:

- Batch candidates
- Detect duplicates and contradictions
- Match candidates to memories
- Recommend create, revise, merge, dispute, or reject
- Assign retention
- Route review
- Write idempotently
- Request projections
- Audit decisions

It never executes external tools.

### 13.1 Consolidation transaction

Within one PostgreSQL transaction:

1. Lock candidate.
2. Confirm eligibility.
3. Re-evaluate policy.
4. Load related memories.
5. Decide outcome.
6. Create memory/revision or update status.
7. Attach sources.
8. Set current revision.
9. Record decision.
10. Write outbox events.
11. Commit.

Milvus and Neo4j update after commit.

### 13.2 Idempotency

Candidate ID plus consolidation policy version forms the idempotency scope. Retry returns the existing decision.

## 14. Duplicate, update, contradiction, and merge

### Exact duplicate

Do not create another memory. Add useful provenance and recurrence evidence.

### Semantic duplicate

Link to the existing memory; revise canonical wording only if necessary.

### Compatible update

Create immutable revision, update current revision, mark projections stale, and publish update event.

### Contradiction

Never average silently. Prefer clear recent owner correction; otherwise mark Disputed, block retrieval, and request clarification.

### Merge

Create a canonical revision or memory, record superseded IDs, and retain all provenance.
## 15. Short-term working memory

### 15.1 Redis structure

Keys are namespaced by environment, owner, conversation or run, purpose, and schema version.

Working state may contain:

- Recent message IDs
- Conversation summary ID
- Active goal and plan
- Tool-result references
- Pending approvals
- Unresolved questions
- Context-budget estimates
- Stream progress

Use canonical IDs instead of copying durable records. Never store secrets.

### 15.2 TTL behavior

- Every key has a TTL unless it is an active bounded lease.
- TTL extends only through explicit activity.
- Conversation close clears unnecessary state.
- Kill switch may clear agent working state.
- Redis eviction cannot lose authoritative information.

### 15.3 Context compression

When history exceeds budget:

1. Preserve recent messages needed for coherence.
2. Preserve unresolved instructions and constraints.
3. Create a source-linked summary.
4. Validate it against key messages.
5. Record model and prompt versions.
6. Retain evidence message IDs.
7. Never treat summary inference as owner fact.

## 16. Long-term lifecycle

### Create

Accepted candidate -> memory row -> revision 1 -> sources -> Proposed or Active -> outbox event.

### Read

Policy prefilter -> retrieve -> PostgreSQL reauthorization -> context inclusion -> access event.

### Update

Owner correction or evidence -> immutable revision -> projection refresh -> audit.

### Archive

Archived records remain in history but leave normal retrieval.

### Dispute

Disputed records are blocked pending resolution.

### Delete

Deleting blocks use immediately; workers remove derived projections before final purge.

## 17. Semantic indexing

### 17.1 Eligibility

Embed only when:

- Memory is Active.
- Owner policy allows indexing.
- Classification is eligible for the embedding provider.
- Secret detection passed.
- Required review exists.
- Validity and retention windows are active.

Secret and Restricted memory never goes to external embedding providers by default.

### 17.2 Embedding input

Embed minimum canonical text. Exclude raw transcripts, credentials, unrelated context, audit metadata, policy internals, and rejected observations.

### 17.3 Vector metadata

Each vector contains:

- Memory ID
- Owner ID
- Revision ID
- Classification
- Memory kind
- Embedding model and version
- Projection version
- Lifecycle status

### 17.4 Versioning and rebuild

Model or dimension change creates a new collection version. Verify coverage and retrieval before switching. Milvus must be completely rebuildable from PostgreSQL.

### 17.5 Deletion

PostgreSQL blocks use immediately. A worker removes vectors. Reconciliation detects stale and orphaned vectors.

## 18. Knowledge-graph projection

### 18.1 Eligible concepts

Owner-approved people, organizations, projects, goals, milestones, documents, technologies, tools, memories, topics, and concepts.

### 18.2 Projection rules

- PostgreSQL owns IDs, content, classification, and permissions.
- Neo4j nodes use canonical opaque IDs.
- Owner and classification accompany projections.
- Sensitive relationship types may be excluded.
- Traversal is owner-scoped.
- Results are reauthorized in PostgreSQL.
- Deleted and disputed records are blocked immediately.
- Sync is event-driven and idempotent.
- Full rebuild is supported.

### 18.3 Relationship confidence

Explicit and inferred relationships are distinct. Inferred edges contain confidence, provenance, source version, and projection version.

### 18.4 Uses

Graph retrieval supports multi-hop project context, goal reasoning, entity disambiguation, related-memory discovery, and knowledge navigation. It never bypasses authorization.

## 19. Reflection Agent

### 19.1 Purpose

Reflection proposes higher-level insights from permitted episodic history.

Examples:

- An owner goal is recurring.
- A project remains blocked.
- A preference appears stable.
- A goal may be stale.
- Memories conflict.
- A recurring workflow may benefit from automation.

### 19.2 Activation and schedule

Reflection is disabled by default until enabled by the owner.

Supported triggers:

- Owner request
- Daily or weekly schedule
- Important conversation completion
- Project milestone
- Maintenance window

The owner controls scope, frequency, model eligibility, cost, and review.

### 19.3 Input

Minimum policy-scoped input:

- Eligible recent episodes
- Relevant existing memories
- Active goals and projects
- Unresolved prior insights
- Companion settings

Reflection never receives unrestricted history.

### 19.4 Output

Each insight includes:

- Insight type
- Safe summary
- Evidence references
- Confidence
- Classification
- Proposed action
- Affected memory IDs
- Contradictions
- Retention or review recommendation
- Prompt and model versions

### 19.5 Safety

Reflection cannot:

- Activate protected memory directly
- Diagnose health
- Infer protected traits without explicit policy
- Change goals, priority, permission, or security mode
- Trigger external actions
- Hide evidence
- create dependency-oriented prompts
- Treat repetition as proof

## 20. Companion context assembly

Companion requests use a declared purpose and separate context budgets for:

- Current conversation
- Stable preferences
- Active goals
- Active projects and milestones
- Owner-confirmed life events
- Communication preferences
- Recent accepted emotional context
- Relevant episodes

The Companion Service uses Memory Service APIs and cannot query stores directly. It explains materially influential memories.

## 21. Emotional-awareness lifecycle

1. Detect explicit statement or possible signal.
2. Label source as explicit or inferred.
3. Calculate confidence.
4. Apply prohibited-inference rules.
5. Choose transient context or proposed observation.
6. Assign short expiry and review policy.
7. Use only for supportive response adaptation.
8. Record use when it materially changes a response.
9. Expire automatically.
10. Apply owner correction immediately.

Mood trends require explicit enablement, multiple eligible observations, minimum evidence, and a bounded time window. They never become permanent personality traits.

## 22. Retrieval pipeline

1. Receive query and declared purpose.
2. Authenticate actor.
3. Check kill switch and memory feature state.
4. Resolve owner and security mode.
5. Determine permitted classifications and memory types.
6. Parse query without allowing retrieved content to change policy.
7. Retrieve structured PostgreSQL matches.
8. Retrieve Milvus candidates when allowed.
9. Retrieve Neo4j candidates when allowed.
10. Retrieve episodic and companion records with temporal filters.
11. Deduplicate IDs.
12. Load canonical PostgreSQL records.
13. Reauthorize every record.
14. Remove invalid, disputed, expired, deleting, and deleted records.
15. Score relevance and utility.
16. Rerank within budget.
17. Build labeled context with provenance.
18. Record access decisions.
19. Return context and explanation metadata.

## 23. Retrieval scoring

Configurable signals:

- Semantic relevance
- Exact lexical match
- Structured-field match
- Graph proximity
- Recency
- Importance
- Confidence
- Goal or project relevance
- Conversation continuity
- Source reliability

Privacy cost and uncertainty are penalties. Scores never override authorization.

## 24. Context budget

Separate budgets exist for:

- System and safety instructions
- Current owner instruction
- Recent conversation
- Durable memories
- Episodic context
- Documents
- Companion context
- Tool results

When constrained:

1. Preserve owner instruction and policy.
2. Preserve relevant recent context.
3. Prefer high-confidence, high-utility memory.
4. Use evidence-linked summaries.
5. Drop low-value context instead of critical policy.
6. Record eligible memories omitted by budget.

## 25. Retrieval explanations

For materially used memory, NOVO can show:

- Title and type
- Relevance reason
- Source
- Confidence
- Classification
- Last update
- External transmission status
- Inspect or correct link

The response shows concise explanations; Control Center shows full evidence.

## 26. Memory access policy

Inputs include:

- Owner
- Actor type and ID
- Security mode
- Purpose
- Memory type
- Classification
- Source
- Status
- Validity and retention
- Destination provider
- Requesting agent or tool
- Owner overrides
- Kill-switch state

Decisions:

- allow
- deny
- allow with redaction
- allow locally only
- require approval
- allow summary only

## 27. Classification behavior

### Public

Usable broadly under normal policy.

### Private

Default personal memory. External use requires configured provider eligibility and minimum context.

### Confidential

Requires explicit provider eligibility, strong minimization, and audited access.

### Secret

Not sent externally by default. Local access is narrowly scoped.

### Restricted

Normally excluded from model context, external embeddings, reflection, graph projection, and automation.

Classification may be raised automatically but never silently lowered.

## 28. Privacy Firewall

Before external model or embedding use:

1. Resolve permitted classifications.
2. Detect secrets and credentials.
3. Detect prohibited fields.
4. Remove unnecessary identifiers.
5. Minimize evidence.
6. Keep any redaction map in protected transient state only.
7. Record data categories and destination.
8. Reject if safe transformation is impossible.

## 29. Prompt-injection protection

- Source content is data, not policy.
- Quoted instructions are labeled untrusted.
- Extraction uses strict structured output.
- Commands in content are not executable.
- Retrieved memory cannot change permissions.
- Reflection ignores instructions embedded in history.
- Documents cannot force secret storage.
- Candidate content is sanitized.
- Suspicious sources may be quarantined.

## 30. Owner controls

Memory Center supports:

- View all lifecycle states
- Search by type, tag, source, class, and date
- Inspect provenance and revisions
- Inspect access and response use
- Edit by creating a revision
- Confirm or reject candidates
- Resolve contradictions
- Change classification, retention, and review date
- Pin or archive
- Disable vector or graph projection
- Export and delete
- Pause candidate extraction
- Disable reflection
- Disable emotional observations
- Reset companion context
## 31. Correction and revision

Owner correction is a high-priority explicit event.

Process:

1. Authenticate and authorize.
2. Lock memory.
3. Create immutable revision.
4. Record reason and actor.
5. Set current revision.
6. Mark vector and graph projections stale.
7. Publish memory.updated.
8. Refresh projections.
9. Invalidate caches.
10. Record audit evidence.

Corrections propagate to summaries and derived insights through repair jobs.

## 32. Deletion lifecycle

### 32.1 Immediate block

After authorization:

- Set status Deleting.
- Deny retrieval.
- Remove or block Redis projection.
- Invalidate context caches.
- Reject new embedding or graph jobs.

### 32.2 Physical cleanup

Workers remove:

- Milvus vectors
- Neo4j nodes and relationships
- Companion projections
- Derived summaries when required
- Export artifacts
- Search projections

PostgreSQL content is purged or cryptographically erased according to policy. Audit records deletion without preserving deleted content.

### 32.3 Source-aware deletion

When a conversation or document is deleted:

1. Remove its provenance links.
2. Identify derived memories.
3. Delete or dispute memory with no valid source.
4. Recalculate confidence when other sources remain.
5. Preserve explicit owner memory only when policy permits.
6. Refresh summaries and projections.

### 32.4 Backup disclosure

The UI distinguishes live-store deletion from encrypted backup expiry.

## 33. Retention, decay, and review

Retention depends on type, classification, source, confidence, owner setting, last use, active goal relevance, and pinning.

Decay may reduce retrieval priority but cannot alter content.

Review jobs may:

- Mark stale
- Request confirmation
- Archive
- Shorten retention
- Recalculate confidence
- Propose deletion

Pinned memory does not auto-expire but remains editable and deletable.

## 34. Events and queues

Commands:

- memory.extract_candidates
- memory.consolidate
- memory.embed
- memory.delete_projection
- memory.reflect
- memory.rebuild_graph
- memory.reconcile

Events:

- memory.candidate_created
- memory.candidate_rejected
- memory.created
- memory.updated
- memory.disputed
- memory.archived
- memory.deletion_requested
- memory.deleted
- memory.embedding_requested
- memory.embedding_completed
- memory.graph_projection_updated
- reflection.completed
- emotional_observation.created
- emotional_observation.expired
- goal.updated
- project.updated

Events use the transactional outbox and at-least-once delivery. Consumers are idempotent and schema-version aware.

## 35. Concurrency rules

- Optimistic versioning protects owner edits.
- Row locks protect consolidation and contradiction resolution.
- Candidate consolidation occurs once per policy version.
- Projection workers compare source revision.
- Late workers cannot reactivate deleted or disputed memory.
- Deletion wins over embedding and graph updates.
- Owner correction wins over reflection proposals.
- Conflicts are visible; no silent last-write-wins.
- Long-running model work occurs outside database transactions.
- A final policy and state check happens immediately before commit.

## 36. Failure behavior

| Failure | Required behavior |
|---|---|
| PostgreSQL unavailable | No durable mutation claims success |
| Redis unavailable | Reconstruct safe context or report degradation |
| Milvus unavailable | Structured retrieval continues; semantic memory is degraded |
| Neo4j unavailable | Graph reasoning is disabled |
| RabbitMQ unavailable | Outbox retains work |
| Embedding provider unavailable | Canonical memory remains; projection is pending or failed |
| Reflection model unavailable | Reflection fails without memory mutation |
| Privacy Firewall failure | External transmission is denied |
| Audit failure | Sensitive access or mutation fails closed |
| Projection deletion failure | Canonical status blocks use while cleanup retries |

## 37. Recovery and reconciliation

Scheduled checks verify:

- Active memories have a valid current revision.
- Active memories have provenance.
- Milvus vectors match active revision and model.
- Neo4j projections match source version.
- Deleted memory has no usable projections.
- Redis contains no expired protected context.
- Candidate and reflection runs are not abandoned.
- Outbox events are published or visibly pending.
- Access events reference policy decisions.
- Companion records have valid owner and source.

Repairs are idempotent, policy-checked, and audited.

## 38. Observability

Metrics:

- Candidates by source and outcome
- Acceptance, rejection, temporary, and review rates
- Consolidation latency and failures
- Duplicate and contradiction rates
- Creation and revision rates
- Retrieval latency by source
- Semantic and graph hit rates
- Reranker contribution
- Context-budget utilization
- Correction and deletion rates
- Projection lag
- Reflection cost, latency, and acceptance
- Emotional observation rejection and expiry
- Unauthorized denials
- Privacy Firewall redactions

Raw memory text never appears in metric labels.

## 39. Audit requirements

Evidence is required for:

- Creation and revision
- Classification change
- Candidate confirmation or rejection
- Dispute resolution
- Archive and deletion
- Reflection
- Emotional-observation storage
- Sensitive retrieval
- External transmission
- Semantic or graph projection
- Export
- Policy change
- Administrative repair

Audit uses IDs, hashes, categories, reasons, and outcomes rather than sensitive content.

## 40. Performance objectives

Initial measurable objectives:

| Operation | Provisional target |
|---|---|
| Redis working-context read | p95 under 50 ms |
| Structured PostgreSQL retrieval | p95 under 100 ms |
| Milvus search excluding embedding | p95 under 250 ms |
| Combined retrieval and authorization | p95 under 500 ms |
| Memory write transaction | p95 under 250 ms |
| Canonical deletion block | Effective immediately after commit |
| Projection lag | Visible and normally below five minutes |

Correctness and policy outrank latency.

## 41. Configuration

Owner controls:

- Candidate extraction enabled
- Automatic acceptance threshold
- Review rules by classification
- Retention by type
- Reflection enabled, schedule, scope, budget, and model policy
- Emotional awareness and retention
- Companion context categories
- Semantic indexing eligibility
- Graph projection eligibility
- External provider classification limits
- Context budgets
- Explanation detail
- Archive and review behavior

Configuration is versioned and audited.

## 42. Service contracts

Memory application interfaces:

- Propose candidate
- List and resolve candidates
- Create explicit memory
- Retrieve context for a declared purpose
- Get memory, sources, and revisions
- Correct or classify memory
- Archive or restore
- Request deletion
- Export memory
- Run consolidation
- Request reflection
- Resolve insight
- Rebuild semantic projection
- Rebuild graph projection
- Explain memory use

API Design owns transport endpoints. This document owns business rules.

## 43. Security tests

Required tests:

- Cross-owner access is impossible.
- Redis manipulation cannot bypass PostgreSQL.
- Milvus metadata cannot authorize content.
- Neo4j results are reauthorized.
- Credentials cannot become memory.
- Restricted memory cannot reach external models by default.
- Retrieved injection cannot alter policy.
- Emotional inference cannot authorize tools.
- Reflection cannot activate protected memory directly.
- Deleted memory cannot be retrieved during cleanup.
- Memory cannot grant approval or security mode.
- Audit failure blocks sensitive mutation.

## 44. Functional tests

- Explicit remember creates candidate and provenance.
- Duplicate does not create duplicate memory.
- Compatible update creates a revision.
- Contradiction enters Disputed or review.
- Source deletion recalculates derived memory.
- Expired memory is excluded.
- Owner correction immediately changes retrieval.
- Context budget selects correct records.
- Semantic retrieval returns canonical authorized revision.
- Graph retrieval supports safe multi-hop context.
- Consolidation retry is idempotent.
- Reflection remains reversible.
- Emotional observation expires.
- Multi-store deletion reconciles.

## 45. Quality evaluation

Measure:

- Retrieval precision and recall
- Provenance completeness
- Owner correction frequency
- False durable-memory rate
- Duplicate rate
- Contradiction detection
- Context usefulness
- Stale-memory influence
- Companion continuity
- Emotional-inference calibration
- Reflection acceptance
- Privacy and policy violations
- Cost per useful retrieved memory

Memory volume is not a success metric.

## 46. Rollout phases

### M1: Conversation continuity

PostgreSQL messages, Redis working memory, manual summaries, no automatic durable extraction.

### M2: Explicit memory

Remember command, Memory Center, provenance, revisions, classification, correction, archive, and deletion.

### M3: Semantic memory

Milvus, hybrid retrieval, PostgreSQL reauthorization, explanations, and reconciliation.

### M4: Candidate consolidation

Extraction, scoring, duplicate and contradiction detection, review queue, and low-risk consolidation.

### M5: Episodic and companion memory

Goals, projects, interests, life events, episodes, companion profile, and opt-in emotional awareness.

### M6: Reflection

Bounded scheduled reflection, insight review, pattern proposals, stale-memory review, and evaluation.

### M7: Knowledge graph

Neo4j projection, synchronization, multi-hop retrieval, rebuild, and reconciliation.

Every phase requires security, audit, deletion, dashboard, migration, backup, and restore tests.

## 47. Open decisions

1. Retention by kind and classification.
2. Automatic acceptance threshold.
3. Whether Confidential always requires review.
4. Local versus external embedding models.
5. Reranking model and privacy policy.
6. Emotional-observation default TTL.
7. Reflection schedule and default disabled state.
8. Minimum evidence for mood trends.
9. Allowed sensitive graph relationships.
10. Whether archived memory remains indexed.
11. Conversation-summary refresh strategy.
12. Explanation detail.
13. Confidence recalculation after source deletion.
14. Policy language for purposes and destinations.

Conservative defaults: explicit durable storage, short emotional retention, reflection disabled, no external Secret or Restricted processing, and owner review for sensitive inference.

## 48. Definition of done

The memory architecture is accepted when:

- Every memory type has an authority, lifecycle, policy, and deletion rule.
- Candidate extraction cannot silently create a profile.
- Consolidation is sourced, reviewable, and idempotent.
- Reflection proposes only reversible insights.
- Emotional awareness is uncertain, temporary, non-diagnostic, and non-authorizing.
- Companion context is transparent and controlled.
- Milvus and Neo4j are derived, rebuildable, and reauthorized.
- Retrieval explains materially used memories.
- Correction and deletion propagate across stores.
- Events, failure recovery, audit, metrics, and tests are specified.
- Database, Agent, RAG, Security, API, Dashboard, and Roadmap use the same states and responsibilities.

## 49. Orchestrator and Guardrails Integration

### 49.1 Tiered retrieval

Memory retrieval is selected by the Orchestrator rather than automatically running every retrieval system.

Fast path:

1. Recent Redis conversation state.
2. Cached source-linked summary.
3. Compact structured PostgreSQL lookup.
4. Minimal semantic search only if structured data is insufficient.

Deep path may add broader semantic retrieval, episodic search, RAG, graph traversal, multi-source reranking, and structured run tracking.

Graph retrieval is used only for relationship-heavy or multi-hop queries. A structured exact match stops broader retrieval when it already answers the question.

### 49.2 Interactive latency rules

- Reflection never blocks an interactive reply.
- Candidate extraction and consolidation run after the response unless explicitly requested.
- Embedding and graph projection are background consistency work.
- Broad retrieval requires a query-class justification.
- Cached summaries are used only when their source/version remains valid.
- User-facing latency and projection consistency latency are measured separately.

### 49.3 Memory Guardrails

Before retrieval: owner, purpose, classification, status, provider, and destination filters.

Before write: secret rejection, provenance, atomic claim validation, classification, contradiction detection, and sensitive-inference review.

After model extraction: strict candidate schema, evidence-reference verification, allowed type validation, confidence bounds, and deterministic duplicate checks.

Before egress: minimum content, provider eligibility, redaction, classification limit, and egress audit.

### 49.4 Free-model memory safety

Free models use smaller extraction prompts, fewer claims per request, strict structured schemas, bounded repair, and evidence-linked output. Deterministic hashing, exact matching, constraints, and source checks run before semantic/model judgment.

Long summaries from free models are not trusted without evidence references and coverage checks. Invalid output becomes Failed or review-required; it never silently becomes durable memory.

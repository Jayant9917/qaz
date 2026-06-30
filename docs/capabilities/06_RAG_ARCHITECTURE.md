# NOVO RAG Architecture

**Status:** Draft for owner review
**Version:** 0.1
**Owner:** Jay Rana
**Default mode:** Assistant Mode
**Last updated:** 2026-06-24

## 1. Purpose

Retrieval-Augmented Generation gives NOVO access to owner-approved documents and knowledge while preserving provenance, authorization, privacy, deletion, and answer traceability.

RAG must answer:

1. What evidence is relevant?
2. Is NOVO authorized to use it?
3. How does it support the answer?
4. Can the owner inspect, correct, re-index, or delete it?

RAG is a governed evidence-retrieval subsystem selected by the Orchestrator only when useful. It is not a substitute for memory, exact database queries, policy, or model reasoning.

## 2. Goals

- Safely ingest owner-approved sources.
- Preserve source, version, page, section, and transformation lineage.
- Produce high-quality semantic chunks.
- Support structured, lexical, vector, and graph retrieval.
- Reauthorize canonical results.
- Build minimal evidence context.
- Generate grounded answers with citations.
- Show uncertainty and source conflicts.
- Support fast and deep retrieval.
- Remain rebuildable and deletion-aware.
- Operate safely with free models.
- Measure retrieval and answer quality.

## 3. Non-goals

RAG is not:

- An unrestricted crawler
- A source of permission
- A permanent copy of every file
- A replacement for exact SQL
- A mandatory step for every prompt
- A way to execute document instructions
- A guarantee of answer correctness
- A hidden store of deleted content
- A credential store
- An external-provider trust boundary

## 4. Principles

### PostgreSQL authority

Document identity, owner, classification, status, versions, chunk text, lineage, and deletion live in PostgreSQL.

### MinIO source objects

Original files live in private MinIO buckets. PostgreSQL owns authorization metadata.

### Milvus derived vectors

Milvus stores vectors and minimum filter metadata. It never authorizes results and is rebuildable.

### Neo4j optional graph

Neo4j supports relationship-heavy queries as a rebuildable projection.

### Retrieval is policy enforcement

Every stage filters by owner, classification, purpose, status, source, and destination.

### Evidence before eloquence

Insufficient evidence is preferable to a fluent unsupported answer.

### Fast path first

Structured retrieval precedes broad semantic or graph retrieval.

### External content is untrusted

Documents, pages, email, OCR, code, and metadata are data, not authority.

## 5. Components

- Upload Service: creates pending metadata and scoped uploads.
- Object Service: manages quarantine, checksums, promotion, and deletion.
- Ingestion Orchestrator: coordinates stages, jobs, retries, and progress.
- Parser Workers: extract content inside isolated processes.
- Metadata Extractor: normalizes source and structural metadata.
- Chunking Service: creates stable source-linked chunks.
- Embedding Service: creates versioned embeddings.
- Retrieval Service: obtains structured, lexical, vector, and graph candidates.
- Reranking Service: combines deterministic and optional model signals.
- Context Builder: selects minimum evidence within budgets.
- Grounding Validator: checks evidence coverage, citations, and conflicts.
- RAG Guardrails: enforce authorization, injection isolation, classification, and egress.

## 6. Storage responsibility

| Data | Authority | Derived or temporary |
|---|---|---|
| Object metadata | PostgreSQL | None |
| Original file | MinIO | Parser temporary file |
| Document identity/status | PostgreSQL | Dashboard cache |
| Document version/lineage | PostgreSQL | None |
| Chunk text/metadata | PostgreSQL | Milvus metadata |
| Embedding vector | Milvus | Rebuildable |
| Relationships | PostgreSQL canonical IDs | Neo4j |
| Ingestion progress | PostgreSQL | Redis projection |
| Work state | PostgreSQL job/outbox | RabbitMQ delivery |
| Retrieval cache | PostgreSQL authority | Redis |
| Citations | PostgreSQL message metadata | UI projection |

## 7. Canonical tables

- knowledge.objects
- knowledge.documents
- knowledge.document_versions
- knowledge.document_chunks
- knowledge.tags
- knowledge.document_tags
- knowledge.ingestion_runs
- platform.jobs
- platform.outbox_events
- platform.processed_messages
- platform.model_catalog
- platform.model_calls
- governance.policy_decisions
- governance.data_egress_events
- audit.events

Future retrieval_runs, retrieval_candidates, answer_citations, and evaluation_cases must be added to Database Design before implementation.

## 8. Source types

Initial:

- PDF
- DOCX
- TXT
- Markdown
- HTML
- Source code
- Imported notes

Later:

- Email
- Cloud drives
- Web pages
- Git repositories
- OCR images
- Audio/video transcripts
- Structured datasets

Each connector declares scopes, sync direction, schedule, provenance, retention, and deletion behavior.

## 9. Document states

- pending_upload
- quarantined
- scanning
- uploaded
- parsing
- normalizing
- chunking
- embedding
- partially_ready
- ready
- failed
- superseded
- deleting
- deleted

Only Ready and policy-approved Partially Ready versions enter normal retrieval.

## 10. Ingestion flow

1. Authenticate owner.
2. Authorize upload or connector.
3. Validate quota, type, and classification.
4. Create pending document and object metadata.
5. Issue short-lived object-specific upload URL.
6. Upload into quarantine.
7. Verify size, checksum, MIME, extension, and ownership.
8. Scan malware and prohibited types.
9. Promote approved object.
10. Create immutable document version.
11. Publish ingestion command through outbox.
12. Parse in sandbox.
13. Normalize content.
14. Extract structure and metadata.
15. Create canonical chunks.
16. Validate coverage and lineage.
17. Publish embedding batches.
18. Upsert eligible vectors.
19. Optionally project authorized graph entities.
20. Mark Ready or Partially Ready.
21. Notify owner and audit.

## 11. Upload and quarantine

- Private quarantine bucket
- Opaque object key
- Maximum object size
- Archive expansion and recursion limits
- Declared/detected MIME agreement
- Extension validation
- SHA-256 checksum
- Malware scan
- No macros, scripts, or embedded object execution
- No parser network by default
- No host filesystem outside sandbox
- Filename retained only as metadata
- Timed quarantine cleanup
- Safe rejection audit

## 12. Parser architecture

Parser selection is deterministic from detected type.

Each parser records:

- Name and version
- Object and version
- Start/end time
- Page/element count
- Character count
- Warnings
- Safe error code
- Output checksum
- Extraction confidence where relevant

Parser output is untrusted and schema-validated. A crash cannot mark a document Ready.

## 13. Normalization

Normalization may:

- Normalize Unicode and whitespace
- Remove repeated headers/footers with evidence
- Preserve paragraphs, headings, lists, and tables
- Preserve code blocks and language
- Preserve page/position mapping
- Detect language and OCR origin
- Mark low-quality extraction
- Remove executable artifacts
- Preserve original source locators

Cleaning never silently rewrites meaning or removes provenance.

## 14. Metadata extraction

Required when available:

- Owner
- Document/version ID
- Filename
- Title and author
- Source type and URI
- Created/modified/import dates
- Language
- Classification
- Page and section path
- Content type
- Tags
- Parser/chunker versions
- Object checksum
- Access policy
- Retention
- Source locator

Model-derived metadata is marked inferred with confidence.

## 15. Semantic chunking

Preferred boundaries:

1. Document structure
2. Heading hierarchy
3. Paragraph
4. List/table
5. Code symbol
6. Semantic topic shift
7. Sentence
8. Token fallback

Fixed-length splitting is not the primary strategy.

Chunks must remain independently understandable while preserving parent context.

## 16. Chunk contract

Each chunk contains:

- Chunk, owner, document, and version IDs
- Ordinal
- Text and content hash
- Page range and section path
- Content type and language
- Token count
- Classification
- Source locator
- Parent/neighbor references where useful
- Embedding state
- Parser/chunker versions
- Lifecycle state

A chunk never includes unrelated text merely to inflate context.

## 17. Chunk quality checks

- Complete document coverage
- No unexplained overlaps or gaps
- Stable ordering
- Valid page and section locators
- Token limits
- Minimum useful content
- Table/code preservation
- Duplicate detection
- Classification inheritance
- Source checksum linkage
- Deterministic output for same source and versions

Failed quality checks prevent Ready state.
## 18. Embedding eligibility

A chunk may be embedded only when:

- Document/version is eligible.
- Chunk is active.
- Owner permits semantic indexing.
- Classification permits selected provider.
- Secret detection passed.
- Retention remains active.
- Required review completed.
- Chunk quality passed.

Secret and Restricted content does not go to external embedding models by default.

## 19. Embedding input and output

Input contains minimum canonical chunk text plus only metadata needed for interpretation.

Exclude:

- Credentials
- Unrelated owner context
- Audit details
- Hidden policy internals
- Rejected content
- Full document when chunk is sufficient

Every vector records chunk ID, owner, document/version, class, embedding model/version, projection version, and lifecycle state.

## 20. Milvus collection strategy

Collections are versioned by:

- Embedding provider/model
- Vector dimension
- Distance metric
- Normalization behavior
- Projection schema

Re-embedding writes a new version. NOVO verifies coverage, quality, and authorization metadata before switching the active projection.

Milvus is fully rebuildable from PostgreSQL and MinIO.

## 21. Indexing workflow

1. Select eligible pending chunks.
2. Lock or lease bounded batch.
3. Recheck policy and document state.
4. Create minimum embedding input.
5. Run Egress Guardrails.
6. Call eligible embedding model.
7. Validate vector shape and finiteness.
8. Upsert idempotently.
9. Mark chunk indexed with projection version.
10. Record usage and safe errors.
11. Publish embedding completion.
12. Reconcile batch counts.

Late workers cannot index deleted, superseded, or newly restricted chunks.

## 22. Index idempotency

Logical key:

- Chunk ID
- Chunk content hash
- Embedding version
- Projection version

Retry returns or replaces the same projection instead of creating duplicates.

## 23. Query classification

The Orchestrator classifies:

- Exact structured lookup
- Known-document lookup
- Lexical/factual query
- Semantic concept query
- Relationship/multi-hop query
- Broad synthesis
- Comparison
- Timeline
- Code lookup
- Unsupported or external-freshness query

Classification determines Fast/Deep Path and retrieval modules.

## 24. Fast-path retrieval

Use for small, well-scoped questions.

Order:

1. Recent conversation and known document context.
2. Exact document/tag/metadata lookup.
3. PostgreSQL lexical search.
4. Small vector query only if needed.
5. Canonical reload and authorization.
6. Deterministic ranking.
7. Compact evidence context.
8. Tier 1 generation and grounding validation.

Fast path avoids graph traversal, broad corpus search, model reranking, and agent planning unless escalation is justified.

## 25. Deep-path retrieval

Use for large, ambiguous, comparative, multi-source, multi-hop, or research questions.

May include:

- Query decomposition
- Multiple filtered searches
- Structured metadata constraints
- Lexical retrieval
- Vector retrieval
- Graph traversal
- Neighbor/parent expansion
- Deduplication
- Cross-encoder or Tier 2 reranking
- Evidence diversity selection
- Conflict analysis
- Iterative retrieval with bounded steps
- Durable retrieval/run trace

Deep path uses explicit budgets and stopping conditions.

## 26. Structured retrieval

Structured queries are preferred for:

- Document identity
- Tags
- Author
- Date
- Page
- Section
- Classification
- Source type
- Version
- Status
- Exact project or entity ID

Exact PostgreSQL results may eliminate the need for vector search.

## 27. Lexical retrieval

PostgreSQL full-text or equivalent lexical search supports:

- Exact terms
- Names
- Identifiers
- Error codes
- Code symbols
- Rare vocabulary
- Quoted phrases

Lexical indexes are owner- and status-filtered. Ranking includes term frequency, field weight, and structural context.

## 28. Vector retrieval

Milvus query requires:

- Owner filter
- Active projection version
- Allowed classification
- Active lifecycle state
- Optional document/source/tag filters
- Top-K bound
- Deadline

Returned IDs are candidate hints only. PostgreSQL canonical reload and reauthorization are mandatory.

## 29. Graph retrieval

Neo4j is used only when relationship or multi-hop reasoning adds value.

Examples:

- Which documents relate a project to a technology?
- What milestones depend on this goal?
- Which sources connect two concepts?

Graph results contain canonical IDs and paths. PostgreSQL reauthorizes every node and supporting chunk. Graph-only claims without canonical evidence do not enter the answer.

## 30. Hybrid retrieval

Candidate sources:

- Structured
- Lexical
- Vector
- Graph
- Recent conversation/document context

Fusion may use reciprocal-rank fusion or a tested weighted method.

Initial deterministic signals:

- Exact match
- Lexical score
- Vector similarity
- Metadata match
- Graph distance
- Recency
- Source authority
- Section importance

Fusion is evaluated on NOVO-specific queries rather than chosen by fashion.

## 31. Candidate filtering

Before reranking, remove:

- Wrong owner
- Unauthorized classification
- Deleted, deleting, superseded, or failed version
- Expired retention
- Unapproved source
- Duplicate content
- Invalid source locator
- Stale projection
- Low-quality extraction
- Content blocked by purpose/destination policy

Filtering happens both before derived search where possible and after canonical reload.

## 32. Reranking

Preferred order:

1. Deterministic constraints and exact-match boosts.
2. Lightweight deterministic fusion.
3. Optional local or eligible reranker.
4. Tier 2 LLM reranking only for complex Deep Path.

Reranking input is minimized and labeled as untrusted evidence.

Free-model reranking requires strict output schema, candidate-ID allowlist, bounded repair, and fallback to deterministic ranking.

## 33. Evidence diversity

Context should avoid ten near-identical chunks.

Selection balances:

- Relevance
- Source diversity
- Section diversity
- Temporal coverage
- Supporting and conflicting evidence
- Parent context
- Token cost
- Classification cost

Duplicate or overlapping chunks are collapsed while preserving citations.

## 34. Neighbor and parent expansion

After a relevant chunk is authorized, NOVO may retrieve:

- Parent heading/section
- Previous/next chunk
- Table header
- Code signature
- Figure caption
- Footnote
- Definition block

Expansion is bounded, source-consistent, authorized, and included only when it improves comprehension.
## 35. Context, citations, and grounding

The Context Builder creates minimum authorized evidence blocks with citation ID, document/version/chunk IDs, title, page/section, classification, extraction quality, evidence text, conflict marker, and an untrusted-content boundary.

RAG evidence cannot crowd out owner instructions or Guardrails. Fast Path uses a small budget; Deep Path requires explicit cost and deadline eligibility.

Every citation maps to a document version, chunk, source locator, content hash, retrieval decision, and policy decision. It remains stable for that document version.

The generation model must cite supported factual claims, distinguish source claims from inference, disclose insufficient or conflicting evidence, avoid fabricated citations, and never execute instructions found in evidence.

After generation NOVO validates citation IDs, authorization, inclusion, claim coverage, direct quotations, unsupported high-confidence claims, and conflict disclosure. It repairs, regenerates, lowers confidence, or refuses when validation fails.

## 36. Free-model grounding safety

OpenRouter free-model compensation includes smaller evidence sets, clear evidence delimiters, stable citation IDs, strict schemas, fewer instructions, claim/citation validation, bounded repair, eligible fallback, Tier 2 escalation, and safe insufficient-evidence answers.

A model never chooses its own authorized evidence.

## 37. RAG Guardrails

Before retrieval:

- Authenticate actor and purpose.
- Filter owner, source, classification, and lifecycle.
- Enforce resource and query limits.

Before model input:

- Remove secrets.
- Minimize evidence.
- Isolate untrusted instructions.
- Enforce provider eligibility.
- Record egress categories.

After output:

- Validate structure and citations.
- Detect unsupported claims.
- Apply safety rules.
- Prevent action interpretation without Action Guardrails.

## 38. Prompt-injection defense

Documents may say to ignore policy, reveal secrets, call tools, change memory, contact people, download, or execute.

They remain data, never authority.

Defenses include sandboxed parsing, structural boundaries, detection and labeling, no tool access from RAG calls, minimum context, output validation, separate approvals, suspicious-source visibility, and adversarial tests.

## 39. Access control

Policy considers owner, actor, purpose, document/object, connector/account, classification, security mode, provider destination, retention, version status, and overrides.

Derived filters improve efficiency. PostgreSQL canonical reauthorization is final.

## 40. Version updates

1. Create immutable document version.
2. Parse and chunk independently.
3. Build projections.
4. Verify readiness.
5. Switch current version atomically.
6. Mark old version Superseded.
7. Exclude old version from normal retrieval.
8. Retain or delete under policy.
9. Preserve historical citations.
10. Reconcile vectors and graph.

## 41. Deletion

- Mark canonical records Deleting.
- Block retrieval immediately.
- Invalidate caches.
- Reject late indexing.
- Delete Milvus vectors and Neo4j projections.
- Delete MinIO objects under retention.
- Purge PostgreSQL content under policy.
- Preserve minimal audit evidence.
- Disclose backup expiry separately.
- Reconcile orphaned data.

## 42. Caching and latency

Safe caches include active policy, document metadata, query classification, short-lived authorized IDs, source-linked summaries, non-sensitive query embeddings, and model health.

Keys include owner, purpose, policy version, document version, projection version, and classification scope.

Rules:

1. Skip RAG when current context answers.
2. Use structured lookup before vectors.
3. Filter corpus before semantic search.
4. Bound Top-K.
5. Use graph only for multi-hop value.
6. Avoid LLM reranking on Fast Path.
7. Batch embeddings asynchronously.
8. Invalidate on policy, deletion, classification, version, or kill-switch change.
9. Separate user latency from projection consistency.
10. Record escalation reason.
## 43. Performance objectives

| Operation | Provisional target |
|---|---|
| Structured lookup | p95 under 100 ms |
| Lexical retrieval | p95 under 150 ms |
| Milvus query | p95 under 250 ms |
| Fast candidate pipeline | p95 under 500 ms |
| Deep retrieval | Visible deadline and progress |
| Canonical deletion block | Immediate after commit |
| Normal projection lag | Under five minutes |

Correctness, authorization, and grounding outrank latency.

## 44. Events and jobs

Commands:

- document.ingest
- document.parse
- document.chunk
- document.embed
- document.project_graph
- document.delete_projection
- rag.retrieve_deep
- rag.reconcile
- rag.evaluate

Events:

- document.uploaded
- document.scan_failed
- document.parsed
- document.chunked
- document.embedding_requested
- document.indexed
- document.partially_ready
- document.ready
- document.failed
- document.superseded
- document.deletion_requested
- document.deleted
- rag.retrieval_completed
- rag.grounding_failed
- graph.projection_updated

Events use transactional outbox. Consumers are idempotent and schema-version aware.

## 45. Service contracts

Application interfaces:

- Request and confirm upload
- Register connector source
- Get ingestion status
- Retry failed stage
- List documents and versions
- Search documents
- Retrieve evidence for declared purpose
- Explain retrieval
- Resolve citation source
- Re-index document
- Rebuild embedding projection
- Rebuild graph projection
- Request deletion
- Export document metadata
- Run evaluation

API Specification owns transport contracts. This document owns RAG behavior.

## 46. Failure behavior

| Failure | Required behavior |
|---|---|
| PostgreSQL unavailable | No authoritative mutation or retrieval claim |
| MinIO unavailable | Metadata remains; object operations pause |
| Parser failure | Version Failed with safe retry |
| Malware scan failure | Object remains quarantined |
| RabbitMQ unavailable | Outbox retains work |
| Embedding provider unavailable | Chunks remain; projection Pending/Failed |
| Milvus unavailable | Structured and lexical retrieval continue |
| Neo4j unavailable | Graph retrieval disabled |
| Reranker unavailable | Deterministic ranking fallback |
| Model unavailable | Eligible fallback or transparent failure |
| Guardrail failure | Retrieval or egress denied |
| Citation failure | Repair, regenerate, or refuse |
| Audit failure | Sensitive operation fails closed |

## 47. Reconciliation

Scheduled checks verify:

- Object metadata matches MinIO.
- Current document version is valid.
- Chunk counts match ingestion records.
- Every chunk has a valid source locator.
- Vectors match active chunk hashes and projection version.
- Deleted and superseded chunks are not retrievable.
- Graph projections match source versions.
- Failed or abandoned runs are visible.
- Outbox events are published or pending.
- Cached results use active policy and versions.
- Historical citations still resolve.

Repairs are idempotent and audited.

## 48. Observability

Metrics:

- Uploads by type and status
- Scan and parser failure
- Parse, chunk, and embedding latency
- Chunks per document
- Token distribution
- Projection lag
- Retrieval latency by mode
- Structured, lexical, vector, and graph contribution
- Filter and reauthorization removal rate
- Reranker improvement
- Citation coverage
- Unsupported-claim rate
- Insufficient-evidence rate
- Cache hit rate
- Cost per grounded answer
- Deletion cleanup lag
- Free-model fallback and repair rate

Raw document text never appears in metric labels.

## 49. Evaluation framework

### Retrieval quality

- Precision at K
- Recall at K
- Mean reciprocal rank
- Normalized discounted cumulative gain
- Source diversity
- Authorization correctness
- Stale-result rate

### Answer quality

- Citation correctness
- Citation completeness
- Faithfulness
- Answer relevance
- Conflict disclosure
- Unsupported-claim rate
- Refusal correctness
- Owner usefulness

### Operations

- Latency
- Cost
- Projection freshness
- Failure/retry rate
- Delete completion
- Free-model fallback rate

Evaluation sets contain representative owner-approved documents plus synthetic and adversarial cases.

## 50. Required security tests

- Cross-owner retrieval denial
- Classification/provider exclusion
- Milvus metadata tampering
- Neo4j canonical reauthorization
- Prompt-injected document
- Secret embedded in source
- Unauthorized connector account
- Deleted document during retrieval
- Superseded version exclusion
- Citation access after policy change
- RAG output attempting a tool action
- Egress audit and minimization
- Audit failure behavior

## 51. Required ingestion tests

- Upload authorization and quota
- MIME/checksum mismatch
- Archive bomb
- Parser sandbox
- Malware quarantine
- Deterministic parsing/chunking
- Metadata and page locator integrity
- Table and code preservation
- Duplicate upload/version
- Idempotent retry
- Embedding class eligibility
- Projection-version switch
- Deletion during embedding
- Full projection rebuild

## 52. Required retrieval tests

- Structured lookup before semantic search
- Exact identifier and rare-term lexical search
- Vector concept retrieval
- Hybrid fusion
- Bounded Top-K
- Graph multi-hop only when useful
- Duplicate collapse
- Neighbor/parent expansion
- Fast/Deep routing
- Deterministic fallback without reranker
- Conflicting source inclusion
- Context-budget enforcement

## 53. Required grounding tests

- Valid citation resolution
- Fabricated citation rejection
- Quote verification
- Unsupported claim detection
- Insufficient-evidence response
- Conflict disclosure
- Source-claim versus inference labeling
- Free-model malformed schema
- Bounded repair
- Tier fallback
- High-stakes stricter validation

## 54. Rollout phases

### R1: Secure upload

MinIO quarantine, object metadata, scanning, parsing, status UI.

### R2: Canonical chunks

Normalization, semantic chunking, lineage, PostgreSQL search.

### R3: Semantic retrieval

Embeddings, Milvus, Fast Path filtering, canonical reauthorization.

### R4: Grounded answers

Context Builder, citations, grounding validator, evaluation set.

### R5: Hybrid Deep Path

Query decomposition, fusion, reranking, conflicts, durable traces.

### R6: Graph RAG

Neo4j projection, multi-hop queries, canonical reauthorization.

### R7: Connectors and continuous sync

Email, cloud, web, and repository connectors with scoped permissions and deletion.

Every phase requires security, deletion, observability, evaluation, dashboard, and restore tests.

## 55. Open decisions

1. Initial parser libraries.
2. Malware scanner and sandbox technology.
3. Initial embedding model and provider.
4. Local embedding timeline.
5. Chunk targets by content type.
6. Overlap policy.
7. PostgreSQL full-text configuration.
8. Milvus metric and index type.
9. Hybrid fusion method.
10. Reranker and provider policy.
11. Fast/Deep classification thresholds.
12. Citation storage tables.
13. Retrieval-run persistence.
14. OCR/table quality threshold.
15. Connector priority.
16. Web freshness and robots policy.
17. Superseded-version retention.
18. Evaluation dataset governance.

Conservative defaults: private sources, explicit upload, deterministic parsing, no external Secret/Restricted embedding, bounded Top-K, PostgreSQL reauthorization, and citation-required factual answers.

## 56. Integration requirements

Agent Architecture must consume the Retrieval Service rather than query stores directly.

API Specification must expose upload, status, search, citation, re-index, and deletion contracts.

Frontend Architecture must show source state, indexing progress, citations, conflicts, and deletion progress.

Testing Strategy must implement the security, ingestion, retrieval, grounding, and evaluation suites defined here.

Observability must expose projection lag, retrieval contribution, grounding failure, and deletion health.

Roadmaps must preserve rollout dependencies.

## 57. RAG invocation contract

RAG is a subordinate capability of the NOVO Orchestrator, not a free-floating search engine. Application clients, agents, and models must not query PostgreSQL, Milvus, or Neo4j directly.

### 57.1 Invocation conditions

The Orchestrator may invoke RAG when one or more of these conditions apply:

- Current conversation context is insufficient.
- Authorized memory alone is insufficient.
- A structured database lookup is insufficient.
- The answer requires evidence from owner documents.
- Citations or document grounding are required.
- The request requires document comparison or synthesis.
- Deep research or multi-document reasoning is required.
- The owner explicitly requests search within approved documents.

RAG must still be skipped when a cheaper authorized source fully answers the request.

### 57.2 Invocation request

The Orchestrator must provide:

| Field | Requirement |
|---|---|
| owner_id | Authenticated owner scope |
| actor_id and actor_type | Requesting identity |
| purpose | Declared retrieval purpose |
| query | Validated search question |
| retrieval_mode | fast or deep |
| classification_ceiling | Maximum eligible classification |
| provider_destination | Intended generation/reranking destination |
| token_budget | Maximum evidence tokens |
| latency_budget_ms | Retrieval deadline |
| allowed_sources | Connector/source allowlist |
| document_scope | Optional document/version/tag scope |
| citation_strictness | none, preferred, required, or claim_level |
| max_rounds | Retrieval round limit |
| correlation_id and trace_id | Observability linkage |

Missing owner, purpose, classification ceiling, or budget causes rejection rather than an unbounded default search.

## 58. RAG output contract

The Retrieval Service returns a typed response to the Orchestrator.

Required top-level fields:

- retrieval_mode
- retrieval_run_id
- query_classification
- status
- candidate_summary
- selected_evidence
- dropped_candidates_count
- grounding_warnings
- token_cost_estimate
- latency_ms
- retrieval_confidence
- projection_versions
- policy_decision_id

Each selected_evidence item contains:

- chunk_id
- document_id
- version_id
- source_locator
- citation_label
- relevance_reason
- relevance_score
- retrieval_sources
- classification
- conflict_flag
- extraction_quality
- content_hash
- evidence_text or protected content reference

Status values:

- sufficient
- partial
- insufficient
- denied
- degraded
- failed

Retrieval confidence describes evidence adequacy, not certainty that the generated answer is correct. The Orchestrator and Grounding Validator must preserve warnings and insufficiency status.

## 59. When not to use RAG

NOVO must normally skip RAG for:

- Casual chat and small talk
- Pure reasoning that does not require owner documents
- Questions already answered by the current turn
- Questions answered by recent authorized conversation context
- Exact trusted structured database lookups
- Memory-only personalization
- Real-time web questions that belong to the web/search subsystem
- Action requests that require tools rather than document evidence
- Simple calculations
- Requests where the owner explicitly excludes document access

If RAG is skipped, the Orchestrator records the chosen information source when an explanation trace is required.

RAG may be added later only when the request changes, evidence becomes necessary, or confidence falls below the response policy threshold.

## 60. Retrieval budget tiers

Budgets are hard upper bounds. The Retrieval Service may stop earlier when evidence is sufficient.

### 60.1 Fast Path budget

- Maximum one or two retrieval rounds
- Maximum eight to twelve raw candidate chunks before canonical filtering
- Maximum four to six evidence chunks in final context
- No graph traversal by default
- No LLM reranker by default
- Deterministic fusion and ranking preferred
- One bounded neighbor/parent expansion per selected source
- Strict token and latency budget
- Stop when sufficient structured or grounded evidence is found

Default provisional latency target: candidate retrieval and canonical authorization under 500 ms, excluding final answer generation.

### 60.2 Deep Path budget

- Maximum three to five retrieval rounds
- Bounded query decomposition
- Per-round Top-K and total-candidate limit
- Graph retrieval only for justified multi-hop questions
- Reranker only when deterministic ranking is insufficient
- Tier 2 model only when policy and budget permit
- Explicit overall token, cost, and deadline limits
- Durable retrieval trace

### 60.3 Stopping conditions

Stop retrieval when:

- Evidence confidence reaches the configured threshold.
- Required citation coverage is available.
- Additional rounds produce no meaningful new evidence.
- Candidate diversity stops improving.
- Token, latency, cost, or round budget is exhausted.
- Policy or source scope blocks further search.
- Owner cancellation or kill switch occurs.

Budget exhaustion returns Partial or Insufficient status; it never silently expands limits.

## 61. Initial embedding and reranking strategy

### Phase 1: eligible low-cost provider

- Use a free or low-cost eligible embedding provider through the provider-neutral gateway when owner policy allows.
- Exclude Secret and Restricted content from external embedding.
- Keep prompts/chunks small and batch asynchronously.
- Record provider, model, dimension, version, cost, and eligibility.
- Preserve full rebuild capability.

### Phase 2: local embeddings

- Move eligible embeddings to a local model for privacy and lower recurring cost.
- Re-index into a new versioned Milvus collection.
- Evaluate retrieval quality before switching.
- Keep provider fallback optional and policy-controlled.

### Phase 3: hybrid local reranking

- Add an optional local reranker for Deep Path.
- Preserve deterministic Fast Path ranking.
- Compare quality, latency, memory use, and power cost.
- Fall back safely when local inference is unavailable.

The architecture remains model- and provider-agnostic throughout all phases.

## 62. Definition of done

RAG Architecture is accepted when:

- Every source has authorization, provenance, version, and deletion behavior.
- Ingestion is sandboxed, idempotent, and observable.
- Chunking preserves stable source lineage.
- Milvus and Neo4j are derived and rebuildable.
- Fast Path avoids unnecessary retrieval.
- Deep Path has budgets and stopping conditions.
- Every candidate is canonically reauthorized.
- External content cannot change policy or execute tools.
- Answers expose citations, uncertainty, and conflicts.
- Free-model output is validated and safely degradable.
- Updates and deletions propagate across all stores.
- Failure, reconciliation, metrics, evaluation, and tests are specified.
- Downstream documents can use these contracts without redefining them.

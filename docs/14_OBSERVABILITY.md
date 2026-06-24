# NOVO Observability

**Status:** Draft for implementation
**Owner:** Jay Rana
**Updated:** 2026-06-24

## 1. Purpose

Observability enables NOVO to explain system health, performance, cost, failures, model behavior, and security events without leaking owner data.

Operational telemetry and audit evidence are separate systems with different purposes and retention.

## 2. Observability pillars

- Structured logs
- Metrics
- Distributed traces
- AI/model telemetry
- Audit evidence
- Health and synthetic checks
- Owner-facing status
- Incident runbooks

## 3. Principles

1. Correlate every meaningful operation.
2. Redact before emission.
3. No raw secrets.
4. No raw sensitive prompts by default.
5. Metrics labels are bounded.
6. Audit is not a log substitute.
7. Alerts must be actionable.
8. User-visible failures match telemetry.
9. Measure Fast and Deep Path separately.
10. Retention matches sensitivity and usefulness.

## 4. Correlation identifiers

Use where relevant:

- request_id
- trace_id
- span_id
- correlation_id
- causation_id
- owner_id or privacy-safe pseudonymous ID
- session_id
- conversation_id
- response_id
- agent_run_id
- step_id
- job_id
- model_call_id
- tool_action_id
- approval_id
- document_id
- memory_id

Do not use high-cardinality IDs as metric labels.

## 5. Structured logs

Common fields:

- timestamp
- severity
- service
- environment
- version
- event name
- request/trace IDs
- actor type
- resource type
- status/outcome
- duration
- safe error code
- retry count

Message text is concise and payload-free.

## 6. Log levels

- DEBUG: development details, disabled/minimized in production.
- INFO: lifecycle and successful significant operations.
- WARN: degraded, retry, unusual but contained state.
- ERROR: failed operation requiring investigation.
- CRITICAL: security/control/data-integrity incident.

Do not log the same failure repeatedly at every layer without value.

## 7. Redaction

Redact:

- Passwords
- Tokens
- Cookies
- API keys
- Authorization headers
- Approval/reauth tokens
- Credentials
- Private keys
- Raw prompts/responses where sensitive
- Document/memory content
- Personal identifiers not required

Redaction failures block external telemetry export.

## 8. Metrics architecture

Use OpenTelemetry-compatible metrics where practical.

Metric names include subsystem and unit.

Counters are monotonic.

Histograms use reviewed buckets.

Avoid user-controlled label values.

## 9. API metrics

- Request rate
- Error rate by safe code
- Duration
- Active requests
- Body rejection
- Rate limits
- Authentication/authorization outcomes
- SSE connections/reconnects
- WebSocket sessions
- Pagination/export volume

## 10. Orchestrator metrics

- Fast/Deep route count
- Route-classification latency
- Escalation rate
- Retrieval selection
- Model tier
- Sync/async choice
- Budget exhaustion
- Route failures
- Fast-path p50/p95/p99
- Decision explanation availability

## 11. Model metrics

- Calls by provider/model/tier
- Availability
- Latency
- Input/output/cached tokens
- Cost
- Structured-output validity
- Repair attempts
- Fallback
- Timeout
- Rate limit
- Grounding failure
- Provider health age

Free-model quality/availability is tracked separately.

## 12. Prompt metrics

- Template/version use
- Render failure
- Evaluation status
- Token size
- Activation/rollback
- Output validity by prompt version
- Quality regression

Prompt content is not a label.

## 13. Memory metrics

- Candidate outcomes
- Consolidation latency
- Duplicate/contradiction
- Creation/revision
- Retrieval latency/hit
- Correction/deletion
- Projection lag
- Reflection cost/acceptance
- Emotional observation expiry/rejection
- Access denial
- Reconciliation failure

## 14. RAG metrics

- Upload/scan/parser status
- Parse/chunk/embed latency
- Chunk/token distribution
- Projection freshness
- Fast/Deep retrieval latency
- Source contribution
- Filter/reauthorization drops
- Reranker improvement
- Citation coverage
- Grounding/unsupported claim
- Retrieval confidence
- Cost per grounded answer
- Delete cleanup lag

## 15. Agent metrics

- Run/step count
- State duration
- Plan revisions
- Approval/input wait
- Retry
- Partial success
- Cancellation
- Loop stop
- Budget use
- Worker heartbeat
- Cost per goal
- Ambiguous effects

## 16. Tool metrics

- Proposals/executions
- Denial/approval
- Success/failure/ambiguity
- Latency
- Retry/reconcile
- Idempotency hit
- Rate limit
- Credential health
- Circuit state
- Data-egress categories

## 17. Queue/worker metrics

- Queue depth
- Oldest message age
- Publish/consume rate
- Processing duration
- Retry
- Dead-letter
- Worker concurrency
- Job lease expiry
- Heartbeat
- Cancellation latency
- Outbox unpublished age

## 18. Data-service metrics

PostgreSQL:

- Connections
- Query latency
- Locks/deadlocks
- Replication/PITR
- Disk
- Vacuum
- Slow queries

Redis:

- Memory
- Eviction
- Hit/miss
- Latency
- Connections

MinIO:

- Capacity
- Object errors
- Throughput
- Replication/backup

Milvus/Neo4j:

- Query latency
- Projection count/lag
- Errors
- Capacity
- Reconciliation mismatch

## 19. Security metrics

- Login failures/lockouts
- Session revocation
- Permission denial
- Approval outcome
- Critical action
- Kill switch
- Policy-cache mismatch
- Secret detection
- Privacy Firewall block
- Egress by destination/class
- Audit failure/tamper
- Plugin/integration change
- Computer unexpected-state stop

Security metrics avoid creating sensitive profiles.

## 20. Distributed tracing

Propagate W3C Trace Context across:

- Browser/API
- Internal service calls
- Model gateway
- Tool gateway
- Outbox/RabbitMQ
- Workers
- MinIO/Milvus/Neo4j adapters

Trace spans represent meaningful boundaries, not every function.

## 21. Trace sampling

- High sample for errors and Critical actions
- Lower sample for high-volume safe reads
- Always retain required audit separately
- Tail sampling if supported
- Never sample raw secret payload
- Configurable by environment

## 22. AI telemetry and Langfuse

Langfuse may track model call, prompt version, tokens, cost, latency, evaluation, and trace relationships.

Rules:

- Local deployment preferred until privacy decision.
- Redact/minimize inputs and outputs.
- Classification controls export.
- Langfuse is not audit authority.
- Provider outage does not break core audit.
- Retention is explicit.

## 23. Audit relationship

Audit records who did what, why, under which policy, and outcome.

Telemetry diagnoses operation.

Telemetry may link to audit event ID. It never replaces or mutates audit.

## 24. Health checks

- Liveness
- Readiness
- Startup/schema compatibility
- Authenticated dependency status
- Synthetic chat
- Synthetic job
- Backup freshness
- Projection freshness
- Audit verification

Public health is minimal.

## 25. Dashboards

### Owner system dashboard

- Overall state
- Kill switch/mode
- Dependency health
- Active runs/jobs
- Pending approvals
- Recent failures
- Model usage/cost
- Backup status

### Fast Path

- Latency
- Route volume
- Model validity/fallback
- Context/retrieval use

### Deep Path

- Run/step state
- Queue age
- Approval wait
- Budget and failures

### Memory/RAG

- Candidate/index/projection
- Retrieval quality
- Grounding
- Deletion lag

### Security

- Denials
- approvals
- egress
- session
- audit integrity
- incidents

## 26. SLOs

Initial SLOs are provisional:

- API availability
- Chat Fast Path latency
- Policy decision latency
- Audit write success
- Job start delay
- Projection freshness
- Citation resolution
- Backup freshness
- Restore success
- Kill-switch propagation

Each SLO has an error budget and measurement source.

## 27. Suggested initial targets

- Fast chat response start p95 under two seconds excluding provider outage.
- Policy hot-path p95 under 50 ms.
- Audit required-write success 100 percent for protected effects.
- Kill-switch API enforcement immediate after commit.
- Worker kill-switch observation within configured checkpoint target.
- Normal projection lag under five minutes.
- Daily backup freshness when production is active.
- Zero unresolved Critical alert.

Targets are revised from evidence.

## 28. Alerts

Alert only when action is required.

Critical:

- Audit write/verification failure
- Kill-switch enforcement failure
- Credential leak
- Unauthorized access
- Database corruption/unavailability
- Backup failure beyond window
- Destructive ambiguous action

High:

- Queue age
- Disk capacity
- Projection deletion lag
- Repeated model invalid output
- Policy cache mismatch
- Worker crash loop

Warning:

- Provider degradation
- Elevated latency
- Retry increase
- Backup duration
- Evaluation regression

## 29. Alert routing

Initial personal deployment:

- Control Center
- Local notification
- Optional owner-approved email/push

Sensitive alert content remains inside authenticated UI.

Alerts deduplicate and include runbook, request/trace ID, impact, and next action.

## 30. Incident workflow

1. Alert fires.
2. Confirm impact.
3. Activate kill-switch scope if needed.
4. Preserve safe evidence.
5. Revoke sessions/credentials.
6. Contain dependency/integration.
7. Restore service safely.
8. Reconcile data/external effects.
9. Document root cause.
10. Add regression test.
11. Update runbook/SLO.

## 31. Runbooks

Required:

- PostgreSQL down/corrupt
- Redis loss
- RabbitMQ backlog
- MinIO unavailable
- Milvus/Neo4j degraded
- OpenRouter outage
- Invalid free-model output spike
- Audit failure
- Credential leak
- Failed migration
- Backup/restore
- Stuck agent/job
- Kill-switch
- Computer-control incident
- Disk full

## 32. Retention

Separate policies for:

- Application logs
- Metrics
- Traces
- AI telemetry
- Audit
- Security incidents
- Debug captures

Shorter retention for detailed operational data; longer aggregated metrics. Raw sensitive payload capture is disabled by default.

## 33. Cost observability

Track:

- Model/embedding cost
- Infrastructure storage
- Object/vector growth
- Tokens per task
- Cost per grounded answer
- Cost per completed agent run
- Free-to-paid escalation
- Backup/storage cost
- Local inference resource cost

Budgets and alerts prevent surprise cost.

## 34. Frontend status

User-facing status distinguishes:

- Operational
- Degraded
- Paused
- Awaiting approval
- Dependency unavailable
- Failed
- Partially complete
- Cancelling
- Deleted/cleanup pending

Never show success solely because an HTTP request was accepted.

## 35. Observability testing

- Log schema
- Redaction
- Metric label cardinality
- Trace propagation
- Event correlation
- Alert firing
- Alert dedupe
- Dashboard query
- SLO calculation
- Telemetry outage behavior
- Audit independence
- Retention cleanup
- Runbook drill

## 36. Definition of done

- Logs, metrics, traces, AI telemetry, and audit have clear boundaries.
- Correlation follows requests, jobs, models, tools, and workers.
- Sensitive content is redacted before emission.
- Fast/Deep behavior and free-model quality are measurable.
- Dashboards and actionable alerts exist.
- SLOs, runbooks, retention, and incident workflow are defined.
- Telemetry outage cannot disable required audit or protected controls.

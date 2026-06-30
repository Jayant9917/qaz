# NOVO Testing Strategy

**Status:** Draft for implementation
**Owner:** Jay Rana
**Updated:** 2026-06-24

## 1. Purpose

Testing proves NOVO is useful, safe, deterministic around external effects, recoverable, and faithful to its documentation.

AI output quality tests supplement rather than replace ordinary software tests.

## 2. Quality objectives

- Correct application behavior
- Owner isolation
- Policy and Guardrail enforcement
- No duplicate external effects
- Provenance and grounding
- Reliable migrations and recovery
- Fast-path latency
- Safe free-model degradation
- Accessible frontend
- Observable failures
- Reproducible releases

## 3. Test pyramid

### Unit

Pure domain logic, schemas, policies, scoring, state transitions, ranking, hashing, and redaction.

### Component

Module with real database or controlled adapters.

### Integration

Service protocols: PostgreSQL, Redis, RabbitMQ, MinIO, Milvus, Neo4j, OpenRouter mock.

### Contract

API, events, tool adapters, prompts, model structured output.

### End-to-end

Owner-visible workflows through frontend/API/workers.

### Evaluation

Retrieval, grounding, model routing, companion behavior, and safety datasets.

### Operational

Performance, resilience, backup/restore, migration, and incident drills.

## 4. Test environments

- Unit: no external network.
- Component: ephemeral service/container.
- Integration: isolated Compose profile.
- E2E: production-like synthetic environment.
- Evaluation: frozen datasets and model/provider metadata.
- Recovery: isolated restore environment.

Production data is never copied into normal tests.

## 5. Determinism

Use deterministic clocks, IDs, randomness, and mock providers where possible.

Model-dependent tests separate:

- Contract correctness
- Evaluation quality
- Live-provider smoke

CI must not fail unpredictably because a free model changed.

## 6. Fixtures and factories

Factories create:

- Owner/user/session
- Conversations/messages
- Memories/revisions/sources
- Documents/versions/chunks
- Agent runs/steps
- Tools/capabilities/integrations
- Permissions/policies/approvals
- Jobs/outbox
- Audit events
- Companion goals/observations

Fixtures default to synthetic low-sensitivity values.

## 7. Database tests

- Migrations from empty database
- Upgrade from supported versions
- Constraint violations
- Foreign keys
- Unique/idempotency
- Optimistic locks
- Row locks and races
- RLS/cross-owner
- Append-only tables
- Index existence
- Query plans at scale
- Retention/deletion
- Backup/restore

## 8. Authentication/session tests

- Valid/invalid login
- Rate limit
- Session fixation
- Rotation
- Expiry
- Logout
- Device revocation
- Global revocation
- CSRF
- Reauthentication
- Recovery
- Kill-switch control access

## 9. Policy tests

Property-test permission precedence across combinations of:

- Allow/Deny/Ask
- Specific/broad resource
- Priority
- Mode
- Classification
- Destination
- Expiry
- Approval
- Kill switch
- Safety budget

Deny and nondelegable rules must never be bypassed.

## 10. Guardrail tests

Input:

- Secrets
- Prompt injection
- Oversized payload
- Prohibited type
- Classification mismatch

Output:

- Malformed JSON
- Unknown fields
- Invalid enum/range
- Fabricated citation
- Unsafe action claim

Action:

- Permission denial
- Approval mismatch
- Idempotency collision
- Stale policy
- Revoked session

Memory/egress:

- Missing provenance
- Sensitive inference
- Restricted provider
- Redaction failure

## 11. Orchestrator tests

- Simple chat selects Fast Path
- Deep task selects Deep Path
- Structured lookup stops broader retrieval
- RAG skipped when not needed
- Correct model tier
- Cost/latency budget
- Async boundary
- Route explanation
- Eligible fallback
- No fallback privacy weakening

## 12. Model tests

Contract tests use mock model responses.

Evaluation tests cover:

- Instruction following
- Structured output
- Grounding
- Citation behavior
- Tool argument quality
- Planning
- Summarization
- Candidate extraction
- Refusal
- Free-model variance

Live smoke tests are optional/manual or scheduled, not required for every commit.

## 13. Prompt tests

- Template renders with valid variables
- Missing/unknown variable rejected
- No secret literals
- Purpose binding
- Prompt hash/version
- Injection boundaries
- Evaluation regression
- Activation/rollback
- Model compatibility

## 14. Memory tests

Use requirements from Memory Architecture:

- Explicit remember
- Provenance
- Duplicate/contradiction
- Revision
- Source deletion
- Retrieval authorization
- Semantic/graph projection
- Emotional expiry
- Reflection review
- Multi-store deletion
- Reconciliation

## 15. RAG tests

- Secure upload/quarantine
- Parser sandbox
- Deterministic chunking
- Metadata/locator
- Embedding eligibility
- Projection switch
- Structured/lexical/vector/graph retrieval
- Hybrid ranking
- RAG skip rules
- Fast/Deep budgets
- Citation/grounding
- Prompt-injected sources
- Version update/deletion
- Evaluation metrics

## 16. Agent tests

- Run/step transitions
- Plan validation
- Replanning
- Approval pause/resume
- Human input
- Worker crash/redelivery
- Cancellation
- Budget and loops
- Partial success
- Ambiguous effect
- Compensation
- Kill switch
- Restore/recovery

## 17. Tool tests

Every adapter passes a shared conformance suite:

- Manifest/schema
- Preview
- Permission
- Risk
- Approval hash
- Idempotency
- Timeout
- Retry class
- Ambiguous outcome
- Reconcile
- Result sanitization
- Credential isolation
- Revoke/disable
- Audit

## 18. API tests

- OpenAPI snapshot/compatibility
- Schema validation
- Authentication/authorization
- Pagination/filter
- Idempotency
- Concurrency/version
- Error redaction
- SSE resume/dedupe
- WebSocket limits
- Upload flow
- Rate limits
- Kill switch

## 19. Frontend tests

- Components and variants
- Loading/empty/error/degraded
- Chat streaming
- Approval consequence
- Memory/document/run views
- Citation evidence
- Session expiry
- Permission denial
- Kill switch
- Recovery mode
- Responsive layouts
- Keyboard/screen reader
- XSS/Markdown sanitization

## 20. Security abuse suite

- Website/document/email prompt injection
- Credential exfiltration request
- Model fabricates approval
- Action arguments change after approval
- Tool output injects instructions
- Stale Allow cache after Deny
- Duplicate RabbitMQ delivery
- Plugin scope expansion
- Path traversal/symlink
- SSRF
- Archive bomb
- Computer unexpected dialog
- Emotional manipulation
- Reflection sensitive inference
- Audit unavailable
- Restore replays action

## 21. Concurrency tests

- Approval double consumption
- Duplicate message
- Parallel tool execution
- Candidate consolidation race
- Memory delete versus embedding
- Document switch versus retrieval
- Job lease expiry
- Automation budget
- Kill switch during action
- Policy activation during run

Use deterministic barriers and repeated stress execution.

## 22. Property-based testing

Useful for:

- Permission precedence
- Action canonicalization/hash
- Idempotency keys
- State transitions
- Chunk boundaries
- Citation mapping
- Redaction
- Pagination cursors
- Budget accounting

## 23. Fuzzing

Fuzz:

- Parsers
- Archive handling
- API schemas
- Tool results
- Model JSON
- Markdown/HTML
- URLs and paths
- Policy documents
- Event envelopes

Crashes, hangs, excessive resources, and unsafe parsing are failures.

## 24. Performance tests

Measure:

- API/chat p50/p95/p99
- SSE concurrency
- PostgreSQL query plans
- Redis latency
- RAG Fast Path
- Milvus query
- Queue throughput/age
- Embedding batches
- Agent concurrency
- Frontend performance
- Backup/restore
- Delete reconciliation

Performance tests include resource limits and realistic data scale.

## 25. Resilience tests

Inject:

- PostgreSQL outage
- Redis loss
- RabbitMQ restart
- MinIO outage
- Milvus/Neo4j outage
- OpenRouter timeout
- Worker crash
- Disk pressure
- Network partition
- Clock skew
- Expired credential
- Audit failure

Verify documented degradation/fail-closed behavior.

## 26. Migration tests

For every migration:

- Fresh upgrade
- Prior-version upgrade
- Data backfill
- Concurrent compatible app
- Constraint validation
- Index creation
- Rollback or compensation
- Backup/restore
- No data authority conflict

## 27. Backup/restore tests

Regular drill:

1. Create representative data.
2. Backup.
3. Mutate/delete.
4. Restore isolated.
5. Verify PostgreSQL and MinIO.
6. Rebuild Milvus/Neo4j.
7. Replay safe outbox.
8. Verify audit/control state.
9. Run smoke/security tests.
10. Measure RPO/RTO.

## 28. AI evaluation datasets

Datasets are versioned, reviewed, and classified.

Categories:

- Normal chat
- Coding
- Memory extraction
- Contradiction
- Document Q&A
- Multi-document synthesis
- Citations
- Tool planning
- Refusal/safety
- Companion tone
- Emotional inference
- Adversarial injection

Expected outputs may use rubrics rather than exact text.

## 29. Evaluation gates

Define minimum thresholds for:

- Retrieval precision/recall
- Citation correctness
- Faithfulness
- Structured-output validity
- Tool argument validity
- Memory false-positive rate
- Policy violation rate zero for critical invariants
- Companion manipulation failures zero
- Latency/cost

Quality regression beyond tolerance blocks release or model activation.

## 30. Coverage

Code coverage is a signal, not the goal.

Required:

- High coverage of policy, Guardrails, state machines, idempotency, approval, deletion, and audit.
- Every incident/bug adds regression test.
- Critical branches require explicit tests.

## 31. CI pipeline

Pull request:

- Format/lint
- Type checks
- Unit
- Fast component
- Migration check
- OpenAPI/event/schema compatibility
- Secret/dependency scan

Main/nightly:

- Integration
- E2E
- Security abuse
- AI evaluation
- Performance baseline
- Reconciliation
- Backup/restore scheduled

Release:

- Full gates
- Image scan/SBOM
- Migration rehearsal
- Smoke and rollback readiness

## 32. Test data privacy

- Synthetic by default
- No production dumps
- Redact captured fixtures
- No secrets
- Expiring test credentials
- Isolated buckets/databases
- Cleanup verification
- Evaluation export approval where applicable

## 33. Flaky-test policy

- Quarantine is temporary and visible.
- Owner is assigned.
- Root cause and deadline recorded.
- Flaky security/critical test blocks release.
- Do not blindly retry to hide failures.

## 34. Test reporting

Report:

- Suite/pass/fail
- Duration
- Flakiness
- Coverage
- Evaluation deltas
- Performance deltas
- Security findings
- Migration/restore result
- Artifacts and request/trace IDs
- Release-gate status

## 35. Definition of done

- Test pyramid and environments are implemented.
- Critical invariants have deterministic tests.
- AI quality has versioned evaluation.
- Security abuse cases run automatically.
- Migrations, backup, restore, and reconciliation are tested.
- CI gates prevent unsafe release.
- Failures are reproducible and privacy-safe.

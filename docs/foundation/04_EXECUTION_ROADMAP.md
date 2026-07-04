# NOVO Execution Roadmap

**Status:** Draft for implementation
**Owner:** Jay Rana
**Updated:** 2026-06-30

## 1. Purpose

This document converts the accepted NOVO architecture into an engineering execution sequence. It defines build order, dependencies, vertical slices, milestone gates, and codebase-initialization requirements.

The Product Roadmap describes user value over time. This Execution Roadmap describes how engineering delivers it safely.

## 2. Delivery principles

1. Build one end-to-end vertical slice at a time.
2. Security, audit, deletion, and tests ship with each capability.
3. PostgreSQL is authoritative from the first release.
4. Fast Path exists before complex agents.
5. Models never directly mutate state or execute tools.
6. Start with Assistant Mode.
7. Prefer modular monolith plus separate workers.
8. Keep derived stores rebuildable.
9. Use OpenRouter free models behind provider-neutral interfaces.
10. Do not introduce Neo4j, computer control, or autonomy before their dependencies are proven.
11. The desktop assistant is the primary daily-use client; the web frontend is the Control Center.
12. Desktop voice/GUI must call governed backend APIs instead of bypassing backend permissions, audit, or tool controls.

## 3. Architecture decision gate

Before implementation begins, record provisional decisions for:

- Python and Node versions
- Package managers
- PostgreSQL version
- Redis, RabbitMQ, MinIO, and Milvus versions
- Local container runtime
- Authentication approach
- Secrets Provider for development
- OpenRouter model selection and fallback
- Embedding strategy
- Policy representation
- Repository linting and formatting
- CI provider
- Initial deployment target

Unresolved decisions use conservative defaults and remain visible in an Architecture Decision Record.

## 4. Initial repository structure

Recommended codebase:

- backend/app/api
- backend/app/identity
- backend/app/conversations
- backend/app/orchestrator
- backend/app/agents
- backend/app/memory
- backend/app/knowledge
- backend/app/tools
- backend/app/models
- backend/app/governance
- backend/app/audit
- backend/app/files
- backend/app/jobs
- backend/app/observability
- backend/app/infrastructure
- backend/workers
- backend/migrations
- backend/tests
- frontend/app
- frontend/components
- frontend/features
- frontend/lib
- frontend/tests
- desktop/app
- desktop/voice
- desktop/ui
- desktop/tests
- prompts/system
- prompts/agents
- prompts/tools
- prompts/companion
- prompts/memory
- infra/compose
- infra/config
- scripts
- docs
- research

## 5. Phase E0: Engineering foundation

Deliver:

- Python/FastAPI project
- Next.js/TypeScript project
- Shared development commands
- Environment validation
- Formatting, linting, type checks
- Unit-test harnesses
- Docker Compose base profile
- PostgreSQL and Alembic
- Structured logging and trace IDs
- Configuration and Secrets Provider interface
- Health, liveness, and readiness endpoints
- CI workflow
- Architecture dependency rules

Exit gate:

- Fresh clone starts the minimal stack.
- API and frontend health checks pass.
- Migration upgrade/downgrade tests pass.
- No secrets are committed.
- CI is green.

## 6. Phase E1: Identity and Control foundation

Deliver:

- Owner account bootstrap
- Authentication
- Session lifecycle and revocation
- User settings
- Security modes
- system_control_state
- Audit event append path
- Row-level security
- Basic Control Center shell
- Kill-switch activation/deactivation
- Rate limits and CSRF protections

Exit gate:

- Cross-owner/RLS tests pass.
- Session theft/revocation tests pass.
- Kill switch blocks protected routes.
- Audit failure blocks protected mutation.
- Recovery access remains available.

## 7. Phase E2: Conversation Fast Path

Deliver:

- Conversations and ordered messages
- Chat API and SSE streaming
- Orchestrator request classification
- Fast Path routing
- Prompt Registry minimum implementation
- Model Registry and OpenRouter gateway
- Tier 1 free-model routing
- Input and Output Guardrails
- Token, latency, and cost accounting
- Conversation UI and history

Exit gate:

- Simple chat avoids agent runs and broad retrieval.
- Invalid model output fails safely.
- Provider fallback preserves policy.
- Response latency and failure metrics exist.
- Message ordering and idempotency tests pass.

## 8. Phase E2.5: Desktop Assistant Shell and Voice Prototype

Deliver:

- Local desktop app shell
- Text input connected to existing backend chat APIs
- Assistant status states: idle, listening, thinking, transcribing, speaking, blocked, degraded
- Live transcript and response display
- Basic animation/presence surface
- Push-to-talk microphone capture wired to local transcription
- Speech-to-text adapter boundary
- Text-to-speech adapter boundary
- Stop/interruption control for playback and streaming
- Non-blocking GUI threading model for audio and backend calls
- Structured voice/backend error reporting with safe user messages and exact terminal tracebacks
- STT startup probing plus CPU fallback if the CUDA runtime is broken
- Safe local settings persistence without secrets
- Session/bootstrap flow compatible with the backend
- Safety rule: desktop cannot directly access documents, email, tools, memory, credentials, or model providers

Exit gate:

- Desktop app can send a message to NOVO backend and display the streamed answer.
- GUI remains responsive while waiting for backend responses.
- Audio and backend work do not block the main UI thread.
- Desktop app shows degraded/backend-unavailable state clearly.
- Desktop/backend error paths keep exact tracebacks in the terminal while presenting safe user-facing messages.
- Safe local settings persist backend URL, email, and window size without secrets.
- Existing web Control Center remains available for audit, permissions, settings, and kill switch.

## 9. Phase E3: Explicit Memory

Deliver:

- Redis working context
- Explicit remember command
- Durable memory core: memory.memories and memory.memory_access_events
- Memory CRUD, explicit remember, correction, archive, restore, delete, and access-event APIs
- Memory Guardrails
- Memory Center
- Correction, classification, provenance, and deletion workflows
- Access explanation
- Candidate extraction disabled by default

Implemented so far in this slice:

- Owner-scoped memory records with provenance fields
- Append-only access logging
- API routes for list/create/get/update/remember/correct/archive/restore/delete/access-events
- Integration and user-flow tests for the memory lifecycle

Still planned for later E3 slices:

- Redis working context
- Revisions, sources, tags, relations, candidates, consolidation, and reflection
- Memory guardrails and Memory Center
- Broader provenance, reconciliation, and export flows
- Candidate extraction and reflection workflows

Exit gate:

- Secrets cannot become memory.
- Provenance is mandatory.
- Correction affects retrieval immediately.
- Deletion blocks and reconciles.
- Memory export and audit work.

## 10. Phase E4: Secure Documents and RAG

Deliver:

- MinIO object lifecycle
- Quarantine and file validation
- Sandboxed parsing
- Documents, versions, and chunks
- PostgreSQL lexical search
- Embeddings and Milvus
- Fast RAG invocation/output contracts
- Citations and grounding validation
- RAG Guardrails
- Document Control Center

Exit gate:

- Prompt-injected document cannot execute or alter policy.
- Citations resolve to canonical versions.
- Cross-owner retrieval is impossible.
- Projection rebuild and deletion pass.
- RAG evaluation baseline exists.

## 11. Phase E5: Deep Orchestration

Deliver:

- Durable agent runs, steps, and decisions
- Deep Path routing
- Planning and bounded loops
- Jobs, outbox, RabbitMQ workers
- Approval pause/resume
- Tier 2 reasoning escalation
- Cancellation, heartbeat, and checkpointing
- Agent-run dashboard

Exit gate:

- Multi-step tasks resume safely.
- Worker crash does not duplicate effects.
- Budgets and deadlines stop loops.
- Decisions explain retrieval/model/tool choices.
- Kill switch stops active runs.

## 12. Phase E6: Governed Tools

Deliver:

- Tool and capability registry
- Strict schemas
- Integration accounts and vault references
- Permission evaluation
- Risk classification
- Preview and action hash
- Approval Engine
- Idempotency and reconciliation
- Initial low-risk tools
- Tool usage dashboard

Suggested first tools:

- Weather/read
- Notes/read
- Notes/create with approval policy
- Calendar/read
- Document search

Exit gate:

- Model output cannot directly execute.
- Changed arguments invalidate approval.
- Ambiguous outcomes do not retry blindly.
- Credentials never enter prompts/logs.
- Tool removal and revocation are tested.

## 13. Phase E7: Consolidation and Companion foundation

Deliver:

- Memory candidates
- Consolidation scoring
- Duplicate and contradiction handling
- Review queue
- Goals, projects, interests, life events
- Companion profile and personality settings
- Emotional observations behind opt-in
- Companion response context
- Personal development UI

Exit gate:

- Inferences are labeled and editable.
- Emotional context cannot authorize actions.
- Companion adaptation is resettable.
- Candidate retries are idempotent.
- Dependency/manipulation abuse tests pass.

## 14. Phase E8: Reflection and Automation

Deliver:

- Reflection Agent
- Scheduled bounded runs
- Insight review
- Automations and executions
- Safety budgets
- Expiry and revocation
- Notifications
- Scheduler and worker controls

Exit gate:

- Reflection only proposes reversible changes.
- Automation stops on policy/version changes.
- Safety budgets are race-safe.
- Notifications do not leak sensitive content.
- No sensitive work auto-resumes after kill switch.

## 15. Phase E9: Knowledge Graph

Deliver:

- Neo4j local profile
- Graph-sync events and worker
- Entity/relationship projections
- Canonical reauthorization
- Multi-hop RAG
- Rebuild and reconciliation
- Graph visibility in Control Center

Exit gate:

- PostgreSQL remains authority.
- Deleted/disputed content is blocked immediately.
- Full graph rebuild succeeds.
- Sensitive relationship policy passes.
- Graph retrieval demonstrates measurable value.

## 16. Phase E10: Computer Control

Deliver:

- Isolated Playwright sandbox
- Computer sessions/actions/evidence
- Observation and expected-state validation
- Step-level Guardrails
- Download quarantine
- Approval-bound external effects
- Unexpected-state stop
- Session replay and kill switch

Exit gate:

- Sandbox restrictions are tested.
- UI changes stop execution safely.
- Upload/download controls pass.
- Critical actions require exact approval.
- Host secrets are inaccessible.

## 17. Cross-cutting work in every phase

Every phase includes:

- Database migration
- API contract
- Frontend visibility
- Desktop visibility when the feature affects daily interaction
- Security threat update
- Audit events
- Observability
- Unit/integration/E2E tests
- Abuse cases
- Backup/restore implication
- Deletion/retention implication
- Documentation update
- Performance baseline

## 18. Milestone definitions

### Foundation Ready

E0 and E1 complete.

### Useful Assistant

E2, E2.5, and E3 complete.

### Knowledge Assistant

E4 complete.

### Governed Operator

E5 and E6 complete.

### Personal Companion

E7 and E8 complete.

### Advanced NOVO

E9 and E10 complete.

## 19. Definition of Ready for an epic

An epic begins only when:

- User outcome is clear.
- Owning module is identified.
- Data authority is known.
- API and event boundaries are drafted.
- Desktop and Control Center responsibilities are separated.
- Risk and permissions are classified.
- Audit and deletion behavior are defined.
- Dependencies are complete.
- Acceptance and abuse tests exist.
- Open decisions have safe defaults.

## 20. Definition of Done for an epic

- Behavior implemented
- Migrations reviewed
- Tests and security gates pass
- Audit and explanations visible
- Errors and degraded behavior implemented
- Metrics and alerts exist
- Documentation updated
- Restore/deletion tested when relevant
- No unresolved Critical vulnerability
- Owner acceptance criteria met
- Desktop behavior and Control Center visibility are both addressed when relevant

## 21. Major execution risks

| Risk | Mitigation |
|---|---|
| Scope explosion | Vertical slices and exit gates |
| Infrastructure overload | Lightweight Compose profiles |
| Free-model instability | Registry health, validation, fallback |
| Premature autonomy | Assistant Mode and phased tools |
| Memory overcollection | Explicit memory first and review |
| Security bolted on late | Controls required per phase |
| Documentation drift | Contract tests and doc ownership |
| Too many derived stores | Add only after measurable need |
| Weak evaluation | Baseline datasets before optimization |
| Solo-maintainer fatigue | Small milestones and automation |
| Desktop app bypasses governance | All real capabilities go through backend APIs |
| GUI freezes during voice/model calls | Dedicated audio/backend worker threads |

## 22. Immediate initialization backlog

1. Create backend and frontend directories.
2. Pin runtime/tool versions.
3. Add environment examples without secrets.
4. Create minimal Docker Compose profile.
5. Initialize FastAPI and Next.js.
6. Add PostgreSQL and first Alembic migration.
7. Add configuration validation.
8. Add structured logging and trace middleware.
9. Add health endpoints.
10. Add test/lint/type-check commands.
11. Add CI.
12. Create ADR template and initial decisions.
13. Implement users, sessions, and system control state.
14. Implement append-only audit foundation.
15. Build empty Control Center navigation.


## 23. Immediate desktop backlog

1. Decide desktop technology: Python CustomTkinter, PySide6, Pygame, Tauri, or Electron.
2. Create `desktop/` project scaffold.
3. Define backend client for login, health, conversations, message send, and response events.
4. Build a non-blocking desktop shell with text input and response display.
5. Add status animation states.
6. Add push-to-talk placeholder and audio adapter interfaces.
7. Add safe local config without secrets.
8. Add desktop smoke test for API client and GUI startup where practical.
9. Keep the web Control Center for permissions, audit, system state, and kill switch.

## 24. Execution roadmap acceptance

This roadmap is ready when implementation order, dependencies, phase gates, and the immediate initialization backlog are accepted, and code does not begin with a later phase while an earlier security dependency is missing.

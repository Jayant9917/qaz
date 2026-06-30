# NOVO Product Roadmap

**Status:** Draft for owner review
**Owner:** Jay Rana
**Updated:** 2026-06-30

## 1. Purpose

This roadmap describes the progression of owner value. Engineering sequence and release gates are defined in 04_EXECUTION_ROADMAP.md.

Dates should be assigned only after foundation estimates and capacity are known. Scope and exit criteria matter more than fictional deadlines.

## 2. Product strategy

NOVO evolves through these identities:

1. Trusted private chat assistant
2. Local desktop assistant with voice/presence
3. Memory-enabled personal assistant
4. Grounded personal knowledge assistant
5. Governed operator
6. Personal AI companion
7. Bounded automation platform
8. Advanced local-first personal AI OS

Each stage must remain useful independently.

## 3. Release P0: Foundation

Owner value:

- Secure local access
- Visible system state
- Reliable startup and recovery

Scope:

- Authentication and sessions
- Assistant Mode
- Control Center shell
- Audit foundation
- Kill switch
- Configuration and secrets
- Health and backup basics

Exit:

- Owner can log in, inspect status, revoke sessions, and stop protected work.
- Cross-owner and recovery tests pass.

## 4. Release P1: Fast conversational NOVO

Owner value:

- Responsive daily conversation
- Persisted chat history
- Cost-controlled free-model access

Scope:

- Chat UI
- SSE streaming
- Orchestrator Fast Path
- Model and Prompt Registries
- OpenRouter Tier 1
- Input/Output Guardrails
- Conversation search and settings

Exit:

- Normal chat is fast and does not create heavy agent runs.
- Model failures degrade safely.
- Usage, cost, and routing are visible.

## 5. Release P1.5: Desktop Assistant

Owner value:

- NOVO feels like a real local assistant instead of only a browser dashboard.
- The owner can talk or type to a dedicated desktop app.
- The assistant can show listening, thinking, speaking, blocked, and degraded states.

Scope:

- Desktop app shell
- Backend health/session connection
- Text chat through existing backend APIs
- Streaming response display
- Push-to-talk or microphone button
- Speech-to-text and text-to-speech adapter boundaries
- Basic assistant animation or presence surface
- Non-blocking GUI/audio/backend threading

Exit:

- Desktop app can ask NOVO a question and display the answer.
- Desktop app remains responsive during backend/model waits.
- Desktop app does not directly access documents, email, tools, memory, credentials, or model providers.
- Web Control Center remains available for settings, permissions, audit, and kill switch.

## 6. Release P2: Memory-enabled assistant

Owner value:

- NOVO remembers deliberately selected facts and preferences.

Scope:

- Short-term context
- Explicit long-term memory
- Memory Center
- Provenance and revisions
- Correction, archive, export, deletion
- Classification and access explanations

Exit:

- Owner fully controls what NOVO remembers.
- Secrets cannot become memory.
- Corrections and deletion propagate.

## 7. Release P3: Personal knowledge assistant

Owner value:

- Upload documents and receive grounded answers with citations.

Scope:

- Secure document upload
- Parsing and chunking
- PostgreSQL lexical search
- Milvus semantic retrieval
- Fast/deep RAG
- Citations and grounding
- Document Center

Exit:

- Owner can trace every answer to source.
- Prompt-injected sources cannot control NOVO.
- Retrieval quality baseline is accepted.

## 8. Release P4: Governed operator

Owner value:

- NOVO completes multi-step work without hiding actions.

Scope:

- Deep Path agent runs
- Tool Registry
- Initial read tools
- Approval Engine
- Permission Center
- Scoped integrations
- Jobs/workers
- Run explanations

Exit:

- Every external effect is previewed, governed, idempotent, and audited.
- Kill switch stops active work.
- No model output directly executes.

## 9. Release P5: Practical tools

Owner value:

- NOVO assists with notes, calendar, documents, email drafts, search, GitHub, and coding workflows.
- Desktop assistant can present tool results naturally while the backend governs access.

Scope expands capability by capability, not by giving broad application access.

Each tool ships with:

- Narrow scopes
- Permission defaults
- Risk model
- Preview
- Approval
- Reconciliation
- Dashboard history
- Revocation

## 10. Release P6: Companion foundation

Owner value:

- Continuity across goals, projects, interests, milestones, and communication style.

Scope:

- Memory candidates and consolidation
- Goals/projects/life events
- Companion profile
- Personal development support
- Opt-in emotional awareness
- Personality controls
- Review and reset

Exit:

- Companion behavior is transparent and non-manipulative.
- Inference is labeled, temporary where appropriate, and editable.
- Owner-defined goals remain authoritative.

## 11. Release P7: Reflection and automation

Owner value:

- NOVO helps identify patterns and runs bounded recurring workflows.

Scope:

- Reflection Agent
- Insight review
- Automations
- Safety budgets
- Scheduling
- Notifications
- Expiry and pause

Exit:

- Reflection only proposes reversible updates.
- Automations stop on policy/budget changes.
- Owner sees every run and can revoke it.

## 12. Release P8: Knowledge graph

Owner value:

- NOVO understands relationships among projects, goals, documents, technologies, people, and events.

Scope:

- Neo4j projection
- Entity relationships
- Graph-assisted retrieval
- Multi-hop answers
- Graph inspection and correction

Exit:

- Graph adds measurable value.
- PostgreSQL authorization remains final.
- Graph is rebuildable and deletion-aware.

## 13. Release P9: Advanced voice

Owner value:

- More natural hands-free interaction beyond the P1.5 prototype.

Scope:

- Speech-to-text
- Text-to-speech
- Push-to-talk
- Wake word later
- Voice identity confidence
- Spoken approvals only where risk policy permits
- Conversation handoff among clients

Exit:

- Voice follows the same permission and audit model.
- Sensitive actions never rely on uncertain voice identity alone.

## 14. Release P10: Computer interaction

Owner value:

- NOVO can observe and perform constrained browser/GUI work.

Scope:

- Playwright sandbox
- Guided browser actions
- Downloads and uploads
- Evidence/replay
- Step approvals
- Unexpected-state stop
- Later computer-use reasoning

Exit:

- Sandbox and kill-switch tests pass.
- Critical actions remain explicitly approved.
- Host secrets and unrelated applications remain inaccessible.

## 15. Release P11: Local and offline intelligence

Owner value:

- Improved privacy, resilience, and recurring cost.

Scope:

- Local embeddings
- Local reranker
- Local model gateway
- Offline chat/memory/RAG subset
- Provider outage fallback
- Hardware-aware routing

Exit:

- Local routes meet minimum quality and security.
- Private classifications remain local.
- Switching providers does not change product behavior.

## 16. Future directions

- Mobile applications
- Wearable integration
- Smart home
- Multi-agent collaboration
- Advanced knowledge graph
- Personal digital twin for simulation
- Screen understanding
- Shared household profiles with isolation
- Plugin ecosystem with strict trust controls

Future features never weaken owner control.

## 17. Product health metrics

- Weekly useful tasks completed
- Owner-confirmed time saved
- Grounded-answer usefulness
- Memory correction/deletion rate
- Approval modification/rejection rate
- Tool success and ambiguous-outcome rate
- Automation intervention rate
- Fast-path latency
- Desktop response latency and GUI responsiveness
- Cost per useful task
- Kill-switch and privacy incidents
- Companion feature opt-out/reset rate
- Restore-test success

Engagement time alone is not success.

## 18. Roadmap decision rules

Advance when:

- Current release is genuinely useful.
- Security gates pass.
- Operational burden is acceptable.
- Owner trusts the capability.
- Dependencies are stable.
- Evaluation demonstrates value.

Delay or remove when:

- Capability adds complexity without value.
- Privacy cannot be controlled.
- Free-model quality is insufficient.
- Maintenance cost exceeds personal value.
- A simpler deterministic workflow works better.

## 19. Definition of roadmap success

NOVO succeeds when it becomes a trusted daily system that saves time, improves recall and organization, supports growth, and performs approved work transparently without making the owner less informed, less private, or less in control.

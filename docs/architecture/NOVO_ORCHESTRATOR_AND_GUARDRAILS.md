# NOVO Orchestrator and Guardrails

**Status:** Draft for implementation
**Owner:** Jay Rana
**Version:** 0.1
**Updated:** 2026-06-24

## 1. Purpose

This is the central runtime contract for request orchestration, fast/deep routing, guardrail enforcement, model selection, OpenRouter usage, performance, and execution boundaries.

NOVO is a fast, memory-first, policy-governed AI system with explicit orchestration and a strict separation between interactive answers and deep workflows.

## 2. Why these subsystems exist

Without an Orchestrator, every request risks becoming an expensive agent workflow.

Without Guardrails, model output can become an unsafe shortcut to tools, memory mutation, or data egress.

The Orchestrator decides what work is useful. Guardrails and Governance decide what work is permitted.

## 3. Runtime flow

Request enters API.

Orchestrator classifies request.

Guardrails validate input and permitted context.

Orchestrator selects Fast Path or Deep Path.

Model Router selects an eligible model from Model Registry.

Prompt Registry supplies an approved version.

Output Guardrails validate result.

If an action is proposed, Action Guardrails and Approval Engine evaluate it.

Durable effects commit through application services, audit, jobs, and outbox.

## 4. Fast path

Use for:

- Normal conversation
- Follow-up questions
- Simple explanations
- Small coding help
- Compact memory lookup
- Lightweight summarization
- No-tool answers
- Bounded safe read-only tools

Pipeline:

1. Authenticate and load active control state.
2. Classify intent and risk.
3. Load recent Redis context and valid cached summary.
4. Perform compact structured lookup only when useful.
5. Apply input Guardrails.
6. Select Tier 1 eligible model.
7. Validate output.
8. Stream response.
9. Schedule optional non-blocking candidate extraction after response.

Fast path avoids broad memory search, graph traversal, reflection, full planning, and heavy audit joins.

## 5. Deep path

Use for:

- Multi-step tasks
- Tool-heavy workflows
- Approval-required actions
- Long research
- Large document synthesis
- Complex RAG
- Graph reasoning
- Memory consolidation
- Reflection
- Automation
- Export and rebuild

Pipeline:

1. Create durable agent run.
2. Classify risk, data, latency, and cost.
3. Build targeted retrieval plan.
4. Run Guardrails before each retrieval source.
5. Create structured steps and decisions.
6. Select Tier 2 model when justified.
7. Validate every output and proposed action.
8. Pause for approvals.
9. Move long work to jobs/workers.
10. Commit effects with outbox and audit.
11. Return progress and final explanation.

## 6. Orchestrator responsibilities

- Intent and request classification
- Fast/deep routing
- Sync/async routing
- Retrieval-source selection
- Context budget allocation
- Tool-necessity decision
- Agent-run necessity decision
- Model tier and eligibility request
- Prompt purpose selection
- Cost and deadline enforcement
- Run, step, decision, and trace creation
- Failure and fallback coordination
- Background-job routing

The Orchestrator does not grant permission, resolve approval, retrieve secrets directly, or execute tools directly.

## 7. Guardrails responsibilities

### 7.1 Input Guardrails

- Secret and credential detection
- Prompt-injection detection
- Untrusted instruction isolation
- Classification filtering
- Provider eligibility
- Context minimization
- Input size and type limits

### 7.2 Output Guardrails

- JSON and schema validation
- Allowed enum and field validation
- Unsupported-claim detection for sensitive actions
- Tool argument validation
- Unsafe content handling
- Repair, fallback, refusal, or review routing

### 7.3 Action Guardrails

- Tool and capability permission
- Integration and account scope
- Resource and destination scope
- Risk and security mode
- Approval requirement and action-hash binding
- Idempotency
- Safety budget
- Kill-switch and session state
- Final pre-execution policy recheck

### 7.4 Memory Guardrails

- Secret rejection
- Provenance requirement
- Atomic candidate schema
- Classification
- Confidence bounds
- Duplicate and contradiction checks
- Sensitive inference review
- Retrieval reauthorization
- Deletion and dispute blocking

### 7.5 Egress Guardrails

- Provider/destination eligibility
- Allowed classification
- Redaction and minimization
- Data-category calculation
- Policy-decision linkage
- Egress audit
- Fail closed on unknown destination

## 8. Critical invariants

- No model output directly mutates state.
- No model output directly executes a tool.
- No retrieved content changes policy.
- No fast path bypasses Guardrails.
- No fallback selects a less eligible provider.
- No cached policy survives a version or kill-switch mismatch.
- No free-model parse failure becomes an action.
- No deep workflow hides approval-bound effects.

## 9. Model routing

### Tier 1: fast default

For chat, reformulation, simple coding, lightweight classification, summaries, and low-risk extraction drafts.

### Tier 2: stronger reasoning

For hard debugging, contradiction resolution, synthesis, complex planning, document reasoning, and safety-sensitive interpretation.

### Tier 3: local/private future

For offline work, provider outages, and Secret or Restricted local-only processing.

Routing inputs:

- Task capability
- Complexity
- Latency target
- Context size
- Classification
- Provider eligibility
- Structured-output reliability
- Tool-output reliability
- Health and availability
- Observed quality
- Cost and owner budget
- Fallback policy

## 10. OpenRouter initial strategy

OpenRouter is the initial provider gateway because NOVO prioritizes cost control and free-model experimentation during Version 1.

OpenRouter is not the trust boundary. NOVO owns:

- Authentication
- Memory authorization
- Classification
- Privacy filtering
- Prompt construction
- Output validation
- Tool authorization
- Audit and egress records

The Model Gateway remains provider-neutral for local models, OpenAI, Anthropic, Gemini, and other future providers.

## 11. Free-model constraints

Expected limitations:

- Variable quality
- Fluctuating latency
- Availability changes
- Weak structured output
- Unreliable tool arguments
- Reduced long-context performance
- Higher hallucination risk
- Provider-side model replacement

Compensations:

- Smaller prompts and context
- Strict schemas
- Deterministic preprocessing
- Bounded validation and repair
- Health-aware fallback
- Evidence-linked summaries
- Independent action validation
- Safe refusal or degradation
- Never asking one model to own the entire workflow

## 12. Execution routing matrix

| Request type | Path | Retrieval | Tier | Tools | Behavior |
|---|---|---|---|---|---|
| Simple chat | Fast | Recent context | 1 | No | Lowest latency |
| Follow-up | Fast | Recent context/summary | 1 | No | No agent run |
| Coding explanation | Fast then escalate | Optional docs | 1 then 2 | Optional | Avoid heavy planning |
| Exact memory | Fast | Structured first | 1 | No | Semantic only if needed |
| Document Q&A | Fast or Deep | Targeted chunks | 1 or 2 | Optional | Size/complexity based |
| Multi-step task | Deep | Targeted multi-source | 2 | Yes | Tracked run |
| Approval action | Deep | Minimum necessary | 2 | Yes | Pause for approval |
| Ingestion/embedding | Async Deep | Job data | Background | Worker | Never block chat |
| Consolidation/reflection | Async Deep | Policy-scoped history | 2/background | No external effect | Reviewable |
| Graph reasoning | Deep | Graph plus canonical reload | 2 | Optional | Multi-hop only |

## 13. Latency and performance rules

1. Answer directly from valid current context when possible.
2. Try structured lookup before semantic retrieval.
3. Use semantic retrieval only when structured data is insufficient.
4. Use graph retrieval only for multi-hop questions.
5. Prefer deterministic ranking before LLM reranking.
6. Avoid tools when no external effect or fresh external data is needed.
7. Avoid agent runs for simple responses.
8. Keep hot-path policies compiled, versioned, and safely cached.
9. Stream validated response output where possible.
10. Separate response latency from background consistency.

## 14. Sync and async boundaries

Synchronous:

- Authentication
- Control-state check
- Request classification
- Fast policy decision
- Compact retrieval
- Prompt sanitation
- Model response streaming
- Output validation
- Approval create/resolve

Asynchronous:

- Ingestion and parsing
- Embeddings
- Graph projection
- Candidate consolidation
- Reflection
- Long research
- Export
- Rebuild and reconciliation
- Long automation
- Analytics aggregation

Async work returns a durable job ID and visible progress.

## 15. Failure and fallback

| Failure | Behavior |
|---|---|
| Tier 1 unavailable | Eligible Tier 1 fallback, then Tier 2 only if policy/cost permits |
| Invalid output | Repair once or bounded times, fallback, then safe failure |
| Tool JSON invalid | Never execute; validate, repair, or request clarification |
| Policy cache stale | Reload authoritative version or fail closed |
| Redis unavailable | Authoritative fallback where safe |
| Retrieval unavailable | Answer only from verified context and disclose limitation |
| OpenRouter unavailable | Eligible provider/local fallback or transparent error |
| Guardrail failure | Protected operation denied |
| Audit failure | Sensitive action denied |
| Deadline exceeded | Cancel/defer to async and report state |

## 16. OpenClaw design boundary

NOVO may borrow local-first responsiveness, provider neutrality, tool abstraction, multi-channel direction, automation mindset, and practical routing.

NOVO rejects broad default permissions, one omnipotent agent, mixed reasoning/unrestricted execution, plugin trust by default, and autonomous bypass of durable policy.

See OPENCLAW_NOTES.md.

## 17. Open decisions

1. Fast-path classification implementation: deterministic rules, compact model, or hybrid.
2. Tier 1 free-model minimum quality threshold.
3. Maximum repair attempts.
4. Fast-path latency objective by request type.
5. Policy cache TTL and invalidation mechanism.
6. Whether model health is active probing or passive observation.
7. Tier 2 cost escalation policy.
8. Streaming validation strategy.
9. When a fast request may be upgraded mid-flight.
10. Whether degraded responses may be enriched asynchronously.

## 18. Definition of done

- Every request receives an explicit path decision.
- Simple requests avoid unnecessary agent/retrieval work.
- Protected operations pass every required Guardrail stage.
- Free-model output cannot directly create external effects.
- Model fallback preserves privacy and classification eligibility.
- Hot-path governance is measured and safely cached.
- Background work never blocks ordinary chat unnecessarily.
- Run and decision traces explain deep-path behavior.
- Failure and fallback behavior is deterministic and testable.

# NOVO Agent Architecture

**Status:** Draft for owner review
**Owner:** Jay Rana
**Updated:** 2026-06-24

## 1. Purpose

This document defines how NOVO classifies, plans, executes, pauses, resumes, cancels, and explains multi-step work.

The Agent Engine is not the entry point for every request. The Orchestrator invokes it only when Deep Path capabilities are justified.

## 2. Responsibilities

- Execute bounded multi-step goals
- Maintain durable run state
- Create validated plans and steps
- Request authorized context
- Propose typed tool actions
- Pause for approvals
- Route long steps to workers
- Recover from interruption
- Enforce budgets and deadlines
- Explain decisions and outcomes

## 3. Non-responsibilities

Agents do not:

- Authenticate users
- Grant permissions
- Resolve their own approvals
- Retrieve secrets directly
- Query storage implementations directly
- Execute provider adapters directly
- Change security mode or policy
- Disable audit or Guardrails
- Treat model output as executable authority

## 4. Runtime hierarchy

- Orchestrator: chooses Fast/Deep Path and required capabilities.
- Agent Engine: manages durable Deep Path workflow.
- Planner: proposes bounded steps.
- Step Executor: invokes application services.
- Tool Gateway: validates and executes governed capabilities.
- Workers: perform asynchronous steps.
- Guardrails and Policy: authorize every protected boundary.
- Audit: records decisions and effects.

## 5. Agent types

### Task Agent

General bounded multi-step execution.

### Research Agent

Multi-source RAG and synthesis without external side effects by default.

### Coding Agent

Code analysis, edits, tests, and repository operations within workspace policy.

### Reflection Agent

Produces reviewable memory insights; never directly changes protected memory.

### Companion Agent

Coordinates goals, projects, tone, and continuity through governed services.

### Automation Agent

Runs an approved workflow under schedule, expiry, and safety budgets.

### Computer Use Agent

Plans and observes sandboxed GUI work. Computer Control Layer performs validated actions.

Agent types are capability profiles, not unrestricted identities.

## 6. Fast Path boundary

Fast Path does not create a durable agent run unless escalation occurs.

Use Fast Path for normal chat, follow-ups, simple code help, exact memory lookup, lightweight RAG, and no-effect responses.

Escalate when the request requires multi-step state, tools, approvals, broad retrieval, async work, durable progress, or complex recovery.

## 7. Deep Path entry contract

The Orchestrator supplies:

- Owner and actor
- Goal
- Trigger and source
- Security mode
- Policy snapshot
- Classification ceiling
- Allowed capabilities
- Retrieval plan
- Model tier ceiling
- Token/cost/time budgets
- Deadline
- Correlation and trace IDs
- Approval strategy
- Cancellation state

Missing security context causes rejection.

## 8. Run state machine

States:

- created
- classifying
- planning
- running
- awaiting_approval
- awaiting_input
- queued
- paused
- cancelling
- cancelled
- succeeded
- partially_succeeded
- failed
- expired

Only defined transitions are allowed. Terminal runs cannot resume without a new run.

## 9. Step state machine

- pending
- ready
- running
- awaiting_approval
- awaiting_input
- queued
- retry_wait
- succeeded
- skipped
- cancelled
- failed
- compensated

Step sequence and parent relationships are durable.

## 10. Planning

The Planner creates a structured plan with:

- Step purpose
- Required capability
- Inputs and output schema
- Dependencies
- Risk
- Retrieval need
- Approval checkpoint
- Sync/async choice
- Retry safety
- Deadline and budget
- Completion test
- Compensation when possible

Plans are model proposals validated by deterministic rules.

## 11. Plan validation

Reject or revise plans that:

- Use undeclared capabilities
- Exceed budget or deadline
- Skip required approval
- Access unauthorized resources
- Duplicate an effect
- Depend on missing outputs
- Contain unbounded loops
- Ask models to execute directly
- Hide external transmission
- Lack success criteria
- Conflict with kill switch

## 12. Adaptive planning

NOVO may replan after new information, failure, denial, or changed state.

Replanning:

- Preserves completed effects
- Cannot change approved material arguments
- Re-evaluates policy
- Records reason and alternatives
- Respects remaining budget
- Never converts denial into a workaround
- Requests new approval for changed action

## 13. Context acquisition

Agents request context through services:

- Conversation Service
- Memory Service
- Retrieval Service
- Companion Service
- Tool read capabilities

Each request declares purpose, scope, classification ceiling, token budget, and destination.

Agents do not query Redis, PostgreSQL, Milvus, Neo4j, or MinIO directly.

## 14. Model use

The Model Router selects from the Registry using capability, context, privacy, health, latency, quality, and cost.

- Tier 1 for classification, reformulation, and simple steps.
- Tier 2 for complex planning, debugging, contradictions, and synthesis.
- Tier 3 future local/private processing.

Free-model output receives strict schema validation and bounded repair.

## 15. Prompt use

Prompt Registry provides immutable approved versions for planner, executor, research, coding, reflection, companion, and computer-use purposes.

Every model call records prompt version and hash.

Agents cannot edit active prompts.

## 16. Tool proposal contract

A proposal contains:

- Tool and capability
- Integration/account
- Typed arguments
- Resource and destination
- Expected effect
- Risk
- Idempotency key
- Preview requirement
- Reason
- Run and step IDs

Tool Gateway owns validation and execution.

## 17. Approval pause and resume

When approval is needed:

1. Persist run and step state.
2. Create exact action preview/hash.
3. Set awaiting_approval.
4. Notify owner.
5. Release worker resources.
6. On response, lock approval and run.
7. Recheck policy, state, expiry, and hash.
8. Resume exact step or end safely.

Approval expiry does not imply rejection of the entire goal; the plan may request owner direction.

## 18. Human input

Clarification requests include:

- Missing decision
- Safe options
- Consequence of each option
- Current run state
- Expiry if applicable

Agents should not ask unnecessary questions when safe defaults are defined.

## 19. Async execution

Long work becomes platform.jobs and RabbitMQ commands.

Workers:

- Lease jobs
- Heartbeat
- Check cancellation and kill switch
- Execute bounded work
- Commit durable outcome before acknowledgment
- Support idempotent redelivery
- Save safe failure detail
- Publish events through outbox

## 20. Budgets

Every run has limits for:

- Steps
- Model calls
- Input/output tokens
- Cost
- Wall-clock time
- Tool calls
- External actions
- Retrieval rounds
- Files/records affected
- Recipients/destinations
- Retry attempts

Budget exhaustion pauses, degrades, or fails transparently. It never silently expands.

## 21. Loop prevention

- Maximum plan revisions
- Maximum repeated identical step
- No-progress detection
- Duplicate action-hash detection
- Deadline
- Cost ceiling
- Repeated failure circuit breaker
- Owner cancellation
- Kill-switch checkpoints

## 22. Retry and compensation

Retry only when failure classification permits it.

- Idempotent read: bounded retry.
- Idempotent write: retry with stable key.
- Ambiguous external effect: reconcile first.
- Non-idempotent effect: no blind retry.
- Policy denial: no retry workaround.
- Validation failure: bounded repair or clarification.

Compensation is a new governed action, not a database rollback fantasy.

## 23. Failure model

Failure classes:

- validation
- authorization
- approval
- dependency
- timeout
- provider unavailable
- ambiguous effect
- budget
- cancellation
- guardrail
- internal invariant

Runs report succeeded, partially_succeeded, failed, or cancelled with completed effects and unresolved items.

## 24. Cancellation

Cancellation is durable and checked:

- Before each step
- Before model calls
- Before retrieval
- Before tool execution
- During long workers
- Before external mutation
- Before commit where safe

Cancellation cannot undo completed external effects; NOVO reports them and may propose compensation.

## 25. Memory interaction

Agents may propose memory candidates through Memory Service.

They cannot directly create Active memory, lower classification, resolve contradiction, or delete evidence.

Reflection and companion behavior follows Memory Guardrails.

## 26. RAG interaction

Agents use the RAG invocation and output contracts.

Research uses bounded rounds, citations, conflict handling, and grounding warnings.

Retrieved document instructions never become agent instructions.

## 27. Companion behavior

Companion Agent uses owner-controlled profile, goals, projects, and permitted emotional context.

It cannot use emotional inference to obtain approval, alter priorities, or encourage dependency.

## 28. Computer use

Computer Use Agent creates typed steps.

Computer Control Layer validates expected UI state, sandbox scope, approval, and evidence.

Unexpected state stops execution and returns control to the plan.

## 29. Automation

Automation runs carry workflow version, policy version, schedule, expiry, and safety budgets.

Changed policy, expired authorization, or kill switch prevents execution.

## 30. Multi-agent future

Multi-agent collaboration is deferred.

When introduced:

- One Orchestrator owns the goal.
- Agents have separate capability profiles.
- Delegation is explicit and traced.
- No shared unrestricted secret context.
- Sub-results are untrusted until validated.
- Budgets apply globally and per agent.
- Cyclic delegation is prohibited.

## 31. Events

- agent.run_created
- agent.plan_created
- agent.step_started
- agent.awaiting_approval
- agent.awaiting_input
- agent.step_completed
- agent.step_failed
- agent.run_paused
- agent.run_cancelled
- agent.run_completed
- agent.run_failed
- agent.budget_exhausted

Events use outbox and contain no secret payloads.

## 32. Observability

Track:

- Fast-to-Deep escalation
- Run/step latency
- Planning revisions
- Model tier/fallback
- Tool proposals and outcomes
- Approval wait
- Retry and ambiguous effects
- Budget use
- Cancellation propagation
- Worker heartbeat
- Partial success
- Cost per completed goal

## 33. Security requirements

- Owner isolation
- Purpose-scoped retrieval
- Strict tool schemas
- No direct model execution
- Guardrails at every boundary
- Final pre-effect policy recheck
- Secrets Provider only
- Kill-switch compliance
- Append-only decisions/audit
- Prompt injection tests
- Free-model malformed-output tests

## 34. Required tests

- Fast request avoids run
- Escalation creates correct context
- Valid and invalid state transitions
- Plan capability validation
- Approval pause/resume
- Changed action invalidation
- Worker crash/redelivery
- Cancellation at each checkpoint
- Budget exhaustion
- Ambiguous tool outcome
- Policy change mid-run
- Kill switch
- Memory and RAG authorization
- Prompt injection
- Partial success and compensation
- Multi-step restore/recovery

## 35. Rollout

A1: Durable runs and state machines.
A2: Deterministic steps and async workers.
A3: Validated model planning.
A4: Approval-bound tools.
A5: Research and coding profiles.
A6: Reflection, companion, and automation.
A7: Computer Use Agent.
A8: Carefully bounded multi-agent collaboration.

## 36. Open decisions

- Planning schema
- Deterministic versus model classification boundary
- Maximum default steps
- Checkpoint granularity
- Compensation catalog
- Tier 2 escalation policy
- Run retention
- Human-input expiry
- Multi-agent timeline
- Coding workspace permissions

## 37. Definition of done

- Simple chat does not require agents.
- Deep runs are durable, bounded, resumable, and cancellable.
- Plans and outputs are validated.
- Every protected boundary uses Guardrails.
- Actions are permissioned, approved, idempotent, and audited.
- Failures and partial effects are visible.
- Memory/RAG contracts are respected.
- Free-model failures cannot create effects.
- Tests cover transitions, races, recovery, and abuse.

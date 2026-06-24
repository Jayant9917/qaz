# Agent Architecture

Describe the design of agents, orchestration patterns, and decision workflows.

## Required Runtime Decisions

This file remains a placeholder for the full Agent Architecture. The following accepted requirements are binding.

### NOVO Orchestrator

The Orchestrator sits above agent execution. It classifies the request, selects Fast or Deep Path, chooses retrieval sources, requests a model tier, decides sync versus async, and creates run/step/decision traces.

Simple chat must not create a full agent plan. The Agent Engine is invoked only when multi-step state, tools, approvals, durable workflow progress, or complex retrieval justify it.

### Fast and Deep paths

Fast Path uses recent context, compact structured retrieval, Tier 1 routing, and output validation.

Deep Path uses durable agent.runs, ordered run_steps, decisions, targeted retrieval, Tier 2 reasoning when needed, jobs/workers, and approval checkpoints.

### Guardrails

Agents cannot execute model-produced actions directly. Every proposed tool action passes typed schema validation, Policy Decision, Action Guardrails, approval, idempotency, final state check, and audit.

Every model call passes Input and Output Guardrails. Every memory read/write uses Memory Guardrails. Every external transmission uses Egress Guardrails.

### Free-model behavior

Free-model planning output is untrusted. Plans, steps, tool arguments, stop conditions, and structured results require validation. Repair is bounded. Invalid output causes clarification, fallback, or safe failure.

### Async rules

Long research, automation, ingestion, reflection, consolidation, export, and rebuild run as durable jobs. Agent workers heartbeat, checkpoint, support cancellation, and stop at kill-switch checkpoints.

Central reference: architecture/NOVO_ORCHESTRATOR_AND_GUARDRAILS.md.

# OpenClaw Reference Notes for NOVO

**Status:** Architecture decision note
**Owner:** Jay Rana
**Updated:** 2026-06-24

## Purpose

This note records selective ideas NOVO may borrow from OpenClaw-style agent systems and the boundaries NOVO must preserve. It is not a dependency commitment or a request to copy implementation.

## Ideas NOVO may borrow

- Local-first and responsive interaction
- Model-agnostic execution
- Clear tool and skill abstraction
- Multi-channel presence
- Automation-oriented workflows
- Practical routing among capabilities
- Replaceable adapters
- Background execution for long work

## Patterns NOVO rejects

- Wide-open default permissions
- A single agent identity with access to everything
- Mixing reasoning with unrestricted execution
- Plugin trust by default
- Unbounded autonomous loops
- Hidden or weak approval boundaries
- Model-generated permission changes
- Direct execution from unvalidated model output
- Treating conversation memory as unrestricted authority
- Autonomous work that bypasses durable audit

## NOVO positioning

NOVO remains:

- Memory-first
- Policy-first
- Provenance-first
- Deletion-aware
- Approval-aware
- Audit-friendly
- Provider-agnostic
- Fast-path capable
- Exact and controlled

NOVO should feel responsive and capable without becoming an ungoverned super-agent.

## Design consequences

1. Orchestrator and Guardrails remain separate responsibilities.
2. Tools expose narrow capabilities rather than broad application access.
3. Every mutation passes a deterministic application service.
4. Plugins and integrations are untrusted until registered, scoped, and approved.
5. Autonomous Mode remains bounded by explicit policy and safety budgets.
6. Memory never grants authority.
7. Provider or model changes never weaken classification policy.
8. Kill switch and audit remain outside agent control.

## Revisit conditions

Revisit this note when NOVO adds plugin installation, multi-agent collaboration, computer control, multi-channel messaging, or third-party skills.

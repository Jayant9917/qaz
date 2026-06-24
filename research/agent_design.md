# Agent Design Research Notes

**Status:** Active research notebook
**Normative specification:** docs/07_AGENT_ARCHITECTURE.md

## Purpose

Capture experiments, alternatives, benchmarks, and unresolved questions without changing the accepted Agent Architecture.

## Research topics

- Deterministic versus model request classification
- Planner schema and validation
- Fast-to-Deep escalation quality
- Checkpoint granularity
- Loop/no-progress detection
- Compensation patterns
- Tier 1 versus Tier 2 planning quality
- Worker lease and cancellation behavior
- Multi-agent value and risk

## Experiment template

- Question
- Hypothesis
- Dataset/scenario
- Implementation/version
- Metrics
- Result
- Security impact
- Operational impact
- Recommendation
- Architecture decision required

## Current constraints

No experiment may bypass Guardrails, approval, audit, budgets, or the rule that model output cannot directly execute tools.

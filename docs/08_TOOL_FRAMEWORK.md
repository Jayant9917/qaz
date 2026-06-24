# Tool Framework

Describe the architecture, integration patterns, and management of tool execution in NOVO.

## 1. Overview

## 2. Tool registry and lifecycle

## 3. Safety and sandboxing

## 4. Observability and audit

## Accepted Tool Runtime Requirements

This file remains a placeholder for the full Tool Framework. The following requirements are binding.

### Orchestrator boundary

The Orchestrator may decide that a capability is needed but never calls provider adapters directly. It submits a typed proposal to the Tool Gateway.

### No direct model execution

Model output is untrusted data. It cannot execute a tool, mutate state, select credentials, approve itself, or bypass preview.

### Execution pipeline

1. Resolve registered tool and capability version.
2. Validate strict input schema and reject unknown fields.
3. Resolve integration and resource scope.
4. Evaluate risk, security mode, permission, destination, and safety budget.
5. Generate deterministic preview and action hash.
6. Obtain exact approval when required.
7. Recheck policy, control state, expiry, and idempotency immediately before execution.
8. Retrieve scoped credential from Secrets Provider.
9. Execute with deadline and provider idempotency where available.
10. Validate and sanitize result.
11. Persist action outcome, provider request ID, and audit evidence.

### Free-model compensation

Unreliable tool JSON is never trusted. Use strict schemas, deterministic normalization, bounded repair, capability allowlists, preview comparison, and safe refusal.

### Retry rules

Read-only idempotent calls may use bounded retry. Non-idempotent actions retry only with provider idempotency or an execution reconciliation rule. An ambiguous outcome never retries blindly.

### Async rules

Long tools return durable jobs. Progress and cancellation remain visible. Approval-bound action parameters cannot change after approval.

Central reference: architecture/NOVO_ORCHESTRATOR_AND_GUARDRAILS.md.

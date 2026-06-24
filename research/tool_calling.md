# Tool Calling Research Notes

**Status:** Active adapter and safety notebook
**Normative specification:** docs/08_TOOL_FRAMEWORK.md

## Purpose

Track provider behavior, adapter experiments, schemas, idempotency, reconciliation, and permission design.

## Provider research template

- Tool/capability
- Provider/API version
- Required scopes
- Input/output schema
- Side effect
- Idempotency support
- Retry behavior
- Reconciliation method
- Rate limits
- Failure modes
- Data egress
- Risk recommendation
- Test evidence

## Priority research

- Initial tool order
- Email send reconciliation
- Calendar idempotency
- Filesystem path/symlink controls
- Git/GitHub safety
- Browser download/upload
- MCP capability discovery
- Plugin updates
- Computer-control expected-state validation

## Constraint

Provider experiments use dedicated test accounts and credentials in the Secrets Provider. Model-generated arguments are always validated before execution.

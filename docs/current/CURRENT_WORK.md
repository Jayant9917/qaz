# NOVO Current Work

This is the single living documentation file for ongoing NOVO work.

When the project changes, update this file first so the current state stays easy to follow.

## Current checkpoint

- E2 complete / E3 ready

## What this file is for

Use this file for the latest work-in-progress summary:

- what we are building right now
- what changed most recently
- what is blocked
- what the next step is
- any decisions that should not be forgotten

## Update rule

Keep this file short, current, and easy for a junior engineer to read.
If a detail becomes historical, move it into the relevant folder under `docs/` instead of keeping it here.

## Current status snapshot

- E2 is complete.
- The next engineering phase is E3: explicit memory.
- The docs have been reorganized into purpose-based folders, and this file is the single living work log.
- The new API documentation lives under `docs/api/`.

## What was completed in E2

- Conversation fast path
- Ordered messages and conversation history
- Chat API with SSE response streaming
- Fast-path routing and orchestration selection
- Prompt registry minimum implementation
- Model registry and OpenRouter gateway
- Input and output guardrails
- Token, latency, and cost accounting
- Conversation UI and history in the frontend

## What comes next

- E3 explicit memory
- Redis working context
- memory records, revisions, sources, and tags
- memory guardrails and memory center
- correction, archive, classification, deletion, and provenance

# NOVO Frontend

Next.js Control Center foundation for NOVO.

This E2 Control Center shell exists to give the backend, API contracts, and future Control Center modules a stable browser home while the conversation fast path and phase handoff remain visible.

## Local commands

From the repository root:

- Install: `pnpm install`
- Run: `pnpm --filter @novo/frontend dev`
- Build: `pnpm --filter @novo/frontend build`
- Lint: `pnpm --filter @novo/frontend lint`
- Type check: `pnpm --filter @novo/frontend typecheck`

## E2 Control Center scope

- App router shell
- Health/status page
- API URL configuration
- Shared visual language for Control Center modules
- Live backend/session visibility for the owner
- Browser session cookie handling with CSRF support
- WSL-only frontend development on Windows when building or running Next.js

Authentication, chat, approvals, permissions, memory, agents, tools, and audit screens start in later phases.

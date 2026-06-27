# NOVO Frontend

Next.js Control Center foundation for NOVO.

This E1 Control Center shell exists to give the backend, API contracts, and future Control Center modules a stable browser home while identity and control foundation work continues.

## Local commands

From the repository root:

- Install: `pnpm install`
- Run: `pnpm --filter @novo/frontend dev`
- Build: `pnpm --filter @novo/frontend build`
- Lint: `pnpm --filter @novo/frontend lint`
- Type check: `pnpm --filter @novo/frontend typecheck`

## E1 Control Center scope

- App router shell
- Health/status page
- API URL configuration
- Shared visual language placeholders for Control Center modules
- Live backend/session visibility for the owner
- Browser session cookie handling with CSRF support

Authentication, chat, approvals, permissions, memory, agents, tools, and audit screens start in later phases.

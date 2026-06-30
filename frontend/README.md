# NOVO Frontend

Next.js Control Center foundation for NOVO. The main daily-use product direction is the NOVO Desktop Assistant; this frontend remains the web Control Center for governance, inspection, settings, audit, and recovery.

This E2 Control Center shell gives the backend, API contracts, and future governance modules a stable browser home while the desktop assistant becomes the primary face of NOVO.

## Local commands

From the repository root:

- Install: `pnpm install`
- Run: `pnpm --filter @novo/frontend dev`
- Build: `pnpm --filter @novo/frontend build`
- Lint: `pnpm --filter @novo/frontend lint`
- Type check: `pnpm --filter @novo/frontend typecheck`

## Control Center scope

- App router shell
- Health/status page
- API URL configuration
- Shared visual language for Control Center modules
- Live backend/session visibility for the owner
- Browser session cookie handling with CSRF support
- WSL-only frontend development on Windows when building or running Next.js

Current implemented surfaces include login/session handling, chat, permissions, audit, settings, system-state views, and backend health. Future Control Center work should focus on memory review, documents/RAG management, model/prompt settings, tool permissions, approvals, agent-run inspection, and recovery while the desktop assistant handles daily interaction.

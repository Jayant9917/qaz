# NOVO

NOVO is an owner-controlled Personal AI Operating System.

The primary product direction is now a local **NOVO Desktop Assistant**: a real desktop GUI with voice, presence, chat, and task interaction. The existing Next.js frontend remains important as the **NOVO Control Center** for permissions, audit, settings, system state, memory review, documents, models, tools, and recovery.

Current checkpoint: E2 complete / E3 ready. See [docs/checkpoints/17_E2_COMPLETE_E3_READY.md](D:/NOVO/docs/checkpoints/17_E2_COMPLETE_E3_READY.md).

## Repository areas

- backend: FastAPI modular application and workers
- frontend: Next.js Control Center and administrative dashboard
- desktop: planned local desktop assistant shell and voice interface
- infra: local and production infrastructure definitions
- prompts: version-controlled development prompt sources
- scripts: developer commands
- docs: normative product and architecture specifications
- research: non-normative research notebooks

## Prerequisites

- Python 3.12
- Node.js 20.x
- pnpm 10.34.4
- Docker with Compose for PostgreSQL and Redis
- WSL Ubuntu for frontend development and builds on Windows

Docker Desktop is installed and the core Compose services are available locally. The application can still run unit tests after dependencies are installed, but infrastructure readiness checks require the core Compose profile.

## Quick start

1. Copy .env.example to .env and keep it local.
2. Install backend dependencies.
3. Install frontend dependencies with pnpm install.
4. Start PostgreSQL and Redis with the core Compose profile.
5. Run backend and frontend development servers.
6. Run the quality scripts.

Frontend development and production builds should run through WSL Ubuntu on this Windows machine so Next.js can avoid the local spawn/permission issue we found in the native Windows environment.

Browser sessions use HttpOnly cookies with CSRF protection; bearer headers remain a compatibility path for non-browser clients only.

The desktop assistant should talk to the backend APIs instead of directly reading documents, email, memory, tool credentials, or model providers. The backend remains the authority for permissions, audit, memory, RAG, tools, model calls, and kill-switch enforcement.

See backend/README.md, frontend/README.md, and infra/README.md.

## Security

Never commit credentials or real owner data. OpenRouter and other provider secrets will be integrated through the Secrets Provider in later phases.

## Documentation

Start with docs/current/CURRENT_WORK.md for the latest live state, then read:

- docs/foundation/01_PROJECT_VISION.md
- docs/foundation/04_EXECUTION_ROADMAP.md
- docs/product/16_DESKTOP_ASSISTANT_ARCHITECTURE.md

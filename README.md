# NOVO

NOVO is an owner-controlled Personal AI Operating System.

This repository is currently in Phase E0: Engineering Foundation.

## Repository areas

- backend: FastAPI modular application and workers
- frontend: Next.js Control Center and chat shell
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

Docker is not currently installed on this workstation. The application can still run unit tests after dependencies are installed, but infrastructure readiness checks require the core Compose profile.

## Quick start

1. Copy .env.example to .env and keep it local.
2. Install backend dependencies.
3. Install frontend dependencies with pnpm install.
4. Start PostgreSQL and Redis with the core Compose profile.
5. Run backend and frontend development servers.
6. Run the quality scripts.

See backend/README.md, frontend/README.md, and infra/README.md.

## Security

Never commit credentials or real owner data. OpenRouter and other provider secrets will be integrated through the Secrets Provider in later phases.

## Documentation

Start with docs/01_PROJECT_VISION.md and docs/04_EXECUTION_ROADMAP.md.
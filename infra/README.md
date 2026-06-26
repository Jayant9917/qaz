# NOVO Infrastructure

Infrastructure definitions for local development and future deployment.

## E0 local core

The core Compose file starts only the services needed for early backend development:

- PostgreSQL
- Redis

Milvus, RabbitMQ, MinIO, observability, and computer-control sandbox services are intentionally deferred until their implementation phases.

## Commands

From the repository root:

- Start core infrastructure: `docker compose -f infra/compose/docker-compose.core.yml up -d`
- Stop core infrastructure: `docker compose -f infra/compose/docker-compose.core.yml down`
- View logs: `docker compose -f infra/compose/docker-compose.core.yml logs -f`

Use `.env.example` as the source of local variable names. Do not commit `.env`.

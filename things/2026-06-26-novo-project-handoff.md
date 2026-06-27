# NOVO Project Handoff Notes

**Date:** 2026-06-26  
**Project:** NOVO  
**Owner:** Jay Rana  
**Current phase:** E1 in progress  
**Purpose of this file:** A complete reference note for anyone who needs to understand what NOVO is, what has been built so far, why it was built that way, and what still remains.

---

## 1. What NOVO is

NOVO is being built as an owner-controlled Personal AI Operating System.

The core idea is simple:

- the owner stays in control,
- NOVO never performs sensitive actions silently,
- every meaningful action should be visible, explainable, and auditable,
- security and governance come before advanced AI behavior,
- the system should eventually feel like a companion, not just a tool.

At the product level, NOVO is intended to grow into:

- a control center,
- a secure AI assistant,
- a memory system,
- a document/knowledge system,
- an agent system,
- a governance and audit layer,
- and later, a companion interface with personality and context.

The work so far has focused on building the foundation the right way, instead of jumping too early into advanced AI features.

---

## 2. The big architecture idea

NOVO was designed as a modular monolith first, with clear domain separation.

The main principle is:

> build one safe, understandable, testable layer at a time.

That means:

- identity and sessions first,
- permissions and security next,
- audit and kill switch next,
- then conversation,
- then memory,
- then knowledge/RAG,
- then agents,
- then automation and computer control later.

This sequence matters because AI features are dangerous without a strong identity, governance, and audit base.

The architecture documents were created first so the implementation would not drift randomly. The docs are the source of truth for product direction, system boundaries, database shape, and phased execution.

---

## 3. Documentation created so far

The repository now has a full documentation set in `docs/`.

The major files include:

- `docs/01_PROJECT_VISION.md`
- `docs/02_SYSTEM_ARCHITECTURE.md`
- `docs/03_DATABASE_DESIGN.md`
- `docs/04_EXECUTION_ROADMAP.md`
- `docs/05_MEMORY_ARCHITECTURE.md`
- `docs/06_RAG_ARCHITECTURE.md`
- `docs/07_AGENT_ARCHITECTURE.md`
- `docs/08_TOOL_FRAMEWORK.md`
- `docs/09_SECURITY_GOVERNANCE.md`
- `docs/10_API_SPECIFICATION.md`
- `docs/11_FRONTEND_ARCHITECTURE.md`
- `docs/12_DEPLOYMENT_ARCHITECTURE.md`
- `docs/13_TESTING_STRATEGY.md`
- `docs/14_OBSERVABILITY.md`
- `docs/15_PRODUCT_ROADMAP.md`

These docs are intentionally detailed. They define:

- the product vision,
- the backend and frontend architecture,
- the database schema strategy,
- the security model,
- the memory/RAG/agent future path,
- the execution phases,
- and the production readiness rules.

The execution roadmap is especially important because it defines the phase order:

- E0 = engineering foundation
- E1 = identity and control foundation
- E2 = conversation fast path
- E3 = explicit memory
- E4 = secure documents and RAG
- E5 = deep orchestration

We are currently in E1 in progress.

---

## 4. Why the project is split into many schemas

The database is intentionally split into schemas such as:

- `identity`
- `governance`
- `audit`
- `memory`
- `knowledge`
- `chat`
- `agent`
- `automation`
- `platform`
- `public`

These schemas are not random. They are like folders inside PostgreSQL.

Each schema groups tables by business purpose:

- `identity` holds users, sessions, and settings
- `governance` holds permissions, control state, and policy-related data
- `audit` holds append-only evidence and logs
- `memory` holds long-term and semantic memory structures
- `knowledge` holds documents, chunks, and future retrieval data
- `chat` holds conversations and messages
- `agent` holds agent runs and decisions
- `automation` holds automations and scheduled execution
- `platform` holds system-level support data and metadata
- `public` holds default PostgreSQL objects and migration bookkeeping

This design helps with:

- clarity,
- separation of concerns,
- access control,
- row-level security,
- and future scaling.

It also makes the project easier to reason about when the codebase grows.

---

## 5. What we built first and why

The implementation did not start with AI features.

It started with the parts that make the rest safe.

### Why E0 came first

E0 was the engineering foundation phase. It was needed to make sure the project could:

- install correctly,
- run locally,
- pass tests,
- have a stable backend/frontend scaffold,
- and have a reproducible dev environment.

Without E0, every later phase would be fragile.

### Why E1 came next

E1 is the identity and control foundation.

That was the correct next step because NOVO cannot safely do anything sensitive without:

- a user identity,
- session management,
- permission checks,
- control state,
- kill switch behavior,
- audit logging,
- CSRF protection,
- rate limiting,
- and policy enforcement.

In plain terms:

> we built the locks before we built the doors.

That is the right order for this product.

---

## 6. What is already implemented in the backend

The backend is a FastAPI modular application under `backend/src/novo`.

The codebase already contains the following major areas:

- `api`
- `core`
- `identity`
- `governance`
- `audit`
- `infrastructure`
- `agents`
- `memory`
- `knowledge`
- `chat`
- `orchestrator`
- `tools`
- `files`
- `jobs`
- `observability`

Some of these folders are active, some are placeholders for later phases, and some have partial implementation.

### Core backend features already built

We now have:

- health endpoints,
- structured app startup,
- configuration loading,
- logging,
- request context handling,
- database integration,
- rate limiting support,
- row-level security helpers,
- identity/session routes,
- control routes,
- audit routes,
- permission routes,
- migration support,
- and test coverage for the security foundation.

### Why these pieces matter

These are not “nice to have” foundation pieces.

They are what allow NOVO to operate safely in the real world:

- log what happened,
- know who did it,
- know whether they were allowed,
- know what changed,
- know whether the change is reversible,
- and know when to stop everything if policy is violated.

---

## 7. What is already implemented in the frontend

The frontend is a Next.js app used as the NOVO Control Center.

The UI work so far has focused on:

- the landing/control center shell,
- the login page,
- the overall visual identity,
- and the direction for a future dashboard-like interface.

The design direction is intentionally inspired by calm, polished, high-contrast control surfaces.

We also worked through UI reference direction from Framer-style layouts:

- dark background,
- wide canvas,
- left navigation zone,
- hero section,
- clean status cards,
- strong typography,
- and a “control center” feel rather than a generic app shell.

The UI should eventually become the place where the owner can:

- see NOVO’s state,
- see the current phase,
- inspect backend health,
- manage permissions,
- manage memory,
- manage tools,
- view audit logs,
- and interact with NOVO conversationally.

---

## 8. Database state right now

The database is PostgreSQL and is being managed with Alembic migrations.

### Current schema count

At the time of this handoff, the database has multiple schemas in place. The visible schemas include:

- `agent`
- `audit`
- `automation`
- `chat`
- `governance`
- `identity`
- `knowledge`
- `memory`
- `platform`
- `public`

### Current table count

The live database currently has 11 base tables.

The table inventory observed earlier was:

- `audit.audit_logs`
- `governance.control_events`
- `governance.permissions`
- `governance.role_permissions`
- `governance.system_control_state`
- `identity.roles`
- `identity.sessions`
- `identity.user_roles`
- `identity.users`
- `platform.schema_metadata`
- `public.alembic_version`

### What seed data exists

There is no separate seed file yet.

Instead, seed/bootstrap logic is currently inside the backend code:

- `backend/src/novo/identity/service.py`
- `backend/src/novo/main.py`

The bootstrap flow creates:

- the owner role,
- default permissions,
- the bootstrap owner user,
- and the owner control-state row.

That means the project currently seeds itself during startup rather than through a separate seed command.

That approach was acceptable for early foundation work because it keeps the environment easier to bring up while the schema is still evolving.

---

## 9. Security work completed so far

This project has already gone well beyond a basic scaffold.

The security foundation now includes:

- authentication routes,
- session handling,
- login/logout/current-user behavior,
- permissions plumbing,
- audit logging,
- CSRF protection,
- rate limiting,
- row-level security,
- kill switch control,
- and protected mutation tests.

### Important security concepts already implemented

#### Session and identity

The system now supports real identity-backed access instead of anonymous access.

#### Permission model

The database includes a permissions structure that can be expanded later.

#### Control state

The project has a `system_control_state` concept to support kill switch / operating mode behavior.

#### Audit requirement

Important actions are expected to create audit evidence.

#### RLS / isolation

Row-level security is used so that owner-scoped data stays isolated.

#### Rate limiting

Request throttling is included so the API does not become trivially abusable.

#### CSRF

CSRF protection was added for state-changing browser flows.

#### Runtime DB role

A restricted runtime database role was added so the application does not run with overly broad privileges.

This is a strong security direction and a good sign for the architecture.

---

## 10. Tests and verification already done

The backend test suite has been run successfully.

At one point, backend tests reported:

- `10 passed`

The quality checks were also validated:

- backend linting,
- formatting-related checks,
- and frontend quality checks were used as part of the validation flow.

The work also uncovered and fixed real issues along the way, including:

- CORS misconfiguration,
- login validation mismatch,
- incorrect password/username assumptions,
- frontend server issues,
- and local PostgreSQL port conflicts.

That is normal for a project still in active foundation work.

The important part is that the issues were discovered early instead of being left hidden.

---

## 11. Environment and local machine setup

The local development environment now includes:

- Python 3.12.10
- Node.js 20.19.5
- pnpm 10.34.4
- Docker Desktop
- PostgreSQL container
- Redis container

### Database port decision

There was a conflict because the user already had local PostgreSQL and pgAdmin on port 5432.

The Docker Postgres container was moved to port 5433 so it would not collide with the local database.

That was the correct fix because:

- local Postgres remains usable,
- Docker Postgres remains usable,
- and pgAdmin can connect to either one explicitly.

### pgAdmin connection to Docker Postgres

To inspect the Docker database in pgAdmin, connect with:

- host: `localhost`
- port: `5433`
- database: the Docker database name from `.env`
- user: the Docker user from `.env`
- password: the Docker password from `.env`

This lets you view the Docker-managed NOVO database without disturbing your local native Postgres installation.

---

## 12. The .env file situation

The project uses an `.env` file at the repo root:

- `D:\NOVO\.env`

That file is local and should not be committed.

The repository also has:

- `.env.example`

The purpose of `.env.example` is to show the required variables without exposing secrets.

This is the right pattern:

- `.env.example` = safe template
- `.env` = actual local secrets and settings

This keeps the project reproducible without leaking credentials.

---

## 13. Commands used so far

The main workflows that were used include:

### Backend setup

- install backend dependencies with editable dev extras
- run backend tests
- run ruff checks
- run Alembic migrations

### Frontend setup

- run Next.js dev mode through pnpm
- inspect browser behavior and hydrate/runtime errors

### Local infrastructure

- start Docker Compose core services
- bring up PostgreSQL and Redis

### Combined development

We also created a common command path so backend and frontend can be run together from the root workspace.

That matters because it gives a single developer entry point instead of making the process feel fragmented.

---

## 14. Problems that were found and fixed along the way

This project did not progress in a straight line. That is normal.

The main issues we ran into were:

- pnpm / Node version mismatch concerns,
- Next.js frontend runtime errors,
- invalid package.json behavior in some command contexts,
- CORS policy issues between frontend and backend,
- login validation failures,
- wrong test credentials,
- Docker database port conflict with an existing local PostgreSQL service,
- and the need to separate local and containerized database configuration cleanly.

Each one was useful because it exposed a real integration boundary.

### Why these issues mattered

If we had ignored them, we would have ended up with:

- a fragile dev environment,
- confusing onboarding,
- hidden security assumptions,
- and unreliable startup behavior.

Instead, the environment now has clearer boundaries and more realistic behavior.

---

## 15. Current phase status

Current execution phase:

### E1 — Identity and Control foundation

This phase is about making sure NOVO is secure before it becomes smart.

In practical terms, E1 focuses on:

- user identity,
- sessions,
- permissions,
- audit logs,
- security modes,
- kill switch behavior,
- CSRF,
- rate limiting,
- and owner-controlled access.

E1 is still in progress because the security foundation is not fully complete yet.

The roadmap items still to finish include things like:

- system control state finalization,
- kill switch activation/deactivation behavior,
- security modes,
- more robust row-level security,
- cross-owner tests,
- session theft/revocation tests,
- and audit failure blocking for protected mutations.

---

## 16. What should happen next

The next steps are still foundation work, not advanced AI work.

### Next priorities

1. finish the remaining E1 security and governance pieces,
2. verify migrations and seeding are clean,
3. stabilize local startup commands,
4. keep the backend/frontend dev loop easy to run,
5. make sure the project remains testable and predictable,
6. only then move into E2 conversation work.

### What should not start yet

These should wait until the identity/security base is complete:

- RAG
- memory intelligence
- agents
- tool execution
- computer control
- advanced automation
- companion-style long-term behavior

That order prevents expensive architectural mistakes later.

---

## 17. Why the project is being built this way

The short version:

We are not trying to build “just a chatbot.”

We are building a personal AI operating system that can eventually become:

- a control center,
- a companion,
- a memory system,
- a secure assistant,
- and an automation layer.

That goal requires a different architecture than a normal app.

The system needs:

- durable identity,
- policy enforcement,
- data classification,
- auditability,
- owner transparency,
- recoverability,
- and future-proof domain separation.

That is why the docs are deep, the schemas are split, and the build order is conservative.

---

## 18. Current practical reference points

If someone else takes over this project, the most important things for them to know are:

- NOVO is in E1 in progress.
- The docs are the source of truth.
- The backend foundation already works.
- The database is already structured by schema.
- Security and governance are the current focus.
- Seed/bootstrap logic exists in code, not as a separate seed file yet.
- Docker Postgres is on port 5433 because local Postgres already uses 5432.
- `.env.example` exists as the safe template; `.env` is local only.
- The system is intentionally being built in small verified phases.

---

## 19. Very short summary

If I had to explain the whole project in one paragraph:

NOVO is an owner-controlled personal AI OS being built in phases, starting with engineering foundations and then identity/security, before moving into chat, memory, RAG, agents, and automation. So far, the repo has a documented architecture, a structured PostgreSQL schema strategy, a working backend foundation, security controls like sessions, permissions, CSRF, rate limiting, audit, kill switch, and row-level security, plus an evolving frontend Control Center. The project is intentionally being built slowly and safely so future AI features do not become a security or architecture risk.

---

## 20. Notes for future updates

This file should be updated whenever:

- a phase is completed,
- a new schema or migration is added,
- a major architectural decision changes,
- seed/bootstrap behavior changes,
- the dev environment changes,
- or a new frontend/control-center milestone is reached.

That way this file stays useful as a real handoff reference instead of becoming stale.


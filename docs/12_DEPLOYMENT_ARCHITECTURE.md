# NOVO Deployment Architecture

**Status:** Draft for implementation
**Owner:** Jay Rana
**Updated:** 2026-06-24

## 1. Purpose

This document defines how NOVO is configured, packaged, deployed, upgraded, backed up, restored, and operated across development and personal production.

## 2. Deployment principles

- Local/private first
- Reproducible
- Environment separated
- Secrets externalized
- Private data services
- Minimal exposed ports
- Health-checked
- Resource bounded
- Backup before migration
- Rollback/compensation planned
- Security controls available without models
- Scale only when measured

## 3. Environments

### Local development

Developer machine, disposable data allowed, safe mock integrations, debug visibility, no production credentials.

### Integration/test

CI or isolated local environment with real service protocols, synthetic data, migration and contract tests.

### Personal production

Hardened private deployment with real owner data, encrypted storage/backups, TLS, production secrets, monitoring, and restore procedures.

### Recovery

Isolated minimal environment for database/object restore, integrity checks, policy repair, and audit review.

## 4. Initial topology

Containers/processes:

- reverse-proxy optional locally
- frontend
- api
- agent-worker
- background-worker
- reflection-worker optional
- scheduler
- postgres
- redis
- rabbitmq
- minio
- milvus and required dependencies
- neo4j optional profile
- observability stack optional profile
- secrets provider or development adapter

## 5. Compose profiles

### core

Frontend, API, PostgreSQL, Redis.

### knowledge

Core plus MinIO, RabbitMQ, worker, Milvus.

### full

Knowledge plus scheduler, agent worker, observability.

### graph

Full plus Neo4j and graph worker.

### computer

Full plus isolated browser/computer-control worker.

Profiles keep development practical on limited hardware.

## 6. Network zones

- edge: reverse proxy to frontend/API
- app: API and workers
- data: PostgreSQL, Redis, RabbitMQ, MinIO, Milvus, Neo4j, vault
- automation: browser/computer sandbox
- observability: telemetry collectors and dashboards

Data services are never internet-exposed.

## 7. Exposed services

Public/private client entry:

- HTTPS frontend/API
- Optional private VPN endpoint

Not exposed publicly:

- PostgreSQL
- Redis
- RabbitMQ management
- MinIO admin
- Milvus
- Neo4j
- Vault/admin
- Metrics
- Debug endpoints

## 8. TLS

- TLS at client boundary
- TLS across trust boundaries
- Service certificates or authenticated private transport for production
- Automated renewal where possible
- No certificate verification bypass
- Secure cookies only under HTTPS production

## 9. Configuration

Configuration classes:

- Committed safe defaults
- Environment-specific non-secret values
- Owner policy in PostgreSQL
- Dynamic control state in PostgreSQL/Redis projection
- Secrets in Secrets Provider

Startup validates mandatory values and refuses insecure production defaults.

## 10. Secrets

- No secrets in repository, image, Compose file, logs, or frontend.
- Development uses a clearly marked local adapter.
- Production uses selected vault/OS/cloud provider.
- Services receive only required references.
- Rotation and revocation documented.
- Separate credentials per environment and runtime role.
- Secret scanning in CI.

## 11. Container images

- Minimal base images
- Pinned versions/digests in production
- Non-root user
- Read-only filesystem where possible
- No compiler/build secrets in runtime image
- Multi-stage builds
- Health check
- Resource limit
- Dependency/SBOM scan
- Signed or verified release artifacts

## 12. Persistent volumes

Persistent:

- PostgreSQL
- MinIO
- Milvus
- Neo4j when enabled
- RabbitMQ durable state where required
- Vault data when self-hosted
- Observability data by retention policy

Redis persistence is optional operational support, not authority.

Volume ownership, encryption, backup, and restore are documented.

## 13. API scaling

API is stateless except externalized session/control state.

Scale behind load balancer when needed.

SSE requires proxy buffering disabled and suitable connection timeout.

WebSocket requires connection-aware routing only when protocol needs it.

## 14. Worker scaling

Scale independently by queue/workload:

- agent
- ingestion/parser
- embedding
- reflection
- graph sync
- automation
- computer control
- maintenance

Workers have separate service identities, limits, concurrency, and queue permissions.

## 15. Resource controls

Per service:

- CPU
- memory
- file descriptors
- process count
- request/body size
- connection pool
- concurrency
- queue prefetch
- timeout
- temporary storage
- network egress

Parser and computer workers receive the strictest isolation.

## 16. Database deployment

- Version-pinned PostgreSQL
- Private network
- TLS
- Separate roles
- Connection pooling
- Automated encrypted backup
- Point-in-time recovery when supported
- Disk-space alert
- Vacuum/analyze monitoring
- Migration role separate from runtime
- Restore tests

## 17. Redis deployment

- Private/authenticated
- Memory limit and eviction policy
- Namespaced keys
- Optional persistence
- Health monitoring
- No authority assumption
- Safe restart behavior

## 18. RabbitMQ deployment

- TLS and separate users/vhost
- Durable exchanges/queues
- Publisher confirms
- Dead-letter topology
- Queue depth/age alerts
- Disk/memory watermark
- Definitions under version control
- Outbox replay recovery

## 19. MinIO deployment

- Private buckets
- Encryption
- Versioning where needed
- Lifecycle rules
- Quarantine isolation
- Capacity alerts
- Integrity checks
- Encrypted replication/backup
- Short-lived presigned URLs

## 20. Milvus and Neo4j

Both are derived.

- Private authenticated network
- Version-pinned
- Capacity/latency monitoring
- Snapshot optional for faster recovery
- Full rebuild procedure
- Projection version visible
- No direct client access
- Canonical reauthorization remains in API/service

## 21. OpenRouter egress

Only Model Gateway can reach configured model endpoint.

Controls:

- Endpoint allowlist
- TLS
- Scoped API key
- Timeouts
- Proxy configuration if used
- Egress logging by category, not payload
- Kill-switch support
- Provider outage handling

## 22. Computer-control deployment

Separate sandbox/worker pool:

- No host credential access
- Restricted mounts
- Restricted network
- Ephemeral browser profile unless approved
- Download quarantine
- Session deadline
- Evidence storage policy
- Killable process group
- No privileged container

## 23. Health checks

Liveness: process/event loop responsive.

Readiness: role can serve mandatory dependencies.

Startup: migrations/schema compatibility/configuration valid.

Dependency detail: authenticated operations endpoint only.

Health checks do not expose credentials/topology publicly.

## 24. Deployment pipeline

1. Lint, type check, unit tests.
2. Dependency/security scan.
3. Build immutable images.
4. Generate SBOM.
5. Integration and migration tests.
6. Contract/E2E tests.
7. Backup current production.
8. Apply expand migrations.
9. Deploy workers/API/frontend in compatible order.
10. Run smoke/readiness checks.
11. Switch traffic.
12. Observe.
13. Run backfill/switch/contract phases separately.
14. Record release and audit.

## 25. Migration strategy

Use expand, backfill, switch, contract.

- Never auto-run production migrations at app startup.
- Backup before destructive migration.
- Large backfill is resumable.
- Old/new versions remain compatible during rollout.
- Contract migration occurs after verification.
- Migration failure preserves recovery path.

## 26. Rollback

Code rollback is allowed when schema remains compatible.

For irreversible data migration, use forward compensation or restore after explicit decision.

Rollback plan includes:

- Image versions
- Schema compatibility
- Worker compatibility
- Queue event compatibility
- Prompt/policy versions
- Provider routing
- Cache invalidation
- External effects that cannot roll back

## 27. Backup

PostgreSQL:

- Full backup
- WAL/PITR where supported
- Integrity check

MinIO:

- Versioned encrypted backup or replication

Vault:

- Provider-specific protected backup

Derived stores:

- Optional snapshot plus rebuild procedure

Configuration/policies:

- Included through PostgreSQL and version-controlled safe config

## 28. Restore order

1. Establish recovery trust and keys.
2. Restore Secrets Provider access.
3. Restore PostgreSQL.
4. Verify audit/control/policy state.
5. Restore MinIO.
6. Reconcile checksums.
7. Recreate RabbitMQ topology.
8. Replay pending outbox carefully.
9. Rebuild Milvus.
10. Rebuild Neo4j.
11. Warm Redis.
12. Run integrity/security tests.
13. Re-enable models/tools/automations explicitly.

## 29. CI/CD environments

CI uses synthetic data and isolated service instances.

No production secret or owner data.

Artifacts are immutable between test and deployment.

Protected branch/release approval policy is selected during repository initialization.

## 30. Logging and telemetry deployment

- Structured stdout or collector
- Central OpenTelemetry collector when enabled
- Redaction before export
- Local-first dashboards
- Langfuse deployment decision
- Retention/rotation
- Disk protection
- No raw sensitive prompts by default

## 31. Personal production options

Preferred initial options:

- Hardened Linux host/home server
- Private cloud VM through VPN
- Windows development remains supported

Production choice depends on hardware, privacy, uptime, remote access, and maintenance capacity.

## 32. Capacity planning

Monitor:

- PostgreSQL size/connections
- MinIO objects/throughput
- Vector count/query latency
- Queue depth/age
- Redis memory/eviction
- CPU/memory
- Model request rate/cost
- Parser temp storage
- Backup duration
- Restore duration

Scale from evidence, not anticipated complexity.

## 33. Disaster scenarios

Runbooks for:

- Disk failure
- Database corruption
- Lost vault access
- Credential exposure
- Failed migration
- Queue backlog
- MinIO object loss
- Provider outage
- Malicious document
- Audit integrity failure
- Host compromise
- Accidental deletion

## 34. Initialization deliverables

- compose core profile
- environment example
- configuration validator
- health endpoints
- migration command
- backup/restore scripts
- local secrets adapter
- service-role credentials
- private networks/volumes
- developer start/stop/reset commands
- smoke test
- documented minimum hardware

## 35. Definition of done

- Environments and trust zones are explicit.
- Minimal stack starts reproducibly.
- Production exposes only intended entry points.
- Secrets and service identities are isolated.
- Deploy, migration, rollback, backup, and restore are tested.
- Derived stores rebuild.
- Health and resource limits exist.
- Security controls remain available during model outage.

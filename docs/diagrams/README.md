# NOVO Architecture Visualizations

This folder provides visual companions to the normative specifications. Diagrams explain architecture; the numbered specification files remain authoritative when wording differs.

## Diagram index

| Document | Shows |
|---|---|
| V2_SYSTEM_ARCHITECTURE.md | Complete Version 2 components and storage boundaries |
| DATABASE_RELATIONSHIPS.md | Normalized PostgreSQL domains, foreign keys, and index coverage |
| MEMORY_COMPANION_PIPELINE.md | Memory candidates, consolidation, reflection, companion response |
| EVENTS_AND_REGISTRIES.md | Domain events, RabbitMQ delivery, model registry, prompt registry |
| COMPUTER_CONTROL_FLOW.md | Governed browser and computer-use execution |

## Reading order

1. Start with the Version 2 system architecture.
2. Review database relationships and normalization.
3. Follow the memory/companion lifecycle.
4. Review asynchronous events and registries.
5. Review computer-control safety boundaries.

## Legend

- Solid arrows show direct calls or durable relationships.
- Dotted arrows show asynchronous events or derived synchronization.
- PostgreSQL is authoritative unless a diagram explicitly states otherwise.
- Redis is ephemeral.
- Milvus and Neo4j are rebuildable derived indexes.
- MinIO stores binary objects.
- RabbitMQ delivers events and commands but is not a source of truth.
- Every model, memory, companion, and tool path passes governance.

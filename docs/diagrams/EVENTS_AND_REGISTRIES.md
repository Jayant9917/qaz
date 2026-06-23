# Domain Events and Registries

## 1. Domain-event delivery

~~~mermaid
flowchart LR
    UseCase["Application transaction"] --> PG["Business rows"]
    UseCase --> Outbox["Transactional outbox row"]
    PG --> Commit{"Single PostgreSQL commit"}
    Outbox --> Commit
    Commit --> Publisher["Outbox Publisher"]
    Publisher --> MQ["RabbitMQ"]
    MQ --> RAG["RAG consumer"]
    MQ --> Memory["Memory consumer"]
    MQ --> Notify["Notification consumer"]
    MQ --> Graph["Graph-sync consumer"]
    MQ --> Analytics["Analytics consumer"]
    RAG --> Processed["Processed-message record"]
    Memory --> Processed
    Graph --> Processed
~~~

Domain events are immutable facts such as document.uploaded.v1, memory.created.v1, goal.updated.v1, approval.resolved.v1, and tool_action.completed.v1. RabbitMQ is the delivery mechanism, not the definition or authority.

Every event envelope includes event ID, type, schema version, time, owner, actor, correlation ID, causation ID, trace ID, and a minimal payload or object reference.

## 2. Model registry

~~~mermaid
flowchart LR
    Registry["Model Registry"] --> Provider["Provider"]
    Registry --> Capability["Capabilities"]
    Registry --> Context["Context window"]
    Registry --> Price["Cost"]
    Registry --> Latency["Observed latency"]
    Registry --> Availability["Health and availability"]
    Registry --> Privacy["Classification eligibility"]
    Request["Model request"] --> Router["Model Router"]
    Registry --> Router
    Policy["Owner model policy"] --> Router
    Router --> Choice["Eligible model + explanation"]
~~~

## 3. Prompt registry

~~~mermaid
flowchart TD
    Template["Prompt Template"] --> Version["Immutable Prompt Version"]
    Version --> Binding["Purpose Binding"]
    Binding --> System["System"]
    Binding --> Agent["Agent"]
    Binding --> Tool["Tool"]
    Binding --> Companion["Companion"]
    Binding --> Memory["Memory/Reflection"]
    Version --> Test["Evaluation and security tests"]
    Test --> Approval{"Approved?"}
    Approval -->|yes| Active["Active version"]
    Approval -->|no| Draft["Draft/rejected"]
    Active --> Render["Typed render with allowed variables"]
    Render --> Model["Model Gateway"]
~~~

Recommended repository layout:

- prompts/system
- prompts/agents
- prompts/tools
- prompts/companion
- prompts/memory

Files are development sources. PostgreSQL prompt_templates and prompt_versions provide runtime identity, activation, audit, and rollback. Protected production prompts cannot be modified by an agent.

# NOVO Version 2 System Architecture

## Complete component map

~~~mermaid
flowchart TB
    Owner["Owner"] --> UI["Next.js Control Center"]
    UI --> API["FastAPI API"]

    subgraph Control["Security and Governance Control Plane"]
        Policy["Policy Decision Point"]
        Privacy["Privacy Firewall"]
        Approval["Approval Engine"]
        Audit["Audit Service"]
        Kill["Kill Switch"]
        Vault["Secrets Provider"]
    end

    subgraph Intelligence["Intelligence Layer"]
        Agent["Agent Engine"]
        Companion["Companion Service"]
        ModelRouter["Model Router"]
        ModelRegistry["Model Registry"]
        PromptRegistry["Prompt Registry"]
        Computer["Computer Control Layer"]
    end

    subgraph CompanionParts["Companion Intelligence"]
        Emotion["Emotional Signal Analyzer"]
        Continuity["Continuity and Relationship Tracker"]
        Personality["Personality Engine"]
        Growth["Goals and Growth Service"]
    end

    subgraph MemoryLayer["Memory and Knowledge"]
        Memory["Memory Service"]
        Candidate["Memory Candidate Pipeline"]
        Consolidation["Consolidation Service"]
        Reflection["Reflection Agent"]
        RAG["RAG Service"]
        Graph["Knowledge Graph Service"]
    end

    subgraph Durable["Storage and Delivery"]
        PG[("PostgreSQL - authority")]
        Redis[("Redis - ephemeral")]
        Milvus[("Milvus - vectors")]
        Neo4j[("Neo4j - derived graph")]
        MinIO[("MinIO - objects")]
        MQ[("RabbitMQ - delivery")]
    end

    API --> Policy
    API --> Agent
    Agent --> Companion
    Agent --> ModelRouter
    Agent --> Computer
    Companion --> Emotion
    Companion --> Continuity
    Companion --> Personality
    Companion --> Growth
    Companion --> Memory
    Memory --> Candidate
    Candidate --> Consolidation
    Consolidation --> Reflection
    Reflection --> Memory
    Memory --> RAG
    Memory --> Graph
    ModelRouter --> ModelRegistry
    ModelRouter --> PromptRegistry
    ModelRouter --> Privacy
    Computer --> Approval

    Policy --> PG
    Audit --> PG
    Memory --> PG
    Memory --> Redis
    Memory --> Milvus
    Graph --> Neo4j
    RAG --> MinIO
    ModelRegistry --> PG
    PromptRegistry --> PG
    Agent -. commands/events .-> MQ
    MQ -. work .-> Consolidation
    MQ -. work .-> Reflection

    Policy -. guards .-> Agent
    Policy -. guards .-> Companion
    Policy -. guards .-> Memory
    Policy -. guards .-> Computer
    Kill -. stops .-> Agent
    Kill -. stops .-> Computer
    Vault -. scoped credentials .-> ModelRouter
    Vault -. scoped credentials .-> Computer
~~~

## Component boundaries

| Component | Owns | Must not do |
|---|---|---|
| Companion Service | Companion orchestration and continuity | Bypass memory policy or claim consciousness |
| Emotional Signal Analyzer | Uncertain emotional observations | Diagnose, authorize, manipulate, or override intent |
| Personality Engine | Configurable response style | Hide adaptation or create dependency |
| Growth Service | Owner-defined goals and progress | Define success for the owner |
| Consolidation Service | Score, deduplicate, merge, expire candidates | Silently rewrite approved memory |
| Reflection Agent | Propose insights and memory changes | Directly activate sensitive memory |
| Knowledge Graph Service | Entity/relation projection and graph query | Become authority for permissions or memory text |
| Model Registry | Model capability, price, context, health | Store provider secrets |
| Prompt Registry | Versioned templates and bindings | Allow runtime agents to rewrite protected prompts |
| Computer Control Layer | Sandboxed GUI execution | Operate outside policy, approval, or evidence capture |

## Knowledge graph authority

PostgreSQL stores canonical entities, memories, ownership, classifications, and graph synchronization state. Neo4j stores a derived relationship projection.

~~~mermaid
flowchart LR
    PG["PostgreSQL canonical records"] --> Sync["Graph Sync Worker"]
    Sync --> Neo4j["Neo4j relationship projection"]
    Neo4j --> Query["Graph Query"]
    Query --> ReAuth["PostgreSQL reauthorization"]
    ReAuth --> Context["Permitted reasoning context"]
~~~

Example relationship:

~~~mermaid
graph LR
    Jay["Jay"] -->|WORKS_ON| NOVO["NOVO"]
    NOVO -->|USES| Milvus["Milvus"]
    NOVO -->|USES| PostgreSQL["PostgreSQL"]
    NOVO -->|HAS_GOAL| Privacy["Owner-controlled privacy"]
~~~

## Orchestrated request flow

```mermaid
flowchart TB
    Request["API / Chat Request"] --> Orchestrator["NOVO Orchestrator"]
    Orchestrator --> Classify["Intent, Risk, Complexity, Latency, Privacy"]
    Classify --> Choice{"Fast or Deep?"}

    Choice -->|Fast| Fast["Fast Path"]
    Fast --> Recent["Recent Context / Cached Summary"]
    Recent --> Structured["Optional Structured Lookup"]
    Structured --> InputG["Input Guardrails"]
    InputG --> Tier1["Tier 1 Free/Fast Model"]
    Tier1 --> OutputG["Output Guardrails"]
    OutputG --> Reply["Streamed Reply"]

    Choice -->|Deep| Deep["Deep Path"]
    Deep --> Retrieval["Targeted Memory / RAG / Graph"]
    Retrieval --> Plan["Tracked Agent Run and Steps"]
    Plan --> Tier2["Tier 2 Reasoning Model"]
    Tier2 --> OutputG2["Output Guardrails"]
    OutputG2 --> Action{"Action Needed?"}
    Action -->|No| Result["Final Result"]
    Action -->|Yes| ActionG["Action Guardrails"]
    ActionG --> Approval["Policy and Approval"]
    Approval --> Tool["Tool Gateway"]

    Deep -. long work .-> Jobs["Jobs / Outbox / RabbitMQ"]
    Jobs --> Workers["Background Workers"]

    Registry["Model Registry"] --> Tier1
    Registry --> Tier2
    Prompts["Prompt Registry"] --> Tier1
    Prompts --> Tier2
    Control["Kill Switch / Control State"] -. enforces .-> Orchestrator
    Audit["Audit and Decision Trace"] -. records .-> Orchestrator
```

Fast Path still runs required Guardrails. Deep Path adds planning, broad retrieval, durable progress, tools, approvals, and asynchronous execution only when justified.

Central specification: ../architecture/NOVO_ORCHESTRATOR_AND_GUARDRAILS.md.

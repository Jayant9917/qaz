# Memory and Companion Pipeline

## 1. Memory creation and consolidation

~~~mermaid
flowchart TD
    Input["Conversation, tool result, explicit instruction, document, life event"] --> Extract["Candidate Extractor"]
    Extract --> Candidate["Memory Candidate"]
    Candidate --> Classify["Classification and Privacy Policy"]
    Classify --> Score["Importance, confidence, novelty, recurrence, usefulness"]
    Score --> Deduplicate["Duplicate and contradiction detection"]
    Deduplicate --> Decision{"Consolidation decision"}
    Decision -->|reject| Rejected["Rejected with reason"]
    Decision -->|temporary| Short["Short-term memory with TTL"]
    Decision -->|review| Review["Owner review queue"]
    Decision -->|allow| Durable["Long-term memory revision"]
    Review -->|approve/edit| Durable
    Review -->|reject| Rejected
    Durable --> PG["PostgreSQL authority"]
    PG -. permitted embedding .-> Milvus["Milvus"]
    PG -. relation projection .-> Neo4j["Neo4j"]
    PG --> Audit["Memory and audit history"]
~~~

## 2. Reflection Agent

~~~mermaid
sequenceDiagram
    participant S as Scheduler
    participant R as Reflection Agent
    participant P as Policy
    participant H as Conversation History
    participant M as Memory Service
    participant O as Owner Review
    participant A as Audit

    S->>P: Request scheduled reflection
    P-->>S: Allowed scope and budget
    S->>R: Start bounded reflection run
    R->>H: Retrieve permitted recent episodes
    R->>M: Retrieve relevant existing memories
    R->>R: Detect patterns, goals, contradictions, and stale memories
    R->>M: Submit structured insight proposals
    M->>P: Classify each proposal
    alt Requires review
        M->>O: Show evidence, confidence, and proposed change
        O-->>M: Approve, edit, or reject
    else Policy allows
        M->>M: Create revision or candidate
    end
    M->>A: Record sources, decision, and outcome
~~~

The Reflection Agent never silently invents identity. Repetition alone is not truth. Each insight has evidence, confidence, classification, expiry/review rules, and a reversible outcome.

## 3. Companion response assembly

~~~mermaid
flowchart LR
    Message["Owner message"] --> Emotion["Emotional signal inference"]
    Message --> Intent["Intent and goal detection"]
    Emotion --> Policy["Companion privacy policy"]
    Intent --> Context["Continuity context"]
    Memory["Permitted memories"] --> Context
    Goals["Goals and projects"] --> Context
    Style["Owner-controlled style"] --> Personality["Personality Engine"]
    Policy --> Context
    Context --> Response["Response Planner"]
    Personality --> Response
    Response --> Model["Model with minimum context"]
    Model --> Safety["Truthfulness and manipulation check"]
    Safety --> Output["Companion response + explanation"]
~~~

## 4. Emotional observation rules

- Emotional observations are uncertain inferences, not diagnoses.
- Explicit owner statements outrank inference.
- Observations include source, confidence, model/rule version, and expiry.
- They are editable, rejectable, and deletable.
- They cannot authorize tools or change security mode.
- They cannot be used to maximize engagement or dependency.
- Trend aggregation requires sufficient evidence and policy permission.

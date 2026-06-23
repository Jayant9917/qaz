# Computer Control Safety Flow

## Governed execution

~~~mermaid
sequenceDiagram
    actor O as Owner
    participant A as Agent
    participant P as Policy Engine
    participant C as Computer Control Layer
    participant S as Sandbox
    participant E as Evidence Store
    participant U as Audit

    A->>P: Propose typed computer action
    P->>P: Evaluate application, account, target, risk, mode, and budget
    alt Denied
        P-->>A: Deny with reason
    else Approval required
        P->>O: Preview exact action and consequences
        O-->>P: Approve exact action hash
        P-->>C: One-time constrained permit
    else Allowed by bounded policy
        P-->>C: Constrained permit
    end
    C->>S: Start isolated session
    S->>S: Observe current UI and validate expected state
    S->>S: Execute one bounded step
    S->>E: Store policy-approved screenshot/action evidence
    S->>P: Recheck before sensitive transition
    S-->>C: Typed result and final state
    C->>U: Record action, evidence references, and outcome
    C-->>A: Sanitized result
~~~

## Layer responsibilities

- Playwright is preferred for deterministic browser automation.
- Browser-use reasoning may propose navigation steps but does not authorize them.
- The Computer Use Agent plans and observes.
- The Computer Control Layer validates and executes.
- The sandbox restricts filesystem, network, applications, clipboard, credentials, and time.
- Unexpected pages, dialogs, recipients, amounts, downloads, or privilege prompts stop execution.
- Downloads enter MinIO quarantine and the document-ingestion security pipeline.
- The kill switch terminates sessions and revokes pending permits.

## Risk examples

| Action | Default risk |
|---|---|
| Read a permitted public page | Safe |
| Navigate within an authenticated account | Sensitive |
| Fill a form without submission | Sensitive |
| Submit a form or send a message | Sensitive and approval-bound |
| Download a file | Sensitive; quarantine required |
| Upload owner data | Critical data-egress review |
| Delete, purchase, transfer money, or change security | Critical; explicit approval |

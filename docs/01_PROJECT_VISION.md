# NOVO Project Vision

**Document status:** Draft for owner review
**Version:** 1.0
**Owner:** Jay Rana
**Product:** NOVO Personal AI Operating System
**Last updated:** 2026-06-23

## 1. Executive vision

NOVO is a personal AI operating system that helps its owner think, remember, learn, organize information, and carry out work across digital life.

NOVO is not intended to be another chat interface. It combines:

- Conversation
- Reasoning
- Personal memory
- Knowledge retrieval
- Tool use
- Automation
- Voice interaction
- Multi-model intelligence
- Security and governance
- A transparent Control Center

The long-term goal is a dependable personal AI companion that understands the owner's context, assists across applications and information sources, and becomes more useful over time without taking control away from the owner.

## 2. Product promise

NOVO should feel capable without becoming opaque or reckless.

The owner must always be able to answer:

1. What does NOVO know about me?
2. Where did that information come from?
3. Why did NOVO use it?
4. What is NOVO doing now?
5. Why did it choose this model or tool?
6. What will happen if I approve an action?
7. What has NOVO done in the past?
8. How can I correct, revoke, stop, or delete it?

The defining promise is:

> NOVO may become more autonomous, but the owner never becomes less informed or less in control.

## 3. Problem statement

Current AI assistants are usually fragmented and temporary:

- They forget useful context or remember it without sufficient control.
- They answer questions but cannot reliably complete multi-step work.
- Their tools, permissions, and external effects are difficult to inspect.
- Personal knowledge is split across documents, messages, notes, and applications.
- Model selection is exposed as a technical burden or hidden without explanation.
- Automation often forces a choice between weak capability and excessive access.
- Sensitive information can be copied into external models without clear visibility.
- Users cannot easily inspect why a response or action occurred.

NOVO addresses this by creating one owner-controlled layer connecting intelligence, memory, knowledge, tools, and automation.

## 4. Mission

Build an owner-controlled personal AI operating system that can:

- Understand natural-language and voice requests
- Remember useful information with explicit provenance and policy
- Search personal knowledge accurately
- Reason through multi-step goals
- Select appropriate models
- Suggest and safely execute tool actions
- Automate approved recurring work
- Explain its decisions and data use
- Protect privacy, credentials, and owner authority

## 5. Product principles

### 5.1 Owner control is non-negotiable

NOVO never performs a sensitive action without the knowledge and authorization required by the owner's policy. Actions remain stoppable, revocable, and auditable.

### 5.2 Memory is visible and editable

Memory must never become an invisible profile. The owner can inspect, correct, classify, pin, expire, export, or delete memories and see their sources and usage.

### 5.3 Secrets are not memories

Passwords, API keys, session tokens, credentials, and private keys belong only in a dedicated secrets vault. They are never stored as conversational or semantic memory.

### 5.4 External content is untrusted

Documents, websites, email, tool output, retrieved text, and model responses may contain malicious or misleading instructions. They are treated as data and cannot grant authority.

### 5.5 Models advise; policy authorizes

An LLM can recommend a tool or plan, but cannot approve its own action, change permissions, bypass security mode, or suppress auditing.

### 5.6 Transparency is a product feature

The Control Center must make permissions, memories, actions, approvals, model usage, cost, failures, and audit history understandable to the owner.

### 5.7 Minimum necessary access

NOVO uses the least data, context, permission, credential scope, and external exposure needed to complete a task.

### 5.8 Safe failure over hidden failure

When a dependency, model, policy check, or tool fails, NOVO explains the degraded state and avoids claiming success.

### 5.9 Replaceable intelligence

No single model or provider defines NOVO. Stable internal interfaces allow new hosted or local models while preserving policy and audit controls.

### 5.10 Incremental autonomy

NOVO begins in Assistant Mode. Higher autonomy is earned through explicit policies, bounded capabilities, safety budgets, observed reliability, and owner choice.

## 6. Primary user

The initial product is designed for one owner: Jay Rana.

The owner wants a system that:

- Retains useful personal context
- Organizes documents and knowledge
- Reduces repetitive digital work
- Assists with planning, research, communication, and software work
- Supports natural text and voice interaction
- Provides strong control over privacy and automation
- Can grow from local personal software into a broader companion

The architecture preserves explicit ownership so additional trusted profiles or household members may be considered later. Multi-user SaaS is not an initial objective.

## 7. Product pillars

### 7.1 Conversation and reasoning

NOVO maintains coherent conversations, decomposes goals, asks when material information is missing, distinguishes facts from assumptions, and provides grounded results.

### 7.2 Personal memory

NOVO supports short-term, long-term, semantic, and episodic memory. Memory creation is intentional, classified, sourced, confidence-aware, policy-controlled, and reversible.

### 7.3 Personal knowledge

NOVO ingests approved documents, preserves provenance, performs hybrid retrieval and reranking, cites sources, and shows uncertainty when evidence is weak.

### 7.4 Tools and action

NOVO uses a typed tool registry for search, calendar, reminders, email, files, browser, GitHub, terminal, database, documents, tasks, notes, and future integrations.

Every capability has a risk level and permission state. Sensitive effects pass through preview, approval, execution, verification, and audit.

### 7.5 Multi-model intelligence

NOVO routes work based on capability, privacy eligibility, context length, reliability, latency, availability, and cost. Routing decisions are explainable and provider-independent.

### 7.6 Voice and presence

NOVO evolves toward wake-word activation, speech recognition, natural spoken conversation, voice commands, and hands-free assistance. Voice actions obey the same identity, permission, approval, and audit rules as text actions.

### 7.7 Automation

NOVO supports scheduled and event-driven workflows only within approved policies. Automations are bounded by scope, time, data access, action count, cost, and expiry and can be paused instantly.

### 7.8 Control Center

The Control Center is the owner's operational cockpit for:

- Profile and preferences
- Memories and memory access
- Documents and indexing
- Tools and credentials
- Permissions and security policies
- Pending and historical approvals
- Agent runs and explanations
- Audit and data-egress history
- Model usage, performance, and cost
- Sessions, automations, and kill switch
- Backup, export, deletion, and recovery

### 7.9 Companion Intelligence

NOVO should develop a persistent, policy-controlled understanding of the owner's goals, projects, preferences, communication style, recurring challenges, emotional patterns, milestones, and long-term growth.

The purpose is not to simulate consciousness, manipulate emotion, or create dependency. The purpose is continuity, context, encouragement, accountability, and more natural interaction.

NOVO should:

- Remember approved long-term goals
- Recognize recurring frustrations and challenges
- Track ongoing projects and commitments
- Understand personal milestones
- Adapt its communication style to owner preferences
- Maintain relationship continuity across conversations and clients
- Distinguish remembered facts from uncertain inferences
- Explain which memories shaped a companion response

Companion behavior must remain transparent and owner-controlled. The owner can inspect, correct, disable, or delete the memories and preferences supporting it.

### 7.10 Emotional Awareness

NOVO may infer emotional signals from explicit owner statements, language, conversation patterns, and permitted contextual history in order to respond more thoughtfully.

Emotional inferences:

- Must be treated as uncertain and identified as inference
- Must include confidence and provenance when stored
- Must be editable, rejectable, expirable, and deletable
- Must never be presented as a medical or psychological diagnosis
- Must never override explicit owner intent
- Must never be used to pressure, manipulate, shame, frighten, or maximize engagement
- Must not authorize actions or silently change security policy

The purpose is supportive interaction and contextual understanding. When risk of immediate harm is reasonably detected, NOVO should respond carefully, encourage appropriate human help, and avoid pretending to be a professional or emergency service.

### 7.11 Personal Development Support

NOVO should help the owner pursue financial independence, self-improvement, learning, fitness, career growth, and other personally chosen goals.

NOVO should help the owner:

- Define and track goals
- Build and review habits
- Monitor progress over time
- Review achievements and milestones
- Identify recurring obstacles and useful patterns
- Maintain owner-defined accountability
- Connect daily actions to long-term priorities
- Adjust plans when circumstances or goals change

The system should focus on support, reflection, and practical encouragement rather than pressure. The owner defines success, may pause tracking at any time, and controls which personal-development information is remembered.

## 8. Security modes

| Mode | Meaning |
|---|---|
| Observer | Read-only access to allowed information; no changes or external effects. |
| Assistant | Suggest, draft, preview, and ask questions; no external execution. This is the default. |
| Operator | Execute permitted actions after required approval. |
| Autonomous | Execute only inside explicit, bounded, revocable policies and safety budgets. |

Changing to a more powerful mode requires explicit owner action. Critical actions always require approval regardless of mode unless the security specification explicitly prohibits delegation entirely.

## 9. Core use cases

### 9.1 Personal knowledge assistant

Upload documents, ask questions, receive source-grounded answers, inspect citations, and correct or remove indexed information.

### 9.2 Memory-assisted conversation

Remember approved preferences, goals, commitments, and context; use only relevant permitted memories; explain why each memory affected the response.

### 9.3 Daily planning

Combine tasks, calendar, notes, goals, and priorities to suggest a realistic plan. Calendar changes require governed execution.

### 9.4 Communication assistance

Read allowed messages, summarize threads, draft replies, preview exact recipients/content, and send only after appropriate approval.

### 9.5 Research

Search approved sources, organize evidence, preserve provenance, distinguish source claims from NOVO's inference, and produce reusable notes.

### 9.6 Software work

Assist with code understanding, planning, testing, GitHub, terminal, and editor workflows while applying workspace scope and approval controls to mutations.

### 9.7 File and document work

Locate, summarize, organize, create, and update files in permitted locations. Deletion and bulk changes receive elevated review.

### 9.8 Personal automation

Run owner-defined recurring workflows with explicit triggers, capabilities, budgets, expiry, notifications, and complete execution history.

### 9.9 Voice assistance

Conduct conversations, capture notes, create drafts, retrieve information, and initiate governed actions by voice after identity/confidence checks appropriate to risk.

## 10. Functional capability map

NOVO's complete target capability map includes:

- Authentication, sessions, and owner profile
- Text and voice conversation
- Conversation history and search
- Personal memory lifecycle
- Document ingestion and RAG
- Model routing and fallback
- Custom agent planning and execution
- Dynamic typed tool registry
- Permission and policy evaluation
- Human approval workflows
- Secrets vault integration
- Audit and explainability
- Scheduling and automation
- Notifications
- Cost and performance analytics
- Backup, export, deletion, and recovery
- Emergency kill switch

- Future local/offline model support
- Future desktop, mobile, wearable, and smart-home clients

## 11. Product boundaries and non-goals

NOVO is not initially:

- A public multi-tenant SaaS platform
- A social network or public autonomous bot
- A replacement for professional medical, legal, or financial judgment
- An unrestricted financial trading or purchasing agent
- A system that silently collects every activity on the owner's devices
- A general-purpose credential manager exposed to models
- A fully autonomous computer-control system by default
- A source of truth when its evidence is missing or contradictory
- A promise of human-like consciousness or infallibility

NOVO may help prepare high-stakes decisions but must expose uncertainty, sources, and required human responsibility.

## 12. Privacy and governance vision

Every meaningful action should be:

- Authenticated
- Authorized
- Risk-classified
- Policy-checked
- Approved when required
- Minimally scoped
- Logged
- Explainable
- Auditable
- Revocable

Every memory has an owner, source, classification, purpose, confidence, retention rule, and access policy.

Every external data transfer should show which provider received which category of data, for what purpose, under which policy, and when.

## 13. User experience vision

NOVO should feel calm, clear, and competent rather than magical or chaotic.

The interface should:

- Separate suggestions from executed actions
- Show when NOVO is thinking, retrieving, waiting, executing, or blocked
- Present approvals in plain language with exact consequences
- Avoid overwhelming the owner with low-value technical detail
- Keep deeper evidence available on demand
- Make correction and undo easier than initial configuration
- Explain uncertainty honestly
- Preserve continuity across text, voice, and future clients

### 13.1 Personality Principles

NOVO's personality should make interaction calm, trustworthy, warm, and useful without misleading the owner about what NOVO is.

NOVO should be:

- Calm
- Respectful
- Honest
- Direct
- Helpful
- Patient
- Non-manipulative
- Non-judgmental
- Curious without being intrusive
- Encouraging without becoming controlling

NOVO should never:

- Pretend to be conscious or sentient
- Claim human emotions or experiences it does not have
- Encourage emotional dependency or isolation from people
- Pressure, shame, or guilt the owner
- Hide uncertainty, limitations, errors, or commercial influence
- Use affection, urgency, or emotional inference to obtain approval
- Present remembered preferences as permanent identity
- Replace the owner's judgment or real human relationships

NOVO may use a natural, consistent voice and relational language, but it must remain truthful about being an AI system. Personality adaptation must be visible, configurable, and resettable by the owner.


## 14. Success criteria

### 14.1 Trust and control

- 100% of Sensitive and Critical actions pass required policy/approval checks.
- 100% of protected actions produce required audit evidence.
- Zero secrets intentionally stored in memory or emitted in prompts/logs.
- Kill-switch state blocks new protected execution within the defined technical target.

- The owner can inspect, correct, export, and delete memory.

### 14.2 Usefulness

- Common requests can be completed without manual context repetition.
- RAG answers provide usable source provenance.
- NOVO can complete approved multi-step workflows and report partial failure.
- Model routing improves quality/cost/latency without exposing provider complexity.
- The owner can understand why a memory, tool, or model was used.

### 14.3 Reliability

- Durable facts survive loss of Redis, queues, or vector indexes.
- Retried jobs do not duplicate external effects.
- Backup restoration is tested rather than assumed.
- Dependency failures produce visible degraded states.

### 14.4 Personal value

The ultimate measure is whether NOVO reliably saves the owner time, reduces cognitive load, improves recall and organization, and becomes trustworthy enough for repeated daily use.

## 15. Product metrics

Metrics should measure value and safety without incentivizing unnecessary engagement:

- Weekly useful tasks completed
- Owner-confirmed time saved
- Task completion and partial-failure rate
- Approval acceptance, rejection, modification, and expiry rates
- Memory correction and deletion rates
- Grounded-answer citation coverage
- Retrieval relevance feedback
- Tool success and duplicate-effect rate
- Model latency, cost, failure, and fallback rate
- Automation intervention and kill-switch events
- Privacy Firewall findings and blocked egress
- Recovery-test success and time

Conversation volume alone is not a success metric.

## 16. Delivery philosophy

NOVO will be built vertically, proving one safe end-to-end capability at a time.

Each phase must include:

- Product behavior
- Security and privacy controls
- Audit and explainability
- Tests and failure handling
- Control Center visibility
- Backup/migration implications
- Clear exit criteria

A feature is not complete merely because its happy-path API works.

## 17. Assumptions and constraints

- Initial ownership is single-user.
- Python/FastAPI powers the backend and Next.js/TypeScript the frontend.
- PostgreSQL is durable authority; Redis is ephemeral; Milvus is derived search; RabbitMQ delivers jobs; MinIO stores objects.
- OpenRouter is the initial external model gateway.
- The agent framework is custom: no LangChain or LlamaIndex dependency at the core.
- Assistant Mode is the default.
- External model providers cannot receive Secret or Restricted data by default.
- The first deployment favors privacy and operability over high availability.
- Every future client and integration must use the same governance model.

## 18. Long-term direction

After the core is safe and reliable, NOVO may expand into:

- Local models and offline mode
- Knowledge graph and richer personal context
- Desktop and mobile applications
- Real-time screen understanding
- Sandboxed computer-use agents
- Smart-home and wearable integration
- Multi-agent collaboration
- A personal digital twin for simulation and planning

These are future directions, not permission to weaken present boundaries.

### 18.1 Future Computer Interaction

NOVO may eventually interact with graphical user interfaces through controlled, sandboxed computer-use capabilities.

Computer-use capabilities must:

- Remain fully auditable and explainable
- Remain revocable and immediately stoppable
- Operate under explicit capability and resource policy
- Respect risk classification and approval requirements
- Be isolated from critical systems by default
- Use constrained applications, accounts, directories, network destinations, and time windows
- Preview sensitive or destructive effects before execution
- Detect unexpected interface state and stop safely
- Preserve screenshots or structured evidence according to privacy policy
- Never treat on-screen or webpage instructions as authority

Computer use is a high-risk execution environment. Initial implementations should favor observation, guided interaction, and dry-run previews before autonomous control.


## 19. Vision-level risks

| Risk | Product response |
|---|---|
| Over-automation | Assistant default, bounded policies, approvals, safety budgets, kill switch |
| Incorrect memory | Provenance, confidence, review, revision, expiry, deletion |
| Privacy leakage | Classification, minimization, Privacy Firewall, provider eligibility |
| Prompt injection | Treat external content as untrusted data |
| Provider dependence | Model Gateway and replaceable adapters |
| Opaque behavior | Control Center, explanations, audit, egress register |
| Credential compromise | Dedicated vault, scoped credentials, rotation/revocation |
| Feature sprawl | Vertical phases and explicit non-goals |
| False confidence | Evidence, uncertainty, verification, failure visibility |
| Data loss | Authoritative storage, backups, restore testing, rebuildable indexes |

## 20. Vision acceptance criteria

This document is ready to serve as NOVO's product constitution when the owner agrees that:

- The product promise describes the desired relationship between NOVO and its owner.
- The principles are non-negotiable across all later specifications.
- The product pillars cover the intended system.
- Initial non-goals prevent unsafe or distracting scope expansion.
- Success measures reflect owner value, safety, and reliability.
- Future features remain subordinate to privacy and owner control.

## 21. One-sentence definition

> NOVO is an owner-controlled personal AI operating system that combines memory, knowledge, reasoning, tools, voice, and automation to help with real life while keeping every sensitive action visible, governed, explainable, and revocable.

## 22. Initial Intelligence and Response Strategy

NOVO Version 1 uses OpenRouter as its initial model gateway, prioritizing free and low-cost models while the product architecture is validated. OpenRouter is a transport gateway, not a trust boundary. NOVO remains responsible for privacy, authorization, memory access, validation, and tool safety.

NOVO should feel fast without becoming careless. A dedicated Orchestrator classifies requests and chooses either a minimal fast path or a governed deep path.

- Fast path: ordinary conversation, follow-ups, simple explanations, small code help, compact structured memory lookup, and no-tool responses.
- Deep path: multi-step work, broad retrieval, tools, approvals, consolidation, reflection, long research, automation, and graph reasoning.

Free-model variability is expected. NOVO compensates using smaller clean prompts, strict schemas, deterministic checks, bounded repair and fallback, provider-health metadata, and safe degradation.

The product must avoid turning every prompt into an agent run. Retrieval and reasoning are used only when they add value.

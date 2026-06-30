# NOVO Frontend Architecture

**Status:** Draft for owner review
**Owner:** Jay Rana
**Framework:** Next.js and TypeScript
**Updated:** 2026-06-30

## 1. Purpose

The frontend is NOVO's web Control Center. It is not the main daily-use assistant once the desktop app exists. It must make capability, state, risk, evidence, memory, approvals, and failures understandable without pretending UI controls are security enforcement.

The NOVO Desktop Assistant is the primary daily interaction surface for voice, presence, chat, and task flow. This web frontend remains the administrative and inspection surface.

## 2. Principles

- Calm and transparent
- Fast perceived response
- Suggestions visually distinct from executed actions
- Exact approval consequences
- Progressive disclosure
- Accessible
- Responsive
- Error and degraded states are first-class
- No secrets in browser storage
- Server remains authorization authority

## 3. Technology

- Next.js App Router
- TypeScript strict mode
- React
- Tailwind CSS
- shadcn/ui
- React Query for server state
- Framer Motion only where state comprehension improves
- Zod or generated schemas at client boundaries
- Playwright for E2E
- Component testing framework selected during initialization

## 4. Application areas

- Chat
- Conversations
- Approvals
- Agent Runs
- Memory Center
- Documents/RAG
- Companion and Goals
- Tools and Integrations
- Permissions and Policies
- Models and Prompts
- Automations
- Audit and Egress
- Analytics
- System Controls
- Settings
- Recovery

The web chat route remains useful for testing, fallback, and detailed conversation review, but the desktop assistant owns the main talk-to-NOVO experience.

## 5. Route structure

Suggested routes:

- /
- /chat
- /chat/{conversation_id}
- /approvals
- /runs
- /runs/{id}
- /memory
- /memory/{id}
- /documents
- /documents/{id}
- /companion
- /goals
- /projects
- /tools
- /integrations
- /permissions
- /policies
- /models
- /prompts
- /automations
- /audit
- /egress
- /analytics
- /settings
- /system
- /recovery

## 6. Layout

Desktop:

- Left navigation
- Main workspace
- Optional right evidence/inspector panel
- Persistent system state indicator
- Approval/kill-switch notification area

Mobile:

- Collapsible navigation
- Full-screen task surfaces
- Bottom sheets for evidence and approvals
- No hidden critical consequences

## 7. State layers

### Local UI state

Open panels, draft input, selection, transient filters.

### Server state

React Query manages resources, pagination, invalidation, retries, and optimistic updates where safe.

### Streaming state

Dedicated response/run event reducer keyed by response or run ID.

### Durable state

Always retrieved from API. Browser state is not authoritative.

## 8. Authentication UI

- Login/passkey/TOTP
- Device/session list
- Session revocation
- Reauthentication modal
- Recovery flow
- Lockout and rate-limit feedback
- No sensitive token display

Session cookie remains HttpOnly. The browser reads only the companion CSRF cookie and never stores bearer tokens in localStorage.

## 9. Chat experience

Web chat shows:

- Owner and NOVO messages
- Streaming status
- Fast/Deep route indicator when useful
- Model/provider disclosure on demand
- Citations
- Tool proposals
- Approval pause
- Job progress
- Warnings and degraded state
- Stop/cancel
- Regenerate with explanation
- Memory-use indicator

Do not expose hidden chain-of-thought.

The desktop assistant may present the same conversation through a more compact, voice-first surface. The backend response contract should support both clients.

## 10. Composer

Supports:

- Text
- Attachments
- Document scope
- Response mode preferences
- Optional model policy
- Stop generation
- Keyboard accessibility
- Draft persistence without sensitive browser leakage

Upload begins only after authorized upload request.

## 11. Streaming

SSE client:

- Tracks last event ID
- Reconnects safely
- Deduplicates events
- Separates tokens from final committed message
- Handles approval/job transitions
- Handles cancellation
- Shows partial response status
- Never interprets missing completion as success

## 12. Approval experience

Approval card displays:

- Exact action
- Account/integration
- Target/recipient
- Content or payload summary
- Data leaving NOVO
- Risk
- Reason
- Reversibility
- Expiry
- Reauthentication requirement

Actions:

- Approve
- Reject
- Edit proposal
- Cancel

Editing creates a new proposal. UI never edits an approved action in place.

## 13. Memory Center

Views:

- Active
- Proposed
- Disputed
- Archived
- Deleting
- Deleted metadata where permitted

Capabilities:

- Search/filter
- Provenance
- Revisions
- Confidence/classification
- Access history
- External-use history
- Correct
- Confirm/reject
- Resolve contradiction
- Archive/restore
- Projection controls
- Export/delete
- Reflection and emotional-awareness settings

## 14. Document Center

Shows:

- Upload
- Quarantine/scan state
- Ingestion stages
- Current and prior versions
- Chunk/embedding status
- Classification
- Tags
- Retrieval metrics
- Source preview
- Re-index/retry
- Citation usage
- Deletion progress
- Safe failures

## 15. Citation and evidence panel

For a selected claim:

- Citation label
- Document/version
- Page/section
- Evidence excerpt
- Relevance reason
- Conflict indicator
- Retrieval mode
- Open source
- Report mismatch

Evidence remains access-controlled.

## 16. Agent Runs

List and detail show:

- Goal
- Trigger
- State
- Path
- Plan and steps
- Current activity
- Decisions
- Retrieval/model/tool reasons
- Approvals
- Budgets
- Cost
- Completed effects
- Failures
- Pause/cancel
- Final result

Internal secrets and unsafe raw payloads remain hidden.

## 17. Tools and Integrations

- Tool/capability catalog
- Enabled state
- Risk
- Permissions
- Connected accounts
- Granted provider scopes
- Credential health without secret
- Last use
- Success/failure
- Disable/revoke
- Test connection
- Capability expansion warning

## 18. Permission Center

Supports:

- Allow, Deny, Ask
- Capability/integration/resource scope
- Classification/destination
- Time/expiry
- Safety budgets
- Policy simulation
- Conflict and precedence explanation
- Version/change history

Dangerous broad Allow displays a clear warning.

## 19. Policies

- Active version
- Draft versions
- Diff
- Validation/evaluation
- Activation/retirement
- Simulation
- Rollback
- Audit history

UI does not permit invalid raw policy activation.

## 20. Companion Center

- Communication style
- Personality controls
- Goals/projects
- Milestones
- Interests/life events
- Emotional observations
- Confidence and source
- Opt-in/disable
- Reset
- Reflection proposals
- Personal development review

Language must avoid diagnosis or dependency.

## 21. Models

- Registry
- Provider/model
- Free/paid/local tier
- Capability
- Context
- Eligibility
- Health
- Latency
- Quality
- Cost
- Fallback order
- Route simulator
- Usage

## 22. Prompts

Privileged view:

- Template/purpose
- Versions
- Hash
- Variable schema
- Evaluation
- Active binding
- Diff
- Activate/retire/rollback

Prompt changes require authorization and audit.

## 23. Automations

- List and status
- Trigger
- Workflow summary
- Permissions
- Policy version
- Safety budgets
- Expiry
- Last/next run
- Run history
- Enable/disable
- Manual run
- Cancel

## 24. Audit and egress

Audit timeline filters actor, action, resource, risk, outcome, date, and correlation.

Egress view shows destination, purpose, categories, classification ceiling, model/tool, policy decision, and time.

Sensitive payload is not duplicated.

## 25. System controls

Persistent visibility:

- Security mode
- Kill switch
- Tool enablement
- Automation enablement
- External model enablement
- Degraded dependencies
- Active sessions
- Pending Critical approvals

Kill switch is easy to activate and deliberately harder to deactivate.

The Control Center remains the preferred place for detailed system controls even after the desktop app exists. The desktop app may expose emergency stop/kill-switch affordances, but detailed recovery and inspection belong here.

## 26. Recovery mode

Minimal local UI independent of models/tools:

- Login/re-authentication
- System health
- Kill switch
- Session revocation
- Policy repair
- Audit inspection
- Backup/restore status
- Integration revocation
- Safe restart

## 27. Loading and progress

Use:

- Skeleton for predictable reads
- Explicit stage for jobs
- Percentage only when meaningful
- Last heartbeat
- Cancel state
- Retry guidance
- No fake progress

## 28. Error experience

Errors include safe message, code, request ID, retryability, and next action.

Differentiate:

- Denied
- Approval required
- Validation
- Conflict
- Dependency degraded
- Timeout
- Cancelled
- Partial success
- Unknown outcome

## 29. Accessibility

- WCAG AA target
- Keyboard navigation
- Visible focus
- Semantic landmarks
- Screen-reader labels
- Contrast
- Reduced motion
- Captions/transcripts
- Non-color-only risk/status
- Accessible charts and tables
- Approval consequence readable without hover

## 30. Responsive and performance

- Route-level code splitting
- Paginated tables
- Virtualize only when needed
- Streaming chat
- Avoid large client bundles
- Image/file preview limits
- Server components for suitable reads
- Query prefetch for likely navigation
- Measure interaction and response latency
- Keep Control Center usable during model outage

## 31. Security

- No bearer token in localStorage
- HttpOnly session cookie plus CSRF cookie transport
- CSRF protection
- Strict CSP
- Safe Markdown rendering
- HTML sanitization
- Link/domain warnings
- No raw provider HTML
- No secret logging
- Clipboard caution for secrets
- Presigned URL expiry
- Frame protection
- Dependency review
- Server-side authorization always

## 32. Analytics privacy

Product analytics should be local or privacy-preserving where possible.

Do not record raw message, memory, document, prompt, token, or secret in analytics events.

## 33. Component architecture

Reusable components:

- StatusBadge
- RiskBadge
- ClassificationBadge
- ApprovalCard
- EvidenceCard
- SourceCitation
- RunTimeline
- JobProgress
- AuditTimeline
- PolicyDecision
- EmptyState
- ErrorPanel
- KillSwitchControl
- DataTable
- InspectorPanel

## 34. Data-fetching rules

- Feature modules own query keys.
- Mutations invalidate exact dependent resources.
- Optimistic updates only for reversible low-risk UI changes.
- Approval, policy, permission, and control-state mutations wait for server.
- Errors preserve current authoritative display.
- Streaming completion triggers canonical refetch.

## 35. Testing

- Component states
- Accessibility
- API contract mocks
- Streaming reconnect
- Approval flows
- Session expiry
- Permission denial
- Memory correction/deletion
- Document ingestion
- Citation panel
- Agent cancel
- Kill switch
- Recovery mode
- Responsive layouts
- XSS/unsafe Markdown

## 36. Definition of done

- Every major backend capability has a transparent owner-facing surface.
- Capabilities used by the desktop assistant have corresponding Control Center visibility where review, correction, audit, or configuration is required.
- Suggestions, approvals, execution, and completion are distinct.
- Memory, evidence, policy, audit, and egress are inspectable.
- Critical controls remain usable during model outage.
- Accessibility and responsive tests pass.
- Browser storage contains no secrets.
- UI never substitutes for server authorization.

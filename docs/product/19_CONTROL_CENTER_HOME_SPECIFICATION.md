# NOVO Control Center Home Page Specification

**Route:** `http://localhost:3000/`  
**Frontend entrypoint:** `frontend/src/app/page.tsx`  
**Main component:** `frontend/src/app/control-center-shell.tsx`  
**Shared styling:** `frontend/src/app/globals.css`  
**Health component:** `frontend/src/app/backend-health-card.tsx`

## 1. Purpose

The NOVO home page is the public-facing entry surface for the web Control Center.

It is not the main chat experience and it is not the desktop assistant. Its job is to introduce NOVO, show that the backend is available, identify the current product phase, and direct the owner to authenticated Control Center areas.

The page is designed around three principles:

1. **Identity first** — the owner should understand that NOVO is owner-controlled.
2. **Evidence visible** — system status and backend health should be visible before advanced actions.
3. **Safe expansion** — the product should communicate that governance comes before automation.

The home page is therefore a calm product shell and system-status gateway, not a data-heavy dashboard.

## 2. Current visual reference

The current page is a dark, minimal Control Center interface with:

- Black background.
- White primary typography.
- Muted gray supporting text.
- Thin gray borders.
- Rounded cards.
- A compact top navigation.
- A large hero message on the left.
- A NOVO visual preview/video on the right.
- Floating backend and health cards over the preview.
- Three supporting principle cards below the hero.
- A current-phase card aligned at the bottom-right.

The design communicates that NOVO is an operating system interface rather than a standard marketing landing page.

## 3. Page structure

The page hierarchy is:

```text
Home page `/`
└── Control Center shell
    ├── Sticky top navigation
    │   ├── NOVO brand lockup
    │   ├── Primary navigation links
    │   ├── Current phase badge
    │   └── Sign in button
    ├── Main control grid
    │   └── Hero panel
    │       ├── Hero copy
    │       ├── Hero actions
    │       ├── Visual preview frame
    │       │   ├── Background video
    │       │   ├── Backend live badge
    │       │   └── Live health detail card
    │       └── Three product-principle cards
    └── Current phase footer card
```

## 4. Top navigation

The top bar uses the `control-topbar` class and remains sticky while the page is scrolled.

### 4.1 Brand lockup

The left side contains:

- A rounded square `N` brand mark.
- The title `NOVO Control Center`.
- The subtitle `Owner-first AI OS`.

This tells the user that the page is the administrative and governance surface of NOVO.

### 4.2 Navigation links

The current navigation links are:

| Label | Destination | Purpose |
|---|---|---|
| Overview | `#overview` | Returns to the home hero section |
| Chat | `/chat` | Opens the browser chat interface |
| Memory | `/memory` | Opens the Memory Center |
| Identity | `#identity` | Intended identity section anchor; no current home section is rendered at this anchor |
| Sessions | `#sessions` | Intended sessions section anchor; no current home section is rendered at this anchor |
| Permissions | `/permissions` | Opens the permissions Control Center page |
| Audit | `/audit` | Opens the audit page |
| Settings | `/settings` | Opens the settings page |

The `Memory` item was added after the Memory Center implementation and points to the live memory interface.

The `Identity` and `Sessions` links are currently forward-looking anchors. The actual session and identity UI exists in reusable components and other Control Center surfaces, but those components are not currently rendered inside the home hero page.

### 4.3 Current phase badge

The right side of the top bar displays:

- Label: `Current phase`
- Value: `E2 frontend control center`
- A safe-status dot

This badge communicates the current development stage rather than a live backend state.

### 4.4 Sign in button

The top-right `Sign in` button links to:

```text
/login
```

It does not perform authentication directly. It takes the owner to the login flow.

## 5. Hero panel

The main hero uses the `hero-panel` class and is the primary visual area of the page.

### 5.1 Eyebrow

The hero begins with:

```text
Visible product layer
```

This identifies the page as the visible interface layer of a larger governed system.

### 5.2 Main heading

The current heading is:

```text
The place where NOVO becomes an interface.
```

The heading is intentionally large and split over multiple lines through a constrained maximum width. It positions the home page as the interface layer of the NOVO operating system.

### 5.3 Supporting description

The current supporting text is:

```text
This shell is the owner-facing Control Center: calm, direct, and built to surface system state before any advanced automation appears.
```

This explains the product philosophy:

- Owner-facing.
- Calm rather than noisy.
- Direct rather than hidden.
- System-state aware.
- Governance before automation.

### 5.4 Hero actions

The hero contains two actions.

#### Sign in

- Style: primary white button.
- Destination: `/login`.
- Purpose: start or resume the owner authentication flow.

#### View identity

- Style: secondary outlined button.
- Destination: `#identity`.
- Intended purpose: scroll to an identity section.
- Current limitation: the home page does not currently render an element with the `identity` ID, so this action does not currently reveal a dedicated identity panel.

## 6. Visual preview frame

The right side of the hero contains the visual preview frame.

### 6.1 Frame behavior

The frame:

- Uses a 16:11 aspect ratio.
- Has a minimum height of 420 pixels.
- Has a maximum height of 560 pixels.
- Has rounded corners.
- Uses a dark background with purple radial glow layers.
- Uses a thin translucent border.
- Uses a large shadow to separate the frame from the black page.

### 6.2 Background video

The frame loads this public asset:

```text
/06037dd15f67cd8a21a4d627c5854160.mp4
```

The video is configured with:

- `autoPlay`
- `muted`
- `loop`
- `playsInline`
- `preload="metadata"`

The video is visual decoration and product presence. It is not connected to backend state and does not control NOVO functionality.

### 6.3 Overlay

The frame has a visual overlay consisting of:

- A central purple radial highlight.
- A subtle top-to-bottom black gradient.

The overlay does not receive pointer events, so it does not block the health cards or the visual frame.

## 7. Backend live badge

The top-left floating card inside the visual frame displays:

- A safe-status dot.
- Label: `Backend`.
- Value: `live`.

This is currently a static visual status badge. The live backend request is performed by the separate `BackendHealthCard` on the top-right of the frame.

## 8. Live backend health card

The `BackendHealthCard` is a client-side component that checks the backend after the page loads.

### 8.1 Request

It calls:

```text
GET {API_BASE}/health/live
```

The API base is resolved by `frontend/src/lib/api.ts`:

- `NEXT_PUBLIC_NOVO_API_URL` when configured.
- Otherwise `http://{current-browser-host}:8000/api/v1` in the browser.
- Otherwise `http://localhost:8000/api/v1` during server-side evaluation.

### 8.2 Request behavior

The health request:

- Does not require authentication.
- Uses `cache: "no-store"`.
- Uses an `AbortController`.
- Times out after 2.5 seconds.
- Cancels when the component unmounts.

### 8.3 Initial state

Before the backend responds, the card displays:

```text
Checking backend status...
```

The status is `loading`.

### 8.4 Successful response

The component expects a response shaped approximately like:

```json
{
  "status": "alive",
  "service": "NOVO API",
  "version": "0.1.0"
}
```

The card displays:

- Health detail: `{service} ? v{version}` according to the current component string.
- A status pill containing the returned status.

The intended visual result is similar to:

```text
Health detail
NOVO API ? v0.1.0       alive
```

### 8.5 Non-success response

If the response is not successful, the card displays:

```text
Health endpoint returned {status code}
```

The state becomes `degraded`.

### 8.6 Network failure

If the backend cannot be reached or the request times out, the card displays:

```text
Backend not reachable
```

The state becomes `offline`.

### 8.7 Health state styling

The health pill uses a state-specific class:

- `health-loading`
- `health-alive`
- `health-degraded`
- `health-offline`

The page should make degraded and offline states visible rather than pretending the system is ready.

## 9. Principle cards

Below the hero split are three support cards generated from the `focusItems` array.

### 9.1 Identity first

Title:

```text
Identity first
```

Description:

```text
Every screen keeps owner identity, session freshness, and current security mode visible.
```

Product meaning:

- NOVO must know which owner is active.
- Sessions should be visible and understandable.
- Security mode should not be hidden behind settings.

### 9.2 Evidence visible

Title:

```text
Evidence visible
```

Description:

```text
Audit, control state, and backend health stay close to the actions they explain.
```

Product meaning:

- Actions should have visible context.
- The owner should be able to inspect audit and system state.
- Backend health should be observable near the product interface.

### 9.3 Safe expansion

Title:

```text
Safe expansion
```

Description:

```text
The shell is ready for permissions, audit, and settings before advanced automation arrives.
```

Product meaning:

- NOVO expands in stages.
- Governance surfaces arrive before tools and automation.
- The interface should not imply capabilities that are not ready.

## 10. Current phase footer

The bottom-right phase card repeats the development status.

Visible content:

- Label: `Current phase`
- Help text: `The active phase and what this screen is meant to show.`
- Value: `E2 frontend control center`
- Description: `Dashboard shell + live backend visibility.`

This card is a product-development indicator. It is not a backend health reading and does not change automatically from API responses.

## 11. Styling system

The home page uses shared styles from `frontend/src/app/globals.css`.

### 11.1 Global visual language

- Color scheme: dark.
- Page background: black.
- Primary text: white.
- Secondary text: gray.
- Tertiary text: darker gray.
- Borders: translucent white/gray.
- Accent: white primary actions and purple visual glow.
- Safe state: mint/green.
- Danger state: red.
- Focus ring: white.

### 11.2 Typography

- Font family: `Inter`, with fallback to `Inter Placeholder` and sans-serif.
- Body font size: 12px.
- Body weight: 500.
- Main home heading uses a responsive `clamp()` size and tight letter spacing.
- Hero text is deliberately large and high contrast.

### 11.3 Cards

Cards generally use:

- Rounded corners between 18px and 34px.
- Translucent black/white backgrounds.
- Thin borders.
- Spacious padding.
- Muted supporting text.

### 11.4 Buttons

Primary buttons:

- White background.
- Black text.
- Rounded corners.

Secondary buttons:

- Translucent background.
- Border.
- White text.

Both have hover and active movement transitions.

## 12. Responsive behavior

The page adapts to smaller screens through CSS media queries.

At widths below approximately 1120px:

- The hero split becomes a single-column layout.
- Support cards reduce to two columns.
- The phase footer aligns to the start.
- The bottom phase card uses full width.

At widths below approximately 980px:

- The overall control grid becomes one column.
- The hero panel is no longer sticky.
- Support cards become one column.
- Top navigation wraps.

The intended mobile behavior is to preserve:

- Brand identity.
- Sign-in access.
- Backend health visibility.
- Hero message readability.
- Principle-card readability.

## 13. Data and authority boundaries

The home page is primarily a presentation shell.

It directly reads only public backend health data through `BackendHealthCard`.

It does not directly read:

- Memory data.
- Documents.
- Email.
- Tools.
- Credentials.
- Model providers.
- Database records.

Authenticated operational data is handled by dedicated Control Center routes and components such as:

- `/chat`
- `/memory`
- `/permissions`
- `/audit`
- `/settings`
- `/system`

The backend remains the authorization authority.

## 14. Current home-page limitations

The current implementation is a Control Center shell, not a complete dashboard.

Current limitations:

- Identity and session panels are not rendered directly on `/`.
- `View identity` points to `#identity`, but no current home element uses that ID.
- `Sessions` points to `#sessions`, but no current home element uses that ID.
- The top-left `Backend live` badge is static and separate from the live health request.
- The home page does not show current user details.
- The home page does not show permissions count.
- The home page does not show audit activity.
- The home page does not show kill-switch state.
- The home page does not show security mode from the backend.
- The phase text is hardcoded to `E2 frontend control center`.
- The preview video is decorative rather than state-aware.
- The health card checks once on mount and does not continuously poll.
- There is no retry button on the health card.
- There is no authenticated dashboard redirect after login.

The reusable `OverviewPanels`, `SessionPanel`, `ControlStatePanel`, `PermissionsPanel`, and `AuditPanel` components already provide much of the missing operational visibility on other routes.

## 15. Recommended future home-page evolution

The next version of the home page should keep the current calm hero design while adding live, owner-relevant state below or beside it.

Recommended additions:

### Identity block

- Current owner name.
- Session status.
- Session expiry.
- Sign-out action.
- Security mode.

### System state block

- Kill-switch state.
- Tools enabled/disabled.
- Automations enabled/disabled.
- External model state.
- Control-state version.

### Evidence block

- Recent audit event.
- Last backend health check.
- Current degraded services.
- Link to audit history.

### Quick actions

- Open Chat.
- Open Memory Center.
- Open Permissions.
- Open Audit.
- Open System Controls.

### Honest phase state

The phase badge should eventually come from a versioned product configuration or release-state endpoint rather than hardcoded text.

### Health recovery

Add:

- Refresh health button.
- Last checked time.
- Retry state.
- Readiness status in addition to liveness.
- Links to startup instructions when dependencies are unavailable.

## 16. Definition of done for the complete home page

The home page should be considered complete when it:

1. Introduces NOVO clearly.
2. Explains that the page is the owner-facing Control Center.
3. Shows whether the backend is alive, degraded, or offline.
4. Shows the current authenticated owner when signed in.
5. Shows session freshness and security mode.
6. Shows kill-switch and protected-system state.
7. Links to Chat, Memory, Permissions, Audit, Settings, and System Controls.
8. Provides visible recovery guidance when the backend is unavailable.
9. Keeps evidence close to the state or actions it explains.
10. Does not claim that advanced automation exists before it is implemented.
11. Remains responsive on desktop and mobile.
12. Preserves the backend as the authority for protected state.

## 17. Run and test

Start the frontend from the repository root:

```powershell
cd D:\NOVO
pnpm --filter @novo/frontend dev
```

Open the home page:

```text
http://localhost:3000/
```

The backend health card expects the API to be available at:

```text
http://localhost:8000/api/v1/health/live
```

Run frontend checks:

```powershell
cd D:\NOVO
pnpm --filter @novo/frontend lint
pnpm --filter @novo/frontend typecheck
pnpm --filter @novo/frontend test
```

## 18. Product meaning

The home page represents NOVO's central product idea:

> NOVO should become more capable only after the owner can see, understand, and control the system.

It is intentionally not a busy analytics dashboard. It is the calm front door to a governed personal AI operating system.

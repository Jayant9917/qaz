import { BackendHealthCard } from "./backend-health-card";

const navItems = [
  { label: "Overview", href: "#overview" },
  { label: "Chat", href: "/chat" },
  { label: "Memory", href: "/memory" },
  { label: "Identity", href: "#identity" },
  { label: "Sessions", href: "#sessions" },
  { label: "Permissions", href: "/permissions" },
  { label: "Audit", href: "/audit" },
  { label: "Settings", href: "/settings" },
];

const focusItems = [
  {
    title: "Identity first",
    description: "Every screen keeps owner identity, session freshness, and current security mode visible.",
  },
  {
    title: "Evidence visible",
    description: "Audit, control state, and backend health stay close to the actions they explain.",
  },
  {
    title: "Safe expansion",
    description: "The shell is ready for permissions, audit, and settings before advanced automation arrives.",
  },
];

export function ControlCenterShell() {
  return (
    <main className="control-center-shell" id="overview">
      <header className="topbar control-topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            N
          </div>
          <div className="brand-copy">
            <div className="brand-title">NOVO Control Center</div>
            <div className="brand-subtitle">Owner-first AI OS</div>
          </div>
        </div>

        <nav className="topnav" aria-label="Primary navigation">
          {navItems.map((item) => (
            <a href={item.href} key={item.label} className="topnav-link">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="topbar-actions">
          <div className="phase-badge" aria-label="Current phase summary">
            <span className="status-dot status-safe" aria-hidden="true" />
            <div>
              <span className="phase-label">Current phase</span>
              <strong>E2 frontend control center</strong>
            </div>
          </div>
          <a className="signin-button" href="/login">
            Sign in
          </a>
        </div>
      </header>

      <section className="control-grid" aria-label="NOVO control center">
        <section className="hero-panel" aria-labelledby="control-center-title">
          <div className="hero-split">
            <div className="hero-copy-column">
              <div className="eyebrow">Visible product layer</div>
              <h1 id="control-center-title">The place where NOVO becomes an interface.</h1>
              <p className="lead hero-lead">
                This shell is the owner-facing Control Center: calm, direct, and built to surface system state before
                any advanced automation appears.
              </p>

              <div className="hero-actions">
                <a className="primary-button" href="/login">
                  Sign in
                </a>
                <a className="secondary-button" href="#identity">
                  View identity
                </a>
              </div>
            </div>

            <div className="hero-visual-column" aria-label="NOVO dashboard preview">
              <div className="hero-frame">
                <video className="hero-video" autoPlay muted loop playsInline preload="metadata">
                  <source src="/06037dd15f67cd8a21a4d627c5854160.mp4" type="video/mp4" />
                </video>
                <div className="hero-overlay" />
                <div className="hero-card hero-card-left">
                  <span className="status-dot status-safe" aria-hidden="true" />
                  <div>
                    <div className="card-label">Backend</div>
                    <strong>live</strong>
                  </div>
                </div>
                <BackendHealthCard />
              </div>
            </div>
          </div>

          <div className="hero-support-grid" aria-label="Control center highlights">
            {focusItems.map((item) => (
              <article key={item.title} className="rail-card focus-card">
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="phase-footer" aria-label="Current phase summary">
          <section className="rail-card phase-card phase-card-bottom">
            <div className="card-label">Current phase</div>
            <p className="card-help">The active phase and what this screen is meant to show.</p>
            <strong>E2 frontend control center</strong>
            <p>Dashboard shell + live backend visibility.</p>
          </section>
        </section>
      </section>
    </main>
  );
}

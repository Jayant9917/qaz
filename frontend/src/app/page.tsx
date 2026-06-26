const navigation = [
  { label: "Overview", active: true },
  { label: "Identity" },
  { label: "Permissions" },
  { label: "Audit Logs" },
  { label: "System Status" },
];

const cards = [
  {
    title: "Security foundation",
    body: "Identity, sessions, permissions, and audit are the first live surfaces so the owner always stays in control.",
  },
  {
    title: "Visible phase tracking",
    body: "The Control Center shows the current phase, the active backend, and what is being built next.",
  },
  {
    title: "Owner-first design",
    body: "Every future tool, memory, and agent surface will be plugged into approval and audit paths before it can act.",
  },
  {
    title: "Companion-ready shell",
    body: "The layout leaves room for chat, voice, face, memory, and growth features without changing the product structure later.",
  },
];

async function getBackendHealth() {
  const apiBase = process.env.NEXT_PUBLIC_NOVO_API_URL ?? "http://localhost:8000/api/v1";
  try {
    const response = await fetch(`${apiBase}/health/live`, { cache: "no-store" });
    if (!response.ok) {
      return { status: "degraded", detail: `Health endpoint returned ${response.status}` };
    }

    const data = (await response.json()) as { status?: string; service?: string; version?: string };
    return {
      status: data.status ?? "alive",
      detail: `${data.service ?? "NOVO API"} · v${data.version ?? "unknown"}`,
    };
  } catch {
    return { status: "offline", detail: "Backend not reachable" };
  }
}

export default async function Home() {
  const backend = await getBackendHealth();

  return (
    <main className="novo-shell">
      <aside className="novo-sidebar">
        <section className="brand-block">
          <div className="brand-icon" aria-hidden="true">
            N
          </div>
          <div className="brand-copy">
            <div className="brand-title">NOVO Control Center</div>
            <div className="brand-subtitle">Owner-first AI OS</div>
          </div>
        </section>

        <section className="phase-card">
          <div className="phase-topline">
            <span className={`status-dot status-${backend.status}`} aria-hidden="true" />
            <span>Current phase</span>
          </div>
          <strong>E2 frontend control center</strong>
          <p>Dashboard shell + live backend visibility.</p>
        </section>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {navigation.map((item) => (
            <a href="#" key={item.label} className={`nav-item${item.active ? " active" : ""}`}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="issue-pill" aria-label="Open issues">
          <span className="issue-mark">N</span>
          <span className="issue-count">1 Issue</span>
          <span className="issue-close" aria-hidden="true">
            ×
          </span>
        </div>
      </aside>

      <section className="novo-main">
        <header className="hero-panel">
          <div className="hero-copy">
            <div className="eyebrow">Visible product layer</div>
            <h1>The place where NOVO becomes an interface, not just a backend.</h1>
            <p className="lead">
              This first Control Center slice gives you a calm, owner-controlled dashboard that shows
              the system phase, backend health, and the core surfaces NOVO will grow into.
            </p>
          </div>

          <div className="status-stack">
            <article className="status-card">
              <div className={`status-dot status-${backend.status}`} aria-hidden="true" />
              <div>
                <div className="card-label">Backend</div>
                <strong>{backend.status}</strong>
              </div>
            </article>

            <article className="status-card">
              <div>
                <div className="card-label">Health detail</div>
                <strong>{backend.detail}</strong>
              </div>
            </article>
          </div>
        </header>

        <section className="module-grid" aria-label="Control Center modules">
          {cards.map((card) => (
            <article className="info-card" key={card.title}>
              <h2>{card.title}</h2>
              <p>{card.body}</p>
            </article>
          ))}
        </section>

        <section className="sequence-card">
          <div className="eyebrow">Build sequence</div>
          <ol>
            <li>Security foundation backend</li>
            <li>Visible frontend Control Center</li>
            <li>Login, session, and current user views</li>
            <li>Permissions and audit screens</li>
            <li>Memory, RAG, agents, and companion surfaces</li>
          </ol>
        </section>
      </section>
    </main>
  );
}
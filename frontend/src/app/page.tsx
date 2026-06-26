const navigation = [
  "Overview",
  "Identity",
  "Permissions",
  "Audit Logs",
  "System Status",
];

const moduleCards = [
  {
    title: "Security foundation",
    body: "Identity, sessions, permissions, and audit are the first live surfaces so the owner always stays in control.",
  },
  {
    title: "Visible phase tracking",
    body: "The Control Center now shows the current phase, the active backend, and what is being built next.",
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
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-lockup">
            <span className="brand-mark">N</span>
            <div>
              <div className="eyebrow">NOVO Control Center</div>
              <div className="brand-name">Owner-first AI OS</div>
            </div>
          </div>

          <div className="phase-card">
            <span className={`phase-dot phase-${backend.status}`} aria-hidden="true" />
            <div>
              <div className="phase-label">Current phase</div>
              <strong>E2 frontend control center</strong>
              <p>Dashboard shell + live backend visibility.</p>
            </div>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary navigation">
          {navigation.map((item) => (
            <a href="#" key={item} className="nav-link">
              {item}
            </a>
          ))}
        </nav>

        <div className="sidebar-note">
          <span>Next up</span>
          <p>Protected auth views, then permissions and audit screens.</p>
        </div>
      </aside>

      <section className="main-panel">
        <header className="hero-panel">
          <div>
            <div className="eyebrow">Visible product layer</div>
            <h1>The place where NOVO becomes an interface, not just a backend.</h1>
            <p className="lead">
              This first Control Center slice gives you a calm, owner-controlled dashboard that shows
              the system phase, backend health, and the core surfaces NOVO will grow into.
            </p>
          </div>

          <div className="status-stack">
            <div className="status-card">
              <span className={`status-indicator status-${backend.status}`} aria-hidden="true" />
              <div>
                <div className="status-label">Backend</div>
                <strong>{backend.status}</strong>
              </div>
            </div>
            <div className="status-card muted">
              <div>
                <div className="status-label">Health detail</div>
                <strong>{backend.detail}</strong>
              </div>
            </div>
          </div>
        </header>

        <section className="grid" aria-label="Control Center modules">
          {moduleCards.map((module) => (
            <article className="card" key={module.title}>
              <h2>{module.title}</h2>
              <p>{module.body}</p>
            </article>
          ))}
        </section>

        <section className="timeline-card">
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
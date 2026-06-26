const modules = [
  {
    title: "Governance First",
    body: "Permissions, approvals, audit logs, and security modes are treated as core product surfaces, not hidden backend details.",
  },
  {
    title: "Companion Ready",
    body: "The shell is prepared for future memory, goals, projects, emotional awareness, and relationship continuity modules.",
  },
  {
    title: "Operator Safe",
    body: "Agent actions, tool access, RAG, and computer control will flow through visible owner-controlled approval paths.",
  },
  {
    title: "Phase E0",
    body: "This is the engineering foundation: structure, configuration, local development, and health visibility before features.",
  },
];

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_NOVO_API_URL ?? "http://localhost:8000/api/v1";

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="eyebrow">NOVO Control Center</div>
        <h1>Your Personal AI OS starts here.</h1>
        <p className="lead">
          NOVO is being built as an owner-controlled AI companion and operating system:
          transparent, auditable, secure, and calm enough to become genuinely useful in daily life.
        </p>
        <div className="status-pill" aria-label="Current implementation phase">
          <span className="status-dot" aria-hidden="true" />
          Phase E0 foundation active · API {apiUrl}
        </div>
      </section>

      <section className="grid" aria-label="Foundation modules">
        {modules.map((module) => (
          <article className="card" key={module.title}>
            <h2>{module.title}</h2>
            <p>{module.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

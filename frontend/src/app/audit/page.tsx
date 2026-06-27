import Link from "next/link";

import { AuditPanel } from "../audit-panel";

export default function AuditPage() {
  return (
    <main className="surface-page">
      <header className="surface-page-header">
        <Link className="surface-backlink" href="/">&larr; Back to Control Center</Link>
        <div>
          <div className="card-label">NOVO Control Center</div>
          <h1>Audit</h1>
        </div>
      </header>

      <section className="surface-page-stack">
        <AuditPanel />
      </section>
    </main>
  );
}

import Link from "next/link";

import { PermissionsPanel } from "../permissions-panel";

export default function PermissionsPage() {
  return (
    <main className="surface-page">
      <header className="surface-page-header">
        <Link className="surface-backlink" href="/">&larr; Back to Control Center</Link>
        <div>
          <div className="card-label">NOVO Control Center</div>
          <h1>Permissions</h1>
        </div>
      </header>

      <section className="surface-page-stack">
        <PermissionsPanel />
      </section>
    </main>
  );
}

import Link from "next/link";

import { SessionPanel } from "../session-panel";

export default function SettingsPage() {
  return (
    <main className="surface-page">
      <header className="surface-page-header">
        <Link className="surface-backlink" href="/">&larr; Back to Control Center</Link>
        <div>
          <div className="card-label">NOVO Control Center</div>
          <h1>Settings</h1>
        </div>
      </header>

      <section className="surface-page-stack">
        <SessionPanel />
        <article className="surface-note">
          <div className="card-label">Note</div>
          <strong>Settings screens will expand here next.</strong>
          <p>For now, this route surfaces the authenticated owner session and keeps the route contract ready.</p>
        </article>
      </section>
    </main>
  );
}

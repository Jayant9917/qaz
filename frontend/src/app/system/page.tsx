import Link from "next/link";

import { ControlStatePanel } from "../control-state-panel";
import { OverviewPanels } from "../overview-panels";

export default function SystemControlPage() {
  return (
    <main className="surface-page">
      <header className="surface-page-header">
        <Link className="surface-backlink" href="/">&larr; Back to Control Center</Link>
        <div>
          <div className="card-label">NOVO Control Center</div>
          <h1>System control</h1>
        </div>
      </header>

      <section className="surface-page-stack">
        <OverviewPanels />
        <ControlStatePanel />
      </section>
    </main>
  );
}

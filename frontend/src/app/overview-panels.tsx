"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type ControlState = {
  owner_id: string;
  kill_switch_active: boolean;
  automations_enabled: boolean;
  tools_enabled: boolean;
  external_models_enabled: boolean;
  security_mode: string;
  changed_at: string;
  version: number;
};

type Permission = {
  id: string;
  key: string;
  resource: string;
  action: string;
  risk_level: string;
  description: string;
};

type AuditLog = {
  id: string;
  action: string;
  resource_type: string;
  outcome: string;
  created_at: string;
};

type OverviewState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "ready"; control: ControlState; permissions: Permission[]; logs: AuditLog[] }
  | { kind: "error"; message: string };

const stateLabel: Record<string, string> = {
  assistant: "Assistant mode",
  suggest: "Suggest only",
  operator: "Operator mode",
  autonomous: "Autonomous mode",
  observer: "Observer mode",
};

export function OverviewPanels() {
  const [state, setState] = useState<OverviewState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadOverview() {
      try {
        const [controlResponse, permissionsResponse, auditResponse] = await Promise.all([
          fetch(`${apiBase}/control/state`, {
            credentials: "include",
            cache: "no-store",
            signal: controller.signal,
          }),
          fetch(`${apiBase}/permissions`, {
            credentials: "include",
            cache: "no-store",
            signal: controller.signal,
          }),
          fetch(`${apiBase}/audit/logs`, {
            credentials: "include",
            cache: "no-store",
            signal: controller.signal,
          }),
        ]);

        if (controlResponse.status === 401 || permissionsResponse.status === 401 || auditResponse.status === 401) {
          if (!cancelled) {
            setState({ kind: "anonymous" });
          }
          return;
        }

        if (!controlResponse.ok) {
          throw new Error(`Control state failed with ${controlResponse.status}`);
        }
        if (!permissionsResponse.ok) {
          throw new Error(`Permissions failed with ${permissionsResponse.status}`);
        }
        if (!auditResponse.ok) {
          throw new Error(`Audit logs failed with ${auditResponse.status}`);
        }

        const [control, permissions, logs] = (await Promise.all([
          controlResponse.json(),
          permissionsResponse.json(),
          auditResponse.json(),
        ])) as [ControlState, Permission[], AuditLog[]];

        if (!cancelled) {
          setState({ kind: "ready", control, permissions, logs });
        }
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "Unknown overview error" });
        }
      }
    }

    void loadOverview();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <section className="overview-grid" aria-label="System status overview">
        <article className="overview-card">
          <div className="card-label">System status</div>
          <p className="card-help">Current security mode, kill switch, tools, and automation state.</p>
          <strong>Loading secure overview...</strong>
        </article>
        <article className="overview-card">
          <div className="card-label">Session</div>
          <p className="card-help">Who is signed in and whether the owner session is active.</p>
          <strong>Checking identity...</strong>
        </article>
        <article className="overview-card">
          <div className="card-label">Security</div>
          <p className="card-help">What is protected and what remains hidden until sign-in.</p>
          <strong>Preparing control state...</strong>
        </article>
      </section>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <section className="overview-grid" aria-label="System status overview">
        <article className="overview-card">
          <div className="card-label">System status</div>
          <strong>Sign in required</strong>
          <p>Secure overview cards become available after the owner session loads.</p>
        </article>
        <article className="overview-card">
          <div className="card-label">Session</div>
          <strong>No authenticated owner session.</strong>
          <p>Use the Control Center login to see identity, permissions, and audit in one place.</p>
        </article>
        <article className="overview-card">
          <div className="card-label">Security</div>
          <strong>Protected state hidden</strong>
          <p>Kill switch, permissions, and audit require an authenticated browser session.</p>
        </article>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="overview-grid" aria-label="System status overview">
        <article className="overview-card overview-card-error">
          <div className="card-label">System status</div>
          <strong>Overview unavailable.</strong>
          <p>{state.message}</p>
        </article>
      </section>
    );
  }

  const { control, permissions, logs } = state;
  const recentLog = logs[0];

  return (
    <section className="overview-grid" aria-label="System status overview">
      <article className="overview-card">
        <div className="card-label">System status</div>
        <strong>{stateLabel[control.security_mode] ?? control.security_mode}</strong>
        <p>
          Kill switch {control.kill_switch_active ? "active" : "inactive"} - tools {control.tools_enabled ? "enabled" : "disabled"} - automations {control.automations_enabled ? "enabled" : "disabled"}
        </p>
      </article>

      <article className="overview-card">
        <div className="card-label">Session</div>
        <strong>Owner control is visible</strong>
        <p>
          Permission catalog: {permissions.length} entries - current control version {control.version}
        </p>
      </article>

      <article className="overview-card overview-card-audit" id="audit">
        <div className="card-label">Audit snapshot</div>
        {recentLog ? (
          <>
            <strong>{recentLog.action}</strong>
            <p>
              {recentLog.resource_type} - {recentLog.outcome} - {new Date(recentLog.created_at).toLocaleString()}
            </p>
          </>
        ) : (
          <>
            <strong>No audit entries yet.</strong>
            <p>The first meaningful event will appear here after the owner starts using the Control Center.</p>
          </>
        )}
      </article>

      <article className="overview-card overview-card-wide">
        <div className="card-label">Security state</div>
        <strong>{control.security_mode}</strong>
        <p>
          External models {control.external_models_enabled ? "enabled" : "disabled"} - owner session controls remain the authority.
        </p>
      </article>
    </section>
  );
}

"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type AuditLog = {
  id: string;
  action: string;
  resource_type: string;
  outcome: string;
  created_at: string;
};

type ViewState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "ready"; data: AuditLog[] }
  | { kind: "error"; message: string };

export function AuditPanel() {
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadAudit() {
      try {
        const response = await fetch(`${apiBase}/audit/logs`, {
          credentials: "include",
          cache: "no-store",
          signal: controller.signal,
        });

        if (response.status === 401) {
          if (!cancelled) {
            setState({ kind: "anonymous" });
          }
          return;
        }

        if (!response.ok) {
          throw new Error(`Audit logs failed with ${response.status}`);
        }

        const data = (await response.json()) as AuditLog[];
        if (!cancelled) {
          setState({ kind: "ready", data });
        }
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "Unknown audit error" });
        }
      }
    }

    void loadAudit();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <article className="governance-card governance-card-span2" id="audit">
        <div className="card-label">Audit</div>
        <p className="card-help">Recent security and action history with outcomes.</p>
        <strong>Loading audit snapshot...</strong>
      </article>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <article className="governance-card governance-card-span2" id="audit">
        <div className="card-label">Audit</div>
        <strong>Sign in required</strong>
        <p>Audit history becomes visible after the owner authenticates.</p>
      </article>
    );
  }

  if (state.kind === "error") {
    return (
      <article className="governance-card governance-card-span2 governance-card-error" id="audit">
        <div className="card-label">Audit</div>
        <strong>Audit snapshot unavailable</strong>
        <p>{state.message}</p>
      </article>
    );
  }

  const { data } = state;

  return (
    <article className="governance-card governance-card-span2" id="audit">
      <div className="card-label">Audit</div>
      <strong>{data.length} recent events</strong>
      <div className="audit-list">
        {data.slice(0, 5).map((log) => (
          <div key={log.id} className="audit-row">
            <div>
              <strong>{log.action}</strong>
              <p>{log.resource_type}</p>
            </div>
            <span className="tag">{log.outcome}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

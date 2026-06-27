"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type Permission = {
  id: string;
  key: string;
  resource: string;
  action: string;
  risk_level: string;
  description: string;
};

type ViewState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "ready"; data: Permission[] }
  | { kind: "error"; message: string };

export function PermissionsPanel() {
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadPermissions() {
      try {
        const response = await fetch(`${apiBase}/permissions`, {
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
          throw new Error(`Permissions failed with ${response.status}`);
        }

        const data = (await response.json()) as Permission[];
        if (!cancelled) {
          setState({ kind: "ready", data });
        }
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "Unknown permissions error" });
        }
      }
    }

    void loadPermissions();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <article className="governance-card governance-card-span2" id="permissions">
        <div className="card-label">Permissions</div>
        <p className="card-help">What the owner is allowed to read, write, or approve.</p>
        <strong>Loading permission catalog...</strong>
      </article>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <article className="governance-card governance-card-span2" id="permissions">
        <div className="card-label">Permissions</div>
        <strong>Sign in required</strong>
        <p>The owner session is required to inspect the permission catalog.</p>
      </article>
    );
  }

  if (state.kind === "error") {
    return (
      <article className="governance-card governance-card-span2 governance-card-error" id="permissions">
        <div className="card-label">Permissions</div>
        <strong>Permission catalog unavailable</strong>
        <p>{state.message}</p>
      </article>
    );
  }

  const { data } = state;

  return (
    <article className="governance-card governance-card-span2" id="permissions">
      <div className="card-label">Permissions</div>
      <strong>{data.length} granted permissions</strong>
      <div className="permission-list">
        {data.slice(0, 6).map((permission) => (
          <div key={permission.id} className="permission-row">
            <div>
              <strong>{permission.key}</strong>
              <p>{permission.description}</p>
            </div>
            <span className="tag">{permission.risk_level}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

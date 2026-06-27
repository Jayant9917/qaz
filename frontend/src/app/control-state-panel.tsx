"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type ControlState = {
  kill_switch_active: boolean;
  automations_enabled: boolean;
  tools_enabled: boolean;
  external_models_enabled: boolean;
  security_mode: string;
  changed_at: string;
  version: number;
};

type ViewState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "ready"; data: ControlState }
  | { kind: "error"; message: string };

export function ControlStatePanel() {
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadState() {
      try {
        const response = await fetch(`${apiBase}/control/state`, {
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
          throw new Error(`Control state failed with ${response.status}`);
        }

        const data = (await response.json()) as ControlState;
        if (!cancelled) {
          setState({ kind: "ready", data });
        }
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "Unknown control error" });
        }
      }
    }

    void loadState();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <article className="governance-card">
        <div className="card-label">Control state</div>
        <p className="card-help">Live owner controls for kill switch, automation, tools, and models.</p>
        <strong>Loading security state...</strong>
      </article>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <article className="governance-card">
        <div className="card-label">Control state</div>
        <strong>Sign in required</strong>
        <p>Security mode and kill switch visibility require the owner session.</p>
      </article>
    );
  }

  if (state.kind === "error") {
    return (
      <article className="governance-card governance-card-error">
        <div className="card-label">Control state</div>
        <strong>Unavailable</strong>
        <p>{state.message}</p>
      </article>
    );
  }

  const { data } = state;

  return (
    <article className="governance-card">
      <div className="card-label">Control state</div>
      <strong>{data.security_mode}</strong>
      <p>
        Kill switch {data.kill_switch_active ? "active" : "inactive"} - tools {data.tools_enabled ? "enabled" : "disabled"} - automations {data.automations_enabled ? "enabled" : "disabled"}
      </p>
      <div className="governance-tags">
        <span className="tag">External models {data.external_models_enabled ? "on" : "off"}</span>
        <span className="tag">v{data.version}</span>
      </div>
    </article>
  );
}

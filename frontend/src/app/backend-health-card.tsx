"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type BackendState = {
  status: "loading" | "alive" | "degraded" | "offline";
  detail: string;
};

export function BackendHealthCard() {
  const [state, setState] = useState<BackendState>({
    status: "loading",
    detail: "Checking backend status...",
  });

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2500);

    async function loadHealth() {
      try {
        const response = await fetch(`${apiBase}/health/live`, {
          cache: "no-store",
          signal: controller.signal,
        });

        if (!response.ok) {
          setState({
            status: "degraded",
            detail: `Health endpoint returned ${response.status}`,
          });
          return;
        }

        const data = (await response.json()) as { status?: string; service?: string; version?: string };
        setState({
          status: (data.status as BackendState["status"]) ?? "alive",
          detail: `${data.service ?? "NOVO API"} ? v${data.version ?? "unknown"}`,
        });
      } catch {
        setState({
          status: "offline",
          detail: "Backend not reachable",
        });
      } finally {
        clearTimeout(timeout);
      }
    }

    void loadHealth();
    return () => {
      controller.abort();
      clearTimeout(timeout);
    };
  }, []);

  return (
    <div className="hero-card hero-card-right">
      <div>
        <div className="card-label">Health detail</div>
        <strong>{state.detail}</strong>
      </div>
      <div className={`health-pill health-${state.status}`}>{state.status}</div>
    </div>
  );
}

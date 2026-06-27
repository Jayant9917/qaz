"use client";

import { useEffect, useState } from "react";

import { getApiBase } from "../lib/api";
import { getCookieValue } from "../lib/cookies";

const apiBase = getApiBase();

type MeResponse = {
  user: {
    id: string;
    email: string;
    display_name: string;
    is_active: boolean;
    created_at: string;
  };
  roles: string[];
  permissions: string[];
  session: {
    id: string;
    expires_at: string;
    created_at: string;
    last_used_at: string | null;
    revoked_at: string | null;
  };
};

type ViewState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated"; data: MeResponse }
  | { kind: "error"; message: string };

export function SessionPanel() {
  const [state, setState] = useState<ViewState>({ kind: "loading" });
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      try {
        const response = await fetch(`${apiBase}/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });

        if (response.status === 401) {
          if (!cancelled) {
            setState({ kind: "anonymous" });
          }
          return;
        }

        if (!response.ok) {
          throw new Error(`Auth lookup failed with ${response.status}`);
        }

        const data = (await response.json()) as MeResponse;
        if (!cancelled) {
          setState({ kind: "authenticated", data });
        }
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "Unknown auth error" });
        }
      }
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      const csrfToken = getCookieValue("novo_csrf_token");
      await fetch(`${apiBase}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRF-Token": csrfToken ?? "",
        },
      });
    } finally {
      setState({ kind: "anonymous" });
      setLoggingOut(false);
    }
  }

  if (state.kind === "loading") {
    return (
      <section className="status-card session-card">
        <div className="card-label">Identity</div>
        <p className="card-help">Current owner account, roles, and active browser session.</p>
        <strong>Loading owner session...</strong>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="status-card session-card session-error">
        <div>
          <div className="card-label">Identity</div>
          <p className="card-help">Current owner account, roles, and active browser session.</p>
          <strong>Could not load the current user.</strong>
          <p>{state.message}</p>
        </div>
      </section>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <section className="status-card session-card session-anonymous">
        <div>
          <div className="card-label">Identity</div>
          <strong>No owner session yet.</strong>
          <p>Sign in to unlock the authenticated dashboard state.</p>
        </div>
        <a className="session-link" href="/login">
          Sign in
        </a>
      </section>
    );
  }

  const { data } = state;

  return (
    <section className="status-card session-card session-authenticated">
      <div className="session-meta">
        <div className="card-label">Current user</div>
        <strong>{data.user.display_name}</strong>
        <p>{data.user.email}</p>
        <div className="session-tags">
          {data.roles.map((role) => (
            <span key={role} className="tag">
              {role}
            </span>
          ))}
        </div>
      </div>

      <div className="session-actions">
        <div className="session-stat">
          <span>Permissions</span>
          <strong>{data.permissions.length}</strong>
        </div>
        <div className="session-stat">
          <span>Session</span>
          <strong>{data.session.id.slice(0, 8)}</strong>
        </div>
        <button className="session-link session-button" onClick={handleLogout} disabled={loggingOut}>
          {loggingOut ? "Signing out..." : "Sign out"}
        </button>
      </div>
    </section>
  );
}

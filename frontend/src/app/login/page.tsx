"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { getApiBase } from "../../lib/api";

const apiBase = getApiBase();

type LoginResponse = {
  access_token: string;
  csrf_token: string;
  token_type: string;
  expires_at: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@novo.example");
  const [password, setPassword] = useState("novo-owner-1234");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const payload = (await response.json().catch(() => null)) as LoginResponse | { detail?: string } | null;

      if (!response.ok) {
        throw new Error(payload && "detail" in payload && payload.detail ? payload.detail : `Login failed with ${response.status}`);
      }

      if (!payload || typeof payload !== "object" || !("csrf_token" in payload)) {
        throw new Error("Login succeeded, but the response did not include a CSRF token.");
      }

      router.push("/");
      router.refresh();
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in right now.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="eyebrow">NOVO Access</div>
        <h1>Sign in to the Control Center.</h1>
        <p className="lead">
          Use the owner session to unlock the authenticated dashboard state, current user view, and future
          permission-gated surfaces.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error ? <p className="auth-error">{error}</p> : null}

          <button className="auth-button" type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Enter NOVO"}
          </button>
        </form>

        <p className="auth-note">
          This login page uses the backend session cookie model. The access token is returned for compatibility,
          but the browser session is now maintained by HttpOnly cookies instead of localStorage.
        </p>
      </section>
    </main>
  );
}

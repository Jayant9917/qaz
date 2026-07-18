"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AlertCircle, ArrowRight, CheckCircle, Play, XCircle } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { getApiBase } from "../lib/api";

const apiBase = getApiBase();

type HealthResponse = { status: string; service?: string; version?: string };
type HealthState = "loading" | "alive" | "degraded" | "offline";

const navItems = [
  { label: "Overview", href: "/#overview" },
  { label: "Chat", href: "/chat" },
  { label: "Memory", href: "/memory" },
  { label: "Identity", href: "/settings" },
  { label: "Sessions", href: "/settings" },
  { label: "Permissions", href: "/permissions" },
  { label: "Audit", href: "/audit" },
  { label: "Settings", href: "/settings" },
];

const focusItems = [
  {
    title: "Identity first",
    description: "Every screen keeps owner identity, session freshness, and current security mode visible.",
  },
  {
    title: "Evidence visible",
    description: "Audit, control state, and backend health stay close to the actions they explain.",
  },
  {
    title: "Safe expansion",
    description: "The shell is ready for permissions, audit, and settings before advanced automation arrives.",
  },
];

function HealthIcon({ health }: { health: HealthState }) {
  if (health === "alive") return <CheckCircle size={18} className="home-health-icon home-health-alive" />;
  if (health === "degraded") return <AlertCircle size={18} className="home-health-icon home-health-degraded" />;
  if (health === "offline") return <XCircle size={18} className="home-health-icon home-health-offline" />;
  return null;
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthState>("loading");
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const checkHealth = useCallback(async () => {
    setHealth("loading");
    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 2500);
      const response = await fetch(`${apiBase}/health/live`, { cache: "no-store", signal: controller.signal });
      window.clearTimeout(timeout);
      if (!response.ok) {
        setHealth("degraded");
        return;
      }
      setHealthData((await response.json()) as HealthResponse);
      setHealth("alive");
    } catch {
      setHealth("offline");
    }
  }, []);

  useEffect(() => {
    void checkHealth();
  }, [checkHealth, retryCount]);

  return (
    <main className="home-page" id="overview">
      <nav className="home-nav" aria-label="Primary navigation">
        <div className="home-nav-inner">
          <Link href="/" className="home-brand">
            <span className="home-brand-mark">N</span>
            <span><strong>NOVO Control Center</strong><small>Owner-first AI OS</small></span>
          </Link>
          <div className="home-nav-links">
            {navItems.map((item) => <Link key={item.label} href={item.href}>{item.label}</Link>)}
          </div>
          <div className="home-nav-actions">
            <div className="home-phase-pill"><span className="home-phase-dot" />Current phase <strong>E2 frontend control center</strong></div>
            <Link href="/login" className="home-signin">Sign in</Link>
          </div>
        </div>
      </nav>

      <section className="home-main">
        <div className="home-hero-grid">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="home-eyebrow">Visible product layer</div>
            <h1>The place<br />where NOVO<br />becomes an<br />interface.</h1>
            <p className="home-hero-copy">This shell is the owner-facing Control Center: calm, direct, and built to surface system state before any advanced automation appears.</p>
            <div className="home-hero-actions">
              <Link href="/login" className="home-primary-button">Sign in <ArrowRight size={18} /></Link>
              <Link href="/settings" className="home-secondary-button">View identity</Link>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="home-preview">
            <video className="home-preview-video" autoPlay muted loop playsInline preload="metadata">
              <source src="/06037dd15f67cd8a21a4d627c5854160.mp4" type="video/mp4" />
            </video>
            <div className="home-preview-overlay" />
            <div className="home-backend-badge"><span className="home-live-dot" />Backend <strong>live</strong></div>
            <div className="home-health-card">
              <div className="home-health-label">Health detail</div>
              <AnimatePresence mode="wait">
                {health === "loading" ? <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="home-health-loading">Checking backend status...</motion.div> : <motion.div key={health} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="home-health-result"><div><strong>{healthData?.service ?? (health === "offline" ? "Backend" : "NOVO API")} ? v{healthData?.version ?? "0.1.0"}</strong><small className={`home-health-text home-health-text-${health}`}>{health}</small></div><HealthIcon health={health} /></motion.div>}
              </AnimatePresence>
              <button type="button" className="home-retry" onClick={() => setRetryCount((count) => count + 1)}>Retry check</button>
            </div>
            <div className="home-play-mark" aria-hidden="true"><Play size={32} /></div>
          </motion.div>
        </div>

        <div className="home-focus-grid">
          {focusItems.map((item, index) => <motion.article key={item.title} initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }} className="home-focus-card"><strong>{item.title}</strong><p>{item.description}</p></motion.article>)}
        </div>
      </section>

      <footer className="home-phase-footer">
        <div><div className="home-footer-label">Current phase</div><strong>E2 frontend control center</strong></div>
        <p>Dashboard shell + live backend visibility. The active phase and what this screen is meant to show.</p>
      </footer>

      <style>{`
        .home-page { min-height: 100vh; overflow: hidden; background: #09090b; color: #fff; }
        .home-nav { position: sticky; top: 0; z-index: 50; border-bottom: 1px solid #27272a; background: rgba(9, 9, 11, 0.82); backdrop-filter: blur(20px); }
        .home-nav-inner { width: min(1400px, calc(100% - 64px)); min-height: 88px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
        .home-brand { display: flex; align-items: center; gap: 14px; min-width: 220px; }
        .home-brand-mark { display: grid; place-items: center; width: 54px; height: 54px; border-radius: 17px; background: #fafafa; color: #09090b; font-size: 22px; font-weight: 800; }
        .home-brand strong, .home-brand small { display: block; }
        .home-brand strong { color: #fafafa; font-size: 15px; letter-spacing: -0.03em; }
        .home-brand small { margin-top: 4px; color: #71717a; font-size: 12px; }
        .home-nav-links { display: flex; align-items: center; justify-content: center; gap: 24px; flex-wrap: wrap; }
        .home-nav-links a { color: #a1a1aa; font-size: 12px; transition: color 160ms ease; }
        .home-nav-links a:hover { color: #fff; }
        .home-nav-actions { display: flex; align-items: center; gap: 14px; }
        .home-phase-pill { display: flex; align-items: center; gap: 8px; border: 1px solid #3f3f46; border-radius: 999px; background: #18181b; color: #a1a1aa; padding: 10px 14px; font-size: 11px; white-space: nowrap; }
        .home-phase-pill strong { color: #34d399; font-weight: 600; }
        .home-phase-dot, .home-live-dot { width: 8px; height: 8px; border-radius: 999px; background: #34d399; box-shadow: 0 0 14px rgba(52, 211, 153, 0.65); }
        .home-signin, .home-primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 10px; border-radius: 16px; background: #fafafa; color: #09090b; padding: 13px 20px; font-size: 13px; font-weight: 600; transition: transform 160ms ease, background 160ms ease; }
        .home-signin:hover, .home-primary-button:hover { background: #e4e4e7; transform: translateY(-1px); }
        .home-main { width: min(1400px, calc(100% - 64px)); margin: 0 auto; padding: 76px 0 96px; }
        .home-hero-grid { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); align-items: center; gap: 72px; }
        .home-eyebrow { margin-bottom: 20px; color: #a1a1aa; font-size: 12px; letter-spacing: 0.22em; text-transform: uppercase; }
        .home-hero-grid h1 { margin: 0 0 28px; max-width: 7ch; color: #fafafa; font-size: clamp(50px, 6vw, 88px); font-weight: 600; letter-spacing: -0.075em; line-height: 0.99; }
        .home-hero-copy { max-width: 480px; margin: 0; color: #a1a1aa; font-size: 18px; line-height: 1.55; }
        .home-hero-actions { display: flex; align-items: center; gap: 12px; margin-top: 36px; }
        .home-secondary-button { display: inline-flex; align-items: center; justify-content: center; border: 1px solid #3f3f46; border-radius: 16px; color: #fafafa; padding: 13px 20px; font-size: 13px; transition: border-color 160ms ease, transform 160ms ease; }
        .home-secondary-button:hover { border-color: #71717a; transform: translateY(-1px); }
        .home-preview { position: relative; aspect-ratio: 16 / 11; min-height: 400px; overflow: hidden; border: 1px solid #3f3f46; border-radius: 32px; background: #000; box-shadow: 0 32px 100px rgba(0, 0, 0, 0.55); }
        .home-preview-video, .home-preview-overlay { position: absolute; inset: 0; width: 100%; height: 100%; }
        .home-preview-video { z-index: 1; object-fit: contain; background: #000; transform: scale(1.08); }
        .home-preview-overlay { z-index: 2; pointer-events: none; background: linear-gradient(135deg, rgba(76, 29, 149, 0.32), transparent 48%, rgba(0, 0, 0, 0.7)); }
        .home-backend-badge, .home-health-card { position: absolute; z-index: 3; border: 1px solid #3f3f46; background: rgba(24, 24, 27, 0.9); backdrop-filter: blur(14px); }
        .home-backend-badge { top: 24px; left: 24px; display: flex; align-items: center; gap: 10px; border-radius: 16px; padding: 13px 16px; color: #a1a1aa; font-size: 12px; }
        .home-backend-badge strong { color: #34d399; font-family: ui-monospace, monospace; font-weight: 500; }
        .home-health-card { top: 24px; right: 24px; width: 270px; border-radius: 22px; padding: 18px; }
        .home-health-label, .home-footer-label { margin-bottom: 10px; color: #71717a; font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; }
        .home-health-loading { color: #a1a1aa; font-size: 13px; }
        .home-health-result { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
        .home-health-result strong { display: block; color: #f4f4f5; font-size: 13px; font-weight: 600; }
        .home-health-result small { display: block; margin-top: 6px; font-size: 11px; text-transform: capitalize; }
        .home-health-text-alive, .home-health-alive { color: #34d399; }
        .home-health-text-degraded, .home-health-degraded { color: #fbbf24; }
        .home-health-text-offline, .home-health-offline { color: #f87171; }
        .home-retry { margin-top: 16px; border: 0; background: transparent; color: #a1a1aa; font-size: 11px; text-decoration: underline; text-underline-offset: 4px; cursor: pointer; }
        .home-retry:hover { color: #fff; }
        .home-play-mark { position: absolute; z-index: 3; inset: 0; display: grid; place-items: center; color: #c4b5fd; opacity: 0.7; pointer-events: none; }
        .home-play-mark svg { filter: drop-shadow(0 0 24px rgba(168, 85, 247, 0.9)); }
        .home-focus-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 70px; }
        .home-focus-card { min-height: 132px; border: 1px solid #27272a; border-radius: 24px; background: #18181b; padding: 24px; transition: border-color 160ms ease, transform 160ms ease; }
        .home-focus-card:hover { border-color: #52525b; transform: translateY(-2px); }
        .home-focus-card strong { color: #fafafa; font-size: 15px; font-weight: 600; }
        .home-focus-card p { margin: 12px 0 0; color: #a1a1aa; font-size: 13px; line-height: 1.6; }
        .home-phase-footer { display: flex; align-items: center; justify-content: space-between; gap: 28px; border-top: 1px solid #27272a; background: #18181b; padding: 30px max(32px, calc((100% - 1400px) / 2)); }
        .home-phase-footer strong { color: #fafafa; font-size: 16px; font-weight: 600; }
        .home-phase-footer p { max-width: 420px; margin: 0; color: #a1a1aa; font-size: 13px; line-height: 1.5; }
        @media (max-width: 1150px) { .home-nav-inner { width: min(100% - 40px, 900px); } .home-nav-links { gap: 14px; } .home-phase-pill { display: none; } .home-main { width: min(100% - 40px, 900px); } .home-hero-grid { gap: 40px; } }
        @media (max-width: 850px) { .home-nav-inner { min-height: 72px; flex-wrap: wrap; padding: 12px 0; } .home-nav-links { order: 3; width: 100%; justify-content: flex-start; overflow-x: auto; padding-bottom: 4px; } .home-main { padding-top: 48px; } .home-hero-grid { grid-template-columns: 1fr; } .home-preview { min-height: 360px; } .home-focus-grid { grid-template-columns: 1fr; margin-top: 48px; } .home-phase-footer { align-items: flex-start; flex-direction: column; padding: 26px 20px; } }
        @media (max-width: 520px) { .home-nav-inner, .home-main { width: calc(100% - 32px); } .home-brand-mark { width: 44px; height: 44px; } .home-brand strong { font-size: 13px; } .home-brand small { font-size: 11px; } .home-hero-grid h1 { font-size: 54px; } .home-hero-copy { font-size: 16px; } .home-preview { min-height: 300px; border-radius: 24px; } .home-health-card { top: 14px; right: 14px; width: 220px; padding: 14px; } .home-backend-badge { top: 14px; left: 14px; padding: 10px 12px; } }
      `}</style>
    </main>
  );
}

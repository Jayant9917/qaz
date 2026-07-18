"use client";

import Link from "next/link";
import React, { FormEvent, useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Archive, Clock, Edit3, Eye, Info, Plus, RotateCcw, Trash2 } from "lucide-react";

import { getApiBase } from "../../lib/api";
import { getCookieValue } from "../../lib/cookies";
import { getUserFacingErrorMessage } from "../../lib/user-facing-errors";

const apiBase = getApiBase();

interface Memory {
  id: string;
  title: string;
  canonical_content: string;
  kind: string;
  classification: string;
  status: string;
  access_count: number;
  created_at: string;
  updated_at: string;
  last_accessed_at: string | null;
  source_type: string;
  source_locator: Record<string, unknown>;
  evidence_excerpt: string | null;
  version: number;
}

interface Revision {
  id: string;
  version: number;
  title: string;
  canonical_content: string;
  status: string;
  source_type: string;
  created_at: string;
}

interface AccessEvent {
  id: string;
  purpose: string;
  decision: string;
  actor_type: string;
  used_in_prompt: boolean;
  created_at: string;
}
interface MemoryListResponse {
  items: Memory[];
}

type Notice = { kind: "success" | "error"; text: string } | null;

export default function MemoryCenter() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [history, setHistory] = useState<Memory[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [notice, setNotice] = useState<Notice>(null);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [accessEvents, setAccessEvents] = useState<AccessEvent[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);

  const authFetch = useCallback(async (path: string, init: RequestInit = {}) => {
    const csrfToken = getCookieValue("novo_csrf_token");
    const headers = new Headers(init.headers);
    headers.set("Content-Type", "application/json");
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
    return fetch(`${apiBase}${path}`, {
      ...init,
      credentials: "include",
      headers,
    });
  }, []);

  const loadMemories = useCallback(async (status: "active" | "archived" = "active") => {
    const response = await authFetch(`/memories?status=${status}`);
    if (response.status === 401) {
      window.location.href = "/login";
      return [];
    }
    if (!response.ok) {
      throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to load memories."));
    }
    const data = (await response.json()) as MemoryListResponse;
    return data.items;
  }, [authFetch]);

  const refreshActive = useCallback(async () => {
    setMemories(await loadMemories("active"));
  }, [loadMemories]);

  useEffect(() => {
    void refreshActive()
      .catch((error: unknown) => setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to load memories." }))
      .finally(() => setLoading(false));
  }, [refreshActive]);

  async function handleRemember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    setNotice(null);
    try {
      const response = await authFetch("/memories/remember", {
        method: "POST",
        body: JSON.stringify({ title: title.trim() || undefined, content: content.trim() }),
      });
      if (response.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!response.ok) {
        throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to save memory."));
      }
      setTitle("");
      setContent("");
      await refreshActive();
      setNotice({ kind: "success", text: "Memory saved successfully." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Something went wrong." });
    } finally {
      setSaving(false);
    }
  }

  async function handleRestore(id: string) {
    setBusyId(id);
    try {
      const response = await authFetch("/memories/" + id + "/restore", { method: "POST" });
      if (!response.ok) throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to restore memory."));
      setHistory((current) => current.filter((memory) => memory.id !== id));
      setMemories(await loadMemories("active"));
      setNotice({ kind: "success", text: "Memory restored." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to restore memory." });
    } finally {
      setBusyId(null);
    }
  }

  async function handleCorrect(memory: Memory) {
    const nextContent = window.prompt("Correct this memory", memory.canonical_content)?.trim();
    if (!nextContent || nextContent === memory.canonical_content) return;
    setBusyId(memory.id);
    try {
      const response = await authFetch("/memories/" + memory.id + "/correct", {
        method: "POST",
        body: JSON.stringify({ canonical_content: nextContent, title: memory.title, evidence_excerpt: nextContent }),
      });
      if (!response.ok) throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to correct memory."));
      await refreshActive();
      setNotice({ kind: "success", text: "Memory corrected. Its version was updated." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to correct memory." });
    } finally {
      setBusyId(null);
    }
  }

  async function handleDetails(memory: Memory) {
    try {
      const [detailResponse, eventsResponse, revisionsResponse] = await Promise.all([
        authFetch("/memories/" + memory.id),
        authFetch("/memories/" + memory.id + "/access-events"),
        authFetch("/memories/" + memory.id + "/revisions"),
      ]);
      if (!detailResponse.ok || !eventsResponse.ok || !revisionsResponse.ok) throw new Error("Could not load memory details.");
      setSelectedMemory((await detailResponse.json()) as Memory);
      setAccessEvents(((await eventsResponse.json()) as { items: AccessEvent[] }).items);
      setRevisions(((await revisionsResponse.json()) as { items: Revision[] }).items);
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Could not load memory details." });
    }
  }  async function handleArchive(id: string) {
    if (!window.confirm("Archive this memory?")) return;
    setBusyId(id);
    try {
      const response = await authFetch(`/memories/${id}/archive`, { method: "POST" });
      if (!response.ok) throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to archive memory."));
      await refreshActive();
      setNotice({ kind: "success", text: "Memory archived." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to archive memory." });
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(id: string, memoryTitle: string) {
    if (!window.confirm(`Delete "${memoryTitle || "this memory"}" permanently?`)) return;
    setBusyId(id);
    try {
      const response = await authFetch(`/memories/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to delete memory."));
      await refreshActive();
      setNotice({ kind: "success", text: "Memory deleted." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to delete memory." });
    } finally {
      setBusyId(null);
    }
  }

  async function handleEdit(memory: Memory) {
    const nextContent = window.prompt("Update memory content", memory.canonical_content)?.trim();
    if (!nextContent || nextContent === memory.canonical_content) return;
    setBusyId(memory.id);
    try {
      const response = await authFetch(`/memories/${memory.id}`, {
        method: "PATCH",
        body: JSON.stringify({ canonical_content: nextContent }),
      });
      if (!response.ok) throw new Error(getUserFacingErrorMessage(response.status, await response.text(), "Failed to update memory."));
      await refreshActive();
      setNotice({ kind: "success", text: "Memory updated." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to update memory." });
    } finally {
      setBusyId(null);
    }
  }

  async function toggleHistory() {
    if (!showHistory) {
      try {
        setHistory(await loadMemories("archived"));
      } catch (error) {
        setNotice({ kind: "error", text: error instanceof Error ? error.message : "Failed to load history." });
        return;
      }
    }
    setShowHistory((current) => !current);
  }

  const displayedMemories = showHistory ? history : memories;

  return (
    <main className="memory-center-page">
      <div className="memory-center-shell">
        <header className="memory-center-header">
          <div>
            <Link href="/" className="memory-back-link">&larr; Back to Control Center</Link>
            <h1>Memory Center</h1>
            <p>What NOVO should remember about you</p>
          </div>
          <div className="memory-brand-label">NOVO Control Center</div>
        </header>

        <div className="memory-grid">
          <div>
            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="memory-form-card">
              <div className="memory-card-heading">
                <div className="memory-icon memory-icon-green"><Plus size={20} /></div>
                <div><h2>Explicit Memory</h2><p>Durable facts and preferences you approve</p></div>
              </div>
              <form onSubmit={handleRemember} className="memory-form">
                <label>Title (optional)<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g., Communication Style" /></label>
                <label>Memory Content<textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="I prefer concise technical explanations." rows={6} required /></label>
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} disabled={saving || !content.trim()} type="submit" className="memory-submit-button">{saving ? "Saving..." : "Remember this"}</motion.button>
              </form>
              <AnimatePresence mode="wait">
                {notice && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className={`memory-notice memory-notice-${notice.kind}`}>{notice.text}</motion.p>}
              </AnimatePresence>
            </motion.section>
          </div>

          <section>
            <div className="memory-list-header">
              <div><h2>{showHistory ? "Archived Memories" : "Active Memories"}</h2><span className="memory-count">{displayedMemories.length} total</span></div>
              <button className="memory-history-button" type="button" onClick={() => void toggleHistory()}><Clock size={16} /> {showHistory ? "Back to Active" : "View History"}</button>
            </div>

            <AnimatePresence mode="wait">
              {loading ? <div className="memory-empty-state">Loading memories...</div> : displayedMemories.length === 0 ? <div className="memory-empty-state">{showHistory ? "No archived memories." : "No active memories yet."}</div> : <div className="memory-cards">{displayedMemories.map((memory, index) => <motion.article key={memory.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }} className="memory-item-card"><div className="memory-item-top"><div><h3>{memory.title}</h3><p>{memory.canonical_content}</p></div><div className="memory-item-actions"><button type="button" onClick={() => void handleEdit(memory)} disabled={busyId === memory.id} title="Edit"><Edit3 size={16} /></button>{!showHistory && <button type="button" onClick={() => void handleArchive(memory.id)} disabled={busyId === memory.id} className="memory-action-archive" title="Archive"><Archive size={16} /></button>}{showHistory && <button type="button" onClick={() => void handleRestore(memory.id)} disabled={busyId === memory.id} className="memory-action-restore" title="Restore"><RotateCcw size={16} /></button>}<button type="button" onClick={() => void handleCorrect(memory)} disabled={busyId === memory.id} title="Correct"><Edit3 size={16} /></button><button type="button" onClick={() => void handleDetails(memory)} title="View details"><Info size={16} /></button><button type="button" onClick={() => void handleDelete(memory.id, memory.title)} disabled={busyId === memory.id} className="memory-action-delete" title="Delete"><Trash2 size={16} /></button></div></div><div className="memory-item-meta"><span><Eye size={14} /> Accessed {memory.access_count} times</span><span>Added {new Date(memory.created_at).toLocaleDateString()}</span><span>{memory.kind} - {memory.classification}</span></div></motion.article>)}</div>}
            </AnimatePresence>
          </section>
        </div>
      </div>
      {selectedMemory ? (
        <div className="memory-detail-backdrop" role="presentation" onClick={() => setSelectedMemory(null)}>
          <section className="memory-detail-panel" role="dialog" aria-modal="true" aria-label="Memory details" onClick={(event) => event.stopPropagation()}>
            <div className="memory-detail-header">
              <div><span className="memory-detail-kicker">Memory details</span><h2>{selectedMemory.title}</h2></div>
              <button type="button" onClick={() => setSelectedMemory(null)} className="memory-detail-close">Close</button>
            </div>
            <p className="memory-detail-content">{selectedMemory.canonical_content}</p>
            <div className="memory-detail-grid">
              <div><span>Source</span><strong>{selectedMemory.source_type}</strong></div>
              <div><span>Version</span><strong>{selectedMemory.version}</strong></div>
              <div><span>Created</span><strong>{new Date(selectedMemory.created_at).toLocaleString()}</strong></div>
              <div><span>Last accessed</span><strong>{selectedMemory.last_accessed_at ? new Date(selectedMemory.last_accessed_at).toLocaleString() : "Never"}</strong></div>
            </div>
            <div className="memory-detail-section"><span>Evidence</span><p>{selectedMemory.evidence_excerpt || "No evidence excerpt recorded."}</p></div>
            <div className="memory-detail-section"><span>Source locator</span><pre>{JSON.stringify(selectedMemory.source_locator, null, 2)}</pre></div>
            <div className="memory-detail-section"><span>Access history</span>{accessEvents.length === 0 ? <p>No access events yet.</p> : <ul>{accessEvents.map((event) => <li key={event.id}>{new Date(event.created_at).toLocaleString()} · {event.purpose} · {event.decision}{event.used_in_prompt ? " · used in prompt" : ""}</li>)}</ul>}</div><div className="memory-detail-section"><span>Previous versions</span>{revisions.length === 0 ? <p>No revision snapshots yet.</p> : <ul>{revisions.map((revision) => <li key={revision.id}>Version {revision.version} · {new Date(revision.created_at).toLocaleString()} · {revision.source_type}<br />{revision.canonical_content}</li>)}</ul>}</div>
          </section>
        </div>
      ) : null}
      <style>{`
        .memory-center-page { min-height: 100vh; background: #09090b; color: #e4e4e7; }
        .memory-center-shell { max-width: 1180px; margin: 0 auto; padding: 48px 32px 80px; }
        .memory-center-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; margin-bottom: 52px; }
        .memory-back-link { color: #71717a; font-size: 14px; }
        .memory-back-link:hover { color: #a1a1aa; }
        .memory-center-header h1 { margin: 28px 0 8px; color: #fafafa; font-size: clamp(42px, 6vw, 72px); font-weight: 600; letter-spacing: -0.06em; line-height: 0.98; }
        .memory-center-header p, .memory-brand-label { color: #71717a; }
        .memory-brand-label { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; }
        .memory-grid { display: grid; grid-template-columns: minmax(280px, 2fr) minmax(0, 3fr); gap: 32px; }
        .memory-form-card, .memory-item-card { border: 1px solid #27272a; border-radius: 24px; background: #18181b; }
        .memory-form-card { padding: 28px; }
        .memory-card-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
        .memory-card-heading h2, .memory-list-header h2 { margin: 0; color: #fafafa; font-size: 22px; font-weight: 600; }
        .memory-card-heading p { margin: 5px 0 0; color: #71717a; font-size: 14px; }
        .memory-icon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 14px; }
        .memory-icon-green { background: rgba(16, 185, 129, 0.12); color: #34d399; }
        .memory-form { display: grid; gap: 22px; }
        .memory-form label { display: grid; gap: 8px; color: #71717a; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; }
        .memory-form input, .memory-form textarea { width: 100%; border: 1px solid #27272a; border-radius: 16px; background: #09090b; color: #f4f4f5; padding: 13px 16px; font: inherit; font-size: 15px; letter-spacing: normal; text-transform: none; outline: none; resize: vertical; }
        .memory-form textarea { border-radius: 20px; line-height: 1.5; }
        .memory-form input:focus, .memory-form textarea:focus { border-color: #10b981; }
        .memory-submit-button { border: 0; border-radius: 16px; background: #fafafa; color: #09090b; padding: 15px; font-weight: 600; cursor: pointer; }
        .memory-submit-button:disabled { cursor: not-allowed; opacity: 0.5; }
        .memory-notice { margin: 16px 0 0; font-size: 14px; }
        .memory-notice-success { color: #34d399; }
        .memory-notice-error { color: #f87171; }
        .memory-list-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; }
        .memory-count { display: inline-block; margin-top: 7px; border-radius: 999px; background: #27272a; color: #a1a1aa; padding: 4px 10px; font: 12px ui-monospace, monospace; }
        .memory-history-button { display: inline-flex; align-items: center; gap: 7px; border: 0; background: transparent; color: #a1a1aa; cursor: pointer; }
        .memory-history-button:hover { color: #fafafa; }
        .memory-empty-state { display: grid; min-height: 260px; place-items: center; border: 1px dashed #27272a; border-radius: 24px; color: #71717a; }
        .memory-cards { display: grid; gap: 14px; }
        .memory-item-card { padding: 22px; transition: border-color 160ms ease; }
        .memory-item-card:hover { border-color: #3f3f46; }
        .memory-item-top { display: flex; justify-content: space-between; gap: 18px; }
        .memory-item-top h3 { margin: 0 0 8px; color: #f4f4f5; font-size: 17px; font-weight: 500; }
        .memory-item-top p { margin: 0; color: #a1a1aa; line-height: 1.6; white-space: pre-wrap; }
        .memory-item-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 160ms ease; }
        .memory-item-card:hover .memory-item-actions, .memory-item-actions:focus-within { opacity: 1; }
        .memory-item-actions button { display: grid; place-items: center; border: 0; border-radius: 10px; background: transparent; color: #a1a1aa; padding: 8px; cursor: pointer; }
        .memory-item-actions button:hover { background: #27272a; color: #fafafa; }
        .memory-item-actions button:disabled { cursor: wait; opacity: 0.45; }
        .memory-item-actions .memory-action-archive { color: #fbbf24; }
        .memory-item-actions .memory-action-delete { color: #f87171; }
        .memory-item-actions .memory-action-restore { color: #34d399; }
        .memory-detail-backdrop { position: fixed; inset: 0; z-index: 80; display: grid; place-items: center; padding: 24px; background: rgba(0,0,0,.72); }
        .memory-detail-panel { width: min(680px, 100%); max-height: 88vh; overflow: auto; border: 1px solid #3f3f46; border-radius: 24px; background: #18181b; padding: 28px; box-shadow: 0 24px 80px rgba(0,0,0,.5); }
        .memory-detail-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
        .memory-detail-kicker, .memory-detail-section > span, .memory-detail-grid span { display: block; color: #71717a; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; }
        .memory-detail-header h2 { margin: 8px 0 0; color: #fafafa; font-size: 25px; }
        .memory-detail-close { border: 1px solid #3f3f46; border-radius: 10px; background: transparent; color: #d4d4d8; padding: 8px 12px; cursor: pointer; }
        .memory-detail-content { margin: 24px 0; color: #e4e4e7; line-height: 1.6; white-space: pre-wrap; }
        .memory-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; border-top: 1px solid #27272a; border-bottom: 1px solid #27272a; padding: 18px 0; }
        .memory-detail-grid strong { display: block; margin-top: 6px; color: #d4d4d8; font-size: 13px; }
        .memory-detail-section { margin-top: 20px; }
        .memory-detail-section p, .memory-detail-section li { color: #a1a1aa; font-size: 13px; line-height: 1.5; }
        .memory-detail-section pre { overflow: auto; border-radius: 12px; background: #09090b; color: #a7f3d0; padding: 12px; font-size: 12px; }
        .memory-item-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 18px; margin-top: 20px; padding-top: 14px; border-top: 1px solid #27272a; color: #71717a; font-size: 11px; }
        .memory-item-meta span { display: inline-flex; align-items: center; gap: 6px; }
        @media (max-width: 850px) { .memory-center-shell { padding: 32px 20px 60px; } .memory-center-header { display: block; } .memory-brand-label { margin-top: 24px; } .memory-grid { grid-template-columns: 1fr; } }
        @media (max-width: 520px) { .memory-list-header, .memory-item-top { align-items: flex-start; flex-direction: column; } .memory-item-actions { opacity: 1; } }
      `}</style>
    </main>
  );
}

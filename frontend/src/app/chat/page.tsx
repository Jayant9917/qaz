"use client";

import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getApiBase } from "../../lib/api";
import { getCookieValue } from "../../lib/cookies";
import { getUserFacingErrorMessage } from "../../lib/user-facing-errors";

type Conversation = {
  id: string;
  title: string;
  status: string;
  classification: string;
  created_at: string;
  updated_at: string;
};

type Message = {
  id: string;
  conversation_id: string;
  sequence_no: number;
  role: string;
  content: string;
  created_at: string;
  response_id?: string | null;
};

type ConversationListResponse = {
  items: Conversation[];
};

type MessageListResponse = {
  items: Message[];
};

type LocalMessageDraft = {
  id: string;
  conversation_id: string;
  sequence_no: number;
  role: string;
  content: string;
  created_at: string;
  response_id?: string | null;
};

type ToastTone = "info" | "success" | "error";

type Toast = {
  id: string;
  tone: ToastTone;
  title: string;
  description: string;
};

type SendMessageResponse = {
  message: Message;
  response_id: string;
};

type MemorySuggestion = {
  title: string;
  content: string;
  kind: string;
  classification: string;
  confidence: number;
  importance: number;
  reason: string;
};

type MemoryNotice = {
  id: string;
  title: string;
};

type StreamCompletedEvent = {
  response_id: string;
  conversation_id: string;
  assistant_message: Message;
};

const CHAT_STORAGE_KEYS = {
  conversations: "novo.chat.conversations",
  selectedConversationId: "novo.chat.selectedConversationId",
  sidebarQuery: "novo.chat.sidebarQuery",
} as const;

function formatInlineText(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(\*\*([^*]+)\*\*|`([^`]+)`|\*([^*]+)\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2]) {
      parts.push(<strong key={`bold-${match.index}`}>{match[2]}</strong>);
    } else if (match[3]) {
      parts.push(<code key={`code-${match.index}`}>{match[3]}</code>);
    } else if (match[4]) {
      parts.push(<em key={`italic-${match.index}`}>{match[4]}</em>);
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

function normalizeConversationTitle(value: string): string {
  return value.replace(/\s+/g, " ").replace(/["'`]/g, "").trim();
}

function deriveConversationTitle(message: string): string {
  const cleaned = normalizeConversationTitle(message)
    .replace(/[^\w\s?-]/g, "")
    .trim();

  if (!cleaned) {
    return "New chat";
  }

  const words = cleaned.split(/\s+/).slice(0, 6);
  const title = words.join(" ");
  return title.length > 48 ? `${title.slice(0, 45).trim()}...` : title;
}

function renderMessageContent(content: string): ReactNode[] {
  const normalized = content.replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return [];
  }

  const lines = normalized.split("\n");
  const nodes: ReactNode[] = [];

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    if (!trimmed) {
      nodes.push(<div key={`blank-${index}`} className="message-gap" />);
      return;
    }

    const headingMatch = /^(#{1,3})\s+(.+)$/.exec(trimmed);
    if (headingMatch) {
      const depth = headingMatch[1].length;
      const HeadingTag = (depth === 1 ? "h3" : depth === 2 ? "h4" : "h5") as
        | "h3"
        | "h4"
        | "h5";
      nodes.push(
        <HeadingTag key={`heading-${index}`} className={`message-heading message-heading-${depth}`}>
          {formatInlineText(headingMatch[2])}
        </HeadingTag>,
      );
      return;
    }

    const bulletMatch = /^([-*]|\d+\.)\s+(.+)$/.exec(trimmed);
    if (bulletMatch) {
      nodes.push(
        <div key={`bullet-${index}`} className="message-bullet">
          <span className="message-bullet-mark">{bulletMatch[1]}</span>
          <span className="message-bullet-copy">{formatInlineText(bulletMatch[2])}</span>
        </div>,
      );
      return;
    }

    nodes.push(
      <p key={`paragraph-${index}`} className="message-paragraph">
        {formatInlineText(trimmed)}
      </p>,
    );
  });

  return nodes;
}

export default function ChatPage() {
  const apiBase = useMemo(() => getApiBase(), []);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sidebarQuery, setSidebarQuery] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamingReply, setStreamingReply] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const streamRef = useRef<EventSource | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [memorySuggestion, setMemorySuggestion] = useState<MemorySuggestion | null>(null);
  const [isSavingMemory, setIsSavingMemory] = useState(false);
  const [memoryNotice, setMemoryNotice] = useState<MemoryNotice | null>(null);

  const removeToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    setToasts((current) => [...current, { ...toast, id }]);
    globalThis.setTimeout(() => {
      removeToast(id);
    }, 5000);
  }, [removeToast]);

  const nextConversationTitle = useCallback((items: Conversation[]) => {
    const baseTitle = "New chat";
    const existingTitles = new Set(items.map((conversation) => conversation.title.toLowerCase()));
    if (!existingTitles.has(baseTitle.toLowerCase())) {
      return baseTitle;
    }

    let index = 2;
    while (existingTitles.has(`${baseTitle} ${index}`.toLowerCase())) {
      index += 1;
    }

    return `${baseTitle} ${index}`;
  }, []);

  const authFetch = useCallback(
    async (path: string, init?: RequestInit) => {
      const csrfToken = getCookieValue("novo_csrf_token");
      return fetch(`${apiBase}${path}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
          ...(init?.headers ?? {}),
        },
        ...init,
      });
    },
    [apiBase],
  );

  const sortedConversations = useMemo(
    () =>
      [...conversations].sort(
        (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
      ),
    [conversations],
  );

  const filteredConversations = useMemo(() => {
    const query = sidebarQuery.trim().toLowerCase();
    if (!query) {
      return sortedConversations;
    }

    return sortedConversations.filter((conversation) => {
      const haystack = `${conversation.title} ${conversation.status} ${conversation.classification}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [sidebarQuery, sortedConversations]);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  );

  const loadConversations = useCallback(async () => {
    const response = await authFetch("/conversations");
    if (!response.ok) {
      const bodyText = await response.text();
      throw new Error(
        getUserFacingErrorMessage(response.status, bodyText, `Failed to load conversations (${response.status})`),
      );
    }

    const payload = (await response.json()) as ConversationListResponse;
    setConversations(payload.items);
    if (payload.items.length > 0) {
      setSelectedConversationId((current) => {
        if (current && payload.items.some((conversation) => conversation.id === current)) {
          return current;
        }
        return payload.items[0].id;
      });
    }
  }, [authFetch]);

  const loadMessages = useCallback(
    async (conversationId: string) => {
      const response = await authFetch(`/conversations/${conversationId}/messages`);
      if (!response.ok) {
        const bodyText = await response.text();
        throw new Error(
          getUserFacingErrorMessage(response.status, bodyText, `Failed to load messages (${response.status})`),
        );
      }

      const payload = (await response.json()) as MessageListResponse;
      setMessages(payload.items);
    },
    [authFetch],
  );

  const startResponseStream = useCallback(
    (responseId: string) => {
      streamRef.current?.close();
      setStreamingReply("");

      const source = new EventSource(`${apiBase}/conversations/responses/${responseId}/events`, {
        withCredentials: true,
      });
      streamRef.current = source;

      source.addEventListener("response.token", (event) => {
        const payload = JSON.parse((event as MessageEvent).data) as { content?: string };
        if (typeof payload.content === "string") {
          setStreamingReply(payload.content);
        }
      });

      source.addEventListener("response.completed", (event) => {
        const payload = JSON.parse((event as MessageEvent).data) as StreamCompletedEvent;
        setMessages((current) => [...current, payload.assistant_message]);
        setStreamingReply("");
        source.close();
        streamRef.current = null;
      });

      source.addEventListener("response.failed", (event) => {
        const payload = JSON.parse((event as MessageEvent).data) as { error_message?: string };
        const message = payload.error_message ?? "NOVO was unable to generate a reply.";
        setStatus(message);
        setStreamingReply("");
        pushToast({ tone: "error", title: "Reply failed", description: message });
        source.close();
        streamRef.current = null;
      });

      source.onerror = () => {
        const message = "The live reply stream disconnected. Please try sending the message again.";
        setStatus(message);
        pushToast({ tone: "error", title: "Stream disconnected", description: message });
        source.close();
        streamRef.current = null;
      };
    },
    [apiBase, pushToast],
  );

  useEffect(() => {
    try {
      const cachedConversations = window.localStorage.getItem(CHAT_STORAGE_KEYS.conversations);
      if (cachedConversations) {
        setConversations(JSON.parse(cachedConversations) as Conversation[]);
      }
    } catch {
      // Ignore stale cache parsing issues.
    }

    try {
      const cachedSelectedConversationId = window.localStorage.getItem(
        CHAT_STORAGE_KEYS.selectedConversationId,
      );
      if (cachedSelectedConversationId) {
        setSelectedConversationId(cachedSelectedConversationId);
      }
    } catch {
      // Ignore stale cache parsing issues.
    }

    try {
      const cachedQuery = window.localStorage.getItem(CHAT_STORAGE_KEYS.sidebarQuery);
      if (cachedQuery) {
        setSidebarQuery(cachedQuery);
      }
    } catch {
      // Ignore stale cache parsing issues.
    }

    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    try {
      window.localStorage.setItem(CHAT_STORAGE_KEYS.conversations, JSON.stringify(conversations));
    } catch {
      // Ignore cache write failures.
    }
  }, [conversations, hydrated]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    try {
      if (selectedConversationId) {
        window.localStorage.setItem(CHAT_STORAGE_KEYS.selectedConversationId, selectedConversationId);
      } else {
        window.localStorage.removeItem(CHAT_STORAGE_KEYS.selectedConversationId);
      }
    } catch {
      // Ignore cache write failures.
    }
  }, [hydrated, selectedConversationId]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    try {
      window.localStorage.setItem(CHAT_STORAGE_KEYS.sidebarQuery, sidebarQuery);
    } catch {
      // Ignore cache write failures.
    }
  }, [hydrated, sidebarQuery]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        setLoading(true);
        await loadConversations();
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Unable to load NOVO chat.";
          setStatus(message);
          pushToast({ tone: "error", title: "Could not load chats", description: message });
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
      streamRef.current?.close();
      streamRef.current = null;
    };
  }, [loadConversations, pushToast]);

  useEffect(() => {
    if (!selectedConversationId) {
      setMessages([]);
      return;
    }

    let cancelled = false;
    const conversationId = selectedConversationId;

    async function refreshMessages() {
      try {
        await loadMessages(conversationId);
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Unable to load conversation messages.";
          setStatus(message);
          pushToast({ tone: "error", title: "Could not load messages", description: message });
        }
      }
    }

    void refreshMessages();

    return () => {
      cancelled = true;
    };
  }, [loadMessages, selectedConversationId, pushToast]);

  const handleCreateConversation = useCallback(async () => {
    setStatus(null);
    try {
      const conversationTitle = nextConversationTitle(conversations);
      const response = await authFetch("/conversations", {
        method: "POST",
        body: JSON.stringify({ title: conversationTitle, classification: "private" }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(
          getUserFacingErrorMessage(response.status, detail, `Failed to create conversation (${response.status})`),
        );
      }

      const conversation = (await response.json()) as Conversation;
      setConversations((current) => [conversation, ...current]);
      setSelectedConversationId(conversation.id);
      setStatus(`Conversation "${conversation.title}" created.`);
      pushToast({
        tone: "success",
        title: "Conversation created",
        description: `You can now message NOVO in "${conversation.title}".`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create conversation.";
      setStatus(message);
      pushToast({ tone: "error", title: "Could not create conversation", description: message });
    }
  }, [authFetch, conversations, nextConversationTitle, pushToast]);

  const requestMemorySuggestion = useCallback(
    async (content: string, conversationId: string, messageId: string) => {
      try {
        const response = await authFetch("/memories/suggest", {
          method: "POST",
          body: JSON.stringify({
            content,
            source_locator: { channel: "chat", conversation_id: conversationId, message_id: messageId },
          }),
        });
        if (!response.ok) {
          return;
        }
        const suggestion = (await response.json()) as {
          should_suggest?: boolean;
          title?: string;
          content?: string;
          kind?: string;
          classification?: string;
          confidence?: number;
          importance?: number;
          auto_save?: boolean;
          reason?: string;
        };
        if (
          suggestion.should_suggest &&
          suggestion.title &&
          suggestion.content &&
          suggestion.kind &&
          suggestion.classification &&
          typeof suggestion.confidence === "number" &&
          typeof suggestion.importance === "number" &&
          suggestion.reason
        ) {
          setMemorySuggestion({
            title: suggestion.title,
            content: suggestion.content,
            kind: suggestion.kind,
            classification: suggestion.classification,
            confidence: suggestion.confidence,
            importance: suggestion.importance,
            reason: suggestion.reason,
          });
        }
      } catch {
        // Memory suggestions are optional and must never interrupt chat.
      }
    },
    [authFetch],
  );

  const handleApproveMemory = useCallback(async () => {
    if (!memorySuggestion || isSavingMemory) {
      return;
    }
    setIsSavingMemory(true);
    try {
      const response = await authFetch("/memories/remember", {
        method: "POST",
        body: JSON.stringify({
          content: memorySuggestion.content,
          title: memorySuggestion.title,
          kind: memorySuggestion.kind,
          classification: memorySuggestion.classification,
          confidence: memorySuggestion.confidence,
          importance: memorySuggestion.importance,
          source_locator: { channel: "chat", approval: "owner" },
          evidence_excerpt: memorySuggestion.content,
        }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(getUserFacingErrorMessage(response.status, detail, "Could not save this memory."));
      }
      setMemorySuggestion(null);
      pushToast({
        tone: "success",
        title: "Memory saved",
        description: "NOVO will use this approved detail in future conversations.",
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: "Memory not saved",
        description: error instanceof Error ? error.message : "Could not save this memory.",
      });
    } finally {
      setIsSavingMemory(false);
    }
  }, [authFetch, isSavingMemory, memorySuggestion, pushToast]);
  const handleUndoMemory = useCallback(async () => {
    if (!memoryNotice) {
      return;
    }
    const response = await authFetch("/memories/" + memoryNotice.id, { method: "DELETE" });
    if (response.ok) {
      setMemoryNotice(null);
      pushToast({ tone: "info", title: "Memory undone", description: "The detail was removed from NOVO memory." });
    }
  }, [authFetch, memoryNotice, pushToast]);
  const handleSendMessage = useCallback(async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedConversationId || !draft.trim() || isSending) {
      return;
    }

    const draftText = draft.trim();
    const pendingMessage: LocalMessageDraft = {
      id: crypto.randomUUID(),
      conversation_id: selectedConversationId,
      sequence_no: messages.length + 1,
      role: "user",
      content: draftText,
      created_at: new Date().toISOString(),
      response_id: null,
    };

    setStatus(null);
    setIsSending(true);
    setMessages((current) => [...current, pendingMessage]);
    setDraft("");

    const shouldAutoRename = !selectedConversation || selectedConversation.title.toLowerCase().startsWith("new chat");
    const nextConversationTitle = shouldAutoRename ? deriveConversationTitle(draftText) : null;

    try {
      const response = await authFetch(`/conversations/${selectedConversationId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content: draftText, role: "user" }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(
          getUserFacingErrorMessage(response.status, detail, `Failed to send message (${response.status})`),
        );
      }

      const payload = (await response.json()) as SendMessageResponse;
      setMessages((current) =>
        current.map((message) =>
          message.id === pendingMessage.id
            ? {
                ...message,
                id: payload.message.id,
                sequence_no: payload.message.sequence_no,
                created_at: payload.message.created_at,
                response_id: payload.message.response_id,
              }
            : message,
        ),
      );

      if (nextConversationTitle) {
        try {
          const renameResponse = await authFetch(`/conversations/${selectedConversationId}`, {
            method: "PATCH",
            body: JSON.stringify({ title: nextConversationTitle }),
          });

          if (renameResponse.ok) {
            const renamedConversation = (await renameResponse.json()) as Conversation;
            setConversations((current) =>
              current.map((conversation) =>
                conversation.id === renamedConversation.id ? renamedConversation : conversation,
              ),
            );
          }
        } catch {
          // Ignore rename failures; the chat still works.
        }
      }

      startResponseStream(payload.response_id);
      void requestMemorySuggestion(draftText, selectedConversationId, payload.message.id);
    } catch (error) {
      setMessages((current) => current.filter((message) => message.id !== pendingMessage.id));
      const message = error instanceof Error ? error.message : "Failed to send message.";
      setStatus(message);
      pushToast({ tone: "error", title: "Message not sent", description: message });
      setDraft(draftText);
    } finally {
      setIsSending(false);
    }
  }, [authFetch, draft, isSending, messages.length, pushToast, requestMemorySuggestion, selectedConversation, selectedConversationId, startResponseStream]);

  return (
    <main className="chat-shell">
      <section className="chat-app">
        <aside className="chat-sidebar" aria-label="Chat history sidebar">
          <div className="sidebar-brand">
            <div className="sidebar-brand-mark" aria-hidden="true">
              N
            </div>
            <div className="sidebar-brand-copy">
              <strong>NOVO</strong>
              <span>Owner-first AI OS</span>
            </div>
          </div>

          <button className="sidebar-new-chat" type="button" onClick={() => void handleCreateConversation()}>
            <span aria-hidden="true">?</span>
            <span>New chat</span>
          </button>

          <label className="sidebar-search" htmlFor="chat-history-search">
            <span>Search chats</span>
            <input
              id="chat-history-search"
              name="chatHistorySearch"
              value={sidebarQuery}
              onChange={(event) => setSidebarQuery(event.target.value)}
              placeholder="Search chats"
            />
          </label>

          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <strong>Recents</strong>
              <span>{filteredConversations.length}</span>
            </div>

            <div className="sidebar-conversation-list">
              {loading && conversations.length === 0 ? <p className="sidebar-empty">Loading chat history...</p> : null}
              {!loading && filteredConversations.length === 0 ? (
                <p className="sidebar-empty">No chats match your search.</p>
              ) : null}
              {filteredConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`sidebar-conversation ${conversation.id === selectedConversationId ? "is-selected" : ""}`}
                  onClick={() => setSelectedConversationId(conversation.id)}
                >
                  <span className="sidebar-conversation-title">{conversation.title}</span>
                  <span className="sidebar-conversation-meta">
                    <span>{conversation.status}</span>
                    <span>{conversation.classification}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="sidebar-avatar" aria-hidden="true">
              JR
            </div>
            <div className="sidebar-footer-copy">
              <strong>NOVO Owner</strong>
              <span>Chat history is persisted in the database and cached for quick reloads.</span>
            </div>
          </div>
        </aside>

        <main className="chat-main" aria-label="Conversation workspace">
          <div className="chat-main-shell">
            <header className="chat-main-header">
              <div>
                <div className="eyebrow">E2 Conversation Fast Path</div>
                <h1>{messages.length === 0 ? "Where should we begin?" : selectedConversation?.title ?? "Conversation"}</h1>
                <p className="lead">
                  {selectedConversation
                    ? `You are viewing "${selectedConversation.title}".`
                    : "Pick a chat from the sidebar or start a new one."}
                </p>
              </div>

              <div className="chat-main-badge">
                <span>Active chat</span>
                <strong>{selectedConversation?.status ?? "idle"}</strong>
              </div>
            </header>

            {messages.length === 0 ? (
              <section className="chat-empty-stage" aria-label="Start a chat">
                <div className="chat-empty-stage-copy">
                  <h2>Where should we begin?</h2>
                  <p>Ask NOVO anything. Your recent chats stay in the sidebar.</p>
                </div>
              </section>
            ) : (
              <section className="chat-thread" aria-label="Conversation messages">
                <div className="chat-messages">
                  {messages.map((message) => (
                    <article key={message.id} className={`chat-message chat-message-${message.role}`}>
                      <div className="chat-message-meta">
                        <strong>{message.role}</strong>
                        <span>#{message.sequence_no}</span>
                      </div>
                      {renderMessageContent(message.content)}
                    </article>
                  ))}
                  {streamingReply ? (
                    <article className="chat-message chat-message-assistant">
                      <div className="chat-message-meta">
                        <strong>assistant</strong>
                        <span>streaming</span>
                      </div>
                      {renderMessageContent(streamingReply)}
                    </article>
                  ) : null}
                </div>
              </section>
            )}

            {memoryNotice ? (
              <aside className="chat-memory-notice" aria-label="Saved memory notification">
                <span>Saved to memory: <strong>{memoryNotice.title}</strong></span>
                <button type="button" onClick={() => void handleUndoMemory()}>Undo</button>
              </aside>
            ) : null}
            {memorySuggestion ? (
              <aside className="chat-memory-suggestion" aria-label="Memory suggestion">
                <div>
                  <div className="eyebrow">NOVO noticed durable context</div>
                  <strong>{memorySuggestion.title}</strong>
                  <p>{memorySuggestion.content}</p>
                  <small>{memorySuggestion.reason} Nothing is saved until you approve it.</small>
                </div>
                <div className="chat-memory-suggestion-actions">
                  <button type="button" onClick={() => void handleApproveMemory()} disabled={isSavingMemory}>
                    {isSavingMemory ? "Saving..." : "Remember this"}
                  </button>
                  <button type="button" onClick={() => setMemorySuggestion(null)} disabled={isSavingMemory}>
                    Not now
                  </button>
                </div>
              </aside>
            ) : null}
            <form className="chat-compose" onSubmit={(event) => void handleSendMessage(event)}>
              <div className="chat-compose-shell">
                <button type="button" className="chat-compose-plus" aria-label="Add attachment">
                  +
                </button>
                <textarea
                  id="message-draft"
                  name="messageDraft"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Ask NOVO anything"
                  rows={1}
                />
                <div className="chat-compose-tools">
                  <button type="button" className="chat-mode-pill" aria-label="Mode selector">
                    Instant
                  </button>
                  <button type="button" className="chat-compose-icon" aria-label="Voice input">
                    Mic
                  </button>
                  <button className="chat-send-button" type="submit" disabled={!selectedConversationId || !draft.trim() || isSending}>
                    {isSending ? "..." : "Send"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </main>
      </section>

      <div className="chat-toasts" aria-live="polite" aria-relevant="additions">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.tone}`} role={toast.tone === "error" ? "alert" : "status"}>
            <div className="toast-copy">
              <strong>{toast.title}</strong>
              <p>{toast.description}</p>
            </div>
            <button
              type="button"
              className="toast-dismiss"
              onClick={() => removeToast(toast.id)}
              aria-label={`Dismiss ${toast.title}`}
            >
              x
            </button>
          </div>
        ))}
      </div>

      {status ? <p className="chat-status">{status}</p> : null}
    </main>
  );
}

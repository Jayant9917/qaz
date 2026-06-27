"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getApiBase } from "../../lib/api";
import { getCookieValue } from "../../lib/cookies";

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

type SendMessageResponse = {
  message: Message;
  response_id: string;
};

type StreamCompletedEvent = {
  response_id: string;
  conversation_id: string;
  assistant_message: Message;
};

export default function ChatPage() {
  const apiBase = useMemo(() => getApiBase(), []);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [title, setTitle] = useState("New chat");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamingReply, setStreamingReply] = useState("");
  const streamRef = useRef<EventSource | null>(null);

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

  const loadConversations = useCallback(async () => {
    const response = await authFetch("/conversations");
    if (!response.ok) {
      throw new Error(`Failed to load conversations (${response.status})`);
    }

    const payload = (await response.json()) as ConversationListResponse;
    setConversations(payload.items);
    if (payload.items.length > 0) {
      setSelectedConversationId((current) => current ?? payload.items[0].id);
    }
  }, [authFetch]);

  const loadMessages = useCallback(
    async (conversationId: string) => {
      const response = await authFetch(`/conversations/${conversationId}/messages`);
      if (!response.ok) {
        throw new Error(`Failed to load messages (${response.status})`);
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

      const source = new EventSource(`${apiBase}/responses/${responseId}/events`, {
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
        setStatus(payload.error_message ?? "NOVO was unable to generate a reply.");
        setStreamingReply("");
        source.close();
        streamRef.current = null;
      });

      source.onerror = () => {
        source.close();
        streamRef.current = null;
      };
    },
    [apiBase],
  );

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        setLoading(true);
        await loadConversations();
      } catch (error) {
        if (!cancelled) {
          setStatus(error instanceof Error ? error.message : "Unable to load NOVO chat.");
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
  }, [loadConversations]);

  useEffect(() => {
    if (!selectedConversationId) {
      setMessages([]);
      return;
    }

    const activeConversationId = selectedConversationId;
    let cancelled = false;

    async function refreshMessages() {
      try {
        await loadMessages(activeConversationId);
      } catch (error) {
        if (!cancelled) {
          setStatus(error instanceof Error ? error.message : "Unable to load conversation messages.");
        }
      }
    }

    void refreshMessages();

    return () => {
      cancelled = true;
    };
  }, [loadMessages, selectedConversationId]);

  async function handleCreateConversation() {
    setStatus(null);
    const response = await authFetch("/conversations", {
      method: "POST",
      body: JSON.stringify({ title, classification: "private" }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create conversation (${response.status})`);
    }

    const conversation = (await response.json()) as Conversation;
    setConversations((current) => [conversation, ...current]);
    setSelectedConversationId(conversation.id);
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedConversationId || !draft.trim()) {
      return;
    }

    setStatus(null);
    const response = await authFetch(`/conversations/${selectedConversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: draft.trim(), role: "user" }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send message (${response.status})`);
    }

    const payload = (await response.json()) as SendMessageResponse;
    setMessages((current) => [...current, payload.message]);
    setDraft("");
    startResponseStream(payload.response_id);
  }

  return (
    <main className="chat-shell">
      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <div className="eyebrow">E2 Conversation Fast Path</div>
            <h1>Talk to NOVO.</h1>
            <p className="lead">
              This is the owner-facing chat surface. It keeps conversations, messages, and the current session in one
              place.
            </p>
          </div>

          <div className="chat-header-actions">
            <input
              className="chat-title-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              aria-label="Conversation title"
            />
            <button className="primary-button" type="button" onClick={() => void handleCreateConversation()}>
              New conversation
            </button>
          </div>
        </header>

        <div className="chat-layout">
          <aside className="chat-sidebar">
            <div className="card-label">Conversations</div>
            {loading ? <p className="card-help">Loading conversations...</p> : null}
            {conversations.length === 0 && !loading ? (
              <p className="card-help">No conversations yet. Create the first one.</p>
            ) : null}
            <div className="chat-list">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`chat-list-item ${conversation.id === selectedConversationId ? "is-selected" : ""}`}
                  onClick={() => setSelectedConversationId(conversation.id)}
                >
                  <strong>{conversation.title}</strong>
                  <span>{conversation.status}</span>
                </button>
              ))}
            </div>
          </aside>

          <section className="chat-thread" aria-label="Conversation messages">
            {messages.length === 0 ? (
              <div className="chat-empty-state">
                <strong>No messages yet.</strong>
                <p>Send the first owner message to start the conversation.</p>
              </div>
            ) : (
              <div className="chat-messages">
                {messages.map((message) => (
                  <article key={message.id} className={`chat-message chat-message-${message.role}`}>
                    <div className="chat-message-meta">
                      <strong>{message.role}</strong>
                      <span>#{message.sequence_no}</span>
                    </div>
                    <p>{message.content}</p>
                  </article>
                ))}
                {streamingReply ? (
                  <article className="chat-message chat-message-assistant">
                    <div className="chat-message-meta">
                      <strong>assistant</strong>
                      <span>streaming</span>
                    </div>
                    <p>{streamingReply}</p>
                  </article>
                ) : null}
              </div>
            )}

            <form className="chat-compose" onSubmit={(event) => void handleSendMessage(event)}>
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask NOVO something..."
                rows={4}
              />
              <button className="primary-button" type="submit" disabled={!selectedConversationId || !draft.trim()}>
                Send message
              </button>
            </form>
          </section>
        </div>

        {status ? <p className="chat-status">{status}</p> : null}
      </section>
    </main>
  );
}



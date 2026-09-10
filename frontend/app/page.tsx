"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { Button } from "@/components/Button";
import { ChatMessage } from "@/components/ChatMessage";
import { AgentStatus, AgentState } from "@/components/AgentStatus";
import { Input } from "@/components/Input";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

type BackendStatus = "checking" | "connected" | "disconnected";

interface Message {
  id: number;
  role: "user" | "agent";
  text: string;
}

// ─── Demo seed messages ───────────────────────────────────────────────────────

const SEED_MESSAGES: Message[] = [
  {
    id: 1,
    role: "user",
    text: "Find a room for 8 people tomorrow at 4 PM.",
  },
  {
    id: 2,
    role: "agent",
    text: "I'll find the best available option. Give me a moment.",
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [messages, setMessages] = useState<Message[]>(SEED_MESSAGES);
  const [agentState, setAgentState] = useState<AgentState>("idle");
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Health check ────────────────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        setBackendStatus(res.ok ? "connected" : "disconnected");
      } catch {
        setBackendStatus("disconnected");
      }
    };
    check();
  }, []);

  // ── Auto-scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentState]);

  // ── Send message ────────────────────────────────────────────────────────────
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || agentState !== "idle") return;

    const userMsg: Message = { id: Date.now(), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setAgentState("thinking");

    // Placeholder: simulate agent thinking → response
    // Agent team: replace this timeout with a real API call to agent/backend
    setTimeout(() => {
      setAgentState("idle");
      const agentMsg: Message = {
        id: Date.now() + 1,
        role: "agent",
        text: "Agent workflow not yet implemented. Connect this to the backend API → MCP server → Strands agent.",
      };
      setMessages((prev) => [...prev, agentMsg]);
    }, 1400);
  };

  // ── Status pill ─────────────────────────────────────────────────────────────
  const statusPillClass =
    backendStatus === "connected"
      ? "status-pill status-pill-connected"
      : backendStatus === "disconnected"
      ? "status-pill status-pill-error"
      : "status-pill status-pill-checking";

  const statusDotClass =
    backendStatus === "connected"
      ? "status-dot status-dot-connected animate-dot-pulse"
      : backendStatus === "disconnected"
      ? "status-dot status-dot-error"
      : "status-dot status-dot-checking animate-dot-pulse";

  const statusLabel =
    backendStatus === "connected"
      ? "Backend connected"
      : backendStatus === "disconnected"
      ? "Backend unavailable"
      : "Checking…";

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div
      className="page-bg animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "32px 20px",
        gap: 28,
      }}
    >
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header style={{ textAlign: "center" }}>
        {/* Wordmark */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 8,
          }}
        >
          {/* Logo mark */}
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-md)",
              background: "var(--color-accent)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
            aria-hidden
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>

          <h1 className="text-page-title" style={{ fontSize: "1.5rem" }}>
            SpacePilot
          </h1>
        </div>

        <p className="text-secondary" style={{ marginBottom: 14 }}>
          Your workspace. On autopilot.
        </p>

        {/* Backend status */}
        <span className={statusPillClass} id="backend-status">
          <span className={statusDotClass} />
          {statusLabel}
        </span>
      </header>

      {/* ── Chat panel ──────────────────────────────────────────────────── */}
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: 660,
          display: "flex",
          flexDirection: "column",
          height: 440,
        }}
      >
        {/* Messages area */}
        <div
          id="chat-messages"
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px 20px 12px",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {messages.map((msg) => (
            <ChatMessage key={msg.id} role={msg.role} text={msg.text} />
          ))}

          {/* Agent thinking indicator */}
          {agentState === "thinking" && (
            <AgentStatus state="thinking" />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Divider */}
        <div className="divider" />

        {/* Input row */}
        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            gap: 10,
            padding: "14px 16px",
            alignItems: "center",
          }}
        >
          <Input
            id="chat-input"
            variant="chat"
            placeholder='Ask anything — "Book a room for 8 people at 4 PM"'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            autoComplete="off"
            disabled={agentState !== "idle"}
            style={{ flex: 1 }}
          />
          <Button
            id="chat-send-btn"
            type="submit"
            variant="primary"
            disabled={!input.trim() || agentState !== "idle"}
            loading={agentState === "thinking"}
          >
            Send
          </Button>
        </form>
      </div>

      {/* ── Capability tags ──────────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {[
          "Room Booking",
          "Navigation",
          "Team Availability",
          "Campus Events",
          "Policies",
        ].map((tag) => (
          <span
            key={tag}
            style={{
              fontSize: "0.75rem",
              color: "var(--color-text-muted)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-full)",
              padding: "3px 10px",
            }}
          >
            {tag}
          </span>
        ))}
      </div>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer>
        <p className="text-caption" style={{ textAlign: "center" }}>
          Hackathon demo &middot; Frontend → Backend → MCP → Agent
        </p>
      </footer>
    </div>
  );
}

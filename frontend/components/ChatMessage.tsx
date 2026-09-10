import React from "react";

export interface ChatMessageProps {
  role: "user" | "agent";
  text: string;
  /** If true, renders the thinking indicator instead of text */
  thinking?: boolean;
}

export function ChatMessage({ role, text, thinking = false }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`animate-msg-appear ${isUser ? "bubble-user" : "bubble-agent"}`}
    >
      {thinking ? (
        /* Agent thinking dots — shown while agent is processing */
        <span style={{ display: "inline-flex", gap: 4, alignItems: "center", padding: "2px 0" }}>
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </span>
      ) : (
        text
      )}
    </div>
  );
}

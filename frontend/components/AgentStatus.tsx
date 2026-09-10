import React from "react";

export type AgentState =
  | "idle"        // waiting for user input
  | "thinking"    // LLM reasoning
  | "using-tool"  // executing an MCP tool
  | "done";       // response delivered

interface AgentStatusProps {
  state: AgentState;
  toolName?: string;  // shown when state === "using-tool"
}

const labels: Record<AgentState, string> = {
  idle:        "Ready",
  thinking:    "Thinking…",
  "using-tool": "Using tool",
  done:        "Done",
};

export function AgentStatus({ state, toolName }: AgentStatusProps) {
  if (state === "idle" || state === "done") return null;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 12px",
        borderRadius: "var(--radius-full)",
        border: "1px solid var(--color-border)",
        backgroundColor: "var(--color-surface)",
        fontSize: "0.8125rem",
        color: "var(--color-text-secondary)",
        alignSelf: "flex-start",
      }}
    >
      {state === "thinking" && (
        <>
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </>
      )}
      {state === "using-tool" && (
        <span className="spinner" />
      )}
      <span>
        {labels[state]}
        {state === "using-tool" && toolName && (
          <span style={{ color: "var(--color-accent)", marginLeft: 4 }}>
            {toolName}
          </span>
        )}
      </span>
    </div>
  );
}

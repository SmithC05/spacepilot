import React from "react";

interface LoadingIndicatorProps {
  /** "spinner" = spinning arc, "dots" = three pulsing dots, "bar" = thin progress bar */
  variant?: "spinner" | "dots" | "bar";
  size?: number;
  label?: string;
}

export function LoadingIndicator({
  variant = "spinner",
  size = 16,
  label,
}: LoadingIndicatorProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        color: "var(--color-text-muted)",
        fontSize: "0.8125rem",
      }}
      aria-label={label || "Loading"}
      role="status"
    >
      {variant === "spinner" && (
        <span className="spinner" style={{ width: size, height: size }} />
      )}

      {variant === "dots" && (
        <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </span>
      )}

      {variant === "bar" && (
        /* Indeterminate progress bar */
        <span
          style={{
            display: "block",
            width: 80,
            height: 2,
            background: "var(--color-border)",
            borderRadius: 2,
            overflow: "hidden",
            position: "relative",
          }}
        >
          <span
            style={{
              position: "absolute",
              inset: 0,
              background: "var(--color-accent)",
              borderRadius: 2,
              animation: "loading-bar 1.4s ease-in-out infinite",
            }}
          />
        </span>
      )}

      {label && <span>{label}</span>}
    </div>
  );
}

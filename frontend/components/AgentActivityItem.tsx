import React from "react";
import { TimelineStep } from "./AgentActivityTimeline";

interface AgentActivityItemProps {
  step: TimelineStep;
  isLast: boolean;
}

export function AgentActivityItem({ step, isLast }: AgentActivityItemProps) {
  const isRunning = step.status === "running";
  const isCompleted = step.status === "completed";
  const isPending = step.status === "pending";
  const isFailed = step.status === "failed";

  return (
    <div className="animate-timeline-enter" style={{ display: "flex", gap: 16 }}>
      {/* Connector column */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div
          style={{
            width: 20,
            height: 20,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: isCompleted
              ? "transparent"
              : isRunning
              ? "var(--color-surface)"
              : "transparent",
            marginTop: 2, // align with first line of text
            position: "relative",
          }}
        >
          {isCompleted && (
            <svg className="animate-check-appear" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          )}
          {isRunning && (
            <>
              <div
                className="animate-pulse-subtle"
                style={{
                  position: "absolute",
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: "var(--color-accent)",
                  opacity: 0.2,
                }}
              />
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: "var(--color-accent)",
                  zIndex: 1,
                }}
              />
            </>
          )}
          {isPending && (
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                border: "1px solid var(--color-text-muted)",
                backgroundColor: "transparent",
              }}
            />
          )}
          {isFailed && (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-error)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          )}
        </div>
        
        {/* Vertical line connecting to next item */}
        {!isLast && (
          <div
            style={{
              width: 1.5,
              flex: 1,
              backgroundColor: isCompleted ? "var(--color-border-strong)" : "var(--color-border)",
              marginTop: 4,
              marginBottom: 4,
              minHeight: 16,
            }}
          />
        )}
      </div>

      {/* Content column */}
      <div
        style={{
          paddingBottom: isLast ? 0 : 20,
          flex: 1,
        }}
      >
        <div
          style={{
            backgroundColor: isRunning ? "var(--color-surface-subtle)" : "transparent",
            border: isRunning ? "1px solid var(--color-border)" : "1px solid transparent",
            borderRadius: "var(--radius-md)",
            padding: isRunning ? "8px 12px" : "2px 0",
            display: "inline-block",
            maxWidth: "100%",
            transition: "all var(--duration-base) ease",
          }}
        >
          <p
            style={{
              fontSize: "0.875rem",
              fontWeight: isRunning ? 500 : 400,
              color: isPending ? "var(--color-text-muted)" : isFailed ? "var(--color-error)" : "var(--color-text)",
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {step.title}
          </p>
          {step.description && (
            <p
              style={{
                fontSize: "0.8125rem",
                color: "var(--color-text-secondary)",
                marginTop: 2,
                marginBottom: 0,
                lineHeight: 1.4,
              }}
            >
              {step.description}
            </p>
          )}
          {isFailed && (
            <button
              style={{
                marginTop: 8,
                fontSize: "0.75rem",
                color: "var(--color-text)",
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border-strong)",
                padding: "4px 10px",
                borderRadius: "var(--radius-sm)",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

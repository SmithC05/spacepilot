import React from "react";
import { AgentActivityItem } from "./AgentActivityItem";

export type TimelineStatus = "pending" | "running" | "completed" | "failed";

export interface TimelineStep {
  id: string;
  title: string;
  description?: string;
  status: TimelineStatus;
}

interface AgentActivityTimelineProps {
  steps: TimelineStep[];
}

export function AgentActivityTimeline({ steps }: AgentActivityTimelineProps) {
  if (!steps || steps.length === 0) return null;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        padding: "8px 16px 8px 8px", // Slight padding adjustment for optical alignment
      }}
    >
      {steps.map((step, index) => (
        <AgentActivityItem
          key={step.id}
          step={step}
          isLast={index === steps.length - 1}
        />
      ))}
    </div>
  );
}

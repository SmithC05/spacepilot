import React from "react";

export type BackendStatusType = "checking" | "connected" | "disconnected";

interface ConnectionStatusProps {
  status: BackendStatusType;
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const statusPillClass =
    status === "connected"
      ? "status-pill status-pill-connected"
      : status === "disconnected"
      ? "status-pill status-pill-error"
      : "status-pill status-pill-checking";

  const statusDotClass =
    status === "connected"
      ? "status-dot status-dot-connected"
      : status === "disconnected"
      ? "status-dot status-dot-error"
      : "status-dot status-dot-checking animate-dot-pulse";

  const statusLabel =
    status === "connected"
      ? "Backend connected"
      : status === "disconnected"
      ? "Backend unavailable"
      : "Checking…";

  return (
    <span className={statusPillClass} id="backend-status">
      <span className={statusDotClass} />
      {statusLabel}
    </span>
  );
}

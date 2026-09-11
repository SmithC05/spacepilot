import React from "react";
import { RouteData } from "@/types/route";

interface RoutePanelProps {
  route: RouteData;
}

export function RoutePanel({ route }: RoutePanelProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        height: "100%",
        padding: "4px",
      }}
    >
      {/* Header info */}
      <div>
        <h3 style={{ margin: 0, fontSize: "1.25rem", color: "var(--color-text)", fontWeight: 600 }}>
          {route.destination}
        </h3>
        <p style={{ margin: "4px 0 0 0", fontSize: "0.9375rem", color: "var(--color-text-secondary)" }}>
          {route.distance_m}m · ~{route.duration_minutes} min walk
        </p>
      </div>

      {/* Accessibility Alert */}
      {route.accessible && (
        <div
          style={{
            backgroundColor: "var(--color-bg)",
            border: "1px solid var(--color-accent)",
            borderRadius: "var(--radius-md)",
            padding: "12px 16px",
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: "2px" }}>
             <path d="M 12 2 a 2 2 0 1 0 0 4 a 2 2 0 1 0 0 -4 Z" />
             <path d="M 6 8 h 12 l -2 12 l -4 -6 l -4 6 Z" />
          </svg>
          <div>
            <strong style={{ display: "block", color: "var(--color-accent)", fontSize: "0.9375rem", fontWeight: 600, marginBottom: "4px" }}>
              Accessible route available
            </strong>
            <div style={{ display: "flex", flexDirection: "column", gap: "2px", fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg> Elevator available
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg> Step-free path
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Instructions list */}
      <div>
        <h4 style={{ margin: "0 0 12px 0", fontSize: "0.875rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
          Route Instructions
        </h4>
        <ol style={{ margin: 0, paddingLeft: "20px", color: "var(--color-text)", fontSize: "0.9375rem", display: "flex", flexDirection: "column", gap: "10px" }}>
          {route.steps.map((step, idx) => (
            <li key={idx} style={{ paddingLeft: "4px" }}>
              {step}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

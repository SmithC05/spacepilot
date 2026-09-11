import React from "react";
import { RouteData } from "@/types/route";
import { CampusMap } from "./CampusMap";
import { RoutePanel } from "./RoutePanel";

interface RouteDetailsProps {
  route: RouteData;
}

export function RouteDetails({ route }: RouteDetailsProps) {
  return (
    <div
      className="animate-timeline-enter"
      style={{
        marginTop: "16px",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        padding: "24px",
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: "32px",
        width: "100%",
      }}
    >
      <div style={{ order: 1 }}>
        <CampusMap route={route} />
      </div>
      <div style={{ order: 2 }}>
        <RoutePanel route={route} />
      </div>
    </div>
  );
}

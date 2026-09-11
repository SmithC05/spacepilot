import React from "react";
import { RouteData } from "@/types/route";

interface CampusMapProps {
  route: RouteData;
}

export function CampusMap({ route }: CampusMapProps) {
  return (
    <div
      style={{
        backgroundColor: "var(--color-bg)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        padding: "16px",
        height: "100%",
        minHeight: "240px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 300 200"
        style={{ maxWidth: "400px" }}
      >
        {/* Background structures (buildings, corridors) */}
        <rect x="20" y="20" width="100" height="70" fill="var(--color-surface)" stroke="var(--color-border)" rx="4" />
        <rect x="180" y="20" width="100" height="70" fill="var(--color-surface)" stroke="var(--color-border)" rx="4" />
        <rect x="20" y="110" width="260" height="70" fill="var(--color-surface)" stroke="var(--color-border)" rx="4" />

        {/* Labels for abstraction */}
        <text x="70" y="60" fontSize="10" fill="var(--color-text-muted)" textAnchor="middle">Main Entrance</text>
        <text x="230" y="60" fontSize="10" fill="var(--color-text-muted)" textAnchor="middle">{route.destination}</text>
        <text x="150" y="170" fontSize="10" fill="var(--color-text-muted)" textAnchor="middle">Main Corridor</text>

        {/* Route Line */}
        <path
          className="route-path"
          d="M 70 80 L 70 120 L 120 120 L 120 145 L 230 145 L 230 80"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Start Marker */}
        <circle cx="70" cy="80" r="4" fill="var(--color-accent)" />
        <text x="50" y="77" fontSize="10" fill="var(--color-text-secondary)" fontWeight="600" textAnchor="end">START</text>

        {/* End Marker (Pulse effect & solid) */}
        <circle className="animate-pulse-subtle" cx="230" cy="80" r="8" fill="var(--color-accent)" />
        <circle cx="230" cy="80" r="5" fill="var(--color-accent)" />
        <text x="245" y="77" fontSize="10" fill="var(--color-text)" fontWeight="600">DEST</text>

        {/* Accessible Elevator node if applicable */}
        {route.accessible && (
          <g transform="translate(145, 140)">
             <circle cx="5" cy="5" r="7" fill="var(--color-surface)" stroke="var(--color-accent)" strokeWidth="1.5" />
             {/* Small accessibility icon abstraction inside elevator */}
             <circle cx="5" cy="3" r="1.5" fill="var(--color-accent)"/>
             <path d="M 3 5 L 7 5 M 5 5 L 5 8 M 4 8 L 6 8" stroke="var(--color-accent)" strokeWidth="1" />
             <text x="18" y="8" fontSize="9" fill="var(--color-accent)" textAnchor="start">Elevator</text>
          </g>
        )}
      </svg>
    </div>
  );
}

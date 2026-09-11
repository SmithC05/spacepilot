import React from "react";
import { Room } from "@/types/room";

interface BookingSuccessProps {
  room: Room;
}

export function BookingSuccess({ room }: BookingSuccessProps) {
  return (
    <div
      className="animate-timeline-enter"
      style={{
        marginTop: "24px",
        padding: "24px",
        backgroundColor: "var(--color-bg)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <svg className="animate-check-appear" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <h3 style={{ margin: 0, fontSize: "1.125rem", color: "var(--color-text)", fontWeight: 600 }}>Booking successful</h3>
      </div>
      
      <div style={{ display: "flex", flexDirection: "column", gap: "4px", color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
        <strong style={{ color: "var(--color-text)", fontWeight: 500 }}>{room.name}</strong>
        <span>Tomorrow · 4:00 PM</span>
        <span>{room.capacity} people</span>
      </div>

      <div style={{ marginTop: "8px", paddingTop: "16px", borderTop: "1px solid var(--color-border)" }}>
        <p style={{ margin: 0, color: "var(--color-text)", fontSize: "0.9375rem" }}>Your room has been successfully booked.</p>
      </div>
    </div>
  );
}

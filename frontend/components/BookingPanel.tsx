import React from "react";
import { Room, BookingState } from "@/types/room";
import { Button } from "./Button";

interface BookingPanelProps {
  room: Room;
  bookingState: BookingState;
  onBook: () => void;
}

export function BookingPanel({ room, bookingState, onBook }: BookingPanelProps) {
  return (
    <div
      className="animate-timeline-enter"
      style={{
        marginTop: "24px",
        padding: "24px",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <h3 style={{ margin: 0, fontSize: "1.125rem", color: "var(--color-text)", fontWeight: 600 }}>Ready to book</h3>
      </div>
      
      <div style={{ display: "flex", flexDirection: "column", gap: "4px", color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
        <strong style={{ color: "var(--color-text)", fontWeight: 500 }}>{room.name}</strong>
        <span>Tomorrow · 4:00 PM</span>
        <span>8 people</span>
      </div>

      <div style={{ marginTop: "8px" }}>
        <Button 
          variant="primary" 
          onClick={onBook}
          disabled={bookingState !== "idle"}
          loading={bookingState === "booking"}
          style={{ width: "100%", justifyContent: "center" }}
        >
          Book this room
        </Button>
      </div>
    </div>
  );
}

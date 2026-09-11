import React from "react";
import { Room } from "@/types/room";
import { RoomCard } from "./RoomCard";

interface RoomResultsProps {
  rooms: Room[];
  selectedRoomId: string | null;
  onSelectRoom: (room: Room) => void;
  isLoading?: boolean;
}

export function RoomResults({ rooms, selectedRoomId, onSelectRoom, isLoading }: RoomResultsProps) {
  if (isLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
        <div style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>
          Searching available rooms...
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse-subtle" style={{ height: "240px", backgroundColor: "var(--color-surface)", borderRadius: "var(--radius-xl)", border: "1px solid var(--color-border)" }} />
          ))}
        </div>
      </div>
    );
  }

  if (rooms.length === 0) {
    return (
      <div style={{ marginTop: "16px", padding: "24px", textAlign: "center", backgroundColor: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-xl)" }}>
        <p style={{ color: "var(--color-text)", fontWeight: 500, marginBottom: "8px" }}>No rooms match your requirements.</p>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "0.875rem", marginBottom: "16px" }}>Try changing time, capacity, or equipment.</p>
        <button style={{ padding: "8px 16px", borderRadius: "var(--radius-md)", border: "1px solid var(--color-border-strong)", backgroundColor: "var(--color-bg)", cursor: "pointer", fontSize: "0.875rem" }}>
          Try another request
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px", maxWidth: "100%" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
        {rooms.map(room => (
          <RoomCard 
            key={room.room_id}
            room={room}
            isSelected={selectedRoomId === room.room_id}
            onSelect={onSelectRoom}
          />
        ))}
      </div>
    </div>
  );
}

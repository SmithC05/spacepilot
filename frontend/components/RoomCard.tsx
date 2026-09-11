import React, { useState } from "react";
import { Room } from "@/types/room";
import { Button } from "./Button";

interface RoomCardProps {
  room: Room;
  isSelected: boolean;
  onSelect: (room: Room) => void;
}

export function RoomCard({ room, isSelected, onSelect }: RoomCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="animate-timeline-enter card-interactive"
      onClick={() => onSelect(room)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        backgroundColor: isSelected || isHovered ? "var(--color-surface-subtle)" : "var(--color-surface)",
        border: isSelected ? "2px solid var(--color-accent)" : "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        position: "relative",
        transition: "all 200ms ease",
        height: "100%", // for grid alignment
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <h3 style={{ margin: 0, fontSize: "1.125rem", color: "var(--color-text)", fontWeight: 600 }}>
          {room.name}
        </h3>
        {room.isRecommended && (
          <span
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFF",
              fontSize: "0.75rem",
              padding: "4px 8px",
              borderRadius: "var(--radius-full)",
              fontWeight: 500,
            }}
          >
            Recommended
          </span>
        )}
      </div>

      {/* Meta Info */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", color: "var(--color-text-secondary)", fontSize: "0.875rem" }}>
        <span>{room.capacity} seats</span>
        <span>•</span>
        <span>{room.distance_m}m away</span>
      </div>

      {/* Amenities */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "4px" }}>
        {room.projector && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.875rem", color: "var(--color-text)" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Projector
          </div>
        )}
        {room.whiteboard && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.875rem", color: "var(--color-text)" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Whiteboard
          </div>
        )}
        {room.accessible && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.875rem", color: "var(--color-text)" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Accessible
          </div>
        )}
      </div>

      {/* Recommendation Reason */}
      {room.isRecommended && room.recommendationReason && (
        <div style={{ 
          marginTop: "8px", 
          padding: "12px", 
          backgroundColor: "var(--color-bg)", 
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--color-border)",
          fontSize: "0.875rem",
          color: "var(--color-text-secondary)",
          lineHeight: 1.5
        }}>
          {room.recommendationReason}
        </div>
      )}

      {/* Actions */}
      <div style={{ marginTop: "auto", paddingTop: "16px", display: "flex", gap: "12px" }}>
        <Button 
          variant={isSelected ? "primary" : "secondary"} 
          onClick={(e) => { e.stopPropagation(); onSelect(room); }}
          style={{ flex: 1 }}
        >
          {isSelected ? "Selected" : "Select Room"}
        </Button>
      </div>
    </div>
  );
}

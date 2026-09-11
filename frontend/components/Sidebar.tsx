import React from "react";
import { Button } from "./Button";

export interface ConversationMeta {
  id: string;
  title: string;
  createdAt: number;
}

export interface BookedRoomMeta {
  id: string;
  name: string;
  date: string;
  people: number;
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: ConversationMeta[];
  bookedRooms: BookedRoomMeta[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  isMobile: boolean;
}

export function Sidebar({
  isOpen,
  onClose,
  conversations,
  bookedRooms,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  isMobile,
}: SidebarProps) {
  if (!isOpen && !isMobile) return null;

  const sidebarContent = (
    <div
      style={{
        width: 280,
        height: "100%",
        backgroundColor: "var(--color-surface)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        transition: "transform var(--duration-base) ease",
        transform: isMobile ? (isOpen ? "translateX(0)" : "translateX(-100%)") : "none",
        position: isMobile ? "fixed" : "relative",
        top: isMobile ? 0 : "auto",
        left: isMobile ? 0 : "auto",
        zIndex: isMobile ? 100 : 1,
      }}
    >
      <div style={{ padding: "20px 16px", flexShrink: 0 }}>
        <Button variant="secondary" onClick={onNewChat} style={{ width: "100%", justifyContent: "flex-start", padding: "0 12px" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          New chat
        </Button>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "0 16px 20px", display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Chat History */}
        <div>
          <h3 style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "12px", paddingLeft: "4px" }}>
            Chat History
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {conversations.length === 0 ? (
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", paddingLeft: "4px" }}>No recent chats</span>
            ) : (
              conversations.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => {
                    onSelectConversation(conv.id);
                    if (isMobile) onClose();
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 12px",
                    borderRadius: "var(--radius-md)",
                    border: "none",
                    backgroundColor: activeConversationId === conv.id ? "var(--color-accent-subtle)" : "transparent",
                    color: activeConversationId === conv.id ? "var(--color-text)" : "var(--color-text-secondary)",
                    fontSize: "0.875rem",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    transition: "background-color var(--duration-fast) ease",
                  }}
                  onMouseEnter={(e) => {
                    if (activeConversationId !== conv.id) e.currentTarget.style.backgroundColor = "var(--color-surface-subtle)";
                  }}
                  onMouseLeave={(e) => {
                    if (activeConversationId !== conv.id) e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  {conv.title}
                </button>
              ))
            )}
          </div>
        </div>

        <div style={{ height: 1, backgroundColor: "var(--color-border)", margin: "0 4px" }} />

        {/* Booked Rooms */}
        <div>
          <h3 style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "12px", paddingLeft: "4px" }}>
            Booked Rooms
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {bookedRooms.length === 0 ? (
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", paddingLeft: "4px" }}>No bookings yet</span>
            ) : (
              bookedRooms.map(room => (
                <div key={room.id} style={{ display: "flex", flexDirection: "column", gap: "4px", padding: "10px 12px", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", backgroundColor: "var(--color-bg)" }}>
                  <strong style={{ fontSize: "0.875rem", color: "var(--color-text)" }}>{room.name}</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>{room.date}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" }}>
                    <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--color-accent)" }} />
                    <span style={{ fontSize: "0.75rem", color: "var(--color-accent)", fontWeight: 500 }}>Booked</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );

  return (
    <>
      {isMobile && isOpen && (
        <div
          onClick={onClose}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.4)",
            zIndex: 90,
          }}
        />
      )}
      {sidebarContent}
    </>
  );
}

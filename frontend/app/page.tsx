"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { Button } from "@/components/Button";
import { ChatMessage } from "@/components/ChatMessage";
import { AgentActivityTimeline, TimelineStep, TimelineStatus } from "@/components/AgentActivityTimeline";
import { Header } from "@/components/Header";
import { QuickActions } from "@/components/QuickActions";
import { RoomResults } from "@/components/RoomResults";
import { BookingPanel } from "@/components/BookingPanel";
import { BookingConfirmation } from "@/components/BookingConfirmation";
import { RouteDetails } from "@/components/RouteDetails";
import { BookingSuccess } from "@/components/BookingSuccess";
import { Sidebar, ConversationMeta, BookedRoomMeta } from "@/components/Sidebar";
import { Room, BookingState } from "@/types/room";
import { RouteData } from "@/types/route";
import { AppNotification } from "@/types/notification";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type BackendStatus = "checking" | "connected" | "disconnected";
type AppView = "chat" | "profile" | "settings";

interface Message {
  id: number;
  role: "user" | "agent";
  text?: string;
  type?: "text" | "room_results" | "booking_confirmation" | "route_details" | "booking_success";
  rooms?: Room[];
  selectedRoomId?: string | null;
  bookingState?: BookingState;
  routeData?: RouteData;
  room?: Room; // for booking success
}

interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
}

const MOCK_ROOMS: Room[] = [
  { room_id: "R402", name: "Room 402", capacity: 10, projector: true, whiteboard: true, accessible: true, distance_m: 180, available: true, isRecommended: true, recommendationReason: "Best match for your request — enough capacity, projector available, and an accessible route." },
  { room_id: "R305", name: "Room 305", capacity: 12, projector: true, whiteboard: false, accessible: true, distance_m: 320, available: true },
  { room_id: "R210", name: "Room 210", capacity: 8, projector: false, whiteboard: false, accessible: true, distance_m: 140, available: true }
];

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [messages, setMessages] = useState<Message[]>([]);
  const [executionTimeline, setExecutionTimeline] = useState<TimelineStep[] | null>(null);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // App State
  const [currentView, setCurrentView] = useState<AppView>("chat");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [bookedRooms, setBookedRooms] = useState<BookedRoomMeta[]>([]);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  // Health check & initialization
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        setBackendStatus(res.ok ? "connected" : "disconnected");
      } catch {
        setBackendStatus("disconnected");
      }
    };
    check();

    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);

    // Load from local storage
    const savedConvs = localStorage.getItem("sp_conversations");
    if (savedConvs) setConversations(JSON.parse(savedConvs));

    const savedRooms = localStorage.getItem("sp_bookedRooms");
    if (savedRooms) setBookedRooms(JSON.parse(savedRooms));

    const savedNotifs = localStorage.getItem("sp_notifications");
    if (savedNotifs) setNotifications(JSON.parse(savedNotifs));

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Save changes to local storage
  useEffect(() => {
    if (conversations.length > 0) localStorage.setItem("sp_conversations", JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    if (bookedRooms.length > 0) localStorage.setItem("sp_bookedRooms", JSON.stringify(bookedRooms));
  }, [bookedRooms]);

  useEffect(() => {
    if (notifications.length > 0) localStorage.setItem("sp_notifications", JSON.stringify(notifications));
  }, [notifications]);

  // Sync active conversation messages
  useEffect(() => {
    if (activeConversationId) {
      setConversations(prev => prev.map(c => c.id === activeConversationId ? { ...c, messages } : c));
    }
  }, [messages, activeConversationId]);

  // Auto-scroll
  useEffect(() => {
    if (currentView === "chat") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, executionTimeline, currentView]);

  const handleNewChat = () => {
    setMessages([]);
    setActiveConversationId(null);
    setExecutionTimeline(null);
    setCurrentView("chat");
    if (isMobile) setIsSidebarOpen(false);
  };

  const handleSelectConversation = (id: string) => {
    const conv = conversations.find(c => c.id === id);
    if (conv) {
      setMessages(conv.messages);
      setActiveConversationId(conv.id);
    }
    setExecutionTimeline(null);
    setCurrentView("chat");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || executionTimeline !== null) return;

    if (!activeConversationId) {
      const newId = Date.now().toString();
      setActiveConversationId(newId);
      setConversations(prev => [{ id: newId, title: text, createdAt: Date.now(), messages: [] }, ...prev]);
    }

    const userMsg: Message = { id: Date.now(), role: "user", text, type: "text" };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    const searchSteps: TimelineStep[] = [
      { id: "1", title: "Understanding request", description: "8 people · Tomorrow · 4:00 PM", status: "pending" },
      { id: "2", title: "Checking team availability", status: "pending" },
      { id: "3", title: "Searching available rooms", description: "Finding rooms matching your requirements", status: "pending" },
      { id: "4", title: "Comparing room options", status: "pending" },
      { id: "5", title: "Checking campus policy", status: "pending" },
      { id: "6", title: "Selecting the best option", status: "pending" },
    ];
    setExecutionTimeline(searchSteps);

    let currentSteps = [...searchSteps];
    const updateStep = (idx: number, status: TimelineStatus) => {
      currentSteps = currentSteps.map((s, i) => i === idx ? { ...s, status } : s);
      setExecutionTimeline(currentSteps);
    };

    updateStep(0, "running");

    setTimeout(() => { updateStep(0, "completed"); updateStep(1, "running"); }, 500);
    setTimeout(() => { updateStep(1, "completed"); updateStep(2, "running"); }, 900);
    setTimeout(() => { updateStep(2, "completed"); updateStep(3, "running"); }, 1400);
    setTimeout(() => { updateStep(3, "completed"); updateStep(4, "running"); }, 1900);
    setTimeout(() => { updateStep(4, "completed"); updateStep(5, "running"); }, 2400);
    setTimeout(() => {
      updateStep(5, "completed");
      setTimeout(() => {
        setExecutionTimeline(null);
        const agentTextMsg: Message = { id: Date.now() + 1, role: "agent", type: "text", text: "Here are the best matches I found." };
        const agentRoomsMsg: Message = { id: Date.now() + 2, role: "agent", type: "room_results", rooms: MOCK_ROOMS, selectedRoomId: null, bookingState: "idle" };
        setMessages((prev) => [...prev, agentTextMsg, agentRoomsMsg]);
      }, 500);
    }, 2900);
  };

  const handleSelectRoom = (msgId: number, room: Room) => {
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, selectedRoomId: room.room_id } : m));
  };

  const handleBookRoom = (msgId: number, room: Room) => {
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, bookingState: "booking" } : m));
    
    const bookingSteps: TimelineStep[] = [
      { id: "7", title: "Creating booking", status: "pending" },
      { id: "8", title: "Verifying booking", status: "pending" },
    ];
    setExecutionTimeline(bookingSteps);

    let currentSteps = [...bookingSteps];
    const updateStep = (idx: number, status: TimelineStatus) => {
      currentSteps = currentSteps.map((s, i) => i === idx ? { ...s, status } : s);
      setExecutionTimeline(currentSteps);
    };

    updateStep(0, "running");
    
    setTimeout(() => { updateStep(0, "completed"); updateStep(1, "running"); }, 600);
    setTimeout(() => {
      updateStep(1, "completed");
      setTimeout(() => {
        setExecutionTimeline(null);
        setMessages(prev => prev.map(m => m.id === msgId ? { ...m, type: "booking_confirmation", bookingState: "confirmed" } : m));
      }, 500);
    }, 1200);
  };

  const handleViewRoute = (room: Room) => {
    const mockRoute: RouteData = {
      destination: room.name,
      distance_m: room.distance_m,
      duration_minutes: Math.ceil(room.distance_m / 60),
      accessible: room.accessible,
      steps: [
        "Enter through the main entrance.",
        "Follow the main corridor.",
        room.accessible ? "Take the elevator." : "Take the stairs.",
        `Continue to ${room.name}.`
      ]
    };

    const routeMsg: Message = { id: Date.now(), role: "agent", type: "route_details", routeData: mockRoute };
    setMessages(prev => [...prev, routeMsg]);

    setTimeout(() => {
      const successMsg: Message = { id: Date.now() + 1, role: "agent", type: "booking_success", room };
      setMessages(prev => [...prev, successMsg]);

      const newBookedRoom: BookedRoomMeta = { id: Date.now().toString(), name: room.name, date: "Tomorrow · 4:00 PM", people: room.capacity };
      setBookedRooms(prev => [newBookedRoom, ...prev]);

      const newNotif: AppNotification = { id: Date.now().toString(), title: "Booking successful", message: `${room.name} · Tomorrow at 4:00 PM`, read: false, timestamp: Date.now() };
      setNotifications(prev => [newNotif, ...prev]);
    }, 1500);
  };

  const renderComposer = (isEmpty: boolean) => (
    <div
      className={isEmpty ? "animate-fade-in" : ""}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        width: "100%",
        maxWidth: 800,
        alignSelf: "center",
        animationDelay: isEmpty ? "150ms" : "0ms",
        animationFillMode: isEmpty ? "both" : "none",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: 12,
          alignItems: "center",
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-xl)",
          padding: "10px 10px 10px 20px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.04)",
          transition: "border-color var(--duration-base) ease, box-shadow var(--duration-base) ease",
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "var(--color-accent)";
          e.currentTarget.style.boxShadow = "0 0 0 3px var(--color-accent-ring)";
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = "var(--color-border)";
          e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.04)";
        }}
      >
        <input
          id="chat-input"
          placeholder='Ask SpacePilot anything... "Book a room for 8 people"'
          value={input}
          onChange={(e) => setInput(e.target.value)}
          autoComplete="off"
          disabled={executionTimeline !== null}
          style={{ flex: 1, border: "none", outline: "none", background: "transparent", fontSize: "1rem", color: "var(--color-text)" }}
        />
        <Button
          id="chat-send-btn"
          type="submit"
          variant="primary"
          disabled={!input.trim() || executionTimeline !== null}
          loading={executionTimeline !== null}
          style={{ borderRadius: "var(--radius-full)", padding: "0 22px", height: "40px" }}
        >
          Send
        </Button>
      </form>
      <div style={{ alignSelf: "center", marginBottom: isEmpty ? 0 : 8, marginTop: 4 }}>
        <QuickActions isInitial={isEmpty} />
      </div>
    </div>
  );

  const renderProfileView = () => (
    <div className="animate-fade-in" style={{ width: "100%", maxWidth: 600, display: "flex", flexDirection: "column", gap: "24px" }}>
      <button 
        onClick={() => setCurrentView("chat")}
        style={{ display: "flex", alignItems: "center", gap: "8px", background: "none", border: "none", color: "var(--color-text-secondary)", cursor: "pointer", fontSize: "0.9375rem", alignSelf: "flex-start", padding: 0 }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Back
      </button>
      
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 600, color: "var(--color-text)", margin: "0 0 8px 0" }}>Profile</h2>
      </div>

      <div style={{ backgroundColor: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-xl)", padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <div style={{ width: 80, height: 80, borderRadius: "50%", backgroundColor: "var(--color-text)", color: "var(--color-bg)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2rem", fontWeight: 600 }}>JD</div>
          <div>
            <strong style={{ display: "block", fontSize: "1.25rem", color: "var(--color-text)", marginBottom: "4px" }}>JD</strong>
            <span style={{ color: "var(--color-text-secondary)", fontSize: "0.9375rem" }}>Active User</span>
          </div>
        </div>
        
        <div style={{ height: 1, backgroundColor: "var(--color-border)" }} />
        
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <span style={{ display: "block", fontSize: "0.8125rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>Name</span>
            <span style={{ fontSize: "1rem", color: "var(--color-text)" }}>JD</span>
          </div>
          <div>
            <span style={{ display: "block", fontSize: "0.8125rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>Account Information</span>
            <span style={{ fontSize: "1rem", color: "var(--color-text-secondary)" }}>user@spacepilot.local (placeholder)</span>
          </div>
          <div>
            <span style={{ display: "block", fontSize: "0.8125rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>Current Theme</span>
            <span style={{ fontSize: "1rem", color: "var(--color-text)", textTransform: "capitalize" }}>
              {typeof document !== 'undefined' ? (document.documentElement.classList.contains('dark') ? 'Dark' : 'Light') : 'System'}
            </span>
          </div>
          <div>
            <span style={{ display: "block", fontSize: "0.8125rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>Account Status</span>
            <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: "var(--radius-full)", backgroundColor: "var(--color-accent-subtle)", color: "var(--color-accent)", fontSize: "0.8125rem", fontWeight: 500 }}>
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSettingsView = () => (
    <div className="animate-fade-in" style={{ width: "100%", maxWidth: 600, display: "flex", flexDirection: "column", gap: "24px" }}>
      <button 
        onClick={() => setCurrentView("chat")}
        style={{ display: "flex", alignItems: "center", gap: "8px", background: "none", border: "none", color: "var(--color-text-secondary)", cursor: "pointer", fontSize: "0.9375rem", alignSelf: "flex-start", padding: 0 }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        Back
      </button>
      
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 600, color: "var(--color-text)", margin: "0 0 8px 0" }}>Settings</h2>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
        
        {/* Appearance */}
        <div>
          <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--color-text)", borderBottom: "1px solid var(--color-border)", paddingBottom: "8px", marginBottom: "16px" }}>Appearance</h3>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", backgroundColor: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)" }}>
            <div>
              <strong style={{ display: "block", fontSize: "0.9375rem", color: "var(--color-text)" }}>Theme</strong>
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>Choose light or dark mode.</span>
            </div>
            <div style={{ display: "flex", gap: "8px", backgroundColor: "var(--color-bg)", padding: "4px", borderRadius: "var(--radius-full)", border: "1px solid var(--color-border)" }}>
              <button 
                onClick={() => {
                  document.documentElement.classList.remove("dark");
                  localStorage.setItem("theme", "light");
                  // Trigger re-render by doing a fake state update or let Header handle it
                  window.dispatchEvent(new Event("theme-change"));
                }}
                style={{ padding: "6px 16px", borderRadius: "var(--radius-full)", border: "none", backgroundColor: typeof document !== 'undefined' && !document.documentElement.classList.contains("dark") ? "var(--color-surface)" : "transparent", color: typeof document !== 'undefined' && !document.documentElement.classList.contains("dark") ? "var(--color-text)" : "var(--color-text-muted)", cursor: "pointer", fontSize: "0.875rem", fontWeight: 500, boxShadow: typeof document !== 'undefined' && !document.documentElement.classList.contains("dark") ? "0 2px 4px rgba(0,0,0,0.05)" : "none" }}
              >
                Light
              </button>
              <button 
                onClick={() => {
                  document.documentElement.classList.add("dark");
                  localStorage.setItem("theme", "dark");
                  window.dispatchEvent(new Event("theme-change"));
                }}
                style={{ padding: "6px 16px", borderRadius: "var(--radius-full)", border: "none", backgroundColor: typeof document !== 'undefined' && document.documentElement.classList.contains("dark") ? "var(--color-surface)" : "transparent", color: typeof document !== 'undefined' && document.documentElement.classList.contains("dark") ? "var(--color-text)" : "var(--color-text-muted)", cursor: "pointer", fontSize: "0.875rem", fontWeight: 500, boxShadow: typeof document !== 'undefined' && document.documentElement.classList.contains("dark") ? "0 2px 4px rgba(0,0,0,0.05)" : "none" }}
              >
                Dark
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div>
          <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--color-text)", borderBottom: "1px solid var(--color-border)", paddingBottom: "8px", marginBottom: "16px" }}>Notifications</h3>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", backgroundColor: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)" }}>
            <div>
              <strong style={{ display: "block", fontSize: "0.9375rem", color: "var(--color-text)" }}>Notification preferences</strong>
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>Manage alerts and UI popups. (Frontend only)</span>
            </div>
            <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
              <input type="checkbox" defaultChecked style={{ width: 18, height: 18, accentColor: "var(--color-accent)" }} />
            </label>
          </div>
        </div>

        {/* Account */}
        <div>
          <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--color-text)", borderBottom: "1px solid var(--color-border)", paddingBottom: "8px", marginBottom: "16px" }}>Account</h3>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", backgroundColor: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", cursor: "pointer" }} onClick={() => setCurrentView("profile")}>
            <div>
              <strong style={{ display: "block", fontSize: "0.9375rem", color: "var(--color-text)" }}>Profile</strong>
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>Manage your public information.</span>
            </div>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </div>
        </div>

      </div>
    </div>
  );

  return (
    <div
      className="page-bg animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100dvh",
        maxHeight: "100dvh",
        overflow: "hidden",
      }}
    >
      <Header 
        backendStatus={backendStatus} 
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        notifications={notifications}
        onMarkNotificationsRead={() => setNotifications(prev => prev.map(n => ({ ...n, read: true })))}
        onNavigate={setCurrentView}
      />

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          conversations={conversations}
          bookedRooms={bookedRooms}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          isMobile={isMobile}
        />

        <main
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: currentView === "chat" && messages.length === 0 ? "center" : "flex-start",
            width: "100%",
            padding: "32px 20px",
            overflowY: "auto",
          }}
        >
          {currentView === "profile" && renderProfileView()}
          {currentView === "settings" && renderSettingsView()}
          
          {currentView === "chat" && (
            <div
              style={{
                width: "100%",
                maxWidth: messages.length === 0 ? 800 : 1100,
                display: "flex",
                flexDirection: "column",
                justifyContent: messages.length === 0 ? "center" : "flex-start",
                flex: messages.length === 0 ? 1 : undefined,
                gap: 24,
                transition: "max-width 0.3s ease",
              }}
            >
              {/* Empty State / Welcome */}
              {messages.length === 0 && (
                <div
                  className="animate-welcome"
                  style={{
                    textAlign: "center",
                    marginBottom: "24px",
                  }}
                >
                  <h2 style={{ fontSize: "30px", fontWeight: 600, color: "var(--color-text)", marginBottom: "8px", letterSpacing: "-0.02em" }}>
                    How can SpacePilot help?
                  </h2>
                  <p style={{ fontSize: "16px", color: "var(--color-text-secondary)" }}>
                    Ask naturally. I'll handle the workflow for you.
                  </p>
                </div>
              )}

              {/* Messages area */}
              {messages.length > 0 && (
                <div id="chat-messages" style={{ display: "flex", flexDirection: "column", gap: 16, paddingBottom: 20 }}>
                  {messages.map((msg) => {
                    if (msg.type === "text" || !msg.type) {
                      return <ChatMessage key={msg.id} role={msg.role} text={msg.text || ""} />;
                    }

                    if (msg.type === "room_results" && msg.rooms) {
                      const selectedRoom = msg.rooms.find(r => r.room_id === msg.selectedRoomId);
                      return (
                        <div key={msg.id} style={{ display: "flex", flexDirection: "column" }}>
                          <RoomResults rooms={msg.rooms} selectedRoomId={msg.selectedRoomId || null} onSelectRoom={(r) => handleSelectRoom(msg.id, r)} />
                          {selectedRoom && <BookingPanel room={selectedRoom} bookingState={msg.bookingState || "idle"} onBook={() => handleBookRoom(msg.id, selectedRoom)} />}
                        </div>
                      );
                    }

                    if (msg.type === "booking_confirmation" && msg.rooms) {
                      const confirmedRoom = msg.rooms.find(r => r.room_id === msg.selectedRoomId) || msg.rooms[0];
                      return (
                        <div key={msg.id} style={{ display: "flex", flexDirection: "column" }}>
                          <BookingConfirmation room={confirmedRoom} onViewRoute={() => handleViewRoute(confirmedRoom)} />
                        </div>
                      );
                    }

                    if (msg.type === "route_details" && msg.routeData) {
                      return <div key={msg.id}><RouteDetails route={msg.routeData} /></div>;
                    }

                    if (msg.type === "booking_success" && msg.room) {
                      return <div key={msg.id}><BookingSuccess room={msg.room} /></div>;
                    }
                    
                    return null;
                  })}

                  {executionTimeline && (
                    <div style={{ alignSelf: "flex-start", maxWidth: "100%" }}>
                      <AgentActivityTimeline steps={executionTimeline} />
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}

              {/* Render composer inside scroll area ONLY when empty */}
              {messages.length === 0 && renderComposer(true)}
            </div>
          )}
        </main>
      </div>

      {/* Render composer docked at bottom when active */}
      {currentView === "chat" && messages.length > 0 && (
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
            padding: "16px 20px 24px",
            backgroundColor: "var(--color-bg)",
            borderTop: "1px solid var(--color-border)",
            zIndex: 10,
          }}
        >
          {renderComposer(false)}
        </div>
      )}
    </div>
  );
}

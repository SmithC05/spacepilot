"use client";

import React, { useState, useEffect, useRef } from "react";
import { AppNotification } from "@/types/notification";

interface HeaderProps {
  backendStatus: "checking" | "connected" | "disconnected";
  onToggleSidebar?: () => void;
  notifications?: AppNotification[];
  onMarkNotificationsRead?: () => void;
  onNavigate?: (view: "profile" | "settings") => void;
}

export function Header({ backendStatus, onToggleSidebar, notifications = [], onMarkNotificationsRead, onNavigate }: HeaderProps) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationRef = useRef<HTMLDivElement>(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    if (document.documentElement.classList.contains("dark")) {
      setTheme("dark");
    } else {
      setTheme("light");
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShowNotifications(false);
        setShowProfileMenu(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const changeTheme = (newTheme: "light" | "dark") => {
    setTheme(newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", newTheme);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        height: "72px",
        backgroundColor: "var(--color-bg)",
        borderBottom: "1px solid var(--color-border)",
        width: "100%",
        position: "sticky",
        top: 0,
        zIndex: 10,
        transition: "background-color var(--duration-fast) ease, border-color var(--duration-fast) ease",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        {/* Hamburger Menu */}
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 36,
            height: 36,
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-border)",
            backgroundColor: "var(--color-surface)",
            color: "var(--color-text)",
            cursor: "pointer",
            transition: "all var(--duration-fast) ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-surface-subtle)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-surface)";
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "var(--radius-sm)",
            background: "var(--color-text)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "background-color var(--duration-fast) ease",
          }}
          aria-hidden
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-bg)"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ transition: "stroke var(--duration-fast) ease" }}
          >
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <h1
            style={{
              fontSize: "1.125rem",
              fontWeight: 700,
              color: "var(--color-text)",
              lineHeight: 1.2,
              letterSpacing: "-0.02em",
              transition: "color var(--duration-fast) ease",
            }}
          >
            SpacePilot
          </h1>
          <p
            style={{
              fontSize: "0.75rem",
              color: "var(--color-text-muted)",
              lineHeight: 1.2,
              transition: "color var(--duration-fast) ease",
            }}
          >
            Your workspace. On autopilot.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        {mounted && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              backgroundColor: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-full)",
              padding: "2px",
              gap: "2px",
              transition: "background-color var(--duration-fast) ease, border-color var(--duration-fast) ease",
            }}
          >
            <button
              onClick={() => changeTheme("light")}
              aria-label="Switch to light mode"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 30,
                height: 30,
                borderRadius: "var(--radius-full)",
                border: "none",
                backgroundColor: theme === "light" ? "var(--color-border)" : "transparent",
                color: theme === "light" ? "var(--color-text)" : "var(--color-text-muted)",
                cursor: "pointer",
                transition: "all var(--duration-fast) ease",
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
            </button>
            <button
              onClick={() => changeTheme("dark")}
              aria-label="Switch to dark mode"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 30,
                height: 30,
                borderRadius: "var(--radius-full)",
                border: "none",
                backgroundColor: theme === "dark" ? "var(--color-border)" : "transparent",
                color: theme === "dark" ? "var(--color-text)" : "var(--color-text-muted)",
                cursor: "pointer",
                transition: "all var(--duration-fast) ease",
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            </button>
          </div>
        )}

        {/* Notifications */}
        <div style={{ position: "relative" }} ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="Notifications"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 36,
              height: 36,
              borderRadius: "50%",
              border: "1px solid var(--color-border)",
              backgroundColor: "var(--color-surface)",
              color: "var(--color-text)",
              cursor: "pointer",
              position: "relative",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            {unreadCount > 0 && (
              <span
                style={{
                  position: "absolute",
                  top: -2,
                  right: -2,
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: "var(--color-accent)",
                  border: "2px solid var(--color-bg)",
                }}
              />
            )}
          </button>

          {/* Notification Panel */}
          {showNotifications && (
            <div
              className="animate-fade-in"
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                right: 0,
                width: 320,
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-lg)",
                boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
                zIndex: 50,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--color-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>Notifications</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={onMarkNotificationsRead}
                    style={{ background: "none", border: "none", color: "var(--color-accent)", fontSize: "0.75rem", cursor: "pointer" }}
                  >
                    Mark all as read
                  </button>
                )}
              </div>
              <div style={{ maxHeight: 300, overflowY: "auto", padding: "8px 0" }}>
                {notifications.length === 0 ? (
                  <div style={{ padding: "16px", textAlign: "center", color: "var(--color-text-muted)", fontSize: "0.875rem" }}>
                    No notifications
                  </div>
                ) : (
                  notifications.map(n => (
                    <div
                      key={n.id}
                      style={{
                        padding: "12px 16px",
                        display: "flex",
                        gap: "12px",
                        backgroundColor: n.read ? "transparent" : "var(--color-accent-subtle)",
                      }}
                    >
                      <div style={{ marginTop: 4 }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: n.read ? "transparent" : "var(--color-accent)", border: n.read ? "1px solid var(--color-border)" : "none" }} />
                      </div>
                      <div>
                        <strong style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "var(--color-text)" }}>{n.title}</strong>
                        <span style={{ fontSize: "0.8125rem", color: "var(--color-text-secondary)" }}>{n.message}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar */}
        <div style={{ position: "relative" }} ref={profileRef}>
          <button
            aria-label="Open profile menu"
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              backgroundColor: "var(--color-text)",
              color: "var(--color-bg)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "none",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.9375rem",
              transition: "transform var(--duration-fast) ease, opacity var(--duration-fast) ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.9";
              e.currentTarget.style.transform = "scale(1.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
              e.currentTarget.style.transform = "scale(1)";
            }}
          >
            JD
          </button>

          {/* Profile Menu */}
          {showProfileMenu && (
            <div
              className="animate-fade-in"
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                right: 0,
                width: 180,
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
                zIndex: 50,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
                padding: "8px 0",
              }}
            >
              <div style={{ padding: "8px 16px", borderBottom: "1px solid var(--color-border)", marginBottom: "4px" }}>
                <strong style={{ display: "block", fontSize: "0.9375rem", fontWeight: 600, color: "var(--color-text)" }}>JD</strong>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)" }}>Profile</span>
              </div>
              
              <button 
                style={menuItemStyle} 
                onMouseEnter={handleMenuHover} 
                onMouseLeave={handleMenuLeave}
                onClick={() => {
                  setShowProfileMenu(false);
                  if (onNavigate) onNavigate("profile");
                }}
              >
                Profile
              </button>
              <button 
                style={menuItemStyle} 
                onMouseEnter={handleMenuHover} 
                onMouseLeave={handleMenuLeave}
                onClick={() => {
                  setShowProfileMenu(false);
                  if (onNavigate) onNavigate("settings");
                }}
              >
                Settings
              </button>
              <button 
                style={menuItemStyle} 
                onMouseEnter={handleMenuHover} 
                onMouseLeave={handleMenuLeave}
                onClick={() => changeTheme(theme === "light" ? "dark" : "light")}
              >
                Theme: {theme === "light" ? "Light" : "Dark"}
              </button>
              
              <div style={{ height: 1, backgroundColor: "var(--color-border)", margin: "4px 0" }} />
              
              <button style={menuItemStyle} onMouseEnter={handleMenuHover} onMouseLeave={handleMenuLeave}>Sign out</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

const menuItemStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  textAlign: "left",
  padding: "8px 16px",
  backgroundColor: "transparent",
  border: "none",
  color: "var(--color-text)",
  fontSize: "0.875rem",
  cursor: "pointer",
  transition: "background-color var(--duration-fast) ease",
};

const handleMenuHover = (e: React.MouseEvent<HTMLButtonElement>) => {
  e.currentTarget.style.backgroundColor = "var(--color-surface-subtle)";
};

const handleMenuLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
  e.currentTarget.style.backgroundColor = "transparent";
};

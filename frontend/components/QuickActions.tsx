import React from "react";

const ACTIONS = [
  {
    label: "Room Booking",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
    )
  },
  {
    label: "Navigation",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>
    )
  },
  {
    label: "Team Availability",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
    )
  },
  {
    label: "Campus Events",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
    )
  },
  {
    label: "Policies",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
    )
  },
];

export function QuickActions({ isInitial = false }: { isInitial?: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        flexWrap: "wrap",
        justifyContent: "center",
        padding: "0 4px",
      }}
    >
      {ACTIONS.map((action, index) => (
        <button
          key={action.label}
          className={isInitial ? "animate-quick-action" : ""}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: "0.875rem",
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-full)",
            padding: "8px 14px",
            cursor: "pointer",
            transition:
              "border-color var(--duration-fast) ease, color var(--duration-fast) ease, transform var(--duration-fast) ease, box-shadow var(--duration-fast) ease",
            animationDelay: isInitial ? `${index * 60}ms` : "0ms",
            animationFillMode: isInitial ? "both" : "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-surface-subtle)";
            e.currentTarget.style.borderColor = "var(--color-border-strong)";
            e.currentTarget.style.color = "var(--color-accent)";
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = "0 2px 6px rgba(0,0,0,0.03)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-surface)";
            e.currentTarget.style.borderColor = "var(--color-border)";
            e.currentTarget.style.color = "var(--color-text-secondary)";
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          <span style={{ color: "inherit", display: "flex" }}>{action.icon}</span>
          {action.label}
        </button>
      ))}
    </div>
  );
}

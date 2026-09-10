import React from "react";

interface CardProps {
  children: React.ReactNode;
  interactive?: boolean;
  padding?: string;
  style?: React.CSSProperties;
  className?: string;
  onClick?: () => void;
}

export function Card({
  children,
  interactive = false,
  padding = "20px",
  style,
  className = "",
  onClick,
}: CardProps) {
  return (
    <div
      className={`card ${interactive ? "card-interactive" : ""} ${className}`}
      style={{ padding, ...style }}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

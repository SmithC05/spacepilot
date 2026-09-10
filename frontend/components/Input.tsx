"use client";

import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: "default" | "chat";
  label?: string;
  error?: string;
}

export function Input({
  variant = "default",
  label,
  error,
  id,
  style,
  ...props
}: InputProps) {
  const inputClass = variant === "chat" ? "input input-chat" : "input";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {label && (
        <label
          htmlFor={id}
          style={{
            fontSize: "0.75rem",
            fontWeight: 500,
            color: "var(--color-text-secondary)",
          }}
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={inputClass}
        style={style}
        aria-invalid={!!error}
        {...props}
      />
      {error && (
        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--color-error)",
          }}
        >
          {error}
        </span>
      )}
    </div>
  );
}

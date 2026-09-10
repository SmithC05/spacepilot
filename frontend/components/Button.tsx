"use client";

import React from "react";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantClass: Record<Variant, string> = {
  primary:   "btn btn-primary",
  secondary: "btn btn-secondary",
  ghost:     "btn btn-ghost",
};

const sizeStyle: Record<Size, React.CSSProperties> = {
  sm: { height: 32, padding: "0 12px", fontSize: "0.8125rem" },
  md: { height: 38, padding: "0 16px", fontSize: "0.875rem" },
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  disabled,
  style,
  ...props
}: ButtonProps) {
  return (
    <button
      className={variantClass[variant]}
      disabled={disabled || loading}
      style={{ ...sizeStyle[size], ...style }}
      {...props}
    >
      {loading ? (
        <span className="spinner" aria-label="Loading" />
      ) : icon ? (
        <span style={{ display: "flex", alignItems: "center" }}>{icon}</span>
      ) : null}
      {children}
    </button>
  );
}

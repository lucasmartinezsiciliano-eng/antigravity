"use client"

import React from "react"

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "gold" | "white" | "ghost"
  size?: "sm" | "md" | "lg"
  fullWidth?: boolean
  children: React.ReactNode
}

const VARIANTS = {
  gold: { background: "#FFFFFF", color: "#000" },
  white: { background: "#F0F0F0", color: "#000" },
  ghost: { background: "transparent", color: "#F0F0F0", border: "1px solid #1C1C1C" },
}

const SIZES = {
  sm: { padding: "10px 18px", fontSize: "13px" },
  md: { padding: "14px 24px", fontSize: "14px" },
  lg: { padding: "16px 32px", fontSize: "14px" },
}

export function GlowButton({
  variant = "gold",
  size = "lg",
  fullWidth = false,
  children,
  style,
  ...props
}: GlowButtonProps) {
  const v = VARIANTS[variant]
  const s = SIZES[size]

  return (
    <button
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        width: fullWidth ? "100%" : undefined,
        ...s,
        background: v.background,
        color: v.color,
        fontWeight: 600,
        letterSpacing: "0.02em",
        border: "border" in v ? (v as any).border : "none",
        borderRadius: 10,
        cursor: "pointer",
        fontFamily: "inherit",
        transition: "opacity 0.12s",
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  )
}

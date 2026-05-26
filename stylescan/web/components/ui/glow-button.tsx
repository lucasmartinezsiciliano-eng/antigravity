/**
 * GlowButton — premium solid CTA button.
 * No excessive glow — clean, confident, decisive.
 * v3 anti-slop: removed cult/ui glow pattern.
 */

"use client"

import React from "react"
import { motion } from "framer-motion"

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "gold" | "white" | "ghost"
  size?: "sm" | "md" | "lg"
  fullWidth?: boolean
  children: React.ReactNode
}

const VARIANTS = {
  gold: {
    background: "#C9A84C",
    color: "#0B0A08",
    hoverBackground: "#D4B55A",
  },
  white: {
    background: "#EAE6E1",
    color: "#0B0A08",
    hoverBackground: "#F5F2EE",
  },
  ghost: {
    background: "transparent",
    color: "#EAE6E1",
    hoverBackground: "rgba(232, 226, 218, 0.05)",
    border: "1px solid #242119",
  },
}

const SIZES = {
  sm: { padding: "12px 20px", fontSize: "13px", borderRadius: "10px" },
  md: { padding: "16px 28px", fontSize: "15px", borderRadius: "12px" },
  lg: { padding: "18px 36px", fontSize: "15px", borderRadius: "9999px" },
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
    <motion.button
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        width: fullWidth ? "100%" : undefined,
        ...s,
        background: v.background,
        color: v.color,
        fontWeight: 600,
        letterSpacing: "0.01em",
        border: "border" in v ? (v as any).border : "none",
        cursor: "pointer",
        userSelect: "none",
        WebkitUserSelect: "none",
        fontFamily: "inherit",
        boxShadow: "none",
        transition: "background 0.2s",
        ...style,
      }}
      {...(props as any)}
    >
      {children}
    </motion.button>
  )
}

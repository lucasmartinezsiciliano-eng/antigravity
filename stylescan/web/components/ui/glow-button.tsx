/**
 * GlowButton — inspired by cult/ui glow-button
 * Gold-glow animated CTA button. Matches VISAI's dark/gold aesthetic.
 * Zero external deps beyond framer-motion (already installed).
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
    color: "#080808",
    glowColor: "rgba(201, 168, 76, 0.45)",
    hoverBackground: "#E8C96B",
  },
  white: {
    background: "#E8E8E8",
    color: "#080808",
    glowColor: "rgba(232, 232, 232, 0.25)",
    hoverBackground: "#FFFFFF",
  },
  ghost: {
    background: "transparent",
    color: "#E8E8E8",
    glowColor: "rgba(232, 232, 232, 0.08)",
    hoverBackground: "rgba(232, 232, 232, 0.05)",
    border: "1px solid #1E1E1E",
  },
}

const SIZES = {
  sm: { padding: "12px 20px", fontSize: "14px", borderRadius: "12px" },
  md: { padding: "16px 28px", fontSize: "16px", borderRadius: "16px" },
  lg: { padding: "20px 36px", fontSize: "17px", borderRadius: "9999px" },
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
      whileTap={{ scale: 0.96 }}
      whileHover={{ scale: 1.01 }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
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
        fontWeight: 700,
        letterSpacing: "0.02em",
        border: "border" in v ? (v as any).border : "none",
        cursor: "pointer",
        userSelect: "none",
        WebkitUserSelect: "none",
        fontFamily: "inherit",
        boxShadow: `0 0 20px ${v.glowColor}, 0 0 60px ${v.glowColor.replace("0.45", "0.15").replace("0.25", "0.1").replace("0.08", "0.03")}`,
        transition: "background 0.2s, box-shadow 0.2s",
        ...style,
      }}
      {...(props as any)}
    >
      {children}
    </motion.button>
  )
}

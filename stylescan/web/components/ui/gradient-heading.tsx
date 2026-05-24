/**
 * GradientHeading — inspired by cult/ui
 * Gradient text heading. Adapted for VISAI's dark theme (no cva/radix deps).
 */

import React from "react"

type Variant = "gold" | "white" | "muted" | "gold-light"
type Size    = "sm" | "md" | "lg" | "xl" | "xxl"
type Weight  = "normal" | "semibold" | "bold" | "black"
type As      = "h1" | "h2" | "h3" | "h4" | "span" | "p"

interface GradientHeadingProps {
  children: React.ReactNode
  variant?: Variant
  size?: Size
  weight?: Weight
  as?: As
  className?: string
  style?: React.CSSProperties
}

const GRADIENTS: Record<Variant, string> = {
  gold:        "linear-gradient(160deg, #E8D48A 0%, #C9A84C 45%, #8B6914 100%)",
  "gold-light":"linear-gradient(160deg, #F5E8B4 0%, #E8C96B 50%, #C9A84C 100%)",
  white:       "linear-gradient(160deg, #FFFFFF 0%, #E8E8E8 60%, #AAAAAA 100%)",
  muted:       "linear-gradient(160deg, #888888 0%, #555555 100%)",
}

const SIZES: Record<Size, string> = {
  sm:  "1.125rem",   // 18px
  md:  "1.5rem",     // 24px
  lg:  "2rem",       // 32px
  xl:  "2.75rem",    // 44px
  xxl: "3.5rem",     // 56px
}

const WEIGHTS: Record<Weight, string> = {
  normal:   "400",
  semibold: "600",
  bold:     "700",
  black:    "900",
}

export function GradientHeading({
  children,
  variant = "white",
  size = "lg",
  weight = "bold",
  as: Tag = "h2",
  className,
  style,
}: GradientHeadingProps) {
  return (
    <Tag className={className} style={{ margin: 0, ...style }}>
      <span
        style={{
          background: GRADIENTS[variant],
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          fontSize: SIZES[size],
          fontWeight: WEIGHTS[weight],
          lineHeight: 1.15,
          letterSpacing: "-0.02em",
          display: "inline-block",
          paddingBottom: "0.1em", // prevents descenders being clipped
        }}
      >
        {children}
      </span>
    </Tag>
  )
}

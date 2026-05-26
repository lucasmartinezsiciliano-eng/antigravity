/**
 * GradientHeading → DisplayHeading
 * v3 anti-slop: no more gradient text trick.
 * Uses Syne display font with solid color. The font IS the design.
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

const COLORS: Record<Variant, string> = {
  gold:        "#C9A84C",
  "gold-light":"#D4B55A",
  white:       "#EAE6E1",
  muted:       "#6B6560",
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
  black:    "800",
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
          color: COLORS[variant],
          fontFamily: "var(--font-display)",
          fontSize: SIZES[size],
          fontWeight: WEIGHTS[weight],
          lineHeight: 1.1,
          letterSpacing: "-0.03em",
          display: "inline-block",
        }}
      >
        {children}
      </span>
    </Tag>
  )
}

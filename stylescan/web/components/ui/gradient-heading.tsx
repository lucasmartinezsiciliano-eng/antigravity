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
  gold:        "#FFFFFF",
  "gold-light":"#FFFFFF",
  white:       "#F0F0F0",
  muted:       "#666666",
}

const SIZES: Record<Size, string> = {
  sm: "1.125rem", md: "1.5rem", lg: "2rem", xl: "2.75rem", xxl: "3.5rem",
}

const WEIGHTS: Record<Weight, string> = {
  normal: "400", semibold: "600", bold: "700", black: "700",
}

export function GradientHeading({
  children, variant = "white", size = "lg", weight = "bold",
  as: Tag = "h2", className, style,
}: GradientHeadingProps) {
  return (
    <Tag className={className} style={{
      margin: 0, color: COLORS[variant], fontSize: SIZES[size],
      fontWeight: WEIGHTS[weight], lineHeight: 1.15, letterSpacing: "-0.01em",
      ...style,
    }}>
      {children}
    </Tag>
  )
}

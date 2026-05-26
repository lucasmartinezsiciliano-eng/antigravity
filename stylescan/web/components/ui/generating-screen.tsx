/**
 * GeneratingScreen — premium minimal progress for AI generation.
 * v3 anti-slop: no fake terminal, no monospace, no macOS traffic lights.
 * Clean typography + subtle animation. Says "we're crafting something" not "look at my code."
 */

"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface StepDef {
  text: string
  delay: number
}

const STEPS: StepDef[] = [
  { text: "Preparando tu imagen",           delay: 0 },
  { text: "Analizando estructura craneal",  delay: 1500 },
  { text: "Aplicando máscara capilar",      delay: 3200 },
  { text: "Generando corte 1",              delay: 5000 },
  { text: "Generando corte 2",              delay: 9500 },
  { text: "Generando corte 3",              delay: 14000 },
]

export function GeneratingScreen() {
  const [activeStep, setActiveStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    STEPS.forEach((step, i) => {
      if (i === 0) return
      const t = setTimeout(() => setActiveStep(i), step.delay)
      timers.current.push(t)
    })

    const tick = setInterval(() => setElapsed((e) => e + 1), 1000)
    timers.current.push(tick as any)

    return () => timers.current.forEach(clearTimeout)
  }, [])

  const progress = Math.min((activeStep / (STEPS.length - 1)) * 100, 100)

  return (
    <div style={{
      minHeight: "100dvh",
      background: "var(--bg)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px 20px",
    }}>

      {/* Pulsing logo mark */}
      <motion.div
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ repeat: Infinity, duration: 2.8, ease: "easeInOut" }}
        style={{ marginBottom: 40 }}
      >
        <svg width="56" height="56" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="40" cy="36" rx="18" ry="23" fill="none" stroke="var(--text)" strokeWidth="0.8" opacity="0.1" />
          <circle cx="31" cy="27" r="2.5" fill="var(--gold)" opacity="0.7" />
          <circle cx="49" cy="27" r="2.5" fill="var(--gold)" opacity="0.7" />
          <circle cx="40" cy="39" r="1.8" fill="var(--gold)" opacity="0.5" />
          <path d="M17 14 L17 22 M17 14 L25 14" stroke="var(--gold)" strokeWidth="0.8" fill="none" opacity="0.3" />
          <path d="M63 14 L63 22 M63 14 L55 14" stroke="var(--gold)" strokeWidth="0.8" fill="none" opacity="0.3" />
          <path d="M17 62 L17 54 M17 62 L25 62" stroke="var(--gold)" strokeWidth="0.8" fill="none" opacity="0.3" />
          <path d="M63 62 L63 54 M63 62 L55 62" stroke="var(--gold)" strokeWidth="0.8" fill="none" opacity="0.3" />
        </svg>
      </motion.div>

      {/* Step text — single line, animated swap */}
      <div style={{ height: 28, overflow: "hidden", marginBottom: 24 }}>
        <AnimatePresence mode="wait">
          <motion.p
            key={activeStep}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
            style={{
              fontSize: 15,
              fontWeight: 500,
              color: "var(--text)",
              margin: 0,
              textAlign: "center",
              letterSpacing: "-0.01em",
            }}
          >
            {STEPS[activeStep].text}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Progress bar — thin, gold, elegant */}
      <div style={{
        width: "100%",
        maxWidth: 200,
        height: 2,
        background: "var(--border)",
        borderRadius: 1,
        overflow: "hidden",
        marginBottom: 32,
      }}>
        <motion.div
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          style={{
            height: "100%",
            background: "var(--gold)",
            borderRadius: 1,
          }}
        />
      </div>

      {/* Time + hint */}
      <p style={{
        color: "var(--text-dim)",
        fontSize: 13,
        margin: 0,
        textAlign: "center",
        fontWeight: 300,
      }}>
        {elapsed > 0 && <span>{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")} · </span>}
        Generando 6 imágenes con IA
      </p>

    </div>
  )
}

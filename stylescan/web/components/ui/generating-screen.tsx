"use client"

import { useEffect, useState, useRef } from "react"

const STEPS = [
  { text: "Preparando imagen", delay: 0 },
  { text: "Analizando estructura craneal", delay: 1500 },
  { text: "Aplicando máscara capilar", delay: 3200 },
  { text: "Generando corte 1", delay: 5000 },
  { text: "Generando corte 2", delay: 9500 },
  { text: "Generando corte 3", delay: 14000 },
]

export function GeneratingScreen() {
  const [step, setStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    STEPS.forEach((s, i) => {
      if (i === 0) return
      timers.current.push(setTimeout(() => setStep(i), s.delay))
    })
    const tick = setInterval(() => setElapsed((e) => e + 1), 1000)
    timers.current.push(tick as any)
    return () => timers.current.forEach(clearTimeout)
  }, [])

  return (
    <div style={{
      minHeight: "100dvh", background: "#000",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      padding: "24px 20px",
    }}>
      <div style={{ marginBottom: 32, textAlign: "center" }}>
        <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>VISAI</div>
        <div style={{ width: 120, height: 1, background: "var(--border)", margin: "0 auto" }} />
      </div>

      <p style={{ fontSize: 14, fontWeight: 500, color: "var(--text)", margin: "0 0 8px", textAlign: "center" }}>
        {STEPS[step].text}
      </p>

      <div style={{ width: 160, height: 2, background: "var(--border)", borderRadius: 1, overflow: "hidden", marginBottom: 24 }}>
        <div style={{
          height: "100%", background: "var(--gold)", borderRadius: 1,
          width: `${Math.min((step / (STEPS.length - 1)) * 100, 100)}%`,
          transition: "width 0.5s ease",
        }} />
      </div>

      <p style={{ color: "var(--text-dim)", fontSize: 12, margin: 0, textAlign: "center" }}>
        {elapsed > 0 && `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")} · `}
        6 imágenes · 1-2 min
      </p>
    </div>
  )
}

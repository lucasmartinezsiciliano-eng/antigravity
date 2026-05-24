/**
 * GeneratingScreen — terminal-style animation for the AI generation step.
 * Inspired by cult/ui terminal-animation. Uses only framer-motion (already installed).
 *
 * Shows sequential log lines appearing one by one while fal.ai generates images.
 * Each line auto-advances after a delay. The last line stays as "processing"
 * until the parent signals completion by unmounting this component.
 */

"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Sparkles } from "lucide-react"

type LineStatus = "done" | "active" | "pending"

interface LogLine {
  id: string
  text: string
  delay: number      // ms before this line appears
  duration: number   // ms this line stays "active" before becoming "done"
}

const LINES: LogLine[] = [
  { id: "l1", text: "Cargando tu foto",           delay: 300,  duration: 1200 },
  { id: "l2", text: "Extrayendo mapa craneal",     delay: 1600, duration: 1400 },
  { id: "l3", text: "Aplicando máscara capilar",   delay: 3100, duration: 1600 },
  { id: "l4", text: "Generando corte 1 · frontal", delay: 4800, duration: 2200 },
  { id: "l5", text: "Generando corte 1 · lateral", delay: 7100, duration: 2200 },
  { id: "l6", text: "Generando corte 2 · frontal", delay: 9400, duration: 2200 },
  { id: "l7", text: "Generando corte 2 · lateral", delay: 11700, duration: 2200 },
  { id: "l8", text: "Generando corte 3 · frontal", delay: 14000, duration: 2200 },
  { id: "l9", text: "Generando corte 3 · lateral", delay: 16300, duration: 99999 },
]

function SpinnerIcon() {
  return (
    <motion.span
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
      style={{ display: "inline-block", width: 12, height: 12 }}
    >
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="4.5" stroke="rgba(201,168,76,0.25)" strokeWidth="1.5" />
        <path d="M6 1.5A4.5 4.5 0 0 1 10.5 6" stroke="#C9A84C" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </motion.span>
  )
}

function DoneIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="5" fill="rgba(61,184,130,0.15)" />
      <path d="M3.5 6 L5.5 8 L8.5 4" stroke="#3DB882" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function GeneratingScreen() {
  const [visibleLines, setVisibleLines] = useState<{ id: string; status: LineStatus }[]>([])
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    LINES.forEach((line) => {
      // Appear
      const t1 = setTimeout(() => {
        setVisibleLines((prev) => [...prev, { id: line.id, status: "active" }])
      }, line.delay)

      // Turn to done
      if (line.duration < 99999) {
        const t2 = setTimeout(() => {
          setVisibleLines((prev) =>
            prev.map((l) => l.id === line.id ? { ...l, status: "done" } : l)
          )
        }, line.delay + line.duration)
        timers.current.push(t1, t2)
      } else {
        timers.current.push(t1)
      }
    })

    return () => timers.current.forEach(clearTimeout)
  }, [])

  const activeId = visibleLines.find((l) => l.status === "active")?.id

  return (
    <div style={{
      minHeight: "100dvh",
      background: "#080808",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px 20px",
    }}>
      {/* Icon */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        style={{
          width: 64,
          height: 64,
          borderRadius: 18,
          background: "rgba(201,168,76,0.08)",
          border: "1px solid rgba(201,168,76,0.18)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 28,
        }}
      >
        <motion.div
          animate={{ rotate: [0, 10, -10, 10, 0] }}
          transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        >
          <Sparkles size={26} color="#C9A84C" strokeWidth={1.5} />
        </motion.div>
      </motion.div>

      {/* Terminal window */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.4 }}
        style={{
          width: "100%",
          maxWidth: 360,
          background: "#0C0C0C",
          border: "1px solid #1E1E1E",
          borderRadius: 14,
          overflow: "hidden",
          boxShadow: "0 0 40px rgba(201,168,76,0.04)",
        }}
      >
        {/* Terminal titlebar */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "10px 14px",
          borderBottom: "1px solid #1A1A1A",
          background: "#0A0A0A",
        }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#FF5F56", display: "block" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#FFBD2E", display: "block" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#27C93F", display: "block" }} />
          <span style={{ fontSize: 11, color: "#444", marginLeft: 8, fontFamily: "monospace" }}>visai — prueba virtual</span>
        </div>

        {/* Terminal body */}
        <div style={{ padding: "14px 16px", minHeight: 200, fontFamily: "monospace" }}>
          {/* Prompt line */}
          <div style={{ color: "#555", fontSize: 12, marginBottom: 12 }}>
            <span style={{ color: "#3DB882" }}>▶</span>
            {" "}
            <span style={{ color: "#888" }}>visai generate</span>
            {" "}
            <span style={{ color: "#C9A84C" }}>--cuts=3 --angles=2</span>
          </div>

          {/* Animated log lines */}
          <AnimatePresence>
            {visibleLines.map(({ id, status }) => {
              const line = LINES.find((l) => l.id === id)!
              return (
                <motion.div
                  key={id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 8,
                    fontSize: 12,
                  }}
                >
                  {status === "done"   && <DoneIcon />}
                  {status === "active" && <SpinnerIcon />}
                  <span style={{
                    color: status === "done" ? "#555" : status === "active" ? "#E8E8E8" : "#333",
                  }}>
                    {line.text}
                    {status === "active" && (
                      <motion.span
                        animate={{ opacity: [1, 0, 1] }}
                        transition={{ repeat: Infinity, duration: 0.9 }}
                        style={{ color: "#C9A84C", marginLeft: 4 }}
                      >
                        _
                      </motion.span>
                    )}
                  </span>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {/* Blinking cursor at the end */}
          <motion.div
            animate={{ opacity: [1, 0, 1] }}
            transition={{ repeat: Infinity, duration: 1.2 }}
            style={{ color: "#C9A84C", fontSize: 12, marginTop: 4 }}
          >
            {activeId ? "" : "█"}
          </motion.div>
        </div>
      </motion.div>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        style={{
          color: "#444",
          fontSize: 13,
          marginTop: 20,
          textAlign: "center",
          maxWidth: 280,
          lineHeight: 1.6,
        }}
      >
        Generando 6 imágenes con IA. Puede tardar 1–2 minutos.
      </motion.p>
    </div>
  )
}

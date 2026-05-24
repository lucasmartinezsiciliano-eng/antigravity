/**
 * CutCard — animated haircut result card.
 * Inspired by cult/ui expandable-card + shift-card.
 * Stacks frontal + lateral images with a smooth entrance animation.
 * Tap any photo to open in fullscreen lightbox.
 */

"use client"

import { motion } from "framer-motion"

interface AngleData {
  url: string
  label: string
}

interface CutCardProps {
  cutName: string
  cutIndex: number
  frontal?: AngleData
  lateral?: AngleData
  onPhotoTap: (url: string, label: string, cutName: string) => void
}

export function CutCard({ cutName, cutIndex, frontal, lateral, onPhotoTap }: CutCardProps) {
  if (!frontal?.url && !lateral?.url) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 28,
        delay: cutIndex * 0.12,
      }}
      style={{ marginBottom: 20 }}
    >
      <div
        style={{
          borderRadius: 18,
          overflow: "hidden",
          border: "1px solid #1E1E1E",
          background: "#101010",
          position: "relative",
        }}
      >
        {/* Frontal */}
        {frontal?.url && (
          <motion.button
            type="button"
            whileTap={{ scale: 0.98 }}
            onClick={() => onPhotoTap(frontal.url, "Frontal", cutName)}
            style={{
              display: "block",
              width: "100%",
              padding: 0,
              borderBottom: "1px solid #1E1E1E",
              position: "relative",
              overflow: "hidden",
            }}
            aria-label={`${cutName} frontal — toca para ampliar`}
          >
            <img
              src={frontal.url}
              alt={`${cutName} frontal`}
              style={{
                width: "100%",
                display: "block",
                aspectRatio: "4/5",
                objectFit: "cover",
              }}
              loading={cutIndex === 0 ? "eager" : "lazy"}
            />
            {/* Angle label */}
            <div style={{
              position: "absolute",
              bottom: 10,
              left: 10,
              background: "rgba(0,0,0,0.6)",
              backdropFilter: "blur(6px)",
              borderRadius: 8,
              padding: "3px 8px",
              fontSize: 11,
              color: "rgba(232,232,232,0.7)",
              fontWeight: 600,
              letterSpacing: "0.05em",
            }}>
              FRONTAL
            </div>
            {/* Tap hint */}
            <div style={{
              position: "absolute",
              bottom: 10,
              right: 10,
              background: "rgba(0,0,0,0.5)",
              borderRadius: 8,
              padding: "3px 8px",
              fontSize: 10,
              color: "rgba(232,232,232,0.4)",
            }}>
              ⤢
            </div>
          </motion.button>
        )}

        {/* Lateral */}
        {lateral?.url && (
          <motion.button
            type="button"
            whileTap={{ scale: 0.98 }}
            onClick={() => onPhotoTap(lateral.url, "Lateral", cutName)}
            style={{
              display: "block",
              width: "100%",
              padding: 0,
              position: "relative",
              overflow: "hidden",
            }}
            aria-label={`${cutName} lateral — toca para ampliar`}
          >
            <img
              src={lateral.url}
              alt={`${cutName} lateral`}
              style={{
                width: "100%",
                display: "block",
                aspectRatio: "4/5",
                objectFit: "cover",
              }}
              loading="lazy"
            />
            <div style={{
              position: "absolute",
              bottom: 10,
              left: 10,
              background: "rgba(0,0,0,0.6)",
              backdropFilter: "blur(6px)",
              borderRadius: 8,
              padding: "3px 8px",
              fontSize: 11,
              color: "rgba(232,232,232,0.7)",
              fontWeight: 600,
              letterSpacing: "0.05em",
            }}>
              LATERAL
            </div>
            <div style={{
              position: "absolute",
              bottom: 10,
              right: 10,
              background: "rgba(0,0,0,0.5)",
              borderRadius: 8,
              padding: "3px 8px",
              fontSize: 10,
              color: "rgba(232,232,232,0.4)",
            }}>
              ⤢
            </div>
          </motion.button>
        )}

        {/* Cut name footer with gold accent */}
        <div style={{
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: "#E8E8E8" }}>{cutName}</span>
          <span style={{
            fontSize: 11,
            fontWeight: 600,
            color: "#C9A84C",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}>
            #{cutIndex + 1}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

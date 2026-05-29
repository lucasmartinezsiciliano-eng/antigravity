"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { storage } from "@/lib/storage";
import Reveal from "@/components/Reveal";

function ResultPreview() {
  return (
    <div style={{ marginTop: 48, marginBottom: 48 }}>
      <div style={{
        border: "1px solid var(--border)",
        borderRadius: "var(--r-md)",
        overflow: "hidden",
        background: "var(--surface)",
      }}>
        {/* Header */}
        <div style={{
          padding: "10px 16px",
          background: "var(--surface2)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <span style={{ fontSize: 9, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-dim)", fontWeight: 700 }}>
            Análisis completado
          </span>
          <span style={{ fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.08em", fontWeight: 600 }}>VISAI</span>
        </div>

        {/* Face shape */}
        <div style={{ padding: "20px 16px 16px", borderBottom: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 8 }}>
            Forma craneal
          </div>
          <div style={{
            fontFamily: "var(--font-logo), serif",
            fontSize: 32,
            fontWeight: 400,
            letterSpacing: "-0.02em",
            color: "var(--text)",
            lineHeight: 1,
            marginBottom: 6,
          }}>
            Ovalado
          </div>
          <div style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.01em" }}>
            468 puntos · proporción áurea 0.92 · asimetría baja
          </div>
        </div>

        {/* Cuts */}
        <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column" }}>
          {[
            { n: "01", name: "Textured Crop", sub: "Cuerpo y textura" },
            { n: "02", name: "Taper Fade",    sub: "Degradado lateral" },
            { n: "03", name: "French Crop",   sub: "Flequillo recto" },
          ].map(({ n, name, sub }, i) => (
            <div key={n} style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "10px 0",
              borderBottom: i < 2 ? "1px solid var(--border-subtle)" : "none",
              opacity: i === 0 ? 1 : 0.6,
            }}>
              <span style={{ fontSize: 9, color: "var(--text-dim)", fontWeight: 700, letterSpacing: "0.06em", minWidth: 18 }}>{n}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", lineHeight: 1.3 }}>{name}</div>
                <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 1 }}>{sub}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <div style={{
          padding: "10px 16px",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "var(--surface2)",
        }}>
          <div style={{ width: 4, height: 4, borderRadius: "50%", background: "var(--text-dim)", flexShrink: 0 }} />
          <span style={{ fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.01em" }}>Instrucciones exactas para el barbero</span>
          <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-dim)" }}>→</span>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [existingId, setExistingId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const id = storage.getAnalysisId();
    if (id) setExistingId(id);
    const params = new URLSearchParams(window.location.search);
    const ref = params.get("ref");
    if (ref && /^VISAI-[A-Z0-9]{4,12}$/i.test(ref.trim())) {
      storage.saveBarberCode(ref.trim().toUpperCase());
    }
    if (params.get("reset_cookies") === "1") {
      localStorage.removeItem("visai_cookie_consent");
    }
  }, []);

  return (
    <div className="screen" style={{ paddingTop: 0, paddingBottom: 48, gap: 0 }}>

      {/* ── Logo ── */}
      <div style={{ paddingTop: 32, paddingBottom: 44 }}>
        <span style={{
          fontFamily: "var(--font-logo), serif",
          fontSize: 22,
          fontWeight: 400,
          letterSpacing: "0.06em",
          color: "var(--text)",
          lineHeight: 1,
        }}>
          VISAI
        </span>
      </div>

      {/* ── Hero ── */}
      <div
        className={mounted ? "hero-animate" : ""}
        style={{ marginBottom: 28 }}
      >
        <h1 style={{
          fontFamily: "var(--font-logo), serif",
          fontSize: "clamp(52px, 13vw, 80px)",
          fontWeight: 400,
          lineHeight: 1.02,
          letterSpacing: "-0.02em",
          color: "var(--text)",
          margin: "0 0 20px",
          textWrap: "balance",
        } as React.CSSProperties}>
          Descubre tu corte ideal.
        </h1>
        <p style={{
          margin: 0,
          fontSize: 15,
          color: "var(--text-muted)",
          lineHeight: 1.6,
          maxWidth: 320,
        }}>
          Tu morfología craneal analizada en 2 minutos. Tres cortes exactos para tu cara.
        </p>
      </div>

      {/* ── CTA ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
        {existingId && (
          <Link href={`/result/${existingId}`} className="btn-secondary" style={{ textDecoration: "none" }}>
            Continuar análisis anterior
          </Link>
        )}
        <button
          className="btn-primary"
          onClick={() => router.push("/quiz")}
        >
          Empezar análisis
        </button>
      </div>

      {/* ── Trust ── */}
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {["2 min", "Sin cuenta", "Foto eliminada"].map(chip => (
          <span key={chip} style={{ fontSize: 11, color: "var(--text-dim)" }}>· {chip}</span>
        ))}
      </div>

      {/* ── Product preview ── */}
      <Reveal>
        <ResultPreview />
      </Reveal>

      {/* ── What you get ── */}
      <div style={{ marginBottom: 56 }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {[
            ["Visagismo profesional", "468 puntos · 6 formas · 3 tipos craneales analizados"],
            ["3 cortes personalizados", "Con instrucciones exactas para el barbero"],
            ["16.99 € frente a los 50-80 € del visagista presencial", "En 2 minutos desde tu móvil"],
          ].map(([title, desc], i) => (
            <Reveal key={title} delay={i * 80}>
              <div style={{
                padding: "16px 0",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", lineHeight: 1.4 }}>{title}</div>
                <div style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.5 }}>{desc}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>

      {/* ── How it works (editorial index) ── */}
      <div style={{ marginBottom: 56 }}>
        <Reveal>
          <div style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "var(--text-dim)",
            marginBottom: 28,
          }}>
            Cómo funciona
          </div>
        </Reveal>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {[
            ["Fotos", "3 fotos desde el móvil. Frontal, lateral, perfil."],
            ["Análisis", "Morfología craneal y proporciones medidas con 468 puntos."],
            ["Cortes", "3 recomendaciones exactas, con instrucciones para tu barbero."],
          ].map(([title, desc], i) => (
            <Reveal key={title} delay={i * 90}>
              <div style={{
                display: "grid",
                gridTemplateColumns: "auto 1fr",
                columnGap: 20,
                alignItems: "baseline",
                padding: "22px 0",
                borderTop: "1px solid var(--border)",
                borderBottom: i === 2 ? "1px solid var(--border)" : "none",
              }}>
                <span style={{
                  fontFamily: "var(--font-logo), serif",
                  fontSize: 15,
                  color: "var(--text-dim)",
                  fontVariantNumeric: "tabular-nums",
                  lineHeight: 1,
                }}>
                  0{i + 1}
                </span>
                <div>
                  <div style={{
                    fontFamily: "var(--font-logo), serif",
                    fontSize: "clamp(26px, 7vw, 34px)",
                    fontWeight: 400,
                    letterSpacing: "-0.02em",
                    color: "var(--text)",
                    lineHeight: 1,
                    marginBottom: 8,
                  }}>
                    {title}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.55, maxWidth: 320 }}>{desc}</div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>

      {/* ── Final CTA ── */}
      <Reveal>
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: "auto" }}>
          <button className="btn-primary" onClick={() => router.push("/quiz")}>
            Descubrir mis cortes ideales
          </button>
          <p className="caption" style={{ textAlign: "center", marginTop: 4 }}>
            Sin cuenta · Foto eliminada al instante · RGPD
          </p>
        </div>
      </Reveal>

    </div>
  );
}

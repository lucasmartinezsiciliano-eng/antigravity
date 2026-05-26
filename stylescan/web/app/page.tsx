"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { storage } from "@/lib/storage";

function ResultPreview() {
  return (
    <div style={{
      marginTop: 32,
      border: "1px solid #1C1C1C",
      borderRadius: 14,
      overflow: "hidden",
      background: "#050505",
    }}>
      {/* Bar superior */}
      <div style={{
        padding: "9px 14px",
        background: "#0A0A0A",
        borderBottom: "1px solid #141414",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <span style={{ fontSize: 9, letterSpacing: "0.12em", textTransform: "uppercase", color: "#444", fontWeight: 700 }}>
          ANÁLISIS COMPLETADO
        </span>
        <span style={{ fontSize: 9, color: "#2A2A2A", letterSpacing: "0.06em" }}>VISAI</span>
      </div>

      {/* Forma craneal */}
      <div style={{ padding: "16px 14px 14px", borderBottom: "1px solid #111" }}>
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#444", marginBottom: 6 }}>
          FORMA CRANEAL
        </div>
        <div className="display" style={{ fontSize: 28, fontWeight: 700, color: "#F0F0F0", marginBottom: 3 }}>
          Ovalado
        </div>
        <div style={{ fontSize: 11, color: "#3A3A3A" }}>
          468 puntos · proporción áurea 0.92 · asimetría baja
        </div>
      </div>

      {/* 3 Cortes */}
      <div style={{ padding: "12px 14px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 7 }}>
        {[
          { n: "01", name: "Textured Crop", sub: "Cuerpo y textura" },
          { n: "02", name: "Taper Fade",    sub: "Degradado lateral" },
          { n: "03", name: "French Crop",   sub: "Flequillo recto" },
        ].map(({ n, name, sub }, i) => (
          <div key={n} style={{
            background: i === 0 ? "#0F0F0F" : "transparent",
            border: `1px solid ${i === 0 ? "#242424" : "#141414"}`,
            borderRadius: 10,
            padding: "10px 9px",
          }}>
            <div style={{ fontSize: 9, color: "#333", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 5 }}>{n}</div>
            <div style={{ fontSize: 11, fontWeight: 700, lineHeight: 1.3, color: "#D0D0D0" }}>{name}</div>
            <div style={{ fontSize: 10, color: "#3A3A3A", marginTop: 3, lineHeight: 1.3 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Barber instructions hint */}
      <div style={{
        padding: "9px 14px",
        borderTop: "1px solid #0E0E0E",
        display: "flex",
        alignItems: "center",
        gap: 8,
        background: "#040404",
      }}>
        <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#2A2A2A", flexShrink: 0 }} />
        <span style={{ fontSize: 10, color: "#363636" }}>Instrucciones exactas para tu barbero</span>
        <span style={{ marginLeft: "auto", fontSize: 10, color: "#242424" }}>→</span>
      </div>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [existingId, setExistingId] = useState<string | null>(null);

  useEffect(() => {
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
    <div className="screen" style={{ paddingTop: 0, paddingBottom: 44, gap: 0 }}>

      {/* ── Logo ── */}
      <div style={{ paddingTop: 28, paddingBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 400, letterSpacing: "0.04em", lineHeight: 1, fontFamily: "var(--font-logo), serif" }}>
          VISAI
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 10, margin: "5px 0 0", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Visagismo profesional con IA
        </p>
      </div>

      {/* ── Headline principal ── */}
      <div style={{ marginBottom: 18 }}>
        <h2 className="display" style={{
          margin: "0 0 12px",
          fontSize: 38,
          fontWeight: 700,
          color: "#F0F0F0",
        }}>
          Descubre tu<br />corte ideal.
        </h2>
        <p style={{
          margin: 0,
          fontSize: 15,
          color: "#666",
          lineHeight: 1.55,
          maxWidth: 300,
        }}>
          Visagismo con IA: analiza tu morfología craneal y genera 3 cortes exactos para tu cara.
        </p>
      </div>

      {/* ── CTA principal ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 12 }}>
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

      {/* ── Trust chips ── */}
      <div style={{
        display: "flex",
        gap: 16,
        flexWrap: "wrap",
        marginBottom: 8,
      }}>
        {["2 min", "Sin cuenta", "Foto eliminada"].map(chip => (
          <span key={chip} style={{
            fontSize: 11,
            color: "#3A3A3A",
            letterSpacing: "0.02em",
          }}>
            · {chip}
          </span>
        ))}
      </div>

      {/* ── Product preview ── */}
      <ResultPreview />

      {/* ── Stats ── */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        borderTop: "1px solid var(--border)",
        borderBottom: "1px solid var(--border)",
        margin: "32px 0 28px",
        padding: "16px 0",
      }}>
        {[
          ["468", "PUNTOS"],
          ["6", "FORMAS"],
          ["3", "CRANEALES"],
        ].map(([n, label]) => (
          <div key={label} style={{ textAlign: "center" }}>
            <div className="display" style={{ fontSize: 26, fontWeight: 700, color: "#F0F0F0", lineHeight: 1 }}>{n}</div>
            <div style={{ fontSize: 9, color: "#333", marginTop: 5, letterSpacing: "0.1em" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* ── Qué obtienes ── */}
      <div style={{ marginBottom: 28 }}>
        <p className="label" style={{ marginBottom: 14 }}>Qué obtienes</p>
        <div style={{ display: "flex", flexDirection: "column" }}>
          {[
            ["Visagismo profesional", "Análisis craneal: 468 puntos · 6 formas · 3 tipos craneales"],
            ["3 cortes personalizados", "Con instrucciones exactas para el barbero"],
            ["Visagista profesional: 50-80 €", "VISAI lo hace por 16,99 € en 2 minutos"],
          ].map(([title, desc]) => (
            <div key={title} style={{
              display: "flex",
              flexDirection: "column",
              padding: "13px 0",
              borderBottom: "1px solid var(--border)",
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 3, color: "#E0E0E0" }}>{title}</div>
              <div style={{ fontSize: 12, color: "#3A3A3A" }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Proceso ── */}
      <div style={{ marginBottom: 28 }}>
        <p className="label" style={{ marginBottom: 14 }}>Cómo funciona</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
          {[
            ["01", "Fotos", "3 fotos desde el móvil"],
            ["02", "Análisis", "Morfología y proporciones"],
            ["03", "Cortes", "3 recomendaciones exactas"],
          ].map(([n, title, desc]) => (
            <div key={n} style={{
              padding: "14px 10px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--r-md)",
            }}>
              <div className="display" style={{ fontSize: 18, fontWeight: 700, color: "#2A2A2A", marginBottom: 6 }}>{n}</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2, color: "#C0C0C0" }}>{title}</div>
              <div style={{ fontSize: 10, color: "#3A3A3A", lineHeight: 1.4 }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA final ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: "auto" }}>
        <button className="btn-primary" onClick={() => router.push("/quiz")}>
          Descubrir mis cortes ideales
        </button>
        <p className="caption" style={{ textAlign: "center", marginTop: 2 }}>
          Sin cuenta · Foto eliminada al instante · RGPD
        </p>
      </div>

    </div>
  );
}

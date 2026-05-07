"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ScanFace, Scissors, Sparkles } from "lucide-react";
import { storage } from "@/lib/storage";

const FEATURES = [
  {
    Icon: ScanFace,
    title: "Análisis facial real",
    desc: "468 puntos de referencia. Forma, proporciones y asimetría.",
  },
  {
    Icon: Scissors,
    title: "3 cortes personalizados",
    desc: "Instrucciones exactas para pedir en tu barbería.",
  },
  {
    Icon: Sparkles,
    title: "Prueba virtual",
    desc: "Mira cómo quedas antes de cortarte.",
  },
];


export default function Home() {
  const [existingId, setExistingId] = useState<string | null>(null);

  useEffect(() => {
    const id = storage.getAnalysisId();
    if (id) setExistingId(id);
    const params = new URLSearchParams(window.location.search);
    const ref = params.get("ref");
    if (ref) storage.saveBarberCode(ref.toUpperCase());
    if (params.get("reset_cookies") === "1") {
      localStorage.removeItem("visai_cookie_consent");
    }
  }, []);

  return (
    <div className="screen" style={{ paddingTop: 0, paddingBottom: 44, gap: 32 }}>

      {/* ── Hero — VISAI wordmark (Syne 800 + scan line) ── */}
      <div style={{ textAlign: "center", paddingTop: 16 }}>
        <h1 style={{ margin: "0 0 10px", lineHeight: 1 }}>
          <svg viewBox="0 0 300 80" width="220" height="59" xmlns="http://www.w3.org/2000/svg" aria-label="VISAI" style={{ display: "block", margin: "0 auto" }}>
            <text x="150" y="62" textAnchor="middle"
              style={{ fontFamily: "var(--font-logo), 'Syne', sans-serif" }}
              fontWeight="800" fontSize="58" letterSpacing="6"
              fill="var(--text)">VISAI</text>
            <line x1="4" y1="33" x2="296" y2="33" stroke="var(--text)" strokeWidth="0.7" opacity="0.3" />
            <circle cx="4" cy="33" r="1.5" fill="var(--text)" opacity="0.45" />
            <circle cx="296" cy="33" r="1.5" fill="var(--text)" opacity="0.45" />
          </svg>
        </h1>

        <p style={{ color: "var(--text-muted)", fontWeight: 500, fontSize: 13, margin: 0, letterSpacing: 0.4 }}>
          Visagismo profesional con IA
        </p>
      </div>

      {/* ── Features ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {FEATURES.map(({ Icon, title, desc }) => (
          <div key={title} className="card" style={{ display: "flex", gap: 16, alignItems: "center", padding: "16px 18px" }}>
            <div style={{
              width: 42, height: 42, borderRadius: 12, flexShrink: 0,
              background: "var(--accent-subtle)",
              border: "1px solid rgba(201,168,76,0.15)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Icon size={20} color="var(--accent)" strokeWidth={1.75} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 2 }}>{title}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.45 }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── CTA — pinned to bottom ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: "auto" }}>
        {existingId && (
          <Link href={`/result/${existingId}`} className="btn-secondary" style={{ textDecoration: "none" }}>
            Continuar análisis anterior →
          </Link>
        )}
        <Link href="/quiz" className="btn-primary" style={{ textDecoration: "none" }}>
          Empezar análisis
        </Link>
        <p className="caption" style={{ textAlign: "center", marginTop: 4 }}>
          Pago único · Sin suscripción · Foto eliminada al instante
        </p>
      </div>

    </div>
  );
}

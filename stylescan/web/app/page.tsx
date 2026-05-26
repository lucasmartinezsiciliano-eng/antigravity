"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { storage } from "@/lib/storage";
import { GlowButton } from "@/components/ui/glow-button";

/* ─── Neomarketing principles applied ────────────────────────────────────────
  1. ANCHORING       — Precio referencia visagista (€50–80) vs €12,99
  2. LOSS AVERSION   — Hook con el dolor real antes del beneficio
  3. SOCIAL PROOF    — Specificity: "468 puntos · 6 formas · 3 tipos"
  4. COGNITIVE EASE  — Flujo visual antes de CTA (reduce ansiedad)
  5. MICRO-COMMIT    — Quiz como primer paso
  6. AUTHORITY       — Terminología técnica: visagismo, análisis cefálico
  7. CTA 1ª persona  — "Ver mis cortes" > "Empezar análisis"
  8. RECIPROCITY     — Mostrar el valor antes de pedir dinero
─────────────────────────────────────────────────────────────────────────────*/

function LogoMark({ size = 72 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <ellipse cx="40" cy="36" rx="18" ry="23" fill="none" stroke="var(--text)" strokeWidth="1" opacity="0.15" />
      <line x1="12" y1="36" x2="68" y2="36" stroke="var(--gold)" strokeWidth="0.8" opacity="0.5" />
      <circle cx="12" cy="36" r="1.8" fill="var(--gold)" opacity="0.55" />
      <circle cx="68" cy="36" r="1.8" fill="var(--gold)" opacity="0.55" />
      <circle cx="31" cy="27" r="2.5" fill="var(--gold)" />
      <circle cx="49" cy="27" r="2.5" fill="var(--gold)" />
      <circle cx="40" cy="39" r="1.8" fill="var(--gold)" opacity="0.8" />
      <circle cx="31" cy="50" r="1.6" fill="var(--gold)" opacity="0.45" />
      <circle cx="49" cy="50" r="1.6" fill="var(--gold)" opacity="0.45" />
      <circle cx="20" cy="35" r="1.2" fill="var(--gold)" opacity="0.4" />
      <circle cx="60" cy="35" r="1.2" fill="var(--gold)" opacity="0.4" />
      <line x1="31" y1="27" x2="40" y2="39" stroke="var(--gold)" strokeWidth="0.5" opacity="0.22" />
      <line x1="49" y1="27" x2="40" y2="39" stroke="var(--gold)" strokeWidth="0.5" opacity="0.22" />
      <path d="M17 14 L17 22 M17 14 L25 14" stroke="var(--gold)" strokeWidth="1" fill="none" opacity="0.45" />
      <path d="M63 14 L63 22 M63 14 L55 14" stroke="var(--gold)" strokeWidth="1" fill="none" opacity="0.45" />
      <path d="M17 62 L17 54 M17 62 L25 62" stroke="var(--gold)" strokeWidth="1" fill="none" opacity="0.45" />
      <path d="M63 62 L63 54 M63 62 L55 62" stroke="var(--gold)" strokeWidth="1" fill="none" opacity="0.45" />
    </svg>
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

      {/* ── Hero — editorial, not SaaS ── */}
      <div style={{ textAlign: "center", paddingTop: 28, paddingBottom: 28, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
        <LogoMark size={58} />

        <h1 className="display" style={{ margin: 0, fontSize: 42, fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1 }}>
          VISAI
        </h1>

        <p style={{ color: "var(--gold)", fontWeight: 500, fontSize: 10, margin: 0, letterSpacing: "0.22em", textTransform: "uppercase", opacity: 0.75 }}>
          Visagismo · IA · Barbería
        </p>
      </div>

      {/* ── HOOK — Loss aversion ── */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-md)",
        padding: "20px 18px",
        marginBottom: 18,
      }}>
        <p className="display" style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, letterSpacing: "-0.02em", lineHeight: 1.2 }}>
          ¿Cuántos cortes malos llevas pagando?
        </p>
        <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, fontWeight: 300 }}>
          VISAI analiza la <strong style={{ color: "var(--text)", fontWeight: 600 }}>forma exacta de tu cabeza</strong> y te dice qué cortes te favorecen de verdad — antes de sentarte en el sillón.
        </p>
      </div>

      {/* ── ANCHOR — Price reference ── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "14px 16px",
        background: "var(--gold-subtle)",
        border: "1px solid var(--gold-border)",
        borderRadius: "var(--r-md)",
        marginBottom: 18,
      }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: 12, color: "var(--text-muted)", lineHeight: 1.4, fontWeight: 300 }}>
            Consulta con visagista profesional:
            {" "}<span style={{ textDecoration: "line-through", color: "var(--text-dim)" }}>€50–80</span>
          </p>
          <p style={{ margin: "3px 0 0", fontSize: 13, fontWeight: 600, color: "var(--gold)" }}>
            VISAI: <span style={{ fontSize: 18, fontWeight: 700 }}>12,99 €</span> <span style={{ fontSize: 11, fontWeight: 400, color: "var(--text-muted)" }}>· en 2 min</span>
          </p>
        </div>
        <ChevronRight size={14} color="var(--gold)" opacity={0.4} />
      </div>

      {/* ── WHAT YOU GET — asymmetric, not 3-card grid ── */}
      <div style={{ marginBottom: 18 }}>
        <p className="label" style={{ marginBottom: 12 }}>Qué incluye</p>

        {/* Main feature — large */}
        <div className="card" style={{ padding: "18px", marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
            <span className="display" style={{ fontSize: 15, fontWeight: 700 }}>Análisis craneal completo</span>
            <span style={{ fontSize: 11, color: "var(--gold)", fontWeight: 600 }}>IA</span>
          </div>
          <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 12, lineHeight: 1.6, fontWeight: 300 }}>
            468 puntos de medición. Forma facial, volumen craneal, proporciones y asimetrías.
          </p>
        </div>

        {/* Two smaller features — side by side */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <div className="card" style={{ padding: "14px" }}>
            <span className="display" style={{ fontSize: 13, fontWeight: 700, display: "block", marginBottom: 4 }}>3 cortes exactos</span>
            <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 11, lineHeight: 1.5, fontWeight: 300 }}>
              Con instrucciones para el barbero.
            </p>
          </div>
          <div className="card" style={{ padding: "14px" }}>
            <span className="display" style={{ fontSize: 13, fontWeight: 700, display: "block", marginBottom: 4 }}>Prueba virtual</span>
            <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 11, lineHeight: 1.5, fontWeight: 300 }}>
              Vélo en tu cabeza antes de cortarte.
            </p>
          </div>
        </div>
      </div>

      {/* ── HOW IT WORKS — clean, no numbered circles ── */}
      <div style={{ marginBottom: 18 }}>
        <p className="label" style={{ marginBottom: 12 }}>Cómo funciona</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {[
            { step: "Fotos", desc: "Frontal y dos perfiles. Desde el móvil, en tu barbería." },
            { step: "Análisis", desc: "La IA mide tu cabeza: 6 formas faciales, 3 tipos craneales." },
            { step: "Resultado", desc: "Cortes, instrucciones para el barbero y prueba virtual." },
          ].map((s, i, arr) => (
            <div key={s.step} style={{
              display: "flex",
              gap: 14,
              alignItems: "flex-start",
              padding: "12px 0",
              borderBottom: i < arr.length - 1 ? "1px solid var(--border)" : "none",
            }}>
              <span className="display" style={{
                fontSize: 11, fontWeight: 800, color: "var(--gold)", opacity: 0.6,
                minWidth: 18, paddingTop: 2,
              }}>
                {String.fromCharCode(65 + i)}
              </span>
              <div>
                <span style={{ fontWeight: 600, fontSize: 13, display: "block", marginBottom: 2 }}>{s.step}</span>
                <span style={{ color: "var(--text-muted)", fontSize: 12, lineHeight: 1.5, fontWeight: 300 }}>{s.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── SPECIFICITY — static type, no animated counters ── */}
      <div style={{
        display: "flex",
        gap: 0,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-md)",
        padding: "16px 0",
        marginBottom: 24,
      }}>
        {[
          { n: "468", label: "puntos" },
          { n: "6", label: "formas" },
          { n: "3", label: "craneales" },
        ].map(({ n, label }, i, arr) => (
          <div key={label} style={{
            flex: 1,
            textAlign: "center",
            borderRight: i < arr.length - 1 ? "1px solid var(--border)" : "none",
          }}>
            <div className="display" style={{ fontSize: 24, fontWeight: 800, color: "var(--gold)", lineHeight: 1 }}>
              {n}
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4, fontWeight: 400, letterSpacing: "0.04em" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* ── CTA ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: "auto" }}>
        {existingId && (
          <Link href={`/result/${existingId}`} className="btn-secondary" style={{ textDecoration: "none" }}>
            Continuar mi análisis anterior →
          </Link>
        )}
        <GlowButton
          variant="gold"
          size="lg"
          fullWidth
          onClick={() => router.push("/quiz")}
        >
          Descubrir mis cortes ideales
        </GlowButton>
        <p className="caption" style={{ textAlign: "center", marginTop: 4 }}>
          Sin cuenta · Foto eliminada al instante · RGPD
        </p>
      </div>

    </div>
  );
}

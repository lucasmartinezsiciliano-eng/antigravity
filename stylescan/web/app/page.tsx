"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ScanFace, Scissors, Sparkles, ChevronRight } from "lucide-react";
import { storage } from "@/lib/storage";
import { GradientHeading } from "@/components/ui/gradient-heading";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { GlowButton } from "@/components/ui/glow-button";

/* ─── Neomarketing principles applied ────────────────────────────────────────
  1. ANCHORING       — Precio referencia visagista (€50–80) vs €9,99
  2. LOSS AVERSION   — Hook con el dolor real antes del beneficio
  3. SOCIAL PROOF    — Contador específico + ticker de barberías
  4. SPECIFICITY     — "468 puntos · 6 formas · 3 tipos craneales"
  5. COGNITIVE EASE  — Flujo 3 pasos antes de la CTA (reduce ansiedad)
  6. MICRO-COMMIT    — Quiz como primer paso (pequeño sí antes del pago)
  7. AUTHORITY       — Terminología técnica: visagismo, análisis cefálico
  8. CTA 1ª persona  — "Ver mis cortes" > "Empezar análisis"
  9. RECIPROCITY     — Mostrar el valor antes de pedir dinero
  10. SCARCITY       — "Solo en barberías colaboradoras"
─────────────────────────────────────────────────────────────────────────────*/

const STEPS = [
  { n: "01", label: "3 fotos rápidas", sub: "Frontal y dos perfiles. En la barbería, desde el móvil." },
  { n: "02", label: "IA analiza tu cabeza", sub: "468 puntos · 6 formas faciales · 3 tipos craneales." },
  { n: "03", label: "Tu informe exacto", sub: "Cortes, instrucciones para el barbero y prueba virtual." },
];

const FEATURES = [
  {
    Icon: ScanFace,
    title: "Análisis de forma craneal",
    desc: "Analiza la FORMA de tu cabeza, no solo la cara. 6 tipos faciales · 3 tipos craneales.",
  },
  {
    Icon: Scissors,
    title: "Cortes que sí te van",
    desc: "Con instrucciones exactas para decirle al barbero. Sin dudas en el sillón.",
  },
  {
    Icon: Sparkles,
    title: "Vélo antes de pagarlo",
    desc: "Prueba virtual IA. Mira cómo queda el corte en tu cabeza antes de cortarte.",
  },
];

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
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const id = storage.getAnalysisId();
    if (id) setExistingId(id);
    const params = new URLSearchParams(window.location.search);
    const ref = params.get("ref");
    // Validate format before saving — rejects garbage/spam values (e.g. tracking IDs, injected values)
    if (ref && /^VISAI-[A-Z0-9]{4,12}$/i.test(ref.trim())) {
      storage.saveBarberCode(ref.trim().toUpperCase());
    }
    if (params.get("reset_cookies") === "1") {
      localStorage.removeItem("visai_cookie_consent");
    }
    // Trigger stats animation shortly after mount
    const t = setTimeout(() => setStatsVisible(true), 600);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="screen" style={{ paddingTop: 0, paddingBottom: 44, gap: 0 }}>

      {/* ── Hero ── */}
      <div style={{ textAlign: "center", paddingTop: 24, paddingBottom: 24, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
        <LogoMark size={64} />

        <h1 style={{ margin: 0, lineHeight: 1 }}>
          <svg viewBox="0 0 300 52" width="190" height="33" xmlns="http://www.w3.org/2000/svg" aria-label="VISAI" style={{ display: "block", margin: "0 auto" }}>
            <text x="150" y="42" textAnchor="middle"
              style={{ fontFamily: "var(--font-logo), 'Syne', sans-serif" }}
              fontWeight="800" fontSize="46" letterSpacing="8"
              fill="var(--text)">VISAI</text>
          </svg>
        </h1>

        <p style={{ color: "var(--gold)", fontWeight: 600, fontSize: 10, margin: 0, letterSpacing: "0.18em", textTransform: "uppercase", opacity: 0.85 }}>
          Visagismo · IA · Barbería
        </p>
      </div>

      {/* ── HOOK — Loss aversion: el dolor primero ── */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-md)",
        padding: "18px 18px",
        marginBottom: 16,
      }}>
        <GradientHeading variant="white" size="sm" weight="bold" as="p" style={{ marginBottom: 6 }}>
          ¿Cuántos cortes malos llevas pagando?
        </GradientHeading>
        <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)", lineHeight: 1.55 }}>
          VISAI analiza la <strong style={{ color: "var(--text)" }}>forma exacta de tu cabeza</strong> y te dice qué cortes te favorecen de verdad — antes de sentarte en el sillón.
        </p>
      </div>

      {/* ── ANCHOR — Price reference ── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "12px 16px",
        background: "var(--gold-subtle)",
        border: "1px solid var(--gold-border)",
        borderRadius: "var(--r-md)",
        marginBottom: 16,
      }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: 12, color: "var(--text-muted)", lineHeight: 1.4 }}>
            Una consulta con visagista profesional:
            {" "}<span style={{ textDecoration: "line-through", color: "var(--text-dim)" }}>€50–80</span>
          </p>
          <p style={{ margin: "2px 0 0", fontSize: 13, fontWeight: 700, color: "var(--gold)" }}>
            VISAI: <span style={{ fontSize: 17 }}>12,99 €</span> · Resultado en menos de 2 min
          </p>
        </div>
        <ChevronRight size={16} color="var(--gold)" opacity={0.6} />
      </div>

      {/* ── FEATURES — Benefit framing ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
        {FEATURES.map(({ Icon, title, desc }) => (
          <div key={title} className="card" style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "14px 16px" }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10, flexShrink: 0, marginTop: 1,
              background: "var(--gold-subtle)", border: "1px solid var(--gold-border)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Icon size={17} color="var(--gold)" strokeWidth={1.75} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 2 }}>{title}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, lineHeight: 1.5 }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── PROCESS — Cognitive ease: 3 pasos ── */}
      <div style={{ marginBottom: 16 }}>
        <p className="label" style={{ marginBottom: 12 }}>Cómo funciona</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {STEPS.map((step, i) => (
            <div key={step.n} style={{ display: "flex", gap: 14, alignItems: "flex-start", paddingBottom: i < STEPS.length - 1 ? 14 : 0 }}>
              <div style={{
                display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%",
                  background: "var(--gold-subtle)", border: "1px solid var(--gold-border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 800, color: "var(--gold)", letterSpacing: "0.05em",
                }}>
                  {step.n}
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{ width: 1, flex: 1, minHeight: 16, background: "var(--border)", marginTop: 4 }} />
                )}
              </div>
              <div style={{ paddingBottom: i < STEPS.length - 1 ? 6 : 0 }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>{step.label}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, lineHeight: 1.45 }}>{step.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── SOCIAL PROOF — Specificity + AnimatedNumber ── */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)", borderRadius: "var(--r-md)",
        padding: "14px 16px",
        marginBottom: 20,
      }}>
        {/* Stats row */}
        <div style={{ display: "flex", gap: 0, marginBottom: 12, borderBottom: "1px solid var(--border)", paddingBottom: 12 }}>
          {[
            { value: 468, label: "puntos de análisis", suffix: "" },
            { value: 6,   label: "formas faciales",    suffix: "" },
            { value: 3,   label: "tipos craneales",    suffix: "" },
          ].map(({ value, label, suffix }) => (
            <div key={label} style={{ flex: 1, textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: "var(--gold)", fontVariantNumeric: "tabular-nums" }}>
                {statsVisible ? <AnimatedNumber value={value} stiffness={60} damping={18} /> : "0"}{suffix}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2, lineHeight: 1.3 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA — 1ª persona + micro-commit ── */}
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

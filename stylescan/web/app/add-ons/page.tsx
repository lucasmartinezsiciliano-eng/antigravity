"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, Star, X } from "lucide-react";
import { storage } from "@/lib/storage";
import { api } from "@/lib/api";

type Selection = "none" | "pack" | "colorimetry" | "products";

const OPTIONS: { id: Selection; emoji: string; title: string; sub: string; price: string; badge?: string }[] = [
  {
    id: "pack",
    emoji: "⭐",
    title: "Pack Completo",
    sub: "Colorimetría personal + Guía de productos",
    price: "+10,00 €",
    badge: "MEJOR VALOR",
  },
  {
    id: "colorimetry",
    emoji: "🎨",
    title: "Colorimetría personal",
    sub: "Paleta de ropa, tonos de piel, monturas de gafas",
    price: "+2,49 €",
  },
  {
    id: "products",
    emoji: "🧴",
    title: "Guía de productos",
    sub: "Productos exactos, rutina diaria y técnica de peinado",
    price: "+1,99 €",
  },
];

const TOTAL: Record<Selection, string> = {
  none: "14,99 €",
  pack: "24,99 €",
  colorimetry: "17,48 €",
  products: "16,98 €",
};

export default function AddOnsPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<Selection>("none");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [barberCode, setBarberCode] = useState<string | null>(null);

  useEffect(() => {
    setBarberCode(storage.getBarberCode());
  }, []);

  function removeBarberCode() {
    storage.clearBarberCode();
    setBarberCode(null);
  }

  async function doInitiate(code: string | undefined) {
    const quiz = storage.getQuiz();
    const consent = storage.getConsentState();
    const res = await api.initiate({
      barber_code: code,
      quiz_answers: quiz,
      marketing_consent: consent["marketing_emails"] === true,
      include_colorimetry: selected === "pack" || selected === "colorimetry",
      include_products_guide: selected === "pack" || selected === "products",
    });
    storage.saveAnalysisId(res.analysis_id);
    storage.saveCheckoutUrl(res.checkout_url);
    if (res.checkout_url.startsWith("https://checkout.stripe.com")) {
      window.location.href = res.checkout_url;
    } else {
      window.location.href = `/pending?id=${res.analysis_id}`;
    }
  }

  async function handleContinue() {
    setLoading(true);
    setError("");
    try {
      await doInitiate(barberCode ?? undefined);
    } catch (e: any) {
      const msg: string = e.message || "Error al iniciar. Inténtalo de nuevo.";
      if (msg.toLowerCase().includes("barber") || msg.toLowerCase().includes("barbería") || msg.toLowerCase().includes("código")) {
        // Stale barber code in storage — clear it and retry automatically
        storage.clearBarberCode();
        setBarberCode(null);
        try {
          await doInitiate(undefined);
          return;
        } catch (e2: any) {
          setError(e2.message || "Error al iniciar. Inténtalo de nuevo.");
        }
      } else {
        // Network errors ("Load failed", "Failed to fetch") in dev: show retry + bypass
        const isNetworkErr = msg === "Load failed" || msg.toLowerCase().includes("failed to fetch") || msg.toLowerCase().includes("network");
        setError(isNetworkErr
          ? `No se puede conectar al servidor (${msg}). ¿Está el backend corriendo?`
          : msg
        );
      }
      setLoading(false);
    }
  }

  function devBypass() {
    const devId = `dev-${Date.now()}`;
    storage.saveAnalysisId(devId);
    window.location.href = `/capture/${devId}`;
  }

  return (
    <div className="screen" style={{ paddingTop: 32, paddingBottom: 40, justifyContent: "space-between" }}>
      <div>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontSize: 12, letterSpacing: 0.8, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8 }}>
            COMPLETA TU ANÁLISIS
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: -0.5, margin: "0 0 8px" }}>
            ¿Añades algo más?
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0, lineHeight: 1.5 }}>
            El análisis base ya incluye tus 3 cortes ideales y la prueba virtual.
          </p>
        </div>

        {/* Base included */}
        <div style={{
          display: "flex", alignItems: "center", gap: 12, padding: "14px 16px",
          borderRadius: 12, border: "1.5px solid var(--accent)",
          background: "var(--accent-subtle)", marginBottom: 12,
        }}>
          <Check size={16} color="var(--accent)" strokeWidth={2.5} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>Análisis base — incluido</div>
            <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2 }}>
              Forma facial · 3 cortes · Prueba virtual IA
            </div>
          </div>
          <div style={{ fontWeight: 800, fontSize: 15, color: "var(--accent)", flexShrink: 0 }}>14,99 €</div>
        </div>

        {/* Options */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
          {OPTIONS.map((opt) => {
            const isSelected = selected === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => setSelected(isSelected ? "none" : opt.id)}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "14px 16px",
                  borderRadius: 12, textAlign: "left", width: "100%",
                  border: `1.5px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                  background: isSelected ? "var(--accent-subtle)" : "var(--surface)",
                  transition: "border-color 0.15s, background 0.15s",
                  position: "relative",
                }}
              >
                {opt.badge && (
                  <span style={{
                    position: "absolute", top: -9, right: 12,
                    fontSize: 9, fontWeight: 800, letterSpacing: 1,
                    padding: "3px 8px", borderRadius: 99,
                    background: "var(--accent)", color: "#080808",
                  }}>
                    {opt.badge}
                  </span>
                )}
                <div style={{
                  width: 20, height: 20, borderRadius: 6, flexShrink: 0,
                  border: `1.5px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                  background: isSelected ? "var(--accent)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "border-color 0.15s, background 0.15s",
                }}>
                  {isSelected && (
                    <svg width="9" height="7" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="#080808" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{opt.emoji}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{opt.title}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2 }}>{opt.sub}</div>
                </div>
                <div style={{
                  fontWeight: 700, fontSize: 14, flexShrink: 0, marginLeft: 8,
                  color: isSelected ? "var(--accent)" : "var(--text-muted)",
                }}>
                  {opt.price}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom CTA */}
      <div>
        {/* Total */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "14px 16px", borderRadius: 12,
          background: "var(--surface)", border: "1px solid var(--border)",
          marginBottom: 14,
        }}>
          <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text-muted)" }}>Total</span>
          <span style={{ fontWeight: 900, fontSize: 20 }}>{TOTAL[selected]}</span>
        </div>

        {barberCode && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "10px 14px", borderRadius: 10, marginBottom: 10,
            background: "var(--accent-subtle)", border: "1px solid rgba(201,168,76,0.25)",
          }}>
            <span style={{ fontSize: 13, color: "var(--accent)", fontWeight: 600 }}>
              Código barbería: {barberCode}
            </span>
            <button type="button" onClick={removeBarberCode} aria-label="Eliminar código" style={{ background: "none", border: "none", cursor: "pointer", padding: 2, display: "flex" }}>
              <X size={14} color="var(--text-muted)" />
            </button>
          </div>
        )}

        {error && (
          <div>
            <p style={{ color: "var(--danger)", fontSize: 13, textAlign: "center", marginBottom: 8 }}>{error}</p>
            {(error.includes("conectar") || error.includes("Load failed") || error.includes("fetch")) && (
              <button
                type="button"
                onClick={devBypass}
                style={{
                  width: "100%", padding: "12px", borderRadius: 12, marginBottom: 8,
                  background: "var(--surface2)", border: "1px dashed var(--border)",
                  color: "var(--text-muted)", fontSize: 13, fontWeight: 600,
                }}
              >
                🛠 Continuar en modo dev (sin backend) →
              </button>
            )}
          </div>
        )}

        <button
          type="button"
          className="btn-primary"
          onClick={handleContinue}
          disabled={loading}
        >
          {loading ? "Iniciando…" : selected === "none" ? "Solo el análisis — Pagar →" : `Añadir ${OPTIONS.find(o => o.id === selected)?.title} — Pagar →`}
        </button>

        <p className="caption" style={{ textAlign: "center", marginTop: 10 }}>
          Pago único · Sin suscripción · Stripe SSL 256-bit
        </p>
      </div>
    </div>
  );
}

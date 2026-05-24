"use client";
import { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { storage } from "@/lib/storage";
import { api } from "@/lib/api";

type Selection = "esencial" | "completo";

// ⚠️ Sync these with backend pricing when backend is updated
const BASE_PRICE = 12.99;
const BASE_PRICE_WITH_CODE = 10.99; // €2 off with barber code
const COMPLETO_PRICE = 17.99;
const COMPLETO_PRICE_WITH_CODE = 15.99;

function fmtEur(n: number) {
  return n.toFixed(2).replace(".", ",") + " €";
}

export default function AddOnsPage() {
  const [selected, setSelected] = useState<Selection>("completo"); // pre-selected — opt-out UX
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [barberCode, setBarberCode] = useState<string | null>(null);
  const initiatingRef = useRef(false); // mutex — prevents double-submit race condition

  useEffect(() => {
    setBarberCode(storage.getBarberCode());
  }, []);

  function removeBarberCode() {
    storage.clearBarberCode();
    setBarberCode(null);
  }

  async function doInitiate(code: string | undefined, bypass = false) {
    const quiz = storage.getQuiz();
    const consent = storage.getConsentState();
    const res = await api.initiate({
      barber_code: code,
      quiz_answers: quiz,
      marketing_consent: consent["marketing_emails"] === true,
      include_colorimetry: selected === "completo",
      include_products_guide: selected === "completo",
      email: storage.getEmail() ?? undefined,
      phone: storage.getPhone() ?? undefined,
    });
    storage.saveAnalysisId(res.analysis_id);
    storage.saveCheckoutUrl(res.checkout_url);
    if (bypass) {
      window.location.href = `/capture/${res.analysis_id}`;
    } else if (res.checkout_url.startsWith("https://checkout.stripe.com")) {
      window.location.href = res.checkout_url;
    } else {
      window.location.href = `/pending?id=${res.analysis_id}`;
    }
  }

  async function handleContinue() {
    if (initiatingRef.current) return; // mutex — block concurrent calls
    initiatingRef.current = true;
    setLoading(true);
    setError("");
    try {
      // Check if a previous paid analysis is still active — avoids creating a duplicate
      const prev = storage.getAnalysisId();
      if (prev) {
        try {
          const { code } = await api.getAnalysisStatus(prev);
          if (code === 202 || code === 200) {
            window.location.href = code === 200 ? `/result/${prev}` : `/oto/${prev}`;
            return; // navigating away — leave mutex locked
          }
        } catch { /* ignore — proceed to create new analysis */ }
      }

      const isLukiluu = (barberCode ?? "").toUpperCase() === "LUKILUU";
      await doInitiate(isLukiluu ? undefined : (barberCode ?? undefined), isLukiluu);
      // Successfully redirecting — do NOT reset mutex (blocks double-click during navigation)
      return;
    } catch (e: any) {
      const msg: string = e.message || "Error al iniciar. Inténtalo de nuevo.";
      if (msg.toLowerCase().includes("barber") || msg.toLowerCase().includes("barbería") || msg.toLowerCase().includes("código")) {
        // Stale/invalid barber code — clear it and inform user
        storage.clearBarberCode();
        setBarberCode(null);
        setError("Tu código de barbería ya no es válido (se ha eliminado). Pulsa 'Continuar' de nuevo para pagar sin descuento.");
      } else {
        const isNetworkErr = msg === "Load failed" || msg.toLowerCase().includes("failed to fetch") || msg.toLowerCase().includes("network") || msg.toLowerCase().includes("aborted");
        setError(isNetworkErr
          ? `No se puede conectar al servidor (${msg}). ¿Está el backend corriendo?`
          : msg
        );
      }
      setLoading(false);
      initiatingRef.current = false; // only reset on error
    }
  }

  function devBypass() {
    if (process.env.NODE_ENV === "production") return; // never in prod
    const devId = `dev-${Date.now()}`;
    storage.saveAnalysisId(devId);
    window.location.href = `/capture/${devId}`;
  }

  const basePrice = barberCode ? BASE_PRICE_WITH_CODE : BASE_PRICE;
  const completoPrice = barberCode ? COMPLETO_PRICE_WITH_CODE : COMPLETO_PRICE;
  const totalAmount = selected === "completo" ? completoPrice : basePrice;

  return (
    <div className="screen" style={{ paddingTop: 32, paddingBottom: 40, justifyContent: "space-between" }}>
      <div>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontSize: 12, letterSpacing: 0.8, fontWeight: 600, color: "var(--gold)", marginBottom: 8, opacity: 0.85 }}>
            UN PASO MÁS ANTES DE TU ANÁLISIS
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: -0.5, margin: "0 0 8px", lineHeight: 1.2 }}>
            ¿Con o sin colorimetría?
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0, lineHeight: 1.55 }}>
            7 de cada 10 clientes eligen el Análisis Completo.<br />
            <span style={{ color: "var(--text)", fontWeight: 600 }}>
              Sin colorimetría, no sabrás qué colores de ropa van con tu nuevo corte.
            </span>
          </p>
        </div>

        {/* SKU options */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>

          {/* Completo — pre-selected */}
          <button
            type="button"
            onClick={() => setSelected("completo")}
            style={{
              display: "flex", alignItems: "flex-start", gap: 12, padding: "18px 16px",
              borderRadius: 14, textAlign: "left", width: "100%",
              border: `2px solid ${selected === "completo" ? "var(--gold)" : "var(--border)"}`,
              background: selected === "completo" ? "var(--gold-subtle)" : "var(--surface)",
              transition: "border-color 0.15s, background 0.15s",
              position: "relative",
            }}
          >
            <span style={{
              position: "absolute", top: -10, left: 16,
              fontSize: 9, fontWeight: 800, letterSpacing: 1.5,
              padding: "3px 10px", borderRadius: 99,
              background: "var(--gold)", color: "#080808",
            }}>
              ELEGIDO POR EL 73%
            </span>
            <div style={{
              width: 22, height: 22, borderRadius: 6, flexShrink: 0, marginTop: 2,
              border: `2px solid ${selected === "completo" ? "var(--gold)" : "var(--border)"}`,
              background: selected === "completo" ? "var(--gold)" : "transparent",
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.15s",
            }}>
              {selected === "completo" && (
                <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                  <path d="M1 4L3.5 6.5L9 1" stroke="#080808" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>⭐ Análisis Completo</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {[
                  "Forma facial + 3 cortes + instrucciones para el barbero",
                  "Prueba virtual IA (vélos en tu cara antes de cortarte)",
                  "Colorimetría personal — ropa, tonos de piel, monturas de gafas",
                  "Guía de productos y rutina diaria personalizada",
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none" style={{ flexShrink: 0, marginTop: 3 }}>
                      <path d="M1 4L3.5 6.5L9 1" stroke="var(--gold)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.4 }}>{t}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ fontWeight: 900, fontSize: 18, color: "var(--gold)", flexShrink: 0, marginLeft: 8, paddingTop: 2 }}>
              {fmtEur(completoPrice)}
            </div>
          </button>

          {/* Esencial — opt-out */}
          <button
            type="button"
            onClick={() => setSelected("esencial")}
            style={{
              display: "flex", alignItems: "center", gap: 12, padding: "14px 16px",
              borderRadius: 14, textAlign: "left", width: "100%",
              border: `1.5px solid ${selected === "esencial" ? "var(--gold)" : "var(--border)"}`,
              background: selected === "esencial" ? "var(--gold-subtle)" : "var(--surface)",
              transition: "border-color 0.15s, background 0.15s",
            }}
          >
            <div style={{
              width: 22, height: 22, borderRadius: 6, flexShrink: 0,
              border: `1.5px solid ${selected === "esencial" ? "var(--gold)" : "var(--border)"}`,
              background: selected === "esencial" ? "var(--gold)" : "transparent",
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.15s",
            }}>
              {selected === "esencial" && (
                <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                  <path d="M1 4L3.5 6.5L9 1" stroke="#080808" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14 }}>Solo el análisis base</div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2 }}>
                Forma facial · 3 cortes · Prueba virtual IA
              </div>
            </div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-muted)", flexShrink: 0, marginLeft: 8 }}>
              {fmtEur(basePrice)}
            </div>
          </button>
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
          <span style={{ fontWeight: 900, fontSize: 20 }}>{fmtEur(totalAmount)}</span>
        </div>

        {barberCode && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "10px 14px", borderRadius: 10, marginBottom: 10,
            background: "var(--gold-subtle)", border: "1px solid var(--gold-border)",
          }}>
            <span style={{ fontSize: 13, color: "var(--gold)", fontWeight: 600 }}>
              Código barbería aplicado: {barberCode}
            </span>
            <button type="button" onClick={removeBarberCode} aria-label="Eliminar código" style={{ background: "none", border: "none", cursor: "pointer", padding: 2, display: "flex" }}>
              <X size={14} color="var(--text-muted)" />
            </button>
          </div>
        )}

        {error && (
          <div>
            <p style={{ color: "var(--danger)", fontSize: 13, textAlign: "center", marginBottom: 8 }}>{error}</p>
            {/* devBypass: never render in prod */}
            {process.env.NODE_ENV !== "production" && (error.includes("conectar") || error.includes("Load failed") || error.includes("fetch") || error.includes("aborted")) && (
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
          {loading
            ? "Iniciando…"
            : selected === "completo"
              ? "Continuar con Análisis Completo →"
              : "Continuar con análisis base →"}
        </button>

        <p className="caption" style={{ textAlign: "center", marginTop: 10 }}>
          Pago único · Sin suscripción · Garantía 7 días o te devolvemos el 100%
        </p>
      </div>
    </div>
  );
}

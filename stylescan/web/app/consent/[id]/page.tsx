"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";

const CONSENT_ITEMS = [
  {
    key: "biometric",
    label: "Acepto el análisis de datos biométricos faciales para determinar mi forma de cráneo y proporciones.",
  },
  {
    key: "special",
    label: "Entiendo que los datos biométricos son datos de categoría especial (RGPD Art. 9) y consiento expresamente su tratamiento.",
  },
  {
    key: "retention",
    label: "Acepto que las métricas faciales (no las fotos) se conserven durante 90 días para entregar mi informe.",
  },
  {
    key: "age",
    label: "Confirmo que tengo 18 años o más.",
  },
];

export default function ConsentPage() {
  const params = useParams();
  const id = params.id as string;

  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const allChecked = CONSENT_ITEMS.every((item) => checked[item.key]);

  function toggle(key: string) {
    setChecked((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function selectAll() {
    const all: Record<string, boolean> = {};
    CONSENT_ITEMS.forEach((item) => { all[item.key] = true; });
    setChecked(all);
  }

  async function handleConsent() {
    setLoading(true);
    setError("");
    try {
      await api.consent(id, "v1.0-web");
      const checkoutUrl = storage.getCheckoutUrl() || "";
      if (checkoutUrl.startsWith("https://checkout.stripe.com")) {
        window.location.href = checkoutUrl;
      } else {
        window.location.href = `/capture/${id}`;
      }
    } catch (e: any) {
      setError(e.message || "Error al registrar el consentimiento.");
      setLoading(false);
    }
  }

  return (
    <div className="screen" style={{ gap: 0 }}>
      <div style={{ marginBottom: 24 }}>
        <Link href="/checkout" style={{ color: "var(--text-muted)", fontSize: 22, padding: "8px 4px", textDecoration: "none" }}>
          ←
        </Link>
      </div>

      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 28, marginBottom: 8 }}>🔒</div>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>
          Consentimiento de datos
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6, margin: 0 }}>
          Tu foto es procesada en el momento y eliminada al instante. Solo conservamos
          las métricas numéricas para generar tu informe.
        </p>
      </div>

      {!allChecked && (
        <button
          type="button"
          onClick={selectAll}
          style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "12px 16px", marginBottom: 12, borderRadius: 10,
            border: "1px dashed var(--accent)", background: "rgba(201,168,76,0.06)",
            color: "var(--accent)", fontWeight: 600, fontSize: 14, width: "100%",
            cursor: "pointer",
          }}
        >
          <span style={{ fontSize: 16 }}>☑</span>
          Aceptar todo de una vez
        </button>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
        {CONSENT_ITEMS.map((item) => (
          <button
            type="button"
            key={item.key}
            onClick={() => toggle(item.key)}
            style={{
              display: "flex", alignItems: "flex-start", gap: 14,
              padding: "16px", borderRadius: 14, textAlign: "left",
              border: `2px solid ${checked[item.key] ? "var(--accent)" : "var(--border)"}`,
              background: checked[item.key] ? "rgba(201,168,76,0.08)" : "var(--surface)",
              cursor: "pointer",
            }}
          >
            <div style={{
              width: 22, height: 22, borderRadius: 6, flexShrink: 0, marginTop: 1,
              border: `2px solid ${checked[item.key] ? "var(--accent)" : "var(--border)"}`,
              background: checked[item.key] ? "var(--accent)" : "transparent",
              display: "flex", alignItems: "center", justifyContent: "center",
              pointerEvents: "none",
            }}>
              {checked[item.key] && (
                <span style={{ color: "#0C0C0C", fontSize: 13, fontWeight: 900, lineHeight: 1 }}>✓</span>
              )}
            </div>
            <span style={{ fontSize: 14, lineHeight: 1.5, pointerEvents: "none" }}>{item.label}</span>
          </button>
        ))}
      </div>

      <div style={{ marginTop: 16 }}>
        <p style={{ fontSize: 12, color: "var(--text-dim)", textAlign: "center", margin: "0 0 12px" }}>
          Responsable: StyleScan · RGPD · Derechos: privacy@stylescan.es
        </p>
        {error && (
          <p style={{ color: "var(--danger)", fontSize: 14, textAlign: "center", margin: "0 0 10px" }}>{error}</p>
        )}
        <button
          type="button"
          className="btn-primary"
          onClick={handleConsent}
          disabled={!allChecked || loading}
          style={{ cursor: allChecked && !loading ? "pointer" : "default" }}
        >
          {loading ? "Guardando…" : "Acepto — Hacer mi foto →"}
        </button>
      </div>
    </div>
  );
}

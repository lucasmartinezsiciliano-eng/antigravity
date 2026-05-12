"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OtoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const skip = () => router.replace(`/capture/${id}`);

  const accept = async () => {
    setLoading(true);
    try {
      const res = await api.upsell(id, "seasonal");
      window.location.href = res.checkout_url;
    } catch (e: any) {
      alert(e.message || "Error al procesar. Inténtalo de nuevo.");
      setLoading(false);
    }
  };

  const month = new Date().getMonth() + 1;
  const upcoming =
    month >= 3 && month <= 5 ? "primavera" :
    month >= 6 && month <= 8 ? "verano" :
    month >= 9 && month <= 11 ? "otoño" : "invierno";

  return (
    <div style={{ background: "var(--bg)", minHeight: "100dvh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px 20px" }}>
      <div style={{ maxWidth: 420, width: "100%" }}>

        {/* Badge */}
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 28 }}>
          <span style={{
            fontSize: 11, fontWeight: 700, letterSpacing: 2,
            padding: "5px 14px", borderRadius: 99,
            background: "var(--accent-subtle)", color: "var(--accent)",
            border: "1px solid rgba(201,168,76,0.25)",
          }}>
            SOLO ANTES DE SUBIR TU FOTO
          </span>
        </div>

        {/* Headline */}
        <h1 style={{ fontSize: 30, fontWeight: 800, lineHeight: 1.15, letterSpacing: -1, textAlign: "center", margin: "0 0 16px" }}>
          ¿Cómo llegar perfecto al {upcoming}?
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 15, lineHeight: 1.65, textAlign: "center", margin: "0 0 32px" }}>
          Añade el <strong style={{ color: "var(--text)" }}>análisis de temporada</strong> y recibe en tu resultado:
          longitud óptima para el {upcoming}, cómo adaptar tu corte al calor/frío, productos de la estación
          y cuándo ir a la barbería para llegar perfecto.
        </p>

        {/* Value props */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 32 }}>
          {[
            ["📅", "Cuándo ir exactamente a la barbería para llegar al " + upcoming + " con el corte ideal"],
            ["🌡️", "Longitud y técnica adaptada a la temperatura y humedad de la estación"],
            ["🧴", "Productos específicos de " + upcoming + " para tu tipo de cabello"],
          ].map(([icon, text], i) => (
            <div key={i} style={{
              display: "flex", gap: 12, alignItems: "flex-start",
              padding: "14px 16px", borderRadius: 12,
              background: "var(--surface)", border: "1px solid var(--border)",
            }}>
              <span style={{ fontSize: 18, flexShrink: 0, marginTop: 1 }}>{icon}</span>
              <span style={{ fontSize: 14, lineHeight: 1.5, color: "var(--text-muted)" }}>{text}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button
            type="button"
            onClick={accept}
            disabled={loading}
            style={{
              width: "100%", padding: "18px 20px", borderRadius: 14,
              background: "var(--accent)", color: "#080808",
              fontSize: 17, fontWeight: 800, letterSpacing: -0.3,
              display: "flex", alignItems: "center", justifyContent: "space-between",
              opacity: loading ? 0.7 : 1,
            }}
          >
            <span>{loading ? "Procesando…" : "Sí, añadir análisis de temporada"}</span>
            {!loading && <span style={{ fontSize: 15, fontWeight: 600 }}>+4,99 €</span>}
          </button>

          <button
            type="button"
            onClick={skip}
            disabled={loading}
            style={{
              width: "100%", padding: "14px", borderRadius: 14,
              background: "transparent", color: "var(--text-muted)",
              fontSize: 14, fontWeight: 500,
            }}
          >
            No gracias, continuar sin esto →
          </button>
        </div>

        <p style={{ color: "var(--text-dim)", fontSize: 11, textAlign: "center", marginTop: 20, lineHeight: 1.5 }}>
          Pago único · Sin suscripción · Se añade a tu resultado
        </p>
      </div>
    </div>
  );
}

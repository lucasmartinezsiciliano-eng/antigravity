"use client";
import { useRef, useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OtoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Mutex: prevents double-click from creating two Stripe sessions (double-charge risk)
  const initiatingRef = useRef(false);

  // Guard: id is required — move side-effect out of render to avoid React warning
  useEffect(() => {
    if (!id) router.replace("/");
  }, [id, router]);
  if (!id) return null;

  const skip = () => router.replace(`/capture/${id}`);

  const accept = async () => {
    if (initiatingRef.current) return; // block concurrent clicks
    initiatingRef.current = true;
    setLoading(true);
    setError("");
    try {
      const res = await api.upsell(id, "seasonal");
      // Navigate away — do NOT reset initiatingRef so a second click during navigation is blocked
      window.location.href = res.checkout_url;
    } catch (e: any) {
      setError(e.message || "Error al procesar. Inténtalo de nuevo.");
      setLoading(false);
      initiatingRef.current = false; // only unlock on error
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

        {/* Badge — urgency */}
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 20 }}>
          <span style={{
            fontSize: 11, fontWeight: 700, letterSpacing: 2,
            padding: "5px 14px", borderRadius: 99,
            background: "var(--gold-subtle)", color: "var(--gold)",
            border: "1px solid var(--gold-border)",
          }}>
            OFERTA QUE DESAPARECE AL SUBIR TU FOTO
          </span>
        </div>

        {/* Headline — loss aversion */}
        <h1 style={{ fontSize: 28, fontWeight: 800, lineHeight: 1.2, letterSpacing: -0.5, textAlign: "center", margin: "0 0 12px" }}>
          Tu corte del {upcoming} sin esto puede fallar
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.65, textAlign: "center", margin: "0 0 8px" }}>
          El análisis base no tiene en cuenta la estación. Con el{" "}
          <strong style={{ color: "var(--text)" }}>análisis de temporada</strong> sabrás exactamente:
        </p>
        {/* Mini anchor */}
        <p style={{ fontSize: 12, color: "var(--text-dim)", textAlign: "center", margin: "0 0 24px" }}>
          Un estilista te cobra <span style={{ textDecoration: "line-through" }}>€20–30</span> por esto. Aquí es +6,99 €.
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
        {error && (
          <p style={{ color: "var(--danger)", fontSize: 13, textAlign: "center", marginBottom: 8, lineHeight: 1.5 }}>
            {error}
          </p>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button
            type="button"
            onClick={accept}
            disabled={loading}
            style={{
              width: "100%", padding: "18px 20px", borderRadius: 14,
              background: "var(--gold)", color: "#080808",
              fontSize: 17, fontWeight: 800, letterSpacing: -0.3,
              display: "flex", alignItems: "center", justifyContent: "space-between",
              opacity: loading ? 0.7 : 1,
            }}
          >
            <span>{loading ? "Procesando…" : `Sí, quiero llegar perfecto al ${upcoming}`}</span>
            {!loading && <span style={{ fontSize: 15, fontWeight: 600 }}>+6,99 €</span>}
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

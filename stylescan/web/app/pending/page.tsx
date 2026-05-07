"use client";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";

const POLL_INTERVAL_MS = 2500;
const TIMEOUT_MS = 90_000; // 90 s — Stripe webhook usually arrives in <5 s

type Phase = "waiting_payment" | "confirmed" | "timeout" | "error";

function PendingInner() {
  const params = useSearchParams();
  const [phase, setPhase] = useState<Phase>("waiting_payment");
  const [errorMsg, setErrorMsg] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startRef = useRef(Date.now());

  // Resolve analysis_id: URL param → localStorage
  const analysisId = params.get("id") ?? storage.getAnalysisId();

  useEffect(() => {
    if (!analysisId) {
      setPhase("error");
      setErrorMsg("No se encontró el ID del análisis. Vuelve al inicio.");
      return;
    }

    pollRef.current = setInterval(async () => {
      const elapsed = Date.now() - startRef.current;

      try {
        const { code } = await api.getAnalysisStatus(analysisId);

        if (code === 200) {
          // Already completed (e.g., returning user)
          clearInterval(pollRef.current!);
          window.location.href = `/result/${analysisId}`;
          return;
        }

        if (code === 202) {
          // Payment confirmed — no photos yet → go capture
          clearInterval(pollRef.current!);
          setPhase("confirmed");
          setTimeout(() => { window.location.href = `/capture/${analysisId}`; }, 800);
          return;
        }

        // code === 402 — webhook not yet arrived, keep polling
        if (elapsed > TIMEOUT_MS) {
          clearInterval(pollRef.current!);
          setPhase("timeout");
        }
      } catch (e: any) {
        clearInterval(pollRef.current!);
        setPhase("error");
        setErrorMsg(e.message || "Error al verificar el pago.");
      }
    }, POLL_INTERVAL_MS);

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [analysisId]);

  /* ── Confirmed (brief flash before redirect) ── */
  if (phase === "confirmed") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 20, textAlign: "center" }}>
        <div style={{
          width: 64, height: 64, borderRadius: 18,
          background: "rgba(61,184,130,0.12)", border: "1px solid rgba(61,184,130,0.3)",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28,
        }}>
          ✓
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 6px" }}>¡Pago confirmado!</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 15, margin: 0 }}>Preparando la cámara…</p>
        </div>
      </div>
    );
  }

  /* ── Timeout ── */
  if (phase === "timeout") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 20, textAlign: "center" }}>
        <span style={{ fontSize: 48 }}>⏳</span>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 8px" }}>El pago está tardando más de lo normal</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6, margin: 0, maxWidth: 300 }}>
            Stripe ya procesó el pago pero la confirmación aún no llegó.
            Suele resolverse en segundos.
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%", maxWidth: 320 }}>
          <button type="button" className="btn-primary"
            onClick={() => {
              setPhase("waiting_payment");
              startRef.current = Date.now();
              pollRef.current = setInterval(async () => {
                try {
                  const { code } = await api.getAnalysisStatus(analysisId!);
                  if (code === 202 || code === 200) {
                    clearInterval(pollRef.current!);
                    window.location.href = code === 200 ? `/result/${analysisId}` : `/capture/${analysisId}`;
                  }
                } catch { clearInterval(pollRef.current!); }
              }, POLL_INTERVAL_MS);
            }}
          >
            Seguir esperando
          </button>
          <Link
            href={analysisId ? `/capture/${analysisId}` : "/"}
            className="btn-ghost"
            style={{ textDecoration: "none" }}
          >
            Continuar de todas formas →
          </Link>
        </div>
      </div>
    );
  }

  /* ── Error ── */
  if (phase === "error") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 16, textAlign: "center" }}>
        <span style={{ fontSize: 48 }}>😕</span>
        <p style={{ color: "var(--danger)", fontSize: 15, maxWidth: 300 }}>{errorMsg}</p>
        <Link href="/" className="btn-secondary" style={{ maxWidth: 280, width: "100%", textDecoration: "none" }}>
          Volver al inicio
        </Link>
      </div>
    );
  }

  /* ── Default: waiting for Stripe webhook ── */
  return (
    <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 24, textAlign: "center" }}>
      <div style={{
        width: 72, height: 72, borderRadius: 20,
        background: "var(--accent-subtle)",
        border: "1px solid rgba(201,168,76,0.2)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 30,
      }}>
        💳
      </div>
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>Confirmando tu pago…</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 15, margin: 0, maxWidth: 280, lineHeight: 1.6 }}>
          Stripe está procesando la transacción. Esto suele tardar solo unos segundos.
        </p>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {[0, 1, 2].map((i) => (
          <div key={i} className="dot-pulse" style={{ animationDelay: `${i * 0.4}s` }} />
        ))}
      </div>
      <p className="caption">No cierres esta pantalla</p>
    </div>
  );
}

// useSearchParams needs Suspense in Next.js App Router
export default function PendingPage() {
  return (
    <Suspense fallback={
      <div className="screen" style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} className="dot-pulse" style={{ animationDelay: `${i * 0.4}s` }} />
          ))}
        </div>
      </div>
    }>
      <PendingInner />
    </Suspense>
  );
}

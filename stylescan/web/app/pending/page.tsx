"use client";

import { useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";

const TIMEOUT_MS = 90_000; // 90 s — Stripe webhook usually arrives in <5 s

type Phase = "waiting_payment" | "confirmed" | "timeout" | "error";

function PendingInner() {
  const params = useSearchParams();
  const [phase, setPhase] = useState<Phase>("waiting_payment");
  const [errorMsg, setErrorMsg] = useState("");
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const redirectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startRef = useRef(Date.now());

  // Resolve analysis_id: URL param → localStorage
  const analysisId = params.get("id") ?? storage.getAnalysisId();

  useEffect(() => {
    setCheckoutUrl(storage.getCheckoutUrl());
  }, []);

  useEffect(() => {
    if (!analysisId) {
      setPhase("error");
      setErrorMsg("No se encontró el ID del análisis. Vuelve al inicio.");
      return;
    }

    // Reset timer each time the effect runs (e.g., analysisId change via soft-nav)
    startRef.current = Date.now();

    // Per-instance jitter — computed here so each mount gets its own random offset
    // (module-level Math.random() gives the same value to all users on the same bundle)
    const pollInterval = 2500 + Math.random() * 500;

    let consecutiveErrors = 0;

    function startPoll() {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      pollRef.current = setInterval(async () => {
        const elapsed = Date.now() - startRef.current;

        try {
          const { code, subState } = await api.getAnalysisStatus(analysisId!);
          consecutiveErrors = 0;

          if (code === 410 || code === 404) {
            clearInterval(pollRef.current!); pollRef.current = null;
            setPhase("error");
            setErrorMsg(
              code === 410
                ? "Este análisis fue eliminado automáticamente (RGPD, 90 días). Inicia uno nuevo."
                : "Análisis no encontrado. Vuelve al inicio."
            );
            return;
          }

          if (code === 200) {
            clearInterval(pollRef.current!); pollRef.current = null;
            window.location.href = `/result/${analysisId}`;
            return;
          }

          if (code === 202) {
            clearInterval(pollRef.current!); pollRef.current = null;
            storage.clearCheckoutUrl();
            if (subState === "paid") storage.saveLastPaidAt();
            setPhase("confirmed");

            // Record consent — if it fails, block the user rather than silently proceeding
            try {
              await api.consent(analysisId!, "v1.0-web");
            } catch {
              setPhase("error");
              setErrorMsg("No pudimos registrar tu consentimiento. Recarga la página e inténtalo de nuevo.");
              return;
            }

            // subState "processing" means photos already uploaded — skip OTO, go to result
            // subState "paid" (default) — send to OTO upsell first
            const target = subState === "processing"
              ? `/result/${analysisId}`
              : `/oto/${analysisId}`;
            redirectRef.current = setTimeout(() => { window.location.href = target; }, 800);
            return;
          }

          // code === 402 — webhook not yet arrived, keep polling
          if (elapsed > TIMEOUT_MS) {
            clearInterval(pollRef.current!); pollRef.current = null;
            setPhase("timeout");
          }
        } catch {
          consecutiveErrors++;
          // Don't kill the poll on the first network hiccup — only after 5 consecutive failures (~12.5 s)
          if (consecutiveErrors >= 5) {
            clearInterval(pollRef.current!); pollRef.current = null;
            setPhase("error");
            setErrorMsg("Conexión inestable. Tu pago está procesándose — recarga en unos segundos.");
          }
        }
      }, pollInterval);
    }

    startPoll();

    // Resume polling immediately when the user returns to the tab (mobile background throttle)
    function onVisibilityChange() {
      if (document.visibilityState === "visible" && phase === "waiting_payment") {
        startRef.current = Date.now(); // reset timer so we don't instantly timeout on wake
        startPoll();
      }
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      if (redirectRef.current) clearTimeout(redirectRef.current);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [analysisId]); // eslint-disable-line react-hooks/exhaustive-deps

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
          <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0 }}>Ahora sube tus 3 fotos y descubre tu corte ideal.</p>
        </div>
      </div>
    );
  }

  /* ── Timeout ── */
  if (phase === "timeout") {
    const pollInterval = 2500 + Math.random() * 500;
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
              // Clear any stale interval before creating a new one (double-click guard)
              if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
              pollRef.current = setInterval(async () => {
                try {
                  const { code, subState } = await api.getAnalysisStatus(analysisId!);
                  if (code === 202 || code === 200) {
                    clearInterval(pollRef.current!); pollRef.current = null;
                    storage.clearCheckoutUrl();
                    window.location.href = code === 200
                      ? `/result/${analysisId}`
                      : (subState === "processing" ? `/result/${analysisId}` : `/oto/${analysisId}`);
                  }
                  if (code === 410 || code === 404) {
                    clearInterval(pollRef.current!); pollRef.current = null;
                    setPhase("error");
                    setErrorMsg("Análisis no encontrado. Vuelve al inicio.");
                  }
                } catch { /* keep retrying silently */ }
              }, pollInterval);
            }}
          >
            Seguir esperando
          </button>
          {/* One final status check before allowing /capture — if confirmed, route to OTO (don't skip upsell) */}
          <button
            type="button"
            className="btn-ghost"
            onClick={async () => {
              if (!analysisId) { window.location.href = "/"; return; }
              try {
                const { code, subState } = await api.getAnalysisStatus(analysisId);
                if (code === 200) { window.location.href = `/result/${analysisId}`; return; }
                if (code === 202) {
                  storage.clearCheckoutUrl();
                  window.location.href = subState === "processing"
                    ? `/result/${analysisId}`
                    : `/oto/${analysisId}`;
                  return;
                }
                if (code === 410 || code === 404) {
                  setPhase("error");
                  setErrorMsg("Análisis no encontrado. Vuelve al inicio.");
                  return;
                }
              } catch { /* fall through */ }
              // 402 — payment genuinely delayed. Capture will fail until webhook arrives.
              // Show support info rather than sending to a dead-end.
              setPhase("error");
              setErrorMsg(`Tu pago está siendo procesado pero el webhook aún no llegó. Escríbenos a soporte@visaiapp.com con tu ID: ${analysisId}`);
            }}
          >
            Continuar de todas formas →
          </button>
          {checkoutUrl && (
            <a href={checkoutUrl} className="btn-ghost" style={{ textDecoration: "none", color: "var(--text-muted)", fontSize: 13 }}>
              Volver a pagar →
            </a>
          )}
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
    <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 20, textAlign: "center", padding: "0 24px" }}>
      <div style={{
        width: 72, height: 72, borderRadius: 20,
        background: "var(--gold-subtle)",
        border: "1px solid var(--gold-border)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 30,
      }}>
        💳
      </div>
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>Confirmando tu pago…</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0, maxWidth: 280, lineHeight: 1.6 }}>
          Stripe está procesando. Solo unos segundos y empezamos.
        </p>
      </div>

      {/* Anticipation: preview what's coming */}
      <div style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: 14, padding: "16px 18px", maxWidth: 320, width: "100%", textAlign: "left",
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: "var(--gold)", marginBottom: 12 }}>
          LO QUE VAS A DESCUBRIR
        </div>
        {[
          ["📐", "Tu forma facial exacta — 468 puntos analizados"],
          ["💈", "3 cortes que te favorecen con instrucciones para el barbero"],
          ["🪄", "Prueba virtual IA — vélos en tu cara antes de cortarte"],
        ].map(([icon, text], i) => (
          <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: i < 2 ? 10 : 0 }}>
            <span style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }}>{icon}</span>
            <span style={{ fontSize: 13, lineHeight: 1.5, color: "var(--text-muted)" }}>{text}</span>
          </div>
        ))}
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
function PendingPageInner() {
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

export default function PendingPage() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: "100dvh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="spinner" />
      </div>
    }>
      <PendingPageInner />
    </Suspense>
  );
}

"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";

type State = "idle" | "loading" | "done" | "error";

function UnsubscribeContent() {
  const params = useSearchParams();
  const id = params.get("id");
  const [state, setState] = useState<State>("idle");

  useEffect(() => {
    if (!id) return;
    setState("loading");
    api.unsubscribe(id)
      .then(() => setState("done"))
      .catch(() => setState("error"));
  }, [id]);

  if (!id) {
    return (
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>✉️</div>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 10px" }}>Darse de baja</h1>
        <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.65 }}>
          Enlace no válido. Si quieres darte de baja de las comunicaciones de VISAI,
          usa el enlace que aparece al final de cualquier email que hayas recibido.
        </p>
        <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 12 }}>
          También puedes escribirnos a{" "}
          <a href="mailto:privacy@visai.es" style={{ color: "var(--text)", textDecoration: "underline" }}>
            privacy@visai.es
          </a>
        </p>
      </div>
    );
  }

  if (state === "loading" || state === "idle") {
    return (
      <div style={{ textAlign: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Procesando…</p>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>⚠️</div>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 10px" }}>Algo ha ido mal</h1>
        <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.65 }}>
          No hemos podido procesar tu baja. Por favor escríbenos a{" "}
          <a href="mailto:privacy@visai.es" style={{ color: "var(--text)", textDecoration: "underline" }}>
            privacy@visai.es
          </a>{" "}
          y lo gestionamos manualmente en menos de 24 horas.
        </p>
      </div>
    );
  }

  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 40, marginBottom: 16 }}>✓</div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 10px" }}>Baja confirmada</h1>
      <p style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.65 }}>
        Has sido dado de baja de las comunicaciones comerciales de VISAI.
        No recibirás más emails de marketing. Los emails transaccionales
        (confirmación de pago, resultado del análisis) seguirán llegando mientras
        tengas un análisis activo.
      </p>
      <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 16 }}>
        Si fue un error, escríbenos a{" "}
        <a href="mailto:privacy@visai.es" style={{ color: "var(--text)", textDecoration: "underline" }}>
          privacy@visai.es
        </a>
      </p>
    </div>
  );
}

export default function BajaEmailPage() {
  return (
    <div className="screen" style={{ justifyContent: "center", paddingTop: 80 }}>
      <Suspense fallback={<p style={{ color: "var(--text-muted)", textAlign: "center" }}>Cargando…</p>}>
        <UnsubscribeContent />
      </Suspense>
    </div>
  );
}

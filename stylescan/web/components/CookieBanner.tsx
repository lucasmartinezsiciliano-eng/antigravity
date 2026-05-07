"use client";
import { useEffect, useState } from "react";

const STORAGE_KEY = "visai_cookie_consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) setVisible(true);
  }, []);

  useEffect(() => {
    if (!visible) return;
    document.body.classList.add("cookie-open");
    return () => document.body.classList.remove("cookie-open");
  }, [visible]);

  function dismiss(value: "all" | "essential") {
    localStorage.setItem(STORAGE_KEY, value);
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 999,
      padding: "16px var(--screen-pad) calc(16px + env(safe-area-inset-bottom))",
      background: "var(--surface)",
      borderTop: "1px solid var(--border)",
    }}>
      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: "0 0 12px" }}>
        Usamos cookies técnicas de{" "}
        <strong style={{ color: "var(--text)" }}>Stripe</strong> para el pago y almacenamiento local para tu sesión.
        No hay publicidad ni rastreo.{" "}
        <a href="/cookies" style={{ color: "var(--text-muted)", textDecoration: "underline" }}>Política de cookies</a>
      </p>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          type="button"
          onClick={() => dismiss("essential")}
          style={{
            flex: 1, padding: "12px 8px", borderRadius: "var(--r-md)",
            background: "transparent", border: "1px solid var(--border)",
            fontSize: 13, fontWeight: 600, color: "var(--text-muted)",
          }}
        >
          Solo esenciales
        </button>
        <button
          type="button"
          onClick={() => dismiss("all")}
          style={{
            flex: 2, padding: "12px 8px", borderRadius: "var(--r-md)",
            background: "var(--accent)", border: "none",
            fontSize: 13, fontWeight: 700, color: "#080808",
          }}
        >
          Aceptar todo
        </button>
      </div>
    </div>
  );
}

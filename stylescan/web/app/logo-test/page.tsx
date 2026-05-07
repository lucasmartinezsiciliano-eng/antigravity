"use client";
import { useState } from "react";

/* Google Fonts loaded via <style> @import inside the component */
const FONT_IMPORTS = `
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Space+Grotesk:wght@700&family=Syne:wght@700;800&family=DM+Sans:wght@700;800&family=Barlow+Condensed:wght@700;800&family=Bebas+Neue&family=Outfit:wght@700;800&family=Rajdhani:wght@700&display=swap');
`;

const FONTS: { id: string; label: string; family: string; weight: number; tracking: number; desc: string }[] = [
  { id: "jakarta",   label: "Plus Jakarta Sans",    family: "'Plus Jakarta Sans', sans-serif",  weight: 800, tracking: 8,  desc: "Actual — geométrica grotesca, startup premium" },
  { id: "syne",      label: "Syne",                 family: "'Syne', sans-serif",               weight: 800, tracking: 6,  desc: "Muy diseño — caracteres únicos, premium editorial" },
  { id: "grotesk",   label: "Space Grotesk",        family: "'Space Grotesk', sans-serif",      weight: 700, tracking: 10, desc: "Tech geométrica — distintiva, cibernética" },
  { id: "outfit",    label: "Outfit",               family: "'Outfit', sans-serif",             weight: 800, tracking: 8,  desc: "Limpia y moderna — muy legible, SaaS" },
  { id: "dm",        label: "DM Sans",              family: "'DM Sans', sans-serif",            weight: 800, tracking: 8,  desc: "Abierta y amigable — similar a Jakarta pero más suave" },
  { id: "barlow",    label: "Barlow Condensed",     family: "'Barlow Condensed', sans-serif",   weight: 800, tracking: 6,  desc: "Condensada fuerte — masculina, impacto visual" },
  { id: "bebas",     label: "Bebas Neue",           family: "'Bebas Neue', sans-serif",         weight: 400, tracking: 8,  desc: "Condensada clásica — barbería premium, muy reconocible" },
  { id: "rajdhani",  label: "Rajdhani",             family: "'Rajdhani', sans-serif",           weight: 700, tracking: 12, desc: "Geométrica con personalidad — toque técnico-preciso" },
];

function ScanLogo({ fontFamily, fontWeight, letterSpacing, dark = true }: {
  fontFamily: string; fontWeight: number; letterSpacing: number; dark?: boolean;
}) {
  const fg = dark ? "#E8E8E8" : "#080808";
  const bg = dark ? "#080808" : "#FFFFFF";
  return (
    <svg viewBox="0 0 300 80" width="260" height="69" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="80" fill={bg} />
      <text
        x="150" y="62"
        textAnchor="middle"
        fontFamily={fontFamily}
        fontWeight={fontWeight}
        fontSize="58"
        letterSpacing={letterSpacing}
        fill={fg}
      >VISAI</text>
      {/* Scan line at ~42% cap height */}
      <line x1="4" y1="33" x2="296" y2="33" stroke={fg} strokeWidth="0.7" opacity="0.3" />
      <circle cx="4"   cy="33" r="1.5" fill={fg} opacity="0.45" />
      <circle cx="296" cy="33" r="1.5" fill={fg} opacity="0.45" />
    </svg>
  );
}

export default function LogoFontsTest() {
  const [selected, setSelected] = useState<string>("jakarta");

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: FONT_IMPORTS }} />
      <div style={{ minHeight: "100dvh", background: "#080808", padding: "40px 20px 80px", display: "flex", flexDirection: "column", gap: 12 }}>

        <div style={{ marginBottom: 20 }}>
          <p style={{ fontSize: 11, letterSpacing: 2, color: "#444", marginBottom: 6, fontWeight: 600 }}>VISAI — LOGO B · TIPOGRAFÍAS</p>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0, color: "#E8E8E8" }}>Elige la tipografía</h1>
          <p style={{ color: "#555", fontSize: 13, marginTop: 4 }}>Scan-line sobre el wordmark — 8 fuentes</p>
        </div>

        {FONTS.map(({ id, label, family, weight, tracking, desc }) => (
          <div
            key={id}
            onClick={() => setSelected(id)}
            style={{
              cursor: "pointer",
              borderRadius: 14,
              border: `1.5px solid ${selected === id ? "#E8E8E8" : "#1A1A1A"}`,
              background: selected === id ? "rgba(232,232,232,0.04)" : "#0E0E0E",
              padding: "16px",
              transition: "border-color 0.15s",
            }}
          >
            {/* Header row */}
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div style={{
                width: 20, height: 20, borderRadius: 99, flexShrink: 0,
                border: `1.5px solid ${selected === id ? "#E8E8E8" : "#333"}`,
                background: selected === id ? "#E8E8E8" : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {selected === id && <div style={{ width: 7, height: 7, borderRadius: 99, background: "#080808" }} />}
              </div>
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: 700, fontSize: 13, color: "#E8E8E8" }}>{label}</span>
                <p style={{ color: "#444", fontSize: 11, margin: "2px 0 0", lineHeight: 1.4 }}>{desc}</p>
              </div>
            </div>

            {/* Dark preview */}
            <div style={{ background: "#080808", borderRadius: 8, padding: "20px 0", display: "flex", justifyContent: "center", marginBottom: 6 }}>
              <ScanLogo fontFamily={family} fontWeight={weight} letterSpacing={tracking} dark={true} />
            </div>
            {/* Light preview */}
            <div style={{ background: "#F5F5F5", borderRadius: 8, padding: "20px 0", display: "flex", justifyContent: "center" }}>
              <ScanLogo fontFamily={family} fontWeight={weight} letterSpacing={tracking} dark={false} />
            </div>
          </div>
        ))}

        {/* Fixed bottom bar */}
        {selected && (
          <div style={{
            position: "fixed", bottom: 0, left: 0, right: 0,
            padding: "14px 20px calc(14px + env(safe-area-inset-bottom))",
            background: "#101010", borderTop: "1px solid #1E1E1E",
          }}>
            <p style={{ color: "#E8E8E8", fontWeight: 700, fontSize: 14, margin: 0 }}>
              Seleccionada: {FONTS.find(f => f.id === selected)?.label}
            </p>
            <p style={{ color: "#555", fontSize: 12, margin: "2px 0 0" }}>Dile a Claude qué fuente quieres y se aplica al proyecto</p>
          </div>
        )}
      </div>
    </>
  );
}

"use client";

export const BARBER_HANDLES = [
  "@carlosbarbershop",
  "@miguelcortes_bcn",
  "@barberia_clasica",
  "@elmaestrobarber",
  "@gentlemenscut_mad",
  "@barberstyle_vlc",
  "@navalhas_bcn",
  "@cortes_premium",
  "@lanavaja_bcn",
  "@mastercut_mad",
];

export default function BarberTicker() {
  if (!BARBER_HANDLES.length) return null;
  const items = [...BARBER_HANDLES, ...BARBER_HANDLES];
  return (
    <div className="marquee-root" aria-label="Barberías colaboradoras">
      <div className="marquee-track" aria-hidden="true">
        {items.map((h, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center" }}>
            <span className="marquee-handle">{h}</span>
            <span className="marquee-sep">✦</span>
          </span>
        ))}
      </div>
    </div>
  );
}

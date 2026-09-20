import type { Metadata, Viewport } from "next";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "Coche Europa — buscar e inspeccionar coches en Europa",
  description:
    "Busca en todos los portales de coches de Europa a la vez, calcula lo que cuesta de verdad traerlo a Espana y revisalo paso a paso antes de pagar.",
  applicationName: "Coche Europa",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0b0c0e",
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <Nav />
        {children}
        <footer className="wrap no-print" style={{ padding: "48px 18px 40px", color: "var(--dim)", fontSize: 13 }}>
          <div style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 20 }}>
            Coche Europa · Los importes fiscales son orientativos y no sustituyen a una gestoria.
            Todo lo que guardes se queda en tu navegador.
          </div>
        </footer>
      </body>
    </html>
  );
}

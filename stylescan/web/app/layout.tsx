import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import BarberTicker from "@/components/BarberTicker";
import CookieBanner from "@/components/CookieBanner";

const jakartaSans = Plus_Jakarta_Sans({
  weight: ["400", "500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VISAI — Tu corte ideal con IA",
  description: "Análisis facial profesional con visagismo. 3 cortes personalizados para tu forma de cara.",
  applicationName: "VISAI",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#080808",
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={jakartaSans.variable}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap" rel="stylesheet" />
      </head>
      <body className={jakartaSans.className}>
        <BarberTicker />
        {children}
        <CookieBanner />
        <footer className="legal-footer">
          <div>VISAI &nbsp;·&nbsp; Análisis facial con IA</div>
          <div>
            <a href="/aviso-legal">Aviso Legal</a>
            &nbsp;·&nbsp;
            <a href="/privacidad">Privacidad</a>
            &nbsp;·&nbsp;
            <a href="/cookies">Cookies</a>
            &nbsp;·&nbsp;
            <a href="/terminos">Términos</a>
            &nbsp;·&nbsp;
            <a href="/reembolso">Reembolsos</a>
          </div>
          <div>
            <a href="mailto:privacy@visai.es">privacy@visai.es</a>
            &nbsp;·&nbsp; Responsable: VISAI
          </div>
        </footer>
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { IBM_Plex_Sans, DM_Serif_Display } from "next/font/google";
import "./globals.css";
import BarberTicker from "@/components/BarberTicker";
import CookieBanner from "@/components/CookieBanner";

const ibmPlexSans = IBM_Plex_Sans({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-logo",
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
  themeColor: "#000000",
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${ibmPlexSans.variable} ${dmSerifDisplay.variable}`}>
      <head />
      <body className={ibmPlexSans.className}>
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
            <a href="mailto:privacy@visaiapp.com">privacy@visaiapp.com</a>
            &nbsp;·&nbsp; Responsable: VISAI
          </div>
        </footer>
      </body>
    </html>
  );
}

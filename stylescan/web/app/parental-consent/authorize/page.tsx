"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, AlertCircle, Clock, ArrowLeft } from "lucide-react";
import Link from "next/link";

type ConsentStatus = "loading" | "authorized" | "expired" | "error";

export default function ParentalConsentAuthorizePage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<ConsentStatus>("loading");
  const [error, setError] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  useEffect(() => {
    const authorize = async () => {
      if (!token) {
        setStatus("error");
        setError("No authorization token provided");
        return;
      }

      try {
        const { api } = await import("@/lib/api");
        const response = await api.authorizeParentalConsent(token);

        // Check response status
        if (response.status === "authorized") {
          setStatus("authorized");
          const now = new Date();
          now.setHours(now.getHours() + 72);
          setExpiresAt(now.toLocaleDateString("es-ES"));
        } else if (response.status === "expired") {
          setStatus("expired");
          setError("El link de autorización ha expirado. Solicita uno nuevo.");
        } else {
          setStatus("error");
          setError("Error procesando la autorización. Intenta de nuevo.");
        }
      } catch (err: any) {
        const message = err.message || "Error desconocido";
        if (message.includes("expired") || message.includes("expirado")) {
          setStatus("expired");
          setError("El link de autorización ha expirado. Solicita uno nuevo.");
        } else {
          setStatus("error");
          setError(message || "Error procesando la autorización. Intenta de nuevo.");
        }
        console.error(err);
      }
    };

    authorize();
  }, [token]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {status === "loading" && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
            <div className="animate-spin mb-4">
              <div className="h-12 w-12 border-4 border-gold border-t-transparent rounded-full mx-auto" />
            </div>
            <h1 className="text-white font-bold text-lg mb-2">
              Procesando autorización...
            </h1>
            <p className="text-gray-400">Por favor espera un momento</p>
          </div>
        )}

        {status === "authorized" && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
            <div className="mb-4 flex justify-center">
              <CheckCircle2 className="h-16 w-16 text-green-500" />
            </div>
            <h1 className="text-white font-bold text-2xl mb-2">
              ¡Autorización Confirmada!
            </h1>
            <p className="text-gray-400 mb-6">
              Has autorizado el análisis facial de tu hijo/a. VISAI ha recibido tu
              consentimiento.
            </p>

            <div className="bg-gray-800 rounded-lg p-4 mb-6 text-left">
              <h3 className="text-white font-semibold mb-3">Próximos pasos:</h3>
              <ul className="text-gray-300 text-sm space-y-2">
                <li className="flex gap-2">
                  <span className="text-gold">✓</span>
                  Tu hijo/a puede continuar con el análisis
                </li>
                <li className="flex gap-2">
                  <span className="text-gold">✓</span>
                  Recibirá recomendaciones personalizadas de cortes
                </li>
                <li className="flex gap-2">
                  <span className="text-gold">✓</span>
                  Sus datos biométricos se eliminan en 90 días
                </li>
              </ul>
            </div>

            <div className="bg-blue-900/30 border border-blue-700/50 rounded p-4 mb-6">
              <p className="text-blue-200 text-xs">
                <strong>Nota:</strong> Esta autorización es válida hasta{" "}
                <strong>{expiresAt}</strong>. Si necesitas revocar el consentimiento,
                contacta a legal@visaiapp.com
              </p>
            </div>

            <Link href="/">
              <button className="w-full bg-gold hover:bg-gold/90 text-black font-bold py-2 rounded transition-colors">
                Volver al Inicio
              </button>
            </Link>
          </div>
        )}

        {status === "expired" && (
          <div className="bg-gray-900 border border-orange-600/50 rounded-lg p-8 text-center">
            <div className="mb-4 flex justify-center">
              <Clock className="h-16 w-16 text-orange-500" />
            </div>
            <h1 className="text-white font-bold text-2xl mb-2">Link Expirado</h1>
            <p className="text-gray-400 mb-6">
              El link de autorización ha expirado (válido 72 horas).
            </p>

            <div className="bg-orange-900/30 border border-orange-700/50 rounded p-4 mb-6">
              <p className="text-orange-200 text-sm">
                Solicita un nuevo link de autorización. Tu hijo/a puede reintentar el
                análisis y recibirá un nuevo email.
              </p>
            </div>

            <Link href="/">
              <button className="w-full bg-gold hover:bg-gold/90 text-black font-bold py-2 rounded transition-colors">
                Ir al Análisis
              </button>
            </Link>
          </div>
        )}

        {status === "error" && (
          <div className="bg-gray-900 border border-red-600/50 rounded-lg p-8 text-center">
            <div className="mb-4 flex justify-center">
              <AlertCircle className="h-16 w-16 text-red-500" />
            </div>
            <h1 className="text-white font-bold text-2xl mb-2">Error</h1>
            <p className="text-gray-400 mb-6">{error}</p>

            <Link href="/">
              <button className="w-full bg-gold hover:bg-gold/90 text-black font-bold py-2 rounded transition-colors">
                Volver al Inicio
              </button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

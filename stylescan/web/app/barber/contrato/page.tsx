"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ChevronLeft, CheckCircle2, FileText, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

const ARTICLES = [
  {
    title: "Art. 1 — Objeto del contrato",
    body: `El presente Contrato regula la relación de colaboración no laboral entre VISAI y el Barbero Partner, consistente en:

a) La participación en el Programa Barbero Partner mediante un código de descuento personal e intransferible.
b) La aportación voluntaria de fotografías de referencia para enriquecer el catálogo visual de la plataforma.
c) La percepción de comisiones económicas por cada análisis pagado generado a través del código.

La relación tiene carácter mercantil independiente. No existe relación laboral, de agencia ni representación entre las partes.`,
  },
  {
    title: "Art. 2 — Código de descuento y uso",
    body: `VISAI asignará al Barbero Partner un código único y personalizado (p. ej., NOMBRE-VISAI) que permite a los clientes obtener un descuento de 2 € en el análisis.

El Barbero Partner se compromete a usar el Código solo para fines lícitos, sin publicidad engañosa, spam ni prácticas contrarias a la normativa de competencia desleal. Queda prohibida la cesión o comercialización del Código a terceros.

VISAI puede desactivar el Código si detecta uso contrario a lo estipulado.`,
  },
  {
    title: "Art. 3 — Fotos de referencia (RGPD)",
    body: `El Barbero Partner garantiza que, antes de subir cualquier fotografía en la que aparezca una persona identificable, ha obtenido el consentimiento explícito, libre, informado y documentado de dicha persona para su captura, almacenamiento y uso por VISAI.

El Barbero Partner conservará los registros de consentimiento durante mínimo 3 años y los proporcionará a VISAI en 48 horas si se requieren.

INDEMNIZACIÓN: si cualquier persona fotografiada ejercita acciones legales contra VISAI, el Barbero Partner asumirá íntegramente la responsabilidad e indemnizará a VISAI por todos los daños y costas derivados.

El Barbero Partner concede a VISAI una licencia no exclusiva, gratuita y revocable para usar las fotografías en el servicio de visualización. Esta licencia puede revocarse en cualquier momento mediante solicitud escrita.`,
  },
  {
    title: "Art. 4 — Emails de clientes (RGPD)",
    body: `Si el Barbero Partner facilita emails de clientes, declara que dichos clientes han otorgado consentimiento previo y explícito para recibir comunicaciones de VISAI.

VISAI enviará un correo de bienvenida en el primer contacto identificando la fuente e informando del derecho de baja (Art. 21 LSSI-CE / RGPD). El Barbero Partner no puede facilitar emails obtenidos sin consentimiento expreso.`,
  },
  {
    title: "Art. 5 — Menores de edad",
    body: `El servicio está dirigido exclusivamente a mayores de 18 años.

PROHIBICIÓN EXPRESA: el Barbero Partner no puede facilitar, promover ni permitir el uso del Código por menores de 18 años, ni subir fotografías en las que aparezcan menores.

En caso de incumplimiento, el Barbero Partner asume la responsabilidad exclusiva e íntegra frente a los menores afectados, sus representantes legales, las autoridades y frente a VISAI. VISAI queda completamente exonerada.`,
  },
  {
    title: "Art. 7 — Comisiones y pagos",
    body: `VISAI abonará 2,00 € por cada análisis pagado y completado mediante el Código del Barbero Partner.

Las comisiones se liquidan mensualmente dentro de los primeros 15 días naturales del mes siguiente, via transferencia SEPA al IBAN facilitado. No se realizan transferencias inferiores a 10 €; el importe se acumula al siguiente período.

VISAI puede retener comisiones si existen reclamaciones en curso, procedimientos judiciales o sospecha de fraude. Los ingresos son rendimientos de actividad económica: el Barbero Partner es responsable de sus obligaciones fiscales ante la AEAT.`,
  },
  {
    title: "Art. 8 — Confidencialidad (NDA)",
    body: `El Barbero Partner se obliga a mantener en estricta confidencialidad toda información técnica, comercial o de negocio de VISAI: metodología de análisis, algoritmos, prompts, bases de datos, precios internos y estrategias comerciales.

Esta obligación permanece vigente durante el Contrato y 3 años tras su extinción.`,
  },
  {
    title: "Art. 9 — Propiedad intelectual",
    body: `VISAI es titular exclusivo de todos los derechos sobre la plataforma, tecnología de análisis, algoritmos, modelos de IA, diseño, software y marcas. Los informes generados son propiedad de VISAI.

El Barbero Partner no puede reproducir, distribuir, comercializar, transformar ni usar los informes para entrenar modelos propios de IA.`,
  },
  {
    title: "Art. 10 — Duración y resolución",
    body: `El Contrato es indefinido. Cualquiera de las partes puede resolverlo con 30 días de preaviso por escrito.

VISAI puede resolver inmediatamente si el Barbero Partner: incumple obligaciones esenciales (Arts. 3, 4, 5), usa el Código de forma fraudulenta, o causa daño reputacional grave a VISAI. Las comisiones devengadas se abonan en el siguiente ciclo salvo causa justificada de retención.`,
  },
  {
    title: "Art. 11 — Protección de datos",
    body: `VISAI actúa como responsable del tratamiento de datos de los clientes finales conforme al RGPD y la LOPDGDD. El Barbero Partner actúa como introductor de contactos, no como encargado del tratamiento (Art. 28 RGPD).

Los datos del Barbero Partner (nombre, IBAN, NIF, email) se tratan para gestionar el Contrato y liquidar comisiones, con base en el Art. 6.1.b RGPD. Se conservan durante la vigencia del Contrato y hasta 5 años tras su extinción.`,
  },
  {
    title: "Art. 15 — Aceptación electrónica",
    body: `Este Contrato se formaliza mediante aceptación electrónica. El clic en "Acepto el contrato" tiene plena validez jurídica conforme al Art. 23 LSSI-CE, con los mismos efectos que la firma manuscrita.

VISAI registra y conserva como prueba: timestamp UTC, dirección IP, user-agent y versión del contrato aceptada.`,
  },
  {
    title: "Art. 14 — Ley aplicable y jurisdicción",
    body: `El presente Contrato se rige por el Derecho español. Para cualquier controversia, las partes se someten a los Juzgados y Tribunales del domicilio de VISAI, con renuncia a cualquier otro fuero.`,
  },
];

function ContratoInner() {
  const params = useSearchParams();
  const router = useRouter();
  const barberId = params.get("id") || "";

  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function handleSign() {
    if (!accepted || !barberId) return;
    setLoading(true);
    setError("");
    try {
      await api.signBarberContract(barberId);
      setDone(true);
      setTimeout(() => router.push(`/barber/dashboard?id=${barberId}`), 2000);
    } catch (e: any) {
      setError(e.message || "Error al registrar la firma. Inténtalo de nuevo.");
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center px-6">
          <CheckCircle2 className="h-16 w-16 text-green-400 mx-auto mb-4" />
          <h2 className="text-white text-2xl font-bold mb-2">Contrato firmado</h2>
          <p className="text-gray-400">Redirigiendo a tu panel…</p>
        </div>
      </div>
    );
  }

  if (!barberId) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center px-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-white">Acceso no válido. Usa el enlace que te enviamos.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gradient-to-b from-gray-900 to-black sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-white transition-colors">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <FileText className="h-5 w-5 text-gold" />
          <div>
            <h1 className="text-white font-bold text-base leading-tight">Contrato de Colaboración</h1>
            <p className="text-gray-500 text-xs">Programa Barbero Partner VISAI · v1.0</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Intro */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 mb-6">
          <p className="text-gray-300 text-sm leading-relaxed">
            Lee el contrato completo antes de firmar. Al aceptar, declaras haber leído y comprendido todos los términos.
            La aceptación electrónica tiene plena validez legal (Art. 23 LSSI-CE).
          </p>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500">
            <span>Ley española</span>
            <span>·</span>
            <span>RGPD compatible</span>
            <span>·</span>
            <span>Firma con validez legal</span>
          </div>
        </div>

        {/* Articles */}
        <div className="space-y-3 mb-8">
          {ARTICLES.map((article, i) => (
            <ArticleBlock key={i} title={article.title} body={article.body} />
          ))}
        </div>

        {/* Accept + Sign */}
        <div className="sticky bottom-0 bg-black border-t border-gray-800 pt-4 pb-6 -mx-4 px-4">
          <button
            type="button"
            onClick={() => setAccepted(!accepted)}
            className="flex items-start gap-3 w-full text-left mb-4 group"
          >
            <div className={`mt-0.5 w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center transition-colors ${
              accepted ? "bg-gold border-gold" : "border-gray-600 group-hover:border-gray-400"
            }`}>
              {accepted && <span className="text-black text-xs font-black leading-none">✓</span>}
            </div>
            <span className="text-sm text-gray-300 leading-relaxed">
              He leído y acepto íntegramente el Contrato de Colaboración con VISAI en toda su extensión, incluyendo
              las obligaciones respecto a consentimiento de fotografías, protección de menores y confidencialidad.
            </span>
          </button>

          {error && (
            <p className="text-red-400 text-sm mb-3 text-center">{error}</p>
          )}

          <button
            type="button"
            onClick={handleSign}
            disabled={!accepted || loading}
            className={`w-full py-4 rounded-lg font-bold text-base transition-all ${
              accepted && !loading
                ? "bg-gold text-black hover:bg-gold/90 cursor-pointer"
                : "bg-gray-800 text-gray-600 cursor-not-allowed"
            }`}
          >
            {loading ? "Firmando…" : "Acepto el contrato — Activar mi código"}
          </button>

          <p className="text-xs text-gray-600 text-center mt-3">
            Se registran: timestamp UTC · IP · versión del contrato
          </p>
        </div>
      </div>
    </div>
  );
}

function ArticleBlock({ title, body }: { title: string; body: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-800/50 transition-colors"
      >
        <span className="text-white font-semibold text-sm">{title}</span>
        <span className={`text-gray-500 text-lg transition-transform ${open ? "rotate-90" : ""}`}>›</span>
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-gray-800">
          <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-line pt-3">{body}</p>
        </div>
      )}
    </div>
  );
}

export default function ContratoPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="h-8 w-8 border-4 border-gold border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ContratoInner />
    </Suspense>
  );
}

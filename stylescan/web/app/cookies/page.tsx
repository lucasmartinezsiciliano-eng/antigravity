"use client";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";

function RevokeButton() {
  function revoke() {
    localStorage.removeItem("visai_cookie_consent");
    window.location.reload();
  }
  return (
    <button
      type="button"
      onClick={revoke}
      style={{
        padding: "10px 18px", borderRadius: "var(--r-md)",
        background: "transparent", border: "1px solid var(--border)",
        fontSize: 13, fontWeight: 600, color: "var(--text-muted)",
      }}
    >
      Retirar consentimiento
    </button>
  );
}

export default function CookiesPage() {
  const router = useRouter();

  return (
    <div className="screen" style={{ gap: 0 }}>

      {/* Back */}
      <div style={{ marginBottom: 28 }}>
        <button type="button" className="back-btn" onClick={() => router.back()} aria-label="Volver">
          <ChevronLeft size={20} strokeWidth={2} />
        </button>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <p className="label" style={{ marginBottom: 10 }}>LSSI + ePrivacy</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", lineHeight: 1.2 }}>
          Politica de Cookies
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          Actualizado el 6 de mayo de 2026
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 28, paddingBottom: 48 }}>

        {/* 1. Qué son */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>1. Que son las cookies</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Las cookies son pequenos archivos de texto que los sitios web depositan en el dispositivo del usuario.
              La normativa aplicable es la Ley 34/2002 de Servicios de la Sociedad de la Informacion (LSSI-CE) y la
              Directiva 2002/58/CE (ePrivacy), que exigen informacion clara y, en el caso de cookies no esenciales,
              consentimiento previo del usuario.
            </p>
          </div>
        </section>

        {/* 2. VISAI usa localStorage, no cookies propias */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>2. Almacenamiento local en VISAI</p>
          <div className="card" style={{
            borderColor: "rgba(232,232,232,0.12)",
            background: "var(--accent-glow)",
          }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 8px" }}>
              VISAI no instala cookies propias de rastreo, analitica ni publicidad.
            </p>
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              El estado de la sesion (resultado del analisis, preferencias del usuario, registro del consentimiento)
              se guarda exclusivamente mediante la API <code style={{ fontFamily: "monospace", fontSize: 13 }}>localStorage</code> del
              navegador, que almacena datos localmente en tu dispositivo sin transmitirlos a terceros ni tener fecha
              de expiracion controlada por el servidor. Puedes borrar estos datos en cualquier momento desde la
              configuracion de tu navegador (ver seccion 5).
            </p>
          </div>
        </section>

        {/* 3. Cookies de terceros */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>3. Cookies de terceros</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>

            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <p style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", margin: 0 }}>Stripe</p>
                <span style={{
                  fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
                  background: "var(--surface2)", color: "var(--text-muted)",
                  padding: "2px 8px", borderRadius: "var(--r-full)",
                }}>
                  Estrictamente necesaria
                </span>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.65, margin: "0 0 8px" }}>
                Al acceder a la pantalla de pago, Stripe puede instalar una cookie de sesion (
                <code style={{ fontFamily: "monospace" }}>__stripe_mid</code>,{" "}
                <code style={{ fontFamily: "monospace" }}>__stripe_sid</code>) para detectar fraude, gestionar la
                sesion de pago segura y cumplir la normativa PCI-DSS. Estas cookies son necesarias para completar
                la transaccion y no requieren consentimiento previo en virtud de su caracter estrictamente tecnico.
              </p>
              <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 6px" }}>
                Duracion: sesion (se eliminan al cerrar el navegador) + hasta 1 ano para cookies de fraude.
              </p>
              <a
                href="https://stripe.com/es/cookie-settings"
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "underline" }}
              >
                Politica de cookies de Stripe
              </a>
            </div>

          </div>

          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, marginTop: 12 }}>
            VISAI no utiliza cookies de Google Analytics, Facebook Pixel, ni ninguna otra herramienta de analitica
            o publicidad comportamental.
          </p>
        </section>

        {/* 4. Tabla resumen */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>4. Tabla resumen</p>
          <div className="card" style={{ overflowX: "auto", padding: 0 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Nombre", "Proveedor", "Tipo", "Duracion"].map((h) => (
                    <th key={h} style={{
                      padding: "12px 14px", textAlign: "left",
                      color: "var(--text-muted)", fontWeight: 700,
                      fontSize: 11, letterSpacing: "0.07em", textTransform: "uppercase",
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["visai_cookie_consent", "VISAI", "Tecnica / Preferencia", "Hasta borrado manual"],
                  ["visai_*", "VISAI", "Tecnica / Sesion analisis", "Hasta borrado manual"],
                  ["__stripe_mid", "Stripe", "Necesaria / Fraude", "Hasta 1 ano"],
                  ["__stripe_sid", "Stripe", "Necesaria / Sesion", "Sesion"],
                ].map(([name, provider, type, duration], i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "11px 14px", color: "var(--text)", fontFamily: "monospace", fontSize: 12 }}>{name}</td>
                    <td style={{ padding: "11px 14px", color: "var(--text-muted)" }}>{provider}</td>
                    <td style={{ padding: "11px 14px", color: "var(--text-muted)" }}>{type}</td>
                    <td style={{ padding: "11px 14px", color: "var(--text-muted)" }}>{duration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 5. Como gestionar */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>5. Como gestionar y eliminar las cookies</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 14px" }}>
              Puedes eliminar las cookies instaladas por Stripe y los datos de localStorage en cualquier momento
              desde la configuracion de tu navegador. A continuacion te indicamos como acceder a esa opcion en
              los navegadores mas comunes:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                ["Chrome / Chromium", "Ajustes > Privacidad y seguridad > Borrar datos de navegacion > Cookies y otros datos de sitios"],
                ["Firefox", "Ajustes > Privacidad y seguridad > Cookies y datos del sitio > Limpiar datos"],
                ["Safari (iOS)", "Ajustes > Safari > Borrar historial y datos de sitios web"],
                ["Samsung Internet", "Menu > Ajustes > Privacidad > Borrar datos de navegacion"],
              ].map(([browser, path]) => (
                <div key={browser} style={{ paddingBottom: 10, borderBottom: "1px solid var(--border)" }}>
                  <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", margin: "0 0 2px" }}>{browser}</p>
                  <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5, margin: 0 }}>{path}</p>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.65, marginTop: 12 }}>
              Ten en cuenta que deshabilitar las cookies de Stripe puede impedir la finalizacion del proceso de
              pago. La eliminacion del localStorage borrara el resultado de tu analisis guardado localmente.
            </p>
          </div>
        </section>

        {/* 6. Cambiar preferencias */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>6. Cambiar tus preferencias</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 14px" }}>
              Puedes retirar o modificar tu consentimiento en cualquier momento borrando la clave{" "}
              <code style={{ fontFamily: "monospace", fontSize: 13 }}>visai_cookie_consent</code> de tu localStorage.
              Al recargar la pagina, el banner de cookies volvera a aparecer.
            </p>
            <RevokeButton />
          </div>
        </section>

        {/* 7. Contacto */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>7. Contacto</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Para cualquier consulta sobre esta politica, puedes contactarnos en{" "}
              <a href="mailto:privacy@visai.es" style={{ color: "var(--text)", textDecoration: "underline" }}>
                privacy@visai.es
              </a>
              .
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}

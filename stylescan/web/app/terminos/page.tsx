"use client";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";

export default function TerminosPage() {
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
        <p className="label" style={{ marginBottom: 10 }}>Condiciones del servicio</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", lineHeight: 1.2 }}>
          Terminos y Condiciones
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          Actualizado el 6 de mayo de 2026
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 28, paddingBottom: 48 }}>

        {/* 1. Aceptación */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>1. Aceptacion de los terminos</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              El acceso y uso de la plataforma VISAI implica la aceptacion expresa, plena y sin reservas de los
              presentes Terminos y Condiciones. Si no estas de acuerdo con alguna de las condiciones aqui recogidas,
              debes abstenerte de utilizar el servicio. VISAI se reserva el derecho a modificar estos terminos en
              cualquier momento, notificando los cambios sustanciales en la aplicacion.
            </p>
          </div>
        </section>

        {/* 2. Descripción del servicio */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>2. Descripcion del servicio</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 12px" }}>
              VISAI es una aplicacion de analisis facial por inteligencia artificial dirigida al sector de la
              barberia y peluqueria. El servicio consiste en:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                "Captura de una fotografia facial del usuario.",
                "Procesamiento mediante IA para identificar la morfologia craneal y proporciones faciales.",
                "Generacion de un informe orientativo con recomendaciones de corte de cabello y barba adaptadas.",
                "Entrega del informe de forma digital inmediata tras el pago.",
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: "var(--text-muted)",
                    background: "var(--surface2)", borderRadius: "var(--r-full)",
                    padding: "2px 8px", flexShrink: 0, marginTop: 2,
                  }}>
                    {i + 1}
                  </span>
                  <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.65, margin: 0 }}>{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 3. Requisitos del usuario */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>3. Requisitos del usuario</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Requirement
                title="Edad minima: 18 anos"
                text="El uso de VISAI esta restringido a personas mayores de 18 anos. El tratamiento de datos biometricos de menores esta expresamente prohibido. Al aceptar estos terminos, el usuario declara y garantiza ser mayor de edad."
              />
              <Requirement
                title="Uso personal"
                text="El servicio esta concebido para uso personal del usuario final. No esta permitido el uso automatizado, masivo o con fines de reventa sin autorizacion escrita previa de VISAI."
              />
              <Requirement
                title="Imagen propia"
                text="El usuario debe fotografiarse a si mismo. Queda expresamente prohibido subir imagenes de terceros sin su consentimiento expreso. VISAI no asume ninguna responsabilidad por el uso fraudulento de imagenes ajenas."
              />
            </div>
          </div>
        </section>

        {/* 4. Carácter orientativo */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>4. Caracter orientativo del analisis</p>
          <div className="card" style={{
            borderColor: "rgba(232,232,232,0.12)",
            background: "var(--accent-glow)",
          }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 8px" }}>
              El informe de VISAI es ORIENTATIVO, no un diagnostico profesional.
            </p>
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Los resultados del analisis facial generados por VISAI constituyen recomendaciones esteticas
              orientativas basadas en proporciones y tendencias del sector de la barberia. No tienen la consideracion
              de asesoramiento medico, dermatologico ni de ninguna actividad sanitaria regulada. Las recomendaciones
              estan sujetas a la interpretacion profesional del barbero o estilista, cuyo criterio debe primar en
              todo momento. VISAI no se hace responsable del resultado final del corte ni de la insatisfaccion estetica
              derivada de seguir las recomendaciones del informe.
            </p>
          </div>
        </section>

        {/* 5. Precio y pago */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>5. Precio y condiciones de pago</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              El precio del servicio es el indicado en la pantalla de pago en el momento de la compra, con el IVA
              incluido. El pago se realiza de forma segura a traves de Stripe. La compra da derecho a la entrega
              inmediata del informe digital. Consulta la{" "}
              <a href="/reembolso" style={{ color: "var(--text)", textDecoration: "underline" }}>
                Politica de Reembolso
              </a>{" "}
              para conocer las condiciones de desistimiento y devolucion.
            </p>
          </div>
        </section>

        {/* 6. Propiedad intelectual */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>6. Propiedad intelectual</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Todos los derechos de propiedad intelectual e industrial sobre la plataforma VISAI — incluyendo el
              software, los modelos de IA, los algoritmos de analisis facial, el diseno visual, los textos y el
              informe generado como obra derivada de los modelos de VISAI — son titularidad exclusiva de VISAI o de
              sus licenciantes. Se concede al usuario una licencia de uso personal, no exclusiva, intransferible y
              revocable del informe para su uso privado. Queda prohibida cualquier reproduccion, distribucion,
              ingenieria inversa o explotacion comercial sin autorizacion.
            </p>
          </div>
        </section>

        {/* 7. Conducta prohibida */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>7. Usos prohibidos</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                "Intentar vulnerar, eludir o comprometer los sistemas de seguridad de VISAI.",
                "Usar scrapers, bots o medios automatizados para acceder al servicio.",
                "Subir imagenes que contengan desnudos, violencia o cualquier contenido ilegal.",
                "Suplantar la identidad de terceros o usar imagenes de personas sin su consentimiento.",
                "Revender, sublicenciar o distribuir los informes generados con fines comerciales.",
                "Realizar ingenieria inversa sobre los modelos de IA o el codigo de la plataforma.",
              ].map((item, i) => (
                <div key={i} style={{
                  display: "flex", gap: 12, alignItems: "flex-start",
                  paddingBottom: 8, borderBottom: "1px solid var(--border)",
                }}>
                  <span style={{
                    width: 6, height: 6, borderRadius: "50%",
                    background: "var(--text-muted)", flexShrink: 0, marginTop: 6,
                  }} />
                  <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 8. Limitación de responsabilidad */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>8. Limitacion de responsabilidad</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              En la maxima medida permitida por la legislacion aplicable, VISAI no sera responsable de daños
              indirectos, incidentales, especiales, consecuentes o ejemplares, incluyendo la perdida de beneficios,
              datos o fondo de comercio, derivados del uso o imposibilidad de uso del servicio. La responsabilidad
              total de VISAI frente al usuario, por cualquier causa y con independencia de la forma de la accion,
              estara en todo caso limitada al importe abonado por el usuario en la transaccion que origino el
              perjuicio. Esta limitacion no afecta a los derechos que la normativa de consumidores reconoce con
              caracter imperativo.
            </p>
          </div>
        </section>

        {/* 9. Ley aplicable */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>9. Legislacion aplicable y jurisdiccion</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Los presentes Terminos y Condiciones se rigen por la legislacion española. Las partes se someten a los
              Juzgados y Tribunales del domicilio del usuario consumidor (segun art. 52.3 LEC) para la resolucion de
              cualquier conflicto derivado de la interpretacion o ejecucion del presente contrato.
            </p>
          </div>
        </section>

        {/* 10. Contacto */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>10. Contacto</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              Para cualquier consulta relativa a estos Terminos, contacta con nosotros en{" "}
              <a href="mailto:info@visai.es" style={{ color: "var(--text)", textDecoration: "underline" }}>
                info@visai.es
              </a>
              .
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}

function Requirement({ title, text }: { title: string; text: string }) {
  return (
    <div style={{ paddingBottom: 10, borderBottom: "1px solid var(--border)" }}>
      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 4px" }}>{title}</p>
      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>{text}</p>
    </div>
  );
}

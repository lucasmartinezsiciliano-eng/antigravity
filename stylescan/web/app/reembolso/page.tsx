"use client";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";

export default function ReembolsoPage() {
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
        <p className="label" style={{ marginBottom: 10 }}>LGDCU Art. 103.m</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", lineHeight: 1.2 }}>
          Politica de Reembolso
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          Actualizado el 6 de mayo de 2026
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 28, paddingBottom: 48 }}>

        {/* Resumen destacado */}
        <div className="card" style={{
          borderColor: "rgba(232,232,232,0.12)",
          background: "var(--accent-glow)",
        }}>
          <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 8px" }}>
            Resumen: contenido digital de entrega inmediata
          </p>
          <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
            El informe de VISAI es contenido digital que se genera y entrega de forma inmediata tras el pago.
            Al completar la compra, el usuario consiente expresamente la entrega inmediata y reconoce que, una vez
            entregado el informe, pierde el derecho de desistimiento de 14 dias previsto en el TRLGDCU.
          </p>
        </div>

        {/* 1. Derecho de desistimiento */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>1. Derecho de desistimiento y excepcion aplicable</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              El articulo 103.m del Real Decreto Legislativo 1/2007 (Texto Refundido de la Ley General para la
              Defensa de los Consumidores y Usuarios, TRLGDCU) establece que el derecho de desistimiento NO es
              aplicable a los contratos de suministro de contenido digital que no se preste en soporte material,
              cuando la ejecucion haya comenzado con el previo consentimiento expreso del consumidor y con el
              reconocimiento por su parte de que, en consecuencia, pierde su derecho de desistimiento.
            </p>
            <div style={{
              marginTop: 16, padding: "14px 16px",
              background: "var(--surface2)", borderRadius: "var(--r-md)",
            }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", margin: "0 0 6px" }}>
                Condicion que el usuario acepta expresamente al comprar:
              </p>
              <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: 0, fontStyle: "italic" }}>
                "Consiento que VISAI comience la ejecucion del servicio de forma inmediata y reconozco que, al
                iniciarse la entrega del contenido digital, pierdo mi derecho de desistimiento de 14 dias
                conforme al art. 103.m TRLGDCU."
              </p>
            </div>
          </div>
        </section>

        {/* 2. Cuándo no hay reembolso */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>2. Cuando no procede el reembolso</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                ["Informe entregado correctamente", "Una vez generado y mostrado el informe de analisis facial, la prestacion del servicio se considera completada y no procede reembolso por cambio de opinion."],
                ["Insatisfaccion con el resultado estetico", "El informe es orientativo. La discrepancia entre las recomendaciones y las preferencias personales del usuario no constituye un defecto del servicio."],
                ["Error del usuario al fotografiarse", "El resultado adverso derivado de una imagen de baja calidad, iluminacion deficiente o posicion incorrecta es responsabilidad del usuario."],
              ].map(([title, text]) => (
                <div key={title as string} style={{ paddingBottom: 10, borderBottom: "1px solid var(--border)" }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 4px" }}>{title}</p>
                  <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 3. Cuando sí hay reembolso / solución */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>3. Cuando si procede reembolso o solucion</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                ["Error tecnico en la entrega", "Si el informe no se genero correctamente o no pudo mostrarse por un fallo tecnico de VISAI, tienes derecho a la repeticion del servicio o al reembolso completo."],
                ["Cobro duplicado", "Si tu cuenta fue cobrada mas de una vez por el mismo analisis, reembolsaremos el importe duplicado."],
                ["Servicio no iniciado", "Si el pago se proceso pero el analisis no llego a ejecutarse por causas tecnicas ajenas al usuario, procede el reembolso completo."],
              ].map(([title, text]) => (
                <div key={title as string} style={{ paddingBottom: 10, borderBottom: "1px solid var(--border)" }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 4px" }}>{title}</p>
                  <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 4. Proceso de reclamación */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>4. Como tramitar una reclamacion</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 16px" }}>
              Si crees que tu caso esta cubierto por los supuestos del apartado anterior, sigue estos pasos:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                ["Contacta dentro de las 24 horas", "Envia un email a hola@visai.es dentro de las 24 horas siguientes a la compra, indicando el problema experimentado."],
                ["Indica tu referencia de pago", "Incluye el identificador de transaccion que Stripe envia a tu email de pago, o el numero de pedido que aparece en la aplicacion."],
                ["Describe el fallo tecnico", "Adjunta, si es posible, una captura de pantalla del error o del estado en que quedo la aplicacion."],
                ["Plazo de resolucion", "VISAI revisara tu solicitud y respondera en un plazo maximo de 3 dias habiles. Si el reembolso procede, se hara a traves del mismo metodo de pago utilizado en la compra en 5-10 dias habiles."],
              ].map(([step, desc], i) => (
                <div key={i} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                  <span style={{
                    fontSize: 12, fontWeight: 700, color: "var(--text-muted)",
                    background: "var(--surface2)", borderRadius: "var(--r-full)",
                    padding: "3px 9px", flexShrink: 0, marginTop: 1,
                  }}>
                    {i + 1}
                  </span>
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 3px" }}>{step}</p>
                    <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 5. Contacto directo */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>5. Contacto</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 14px" }}>
              Para reclamaciones de reembolso o soporte tecnico relacionado con el pago, escribe a:
            </p>
            <a
              href="mailto:hola@visai.es"
              style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                padding: "14px 20px", borderRadius: "var(--r-full)",
                border: "1px solid var(--border)", background: "var(--surface2)",
                fontSize: 15, fontWeight: 600, color: "var(--text)", textDecoration: "none",
              }}
            >
              hola@visai.es
            </a>
            <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, marginTop: 12 }}>
              Si tu reclamacion no es atendida satisfactoriamente, puedes acudir al sistema de resolucion de
              litigios en linea de la Union Europea en{" "}
              <a
                href="https://ec.europa.eu/consumers/odr"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "var(--text)", textDecoration: "underline" }}
              >
                ec.europa.eu/consumers/odr
              </a>
              .
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}

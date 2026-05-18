"use client";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";

export default function PrivacidadPage() {
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
        <p className="label" style={{ marginBottom: 10 }}>Informacion RGPD Art. 13</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", lineHeight: 1.2 }}>
          Politica de Privacidad
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          Actualizado el 6 de mayo de 2026
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 28, paddingBottom: 48 }}>

        {/* 1. Responsable */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>1. Responsable del tratamiento</p>
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <InfoRow label="Denominacion" value="LUKIMPORTA MEDITERRANEO, S.L." />
            <InfoRow label="NIF" value="B-[COMPLETAR]" />
            <InfoRow label="Domicilio" value="Avenida Roma, 7, 7.o — Tarragona (Cataluna)" />
            <InfoRow label="DPO / Contacto privacidad" value="privacy@visaiapp.com" />
          </div>
        </section>

        {/* 2. Datos que tratamos */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>2. Datos que tratamos</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <DataBlock
              title="Datos biometricos faciales (Art. 9 RGPD)"
              text="Cuando realizas el analisis, tu imagen facial se procesa momentaneamente para extraer metricas numericas (proporciones craneales, distancias entre puntos de referencia). La imagen original NO se almacena. Unicamente conservamos las metricas numericas resultantes. Estos datos son datos de categoria especial conforme al Art. 9 RGPD y solo los tratamos con tu consentimiento explicito previo."
            />
            <DataBlock
              title="Datos de pago"
              text="Los datos de tarjeta de credito/debito son procesados directamente por Stripe. VISAI no almacena, transmite ni tiene acceso en ningun momento al numero de tarjeta, CVV ni fecha de caducidad. Unicamente conservamos la referencia del pago generada por Stripe para justificacion contable."
            />
            <DataBlock
              title="Datos de marketing"
              text="Si has dado tu consentimiento expreso, tratamos tu direccion de correo electronico para enviarte comunicaciones comerciales sobre novedades, tendencias y ofertas de VISAI. Puedes revocar este consentimiento en cualquier momento sin consecuencias."
            />
            <DataBlock
              title="Datos de navegacion"
              text="Recogemos de forma anonima datos tecnicos de uso (tipo de dispositivo, sistema operativo, idioma, resolucion de pantalla) con fines de mejora tecnica del servicio. No utilizamos cookies de rastreo ni publicidad comportamental."
            />
          </div>
        </section>

        {/* 3. Base jurídica */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>3. Base juridica del tratamiento</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <LegalBasis
                type="Consentimiento (Art. 6.1.a + Art. 9.2.a RGPD)"
                text="Datos biometricos faciales y comunicaciones de marketing. Puedes retirar tu consentimiento en cualquier momento sin que ello afecte a la licitud del tratamiento previo."
              />
              <LegalBasis
                type="Ejecucion de contrato (Art. 6.1.b RGPD)"
                text="Procesamiento del pago y entrega del informe de analisis."
              />
              <LegalBasis
                type="Interes legitimo (Art. 6.1.f RGPD)"
                text="Mejora tecnica del servicio mediante datos de navegacion anonimos y prevencion del fraude."
              />
              <LegalBasis
                type="Obligacion legal (Art. 6.1.c RGPD)"
                text="Conservacion de registros de transacciones economicas conforme a la Ley 58/2003 General Tributaria."
              />
            </div>
          </div>
        </section>

        {/* 4. Plazos de conservación */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>4. Plazos de conservacion</p>
          <div className="card">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <RetentionRow category="Metricas biometricas faciales" period="90 dias desde el analisis" />
              <RetentionRow category="Registros de consentimiento" period="5 anos (exigencia legal LOPDGDD)" />
              <RetentionRow category="Correo de marketing" period="3 anos desde el ultimo consentimiento, o hasta baja" />
              <RetentionRow category="Datos de pago (referencia Stripe)" period="5 anos (obligacion contable)" />
            </div>
          </div>
        </section>

        {/* 5. Encargados de tratamiento */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>5. Encargados del tratamiento y transferencias internacionales</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <ProcessorBlock
              name="Stripe, Inc."
              role="Procesador de pagos"
              location="EE.UU."
              transfer="Clausulas Contractuales Estandar (SCC) de la Comision Europea"
              url="https://stripe.com/es/privacy"
            />
            <ProcessorBlock
              name="OpenRouter, Inc."
              role="Enrutamiento de modelos de IA para generacion del informe"
              location="EE.UU."
              transfer="Clausulas Contractuales Estandar (SCC)"
              url="https://openrouter.ai/privacy"
            />
            <ProcessorBlock
              name="fal.ai, Inc."
              role="Procesamiento de imagen e inferencia del modelo de analisis facial"
              location="EE.UU."
              transfer="Clausulas Contractuales Estandar (SCC)"
              url="https://fal.ai/privacy"
            />
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, marginTop: 12 }}>
            Todos los encargados han firmado el correspondiente contrato de encargo del tratamiento (DPA) y ofrecen
            garantias suficientes para el cumplimiento del RGPD. No se realizan otras transferencias internacionales
            de datos fuera de las indicadas.
          </p>
        </section>

        {/* 6. Derechos */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>6. Tus derechos</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.65, margin: "0 0 14px" }}>
              Conforme al RGPD (Arts. 15-22), puedes ejercer los siguientes derechos enviando un email a{" "}
              <a href="mailto:privacy@visaiapp.com" style={{ color: "var(--text)", textDecoration: "underline" }}>
                privacy@visaiapp.com
              </a>{" "}
              con copia de tu documento de identidad:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                ["Acceso (Art. 15)", "Obtener confirmacion de si tratamos tus datos y recibir una copia."],
                ["Rectificacion (Art. 16)", "Corregir datos inexactos o completar datos incompletos."],
                ["Supresion (Art. 17)", "Solicitar el borrado de tus datos cuando ya no sean necesarios."],
                ["Portabilidad (Art. 20)", "Recibir tus datos en formato estructurado y de uso comun."],
                ["Oposicion (Art. 21)", "Oponerte al tratamiento basado en interes legitimo."],
                ["Limitacion (Art. 18)", "Solicitar la suspension temporal del tratamiento en ciertos supuestos."],
                ["Retirada del consentimiento", "En cualquier momento para los tratamientos basados en consentimiento, sin efecto retroactivo."],
              ].map(([right, desc]) => (
                <div key={right} style={{
                  paddingBottom: 10, borderBottom: "1px solid var(--border)",
                }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 2px" }}>{right}</p>
                  <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>{desc}</p>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, margin: "14px 0 0" }}>
              Atenderemos tu solicitud en el plazo maximo de un mes (prorrogable dos meses adicionales en casos
              complejos). Si no obtienes respuesta satisfactoria, puedes reclamar ante la Agencia Española de
              Proteccion de Datos (AEPD) en{" "}
              <a
                href="https://www.aepd.es"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "var(--text)", textDecoration: "underline" }}
              >
                www.aepd.es
              </a>
              .
            </p>
          </div>
        </section>

        {/* 7. Seguridad */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>7. Seguridad del tratamiento</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              VISAI aplica medidas tecnicas y organizativas apropiadas para proteger tus datos personales frente a
              accesos no autorizados, perdida, destruccion o alteracion accidental. Estas medidas incluyen cifrado de
              datos en transito (TLS 1.2+), control de acceso basado en roles, registros de auditoria y revision
              periodica de los sistemas. En caso de brecha de seguridad que afecte a tus derechos y libertades,
              lo notificaremos a la AEPD en las 72 horas siguientes a su deteccion y a ti directamente si el riesgo
              fuera alto.
            </p>
          </div>
        </section>

        {/* 8. Cambios */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>8. Actualizaciones de esta politica</p>
          <div className="card">
            <p style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.75, margin: 0 }}>
              VISAI puede actualizar esta Politica de Privacidad para adaptarla a cambios legislativos o del servicio.
              Notificaremos los cambios sustanciales mediante aviso en la aplicacion o por correo electronico si
              disponemos de el. La fecha de "Ultima actualizacion" que aparece al inicio de este documento refleja
              siempre la version vigente.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ paddingBottom: 8, borderBottom: "1px solid var(--border)" }}>
      <p className="caption" style={{ margin: "0 0 2px" }}>{label}</p>
      <p style={{ fontSize: 14, color: "var(--text)", margin: 0 }}>{value}</p>
    </div>
  );
}

function DataBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="card">
      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", margin: "0 0 6px" }}>{title}</p>
      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.65, margin: 0 }}>{text}</p>
    </div>
  );
}

function LegalBasis({ type, text }: { type: string; text: string }) {
  return (
    <div style={{ paddingBottom: 10, borderBottom: "1px solid var(--border)" }}>
      <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", margin: "0 0 3px" }}>{type}</p>
      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.55, margin: 0 }}>{text}</p>
    </div>
  );
}

function RetentionRow({ category, period }: { category: string; period: string }) {
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "flex-start",
      gap: 12, paddingBottom: 8, borderBottom: "1px solid var(--border)",
    }}>
      <span style={{ fontSize: 13, color: "var(--text-muted)", flex: 1 }}>{category}</span>
      <span style={{ fontSize: 13, color: "var(--text)", fontWeight: 600, textAlign: "right", flexShrink: 0 }}>{period}</span>
    </div>
  );
}

function ProcessorBlock({
  name, role, location, transfer, url,
}: {
  name: string; role: string; location: string; transfer: string; url: string;
}) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
        <p style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", margin: 0 }}>{name}</p>
        <span className="caption" style={{
          background: "var(--surface2)", padding: "2px 8px",
          borderRadius: "var(--r-full)", flexShrink: 0,
        }}>
          {location}
        </span>
      </div>
      <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "0 0 6px", lineHeight: 1.5 }}>{role}</p>
      <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 8px", lineHeight: 1.4 }}>
        Garantia: {transfer}
      </p>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "underline" }}
      >
        Politica de privacidad del encargado
      </a>
    </div>
  );
}

"use client";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";

export default function AvisoLegalPage() {
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
        <p className="label" style={{ marginBottom: 10 }}>Identificacion del titular</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", lineHeight: 1.2 }}>
          Aviso Legal
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          Actualizado el 6 de mayo de 2026
        </p>
      </div>

      {/* Content */}
      <div style={{ display: "flex", flexDirection: "column", gap: 28, paddingBottom: 48 }}>

        {/* 1. Datos identificativos */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>1. Datos identificativos</p>
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <p style={{ fontSize: 14, lineHeight: 1.65, margin: 0, color: "var(--text)" }}>
              En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la
              Información y de Comercio Electrónico (LSSI-CE), se facilitan los siguientes datos identificativos:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Row label="Denominacion social" value="[COMPLETAR]" />
              <Row label="NIF" value="[COMPLETAR]" />
              <Row label="Domicilio social" value="[COMPLETAR]" />
              <Row label="Registro Mercantil" value="[COMPLETAR]" />
              <Row label="Correo de contacto" value="info@visai.es" />
              <Row label="Correo de privacidad" value="privacy@visaiapp.com" />
              <Row label="Actividad" value="Analisis biometrico facial mediante inteligencia artificial orientado al sector de la peluqueria y barberia" />
            </div>
          </div>
        </section>

        {/* 2. Objeto del sitio */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>2. Objeto del sitio web</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              VISAI pone a disposicion de los usuarios una aplicacion web que, mediante el procesamiento de una imagen
              facial, genera recomendaciones orientativas de corte de cabello y barba adaptadas a la morfologia craneal
              del usuario. El resultado del analisis tiene caracter meramente informativo y orientativo, sin constituir
              en ningun caso asesoramiento profesional de salud, estetica medica ni actividad regulada equivalente.
            </p>
          </div>
        </section>

        {/* 3. Condiciones de acceso */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>3. Condiciones de acceso y uso</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              El acceso y uso de esta plataforma implica la aceptacion plena de las presentes condiciones legales, así
              como de la Politica de Privacidad y la Politica de Cookies. El usuario declara ser mayor de 18 años.
              Queda prohibido el uso del servicio para fines ilicitos, fraudulentos o contrarios al ordenamiento
              juridico español.
            </p>
          </div>
        </section>

        {/* 4. Propiedad intelectual */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>4. Propiedad intelectual e industrial</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              Todos los contenidos del sitio web — incluyendo, sin caracter limitativo, textos, graficos, imagenes,
              logotipos, iconos, codigo fuente, diseno visual y estructura — son propiedad exclusiva de VISAI o de sus
              licenciantes, y estan protegidos por la legislacion española e internacional sobre propiedad intelectual
              e industrial. Queda expresamente prohibida su reproduccion, distribucion, comunicacion publica o
              transformacion sin autorizacion escrita previa del titular.
            </p>
          </div>
        </section>

        {/* 5. Responsabilidad */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>5. Limitacion de responsabilidad</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              VISAI no garantiza la disponibilidad continua e ininterrumpida del servicio ni la ausencia de errores
              tecnicos. Los resultados del analisis facial son orientativos y no sustituyen el criterio profesional de
              un barbero o esteticista. VISAI no sera responsable de decisiones tomadas por el usuario exclusivamente
              en base al informe generado. En la maxima medida permitida por la legislacion aplicable, VISAI queda
              exonerada de cualquier daño directo, indirecto o consecuente derivado del uso o imposibilidad de uso del
              servicio.
            </p>
          </div>
        </section>

        {/* 6. Legislación aplicable */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>6. Legislacion y jurisdiccion</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              Las presentes condiciones se rigen por la legislacion española. Para la resolucion de cualquier
              controversia derivada del acceso o uso del presente sitio web, las partes, con renuncia a cualquier otro
              fuero que pudiera corresponderles, se someten a la jurisdiccion de los Juzgados y Tribunales de la ciudad
              del domicilio social de VISAI, salvo que la normativa aplicable establezca otro fuero imperativo.
            </p>
          </div>
        </section>

        {/* 7. Resolución de litigios en línea */}
        <section>
          <p className="label" style={{ marginBottom: 12 }}>7. Resolucion de litigios en linea</p>
          <div className="card">
            <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, color: "var(--text-muted)" }}>
              Conforme al Reglamento (UE) 524/2013, los consumidores de la Union Europea pueden acceder a la
              plataforma de resolucion de litigios en linea de la Comision Europea a traves de{" "}
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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 2,
      paddingBottom: 10, borderBottom: "1px solid var(--border)",
    }}>
      <span className="caption" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.5 }}>{value}</span>
    </div>
  );
}

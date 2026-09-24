"use client";

import Link from "next/link";
import { useState } from "react";
import { contextFromDossier, phasesFor } from "@/lib/checklist";
import { calcularCostes } from "@/lib/import-cost";
import { COUNTRIES } from "@/lib/portals";
import { evaluate, precioMaximo } from "@/lib/scoring";
import { useDossiers } from "./useDossiers";

const euros = (n: number) =>
  Math.round(n).toLocaleString("es-ES", { maximumFractionDigits: 0 }) + " €";

export default function Informe() {
  const { listo, activo: d } = useDossiers();
  const [copiado, setCopiado] = useState(false);

  if (!listo) {
    return (
      <main className="wrap narrow" style={{ paddingTop: 28 }}>
        <p className="muted">Cargando...</p>
      </main>
    );
  }

  if (!d) {
    return (
      <main className="wrap narrow" style={{ paddingTop: 28 }}>
        <h1 style={{ fontSize: 26 }}>Sin revisiones todavia</h1>
        <p className="muted small" style={{ marginTop: 8 }}>
          El informe se genera a partir de la revision guiada. Empieza por ahi.
        </p>
        <Link href="/revision" className="btn primary" style={{ marginTop: 18 }}>
          Revisar un coche
        </Link>
      </main>
    );
  }

  const ctx = contextFromDossier(d);
  const v = evaluate(d.answers, ctx);
  const costes = d.cost ? calcularCostes(d.cost) : null;
  const maximo = precioMaximo({
    precioEspana: d.cost?.precioEspana,
    sobrecosteImportacion: costes?.sobrecoste ?? 0,
    descuentoDefectos: v.descuento,
  });

  const clase =
    v.level === "ok" ? "ok" : v.level === "negociar" ? "warn" : v.level === "incompleto" ? "" : "bad";

  const pendientes = phasesFor(ctx)
    .map((f) => ({ ...f, items: f.items.filter((i) => !d.answers[i.id]) }))
    .filter((f) => f.items.length > 0);

  function resumenTexto(): string {
    const l: string[] = [];
    l.push(`${d!.name} — ${v.title}`);
    l.push(`Nota: ${v.score}/100 (${v.answered} de ${v.totalItems} puntos revisados)`);
    if (v.redFlags.length) l.push(`\nMotivos para irse:\n- ${v.redFlags.map((f) => f.label).join("\n- ")}`);
    if (v.negociables.length)
      l.push(
        `\nDefectos (${euros(v.descuento)} de arreglos):\n- ${v.negociables
          .map((f) => `${f.label}${f.repairCost ? ` (~${f.repairCost} EUR)` : ""}`)
          .join("\n- ")}`,
      );
    if (costes) l.push(`\nCoste puerta a puerta en Espana: ${euros(costes.total)} (+${euros(costes.sobrecoste)} sobre el anuncio)`);
    if (maximo) l.push(`Precio maximo recomendado: ${euros(maximo)}`);
    return l.join("\n");
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(resumenTexto());
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* sin portapapeles: el usuario siempre puede imprimir */
    }
  }

  return (
    <main className="wrap narrow" style={{ paddingTop: 24, paddingBottom: 46 }}>
      <div className="spread">
        <div>
          <h1 style={{ fontSize: 26 }}>{d.name}</h1>
          <div className="tiny dim">
            Revision del {new Date(d.updatedAt).toLocaleDateString("es-ES")}
            {ctx.country ? ` · ${COUNTRIES[ctx.country]?.flag} ${COUNTRIES[ctx.country]?.name}` : ""}
          </div>
        </div>
        <span className={`pill ${clase}`}>{v.title}</span>
      </div>

      <section className="card" style={{ marginTop: 20 }}>
        <div className="row" style={{ gap: 26 }}>
          <div>
            <div className="tiny dim">NOTA</div>
            <div className="big-num">{v.answered === 0 ? "—" : v.score}</div>
          </div>
          <div>
            <div className="tiny dim">REVISADO</div>
            <div className="big-num">
              {Math.round((v.answered / Math.max(1, v.totalItems)) * 100)}%
            </div>
          </div>
          {v.descuento > 0 && (
            <div>
              <div className="tiny dim">ARREGLOS</div>
              <div className="big-num" style={{ color: "var(--warn)" }}>
                {euros(v.descuento)}
              </div>
            </div>
          )}
        </div>
        <p style={{ marginTop: 16, fontSize: 15.5, lineHeight: 1.6 }}>{v.message}</p>
      </section>

      {v.redFlags.length > 0 && (
        <section className="card" style={{ marginTop: 16, borderColor: "var(--bad)" }}>
          <h3 style={{ color: "var(--bad)" }}>Motivos para levantarse e irse</h3>
          <div className="stack" style={{ marginTop: 12 }}>
            {v.redFlags.map((f) => (
              <div key={f.id} className="note bad small">
                <strong style={{ color: "var(--text)" }}>{f.label}</strong>
                {d.notes[f.id] && <div className="dim">{d.notes[f.id]}</div>}
              </div>
            ))}
          </div>
        </section>
      )}

      {v.negociables.length > 0 && (
        <section className="card" style={{ marginTop: 16 }}>
          <div className="spread">
            <h3>Para negociar</h3>
            <span className="pill warn">
              {v.descuento > 0 ? euros(v.descuento) : `${v.negociables.length} puntos`}
            </span>
          </div>
          <p className="tiny muted" style={{ marginTop: 6 }}>
            No pidas descuento en general: ensena esta lista y pide el importe de cada arreglo.
          </p>
          <div className="lines" style={{ marginTop: 12 }}>
            {v.negociables.map((f) => (
              <div key={f.id} className="line">
                <div>
                  <div className="small">{f.label}</div>
                  {d.notes[f.id] && <div className="tiny dim">{d.notes[f.id]}</div>}
                </div>
                <div className="amt">{f.repairCost ? euros(f.repairCost) : "—"}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {costes && (
        <section className="card" style={{ marginTop: 16 }}>
          <h3>Coste puerta a puerta</h3>
          <div className="lines" style={{ marginTop: 12 }}>
            {costes.lines.map((l) => (
              <div key={l.key} className="line">
                <span className="small">{l.label}</span>
                <span className="amt">{euros(l.amount)}</span>
              </div>
            ))}
            <div className="line total">
              <span>Total en Espana</span>
              <span className="amt">{euros(costes.total)}</span>
            </div>
          </div>
        </section>
      )}

      {maximo !== undefined && (
        <section className="card" style={{ marginTop: 16, borderColor: "var(--accent-line)" }}>
          <div className="tiny dim">NO PAGUES MAS DE</div>
          <div className="big-num" style={{ color: "var(--accent)" }}>
            {euros(maximo)}
          </div>
          <p className="small muted" style={{ marginTop: 8 }}>
            Precio del mismo coche en Espana, menos lo que cuesta traerlo, menos los arreglos
            detectados, menos un 5% de margen para los imprevistos. Por encima de esa cifra, sale
            mejor comprarlo aqui.
          </p>
        </section>
      )}

      {pendientes.length > 0 && (
        <section className="card" style={{ marginTop: 16 }}>
          <h3>Te falta por mirar</h3>
          <div className="stack small muted" style={{ marginTop: 10 }}>
            {pendientes.map((f) => (
              <div key={f.id}>
                <strong style={{ color: "var(--text)" }}>{f.title}:</strong>{" "}
                {f.items.map((i) => i.label).join(" · ")}
              </div>
            ))}
          </div>
          <Link href="/revision" className="btn sm" style={{ marginTop: 14 }}>
            Seguir revisando
          </Link>
        </section>
      )}

      <div className="row no-print" style={{ marginTop: 22 }}>
        <button className="btn primary" onClick={() => window.print()}>
          Imprimir o guardar en PDF
        </button>
        <button className="btn" onClick={copiar}>
          {copiado ? "Copiado" : "Copiar resumen"}
        </button>
        <a
          className="btn ghost"
          href={`https://wa.me/?text=${encodeURIComponent(resumenTexto())}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          Enviar por WhatsApp
        </a>
      </div>
    </main>
  );
}

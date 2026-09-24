"use client";

import Link from "next/link";
import { createDossier, deleteDossier, setActiveId } from "@/lib/storage";
import { evaluate } from "@/lib/scoring";
import { contextFromDossier } from "@/lib/checklist";
import { useDossiers } from "./useDossiers";

export default function Dossiers() {
  const { listo, dossiers } = useDossiers();

  if (!listo) return null;

  function nuevo() {
    const nombre = window.prompt("Que coche vas a mirar?", "BMW Serie 3 2019");
    if (nombre === null) return;
    createDossier({ name: nombre.trim() || "Coche sin nombre" });
  }

  function borrar(id: string, name: string) {
    if (!window.confirm(`Borrar "${name}" y su revision?`)) return;
    deleteDossier(id);
  }

  return (
    <section style={{ marginTop: 52 }}>
      <div className="spread" style={{ marginBottom: 14 }}>
        <h2>Tus coches</h2>
        <button className="btn sm" onClick={nuevo}>
          + Anadir coche
        </button>
      </div>

      {dossiers.length === 0 ? (
        <div className="card flat" style={{ borderStyle: "dashed" }}>
          <p className="muted small">
            Todavia no sigues ningun coche. Cada uno que te interese se guarda aqui con su revision,
            sus notas y su calculo de costes. Todo queda en este navegador.
          </p>
        </div>
      ) : (
        <div className="grid grid-2">
          {dossiers.map((d) => {
            const v = evaluate(d.answers, contextFromDossier(d));
            const clase =
              v.level === "ok"
                ? "ok"
                : v.level === "huir" || v.level === "riesgo"
                  ? "bad"
                  : v.level === "negociar"
                    ? "warn"
                    : "";
            return (
              <div key={d.id} className="card">
                <div className="spread">
                  <strong>{d.name}</strong>
                  <span className={`pill ${clase}`}>
                    {v.level === "incompleto" ? "En curso" : v.title}
                  </span>
                </div>
                <div className="bar" style={{ margin: "12px 0 8px" }}>
                  <i style={{ width: `${Math.round((v.answered / Math.max(1, v.totalItems)) * 100)}%` }} />
                </div>
                <div className="spread tiny muted">
                  <span>
                    {v.answered} de {v.totalItems} puntos
                  </span>
                  <span>{v.descuento > 0 ? `${v.descuento} EUR a negociar` : ""}</span>
                </div>
                <div className="row" style={{ marginTop: 14 }}>
                  <Link href="/revision" className="btn sm" onClick={() => setActiveId(d.id)}>
                    Seguir revision
                  </Link>
                  <Link href="/informe" className="btn sm ghost" onClick={() => setActiveId(d.id)}>
                    Informe
                  </Link>
                  <button
                    className="btn sm ghost"
                    style={{ marginLeft: "auto", color: "var(--dim)" }}
                    onClick={() => borrar(d.id, d.name)}
                  >
                    Borrar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

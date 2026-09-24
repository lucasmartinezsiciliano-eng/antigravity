"use client";

import Link from "next/link";
import { useState } from "react";
import { contextFromDossier, phasesFor } from "@/lib/checklist";
import { evaluate } from "@/lib/scoring";
import { COUNTRIES } from "@/lib/portals";
import { createDossier, saveDossier, setActiveId, setAnswer, setNote } from "@/lib/storage";
import { useDossiers } from "./useDossiers";
import type { Answer, CountryCode, Dossier, Fuel, Gearbox } from "@/lib/types";

const PAISES: CountryCode[] = ["DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU"];

export default function Revision() {
  const { listo, dossiers, activo: d } = useDossiers();
  const [fase, setFase] = useState(0);
  const [abierto, setAbierto] = useState<string | null>(null);
  const [nombreNuevo, setNombreNuevo] = useState("");

  if (!listo) {
    return (
      <main className="wrap narrow" style={{ paddingTop: 28 }}>
        <p className="muted">Cargando...</p>
      </main>
    );
  }

  if (!d) {
    return (
      <main className="wrap narrow" style={{ paddingTop: 28, paddingBottom: 40 }}>
        <h1 style={{ fontSize: 26 }}>Revisar un coche</h1>
        <p className="muted small" style={{ marginTop: 8 }}>
          Ponle nombre para reconocerlo. Despues eliges de que pais es y que motor lleva, y la lista
          se adapta a ese coche.
        </p>
        <div className="card" style={{ marginTop: 20 }}>
          <label className="field">
            Que coche vas a revisar
            <input
              autoFocus
              value={nombreNuevo}
              onChange={(e) => setNombreNuevo(e.target.value)}
              placeholder="BMW 320d 2019 de Munich"
              onKeyDown={(e) => {
                if (e.key === "Enter" && nombreNuevo.trim()) {
                  createDossier({ name: nombreNuevo.trim() });
                }
              }}
            />
          </label>
          <button
            className="btn primary"
            style={{ marginTop: 14 }}
            disabled={!nombreNuevo.trim()}
            onClick={() => createDossier({ name: nombreNuevo.trim() })}
          >
            Empezar revision
          </button>
        </div>
      </main>
    );
  }

  const ctx = contextFromDossier(d);
  const fases = phasesFor(ctx);
  const actual = fases[Math.min(fase, fases.length - 1)];
  const v = evaluate(d.answers, ctx);

  function responder(itemId: string, a: Answer) {
    setAnswer(d!.id, itemId, d!.answers[itemId] === a ? null : a);
  }

  function cambiarCoche(id: string) {
    setActiveId(id);
    setFase(0);
  }

  function nuevoCoche() {
    const nombre = window.prompt("Que coche vas a revisar?", "");
    if (nombre === null) return;
    createDossier({ name: nombre.trim() || "Coche sin nombre" });
    setFase(0);
  }

  function editarFicha<K extends keyof NonNullable<Dossier["listing"]>>(
    k: K,
    valor: NonNullable<Dossier["listing"]>[K],
  ) {
    saveDossier({ ...d!, listing: { ...d!.listing, [k]: valor } });
  }

  const respondidasFase = actual.items.filter((it) => d.answers[it.id]).length;

  return (
    <main className="wrap narrow" style={{ paddingTop: 24, paddingBottom: 46 }}>
      <div className="spread">
        <div style={{ minWidth: 0 }}>
          <input
            value={d.name}
            onChange={(e) => saveDossier({ ...d, name: e.target.value })}
            style={{
              border: 0,
              background: "transparent",
              padding: 0,
              fontSize: 24,
              fontWeight: 650,
              letterSpacing: "-0.02em",
            }}
          />
          <div className="tiny dim">Se guarda solo, en este navegador</div>
        </div>
        <div className="row" style={{ gap: 6 }}>
          {dossiers.length > 1 && (
            <select
              value={d.id}
              onChange={(e) => cambiarCoche(e.target.value)}
              style={{ width: "auto", fontSize: 13, padding: "7px 30px 7px 10px" }}
            >
              {dossiers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          )}
          <button className="btn sm" onClick={nuevoCoche}>
            + Otro
          </button>
        </div>
      </div>

      {/* Datos que personalizan la lista */}
      <div className="card" style={{ marginTop: 18 }}>
        <div className="tiny dim" style={{ marginBottom: 10 }}>
          DE DONDE Y QUE ES: cambia los puntos que hay que revisar
        </div>
        <div className="grid grid-3">
          <label className="field">
            Pais
            <select
              value={d.listing?.country ?? ""}
              onChange={(e) => editarFicha("country", (e.target.value || undefined) as CountryCode)}
            >
              <option value="">Sin elegir</option>
              {PAISES.map((c) => (
                <option key={c} value={c}>
                  {COUNTRIES[c].flag} {COUNTRIES[c].name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Combustible
            <select
              value={d.listing?.fuel ?? ""}
              onChange={(e) => editarFicha("fuel", (e.target.value || undefined) as Fuel)}
            >
              <option value="">Sin elegir</option>
              <option value="diesel">Diesel</option>
              <option value="gasolina">Gasolina</option>
              <option value="hibrido">Hibrido</option>
              <option value="phev">Hibrido enchufable</option>
              <option value="electrico">Electrico</option>
              <option value="glp">GLP</option>
            </select>
          </label>
          <label className="field">
            Cambio
            <select
              value={d.listing?.gearbox ?? ""}
              onChange={(e) => editarFicha("gearbox", (e.target.value || undefined) as Gearbox)}
            >
              <option value="">Sin elegir</option>
              <option value="manual">Manual</option>
              <option value="automatico">Automatico</option>
            </select>
          </label>
        </div>
      </div>

      {/* Marcador */}
      <div className="card" style={{ marginTop: 16, position: "sticky", top: 62, zIndex: 20 }}>
        <div className="spread">
          <div className="row" style={{ gap: 14 }}>
            <div>
              <div className="tiny dim">NOTA</div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>
                {v.answered === 0 ? "—" : `${v.score}`}
                {v.answered > 0 && <span className="dim" style={{ fontSize: 14 }}>/100</span>}
              </div>
            </div>
            <div>
              <div className="tiny dim">PUNTOS</div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>
                {v.answered}
                <span className="dim" style={{ fontSize: 14 }}>/{v.totalItems}</span>
              </div>
            </div>
            {v.descuento > 0 && (
              <div>
                <div className="tiny dim">A NEGOCIAR</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--warn)" }}>
                  {v.descuento} &euro;
                </div>
              </div>
            )}
          </div>
          <Link href="/informe" className="btn sm">
            Ver informe
          </Link>
        </div>
        <div className="bar" style={{ marginTop: 12 }}>
          <i style={{ width: `${Math.round((v.answered / Math.max(1, v.totalItems)) * 100)}%` }} />
        </div>
        {v.redFlags.length > 0 && (
          <div className="note bad small" style={{ marginTop: 12 }}>
            <strong style={{ color: "var(--bad)" }}>
              {v.redFlags.length} {v.redFlags.length === 1 ? "motivo" : "motivos"} para irte:
            </strong>{" "}
            {v.redFlags.map((f) => f.label).join(" · ")}
          </div>
        )}
      </div>

      {/* Fases */}
      <div className="chips" style={{ marginTop: 18, overflowX: "auto", paddingBottom: 4 }}>
        {fases.map((f, n) => {
          const hechas = f.items.filter((it) => d.answers[it.id]).length;
          return (
            <button
              key={f.id}
              className={`chip${n === fase ? " on" : ""}`}
              onClick={() => setFase(n)}
              style={{ whiteSpace: "nowrap" }}
            >
              {n + 1}. {f.title}{" "}
              <span style={{ opacity: 0.6 }}>
                {hechas}/{f.items.length}
              </span>
            </button>
          );
        })}
      </div>

      <section className="card" style={{ marginTop: 16 }}>
        <div className="spread">
          <h2 style={{ fontSize: 21 }}>{actual.title}</h2>
          <span className="pill">{actual.place}</span>
        </div>
        <p className="muted small" style={{ marginTop: 8 }}>
          {actual.subtitle}
        </p>

        <div style={{ marginTop: 6 }}>
          {actual.items.map((item) => {
            const a = d.answers[item.id];
            const nota = d.notes[item.id] ?? "";
            const open = abierto === item.id;
            return (
              <div key={item.id} className="check">
                <div className="check-head">
                  <div className="check-label">
                    <button
                      onClick={() => setAbierto(open ? null : item.id)}
                      style={{
                        background: "none",
                        border: 0,
                        padding: 0,
                        color: "inherit",
                        font: "inherit",
                        textAlign: "left",
                        cursor: item.detail ? "pointer" : "default",
                      }}
                    >
                      {item.label}
                      {item.critical && (
                        <span className="pill bad tiny" style={{ marginLeft: 7, padding: "1px 7px" }}>
                          clave
                        </span>
                      )}
                      {item.detail && (
                        <span className="dim tiny" style={{ marginLeft: 6 }}>
                          {open ? "▴" : "▾"}
                        </span>
                      )}
                    </button>
                    {open && item.detail && (
                      <p className="small muted" style={{ marginTop: 8, paddingRight: 8 }}>
                        {item.detail}
                        {item.repairCost ? (
                          <span style={{ color: "var(--warn)" }}>
                            {" "}
                            Si falla, cuenta unos {item.repairCost} &euro; de arreglo.
                          </span>
                        ) : null}
                      </p>
                    )}
                  </div>
                  <div className="answers">
                    <button
                      className={`ans${a === "ok" ? " on-ok" : ""}`}
                      onClick={() => responder(item.id, "ok")}
                      aria-label="Bien"
                    >
                      OK
                    </button>
                    <button
                      className={`ans${a === "ko" ? " on-ko" : ""}`}
                      onClick={() => responder(item.id, "ko")}
                      aria-label="Mal"
                    >
                      MAL
                    </button>
                    <button
                      className={`ans${a === "na" ? " on-na" : ""}`}
                      onClick={() => responder(item.id, "na")}
                      aria-label="No aplica"
                    >
                      N/A
                    </button>
                  </div>
                </div>
                {(a === "ko" || nota) && (
                  <input
                    value={nota}
                    onChange={(e) => setNote(d.id, item.id, e.target.value)}
                    placeholder="Que has visto exactamente..."
                    style={{ marginTop: 10, fontSize: 14 }}
                  />
                )}
              </div>
            );
          })}
        </div>

        <div className="spread" style={{ marginTop: 20 }}>
          <button className="btn ghost" onClick={() => setFase(Math.max(0, fase - 1))} disabled={fase === 0}>
            &larr; Anterior
          </button>
          <span className="tiny dim">
            {respondidasFase}/{actual.items.length} en esta fase
          </span>
          {fase < fases.length - 1 ? (
            <button className="btn primary" onClick={() => setFase(fase + 1)}>
              {fases[fase + 1].title} &rarr;
            </button>
          ) : (
            <Link href="/informe" className="btn primary">
              Ver veredicto &rarr;
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}

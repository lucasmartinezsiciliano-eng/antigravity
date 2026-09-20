"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { COUNTRIES } from "@/lib/portals";
import { createDossier } from "@/lib/storage";
import type { CountryCode, Fuel, Listing, SearchFilters, SearchResponse } from "@/lib/types";

const PAISES: CountryCode[] = ["DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU"];

const COMBUSTIBLES: { v: Fuel | ""; label: string }[] = [
  { v: "", label: "Cualquiera" },
  { v: "diesel", label: "Diesel" },
  { v: "gasolina", label: "Gasolina" },
  { v: "hibrido", label: "Hibrido" },
  { v: "phev", label: "Hibrido enchufable" },
  { v: "electrico", label: "Electrico" },
  { v: "glp", label: "GLP" },
];

const euros = (n: number) => n.toLocaleString("es-ES", { maximumFractionDigits: 0 }) + " €";

/**
 * Las imagenes de los portales fallan a menudo: enlaces caducados, proteccion
 * contra hotlinking, anuncios retirados. Un icono de imagen rota queda peor
 * que no poner nada, asi que se cae a la bandera del pais.
 */
function Miniatura({ src, country }: { src?: string; country: CountryCode }) {
  const [roto, setRoto] = useState(false);
  const bandera = COUNTRIES[country]?.flag ?? "\u{1F697}";

  if (!src || roto) {
    return (
      <div className="thumb">
        <span>{bandera}</span>
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt=""
      className="thumb"
      style={{ margin: 0 }}
      loading="lazy"
      onError={() => setRoto(true)}
    />
  );
}

export default function Buscador() {
  const router = useRouter();
  const [f, setF] = useState<SearchFilters>({
    make: "",
    model: "",
    countries: ["DE", "FR"],
    sort: "coste-total",
  });
  const [res, setRes] = useState<SearchResponse | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof SearchFilters>(k: K, v: SearchFilters[K]) =>
    setF((prev) => ({ ...prev, [k]: v }));

  const num = (v: string) => (v === "" ? undefined : Number(v));

  function togglePais(c: CountryCode) {
    setF((prev) => ({
      ...prev,
      countries: prev.countries.includes(c)
        ? prev.countries.filter((x) => x !== c)
        : [...prev.countries, c],
    }));
  }

  async function buscar(e?: React.FormEvent) {
    e?.preventDefault();
    setCargando(true);
    setError(null);
    try {
      const r = await fetch("/api/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(f),
      });
      if (!r.ok) throw new Error(`Error ${r.status}`);
      setRes((await r.json()) as SearchResponse);
    } catch {
      setError("No se ha podido completar la busqueda. Intentalo otra vez.");
    } finally {
      setCargando(false);
    }
  }

  function abrirTodos() {
    const urls = (res?.portals ?? []).filter((p) => p.searchUrl).map((p) => p.searchUrl);
    urls.forEach((u, i) => setTimeout(() => window.open(u, "_blank", "noopener"), i * 250));
  }

  function revisar(l: Listing) {
    createDossier({
      name: `${l.title}${l.year ? ` (${l.year})` : ""}`,
      listing: l,
    });
    router.push("/revision");
  }

  function calcular(l: Listing) {
    const q = new URLSearchParams({
      price: String(l.price),
      country: l.country,
      ...(l.co2 ? { co2: String(l.co2) } : {}),
      ...(l.year ? { year: String(l.year) } : {}),
      ...(l.km ? { km: String(l.km) } : {}),
      ...(l.fuel ? { fuel: l.fuel } : {}),
      name: l.title,
    });
    router.push(`/coste?${q}`);
  }

  const anuncios = res?.listings ?? [];
  const portalesBusqueda = (res?.portals ?? []).filter((p) => p.searchUrl);

  return (
    <main className="wrap" style={{ paddingTop: 28, paddingBottom: 40 }}>
      <h1 style={{ fontSize: 28 }}>Buscar en toda Europa</h1>
      <p className="muted small" style={{ marginTop: 8, maxWidth: 620 }}>
        Rellena los filtros una vez. La misma busqueda se lanza contra todos los portales de los
        paises que elijas, y los espanoles se anaden aparte para comparar precios.
      </p>

      <form className="card" style={{ marginTop: 22 }} onSubmit={buscar}>
        <div className="grid grid-3">
          <label className="field">
            Marca
            <input
              value={f.make}
              onChange={(e) => set("make", e.target.value)}
              placeholder="BMW"
              autoComplete="off"
            />
          </label>
          <label className="field">
            Modelo
            <input
              value={f.model}
              onChange={(e) => set("model", e.target.value)}
              placeholder="Serie 3"
              autoComplete="off"
            />
          </label>
          <label className="field">
            Combustible
            <select
              value={f.fuel ?? ""}
              onChange={(e) => set("fuel", (e.target.value || undefined) as Fuel | undefined)}
            >
              {COMBUSTIBLES.map((c) => (
                <option key={c.v} value={c.v}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Precio desde
            <input
              type="number"
              inputMode="numeric"
              value={f.priceFrom ?? ""}
              onChange={(e) => set("priceFrom", num(e.target.value))}
              placeholder="5000"
            />
          </label>
          <label className="field">
            Precio hasta
            <input
              type="number"
              inputMode="numeric"
              value={f.priceTo ?? ""}
              onChange={(e) => set("priceTo", num(e.target.value))}
              placeholder="20000"
            />
          </label>
          <label className="field">
            Km maximo
            <input
              type="number"
              inputMode="numeric"
              value={f.kmTo ?? ""}
              onChange={(e) => set("kmTo", num(e.target.value))}
              placeholder="150000"
            />
          </label>
          <label className="field">
            Ano desde
            <input
              type="number"
              inputMode="numeric"
              value={f.yearFrom ?? ""}
              onChange={(e) => set("yearFrom", num(e.target.value))}
              placeholder="2017"
            />
          </label>
          <label className="field">
            Ano hasta
            <input
              type="number"
              inputMode="numeric"
              value={f.yearTo ?? ""}
              onChange={(e) => set("yearTo", num(e.target.value))}
              placeholder="2023"
            />
          </label>
          <label className="field">
            CV minimos
            <input
              type="number"
              inputMode="numeric"
              value={f.powerFrom ?? ""}
              onChange={(e) => set("powerFrom", num(e.target.value))}
              placeholder="140"
            />
          </label>
          <label className="field">
            Cambio
            <select
              value={f.gearbox ?? ""}
              onChange={(e) =>
                set("gearbox", (e.target.value || undefined) as SearchFilters["gearbox"])
              }
            >
              <option value="">Cualquiera</option>
              <option value="manual">Manual</option>
              <option value="automatico">Automatico</option>
            </select>
          </label>
          <label className="field">
            Vendedor
            <select
              value={f.seller ?? ""}
              onChange={(e) =>
                set("seller", (e.target.value || undefined) as SearchFilters["seller"])
              }
            >
              <option value="">Cualquiera</option>
              <option value="particular">Particular</option>
              <option value="profesional">Profesional</option>
            </select>
          </label>
          <label className="field">
            Ordenar por
            <select value={f.sort} onChange={(e) => set("sort", e.target.value as SearchFilters["sort"])}>
              <option value="coste-total">Coste puerta a puerta</option>
              <option value="precio">Precio del anuncio</option>
              <option value="km">Kilometros</option>
              <option value="antiguedad">Mas nuevo</option>
            </select>
          </label>
        </div>

        <div style={{ marginTop: 18 }}>
          <div className="small muted" style={{ marginBottom: 8 }}>
            Paises de busqueda
          </div>
          <div className="chips">
            {PAISES.map((c) => (
              <button
                type="button"
                key={c}
                className={`chip${f.countries.includes(c) ? " on" : ""}`}
                onClick={() => togglePais(c)}
              >
                {COUNTRIES[c].flag} {COUNTRIES[c].name}
              </button>
            ))}
          </div>
        </div>

        <div className="row" style={{ marginTop: 20 }}>
          <button className="btn primary" type="submit" disabled={cargando || f.countries.length === 0}>
            {cargando ? "Buscando..." : "Buscar en todos los portales"}
          </button>
          {res && portalesBusqueda.length > 0 && (
            <button className="btn" type="button" onClick={abrirTodos}>
              Abrir los {portalesBusqueda.length} portales
            </button>
          )}
        </div>
        {f.countries.length === 0 && (
          <p className="tiny" style={{ color: "var(--warn)", marginTop: 10 }}>
            Elige al menos un pais.
          </p>
        )}
      </form>

      {error && (
        <div className="note bad" style={{ marginTop: 20 }}>
          {error}
        </div>
      )}

      {res && (
        <>
          {anuncios.length > 0 && (
            <section style={{ marginTop: 34 }}>
              <div className="spread">
                <h2>
                  {anuncios.length} {anuncios.length === 1 ? "coche" : "coches"}
                </h2>
                <span className="tiny dim">
                  {f.sort === "coste-total" ? "ordenados por coste ya en Espana" : ""}
                </span>
              </div>

              {anuncios.some((l) => l.demo) && (
                <div className="note warn" style={{ marginTop: 12 }}>
                  <strong style={{ color: "var(--text)" }}>Estas viendo fichas de ejemplo.</strong> No
                  hay ninguna fuente en vivo conectada, asi que mostramos coches inventados para que
                  veas como funciona la lista. Los anuncios de verdad estan en los portales de abajo.
                </div>
              )}

              <div className="stack" style={{ marginTop: 14 }}>
                {anuncios.map((l) => (
                  <article key={l.id} className="listing">
                    <Miniatura src={l.image} country={l.country} />
                    <div style={{ minWidth: 0 }}>
                      <div className="spread" style={{ alignItems: "flex-start" }}>
                        <strong style={{ fontSize: 15.5 }}>{l.title}</strong>
                        <span className="mono" style={{ fontWeight: 650, whiteSpace: "nowrap" }}>
                          {euros(l.price)}
                        </span>
                      </div>
                      <div className="row tiny muted" style={{ gap: 8, marginTop: 5 }}>
                        {l.year && <span>{l.year}</span>}
                        {l.km !== undefined && <span>{l.km.toLocaleString("es-ES")} km</span>}
                        {l.power && <span>{l.power} CV</span>}
                        {l.fuel && <span>{l.fuel}</span>}
                        {l.co2 !== undefined && <span>{l.co2} g/km</span>}
                        <span>
                          {COUNTRIES[l.country]?.flag} {l.city ?? COUNTRIES[l.country]?.name}
                        </span>
                        {l.demo && <span className="pill warn">EJEMPLO</span>}
                        {!l.demo && <span className="pill">{l.sourceName}</span>}
                      </div>
                      {l.landedCost !== undefined && (
                        <div className="tiny" style={{ marginTop: 7, color: "var(--accent)" }}>
                          ~{euros(l.landedCost)} matriculado en Espana
                          <span className="dim"> (+{euros(l.landedCost - l.price)})</span>
                        </div>
                      )}
                      <div className="row" style={{ marginTop: 10, gap: 7 }}>
                        <button className="btn sm" onClick={() => calcular(l)}>
                          Coste exacto
                        </button>
                        <button className="btn sm" onClick={() => revisar(l)}>
                          Revisar este
                        </button>
                        {l.url && (
                          <a className="btn sm ghost" href={l.url} target="_blank" rel="noopener noreferrer">
                            Ver anuncio
                          </a>
                        )}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          <section style={{ marginTop: 38 }}>
            <h2>Busqueda lanzada en {portalesBusqueda.length} portales</h2>
            <p className="muted small" style={{ marginTop: 8 }}>
              Cada tarjeta abre ese portal con tus filtros ya aplicados. Es la forma honesta de
              buscar en todos: ninguno de ellos deja consultar su catalogo desde fuera.
            </p>
            <div className="grid grid-3" style={{ marginTop: 16 }}>
              {portalesBusqueda.map((p) => (
                <a
                  key={p.portal}
                  className="portal-card"
                  href={p.searchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <div className="spread">
                    <strong style={{ fontSize: 15 }}>{p.name}</strong>
                    <span className="tiny dim">
                      {p.countries.map((c) => COUNTRIES[c]?.flag).join(" ")}
                    </span>
                  </div>
                  <span className="tiny muted">{p.note}</span>
                  <span className="tiny" style={{ color: "var(--accent)", marginTop: "auto" }}>
                    Abrir busqueda &rarr;
                  </span>
                </a>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}

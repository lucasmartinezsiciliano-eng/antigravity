/**
 * El motor: lanza todos los proveedores a la vez, junta lo que vuelve y lo
 * deja en una sola lista comparable.
 *
 * Tres decisiones de diseno que no son negociables:
 *
 *  1. BAJO DEMANDA. Se consulta cuando alguien busca, y no se guarda nada.
 *     No hay indice. Es lo que ampara la jurisprudencia europea de
 *     metabusqueda y lo que separa esto de un scraper.
 *  2. UN PROVEEDOR LENTO NO BLOQUEA LA RESPUESTA. Cada uno tiene su plazo y
 *     el que no llega se reporta como timeout, no se espera.
 *  3. UN PROVEEDOR QUE FALLA NO TUMBA LA BUSQUEDA. Se anota su estado y se
 *     sigue. Media respuesta util vale mas que un error entero.
 */

import { isPartial, ProviderError, type Provider, type ProviderContext } from "./providers/types.ts";
import type { Listing, ProviderResult, Query, SearchResponse } from "./schema.ts";
import { SCHEMA_VERSION, isUsable } from "./schema.ts";
import type { Fetcher } from "./http/fetcher.ts";
import { RobotsBlocked } from "./http/fetcher.ts";

export interface EngineOptions {
  fetcher: Fetcher;
  env?: Record<string, string | undefined>;
  /** Plazo por proveedor. Pasado eso, se responde sin el. */
  providerTimeoutMs?: number;
  log?: (msg: string) => void;
}

export async function search(
  providers: Provider[],
  query: Query,
  warnings: string[],
  opts: EngineOptions,
): Promise<SearchResponse> {
  const t0 = Date.now();
  const env = opts.env ?? process.env;
  const timeout = opts.providerTimeoutMs ?? 12_000;

  const resultados = await Promise.all(
    providers.map((p) => ejecutar(p, query, { ...opts, env, providerTimeoutMs: timeout })),
  );

  const todos = resultados.flatMap((r) => r.listings);
  const { listings, deduped } = fusionar(todos);
  ordenar(listings, query.sort);

  return {
    schemaVersion: SCHEMA_VERSION,
    query,
    listings: listings.slice(0, (query.limit ?? 50) * 3),
    providers: resultados.map((r) => r.meta),
    deduped,
    ms: Date.now() - t0,
    warnings,
  };
}

async function ejecutar(
  provider: Provider,
  query: Query,
  opts: EngineOptions & { env: Record<string, string | undefined>; providerTimeoutMs: number },
): Promise<{ meta: ProviderResult; listings: Listing[] }> {
  const t0 = Date.now();
  const { meta } = provider;
  const base: ProviderResult = {
    provider: meta.id,
    name: meta.name,
    status: "ok",
    count: 0,
    ms: 0,
    searchUrl: safe(() => provider.searchUrl(query)),
  };
  const fin = (status: ProviderResult["status"], message?: string, listings: Listing[] = []) => ({
    meta: { ...base, status, message, count: listings.length, ms: Date.now() - t0 },
    listings,
  });

  if (!provider.search) return fin("solo-enlace", "este portal solo se abre por enlace: no expone sus anuncios");

  const faltan = (meta.requiresEnv ?? []).filter((k) => !opts.env[k]);
  if (faltan.length) return fin("sin-credenciales", `faltan ${faltan.join(", ")}`);

  const ac = new AbortController();
  const reloj = setTimeout(() => ac.abort(), opts.providerTimeoutMs);

  try {
    const ctx: ProviderContext = {
      fetch: (url, init) => opts.fetcher.fetch(url, { ...init, signal: ac.signal }),
      signal: ac.signal,
      env: opts.env,
      log: (m) => opts.log?.(`[${meta.id}] ${m}`),
    };

    const salida = await provider.search(query, ctx);
    const partial = isPartial(salida) ? salida : { listings: salida };
    const limpios = partial.listings.filter(isUsable).slice(0, query.limit ?? 50);

    if (partial.status && partial.status !== "ok") return fin(partial.status, partial.message, limpios);
    return fin(limpios.length ? "ok" : "vacio", partial.message, limpios);
  } catch (e) {
    if (ac.signal.aborted) return fin("timeout", `mas de ${opts.providerTimeoutMs} ms`);
    if (e instanceof RobotsBlocked) return fin("bloqueado-robots", e.message);
    if (e instanceof ProviderError) return fin(e.status, e.message);
    return fin("error", e instanceof Error ? e.message : String(e));
  } finally {
    clearTimeout(reloj);
  }
}

function safe<T>(fn: () => T): T | undefined {
  try {
    return fn();
  } catch {
    return undefined;
  }
}

// --- Deduplicacion ---------------------------------------------------------

/**
 * El mismo coche esta publicado a la vez en varios portales, a veces con
 * precios distintos. Se fusionan y se queda el mas barato, anotando en
 * `derived.alsoOn` donde mas aparece: saber que un anuncio esta en cuatro
 * sitios es informacion util para el que compra.
 */
export function fusionar(listings: Listing[]): { listings: Listing[]; deduped: number } {
  const porClave = new Map<string, Listing>();
  let deduped = 0;

  for (const l of listings) {
    const claves = huellas(l);
    const existente = claves.map((k) => porClave.get(k)).find(Boolean);

    if (!existente) {
      for (const k of claves) porClave.set(k, l);
      continue;
    }

    deduped++;
    const ganador = elegir(existente, l);
    const otros = new Set<string>([
      ...((existente.derived?.alsoOn?.value as string[]) ?? []),
      existente.provider,
      l.provider,
    ]);
    otros.delete(ganador.provider);

    const fusionado: Listing = {
      ...completar(ganador, existente === ganador ? l : existente),
      derived: {
        ...ganador.derived,
        ...(otros.size
          ? { alsoOn: { value: [...otros], source: "dedupe", confidence: "media" as const } }
          : {}),
      },
    };
    for (const k of [...claves, ...huellas(existente)]) porClave.set(k, fusionado);
  }

  return { listings: [...new Set(porClave.values())], deduped };
}

/** Varias huellas por anuncio: con que coincida una, es el mismo coche. */
function huellas(l: Listing): string[] {
  const out: string[] = [];
  if (l.vin && l.vin.length === 17) out.push(`vin:${l.vin.toUpperCase()}`);
  out.push(`url:${l.url.split("?")[0]!.toLowerCase().replace(/\/$/, "")}`);

  // Huella difusa: mismo coche, mismos km redondeados y mismo precio aproximado.
  if (l.make && l.year && l.km !== undefined && l.price) {
    out.push(
      [
        "fz",
        l.make.toLowerCase(),
        (l.model ?? "").toLowerCase(),
        l.year,
        Math.round(l.km / 2000),
        Math.round(l.price / 300),
      ].join("|"),
    );
  }
  return out;
}

/** Ante dos versiones del mismo coche, la mas barata; a igual precio, la mas completa. */
function elegir(a: Listing, b: Listing): Listing {
  if (a.price && b.price && a.price !== b.price) return a.price < b.price ? a : b;
  return campos(a) >= campos(b) ? a : b;
}

const campos = (l: Listing) => Object.values(l).filter((v) => v !== undefined).length;

/** Rellena los huecos del ganador con lo que sepa el otro anuncio. */
function completar(base: Listing, otro: Listing): Listing {
  const out = { ...base };
  for (const [k, v] of Object.entries(otro) as [keyof Listing, unknown][]) {
    if (out[k] === undefined && v !== undefined && k !== "id" && k !== "provider" && k !== "url") {
      (out as Record<string, unknown>)[k] = v;
    }
  }
  return out;
}

// --- Orden -----------------------------------------------------------------

function ordenar(listings: Listing[], sort: Query["sort"] = "precio") {
  const inf = Number.POSITIVE_INFINITY;
  const cmp: Record<NonNullable<Query["sort"]>, (a: Listing, b: Listing) => number> = {
    precio: (a, b) => (a.price ?? inf) - (b.price ?? inf),
    km: (a, b) => (a.km ?? inf) - (b.km ?? inf),
    antiguedad: (a, b) => (b.year ?? 0) - (a.year ?? 0),
    // Sin senal de relevancia real, lo mas util es lo mas descrito primero.
    relevancia: (a, b) => campos(b) - campos(a),
  };
  listings.sort(cmp[sort] ?? cmp.precio);
}
